"""Unit tests for the run_importers CLI argument parsing (1.3.5)."""

from __future__ import annotations

import pytest

from scripts.run_importers import REGISTRY, parse_args


def test_registry_contains_both_importers():
    assert "seoul.public_toilets" in REGISTRY
    assert "mapo.smoking_areas" in REGISTRY


def test_parse_args_source():
    args = parse_args(["--source", "seoul.public_toilets", "--csv", "/tmp/x.csv"])
    assert args.source == "seoul.public_toilets"
    assert args.csv == "/tmp/x.csv"
    assert args.dry_run is False
    assert args.all is False


def test_parse_args_all_dry_run():
    args = parse_args(["--all", "--dry-run"])
    assert args.all is True
    assert args.dry_run is True


def test_parse_args_requires_one_of_source_all():
    with pytest.raises(SystemExit):
        parse_args([])


def test_parse_args_rejects_unknown_source():
    with pytest.raises(SystemExit):
        parse_args(["--source", "made.up"])


def test_parse_args_default_encoding_cp949():
    args = parse_args(["--all"])
    assert args.encoding == "cp949"


def test_parse_args_xlsx_flag():
    args = parse_args(
        ["--source", "seoul.public_toilets", "--xlsx", "/tmp/toilets.xlsx"]
    )
    assert args.xlsx == "/tmp/toilets.xlsx"
