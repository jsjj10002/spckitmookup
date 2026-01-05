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
        "role": "PC 조립 요구사항 분석 전문가",
        "goal": "사용자의 자연어 요청에서 예산, 용도, 선호도 등 핵심 요구사항을 정확하게 추출",
        "backstory": """
당신은 10년 경력의 PC 조립 상담 전문가입니다. 
수천 명의 고객을 상담하며 다양한 요구사항을 분석해왔습니다.
고객이 "배그 풀옵 가능한 컴퓨터"라고 말하면, 이것이 최소 RTX 4060 이상의 
그래픽카드와 충분한 RAM이 필요하다는 것을 즉시 파악합니다.
모호한 요청도 명확한 스펙으로 변환하는 것이 당신의 특기입니다.
하지만, 예산이나 주용도가 전혀 유추되지 않는 경우에는 억지로 값을 채우지 말고 missing_info 필드에 해당 항목을 명시해야 합니다.
항상 한국어로 응답하며, 결과는 반드시 명확한 JSON 또는 구조화된 형식으로 도출해야 합니다.
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
