import json
import torch
from pathlib import Path
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger
from collections import defaultdict

try:
    from torch_geometric.data import HeteroData
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

class NodeType(str, Enum):
    COMPONENT = "component"
    CATEGORY = "category"
    ATTRIBUTE = "attribute"
    PURPOSE = "purpose"
    USER = "user"

class EdgeType(str, Enum):
    BELONGS_TO = "belongs_to"
    HAS_ATTR = "has_attr"
    COMPATIBLE = "compatible"
    SYNERGY = "synergy"
    SUITABLE_FOR = "suitable_for"
    SELECTED = "selected"

@dataclass
class GraphNode:
    id: str; type: NodeType; name: str; attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphEdge:
    source: str; target: str; type: EdgeType; weight: float = 1.0; attributes: Dict[str, Any] = field(default_factory=dict)

class PCComponentGraph:
    def __init__(self, data_dir: str = "backend/data/recommendation"):
        self.data_dir = Path(data_dir)
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.name_to_id: Dict[str, str] = {}
        self.node_to_idx = defaultdict(dict)
        self.idx_to_node = defaultdict(dict)
        self._init_base_nodes()

    def _init_base_nodes(self):
        # [수정] 스토리지 노드를 포함하여 모든 기본 카테고리 생성
        cats = ["cpu", "gpu", "motherboard", "memory", "psu", "case", "cooler", "storage"]
        for c in cats: 
            self.nodes[f"cat_{c}"] = GraphNode(id=f"cat_{c}", type=NodeType.CATEGORY, name=c)

    def add_node(self, node: GraphNode): self.nodes[node.id] = node
    def add_edge(self, edge: GraphEdge): self.edges.append(edge)

    def add_component(self, component_id: str, name: str, category: str, attributes: Optional[Dict[str, Any]] = None):
        # 카테고리 속성을 명시적으로 저장 (engine.py 필터링용)
        attrs = attributes or {}
        attrs['category'] = category.lower()
        
        node = GraphNode(id=component_id, type=NodeType.COMPONENT, name=name, attributes=attrs)
        self.add_node(node)
        
        # 검색용 정규화 이름 캐싱
        clean_name = name.replace(" ", "").replace("-", "").lower()
        self.name_to_id[clean_name] = component_id
        
        cat_id = f"cat_{category.lower()}"
        if cat_id not in self.nodes: 
            self.add_node(GraphNode(cat_id, NodeType.CATEGORY, category.lower()))
        self.add_edge(GraphEdge(component_id, cat_id, EdgeType.BELONGS_TO))

    def _find_id_by_name(self, name: str) -> Optional[str]:
        if not name or name.lower() in ["internal", "none"]: return None
        search_term = name.replace(" ", "").replace("-", "").lower()
        if search_term in self.name_to_id: return self.name_to_id[search_term]
        for db_name, db_id in self.name_to_id.items():
            if search_term in db_name or db_name in search_term: return db_id
        return None

    def load_from_json(self):
        node_path = self.data_dir / "component_nodes.json"
        if not node_path.exists(): 
            logger.error(f"데이터 파일을 찾을 수 없습니다: {node_path}")
            return
            
        with open(node_path, "r", encoding="utf-8") as f:
            data = json.load(f).get("data", [])
            for n in data:
                # [강력 수정] 카테고리 판별 로직 고도화
                raw_cat = str(n.get('category', '')).lower()
                node_id = str(n['id']).lower()
                
                if "cpu" in raw_cat or node_id.startswith("cpu"): final_cat = "cpu"
                elif "gpu" in raw_cat or "video" in raw_cat or node_id.startswith("gpu"): final_cat = "gpu"
                elif "motherboard" in raw_cat or node_id.startswith("motherboard"): final_cat = "motherboard"
                elif "memory" in raw_cat or "ram" in raw_cat or node_id.startswith("memory"): final_cat = "memory"
                elif "psu" in raw_cat or "power" in raw_cat or node_id.startswith("psu"): final_cat = "psu"
                elif "cooler" in raw_cat or node_id.startswith("cooler"): final_cat = "cooler"
                elif "storage" in raw_cat or "drive" in raw_cat or node_id.startswith("storage"): final_cat = "storage"
                elif "case" in raw_cat or node_id.startswith("case"): final_cat = "case"
                else: final_cat = "unknown"

                self.add_component(n['id'], n['name'], final_cat, n.get('specs', {}))
        
        self._load_popular_builds()
        logger.info(f"그래프 구축 완료: 노드 {len(self.nodes)}개, 엣지 {len(self.edges)}개")

    def _load_popular_builds(self):
        path = self.data_dir / "popular_builds.json"
        if not path.exists(): return
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            builds = raw.get("data", raw) if isinstance(raw, dict) else raw
            for build in builds:
                # 시너지 대상 확장 (Cooler, Storage 포함)
                parts_keys = ['cpu', 'gpu', 'mb', 'ram', 'storage', 'cooler']
                parts = [build.get(k) for k in parts_keys if build.get(k)]
                p_ids = [self._find_id_by_name(p) for p in parts if self._find_id_by_name(p)]
                
                for i in range(len(p_ids)):
                    for j in range(i + 1, len(p_ids)):
                        self.add_edge(GraphEdge(p_ids[i], p_ids[j], EdgeType.SYNERGY, 1.4))

    def to_pyg(self) -> Optional["HeteroData"]:
        if not HAS_PYG or not self.nodes: return None
        data = HeteroData()
        type_cnt = defaultdict(int)
        
        for nid, node in self.nodes.items():
            nt = node.type.value
            if nid not in self.node_to_idx[nt]:
                idx = type_cnt[nt]
                self.node_to_idx[nt][nid] = idx
                self.idx_to_node[nt][idx] = nid
                type_cnt[nt] += 1
        
        for nt, c in type_cnt.items():
            data[nt].x = torch.randn(c, 128)
            data[nt].num_nodes = c
        
        edge_stores = defaultdict(lambda: {'src': [], 'dst': []})
        for edge in self.edges:
            if edge.source in self.nodes and edge.target in self.nodes:
                s, t = self.nodes[edge.source], self.nodes[edge.target]
                rel = (s.type.value, edge.type.value, t.type.value)
                edge_stores[rel]['src'].append(self.node_to_idx[s.type.value][edge.source])
                edge_stores[rel]['dst'].append(self.node_to_idx[t.type.value][edge.target])
        
        for rel, idxs in edge_stores.items():
            data[rel].edge_index = torch.tensor([idxs['src'], idxs['dst']], dtype=torch.long)
        
        return data