"""
CREWai 멀티 에이전트 오케스트레이터
=====================================

[목표]
------
CREWai 프레임워크를 활용하여 여러 전문 AI 에이전트가 협력적으로 
PC 부품 추천 작업을 수행하도록 조율하는 오케스트레이터.

[배경 지식]
----------
CREWai는 LangChain 기반의 멀티 에이전트 프레임워크로, 각 에이전트에게
특정 역할(Role)과 목표(Goal)를 부여하고, 에이전트들이 순차적 또는 
병렬적으로 작업을 수행하도록 조율함.

[아키텍처]
---------
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

[에이전트 구성]
--------------
1. RequirementAnalyzerAgent (요구사항 분석기)
   - 역할: 사용자 입력에서 핵심 요구사항 추출
   - 입력: 자연어 사용자 쿼리
   - 출력: 구조화된 요구사항 (예산, 목적, 선호도 등)

2. BudgetPlannerAgent (예산 분배 기획자)
   - 역할: 전체 예산을 부품 카테고리별로 최적 분배
   - 입력: 예산, 목적, 우선순위
   - 출력: 카테고리별 예산 할당

3. ComponentSelectorAgent (부품 선택기)
   - 역할: RAG를 활용해 최적 부품 후보 선정
   - 입력: 카테고리별 예산, 요구사항
   - 출력: 부품 후보 목록

4. CompatibilityCheckerAgent (호환성 검증기)
   - 역할: 선택된 부품 간 호환성 검증
   - 입력: 부품 후보 목록
   - 출력: 호환성 검증 결과

5. RecommendationWriterAgent (추천 결과 작성기)
   - 역할: 최종 추천 결과를 사용자 친화적으로 작성
   - 입력: 검증된 부품 목록
   - 출력: 포맷된 추천 결과

[구현 단계]
----------
1단계: CREWai 설치 및 기본 설정
2단계: 각 에이전트 정의 (역할, 목표, 도구)
3단계: Task 정의 (각 에이전트의 작업)
4단계: Crew 구성 및 실행 흐름 정의
5단계: 다른 모듈(RAG, 호환성, 추천)과 연동

[입력/출력 인터페이스]
-------------------
입력 (UserRequest):
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

출력 (RecommendationResult):
```python
{
    "status": "success",
    "recommendation": {
        "components": [...],  # 부품 목록
        "total_price": 1450000,
        "compatibility_check": {...},
        "performance_estimate": {...}
    },
    "agent_logs": [...]  # 각 에이전트 처리 로그
}
```

[참고 기술/라이브러리]
------------------
- CREWai: https://github.com/joaomdmoura/crewAI
- LangChain: https://www.langchain.com/
- Gemini API: LLM 백엔드로 사용
- Pydantic: 데이터 검증

[설치 방법]
----------
```bash
pip install crewai crewai-tools langchain-google-genai
```

[주의사항]
---------
- CREWai는 내부적으로 LangChain을 사용하므로 의존성 충돌 주의
- 여러 에이전트가 동시에 LLM API를 호출하면 Rate Limit 주의
- 각 에이전트의 결과는 다음 에이전트에게 전달되므로 포맷 일관성 유지

[테스트]
-------
backend/tests/test_multi_agent.py 참조
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from loguru import logger
from pydantic import BaseModel, Field
import json

# TODO: CREWai 설치 후 주석 해제
# from crewai import Agent, Task, Crew, Process
# from langchain_google_genai import ChatGoogleGenerativeAI


# ============================================================================
# 데이터 모델 정의
# ============================================================================

class UserRequest(BaseModel):
    """사용자 요청 모델"""
    query: str = Field(..., description="사용자의 자연어 쿼리")
    budget: Optional[int] = Field(None, description="예산 (원)")
    purpose: Optional[str] = Field(None, description="사용 목적 (gaming, work, etc.)")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 선호사항")


class ComponentRecommendation(BaseModel):
    """부품 추천 결과"""
    category: str = Field(..., description="부품 카테고리")
    name: str = Field(..., description="제품명")
    price: int = Field(..., description="가격")
    reason: str = Field(..., description="추천 이유")
    specs: Dict[str, Any] = Field(default_factory=dict, description="주요 스펙")


class RecommendationResult(BaseModel):
    """최종 추천 결과"""
    status: str = Field(..., description="처리 상태")
    components: List[ComponentRecommendation] = Field(default_factory=list)
    total_price: int = Field(0, description="총 가격")
    compatibility_check: Dict[str, Any] = Field(default_factory=dict)
    performance_estimate: Dict[str, Any] = Field(default_factory=dict)
    agent_logs: List[str] = Field(default_factory=list)


# ============================================================================
# 오케스트레이터 구현
# ============================================================================

class AgentOrchestrator:
    """
    멀티 에이전트 오케스트레이터
    
    여러 전문 AI 에이전트를 조율하여 최적의 PC 부품 추천을 생성함.
    
    사용법:
    ```python
    orchestrator = AgentOrchestrator()
    result = orchestrator.run({
        "query": "게임용 PC 추천해줘",
        "budget": 1500000
    })
    ```
    """
    
    def __init__(
        self,
        llm_model: str = "gemini-3-flash-preview",
        temperature: float = 0.7,
        verbose: bool = True,
    ):
        """
        Args:
            llm_model: 사용할 LLM 모델명
            temperature: LLM 생성 온도
            verbose: 상세 로깅 여부
        """
        self.llm_model = llm_model
        self.temperature = temperature
        self.verbose = verbose
        
        # TODO: 실제 구현 시 LLM 및 에이전트 초기화
        # self.llm = ChatGoogleGenerativeAI(model=llm_model, temperature=temperature)
        # self._init_agents()
        # self._init_crew()
        
        logger.info(f"AgentOrchestrator 초기화: model={llm_model}")
    
    def _init_agents(self):
        """
        각 전문 에이전트 초기화
        
        TODO: CREWai 설치 후 구현
        """
        # 예시 코드 (실제 구현 시 주석 해제):
        #
        # self.requirement_analyzer = Agent(
        #     role="요구사항 분석 전문가",
        #     goal="사용자의 PC 조립 요구사항을 정확하게 분석하고 구조화",
        #     backstory="당신은 10년 경력의 PC 조립 상담사입니다...",
        #     llm=self.llm,
        #     verbose=self.verbose
        # )
        #
        # self.budget_planner = Agent(
        #     role="예산 분배 전문가",
        #     goal="주어진 예산을 부품 카테고리별로 최적 분배",
        #     backstory="당신은 가성비 PC 조립의 달인입니다...",
        #     llm=self.llm,
        #     verbose=self.verbose
        # )
        pass
    
    def _init_crew(self):
        """
        Crew (작업 팀) 초기화
        
        TODO: CREWai 설치 후 구현
        """
        # 예시 코드:
        #
        # self.crew = Crew(
        #     agents=[
        #         self.requirement_analyzer,
        #         self.budget_planner,
        #         self.component_selector,
        #         self.compatibility_checker,
        #         self.recommendation_writer
        #     ],
        #     tasks=[...],
        #     process=Process.sequential,  # 순차 처리
        #     verbose=self.verbose
        # )
        pass
    
    def run(self, request: Dict[str, Any]) -> RecommendationResult:
        """
        멀티 에이전트 추천 파이프라인 실행
        
        Args:
            request: 사용자 요청 딕셔너리
            
        Returns:
            RecommendationResult: 추천 결과
            
        Raises:
            ValueError: 요청 형식이 잘못된 경우
            RuntimeError: 에이전트 처리 중 오류 발생
        """
        logger.info(f"멀티 에이전트 파이프라인 시작: {request.get('query', '')[:50]}...")
        
        # 요청 검증
        user_request = UserRequest(**request)
        
        # TODO: 실제 CREWai Crew 실행
        # result = self.crew.kickoff(inputs=request)
        
        # 임시 구현 (개발 중)
        result = self._placeholder_run(user_request)
        
        logger.info("멀티 에이전트 파이프라인 완료")
        return result
    
    def _placeholder_run(self, request: UserRequest) -> RecommendationResult:
        """
        임시 구현 - 실제 CREWai 연동 전 테스트용
        
        실제 구현 시 이 메서드를 Crew.kickoff()로 대체
        """
        return RecommendationResult(
            status="placeholder",
            components=[],
            total_price=0,
            agent_logs=[
                "AgentOrchestrator: 이 기능은 아직 구현 중입니다.",
                f"요청 쿼리: {request.query}",
                f"예산: {request.budget}원",
            ]
        )
    
    async def run_async(self, request: Dict[str, Any]) -> RecommendationResult:
        """
        비동기 멀티 에이전트 실행 (선택적 구현)
        
        대용량 요청이나 동시 처리가 필요한 경우 사용
        
        TODO: asyncio 기반 병렬 처리 구현
        """
        # 현재는 동기 버전 호출
        return self.run(request)


# ============================================================================
# 유틸리티 함수
# ============================================================================

def create_orchestrator(
    config: Optional[Dict[str, Any]] = None
) -> AgentOrchestrator:
    """
    오케스트레이터 팩토리 함수
    
    Args:
        config: 설정 딕셔너리 (선택)
        
    Returns:
        AgentOrchestrator 인스턴스
    """
    config = config or {}
    return AgentOrchestrator(
        llm_model=config.get("llm_model", "gemini-3-flash-preview"),
        temperature=config.get("temperature", 0.7),
        verbose=config.get("verbose", True),
    )


# ============================================================================
# 메인 (테스트용)
# ============================================================================

if __name__ == "__main__":
    # 간단한 테스트
    orchestrator = AgentOrchestrator()
    result = orchestrator.run({
        "query": "게임용 PC 추천해줘",
        "budget": 1500000,
        "purpose": "gaming"
    })
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
