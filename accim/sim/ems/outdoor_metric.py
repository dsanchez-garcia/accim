# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The outdoor temperature of reference of the custom comfort model, comfort standard 99 (proposal B1).

The custom model calculates its comfort temperature (``Tout_metric*m+n``), its setpoints and its applicability with
``Tout_metric``, the metric that its argument ``custom_outdoor_metric`` chooses (:data:`OUTDOOR_METRICS`, the input
``CustAST_metric`` of each zone). By default, ``'pmot'``, it is the running mean outdoor temperature of ASHRAE 55 that
EnergyPlus calculates (the sensor PMOT), as before accim 1.2.0; ``'rmot'`` is that of CEN 15251 (the sensor RMOT). The
EMS calculates the others from the outdoor dry-bulb temperature (the sensor OutT, *Site Outdoor Air Drybulb
Temperature*), without EnergyManagementSystem:TrendVariable, which the Python API backend does not support:

- The program ``SetOutdoorMetric`` (at the beginning of each timestep, before the programs of the zones) adds the
  hourly values of each day: those of the timesteps that end an hour (``Minute`` is 60 at the end of the timestep,
  EMS Application Guide; the built-in variable ``TimeStepsPerHour`` is 0 at this calling point in EnergyPlus 25.1),
  which are the values of the weather file. At the first timestep of each day, it keeps the daily mean of the previous
  day (``Tday_1``, ``Tday_2``... ``Tday_<n>``, those of the n previous days) and the mean of its maximum and minimum
  (``Tmid_1``, ``Tmid_2``, ``Tmid_3``). It does not add the warm-up days.
- The program ``SetOutdoorMetric_<zone>`` (run by ``RunACCIS_<zone>`` after the inputs of the zone) updates the running
  mean of EN 16798-1 of the zone (``RMOTa_<zone>``, with its ``CustAST_alpha``) at the first timestep of each day, and
  sets ``Tout_metric`` (and ``Tout_metric_<zone>``, its EMS output variable).
- The program ``InitOutdoorMetric`` (at the beginning of each environment) restarts them. At the first timestep of the
  environment, if its day is the first day of the run period of the model when the ACCIS was added with a weather
  file (argument ``epw``), the daily values of the previous days and the running means of the zones are those of the
  weather file (:func:`initial_values`, the series of :func:`accim.sim.preview.outdoor_metrics`); otherwise, the native
  running mean of ASHRAE 55 (PMOT), as soon as EnergyPlus has calculated it (decision D3 of the brief of 1.2.0). The
  monthly means are those of the weather file, so ``'monthly_mean'`` needs it.

A model has these EMS objects only if a zone has a metric other than ``'pmot'``
(:func:`set_outdoor_metric_code`, which :func:`accim.sim.ems.programs.set_comfort_standard_code` calls); then the
programs of the custom model use ``Tout_metric`` instead of PMOT. Otherwise, the custom model uses PMOT and the model
is as with accim 1.1.0 (the output IDFs of the comfort standards and of ``'pmot'`` do not change).

The equations (section 11.4 of ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md``): EN 16798-1:2019, Annex B, formula
(B.1), Θrm = (1 − α)·{Θed−1 + α·Θed−2 + α²·Θed−3 + ...}, in its recursive form Θrm = (1 − α)·Θed−1 + α·Θrm−1, with α
recommended 0.8, and its approximate formula (B.2), (Θed−1 + 0.8·Θed−2 + 0.6·Θed−3 + 0.5·Θed−4 + 0.4·Θed−5 +
0.3·Θed−6 + 0.2·Θed−7)/3.8; ASHRAE 55-2020, 5.4.2.1, the arithmetic mean of the daily means of 7 to 30 previous days;
and van der Linden et al. (2006), Te,ref = (T0 + 0.8·T−1 + 0.4·T−2 + 0.2·T−3)/2.4, with Ti the mean of the maximum and
minimum of the day i (T0, of the day so far; before its first hourly value, the outdoor temperature of the timestep).
"""

import copy
import numbers
import os
import re
import warnings
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union

__all__ = [
    'ALPHA_RANGE',
    'DAYS_RANGE',
    'DEFAULT_ALPHA',
    'DEFAULT_DAYS',
    'INIT_PROGRAM',
    'OUTDOOR_METRICS',
    'OUTPUT_PREFIX',
    'PROGRAM',
    'ZONE_PROGRAM_PREFIX',
    'begins_with_weather_file',
    'building_program_lines',
    'check_outdoor_metric_arguments',
    'has_outdoor_metric_code',
    'init_program_lines',
    'initial_values',
    'metric_code',
    'metric_name',
    'ring_days',
    'set_outdoor_metric_code',
    'uses_outdoor_metric',
    'zone_program_lines',
]

#: The metrics of the custom comfort model and their codes (the values of ``CustAST_metric``): 'pmot', the running
#: mean of ASHRAE 55 of EnergyPlus (the default, as before accim 1.2.0); 'rmot', that of CEN 15251 of EnergyPlus;
#: 'rmot_alpha', EN 16798-1 (B.1) with ``custom_alpha``; 'rmot_7day', EN 16798-1 (B.2); 'daily_mean', the daily mean of
#: the previous day; 'ndrm', the arithmetic mean of the ``custom_days`` previous days (ASHRAE 55-2020, 5.4.2.1);
#: 'monthly_mean', the monthly mean of the weather file; 'te_ref_nl', the reference temperature of the Dutch ATG
#: (van der Linden et al., 2006)
OUTDOOR_METRICS = {'pmot': 0, 'rmot': 1, 'rmot_alpha': 2, 'rmot_7day': 3, 'daily_mean': 4, 'ndrm': 5,
                   'monthly_mean': 6, 'te_ref_nl': 7}
#: The alpha of 'rmot_alpha' by default, the value that EN 16798-1 recommends
DEFAULT_ALPHA = 0.8
#: The days of 'ndrm' by default, those of the running mean of ASHRAE 55 of EnergyPlus
DEFAULT_DAYS = 30
#: The ranges outside which alpha and the days warn (decision D7): the ratio between the weights of consecutive days of
#: ASHRAE 55-2020, 5.4.2.1, and its 7 to 30 days
ALPHA_RANGE = (0.6, 0.9)
DAYS_RANGE = (7, 30)
#: The names of the programs and of the EMS output variables of each zone (``<prefix><zone>``)
PROGRAM = 'SetOutdoorMetric'
ZONE_PROGRAM_PREFIX = 'SetOutdoorMetric_'
INIT_PROGRAM = 'InitOutdoorMetric'
OUTPUT_PREFIX = 'Tout_metric_'
#: The inputs of each zone (SetInputData_<zone>)
INPUTS = ('CustAST_metric', 'CustAST_alpha', 'CustAST_days')
#: The daily means that SetOutdoorMetric keeps, at least (those of 'ndrm' with the most days of ASHRAE 55)
_MIN_RING_DAYS = 30
#: The weights of the daily means of the 7 previous days of EN 16798-1 (B.2), whose sum is 3.8
_B2_WEIGHTS = (1, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2)
_B2_DIVISOR = 3.8
#: The weights of the means of the maximum and minimum of the day and the 3 previous days of the ATG, whose sum is 2.4
_ATG_WEIGHTS = (1, 0.8, 0.4, 0.2)
_ATG_DIVISOR = 2.4
#: The first of the global variables of the programs, which identifies their EnergyManagementSystem:GlobalVariable
_FIRST_GLOBAL_VARIABLE = 'Tout_metric'
#: The EMS output variable of the metric of the zone that runs last (as the comfort temperature of the whole model)
_OUTPUT = 'Tout_metric'
#: The metrics whose programs begin with the values of the weather file, or with PMOT without it: rmot_alpha,
#: rmot_7day, daily_mean, ndrm and te_ref_nl ('pmot' and 'rmot' are those of EnergyPlus; 'monthly_mean' needs the
#: weather file)
_NEEDS_INITIAL_VALUES = frozenset({2, 3, 4, 5, 7})
_DAILY_MEAN_LINE = re.compile(r'^set Tday_(\d+) = ')
_MONTHLY_MEAN = 'OutdoorMonthlyMean'
_COUNT_HOURS_PREFIX = 'CountHours_'
#: The values of initial_values already calculated (AddAccis writes the programs for each output IDF), by weather file
_INITIAL_VALUES: Dict[tuple, Dict[str, Any]] = {}


def metric_code(value: Any) -> int:
    """The code of a metric of :data:`OUTDOOR_METRICS`, from its name or its code (as the input ``CustAST_metric``).

    :raises ValueError: If it is not a metric.
    """
    if isinstance(value, str):
        if value.lower() in OUTDOOR_METRICS:
            return OUTDOOR_METRICS[value.lower()]
    elif isinstance(value, numbers.Real) and not isinstance(value, bool) and value in OUTDOOR_METRICS.values():
        return int(value)
    raise ValueError(f'custom_outdoor_metric must be one of {list(OUTDOOR_METRICS)} (or its code, 0 to 7), not '
                     f'{value!r}.')


def metric_name(code: Any) -> str:
    """The name of the metric of a code (or name) of :data:`OUTDOOR_METRICS`."""
    code = metric_code(code)
    return next(name for name, number in OUTDOOR_METRICS.items() if number == code)


def check_outdoor_metric_arguments(metric: Any, alpha: Any, days: Any, where: str = '') -> int:
    """Check the arguments of the outdoor metric of the custom model, and warn if alpha or the days are outside the
    ranges of ASHRAE 55-2020, 5.4.2.1 (decision D7).

    :param metric: ``custom_outdoor_metric``, a name or code of :data:`OUTDOOR_METRICS`.
    :param alpha: ``custom_alpha``, between 0 and 1 (not included).
    :param days: ``custom_days``, an integer of at least 1.
    :param where: The zone, for the messages.
    :return: The code of the metric.
    :raises ValueError: If a value is not valid.
    """
    code = metric_code(metric)
    suffix = f' (zone {where!r})' if where else ''
    if isinstance(alpha, bool) or not isinstance(alpha, numbers.Real) or not 0 < alpha < 1:
        raise ValueError(f'custom_alpha must be a number between 0 and 1 (not included){suffix}, not {alpha!r}.')
    if isinstance(days, bool) or not isinstance(days, numbers.Real) or days != int(days) or days < 1:
        raise ValueError(f'custom_days must be an integer of at least 1{suffix}, not {days!r}.')
    if code == OUTDOOR_METRICS['rmot_alpha'] and not ALPHA_RANGE[0] <= alpha <= ALPHA_RANGE[1]:
        warnings.warn(f'custom_alpha {alpha}{suffix} is outside {ALPHA_RANGE[0]} to {ALPHA_RANGE[1]}, the ratio '
                      f'between the weights of consecutive days of ASHRAE 55-2020 (5.4.2.1); EN 16798-1 recommends '
                      f'0.8.')
    if code == OUTDOOR_METRICS['ndrm'] and not DAYS_RANGE[0] <= days <= DAYS_RANGE[1]:
        warnings.warn(f'custom_days {days}{suffix} is outside the {DAYS_RANGE[0]} to {DAYS_RANGE[1]} days of ASHRAE '
                      f'55-2020 (5.4.2.1).')
    return code


def ring_days(days: Iterable[Any] = ()) -> int:
    """The daily means that SetOutdoorMetric keeps: 30, or more if a zone has more ``custom_days``."""
    return max([_MIN_RING_DAYS] + [int(d) for d in days if isinstance(d, numbers.Real) and not isinstance(d, bool)])


def _number(value: float) -> str:
    return repr(float(value))


def building_program_lines(ring: int, initial: Optional[Mapping[str, Any]] = None) -> List[str]:
    """The lines of the program SetOutdoorMetric.

    :param ring: The number of daily means kept (:func:`ring_days`).
    :param initial: The values of the weather file (:func:`initial_values`); None without a weather file.
    """
    lines = ['set OutdoorDayClosed = 0',
             # The first timestep of the environment: the values of the days before the run period
             'if OutdoorInit == -1']
    if initial is not None:
        lines.append(f"if DayOfYear == {int(initial['start_day'])}")
        lines += [f'set Tday_{k} = {_number(v)}' for k, v in enumerate(initial['daily_means'][:ring], start=1)]
        lines += [f'set Tmid_{k} = {_number(v)}' for k, v in enumerate(initial['mid_ranges'], start=1)]
        lines += ['set OutdoorInit = 1', 'else', 'set OutdoorInit = 0', 'endif']
    else:
        lines.append('set OutdoorInit = 0')
    lines.append('endif')
    # Otherwise, the running mean of ASHRAE 55 of EnergyPlus, once it has calculated it
    lines.append('if (OutdoorInit == 0) && (PMOT <> 0)')
    lines += [f'set Tday_{k} = PMOT' for k in range(1, ring + 1)]
    lines += [f'set Tmid_{k} = PMOT' for k in range(1, len(_ATG_WEIGHTS))]
    lines += ['set OutdoorInit = 2', 'endif',
              # The days of the simulation, not those of the warm-up
              'if WarmupFlag == 0',
              # The first timestep of a day: the daily values of the previous day, if it was simulated
              'if (Hour == 0) && (TimeStepNum == 1)',
              'if OutdoorHours == 24']
    lines += [f'set Tday_{k} = Tday_{k - 1}' for k in range(ring, 1, -1)]
    lines += ['set Tday_1 = OutdoorSum/24']
    lines += [f'set Tmid_{k} = Tmid_{k - 1}' for k in range(len(_ATG_WEIGHTS) - 1, 1, -1)]
    lines += ['set Tmid_1 = (OutdoorMax+OutdoorMin)/2', 'set OutdoorDayClosed = 1', 'endif',
              'set OutdoorSum = 0', 'set OutdoorHours = 0', 'endif',
              # The end of an hour: the hourly value of the weather file
              'if Minute > 59.5',
              'if OutdoorHours == 0', 'set OutdoorMax = OutT', 'set OutdoorMin = OutT', 'else',
              'set OutdoorMax = @Max OutdoorMax OutT', 'set OutdoorMin = @Min OutdoorMin OutT', 'endif',
              'set OutdoorSum = OutdoorSum+OutT', 'set OutdoorHours = OutdoorHours+1', 'endif',
              'endif']
    if initial is not None:
        # The monthly means of the weather file
        for month, value in enumerate(initial['monthly_means'], start=1):
            lines += [f"{'if' if month == 1 else 'elseif'} Month == {month}",
                      f'set OutdoorMonthlyMean = {_number(value)}']
        lines.append('endif')
    return lines


def zone_program_lines(zone: str, ring: int, initial_running_mean: Optional[float] = None,
                       monthly_means: bool = False) -> List[str]:
    """The lines of the program SetOutdoorMetric_<zone>.

    :param zone: The name of the zone in the EMS objects.
    :param ring: The number of daily means kept (:func:`ring_days`).
    :param initial_running_mean: The running mean of EN 16798-1 (B.1) of the weather file on the first day of the run
        period, with the alpha of the zone (:func:`initial_values`); None without a weather file.
    :param monthly_means: True if SetOutdoorMetric has the monthly means of a weather file.
    """
    running_mean, initialised = f'RMOTa_{zone}', f'OutdoorMetricInit_{zone}'
    lines = [f'if {initialised} == -1']
    if initial_running_mean is not None:
        lines += ['if OutdoorInit == 1', f'set {running_mean} = {_number(initial_running_mean)}',
                  f'set {initialised} = 1', 'elseif OutdoorInit == 2']
    else:
        lines.append('if OutdoorInit == 2')
    lines += [f'set {running_mean} = PMOT', f'set {initialised} = 1', 'endif', 'endif',
              # EN 16798-1 (B.1), recursive, with the daily mean of the previous day
              'if OutdoorDayClosed == 1',
              f'set {running_mean} = (1-CustAST_alpha)*Tday_1+CustAST_alpha*{running_mean}', 'endif',
              'if CustAST_metric == 1', 'set Tout_metric = RMOT',
              'elseif CustAST_metric == 2', f'set Tout_metric = {running_mean}',
              # EN 16798-1 (B.2)
              'elseif CustAST_metric == 3',
              'set Tout_metric = (' + '+'.join(f'{_weight(w)}Tday_{k}' for k, w in enumerate(_B2_WEIGHTS, 1))
              + f')/{_B2_DIVISOR}',
              'elseif CustAST_metric == 4', 'set Tout_metric = Tday_1',
              # ASHRAE 55-2020 (5.4.2.1): the arithmetic mean of the custom_days previous days
              'elseif CustAST_metric == 5', 'set OutdoorDaysSum = Tday_1']
    for k in range(2, ring + 1):
        lines += [f'if CustAST_days >= {k}', f'set OutdoorDaysSum = OutdoorDaysSum+Tday_{k}', 'endif']
    lines += ['set Tout_metric = OutdoorDaysSum/CustAST_days', 'elseif CustAST_metric == 6']
    # Without the monthly means of a weather file, EnergyPlus stops
    lines.append('set Tout_metric = OutdoorMonthlyMean' if monthly_means else 'set Tout_metric = @FatalHaltEp 6')
    # The ATG (van der Linden et al., 2006): T0 is the mean of the maximum and minimum of the day so far
    lines += ['elseif CustAST_metric == 7', 'if OutdoorHours > 0', 'set OutdoorMidRange = (OutdoorMax+OutdoorMin)/2',
              'else', 'set OutdoorMidRange = OutT', 'endif',
              'set Tout_metric = (OutdoorMidRange+'
              + '+'.join(f'{_weight(w)}Tmid_{k}' for k, w in enumerate(_ATG_WEIGHTS[1:], 1)) + f')/{_ATG_DIVISOR}',
              'else', 'set Tout_metric = PMOT', 'endif',
              f'set {OUTPUT_PREFIX}{zone} = Tout_metric']
    return lines


def _weight(weight: float) -> str:
    return '' if weight == 1 else f'{weight}*'


def init_program_lines(zones: Sequence[str], ring: int = _MIN_RING_DAYS) -> List[str]:
    """The lines of the program InitOutdoorMetric, at the beginning of each environment: the daily values and the
    running means are 0 (the value of PMOT before EnergyPlus calculates it) until SetOutdoorMetric begins them.

    :param zones: The names of the zones in the EMS objects.
    :param ring: The number of daily means kept (:func:`ring_days`).
    """
    return (['set OutdoorInit = -1', 'set OutdoorDayClosed = 0', 'set OutdoorSum = 0', 'set OutdoorHours = 0']
            + [f'set Tday_{k} = 0' for k in range(1, ring + 1)]
            + [f'set Tmid_{k} = 0' for k in range(1, len(_ATG_WEIGHTS))]
            + [line for zone in zones for line in (f'set OutdoorMetricInit_{zone} = -1', f'set RMOTa_{zone} = 0')])


def global_variables(ring: int, zones: Sequence[str]) -> List[str]:
    """The EMS global variables of the programs (the inputs of the zones included)."""
    names = [_FIRST_GLOBAL_VARIABLE, *INPUTS, 'OutdoorInit', 'OutdoorDayClosed', 'OutdoorSum', 'OutdoorHours',
             'OutdoorMax', 'OutdoorMin', 'OutdoorMonthlyMean']
    names += [f'Tday_{k}' for k in range(1, ring + 1)] + [f'Tmid_{k}' for k in range(1, len(_ATG_WEIGHTS))]
    for zone in zones:
        names += [f'RMOTa_{zone}', f'OutdoorMetricInit_{zone}', f'{OUTPUT_PREFIX}{zone}']
    return names


def initial_values(epw: Union[str, Any], start_day: int, ring: int,
                   alphas: Mapping[str, float]) -> Dict[str, Any]:
    """The values of the weather file with which the programs begin on the first day of the run period (decision D3):
    the series of :func:`accim.sim.preview.outdoor_metrics`, whose first days take the last ones of the file.

    :param epw: The weather file.
    :param start_day: The first day of the run period (day of the year).
    :param ring: The number of daily means kept (:func:`ring_days`).
    :param alphas: The alpha of each zone.
    :return: ``start_day``; ``daily_means``, the daily means of the ``ring`` previous days (the previous one first);
        ``mid_ranges``, the means of the maximum and minimum of the 3 previous days; ``running_means``, the running
        mean of EN 16798-1 (B.1) of the day with the alpha of each zone, by zone; ``monthly_means``, those of the 12
        months.
    """
    try:
        status = os.stat(epw)
        key = (os.path.abspath(epw), status.st_mtime_ns, status.st_size, int(start_day), int(ring),
               tuple(sorted((str(zone), float(alpha)) for zone, alpha in alphas.items())))
    except (OSError, TypeError, ValueError):
        key = None
    if key is not None and key in _INITIAL_VALUES:
        return copy.deepcopy(_INITIAL_VALUES[key])
    values = _initial_values(epw, start_day, ring, alphas)
    if key is not None:
        _INITIAL_VALUES[key] = copy.deepcopy(values)
    return values


def _initial_values(epw: Union[str, Any], start_day: int, ring: int,
                    alphas: Mapping[str, float]) -> Dict[str, Any]:
    from accim.sim.preview import outdoor_metrics

    daily = outdoor_metrics(epw, frequency='daily')
    number_of_days = len(daily)
    first = (int(start_day) - 1) % number_of_days
    mean = daily['daily_mean'].to_numpy()
    mid_range = ((daily['daily_max'] + daily['daily_min']) / 2).to_numpy()
    running_means: Dict[str, float] = {}
    by_alpha: Dict[float, float] = {}
    for zone, alpha in alphas.items():
        if alpha not in by_alpha:
            by_alpha[alpha] = float(outdoor_metrics(epw, alpha=float(alpha), frequency='daily')['RMOT'].iloc[first])
        running_means[zone] = by_alpha[alpha]
    monthly = daily.groupby(daily['date'].dt.month)['daily_mean'].mean()
    return {
        'start_day': first + 1,
        'daily_means': [float(mean[(first - k) % number_of_days]) for k in range(1, ring + 1)],
        'mid_ranges': [float(mid_range[(first - k) % number_of_days]) for k in range(1, len(_ATG_WEIGHTS))],
        'running_means': running_means,
        'monthly_means': [float(monthly.get(month, float('nan'))) for month in range(1, 13)],
    }


def has_outdoor_metric_code(idf) -> bool:
    """True if the model has the programs of the outdoor metric of the custom model."""
    return idf.getobject('EnergyManagementSystem:Program', PROGRAM) is not None


def begins_with_weather_file(idf) -> bool:
    """True if the programs of the outdoor metric of the custom model of a model begin with the values of a weather
    file (``epw`` of :func:`set_outdoor_metric_code`), and False if they begin with PMOT (or the model has none)."""
    program = idf.getobject('EnergyManagementSystem:Program', PROGRAM)
    return program is not None and any(line.startswith('if DayOfYear ==') for line in _program_lines(program))


def uses_outdoor_metric(idf) -> bool:
    """True if a zone of the model has an outdoor metric other than 'pmot' (``CustAST_metric`` is not 0 in its program
    SetInputData_<zone>), so that its custom model needs the EMS code of :func:`set_outdoor_metric_code`."""
    from accim.sim.ems.inputs import input_programs, read_inputs

    return any(read_inputs(program).get(INPUTS[0], 0) != 0 for program in input_programs(idf).values())


def _remove(idf, objects) -> None:
    for obj in list(objects):
        idf.removeidfobject(obj)


def _program_lines(program) -> List[str]:
    return [str(value).strip() for value in program.fieldvalues[2:]]


def _zone_frequencies(idf, zones: Sequence[str]) -> List[str]:
    """The frequencies of the Output:Variable objects of the comfort temperature of the zones (those with which the
    outputs of the metric of the zones are added)."""
    names = {f'COMFORT TEMPERATURE_{zone}'.upper() for zone in zones} | {'COMFORT TEMPERATURE'}
    frequencies = []
    for output in idf.idfobjects['Output:Variable']:
        if str(output.Variable_Name).upper() in names and output.Reporting_Frequency not in frequencies:
            frequencies.append(output.Reporting_Frequency)
    return frequencies


def _ring_of(program) -> int:
    """The number of daily means that a program SetOutdoorMetric keeps."""
    return max((int(match.group(1)) for line in _program_lines(program) if (match := _DAILY_MEAN_LINE.match(line))),
               default=0)


def _has_monthly_means(program) -> bool:
    """True if a program SetOutdoorMetric has the monthly means of a weather file."""
    return any(line.startswith(f'set {_MONTHLY_MEAN} =') for line in _program_lines(program))


def _set_custom_model_lines(idf, enabled: bool) -> None:
    """Write the programs of the custom model of a model (those of accim 1.0.0 or later) with its outdoor metric,
    Tout_metric (``enabled``), or with the running mean of ASHRAE 55 of EnergyPlus, PMOT, as before accim 1.2.0:
    the comfort temperature (SetComfTemp), the subprograms of its setpoints (SetAST_CS99_<chunk>), the hour counters
    (CountHours_<zone>, where it gets a branch of its own) and the ventilation setpoint (SetVST, in mixed mode). The
    programs whose lines are not those of accim (of the comfort standards of the model) do not change."""
    from accim.sim.ems import program_lines as pl
    from accim.sim.ems.programs import set_program_lines
    from accim.sim.ems.setast import CUSTOM_COMFORT_STANDARD

    def replace(program, lines: Sequence[str]) -> None:
        if list(lines) != _program_lines(program):
            set_program_lines(program, lines)

    variable = pl.OUTDOOR_METRIC_VARIABLE
    old, new = ('PMOT', variable) if enabled else (variable, 'PMOT')
    comfort_temperature = {False: 'set ComfTemp = PMOT*m+n', True: f'set ComfTemp = {variable}*m+n'}
    subprogram = re.compile(rf'^SetAST_CS{CUSTOM_COMFORT_STANDARD}_\d+$', re.IGNORECASE)
    word = re.compile(rf'\b{old}\b')
    for program in idf.idfobjects['EnergyManagementSystem:Program']:
        name = str(program.Name)
        if name.upper() == 'SETCOMFTEMP':
            replace(program, [comfort_temperature[enabled] if line == comfort_temperature[not enabled] else line
                              for line in _program_lines(program)])
        elif subprogram.match(name):
            replace(program, [word.sub(new, line) for line in _program_lines(program)])
        elif name.upper().startswith(_COUNT_HOURS_PREFIX.upper()):
            zone = name[len(_COUNT_HOURS_PREFIX):]
            base = pl.format_lines(pl.COUNT_HOURS, zone=zone)
            variant = pl.format_lines(pl.COUNT_HOURS_OUTDOOR_METRIC, zone=zone)
            source, target = (base, variant) if enabled else (variant, base)
            lines = _program_lines(program)
            if lines == source:
                replace(program, target)
                continue
            try:
                standards = pl.chain_comfort_standards(lines)
            except ValueError:
                continue
            # The hour counters of some comfort standards only (the output IDFs of AddAccis)
            if (standards is not None and CUSTOM_COMFORT_STANDARD in standards
                    and lines == pl.for_comfort_standards(source, standards)):
                replace(program, pl.for_comfort_standards(target, standards))
        elif name.upper() == 'SETVST':
            source, target = (pl.SET_VST, pl.SET_VST_OUTDOOR_METRIC) if enabled else (pl.SET_VST_OUTDOOR_METRIC,
                                                                                       pl.SET_VST)
            if _program_lines(program) == list(source):
                replace(program, target)


def _remove_outdoor_metric_code(idf, zone_programs: Mapping[str, Any]) -> None:
    """Remove the EMS objects of the outdoor metric of the custom model, and its inputs."""
    from accim.sim.ems.inputs import RUN_PROGRAM_PREFIX
    from accim.sim.ems.programs import set_program_lines

    zones = list(zone_programs)
    own_programs = {PROGRAM.upper(), INIT_PROGRAM.upper()} | {f'{ZONE_PROGRAM_PREFIX}{z}'.upper() for z in zones}
    outputs = {_OUTPUT.upper()} | {f'{OUTPUT_PREFIX}{zone}'.upper() for zone in zones}
    _remove(idf, [p for p in idf.idfobjects['EnergyManagementSystem:Program'] if p.Name.upper() in own_programs])
    _remove(idf, [m for m in idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']
                  if m.Name.upper() in own_programs])
    _remove(idf, [g for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
                  if str(g.fieldvalues[1]).strip() == _FIRST_GLOBAL_VARIABLE])
    _remove(idf, [o for o in idf.idfobjects['EnergyManagementSystem:OutputVariable'] if o.Name.upper() in outputs])
    _remove(idf, [o for o in idf.idfobjects['Output:Variable'] if str(o.Variable_Name).upper() in outputs])
    for zone, program in zone_programs.items():
        lines = _program_lines(program)
        kept = [line for line in lines if line.split('=')[0].replace('set', '', 1).strip() not in INPUTS]
        if kept != lines:
            set_program_lines(program, kept)
        run_program = idf.getobject('EnergyManagementSystem:Program', f'{RUN_PROGRAM_PREFIX}{zone}')
        if run_program is not None:
            run_line = f'run {ZONE_PROGRAM_PREFIX}{zone}'
            lines = _program_lines(run_program)
            if run_line in lines:
                set_program_lines(run_program, [line for line in lines if line != run_line])


def _run_period_start(idf) -> int:
    """The first day (of the year) of the first RunPeriod of a model."""
    from accim.sim.arguments import to_day_of_year

    run_periods = idf.idfobjects['RunPeriod']
    if not run_periods:
        raise ValueError('The model has no RunPeriod: the outdoor metric of the custom model cannot begin with the '
                         'values of the weather file.')
    return to_day_of_year(f'{int(run_periods[0].Begin_Day_of_Month):02d}/{int(run_periods[0].Begin_Month):02d}',
                          'the first day of the RunPeriod')


def set_outdoor_metric_code(idf, enabled: bool, epw: Union[str, Any, None] = None, rewrite: bool = False) -> None:
    """Add (or update) the EMS objects of the outdoor metric of the custom model to a model with the ACCIS, or remove
    them.

    With ``enabled``:

    - the inputs ``CustAST_metric``, ``CustAST_alpha`` and ``CustAST_days`` in each program SetInputData_<zone> (with
      their default values if they are missing);
    - the programs SetOutdoorMetric (with a program calling manager at BeginTimestepBeforePredictor, before those of
      the zones), SetOutdoorMetric_<zone> (which RunACCIS_<zone> runs after SetInputData_<zone>) and InitOutdoorMetric
      (at BeginNewEnvironment), and their global variables;
    - the EMS output variables ``Tout_metric`` (of the zone that runs last, as the comfort temperature) and
      ``Tout_metric_<zone>``, with Output:Variable objects at the frequencies of those of the comfort temperature;
    - the programs of the custom model with its outdoor metric, Tout_metric, instead of PMOT: SetComfTemp, the
      subprograms SetAST_CS99_<chunk>, CountHours_<zone> and, in mixed mode, SetVST.

    The daily means kept are those of :func:`ring_days` for the ``CustAST_days`` of the zones. With a weather file,
    the programs begin with its values on the first day of the first RunPeriod of the model (:func:`initial_values`);
    without it, with the running mean of ASHRAE 55 of EnergyPlus (PMOT, decision D3), with a warning if a zone has a
    metric that EnergyPlus does not calculate. Without a weather file and ``rewrite``, a model that already has the
    programs keeps them (and the values of the weather file with which they begin) if they keep enough daily means
    (and the monthly means, if a zone needs them).

    Without ``enabled``, all of them are removed, and the programs of the custom model use PMOT: the model is as
    before accim 1.2.0. :func:`accim.sim.ems.programs.set_comfort_standard_code` calls this function with
    ``enabled`` if the model has the code of the custom model and a zone has a metric other than 'pmot'.

    :param idf: The model (eppy), with the ACCIS of accim 1.0.0 or later (programs SetInputData_<zone>).
    :param enabled: True to add or update them, False to remove them.
    :param epw: The weather file with which the programs begin; None for the running mean of ASHRAE 55 of
        EnergyPlus.
    :param rewrite: True to write the programs again even if the model has them (without ``epw``, they begin with
        PMOT).
    :raises ValueError: If a zone has the metric 'monthly_mean' and the programs do not have the monthly means of a
        weather file (decision D3), the model has no RunPeriod (with ``epw``), or the model already declares the EMS
        global variable Tout_metric.
    """
    from accim.sim.ems.inputs import INPUT_VARIABLES, RUN_PROGRAM_PREFIX, input_programs, read_inputs
    from accim.sim.ems.programs import add_program, set_program_lines

    zone_programs = input_programs(idf)
    zones = list(zone_programs)
    if not enabled:
        _remove_outdoor_metric_code(idf, zone_programs)
        _set_custom_model_lines(idf, False)
        return

    # 1. The inputs of the zones
    defaults = {item.variable: item.default for item in INPUT_VARIABLES if item.variable in INPUTS}
    values: Dict[str, Dict[str, Any]] = {}
    for zone, program in zone_programs.items():
        inputs = read_inputs(program)
        missing = [name for name in INPUTS if name not in inputs]
        if missing:
            set_program_lines(program, _program_lines(program) + [f'set {name} = {defaults[name]}' for name in missing])
            inputs = read_inputs(program)
        values[zone] = inputs
    ring = ring_days(values[zone]['CustAST_days'] for zone in zones)
    metrics = {metric_code(values[zone]['CustAST_metric']) for zone in zones}
    monthly = OUTDOOR_METRICS['monthly_mean'] in metrics

    # 2. The programs: those of the model stay if they can (without a weather file)
    existing = idf.getobject('EnergyManagementSystem:Program', PROGRAM)
    keep = (epw is None and not rewrite and existing is not None and _ring_of(existing) >= ring
            and (not monthly or _has_monthly_means(existing))
            and all(idf.getobject('EnergyManagementSystem:Program', f'{ZONE_PROGRAM_PREFIX}{zone}') is not None
                    for zone in zones)
            and idf.getobject('EnergyManagementSystem:Program', INIT_PROGRAM) is not None)
    if keep:
        ring = _ring_of(existing)
    else:
        if monthly and epw is None:
            raise ValueError("custom_outdoor_metric 'monthly_mean' needs the weather file of the simulation (argument "
                             "epw), whose monthly means the EMS programs keep.")
        initial = None
        if epw is not None:
            alphas = {zone: values[zone]['CustAST_alpha'] for zone in zones}
            initial = initial_values(epw, _run_period_start(idf), ring, alphas)
        elif metrics & _NEEDS_INITIAL_VALUES:
            names = sorted(metric_name(code) for code in metrics & _NEEDS_INITIAL_VALUES)
            warnings.warn(f'custom_outdoor_metric {names} begins with the running mean of ASHRAE 55 that EnergyPlus '
                          f'calculates (PMOT), without a weather file (argument epw): give the weather file of the '
                          f'simulation to begin with its values.')

        def write(name: str, lines: List[str]) -> None:
            program = idf.getobject('EnergyManagementSystem:Program', name)
            if program is None:
                add_program(idf, name, lines)
            else:
                set_program_lines(program, lines)

        write(PROGRAM, building_program_lines(ring, initial))
        for zone in zones:
            write(f'{ZONE_PROGRAM_PREFIX}{zone}',
                  zone_program_lines(zone, ring, None if initial is None else initial['running_means'][zone],
                                     initial is not None))
        write(INIT_PROGRAM, init_program_lines(zones, ring))

    # 3. RunACCIS_<zone> runs SetOutdoorMetric_<zone> after the inputs of the zone
    for zone in zones:
        run_program = idf.getobject('EnergyManagementSystem:Program', f'{RUN_PROGRAM_PREFIX}{zone}')
        if run_program is None:
            continue
        run_line = f'run {ZONE_PROGRAM_PREFIX}{zone}'
        lines = _program_lines(run_program)
        if run_line not in lines:
            index = next((n + 1 for n, line in enumerate(lines) if line.lower().startswith('run setinputdata_')), 0)
            set_program_lines(run_program, lines[:index] + [run_line] + lines[index:])

    # 4. The program calling managers: SetOutdoorMetric before the programs of the zones
    managers = idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']
    names = {m.Name.upper() for m in managers}
    if PROGRAM.upper() not in names:
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=PROGRAM,
                         EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor', Program_Name_1=PROGRAM)
        managers = idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']
        position = next((n for n, m in enumerate(managers)
                         if str(m.Program_Name_1).upper().startswith(('SETGEOVAR', RUN_PROGRAM_PREFIX.upper()))
                         and str(m.EnergyPlus_Model_Calling_Point).upper() == 'BEGINTIMESTEPBEFOREPREDICTOR'), None)
        if position is not None:
            managers.insert(position, managers.pop(len(managers) - 1))
    if INIT_PROGRAM.upper() not in names:
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=INIT_PROGRAM,
                         EnergyPlus_Model_Calling_Point='BeginNewEnvironment', Program_Name_1=INIT_PROGRAM)

    # 5. The global variables, in one object
    _remove(idf, [g for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
                  if str(g.fieldvalues[1]).strip() == _FIRST_GLOBAL_VARIABLE])
    declared = {str(name).strip().upper() for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
                for name in g.fieldvalues[1:] if str(name).strip()}
    names = [name for name in global_variables(ring, zones) if name.upper() not in declared]
    if names and names[0] != _FIRST_GLOBAL_VARIABLE:
        raise ValueError(f'The model already declares the EMS global variable {_FIRST_GLOBAL_VARIABLE}.')
    idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                     **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(names, start=1)})

    # 6. The EMS output variables, and their Output:Variable objects
    frequencies = _zone_frequencies(idf, zones)
    requested = {(str(o.Variable_Name).upper(), str(o.Reporting_Frequency).upper())
                 for o in idf.idfobjects['Output:Variable']}
    for name, variable in [(_OUTPUT, _FIRST_GLOBAL_VARIABLE)] + [(f'{OUTPUT_PREFIX}{zone}',) * 2 for zone in zones]:
        if idf.getobject('EnergyManagementSystem:OutputVariable', name) is None:
            idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=variable,
                             Type_of_Data_in_Variable='Averaged', Update_Frequency='ZoneTimestep',
                             EMS_Program_or_Subroutine_Name='', Units='C')
        for frequency in frequencies:
            if (name.upper(), str(frequency).upper()) not in requested:
                idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name,
                                 Reporting_Frequency=frequency, Schedule_Name='')

    # 7. The programs of the custom model with Tout_metric
    _set_custom_model_lines(idf, True)
