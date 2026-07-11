import unittest

from fintan_cli import build_parser


class CliParserTest(unittest.TestCase):
    def test_parser_accepts_symbol_validation_command(self):
        args = build_parser().parse_args(["symbols", "validate", "--all"])

        self.assertEqual(args.command, "symbols")
        self.assertEqual(args.symbol_action, "validate")
        self.assertTrue(args.all_symbols)

    def test_parser_accepts_fetch_history_command(self):
        args = build_parser().parse_args(
            [
                "fetch-history",
                "AAPL",
                "MSFT",
                "--start",
                "2025-01-02T09:30:00",
                "--end",
                "2025-01-02T16:00:00",
                "--num-intervals",
                "50",
                "--batch-size",
                "128",
            ]
        )

        self.assertEqual(args.command, "fetch-history")
        self.assertEqual(args.symbols, ["AAPL", "MSFT"])
        self.assertEqual(args.num_intervals, 50)
        self.assertEqual(args.batch_size, 128)

    def test_parser_accepts_trading_subcommand(self):
        args = build_parser().parse_args(["trading", "buy-limit", "AAPL", "2", "100.50"])

        self.assertEqual(args.command, "trading")
        self.assertEqual(args.trading_action, "buy-limit")
        self.assertEqual(args.symbol, "AAPL")
        self.assertEqual(args.qty, 2)
        self.assertEqual(args.limit_price, 100.50)


if __name__ == "__main__":
    unittest.main()
