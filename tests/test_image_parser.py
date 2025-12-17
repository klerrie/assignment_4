"""
Tests for image parsing functionality.
Bonus test for image validation and encoding.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.image_parser import ImageParser


class TestImageParser:
    """Test suite for image parsing utilities."""
    
    def test_validate_image_valid_format(self):
        """Test validation of valid image formats."""
        parser = ImageParser()
        
        # Create a temporary valid image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b'fake image data')
            tmp_path = tmp.name
        
        try:
            is_valid, error = parser.validate_image(tmp_path)
            assert is_valid is True
            assert error is None
        finally:
            os.unlink(tmp_path)
    
    def test_validate_image_invalid_format(self):
        """Test validation rejects invalid image formats."""
        parser = ImageParser()
        
        # Create a temporary invalid file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'not an image')
            tmp_path = tmp.name
        
        try:
            is_valid, error = parser.validate_image(tmp_path)
            assert is_valid is False
            assert "Unsupported image format" in error
        finally:
            os.unlink(tmp_path)
    
    def test_validate_image_nonexistent(self):
        """Test validation rejects nonexistent files."""
        parser = ImageParser()
        
        is_valid, error = parser.validate_image("/nonexistent/path/image.jpg")
        assert is_valid is False
        assert "not found" in error.lower()
    
    def test_encode_image(self):
        """Test image encoding to base64."""
        parser = ImageParser()
        
        # Create a temporary image file
        test_content = b'test image content'
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(test_content)
            tmp_path = tmp.name
        
        try:
            encoded = parser.encode_image(tmp_path)
            assert isinstance(encoded, str)
            assert len(encoded) > 0
            # Base64 encoded string should be longer than original
            assert len(encoded) >= len(test_content)
        finally:
            os.unlink(tmp_path)
    
    @patch('src.image_parser.OpenAI')
    @patch('src.tracing.tracing_manager')
    def test_parse_image_success(self, mock_tracing, mock_openai_class):
        """Test successful image parsing."""
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b'fake image data')
            tmp_path = tmp.name
        
        try:
            # Mock OpenAI client - set up before creating parser
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Mock response with proper structure - use spec to ensure proper behavior
            mock_message = MagicMock()
            mock_message.content = "Extracted contract text: Section 1: Definitions..."
            
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 500
            mock_usage.completion_tokens = 200
            mock_usage.total_tokens = 700
            
            # Create a proper list for choices to ensure len() works correctly
            choices_list = [mock_choice]
            mock_response = MagicMock()
            # Use PropertyMock or set directly as a list
            type(mock_response).choices = choices_list
            mock_response.usage = mock_usage
            mock_client.chat.completions.create.return_value = mock_response
            
            # Mock tracing
            mock_trace = MagicMock()
            mock_tracing.create_trace.return_value = mock_trace
            
            # Now create parser (after mocks are set up)
            parser = ImageParser()
            
            result = parser.parse_image(
                image_path=tmp_path,
                session_id="test_session",
                contract_id="test_contract",
                document_type="original"
            )
            
            assert isinstance(result, str)
            assert "Extracted contract text" in result
            assert mock_client.chat.completions.create.called
        finally:
            os.unlink(tmp_path)
    
    def test_parse_image_invalid_file(self):
        """Test parsing fails for invalid image files."""
        parser = ImageParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse_image(
                image_path="/nonexistent/image.jpg",
                session_id="test_session",
                contract_id="test_contract"
            )
        
        assert "validation failed" in str(exc_info.value).lower()
