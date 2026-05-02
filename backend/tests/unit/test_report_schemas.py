"""Pydantic schema sanity for reports (Phase 3.3.6 unit tests)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.report import (
    ReportCreate,
    ReportDismissBody,
    ReportResolveBody,
)


def test_report_create_minimal():
    r = ReportCreate.model_validate({"report_type": "out_of_order"})
    assert r.report_type.value == "out_of_order"
    assert r.description is None
    assert r.photo_url is None


def test_report_create_rejects_unknown_type():
    with pytest.raises(ValidationError):
        ReportCreate.model_validate({"report_type": "exploded"})


def test_report_create_long_description_rejected():
    with pytest.raises(ValidationError):
        ReportCreate.model_validate(
            {"report_type": "dirty", "description": "x" * 501}
        )


def test_resolve_body_requires_note():
    with pytest.raises(ValidationError):
        ReportResolveBody.model_validate({})
    with pytest.raises(ValidationError):
        ReportResolveBody.model_validate({"resolution_note": ""})
    ok = ReportResolveBody.model_validate({"resolution_note": "fixed today"})
    assert ok.resolution_note == "fixed today"


def test_dismiss_body_optional_reason():
    a = ReportDismissBody.model_validate({})
    assert a.reason is None
    b = ReportDismissBody.model_validate({"reason": "spam"})
    assert b.reason == "spam"
