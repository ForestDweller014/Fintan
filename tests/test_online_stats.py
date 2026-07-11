import math
import unittest

from online_stats import welford_mean_std, welford_zscore


class OnlineStatsTest(unittest.TestCase):
    def test_welford_population_std_matches_two_pass_calculation(self):
        values = [0.0, 2.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]

        mean, std_dev = welford_mean_std(values)
        expected_mean = sum(values) / len(values)
        expected_std = math.sqrt(
            sum((value - expected_mean) ** 2 for value in values) / len(values)
        )

        self.assertAlmostEqual(mean, expected_mean)
        self.assertAlmostEqual(std_dev, expected_std)

    def test_welford_zscore_returns_last_value_zscore(self):
        values = [10.0, 12.0, 13.0, 17.0]
        mean = sum(values) / len(values)
        std_dev = math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))

        self.assertAlmostEqual(welford_zscore(values), (values[-1] - mean) / std_dev)

    def test_welford_zscore_handles_empty_and_flat_series(self):
        self.assertEqual(welford_zscore([]), 0.0)
        self.assertEqual(welford_zscore([3.0, 3.0, 3.0]), 0.0)


if __name__ == "__main__":
    unittest.main()
