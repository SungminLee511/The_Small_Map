"""Startup security checks — Phase 5.4.

Bail out at import-time if production config is obviously unsafe.
Currently catches:

- ``jwt_secret`` / ``app_secret_key`` left at the ``change-me`` placeholder
- ``admin_token`` empty (admin endpoints would 401 silently, but a
  production deploy without one is almost certainly a misconfig — warn)
- CORS frontend URL still pointing at localhost in production

In non-production environments these are warnings only.
"""

from __future__ import annotations

import logging

log = logging.getLogger("smallmap.security")

PLACEHOLDERS = {"", "change-me", "changeme", "secret"}


class InsecureProductionConfigError(RuntimeError):
    pass


def check_settings(settings) -> list[str]:
    """Return the list of issues found. Raises in production if any.

    Always safe to call. The caller decides whether to raise or just log.
    """
    issues: list[str] = []

    if str(settings.jwt_secret).strip().lower() in PLACEHOLDERS:
        issues.append("jwt_secret is unset or placeholder")
    if str(settings.app_secret_key).strip().lower() in PLACEHOLDERS:
        issues.append("app_secret_key is unset or placeholder")
    if not settings.admin_token:
        issues.append("admin_token is empty (admin endpoints unreachable)")
    if "localhost" in (settings.frontend_base_url or "").lower():
        issues.append("frontend_base_url still points at localhost")
    if not settings.auth_cookie_secure:
        issues.append("auth_cookie_secure=False (cookies sent over HTTP)")

    return issues


def enforce_at_startup(settings) -> None:
    """Log every issue. In production, raise on the critical subset."""
    issues = check_settings(settings)
    for msg in issues:
        log.warning("startup_security_issue", extra={"issue": msg})

    if str(settings.app_env).lower() == "production":
        critical = [
            i
            for i in issues
            if i.startswith("jwt_secret")
            or i.startswith("app_secret_key")
            or i.startswith("auth_cookie_secure")
        ]
        if critical:
            raise InsecureProductionConfigError(
                "refusing to boot with insecure production config: "
                + "; ".join(critical)
            )
