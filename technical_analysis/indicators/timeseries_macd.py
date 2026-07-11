import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from technical_analysis.indicators import live_plotter

def calculate_ema(values, n):
    alpha = 2 / (n + 1)
    ema = [np.nan] * (n - 1)
    initial_sma = sum(values[:n]) / n
    ema.append(initial_sma)
    
    for value in values[n:]:
        ema.append(alpha * value + (1 - alpha) * ema[-1])
    
    return ema

def calculate_ema_update(prev_val, prev_ema, n):
    alpha = 2 / (n + 1)
    return alpha * prev_val + (1 - alpha) * prev_ema

def generate_macd_signals_update(data_table: pd.DataFrame, input_series: pd.Series, short_period: int = 12, long_period: int = 26, signal_period: int = 9):
    """
    Update the MACD signals in a given MACD DataFrame by processing the last data point in the given data series.
    Input parameters: data_table: pd.DataFrame, input_series: pd.Series, short_period: int, long_period: int, signal_period: int
    Parameter clarifications: input_series is one-dimensional timeseries data for a single metric (VWAP, total_volume, etc.)
    The DataFrame must have the following columns:
    - short_ema
    - long_ema
    - macd_line
    - signal_line
    This function does not have a return value. It updates the DataFrame in place.
    """
    
    short_ema = calculate_ema_update(input_series.iloc[-1], data_table['short_ema'].iloc[-1], short_period)
    long_ema = calculate_ema_update(input_series.iloc[-1], data_table['long_ema'].iloc[-1], long_period)
    macd_line = short_ema - long_ema
    signal_line = calculate_ema_update(macd_line, data_table['signal_line'].iloc[-1], signal_period)
    macd_histogram = macd_line - signal_line
    data_delta = input_series.iloc[-1] - input_series.iloc[-2]
    macd_delta = macd_line - data_table['macd_line'].iloc[-1]
    divergence_magnitude = macd_delta / data_delta
    data_table.loc[len(data_table)] = [short_ema, long_ema, macd_line, signal_line, macd_histogram, divergence_magnitude]

def generate_macd_signals(input_series: pd.Series, short_period: int = 12, long_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """
    Generate an MACD signal DataFrame for a given data series.
    Input parameters: input_series: pd.Series, short_period: int, long_period: int, signal_period: int
    Parameter clarifications: input_series is one-dimensional timeseries data for a single metric (VWAP, total_volume, etc.)
    Returns a DataFrame with the following columns containing timeseries data:
    - short_ema
    - long_ema
    - macd_line
    - signal_line
    - macd_histogram
    - divergence_magnitude
    The number of rows in the DataFrame is equal to the number of data points in the input series.
    Each row corresponds to a data point in the input series and stores the signals as a float.
    Rows may contain NaN values.
    """

    result = pd.DataFrame({'short_ema': [np.nan] * len(input_series),
                           'long_ema': [np.nan] * len(input_series),
                           'macd_line': [np.nan] * len(input_series),
                           'signal_line': [np.nan] * len(input_series),
                           'macd_histogram': [np.nan] * len(input_series),
                           'divergence_magnitude': [np.nan] * len(input_series)})
    
    result['short_ema'] = calculate_ema(input_series, short_period)
    result['long_ema'] = calculate_ema(input_series, long_period)

    macd_line = result['short_ema'] - result['long_ema']
    result['macd_line'] = macd_line

    macd_line_clean = macd_line.dropna().tolist()
    signal_line_values = calculate_ema(macd_line_clean, signal_period)
    
    result.loc[len(result) - len(signal_line_values):, 'signal_line'] = signal_line_values

    result['macd_histogram'] = result['macd_line'] - result['signal_line']

    data_deltas = input_series.diff()
    macd_deltas = macd_line.diff()
    
    divergence_magnitude = [macd_deltas[i] / data_deltas[i] for i in range(1, len(data_deltas))]
    result.loc[1:len(divergence_magnitude), 'divergence_magnitude'] = divergence_magnitude

    return result

def plot_macd_signals(symbol, dynamic_data):
    fig, ax = plt.subplots(figsize=(12, 8))

    line, = ax.plot([], [], label='divergence_magnitude', color='red', linewidth=2)
    lines = {'divergence_magnitude': line}

    bar_container = list(ax.bar([], [], alpha=0.7, color='blue', label='macd_histogram'))

    ax.set_xlim(1, len(dynamic_data) + 5)
    ax.set_ylim(-4, 4)
    ax.set_xlabel("1-minute intervals")
    ax.set_ylabel("Normalized Values")
    ax.set_title("MACD Signals Over Time for " + symbol)
    ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1))
    ax.grid()
    plt.tight_layout()

    def frame_update(ax, dynamic_data, lines, bar_container):
        x_values = dynamic_data.index + 1

        y_hist = (dynamic_data['macd_histogram'] - dynamic_data['macd_histogram'].mean()) / dynamic_data['macd_histogram'].std()

        current_num_bars = len(bar_container)
        for new_x, new_y in zip(x_values, y_hist):
            if new_x <= current_num_bars:
                bar_container[int(new_x)-1].set_height(new_y)
            else:
                new_bar = ax.bar(new_x, new_y, alpha=0.7, color='blue', label='macd_histogram')
                bar_container.append(new_bar[0])

        y_div = (dynamic_data['divergence_magnitude'] - dynamic_data['divergence_magnitude'].mean()) / dynamic_data['divergence_magnitude'].std()
        lines['divergence_magnitude'].set_data(x_values, y_div)

        ax.set_xlim(1, len(dynamic_data))
        ax.set_ylim(-4, 4)

        return [lines['divergence_magnitude']] + bar_container

    plotter = live_plotter.live_plotter(fig, ax, lines, dynamic_data, bar_container, frame_update=frame_update)
    return plotter