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

[주의사항]
---------
- 각 에이전트의 backstory는 한글로 작성 (한국어 응답 유도)
- tool은 실제 구현된 함수만 연결
- verbose=True로 설정하면 디버깅 용이
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

# TODO: CREWai 설치 후 주석 해제
# from crewai import Agent
# from crewai_tools import BaseTool


# ============================================================================
# 에이전트 설정 상수
# ============================================================================

AGENT_CONFIGS = {
    "requirement_analyzer": {
        "role": "PC 조립 요구사항 분석 전문가",
        "goal": "사용자의 자연어 요청에서 핵심 요구사항을 정확하게 추출하고 구조화하여 다른 에이전트가 활용할 수 있도록 함",
        "backstory": """
당신은 10년 경력의 PC 조립 상담 전문가입니다. 
수천 명의 고객을 상담하며 다양한 요구사항을 분석해왔습니다.
고객이 "배그 풀옵 가능한 컴퓨터"라고 말하면, 이것이 최소 RTX 4060 이상의 
그래픽카드와 충분한 RAM이 필요하다는 것을 즉시 파악합니다.
모호한 요청도 명확한 스펙으로 변환하는 것이 당신의 특기입니다.
항상 한국어로 응답합니다.
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
        "goal": "주어진 예산과 요구사항에 맞는 최적의 부품을 데이터베이스에서 선택",
        "backstory": """
당신은 PC 부품 리뷰어 겸 조립 기술자입니다.
모든 CPU, GPU, 메모리, SSD의 벤치마크 점수를 외우고 있으며,
실제 성능과 스펙 차이를 정확히 알고 있습니다.
"스펙시트 상 좋아 보이지만 실제로는..."이라는 말을 자주 합니다.
검색 도구를 활용해 최신 부품 정보를 찾아내는 것이 특기입니다.
항상 한국어로 응답합니다.
        """,
    },
    "compatibility_checker": {
        "role": "PC 부품 호환성 검증 전문가",
        "goal": "선택된 부품들 간의 호환성을 철저히 검증하여 조립 문제 방지",
        "backstory": """
당신은 PC 조립 공방의 기술 책임자입니다.
CPU 소켓, 메모리 세대, 전원 커넥터, 케이스 규격 등
모든 호환성 이슈를 경험으로 알고 있습니다.
"이 CPU는 이 메인보드와 맞지 않습니다"라고 말하면 100% 정확합니다.
고객이 부품을 잘못 구매해 낭패를 보는 것을 막는 것이 사명입니다.
항상 한국어로 응답합니다.
        """,
    },
    "recommendation_writer": {
        "role": "PC 추천 결과 작성 전문가",
        "goal": "기술 정보를 사용자 친화적인 추천 결과로 변환하여 전달",
        "backstory": """
당신은 IT 전문 기자 겸 테크 유튜버입니다.
복잡한 기술 용어를 누구나 이해할 수 있게 설명하는 재능이 있습니다.
추천하는 부품의 장점과 단점을 균형있게 전달하며,
"왜 이 부품인가"를 명확하게 설명합니다.
독자/시청자가 자신감을 갖고 구매 결정을 내릴 수 있도록 돕습니다.
항상 한국어로 응답합니다.
        """,
    },
}


# ============================================================================
# 기본 에이전트 클래스 (CREWai Agent 래퍼)
# ============================================================================

class BaseAgent:
    """
    기본 에이전트 클래스
    
    CREWai Agent를 래핑하여 공통 기능 제공.
    실제 구현 시 crewai.Agent를 상속.
    
    TODO: CREWai 설치 후 Agent 상속으로 변경
    """
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[Any]] = None,
        verbose: bool = True,
    ):
        """
        Args:
            role: 에이전트 역할
            goal: 에이전트 목표
            backstory: 에이전트 배경 스토리
            tools: 사용 가능한 도구 목록
            verbose: 상세 로깅 여부
        """
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.verbose = verbose
        
        logger.info(f"Agent 초기화: {role}")
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        작업 실행 (placeholder)
        
        TODO: CREWai 연동 시 실제 구현
        """
        logger.info(f"[{self.role}] 작업 실행: {task[:50]}...")
        return {"status": "placeholder", "message": "구현 예정"}


# ============================================================================
# 전문 에이전트 클래스
# ============================================================================

class RequirementAnalyzerAgent(BaseAgent):
    """
    요구사항 분석 에이전트
    
    [역할]
    사용자의 자연어 요청을 분석하여 구조화된 요구사항으로 변환.
    
    [입력 예시]
    "150만원으로 배그 풀옵 가능한 PC 만들어줘, 조용한 게 좋아"
    
    [출력 예시]
    {
        "budget": 1500000,
        "purpose": "gaming",
        "target_games": ["PUBG"],
        "performance_tier": "high",
        "preferences": {
            "noise_level": "quiet",
            "aesthetics": null
        }
    }
    
    [분석 항목]
    - 예산 추출 (명시적/암시적)
    - 사용 목적 분류 (게임/업무/영상편집/개발 등)
    - 성능 티어 판단 (entry/mid/high/enthusiast)
    - 추가 선호사항 (소음, RGB, 크기 등)
    """
    
    def __init__(self, verbose: bool = True):
        config = AGENT_CONFIGS["requirement_analyzer"]
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[],  # TODO: 요구사항 파싱 도구 추가
            verbose=verbose,
        )
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """
        사용자 쿼리 분석
        
        Args:
            query: 사용자 자연어 쿼리
            
        Returns:
            구조화된 요구사항 딕셔너리
        """
        logger.info(f"요구사항 분석 중: {query[:50]}...")
        
        # TODO: LLM을 활용한 실제 분석 구현
        # 현재는 placeholder 반환
        return {
            "budget": None,
            "purpose": "general",
            "performance_tier": "mid",
            "preferences": {},
            "raw_query": query,
        }


class BudgetPlannerAgent(BaseAgent):
    """
    예산 분배 에이전트
    
    [역할]
    총 예산을 각 부품 카테고리에 최적 비율로 분배.
    
    [예산 분배 가이드라인]
    
    게임용 PC (Gaming):
    - GPU: 35-40%
    - CPU: 20-25%
    - 메인보드: 8-12%
    - 메모리: 8-10%
    - 저장장치: 10-12%
    - PSU: 5-8%
    - 케이스: 5-8%
    - 쿨러: 3-5%
    
    업무용 PC (Workstation):
    - CPU: 30-35%
    - GPU: 15-20%
    - 메인보드: 10-15%
    - 메모리: 15-20%
    - 저장장치: 12-15%
    - PSU: 5-8%
    - 케이스: 3-5%
    - 쿨러: 3-5%
    
    [입력]
    {
        "total_budget": 1500000,
        "purpose": "gaming",
        "priority": "performance"  # or "balanced", "quiet"
    }
    
    [출력]
    {
        "allocations": {
            "gpu": {"budget": 550000, "ratio": 0.37},
            "cpu": {"budget": 350000, "ratio": 0.23},
            ...
        },
        "reasoning": "게임용 PC이므로 GPU에 37% 할당..."
    }
    """
    
    # 목적별 기본 분배 비율
    BUDGET_TEMPLATES = {
        "gaming": {
            "gpu": 0.37,
            "cpu": 0.23,
            "motherboard": 0.10,
            "memory": 0.09,
            "storage": 0.11,
            "psu": 0.05,
            "case": 0.05,
        },
        "workstation": {
            "cpu": 0.32,
            "gpu": 0.18,
            "motherboard": 0.12,
            "memory": 0.18,
            "storage": 0.12,
            "psu": 0.05,
            "case": 0.03,
        },
        "general": {
            "cpu": 0.25,
            "gpu": 0.25,
            "motherboard": 0.10,
            "memory": 0.12,
            "storage": 0.15,
            "psu": 0.07,
            "case": 0.06,
        },
    }
    
    def __init__(self, verbose: bool = True):
        config = AGENT_CONFIGS["budget_planner"]
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[],
            verbose=verbose,
        )
    
    def plan(
        self,
        total_budget: int,
        purpose: str = "general",
        adjustments: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        예산 분배 계획 수립
        
        Args:
            total_budget: 총 예산 (원)
            purpose: 사용 목적
            adjustments: 비율 조정값 (선택)
            
        Returns:
            예산 분배 결과
        """
        logger.info(f"예산 분배 중: {total_budget:,}원, 목적: {purpose}")
        
        # 기본 템플릿 선택
        template = self.BUDGET_TEMPLATES.get(purpose, self.BUDGET_TEMPLATES["general"])
        
        # 조정값 적용
        if adjustments:
            template = {**template, **adjustments}
        
        # 예산 계산
        allocations = {}
        for category, ratio in template.items():
            allocations[category] = {
                "budget": int(total_budget * ratio),
                "ratio": ratio,
            }
        
        return {
            "total_budget": total_budget,
            "purpose": purpose,
            "allocations": allocations,
            "reasoning": f"{purpose}용 PC이므로 해당 목적에 최적화된 비율로 분배",
        }


class ComponentSelectorAgent(BaseAgent):
    """
    부품 선택 에이전트
    
    [역할]
    RAG 시스템을 활용하여 각 카테고리별 최적 부품 선택.
    
    [선택 기준]
    1. 예산 적합성: 할당 예산 내에서 최고 성능
    2. 브랜드 신뢰도: 검증된 제조사 우선
    3. 사용자 평가: 리뷰/평점 고려
    4. 가용성: 현재 구매 가능한 제품
    
    [RAG 연동]
    backend/rag/retriever.py의 PCComponentRetriever를 도구로 사용.
    
    [입력]
    {
        "category": "gpu",
        "budget": 550000,
        "requirements": {
            "min_vram": "8GB",
            "brand_preference": ["NVIDIA"]
        }
    }
    
    [출력]
    {
        "selected": {
            "name": "RTX 4060 Ti",
            "price": 520000,
            "specs": {...}
        },
        "alternatives": [...],
        "reasoning": "예산 내 최고 성능의 그래픽카드..."
    }
    """
    
    def __init__(self, retriever=None, verbose: bool = True):
        """
        Args:
            retriever: PCComponentRetriever 인스턴스 (RAG 검색용)
            verbose: 상세 로깅 여부
        """
        config = AGENT_CONFIGS["component_selector"]
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[],  # TODO: RAG 검색 도구 연결
            verbose=verbose,
        )
        self.retriever = retriever
    
    def select(
        self,
        category: str,
        budget: int,
        requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        부품 선택
        
        Args:
            category: 부품 카테고리
            budget: 할당 예산
            requirements: 추가 요구사항
            
        Returns:
            선택 결과
        """
        logger.info(f"부품 선택 중: {category}, 예산: {budget:,}원")
        
        # TODO: RAG retriever 연동
        if self.retriever:
            # results = self.retriever.retrieve(query=f"{category} {budget}원", top_k=5)
            pass
        
        # Placeholder 반환
        return {
            "category": category,
            "selected": None,
            "alternatives": [],
            "reasoning": "RAG 시스템 연동 후 구현 예정",
        }


class CompatibilityCheckerAgent(BaseAgent):
    """
    호환성 검증 에이전트
    
    [역할]
    선택된 부품들 간의 호환성을 검증.
    
    [검증 항목]
    1. CPU-메인보드 소켓 호환성
    2. 메모리 세대/속도 호환성
    3. GPU 슬롯 및 전원 호환성
    4. 케이스-메인보드 폼팩터 호환성
    5. PSU 용량 충분성
    6. 쿨러 소켓 호환성
    7. 저장장치 인터페이스 호환성
    
    [의존 모듈]
    backend/modules/compatibility/engine.py의 CompatibilityEngine 활용.
    
    [입력]
    {
        "components": [
            {"category": "cpu", "name": "Intel Core i5-14600K", ...},
            {"category": "motherboard", "name": "MSI MAG Z790", ...},
            ...
        ]
    }
    
    [출력]
    {
        "is_compatible": true,
        "checks": [
            {"pair": ["cpu", "motherboard"], "status": "pass", "note": "LGA1700 소켓 호환"},
            {"pair": ["gpu", "psu"], "status": "warning", "note": "권장 650W, 현재 550W"},
            ...
        ],
        "overall_notes": "전체적으로 호환 가능하나 PSU 용량 여유 권장"
    }
    """
    
    def __init__(self, compatibility_engine=None, verbose: bool = True):
        """
        Args:
            compatibility_engine: CompatibilityEngine 인스턴스
            verbose: 상세 로깅 여부
        """
        config = AGENT_CONFIGS["compatibility_checker"]
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[],
            verbose=verbose,
        )
        self.compatibility_engine = compatibility_engine
    
    def check(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        호환성 검증
        
        Args:
            components: 부품 목록
            
        Returns:
            호환성 검증 결과
        """
        logger.info(f"호환성 검증 중: {len(components)}개 부품")
        
        # TODO: CompatibilityEngine 연동
        if self.compatibility_engine:
            # return self.compatibility_engine.check_all(components)
            pass
        
        # Placeholder 반환
        return {
            "is_compatible": True,
            "checks": [],
            "overall_notes": "호환성 검증 모듈 연동 후 구현 예정",
        }


class RecommendationWriterAgent(BaseAgent):
    """
    추천 결과 작성 에이전트
    
    [역할]
    기술 정보를 사용자 친화적인 추천 결과로 작성.
    
    [출력 포맷]
    - 요약: 한 줄 요약
    - 부품 목록: 카테고리별 추천 부품과 이유
    - 총 가격: 예상 총 비용
    - 성능 예측: 예상 게임/작업 성능
    - 주의사항: 조립 시 참고사항
    
    [스타일 가이드]
    - 전문 용어는 괄호 안에 설명 추가
    - 장점/단점을 균형있게 기술
    - 불필요한 과장 표현 지양
    - 해시태그 형식의 핵심 키워드 제공
    
    [출력 예시]
    ```
    {
        "summary": "150만원으로 배그 풀옵 가능한 게임용 PC",
        "components": [
            {
                "category": "GPU",
                "name": "RTX 4060 Ti 8GB",
                "price": 520000,
                "hashtags": ["#배그풀옵", "#1080p최적화"],
                "reason": "배그 울트라 설정 90fps 이상 가능"
            },
            ...
        ],
        "total_price": 1480000,
        "performance_estimate": {
            "pubg_ultra_fps": "90-100",
            "general_benchmark": "높음"
        },
        "notes": "케이스 쿨링에 신경 쓰면 더 좋은 성능 유지 가능"
    }
    ```
    """
    
    def __init__(self, verbose: bool = True):
        config = AGENT_CONFIGS["recommendation_writer"]
        super().__init__(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[],
            verbose=verbose,
        )
    
    def write(
        self,
        components: List[Dict[str, Any]],
        user_request: Dict[str, Any],
        compatibility_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        추천 결과 작성
        
        Args:
            components: 선택된 부품 목록
            user_request: 원본 사용자 요청
            compatibility_result: 호환성 검증 결과
            
        Returns:
            포맷된 추천 결과
        """
        logger.info("추천 결과 작성 중...")
        
        # TODO: LLM을 활용한 자연어 결과 생성
        
        # Placeholder 반환
        total_price = sum(c.get("price", 0) for c in components)
        
        return {
            "summary": f"사용자 요청에 맞춘 PC 구성 (총 {total_price:,}원)",
            "components": components,
            "total_price": total_price,
            "performance_estimate": {},
            "notes": "추천 결과 작성 모듈 구현 예정",
        }


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    # 에이전트 테스트
    analyzer = RequirementAnalyzerAgent()
    result = analyzer.analyze("150만원으로 배그 풀옵 가능한 PC 만들어줘")
    print(f"분석 결과: {result}")
    
    planner = BudgetPlannerAgent()
    budget_result = planner.plan(1500000, "gaming")
    print(f"예산 분배: {budget_result}")
