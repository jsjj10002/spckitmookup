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
import os
import re

from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.rag.vector_store import PCComponentVectorStore
from backend.rag.retriever import PCComponentRetriever
from backend.modules.compatibility.engine import CompatibilityEngine
# 에이전트 클래스는 _init_agents()에서 지연 import (테스트 mock 호환성)
from backend.rag.config import GENERATION_MODEL


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
    


# ...

    def __init__(
        self,
        llm_model: str = GENERATION_MODEL,
        temperature: float = 0.7,
        verbose: bool = True,
    ):
        """
        Args:
            llm_model: 사용할 LLM 모델명 (기본값: config.GENERATION_MODEL)
            temperature: LLM 생성 온도
            verbose: 상세 로깅 여부
        """
        self.llm_model = llm_model
        self.temperature = temperature
        self.verbose = verbose
        
        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=llm_model, 
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

        # 의존성 모듈 초기화
        # 1. RAG Retrieve (Vector Store -> Retriever)
        self.vector_store = PCComponentVectorStore() 
        self.retriever = PCComponentRetriever(self.vector_store)

        # 2. Compatibility Engine
        self.compatibility_engine = CompatibilityEngine()

        # 에이전트 및 크루 초기화
        self._init_agents()
        self._init_crew()
        
        logger.info(f"AgentOrchestrator 초기화 완료: model={llm_model}")
    
    def _init_agents(self):
        """
        각 전문 에이전트 초기화
        """
        # 에이전트 클래스 지연 import (테스트 mock 호환성을 위해)
        from backend.modules.multi_agent.agents import (
            RequirementAnalyzerAgent,
            BudgetPlannerAgent,
            ComponentSelectorAgent,
            CompatibilityCheckerAgent,
            RecommendationWriterAgent
        )
        
        self.requirement_analyzer = RequirementAnalyzerAgent(
            llm=self.llm, 
            verbose=self.verbose
        )
        
        self.budget_planner = BudgetPlannerAgent(
            llm=self.llm, 
            verbose=self.verbose
        )
        
        self.component_selector = ComponentSelectorAgent(
            retriever=self.retriever,
            llm=self.llm, 
            verbose=self.verbose
        )
        
        self.compatibility_checker = CompatibilityCheckerAgent(
            compatibility_engine=self.compatibility_engine,
            llm=self.llm, 
            verbose=self.verbose
        )
        
        self.recommendation_writer = RecommendationWriterAgent(
            llm=self.llm, 
            verbose=self.verbose
        )
    
    def _init_crew(self):
        """
        Crew (작업 팀) 및 Task 초기화
        """
        # 1. 요구사항 분석 태스크
        task_analyze = Task(
            description="사용자의 요청({query})을 분석하여 예산(budget), 주용도(purpose), 선호사항(preferences)을 명확하게 추출하세요. "
                        "예산이 명시되지 않았다면 용도에 맞는 합리적인 예산을 추정하세요.",
            expected_output="JSON 형식의 요구사항 명세서 (budget, purpose, preferences 필드 포함)",
            agent=self.requirement_analyzer
        )

        # 2. 예산 분배 태스크
        task_budget = Task(
            description="이전 단계의 요구사항 분석 결과를 바탕으로, 총 예산을 CPU, GPU, Mainboard, Memory, SSD, Power, Case 등 "
                        "주요 카테고리별로 최적으로 분배하세요. 용도에 따라 가중치를 다르게 두어야 합니다.",
            expected_output="각 부품 카테고리별 할당 예산 금액과 그 비율이 포함된 예산 기획안",
            agent=self.budget_planner
        )

        # 3. 부품 선택 태스크
        task_select = Task(
            description="기획된 예산과 사용자의 요구사항을 바탕으로 'PC Component Search Tool'을 사용하여 실제 구매 가능한 최선의 부품들을 선정하세요. "
                        "각 카테고리(CPU, GPU, Mainboard, RAM, SSD, Power, Case)별로 하나씩 선정해야 합니다. "
                        "검색 결과가 없으면 유사한 가격대의 대안을 찾으세요.",
            expected_output="선정된 부품들의 상세 목록 (제품명, 가격, 스펙 포함)과 선정 이유",
            agent=self.component_selector
        )

        # 4. 호환성 검증 태스크
        task_check = Task(
            description="선정된 부품 목록을 'PC Compatibility Check Tool'을 사용하여 기술적으로 검증하세요. "
                        "CPU-메인보드 소켓, 램 규격, 파워 용량, 케이스 크기 등 모든 호환성을 확인해야 합니다. "
                        "문제가 있다면 구체적으로 지적하세요.",
            expected_output="호환성 검증 통과 여부 및 상세 검증 리포트",
            agent=self.compatibility_checker
        )

        # 5. 최종 견적서 작성 태스크
        task_write = Task(
            description="지금까지의 모든 과정(요구사항, 부품 선정, 호환성 검증)을 종합하여 사용자에게 전달할 최종 견적서를 작성하세요. "
                        "부품 리스트, 총 가격, 그리고 이 견적의 장점을 친절하게 설명하세요. "
                        "반드시 최종 결과는 JSON 포맷의 데이터와 함께 마크다운 설명이 포함되어야 합니다.",
            expected_output="사용자 친화적인 최종 PC 견적서 (JSON 데이터 블록 포함)",
            agent=self.recommendation_writer
        )

        # Crew 구성
        self.crew = Crew(
            agents=[
                self.requirement_analyzer,
                self.budget_planner,
                self.component_selector,
                self.compatibility_checker,
                self.recommendation_writer
            ],
            tasks=[task_analyze, task_budget, task_select, task_check, task_write],
            process=Process.sequential,
            verbose=self.verbose
        )
    
    def run(self, request: Dict[str, Any]) -> RecommendationResult:
        """
        멀티 에이전트 추천 파이프라인 실행
        
        Args:
            request: 사용자 요청 딕셔너리
            
        Returns:
            RecommendationResult: 추천 결과
        """
        logger.info(f"멀티 에이전트 파이프라인 시작: {request.get('query', '')[:50]}...")
        
        try:
            # 입력 데이터 준비
            inputs = {
                "query": request.get("query"),
                "budget": request.get("budget"),
                "purpose": request.get("purpose")
            }
            
            # CrewAI 실행
            crew_output = self.crew.kickoff(inputs=inputs)
            
            # 결과 파싱 및 반환
            return self._parse_crew_output(str(crew_output))

        except Exception as e:
            logger.error(f"파이프라인 실행 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return RecommendationResult(
                status="error",
                components=[],
                agent_logs=[f"Error: {str(e)}"]
            )

    def _parse_crew_output(self, output_text: str) -> RecommendationResult:
        """
        CrewAI의 텍스트 출력을 구조화된 결과로 변환
        """
        # JSON 블록 추출 시도
        try:
            # ```json ... ``` 패턴 찾기
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", output_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                
                # RecommendationResult 구조에 맞게 매핑
                return RecommendationResult(
                    status="success",
                    components=[
                        ComponentRecommendation(**comp) if isinstance(comp, dict) else comp 
                        for comp in data.get("components", []) 
                    ],
                    total_price=data.get("total_price", 0),
                    compatibility_check=data.get("compatibility_check", {}),
                    performance_estimate=data.get("performance_estimate", {}),
                    agent_logs=[output_text] 
                )
            else:
                # JSON을 못 찾은 경우 텍스트 전체 반환
                logger.warning("결과에서 JSON 블록을 찾지 못했습니다.")
                return RecommendationResult(
                    status="partial_success",
                    components=[],
                    agent_logs=[output_text]
                )
                
        except Exception as e:
            logger.error(f"결과 파싱 중 오류: {e}")
            return RecommendationResult(
                status="parsing_error",
                components=[],
                agent_logs=[f"Parsing Error: {str(e)}", output_text]
            )

    def _placeholder_run(self, request: UserRequest) -> RecommendationResult:
        """
        Deprecated: 실제 구현으로 대체됨
        """
        pass
    
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
