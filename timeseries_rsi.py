from typing import List, Dict
from signal_utils import can_generate_signal
from app_config import APP_CONFIG

PREDICTION_SIZE = APP_CONFIG["PREDICTION_SIZE"]

def generate_rsi_signals(bar_data: List[Dict], curr_interval_index: int) -> Dict:
    """
    Generate RSI indicator metadata for the bar at `curr_interval_index` using
    a lookback window of length PREDICTION_SIZE (including the current bar).

    Uses Wilder's smoothing for average gain/loss.
    Returns the metadata dict for the last interval in the lookback.
    """
    period = PREDICTION_SIZE
    metadata_list: List[Dict] = []
    # Determine start of lookback window
    start_idx = curr_interval_index - period

    for idx in range(start_idx, curr_interval_index + 1):
        bar = bar_data[idx]
        close = bar.get("c")

        if not metadata_list:
            # Initialize with zero gains/losses
            avg_gain = 0.0
            avg_loss = 0.0
        else:
            prev = metadata_list[-1]
            prev_close = prev["close"]
            delta = close - prev_close
            gain = delta if delta > 0 else 0.0
            loss = -delta if delta < 0 else 0.0
            # Wilder's smoothing
            avg_gain = (prev["avg_gain"] * (period - 1) + gain) / period
            avg_loss = (prev["avg_loss"] * (period - 1) + loss) / period

        # Compute RS and RSI
        rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
        rsi = (100 - (100 / (1 + rs)) if avg_loss != 0 else 100.0) / 100.0

        metadata = {
            "close": close,
            "avg_gain": avg_gain,
            "avg_loss": avg_loss,
            "rs": rs,
            "rsi": rsi,
        }
        metadata_list.append(metadata)

    # Return metadata for the latest interval
    return {"rsi": metadata_list[-1]["rsi"]}


def generate_rsi_batch(bar_data: List[Dict], start_index: int, batch_size: int) -> List[Dict]:
    """
    Scan `batch_size` consecutive intervals starting at `start_index`, filter by
    `can_generate_signal`, then concurrently compute RSI metadata for each valid
    interval.

    Returns a list of metadata dicts for all intervals where a signal could be generated.
    """
    results = []

    end_index = min(len(bar_data), start_index + batch_size)
    for i in range(start_index, end_index, PREDICTION_SIZE + 1):
        if can_generate_signal(bar_data, i):
            results.append(generate_rsi_signals(bar_data, i))

    return results
