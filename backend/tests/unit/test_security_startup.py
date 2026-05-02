"""Unit tests for security_startup checks — Phase 5.4."""

from __future__ import annotations

import pytest

from app.core.security_startup import (
    InsecureProductionConfigError,
    check_settings,
    enforce_at_startup,
)


class _S:
    """Minimal settings stand-in."""

    def __init__(self, **kw):
        self.app_env = kw.get("app_env", "development")
        self.jwt_secret = kw.get("jwt_secret", "change-me")
        self.app_secret_key = kw.get("app_secret_key", "change-me")
        self.admin_token = kw.get("admin_token", "")
        self.frontend_base_url = kw.get("frontend_base_url", "http://localhost:5173")
        self.auth_cookie_secure = kw.get("auth_cookie_secure", False)


def test_default_settings_are_flagged():
    issues = check_settings(_S())
    assert any("jwt_secret" in i for i in issues)
    assert any("app_secret_key" in i for i in issues)
    assert any("admin_token" in i for i in issues)
    assert any("localhost" in i for i in issues)
    assert any("auth_cookie_secure" in i for i in issues)


def test_real_secrets_clear_main_warnings():
    settings = _S(
        jwt_secret="a-real-32-char-random-value-here-xx",
        app_secret_key="another-real-secret-value-here",
        admin_token="ops-admin-token",
        frontend_base_url="https://smallmap.example.com",
        auth_cookie_secure=True,
    )
    issues = check_settings(settings)
    assert issues == []


def test_dev_environment_only_warns():
    # Even with placeholders, dev should not raise.
    enforce_at_startup(_S(app_env="development"))


def test_production_with_placeholders_raises():
    settings = _S(app_env="production")
    with pytest.raises(InsecureProductionConfigError):
        enforce_at_startup(settings)


def test_production_passes_with_real_secrets():
    settings = _S(
        app_env="production",
        jwt_secret="a-real-32-char-random-value-here-xx",
        app_secret_key="another-real-secret-value-here",
        admin_token="ops-admin-token",
        frontend_base_url="https://smallmap.example.com",
        auth_cookie_secure=True,
    )
    enforce_at_startup(settings)  # no raise
