"""Run public-data importers.

Usage::

    python -m scripts.run_importers --source seoul.public_toilets --csv path.csv
    python -m scripts.run_importers --all --dry-run

Flags:
    --source X    only run importer with this source_id
    --all         run every registered importer
    --csv PATH    pass a local CSV path to importers that accept it
    --api-url URL pass an API URL to importers that accept it
    --dry-run     don't commit; print the would-be report
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import Callable

from app.db import async_session_factory
from app.importers.base import BaseImporter, ImportReport
from app.importers.seoul_public_toilets import SeoulPublicToiletsImporter
from app.importers.seoul_smoking_areas import (
    MapoSmokingAreasImporter,
    kakao_geocode,
)

logger = logging.getLogger("run_importers")

# Registry of importer factories. Each factory takes the parsed CLI args and
# returns a BaseImporter instance (or raises if required args missing).
ImporterFactory = Callable[[argparse.Namespace], BaseImporter]


def _make_toilets(args: argparse.Namespace) -> BaseImporter:
    return SeoulPublicToiletsImporter(
        csv_path=args.csv,
        api_url=args.api_url,
        encoding=args.encoding,
    )


def _make_smoking(args: argparse.Namespace) -> BaseImporter:
    geocoder = None
    if args.kakao_rest_key:
        async def geocoder(addr: str):  # noqa: E306
            return await kakao_geocode(addr, rest_api_key=args.kakao_rest_key)
    return MapoSmokingAreasImporter(
        csv_path=args.csv,
        geocoder=geocoder,
        encoding=args.encoding,
    )


REGISTRY: dict[str, ImporterFactory] = {
    SeoulPublicToiletsImporter.source_id: _make_toilets,
    MapoSmokingAreasImporter.source_id: _make_smoking,
}


async def _run_one(importer: BaseImporter, *, dry_run: bool) -> ImportReport:
    async with async_session_factory() as session:
        report = await importer.run(session)
        if dry_run:
            await session.rollback()
            logger.info("[DRY-RUN] rolled back changes for %s", importer.source_id)
    return report


async def run_all(
    importers: list[BaseImporter], *, dry_run: bool
) -> list[ImportReport]:
    reports: list[ImportReport] = []
    for imp in importers:
        try:
            reports.append(await _run_one(imp, dry_run=dry_run))
        except Exception as e:  # noqa: BLE001
            logger.exception("Importer %s crashed: %s", imp.source_id, e)
            reports.append(
                ImportReport(source_id=imp.source_id, errors=[f"crashed: {e}"])
            )
    return reports


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run public-data importers")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--source",
        choices=sorted(REGISTRY.keys()),
        help="Run a single importer by source_id",
    )
    g.add_argument("--all", action="store_true", help="Run every importer")
    p.add_argument("--csv", help="Local CSV path (passed to importers that accept it)")
    p.add_argument("--api-url", help="HTTP API URL (passed to importers that accept it)")
    p.add_argument("--encoding", default="cp949", help="CSV encoding (default cp949)")
    p.add_argument(
        "--kakao-rest-key",
        help="Kakao REST API key for geocoding (smoking-areas importer)",
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Don't commit DB changes; print report"
    )
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    return p.parse_args(argv)


async def amain(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if args.all:
        factories = list(REGISTRY.values())
    else:
        factories = [REGISTRY[args.source]]

    importers: list[BaseImporter] = []
    for factory in factories:
        try:
            importers.append(factory(args))
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to construct importer: %s", e)
            return 2

    reports = await run_all(importers, dry_run=args.dry_run)

    print("\n=== Importer reports ===")
    rc = 0
    for r in reports:
        print(r)
        if r.errors:
            for err in r.errors:
                print(f"  ! {err}")
            rc = 1
    return rc


def main() -> None:
    sys.exit(asyncio.run(amain()))


if __name__ == "__main__":
    main()
