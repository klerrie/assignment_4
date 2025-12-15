"""
Tests for Pydantic model validation.
Covers both valid and invalid outputs.
"""
import pytest
from pydantic import ValidationError
from src.models import ContractChangeOutput


class TestPydanticValidation:
    """Test suite for ContractChangeOutput validation."""
    
    def test_valid_output(self):
        """Test that valid output passes validation."""
        valid_data = {
            "sections_changed": [
                "Section 3: Payment Terms",
                "Section 7: Termination Clause"
            ],
            "topics_touched": [
                "Payment Schedule",
                "Liability",
                "Termination Rights"
            ],
            "summary_of_the_change": "The payment terms were extended from 30 to 45 days, and a new termination clause was added allowing either party to terminate with 60 days notice."
        }
        
        output = ContractChangeOutput(**valid_data)
        
        assert len(output.sections_changed) == 2
        assert len(output.topics_touched) == 3
        assert len(output.summary_of_the_change) >= 50
        assert "Payment Terms" in output.sections_changed[0]
    
    def test_invalid_empty_sections(self):
        """Test that empty sections_changed fails validation."""
        invalid_data = {
            "sections_changed": [],
            "topics_touched": ["Payment Schedule"],
            "summary_of_the_change": "This is a valid summary that is long enough to pass the minimum length requirement of 50 characters."
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ContractChangeOutput(**invalid_data)
        
        assert "sections_changed" in str(exc_info.value)
    
    def test_invalid_empty_topics(self):
        """Test that empty topics_touched fails validation."""
        invalid_data = {
            "sections_changed": ["Section 3: Payment Terms"],
            "topics_touched": [],
            "summary_of_the_change": "This is a valid summary that is long enough to pass the minimum length requirement of 50 characters."
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ContractChangeOutput(**invalid_data)
        
        assert "topics_touched" in str(exc_info.value)
    
    def test_invalid_short_summary(self):
        """Test that summary shorter than 50 characters fails validation."""
        invalid_data = {
            "sections_changed": ["Section 3: Payment Terms"],
            "topics_touched": ["Payment Schedule"],
            "summary_of_the_change": "Short summary"  # Less than 50 chars
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ContractChangeOutput(**invalid_data)
        
        assert "summary_of_the_change" in str(exc_info.value)
        assert "50" in str(exc_info.value)
    
    def test_invalid_empty_string_sections(self):
        """Test that sections with empty strings fail validation."""
        invalid_data = {
            "sections_changed": ["Section 3: Payment Terms", ""],
            "topics_touched": ["Payment Schedule"],
            "summary_of_the_change": "This is a valid summary that is long enough to pass the minimum length requirement of 50 characters."
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ContractChangeOutput(**invalid_data)
        
        assert "non-empty" in str(exc_info.value).lower()
    
    def test_whitespace_trimming(self):
        """Test that whitespace is trimmed from fields."""
        data = {
            "sections_changed": ["  Section 3: Payment Terms  ", "  Section 7  "],
            "topics_touched": ["  Payment Schedule  "],
            "summary_of_the_change": "  This is a valid summary that is long enough to pass the minimum length requirement of 50 characters.  "
        }
        
        output = ContractChangeOutput(**data)
        
        assert output.sections_changed[0] == "Section 3: Payment Terms"
        assert output.sections_changed[1] == "Section 7"
        assert output.topics_touched[0] == "Payment Schedule"
        assert output.summary_of_the_change.startswith("This is")
        assert output.summary_of_the_change.endswith("characters.")
    
    def test_model_serialization(self):
        """Test that model can be serialized to JSON."""
        data = {
            "sections_changed": ["Section 3: Payment Terms"],
            "topics_touched": ["Payment Schedule"],
            "summary_of_the_change": "This is a valid summary that is long enough to pass the minimum length requirement of 50 characters."
        }
        
        output = ContractChangeOutput(**data)
        json_output = output.model_dump()
        
        assert isinstance(json_output, dict)
        assert "sections_changed" in json_output
        assert "topics_touched" in json_output
        assert "summary_of_the_change" in json_output
