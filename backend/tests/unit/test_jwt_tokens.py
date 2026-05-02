"""Unit tests for JWT helpers (Phase 2.2.2)."""

from __future__ import annotations

import time
import uuid

from app.core.jwt_tokens import (
    decode_session_token,
    issue_session_token,
    make_oauth_state,
)


def test_round_trip():
    uid = uuid.uuid4()
    tok = issue_session_token(uid)
    assert decode_session_token(tok) == uid


def test_garbage_token_returns_none():
    assert decode_session_token("not.a.token") is None
    assert decode_session_token("") is None


def test_oauth_state_random():
    a = make_oauth_state()
    b = make_oauth_state()
    assert a != b
    assert len(a) >= 32


def test_decode_rejects_tampered_token():
    uid = uuid.uuid4()
    tok = issue_session_token(uid)
    # Flip the last char of the signature
    tampered = tok[:-1] + ("A" if tok[-1] != "A" else "B")
    assert decode_session_token(tampered) is None


def test_decode_rejects_expired_token(monkeypatch):
    from app.core import jwt_tokens

    # Force a 1-second token then sleep past it
    monkeypatch.setattr(jwt_tokens.settings, "jwt_ttl_seconds", 1)
    tok = issue_session_token(uuid.uuid4())
    time.sleep(1.5)
    assert decode_session_token(tok) is None
