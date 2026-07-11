import pandas as pd
import numpy as np
from dateutil import parser
from datetime import datetime, timedelta
from brokerage_api.market_data import stock_api
import matplotlib.pyplot as plt
from technical_analysis.indicators import live_plotter

def aggregate_trades_with_quotes(trades, quotes):
    quote_index = 0
    result = []
    
    for trade in trades:
        trade_time = trade['t']
        
        while (quote_index < len(quotes) - 1 and quotes[quote_index + 1]['t'] <= trade_time):
            quote_index += 1
        
        if quote_index < len(quotes) and quotes[quote_index]['t'] <= trade_time:
            matching_quote = quotes[quote_index]
            trade['bp'] = matching_quote['bp']
            trade['bs'] = matching_quote['bs']
            trade['ap'] = matching_quote['ap']
            trade['as'] = matching_quote['as']
        else:
            trade['bp'] = np.nan
            trade['bs'] = np.nan
            trade['ap'] = np.nan
            trade['as'] = np.nan
        
        result.append(trade)
    
    return result

def calculate_aggression_metrics(trades):
    for trade in trades:
        bid_price = trade.get('bp')
        ask_price = trade.get('ap')
        trade_price = trade.get('p')
        
        if pd.notna(bid_price) and pd.notna(ask_price) and ask_price > bid_price:
            spread = ask_price - bid_price
            
            trade['buy_aggression'] = (ask_price - trade_price) / spread
            trade['sell_aggression'] = (trade_price - bid_price) / spread
        else:
            trade['buy_aggression'] = np.nan
            trade['sell_aggression'] = np.nan
    
    return trades

def calculate_stat_metrics(trades):
    valid_trades = [trade for trade in trades if pd.notna(trade.get('buy_aggression')) and pd.notna(trade.get('sell_aggression')) and pd.notna(trade.get('p'))]
    
    if not valid_trades:
        # Always return a list of np.nan for consistency
        return [np.nan, np.nan, np.nan, np.nan, np.nan]

    total_volume = sum(trade['s'] for trade in valid_trades)
    
    vw_buy_aggression = sum(trade['buy_aggression'] * trade['s'] for trade in valid_trades) / total_volume
    vw_sell_aggression = sum(trade['buy_aggression'] * trade['s'] for trade in valid_trades) / total_volume
    vwap = sum(trade['p'] * trade['s'] for trade in valid_trades) / total_volume

    variance_vwap = (
        sum(trade['s'] * (trade['p'] - vwap) ** 2 for trade in valid_trades) / total_volume
    )
    
    return [vw_buy_aggression, vw_sell_aggression, vwap, variance_vwap, total_volume]

def generate_interval_metrics_update(data_table: pd.DataFrame, symbol: str, interval_start: datetime, interval_end: datetime):
    trades_response = stock_api.get_single_historical_trades(symbol, {"start": interval_start.isoformat(timespec='seconds'), "end": interval_end.isoformat(timespec='seconds')})
    quotes_response = stock_api.get_single_historical_quotes(symbol, {"start": interval_start.isoformat(timespec='seconds'), "end": interval_end.isoformat(timespec='seconds')})
    trades = trades_response["trades"] if trades_response and "trades" in trades_response else []
    quotes = quotes_response["quotes"] if quotes_response and "quotes" in quotes_response else []
    
    for trade in trades:
        trade['t'] = parser.isoparse(trade['t'])
    for quote in quotes:
        quote['t'] = parser.isoparse(quote['t'])
    trades.sort(key=lambda x: x['t'])
    quotes.sort(key=lambda x: x['t'])
    
    aggregated_trades = aggregate_trades_with_quotes(trades, quotes)
    calculate_aggression_metrics(aggregated_trades)
    metrics = calculate_stat_metrics(aggregated_trades)
    # add close, open, high, and low to metrics
    if aggregated_trades:
        close = aggregated_trades[-1]["p"]
        open_ = aggregated_trades[0]["p"]
        high = max([trade["p"] for trade in aggregated_trades])
        low = min([trade["p"] for trade in aggregated_trades])
    else:
        close = open_ = high = low = np.nan
    metrics += [close, open_, high, low]
    data_table.loc[len(data_table)] = metrics

def partition_trades_by_intervals(trades, start_time, interval_time, num_intervals):
    partitions = [[] for _ in range(num_intervals)]

    for trade in trades:
        trade_time = trade['t']

        interval_index = int((trade_time - start_time) / interval_time)

        if 0 <= interval_index < num_intervals:
            partitions[interval_index].append(trade)
        else:
            partitions[-1].append(trade)

    return partitions

def generate_interval_metrics(symbol: str, interval_start: datetime, interval_end: datetime) -> pd.DataFrame:
    interval_metrics = pd.DataFrame({'vw_buy_aggression':[], 'vw_sell_aggression':[], 'VWAP':[], 'variance_VWAP':[], 'total_volume':[], 'closing_price':[], 'opening_price':[], 'high':[], 'low':[]})
    
    generate_interval_metrics_update(interval_metrics, symbol, interval_start, interval_end)

    return interval_metrics

def plot_interval_metrics(symbol, dynamic_data):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    lines = {}
    for column in dynamic_data.columns:
        lines[column], = ax.plot([], [], label=column)
    
    ax.set_xlim(1, len(dynamic_data) + 5)
    ax.set_ylim(-4, 4)
    ax.set_xlabel("1-minute intervals")
    ax.set_ylabel("Normalized Values")
    ax.set_title("Interval Metrics Over Time for " + symbol)
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