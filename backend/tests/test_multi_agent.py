"""
CREWai 멀티 에이전트 모듈 테스트
================================

테스트 실행:
```bash
pytest backend/tests/test_multi_agent.py -v
```
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestAgentOrchestrator:
    """AgentOrchestrator 테스트"""
    
    def test_orchestrator_initialization(self):
        """오케스트레이터 초기화 테스트"""
        from backend.modules.multi_agent.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        assert orchestrator is not None
        assert orchestrator.llm_model == "gemini-3-flash-preview"
        assert orchestrator.verbose == True
    
    def test_orchestrator_run_placeholder(self):
        """오케스트레이터 실행 (placeholder) 테스트"""
        from backend.modules.multi_agent.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        result = orchestrator.run({
            "query": "게임용 PC 추천해줘",
            "budget": 1500000,
            "purpose": "gaming"
        })
        
        assert result.status == "placeholder"
        assert len(result.agent_logs) > 0
    
    def test_user_request_validation(self):
        """UserRequest 모델 검증 테스트"""
        from backend.modules.multi_agent.orchestrator import UserRequest
        
        # 정상 요청
        request = UserRequest(
            query="게임용 PC 추천",
            budget=1500000,
            purpose="gaming"
        )
        
        assert request.query == "게임용 PC 추천"
        assert request.budget == 1500000
    
    def test_create_orchestrator_factory(self):
        """팩토리 함수 테스트"""
        from backend.modules.multi_agent.orchestrator import create_orchestrator
        
        orchestrator = create_orchestrator({
            "llm_model": "gemini-3-flash-preview",
            "temperature": 0.5
        })
        
        assert orchestrator.llm_model == "gemini-3-flash-preview"
        assert orchestrator.temperature == 0.5


class TestAgents:
    """개별 에이전트 테스트"""
    
    def test_requirement_analyzer(self):
        """RequirementAnalyzerAgent 테스트"""
        from backend.modules.multi_agent.agents import RequirementAnalyzerAgent
        
        agent = RequirementAnalyzerAgent()
        result = agent.analyze("150만원으로 배그 풀옵 가능한 PC")
        
        assert "raw_query" in result
        assert result["raw_query"] == "150만원으로 배그 풀옵 가능한 PC"
    
    def test_budget_planner(self):
        """BudgetPlannerAgent 테스트"""
        from backend.modules.multi_agent.agents import BudgetPlannerAgent
        
        agent = BudgetPlannerAgent()
        result = agent.plan(1500000, "gaming")
        
        assert result["total_budget"] == 1500000
        assert "allocations" in result
        assert "gpu" in result["allocations"]
        # 게임용은 GPU에 가장 많이 할당
        assert result["allocations"]["gpu"]["ratio"] > 0.3
    
    def test_budget_planner_different_purposes(self):
        """목적별 예산 분배 테스트"""
        from backend.modules.multi_agent.agents import BudgetPlannerAgent
        
        agent = BudgetPlannerAgent()
        
        # 게임용: GPU에 높은 비율
        gaming = agent.plan(1000000, "gaming")
        assert gaming["allocations"]["gpu"]["ratio"] > gaming["allocations"]["cpu"]["ratio"]
        
        # 워크스테이션: CPU에 높은 비율
        workstation = agent.plan(1000000, "workstation")
        assert workstation["allocations"]["cpu"]["ratio"] > workstation["allocations"]["gpu"]["ratio"]


# pytest 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
