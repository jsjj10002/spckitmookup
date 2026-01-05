import sys
import os
import unittest
from unittest.mock import MagicMock, ANY

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.modules.multi_agent.tools import AutoStepBuilderTool

class TestAutoStepBuilder(unittest.TestCase):
    def test_strict_ordering(self):
        """Test if AutoStepBuilderTool follows the strict 1->8 step order"""
        
        # Mock Pipeline
        mock_pipeline = MagicMock()
        mock_session = MagicMock()
        mock_session.session_id = "test_session"
        mock_pipeline.start_session.return_value = mock_session
        
        # Mock Candidate Result
        mock_candidate = MagicMock()
        mock_candidate.component_id = "comp_1"
        mock_candidate.name = "Test Component"
        mock_candidate.price = 10000
        mock_candidate.dict.return_value = {"name": "Test Component", "price": 10000}
        
        mock_step_result = MagicMock()
        mock_step_result.candidates = [mock_candidate]
        mock_step_result.category = "test_category"
        
        mock_pipeline.get_step_candidates.return_value = mock_step_result
        mock_pipeline.get_summary.return_value = {"status": "complete"}
        
        # Init Tool
        tool = AutoStepBuilderTool(pipeline=mock_pipeline)
        
        # Run Tool
        result = tool._run(budget=1500000, purpose="gaming")
        
        # Verification
        print("Verifying Pipeline Calls...")
        
        # 1. Check start_session
        mock_pipeline.start_session.assert_called_with(budget=1500000, purpose="gaming")
        print("✅ Session started correctly")
        
        # 2. Check strict order 1 to 8
        expected_calls = []
        for step in range(1, 9):
            # We expect get_step_candidates called for each step
            # And select_component called for each step
            pass 
            
        # Verify get_step_candidates calls
        self.assertEqual(mock_pipeline.get_step_candidates.call_count, 8)
        
        # Check explicit Step calls
        calls = mock_pipeline.get_step_candidates.call_args_list
        for i, call in enumerate(calls):
            step_arg = call.kwargs['step']
            print(f"Call {i+1}: Step {step_arg}")
            self.assertEqual(step_arg, i + 1)
            
        print("✅ Strict ordering (1->8) confirmed!")

if __name__ == '__main__':
    unittest.main()
