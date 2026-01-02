# Multi-Agent 모듈

> CREWai 프레임워크 기반 멀티 에이전트 PC 부품 추천 시스템

## 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [파일 구조](#파일-구조)
- [에이전트 구성](#에이전트-구성)
- [데이터 모델](#데이터-모델)
- [사용법](#사용법)
- [구현 가이드](#구현-가이드)
- [테스트](#테스트)
- [참고 자료](#참고-자료)

---

## 개요

### 목표

여러 전문 AI 에이전트가 협력적으로 PC 부품 추천 작업을 수행하도록 조율하는 오케스트레이터 시스템 구현.

### 배경

단일 LLM 호출로는 복잡한 PC 조립 추천의 모든 측면(요구사항 분석, 예산 분배, 부품 선택, 호환성 검증)을 동시에 처리하기 어렵다. 각 영역별 전문 에이전트를 두고 순차적/병렬적으로 협력하게 하면 더 정확하고 신뢰성 높은 추천이 가능하다.

### 핵심 기술

- **CREWai**: LangChain 기반 멀티 에이전트 프레임워크
- **Google Gemini API**: LLM 백엔드 (`gemini-3-pro-preview`, `gemini-3-flash-preview`)
- **Pydantic**: 데이터 검증 및 스키마 정의

---

## 아키텍처

```
사용자 요청
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    AgentOrchestrator                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Crew (작업 조율)                   │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │    │
│  │  │ 요구사항  │→│ 예산 분배 │→│   부품 선택기     │  │    │
│  │  │ 분석기   │  │   기획자  │  │                  │  │    │
│  │  └──────────┘  └──────────┘  └────────┬─────────┘  │    │
│  │                                        │            │    │
│  │                                        ▼            │    │
│  │  ┌──────────────────┐  ┌──────────────────────┐   │    │
│  │  │  추천 결과 작성기 │←│   호환성 검증기      │   │    │
│  │  └──────────────────┘  └──────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
최종 추천 결과
```

### 처리 흐름

1. **요구사항 분석** → 사용자 쿼리에서 예산, 목적, 선호도 추출
2. **예산 분배** → 목적에 맞게 카테고리별 예산 할당
3. **부품 선택** → RAG 시스템으로 최적 부품 후보 선정
4. **호환성 검증** → 선택된 부품 간 호환성 확인
5. **결과 작성** → 사용자 친화적 추천 결과 생성

---

## 파일 구조

```
multi_agent/
├── __init__.py          # 모듈 초기화 및 exports
├── orchestrator.py      # 메인 오케스트레이터 클래스
├── agents.py            # 개별 에이전트 정의
└── README.md            # 이 문서
```

### 파일별 역할

| 파일 | 역할 | 주요 클래스/함수 |
|------|------|------------------|
| `orchestrator.py` | 에이전트 조율 및 파이프라인 관리 | `AgentOrchestrator`, `UserRequest`, `RecommendationResult` |
| `agents.py` | 개별 전문 에이전트 정의 | `RequirementAnalyzerAgent`, `BudgetPlannerAgent`, `ComponentSelectorAgent`, `CompatibilityCheckerAgent`, `RecommendationWriterAgent` |

---

## 에이전트 구성

### 1. RequirementAnalyzerAgent (요구사항 분석기)

| 항목 | 내용 |
|------|------|
| **역할** | 사용자 입력에서 핵심 요구사항 추출 |
| **입력** | 자연어 사용자 쿼리 |
| **출력** | 구조화된 요구사항 (예산, 목적, 선호도 등) |

**분석 항목:**
- 예산 추출 (명시적/암시적)
- 사용 목적 분류 (게임/업무/영상편집/개발 등)
- 성능 티어 판단 (entry/mid/high/enthusiast)
- 추가 선호사항 (소음, RGB, 크기 등)

### 2. BudgetPlannerAgent (예산 분배 기획자)

| 항목 | 내용 |
|------|------|
| **역할** | 전체 예산을 부품 카테고리별로 최적 분배 |
| **입력** | 예산, 목적, 우선순위 |
| **출력** | 카테고리별 예산 할당 |

**예산 분배 템플릿 (게임용 PC):**

| 카테고리 | 비율 |
|----------|------|
| GPU | 35-40% |
| CPU | 20-25% |
| 메인보드 | 8-12% |
| 메모리 | 8-10% |
| 저장장치 | 10-12% |
| PSU | 5-8% |
| 케이스 | 5-8% |

### 3. ComponentSelectorAgent (부품 선택기)

| 항목 | 내용 |
|------|------|
| **역할** | RAG를 활용해 최적 부품 후보 선정 |
| **입력** | 카테고리별 예산, 요구사항 |
| **출력** | 부품 후보 목록 |
| **의존성** | `backend/rag/retriever.py` |

### 4. CompatibilityCheckerAgent (호환성 검증기)

| 항목 | 내용 |
|------|------|
| **역할** | 선택된 부품 간 호환성 검증 |
| **입력** | 부품 후보 목록 |
| **출력** | 호환성 검증 결과 |
| **의존성** | `backend/modules/compatibility/engine.py` |

### 5. RecommendationWriterAgent (추천 결과 작성기)

| 항목 | 내용 |
|------|------|
| **역할** | 최종 추천 결과를 사용자 친화적으로 작성 |
| **입력** | 검증된 부품 목록 |
| **출력** | 포맷된 추천 결과 |

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
                "reason": "배그 울트라 설정 90fps 이상 가능"
            },
            # ...
        ],
        "total_price": 1450000,
        "compatibility_check": {
            "is_compatible": True,
            "warnings": []
        },
        "performance_estimate": {
            "pubg_ultra_fps": "90-100"
        }
    },
    "agent_logs": [...]  # 각 에이전트 처리 로그
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

### 팩토리 함수 사용

```python
from backend.modules.multi_agent import create_orchestrator

orchestrator = create_orchestrator({
    "llm_model": "gemini-3-pro-preview",
    "temperature": 0.5,
    "verbose": True
})
```

### 비동기 실행

```python
import asyncio
from backend.modules.multi_agent import AgentOrchestrator

async def main():
    orchestrator = AgentOrchestrator()
    result = await orchestrator.run_async({
        "query": "영상편집용 PC",
        "budget": 2000000
    })
    return result

result = asyncio.run(main())
```

---

## 구현 가이드

### 1단계: CREWai 설치 및 기본 설정

```bash
pip install crewai crewai-tools langchain-google-genai
```

### 2단계: 각 에이전트 정의

`agents.py`에서 각 에이전트의 역할(role), 목표(goal), 배경 스토리(backstory)를 정의한다.

```python
from crewai import Agent

requirement_analyzer = Agent(
    role="PC 조립 요구사항 분석 전문가",
    goal="사용자의 자연어 요청에서 핵심 요구사항을 정확하게 추출",
    backstory="당신은 10년 경력의 PC 조립 상담 전문가입니다...",
    llm=llm,
    verbose=True
)
```

### 3단계: Task 정의

각 에이전트가 수행할 작업(Task)을 정의한다.

```python
from crewai import Task

analyze_task = Task(
    description="사용자 쿼리: {query}\n\n"
                "위 요청에서 예산, 목적, 선호사항을 추출하세요.",
    agent=requirement_analyzer,
    expected_output="JSON 형식의 구조화된 요구사항"
)
```

### 4단계: Crew 구성 및 실행

```python
from crewai import Crew, Process

crew = Crew(
    agents=[
        requirement_analyzer,
        budget_planner,
        component_selector,
        compatibility_checker,
        recommendation_writer
    ],
    tasks=[
        analyze_task,
        budget_task,
        select_task,
        check_task,
        write_task
    ],
    process=Process.sequential,  # 순차 처리
    verbose=True
)

result = crew.kickoff(inputs={"query": user_query})
```

### 5단계: 다른 모듈 연동

```python
# RAG 시스템 연동
from backend.rag import PCComponentRetriever

# 호환성 검사 연동
from backend.modules.compatibility import CompatibilityEngine
```

---

## 테스트

### 테스트 파일 위치

```
backend/tests/test_multi_agent.py
```

### 테스트 실행

```bash
# 전체 테스트
pytest backend/tests/test_multi_agent.py -v

# 특정 테스트
pytest backend/tests/test_multi_agent.py::test_orchestrator_initialization -v
```

### 테스트 항목

1. **오케스트레이터 초기화 테스트**
   - 기본 설정 확인
   - 커스텀 설정 확인

2. **요청 검증 테스트**
   - 유효한 요청 처리
   - 잘못된 요청 에러 처리

3. **에이전트 개별 테스트**
   - 요구사항 분석기 테스트
   - 예산 분배 기획자 테스트

---

## TODO

### 필수 구현

- [ ] CREWai 설치 및 의존성 정리
- [ ] 각 에이전트의 실제 LLM 연동
- [ ] Task 정의 및 프롬프트 최적화
- [ ] RAG 시스템 연동 (ComponentSelectorAgent)
- [ ] 호환성 검사 연동 (CompatibilityCheckerAgent)

### 선택적 구현

- [ ] 병렬 처리 모드 구현
- [ ] 에이전트 간 피드백 루프 추가
- [ ] 사용자 피드백 반영 시스템
- [ ] 에이전트 로그 시각화

---

## 주의사항

1. **Rate Limit**: 여러 에이전트가 동시에 LLM API를 호출하면 Rate Limit에 걸릴 수 있음
2. **의존성 충돌**: CREWai는 내부적으로 LangChain을 사용하므로 버전 충돌 주의
3. **포맷 일관성**: 에이전트 간 데이터 전달 시 JSON 포맷 일관성 유지 필요

---

## 참고 자료

- [CREWai 공식 문서](https://docs.crewai.com/)
- [CREWai GitHub](https://github.com/joaomdmoura/crewAI)
- [LangChain Google Gemini](https://python.langchain.com/docs/integrations/llms/google_ai)
- [Pydantic 문서](https://docs.pydantic.dev/)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-02 | 0.1.0 | 초기 스켈레톤 구현 |
