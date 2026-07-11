import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from technical_analysis.indicators import live_plotter

def generate_rsi_signals_update(data_table: pd.DataFrame, input_series: pd.Series, window: int = 14):
    """
    Update the RSI signals in a given RSI DataFrame by processing the last data point in the given data series.
    Input parameters: data_table: pd.DataFrame, input_series: pd.Series, window: int
    Parameter clarifications: input_series is one-dimensional timeseries data for a single metric (VWAP, total_volume, etc.)
    The DataFrame must have the following columns:
    - gains
    - losses
    - rsi
    - divergence_magnitude
    This function does not have a return value. It updates the DataFrame in place.
    """

    delta = input_series.iloc[-1] - input_series.iloc[-2]

    gain = delta if delta > 0 else 0
    loss = -delta if delta < 0 else 0

    avg_gain = data_table['gains'][-window:].mean()
    avg_loss = data_table['losses'][-window:].mean()

    rs = avg_gain / avg_loss
    rsi = pd.Series(100 - (100 / (1 + rs)))

    rsi_delta = rsi.iloc[-1] - data_table['rsi'].iloc[-1]

    divergence_magnitude = rsi_delta / delta

    data_table.loc[len(data_table)] = [gain, loss, rsi.iloc[-1], divergence_magnitude]

def generate_rsi_signals(input_series: pd.Series, window: int = 14) -> pd.DataFrame:
    """
    Generate an RSI signal DataFrame for a given data series.
    Input parameters: input_series: pd.Series, window: int
    Parameter clarifications: input_series is one-dimensional timeseries data for a single metric (VWAP, total_volume, etc.)
    Returns a DataFrame with the following columns containing timeseries data:
    - gains
    - losses
    - rsi
    - divergence_magnitude
    The number of rows in the DataFrame is equal to the number of data points in the input series.
    Each row corresponds to a data point in the input series and stores the signals as a float.
    Rows may contain NaN values if the window is not full.
    """

    result = pd.DataFrame({
        'gains': [np.nan] * len(input_series),
        'losses': [np.nan] * len(input_series),
        'rsi': [np.nan] * len(input_series),
        'divergence_magnitude': [np.nan] * len(input_series)
    })

    delta = input_series.diff()

    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    avg_gain = gains.rolling(window=window, min_periods=1).mean()
    avg_loss = losses.rolling(window=window, min_periods=1).mean()

    rs = avg_gain / avg_loss
    rsi = pd.Series(100 - (100 / (1 + rs)))
    
    rsi_deltas = np.diff(rsi)
    
    divergence_magnitude = [rsi_deltas[i] / delta[i] for i in range(1, len(delta))]
    
    result.loc[1:, 'gains'] = gains
    result.loc[1:, 'losses'] = losses
    result.loc[len(input_series) - len(rsi.tolist()):, 'rsi'] = rsi.tolist()
    result.loc[1:len(divergence_magnitude), 'divergence_magnitude'] = divergence_magnitude

    return result

def plot_rsi_signals(symbol, dynamic_data):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    lines = {}
    for column in dynamic_data.columns:
        if column not in ("gains", "losses"):
            lines[column], = ax.plot([], [], label=column)
    
    ax.set_xlim(1, len(dynamic_data) + 5)
    ax.set_ylim(-4, 4)
    ax.set_xlabel("1-minute intervals")
    ax.set_ylabel("Normalized Values")
    ax.set_title("RSI Signals Over Time for " + symbol)
    ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1))
    ax.grid()
    plt.tight_layout()

    def frame_update(ax, dynamic_data, lines, bar_container):
        x_values = dynamic_data.index + 1
        for column in lines:
            y_values = (dynamic_data[column] - dynamic_data[column].mean()) / dynamic_data[column].std()
            lines[column].set_data(x_values, y_values)
            ax.set_xlim(1, len(dynamic_data))
            ax.set_ylim(-4, 4)
        return lines.values()

    plotter = live_plotter.live_plotter(fig, ax, lines, dynamic_data, bar_container = None, frame_update = frame_update)
    return plotter