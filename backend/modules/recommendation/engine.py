"""
GNN 기반 초개인화 추천 엔진
============================

[목표]
------
그래프 신경망(GNN)을 활용하여 사용자의 선택/선호에 따라
동적으로 변화하는 개인화된 PC 부품 추천 시스템.

[배경 지식]
----------
기존 추천 시스템의 한계:
1. 협업 필터링: 신규 사용자/부품에 대한 Cold Start 문제
2. 컨텐츠 기반: 부품 간 복잡한 관계 표현 어려움
3. 단순 규칙 기반: 개인화 부족

GNN 기반 추천의 장점:
1. 부품 간 호환성/시너지를 그래프 엣지로 표현
2. 사용자 선호를 노드 임베딩으로 학습
3. 메시지 패싱으로 연관 부품 정보 전파
4. 선택에 따른 동적 추천 업데이트

그래프 구조:
```
사용자(User)
    │
    │ 선호 (PREFERS)
    ▼
┌─────────┐     호환     ┌─────────┐
│  CPU    │────────────→│ 메인보드 │
└────┬────┘             └────┬────┘
     │                       │
     │ 지원                  │ 지원
     ▼                       ▼
┌─────────┐             ┌─────────┐
│ 쿨러    │             │ 메모리  │
└─────────┘             └─────────┘
```

[아키텍처]
---------
```
                 ┌────────────────────────────────────────────┐
                 │         GNNRecommendationEngine            │
                 │                                            │
사용자 선택 ────▶│  ┌─────────────────────────────────────┐  │
                 │  │         PCComponentGraph             │  │
                 │  │  (부품/속성/사용자 관계 그래프)      │  │
                 │  └───────────────┬─────────────────────┘  │
                 │                  │                         │
                 │                  ▼                         │
                 │  ┌─────────────────────────────────────┐  │
                 │  │         RecommendationGNN           │  │
                 │  │  (GraphSAGE / GAT 기반 임베딩)      │  │
                 │  └───────────────┬─────────────────────┘  │
                 │                  │                         │
                 │                  ▼                         │
                 │  ┌─────────────────────────────────────┐  │
                 │  │         Ranking & Filtering          │  │
                 │  │  - 호환성 필터링                     │  │
                 │  │  - 예산 필터링                       │  │
                 │  │  - 다양성 보장                       │  │
                 │  └─────────────────────────────────────┘  │
                 └────────────────────┬───────────────────────┘
                                      │
                                      ▼
                            개인화 추천 결과

```

[그래프 노드 타입]
----------------
1. Component (부품): CPU, GPU, 메모리 등 실제 부품
2. Category (카테고리): cpu, gpu, memory 등 부품 분류
3. Attribute (속성): 브랜드, 소켓, 세대 등
4. User (사용자): 추천 대상 사용자
5. Purpose (목적): gaming, work, development 등

[그래프 엣지 타입]
----------------
1. BELONGS_TO: 부품 → 카테고리
2. HAS_ATTRIBUTE: 부품 → 속성
3. COMPATIBLE_WITH: 부품 ↔ 부품 (호환성)
4. SYNERGY_WITH: 부품 ↔ 부품 (시너지)
5. SELECTED: 사용자 → 부품 (선택함)
6. SUITABLE_FOR: 부품 → 목적

[입력/출력 인터페이스]
-------------------
입력 (RecommendationRequest):
```python
{
    "user_id": "user_123",  # 또는 세션 ID
    "selected_components": [
        {"category": "cpu", "name": "Intel Core i5-14600K"},
        {"category": "gpu", "name": "RTX 4070"}
    ],
    "target_category": "motherboard",  # 추천 받을 카테고리
    "budget": 300000,
    "purpose": "gaming",
    "preferences": {
        "brand": "ASUS",
        "priority": "quality"  # quality, value, performance
    },
    "top_k": 5
}
```

출력 (RecommendationResult):
```python
{
    "recommendations": [
        {
            "rank": 1,
            "component": {
                "id": "mb_asus_rog_z790",
                "name": "ASUS ROG Strix Z790-A Gaming WiFi",
                "category": "motherboard",
                "price": 290000
            },
            "scores": {
                "relevance": 0.92,      # 사용자 선호 적합도
                "compatibility": 1.0,   # 호환성 (필수)
                "synergy": 0.85,        # 선택 부품과의 시너지
                "value": 0.78           # 가성비
            },
            "reasons": [
                "선택한 i5-14600K와 완벽 호환 (LGA1700)",
                "ASUS ROG 라인업으로 브랜드 선호 일치",
                "게이밍에 최적화된 WiFi 6E 및 2.5G LAN"
            ]
        },
        ...
    ],
    "graph_context": {
        "connected_components": 15,
        "compatibility_edges": 8,
        "synergy_score_avg": 0.75
    }
}
```

[구현 단계]
----------
1단계: 그래프 데이터 구조 설계 및 구축
2단계: 그래프 빌더 구현 (부품 DB → 그래프)
3단계: GNN 모델 구현 (GraphSAGE/GAT)
4단계: 추천 로직 구현 (필터링, 랭킹)
5단계: 실시간 업데이트 (선택에 따른 그래프 수정)
6단계: 학습 파이프라인 구현

[참고 기술/라이브러리]
------------------
- PyTorch Geometric (PyG): GNN 프레임워크
  https://pytorch-geometric.readthedocs.io/
- DGL (Deep Graph Library): 또 다른 GNN 프레임워크
  https://www.dgl.ai/
- NetworkX: 그래프 분석 (시각화/전처리용)

[GNN 모델 후보]
--------------
1. GraphSAGE: 귀납적 학습, 새 노드에 일반화 용이
2. GAT (Graph Attention): 이웃 노드 중요도 학습
3. GCN: 기본 GNN, 간단하지만 효과적
4. HeteroGNN: 이종 그래프용 (부품/속성/사용자 구분)

[학습 데이터]
-----------
- 부품 정보: 기존 RAG DB 활용
- 호환성 정보: 제조사 스펙 기반
- 사용자 선택 로그: 세션 데이터 수집 필요
- 전문가 추천: 초기 학습용 레이블

[테스트]
-------
backend/tests/test_recommendation.py 참조
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from pydantic import BaseModel, Field


# ============================================================================
# 열거형 및 상수
# ============================================================================

class RecommendationPriority(str, Enum):
    """추천 우선순위"""
    QUALITY = "quality"       # 품질/신뢰성 우선
    VALUE = "value"           # 가성비 우선
    PERFORMANCE = "performance"  # 성능 우선


# ============================================================================
# 데이터 모델
# ============================================================================

class SelectedComponent(BaseModel):
    """선택된 부품"""
    category: str
    name: str
    component_id: Optional[str] = None


class RecommendationPreferences(BaseModel):
    """추천 선호 설정"""
    brand: Optional[str] = None
    priority: RecommendationPriority = RecommendationPriority.VALUE
    exclude_brands: List[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    """추천 요청"""
    user_id: Optional[str] = None
    selected_components: List[SelectedComponent] = Field(default_factory=list)
    target_category: str
    budget: Optional[int] = None
    purpose: Optional[str] = None
    preferences: Optional[RecommendationPreferences] = None
    top_k: int = Field(5, ge=1, le=20)


class ComponentScore(BaseModel):
    """부품 점수"""
    relevance: float = Field(..., ge=0, le=1, description="사용자 선호 적합도")
    compatibility: float = Field(..., ge=0, le=1, description="호환성")
    synergy: float = Field(..., ge=0, le=1, description="시너지")
    value: float = Field(..., ge=0, le=1, description="가성비")


class RecommendedComponent(BaseModel):
    """추천 부품"""
    rank: int
    component_id: str
    name: str
    category: str
    price: Optional[int] = None
    scores: ComponentScore
    reasons: List[str]


class GraphContext(BaseModel):
    """그래프 컨텍스트 정보"""
    connected_components: int
    compatibility_edges: int
    synergy_score_avg: float


class RecommendationResult(BaseModel):
    """추천 결과"""
    recommendations: List[RecommendedComponent]
    graph_context: Optional[GraphContext] = None
    processing_time_ms: Optional[int] = None


# ============================================================================
# 추천 엔진
# ============================================================================

class GNNRecommendationEngine:
    """
    GNN 기반 PC 부품 추천 엔진
    
    그래프 신경망을 활용하여 사용자의 선택에 따라
    동적으로 변화하는 개인화 추천을 제공.
    
    사용법:
    ```python
    engine = GNNRecommendationEngine()
    
    # 추천 요청
    result = engine.recommend(
        selected_components=[
            {"category": "cpu", "name": "Intel Core i5-14600K"}
        ],
        target_category="motherboard",
        budget=300000,
        purpose="gaming"
    )
    
    for rec in result.recommendations:
        print(f"{rec.rank}. {rec.name} - {rec.scores.relevance:.2f}")
    ```
    """
    
    def __init__(
        self,
        graph_path: Optional[str] = None,
        model_path: Optional[str] = None,
        use_pretrained: bool = False,
    ):
        """
        Args:
            graph_path: 그래프 데이터 경로
            model_path: 학습된 GNN 모델 경로
            use_pretrained: 사전 학습 모델 사용 여부
        """
        self.graph_path = graph_path
        self.model_path = model_path
        
        # 그래프 및 모델 초기화
        self.graph = None  # PCComponentGraph 인스턴스
        self.model = None  # RecommendationGNN 인스턴스
        
        if use_pretrained and model_path:
            self._load_model(model_path)
        
        # 카테고리별 호환성 규칙 (규칙 기반 폴백용)
        self._compatibility_rules = self._init_compatibility_rules()
        
        logger.info("GNNRecommendationEngine 초기화 완료")
    
    def _init_compatibility_rules(self) -> Dict[str, List[str]]:
        """호환성 규칙 초기화"""
        return {
            "cpu": ["motherboard", "cpu_cooler"],
            "motherboard": ["cpu", "memory", "storage", "gpu", "case"],
            "memory": ["motherboard"],
            "gpu": ["motherboard", "psu", "case"],
            "storage": ["motherboard", "case"],
            "psu": ["gpu", "case"],
            "case": ["motherboard", "gpu", "cpu_cooler"],
            "cpu_cooler": ["cpu", "case"],
        }
    
    def recommend(
        self,
        selected_components: List[Dict[str, str]],
        target_category: str,
        budget: Optional[int] = None,
        purpose: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> RecommendationResult:
        """
        부품 추천 생성
        
        Args:
            selected_components: 이미 선택한 부품들
            target_category: 추천 받을 카테고리
            budget: 예산 제한
            purpose: 사용 목적
            preferences: 추가 선호 설정
            top_k: 추천 개수
            
        Returns:
            RecommendationResult: 추천 결과
        """
        import time
        start_time = time.time()
        
        logger.info(f"추천 요청: target={target_category}, selected={len(selected_components)}")
        
        # 1. 후보 부품 조회
        candidates = self._get_candidates(target_category, budget)
        
        # 2. 호환성 필터링
        compatible_candidates = self._filter_by_compatibility(
            candidates, selected_components, target_category
        )
        
        # 3. 점수 계산
        scored_candidates = self._score_candidates(
            compatible_candidates,
            selected_components,
            purpose,
            preferences,
        )
        
        # 4. 랭킹 및 상위 K개 선택
        recommendations = self._rank_and_select(scored_candidates, top_k)
        
        # 5. 추천 이유 생성
        recommendations = self._generate_reasons(
            recommendations, selected_components, purpose
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return RecommendationResult(
            recommendations=recommendations,
            graph_context=GraphContext(
                connected_components=len(candidates),
                compatibility_edges=len(compatible_candidates),
                synergy_score_avg=0.75,  # Placeholder
            ),
            processing_time_ms=processing_time,
        )
    
    def _get_candidates(
        self,
        category: str,
        budget: Optional[int],
    ) -> List[Dict[str, Any]]:
        """
        후보 부품 조회
        
        TODO: RAG 또는 DB에서 실제 부품 데이터 로드
        """
        # Placeholder: 테스트용 더미 데이터
        dummy_candidates = {
            "motherboard": [
                {"id": "mb_asus_z790_a", "name": "ASUS ROG Strix Z790-A Gaming WiFi", "price": 290000, "socket": "LGA1700", "brand": "ASUS"},
                {"id": "mb_msi_z790", "name": "MSI MAG Z790 TOMAHAWK WIFI", "price": 280000, "socket": "LGA1700", "brand": "MSI"},
                {"id": "mb_gigabyte_z790", "name": "GIGABYTE Z790 AORUS ELITE AX", "price": 260000, "socket": "LGA1700", "brand": "GIGABYTE"},
                {"id": "mb_asus_b760", "name": "ASUS TUF Gaming B760M-PLUS WIFI", "price": 180000, "socket": "LGA1700", "brand": "ASUS"},
            ],
            "memory": [
                {"id": "mem_samsung_32gb", "name": "Samsung DDR5-5600 32GB (16x2)", "price": 150000, "capacity": 32, "speed": 5600},
                {"id": "mem_gskill_32gb", "name": "G.SKILL Trident Z5 DDR5-6000 32GB", "price": 180000, "capacity": 32, "speed": 6000},
                {"id": "mem_corsair_32gb", "name": "Corsair Vengeance DDR5-5600 32GB", "price": 145000, "capacity": 32, "speed": 5600},
            ],
            "storage": [
                {"id": "ssd_samsung_990pro", "name": "Samsung 990 PRO 1TB", "price": 150000, "capacity": 1000, "type": "NVMe"},
                {"id": "ssd_wd_sn850x", "name": "WD Black SN850X 1TB", "price": 140000, "capacity": 1000, "type": "NVMe"},
                {"id": "ssd_sk_p41", "name": "SK hynix Platinum P41 1TB", "price": 130000, "capacity": 1000, "type": "NVMe"},
            ],
            "gpu": [
                {"id": "gpu_rtx4070_super", "name": "RTX 4070 SUPER", "price": 750000, "vram": 12, "brand": "NVIDIA"},
                {"id": "gpu_rtx4070", "name": "RTX 4070", "price": 650000, "vram": 12, "brand": "NVIDIA"},
                {"id": "gpu_rtx4060ti", "name": "RTX 4060 Ti", "price": 500000, "vram": 8, "brand": "NVIDIA"},
            ],
            "cpu": [
                {"id": "cpu_i5_14600k", "name": "Intel Core i5-14600K", "price": 380000, "cores": 14, "socket": "LGA1700"},
                {"id": "cpu_i7_14700k", "name": "Intel Core i7-14700K", "price": 520000, "cores": 20, "socket": "LGA1700"},
                {"id": "cpu_r7_7800x3d", "name": "AMD Ryzen 7 7800X3D", "price": 450000, "cores": 8, "socket": "AM5"},
            ],
        }
        
        candidates = dummy_candidates.get(category, [])
        
        # 예산 필터링
        if budget:
            candidates = [c for c in candidates if c["price"] <= budget]
        
        return candidates
    
    def _filter_by_compatibility(
        self,
        candidates: List[Dict[str, Any]],
        selected: List[Dict[str, str]],
        target_category: str,
    ) -> List[Dict[str, Any]]:
        """
        호환성 기반 필터링
        
        TODO: 실제 호환성 검사 로직 구현
        """
        if not selected:
            return candidates
        
        # 간단한 호환성 검사 (예: CPU 소켓 - 메인보드)
        compatible = []
        
        for candidate in candidates:
            is_compatible = True
            
            # 메인보드-CPU 소켓 호환성
            if target_category == "motherboard":
                for sel in selected:
                    if sel.get("category") == "cpu":
                        # Intel 14세대는 LGA1700 소켓
                        if "14600" in sel.get("name", "") or "14700" in sel.get("name", ""):
                            if candidate.get("socket") != "LGA1700":
                                is_compatible = False
                        # AMD 7000 시리즈는 AM5 소켓
                        elif "7800" in sel.get("name", "") or "7900" in sel.get("name", ""):
                            if candidate.get("socket") != "AM5":
                                is_compatible = False
            
            if is_compatible:
                compatible.append(candidate)
        
        return compatible
    
    def _score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        selected: List[Dict[str, str]],
        purpose: Optional[str],
        preferences: Optional[Dict[str, Any]],
    ) -> List[Tuple[Dict[str, Any], ComponentScore]]:
        """
        후보 부품 점수 계산
        
        TODO: GNN 임베딩 기반 점수 계산으로 대체
        """
        scored = []
        
        for candidate in candidates:
            # 기본 점수 (placeholder)
            relevance = 0.7
            compatibility = 1.0  # 이미 필터링됨
            synergy = 0.7
            value = 0.7
            
            # 브랜드 선호 반영
            if preferences:
                pref_brand = preferences.get("brand")
                if pref_brand and candidate.get("brand") == pref_brand:
                    relevance += 0.2
                
                priority = preferences.get("priority", "value")
                if priority == "performance":
                    # 더 비싼 제품 선호
                    if candidate.get("price", 0) > 200000:
                        relevance += 0.1
                elif priority == "value":
                    # 가성비 제품 선호
                    value = min(1.0, value + 0.2)
            
            # 목적 기반 조정
            if purpose == "gaming":
                if "gaming" in candidate.get("name", "").lower():
                    relevance += 0.1
                if "rog" in candidate.get("name", "").lower():
                    synergy += 0.1
            
            score = ComponentScore(
                relevance=min(1.0, relevance),
                compatibility=compatibility,
                synergy=min(1.0, synergy),
                value=min(1.0, value),
            )
            
            scored.append((candidate, score))
        
        return scored
    
    def _rank_and_select(
        self,
        scored_candidates: List[Tuple[Dict[str, Any], ComponentScore]],
        top_k: int,
    ) -> List[RecommendedComponent]:
        """랭킹 및 상위 K개 선택"""
        # 종합 점수 계산 (가중 평균)
        def total_score(scores: ComponentScore) -> float:
            return (
                scores.relevance * 0.3 +
                scores.compatibility * 0.3 +
                scores.synergy * 0.2 +
                scores.value * 0.2
            )
        
        # 정렬
        sorted_candidates = sorted(
            scored_candidates,
            key=lambda x: total_score(x[1]),
            reverse=True
        )
        
        # 상위 K개 선택
        recommendations = []
        for rank, (candidate, scores) in enumerate(sorted_candidates[:top_k], 1):
            recommendations.append(RecommendedComponent(
                rank=rank,
                component_id=candidate["id"],
                name=candidate["name"],
                category=candidate.get("category", "unknown"),
                price=candidate.get("price"),
                scores=scores,
                reasons=[],  # 나중에 채움
            ))
        
        return recommendations
    
    def _generate_reasons(
        self,
        recommendations: List[RecommendedComponent],
        selected: List[Dict[str, str]],
        purpose: Optional[str],
    ) -> List[RecommendedComponent]:
        """추천 이유 생성"""
        for rec in recommendations:
            reasons = []
            
            # 호환성 이유
            if rec.scores.compatibility == 1.0:
                for sel in selected:
                    reasons.append(f"선택한 {sel.get('name', '')}와 완벽 호환")
                    break
            
            # 목적 적합성 이유
            if purpose and rec.scores.relevance > 0.8:
                reasons.append(f"{purpose}에 최적화된 제품")
            
            # 가성비 이유
            if rec.scores.value > 0.8:
                reasons.append("가격 대비 우수한 성능")
            
            # 시너지 이유
            if rec.scores.synergy > 0.8:
                reasons.append("선택한 부품들과 높은 시너지")
            
            rec.reasons = reasons[:3]  # 최대 3개
        
        return recommendations
    
    def update_graph_with_selection(
        self,
        user_id: str,
        component: Dict[str, str],
    ):
        """
        사용자 선택 시 그래프 업데이트
        
        TODO: 실시간 그래프 업데이트 구현
        """
        logger.info(f"그래프 업데이트: user={user_id}, component={component.get('name')}")
        # 사용자-부품 SELECTED 엣지 추가
        pass
    
    def train(
        self,
        training_data: List[Dict[str, Any]],
        epochs: int = 100,
    ):
        """
        GNN 모델 학습
        
        TODO: PyTorch Geometric 기반 학습 구현
        """
        logger.info(f"GNN 모델 학습 시작: {len(training_data)}개 데이터, {epochs} epochs")
        # self.model.train(...)
        pass
    
    def _load_model(self, path: str):
        """학습된 모델 로드"""
        logger.info(f"모델 로드: {path}")
        # self.model = RecommendationGNN.load(path)
        pass


# ============================================================================
# 간편 함수
# ============================================================================

def get_recommendations(
    selected_components: List[Dict[str, str]],
    target_category: str,
    budget: Optional[int] = None,
    top_k: int = 5,
) -> RecommendationResult:
    """
    간편 추천 함수
    
    Args:
        selected_components: 선택한 부품들
        target_category: 추천 받을 카테고리
        budget: 예산 제한
        top_k: 추천 개수
        
    Returns:
        RecommendationResult: 추천 결과
    """
    engine = GNNRecommendationEngine()
    return engine.recommend(
        selected_components=selected_components,
        target_category=target_category,
        budget=budget,
        top_k=top_k,
    )


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    import json
    
    engine = GNNRecommendationEngine()
    
    # 테스트: CPU 선택 후 메인보드 추천
    result = engine.recommend(
        selected_components=[
            {"category": "cpu", "name": "Intel Core i5-14600K"}
        ],
        target_category="motherboard",
        budget=300000,
        purpose="gaming",
        preferences={"brand": "ASUS", "priority": "quality"},
    )
    
    print("추천 결과:")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
