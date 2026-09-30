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
series = return_time_series(result)
"""

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
    """Sum a nonempty finite scalar-valued BESOS series, failing on bad data.

    Unlike the permissive legacy :func:`sum_results`, this opt-in reducer
    rejects missing ``Value``, empty/non-numeric/multidimensional series,
    NaN/Inf and overflow instead of allowing pandas to skip missing values.
    Returns a finite Python ``float``. It is importable by multiprocessing
    workers as ``accim.parametric_and_optimisation.objectives:checked_sum_results``.

    Use for cumulative energy or timestep-increment discomfort objectives.
    Do not multiply already integrated hourly degree-hour/hour outputs by
    duration again. This reducer performs no unit conversion.
    """
    import numpy as np

    data = getattr(result, 'data', None)
    if data is None or 'Value' not in data:
        raise ValueError('Missing BESOS result / Value series; inspect the EnergyPlus error file.')
    try:
        values = np.asarray(data['Value'], dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError('Objective values must be numeric scalars.') from exc
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError('Objective series must be nonempty, one-dimensional and finite.')
    with np.errstate(over='ignore', invalid='ignore'):
        total = float(values.sum())
    if not np.isfinite(total):
        raise ValueError('Objective sum must be a finite scalar.')
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
