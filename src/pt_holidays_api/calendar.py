from __future__ import annotations

from datetime import date, timedelta


def easter_sunday(year: int) -> date:
    """Return Gregorian Easter Sunday using the Meeus/Jones/Butcher algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def resolve_rule(year: int, rule: dict) -> date:
    if rule["kind"] == "fixed":
        return date(year, rule["month"], rule["day"])
    if rule["kind"] == "easter_offset":
        return easter_sunday(year) + timedelta(days=rule["offset"])
    raise ValueError(f"Unsupported rule kind: {rule['kind']}")
