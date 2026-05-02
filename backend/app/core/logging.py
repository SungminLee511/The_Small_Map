"""Structured JSON logging — Phase 5.1.

Stdlib-only. No structlog dependency to keep the test environment cheap.
The ``JsonFormatter`` emits one JSON object per record so logs are easy to
ingest by any log shipper (Loki, Datadog, CloudWatch).

Usage::

    from app.core.logging import setup_logging
    setup_logging(level="INFO")

    import logging
    log = logging.getLogger("smallmap.poi")
    log.info("created", extra={"poi_id": str(poi.id)})

The request middleware in ``app.core.request_logging`` adds per-request
fields (``method``, ``path``, ``status``, ``latency_ms``, ``user_id``,
``client_ip``) and is wired in ``app.main``.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Reserved attributes on a LogRecord — anything else in record.__dict__ is
# treated as a structured field (set via ``log.info(..., extra={...})``).
_RECORD_RESERVED = {
    "name", "msg", "args", "levelname", "levelno", "pathname",
    "filename", "module", "exc_info", "exc_text", "stack_info",
    "lineno", "funcName", "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process", "message",
    "asctime", "taskName",
}

# Field names that should be redacted regardless of where they appear.
# Keep this list short and obvious — use it to scrub anything that might
# accidentally end up in ``extra``.
_REDACTED_KEYS = {
    "password", "token", "jwt", "authorization", "cookie",
    "set-cookie", "kakao_access_token", "secret",
}


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: ("[REDACTED]" if k.lower() in _REDACTED_KEYS else _redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


class JsonFormatter(logging.Formatter):
    """One-line JSON per record."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Pull structured extras off the record.
        for key, value in record.__dict__.items():
            if key in _RECORD_RESERVED or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        try:
            return json.dumps(_redact(payload), default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            # Last-ditch fallback — never let logging itself raise.
            return json.dumps(
                {
                    "ts": payload["ts"],
                    "level": payload["level"],
                    "logger": payload["logger"],
                    "message": str(record.getMessage()),
                    "_format_error": True,
                }
            )


def setup_logging(level: str = "INFO") -> None:
    """Replace the root handler with a single JSON stream handler.

    Idempotent — safe to call multiple times (e.g. during tests).
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    # Tame the noisiest libraries.
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "botocore", "boto3"):
        logging.getLogger(noisy).setLevel("WARNING")
