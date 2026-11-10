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
"""

from typing import Any, Dict, List, Tuple

import numpy as np

__all__ = [
    'ISO7730_STATIC_SETPOINTS',
    'add_standard_lines',
    'metric_variable',
    'needs_outdoor_metric_code',
    'outdoor_metric_standards',
    'remove_standard_lines',
    'setpoint_lines',
    'standard_branches',
    'standard_inputs',
]

#: The static setpoints of ISO 7730 of comfort mode 2 of the built-in comfort standards with the categories 80 and 90
#: (INT ASHRAE55, JPN Rijal, CHN Yang, IND IMAC R, IND Dhaka, ROU Udrea, BRA Rupp, CHL Perez-Fargallo and JPN
#: Aqilah2025: :data:`accim.sim.ems.setpoint_lines.SETPOINT_LINES`), out of the applicability limits: {category:
#: {'cooling': (below the lower limit, above the upper limit), 'heating': (below, above)}}
ISO7730_STATIC_SETPOINTS = {
    80: {'cooling': (25, 27), 'heating': (19, 22)},
    90: {'cooling': (24, 26), 'heating': (20, 23)},
}
#: The variables of the outdoor metrics that EnergyPlus calculates; the EMS calculates the others (Tout_metric)
_NATIVE_METRICS = {'pmot': 'PMOT', 'rmot': 'RMOT'}


def _number(value: float) -> str:
    """A number as Erl reads it: without exponent, and without decimals if it is an integer."""
    return np.format_float_positional(float(value), trim='-')


def _plus(value: float) -> str:
    """A number added to an expression: '+16.9', or '-3.6'."""
    return f'+{_number(value)}' if value >= 0 else f'-{_number(-value)}'


def metric_variable(outdoor_metric: str) -> str:
    """The variable of the EMS with an outdoor metric: PMOT and RMOT for 'pmot' and 'rmot', which EnergyPlus calculates,
    and Tout_metric for the others."""
    from accim.sim.ems.program_lines import OUTDOOR_METRIC_VARIABLE

    return _NATIVE_METRICS.get(outdoor_metric, OUTDOOR_METRIC_VARIABLE)


def needs_outdoor_metric_code(definition) -> bool:
    """True if the outdoor metric of a comfort standard needs the EMS code of the outdoor metric of the custom model
    (it is not 'pmot' nor 'rmot')."""
    return definition.outdoor_metric not in _NATIVE_METRICS


def outdoor_metric_standards() -> set:
    """The registered comfort standards whose outdoor metric needs the EMS code of the outdoor metric."""
    from accim.sim.standards import registered_comfort_standards

    return {number for number, definition in registered_comfort_standards().items()
            if needs_outdoor_metric_code(definition)}


def standard_inputs(definition) -> Dict[str, Any]:
    """The inputs of the outdoor metric (``CustAST_metric``, ``CustAST_alpha`` and ``CustAST_days``) of the zones of a
    comfort standard: those of its outdoor metric if the EMS calculates it, and 'pmot' (0) otherwise, so that its zones
    do not need the EMS code of the outdoor metric."""
    from accim.sim.ems.outdoor_metric import metric_code

    code = metric_code(definition.outdoor_metric) if needs_outdoor_metric_code(definition) else 0
    return {'CustAST_metric': code, 'CustAST_alpha': definition.alpha, 'CustAST_days': definition.days}


def _comfort_temperature(definition, limit: str = '') -> str:
    """The comfort temperature of a comfort standard, of its outdoor metric (or of one of its limits):
    ``<metric>*<slope>+<intercept>``, as that of the built-in comfort standards, or ``<intercept>-<metric>*<-slope>``
    with a negative slope, since Erl does not take a minus sign after a multiplication sign, not even in parentheses
    (EnergyPlus stops with "Minus sign used on the right side of multiplication sign", as
    :mod:`accim.sim.ems.erl`)."""
    regime = definition.regimes[0]
    variable = limit or metric_variable(definition.outdoor_metric)
    if regime.slope < 0:
        return f'{_number(regime.intercept)}-{variable}*{_number(-regime.slope)}'
    return f'{variable}*{_number(regime.slope)}{_plus(regime.intercept)}'


def standard_branches(definition) -> Dict[str, Tuple[str, ...]]:
    """The branches ``elseif ComfStand == <n>`` of a comfort standard in SetComfTemp, SetAppLimits, ApplyCAT and, if its
    outdoor metric is not PMOT, CountHours (with ``{zone}``) and SetVST."""
    from accim.sim.ems import program_lines as pl

    number, regime = definition.number, definition.regimes[0]
    condition = f'elseif ComfStand == {number}'
    metric = metric_variable(definition.outdoor_metric)
    cat_lines: List[str] = []
    for index, (category, (cooling, heating)) in enumerate(definition.category_offsets.items()):
        cat_lines += [f"{'if' if index == 0 else 'elseif'} (CAT == {_number(category)})",
                      f'set ACSToffset = {_number(cooling + regime.cooling_offset)}+CATcoolOffset',
                      f'set AHSToffset = {_number(heating + regime.heating_offset)}+CATheatOffset']
    branches = {
        'SetComfTemp': (condition, f'set ComfTemp = {_comfort_temperature(definition)}'),
        'SetAppLimits': (condition, f'set ACSTaul = {_number(regime.cooling_upper_limit)}',
                         f'set ACSTall = {_number(regime.cooling_lower_limit)}',
                         f'set AHSTaul = {_number(regime.heating_upper_limit)}',
                         f'set AHSTall = {_number(regime.heating_lower_limit)}'),
        'ApplyCAT': (condition, *cat_lines, 'endif'),
    }
    if metric != 'PMOT':
        branches['CountHours'] = (condition, *pl._count_hours_body(metric).split('\n'))
        branches['SetVST'] = (condition, f'if ({metric} >= AHSTall) && ({metric} <= ACSTaul)',
                              'set VST = ComfTemp+VSToffset', 'else', 'set VST = (roundedACST+roundedAHST)/2+VSToffset',
                              'endif')
    return branches


def setpoint_lines(definition) -> Dict[int, Tuple[str, ...]]:
    """The lines of the setpoints of each comfort mode of a comfort standard (without the rounding)."""
    metric = metric_variable(definition.outdoor_metric)
    lines: Dict[int, Tuple[str, ...]] = {}
    for mode in definition.standard.comfort_modes:
        mode = int(mode)
        if mode == 0:
            heating, cooling = definition.static_setpoints
            lines[mode] = (f'set ACST = {_number(cooling)}+ACSTtol', f'set AHST = {_number(heating)}+AHSTtol')
            continue
        result: List[str] = []
        for setpoint, kind in (('ACST', 'cooling'), ('AHST', 'heating')):
            lower, upper, tolerance = f'{setpoint}all', f'{setpoint}aul', f'{setpoint}tol'
            offset = f'{setpoint}offset'
            result += [f'if ({metric} >= {lower}) && ({metric} <= {upper})',
                       f'set {setpoint} = {_comfort_temperature(definition)}+{offset}+{tolerance}']
            if mode == 1:
                static = definition.static_setpoints[0 if kind == 'heating' else 1]
                result += [f'elseif {metric} < {lower}', f'set {setpoint} = {_number(static)}+{tolerance}',
                           f'elseif {metric} > {upper}', f'set {setpoint} = {_number(static)}+{tolerance}']
            elif mode == 2:
                for category in definition.category_offsets:
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
