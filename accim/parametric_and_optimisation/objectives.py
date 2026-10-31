# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Objective reducer helpers for BESOS evaluations.

This module provides small functions that transform the time series stored in
``result.data["Value"]`` into scalar objectives or list outputs.

Usage
-----
Pass these functions as output reducers in optimisation or parametric
configurations when you need a mean, a sum, or the raw time series.

Examples
--------
avg = average_results(result)
total = sum_results(result)
checked_total = checked_sum_results(result)
series = return_time_series(result)
"""
import numpy as np


def average_results(result):
    """Compute the arithmetic mean of ``result.data["Value"]``.

    Parameters
    ----------
    result : Any
        BESOS/evaluator result object exposing a dataframe-like ``data``
        attribute with a ``"Value"`` column.

    Returns
    -------
    float
        Mean of all values in ``result.data["Value"]``.

    Usage
    -----
    Use this reducer when an output must be summarized as a single average
    value.

    Examples
    --------
    avg = average_results(result)
    """
    return result.data["Value"].mean()


def sum_results(result):
    """Compute the sum of ``result.data["Value"]``.

    Parameters
    ----------
    result : Any
        BESOS/evaluator result object exposing ``data["Value"]``.

    Returns
    -------
    float
        Sum of all values in ``result.data["Value"]``.

    Usage
    -----
    Use this reducer when a cumulative metric is required as objective.

    Examples
    --------
    total = sum_results(result)
    """
    return result.data["Value"].sum()


def checked_sum_results(result):
    """Compute the sum of ``result.data["Value"]``, failing on missing or invalid values.

    Unlike :func:`sum_results`, with which pandas skips the missing values (NaN), this reducer stops
    with a ``ValueError`` when the result has no ``"Value"`` series, when the series is empty, not
    numeric or not one-dimensional, when it has NaN or infinite values, or when the sum overflows.

    Parameters
    ----------
    result : Any
        BESOS/evaluator result object exposing ``data["Value"]``.

    Returns
    -------
    float
        Sum of all values in ``result.data["Value"]``, as a finite Python ``float``.

    Raises
    ------
    ValueError
        If the values are missing or invalid; the EnergyPlus error file of the evaluation usually
        explains why.

    Usage
    -----
    Use this reducer instead of :func:`sum_results` for cumulative objectives (energy, for
    instance), so that an incomplete or failed simulation does not pass as a valid value. It makes
    no unit conversion.

    Examples
    --------
    total = checked_sum_results(result)
    """
    data = getattr(result, 'data', None)
    if data is None or 'Value' not in data:
        raise ValueError('The result has no "Value" series; check the EnergyPlus error file of the evaluation.')
    try:
        values = np.asarray(data['Value'], dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError('The values of the objective must be numbers.') from exc
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError('The values of the objective must be a non-empty, one-dimensional series of finite '
                         'numbers.')
    with np.errstate(over='ignore', invalid='ignore'):
        total = float(values.sum())
    if not np.isfinite(total):
        raise ValueError('The sum of the objective is not a finite number.')
    return total


def return_time_series(result):
    """Convert ``result.data["Value"]`` to a Python list.

    Parameters
    ----------
    result : Any
        BESOS/evaluator result object exposing ``data["Value"]``.

    Returns
    -------
    list
        Ordered values from the ``"Value"`` column.

    Usage
    -----
    Use this reducer when downstream post-processing requires the full time
    series instead of a scalar metric.

    Examples
    --------
    values = return_time_series(result)
    """
    return result.data["Value"].to_list()
