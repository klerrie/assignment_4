"""
Image processing utilities for contract document parsing.
Handles validation, encoding, and multimodal LLM API calls.
"""
import os
import base64
from pathlib import Path
from typing import Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv
from src.tracing import tracing_manager

load_dotenv()


class ImageParser:
    """
    Handles image validation, encoding, and multimodal LLM parsing.
    Uses OpenAI via OpenRouter for vision capabilities.
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self):
        """Initialize OpenAI client with OpenRouter configuration."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = "openai/gpt-4o"  # Using GPT-4o for vision
    
    def validate_image(self, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image format and size.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(image_path)
        
        # Check if file exists
        if not path.exists():
            return False, f"Image file not found: {image_path}"
        
        # Check file extension
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported image format: {path.suffix}. Supported formats: {self.SUPPORTED_FORMATS}"
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            return False, f"Image file too large: {file_size} bytes. Maximum size: {self.MAX_FILE_SIZE} bytes"
        
        if file_size == 0:
            return False, "Image file is empty"
        
        return True, None
    
    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def parse_image(
        self,
        image_path: str,
        session_id: str,
        contract_id: str,
        document_type: str = "contract"
    ) -> str:
        """
        Parse contract image using multimodal LLM.
        
        Args:
            image_path: Path to the image file
            session_id: Session identifier for tracing
            contract_id: Contract identifier for tracing
            document_type: Type of document (e.g., "original", "amendment")
            
        Returns:
            Extracted text from the image
        """
        # Validate image
        is_valid, error = self.validate_image(image_path)
        if not is_valid:
            raise ValueError(f"Image validation failed: {error}")
        
        # Encode image
        base64_image = self.encode_image(image_path)
        
        # Create trace for image parsing
        trace = tracing_manager.create_trace(
            name=f"image_parsing_{document_type}",
            session_id=session_id,
            contract_id=contract_id,
            metadata={"document_type": document_type, "image_path": image_path}
        )
        
        # Vision-specific prompt for contract parsing
        vision_prompt = """You are a legal document parser. Analyze this scanned contract image and extract all text content while preserving the document structure and hierarchy. 

Important instructions:
1. Extract ALL text visible in the image, including headers, footers, page numbers, and marginal notes
2. Preserve the document structure: maintain section numbers, headings, subheadings, and paragraph organization
3. Identify and label sections clearly (e.g., "Section 1: Definitions", "Section 2: Terms and Conditions")
4. Preserve formatting cues like bullet points, numbered lists, and indentation
5. Include any tables, schedules, or appendices
6. If text is unclear or partially obscured, indicate with [UNCLEAR] or [PARTIAL]
7. Maintain the logical flow and organization of the document

Return the extracted text in a structured format that preserves the document's hierarchy."""
        
        try:
            # Make multimodal API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": vision_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000,
                temperature=0.1  # Low temperature for accurate extraction
            )
            
            extracted_text = response.choices[0].message.content
            
            # Log generation to trace
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            tracing_manager.create_generation(
                trace=trace,
                name=f"parse_{document_type}_image",
                model=self.model,
                input_data={"image_path": image_path, "prompt": vision_prompt},
                output_data={"extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text},
                usage=usage,
                metadata={"document_type": document_type}
            )
            
            # Score the trace
            trace.score(name="extraction_quality", value=1.0)
            
            return extracted_text
            
        except Exception as e:
            # Log error to trace
            trace.span(
                name="error",
                input={"image_path": image_path},
                output={"error": str(e)},
                level="ERROR"
            )
            raise RuntimeError(f"Failed to parse image {image_path}: {str(e)}") from e
