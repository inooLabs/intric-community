import contextlib
import os

import httpx
import openai

from intric.main.config import get_settings
from intric.main.logging import get_logger

logger = get_logger(__name__)

_traced_async_openai = None


def propagate_trace_attributes():
    """Attach the configured user to all LLM spans created in this context.

    Wraps completion/embedding calls so the drop-in's root spans carry the
    trace-level attributes (user.id etc.) that Langfuse hoists onto traces.
    """
    settings = get_settings()
    if not (settings.langfuse_enabled and settings.langfuse_user_id):
        return contextlib.nullcontext()

    try:
        from langfuse import propagate_attributes

        return propagate_attributes(user_id=settings.langfuse_user_id)
    except Exception as e:
        logger.debug(f"Langfuse attribute propagation skipped: {e}")
        return contextlib.nullcontext()


def _disable_export_tls_verification():
    """Langfuse's OTEL span exporter (urllib3-based OTLPSpanExporter) verifies
    TLS by default. Self-hosted instances behind self-signed certificates need
    verification disabled for trace export to work."""
    import requests
    import urllib3

    import langfuse._client.span_processor as span_processor_module

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    _original = span_processor_module.OTLPSpanExporter
    _session = requests.Session()
    _session.verify = False

    def _patched(*args, **kwargs):
        exporter = _original(*args, **kwargs)
        # Newer OTLP exporters default certificate_file to True and pass
        # verify=certificate_file explicitly on every POST, overriding the
        # session's verify setting. Force it off on the instance.
        exporter._certificate_file = False
        return exporter

    span_processor_module.OTLPSpanExporter = _patched
    return True


def init_langfuse():
    global _traced_async_openai
    settings = get_settings()

    if not (
        settings.langfuse_enabled
        and settings.langfuse_public_key
        and settings.langfuse_secret_key
    ):
        return

    try:
        # Fallback config for anything reading env vars directly
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host

        import langfuse.openai  # noqa: F401  (registers the OpenAI integration)
        from langfuse import Langfuse
        from langfuse.openai import AsyncOpenAI as TracedAsyncOpenAI

        # Trace export must skip TLS verification (self-signed certs)
        export_tls_patched = _disable_export_tls_verification()

        # Create the global client first so the OpenAI drop-in reuses it.
        # The custom httpx client covers non-tracing API requests (auth check,
        # media upload) — the OTEL export path is patched above.
        Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
            environment=settings.langfuse_environment,
            httpx_client=httpx.Client(verify=False),
            debug=settings.langfuse_debug,
        )

        _traced_async_openai = TracedAsyncOpenAI
        logger.info(
            f"Langfuse tracing enabled at {settings.langfuse_host} "
            f"(export TLS verify disabled: {export_tls_patched})"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse: {e}")


def create_async_openai_client(**kwargs) -> openai.AsyncOpenAI:
    """Create an AsyncOpenAI client, traced via Langfuse when enabled."""
    if _traced_async_openai is not None:
        return _traced_async_openai(**kwargs)

    return openai.AsyncOpenAI(**kwargs)
