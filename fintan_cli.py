import argparse
import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Sequence

from historical_file_generator import generate_historical_file
from input_generator import generate_inputs_batch
from interval_generator import generate_market_intervals
from label_generator import generate_labels, generate_labels_batch
from main import check_shortable, ensure_no_duplicates, equity_list, find_duplicate_symbols
from serializer import read_data, shuffle_data
from training_file_generator import generate_training_files

SINGLE_SYMBOL_WITH_PARAMS = {
    "get_single_historical_auctions",
    "get_single_historical_quotes",
    "get_single_historical_trades",
    "get_single_historical_bars",
}
SINGLE_SYMBOL_NO_PARAMS = {
    "get_latest_trade",
    "get_latest_quote",
    "get_snapshot",
}


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid ISO datetime"
        ) from exc


def _parse_key_value(values: Sequence[str] | None) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise argparse.ArgumentTypeError(f"{value!r} must use KEY=VALUE format")
        key, item = value.split("=", 1)
        params[key] = item
    return params


def _resolve_symbols(args: argparse.Namespace) -> list[str]:
    if getattr(args, "all_symbols", False):
        return equity_list

    symbols = getattr(args, "symbols", None)
    if not symbols:
        raise SystemExit("Provide at least one symbol or pass --all.")

    return [symbol.upper() for symbol in symbols]


def _print_json(data: Any) -> None:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            print(data)
            return

    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def _print_records(records: list[dict], limit: int | None = None) -> None:
    for record in records[:limit]:
        _print_json(record)


def cmd_symbols(args: argparse.Namespace) -> int:
    symbols = _resolve_symbols(args)

    if args.symbol_action == "list":
        for symbol in symbols:
            print(symbol)
        return 0

    if args.symbol_action == "duplicates":
        duplicates = find_duplicate_symbols(symbols)
        _print_json({"duplicates": duplicates})
        return 1 if duplicates else 0

    if args.symbol_action == "validate":
        ensure_no_duplicates(symbols)
        _print_json({"valid": True, "count": len(symbols)})
        return 0

    if args.symbol_action == "shortable":
        _print_json(check_shortable(symbols))
        return 0

    raise SystemExit(f"Unknown symbols action: {args.symbol_action}")


def cmd_intervals(args: argparse.Namespace) -> int:
    intervals = generate_market_intervals(args.start, args.end, args.num_intervals)
    if args.count:
        print(len(intervals))
        return 0

    rows = [
        {"start": start.isoformat(), "end": end.isoformat()}
        for start, end in intervals
    ]
    _print_json(rows)
    return 0


async def cmd_fetch_history(args: argparse.Namespace) -> int:
    symbols = _resolve_symbols(args)
    intervals = generate_market_intervals(args.start, args.end, args.num_intervals)
    await generate_historical_file(symbols, intervals, args.batch_size)
    return 0


async def cmd_generate_training(args: argparse.Namespace) -> int:
    symbols = _resolve_symbols(args)
    await generate_training_files(symbols, args.batch_size, args.natural_min)
    return 0


async def cmd_pipeline(args: argparse.Namespace) -> int:
    symbols = _resolve_symbols(args)
    intervals = generate_market_intervals(args.start, args.end, args.num_intervals)
    await generate_historical_file(symbols, intervals, args.fetch_batch_size)
    await generate_training_files(symbols, args.training_batch_size, args.natural_min)
    return 0


def cmd_inputs(args: argparse.Namespace) -> int:
    bar_data = read_data(args.file, args.read_index, args.read_size)
    _print_json(generate_inputs_batch(bar_data, args.start_index, args.batch_size))
    return 0


def cmd_labels(args: argparse.Namespace) -> int:
    bar_data = read_data(args.file, args.read_index, args.read_size)
    if args.batch_size is None:
        _print_json(generate_labels(bar_data, args.start_index, args.natural_min))
    else:
        _print_json(
            generate_labels_batch(
                bar_data,
                args.start_index,
                args.batch_size,
                args.natural_min,
            )
        )
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    _print_records(read_data(args.file, args.read_index, args.batch_size), args.limit)
    return 0


def cmd_shuffle(args: argparse.Namespace) -> int:
    shuffle_data(args.file)
    return 0


async def _call_market_data(args: argparse.Namespace) -> Any:
    from brokerage_api.market_data import stock_api

    if args.api_function in SINGLE_SYMBOL_WITH_PARAMS | SINGLE_SYMBOL_NO_PARAMS:
        if not args.symbol:
            raise SystemExit(f"{args.api_function} requires --symbol.")
    elif args.symbol:
        raise SystemExit(f"{args.api_function} uses --symbols, not --symbol.")

    params = _parse_key_value(args.param)
    if getattr(args, "symbols", None):
        params["symbols"] = ",".join(symbol.upper() for symbol in args.symbols)
    if getattr(args, "start", None):
        params["start"] = args.start
    if getattr(args, "end", None):
        params["end"] = args.end
    if getattr(args, "timeframe", None):
        params["timeframe"] = args.timeframe
    if getattr(args, "limit", None):
        params["limit"] = str(args.limit)

    call: Callable[..., Any] = getattr(stock_api, args.api_function)
    if args.api_function in SINGLE_SYMBOL_WITH_PARAMS:
        return await call(args.symbol.upper(), params)
    if args.api_function in SINGLE_SYMBOL_NO_PARAMS:
        return await call(args.symbol.upper())
    return await call(params)


async def cmd_market_data(args: argparse.Namespace) -> int:
    _print_json(await _call_market_data(args))
    return 0


def cmd_trading(args: argparse.Namespace) -> int:
    if args.trading_action == "account":
        from brokerage_api.trading.accounts_api import get_account

        _print_json(get_account())
        return 0

    if args.trading_action == "positions":
        from brokerage_api.trading.positions_api import get_positions

        _print_json(get_positions())
        return 0

    if args.trading_action == "position":
        from brokerage_api.trading.positions_api import get_position

        _print_json(get_position(args.symbol.upper()))
        return 0

    if args.trading_action == "close-position":
        from brokerage_api.trading.positions_api import close_position

        _print_json(close_position(args.symbol.upper()))
        return 0

    if args.trading_action == "close-all-positions":
        from brokerage_api.trading.positions_api import close_all_positions

        _print_json(close_all_positions())
        return 0

    if args.trading_action == "exercise-option":
        from brokerage_api.trading.positions_api import exercise_option

        _print_json(exercise_option(args.symbol_or_id))
        return 0

    if args.trading_action == "assets":
        from brokerage_api.trading.assets_api import get_assets

        _print_json(get_assets(_parse_key_value(args.param)))
        return 0

    if args.trading_action == "asset":
        from brokerage_api.trading.assets_api import get_asset

        _print_json(get_asset(args.symbol_or_id))
        return 0

    if args.trading_action == "options":
        from brokerage_api.trading.assets_api import get_options

        _print_json(get_options(_parse_key_value(args.param)))
        return 0

    if args.trading_action == "option":
        from brokerage_api.trading.assets_api import get_option

        _print_json(get_option(args.symbol_or_id))
        return 0

    if args.trading_action == "orders":
        from brokerage_api.trading.orders_api import get_orders

        _print_json(get_orders(_parse_key_value(args.param)))
        return 0

    if args.trading_action == "order":
        from brokerage_api.trading.orders_api import get_order

        _print_json(get_order(args.order_id, _parse_key_value(args.param)))
        return 0

    if args.trading_action == "cancel-order":
        from brokerage_api.trading.orders_api import cancel_order

        _print_json(cancel_order(args.order_id))
        return 0

    if args.trading_action == "cancel-all-orders":
        from brokerage_api.trading.orders_api import cancel_all_orders

        _print_json(cancel_all_orders())
        return 0

    if args.trading_action == "place-order":
        from brokerage_api.trading.orders_api import place_order

        _print_json(place_order(json.loads(args.body)))
        return 0

    if args.trading_action == "update-order":
        from brokerage_api.trading.orders_api import update_order

        _print_json(update_order(args.order_id, json.loads(args.body)))
        return 0

    from brokerage_api.trading import orders

    if args.trading_action == "buy-market":
        _print_json(orders.buy_market_order(args.symbol.upper(), args.qty))
    elif args.trading_action == "sell-market":
        _print_json(orders.sell_market_order(args.symbol.upper(), args.qty))
    elif args.trading_action == "buy-limit":
        _print_json(orders.buy_limit_order(args.symbol.upper(), args.qty, args.limit_price))
    elif args.trading_action == "sell-limit":
        _print_json(orders.sell_limit_order(args.symbol.upper(), args.qty, args.limit_price))
    elif args.trading_action == "bracket-order":
        _print_json(
            orders.place_bracket_order(
                args.symbol.upper(),
                args.qty,
                args.take_profit_price,
                args.stop_loss_price,
            )
        )
    elif args.trading_action == "trailing-stop":
        _print_json(orders.place_trailing_stop_order(args.symbol.upper(), args.qty, args.trail_price))
    elif args.trading_action == "short":
        _print_json(orders.short_stock(args.symbol.upper(), args.qty, args.order_type, args.time_in_force))
    elif args.trading_action == "cover-short":
        _print_json(orders.cover_short(args.symbol.upper(), args.qty, args.order_type, args.time_in_force))
    else:
        raise SystemExit(f"Unknown trading action: {args.trading_action}")

    return 0


def _add_symbols_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("symbols", nargs="*", help="Ticker symbols")
    parser.add_argument("--all", action="store_true", dest="all_symbols", help="Use the built-in equity universe")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fintan", description="CLI for Fintan data, indicator, and trading workflows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    symbols = subparsers.add_parser("symbols", help="Inspect the built-in or provided symbol universe")
    symbols.add_argument("symbol_action", choices=["list", "duplicates", "validate", "shortable"])
    _add_symbols_flags(symbols)
    symbols.set_defaults(func=cmd_symbols)

    intervals = subparsers.add_parser("intervals", help="Generate NYSE market intervals")
    intervals.add_argument("--start", required=True, type=_parse_datetime)
    intervals.add_argument("--end", required=True, type=_parse_datetime)
    intervals.add_argument("--num-intervals", type=int, default=50)
    intervals.add_argument("--count", action="store_true")
    intervals.set_defaults(func=cmd_intervals)

    fetch = subparsers.add_parser("fetch-history", help="Fetch Alpaca historical bars into historical_files/")
    _add_symbols_flags(fetch)
    fetch.add_argument("--start", required=True, type=_parse_datetime)
    fetch.add_argument("--end", required=True, type=_parse_datetime)
    fetch.add_argument("--num-intervals", type=int, default=50)
    fetch.add_argument("--batch-size", type=int, default=256)
    fetch.set_defaults(func=cmd_fetch_history)

    training = subparsers.add_parser("generate-training", help="Generate training_files/ from historical_files/")
    _add_symbols_flags(training)
    training.add_argument("--batch-size", type=int, default=256)
    training.add_argument("--natural-min", type=float, default=0.0005)
    training.set_defaults(func=cmd_generate_training)

    pipeline = subparsers.add_parser("pipeline", help="Fetch historical bars and generate training files")
    _add_symbols_flags(pipeline)
    pipeline.add_argument("--start", required=True, type=_parse_datetime)
    pipeline.add_argument("--end", required=True, type=_parse_datetime)
    pipeline.add_argument("--num-intervals", type=int, default=50)
    pipeline.add_argument("--fetch-batch-size", type=int, default=256)
    pipeline.add_argument("--training-batch-size", type=int, default=256)
    pipeline.add_argument("--natural-min", type=float, default=0.0005)
    pipeline.set_defaults(func=cmd_pipeline)

    inputs = subparsers.add_parser("inputs", help="Compute indicator inputs from a JSONL bar file")
    inputs.add_argument("file")
    inputs.add_argument("--start-index", type=int, default=0)
    inputs.add_argument("--batch-size", type=int, default=256)
    inputs.add_argument("--read-index", type=int, default=0)
    inputs.add_argument("--read-size", type=int)
    inputs.set_defaults(func=cmd_inputs)

    labels = subparsers.add_parser("labels", help="Compute labels from a JSONL bar file")
    labels.add_argument("file")
    labels.add_argument("--start-index", type=int, default=0)
    labels.add_argument("--batch-size", type=int)
    labels.add_argument("--natural-min", type=float, default=0.0005)
    labels.add_argument("--read-index", type=int, default=0)
    labels.add_argument("--read-size", type=int)
    labels.set_defaults(func=cmd_labels)

    read = subparsers.add_parser("read-jsonl", help="Read records from a JSONL file")
    read.add_argument("file")
    read.add_argument("--read-index", type=int, default=0)
    read.add_argument("--batch-size", type=int)
    read.add_argument("--limit", type=int)
    read.set_defaults(func=cmd_read)

    shuffle = subparsers.add_parser("shuffle-jsonl", help="Shuffle a JSONL file in place")
    shuffle.add_argument("file")
    shuffle.set_defaults(func=cmd_shuffle)

    market = subparsers.add_parser("market-data", help="Call Alpaca market-data wrappers")
    market.add_argument(
        "api_function",
        choices=[
            "get_historical_auctions",
            "get_historical_quotes",
            "get_historical_trades",
            "get_historical_bars",
            "get_single_historical_auctions",
            "get_single_historical_quotes",
            "get_single_historical_trades",
            "get_single_historical_bars",
            "get_latest_trades",
            "get_latest_trade",
            "get_latest_quotes",
            "get_latest_quote",
            "get_latest_bars",
            "get_snapshots",
            "get_snapshot",
        ],
    )
    market.add_argument("--symbols", nargs="+")
    market.add_argument("--symbol")
    market.add_argument("--start")
    market.add_argument("--end")
    market.add_argument("--timeframe")
    market.add_argument("--limit", type=int)
    market.add_argument("--param", action="append", help="Additional query parameter as KEY=VALUE")
    market.set_defaults(func=cmd_market_data)

    trading = subparsers.add_parser("trading", help="Call Alpaca trading wrappers")
    trading_sub = trading.add_subparsers(dest="trading_action", required=True)
    _add_trading_parsers(trading_sub)

    return parser


def _add_param_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--param", action="append", help="Query parameter as KEY=VALUE")


def _add_order_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("symbol")
    parser.add_argument("qty", type=int)


def _add_trading_parsers(subparsers: argparse._SubParsersAction) -> None:
    for name in ["account", "positions", "close-all-positions", "cancel-all-orders"]:
        subparsers.add_parser(name).set_defaults(func=cmd_trading)

    for name in ["position", "close-position"]:
        parser = subparsers.add_parser(name)
        parser.add_argument("symbol")
        parser.set_defaults(func=cmd_trading)

    parser = subparsers.add_parser("exercise-option")
    parser.add_argument("symbol_or_id")
    parser.set_defaults(func=cmd_trading)

    for name in ["assets", "options", "orders"]:
        parser = subparsers.add_parser(name)
        _add_param_flags(parser)
        parser.set_defaults(func=cmd_trading)

    for name in ["asset", "option"]:
        parser = subparsers.add_parser(name)
        parser.add_argument("symbol_or_id")
        parser.set_defaults(func=cmd_trading)

    parser = subparsers.add_parser("order")
    parser.add_argument("order_id")
    _add_param_flags(parser)
    parser.set_defaults(func=cmd_trading)

    parser = subparsers.add_parser("cancel-order")
    parser.add_argument("order_id")
    parser.set_defaults(func=cmd_trading)

    parser = subparsers.add_parser("place-order")
    parser.add_argument("body", help="JSON request body")
    parser.set_defaults(func=cmd_trading)

    parser = subparsers.add_parser("update-order")
    parser.add_argument("order_id")
    parser.add_argument("body", help="JSON request body")
    parser.set_defaults(func=cmd_trading)

    for name in ["buy-market", "sell-market"]:
        parser = subparsers.add_parser(name)
        _add_order_common(parser)
        parser.set_defaults(func=cmd_trading)

    for name in ["buy-limit", "sell-limit"]:
        parser = subparsers.add_parser(name)
        _add_order_common(parser)
        parser.add_argument("limit_price", type=float)
        parser.set_defaults(func=cmd_trading)

    parser = subparsers.add_parser("bracket-order")
    _add_order_common(parser)
    parser.add_argument("take_profit_price", type=float)
    parser.add_argument("stop_loss_price", type=float)
    parser.set_defaults(func=cmd_trading)

    parser = subparsers.add_parser("trailing-stop")
    _add_order_common(parser)
    parser.add_argument("trail_price", type=float)
    parser.set_defaults(func=cmd_trading)

    for name in ["short", "cover-short"]:
        parser = subparsers.add_parser(name)
        _add_order_common(parser)
        parser.add_argument("--order-type", default="market")
        parser.add_argument("--time-in-force", default="day")
        parser.set_defaults(func=cmd_trading)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    if asyncio.iscoroutine(result):
        return asyncio.run(result)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
