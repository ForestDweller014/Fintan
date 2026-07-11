import math
from typing import Iterable


def welford_mean_std(values: Iterable[float]) -> tuple[float, float]:
    count = 0
    mean = 0.0
    m2 = 0.0

    for value in values:
        count += 1
        delta = value - mean
        mean += delta / count
        m2 += delta * (value - mean)

    if count == 0:
        return 0.0, 0.0

    return mean, math.sqrt(m2 / count)


def welford_zscore(values: Iterable[float]) -> float:
    series = list(values)
    if not series:
        return 0.0

    mean, std_dev = welford_mean_std(series)
    return (series[-1] - mean) / std_dev if std_dev > 0 else 0.0
