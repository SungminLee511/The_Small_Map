"""Unit tests for the Kakao OAuth client glue (Phase 2.2.2)."""

from __future__ import annotations

import pytest

from app.core.kakao_oauth import (
    KakaoProfile,
    _normalize_profile,
    build_authorize_url,
)


def test_authorize_url_contains_required_params():
    url = build_authorize_url(
        client_id="abc", redirect_uri="http://x/cb", state="STATE"
    )
    assert "kauth.kakao.com/oauth/authorize" in url
    assert "client_id=abc" in url
    assert "state=STATE" in url
    assert "redirect_uri=http%3A%2F%2Fx%2Fcb" in url
    assert "response_type=code" in url


def test_normalize_profile_full_payload():
    body = {
        "id": 12345,
        "kakao_account": {
            "email": "u@example.com",
            "profile": {
                "nickname": "Sungmin",
                "profile_image_url": "http://example.com/a.jpg",
            },
        },
    }
    p = _normalize_profile(body)
    assert isinstance(p, KakaoProfile)
    assert p.kakao_id == 12345
    assert p.display_name == "Sungmin"
    assert p.email == "u@example.com"
    assert p.avatar_url == "http://example.com/a.jpg"


def test_normalize_profile_missing_optional_fields():
    body = {"id": 999}
    p = _normalize_profile(body)
    assert p.kakao_id == 999
    assert p.display_name == "kakao-999"
    assert p.email is None
    assert p.avatar_url is None


def test_normalize_profile_missing_id_raises():
    with pytest.raises(RuntimeError):
        _normalize_profile({})


def test_normalize_profile_thumbnail_fallback():
    body = {
        "id": 1,
        "kakao_account": {
            "profile": {"nickname": "x", "thumbnail_image_url": "http://t.png"}
        },
    }
    p = _normalize_profile(body)
    assert p.avatar_url == "http://t.png"
