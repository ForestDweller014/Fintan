from app_config import APP_CONFIG
from signal_utils import can_generate_signal

STAY_SIZE = APP_CONFIG["STAY_SIZE"]
PREDICTION_SIZE = APP_CONFIG["PREDICTION_SIZE"]

def generate_labels(bar_data: list[dict], start_index: int, NATURAL_MIN: float) -> dict:
    # 1) define start_time and start_point
    start_point  = bar_data[start_index]["c"]

    # 2) compute end_interval_index via floor math
    end_interval_index  = start_index + STAY_SIZE - 1

    # 3) one-pass scan for peak/trough and retracements
    peak         = start_point
    trough       = start_point
    running_max  = start_point
    running_min  = start_point
    pre_trough   = start_point
    pre_peak     = start_point
    pre_decline  = 0.0
    pre_incline  = 0.0
    curr_retracement = 0.0

    direction = -1

    for i in range(start_index, end_interval_index + 1):
        price = bar_data[i]["c"]

        # update local extremes and memoize
        if price > running_max:
            running_max = price
            pre_trough  = running_min
        elif price < running_min:
            running_min = price
            pre_peak = running_max

        # record global peak/trough
        if price > peak:
            peak = price
        if price < trough:
            trough = price

        #retracements
        if i > start_index:
            if price < bar_data[i-1]["c"]:
                if direction == 1:
                    pre_incline = max(pre_incline, curr_retracement)
                    direction = -1
                    curr_retracement = 0
                curr_retracement += bar_data[i-1]["c"] - price
            else:
                if direction == -1:
                    pre_decline = max(pre_decline, curr_retracement)
                    direction = 1
                    curr_retracement = 0
                curr_retracement += price - bar_data[i-1]["c"]
        
    if direction == 1:
        pre_decline = max(pre_decline, curr_retracement)
    else:
        pre_incline = max(pre_incline, curr_retracement)

    # ratios
    peak_ratio        = peak / start_point - 1
    trough_ratio      = trough / start_point - 1
    pre_trough_ratio  = pre_trough / start_point - 1
    pre_peak_ratio    = pre_peak / start_point - 1
    pre_decline_ratio = -pre_decline / start_point
    pre_incline_ratio =  pre_incline / start_point

    # 4) uptrend vs downtrend
    if peak > start_point:
        bracket_take_profit_label  = peak_ratio
        trailing_take_profit_label = peak_ratio
        bracket_stop_label         = pre_trough_ratio - NATURAL_MIN
        trailing_stop_label        = pre_decline_ratio - NATURAL_MIN
    else:
        bracket_take_profit_label  = trough_ratio
        trailing_take_profit_label = trough_ratio
        bracket_stop_label         = pre_peak_ratio + NATURAL_MIN
        trailing_stop_label        = pre_incline_ratio + NATURAL_MIN

    # 5) corrected optimal_profit calculations, now absolute values
    optimal_profit_bracket  = abs((1 + bracket_take_profit_label) * start_point - start_point)
    optimal_profit_trailing = abs((1 + trailing_take_profit_label) * start_point - start_point)

    # 6) confidence
    bracket_confidence  = 1.0
    trailing_confidence = 1.0

    # 7) append label
    label = {
        "start_time":                  bar_data[start_index]["t"],
        "bracket_take_profit_label":   bracket_take_profit_label,
        "trailing_take_profit_label":  trailing_take_profit_label,
        "bracket_stop_label":          bracket_stop_label,
        "trailing_stop_label":         trailing_stop_label,
        "optimal_profit_bracket":      optimal_profit_bracket,
        "optimal_profit_trailing":     optimal_profit_trailing,
        "bracket_confidence":          bracket_confidence,
        "trailing_confidence":         trailing_confidence,
    }

    return label

def generate_labels_batch(bar_data: list[dict], start_index: int, batch_size: int, NATURAL_MIN: float) -> list[dict]:
    results = []
    
    end_index = min(len(bar_data), start_index + batch_size)
    for i in range(start_index, end_index, PREDICTION_SIZE + 1):
        if can_generate_signal(bar_data, i):
            results.append(generate_labels(bar_data, i, NATURAL_MIN))

    return results