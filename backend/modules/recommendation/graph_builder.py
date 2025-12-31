"""
PC 부품 그래프 빌더
====================

[목표]
------
PC 부품 데이터를 그래프 구조로 변환하여 GNN 학습에 사용.

[그래프 구조]
-----------
노드 타입:
- component: 실제 PC 부품
- category: 부품 카테고리
- attribute: 부품 속성 (브랜드, 소켓 등)
- purpose: 사용 목적

엣지 타입:
- BELONGS_TO: component → category
- HAS_ATTR: component → attribute
- COMPATIBLE: component ↔ component
- SYNERGY: component ↔ component

[데이터 형식]
-----------
NetworkX 또는 PyTorch Geometric 호환 형식으로 출력

[TODO]
-----
- [ ] RAG DB에서 부품 데이터 로드
- [ ] 호환성 엣지 자동 생성
- [ ] 시너지 엣지 생성 (전문가 데이터 또는 학습)
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from loguru import logger

# TODO: NetworkX/PyTorch Geometric 설치 후 주석 해제
# import networkx as nx
# import torch
# from torch_geometric.data import HeteroData


# ============================================================================
# 열거형 및 상수
# ============================================================================

class NodeType(str, Enum):
    """노드 타입"""
    COMPONENT = "component"
    CATEGORY = "category"
    ATTRIBUTE = "attribute"
    PURPOSE = "purpose"


class EdgeType(str, Enum):
    """엣지 타입"""
    BELONGS_TO = "belongs_to"      # 부품 → 카테고리
    HAS_ATTR = "has_attr"          # 부품 → 속성
    COMPATIBLE = "compatible"      # 부품 ↔ 부품 (호환)
    SYNERGY = "synergy"            # 부품 ↔ 부품 (시너지)
    SUITABLE_FOR = "suitable_for"  # 부품 → 목적


# ============================================================================
# 데이터 클래스
# ============================================================================

@dataclass
class GraphNode:
    """그래프 노드"""
    id: str
    type: NodeType
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """그래프 엣지"""
    source: str
    target: str
    type: EdgeType
    weight: float = 1.0
    attributes: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 그래프 빌더
# ============================================================================

class PCComponentGraph:
    """
    PC 부품 그래프 빌더
    
    부품 데이터를 그래프 구조로 변환하고 관리.
    
    사용법:
    ```python
    graph = PCComponentGraph()
    
    # 부품 데이터 로드
    graph.load_components_from_db(db_connection)
    
    # 호환성 엣지 생성
    graph.build_compatibility_edges()
    
    # PyTorch Geometric 형식으로 내보내기
    pyg_data = graph.to_pyg()
    ```
    """
    
    # 카테고리 목록
    CATEGORIES = [
        "cpu", "gpu", "motherboard", "memory",
        "storage", "psu", "case", "cpu_cooler"
    ]
    
    # 목적 목록
    PURPOSES = [
        "gaming", "work", "development",
        "streaming", "video_editing", "3d_rendering"
    ]
    
    # 소켓 호환성 매핑
    SOCKET_COMPATIBILITY = {
        "LGA1700": ["Intel 12th", "Intel 13th", "Intel 14th"],
        "LGA1200": ["Intel 10th", "Intel 11th"],
        "AM5": ["AMD Ryzen 7000"],
        "AM4": ["AMD Ryzen 3000", "AMD Ryzen 5000"],
    }
    
    def __init__(self):
        """그래프 초기화"""
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        
        # 기본 노드 생성 (카테고리, 목적)
        self._init_base_nodes()
        
        logger.info("PCComponentGraph 초기화 완료")
    
    def _init_base_nodes(self):
        """기본 노드 초기화 (카테고리, 목적)"""
        # 카테고리 노드
        for cat in self.CATEGORIES:
            self.add_node(GraphNode(
                id=f"cat_{cat}",
                type=NodeType.CATEGORY,
                name=cat,
            ))
        
        # 목적 노드
        for purpose in self.PURPOSES:
            self.add_node(GraphNode(
                id=f"purpose_{purpose}",
                type=NodeType.PURPOSE,
                name=purpose,
            ))
    
    def add_node(self, node: GraphNode):
        """노드 추가"""
        self.nodes[node.id] = node
    
    def add_edge(self, edge: GraphEdge):
        """엣지 추가"""
        self.edges.append(edge)
    
    def add_component(
        self,
        component_id: str,
        name: str,
        category: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        부품 노드 추가
        
        Args:
            component_id: 부품 ID
            name: 부품 이름
            category: 카테고리
            attributes: 추가 속성
        """
        # 부품 노드 추가
        node = GraphNode(
            id=component_id,
            type=NodeType.COMPONENT,
            name=name,
            attributes=attributes or {},
        )
        self.add_node(node)
        
        # 카테고리 엣지 추가
        self.add_edge(GraphEdge(
            source=component_id,
            target=f"cat_{category}",
            type=EdgeType.BELONGS_TO,
        ))
        
        # 속성 노드 및 엣지 추가
        if attributes:
            for attr_name, attr_value in attributes.items():
                if attr_value and attr_name in ["brand", "socket", "generation"]:
                    attr_id = f"attr_{attr_name}_{attr_value}".lower().replace(" ", "_")
                    
                    # 속성 노드가 없으면 생성
                    if attr_id not in self.nodes:
                        self.add_node(GraphNode(
                            id=attr_id,
                            type=NodeType.ATTRIBUTE,
                            name=f"{attr_name}: {attr_value}",
                        ))
                    
                    # 속성 엣지 추가
                    self.add_edge(GraphEdge(
                        source=component_id,
                        target=attr_id,
                        type=EdgeType.HAS_ATTR,
                    ))
    
    def add_compatibility_edge(
        self,
        component1_id: str,
        component2_id: str,
        weight: float = 1.0,
        notes: Optional[str] = None,
    ):
        """호환성 엣지 추가"""
        self.add_edge(GraphEdge(
            source=component1_id,
            target=component2_id,
            type=EdgeType.COMPATIBLE,
            weight=weight,
            attributes={"notes": notes} if notes else {},
        ))
    
    def add_synergy_edge(
        self,
        component1_id: str,
        component2_id: str,
        weight: float = 1.0,
        reason: Optional[str] = None,
    ):
        """시너지 엣지 추가"""
        self.add_edge(GraphEdge(
            source=component1_id,
            target=component2_id,
            type=EdgeType.SYNERGY,
            weight=weight,
            attributes={"reason": reason} if reason else {},
        ))
    
    def load_components_from_dict(
        self,
        components: List[Dict[str, Any]],
    ):
        """
        딕셔너리 리스트에서 부품 로드
        
        Args:
            components: 부품 데이터 리스트
        """
        for comp in components:
            self.add_component(
                component_id=comp.get("id", f"comp_{len(self.nodes)}"),
                name=comp.get("name", "Unknown"),
                category=comp.get("category", "unknown"),
                attributes={
                    k: v for k, v in comp.items()
                    if k not in ["id", "name", "category"]
                },
            )
        
        logger.info(f"{len(components)}개 부품 로드 완료")
    
    def build_compatibility_edges(self):
        """
        호환성 엣지 자동 생성
        
        소켓, 폼팩터 등을 기반으로 호환성 엣지 생성.
        """
        component_nodes = [
            n for n in self.nodes.values()
            if n.type == NodeType.COMPONENT
        ]
        
        edges_added = 0
        
        for i, node1 in enumerate(component_nodes):
            for node2 in component_nodes[i+1:]:
                if self._check_compatibility(node1, node2):
                    self.add_compatibility_edge(node1.id, node2.id)
                    edges_added += 1
        
        logger.info(f"{edges_added}개 호환성 엣지 생성")
    
    def _check_compatibility(
        self,
        node1: GraphNode,
        node2: GraphNode,
    ) -> bool:
        """
        두 부품 간 호환성 확인
        
        TODO: 상세 호환성 로직 구현
        """
        # 같은 카테고리는 호환 불가
        cat1 = node1.attributes.get("category")
        cat2 = node2.attributes.get("category")
        
        if cat1 == cat2:
            return False
        
        # CPU-메인보드 소켓 호환성
        socket1 = node1.attributes.get("socket")
        socket2 = node2.attributes.get("socket")
        
        if socket1 and socket2:
            if socket1 != socket2:
                return False
        
        # 기본적으로 호환 가능으로 처리
        return True
    
    def get_neighbors(
        self,
        node_id: str,
        edge_type: Optional[EdgeType] = None,
    ) -> List[str]:
        """
        이웃 노드 조회
        
        Args:
            node_id: 노드 ID
            edge_type: 특정 엣지 타입으로 필터
            
        Returns:
            이웃 노드 ID 리스트
        """
        neighbors = []
        
        for edge in self.edges:
            if edge_type and edge.type != edge_type:
                continue
            
            if edge.source == node_id:
                neighbors.append(edge.target)
            elif edge.target == node_id:
                neighbors.append(edge.source)
        
        return list(set(neighbors))
    
    def get_stats(self) -> Dict[str, Any]:
        """그래프 통계"""
        node_counts = {}
        for node in self.nodes.values():
            node_type = node.type.value
            node_counts[node_type] = node_counts.get(node_type, 0) + 1
        
        edge_counts = {}
        for edge in self.edges:
            edge_type = edge.type.value
            edge_counts[edge_type] = edge_counts.get(edge_type, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_counts": node_counts,
            "edge_counts": edge_counts,
        }
    
    def to_networkx(self):
        """
        NetworkX 그래프로 변환
        
        TODO: NetworkX 설치 후 구현
        """
        # import networkx as nx
        # G = nx.DiGraph()
        # for node in self.nodes.values():
        #     G.add_node(node.id, **node.attributes)
        # for edge in self.edges:
        #     G.add_edge(edge.source, edge.target, weight=edge.weight)
        # return G
        logger.warning("NetworkX 변환은 아직 구현되지 않았습니다.")
        return None
    
    def to_pyg(self):
        """
        PyTorch Geometric HeteroData로 변환
        
        TODO: PyTorch Geometric 설치 후 구현
        """
        # from torch_geometric.data import HeteroData
        # data = HeteroData()
        # ...
        logger.warning("PyTorch Geometric 변환은 아직 구현되지 않았습니다.")
        return None
    
    def save(self, path: str):
        """그래프 저장"""
        data = {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "name": n.name,
                    "attributes": n.attributes,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "type": e.type.value,
                    "weight": e.weight,
                    "attributes": e.attributes,
                }
                for e in self.edges
            ],
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"그래프 저장: {path}")
    
    def load(self, path: str):
        """그래프 로드"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.nodes = {}
        self.edges = []
        
        for node_data in data["nodes"]:
            self.nodes[node_data["id"]] = GraphNode(
                id=node_data["id"],
                type=NodeType(node_data["type"]),
                name=node_data["name"],
                attributes=node_data.get("attributes", {}),
            )
        
        for edge_data in data["edges"]:
            self.edges.append(GraphEdge(
                source=edge_data["source"],
                target=edge_data["target"],
                type=EdgeType(edge_data["type"]),
                weight=edge_data.get("weight", 1.0),
                attributes=edge_data.get("attributes", {}),
            ))
        
        logger.info(f"그래프 로드: {path}, {len(self.nodes)} 노드, {len(self.edges)} 엣지")


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    graph = PCComponentGraph()
    
    # 테스트 부품 추가
    test_components = [
        {"id": "cpu_i5_14600k", "name": "Intel Core i5-14600K", "category": "cpu", "socket": "LGA1700", "brand": "Intel"},
        {"id": "cpu_r7_7800x3d", "name": "AMD Ryzen 7 7800X3D", "category": "cpu", "socket": "AM5", "brand": "AMD"},
        {"id": "mb_asus_z790", "name": "ASUS ROG Strix Z790-A", "category": "motherboard", "socket": "LGA1700", "brand": "ASUS"},
        {"id": "mb_msi_b650", "name": "MSI MAG B650 TOMAHAWK", "category": "motherboard", "socket": "AM5", "brand": "MSI"},
        {"id": "gpu_rtx4070", "name": "RTX 4070", "category": "gpu", "brand": "NVIDIA"},
    ]
    
    graph.load_components_from_dict(test_components)
    graph.build_compatibility_edges()
    
    print("그래프 통계:")
    print(json.dumps(graph.get_stats(), indent=2))
    
    print(f"\ni5-14600K의 호환 이웃:")
    neighbors = graph.get_neighbors("cpu_i5_14600k", EdgeType.COMPATIBLE)
    for n in neighbors:
        print(f"  - {graph.nodes[n].name}")
