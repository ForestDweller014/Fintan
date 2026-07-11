from typing import List, Dict
import math
from signal_utils import can_generate_signal
from app_config import APP_CONFIG
from online_stats import welford_zscore

PREDICTION_SIZE = APP_CONFIG["PREDICTION_SIZE"]

def generate_bollinger_signals(bar_data: List[Dict], curr_interval_index: int) -> Dict:
    """
    Generate Bollinger Bands metadata for the bar at `curr_interval_index`
    using a lookback window of length PREDICTION_SIZE (including the current bar).
    Uses Welford's algorithm for incremental mean and variance (population std).

    Returns:
      {
        "pct_b": <percent b at last bar>,
        "bandwidth_zscore": <z-score of bandwidth over window>
      }
    """
    period = PREDICTION_SIZE
    metadata_list: List[Dict] = []
    start_idx = curr_interval_index - (period - 1)

    for idx in range(start_idx, curr_interval_index + 1):
        bar = bar_data[idx]
        close_price = bar["c"]

        if not metadata_list:
            count = 1
            mean = close_price
            M2 = 0.0
        else:
            prev = metadata_list[-1]
            count = prev["count"] + 1
            delta = close_price - prev["mean"]
            mean = prev["mean"] + delta / count
            M2 = prev["M2"] + delta * (close_price - mean)

        # population standard deviation
        std_dev = math.sqrt(M2 / count)
        upper_band = mean + 2 * std_dev
        lower_band = mean - 2 * std_dev

        # percent‐b
        if (upper_band - lower_band) != 0:
            pct_b = (close_price - lower_band) / (upper_band - lower_band)
        else:
            pct_b = 0.5

        # bandwidth
        if mean != 0:
            bandwidth = (upper_band - lower_band) / mean
        else:
            bandwidth = 0.0

        metadata_list.append({
            "count":    count,
            "mean":     mean,
            "M2":       M2,
            "pct_b":    pct_b,
            "bandwidth": bandwidth,
        })

    # extract the bandwidth series
    bandwidths = [m["bandwidth"] for m in metadata_list]

    # z-score of the last bandwidth via Welford's online population variance
    bw_z = welford_zscore(bandwidths)

    return {"pct_b": metadata_list[-1]["pct_b"], "bandwidth_zscore":  bw_z}


def generate_bollinger_batch(bar_data: List[Dict], start_index: int, batch_size: int) -> List[Dict]:
    """
    Scan `batch_size` consecutive intervals starting at `start_index`, filter by
    `can_generate_signal`, then concurrently compute Bollinger Bands metadata for each valid
    interval.

    Returns a list of metadata dicts for all intervals where a signal could be generated.
    """
    results = []

    end_index = min(len(bar_data), start_index + batch_size)
    for i in range(start_index, end_index, PREDICTION_SIZE + 1):
        if can_generate_signal(bar_data, i):
            results.append(generate_bollinger_signals(bar_data, i))
            results.append(generate_bollinger_signals(bar_data, i + 1))

    return results
