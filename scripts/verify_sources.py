from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def read_json(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def validate_source_registry() -> list[str]:
    errors: list[str] = []
    sources = {source["id"]: source for source in read_json("sources.json")}
    files = ["national_rules.json", "regional_rules.json", "municipal_holidays.json"]

    for file_name in files:
        for row in read_json(file_name):
            for source_id in row.get("sources", []):
                if source_id not in sources:
                    errors.append(f"{file_name}: unknown source id {source_id}")

    for source in sources.values():
        try:
            response = requests.get(
                source["url"],
                headers={"User-Agent": "pt-holidays-api/0.1"},
                timeout=30,
            )
            if response.status_code >= 400:
                errors.append(f"{source['id']}: HTTP {response.status_code}")
        except requests.RequestException as exc:
            if not source.get("allow_insecure_tls"):
                errors.append(f"{source['id']}: {exc}")
                continue

            try:
                response = requests.get(
                    source["url"],
                    headers={"User-Agent": "pt-holidays-api/0.1"},
                    timeout=30,
                    verify=False,
                )
                if response.status_code >= 400:
                    errors.append(f"{source['id']}: HTTP {response.status_code} with TLS fallback")
                else:
                    print(f"WARN: {source['id']} required insecure TLS fallback.")
            except requests.RequestException as fallback_exc:
                errors.append(f"{source['id']}: {fallback_exc}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source coverage and source URLs.")
    parser.add_argument("--skip-url-check", action="store_true")
    args = parser.parse_args()

    municipal = read_json("municipal_holidays.json")
    errors: list[str] = []

    if len(municipal) != 308:
        errors.append(f"Expected 308 municipalities, found {len(municipal)}.")

    missing = [row["municipality"] for row in municipal if len(row.get("sources", [])) < 2]
    if missing:
        errors.append("Municipalities with fewer than two sources: " + ", ".join(missing[:20]))

    if not args.skip_url_check:
        errors.extend(validate_source_registry())

    if errors:
        print("Verification failures:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK: {len(municipal)} municipalities have at least two registered sources.")
    print("OK: all referenced source ids exist and source URLs responded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
