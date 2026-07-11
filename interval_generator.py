from datetime import datetime, timedelta
import pytz
import pandas_market_calendars as mcal
from typing import List, Tuple
from app_config import APP_CONFIG

INTERVAL_DURATION = timedelta(minutes=APP_CONFIG["INTERVAL_DURATION"])


def generate_market_intervals(start_time: datetime, end_time: datetime, num_intervals: int) -> List[Tuple[datetime, datetime]]:
    """
    Return a list of (interval_start, interval_end) tuples between start_time and end_time
    (inclusive), but only during NYSE regular hours (09:30–16:00 ET, Mon–Fri *excluding* holidays).
    Requires pandas_market_calendars.
    """
    # 1) Normalize inputs to America/New_York tz
    eastern = pytz.timezone("America/New_York")
    def to_eastern(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return eastern.localize(dt)
        return dt.astimezone(eastern)

    start = to_eastern(start_time)
    end   = to_eastern(end_time)
    if end <= start:
        return []

    # 2) Fetch NYSE schedule (with holidays) over the full date span
    nyse = mcal.get_calendar("NYSE")
    # pandas_market_calendars wants naive Timestamps in UTC or local — we'll give it UTC
    schedule = nyse.schedule(
        start_date=start.date() - timedelta(days=1),
        end_date=end.date()   + timedelta(days=1),
    )

    intervals: list[tuple[datetime, datetime]] = []

    # 3) For each valid trading day, slice into intervals
    for open_ts, close_ts in schedule[["market_open","market_close"]].itertuples(index=False):
        session_open  = open_ts.tz_convert(eastern).to_pydatetime()
        session_close = close_ts.tz_convert(eastern).to_pydatetime()

        # Clip the open/close by overall start/end bounds
        day_start = max(start, session_open)
        day_end = min(end, session_close)
        if day_end <= day_start:
            continue

        current = day_start
        while current < day_end:
            raw_end = current + (num_intervals - 1) * INTERVAL_DURATION
            clipped_end = min(raw_end, day_end)
            intervals.append((current, clipped_end))

            # Advance: if we didn’t hit session_close or end, keep going; else break
            if raw_end < day_end:
                current = raw_end + INTERVAL_DURATION
            else:
                break

    # Already in time-order and non-overlapping
    return intervals