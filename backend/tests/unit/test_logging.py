"""Unit tests for app.core.logging — Phase 5.1."""

from __future__ import annotations

import json
import logging

from app.core.logging import JsonFormatter, setup_logging


def _make_record(msg: str = "hi", level: int = logging.INFO, **extra) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test", level=level, pathname=__file__, lineno=10,
        msg=msg, args=(), exc_info=None,
    )
    for k, v in extra.items():
        setattr(record, k, v)
    return record


def test_formatter_emits_valid_json_with_core_fields():
    fmt = JsonFormatter()
    line = fmt.format(_make_record("hello"))
    payload = json.loads(line)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "test"
    assert payload["message"] == "hello"
    assert "ts" in payload  # ISO 8601


def test_formatter_includes_extra_fields():
    fmt = JsonFormatter()
    line = fmt.format(_make_record("req", method="GET", path="/x", status=200))
    payload = json.loads(line)

    assert payload["method"] == "GET"
    assert payload["path"] == "/x"
    assert payload["status"] == 200


def test_formatter_redacts_secrets():
    fmt = JsonFormatter()
    line = fmt.format(_make_record("auth", token="abc123", password="hunter2"))
    payload = json.loads(line)

    assert payload["token"] == "[REDACTED]"
    assert payload["password"] == "[REDACTED]"


def test_formatter_redacts_nested_secrets():
    fmt = JsonFormatter()
    line = fmt.format(_make_record("auth", body={"cookie": "x", "ok": True}))
    payload = json.loads(line)

    assert payload["body"] == {"cookie": "[REDACTED]", "ok": True}


def test_formatter_handles_unserializable_extras():
    fmt = JsonFormatter()

    class Weird:
        def __repr__(self) -> str:
            return "<weird>"

    line = fmt.format(_make_record("x", obj=Weird()))
    payload = json.loads(line)
    # default=str fallback should turn the object into its repr.
    assert payload["obj"] == "<weird>"


def test_setup_logging_is_idempotent():
    setup_logging("DEBUG")
    setup_logging("INFO")  # second call should not stack handlers
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
