import sys
import os
import unittest
import json
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.rag.step_by_step import SelectionStep
from backend.modules.multi_agent.orchestrator import AgentOrchestrator

class TestFeedbackChanges(unittest.TestCase):
    def test_step_order(self):
        """Test if CPU_COOLER is Step 7 and CASE is Step 8"""
        print(f"Checking SelectionStep Order...")
        print(f"CPU_COOLER: {SelectionStep.CPU_COOLER.value}")
        print(f"CASE: {SelectionStep.CASE.value}")
        
        self.assertEqual(SelectionStep.CPU_COOLER.value, 7)
        self.assertEqual(SelectionStep.CASE.value, 8)
        print("✅ Step order confirmed: Cooler(7) -> Case(8)")

    def test_missing_info_logic(self):
        """Test if orchestrator halts and asks for info when missing"""
        
        # Mock Orchestrator to partial extent or just mock the inner logic if possible.
        # However, orchestrator is complex to mock fully due to CrewAI.
        # We will unit test the *logic block* by mocking the agent execution result.
        
        # Since checking the logic inside .run() is hard without running Crew,
        # we can try to verify by creating a mocked Orchestraor that skips actual Crew but simulates the first agent result.
        
        # However, Python dynamic nature allows us to mock `self.crew.agents[0].execute_task`
        
        orchestrator = AgentOrchestrator(verbose=False)
        orchestrator.crew = MagicMock()
        orchestrator.crew.tasks = [MagicMock()] # task_analyze
        orchestrator.crew.agents = [MagicMock()] # requirement_analyzer (index 0)
        
        # Case 1: Missing Budget
        mock_result = json.dumps({
            "budget": None,
            "purpose": "gaming",
            "missing_info": ["budget"]
        })
        orchestrator.crew.agents[0].execute_task.return_value = mock_result
        
        print("Testing Missing Info Response...")
        result = orchestrator.run({"query": "게임용 컴퓨터 추천해줘"})
        
        print(f"Result Status: {result.status}")
        print(f"Result Logs: {result.agent_logs}")
        
        self.assertEqual(result.status, "missing_info")
        self.assertTrue("budget" in result.agent_logs[0] or "예산" in result.agent_logs[0])
        print("✅ Correctly identified missing budget")

if __name__ == '__main__':
    unittest.main()
