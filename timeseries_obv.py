from typing import List, Dict
from signal_utils import can_generate_signal
from app_config import APP_CONFIG
from online_stats import welford_zscore

PREDICTION_SIZE = APP_CONFIG["PREDICTION_SIZE"]

def generate_obv_signals(bar_data: List[Dict], curr_interval_index: int) -> Dict:
    """
    Generate OBV indicator metadata for the bar at `curr_interval_index` using
    a lookback window of length PREDICTION_SIZE (including the current bar).

    Returns: {
      'obv': <raw OBV>,
      'obv_zscore': <(OBV - μ_OBV) / σ_OBV>
    }
    """
    metadata_list: List[Dict] = []
    start_idx = curr_interval_index - PREDICTION_SIZE

    for idx in range(start_idx, curr_interval_index + 1):
        bar = bar_data[idx]
        close_price = bar["c"]
        volume      = bar["v"]

        if not metadata_list:
            obv = 0.0
        else:
            prev      = metadata_list[-1]
            prev_obv  = prev["obv"]
            prev_close = prev["close"]
            if close_price > prev_close:
                obv = prev_obv + volume
            elif close_price < prev_close:
                obv = prev_obv - volume
            else:
                obv = prev_obv

        metadata_list.append({
            "close": close_price,
            "volume": volume,
            "obv":    obv,
        })

    # extract the raw OBV series over the window
    obv_series = [m["obv"] for m in metadata_list]

    # z-score normalization via Welford's online population variance
    obv_z = welford_zscore(obv_series)

    return {"obv_zscore":  obv_z}


def generate_obv_batch(bar_data: List[Dict], start_index: int, batch_size: int) -> List[Dict]:
    """
    Scan `batch_size` consecutive intervals starting at `start_index`, filter by
    `can_generate_signal`, then concurrently compute OBV metadata for each valid
    interval.

    Returns a list of metadata dicts for all intervals where a signal could be generated.
    """
    results = []

    end_index = min(len(bar_data), start_index + batch_size)
    for i in range(start_index, end_index, PREDICTION_SIZE + 1):
        if can_generate_signal(bar_data, i):
            results.append(generate_obv_signals(bar_data, i))

    return results
