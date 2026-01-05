# GNN 추천 시스템 모듈 데이터

> 부품 관계 그래프, 호환성 매트릭스, 시너지 데이터

---

## 목차

1. [필요 데이터 목록](#1-필요-데이터-목록)
2. [데이터 수집 방법](#2-데이터-수집-방법)
3. [그래프 데이터 구조](#3-그래프-데이터-구조)
4. [데이터 전처리](#4-데이터-전처리)

---

## 1. 필요 데이터 목록

| 파일명 | 설명 | 우선순위 | 상태 |
|--------|------|----------|------|
| `component_nodes.json` | 부품 노드 정보 | 필수 | 미수집 |
| `compatibility_edges.json` | 호환성 엣지 | 필수 | 미수집 |
| `synergy_edges.json` | 시너지/궁합 엣지 | 권장 | 미수집 |
| `attribute_mappings.json` | 부품-속성 매핑 | 필수 | 미수집 |
| `user_interactions.json` | 사용자 선택 로그 (학습용) | 권장 | 미수집 |
| `popular_builds.json` | 인기 조립 조합 | 권장 | 미수집 |

---

## 2. 데이터 수집 방법

### 2.1 부품 노드 데이터 (component_nodes.json)

**데이터 출처:**
- 기존 SQL 덤프 (`data/pc_data_dump.sql`)에서 추출
- 다나와/컴퓨존 제품 정보

**기존 데이터 활용:**

```python
"""
기존 SQL 덤프에서 노드 데이터 추출
"""
from backend.rag.data_parser import SQLDataParser
import json

def extract_component_nodes():
    """SQL 덤프에서 부품 노드 추출"""
    parser = SQLDataParser()
    records = parser.parse_sql_dump()
    
    nodes = []
    for record in records:
        node = {
            "id": f"{record['category']}_{record.get('id', len(nodes))}",
            "category": record['category'],
            "name": record['name'],
            "brand": extract_brand(record['name']),
            "price": record.get('price'),
            "attributes": extract_attributes(record)
        }
        nodes.append(node)
    
    return nodes

def extract_brand(name: str) -> str:
    """제품명에서 브랜드 추출"""
    brands = {
        "Intel": ["Intel", "인텔"],
        "AMD": ["AMD", "라이젠", "Ryzen"],
        "NVIDIA": ["NVIDIA", "GeForce", "RTX", "GTX"],
        "Samsung": ["삼성", "Samsung"],
        "ASUS": ["ASUS", "아수스", "ROG"],
        "MSI": ["MSI"],
        "Gigabyte": ["GIGABYTE", "기가바이트", "AORUS"],
        # ...
    }
    
    for brand, keywords in brands.items():
        for kw in keywords:
            if kw.lower() in name.lower():
                return brand
    
    return "Unknown"

def extract_attributes(record: dict) -> dict:
    """레코드에서 속성 추출"""
    attrs = {}
    
    # 카테고리별 속성 추출
    category = record.get('category', '')
    
    if category == 'cpu':
        attrs['socket'] = extract_socket(record)
        attrs['cores'] = record.get('cores')
        attrs['tdp'] = record.get('tdp')
    elif category == 'gpu':
        attrs['vram'] = record.get('vram')
        attrs['memory_type'] = record.get('memory_type')
        attrs['length_mm'] = record.get('length')
    elif category == 'motherboard':
        attrs['socket'] = record.get('socket')
        attrs['chipset'] = record.get('chipset')
        attrs['form_factor'] = record.get('form_factor')
        attrs['memory_type'] = record.get('memory_type')
    # ...
    
    return attrs
```

### 2.2 호환성 엣지 (compatibility_edges.json)

**데이터 출처:**
- 제조사 호환성 표
- PC Part Picker 호환성 데이터
- 수동 규칙 정의

**호환성 규칙 기반 생성:**

```python
"""
호환성 엣지 자동 생성
"""

def generate_compatibility_edges(nodes: list) -> list:
    """노드 간 호환성 엣지 생성"""
    edges = []
    
    # 카테고리별 노드 분류
    by_category = {}
    for node in nodes:
        cat = node['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(node)
    
    # CPU-Motherboard 호환성 (소켓 기준)
    for cpu in by_category.get('cpu', []):
        cpu_socket = cpu['attributes'].get('socket')
        if not cpu_socket:
            continue
        
        for mb in by_category.get('motherboard', []):
            mb_socket = mb['attributes'].get('socket')
            if cpu_socket == mb_socket:
                edges.append({
                    "source": cpu['id'],
                    "target": mb['id'],
                    "type": "compatible",
                    "relation": "cpu_motherboard",
                    "confidence": 1.0,
                    "rule": f"socket_match:{cpu_socket}"
                })
    
    # Memory-Motherboard 호환성 (DDR 타입)
    for mem in by_category.get('memory', []):
        mem_type = mem['attributes'].get('memory_type')
        if not mem_type:
            continue
        
        for mb in by_category.get('motherboard', []):
            mb_mem_type = mb['attributes'].get('memory_type')
            if mem_type == mb_mem_type:
                edges.append({
                    "source": mem['id'],
                    "target": mb['id'],
                    "type": "compatible",
                    "relation": "memory_motherboard",
                    "confidence": 1.0
                })
    
    # GPU-Case 호환성 (길이)
    for gpu in by_category.get('gpu', []):
        gpu_length = gpu['attributes'].get('length_mm')
        if not gpu_length:
            continue
        
        for case in by_category.get('case', []):
            max_gpu_length = case['attributes'].get('max_gpu_length')
            if max_gpu_length and gpu_length <= max_gpu_length:
                edges.append({
                    "source": gpu['id'],
                    "target": case['id'],
                    "type": "compatible",
                    "relation": "gpu_case",
                    "confidence": 1.0
                })
    
    return edges
```

### 2.3 시너지 엣지 (synergy_edges.json)

**데이터 출처:**
- 하드웨어 리뷰 (벤치마크 결과)
- 커뮤니티 추천 조합
- 전문가 의견

**시너지 정의:**

```python
"""
부품 간 시너지 관계 정의
시너지 = 함께 사용 시 성능 향상 또는 가성비 최적화
"""

SYNERGY_RULES = [
    # CPU-GPU 밸런스 (병목 최소화)
    {
        "pattern": {
            "cpu_tier": "high",
            "gpu_tier": "high"
        },
        "synergy_score": 1.0,
        "reason": "high_end_balance"
    },
    {
        "pattern": {
            "cpu_tier": "mid",
            "gpu_tier": "mid"
        },
        "synergy_score": 0.9,
        "reason": "mid_range_balance"
    },
    # 동일 브랜드 시너지
    {
        "pattern": {
            "cpu_brand": "AMD",
            "gpu_brand": "AMD"
        },
        "synergy_score": 0.1,  # 낮은 보너스
        "reason": "same_brand_bonus"
    },
    # 게이밍 최적 조합
    {
        "products": [
            "AMD Ryzen 7 7800X3D",
            "NVIDIA RTX 4070"
        ],
        "synergy_score": 0.95,
        "reason": "gaming_optimized",
        "source": "hardware_review"
    }
]

def generate_synergy_edges(nodes: list) -> list:
    """시너지 엣지 생성"""
    edges = []
    
    # 티어 기반 시너지
    by_category = {}
    for node in nodes:
        cat = node['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(node)
    
    # CPU-GPU 밸런스 시너지
    for cpu in by_category.get('cpu', []):
        cpu_tier = get_tier(cpu)
        
        for gpu in by_category.get('gpu', []):
            gpu_tier = get_tier(gpu)
            
            # 같은 티어면 시너지 높음
            if cpu_tier == gpu_tier:
                edges.append({
                    "source": cpu['id'],
                    "target": gpu['id'],
                    "type": "synergy",
                    "score": 0.9,
                    "reason": "balanced_tier"
                })
            # 1단계 차이는 약간의 시너지
            elif abs(TIERS.index(cpu_tier) - TIERS.index(gpu_tier)) == 1:
                edges.append({
                    "source": cpu['id'],
                    "target": gpu['id'],
                    "type": "synergy",
                    "score": 0.6,
                    "reason": "slight_imbalance"
                })
    
    return edges

TIERS = ['entry', 'budget', 'mid', 'mid-high', 'high', 'enthusiast']

def get_tier(node: dict) -> str:
    """부품 티어 판단"""
    price = node.get('price', 0)
    category = node['category']
    
    # 가격 기반 티어 (카테고리별 기준 다름)
    tier_thresholds = {
        'cpu': [100000, 200000, 350000, 500000, 700000],
        'gpu': [200000, 400000, 600000, 900000, 1200000],
        # ...
    }
    
    thresholds = tier_thresholds.get(category, [100000, 300000, 500000, 700000, 1000000])
    
    for i, threshold in enumerate(thresholds):
        if price < threshold:
            return TIERS[i]
    
    return TIERS[-1]
```

### 2.4 인기 조립 조합 (popular_builds.json)

**데이터 출처:**
- 퀘이사존 견적 게시판
- 다나와 PC 견적
- 유튜브 조립 영상
- Reddit r/buildapc

**수동 수집:**

```json
{
  "version": "1.0.0",
  "builds": [
    {
      "id": "gaming_mid_2024",
      "name": "2024 미드레인지 게이밍",
      "purpose": "gaming_1440p",
      "budget_range": [1200000, 1500000],
      "components": {
        "cpu": "AMD Ryzen 5 7600X",
        "motherboard": "MSI B650M 박격포",
        "memory": "G.Skill DDR5 32GB 6000MHz",
        "gpu": "NVIDIA RTX 4060 Ti",
        "storage": "Samsung 980 Pro 1TB",
        "psu": "Seasonic Focus GX-650",
        "case": "NZXT H5 Flow"
      },
      "popularity_score": 0.85,
      "source": "quasarzone",
      "collected_date": "2024-12-01"
    },
    {
      "id": "workstation_high_2024",
      "name": "2024 하이엔드 작업용",
      "purpose": "content_creation",
      "budget_range": [3000000, 4000000],
      "components": {
        "cpu": "Intel Core i9-14900K",
        "motherboard": "ASUS ROG Maximus Z790",
        "memory": "G.Skill DDR5 64GB 6400MHz",
        "gpu": "NVIDIA RTX 4080",
        "storage": "Samsung 990 Pro 2TB",
        "psu": "Corsair RM1000x",
        "case": "Fractal Design Torrent"
      },
      "popularity_score": 0.75,
      "source": "youtube_review"
    }
  ]
}
```

---

## 3. 그래프 데이터 구조

### 전체 그래프 스키마

```
┌─────────────────────────────────────────────────────────────┐
│                    PC Component Graph                        │
│                                                              │
│  Node Types:                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Component │ │ Category │ │Attribute │ │ Purpose  │       │
│  │ (부품)   │ │ (카테고리)│ │  (속성)  │ │  (용도)  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  Edge Types:                                                 │
│  ─────────── BELONGS_TO ───────────                         │
│  Component → Category                                        │
│                                                              │
│  ─────────── HAS_ATTRIBUTE ────────                         │
│  Component → Attribute                                       │
│                                                              │
│  ─────────── COMPATIBLE_WITH ──────                         │
│  Component ↔ Component (양방향)                              │
│                                                              │
│  ─────────── SYNERGY_WITH ─────────                         │
│  Component ↔ Component (가중치)                              │
│                                                              │
│  ─────────── SUITABLE_FOR ─────────                         │
│  Component → Purpose                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### PyTorch Geometric 형식

```python
"""
PyTorch Geometric 데이터 형식으로 변환
"""
import torch
from torch_geometric.data import HeteroData

def build_pyg_graph(nodes: list, edges: list) -> HeteroData:
    """PyTorch Geometric HeteroData 생성"""
    data = HeteroData()
    
    # 노드 인덱스 매핑
    node_mapping = {}
    by_type = {'component': [], 'category': [], 'attribute': [], 'purpose': []}
    
    for i, node in enumerate(nodes):
        node_type = node.get('type', 'component')
        node_mapping[node['id']] = (node_type, len(by_type[node_type]))
        by_type[node_type].append(node)
    
    # 노드 피처 (임베딩으로 대체 가능)
    for node_type, node_list in by_type.items():
        if node_list:
            # 간단한 피처: one-hot 또는 랜덤 초기화
            num_nodes = len(node_list)
            data[node_type].x = torch.randn(num_nodes, 128)  # 128차원 피처
            data[node_type].num_nodes = num_nodes
    
    # 엣지 구성
    edge_types = {}
    for edge in edges:
        source_type, source_idx = node_mapping[edge['source']]
        target_type, target_idx = node_mapping[edge['target']]
        edge_type = (source_type, edge['type'], target_type)
        
        if edge_type not in edge_types:
            edge_types[edge_type] = {'source': [], 'target': [], 'weight': []}
        
        edge_types[edge_type]['source'].append(source_idx)
        edge_types[edge_type]['target'].append(target_idx)
        edge_types[edge_type]['weight'].append(edge.get('score', 1.0))
    
    # 엣지 텐서 생성
    for edge_type, indices in edge_types.items():
        data[edge_type].edge_index = torch.tensor(
            [indices['source'], indices['target']], 
            dtype=torch.long
        )
        data[edge_type].edge_attr = torch.tensor(
            indices['weight'], 
            dtype=torch.float
        ).unsqueeze(1)
    
    return data
```

---

## 4. 데이터 전처리

### 그래프 생성 파이프라인

```python
"""
backend/scripts/build_graph.py
그래프 데이터 생성 스크립트

사용법:
    python backend/scripts/build_graph.py
"""
from pathlib import Path
import json

def main():
    data_dir = Path("backend/data/recommendation")
    
    # 1. 노드 생성 (기존 SQL에서)
    print("[1/4] 노드 데이터 생성...")
    nodes = extract_component_nodes()
    
    # 카테고리/속성/용도 노드 추가
    nodes.extend(generate_category_nodes())
    nodes.extend(generate_attribute_nodes(nodes))
    nodes.extend(generate_purpose_nodes())
    
    with open(data_dir / "component_nodes.json", "w", encoding="utf-8") as f:
        json.dump({"nodes": nodes}, f, ensure_ascii=False, indent=2)
    print(f"  - 총 {len(nodes)}개 노드 생성")
    
    # 2. 호환성 엣지 생성
    print("[2/4] 호환성 엣지 생성...")
    compat_edges = generate_compatibility_edges(nodes)
    
    with open(data_dir / "compatibility_edges.json", "w", encoding="utf-8") as f:
        json.dump({"edges": compat_edges}, f, ensure_ascii=False, indent=2)
    print(f"  - 총 {len(compat_edges)}개 호환성 엣지")
    
    # 3. 시너지 엣지 생성
    print("[3/4] 시너지 엣지 생성...")
    synergy_edges = generate_synergy_edges(nodes)
    
    with open(data_dir / "synergy_edges.json", "w", encoding="utf-8") as f:
        json.dump({"edges": synergy_edges}, f, ensure_ascii=False, indent=2)
    print(f"  - 총 {len(synergy_edges)}개 시너지 엣지")
    
    # 4. 속성 매핑 생성
    print("[4/4] 속성 매핑 생성...")
    attr_edges = generate_attribute_edges(nodes)
    
    with open(data_dir / "attribute_mappings.json", "w", encoding="utf-8") as f:
        json.dump({"edges": attr_edges}, f, ensure_ascii=False, indent=2)
    print(f"  - 총 {len(attr_edges)}개 속성 매핑")
    
    # 통계 출력
    print("\n[완료] 그래프 데이터 생성 완료")
    print(f"  - 노드: {len(nodes)}개")
    print(f"  - 엣지: {len(compat_edges) + len(synergy_edges) + len(attr_edges)}개")

if __name__ == "__main__":
    main()
```

---

## 5. 데이터 요구량

| 항목 | 최소량 | 권장량 |
|------|--------|--------|
| 부품 노드 | 500개 | 5000개+ |
| 호환성 엣지 | 1000개 | 10000개+ |
| 시너지 엣지 | 500개 | 5000개+ |
| 인기 조합 | 20개 | 100개+ |

---

## 담당자 체크리스트

- [ ] 기존 SQL에서 노드 데이터 추출
- [ ] 호환성 엣지 규칙 정의 (5개 이상)
- [ ] 시너지 엣지 규칙 정의 (3개 이상)
- [ ] 인기 조합 20개 이상 수집
- [ ] 그래프 생성 스크립트 실행
- [ ] PyTorch Geometric 변환 테스트
- [ ] GNN 모델 학습 테스트

# GNN 추천 데이터 모듈

> 원본 PC 부품 SQL 데이터를 GNN 학습용 그래프 구조로 정제하는 모듈입니다.

## 📁 데이터 파일 설명

1. **component_nodes.json**: SQL에서 추출된 약 13만 개의 부품 노드 정보 (이름, 브랜드, 가격 등).
2. **compatibility_edges.json**: 소켓, 메모리 규격, 폼팩터에 따른 물리적 연결 데이터.
3. **synergy_edges.json**: 브랜드 일치 등 추천 알고리즘의 가중치를 위한 심리적/성능적 연결 데이터.
4. **attribute_mappings.json**: 부품-속성(LGA1700 등) 간의 매핑 정보.

## 🛠️ 호환성 규칙 정의 (Implemented)
- **Socket Match**: CPU와 메인보드의 소켓(LGA1700, AM5 등) 일치 여부 검증.
- **DDR Type Match**: 메인보드와 메모리의 DDR 규격 일치 여부 검증.
- **Form Factor Match**: 케이스와 메인보드의 크기(ATX, ITX 등) 호환성 검증.
- **Same Brand Synergy**: 동일 브랜드 사용 시 시너지 가중치 부여.

## 🚀 실행 가이드

데이터를 최신화하려면 아래 명령어를 실행하십시오:

```bash
python backend/data/recommendation/build_graph.py