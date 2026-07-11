import unittest
from unittest.mock import patch

from app_config import load_config


class AppConfigTest(unittest.TestCase):
    def test_load_config_uses_safe_defaults_without_local_file(self):
        with patch.dict("os.environ", {}, clear=True):
            config = load_config("missing-config.json")

        self.assertEqual(config["trading_mode"], "paper")
        self.assertEqual(config["paper"]["apiserver_domain"], "https://paper-api.alpaca.markets")
        self.assertEqual(config["PREDICTION_SIZE"], 27)
        self.assertEqual(config["OPENAI_API_KEY"], "")

    def test_environment_overrides_credentials_and_numeric_settings(self):
        env = {
            "TRADING_MODE": "live",
            "ALPACA_LIVE_API_KEY_ID": "live-key",
            "ALPACA_LIVE_API_SECRET_KEY": "live-secret",
            "OPENAI_API_KEY": "openai-token",
            "PREDICTION_SIZE": "42",
        }

        with patch.dict("os.environ", env, clear=True):
            config = load_config("missing-config.json")

        self.assertEqual(config["trading_mode"], "live")
        self.assertEqual(config["live"]["api_key_id"], "live-key")
        self.assertEqual(config["live"]["api_secret_key"], "live-secret")
        self.assertEqual(config["OPENAI_API_KEY"], "openai-token")
        self.assertEqual(config["PREDICTION_SIZE"], 42)

    def test_invalid_trading_mode_raises(self):
        with patch.dict("os.environ", {"TRADING_MODE": "cash"}, clear=True):
            with self.assertRaises(ValueError):
                load_config("missing-config.json")


if __name__ == "__main__":
    unittest.main()
