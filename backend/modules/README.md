# Spckit AI Backend Modules

> PC 부품 추천 시스템의 핵심 모듈 패키지

## 목차

- [개요](#개요)
- [모듈 구조](#모듈-구조)
- [각 모듈 상세](#각-모듈-상세)
  - [1. multi_agent - 멀티 에이전트 오케스트레이션](#1-multi_agent---멀티-에이전트-오케스트레이션)
  - [2. pc_diagnosis - PC 사양 진단](#2-pc_diagnosis---pc-사양-진단)
  - [3. price_prediction - 가격 예측](#3-price_prediction---가격-예측)
  - [4. recommendation - 추천 시스템](#4-recommendation---추천-시스템)
  - [5. compatibility - 호환성 검사](#5-compatibility---호환성-검사)
- [설치 및 의존성](#설치-및-의존성)
- [테스트 실행](#테스트-실행)
- [개발 가이드](#개발-가이드)
- [담당자 배정](#담당자-배정)

---

## 개요

이 디렉토리는 Spckit AI 백엔드의 핵심 기능 모듈들을 포함한다. 각 모듈은 독립적으로 개발 및 테스트 가능하도록 설계되었으며, 팀원들이 분담하여 개발할 수 있다.

### 설계 원칙

1. **모듈 독립성**: 각 모듈은 독립적으로 실행 및 테스트 가능
2. **명확한 인터페이스**: 입력/출력 형식이 Pydantic 모델로 정의됨
3. **상세한 주석**: 목표, 로직, 참고 자료가 코드 내 주석으로 제공됨
4. **테스트 포함**: 각 모듈별 테스트 파일 제공

---

## 모듈 구조

```
backend/modules/
├── __init__.py              # 모듈 패키지 초기화
├── README.md                # 이 문서
│
├── multi_agent/             # 1. CREWai 멀티 에이전트
│   ├── __init__.py
│   ├── orchestrator.py      # 에이전트 오케스트레이터
│   └── agents.py            # 개별 에이전트 정의
│
├── pc_diagnosis/            # 2. PC 사양 진단
│   ├── __init__.py
│   ├── engine.py            # 진단 엔진
│   ├── collectors.py        # 하드웨어 정보 수집
│   └── analyzers.py         # 병목 분석 및 업그레이드 조언
│
├── price_prediction/        # 3. 가격 예측
│   ├── __init__.py
│   ├── predictor.py         # 예측 모델
│   ├── data_collector.py    # 가격 데이터 수집
│   └── features.py          # 특성 추출
│
├── recommendation/          # 4. GNN 추천 시스템
│   ├── __init__.py
│   ├── engine.py            # 추천 엔진
│   ├── graph_builder.py     # 그래프 구축
│   └── models.py            # GNN 모델
│
└── compatibility/           # 5. 호환성 검사
    ├── __init__.py
    ├── engine.py            # 호환성 엔진
    ├── ontology.py          # PC 온톨로지
    └── rules.py             # 호환성 규칙
```

---

## 각 모듈 상세

### 1. multi_agent - 멀티 에이전트 오케스트레이션

**목표**: CREWai 프레임워크를 활용하여 여러 전문 AI 에이전트가 협력적으로 PC 부품 추천 작업을 수행

**핵심 파일**:
- `orchestrator.py`: 에이전트 조율 및 전체 파이프라인 관리
- `agents.py`: 5개 전문 에이전트 정의
  - RequirementAnalyzerAgent: 요구사항 분석
  - BudgetPlannerAgent: 예산 분배
  - ComponentSelectorAgent: 부품 선택
  - CompatibilityCheckerAgent: 호환성 검증
  - RecommendationWriterAgent: 추천 결과 작성

**사용 예시**:
```python
from backend.modules.multi_agent import AgentOrchestrator

orchestrator = AgentOrchestrator()
result = orchestrator.run({
    "query": "게임용 PC 추천해줘",
    "budget": 1500000,
    "purpose": "gaming"
})
```

**필요 라이브러리**:
```bash
pip install crewai crewai-tools langchain-google-genai
```

---

### 2. pc_diagnosis - PC 사양 진단

**목표**: 사용자의 현재 PC 사양을 분석하여 성능 등급, 병목 현상, 업그레이드 추천 제공

**핵심 파일**:
- `engine.py`: 종합 진단 엔진
- `collectors.py`: 하드웨어 정보 수집 및 정규화
- `analyzers.py`: 병목 분석 및 업그레이드 조언

**사용 예시**:
```python
from backend.modules.pc_diagnosis import PCDiagnosisEngine

engine = PCDiagnosisEngine()
result = engine.diagnose({
    "cpu": {"name": "Intel Core i5-12400F"},
    "gpu": {"name": "RTX 3060", "vram": 12},
    "memory": {"capacity": 16, "speed": 3200},
    "storage": {"type": "NVMe SSD", "capacity": 512},
})

print(f"전체 점수: {result.overall_score}")
print(f"성능 등급: {result.tier}")
print(f"병목: {result.bottleneck.description}")
```

**출력 항목**:
- 전체 점수 (0-100)
- 성능 등급 (entry/mid/mid-high/high/enthusiast)
- 병목 분석 결과
- 부품별 점수
- 업그레이드 추천

---

### 3. price_prediction - 가격 예측

**목표**: 시계열 분석을 통해 PC 부품의 미래 가격을 예측하고 최적의 구매 시점 추천

**핵심 파일**:
- `predictor.py`: 가격 예측 모델 (Simple/Prophet/TFT)
- `data_collector.py`: 가격 데이터 수집
- `features.py`: 시계열 특성 추출

**사용 예시**:
```python
from backend.modules.price_prediction import PricePredictionModel

model = PricePredictionModel()
result = model.predict(
    component_id="gpu_rtx4070",
    component_name="RTX 4070",
    category="gpu",
    current_price=700000,
    price_history=[...],  # 가격 이력
    prediction_days=30,
)

print(f"추세: {result.trend.direction}")
print(f"구매 권장: {result.buy_recommendation.action}")
```

**필요 라이브러리**:
```bash
pip install numpy pandas
# 선택적 (고급 모델):
pip install prophet pytorch-forecasting
```

---

### 4. recommendation - GNN 추천 시스템

**목표**: 그래프 신경망을 활용하여 사용자의 선택에 따라 동적으로 변화하는 개인화 추천 제공

**핵심 파일**:
- `engine.py`: 추천 엔진
- `graph_builder.py`: 부품-속성-사용자 그래프 구축
- `models.py`: GNN 모델 (GraphSAGE/GAT)

**사용 예시**:
```python
from backend.modules.recommendation import GNNRecommendationEngine

engine = GNNRecommendationEngine()
result = engine.recommend(
    selected_components=[
        {"category": "cpu", "name": "Intel Core i5-14600K"}
    ],
    target_category="motherboard",
    budget=300000,
    purpose="gaming",
)

for rec in result.recommendations:
    print(f"{rec.rank}. {rec.name} - 적합도: {rec.scores.relevance:.2f}")
```

**필요 라이브러리**:
```bash
pip install torch torch-geometric networkx
```

---

### 5. compatibility - 호환성 검사

**목표**: 온톨로지와 규칙 기반으로 PC 부품 간 호환성을 정확하게 검증

**핵심 파일**:
- `engine.py`: 호환성 검사 엔진
- `ontology.py`: PC 부품 온톨로지 (지식 그래프)
- `rules.py`: 호환성 규칙 정의

**사용 예시**:
```python
from backend.modules.compatibility import CompatibilityEngine

engine = CompatibilityEngine()
result = engine.check_all([
    {"category": "cpu", "name": "Intel i5-14600K", "specs": {"socket": "LGA1700"}},
    {"category": "motherboard", "name": "ASUS Z790", "specs": {"socket": "LGA1700"}},
    {"category": "memory", "name": "DDR5-5600", "specs": {"generation": "DDR5"}},
])

if result.is_compatible:
    print("모든 부품이 호환됩니다!")
else:
    for check in result.checks:
        if check.status == "fail":
            print(f"호환 불가: {check.message}")
```

**검사 항목**:
- CPU-메인보드 소켓
- 메모리-메인보드 타입
- GPU-케이스 길이
- 메인보드-케이스 폼팩터
- 전력 요구량

---

## 설치 및 의존성

### 기본 의존성

```bash
# 가상 환경 생성
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 기본 패키지 설치
pip install pydantic loguru numpy
```

### 모듈별 추가 의존성

| 모듈 | 필수 | 선택 (고급 기능) |
|------|------|-----------------|
| multi_agent | pydantic, loguru | crewai, langchain-google-genai |
| pc_diagnosis | pydantic, loguru, numpy | - |
| price_prediction | pydantic, numpy | prophet, pytorch-forecasting |
| recommendation | pydantic, loguru | torch, torch-geometric |
| compatibility | pydantic, loguru | rdflib, owlready2 |

---

## 테스트 실행

```bash
# 전체 테스트
pytest backend/tests/ -v

# 특정 모듈 테스트
pytest backend/tests/test_multi_agent.py -v
pytest backend/tests/test_pc_diagnosis.py -v
pytest backend/tests/test_price_prediction.py -v
pytest backend/tests/test_recommendation.py -v
pytest backend/tests/test_compatibility.py -v

# 커버리지 포함
pytest backend/tests/ --cov=backend/modules
```

---

## 개발 가이드

### 새 기능 추가 시

1. 해당 모듈 파일에 주석으로 설계 문서화
2. Pydantic 모델로 입력/출력 정의
3. 테스트 케이스 작성
4. README 업데이트

### 코드 스타일

- 타입 힌트 필수
- docstring 작성 (Google 스타일)
- loguru로 로깅
- 한글 주석/메시지 사용

### 브랜치 전략

```bash
# 새 기능 개발
git checkout -b feature/모듈명/기능설명/YYMMDD

# 예시
git checkout -b feature/pc_diagnosis/add-benchmark-db/241231
```

---

## 담당자 배정

| 모듈 | 담당자 | 우선순위 | 예상 기간 |
|------|--------|----------|-----------|
| multi_agent | [이름] | 중 | 2주 |
| pc_diagnosis | [이름] | 중 | 1주 |
| price_prediction | [이름] | 하 | 2주 |
| recommendation | [이름] | 상 | 3주 |
| compatibility | [이름] | 상 | 1주 |
| RAG 개선 | [이름] | 상 | 1주 |

### 개발 순서 권장

1. **compatibility** (1주) - 다른 모듈의 기반
2. **pc_diagnosis** (1주) - 독립적, 빠르게 완성 가능
3. **RAG 개선** (1주) - 기존 코드 수정
4. **recommendation** (3주) - 핵심 기능, GNN 학습 필요
5. **multi_agent** (2주) - 다른 모듈 통합
6. **price_prediction** (2주) - 데이터 수집 선행 필요

---

## 관련 문서

- [RAG 가이드](../../docs/RAG_GUIDE.md)
- [빠른 시작](../../docs/QUICK_START.md)
- [프로젝트 구조](../../docs/PROJECT_STRUCTURE.md)

---

**작성일**: 2024-12-31  
**버전**: 0.1.0
