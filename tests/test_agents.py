"""
Tests for agent handoff and integration.
Verifies that Agent 2 correctly receives Agent 1's output.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.contextualization_agent import ContextualizationAgent
from src.agents.extraction_agent import ExtractionAgent
from src.models import ContractChangeOutput


class TestAgentHandoff:
    """Test suite for agent handoff mechanism."""
    
    def test_agent_1_output_structure(self):
        """Test that Agent 1 returns expected output structure."""
        agent = ContextualizationAgent()
        
        original_text = "Section 1: Definitions\nSection 2: Terms\nSection 3: Payment Terms - 30 days"
        amendment_text = "Section 1: Definitions\nSection 2: Terms\nSection 3: Payment Terms - 45 days"
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Analysis: Documents have 3 sections. Section 3 payment terms changed."
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150
            mock_create.return_value = mock_response
            
            with patch('src.tracing.tracing_manager') as mock_tracing:
                mock_trace = MagicMock()
                mock_tracing.create_trace.return_value = mock_trace
                
                result = agent.analyze_documents(
                    original_text=original_text,
                    amendment_text=amendment_text,
                    session_id="test_session",
                    contract_id="test_contract"
                )
        
        assert "analysis" in result
        assert "original_length" in result
        assert "amendment_length" in result
        assert "usage" in result
        assert isinstance(result["analysis"], str)
        assert len(result["analysis"]) > 0
    
    def test_agent_2_receives_agent_1_output(self):
        """Test that Agent 2 correctly receives and uses Agent 1's output."""
        agent = ExtractionAgent()
        
        original_text = "Section 3: Payment Terms - 30 days"
        amendment_text = "Section 3: Payment Terms - 45 days"
        contextualization_output = {
            "analysis": "Documents have 3 sections. Section 3 payment terms changed from 30 to 45 days.",
            "original_length": 100,
            "amendment_length": 100
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '''{
                "sections_changed": ["Section 3: Payment Terms"],
                "topics_touched": ["Payment Schedule"],
                "summary_of_the_change": "The payment terms were extended from 30 to 45 days in Section 3."
            }'''
            mock_response.usage.prompt_tokens = 200
            mock_response.usage.completion_tokens = 100
            mock_response.usage.total_tokens = 300
            mock_create.return_value = mock_response
            
            with patch('src.tracing.tracing_manager') as mock_tracing:
                mock_trace = MagicMock()
                mock_tracing.create_trace.return_value = mock_trace
                
                result = agent.extract_changes(
                    original_text=original_text,
                    amendment_text=amendment_text,
                    contextualization_output=contextualization_output,
                    session_id="test_session",
                    contract_id="test_contract"
                )
        
        assert isinstance(result, ContractChangeOutput)
        assert len(result.sections_changed) > 0
        assert len(result.topics_touched) > 0
        assert len(result.summary_of_the_change) >= 50
    
    def test_agent_2_uses_contextualization_in_prompt(self):
        """Test that Agent 2's prompt includes Agent 1's contextualization."""
        agent = ExtractionAgent()
        
        original_text = "Section 3: Payment Terms - 30 days"
        amendment_text = "Section 3: Payment Terms - 45 days"
        contextualization_output = {
            "analysis": "TEST CONTEXTUALIZATION ANALYSIS",
            "original_length": 100,
            "amendment_length": 100
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '''{
                "sections_changed": ["Section 3: Payment Terms"],
                "topics_touched": ["Payment Schedule"],
                "summary_of_the_change": "The payment terms were extended from 30 to 45 days in Section 3."
            }'''
            mock_response.usage.prompt_tokens = 200
            mock_response.usage.completion_tokens = 100
            mock_response.usage.total_tokens = 300
            mock_create.return_value = mock_response
            
            with patch('src.tracing.tracing_manager') as mock_tracing:
                mock_trace = MagicMock()
                mock_tracing.create_trace.return_value = mock_trace
                
                agent.extract_changes(
                    original_text=original_text,
                    amendment_text=amendment_text,
                    contextualization_output=contextualization_output,
                    session_id="test_session",
                    contract_id="test_contract"
                )
        
        # Verify that the contextualization was included in the API call
        call_args = mock_create.call_args
        user_message = call_args[1]['messages'][1]['content']  # User message is second
        
        assert "TEST CONTEXTUALIZATION ANALYSIS" in user_message
        assert "CONTEXTUALIZATION ANALYSIS" in user_message
    
    def test_agent_handoff_workflow(self):
        """Test complete handoff workflow from Agent 1 to Agent 2."""
        agent1 = ContextualizationAgent()
        agent2 = ExtractionAgent()
        
        original_text = "Section 1: Definitions\nSection 3: Payment Terms - 30 days"
        amendment_text = "Section 1: Definitions\nSection 3: Payment Terms - 45 days"
        
        with patch.object(agent1.client.chat.completions, 'create') as mock_create_1, \
             patch.object(agent2.client.chat.completions, 'create') as mock_create_2:
            
            # Mock Agent 1 response
            mock_response_1 = MagicMock()
            mock_response_1.choices = [MagicMock()]
            mock_response_1.choices[0].message.content = "Analysis: Section 3 payment terms changed."
            mock_response_1.usage.prompt_tokens = 100
            mock_response_1.usage.completion_tokens = 50
            mock_response_1.usage.total_tokens = 150
            mock_create_1.return_value = mock_response_1
            
            # Mock Agent 2 response
            mock_response_2 = MagicMock()
            mock_response_2.choices = [MagicMock()]
            mock_response_2.choices[0].message.content = '''{
                "sections_changed": ["Section 3: Payment Terms"],
                "topics_touched": ["Payment Schedule"],
                "summary_of_the_change": "The payment terms were extended from 30 to 45 days in Section 3."
            }'''
            mock_response_2.usage.prompt_tokens = 200
            mock_response_2.usage.completion_tokens = 100
            mock_response_2.usage.total_tokens = 300
            mock_create_2.return_value = mock_response_2
            
            with patch('src.tracing.tracing_manager') as mock_tracing:
                mock_trace = MagicMock()
                mock_tracing.create_trace.return_value = mock_trace
                
                # Execute Agent 1
                context_output = agent1.analyze_documents(
                    original_text=original_text,
                    amendment_text=amendment_text,
                    session_id="test_session",
                    contract_id="test_contract"
                )
                
                # Execute Agent 2 with Agent 1's output
                result = agent2.extract_changes(
                    original_text=original_text,
                    amendment_text=amendment_text,
                    contextualization_output=context_output,
                    session_id="test_session",
                    contract_id="test_contract"
                )
        
        # Verify handoff was successful
        assert isinstance(result, ContractChangeOutput)
        assert "Section 3" in result.sections_changed[0]
        assert len(result.summary_of_the_change) >= 50
