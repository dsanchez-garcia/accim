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
``hours_outside_comfort`` and ``fraction_outside_comfort`` turn the adaptive
comfort status that EnergyPlus reports for each People object into a comfort
objective that does not depend on the comfort model that accim controls.

Examples
--------
avg = average_results(result)
total = sum_results(result)
checked_total = checked_sum_results(result)
series = return_time_series(result)
hours = hours_outside_comfort(result)
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


def _comfort_status(result, frequencies):
    """The values of an adaptive comfort status of EnergyPlus (1, 0 or -1, or their means), checked."""
    data = getattr(result, 'data', None)
    if data is None or 'Value' not in data:
        raise ValueError('The result has no "Value" series; check the EnergyPlus error file of the evaluation.')
    try:
        values = np.asarray(data['Value'], dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError('The values of the comfort status must be numbers.') from exc
    if values.ndim != 1 or not np.isfinite(values).all() or ((values < -1) | (values > 1)).any():
        raise ValueError('The values are not those of an adaptive comfort status of EnergyPlus (from -1 to 1), such '
                         'as "Zone Thermal Comfort CEN 15251 Adaptive Model Category II Status".')
    frequency = str(getattr(result, 'frequency', None) or '').strip()
    if frequency and frequency.lower() not in frequencies:
        raise ValueError(f'The comfort status is reported with the frequency {frequency}; this reducer needs '
                         f'{" or ".join(frequencies)} values.')
    # 1 inside the comfort range, 0 outside, -1 without occupants or out of the range of the model
    return values[values >= 0]


def hours_outside_comfort(result):
    """Compute the occupied hours outside the comfort range of an hourly adaptive comfort status of EnergyPlus.

    EnergyPlus reports, for each People object with the adaptive comfort models (which accim adds to all of
    them), whether its zone is within the range of ASHRAE 55 (``Zone Thermal Comfort ASHRAE 55 Adaptive Model
    80% Acceptability Status``, or 90 %) and of CEN 15251 (``Zone Thermal Comfort CEN 15251 Adaptive Model
    Category II Status``, or I or III): 1 inside, 0 outside, and -1 when the zone has no occupants or the running
    mean outdoor temperature is out of the range of the model. These ranges do not depend on the control of
    accim, so they measure comfort with the same model in every evaluation, also when the optimisation changes
    the comfort model that accim controls (the coefficients of the custom model, or the aPMV setpoints).

    Parameters
    ----------
    result : Any
        BESOS result of the status variable of one People object, reported hourly (each value is the mean of
        the status in the hour).

    Returns
    -------
    float
        The sum of ``1 - value`` over the hours whose value is between 0 and 1: the hours, or their fractions,
        that the occupied zone spends outside the comfort range. The hours with -1 do not count, so 0 may also
        mean that the zone is never occupied, or that the key is not the People object of the zone.

    Raises
    ------
    ValueError
        If the values are missing, out of the range -1 to 1 (not a comfort status), or not hourly. If the
        occupants arrive or leave within an hour, its value mixes -1 with the others: report the status at
        each timestep and use :func:`fraction_outside_comfort` instead.

    Usage
    -----
    Use it as the reducer of a VariableReader (or as the ``func`` of a row of the output readers of the
    parametric module) of the status variable, with the People object as key and hourly frequency, to minimise
    the discomfort along with the energy use.

    Examples
    --------
    hours = hours_outside_comfort(result)
    """
    occupied = _comfort_status(result, ('hourly',))
    return float((1 - occupied).sum())


def fraction_outside_comfort(result):
    """Compute the fraction of the occupied time outside the comfort range of an adaptive comfort status.

    The comfort status of EnergyPlus is described in :func:`hours_outside_comfort`. With values of each
    timestep, the fraction is exact whenever the occupants arrive or leave; with hourly values, it is exact if
    they arrive and leave on the hour.

    Parameters
    ----------
    result : Any
        BESOS result of the status variable of one People object, reported at each timestep or hourly.

    Returns
    -------
    float
        The mean of ``1 - value`` over the values between 0 and 1, from 0 (always within the range when occupied)
        to 1; 0 if the zone is never occupied within the range of the model.

    Raises
    ------
    ValueError
        If the values are missing, out of the range -1 to 1 (not a comfort status), or neither of each timestep
        nor hourly.

    Usage
    -----
    Use it as the reducer of the status variable when the time outside the comfort range matters relative to
    the occupied time (the criteria of EN 16798-1 allow a few per cent of the occupied hours, for instance).

    Examples
    --------
    share = fraction_outside_comfort(result)
    """
    occupied = _comfort_status(result, ('timestep', 'hourly'))
    return float((1 - occupied).mean()) if len(occupied) else 0.0


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
