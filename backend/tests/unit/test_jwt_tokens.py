"""Unit tests for JWT helpers (Phase 2.2.2)."""

from __future__ import annotations

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
    # Replace the signature segment with a clearly bogus one.
    head, payload, _sig = tok.rsplit(".", 2)
    tampered = f"{head}.{payload}.AAAA"
    assert decode_session_token(tampered) is None


def test_decode_rejects_expired_token(monkeypatch):
    """Issue a token whose exp is already in the past (negative TTL)."""
    from app.core import jwt_tokens

    monkeypatch.setattr(jwt_tokens.settings, "jwt_ttl_seconds", -10)
    tok = issue_session_token(uuid.uuid4())
    assert decode_session_token(tok) is None
