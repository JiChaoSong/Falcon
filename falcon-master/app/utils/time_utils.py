from __future__ import annotations

from datetime import datetime, timezone
from datetime import timezone, timedelta


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_from_timestamp(timestamp: float | int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

def beijing_now_string() -> str:
    return utc_now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
