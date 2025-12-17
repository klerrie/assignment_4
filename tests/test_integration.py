"""
End-to-end integration test.
Bonus test for complete workflow.
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from src.main import main
from src.models import ContractChangeOutput


class TestIntegration:
    """End-to-end integration test suite."""
    
    @patch('src.main.ImageParser')
    @patch('src.main.ContextualizationAgent')
    @patch('src.main.ExtractionAgent')
    def test_end_to_end_workflow(self, mock_extraction_agent, mock_context_agent, mock_image_parser):
        """Test complete end-to-end workflow."""
        # Create temporary image files
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp1, \
             tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp2:
            tmp1.write(b'original contract')
            tmp2.write(b'amended contract')
            original_path = tmp1.name
            amendment_path = tmp2.name
        
        try:
            # Mock command line arguments - create a list-like object that supports slicing
            argv_list = ['main.py', original_path, amendment_path]
            
            # Create a custom class that behaves like sys.argv
            class MockArgv:
                def __init__(self, values):
                    self.values = values
                
                def __getitem__(self, key):
                    if isinstance(key, slice):
                        return self.values[key]
                    return self.values[key]
                
                def __len__(self):
                    return len(self.values)
            
            # Replace sys.argv with our custom class
            import sys
            original_argv = sys.argv
            sys.argv = MockArgv(argv_list)
            
            # Mock image parser
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_image.side_effect = [
                "Original contract text: Section 1, Section 2, Section 3: Payment Terms - 30 days",
                "Amended contract text: Section 1, Section 2, Section 3: Payment Terms - 45 days"
            ]
            mock_image_parser.return_value = mock_parser_instance
            
            # Mock contextualization agent
            mock_context_instance = MagicMock()
            mock_context_instance.analyze_documents.return_value = {
                "analysis": "Documents have 3 sections. Section 3 payment terms changed.",
                "original_length": 100,
                "amendment_length": 100
            }
            mock_context_agent.return_value = mock_context_instance
            
            # Mock extraction agent
            mock_extraction_instance = MagicMock()
            mock_extraction_instance.extract_changes.return_value = ContractChangeOutput(
                sections_changed=["Section 3: Payment Terms"],
                topics_touched=["Payment Schedule"],
                summary_of_the_change="The payment terms were extended from 30 to 45 days in Section 3."
            )
            mock_extraction_agent.return_value = mock_extraction_instance
            
            with patch('src.tracing.tracing_manager') as mock_tracing:
                mock_trace = MagicMock()
                mock_tracing.create_trace.return_value = mock_trace
                
                # Run main function
                result = main()
            
            # Verify workflow executed successfully
            assert result == 0
            assert mock_parser_instance.parse_image.call_count == 2
            assert mock_context_instance.analyze_documents.called
            assert mock_extraction_instance.extract_changes.called
            
            # Verify Agent 2 received Agent 1's output
            extraction_call_args = mock_extraction_instance.extract_changes.call_args
            assert extraction_call_args is not None
            context_output = extraction_call_args[1]['contextualization_output']
            assert "analysis" in context_output
            
        finally:
            # Restore original sys.argv
            import sys
            sys.argv = original_argv
            os.unlink(original_path)
            os.unlink(amendment_path)
