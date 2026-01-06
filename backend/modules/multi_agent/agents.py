"""
CREWai 에이전트 정의
====================

[목표]
------
각 전문 영역을 담당하는 AI 에이전트 클래스 정의.
CREWai의 Agent를 상속받아 PC 추천 특화 에이전트 구현.

[에이전트 목록]
--------------
1. RequirementAnalyzerAgent - 요구사항 분석
2. BudgetPlannerAgent - 예산 분배
3. ComponentSelectorAgent - 부품 선택
4. CompatibilityCheckerAgent - 호환성 검증
5. RecommendationWriterAgent - 추천 결과 작성

[구현 가이드]
-----------
각 에이전트는 다음 요소를 정의해야 함:
- role: 에이전트의 역할 설명
- goal: 에이전트의 목표
- backstory: 에이전트의 배경 스토리 (성격/전문성 부여)
- tools: 사용 가능한 도구 목록
- llm: 사용할 LLM 모델

[참고 자료]
----------
- CREWai Agent 문서: https://docs.crewai.com/core-concepts/Agents/
- LangChain Tools: https://python.langchain.com/docs/modules/tools/
"""

from typing import List, Dict, Any, Optional, ClassVar
from dataclasses import dataclass
from loguru import logger
import os

from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

# 도구 임포트
from backend.modules.multi_agent.tools import SearchPartsTool, CompatibilityCheckTool, AutoStepBuilderTool
from backend.rag.config import GENERATION_MODEL

# ============================================================================
# 에이전트 설정 상수
# ============================================================================

AGENT_CONFIGS = {
    "requirement_analyzer": {
        "role": "spckitAI PC 견적 도우미",
        "goal": "사용자의 요청에서 '예산(budget)'과 '용도(purpose)'를 파악하여 견적 단계를 시작하는 것",
        "backstory": """
당신은 PC 부품 견적을 돕는 AI 서비스 'spckitAI'입니다.
신속하고 정확하게 견적을 시작하는 것이 목표입니다.

[상담 원칙]
1.  **필수 정보('예산', '용도') 확인**:
    - **둘 다 확인됨**: 추가 질문 금지. 디자인/저장공간 등은 용도에 맞춰 **자동 판단(지레짐작)**하고, 바로 견적을 시작합니다. ('missing_info' 빈배열 반환)
    - **하나라도 누락됨**: **누락된 필수 항목**과 **선택 항목(디자인, 저장공간 등)**을 묶어서, **현재 상황에 맞는 동적인 질문 리스트**를 생성합니다.

2.  **동적 질문 리스트 생성 규칙 (정보 누락 시)**:
    - **초보자 친화적 질문 (쉬운 말로 풀어서)**: '저장공간', '케이스 디자인' 같은 딱딱한 용어 대신, 누구나 쉽게 이해하고 고를 수 있는 질문을 던지세요.
    - **절대 고정된 템플릿을 쓰지 마십시오.** 사용자가 이미 말한 내용은 제외합니다.
    
    - **질문 예시 가이드**:
      - **저장공간**: "사진이나 동영상을 많이 저장하시나요? (기본/대용량 중 선택)"
      - **디자인**: "불빛이 번쩍이는 화려한 게 좋으신가요, 아니면 깔끔하고 심플한 게 좋으신가요?"
      - **예산**: "생각해두신 최대 예산은 얼마 정도인가요?"

3.  **범위 제한**: 견적 범위는 오직 '본체(Tower)'입니다. 모니터, OS 등은 묻지 않습니다.
4.  **인사 생략**: 불필요한 인사는 생략하고 핵심만 말합니다.

[출력 예시]
- 정보 누락(게임용만 언급):
  {"budget": null, "purpose": "gaming", "missing_info": ["budget"], "message": "게임용 PC시군요. 더 정확한 견적을 위해 몇 가지만 골라주세요.\n1. 최대 예산이 어떻게 되시나요? (필수)\n2. 화려한 LED vs 깔끔한 디자인 중 선호하시는 스타일은?\n3. 사진/영상을 많이 저장하시나요?"}
- 정보 완비:
  {"budget": 2000000, "purpose": "gaming", "missing_info": [], "message": "200만원대 고사양 게이밍 PC 견적을 시작하겠습니다."}
        """,
    },
    "budget_planner": {
        "role": "PC 부품 예산 분배 전문가",
        "goal": "주어진 총 예산을 각 부품 카테고리에 최적으로 분배하여 가성비를 극대화",
        "backstory": """
당신은 컴퓨터 부품 시장을 15년간 분석해온 가격 전문가입니다.
어떤 예산이든 최고의 성능을 뽑아내는 분배 비율을 알고 있습니다.
게임용 PC는 GPU에 35-40%, 업무용 PC는 CPU에 30% 투자해야 한다는 것을
경험으로 체득했습니다. 가성비의 달인으로 불립니다.
항상 한국어로 응답합니다.
        """,
    },
    "component_selector": {
        "role": "PC 부품 선택 전문가",
        "goal": "주어진 예산과 요구사항, 검색 도구를 활용해 최적의 부품을 데이터베이스에서 선택",
        "backstory": """
당신은 PC 부품 리뷰어 겸 조립 기술자입니다.
모든 CPU, GPU, 메모리, SSD의 벤치마크 점수를 외우고 있으며,
실제 성능과 스펙 차이를 정확히 알고 있습니다.
제공된 'PC Component Search Tool'을 적극적으로 사용하여 최신 가격과 재고를 확인하고 추천합니다.
자신의 지식보다는 도구 검색 결과를 우선시합니다.
항상 한국어로 응답합니다.
        """,
    },
    "compatibility_checker": {
        "role": "PC 부품 호환성 검증 전문가",
        "goal": "선택된 부품들 간의 호환성을 도구를 통해 철저히 검증하여 조립 문제 방지",
        "backstory": """
당신은 PC 조립 공방의 기술 책임자입니다.
'PC Compatibility Check Tool'을 사용하여 선택된 부품 리스트의 호환성을 검증합니다.
소켓, 메모리 규격, 파워 용량, 케이스 크기 등 모든 면밀히 체크합니다.
문제가 발견되면 구체적으로 경고하고 대안을 제시합니다.
항상 한국어로 응답합니다.
        """,
    },
    "recommendation_writer": {
        "role": "PC 추천 결과 작성 전문가",
        "goal": "기술 정보와 부품 목록을 종합하여 사용자 친화적인 최종 견적서를 작성",
        "backstory": """
당신은 IT 전문 기자 겸 테크 유튜버입니다.
복잡한 기술 용어를 누구나 이해할 수 있게 설명하는 재능이 있습니다.
추천하는 부품의 장점과 단점을 균형있게 전달하며, "왜 이 부품인가"를 명확하게 설명합니다.
최종 결과는 깔끔하게 정리된 JSON 데이터와 함께 친절한 설명을 포함해야 합니다.
항상 한국어로 응답합니다.
        """,
    },
}


# ============================================================================
# 전문 에이전트 클래스
# ============================================================================

class RequirementAnalyzerAgent(Agent):
    """
    요구사항 분석 에이전트
    """
    def __init__(self, llm=None, verbose: bool = True):
        config = AGENT_CONFIGS["requirement_analyzer"]
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[],
            llm=llm,
            verbose=verbose,
            allow_delegation=False,
        )
    
    def analyze(self, query: str) -> str:
        """
        단독 실행 메서드 (테스트용)
        """
        task = Task(
            description=f"다음 사용자 요청을 분석하여 예산, 주용도, 선호사항을 추출하세요.\n요청: {query}",
            expected_output="JSON 형식의 요구사항 분석 결과 (budget, purpose, preferences 포함)",
            agent=self
        )
        crew = Crew(agents=[self], tasks=[task], verbose=self.verbose)
        return crew.kickoff()


class BudgetPlannerAgent(Agent):
    """
    예산 분배 에이전트
    """
    # 목적별 기본 분배 비율 (참고용 속성)
    BUDGET_TEMPLATES: ClassVar[Dict[str, Dict[str, float]]] = {
        "gaming": {"gpu": 0.37, "cpu": 0.23, "motherboard": 0.10, "memory": 0.09, "storage": 0.11, "psu": 0.05, "case": 0.05},
        "workstation": {"cpu": 0.32, "gpu": 0.18, "motherboard": 0.12, "memory": 0.18, "storage": 0.12, "psu": 0.05, "case": 0.03},
        "general": {"cpu": 0.25, "gpu": 0.25, "motherboard": 0.10, "memory": 0.12, "storage": 0.15, "psu": 0.07, "case": 0.06},
    }
    
    def __init__(self, llm=None, verbose: bool = True):
        config = AGENT_CONFIGS["budget_planner"]
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[],
            llm=llm,
            verbose=verbose,
            allow_delegation=False,
        )
    
    def plan(self, total_budget: int, purpose: str = "general") -> str:
        """
        단독 실행 메서드 (테스트용)
        """
        task = Task(
            description=f"총 예산 {total_budget}원, 목적 '{purpose}'에 맞춰 부품별 예산을 분배하세요. CPU, GPU, 메인보드, 메모리, SSD, 파워, 케이스 카테고리별로 금액을 산정하세요.",
            expected_output="각 부품 카테고리별 할당 예산과 근거가 포함된 보고서",
            agent=self
        )
        crew = Crew(agents=[self], tasks=[task], verbose=self.verbose)
        return crew.kickoff()


class ComponentSelectorAgent(Agent):
    """
    부품 선택 에이전트
    """
    def __init__(self, retriever=None, step_pipeline=None, llm=None, verbose: bool = True):
        config = AGENT_CONFIGS["component_selector"]
        
        # 도구 설정
        agent_tools = []
        if retriever:
            search_tool = SearchPartsTool(retriever=retriever)
            agent_tools.append(search_tool)
        
        if step_pipeline:
            auto_tool = AutoStepBuilderTool(pipeline=step_pipeline)
            agent_tools.append(auto_tool)
            
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=agent_tools,
            llm=llm,
            verbose=verbose,
            allow_delegation=False,
        )
    
    def select(self, category: str, budget: int, requirements: Optional[Dict[str, Any]] = None) -> str:
        """
        단독 실행 메서드 (테스트용)
        """
        req_str = f", 요구사항: {requirements}" if requirements else ""
        task = Task(
            description=f"{category} 부품을 찾고 있습니다. 예산은 {budget}원입니다.{req_str} PC Component Search Tool을 사용하여 최적의 부품을 찾아주세요.",
            expected_output="선택된 부품의 상세 정보(제품명, 가격, 스펙)와 선택 이유",
            agent=self
        )
        crew = Crew(agents=[self], tasks=[task], verbose=self.verbose)
        return crew.kickoff()


class CompatibilityCheckerAgent(Agent):
    """
    호환성 검증 에이전트
    """
    def __init__(self, compatibility_engine=None, llm=None, verbose: bool = True):
        config = AGENT_CONFIGS["compatibility_checker"]
        
        # 도구 설정
        agent_tools = []
        if compatibility_engine:
            check_tool = CompatibilityCheckTool(engine=compatibility_engine)
            agent_tools.append(check_tool)
            
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=agent_tools,
            llm=llm,
            verbose=verbose,
            allow_delegation=False,
        )
    
    def check(self, components: List[Dict[str, Any]]) -> str:
        """
        단독 실행 메서드 (테스트용)
        """
        task = Task(
            description=f"다음 부품 목록의 호환성을 검증하세요: {components}",
            expected_output="호환성 검증 결과 보고서 (문제점 및 해결 방안 포함)",
            agent=self
        )
        crew = Crew(agents=[self], tasks=[task], verbose=self.verbose)
        return crew.kickoff()


class RecommendationWriterAgent(Agent):
    """
    추천 결과 작성 에이전트
    """
    def __init__(self, llm=None, verbose: bool = True):
        config = AGENT_CONFIGS["recommendation_writer"]
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[],
            llm=llm,
            verbose=verbose,
            allow_delegation=False,
        )
    
    def write(self, components: List[Dict[str, Any]], user_request: Dict[str, Any]) -> str:
        """
        단독 실행 메서드 (테스트용)
        """
        task = Task(
            description=f"사용자 요청({user_request})에 따라 선정된 다음 부품 목록({components})을 바탕으로 최종 견적서를 작성하세요.",
            expected_output="사용자에게 전달할 최종 PC 견적서 (마크다운 포맷)",
            agent=self
        )
        crew = Crew(agents=[self], tasks=[task], verbose=self.verbose)
        return crew.kickoff()


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    # 테스트를 위한 Mock LLM 설정 (API Key 필요)
    # 실제 실행 시에는 환경 변수 설정 필요
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model=GENERATION_MODEL)
        
        analyzer = RequirementAnalyzerAgent(llm=llm)
        print("Analysis Agent created.")
        
        # result = analyzer.analyze("150만원으로 배그 풀옵 가능한 PC 만들어줘")
        # print(f"분석 결과: {result}")
        
    except Exception as e:
        print(f"테스트 실행 중 오류: {e}")
        print("API Key가 설정되어 있는지 확인하세요.")
