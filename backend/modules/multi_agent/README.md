# Multi-Agent 모듈

> CREWai 프레임워크 기반 멀티 에이전트 PC 부품 추천 시스템

---

## 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [파일 구조](#파일-구조)
- [에이전트 구성](#에이전트-구성)
- [도구(Tools) 정의](#도구tools-정의)
- [외부 모듈 연동](#외부-모듈-연동)
- [데이터 모델](#데이터-모델)
- [사용법](#사용법)
- [구현 가이드](#구현-가이드)
- [테스트](#테스트)
- [변경 이력](#변경-이력)

---

## 개요

### 목표

**추천 에이전트**와 **채팅 에이전트**로 분리된 멀티 에이전트 시스템 구현.

- **추천 에이전트**: 부품 선택, 호환성 검증, 가격 예측치 통합, 맞춤형 추천 제공
- **채팅 에이전트**: 사용자 요구사항 분석, 대화 흐름 관리, 결과 작성

### 핵심 기술

| 기술 | 역할 |
|------|------|
| **CREWai** | LangChain 기반 멀티 에이전트 프레임워크 |
| **Google Gemini API** | LLM 백엔드 (`gemini-3-flash-preview`) |
| **Pydantic** | 데이터 검증 및 스키마 정의 |
| **RAG 파이프라인** | 부품 검색 및 후보 추출 |

---

## 아키텍처

### 전체 시스템 흐름

```
사용자 요청
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AgentOrchestrator                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Crew (작업 조율)                              │    │
│  │                                                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐  │    │
│  │  │              채팅 에이전트 (Chat Agent)                     │  │    │
│  │  │  ┌──────────────────┐  ┌──────────────────────────────┐   │  │    │
│  │  │  │ 요구사항 분석기   │→│   추천 결과 작성기            │   │  │    │
│  │  │  │ (Requirement     │  │   (Recommendation            │   │  │    │
│  │  │  │  Analyzer)       │  │    Writer)                   │   │  │    │
│  │  │  └──────────────────┘  └──────────────────────────────┘   │  │    │
│  │  └────────────────────────────────────────────────────────────┘  │    │
│  │                         │                                         │    │
│  │                         ▼                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐  │    │
│  │  │              추천 에이전트 (Recommendation Agent)           │  │    │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐   │  │    │
│  │  │  │ 예산 분배   │→│ 부품 선택기 │→│   호환성 검증기     │   │  │    │
│  │  │  │ 기획자     │  │ (RAG 연동) │  │   (외부 모듈)       │   │  │    │
│  │  │  └────────────┘  └────────────┘  └────────────────────┘   │  │    │
│  │  │                        │                                    │  │    │
│  │  │       ┌────────────────┼─────────────────────┐             │  │    │
│  │  │       ▼                ▼                     ▼             │  │    │
│  │  │  ┌──────────┐  ┌──────────────┐  ┌─────────────────────┐  │  │    │
│  │  │  │ 가격예측  │  │  추천엔진   │  │   호환성 검사        │  │  │    │
│  │  │  │ (외부)   │  │  (GNN/Rule) │  │   (외부 모듈)        │  │  │    │
│  │  │  └──────────┘  └──────────────┘  └─────────────────────┘  │  │    │
│  │  └────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
    │
    ▼
최종 추천 결과 (부품 목록 + 호환성 + 가격 예측 + 맞춤 추천)
```

### 에이전트 분리 구조

| 에이전트 그룹 | 포함 에이전트 | 역할 |
|--------------|---------------|------|
| **채팅 에이전트** | RequirementAnalyzer, RecommendationWriter | 사용자 대화 처리, 결과 작성 |
| **추천 에이전트** | BudgetPlanner, ComponentSelector, CompatibilityChecker | 부품 선택, 검증, 외부 모듈 연동 |

---

## 파일 구조

```
multi_agent/
├── __init__.py          # 모듈 초기화 및 exports
├── orchestrator.py      # 메인 오케스트레이터 클래스
├── agents.py            # 개별 에이전트 정의
├── tools.py             # CREWai 도구 정의
└── README.md            # 이 문서
```

### 파일별 역할

| 파일 | 역할 | 주요 클래스/함수 |
|------|------|------------------|
| `orchestrator.py` | 에이전트 조율 및 파이프라인 관리 | `AgentOrchestrator`, `UserRequest`, `RecommendationResult` |
| `agents.py` | 개별 전문 에이전트 정의 | `RequirementAnalyzerAgent`, `BudgetPlannerAgent`, `ComponentSelectorAgent`, `CompatibilityCheckerAgent` |
| `tools.py` | CREWai용 도구 래퍼 | `SearchPartsTool`, `CompatibilityCheckTool`, `AutoStepBuilderTool` |

---

## 에이전트 구성

### 1. RequirementAnalyzerAgent (요구사항 분석기) - 채팅 에이전트

| 항목 | 내용 |
|------|------|
| **역할** | 사용자 입력에서 핵심 요구사항 추출 |
| **그룹** | 채팅 에이전트 |
| **입력** | 자연어 사용자 쿼리 |
| **출력** | 구조화된 요구사항 (예산, 목적, 선호도 등) |

**분석 항목:**
- 예산 추출 (명시적/암시적)
- 사용 목적 분류 (게임/업무/영상편집/개발 등)
- 성능 티어 판단 (entry/mid/high/enthusiast)
- 누락 정보 식별 및 추가 질문 생성

### 2. BudgetPlannerAgent (예산 분배 기획자) - 추천 에이전트

| 항목 | 내용 |
|------|------|
| **역할** | 전체 예산을 부품 카테고리별로 최적 분배 |
| **그룹** | 추천 에이전트 |
| **입력** | 예산, 목적, 우선순위 |
| **출력** | 카테고리별 예산 할당 |

**예산 분배 템플릿 (게이밍 PC):**

| 카테고리 | 비율 |
|----------|------|
| GPU | 35-40% |
| CPU | 20-25% |
| 메인보드 | 8-12% |
| 메모리 | 8-10% |
| 저장장치 | 10-12% |
| PSU | 5-8% |
| 케이스 | 5-8% |

### 3. ComponentSelectorAgent (부품 선택기) - 추천 에이전트

| 항목 | 내용 |
|------|------|
| **역할** | RAG + 추천엔진을 활용해 최적 부품 후보 선정 |
| **그룹** | 추천 에이전트 |
| **입력** | 카테고리별 예산, 요구사항, 이전 선택 부품 |
| **출력** | 부품 후보 목록 (호환성/가격예측 정보 포함) |
| **연동 모듈** | `backend/rag/retriever.py`, `backend/data/recommendation/` |

**통합 정보:**
- RAG 검색 결과 (유사도 기반 후보)
- 추천엔진 결과 (시너지 기반 맞춤 추천)
- 가격 예측치 (향후 가격 변동 예상)

### 4. CompatibilityCheckerAgent (호환성 검증기) - 추천 에이전트

| 항목 | 내용 |
|------|------|
| **역할** | 선택된 부품 간 호환성 검증 |
| **그룹** | 추천 에이전트 |
| **입력** | 부품 후보 목록 |
| **출력** | 호환성 검증 결과 |
| **연동 모듈** | `backend/modules/compatibility/engine.py`, `backend/data/compatibility/` |

---

## 도구(Tools) 정의

### 1. SearchPartsTool (PC Component Search Tool)

```python
# tools.py
class SearchPartsTool(BaseTool):
    """
    RAG 시스템을 통한 부품 검색 도구
    
    입력:
        category: str - 부품 카테고리 (cpu, gpu, motherboard 등)
        query: str - 자연어 검색 쿼리
        budget: Optional[int] - 예산 제한
    
    출력:
        List[Dict] - 검색된 부품 목록 (이름, 가격, 스펙, 유사도)
    """
```

### 2. CompatibilityCheckTool (PC Compatibility Check Tool)

```python
class CompatibilityCheckTool(BaseTool):
    """
    호환성 검사 엔진 연동 도구
    
    입력:
        components: List[Dict] - 검사할 부품 목록
    
    출력:
        Dict - 검증 결과 (통과/실패, 경고 메시지)
    """
```

### 3. AutoStepBuilderTool (Auto PC Builder Tool)

```python
class AutoStepBuilderTool(BaseTool):
    """
    Step-by-Step RAG 파이프라인 자동 실행 도구
    
    입력:
        budget: int - 총 예산
        purpose: str - 사용 목적
    
    출력:
        Dict - 완성된 PC 구성 (모든 부품 + 호환성 검증됨)
    """
```

---

## 외부 모듈 연동

### 연동 모듈 목록

```
추천 에이전트
    │
    ├── backend/data/price_prediction/     ← 가격 예측 데이터
    │   ├── price_history/                  (부품별 가격 이력)
    │   ├── exchange_rates.json             (환율 데이터)
    │   └── sale_events.json                (세일 이벤트)
    │
    ├── backend/data/compatibility/        ← 호환성 검사 데이터
    │   ├── cpu_socket_map.json             (CPU-소켓 매핑)
    │   ├── memory_compatibility.json       (메모리 호환성)
    │   ├── form_factor_map.json            (폼팩터 매핑)
    │   └── psu_requirements.json           (전력 요구량)
    │
    └── backend/data/recommendation/       ← 추천 엔진 데이터
        ├── component_nodes.json            (부품 노드 정보)
        ├── compatibility_edges.json        (호환성 엣지)
        ├── synergy_edges.json              (시너지 관계)
        └── popular_builds.json             (인기 조합)
```

### 통합 흐름

```
선택한 부품
    │
    ├─→ [가격 예측 모듈] → 가격 변동 예측치 반환
    │
    ├─→ [호환성 모듈] → 호환성 상태 (pass/fail/warning)
    │
    ├─→ [추천 엔진 모듈] → 시너지 기반 맞춤 추천 부품
    │
    └─→ [통합 결과] → ComponentSelector가 모든 정보 병합하여 반환
```

### 추천 에이전트 출력 예시

```python
{
    "components": [
        {
            "category": "GPU",
            "name": "RTX 4070",
            "price": 650000,
            "reason": "배그 울트라 설정 90fps 이상 가능",
            # 가격 예측 정보
            "price_prediction": {
                "trend": "하락",
                "predicted_price_30d": 620000,
                "recommendation": "2주 대기 권장"
            },
            # 호환성 정보
            "compatibility": {
                "status": "compatible",
                "power_required": 200,
                "length_mm": 240
            },
            # 시너지 정보 (추천엔진)
            "synergy": {
                "with_cpu": 0.95,
                "reason": "gaming_optimized"
            }
        }
    ]
}
```

---

## 데이터 모델

### 입력: UserRequest

```python
{
    "query": "150만원으로 배그 풀옵 가능한 PC 조립해줘",
    "budget": 1500000,
    "purpose": "gaming",
    "preferences": {
        "brand_preference": ["NVIDIA", "Intel"],
        "priority": "performance"
    }
}
```

### 출력: RecommendationResult

```python
{
    "status": "success",
    "recommendation": {
        "components": [
            {
                "category": "GPU",
                "name": "RTX 4070",
                "price": 650000,
                "reason": "배그 울트라 설정 90fps 이상 가능",
                "price_prediction": {...},   # 가격 예측 정보
                "compatibility": {...},      # 호환성 정보
                "synergy": {...}             # 시너지 정보
            }
        ],
        "total_price": 1450000,
        "compatibility_check": {
            "is_compatible": true,
            "warnings": []
        },
        "performance_estimate": {
            "pubg_ultra_fps": "90-100"
        }
    },
    "extracted_requirements": {
        "budget": 1500000,
        "purpose": "gaming"
    },
    "agent_logs": [...]
}
```

---

## 사용법

### 기본 사용

```python
from backend.modules.multi_agent import AgentOrchestrator

# 오케스트레이터 생성
orchestrator = AgentOrchestrator(
    llm_model="gemini-3-flash-preview",
    temperature=0.7
)

# 추천 요청
result = orchestrator.run({
    "query": "게임용 PC 추천해줘",
    "budget": 1500000,
    "purpose": "gaming"
})

print(f"상태: {result.status}")
print(f"총 가격: {result.total_price:,}원")
for comp in result.components:
    print(f"- {comp.category}: {comp.name} ({comp.price:,}원)")
```

---

## 구현 가이드

### 1단계: 의존성 설치

```bash
pip install crewai crewai-tools langchain-google-genai
```

### 2단계: 에이전트-모듈 연동

```python
# orchestrator.py 내 연동 예시
from backend.rag import PCComponentRetriever
from backend.modules.compatibility import CompatibilityEngine
from backend.data.recommendation import RecommendationEngine
from backend.data.price_prediction import PricePredictor

# ComponentSelectorAgent에 모든 모듈 주입
component_selector = ComponentSelectorAgent(
    retriever=PCComponentRetriever(),
    recommendation_engine=RecommendationEngine(),
    price_predictor=PricePredictor(),
    compatibility_engine=CompatibilityEngine()
)
```

---

## 테스트

### 테스트 실행

```bash
# 전체 테스트
pytest backend/tests/test_multi_agent.py -v

# 특정 테스트
pytest backend/tests/test_multi_agent.py::test_orchestrator_initialization -v
```

---

## TODO

### 필수 구현

- [x] CREWai 설치 및 기본 구조
- [x] 에이전트 클래스 정의
- [x] 도구(Tools) 정의
- [ ] 가격 예측 모듈 연동
- [ ] 추천 엔진 연동 (시너지 기반)
- [ ] 채팅 에이전트 ↔ 추천 에이전트 분리 구현

### 선택적 구현

- [ ] 병렬 처리 모드 구현
- [ ] 에이전트 간 피드백 루프 추가
- [ ] 사용자 피드백 반영 시스템

---

## 주의사항

1. **Rate Limit**: 여러 에이전트가 동시에 LLM API를 호출하면 Rate Limit에 걸릴 수 있음
2. **외부 모듈 의존성**: 추천 에이전트는 3개의 외부 모듈(가격예측, 호환성, 추천엔진)에 의존
3. **포맷 일관성**: 에이전트 간 데이터 전달 시 JSON 포맷 일관성 유지 필요

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-02 | 0.1.0 | 초기 스켈레톤 구현 |
| 2026-01-08 | 0.2.0 | 추천/채팅 에이전트 분리 구조 문서화, 외부 모듈(가격예측, 호환성, 추천엔진) 연동 구조 추가 |
