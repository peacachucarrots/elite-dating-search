# chat/utils.py
from datetime import datetime, time
from zoneinfo import ZoneInfo
from app.settings import EASTERN, OFFICE_OPEN, OFFICE_CLOSE

def is_off_hours(now: datetime | None = None) -> bool:
    now = now or datetime.now(tz=EASTERN)
    return not (OFFICE_OPEN <= now.time() <= OFFICE_CLOSE and now.weekday() < 5)

reps_are_online = lambda *a, **kw: not is_off_hours(*a, **kw)