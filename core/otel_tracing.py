# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
OpenTelemetry tracing configuration for SWARMZ.

Provides distributed tracing for LLM calls, agent operations, and system events.
Can export to AI Toolkit (gRPC on port 4317) or console for debugging.
"""

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Lazy import OpenTelemetry to avoid hard dependency
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.trace import Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    TracerProvider = None


_tracer: Optional[Any] = None
_enabled: bool = False


def configure_otel_providers(
    vs_code_extension_port: int = 4317,
    enable_sensitive_data: bool = False,
    console_export: bool = False,
) -> bool:
    """
    Configure OpenTelemetry tracing for SWARMZ.

    Args:
        vs_code_extension_port: gRPC port for AI Toolkit (default 4317)
        enable_sensitive_data: Whether to capture prompts/completions in spans
        console_export: Also export to console for debugging

    Returns:
        True if configuration succeeded, False otherwise
    """
    global _tracer, _enabled

    if not OTEL_AVAILABLE:
        print(
            "[OTEL] OpenTelemetry not available. Install: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp"
        )
        return False

    # Allow disabling via environment
    if os.getenv("OTEL_DISABLED", "").lower() in ("1", "true", "yes"):
        print("[OTEL] Tracing disabled via OTEL_DISABLED environment variable")
        return False

    try:
        # Configure resource with service info
        resource = Resource(
            attributes={
                SERVICE_NAME: "swarmz",
                "service.version": "1.0",
                "deployment.environment": os.getenv("SWARMZ_ENV", "development"),
            }
        )

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Add OTLP exporter (AI Toolkit)
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=f"localhost:{vs_code_extension_port}",
                insecure=True,  # Local development
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            print(
                f"[OTEL] Configured OTLP exporter to localhost:{vs_code_extension_port}"
            )
        except Exception as e:
            print(f"[OTEL] Warning: Could not configure OTLP exporter: {e}")

        # Add console exporter if requested
        if console_export:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
            print("[OTEL] Configured console exporter for debugging")

        # Set global tracer provider
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("swarmz.core")
        _enabled = True

        # Store sensitive data setting
        os.environ["SWARMZ_OTEL_SENSITIVE"] = str(enable_sensitive_data)

        print("[OTEL] Tracing configured successfully")
        return True

    except Exception as e:
        print(f"[OTEL] Failed to configure tracing: {e}")
        return False


def is_tracing_enabled() -> bool:
    """Check if OpenTelemetry tracing is enabled."""
    return _enabled and _tracer is not None


def get_tracer():
    """Get the configured tracer, or None if tracing is disabled."""
    return _tracer


@contextmanager
def trace_operation(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True,
):
    """
    Context manager for tracing an operation.

    Usage:
        with trace_operation("llm_call", {"provider": "openai", "model": "gpt-4"}):
            result = call_llm(...)
    """
    if not is_tracing_enabled():
        yield None
        return

    span = _tracer.start_span(operation_name)

    # Add attributes
    if attributes:
        for key, value in attributes.items():
            # Sanitize based on sensitive data setting
            if not _should_capture_sensitive() and _is_sensitive_key(key):
                value = "[REDACTED]"
            span.set_attribute(key, str(value))

    try:
        yield span
        span.set_status(Status(StatusCode.OK))
    except Exception as e:
        span.set_status(Status(StatusCode.ERROR, str(e)))
        if record_exception:
            span.record_exception(e)
        raise
    finally:
        span.end()


def add_event(span, name: str, attributes: Optional[Dict[str, Any]] = None):
    """Add an event to the current span."""
    if span and is_tracing_enabled():
        span.add_event(name, attributes or {})


def _should_capture_sensitive() -> bool:
    """Check if sensitive data (prompts/completions) should be captured."""
    return os.getenv("SWARMZ_OTEL_SENSITIVE", "false").lower() in ("true", "1", "yes")


def _is_sensitive_key(key: str) -> bool:
    """Check if a key contains sensitive data."""
    sensitive_keys = {
        "prompt",
        "completion",
        "message",
        "messages",
        "system",
        "user_input",
        "assistant_response",
        "api_key",
        "token",
        "password",
        "secret",
    }
    return any(s in key.lower() for s in sensitive_keys)


# Convenience function for tracing LLM calls
@contextmanager
def trace_llm_call(
    provider: str, model: str, operation: str = "chat.completion", **kwargs
):
    """
    Specialized context manager for tracing LLM API calls.

    Usage:
        with trace_llm_call("openai", "gpt-4", messages=messages) as span:
            response = make_api_call(...)
            if span:
                span.set_attribute("response.tokens", response.usage.total_tokens)
    """
    attributes = {
        "llm.provider": provider,
        "llm.model": model,
        "llm.operation": operation,
    }

    # Add additional attributes
    for key, value in kwargs.items():
        if not _is_sensitive_key(key) or _should_capture_sensitive():
            attributes[f"llm.{key}"] = value

    with trace_operation(f"llm.{operation}", attributes) as span:
        yield span
