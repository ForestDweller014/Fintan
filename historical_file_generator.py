import asyncio
from datetime import datetime, timedelta
from time import monotonic
from typing import Any
from serializer import write_data
import time
import sys
from zoneinfo import ZoneInfo
from brokerage_api.market_data.stock_api import (
    get_historical_bars,
    get_historical_quotes,
)
from app_config import APP_CONFIG


MAX_CALLS_PER_PERIOD = APP_CONFIG["MAX_CALLS_PER_PERIOD"]
API_TIMEFRAME = str(APP_CONFIG["INTERVAL_DURATION"]) + "Min"
bars_meta: dict
bars_meta_locks: dict
quotes_meta: dict
quotes_meta_locks: dict
sem: asyncio.Semaphore


class RateLimiter:
    def __init__(self, max_calls: int):
        """
        :param max_calls: number of tokens per full period
        :param period: length of period in seconds (e.g. 60 for per-minute)
        """
        self._rate        = max_calls
        self._period      = 60
        self._start_time  = None
        self._used        = 0               # how many tokens we’ve consumed
        self._first_call = True
        self._lock        = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = monotonic()
                if self._first_call:
                    self._start_time = now
                    self._first_call = False
                    return

                if self._start_time is None:
                    self._start_time = -1

                elapsed   = now - self._start_time
                earned    = elapsed * (self._rate/self._period)
                available = earned - self._used

                if available >= 1.0:
                    self._used += 1
                    return

                # wait until the next token arrives
                next_token = self._start_time + (self._used+1)*(self._period/self._rate)
                await asyncio.sleep(next_token - now)


async def log_progress(bars_meta: dict[str, Any], quotes_meta: dict[str, Any], limiter: RateLimiter) -> None:
    """
    Display a single-line, in-place updating progress bar every 5 seconds.
    Shows bars and quotes segments side by side with counts and percentages.
    """
    BAR_WIDTH = 30  # width of each segment
    first_iteration = True

    print()

    while True:
        try:
            await asyncio.wait_for(
                #asyncio.gather(
                #    bars_meta["done_event_b"].wait(),
                #    quotes_meta["done_event_q"].wait(),
                #), 
                bars_meta["done_event_b"].wait(),
                timeout=5
            )
        except asyncio.TimeoutError:
            pass

        # Retrieve stats
        b  = bars_meta.get("bars_completed", 0)
        q  = quotes_meta.get("quotes_completed", 0)
        bs = bars_meta.get("bars_calls_made", 0)
        qs = quotes_meta.get("quotes_calls_made", 0)
        total_b = bars_meta.get("total_b", 0)
        total_q = quotes_meta.get("total_q", 0)
        remaining_b = bars_meta.get("bars_remaining_calls", 0)
        remaining_q = quotes_meta.get("quotes_remaining_calls", 0)

        # Elapsed time
        if limiter._start_time:
            time_anchor = limiter._start_time
        else:
            time_anchor = time.monotonic()
        elapsed = time.monotonic() - time_anchor
        elapsed_str = str(timedelta(seconds=int(elapsed)))

        # Calculate fill
        frac_b = min(b / total_b, 1.0)
        frac_q = min(q / total_q, 1.0)
        filled_b = int(frac_b * BAR_WIDTH)
        filled_q = int(frac_q * BAR_WIDTH)

        # Build bar strings
        bar_b = "█" * filled_b + "-" * (BAR_WIDTH - filled_b)
        bar_q = "█" * filled_q + "-" * (BAR_WIDTH - filled_q)

        # Compose single-line display
        progress_line = (
            f"Bars:   [{bar_b}] {b}/{total_b} ({frac_b*100:5.1f}%)\n"
            f"Quotes: [{bar_q}] {q}/{total_q} ({frac_q*100:5.1f}%)\n"
            f"Calls → Bars: {bs}, Quotes: {qs}  Remaining Calls → : Bars: {remaining_b}, Quotes: {remaining_q}\n"
            f"Elapsed: {elapsed_str}\n"
        )

        # Clear line and write in-place
        if first_iteration:
            sys.stdout.write(progress_line)
            first_iteration = False
        else:
            sys.stdout.write('\033[4A\033[J' + progress_line)
        sys.stdout.flush()

        if b >= total_b: #and q >= total_q:
            break

    sys.stdout.write(f"\nDone! Total time: {elapsed_str}\n")
    sys.stdout.flush()


async def fetch_bar(SYMBOLS: list[str], idx: int, start: datetime, end: datetime, bar_data: dict[str, list], limiter: RateLimiter) -> None:
    async with sem:
        await limiter.acquire()

        params = {
            "start":     start.isoformat(timespec="seconds"),
            "end":       end.isoformat(timespec="seconds"),
            "limit": 10000,
            "timeframe": API_TIMEFRAME,
            "symbols":   ",".join(SYMBOLS)
        }

        async with bars_meta_locks["bars_calls_made"]:
            bars_meta["bars_calls_made"] += 1

        resp = await get_historical_bars(params)
        if resp:
            bars_by_symbol = resp.get("bars", {})
            for symbol in SYMBOLS:
                # each symbol should have (end - start) / timeframe bars in this slice
                symbol_bars = bars_by_symbol.get(symbol, [])
                #if len(symbol_bars) < 50:
                    #print(str(datetime.fromisoformat(symbol_bars[-1]["t"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))) + ", " + str(len(symbol_bars)))
                    #t = datetime.fromisoformat(symbol_bars[-1]["t"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York")).time()
                    #print(str(t.hour) + ", " + str(t.minute))
                    #if not (t.hour == 4 and t.minute == 0):
                        #print("MISSING DATA DETECTED")
                if symbol_bars:
                    for bar in symbol_bars:
                        bar_data[symbol][idx].append(bar)
                else:
                    # fallback to empty dict if missing
                    bar_data[symbol][idx] = [{}]

            async with bars_meta_locks["bars_remaining_calls"]:
                bars_meta["bars_remaining_calls"] = resp.get("remaining")

        # track completions
        async with bars_meta_locks["bars_completed"]:
            bars_meta["bars_completed"] += 1
            if bars_meta["bars_completed"] >= bars_meta["total_b"]:
                bars_meta["done_event_b"].set()


async def fetch_quote(SYMBOLS: list[str], idx: int, start: datetime, end: datetime, quote_data: dict[str, list], limiter: RateLimiter) -> None:
    async with sem:
        await limiter.acquire()

        params = {
            "start": start.isoformat(timespec="seconds"),
            "end":   end.isoformat(timespec="seconds"),
            "limit": 10000,
            "symbols":  ",".join(SYMBOLS)
        }

        async with quotes_meta_locks["quotes_calls_made"]:
            quotes_meta["quotes_calls_made"] += 1

        resp = await get_historical_quotes(params)
        if resp:
            quotes_by_symbol = resp.get("quotes", {})
            for symbol in SYMBOLS:
                # each symbol should have (end - start) / timeframe quotes in this slice
                symbol_quotes = quotes_by_symbol.get(symbol, [])
                if symbol_quotes:
                    for quote in symbol_quotes:
                        quote_data[symbol][idx].append(quote)
                else:
                    # fallback to empty dict if missing
                    quote_data[symbol][idx] = [{}]

            async with quotes_meta_locks["quotes_remaining_calls"]:
                quotes_meta["quotes_remaining_calls"] = resp.get("remaining")

        async with quotes_meta_locks["quotes_completed"]:
            quotes_meta["quotes_completed"] += 1
            if quotes_meta["quotes_completed"] >= quotes_meta["total_q"]:
                quotes_meta["done_event_q"].set()


async def generate_historical_file_batch(SYMBOLS: list[str], intervals: list[tuple[datetime, datetime]], start_index: int, batch_size: int, limiter: RateLimiter) -> None:
    batch_size = min(batch_size, len(intervals) - start_index) 
    bar_data = {
        symbol: [ [] for _ in range(batch_size) ]
        for symbol in SYMBOLS
    }
    quote_data = {
        symbol: [ [] for _ in range(batch_size) ]
        for symbol in SYMBOLS
    }

    global bars_meta, bars_meta_locks, quotes_meta, quotes_meta_locks, sem
    bars_meta = {
        "bars_completed":       0,
        "bars_calls_made":      0,
        "bars_remaining_calls": None,
        "total_b":              batch_size,
        "done_event_b":         asyncio.Event()
    }
    bars_meta_locks = {
        "bars_completed":       asyncio.Lock(),
        "bars_calls_made":      asyncio.Lock(),
        "bars_remaining_calls": asyncio.Lock(),
        "total_b":              asyncio.Lock()
    }

    quotes_meta = {
        "quotes_completed":       0,
        "quotes_calls_made":      0,
        "quotes_remaining_calls": None,
        "total_q":                batch_size,
        "done_event_q":           asyncio.Event()
    }
    quotes_meta_locks = {
        "quotes_completed":       asyncio.Lock(),
        "quotes_calls_made":      asyncio.Lock(),
        "quotes_remaining_calls": asyncio.Lock(),
        "total_q":                asyncio.Lock()
    }

    sem = asyncio.Semaphore(max(1, int(MAX_CALLS_PER_PERIOD / 60)))

    tasks = [log_progress(bars_meta, quotes_meta, limiter)]

    for idx in range(batch_size):
        s, e = intervals[start_index + idx]
        tasks.append(
            fetch_bar(
                SYMBOLS,
                idx,
                s, e, 
                bar_data,
                limiter
            )
        )
        '''tasks.append(
            fetch_quote(
                SYMBOLS,
                idx,
                s, e, 
                quote_data,
                limiter
            )
        )'''
    await asyncio.gather(*tasks)

    # Append fetched bar_data entries to historical_data.jsonl (one JSON object per line)
    for idx in range(len(SYMBOLS)):
        symbol = SYMBOLS[idx]
        for window_bars in bar_data[symbol]:
            write_data('historical_files/historical_data_' + symbol + ".jsonl", window_bars)
            

async def generate_historical_file(SYMBOLS: list[str], intervals: list[tuple[datetime, datetime]], batch_size: int) -> None:
    limiter = RateLimiter(MAX_CALLS_PER_PERIOD)
    interval_size = len(intervals)
    i = 0
    while (i < interval_size):
        await generate_historical_file_batch(SYMBOLS, intervals, i, batch_size, limiter)
        i += batch_size