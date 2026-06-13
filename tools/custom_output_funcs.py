import pandas as pd


def return_time_series(series: pd.Series):
    """Return the full series unchanged (for hourly/time-series outputs)."""
    return series


def q95(series: pd.Series) -> float:
    """Return the 95th percentile of the series."""
    return float(series.quantile(0.95))


def mean_value(series: pd.Series) -> float:
    """Return the arithmetic mean of the series."""
    return float(series.mean())

