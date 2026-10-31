"""Tests for the reducers of accim.parametric_and_optimisation.objectives.

checked_sum_results comes from the tag archive/feat-comfort-metrics-experiment-api (notes/branch-reviews.md, 2.2).
"""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from accim.parametric_and_optimisation.objectives import (average_results, checked_sum_results, return_time_series,
                                                          sum_results)


def _result(values):
    return SimpleNamespace(data=pd.DataFrame({'Value': values}))


@pytest.mark.parametrize('values', [[], [np.nan], [np.inf], [[1, 2]], ['not a number'], [1e308, 1e308]])
def test_checked_sum_results_rejects_invalid_objectives(values):
    with pytest.raises(ValueError):
        checked_sum_results(SimpleNamespace(data={'Value': values}))


def test_checked_sum_results_returns_one_finite_float():
    result = checked_sum_results(SimpleNamespace(data={'Value': [0.1, 0.2, 0.3]}))

    assert isinstance(result, float)
    assert result == pytest.approx(0.6)


@pytest.mark.parametrize('result', [None, SimpleNamespace(data=None), SimpleNamespace(data={'Other': [1.0]})])
def test_checked_sum_results_needs_a_value_series(result):
    with pytest.raises(ValueError, match='"Value" series'):
        checked_sum_results(result)


def test_with_missing_values_sum_results_skips_them_and_checked_sum_results_stops():
    # An empty or incomplete series must not give a valid objective (0 would look like the best energy use)
    assert sum_results(_result([1.0, np.nan, 2.0])) == 3.0
    assert sum_results(_result(pd.Series([], dtype=float))) == 0.0
    with pytest.raises(ValueError, match='finite numbers'):
        checked_sum_results(_result([1.0, np.nan, 2.0]))
    with pytest.raises(ValueError, match='finite numbers'):
        checked_sum_results(_result(pd.Series([], dtype=float)))


def test_the_reducers_of_a_dataframe_result():
    result = _result([1.0, 2.0, 4.5])

    assert checked_sum_results(result) == 7.5
    assert sum_results(result) == 7.5
    assert average_results(result) == 2.5
    assert return_time_series(result) == [1.0, 2.0, 4.5]
