"""
Langfuse tracing utilities for observability across the contract analysis workflow.
"""
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Try to import Langfuse (version 2.x required)
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None


class TracingManager:
    """
    Manages Langfuse tracing configuration and utilities.
    Provides centralized tracing for all agent calls and LLM invocations.
    """
    
    def __init__(self):
        """Initialize Langfuse client with environment variables."""
        if not LANGFUSE_AVAILABLE:
            import warnings
            warnings.warn(
                "Langfuse package not installed. Tracing will be disabled.",
                UserWarning
            )
            self.client = None
            return
        
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        # Validate required keys (warn but don't fail if missing for development)
        if not public_key or not secret_key:
            import warnings
            warnings.warn(
                "LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not found in environment variables. "
                "Tracing will not work. Please set them in your .env file.",
                UserWarning
            )
            self.client = None
            return
        
        self.client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
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
        if not self.client:
            # Return a dummy trace object if Langfuse is not available
            return DummyTrace()
        
        trace_metadata = {
            "session_id": session_id,
            "contract_id": contract_id,
            **(metadata or {})
        }
        
        # Use Langfuse 2.x API - trace() method
        try:
            trace = self.client.trace(
                name=name,
                metadata=trace_metadata,
                session_id=session_id
            )
            return trace
        except AttributeError:
            # trace() method doesn't exist in this Langfuse version
            import warnings
            warnings.warn(
                "Langfuse trace() method not available. Using dummy trace. "
                "Please ensure you have langfuse>=2.0.0,<3.0.0 installed.",
                UserWarning
            )
            return DummyTrace()
        except Exception as e:
            # Other error, log and fallback to dummy trace
            import warnings
            warnings.warn(
                f"Error creating Langfuse trace: {str(e)}. Using dummy trace.",
                UserWarning
            )
            return DummyTrace()
    
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
        if isinstance(trace, DummyTrace):
            return trace  # Dummy trace returns itself
        
        try:
            if hasattr(trace, 'span'):
                return trace.span(
                    name=name,
                    input=input_data,
                    output=output_data,
                    metadata=metadata or {}
                )
            elif hasattr(trace, 'start_span'):
                return trace.start_span(
                    name=name,
                    input=input_data,
                    output=output_data,
                    metadata=metadata or {}
                )
            else:
                # Fallback if span method doesn't exist
                return DummyTrace()
        except Exception:
            return DummyTrace()
    
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
        if isinstance(trace, DummyTrace):
            return trace  # Dummy trace returns itself
        
        try:
            if hasattr(trace, 'generation'):
                return trace.generation(
                    name=name,
                    model=model,
                    input=input_data,
                    output=output_data,
                    usage=usage,
                    metadata=metadata or {}
                )
            elif hasattr(trace, 'start_generation'):
                return trace.start_generation(
                    name=name,
                    model=model,
                    input=input_data,
                    output=output_data,
                    usage=usage,
                    metadata=metadata or {}
                )
            else:
                # Fallback if generation method doesn't exist
                return DummyTrace()
        except Exception:
            return DummyTrace()


class DummyTrace:
    """Dummy trace object that implements trace methods but does nothing."""
    
    def span(self, *args, **kwargs):
        return self
    
    def generation(self, *args, **kwargs):
        return self
    
    def score(self, *args, **kwargs):
        pass
    
    def update(self, *args, **kwargs):
        pass
    
    def end(self, *args, **kwargs):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


# Global tracing manager instance
tracing_manager = TracingManager()
