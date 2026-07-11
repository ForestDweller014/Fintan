from datetime import datetime, timedelta
from app_config import APP_CONFIG

STAY_SIZE = APP_CONFIG["STAY_SIZE"]
PREDICTION_SIZE = APP_CONFIG["PREDICTION_SIZE"]
INTERVAL_DURATION = timedelta(minutes=APP_CONFIG["INTERVAL_DURATION"])

def can_generate_signal(bar_data: list[dict], curr_interval_index: int) -> bool:
    # parse current timestamp and interval length
    curr_t = datetime.fromisoformat(bar_data[curr_interval_index]["t"])
    interval_sec = INTERVAL_DURATION.total_seconds()  

    # 1) scan past intervals (inclusive of current interval at i=0)
    for i in range(1, PREDICTION_SIZE + 1):
        idx = curr_interval_index - i
        # out of bounds or missing bar?
        if idx < 0 or bar_data[idx] is None:
            #print("PAST INTERVAL CHECK: OUT OF BOUNDS OR MISSING")
            return False

        bar_t = datetime.fromisoformat(bar_data[idx]["t"])
        # too old?
        if bar_t < curr_t - timedelta(seconds=interval_sec * (i + 0.5)):
            #print("PAST INTERVAL CHECK: TOO OLD")
            return False

    # 2) scan future intervals (inclusive of current interval at i=0)
    for i in range(STAY_SIZE):
        idx = curr_interval_index + i
        # out of bounds or missing bar?
        if idx >= len(bar_data) or bar_data[idx] is None:
            #print("FUTURE INTERVAL CHECK: OUT OF BOUNDS OR MISSING")
            return False

        bar_t = datetime.fromisoformat(bar_data[idx]["t"])
        # too far ahead?
        if bar_t > curr_t + timedelta(seconds=interval_sec * (i + 0.5)):
            #print("FUTURE INTERVAL CHECK: TOO FAR AHEAD")
            return False

    # all checks passed
    return True