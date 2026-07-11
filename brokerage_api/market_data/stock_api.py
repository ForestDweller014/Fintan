import aiohttp
from app_config import API_KEY_ID, API_SECRET_KEY

HEADERS = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY_ID,
    "APCA-API-SECRET-KEY": API_SECRET_KEY,
}

# — Alpaca API Wrappers with Remaining Quota —
import aiohttp
from app_config import API_KEY_ID, API_SECRET_KEY

HEADERS = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY_ID,
    "APCA-API-SECRET-KEY": API_SECRET_KEY,
}

async def get_historical_auctions(query_params: dict) -> dict | None:
    url = "https://data.alpaca.markets/v2/stocks/auctions"
    params = query_params.copy()
    result = None
    remaining = 0
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error: {resp.status} - {await resp.text()}")
                    return None
                data = await resp.json()
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
                if result is None:
                    result = data
                else:
                    new_bars = data.get("auctions", {})  # this is a dict: { symbol: [bar1, bar2, …], … }

                    for symbol, bar_list in new_bars.items():
                        if symbol not in result["auctions"]:
                            result["auctions"][symbol] = []
                        result["auctions"][symbol].extend(bar_list)

                token = data.get("next_page_token")
                if not token:
                    break
                params["page_token"] = token
    result["remaining"] = remaining
    return result

async def get_historical_quotes(query_params: dict) -> dict | None:
    url = "https://data.alpaca.markets/v2/stocks/quotes"
    params = query_params.copy()
    result = None
    remaining = 0
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error: {resp.status} - {await resp.text()}")
                    return None
                data = await resp.json()
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
                if result is None:
                    result = data
                else:
                    new_bars = data.get("quotes", {})  # this is a dict: { symbol: [bar1, bar2, …], … }

                    for symbol, bar_list in new_bars.items():
                        if symbol not in result["quotes"]:
                            result["quotes"][symbol] = []
                        result["quotes"][symbol].extend(bar_list)

                token = data.get("next_page_token")
                if not token:
                    break
                params["page_token"] = token
    result["remaining"] = remaining
    return result

async def get_historical_trades(query_params: dict) -> dict | None:
    url = "https://data.alpaca.markets/v2/stocks/trades"
    params = query_params.copy()
    result = None
    remaining = 0
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error: {resp.status} - {await resp.text()}")
                    return None
                data = await resp.json()
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
                if result is None:
                    result = data
                else:
                    new_bars = data.get("trades", {})  # this is a dict: { symbol: [bar1, bar2, …], … }

                    for symbol, bar_list in new_bars.items():
                        if symbol not in result["trades"]:
                            result["trades"][symbol] = []
                        result["trades"][symbol].extend(bar_list)

                token = data.get("next_page_token")
                if not token:
                    break
                params["page_token"] = token
    result["remaining"] = remaining
    return result

async def get_historical_bars(query_params: dict) -> dict | None:
    url = "https://data.alpaca.markets/v2/stocks/bars"
    params = query_params.copy()
    result = None
    remaining = 0
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error: {resp.status} - {await resp.text()}")
                    return None
                data = await resp.json()
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
                if result is None:
                    result = data
                else: 
                    new_bars = data.get("bars", {})  # this is a dict: { symbol: [bar1, bar2, …], … }

                    for symbol, bar_list in new_bars.items():
                        if symbol not in result["bars"]:
                            result["bars"][symbol] = []
                        result["bars"][symbol].extend(bar_list)

                token = data.get("next_page_token")
                if not token:
                    break
                params["page_token"] = token
    result["remaining"] = remaining
    return result

async def get_single_historical_auctions(symbol: str, query_params: dict) -> dict | None:
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/auctions"
    params = query_params.copy()
    result = None
    remaining = 0
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error: {resp.status} - {await resp.text()}")
                    return None
                data = await resp.json()
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
                if result is None:
                    result = data
                else:
                    result["auctions"] += data.get("auctions", [])
                token = data.get("next_page_token")
                if not token:
                    break
                params["page_token"] = token
    result["remaining"] = remaining
    return result

async def get_single_historical_quotes(symbol: str, query_params: dict) -> dict | None:
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes"
    params = query_params.copy()
    result = None
    remaining = 0
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error: {resp.status} - {await resp.text()}")
                    return None
                data = await resp.json()
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
                if result is None:
                    result = data
                else:
                    result["quotes"] += data.get("quotes", [])
                token = data.get("next_page_token")
                if not token:
                    break
                params["page_token"] = token
    result["remaining"] = remaining
    return result

async def get_single_historical_trades(symbol: str, query_params: dict) -> dict | None:
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/trades"
    params = query_params.copy()
    result = None
    remaining = 0
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error: {resp.status} - {await resp.text()}")
                    return None
                data = await resp.json()
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
                if result is None:
                    result = data
                else:
                    result["trades"] += data.get("trades", [])
                token = data.get("next_page_token")
                if not token:
                    break
                params["page_token"] = token
    result["remaining"] = remaining
    return result

async def get_single_historical_bars(symbol: str, query_params: dict) -> dict | None:
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    params = query_params.copy()
    result = None
    remaining = 0
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error: {resp.status} - {await resp.text()}")
                    return None
                data = await resp.json()
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
                if result is None:
                    result = data
                else:
                    result["bars"] += data.get("bars", [])
                token = data.get("next_page_token")
                if not token:
                    break
                params["page_token"] = token
    result["remaining"] = remaining
    return result

async def get_latest_trades(query_params: dict) -> dict | None:
    url = "https://data.alpaca.markets/v2/stocks/trades/latest"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url, params=query_params) as resp:
            if resp.status == 200:
                data = await resp.json()
                data["remaining"] = int(resp.headers.get("X-RateLimit-Remaining", 0))
                return data
            print(f"Error: {resp.status} - {await resp.text()}")
            return None

async def get_latest_trade(symbol: str) -> dict | None:
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/trades/latest"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                data["remaining"] = int(resp.headers.get("X-RateLimit-Remaining", 0))
                return data
            print(f"Error: {resp.status} - {await resp.text()}")
            return None

async def get_latest_quotes(query_params: dict) -> dict | None:
    url = "https://data.alpaca.markets/v2/stocks/quotes/latest"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url, params=query_params) as resp:
            if resp.status == 200:
                data = await resp.json()
                data["remaining"] = int(resp.headers.get("X-RateLimit-Remaining", 0))
                return data
            print(f"Error: {resp.status} - {await resp.text()}")
            return None

async def get_latest_quote(symbol: str) -> dict | None:
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                data["remaining"] = int(resp.headers.get("X-RateLimit-Remaining", 0))
                return data
            print(f"Error: {resp.status} - {await resp.text()}")
            return None

async def get_latest_bars(query_params: dict) -> dict | None:
    url = "https://data.alpaca.markets/v2/stocks/bars/latest"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url, params=query_params) as resp:
            if resp.status == 200:
                data = await resp.json()
                data["remaining"] = int(resp.headers.get("X-RateLimit-Remaining", 0))
                return data
            print(f"Error: {resp.status} - {await resp.text()}")
            return None

async def get_snapshots(query_params: dict) -> dict | None:
    url = "https://data.alpaca.markets/v2/stocks/snapshots"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url, params=query_params) as resp:
            if resp.status == 200:
                data = await resp.json()
                data["remaining"] = int(resp.headers.get("X-RateLimit-Remaining", 0))
                return data
            print(f"Error: {resp.status} - {await resp.text()}")
            return None

async def get_snapshot(symbol: str) -> dict | None:
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/snapshot"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                data["remaining"] = int(resp.headers.get("X-RateLimit-Remaining", 0))
                return data
            print(f"Error: {resp.status} - {await resp.text()}")
            return None
