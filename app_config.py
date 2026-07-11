import json
import os
from copy import deepcopy

DEFAULT_CONFIG = {
    "trading_mode": "paper",
    "live": {
        "api_key_id": "",
        "api_secret_key": "",
        "apiserver_domain": "https://api.alpaca.markets",
    },
    "paper": {
        "api_key_id": "",
        "api_secret_key": "",
        "apiserver_domain": "https://paper-api.alpaca.markets",
    },
    "HUGGINGFACE_HUB_TOKEN": "",
    "FINNHUB_API_KEY": "",
    "GROQ_TOKEN": "",
    "OPENAI_API_KEY": "",
    "STAY_SIZE": 5,
    "PREDICTION_SIZE": 27,
    "INTERVAL_DURATION": 1,
    "MAX_CALLS_PER_PERIOD": 200,
}

ENV_OVERRIDES = {
    "trading_mode": ("TRADING_MODE", str),
    ("live", "api_key_id"): ("ALPACA_LIVE_API_KEY_ID", str),
    ("live", "api_secret_key"): ("ALPACA_LIVE_API_SECRET_KEY", str),
    ("live", "apiserver_domain"): ("ALPACA_LIVE_APISERVER_DOMAIN", str),
    ("paper", "api_key_id"): ("ALPACA_PAPER_API_KEY_ID", str),
    ("paper", "api_secret_key"): ("ALPACA_PAPER_API_SECRET_KEY", str),
    ("paper", "apiserver_domain"): ("ALPACA_PAPER_APISERVER_DOMAIN", str),
    "HUGGINGFACE_HUB_TOKEN": ("HUGGINGFACE_HUB_TOKEN", str),
    "FINNHUB_API_KEY": ("FINNHUB_API_KEY", str),
    "GROQ_TOKEN": ("GROQ_TOKEN", str),
    "OPENAI_API_KEY": ("OPENAI_API_KEY", str),
    "STAY_SIZE": ("STAY_SIZE", int),
    "PREDICTION_SIZE": ("PREDICTION_SIZE", int),
    "INTERVAL_DURATION": ("INTERVAL_DURATION", int),
    "MAX_CALLS_PER_PERIOD": ("MAX_CALLS_PER_PERIOD", int),
}


def _set_nested(config, key, value):
    if isinstance(key, tuple):
        target = config
        for part in key[:-1]:
            target = target[part]
        target[key[-1]] = value
    else:
        config[key] = value


def load_config(config_file="config.json"):
    config = deepcopy(DEFAULT_CONFIG)

    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            file_config = json.load(file)
        for key, value in file_config.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value

    for key, (env_name, caster) in ENV_OVERRIDES.items():
        value = os.getenv(env_name)
        if value is not None:
            _set_nested(config, key, caster(value))

    if config["trading_mode"] not in ("paper", "live"):
        raise ValueError('trading_mode must be "paper" or "live"')

    return config

APP_CONFIG = load_config()
TRADING_CONFIG = APP_CONFIG[APP_CONFIG["trading_mode"]]
API_KEY_ID = TRADING_CONFIG["api_key_id"]
API_SECRET_KEY = TRADING_CONFIG["api_secret_key"]
APISERVER_DOMAIN = TRADING_CONFIG["apiserver_domain"]
HUGGINGFACE_HUB_TOKEN = APP_CONFIG["HUGGINGFACE_HUB_TOKEN"]
FINNHUB_API_KEY = APP_CONFIG["FINNHUB_API_KEY"]
GROQ_TOKEN = APP_CONFIG["GROQ_TOKEN"]
OPENAI_API_KEY = APP_CONFIG["OPENAI_API_KEY"]
