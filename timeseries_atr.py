from typing import List, Dict
from signal_utils import can_generate_signal
from app_config import APP_CONFIG
from online_stats import welford_zscore

PREDICTION_SIZE = APP_CONFIG["PREDICTION_SIZE"]

def generate_atr_signals(bar_data: List[Dict], curr_interval_index: int) -> Dict:
    """
    Generate ATR indicator metadata for the bar at `curr_interval_index` using
    a lookback window of length PREDICTION_SIZE (including the current bar).

    Returns:
      - 'atr': raw Wilder ATR
      - 'atr_zscore': (ATR - μ_ATR) / σ_ATR
      - 'atr_avg_norm': ATR / mean(TrueRange)
      - 'atr_max_norm': ATR / max(TrueRange)
    """
    period = PREDICTION_SIZE
    metadata_list: List[Dict] = []
    start_idx = curr_interval_index - period

    for idx in range(start_idx, curr_interval_index + 1):
        bar   = bar_data[idx]
        high  = bar.get("h", 0.0)
        low   = bar.get("l", 0.0)
        close = bar.get("c", 0.0)

        if not metadata_list:
            true_range = high - low
            atr = true_range
        else:
            prev        = metadata_list[-1]
            prev_close  = prev["close"]
            # three definitions of TR
            range1 = high - low
            range2 = abs(high - prev_close)
            range3 = abs(low  - prev_close)
            true_range = max(range1, range2, range3)
            # Wilder smoothing
            atr = (prev["atr"] * (period - 1) + true_range) / period

        metadata_list.append({
            "high":        high,
            "low":         low,
            "close":       close,
            "true_range":  true_range,
            "atr":         atr,
        })

    # Extract series
    atr_list = [m["atr"] for m in metadata_list]

    # z-score normalization via Welford's online population variance
    atr_z = welford_zscore(atr_list)

    return {"atr_zscore": atr_z}


def generate_atr_batch(bar_data: List[Dict], start_index: int, batch_size: int) -> List[Dict]:
    """
    Scan `batch_size` consecutive intervals starting at `start_index`, filter by
    `can_generate_signal`, then concurrently compute ATR metadata for each valid
    interval.

    Returns a list of metadata dicts for all intervals where a signal could be generated.
    """
    results = []

    end_index = min(len(bar_data), start_index + batch_size)
    for i in range(start_index, end_index, PREDICTION_SIZE + 1):
        if can_generate_signal(bar_data, i):
            results.append(generate_atr_signals(bar_data, i))

    return results
