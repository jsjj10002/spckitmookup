"""
CREWai 멀티 에이전트 모듈 테스트
================================

테스트 실행:
```bash
cd backend
uv run python -m pytest tests/test_multi_agent.py -v
```

주의: 이 테스트는 crewai의 에이전트 초기화를 우회하기 위해
agents 모듈을 mock합니다.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestAgentOrchestrator:
    """AgentOrchestrator 테스트"""
    
    @patch('backend.modules.multi_agent.orchestrator.PCComponentVectorStore')
    @patch('backend.modules.multi_agent.orchestrator.PCComponentRetriever')
    @patch('backend.modules.multi_agent.orchestrator.CompatibilityEngine')
    @patch('backend.modules.multi_agent.orchestrator.ChatGoogleGenerativeAI')
    @patch('backend.modules.multi_agent.orchestrator.Crew')
    @patch('backend.modules.multi_agent.orchestrator.Task')
    def test_orchestrator_initialization(self, mock_task, mock_crew, mock_llm_cls, mock_comp_engine, mock_retriever, mock_vector_store):
        """오케스트레이터 초기화 테스트"""
        # agents 모듈을 mock으로 대체
        mock_agents = MagicMock()
        with patch.dict(sys.modules, {'backend.modules.multi_agent.agents': mock_agents}):
            from backend.modules.multi_agent.orchestrator import AgentOrchestrator
            
            # Mock 설정
            mock_llm_instance = MagicMock()
            mock_llm_cls.return_value = mock_llm_instance
            
            orchestrator = AgentOrchestrator(llm_model="gemini-3-flash-preview")
            
            assert orchestrator is not None
            assert orchestrator.llm_model == "gemini-3-flash-preview"
            assert orchestrator.verbose == True
            
            # 의존성 초기화 확인
            mock_vector_store.assert_called_once()
            mock_retriever.assert_called_once()
            mock_comp_engine.assert_called_once()
            mock_crew.assert_called_once()
    
    @patch('backend.modules.multi_agent.orchestrator.PCComponentVectorStore')
    @patch('backend.modules.multi_agent.orchestrator.PCComponentRetriever')
    @patch('backend.modules.multi_agent.orchestrator.CompatibilityEngine')
    @patch('backend.modules.multi_agent.orchestrator.ChatGoogleGenerativeAI')
    @patch('backend.modules.multi_agent.orchestrator.Crew')
    @patch('backend.modules.multi_agent.orchestrator.Task')
    def test_orchestrator_default_model(self, mock_task, mock_crew, mock_llm_cls, mock_comp_engine, mock_retriever, mock_vector_store):
        """기본 모델 설정 테스트"""
        mock_agents = MagicMock()
        with patch.dict(sys.modules, {'backend.modules.multi_agent.agents': mock_agents}):
            from backend.modules.multi_agent.orchestrator import AgentOrchestrator
            from backend.rag.config import GENERATION_MODEL
            
            # Mock LLM 인스턴스 설정
            mock_llm_instance = MagicMock()
            mock_llm_cls.return_value = mock_llm_instance

            orchestrator = AgentOrchestrator()
            
            # 기본값이 config의 모델과 일치하는지 확인
            assert orchestrator.llm_model == GENERATION_MODEL
    
    @patch('backend.modules.multi_agent.orchestrator.PCComponentVectorStore')
    @patch('backend.modules.multi_agent.orchestrator.PCComponentRetriever')
    @patch('backend.modules.multi_agent.orchestrator.CompatibilityEngine')
    @patch('backend.modules.multi_agent.orchestrator.ChatGoogleGenerativeAI')
    @patch('backend.modules.multi_agent.orchestrator.Crew')
    @patch('backend.modules.multi_agent.orchestrator.Task')
    def test_orchestrator_run_mock(self, mock_task, mock_crew_cls, mock_llm, mock_comp, mock_ret, mock_vec):
        """오케스트레이터 실행 (Mock) 테스트"""
        mock_agents = MagicMock()
        with patch.dict(sys.modules, {'backend.modules.multi_agent.agents': mock_agents}):
            from backend.modules.multi_agent.orchestrator import AgentOrchestrator, RecommendationResult
            
            # Mock Crew 인스턴스 설정
            mock_crew_instance = MagicMock()
            mock_crew_cls.return_value = mock_crew_instance
            
            # Kickoff 결과 설정 (JSON 포함 텍스트)
            fake_result_json = {
                "components": [
                    {"category": "CPU", "name": "Intel Core i5-13400F", "price": 250000, "reason": "Good", "specs": {}}
                ],
                "total_price": 250000,
                "compatibility_check": {"status": "pass"},
                "performance_estimate": {"score": 90}
            }
            mock_crew_instance.kickoff.return_value = f"분석 결과입니다.\n```json\n{json.dumps(fake_result_json)}\n```"
            
            orchestrator = AgentOrchestrator()
            
            result = orchestrator.run({
                "query": "게임용 PC 추천해줘",
                "budget": 1500000,
                "purpose": "gaming"
            })
            
            assert result.status == "success"
            assert len(result.components) == 1
            assert result.components[0].name == "Intel Core i5-13400F"
            assert result.total_price == 250000
    
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
    
    @patch('backend.modules.multi_agent.orchestrator.AgentOrchestrator')
    def test_create_orchestrator_factory(self, mock_orch_cls):
        """팩토리 함수 테스트"""
        from backend.modules.multi_agent.orchestrator import create_orchestrator
        
        create_orchestrator({
            "llm_model": "gemini-3-flash-preview",
            "temperature": 0.5
        })
        
        mock_orch_cls.assert_called_once()
        call_args = mock_orch_cls.call_args[1]
        assert call_args["llm_model"] == "gemini-3-flash-preview"
        assert call_args["temperature"] == 0.5


class TestAgents:
    """개별 에이전트 테스트 - 파일 내용 검사 기반"""
    
    def test_agent_configs_exist(self):
        """에이전트 설정 상수 존재 확인"""
        expected_agent_roles = [
            "requirement_analyzer",
            "budget_planner", 
            "component_selector",
            "compatibility_checker",
            "recommendation_writer"
        ]
        
        agents_file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'multi_agent', 
            'agents.py'
        )
        
        with open(agents_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 각 에이전트 역할이 파일에 정의되어 있는지 확인
        for role in expected_agent_roles:
            assert f'"{role}"' in content or f"'{role}'" in content, f"{role} 설정이 agents.py에 없습니다"
    
    def test_budget_templates_classvar(self):
        """BUDGET_TEMPLATES가 ClassVar로 정의되었는지 확인"""
        agents_file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'multi_agent', 
            'agents.py'
        )
        
        with open(agents_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # ClassVar 타입 힌트가 있는지 확인
        assert "BUDGET_TEMPLATES: ClassVar" in content, "BUDGET_TEMPLATES에 ClassVar 타입 힌트가 필요합니다"
    
    def test_all_agent_classes_defined(self):
        """모든 에이전트 클래스가 정의되어 있는지 확인"""
        expected_classes = [
            "RequirementAnalyzerAgent",
            "BudgetPlannerAgent",
            "ComponentSelectorAgent",
            "CompatibilityCheckerAgent",
            "RecommendationWriterAgent"
        ]
        
        agents_file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'multi_agent', 
            'agents.py'
        )
        
        with open(agents_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for class_name in expected_classes:
            assert f"class {class_name}" in content, f"{class_name} 클래스가 agents.py에 정의되지 않았습니다"


# pytest 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
