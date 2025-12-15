"""
Agent 2: Change Extraction Agent
Receives Agent 1's contextualization output and extracts specific changes.
"""
import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from src.tracing import tracing_manager
from src.models import ContractChangeOutput

load_dotenv()


class ExtractionAgent:
    """
    Agent 2: Extracts specific changes from the amendment using
    Agent 1's contextualization analysis.
    
    This agent mimics the second step in legal analysis: using context
    to identify and extract precise changes.
    """
    
    def __init__(self):
        """Initialize OpenAI client with OpenRouter configuration."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = "openai/gpt-4o"
        self.agent_name = "ExtractionAgent"
    
    def extract_changes(
        self,
        original_text: str,
        amendment_text: str,
        contextualization_output: Dict[str, Any],
        session_id: str,
        contract_id: str
    ) -> ContractChangeOutput:
        """
        Extract specific changes using Agent 1's contextualization.
        
        Args:
            original_text: Extracted text from original contract
            amendment_text: Extracted text from amended contract
            contextualization_output: Output from Agent 1 (contextualization)
            session_id: Session identifier for tracing
            contract_id: Contract identifier for tracing
            
        Returns:
            Validated ContractChangeOutput with extracted changes
        """
        # Create trace for Agent 2 execution
        trace = tracing_manager.create_trace(
            name="agent_2_extraction",
            session_id=session_id,
            contract_id=contract_id,
            metadata={"agent_name": self.agent_name}
        )
        
        # System prompt for change extraction
        system_prompt = """You are a legal change extraction specialist. Your task is to identify and extract specific changes between an original contract and its amendment.

Using the contextualization analysis provided, you must:
1. Identify all sections that were modified, added, or removed
2. Determine which legal topics/subjects were affected by the changes
3. Create a comprehensive summary of all changes

You must return your output in the following JSON format:
{
    "sections_changed": ["Section 3: Payment Terms", "Section 7: Termination Clause"],
    "topics_touched": ["Payment Schedule", "Liability", "Termination Rights"],
    "summary_of_the_change": "A detailed summary of all changes (minimum 50 characters)"
}

Be precise, comprehensive, and ensure all changes are captured."""
        
        user_prompt = f"""Using the contextualization analysis below, extract all specific changes between the original and amended contracts.

=== CONTEXTUALIZATION ANALYSIS (from Agent 1) ===
{contextualization_output.get('analysis', 'No analysis provided')}

=== ORIGINAL CONTRACT ===
{original_text[:6000]}  # Truncate if too long

=== AMENDED CONTRACT ===
{amendment_text[:6000]}  # Truncate if too long

Extract all changes and return ONLY valid JSON in the required format:
{{
    "sections_changed": ["list of section names"],
    "topics_touched": ["list of topics"],
    "summary_of_the_change": "detailed summary (min 50 chars)"
}}"""
        
        try:
            # Make API call with JSON mode for structured output
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.1,  # Very low temperature for precise extraction
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            extraction_output = response.choices[0].message.content
            
            # Log generation to trace
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            tracing_manager.create_generation(
                trace=trace,
                name="change_extraction",
                model=self.model,
                input_data={
                    "has_contextualization": bool(contextualization_output),
                    "prompt": user_prompt[:500] + "..."
                },
                output_data={"extraction": extraction_output},
                usage=usage,
                metadata={"agent_name": self.agent_name}
            )
            
            # Parse and validate with Pydantic
            import json
            try:
                extracted_data = json.loads(extraction_output)
            except json.JSONDecodeError as e:
                trace.span(
                    name="validation_error",
                    input={"raw_output": extraction_output},
                    output={"error": f"JSON parsing failed: {str(e)}"},
                    level="ERROR"
                )
                raise ValueError(f"Failed to parse agent output as JSON: {str(e)}") from e
            
            # Validate with Pydantic model
            try:
                validated_output = ContractChangeOutput(**extracted_data)
            except Exception as e:
                trace.span(
                    name="pydantic_validation_error",
                    input={"extracted_data": extracted_data},
                    output={"error": str(e)},
                    level="ERROR"
                )
                raise ValueError(f"Pydantic validation failed: {str(e)}") from e
            
            # Log successful validation
            trace.span(
                name="validation",
                input={"extracted_data": extracted_data},
                output={"validated": True, "sections_count": len(validated_output.sections_changed)},
                level="DEFAULT"
            )
            
            # Score the trace
            trace.score(name="extraction_quality", value=1.0)
            
            return validated_output
            
        except Exception as e:
            # Log error to trace
            trace.span(
                name="error",
                input={"has_contextualization": bool(contextualization_output)},
                output={"error": str(e)},
                level="ERROR"
            )
            raise RuntimeError(f"Extraction agent failed: {str(e)}") from e
