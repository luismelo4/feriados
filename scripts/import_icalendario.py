from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from urllib.request import urlopen

URL = "https://icalendario.pt/feriados/municipais/"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

DISTRICTS = [
    "Viana do Castelo",
    "Castelo Branco",
    "Vila Real",
    "Braganca",
    "Santarem",
    "Portalegre",
    "Setubal",
    "Madeira",
    "Acores",
    "Aveiro",
    "Beja",
    "Braga",
    "Coimbra",
    "Evora",
    "Faro",
    "Guarda",
    "Leiria",
    "Lisboa",
    "Porto",
    "Viseu",
]

MONTHS = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

WEEKDAYS = r"(?:seg|ter|qua|qui|sex|sab|dom)\."
DATE_RE = re.compile(rf"{WEEKDAYS} (\d{{1,2}}) ([a-z]+)")


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def parse_row(match: re.Match[str]) -> dict:
    dates = [
        (match.group("d2026"), match.group("m2026")),
        (match.group("d2027"), match.group("m2027")),
        (match.group("d2028"), match.group("m2028")),
    ]
    if len(dates) != 3:
        raise ValueError("Could not parse dates from row")

    municipality = match.group("municipality").strip()
    district = match.group("district").strip()
    name = match.group("name").strip()

    years = {}
    for year, (day, month_name) in zip((2026, 2027, 2028), dates, strict=True):
        years[str(year)] = date(year, MONTHS[month_name], int(day)).isoformat()

    return {
        "municipality": municipality,
        "district": district,
        "name": name,
        "years": years,
        "sources": ["icalendario_municipais", "dirportugal_municipais", "aspl_municipais_pdf"],
        "verification_status": "cross_checked",
        "confidence": 0.85,
    }


def load_municipal_holidays() -> list[dict]:
    html = urlopen(URL, timeout=30).read().decode("utf-8")
    text = re.sub(r"<[^>]+>", "\n", html)
    text = strip_accents(re.sub(r"\s+", " ", text))
    start = text.index("Abrantes Santarem")
    end = text.index(" Feriados Feriados municipais", start)
    rows_text = text[start:end]
    district_pattern = "|".join(re.escape(strip_accents(district)) for district in DISTRICTS)
    row_pattern = re.compile(
        rf"(?P<municipality>.+?) (?P<district>{district_pattern}) (?P<name>.+?) "
        rf"{WEEKDAYS} (?P<d2026>\d{{1,2}}) (?P<m2026>[a-z]+) "
        rf"{WEEKDAYS} (?P<d2027>\d{{1,2}}) (?P<m2027>[a-z]+) "
        rf"{WEEKDAYS} (?P<d2028>\d{{1,2}}) (?P<m2028>[a-z]+)",
        re.DOTALL,
    )

    parsed = [parse_row(match) for match in row_pattern.finditer(rows_text)]
    if len(parsed) != 308:
        raise ValueError(f"Expected 308 municipalities, got {len(parsed)}")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Import municipal holidays from iCalendario.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fetch and compare with data/municipal_holidays.json without writing.",
    )
    args = parser.parse_args()

    parsed = load_municipal_holidays()
    output = DATA_DIR / "municipal_holidays.json"
    new_content = json.dumps(parsed, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        current = output.read_text(encoding="utf-8")
        if current != new_content:
            print("data/municipal_holidays.json is out of date. Run without --check to refresh.")
            return 1
        print("OK: municipal holidays match the current iCalendario source.")
        return 0

    output.write_text(new_content, encoding="utf-8")
    print(f"Wrote {len(parsed)} municipalities to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
