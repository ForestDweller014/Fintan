from brokerage_api.trading import orders_api

def place_bracket_order(symbol: str, qty: int, take_profit_price: float, stop_loss_price: float) -> str:
    """
    Place a bracket order for a given symbol, quantity, take profit price, and stop loss price.
    Input parameters: symbol: str, qty: int, take_profit_price: float, stop_loss_price: float
    Returns response data from the API as a JSON-formatted string.
    """
    
    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": "buy",
        "type": "market",
        "time_in_force": "gtc",
        "order_class": "bracket",
        "take_profit": { "limit_price": take_profit_price },
        "stop_loss": { "stop_price": stop_loss_price }
    }
    return orders_api.place_order(payload)

def place_trailing_stop_order(symbol: str, qty: int, trail_price: float) -> str:
    """
    Place a trailing stop order for a given symbol, quantity, and trail price.
    Input parameters: symbol: str, qty: int, trail_price: float
    Returns response data from the API as a JSON-formatted string.
    """

    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": "sell",
        "type": "trailing_stop",
        "trail_price": trail_price,
        "time_in_force": "gtc",
    }
    return orders_api.place_order(payload)

def buy_market_order(symbol: str, qty: int) -> str:
    """
    Place a market order to buy a given symbol and quantity.
    Input parameters: symbol: str, qty: int
    Returns response data from the API as a JSON-formatted string.
    """

    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": "buy",
        "type": "market",
        "time_in_force": "gtc",
    }
    return orders_api.place_order(payload)

def sell_market_order(symbol: str, qty: int) -> str:
    """
    Place a market order to sell a given symbol and quantity.
    Input parameters: symbol: str, qty: int
    Returns response data from the API as a JSON-formatted string.
    """

    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": "sell",
        "type": "market",
        "time_in_force": "gtc",
    }
    return orders_api.place_order(payload)

def buy_limit_order(symbol: str, qty: int, limit_price: float) -> str:
    """
    Place a limit order to buy a given symbol and quantity at a given limit price.
    Input parameters: symbol: str, qty: int, limit_price: float
    Returns response data from the API as a JSON-formatted string.
    """

    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": "buy",
        "type": "limit",
        "time_in_force": "gtc",
        "limit_price": limit_price,
    }
    return orders_api.place_order(payload)

def sell_limit_order(symbol: str, qty: int, limit_price: float) -> str:
    """
    Place a limit order to sell a given symbol and quantity at a given limit price.
    Input parameters: symbol: str, qty: int, limit_price: float
    Returns response data from the API as a JSON-formatted string.
    """

    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": "sell",
        "type": "limit",
        "time_in_force": "gtc",
        "limit_price": limit_price,
    }
    return orders_api.place_order(payload)

def short_stock(symbol: str, qty: int, order_type: str = "market", time_in_force: str = "day") -> str:
    """
    Short a given symbol and quantity.
    Input parameters: symbol: str, qty: int, order_type: str, time_in_force: str
    Returns response data from the API as a JSON-formatted string.
    """

    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": "sell",
        "type": order_type,
        "time_in_force": time_in_force,
    }
    return orders_api.place_order(payload)

def cover_short(symbol: str, qty: int, order_type: str = "market", time_in_force: str = "day") -> str:
    """
    Cover a short position for a given symbol and quantity.
    Input parameters: symbol: str, qty: int, order_type: str, time_in_force: str
    Returns response data from the API as a JSON-formatted string.
    """

    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": "buy",
        "type": order_type,
        "time_in_force": time_in_force,
    }
    return orders_api.place_order(payload)