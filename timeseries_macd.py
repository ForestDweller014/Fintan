from typing import List, Dict
from signal_utils import can_generate_signal
from app_config import APP_CONFIG
from online_stats import welford_zscore

PREDICTION_SIZE = APP_CONFIG["PREDICTION_SIZE"]

def generate_macd_signals(bar_data: List[Dict], curr_interval_index: int) -> Dict:
    # … (your existing EMA/MACD loop unchanged) …
    metadata_list: List[Dict] = []
    start_idx = curr_interval_index - PREDICTION_SIZE
    alpha_short = 2/(12+1)
    alpha_long  = 2/(26+1)
    alpha_sig   = 2/(9 +1)

    for idx in range(start_idx, curr_interval_index+1):
        close = bar_data[idx]["c"]
        if not metadata_list:
            ema_s = ema_l = close
            macd  = signal = hist = 0.0
        else:
            prev = metadata_list[-1]
            ema_s = alpha_short*close + (1-alpha_short)*prev["ema_short"]
            ema_l = alpha_long*close  + (1-alpha_long) *prev["ema_long"]
            macd  = ema_s - ema_l
            signal= alpha_sig*macd + (1-alpha_sig)*prev["signal_line"]
            hist  = macd - signal

        metadata_list.append({
            "ema_short":   ema_s,
            "ema_long":    ema_l,
            "macd_line":   macd,
            "signal_line": signal,
            "histogram":   hist,
        })

    # extract the raw histograms over window
    hists = [m["histogram"] for m in metadata_list]

    # z-score normalization via Welford's online population variance
    hist_z = welford_zscore(hists)

    return {"hist_zscore":  hist_z}


def generate_macd_batch(bar_data: List[Dict], start_index: int, batch_size: int) -> List[Dict]:
    """
    Scan `batch_size` consecutive intervals starting at `start_index`, filter by
    `can_generate_signal`, then concurrently compute MACD metadata for each valid
    interval.

    Returns a list of metadata dicts for all intervals where a signal could be generated.
    """
    results = []

    end_index = min(len(bar_data), start_index + batch_size)
    for i in range(start_index, end_index, PREDICTION_SIZE + 1):
        if can_generate_signal(bar_data, i):
            results.append(generate_macd_signals(bar_data, i))

    return results
