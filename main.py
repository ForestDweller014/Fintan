import asyncio
from typing import List
from datetime import datetime, timedelta
from interval_generator import generate_market_intervals
from historical_file_generator import generate_historical_file
from serializer import read_data

from training_file_generator import generate_training_files
from brokerage_api.trading.assets_api import get_asset

equity_list = [
    "AAPL", "MSFT", "AMZN", "TWLO", "GOOGL", "META", "NVDA", "TSLA", "IBM", "ORCL",
    "CSCO", "INTC", "AMD", "TXN", "QCOM", "AVGO", "MU", "ADBE", "CRM", "PYPL",
    "SHOP", "SPOT", "NFLX", "ZM", "OKTA", "DOCU", "NET", "CRWD", "ZS", "SNOW",
    "MDB", "ESTC", "RBLX", "ROKU", "DDOG", "PINS", "PANW", "FTNT", "SNPS", "TEAM",
    "NOW", "AKAM", "CDNS", "MRVL", "STX", "WDC", "HPE", "HPQ", "JPM", "BAC",
    "WFC", "C",    "GS",    "MS",    "BLK",   "AXP",  "COF",  "BK",   "FIS",  "ABNB",
    "V",   "MA",   "BIDU",  "UBER",  "SPG",   "PLD",  "AMT",  "CCI",  "EQIX", "PG",
    "KO",  "PEP",  "PM",    "MO",    "WMT",   "COST", "WBA",  "CVS",  "CHD",  "KMB",
    "HD",  "LOW",  "MCD",   "SBUX",  "NKE",   "LULU", "PLTR", "RL",   "TGT",  "ULTA",
    "DKS", "GM",   "F",     "XOM",   "CVX",   "COP",  "SLB",  "HAL",  "PSX",  "OXY",
    "MRNA","UNP",  "CSX",   "NSC",   "BA",    "CAT",  "DE",   "GE",   "HON",  "RTX",
    "LMT", "GD",   "LUV",   "DAL",   "AAL",   "UAL",  "FDX",  "UPS",  "MMM",  "EMR",
    "ITW", "DOV",  "PNR",   "DOW",   "DD",    "LYB",  "ECL",  "APD",  "FMC",  "NEM",
    "FCX", "JNJ",  "PFE",   "MRK",   "ABT",   "TMO",  "GILD", "AMGN", "BMY",  "LLY",
    "ABBV","BAX",  "MDT",   "DHR",   "ZBH",   "CRL",  "IQV",  "HCA",  "UNH",  "CI",
    "HUM", "COIN", "CTVA",  "SYK",   "NEE",   "DUK",  "SO",   "AEP",  "EXC",  "D",
    "ES",  "XEL",  "PEG",   "ED",    "T",     "VZ",   "TMUS", "CMCSA","DXCM", "CHTR",
    "O",   "PSA",  "EQR",   "AVB",   "BIIB",  "VRTX", "REGN", "ROST", "TJX",  "BBY",
    "EBAY","SNAP", "TTD",   "NOK",   "BKNG",  "ILMN", "TTWO", "EA",   "RIVN", "PTON",
    "ADP", "SPGI", "ICE",   "MCO",   "EFX",   "CTAS", "LHX",  "APH",  "TEL",  "PAYX",
]


def find_duplicate_symbols(symbols: List[str]) -> List[str]:
    """
    Return a sorted list of symbols that appear more than once in the input list.
    """
    seen = set()
    duplicates = set()
    for symbol in symbols:
        if symbol in seen:
            duplicates.add(symbol)
        else:
            seen.add(symbol)
    return sorted(duplicates)

def ensure_no_duplicates(symbols: List[str]) -> None:
    """
    Raises a ValueError if any duplicate symbols are found.
    """
    dupes = find_duplicate_symbols(symbols)
    if dupes:
        raise ValueError(f"Duplicate symbols found: {dupes}")


def check_shortable(symbols):
    """
    Returns a dict mapping each symbol to its 'shortable' status (True/False).
    Uses the per-symbol get_asset() call for simplicity.
    """
    shortable_map = {}
    for sym in symbols:
        asset = get_asset(sym)
        # get_asset returns a dict on success, or a JSON‐encoded error string
        if isinstance(asset, str):
            # Error: record as not shortable (or handle/log as you prefer)
            print(f"Error fetching {sym}: {asset}")
            shortable_map[sym] = False
        else:
            shortable_map[sym] = bool(asset.get("shortable", False))
    return shortable_map

async def main():
    '''print("Length of equity list: " + str(len(equity_list)))
    try:
        ensure_no_duplicates(equity_list)
        print("No duplicates found.")
    except ValueError as e:
        print(e)
    shortable = check_shortable(equity_list)
    for sym, can_short in shortable.items():
        status = "Shortable" if can_short else "Not shortable"
        print(f"{sym}: {status}")'''

    #intervals = generate_market_intervals(datetime(2023, 7, 23, 9, 30), datetime(2025, 7, 23, 4, 0), 50)
    #print("Number of time intervals: " + str(len(intervals)))
    #await generate_historical_file(equity_list, intervals, 256)

    await generate_training_files(equity_list, 256, 0.0005)
    training_data = read_data('training_data.jsonl')
    print("------------------------")
    print("TRAINING DATA")
    print("------------------------")
    for i in range(5):
        print(training_data[-i])


if __name__ == "__main__":
    asyncio.run(main())