# Fintan

Fintan is a Python pipeline for generating labeled machine learning training data from live US equity market data. It fetches OHLCV bars from the Alpaca API, computes technical indicators as input features, and labels each market interval with optimal trade parameters (take-profit and stop-loss ratios).

---

## Tech Stack

- Python CLI (`argparse`) for market-data, trading, and training-data workflows
- Asyncio + `aiohttp` for concurrent Alpaca market-data ingestion
- Alpaca API for historical bars, quotes, trades, account, asset, position, and order operations
- `pandas_market_calendars` for NYSE trading-session interval generation
- JSONL for historical bar storage and ML training-record output
- `ThreadPoolExecutor` for parallel training-file generation
- `pandas`, `numpy`, and `matplotlib` for technical-analysis and live-plotting utilities

---

## CLI Usage

```bash
# Optional editable install for the `fintan` command:
python -m pip install -e .

# Show all top-level commands:
fintan --help
python -m fintan_cli --help

# Validate the built-in equity universe:
fintan symbols validate --all

# Generate NYSE market intervals:
fintan intervals \
  --start 2025-01-02T09:30:00 \
  --end 2025-01-02T16:00:00 \
  --num-intervals 50

# Fetch historical bars from Alpaca into historical_files/:
fintan fetch-history AAPL MSFT \
  --start 2025-01-02T09:30:00 \
  --end 2025-01-03T16:00:00 \
  --num-intervals 50 \
  --batch-size 256

# Generate training files from existing historical data:
fintan generate-training AAPL MSFT \
  --batch-size 256 \
  --natural-min 0.0005

# Run fetch + training generation together:
fintan pipeline AAPL MSFT \
  --start 2025-01-02T09:30:00 \
  --end 2025-01-03T16:00:00 \
  --num-intervals 50 \
  --fetch-batch-size 256 \
  --training-batch-size 256 \
  --natural-min 0.0005

# Compute indicator inputs or labels from a JSONL bar file:
fintan inputs historical_files/historical_data_AAPL.jsonl --start-index 27 --batch-size 256
fintan labels historical_files/historical_data_AAPL.jsonl --start-index 27 --natural-min 0.0005

# Call market-data wrappers:
fintan market-data get_latest_bars --symbols AAPL MSFT
fintan market-data get_single_historical_bars \
  --symbol AAPL \
  --start 2025-01-02T09:30:00Z \
  --end 2025-01-02T16:00:00Z \
  --timeframe 1Min

# Call trading wrappers:
fintan trading account
fintan trading orders --param status=open
```

The pipeline prints live progress bars showing fetch completion, elapsed time, and remaining API quota.

---

## Overview

The pipeline runs in three stages:

1. **Fetch** — Pull historical 1-minute OHLCV bars for a universe of ~200 US equities from Alpaca's market data API, respecting NYSE trading hours and rate limits. Output stored in `historical_files/` as per-symbol JSONL files.

2. **Compute** — For each valid market interval, compute a set of normalized technical indicators as model input features.

3. **Label** — For each valid signal point, scan the next `STAY_SIZE` bars to compute optimal bracket and trailing stop trade outcomes as training targets. Output stored in `training_files/` as per-symbol JSONL files.

---

## Configuration

Runtime settings are loaded from environment variables, with optional local overrides from an untracked `config.json`. Use `config.example.json` as the safe template and keep your real `config.json` out of Git.

| Key | Description |
|---|---|
| `trading_mode` | `"paper"` or `"live"` — selects which Alpaca credentials to use |
| `live` / `paper` | Alpaca API key, secret, and server domain |
| `HUGGINGFACE_HUB_TOKEN` | HuggingFace API token |
| `FINNHUB_API_KEY` | Finnhub market data API key |
| `GROQ_TOKEN` | Groq LLM API token |
| `OPENAI_API_KEY` | OpenAI API key |
| `STAY_SIZE` | Lookahead bars used for label generation (default: 5) |
| `PREDICTION_SIZE` | Lookback bars used for indicator computation (default: 27) |
| `INTERVAL_DURATION` | Bar size in minutes (default: 1) |
| `MAX_CALLS_PER_PERIOD` | Max Alpaca API calls per minute (default: 200) |

Environment variables:

| Variable | Description |
|---|---|
| `TRADING_MODE` | `"paper"` or `"live"` |
| `ALPACA_LIVE_API_KEY_ID` / `ALPACA_LIVE_API_SECRET_KEY` | Alpaca live trading credentials |
| `ALPACA_PAPER_API_KEY_ID` / `ALPACA_PAPER_API_SECRET_KEY` | Alpaca paper trading credentials |
| `ALPACA_LIVE_APISERVER_DOMAIN` / `ALPACA_PAPER_APISERVER_DOMAIN` | Optional Alpaca API domains |
| `HUGGINGFACE_HUB_TOKEN` | HuggingFace API token |
| `FINNHUB_API_KEY` | Finnhub market data API key |
| `GROQ_TOKEN` | Groq LLM API token |
| `OPENAI_API_KEY` | OpenAI API key |
| `STAY_SIZE`, `PREDICTION_SIZE`, `INTERVAL_DURATION`, `MAX_CALLS_PER_PERIOD` | Numeric pipeline settings |

---

## API Capabilities

All API wrappers live under `brokerage_api/` and connect to [Alpaca](https://alpaca.markets).

### Market Data (`brokerage_api/market_data/stock_api.py`)

All market data functions are `async` and handle pagination automatically.

**Multi-symbol endpoints** (pass a comma-separated symbols query param):

| Function | Description |
|---|---|
| `get_historical_bars(query_params)` | OHLCV bars for multiple symbols over a date range |
| `get_historical_quotes(query_params)` | Bid/ask quote data for multiple symbols |
| `get_historical_trades(query_params)` | Trade-by-trade data for multiple symbols |
| `get_historical_auctions(query_params)` | Auction data for multiple symbols |
| `get_latest_bars(query_params)` | Most recent bar for multiple symbols |
| `get_latest_quotes(query_params)` | Most recent quote for multiple symbols |
| `get_latest_trades(query_params)` | Most recent trade for multiple symbols |
| `get_snapshots(query_params)` | Full snapshot (bar + quote + trade) for multiple symbols |

**Single-symbol endpoints**:

| Function | Description |
|---|---|
| `get_single_historical_bars(symbol, query_params)` | OHLCV bars for one symbol |
| `get_single_historical_quotes(symbol, query_params)` | Quote data for one symbol |
| `get_single_historical_trades(symbol, query_params)` | Trade data for one symbol |
| `get_single_historical_auctions(symbol, query_params)` | Auction data for one symbol |
| `get_latest_trade(symbol)` | Most recent trade for one symbol |
| `get_latest_quote(symbol)` | Most recent quote for one symbol |
| `get_snapshot(symbol)` | Full snapshot for one symbol |

All paginated responses are automatically stitched together. Each result includes a `remaining` field reflecting Alpaca's remaining rate-limit quota from the last response header.

### Options Data (`brokerage_api/market_data/option_api.py`)

Empty — reserved for future options market data endpoints.

### Trading — Orders (`brokerage_api/trading/orders_api.py`)

Synchronous REST wrappers around Alpaca's trading API.

| Function | Description |
|---|---|
| `get_orders(query_params)` | List all orders (filterable by status, symbol, etc.) |
| `get_order(order_id, query_params)` | Get a single order by ID |
| `place_order(body_params)` | Place any order type by passing a raw payload dict |
| `update_order(order_id, body_params)` | Modify an open order |
| `cancel_order(order_id)` | Cancel a specific order |
| `cancel_all_orders()` | Cancel all open orders |

Higher-level order helpers in `brokerage_api/trading/orders.py`:

| Function | Description |
|---|---|
| `place_bracket_order(symbol, qty, take_profit_price, stop_loss_price)` | Market buy with attached take-profit limit and stop-loss |
| `place_trailing_stop_order(symbol, qty, trail_price)` | Sell with a trailing stop |
| `buy_market_order(symbol, qty)` | Market buy |
| `sell_market_order(symbol, qty)` | Market sell |
| `buy_limit_order(symbol, qty, limit_price)` | Limit buy |
| `sell_limit_order(symbol, qty, limit_price)` | Limit sell |
| `short_stock(symbol, qty, order_type, time_in_force)` | Short sell |
| `cover_short(symbol, qty, order_type, time_in_force)` | Cover a short position |

### Trading — Positions (`brokerage_api/trading/positions_api.py`)

| Function | Description |
|---|---|
| `get_positions()` | List all open positions |
| `get_position(symbol)` | Get position for a specific symbol |
| `close_position(symbol)` | Close a specific position |
| `close_all_positions()` | Close all open positions |
| `exercise_option(symbol_or_id)` | Exercise an options contract |

### Trading — Assets (`brokerage_api/trading/assets_api.py`)

| Function | Description |
|---|---|
| `get_assets(query_params)` | List tradeable assets |
| `get_asset(symbol_or_asset_id)` | Get details for a specific asset (includes shortability) |
| `get_options(query_params)` | List options contracts |
| `get_option(symbol_or_id)` | Get details for a specific options contract |

### Trading — Account (`brokerage_api/trading/accounts_api.py`)

| Function | Description |
|---|---|
| `get_account()` | Retrieve account info (buying power, portfolio value, status, etc.) |

---

## Technical Analysis Capabilities

Six indicators are computed over a `PREDICTION_SIZE`-bar lookback window. All are normalized to be scale-invariant across symbols and time periods.

### RSI — Relative Strength Index (`timeseries_rsi.py`)
Uses Wilder's smoothing. Output: `rsi` (0–1 normalized).

### MACD — Moving Average Convergence Divergence (`timeseries_macd.py`)
EMA(12), EMA(26), signal EMA(9). Output: `hist_zscore` — z-score of the MACD histogram over the lookback window.

### ATR — Average True Range (`timeseries_atr.py`)
Wilder's smoothing over true range. Output: `atr_zscore` — z-score of ATR over the lookback window.

### OBV — On-Balance Volume (`timeseries_obv.py`)
Cumulative volume-direction accumulator. Output: `obv_zscore` — z-score of OBV over the lookback window.

### Bollinger Bands (`timeseries_bollinger.py`)
Uses Welford's online algorithm for incremental mean/variance. Outputs:
- `pct_b` — where price sits within the bands (0 = lower, 1 = upper)
- `bandwidth_zscore` — z-score of band width over the lookback window

### Fibonacci Retracement (`timeseries_fibonacci.py`)
Identifies the highest high and lowest low over the lookback window. Output: `fib_pct` — where the current close sits within that range (0 = at low, 1 = at high).

---

## Training Data Schema

Each record in a `training_files/training_data_<SYMBOL>.jsonl` file has the shape:

```json
{
  "inputs": {
    "rsi": 0.673,
    "hist_zscore": -1.506,
    "atr_zscore": 3.015,
    "obv_zscore": 0.937,
    "pct_b": 0.736,
    "bandwidth_zscore": 1.227,
    "fib_pct": 0.801
  },
  "labels": {
    "start_time": "2023-07-25T15:27:00Z",
    "bracket_take_profit_label": 0.000258,
    "trailing_take_profit_label": 0.000258,
    "bracket_stop_label": -0.000706,
    "trailing_stop_label": -0.000964,
    "optimal_profit_bracket": 0.05,
    "optimal_profit_trailing": 0.05,
    "bracket_confidence": 1.0,
    "trailing_confidence": 1.0
  }
}
```

**Labels explained:**
- `bracket_take_profit_label` — ratio of take-profit price to entry price minus 1
- `bracket_stop_label` — ratio of stop-loss price to entry price minus 1 (negative)
- `trailing_take_profit_label` / `trailing_stop_label` — same for trailing stop strategy
- `optimal_profit_bracket` / `optimal_profit_trailing` — absolute dollar profit at optimal exit

---

## Module Reference

| File | Role |
|---|---|
| `fintan_cli.py` | Command-line interface for data, indicator, JSONL, market-data, and trading workflows |
| `main.py` | Legacy script entry point and built-in 200-symbol equity universe |
| `app_config.py` | Loads environment-backed credentials/settings with optional local `config.json` overrides |
| `interval_generator.py` | Generates NYSE-hours market intervals using `pandas_market_calendars` |
| `historical_file_generator.py` | Async rate-limited batch fetcher; writes `historical_files/` |
| `training_file_generator.py` | Converts historical bars into `{inputs, labels}` training records |
| `input_generator.py` | Aggregates all six indicator outputs into a single feature dict |
| `label_generator.py` | Scans lookahead bars to compute optimal trade outcome labels |
| `signal_utils.py` | Validates bar continuity before generating a signal |
| `serializer.py` | JSONL read, write, and shuffle utilities |
| `brokerage_api/` | Alpaca API wrappers (market data + trading) |

---

## Equity Universe

~200 US equities across sectors including Technology, Financials, Healthcare, Consumer Discretionary/Staples, Energy, Industrials, Telecom, and REITs. The full list is defined in `main.py`.

---

## Requirements

```
aiohttp
pandas_market_calendars
pytz
requests
```

---

## Testing

```bash
python -m unittest discover -s tests
python -m fintan_cli --help
```
