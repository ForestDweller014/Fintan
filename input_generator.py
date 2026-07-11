from timeseries_rsi import generate_rsi_batch
from timeseries_macd import generate_macd_batch
from timeseries_atr import generate_atr_batch
from timeseries_obv import generate_obv_batch
from timeseries_bollinger import generate_bollinger_batch
from timeseries_fibonacci import generate_fibonacci_batch

def generate_inputs_batch(bar_data: list[dict], start_index: int, batch_size: int) -> list[dict]:
    inputs = []
    
    inputs.append(generate_rsi_batch(bar_data, start_index, batch_size))
    inputs.append(generate_macd_batch(bar_data, start_index, batch_size))
    inputs.append(generate_atr_batch(bar_data, start_index, batch_size))
    inputs.append(generate_obv_batch(bar_data, start_index, batch_size))
    inputs.append(generate_bollinger_batch(bar_data, start_index, batch_size))
    inputs.append(generate_fibonacci_batch(bar_data, start_index, batch_size))

    merged = []
    for group in zip(*inputs):
        m: dict = {}
        for d in group:
            m.update(d)
        merged.append(m)
    return merged