"""Unit tests for confirmation service helpers (Phase 2.2.7)."""

from __future__ import annotations

import uuid

from app.services.confirmation_service import (
    VERIFICATION_THRESHOLD,
    _submitter_id_from_source,
)


def test_submitter_id_from_source_user():
    uid = uuid.uuid4()
    assert _submitter_id_from_source(f"user:{uid}") == uid


def test_submitter_id_from_source_seed():
    assert _submitter_id_from_source("seed") is None


def test_submitter_id_from_source_importer():
    assert _submitter_id_from_source("seoul.public_toilets") is None


def test_submitter_id_from_source_garbled():
    assert _submitter_id_from_source("user:not-a-uuid") is None


def test_threshold_is_three():
    # Submitter (1) + 2 confirmers
    assert VERIFICATION_THRESHOLD == 3
