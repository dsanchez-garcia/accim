# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The EMS code of the comfort standards defined by their data (proposal B3, :mod:`accim.sim.standards`).

When a comfort standard ``<n>`` (100 or more) is registered (:func:`accim.sim.standards.register_comfort_standard`),
:func:`add_standard_lines` writes its EMS code as that of the built-in comfort standards:

- the branches ``elseif ComfStand == <n>`` of SetComfTemp (``set ComfTemp = <metric>*<slope>+<intercept>``, or
  ``<intercept>-<metric>*<-slope>`` with a negative slope), SetAppLimits (its applicability limits), ApplyCAT (the
  offsets of its categories plus those of its regime, and the offsets ``CATcoolOffset`` and ``CATheatOffset``) and, if
  its outdoor metric is not PMOT, CountHours_<zone> and SetVST
  (:data:`accim.sim.ems.program_lines.REGISTERED_BRANCHES`, which the functions ``set_comf_temp_lines``... of
  :mod:`accim.sim.ems.program_lines` add to the chains of the built-in comfort standards, which do not change);
- the lines of the setpoints of its comfort modes (:data:`accim.sim.ems.setpoint_lines.SETPOINT_LINES`, in the
  subprograms ``SetAST_CS<n>_<chunk>`` of :data:`accim.sim.ems.setast.MODULAR_COMFORT_MODES`): 0, its static setpoints;
  1, 2 and 3, its adaptive setpoints within the applicability limits, and otherwise its static setpoints (1), the
  static setpoints of ISO 7730 that the built-in comfort standards with the categories 80 and 90 use in comfort mode 2
  (:data:`ISO7730_STATIC_SETPOINTS`, 2) or the adaptive setpoints of the limits, extended horizontally (3), as the
  built-in comfort standards (JPN Rijal, for instance).

Its outdoor metric (:data:`accim.sim.ems.outdoor_metric.OUTDOOR_METRICS`) is PMOT ('pmot') or RMOT ('rmot'), the
running means of EnergyPlus, or Tout_metric, which the EMS code of the outdoor metric of the custom model calculates
with the inputs ``CustAST_metric``, ``CustAST_alpha`` and ``CustAST_days`` of the zone (:func:`standard_inputs`, which
the zones of the comfort standard get, :mod:`accim.sim.ems.outdoor_metric`).

A comfort standard with several regimes, or with a regime with its own outdoor metric (:func:`uses_regimes`, task H5
of the review of accim 1.2.0, decision 4 of its section 6), has the code of the custom model: its branches read the
inputs of the custom model (``Tout_metric*m+n``; the limits ``CustAST_ACSTaul``, ``CustAST_ACSTall``,
``CustAST_AHSTaul`` and ``CustAST_AHSTall``; and the offsets of its categories plus ``CustAST_ACSToffset`` and
``CustAST_AHSToffset``), which the program of the regimes of each of its zones (``SelectCustomRegime_<zone>``,
:mod:`accim.sim.ems.custom_regimes`) sets to those of the regime of the timestep, and its outdoor metric is always
Tout_metric (also with 'pmot' or 'rmot', whose values the EMS code of the outdoor metric gives it), so that a regime can
have its own (:func:`standard_metric_variable`).

The built-in comfort standards of :data:`WEATHER_FILE_METRICS` (JPN Aqilah 2025, 23) have another outdoor metric in
the models with the values of the weather file of the simulation (the argument ``epw`` of AddAccis or modify_accis):
their code then reads Tout_metric instead of RMOT (:func:`weather_file_lines`, finding B4-1 of the review of 1.2.0).

The built-in comfort standards of :data:`BUILT_IN_METRICS` (IND IMAC R 7DRM, 9) have an outdoor metric that EnergyPlus
does not calculate: their code always reads Tout_metric, and their zones have the inputs of their outdoor metric
(:func:`own_metric_inputs`), with or without the weather file.
"""

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from accim.sim.ems.erl import format_number

__all__ = [
    'BUILT_IN_METRICS',
    'DEFAULT_METRIC_INPUTS',
    'ISO7730_STATIC_SETPOINTS',
    'WEATHER_FILE_METRICS',
    'add_standard_lines',
    'built_in_metric',
    'left_metric_inputs',
    'metric_variable',
    'needs_outdoor_metric_code',
    'outdoor_metric_standards',
    'own_metric_inputs',
    'regime_standards',
    'remove_standard_lines',
    'setpoint_lines',
    'standard_branches',
    'standard_inputs',
    'standard_metric_variable',
    'uses_regimes',
    'weather_file_definition',
    'weather_file_lines',
]

#: The static setpoints of ISO 7730 of comfort mode 2 of the built-in comfort standards with the categories 80 and 90
#: (INT ASHRAE55, JPN Rijal, CHN Yang, IND IMAC R, IND Dhaka, ROU Udrea, BRA Rupp, CHL Perez-Fargallo and JPN
#: Aqilah2025: :data:`accim.sim.ems.setpoint_lines.SETPOINT_LINES`), out of the applicability limits: {category:
#: {'cooling': (below the lower limit, above the upper limit), 'heating': (below, above)}}
ISO7730_STATIC_SETPOINTS = {
    80: {'cooling': (25, 27), 'heating': (19, 22)},
    90: {'cooling': (24, 26), 'heating': (20, 23)},
}
#: The built-in comfort standards defined by their data whose outdoor metric is another one in the models with the
#: values of the weather file of the simulation (the programs of the outdoor metric begin with them, argument ``epw`` of
#: AddAccis or modify_accis): JPN Aqilah 2025 (23), whose running mean outdoor temperature (α = 0.8, equation 7 of
#: Aqilah et al., 2025) is then the running mean of EN 16798-1:2019 (B.1) with α = 0.8 that the EMS calculates
#: ('rmot_alpha'), which begins with the values of the weather file, instead of the RMOT of EnergyPlus, whose first
#: value in a run period is the sum (1 − α)·{Tod−1 + α·Tod−2 + … + α⁶·Tod−7} of equation 19.82 of the Engineering
#: Reference, not divided by 1 − α⁷ (finding B4-1 of the review of 1.2.0, section 3.1 of
#: ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md``)
WEATHER_FILE_METRICS: Dict[int, str] = {23: 'rmot_alpha'}
#: The built-in comfort standards whose outdoor metric EnergyPlus does not calculate, with its name of
#: :data:`accim.sim.ems.outdoor_metric.OUTDOOR_METRICS`, its alpha and its days: the EMS code of the outdoor metric of
#: the custom model calculates it in every model with a zone of them, as that of the comfort standards defined by their
#: data, and their code reads Tout_metric (:func:`own_metric_inputs`). IND IMAC R 7DRM (9) is model A of Rawal et al.
#: (2022), Building and Environment 219, 109187 (section 4.4 and Fig. 15), Tneut = 0.39·Tout-7DRM + 18.42, whose metric
#: is the 7-day running mean of the outdoor temperature, which the paper tells apart from its weighted version
#: (Tout-7DRM-W): the arithmetic mean of the daily means of the 7 previous days, 'ndrm' with 7 days. EnergyPlus has no
#: such mean (PMOT is that of 30 days, and RMOT is exponential), and until accim 1.2.0 comfort standard 9 read PMOT
#: (the decisions of 2026-11-12, ``notes/decisions.md``). The alpha is that of the inputs of the zones, which 'ndrm'
#: does not use.
BUILT_IN_METRICS: Dict[int, Tuple[str, float, int]] = {9: ('ndrm', 0.8, 7)}
#: The inputs of the outdoor metric of the zones without an outdoor metric of their own: 'pmot', the defaults of
#: :data:`accim.sim.ems.inputs.INPUT_VARIABLES` (:func:`left_metric_inputs`)
DEFAULT_METRIC_INPUTS: Dict[str, Any] = {'CustAST_metric': 0, 'CustAST_alpha': 0.8, 'CustAST_days': 30}
#: The variables of the outdoor metrics that EnergyPlus calculates; the EMS calculates the others (Tout_metric)
_NATIVE_METRICS = {'pmot': 'PMOT', 'rmot': 'RMOT'}
_CHAIN_PROGRAMS = ('SETCOMFTEMP', 'SETVST')
_COUNT_HOURS_PREFIX = 'COUNTHOURS_'
_SUBPROGRAM_PREFIX = 'SETAST_CS'
_OPENING = ('IF', 'WHILE')
_CLOSING = ('ENDIF', 'ENDWHILE')


def _number(value: float) -> str:
    """A number as Erl reads it: without exponent, and without decimals if it is an integer."""
    return format_number(value)


def _plus(value: float) -> str:
    """A number added to an expression: '+16.9', or '-3.6'."""
    return f'+{_number(value)}' if value >= 0 else f'-{_number(-value)}'


def metric_variable(outdoor_metric: str) -> str:
    """The variable of the EMS with an outdoor metric: PMOT and RMOT for 'pmot' and 'rmot', which EnergyPlus calculates,
    and Tout_metric for the others."""
    from accim.sim.ems.program_lines import OUTDOOR_METRIC_VARIABLE

    return _NATIVE_METRICS.get(outdoor_metric, OUTDOOR_METRIC_VARIABLE)


def uses_regimes(definition) -> bool:
    """True if a comfort standard has several regimes, or a regime with its own outdoor metric: its EMS code selects
    the regime of each timestep as the regimes of the custom model (see the module)."""
    return len(definition.regimes) > 1 or any(regime.outdoor_metric is not None for regime in definition.regimes)


def regime_standards() -> set:
    """The comfort standards of the registry with regimes (:func:`uses_regimes`)."""
    from accim.sim.standards import registered_comfort_standards

    return {number for number, definition in registered_comfort_standards().items() if uses_regimes(definition)}


def needs_outdoor_metric_code(definition) -> bool:
    """True if the outdoor metric of a comfort standard needs the EMS code of the outdoor metric of the custom model:
    it is not 'pmot' nor 'rmot', or the comfort standard has regimes (:func:`uses_regimes`)."""
    return definition.outdoor_metric not in _NATIVE_METRICS or uses_regimes(definition)


def standard_metric_variable(definition) -> str:
    """The variable of the outdoor metric in the EMS code of a comfort standard: Tout_metric with regimes
    (:func:`uses_regimes`), and that of its outdoor metric otherwise (:func:`metric_variable`)."""
    from accim.sim.ems.program_lines import OUTDOOR_METRIC_VARIABLE

    return OUTDOOR_METRIC_VARIABLE if uses_regimes(definition) else metric_variable(definition.outdoor_metric)


def outdoor_metric_standards() -> set:
    """The comfort standards whose outdoor metric needs the EMS code of the outdoor metric: the registered ones whose
    outdoor metric EnergyPlus does not calculate (or with regimes), and the built-in ones of :data:`BUILT_IN_METRICS`
    (IND IMAC R 7DRM, 9)."""
    from accim.sim.standards import registered_comfort_standards

    return {number for number, definition in registered_comfort_standards().items()
            if needs_outdoor_metric_code(definition)} | set(BUILT_IN_METRICS)


def built_in_metric(number: Any) -> Optional[Tuple[str, float, int]]:
    """The outdoor metric of a built-in comfort standard of :data:`BUILT_IN_METRICS` (its name, alpha and days), or
    None for the other comfort standards."""
    try:
        return BUILT_IN_METRICS.get(int(number))
    except (TypeError, ValueError):
        return None


def own_metric_inputs(number: Any) -> Optional[Dict[str, Any]]:
    """The inputs of the outdoor metric (``CustAST_metric``, ``CustAST_alpha`` and ``CustAST_days``) of the zones of a
    comfort standard with its own outdoor metric: one defined by its data and registered (:func:`standard_inputs`), or
    a built-in one of :data:`BUILT_IN_METRICS` (IND IMAC R 7DRM, 9: 'ndrm' with 7 days). None for the other comfort
    standards, whose zones keep the inputs of the outdoor metric of the custom model."""
    from accim.sim.ems.outdoor_metric import metric_code
    from accim.sim.standards import comfort_standard_definition

    definition = comfort_standard_definition(number)
    if definition is not None:
        return standard_inputs(definition)
    metric = built_in_metric(number)
    if metric is None:
        return None
    name, alpha, days = metric
    return {'CustAST_metric': metric_code(name), 'CustAST_alpha': alpha, 'CustAST_days': days}


def left_metric_inputs(previous: Any, new: Any, current: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    """The inputs of the outdoor metric that a zone gets when it leaves a built-in comfort standard whose outdoor
    metric the EMS calculates (:data:`BUILT_IN_METRICS`: IND IMAC R 7DRM, 9) for a comfort standard without an outdoor
    metric of its own, while its inputs are still those of the comfort standard that it leaves: those of 'pmot'
    (:data:`DEFAULT_METRIC_INPUTS`), the default of the custom model, which would otherwise inherit the mean of the 7
    previous days. None otherwise: the zone keeps its inputs, or gets those of its new comfort standard.

    :param previous: The comfort standard that the zone leaves.
    :param new: The comfort standard that it gets.
    :param current: The inputs of the zone (:func:`accim.sim.ems.inputs.read_inputs`).
    """
    if built_in_metric(previous) is None or own_metric_inputs(new) is not None:
        return None
    try:
        if int(previous) == int(new):
            return None
        same = all(float(current.get(name)) == float(value) for name, value in own_metric_inputs(previous).items())
    except (TypeError, ValueError):
        return None
    return dict(DEFAULT_METRIC_INPUTS) if same else None


def standard_inputs(definition) -> Dict[str, Any]:
    """The inputs of the outdoor metric (``CustAST_metric``, ``CustAST_alpha`` and ``CustAST_days``) of the zones of a
    comfort standard: those of its outdoor metric if the EMS calculates it, and 'pmot' (0) otherwise, so that its zones
    do not need the EMS code of the outdoor metric."""
    from accim.sim.ems.outdoor_metric import metric_code

    code = metric_code(definition.outdoor_metric) if needs_outdoor_metric_code(definition) else 0
    return {'CustAST_metric': code, 'CustAST_alpha': definition.alpha, 'CustAST_days': definition.days}


def weather_file_definition(number: Any):
    """The definition of a comfort standard of :data:`WEATHER_FILE_METRICS` with the outdoor metric that it has in the
    models with the values of the weather file of the simulation (JPN Aqilah 2025: 'rmot_alpha', α = 0.8), or None for
    the other comfort standards."""
    import dataclasses

    from accim.sim.standards import definition_of

    try:
        number = int(number)
    except (TypeError, ValueError):
        return None
    if number not in WEATHER_FILE_METRICS:
        return None
    return dataclasses.replace(definition_of(number), outdoor_metric=WEATHER_FILE_METRICS[number])


def _branch_header(number: int) -> 're.Pattern':
    return re.compile(rf'^(IF|ELSEIF)\s+\(?\s*ComfStand\s*==\s*{number}\s*\)?$', re.IGNORECASE)


def _replace_in_branches(lines: Iterable[str], number: int, word: 're.Pattern', new: str) -> List[str]:
    """Some lines with a variable replaced in the branches ``if ComfStand == <n>`` or ``elseif ComfStand == <n>`` of a
    comfort standard (whose conditions name it alone), at any depth: from the line after the condition to the next
    ``elseif``, ``else`` or ``endif`` of the same block."""
    header = _branch_header(number)
    result: List[str] = []
    depth = 0
    branch_depth: Optional[int] = None
    for line in lines:
        text = str(line).strip()
        keyword = text.split(' ', 1)[0].upper()
        if branch_depth is not None and depth == branch_depth and keyword in ('ELSEIF', 'ELSE', 'ENDIF'):
            branch_depth = None
        if branch_depth is not None:
            line = word.sub(new, str(line))
        if keyword in _OPENING:
            depth += 1
        elif keyword in _CLOSING:
            depth -= 1
        if keyword in ('IF', 'ELSEIF') and header.match(text):
            branch_depth = depth
        result.append(line)
    return result


def weather_file_lines(name: str, lines: Iterable[str], enabled: bool,
                       comfort_standards: Optional[Iterable[int]] = None) -> List[str]:
    """The lines of an EMS program of the ACCIS with the code of the comfort standards of :data:`WEATHER_FILE_METRICS`
    (of some of them only) with the outdoor metric of the models with the values of the weather file, Tout_metric
    (``enabled``), or with that of their definition (RMOT): their branches in the chains of SetComfTemp,
    CountHours_<zone> and SetVST, and their subprograms SetAST_CS<n>_<chunk> (all their lines). The lines of the other
    programs, and of the other comfort standards, do not change.

    :param name: The name of the program (or of the subprogram whose lines they are).
    :param lines: Its lines.
    :param enabled: True for the outdoor metric of the weather file, False for that of the definition.
    :param comfort_standards: Some comfort standards of :data:`WEATHER_FILE_METRICS`, or None for all of them.
    """
    from accim.sim.standards import definition_of

    lines = list(lines)
    upper_name = str(name).upper()
    numbers = WEATHER_FILE_METRICS if comfort_standards is None else [
        number for number in comfort_standards if number in WEATHER_FILE_METRICS]
    for number in numbers:
        native = metric_variable(definition_of(number).outdoor_metric)
        weather = metric_variable(WEATHER_FILE_METRICS[number])
        old, new = (native, weather) if enabled else (weather, native)
        word = re.compile(rf'\b{old}\b')
        if upper_name.startswith(f'{_SUBPROGRAM_PREFIX}{number}_'):
            lines = [word.sub(new, str(line)) for line in lines]
        elif upper_name in _CHAIN_PROGRAMS or upper_name.startswith(_COUNT_HOURS_PREFIX):
            lines = _replace_in_branches(lines, number, word, new)
    return lines


def _comfort_temperature(definition, limit: str = '') -> str:
    """The comfort temperature of a comfort standard, of its outdoor metric (or of one of its limits):
    ``<metric>*<slope>+<intercept>``, as that of the built-in comfort standards, or ``<intercept>-<metric>*<-slope>``
    with a negative slope, since Erl does not take a minus sign after a multiplication sign, not even in parentheses
    (EnergyPlus stops with "Minus sign used on the right side of multiplication sign", as
    :mod:`accim.sim.ems.erl`). With regimes, ``<metric>*m+n``, the inputs of the custom model that the program of the
    regimes of the zone sets, as the comfort temperature of the custom model."""
    variable = limit or standard_metric_variable(definition)
    if uses_regimes(definition):
        return f'{variable}*m+n'
    regime = definition.regimes[0]
    if regime.slope < 0:
        return f'{_number(regime.intercept)}-{variable}*{_number(-regime.slope)}'
    return f'{variable}*{_number(regime.slope)}{_plus(regime.intercept)}'


def standard_branches(definition) -> Dict[str, Tuple[str, ...]]:
    """The branches ``elseif ComfStand == <n>`` of a comfort standard in SetComfTemp, SetAppLimits, ApplyCAT and, if its
    outdoor metric is not PMOT, CountHours (with ``{zone}``) and SetVST. With regimes (:func:`uses_regimes`), they read
    the inputs of the custom model that the program of the regimes of the zone sets (see the module)."""
    from accim.sim.ems import program_lines as pl

    number, regime = definition.number, definition.regimes[0]
    condition = f'elseif ComfStand == {number}'
    metric = standard_metric_variable(definition)
    regimes = uses_regimes(definition)
    cat_lines: List[str] = []
    # In the numeric order of the categories, whatever the order of the definition (finding B3-2 of the review of
    # accim 1.2.0), as the branches of the built-in comfort standards
    for index, (category, (cooling, heating)) in enumerate(sorted(definition.category_offsets.items())):
        cat_lines.append(f"{'if' if index == 0 else 'elseif'} (CAT == {_number(category)})")
        if regimes:
            # The offsets of the regime of the timestep, inputs of the custom model
            cat_lines += [f'set ACSToffset = {_number(cooling)}+CustAST_ACSToffset+CATcoolOffset',
                          f'set AHSToffset = {_number(heating)}+CustAST_AHSToffset+CATheatOffset']
        else:
            cat_lines += [f'set ACSToffset = {_number(cooling + regime.cooling_offset)}+CATcoolOffset',
                          f'set AHSToffset = {_number(heating + regime.heating_offset)}+CATheatOffset']
    if regimes:
        limits = ('set ACSTaul = CustAST_ACSTaul', 'set ACSTall = CustAST_ACSTall', 'set AHSTaul = CustAST_AHSTaul',
                  'set AHSTall = CustAST_AHSTall')
    else:
        limits = (f'set ACSTaul = {_number(regime.cooling_upper_limit)}',
                  f'set ACSTall = {_number(regime.cooling_lower_limit)}',
                  f'set AHSTaul = {_number(regime.heating_upper_limit)}',
                  f'set AHSTall = {_number(regime.heating_lower_limit)}')
    branches = {
        'SetComfTemp': (condition, f'set ComfTemp = {_comfort_temperature(definition)}'),
        'SetAppLimits': (condition, *limits),
        'ApplyCAT': (condition, *cat_lines, 'endif'),
    }
    if metric != 'PMOT':
        branches['CountHours'] = (condition, *pl._count_hours_body(metric).split('\n'))
        branches['SetVST'] = (condition, f'if ({metric} >= AHSTall) && ({metric} <= ACSTaul)',
                              'set VST = ComfTemp+VSToffset', 'else', 'set VST = (roundedACST+roundedAHST)/2+VSToffset',
                              'endif')
    return branches


def setpoint_lines(definition) -> Dict[int, Tuple[str, ...]]:
    """The lines of the setpoints of each comfort mode of a comfort standard (without the rounding). The static
    setpoints of the comfort standards whose standard does not give them (JPN Aqilah 2025) are the inputs StaticAHST
    and StaticACST of the zone (:mod:`accim.sim.ems.static_setpoints`); those of the others, the numbers of their
    definition."""
    from accim.sim.ems.static_setpoints import INPUTS as STATIC_INPUTS, has_static_setpoints

    metric = standard_metric_variable(definition)
    if has_static_setpoints(definition.standard.number):
        static_setpoints = STATIC_INPUTS
    elif definition.static_setpoints is not None:
        static_setpoints = tuple(_number(value) for value in definition.static_setpoints)
    else:
        static_setpoints = None
    lines: Dict[int, Tuple[str, ...]] = {}
    for mode in definition.standard.comfort_modes:
        mode = int(mode)
        if mode == 0:
            heating, cooling = static_setpoints
            lines[mode] = (f'set ACST = {cooling}+ACSTtol', f'set AHST = {heating}+AHSTtol')
            continue
        result: List[str] = []
        for setpoint, kind in (('ACST', 'cooling'), ('AHST', 'heating')):
            lower, upper, tolerance = f'{setpoint}all', f'{setpoint}aul', f'{setpoint}tol'
            offset = f'{setpoint}offset'
            result += [f'if ({metric} >= {lower}) && ({metric} <= {upper})',
                       f'set {setpoint} = {_comfort_temperature(definition)}+{offset}+{tolerance}']
            if mode == 1:
                static = static_setpoints[0 if kind == 'heating' else 1]
                result += [f'elseif {metric} < {lower}', f'set {setpoint} = {static}+{tolerance}',
                           f'elseif {metric} > {upper}', f'set {setpoint} = {static}+{tolerance}']
            elif mode == 2:
                for category in sorted(definition.category_offsets):
                    below, above = ISO7730_STATIC_SETPOINTS[category][kind]
                    result += [f'elseif CAT=={_number(category)}', f'if {metric} < {lower}',
                               f'set {setpoint} = {_number(below)}+{tolerance}', f'elseif {metric} > {upper}',
                               f'set {setpoint} = {_number(above)}+{tolerance}', 'endif']
            else:
                result += [f'elseif {metric} < {lower}',
                           f'set {setpoint} = {_comfort_temperature(definition, lower)}+{offset}+{tolerance}',
                           f'elseif {metric} > {upper}',
                           f'set {setpoint} = {_comfort_temperature(definition, upper)}+{offset}+{tolerance}']
            result.append('endif')
        lines[mode] = tuple(result)
    return lines


def add_standard_lines(definition) -> None:
    """Add the EMS code of a comfort standard defined by its data to the programs of the ACCIS (see the module)."""
    from accim.sim.ems import program_lines as pl
    from accim.sim.ems.setast import MODULAR_COMFORT_MODES
    from accim.sim.ems.setpoint_lines import SETPOINT_LINES

    number = definition.number
    pl.REGISTERED_BRANCHES[number] = standard_branches(definition)
    for mode, lines in setpoint_lines(definition).items():
        SETPOINT_LINES[(number, mode)] = lines
    MODULAR_COMFORT_MODES[number] = sorted(int(mode) for mode in definition.standard.comfort_modes)


def remove_standard_lines(number: int) -> None:
    """Remove the EMS code of a comfort standard defined by its data from the programs of the ACCIS."""
    from accim.sim.ems import program_lines as pl
    from accim.sim.ems.setast import MODULAR_COMFORT_MODES
    from accim.sim.ems.setpoint_lines import SETPOINT_LINES

    pl.REGISTERED_BRANCHES.pop(number, None)
    for key in [key for key in SETPOINT_LINES if key[0] == number]:
        del SETPOINT_LINES[key]
    MODULAR_COMFORT_MODES.pop(number, None)
