"""Unit tests for haversine geo helper (Phase 2.2.4)."""

from __future__ import annotations

from app.core.geo import haversine_m


def test_zero_distance():
    assert haversine_m(37.5, 126.9, 37.5, 126.9) == 0.0


def test_known_distance_seoul_one_degree_lat():
    # 1 degree of latitude ≈ 111 km regardless of longitude
    d = haversine_m(37.0, 126.9, 38.0, 126.9)
    assert 110_500 <= d <= 111_500


def test_short_distance_under_50m():
    # ~10m east of Mapo HQ (1 degree lng ≈ 88km at 37.5°N → 10m ≈ 0.000113°)
    d = haversine_m(37.566535, 126.901320, 37.566535, 126.901320 + 0.000113)
    assert 9.0 <= d <= 11.5


def test_symmetric():
    a = haversine_m(37.5, 126.9, 37.6, 127.0)
    b = haversine_m(37.6, 127.0, 37.5, 126.9)
    assert abs(a - b) < 1e-6
