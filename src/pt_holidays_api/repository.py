from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .calendar import resolve_rule
from .models import Coverage, DistrictSummary, Holiday, MunicipalitySummary, RegionSummary, SourceRef

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


def list_regions() -> list[RegionSummary]:
    regions: dict[str, list[dict]] = {}
    for rule in regional_rules():
        regions.setdefault(rule["region"], []).append(rule)

    return [
        RegionSummary(
            region=region,
            available_years="calculated by rule",
            holidays=[
                {
                    "name": rule["name"],
                    "start_year": rule.get("start_year", 1900),
                    "sources": rule["sources"],
                    "verification_status": rule["verification_status"],
                    "confidence": rule["confidence"],
                }
                for rule in sorted(items, key=lambda item: (item.get("start_year", 1900), item["name"]))
            ],
        )
        for region, items in sorted(regions.items())
    ]


def list_districts() -> list[DistrictSummary]:
    districts: dict[str, list[dict]] = {}
    for item in municipal_data():
        districts.setdefault(item["district"], []).append(item)

    return [
        DistrictSummary(
            district=district,
            municipality_count=len(items),
            municipality_names=sorted(item["municipality"] for item in items),
            available_years=sorted({int(year) for item in items for year in item["years"]}),
        )
        for district, items in sorted(districts.items())
    ]


def list_municipalities() -> list[MunicipalitySummary]:
    return [
        MunicipalitySummary(
            municipality=item["municipality"],
            district=item["district"],
            holiday_name=item["name"],
            available_years=sorted(int(year) for year in item["years"]),
            sources=item["sources"],
            verification_status=item["verification_status"],
            confidence=item["confidence"],
        )
        for item in sorted(municipal_data(), key=lambda row: row["municipality"])
    ]


def get_holidays(
    year: int,
    region: str | None = None,
    district: str | None = None,
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

    regional_names = {_normalize(rule["region"]): rule["region"] for rule in regional_rules()}
    effective_region = region
    if not effective_region and district and _normalize(district) in regional_names:
        effective_region = regional_names[_normalize(district)]

    if effective_region:
        region_key = _normalize(effective_region)
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
        municipality_key = _normalize(municipality) if municipality else None
        district_key = _normalize(district) if district else None
        for item in municipal_data():
            if municipality_key and _normalize(item["municipality"]) != municipality_key:
                continue
            if district_key and _normalize(item["district"]) != district_key:
                continue

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
