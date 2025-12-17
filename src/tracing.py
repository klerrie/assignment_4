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
            "contract_id": contract_id,
            **(metadata or {})
        }
        
        # Use Langfuse 2.x API - start_as_current_span creates a trace automatically
        try:
            # In Langfuse 2.x, the first span becomes the root span (trace)
            span_context = self.client.start_as_current_span(
                name=name,
                metadata=trace_metadata
            )
            # Enter the context to get the span object
            span_obj = span_context.__enter__()
            # Update the trace with session_id (must be done separately)
            self.client.update_current_trace(session_id=session_id)
            # Wrap the span in a TraceWrapper to provide trace-like interface
            return TraceWrapper(span_obj, span_context)
        except AttributeError:
            # Fallback: try alternative method if start_as_current_span doesn't exist
            try:
                observation_context = self.client.start_as_current_observation(
                    name=name,
                    as_type="span",
                    metadata=trace_metadata
                )
                span_obj = observation_context.__enter__()
                self.client.update_current_trace(session_id=session_id)
                return TraceWrapper(span_obj, observation_context)
            except (AttributeError, Exception):
                import warnings
                warnings.warn(
                    "Langfuse span methods not available. Using dummy trace. "
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
        
        # TraceWrapper and Langfuse span objects both support span/start_span methods
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
        
        # TraceWrapper and Langfuse span objects both support generation/start_generation methods
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


class TraceWrapper:
    """Wrapper for Langfuse span that provides trace-like interface."""
    
    def __init__(self, span, context_manager):
        self.span_obj = span
        self.context_manager = context_manager
    
    def span(self, *args, **kwargs):
        """Create a span - delegates to start_span if span() doesn't exist."""
        if hasattr(self.span_obj, 'span'):
            return self.span_obj.span(*args, **kwargs)
        elif hasattr(self.span_obj, 'start_span'):
            return self.span_obj.start_span(*args, **kwargs)
        return self
    
    def generation(self, *args, **kwargs):
        """Create a generation - delegates to start_generation if generation() doesn't exist."""
        if hasattr(self.span_obj, 'generation'):
            return self.span_obj.generation(*args, **kwargs)
        elif hasattr(self.span_obj, 'start_generation'):
            return self.span_obj.start_generation(*args, **kwargs)
        return self
    
    def start_span(self, *args, **kwargs):
        """Delegate to span object's start_span."""
        if hasattr(self.span_obj, 'start_span'):
            return self.span_obj.start_span(*args, **kwargs)
        return self
    
    def start_generation(self, *args, **kwargs):
        """Delegate to span object's start_generation."""
        if hasattr(self.span_obj, 'start_generation'):
            return self.span_obj.start_generation(*args, **kwargs)
        return self
    
    def score(self, *args, **kwargs):
        """Delegate score calls to span object if available."""
        if hasattr(self.span_obj, 'score'):
            return self.span_obj.score(*args, **kwargs)
        pass
    
    def update(self, *args, **kwargs):
        """Delegate update calls to span object if available."""
        if hasattr(self.span_obj, 'update'):
            return self.span_obj.update(*args, **kwargs)
        pass
    
    def end(self, *args, **kwargs):
        """End the span by exiting the context manager."""
        if self.context_manager:
            self.context_manager.__exit__(None, None, None)
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        if self.context_manager:
            self.context_manager.__exit__(*args)


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
