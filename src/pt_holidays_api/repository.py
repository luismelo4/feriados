from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .calendar import resolve_rule
from .models import Coverage, Holiday, SourceRef

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read_json(name: str):
    with (DATA_DIR / name).open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache
def national_rules() -> list[dict]:
    return _read_json("national_rules.json")


@lru_cache
def regional_rules() -> list[dict]:
    return _read_json("regional_rules.json")


@lru_cache
def municipal_data() -> list[dict]:
    return _read_json("municipal_holidays.json")


@lru_cache
def sources() -> dict[str, SourceRef]:
    raw = _read_json("sources.json")
    return {item["id"]: SourceRef(**item) for item in raw}


def list_sources() -> list[SourceRef]:
    return list(sources().values())


def list_municipalities() -> list[dict]:
    return [
        {
            "municipality": item["municipality"],
            "district": item["district"],
            "available_years": sorted(int(year) for year in item["years"]),
            "verification_status": item["verification_status"],
        }
        for item in sorted(municipal_data(), key=lambda row: row["municipality"])
    ]


def get_holidays(
    year: int,
    region: str | None = None,
    municipality: str | None = None,
) -> list[Holiday]:
    holidays: list[Holiday] = []

    for rule in national_rules():
        holidays.append(
            Holiday(
                date=resolve_rule(year, rule["rule"]),
                name=rule["name"],
                scope="national",
                sources=rule["sources"],
                verification_status=rule["verification_status"],
                confidence=rule["confidence"],
            )
        )

    if region:
        region_key = _normalize(region)
        for rule in regional_rules():
            if year < rule.get("start_year", 1900):
                continue
            if _normalize(rule["region"]) == region_key:
                holidays.append(
                    Holiday(
                        date=resolve_rule(year, rule["rule"]),
                        name=rule["name"],
                        scope="regional",
                        region=rule["region"],
                        sources=rule["sources"],
                        verification_status=rule["verification_status"],
                        confidence=rule["confidence"],
                    )
                )

    if municipality:
        municipality_key = _normalize(municipality)
        for item in municipal_data():
            if _normalize(item["municipality"]) == municipality_key:
                year_key = str(year)
                if year_key not in item["years"]:
                    continue
                holidays.append(
                    Holiday(
                        date=item["years"][year_key],
                        name=item["name"],
                        scope="municipal",
                        district=item["district"],
                        municipality=item["municipality"],
                        sources=item["sources"],
                        verification_status=item["verification_status"],
                        confidence=item["confidence"],
                    )
                )

    return sorted(holidays, key=lambda holiday: (holiday.date, holiday.scope, holiday.name))


def coverage() -> Coverage:
    municipal_years = sorted(
        {int(year) for item in municipal_data() for year in item["years"].keys()}
    )
    return Coverage(
        national_years="calculated by rule",
        regional_years="calculated by rule",
        municipal_years=municipal_years,
        municipalities=len(municipal_data()),
        verification_policy=(
            "verified = legal/official primary source plus secondary check; "
            "cross_checked = two or more concordant secondary sources; "
            "needs_primary_source = useful data but still needs municipal/legal confirmation"
        ),
    )


def _normalize(value: str) -> str:
    return value.casefold().strip()
