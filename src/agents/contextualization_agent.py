"""
Agent 1: Contextualization Agent
Analyzes both documents to identify structure and corresponding sections.
"""
import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from src.tracing import tracing_manager

load_dotenv()


class ContextualizationAgent:
    """
    Agent 1: Analyzes both original and amended contracts to understand
    their structure and identify corresponding sections.
    
    This agent mimics the first step in legal analysis: understanding
    the document context before identifying specific changes.
    """
    
    def __init__(self):
        """Initialize OpenAI client with OpenRouter configuration."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = "openai/gpt-4o"
        self.agent_name = "ContextualizationAgent"
    
    def analyze_documents(
        self,
        original_text: str,
        amendment_text: str,
        session_id: str,
        contract_id: str
    ) -> Dict[str, Any]:
        """
        Analyze both documents to identify structure and corresponding sections.
        
        Args:
            original_text: Extracted text from original contract
            amendment_text: Extracted text from amended contract
            session_id: Session identifier for tracing
            contract_id: Contract identifier for tracing
            
        Returns:
            Dictionary containing document structure analysis
        """
        # Create trace for Agent 1 execution
        trace = tracing_manager.create_trace(
            name="agent_1_contextualization",
            session_id=session_id,
            contract_id=contract_id,
            metadata={"agent_name": self.agent_name}
        )
        
        # System prompt for contextualization
        system_prompt = """You are a legal document analyst specializing in contract structure analysis. Your task is to analyze two contract documents (an original and an amendment) and identify their structure, organization, and corresponding sections.

Your analysis should:
1. Identify the overall structure of both documents (sections, subsections, appendices)
2. Map corresponding sections between the original and amendment
3. Identify the document type and key legal domains covered (e.g., payment terms, liability, intellectual property, termination)
4. Note any structural differences (new sections, removed sections, renumbered sections)
5. Provide a high-level overview of the document organization

Return your analysis in a structured format that will help a downstream agent identify specific changes."""
        
        user_prompt = f"""Analyze the following two contract documents:

=== ORIGINAL CONTRACT ===
{original_text[:8000]}  # Truncate if too long

=== AMENDED CONTRACT ===
{amendment_text[:8000]}  # Truncate if too long

Provide a structured analysis including:
1. Document structure overview (sections, organization)
2. Section mapping between original and amendment
3. Key legal topics/domains present
4. Any structural changes (new/removed/renumbered sections)
5. Context that will help identify specific textual changes"""
        
        try:
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.2  # Low temperature for consistent analysis
            )
            
            analysis_output = response.choices[0].message.content
            
            # Log generation to trace
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            tracing_manager.create_generation(
                trace=trace,
                name="contextualization_analysis",
                model=self.model,
                input_data={
                    "original_length": len(original_text),
                    "amendment_length": len(amendment_text),
                    "prompt": user_prompt[:500] + "..."
                },
                output_data={"analysis": analysis_output[:1000] + "..." if len(analysis_output) > 1000 else analysis_output},
                usage=usage,
                metadata={"agent_name": self.agent_name}
            )
            
            # Score the trace
            trace.score(name="contextualization_quality", value=1.0)
            
            return {
                "analysis": analysis_output,
                "original_length": len(original_text),
                "amendment_length": len(amendment_text),
                "usage": usage
            }
            
        except Exception as e:
            # Log error to trace
            trace.span(
                name="error",
                input={"original_length": len(original_text), "amendment_length": len(amendment_text)},
                output={"error": str(e)},
                level="ERROR"
            )
            raise RuntimeError(f"Contextualization agent failed: {str(e)}") from e
