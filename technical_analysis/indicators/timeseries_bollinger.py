import pandas as pd
import matplotlib.pyplot as plt
from technical_analysis.indicators import live_plotter

def generate_bollinger_signals_update(data_table: pd.DataFrame, input_series: pd.Series, window: int = 20, num_std_dev: float = 2):
    """
    Update the bollinger signals in a given bollinger DataFrame by processing the last data point in the given data series.
    Input parameters: data_table: pd.DataFrame, input_series: pd.Series, window: int, num_std_dev: float
    Parameter clarifications: input_series is one-dimensional timeseries data for a single metric (VWAP, total_volume, etc.)
    The DataFrame must have the following columns:
    - bollinger_volatility
    This function does not have a return value. It updates the DataFrame in place.
    """

    last_mean = input_series[-window:].mean()

    last_std = input_series[-window:].std()

    upper_val = last_mean + num_std_dev * last_std
    lower_val = last_mean - num_std_dev * last_std
    
    volatility = upper_val - lower_val
    
    data_table.loc[len(data_table)] = [volatility]

def generate_bollinger_signals(input_series: pd.Series, window: int = 20, num_std_dev: float = 2) -> pd.DataFrame:
    """
    Generate a bollinger signal DataFrame for a given data series.
    Input parameters: input_series: pd.Series, window: int, num_std_dev: float
    Parameter clarifications: input_series is one-dimensional timeseries data for a single metric (VWAP, total_volume, etc.)
    Returns a DataFrame with the following columns containing timeseries data:
    - bollinger_volatility
    The number of rows in the DataFrame is equal to the number of data points in the input series.
    Each row corresponds to a data point in the input series and stores the signals as a float.
    Rows may contain NaN values if the window is not full.
    """

    rolling_mean = input_series.rolling(window=window).mean()

    rolling_std = input_series.rolling(window=window).std()

    upper_band = rolling_mean + num_std_dev * rolling_std
    lower_band = rolling_mean - num_std_dev * rolling_std
    
    volatility = upper_band - lower_band
    
    result = pd.DataFrame({
        'bollinger_volatility': volatility
    })
    
    return result

def plot_bollinger_signals(symbol, dynamic_data):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    lines = {}
    for column in dynamic_data.columns:
        lines[column], = ax.plot([], [], label=column)
    
    ax.set_xlim(1, len(dynamic_data) + 5)
    ax.set_ylim(-4, 4)
    ax.set_xlabel("1-minute intervals")
    ax.set_ylabel("Normalized Values")
    ax.set_title("Volatility Signals Over Time for " + symbol)
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