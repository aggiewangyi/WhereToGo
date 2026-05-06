import json
from datetime import date, datetime


def safe_json_loads(text: str | None, default=None):
    if not text:
        return default
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def date_range_days(start: date, end: date) -> int:
    return (end - start).days + 1
