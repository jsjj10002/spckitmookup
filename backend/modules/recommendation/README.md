# Recommendation 모듈

> GNN 기반 초개인화 PC 부품 추천 시스템

## 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [파일 구조](#파일-구조)
- [그래프 구조](#그래프-구조)
- [데이터 모델](#데이터-모델)
- [사용법](#사용법)
- [구현 가이드](#구현-가이드)
- [테스트](#테스트)
- [참고 자료](#참고-자료)

---

## 개요

### 목표

그래프 신경망(GNN)을 활용하여 사용자의 선택/선호에 따라 **동적으로 변화하는 개인화된** PC 부품 추천 시스템 구현.

### 기존 추천 시스템의 한계

| 방식 | 한계 |
|------|------|
| **협업 필터링** | 신규 사용자/부품에 대한 Cold Start 문제 |
| **컨텐츠 기반** | 부품 간 복잡한 관계 표현 어려움 |
| **단순 규칙 기반** | 개인화 부족 |

### GNN 기반 추천의 장점

1. **관계 표현**: 부품 간 호환성/시너지를 그래프 엣지로 표현
2. **임베딩 학습**: 사용자 선호를 노드 임베딩으로 학습
3. **정보 전파**: 메시지 패싱으로 연관 부품 정보 전파
4. **동적 업데이트**: 선택에 따른 실시간 추천 업데이트

### 핵심 기술

- **PyTorch Geometric (PyG)**: GNN 프레임워크
- **GraphSAGE / GAT**: GNN 모델 아키텍처
- **Link Prediction**: 부품 간 추천 관계 예측

---

## 아키텍처

```
                 ┌────────────────────────────────────────────┐
                 │         GNNRecommendationEngine            │
                 │                                            │
사용자 선택 ────▶│  ┌─────────────────────────────────────┐  │
                 │  │         PCComponentGraph             │  │
                 │  │  (부품/속성/사용자 관계 그래프)      │  │
                 │  │  - 부품 노드 (Component)             │  │
                 │  │  - 카테고리 노드 (Category)          │  │
                 │  │  - 호환성/시너지 엣지                │  │
                 │  └───────────────┬─────────────────────┘  │
                 │                  │                         │
                 │                  ▼                         │
                 │  ┌─────────────────────────────────────┐  │
                 │  │         RecommendationGNN           │  │
                 │  │  (GraphSAGE / GAT 기반 임베딩)      │  │
                 │  │  - 노드 임베딩 학습                 │  │
                 │  │  - 링크 예측                        │  │
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

---

## 파일 구조

```
recommendation/
├── __init__.py          # 모듈 초기화 및 exports
├── engine.py            # 메인 추천 엔진 (GNNRecommendationEngine)
├── graph_builder.py     # PC 부품 그래프 빌더 (PCComponentGraph)
├── models.py            # GNN 모델 정의 (RecommendationGNN)
└── README.md            # 이 문서
```

### 파일별 역할

| 파일 | 역할 | 주요 클래스 |
|------|------|-------------|
| `engine.py` | 추천 파이프라인 및 결과 생성 | `GNNRecommendationEngine`, `RecommendationResult` |
| `graph_builder.py` | 부품 데이터를 그래프로 변환 | `PCComponentGraph`, `GraphNode`, `GraphEdge` |
| `models.py` | GNN 모델 정의 및 학습 | `RecommendationGNN`, `GNNConfig`, `GNNEvaluator` |

---

## 그래프 구조

### 노드 타입

```
Component (부품)
    │
    ├── cpu: Intel Core i5-14600K
    ├── gpu: RTX 4070
    ├── motherboard: ASUS ROG Z790-A
    └── ...

Category (카테고리)
    │
    ├── cpu
    ├── gpu
    ├── motherboard
    └── ...

Attribute (속성)
    │
    ├── brand: Intel, AMD, NVIDIA
    ├── socket: LGA1700, AM5
    └── ...

Purpose (목적)
    │
    ├── gaming
    ├── work
    └── development
```

### 엣지 타입

| 엣지 타입 | 방향 | 설명 | 예시 |
|-----------|------|------|------|
| `BELONGS_TO` | 부품 → 카테고리 | 부품의 카테고리 | i5-14600K → cpu |
| `HAS_ATTR` | 부품 → 속성 | 부품의 속성 | i5-14600K → LGA1700 |
| `COMPATIBLE` | 부품 ↔ 부품 | 호환 가능 | i5-14600K ↔ Z790 |
| `SYNERGY` | 부품 ↔ 부품 | 시너지 효과 | i5-14600K ↔ DDR5-6000 |
| `SUITABLE_FOR` | 부품 → 목적 | 목적 적합 | RTX 4070 → gaming |

### 그래프 시각화

```
                     ┌─────────┐
                     │ gaming  │
                     └────▲────┘
                          │ SUITABLE_FOR
    ┌──────────┐     ┌────┴────┐     ┌──────────┐
    │  Intel   │     │  i5-    │     │  LGA1700 │
    │  (Brand) │◀────│ 14600K  │────▶│ (Socket) │
    └──────────┘     └────┬────┘     └────▲─────┘
       HAS_ATTR           │               │
                          │COMPATIBLE     │HAS_ATTR
                          │               │
                     ┌────▼────┐          │
                     │ Z790-A  │──────────┘
                     │ (MB)    │
                     └────┬────┘
                          │
                     ┌────▼────┐
                     │  DDR5   │
                     │ (Attr)  │
                     └─────────┘
```

---

## 데이터 모델

### 입력: RecommendationRequest

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

### 출력: RecommendationResult

```python
{
    "recommendations": [
        {
            "rank": 1,
            "component_id": "mb_asus_rog_z790",
            "name": "ASUS ROG Strix Z790-A Gaming WiFi",
            "category": "motherboard",
            "price": 290000,
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
        {
            "rank": 2,
            "component_id": "mb_msi_z790",
            "name": "MSI MAG Z790 TOMAHAWK WIFI",
            "category": "motherboard",
            "price": 280000,
            "scores": {
                "relevance": 0.85,
                "compatibility": 1.0,
                "synergy": 0.82,
                "value": 0.82
            },
            "reasons": [
                "선택한 i5-14600K와 완벽 호환",
                "가격 대비 우수한 성능"
            ]
        }
        # ... top_k개
    ],
    "graph_context": {
        "connected_components": 15,
        "compatibility_edges": 8,
        "synergy_score_avg": 0.75
    },
    "processing_time_ms": 45
}
```

---

## 사용법

### 기본 추천

```python
from backend.modules.recommendation import GNNRecommendationEngine

engine = GNNRecommendationEngine()

# 추천 요청
result = engine.recommend(
    selected_components=[
        {"category": "cpu", "name": "Intel Core i5-14600K"}
    ],
    target_category="motherboard",
    budget=300000,
    purpose="gaming",
    preferences={"brand": "ASUS", "priority": "quality"}
)

# 결과 출력
for rec in result.recommendations:
    print(f"{rec.rank}. {rec.name}")
    print(f"   가격: {rec.price:,}원")
    print(f"   점수: {rec.scores.relevance:.2f}")
    print(f"   이유: {', '.join(rec.reasons)}")
```

### 간편 함수 사용

```python
from backend.modules.recommendation import get_recommendations

result = get_recommendations(
    selected_components=[{"category": "cpu", "name": "i5-14600K"}],
    target_category="motherboard",
    budget=300000,
    top_k=5
)
```

### 그래프 빌더 사용

```python
from backend.modules.recommendation.graph_builder import PCComponentGraph

graph = PCComponentGraph()

# 부품 추가
graph.add_component(
    component_id="cpu_i5_14600k",
    name="Intel Core i5-14600K",
    category="cpu",
    attributes={"socket": "LGA1700", "brand": "Intel"}
)

# 호환성 엣지 추가
graph.add_compatibility_edge(
    "cpu_i5_14600k",
    "mb_asus_z790",
    weight=1.0,
    notes="LGA1700 소켓 호환"
)

# 그래프 저장
graph.save("component_graph.json")

# 통계 확인
stats = graph.get_stats()
print(f"노드 수: {stats['total_nodes']}")
print(f"엣지 수: {stats['total_edges']}")
```

### GNN 모델 사용

```python
from backend.modules.recommendation.models import RecommendationGNN, GNNConfig

# 모델 설정
config = GNNConfig(
    embedding_dim=64,
    hidden_dim=128,
    num_layers=2,
    dropout=0.3
)

# 모델 초기화
model = RecommendationGNN(config, model_type="sage")

# 임베딩 조회
embeddings = model.get_embeddings(["cpu_i5_14600k", "mb_asus_z790"])

# 링크 예측
score = model.predict_link("cpu_i5_14600k", "mb_asus_z790")
print(f"호환 점수: {score:.4f}")

# 추천 생성
recommendations = model.recommend(
    selected_ids=["cpu_i5_14600k"],
    candidate_ids=["mb_asus_z790", "mb_msi_z790", "mb_gigabyte_z790"],
    top_k=3
)
```

---

## 구현 가이드

### 1단계: 그래프 데이터 구축

RAG 시스템의 부품 데이터를 그래프 형태로 변환한다.

```python
# RAG DB에서 부품 로드
from backend.rag import load_components_from_chroma

components = load_components_from_chroma()

# 그래프 빌드
graph = PCComponentGraph()
graph.load_components_from_dict(components)

# 호환성 엣지 자동 생성 (소켓 기반)
graph.build_compatibility_edges()

# 저장
graph.save("data/component_graph.json")
```

### 2단계: GNN 모델 구현

PyTorch Geometric을 사용하여 GraphSAGE 또는 GAT 모델을 구현한다.

```python
import torch
import torch.nn as nn
from torch_geometric.nn import SAGEConv, GATConv

class GraphSAGEModel(nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels, num_layers):
        super().__init__()
        self.convs = nn.ModuleList()
        
        # 첫 번째 레이어
        self.convs.append(SAGEConv(in_channels, hidden_channels))
        
        # 중간 레이어
        for _ in range(num_layers - 2):
            self.convs.append(SAGEConv(hidden_channels, hidden_channels))
        
        # 마지막 레이어
        self.convs.append(SAGEConv(hidden_channels, out_channels))
    
    def forward(self, x, edge_index):
        for conv in self.convs[:-1]:
            x = conv(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=0.3, training=self.training)
        
        x = self.convs[-1](x, edge_index)
        return x
```

### 3단계: 학습 파이프라인 구현

Link Prediction 방식으로 모델을 학습한다.

```python
def train_model(model, data, epochs=100):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        embeddings = model(data.x, data.edge_index)
        
        # Link prediction loss
        pos_score = (embeddings[pos_edge[0]] * embeddings[pos_edge[1]]).sum(dim=1)
        neg_score = (embeddings[neg_edge[0]] * embeddings[neg_edge[1]]).sum(dim=1)
        
        loss = F.binary_cross_entropy_with_logits(
            torch.cat([pos_score, neg_score]),
            torch.cat([torch.ones_like(pos_score), torch.zeros_like(neg_score)])
        )
        
        loss.backward()
        optimizer.step()
        
        if epoch % 10 == 0:
            print(f"Epoch {epoch}, Loss: {loss.item():.4f}")
```

### 4단계: 추론 및 랭킹

학습된 모델로 추천 점수를 계산하고 랭킹한다.

```python
def get_recommendations(model, selected_ids, candidate_ids, top_k=5):
    model.eval()
    
    with torch.no_grad():
        embeddings = model(data.x, data.edge_index)
        
        # 선택된 부품의 평균 임베딩
        selected_emb = embeddings[selected_indices].mean(dim=0)
        
        # 후보 부품과의 유사도 계산
        scores = []
        for candidate_idx in candidate_indices:
            candidate_emb = embeddings[candidate_idx]
            score = F.cosine_similarity(selected_emb.unsqueeze(0), 
                                        candidate_emb.unsqueeze(0))
            scores.append((candidate_ids[candidate_idx], score.item()))
        
        # 상위 K개 반환
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
```

---

## 테스트

### 테스트 파일 위치

```
backend/tests/test_recommendation.py
```

### 테스트 실행

```bash
# 전체 테스트
pytest backend/tests/test_recommendation.py -v

# 특정 테스트
pytest backend/tests/test_recommendation.py::test_recommendation_engine -v
```

### 테스트 항목

1. **그래프 빌더 테스트**
   - 노드/엣지 추가
   - 호환성 엣지 자동 생성
   - 저장/로드

2. **추천 엔진 테스트**
   - 기본 추천 기능
   - 예산 필터링
   - 호환성 필터링

3. **GNN 모델 테스트**
   - 임베딩 생성
   - 링크 예측 점수

4. **평가 메트릭 테스트**
   - Hit Rate @ K
   - NDCG @ K
   - MRR

---

## TODO

### 필수 구현

- [ ] PyTorch Geometric 설치 및 연동
- [ ] RAG 부품 데이터 → 그래프 변환 파이프라인
- [ ] GraphSAGE/GAT 모델 실제 학습
- [ ] 호환성 데이터베이스 구축 (소켓, 폼팩터 등)

### 선택적 구현

- [ ] HeteroGNN (이종 그래프) 구현
- [ ] 사용자 선택 로그 수집 및 학습
- [ ] 실시간 그래프 업데이트
- [ ] A/B 테스트 프레임워크

---

## 모델 성능 목표

| 메트릭 | 목표 | 설명 |
|--------|------|------|
| Hit Rate @ 5 | > 80% | 상위 5개 중 정답 포함 비율 |
| NDCG @ 5 | > 0.70 | 순위 품질 점수 |
| MRR | > 0.50 | 첫 정답 순위 역수 평균 |

---

## 참고 자료

### GNN 라이브러리

- [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/)
- [DGL (Deep Graph Library)](https://www.dgl.ai/)
- [NetworkX](https://networkx.org/)

### 논문

- [GraphSAGE](https://arxiv.org/abs/1706.02216) - Inductive Representation Learning
- [GAT](https://arxiv.org/abs/1710.10903) - Graph Attention Networks
- [GNN for Recommendation](https://arxiv.org/abs/1904.12575) - LightGCN

### 튜토리얼

- [PyG 공식 튜토리얼](https://pytorch-geometric.readthedocs.io/en/latest/get_started/introduction.html)
- [GNN 추천 시스템 구현](https://github.com/gusye1234/LightGCN-PyTorch)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-02 | 0.1.0 | 초기 스켈레톤 구현 |
