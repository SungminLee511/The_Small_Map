"""Sanity check the canonical reputation deltas (Phase 4.2.5 / 4.2.1)."""

from __future__ import annotations

from app.models.reputation_event import EVENT_DELTAS, ReputationEventType


def test_canonical_deltas_match_plan():
    assert EVENT_DELTAS[ReputationEventType.poi_submitted_verified] == 5
    assert EVENT_DELTAS[ReputationEventType.poi_submitted_rejected] == -3
    assert EVENT_DELTAS[ReputationEventType.confirmation] == 1
    assert EVENT_DELTAS[ReputationEventType.report_submitted_resolved] == 2
    assert EVENT_DELTAS[ReputationEventType.report_dismissed_admin] == -5
    assert EVENT_DELTAS[ReputationEventType.daily_active] == 0


def test_every_event_type_has_a_delta():
    for et in ReputationEventType:
        assert et in EVENT_DELTAS
