from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from import_icalendario import load_municipal_holidays

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh external holiday data and optionally fail if files changed."
    )
    parser.add_argument("--check", action="store_true", help="Do not write files; fail on drift.")
    parser.add_argument("--fix", action="store_true", help="Write refreshed data files.")
    args = parser.parse_args()

    if args.check and args.fix:
        parser.error("--check and --fix cannot be used together")

    municipal = load_municipal_holidays()
    new_content = json.dumps(municipal, ensure_ascii=False, indent=2) + "\n"
    target = DATA_DIR / "municipal_holidays.json"
    current = target.read_text(encoding="utf-8")

    if current != new_content:
        if args.fix:
            target.write_text(new_content, encoding="utf-8")
            print("Updated data/municipal_holidays.json from external source.")
        else:
            print("data/municipal_holidays.json differs from the external source.")
            return 1
    else:
        print("OK: data/municipal_holidays.json is current.")

    verify_cmd = [sys.executable, str(Path(__file__).with_name("verify_sources.py"))]
    return subprocess.call(verify_cmd)


if __name__ == "__main__":
    raise SystemExit(main())
