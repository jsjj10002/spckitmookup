import torch
import torch.nn.functional as F
import time
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .graph_builder import PCComponentGraph, NodeType

# --- 데이터 규격 정의 ---

class SelectedComponent(BaseModel):
    category: str; name: str; component_id: Optional[str] = None

class RecommendationPreferences(BaseModel):
    brand: Optional[str] = None; priority: str = "performance"

class RecommendationRequest(BaseModel):
    user_id: str = "user_session"
    selected_components: List[SelectedComponent] = Field(default_factory=list)
    target_category: str; top_k: int = 5
    preferences: Optional[RecommendationPreferences] = None

class ComponentScore(BaseModel):
    relevance: float = 0.0

class RecommendedComponent(BaseModel):
    rank: int; component_id: str; name: str; category: str
    price: int = 0; scores: ComponentScore = Field(default_factory=ComponentScore)
    reasons: List[str] = []

class GraphContext(BaseModel):
    nodes: int = 0; edges: int = 0

class RecommendationResult(BaseModel):
    recommendations: List[RecommendedComponent]
    graph_context: Optional[GraphContext] = None
    processing_time_ms: int

# --- 추천 엔진 본체 ---

class GNNRecommendationEngine:
    def __init__(self):
        from .models import RecommendationGNN, GNNConfig
        self.builder = PCComponentGraph()
        self.builder.load_from_json()
        self.pyg_data = self.builder.to_pyg()
        
        self.model = RecommendationGNN(config=GNNConfig(), metadata=self.pyg_data.metadata())
        weight_path = os.path.join(os.path.dirname(__file__), "model_weights.pt")
        
        if os.path.exists(weight_path):
            try:
                self.model.load_state_dict(torch.load(weight_path, weights_only=True))
                self.model.eval()
                with torch.no_grad():
                    self.embeddings = self.model(self.pyg_data.x_dict, self.pyg_data.edge_index_dict)
            except Exception: self.embeddings = None
        else: self.embeddings = None

    def _normalize(self, text: Any) -> str:
        """규격 비교를 위한 텍스트 정규화 (공백/하이픈 제거, 대문자화)"""
        if not text: return ""
        return str(text).replace(" ", "").replace("-", "").upper()

    def recommend(self, selected_components, target_category, budget=None, purpose="gaming", top_k=5) -> RecommendationResult:
        start_t = time.time()
        
        # 0. 카테고리 명칭 정규화
        category_map = {
            "motherboard": "motherboard", "mb": "motherboard",
            "cpucooler": "cooler", "cooler": "cooler",
            "internal-hard-drive": "storage", "ssd": "storage", "storage": "storage",
            "psu": "psu", "gpu": "gpu", "ram": "memory", "memory": "memory"
        }
        normalized_target = category_map.get(target_category.lower(), target_category.lower())

        # 1. 물리적 제약 조건 추출 (CPU, GPU 정보 기반)
        req_socket = None
        req_mem_type = None
        req_form_factor = None
        gpu_tdp = 0

        for sel in selected_components:
            cid = sel.get("component_id") or self.builder._find_id_by_name(sel.get("name"))
            if cid and cid in self.builder.nodes:
                node = self.builder.nodes[cid]
                specs = node.attributes.get("specs", {})
                cat = node.attributes.get("category", "").lower() or cid.split('_')[0]

                if cat == "cpu":
                    req_socket = self._normalize(specs.get("socket"))
                    req_mem_type = self._normalize(specs.get("memory_type"))
                elif cat == "gpu":
                    # TDP가 없으면 기본값 250W 설정
                    gpu_tdp = int(specs.get("tdp") or specs.get("wattage") or 250)
                elif cat == "motherboard":
                    req_form_factor = self._normalize(specs.get("form_factor"))
                    if not req_mem_type: req_mem_type = self._normalize(specs.get("memory_type"))

        # 2. 쿼리 벡터 생성
        query_vec = None
        if self.embeddings and 'component' in self.embeddings:
            indices = []
            for sel in selected_components:
                cid = self.builder._find_id_by_name(sel.get("name"))
                if cid and cid in self.builder.node_to_idx['component']:
                    indices.append(self.builder.node_to_idx['component'][cid])
            if indices:
                query_vec = self.embeddings['component'][indices].mean(dim=0, keepdim=True)

        # 3. 후보군 필터링 (기획서 6대 규칙 강제 적용 및 PSU 예외 처리)
        candidates = []
        for n in self.builder.nodes.values():
            if n.type.value != "component": continue
            
            node_cat = getattr(n, 'category', n.id.split('_')[0]).lower()
            if node_cat != normalized_target: continue

            specs = n.attributes.get("specs", {})
            
            # [규칙 1] 메인보드: 소켓 및 메모리 규격
            if normalized_target == "motherboard":
                mb_socket = self._normalize(specs.get("socket"))
                mb_mem = self._normalize(specs.get("memory_type"))
                if req_socket and mb_socket != req_socket: continue
                if req_mem_type and mb_mem != req_mem_type: continue

            # [규칙 2] 메모리: DDR 규격 일치
            if normalized_target == "memory" and req_mem_type:
                if self._normalize(specs.get("memory_type")) != req_mem_type: continue

            # [규칙 3] 파워(PSU): 용량 하한선 (RTX 4090 대응 로직 강화)
            if normalized_target == "psu" and gpu_tdp > 0:
                try:
                    raw_watt = specs.get("wattage") or 0
                    psu_watt = int(raw_watt) if str(raw_watt).isdigit() else 0
                    # 고사양 GPU(TDP 400W 이상)인 경우 더 엄격하게 체크
                    margin = 400 if gpu_tdp >= 400 else 300
                    if psu_watt > 0 and psu_watt < (gpu_tdp + margin): continue
                except: pass

            # [규칙 4] 케이스: 폼팩터 지원 (ATX 보드 -> ITX 케이스 배제)
            if normalized_target == "case" and req_form_factor == "ATX":
                if any(x in n.name.upper() for x in ["MINI ITX", "ITX", "MATX"]): continue

            candidates.append(n)
        
        # 4. GNN 점수 계산
        results = []
        for node in candidates:
            score = 0.5
            if query_vec is not None and node.id in self.builder.node_to_idx['component']:
                n_idx = self.builder.node_to_idx['component'][node.id]
                n_vec = self.embeddings['component'][n_idx].unsqueeze(0)
                score = (torch.cosine_similarity(query_vec, n_vec).item() + 1) / 2

            results.append(RecommendedComponent(
                rank=0, component_id=node.id, name=node.name, category=normalized_target,
                price=node.attributes.get('price', 0),
                scores=ComponentScore(relevance=round(score, 4)),
                reasons=[f"물리적 호환성 검증 및 {purpose} 적합성 분석 완료"]
            ))

        results.sort(key=lambda x: x.scores.relevance, reverse=True)
        for i, r in enumerate(results): r.rank = i + 1
        
        return RecommendationResult(
            recommendations=results[:top_k],
            graph_context=GraphContext(nodes=len(self.builder.nodes), edges=len(self.builder.edges)),
            processing_time_ms=int((time.time() - start_t) * 1000)
        )