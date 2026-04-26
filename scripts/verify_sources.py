from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main() -> int:
    municipal = json.loads((DATA_DIR / "municipal_holidays.json").read_text(encoding="utf-8"))
    missing = [row["municipality"] for row in municipal if len(row.get("sources", [])) < 2]
    if missing:
        print("Municipios com menos de duas fontes:", ", ".join(missing[:20]))
        return 1
    print(f"OK: {len(municipal)} municipios têm pelo menos duas fontes registadas.")
    print("Proximo passo: automatizar comparacao de datas contra dumps iCalendario/dirPortugal/ASPL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
