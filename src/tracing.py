"""
Langfuse tracing utilities for observability across the contract analysis workflow.
"""
import os
from typing import Optional, Dict, Any
from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe
from dotenv import load_dotenv

load_dotenv()


class TracingManager:
    """
    Manages Langfuse tracing configuration and utilities.
    Provides centralized tracing for all agent calls and LLM invocations.
    """
    
    def __init__(self):
        """Initialize Langfuse client with environment variables."""
        self.client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )
    
    def create_trace(
        self,
        name: str,
        session_id: str,
        contract_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a new trace with custom metadata.
        
        Args:
            name: Name of the trace operation
            session_id: Unique session identifier
            contract_id: Contract identifier
            metadata: Additional metadata to attach
        """
        trace_metadata = {
            "session_id": session_id,
            "contract_id": contract_id,
            **(metadata or {})
        }
        
        return self.client.trace(
            name=name,
            metadata=trace_metadata
        )
    
    def create_span(
        self,
        trace,
        name: str,
        input_data: Any,
        output_data: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a span within a trace.
        
        Args:
            trace: Parent trace object
            name: Name of the span
            input_data: Input data for the span
            output_data: Output data from the span
            metadata: Additional metadata
        """
        return trace.span(
            name=name,
            input=input_data,
            output=output_data,
            metadata=metadata or {}
        )
    
    def create_generation(
        self,
        trace,
        name: str,
        model: str,
        input_data: Any,
        output_data: Any = None,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a generation span for LLM calls.
        
        Args:
            trace: Parent trace object
            name: Name of the generation
            model: Model name used
            input_data: Input prompt/data
            output_data: Model output
            usage: Token usage information
            metadata: Additional metadata
        """
        return trace.generation(
            name=name,
            model=model,
            input=input_data,
            output=output_data,
            usage=usage,
            metadata=metadata or {}
        )


# Global tracing manager instance
tracing_manager = TracingManager()
