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
``hours_outside_range`` and ``degree_hours`` read the long-term discomfort of
the occupied hours that the ACCIS counts (Methods A and B of CEN/TR 16798-2:2019,
Annex D, with ``report_long_term_discomfort``), ``ppd_weighted_hours`` the
PPD-weighted hours that the setpoints based on the PMV count (Method C, with
``report_ppd_weighted_hours``), and ``deviation_constraint_bound`` gives the
bound of a constraint with the acceptable deviations of its Annex E (Table E.1).
``WorstPeriodDeviation`` is a reader of besos for a constraint with the
deviations of the worst week, month or year of each evaluation.

Examples
--------
avg = average_results(result)
total = sum_results(result)
checked_total = checked_sum_results(result)
series = return_time_series(result)
hours = hours_outside_comfort(result)
hot_hours = hours_outside_range(result)
weighted_hours = ppd_weighted_hours(result)
bound = deviation_constraint_bound(occupied_hours=2100, period='yearly', level='6%')
worst_week = WorstPeriodDeviation(zone='Building', period='weekly', level='6%')
"""
import numpy as np
from besos.objectives import VariableReader


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


def _long_term_outputs(units):
    """The prefixes of the outputs of the long-term discomfort of the ACCIS with some units ('H' for Method A, 'Kh'
    for Method B), ``<output>_`` (:data:`accim.sim.ems.long_term_discomfort.OUTPUTS`)."""
    from accim.sim.ems.long_term_discomfort import OUTPUTS

    return tuple(f'{output}_' for output, (_, output_units) in OUTPUTS.items() if output_units == units)


def _named_sum(result, prefixes, method, outputs):
    """The checked sum of an output, after checking that its name, if the result has it (``'EMS,<output>_<zone>'``
    in the results of besos), begins with one of some prefixes; ``outputs`` says which outputs they are."""
    name = getattr(result, 'name', None)
    if isinstance(name, str) and name.strip():
        variable = name.split(',', 1)[-1].strip().upper()
        if not variable.startswith(tuple(prefix.upper() for prefix in prefixes)):
            expected = ' or '.join(f'"{prefix}<zone>"' for prefix in prefixes)
            raise ValueError(f'{method} reads the outputs {expected} {outputs}, not "{name}".')
    return checked_sum_results(result)


def _long_term_sum(result, units, method):
    """The checked sum of an output of the long-term discomfort of the ACCIS, after checking its name if the result
    has it (``'EMS,<output>_<zone>'`` in the results of besos)."""
    return _named_sum(result, _long_term_outputs(units), method,
                      '(or "..._Building") of the ACCIS (report_long_term_discomfort=True)')


def hours_outside_range(result):
    """Compute the occupied hours outside the comfort range of a zone (or of the building) of the ACCIS.

    Method A of CEN/TR 16798-2:2019, Annex D: the number of occupied hours with the operative temperature outside
    the range, above its upper limit (the warm period) or below its lower limit (the cold period). The ACCIS counts
    them in each timestep with ``report_long_term_discomfort=True`` (:mod:`accim.sim.ems.long_term_discomfort`), with
    the setpoints without the tolerance as the limits: the EMS outputs ``Hours Above Upper Limit_<zone>`` and
    ``Hours Below Lower Limit_<zone>`` (and ``..._Building``, the sums of the zones), summed, in hours.

    Parameters
    ----------
    result : Any
        BESOS result of one of these outputs, at any frequency (each value is the sum of its period).

    Returns
    -------
    float
        The occupied hours outside the range in the simulated period. Divided by the occupied hours (the sum of
        ``Occupied Hours_<zone>``, which do not change from one evaluation to another), they are the percentage of
        Method A.

    Raises
    ------
    ValueError
        If the values are missing or not valid (see :func:`checked_sum_results`), or the result is not one of these
        outputs.

    Usage
    -----
    Use it as the reducer of a VariableReader (or as the ``func`` of a row of the output readers of the parametric
    module) of these outputs, whose key is ``EMS``, as an objective or as a constraint, whose bound
    ``deviation_constraint_bound`` gives with the acceptable deviations of CEN/TR 16798-2:2019, Annex E.

    Examples
    --------
    hot_hours = hours_outside_range(result)
    """
    return _long_term_sum(result, 'H', 'hours_outside_range')


def degree_hours(result):
    """Compute the degree hours of the occupied hours outside the comfort range of a zone (or of the building) of the
    ACCIS.

    Method B of CEN/TR 16798-2:2019, Annex D: the weighting factor is 0 within the range,
    Θo,limit,lower ≤ Θo ≤ Θo,limit,upper, and wf = abs(Θo − Θo,limit) outside it; the indicator is the sum of wf
    times the time, separately for the warm period (Θo > Θo,limit,upper) and the cold period
    (Θo < Θo,limit,lower). The ACCIS counts it in each timestep with ``report_long_term_discomfort=True``
    (:mod:`accim.sim.ems.long_term_discomfort`), with the setpoints without the tolerance as the limits: the EMS
    outputs ``Degree Hours Above Upper Limit_<zone>`` and ``Degree Hours Below Lower Limit_<zone>`` (and
    ``..._Building``, the sums of the zones), summed, in degree hours (Kh).

    Parameters
    ----------
    result : Any
        BESOS result of one of these outputs, at any frequency (each value is the sum of its period).

    Returns
    -------
    float
        The degree hours of the simulated period (K·h).

    Raises
    ------
    ValueError
        If the values are missing or not valid (see :func:`checked_sum_results`), or the result is not one of these
        outputs.

    Usage
    -----
    Use it as the reducer of a VariableReader (or as the ``func`` of a row of the output readers of the parametric
    module) of these outputs, whose key is ``EMS``, to minimise how far the operative temperature goes outside the
    range, not only how long.

    Examples
    --------
    warm_degree_hours = degree_hours(result)
    """
    return _long_term_sum(result, 'Kh', 'degree_hours')


def ppd_weighted_hours(result):
    """Compute the PPD-weighted hours of the occupied hours of a zone with the setpoints based on the PMV.

    Method C of CEN/TR 16798-2:2019, Annex D: the weighting factor is wf = PPD(PMV)/PPD(PMVlimit) in the warm period
    (PMV ≥ PMVlimit,upper) and in the cold period (PMV < PMVlimit,lower), with the PPD of ISO 7730:2025, formula (5),
    and 0 within the range; the indicator is the sum of wf times the time. The setpoints based on the PMV
    (:mod:`accim.sim.pmv_index`, those of :func:`accim.sim.apmv.apply_apmv_setpoints`,
    :func:`accim.sim.apmv.apply_epmv_setpoints` and :func:`accim.sim.apmv.apply_pmv_setpoints`) count it in each
    timestep with ``report_ppd_weighted_hours=True``, with their setpoints without the tolerances as the range, on the
    scale of the PMV: the EMS output ``PPD Weighted Hours_<zone>``, summed, in hours (both periods). The models of the
    ACCIS with temperature setpoints have no PMV, so they do not count it.

    Parameters
    ----------
    result : Any
        BESOS result of this output, at any frequency (each value is the sum of its period).

    Returns
    -------
    float
        The PPD-weighted hours of the simulated period.

    Raises
    ------
    ValueError
        If the values are missing or not valid (see :func:`checked_sum_results`), or the result is not this output.

    Usage
    -----
    Use it as the reducer of a VariableReader (or as the ``func`` of a row of the output readers of the parametric
    module) of this output, whose key is ``EMS``, as an objective or as a constraint of the plans with the setpoints
    based on the PMV ('apmv setpoints' and 'epmv setpoints', with ``report_long_term_discomfort=True``).

    Examples
    --------
    weighted_hours = ppd_weighted_hours(result)
    """
    from accim.sim.pmv_index import PPD_WEIGHTED_HOURS_OUTPUTS

    return _named_sum(result, tuple(f'{output}_' for output in PPD_WEIGHTED_HOURS_OUTPUTS), 'ppd_weighted_hours',
                      'of the setpoints based on the PMV (report_ppd_weighted_hours=True)')


def deviation_constraint_bound(occupied_hours, period='yearly', level='6%'):
    """Compute the bound of a constraint on the occupied hours outside the comfort range with the acceptable
    deviations of CEN/TR 16798-2:2019, Annex E, Table E.1.

    Table E.1 accepts the occupied hours outside the range up to 20 % (or 50 %) of the occupied hours of a week,
    12 % (25 %) of a month, or 3 % (6 %) of a year (the levels '3%' and '6%', named after their yearly percentages,
    :data:`accim.data.postprocessing.long_term_discomfort.DEVIATION_LIMITS`): with 2100 occupied hours a year, 63 h
    on the 3 % level and 126 h on the 6 % level.

    Parameters
    ----------
    occupied_hours : float
        The occupied hours of the period: those of the simulated period (the sum of ``Occupied Hours_<zone>``, or of
        those of all the zones for the building), which do not change from one evaluation to another with the same
        model and weather file.
    period : str
        'yearly', 'monthly' or 'weekly', the period of Table E.1 that ``occupied_hours`` are.
    level : str
        '3%' or '6%'.

    Returns
    -------
    str
        The bound, in the format of the constraint bounds of besos and platypus: ``'<=126.0'`` for 2100 h, 'yearly'
        and '6%' (:func:`accim.data.postprocessing.long_term_discomfort.deviation_limit`).

    Raises
    ------
    ValueError
        If the period or the level is not one of Table E.1.

    Usage
    -----
    Give it as the bound of a constraint whose reducer is ``hours_outside_range`` (``constraint_bounds`` of
    ``set_problem``): an evaluation whose hours outside the range in the simulated period are more than the
    deviation of Table E.1 does not meet the constraint. The weekly and monthly deviations need the occupied hours of
    each week or month: :class:`WorstPeriodDeviation` reads them in each evaluation, for a constraint of the worst
    week or month (and of the year, without the occupied hours of a first simulation).

    Examples
    --------
    bound = deviation_constraint_bound(occupied_hours=2100, period='yearly', level='6%')
    """
    from accim.data.postprocessing.long_term_discomfort import deviation_limit

    return f'<={deviation_limit(occupied_hours, period, level)!r}'


class WorstPeriodDeviation(VariableReader):
    """A reader of besos for a constraint with the acceptable deviations of CEN/TR 16798-2:2019, Annex E, Table E.1,
    in the worst period of each evaluation: the largest excess, over the periods of its run period, of the occupied
    hours outside the range of the long-term discomfort of a zone (or of the building) over the deviation of the
    occupied hours of the period, in hours (proposal C2;
    :func:`~accim.data.postprocessing.long_term_discomfort.period_deviations`). It is 0 or negative if every period is
    within the deviation, so its bound is ``'<=0'``, and the violation of an evaluation that does not meet it is the
    hours beyond the deviation in its worst period.

    The periods are the calendar weeks, from Monday to Sunday ('weekly': 20 % or 50 % of the occupied hours of the
    week, on the levels '3%' and '6%'), the calendar months ('monthly': 12 % or 25 %) or the run period ('yearly': 3 %
    or 6 %, with a run period of a year). Each one is measured against its own occupied hours, so the weeks or months
    that the run period does not cover whole, at its beginning or its end, have the deviation of their occupied hours
    in it.

    In each evaluation, it reads, at the frequency of its periods (daily for the weeks, monthly for the months and run
    period for the year), the output ``<output>_<zone>`` of the long-term discomfort of the ACCIS
    (``report_long_term_discomfort=True``) and the occupied hours of the zone, ``Occupied Hours_<zone>`` (for the
    building, those of the zones of the long-term discomfort, added up), and, for the weeks, the day type of
    EnergyPlus of each day, *Site Day Type Index*
    (:func:`~accim.data.postprocessing.long_term_discomfort.calendar_weeks`); besos adds the outputs to the model
    (:meth:`setup`). The occupied hours are those of each evaluation, so they need no first simulation. The rows of
    the run period are those after the rows of the sizing periods, which EnergyPlus simulates first when ``Run
    Simulation for Sizing Periods`` of the ``SimulationControl`` of the model is Yes (a day, and so a row of each
    frequency, for each ``SizingPeriod:DesignDay``): its days and months are those of the ``RunPeriod`` of the model,
    which must have one (with a year that is not a leap year if it has no year, as EnergyPlus), but for the days 29
    February that EnergyPlus skips when the weather file has not them (the weeks are those of the days simulated). The
    reader raises a ``ValueError`` if the outputs have other rows.

    The evaluators of the optimisations of accim (``set_evaluator``) set it up with their models, also as an
    ``add_output`` (which besos does not set up), each one with its own copy of the reader, so that the models of an
    optimisation of several models do not share its state. The simulations of ``run_parametric_simulation`` cannot
    read it (a ``ValueError``): ``period_deviations`` gives the deviations of each period after them.

    :param zone: The zone, as in the names of the EMS outputs of the ACCIS (``'Block1_Zone1'``), or ``'Building'``
        (the default), the sums of its zones.
    :param output: ``'Hours Above Upper Limit'`` (the default; the warm period) or ``'Hours Below Lower Limit'`` (the
        cold period).
    :param period: ``'weekly'`` (the default), ``'monthly'`` or ``'yearly'``.
    :param level: ``'6%'`` (the default) or ``'3%'``, the levels of Table E.1.
    :param name: The name of the constraint in the results; by default, ``'Worst weekly deviation of Hours Above
        Upper Limit_Building (6%)'``.
    :raises ValueError: If the output, the period or the level is not valid.

    Usage
    -----
    Give it as a constraint of ``set_problem``, with the bound ``'<=0'``; :meth:`setup` raises a ``ValueError`` if the
    model has not the outputs of the long-term discomfort of the zone or does not simulate one run period.

    Examples
    --------
    worst_week = WorstPeriodDeviation(zone='Building', period='weekly', level='6%')
    optim.set_problem(minimize_outputs=[True], constraints=[worst_week], constraint_bounds=['<=0'])
    """

    #: The frequency of the outputs that it reads for each period of Table E.1
    FREQUENCIES = {'weekly': 'Daily', 'monthly': 'Monthly', 'yearly': 'RunPeriod'}
    #: The output of EnergyPlus with the day type of each day, for the calendar weeks
    DAY_TYPE_OUTPUT = ('Environment', 'Site Day Type Index')

    def __init__(self, zone='Building', output='Hours Above Upper Limit', period='weekly', level='6%', name=''):
        from accim.data.postprocessing.long_term_discomfort import deviation_limit

        outputs = [prefix[:-1] for prefix in _long_term_outputs('H')]
        if output not in outputs:
            raise ValueError(f'output must be one of {outputs} (the outputs of the hours outside the range of the '
                             f'long-term discomfort of the ACCIS), not {output!r}.')
        if period not in self.FREQUENCIES:
            raise ValueError(f'period must be one of {list(self.FREQUENCIES)}, not {period!r}.')
        deviation_limit(0.0, period, level)
        zone = str(zone).strip()
        if not zone:
            raise ValueError("zone must be the name of a zone in the EMS outputs of the ACCIS, or 'Building'.")
        super().__init__(key_value='EMS', variable_name=f'{output}_{zone}', frequency=self.FREQUENCIES[period],
                         func=checked_sum_results,
                         name=name or f'Worst {period} deviation of {output}_{zone} ({level})')
        self.zone = zone
        self.output = output
        self.period = period
        self.level = level
        # Set by setup: the outputs of the occupied hours that it adds up, the rows of the sizing periods and of the run
        # period, and the days 29 February of the run period that EnergyPlus may skip
        self.occupied_outputs = None
        self.sizing_rows = None
        self.run_period_rows = None
        self.skipped_rows = (0,)

    def setup(self, building) -> None:
        """Read the outputs of the occupied hours of the zone and the rows of the run period of a model (that of the
        evaluator of besos, which calls it), and add to it the outputs that it reads at the frequency of its period.

        :param building: The model, of eppy.
        :raises ValueError: If the model is not of eppy, has not the outputs of the long-term discomfort of the zone
            and its occupied hours, or does not simulate one run period.
        """
        from besos import eppy_funcs as ef

        from accim.sim.results_size import _environments, _leap_days, _objects

        if ef.get_mode(building) != 'idf':
            raise ValueError(f'{type(self).__name__} reads the model of eppy (an IDF), not an epJSON one.')
        names = {str(o.Name).upper(): str(o.Name) for o in building.idfobjects['EnergyManagementSystem:OutputVariable']}
        prefix = f'{self.output}_'
        zones = [name[len(prefix):] for name in names.values()
                 if name.upper().startswith(prefix.upper()) and name.upper() != f'{prefix}Building'.upper()]
        own = names.get(self.variable_name.upper())
        if own is None:
            raise ValueError(f'The model has no output {self.variable_name} of the long-term discomfort of the ACCIS '
                             f'(report_long_term_discomfort=True); its zones are {sorted(zones)}.')
        if self.zone.upper() != 'BUILDING':
            zones = [own[len(prefix):]]
        if not zones:
            raise ValueError(f'The model has no zones with the output {prefix}<zone> of the long-term discomfort of '
                             f'the ACCIS.')
        occupied = []
        for zone in zones:
            name = names.get(f'Occupied Hours_{zone}'.upper())
            if name is None:
                raise ValueError(f'The model has no output Occupied Hours_{zone} of the ACCIS.')
            occupied.append(name)
        sizing, runs = _environments(building)
        if len(runs) != 1:
            raise ValueError(f'{type(self).__name__} needs a model that simulates one run period (a RunPeriod, with '
                             f'Run Simulation for Weather File Run Periods in its SimulationControl), not {len(runs)}.')
        self.variable_name = own
        super().setup(building)
        for name in occupied:
            VariableReader(key_value='EMS', variable_name=name, frequency=self.frequency).setup(building)
        if self.period == 'weekly':
            key, variable = self.DAY_TYPE_OUTPUT
            VariableReader(key_value=key, variable_name=variable, frequency='Daily').setup(building)
        self.occupied_outputs = occupied
        # The rows of the sizing periods (before those of the run period) and those of the run period: its days
        # without the days 29 February that EnergyPlus skips (the weather files without them), or with them
        self.sizing_rows = {'weekly': sum(period.days for period in sizing),
                            'monthly': sum(period.months for period in sizing), 'yearly': len(sizing)}[self.period]
        self.run_period_rows = {'weekly': runs[0].days, 'monthly': runs[0].months, 'yearly': 1}[self.period]
        leap_days = _leap_days(_objects(building, 'RunPeriod')[0]) if self.period == 'weekly' else 0
        self.skipped_rows = (0, leap_days) if leap_days else (0,)

    def _run_period_values(self, results, key, variable, frequency) -> np.ndarray:
        """The values of an output in the rows of the run period of the results of an evaluation: those after the rows
        of the sizing periods, which EnergyPlus simulates first; as many as the days (or the months) of the run period,
        or its days without the days 29 February that EnergyPlus skipped."""
        wanted = (f'{key},{variable}'.upper(), frequency.upper())
        for (name, result_frequency), result in results.items():
            if (str(name).upper(), str(result_frequency).upper()) == wanted:
                break
        else:
            raise ValueError(f'The results have no output {key},{variable} at {frequency} frequency; check the '
                             f'EnergyPlus error file of the evaluation.')
        try:
            values = np.asarray(result.data['Value'], dtype=float).reshape(-1)
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'The values of {key},{variable} must be numbers.') from exc
        expected = [self.run_period_rows - skipped for skipped in self.skipped_rows]
        if len(values) - self.sizing_rows not in expected or not np.isfinite(values).all():
            raise ValueError(f'The results have {len(values)} values of {key},{variable} at {frequency} frequency, '
                             f'not {self.sizing_rows} of the sizing periods and '
                             f'{" or ".join(str(rows) for rows in expected)} of the run period of the model, as '
                             f'finite numbers.')
        return values[self.sizing_rows:]

    def __call__(self, results) -> float:
        """The largest excess of the hours outside the range over the deviation of Table E.1 in the periods of the run
        period of an evaluation.

        :param results: The results of the evaluation, as besos reads them (``{(name, frequency): EPResults}``).
        :return: The hours (0 or negative if every period is within the deviation).
        :raises ValueError: If :meth:`setup` has not read the model, or the results have not the outputs.
        """
        from accim.data.postprocessing.long_term_discomfort import calendar_weeks, period_deviations

        if self.run_period_rows is None:
            raise ValueError(f'{type(self).__name__} reads the zones and the run period of the model in '
                             f'setup(building): give it as a constraint (or an add_output) of the problem of an '
                             f'optimisation of accim, whose evaluators set it up with their models, or call its setup '
                             f'with the model of the results first.')
        outside = self._run_period_values(results, self.key_value, self.variable_name, self.frequency)
        occupied = np.sum([self._run_period_values(results, self.key_value, name, self.frequency)
                           for name in self.occupied_outputs], axis=0)
        periods = None
        if self.period == 'weekly':
            periods = calendar_weeks(self._run_period_values(results, *self.DAY_TYPE_OUTPUT, 'Daily'))
        deviations = period_deviations(outside, occupied, periods, self.period, self.level)
        return float(deviations['excess_h'].max())


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
