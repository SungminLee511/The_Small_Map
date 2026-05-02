"""Unit tests for the admin router auth gate (1.3.6)."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.routers.admin import _require_admin


def test_require_admin_disabled_when_token_unset(monkeypatch):
    from app.routers import admin as admin_mod

    monkeypatch.setattr(admin_mod.settings, "admin_token", "")
    with pytest.raises(HTTPException) as exc:
        _require_admin("anything")
    assert exc.value.status_code == 503


def test_require_admin_rejects_missing_token(monkeypatch):
    from app.routers import admin as admin_mod

    monkeypatch.setattr(admin_mod.settings, "admin_token", "secret")
    with pytest.raises(HTTPException) as exc:
        _require_admin(None)
    assert exc.value.status_code == 401


def test_require_admin_rejects_bad_token(monkeypatch):
    from app.routers import admin as admin_mod

    monkeypatch.setattr(admin_mod.settings, "admin_token", "secret")
    with pytest.raises(HTTPException) as exc:
        _require_admin("wrong")
    assert exc.value.status_code == 401


def test_require_admin_accepts_correct_token(monkeypatch):
    from app.routers import admin as admin_mod

    monkeypatch.setattr(admin_mod.settings, "admin_token", "secret")
    # Should not raise
    _require_admin("secret")
