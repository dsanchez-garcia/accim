# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Several regimes of the custom comfort model, comfort standard 99 (proposal B2).

The custom model has one comfort temperature (``custom_slope`` and ``custom_intercept``), two offsets and four
applicability limits: the inputs ``m``, ``n``, ``CustAST_ACSToffset``, ``CustAST_AHSToffset``, ``CustAST_ACSTall``,
``CustAST_ACSTaul``, ``CustAST_AHSTall`` and ``CustAST_AHSTaul`` of each zone (its program SetInputData_<zone>). Many
comfort models have several equations or limits, each one under some conditions (section 4, B2, of
``notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md``). With ``custom_regimes``, a list of
:class:`accim.sim.arguments.CustomRegime`, each zone of the custom model has the program ``SelectCustomRegime_<zone>``,
which ``RunACCIS_<zone>`` runs right before SetAppLimits: a chain ``if ... elseif ... endif`` in the order of the list,
which is the priority (decision D6 of the brief of 1.2.0), sets these inputs to the coefficients of the first regime
whose condition holds. SetAppLimits, ApplyCAT, SetComfTemp, the subprograms of SetAST, the hour counters and SetVST use
them as before, without changes. If no condition holds, the inputs of SetInputData_<zone> (the scalar arguments
``custom_slope``...) apply: unless the last regime is 'always', they are the last regime.

The conditions (:data:`accim.sim.arguments.REGIME_CONDITIONS` and :data:`accim.sim.arguments.METRIC_CONDITIONS`):

- 'always': the last regime (``else``).
- 'cooling_season' and 'heating_season': CoolingSeason is 1 or 0. The program calculates CoolingSeason with the lines
  of SetAST_Master (:data:`accim.sim.ems.setast.COOLING_SEASON_LINES`, with the inputs CoolSeasonStart and
  CoolSeasonEnd of the zone), which calculates it again later in the timestep with the same value.
- 'hvac_off' and 'hvac_on', in mixed mode only ('vrf_mm' and 'ex_mm'): NoH_NoC_reqs is 1 or 0, calculated with the
  lines with which the program ApplyAST_<zone> calculates it (:data:`accim.sim.ems.program_lines.HVAC_OFF_FROM_COILS`
  and :data:`accim.sim.ems.program_lines.HVAC_OFF_FROM_LOAD`): from the sensors of the coils of the VRF system of the
  zone, or of the load to the setpoints of its thermostat, which the EMS reads at the beginning of the timestep, so
  they are those of the previous timestep.
- ``('metric_below', x)``, ``('metric_above', x)`` and ``('metric_between', (x1, x2))``: the outdoor metric of the
  custom model of the zone (PMOT, or Tout_metric in the models with the EMS code of its outdoor metric,
  :mod:`accim.sim.ems.outdoor_metric`) is lower than x, higher than x, or from x1 to x2 (both included, as the
  applicability limits of the ACCIS).

The EMS global variable ``CustomRegime_<zone>`` (and the EMS output variable of the same name, averaged) is the number
of the regime of the timestep, from 1, or 0 when the inputs of SetInputData_<zone> apply.
"""

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from accim.sim.arguments import CustomRegime, check_custom_regimes

__all__ = [
    'OUTPUT_PREFIX',
    'PROGRAM_PREFIX',
    'REGIME_INPUTS',
    'condition_expression',
    'condition_text',
    'custom_regimes_of',
    'has_custom_regimes',
    'hvac_off_lines',
    'parse_regime_program',
    'regime_program_lines',
    'set_custom_regimes',
    'set_zone_custom_regimes',
    'uses_hvac_conditions',
    'uses_season_conditions',
]

#: The program of the regimes of each zone is this prefix and the name of the zone in the EMS objects
PROGRAM_PREFIX = 'SelectCustomRegime_'
#: The EMS global variable (and output variable) with the number of the regime of each zone
OUTPUT_PREFIX = 'CustomRegime_'
#: The inputs of the custom model that each regime sets: the field of :class:`accim.sim.arguments.CustomRegime` -> the
#: EMS variable (of SetInputData_<zone>)
REGIME_INPUTS = {
    'slope': 'm',
    'intercept': 'n',
    'cooling_offset': 'CustAST_ACSToffset',
    'heating_offset': 'CustAST_AHSToffset',
    'cooling_lower_limit': 'CustAST_ACSTall',
    'cooling_upper_limit': 'CustAST_ACSTaul',
    'heating_lower_limit': 'CustAST_AHSTall',
    'heating_upper_limit': 'CustAST_AHSTaul',
}
_CUSTOM_COMFORT_STANDARD = 99
#: RunACCIS_<zone> runs the program of the regimes right before this line
_RUN_BEFORE = 'run SetAppLimits'
_SEASON_CONDITIONS = ('cooling_season', 'heating_season')
_HVAC_CONDITIONS = ('hvac_off', 'hvac_on')
_CONDITION_VARIABLES = {'cooling_season': 'CoolingSeason == 1', 'heating_season': 'CoolingSeason == 0',
                        'hvac_off': 'NoH_NoC_reqs == 1', 'hvac_on': 'NoH_NoC_reqs == 0'}
_NUMBER = r'-?\d+(?:\.\d+)?'
_METRIC = r'(?:PMOT|Tout_metric)'
_METRIC_PATTERNS = (
    (re.compile(rf'^{_METRIC}\s*<\s*({_NUMBER})$', re.IGNORECASE), 'metric_below'),
    (re.compile(rf'^{_METRIC}\s*>\s*({_NUMBER})$', re.IGNORECASE), 'metric_above'),
    (re.compile(rf'^\(\s*{_METRIC}\s*>=\s*({_NUMBER})\s*\)\s*&&\s*\(\s*{_METRIC}\s*<=\s*({_NUMBER})\s*\)$',
                re.IGNORECASE), 'metric_between'),
)
_ASSIGNMENT = re.compile(r'^set\s+(\S+)\s*=\s*(\S+)$', re.IGNORECASE)


def _number(value: float) -> str:
    """A number as Erl reads it: without exponent, and without decimals if it is an integer."""
    return np.format_float_positional(float(value), trim='-')


def _value(text: str) -> float:
    number = float(text)
    return int(number) if re.fullmatch(r'-?\d+', text) else number


def _program_lines(program) -> List[str]:
    return [str(value).strip() for value in program.fieldvalues[2:]]


def uses_season_conditions(regimes: Sequence[CustomRegime]) -> bool:
    """True if a regime has the condition 'cooling_season' or 'heating_season'."""
    return any(regime.condition in _SEASON_CONDITIONS for regime in regimes)


def uses_hvac_conditions(regimes: Sequence[CustomRegime]) -> bool:
    """True if a regime has the condition 'hvac_off' or 'hvac_on' (mixed mode only)."""
    return any(regime.condition in _HVAC_CONDITIONS for regime in regimes)


def condition_text(condition: Any) -> str:
    """The text of the condition of a regime: 'always', 'metric_below 10', 'metric_between 10 20'..."""
    if isinstance(condition, str):
        return condition
    name, value = condition
    values = value if isinstance(value, (list, tuple)) else (value,)
    return ' '.join([name, *(_number(v) for v in values)])


def condition_expression(condition: Any, metric: str = 'PMOT') -> Optional[str]:
    """The Erl expression of the condition of a regime (None for 'always').

    :param condition: The condition (that of a :class:`accim.sim.arguments.CustomRegime`).
    :param metric: The variable of the outdoor metric of the custom model: 'PMOT', or 'Tout_metric' in the models with
        the EMS code of its outdoor metric.
    """
    if isinstance(condition, str):
        return _CONDITION_VARIABLES.get(condition)
    name, value = condition
    if name == 'metric_below':
        return f'{metric} < {_number(value)}'
    if name == 'metric_above':
        return f'{metric} > {_number(value)}'
    return f'({metric} >= {_number(value[0])}) && ({metric} <= {_number(value[1])})'


def regime_program_lines(zone: str, regimes: Sequence[CustomRegime], metric: str = 'PMOT',
                         hvac_lines: Optional[Sequence[str]] = None) -> List[str]:
    """The lines of the program SelectCustomRegime_<zone>.

    :param zone: The name of the zone in the EMS objects.
    :param regimes: The regimes, in their order of priority (see :func:`accim.sim.arguments.check_custom_regimes`).
    :param metric: The variable of the outdoor metric of the custom model (see :func:`condition_expression`).
    :param hvac_lines: The lines that set NoH_NoC_reqs in the zone (:func:`hvac_off_lines`), which the conditions
        'hvac_off' and 'hvac_on' need.
    :raises ValueError: If there are no regimes, or a regime has the condition 'hvac_off' or 'hvac_on' without
        ``hvac_lines``.
    """
    from accim.sim.ems.setast import COOLING_SEASON_LINES

    regimes = check_custom_regimes(regimes)
    if not regimes:
        raise ValueError('The program of the regimes of the custom model needs at least one regime.')
    output = f'{OUTPUT_PREFIX}{zone}'
    lines: List[str] = []
    if regimes[-1].condition != 'always':
        # None of the conditions holds: the inputs of SetInputData_<zone>
        lines.append(f'set {output} = 0')
    if uses_season_conditions(regimes):
        lines += list(COOLING_SEASON_LINES)
    if uses_hvac_conditions(regimes):
        if not hvac_lines:
            raise ValueError("The conditions 'hvac_off' and 'hvac_on' of the regimes of the custom model need mixed "
                             "mode (script_type 'vrf_mm' or 'ex_mm'), whose HVAC systems switch off while the windows "
                             "are open.")
        lines += list(hvac_lines)

    def body(number: int, regime: CustomRegime) -> List[str]:
        return ([f'set {variable} = {_number(getattr(regime, field))}' for field, variable in REGIME_INPUTS.items()]
                + [f'set {output} = {number}'])

    if len(regimes) == 1 and regimes[0].condition == 'always':
        return lines + body(1, regimes[0])
    for number, regime in enumerate(regimes, start=1):
        expression = condition_expression(regime.condition, metric)
        if expression is None:
            lines.append('else')
        else:
            lines.append(f"{'if' if number == 1 else 'elseif'} {expression}")
        lines += body(number, regime)
    lines.append('endif')
    return lines


def hvac_off_lines(idf, zone: str) -> Optional[List[str]]:
    """The lines with which the program ApplyAST_<zone> of mixed mode of a zone sets NoH_NoC_reqs (those of
    :data:`accim.sim.ems.program_lines.HVAC_OFF_FROM_COILS` or
    :data:`accim.sim.ems.program_lines.HVAC_OFF_FROM_LOAD`), or None if the zone is not in mixed mode."""
    from accim.sim.ems import program_lines as pl

    program = idf.getobject('EnergyManagementSystem:Program', f'ApplyAST_{zone}')
    if program is None:
        return None
    lines = [line.lower() for line in _program_lines(program)]
    for candidate in (pl.HVAC_OFF_FROM_COILS, pl.HVAC_OFF_FROM_LOAD):
        expected = pl.format_lines(candidate, zone=zone)
        if lines[:len(expected)] == [line.lower() for line in expected]:
            return expected
    return None


def _parse_condition(text: str) -> Any:
    for condition, expression in _CONDITION_VARIABLES.items():
        if re.fullmatch(r'\s*'.join(re.escape(part) for part in expression.split()), text, re.IGNORECASE):
            return condition
    for pattern, name in _METRIC_PATTERNS:
        match = pattern.match(text)
        if match:
            values = [_value(group) for group in match.groups()]
            return (name, tuple(values)) if name == 'metric_between' else (name, values[0])
    raise ValueError(f'{text!r} is not a condition of the regimes of the custom model of accim.')


def parse_regime_program(lines: Sequence[str], zone: str) -> Tuple[CustomRegime, ...]:
    """The regimes of the lines of a program SelectCustomRegime_<zone> (those of :func:`regime_program_lines`).

    :param lines: The lines of the program (without indentation or with it; comments are left out).
    :param zone: The name of the zone in the EMS objects.
    :raises ValueError: If the lines are not those of a program of the regimes of accim.
    """
    from accim.sim.ems import program_lines as pl
    from accim.sim.ems.setast import COOLING_SEASON_LINES

    program = f'{PROGRAM_PREFIX}{zone}'
    output = f'{OUTPUT_PREFIX}{zone}'.lower()
    lines = [str(line).strip() for line in lines if str(line).strip() and not str(line).strip().startswith('!')]
    lowered = [line.lower() for line in lines]

    def error(detail: str) -> ValueError:
        return ValueError(f'The program {program} is not a program of the regimes of the custom model of accim: '
                          f'{detail}.')

    def assignment(line: str) -> Optional[Tuple[str, str]]:
        match = _ASSIGNMENT.match(line)
        return (match.group(1).lower(), match.group(2)) if match else None

    index = 0
    if lines and assignment(lines[0]) == (output, '0'):
        index = 1
    for block in (COOLING_SEASON_LINES, pl.format_lines(pl.HVAC_OFF_FROM_COILS, zone=zone),
                  pl.format_lines(pl.HVAC_OFF_FROM_LOAD, zone=zone)):
        if lowered[index:index + len(block)] == [line.lower() for line in block]:
            index += len(block)
    size = len(REGIME_INPUTS) + 1

    def regime_at(start: int, condition: Any, number: int) -> CustomRegime:
        values = {}
        for line in lines[start:start + size]:
            found = assignment(line)
            if found is None:
                raise error(f'{line!r} is not a line of a regime')
            values[found[0]] = found[1]
        missing = [variable for variable in [*REGIME_INPUTS.values(), output] if variable.lower() not in values]
        if missing:
            raise error(f'the regime {number} does not set {missing}')
        if _value(values[output]) != number:
            raise error(f'the regime {number} sets {output} = {values[output]}')
        return CustomRegime(**{field: _value(values[variable.lower()]) for field, variable in REGIME_INPUTS.items()},
                            condition=condition)

    regimes = []
    closed = True
    if index < len(lines) and not lowered[index].startswith('if '):
        regimes.append(regime_at(index, 'always', 1))
        index += size
    else:
        closed = False
        while index < len(lines):
            keyword, _, rest = lines[index].partition(' ')
            keyword = keyword.lower()
            if keyword == 'endif' and regimes:
                index += 1
                closed = True
                break
            number = len(regimes) + 1
            if (keyword, number == 1) in (('if', True), ('elseif', False)):
                try:
                    condition = _parse_condition(rest.strip())
                except ValueError as exception:
                    raise error(str(exception)) from None
            elif keyword == 'else' and number > 1 and not rest.strip():
                condition = 'always'
            else:
                raise error(f'{lines[index]!r} is not a condition of a regime')
            regimes.append(regime_at(index + 1, condition, number))
            index += 1 + size
    if not regimes or not closed or index != len(lines):
        raise error('it has no regimes, no endif, or lines after them')
    try:
        return check_custom_regimes(regimes)
    except ValueError as exception:
        raise error(str(exception)) from None


def has_custom_regimes(idf) -> bool:
    """True if a zone of the model has the program of the regimes of the custom model."""
    return any(p.Name.upper().startswith(PROGRAM_PREFIX.upper())
               for p in idf.idfobjects['EnergyManagementSystem:Program'])


def custom_regimes_of(idf) -> Dict[str, Tuple[CustomRegime, ...]]:
    """The regimes of the custom model of each zone of a model that has them, by the name of the zone in the EMS
    objects (read from its program SelectCustomRegime_<zone>, see :func:`parse_regime_program`)."""
    prefix = PROGRAM_PREFIX.upper()
    return {program.Name[len(prefix):]: parse_regime_program(_program_lines(program), program.Name[len(prefix):])
            for program in idf.idfobjects['EnergyManagementSystem:Program'] if program.Name.upper().startswith(prefix)}


def _declared(idf) -> set:
    return {str(name).strip().upper() for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
            for name in g.fieldvalues[1:] if str(name).strip()}


def _frequencies(idf, zone: str) -> List[str]:
    """The frequencies of the Output:Variable objects of the comfort temperature of a zone (or of the model)."""
    names = {f'COMFORT TEMPERATURE_{zone}'.upper(), 'COMFORT TEMPERATURE'}
    frequencies = []
    for output in idf.idfobjects['Output:Variable']:
        if str(output.Variable_Name).upper() in names and output.Reporting_Frequency not in frequencies:
            frequencies.append(output.Reporting_Frequency)
    return frequencies


def _remove_zone(idf, zone: str) -> None:
    """Remove the regimes of a zone: its program, the line that runs it, its global variable and its outputs."""
    from accim.sim.ems.inputs import RUN_PROGRAM_PREFIX
    from accim.sim.ems.programs import set_program_lines

    name, output = f'{PROGRAM_PREFIX}{zone}', f'{OUTPUT_PREFIX}{zone}'
    program = idf.getobject('EnergyManagementSystem:Program', name)
    if program is not None:
        idf.removeidfobject(program)
    run_program = idf.getobject('EnergyManagementSystem:Program', f'{RUN_PROGRAM_PREFIX}{zone}')
    if run_program is not None:
        lines = _program_lines(run_program)
        kept = [line for line in lines if line.lower() != f'run {name}'.lower()]
        if kept != lines:
            set_program_lines(run_program, kept)
    for variable in [g for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
                     if [str(v).strip().upper() for v in g.fieldvalues[1:] if str(v).strip()] == [output.upper()]]:
        idf.removeidfobject(variable)
    for object_type, field in (('EnergyManagementSystem:OutputVariable', 'Name'), ('Output:Variable', 'Variable_Name')):
        for obj in [o for o in idf.idfobjects[object_type] if str(getattr(o, field)).upper() == output.upper()]:
            idf.removeidfobject(obj)


def set_zone_custom_regimes(idf, zone: str, regimes: Any) -> None:
    """Write the regimes of the custom model of a zone of a model with the ACCIS of accim 1.0.0 or later (programs
    SetInputData_<zone>), or remove them (with no regimes): the program SelectCustomRegime_<zone>, the line that runs it
    in RunACCIS_<zone> (right before ``run SetAppLimits``), the EMS global variable and output variable
    ``CustomRegime_<zone>``, and its Output:Variable objects, at the frequencies of those of the comfort temperature of
    the zone. The conditions of the outdoor metric compare Tout_metric in the models with the EMS code of the outdoor
    metric of the custom model, and PMOT otherwise.

    :param idf: The model (eppy).
    :param zone: The name of the zone in the EMS objects.
    :param regimes: The regimes (:class:`accim.sim.arguments.CustomRegime`), or None (or an empty list) for none.
    :raises ValueError: If the regimes are not valid, a regime has the condition 'hvac_off' or 'hvac_on' and the zone
        is not in mixed mode, or RunACCIS_<zone> does not run SetAppLimits.
    """
    from accim.sim.ems import program_lines as pl
    from accim.sim.ems.inputs import RUN_PROGRAM_PREFIX
    from accim.sim.ems.outdoor_metric import has_outdoor_metric_code
    from accim.sim.ems.programs import add_program, set_program_lines

    regimes = check_custom_regimes(regimes)
    if not regimes:
        _remove_zone(idf, zone)
        return
    hvac_lines = hvac_off_lines(idf, zone) if uses_hvac_conditions(regimes) else None
    metric = pl.OUTDOOR_METRIC_VARIABLE if has_outdoor_metric_code(idf) else 'PMOT'
    lines = regime_program_lines(zone, regimes, metric, hvac_lines)
    name, output = f'{PROGRAM_PREFIX}{zone}', f'{OUTPUT_PREFIX}{zone}'
    run_program = idf.getobject('EnergyManagementSystem:Program', f'{RUN_PROGRAM_PREFIX}{zone}')
    if run_program is not None:
        run_lines = _program_lines(run_program)
        if f'run {name}'.lower() not in [line.lower() for line in run_lines]:
            index = next((n for n, line in enumerate(run_lines) if line.lower() == _RUN_BEFORE.lower()), None)
            if index is None:
                raise ValueError(f'The program {RUN_PROGRAM_PREFIX}{zone} does not run SetAppLimits.')
            set_program_lines(run_program, run_lines[:index] + [f'run {name}'] + run_lines[index:])
    program = idf.getobject('EnergyManagementSystem:Program', name)
    if program is None:
        add_program(idf, name, lines)
    elif _program_lines(program) != lines:
        set_program_lines(program, lines)
    if output.upper() not in _declared(idf):
        idf.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name=output)
    if idf.getobject('EnergyManagementSystem:OutputVariable', output) is None:
        idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=output, EMS_Variable_Name=output,
                         Type_of_Data_in_Variable='Averaged', Update_Frequency='ZoneTimestep',
                         EMS_Program_or_Subroutine_Name='', Units='')
    requested = {str(o.Reporting_Frequency).upper() for o in idf.idfobjects['Output:Variable']
                 if str(o.Variable_Name).upper() == output.upper()}
    for frequency in _frequencies(idf, zone):
        if str(frequency).upper() not in requested:
            idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=output, Reporting_Frequency=frequency,
                             Schedule_Name='')


def set_custom_regimes(idf, regimes: Any) -> None:
    """Write the regimes of the custom model in the zones of a model with the ACCIS of accim 1.0.0 or later whose
    comfort standard is the custom model (99), and remove them from the other zones (see
    :func:`set_zone_custom_regimes`); with no regimes, remove them from all the zones, so that the model is as without
    them.

    :param idf: The model (eppy).
    :param regimes: The regimes (:class:`accim.sim.arguments.CustomRegime`), in their order of priority, or None (or an
        empty list) for none.
    :raises ValueError: As :func:`set_zone_custom_regimes`.
    """
    from accim.sim.ems.inputs import input_programs, read_inputs

    regimes = check_custom_regimes(regimes)
    if not regimes and not has_custom_regimes(idf):
        return
    for zone, program in input_programs(idf).items():
        comfort_standard = read_inputs(program).get('ComfStand')
        custom = isinstance(comfort_standard, (int, float)) and comfort_standard == _CUSTOM_COMFORT_STANDARD
        set_zone_custom_regimes(idf, zone, regimes if custom else ())
