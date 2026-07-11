from typing import List, Dict
from signal_utils import can_generate_signal
from app_config import APP_CONFIG

PREDICTION_SIZE = APP_CONFIG["PREDICTION_SIZE"]

def generate_fibonacci_signals(bar_data: List[Dict], curr_interval_index: int) -> Dict:
    """
    Generate Fibonacci retracement levels for the bar at `curr_interval_index` using
    the previous PREDICTION_SIZE intervals (including current).

    Returns a dict containing timestamp, lowest_low, highest_high, and Fibonacci levels.
    """
    # Determine start of lookback window
    start_idx = curr_interval_index - PREDICTION_SIZE

    # find lowest low and highest high in the lookback window
    window = bar_data[start_idx: curr_interval_index + 1]
    lows = [bar["l"] for bar in window]
    highs = [bar["h"] for bar in window]
    lowest_low = min(lows)
    highest_high = max(highs)
    diff = highest_high - lowest_low
    close = bar_data[curr_interval_index]["c"]
    fib_pct = (close - lowest_low) / diff

    return {"fib_pct": fib_pct}

def generate_fibonacci_batch(bar_data: List[Dict], start_index: int, batch_size: int) -> List[Dict]:
    """
    Scan `batch_size` intervals starting at `start_index`, filter by `can_generate_signal`,
    then concurrently compute Fibonacci levels metadata for each valid interval.

    Returns a list of metadata dicts for all intervals where a signal could be generated.
    """
    results = []

    end_index = min(len(bar_data), start_index + batch_size)
    for i in range(start_index, end_index, PREDICTION_SIZE + 1):
        if can_generate_signal(bar_data, i):
            results.append(generate_fibonacci_signals(bar_data, i))

    return results
