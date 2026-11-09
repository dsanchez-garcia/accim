# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The floor of the heating setpoint and the ceiling of the cooling setpoint of the ACCIS, and the occupied hours below
some temperatures (proposal B5).

EN 16798-1:2019, Annex B: Table B.2 (B.2.1) gives the default design values of the indoor operative temperature of the
buildings with mechanical cooling systems (the minimum for heating, in winter, and the maximum for cooling, in summer,
:data:`accim.constants.EN16798_TABLE_B2`), and B.2.2 applies them in winter also to the buildings without mechanical
cooling systems, whose adaptive limits (Figure B.1) apply in summer and the mid-seasons. In accim, the applicability
limits change the equation of the setpoints (comfort modes 1, 2 and 3), but they do not bound them.

- ``heating_setpoint_floor`` and ``cooling_setpoint_ceiling`` (the inputs ``AHSTfloor`` and ``ACSTceil`` of the program
  SetInputData_<zone>): the program ``ApplySetpointLimits_<zone>``, which RunACCIS_<zone> runs right after SetAST, sets
  the heating setpoint AHST to AHSTfloor if it is lower, and the cooling setpoint ACST to ACSTceil if it is higher, and
  then rounds them again as the subprograms of SetAST do (:data:`accim.sim.ems.setpoint_lines.ROUNDING`, with
  SetpointAcc): the setpoints are those of bounding AHST and ACST before their rounding, whatever the comfort standard
  and the comfort mode are, as the proposal designs it. The rounding of the cooling setpoint is downwards and strict,
  so a cooling setpoint bounded by the ceiling is one step of SetpointAcc below it (25.9999 °C with a ceiling of 26 °C
  and the default accuracy, 10000), and a heating setpoint bounded by the floor is the floor. The setpoints without the
  tolerance (SetASTnoTol, which runs after it) and those of the ventilation (SetVST) come from the bounded setpoints.
  The floor only bounds the heating setpoint and the ceiling the cooling setpoint: with a floor above the cooling
  setpoint of the comfort model (or a ceiling below its heating setpoint), the heating setpoint is above the cooling
  setpoint. Only the zones with a floor or a ceiling have the program and the inputs, so the output IDFs without them
  do not change.
- ``report_hours_below``: the occupied hours with the operative temperature below each of some temperatures, the EMS
  outputs ``HoursBelow_<T>_<zone>`` (the program ``CountHoursBelow_<zone>``, which RunACCIS_<zone> runs after
  CountHoursNoApp_<zone>): in each timestep, the length of the timestep if the zone has occupants and its operative
  temperature is below T, and 0 otherwise. As in the other hour counters of the ACCIS, the EMS reads at the beginning of
  the timestep the occupants of the timestep and the operative temperature of the previous one.

The setpoints based on the PMV (:mod:`accim.sim.pmv_index`) have neither floor nor ceiling (decision D5 of the brief of
1.2.0): their thermostats have setpoints of the PMV, not of the temperature.
"""

import numbers
from typing import Any, Dict, Iterable, List, Optional, Sequence

from accim.sim.ems.setpoint_lines import ROUNDING

__all__ = [
    'HOURS_BELOW_PREFIX',
    'HOURS_BELOW_PROGRAM_PREFIX',
    'INPUTS',
    'PROGRAM_PREFIX',
    'check_hours_below',
    'check_setpoint_limits',
    'has_setpoint_limits',
    'hours_below_lines',
    'hours_below_variable',
    'limit_program_lines',
    'set_hours_below_code',
    'set_setpoint_limits_code',
    'zone_limits',
]

#: The inputs of the floor of the heating setpoint and the ceiling of the cooling setpoint (SetInputData_<zone>)
INPUTS = ('AHSTfloor', 'ACSTceil')
#: The program of the setpoint limits of each zone is this prefix and the name of the zone
PROGRAM_PREFIX = 'ApplySetpointLimits_'
#: The program of the hours below some temperatures of each zone
HOURS_BELOW_PROGRAM_PREFIX = 'CountHoursBelow_'
#: The EMS variables (and outputs) of the hours below a temperature T of a zone are HoursBelow_<T>_<zone>
HOURS_BELOW_PREFIX = 'HoursBelow_'
_RUN_PREFIX = 'run '


def check_setpoint_limits(floor: Any, ceiling: Any, where: str = '') -> None:
    """Check a floor of the heating setpoint and a ceiling of the cooling setpoint: numbers (in °C) or None, and the
    floor lower than the ceiling.

    :param where: The zone, for the messages.
    :raises ValueError: If they are not valid.
    """
    suffix = f' (zone {where!r})' if where else ''
    for name, value in (('heating_setpoint_floor', floor), ('cooling_setpoint_ceiling', ceiling)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, numbers.Real)):
            raise ValueError(f'{name} must be a number (°C) or None{suffix}, not {value!r}.')
    if floor is not None and ceiling is not None and not floor < ceiling:
        raise ValueError(f'heating_setpoint_floor ({floor}) must be lower than cooling_setpoint_ceiling '
                         f'({ceiling}){suffix}.')


def check_hours_below(thresholds: Any) -> List[float]:
    """Check the temperatures of ``report_hours_below``: a list of different numbers (°C), or None (or an empty list)
    for none.

    :return: The temperatures (an empty list for none).
    :raises ValueError: If they are not valid.
    """
    if thresholds is None:
        return []
    if isinstance(thresholds, numbers.Real) and not isinstance(thresholds, bool):
        thresholds = [thresholds]
    values = list(thresholds) if isinstance(thresholds, (list, tuple, set)) else None
    if values is None or any(isinstance(v, bool) or not isinstance(v, numbers.Real) for v in values):
        raise ValueError(f'report_hours_below must be a list of temperatures (°C), such as [18, 17, 16], or None, '
                         f'not {thresholds!r}.')
    names = [hours_below_variable(value, '') for value in values]
    if len(set(names)) != len(names):
        raise ValueError(f'report_hours_below has repeated temperatures: {values}.')
    return values


def hours_below_variable(threshold: float, zone: str) -> str:
    """The EMS variable (and output) of the occupied hours of a zone below a temperature: ``HoursBelow_18_<zone>``,
    and ``HoursBelow_17p5_<zone>`` for 17.5 (the names of the EMS cannot have dots)."""
    if float(threshold) == int(threshold):
        text = str(int(threshold))
    else:
        text = repr(float(threshold)).replace('.', 'p')
    return f"{HOURS_BELOW_PREFIX}{text.replace('-', 'm')}_{zone}"


def limit_program_lines(floor: bool, ceiling: bool) -> List[str]:
    """The lines of the program ApplySetpointLimits_<zone>: the floor of the heating setpoint and the ceiling of the
    cooling setpoint (those of the zone), and the rounding of the setpoints."""
    lines: List[str] = []
    if floor:
        lines += ['if AHST < AHSTfloor', 'set AHST = AHSTfloor', 'endif']
    if ceiling:
        lines += ['if ACST > ACSTceil', 'set ACST = ACSTceil', 'endif']
    return lines + list(ROUNDING)


def hours_below_lines(zone: str, thresholds: Sequence[float]) -> List[str]:
    """The lines of the program CountHoursBelow_<zone>: the occupied hours below each temperature."""
    names = [(threshold, hours_below_variable(threshold, zone)) for threshold in thresholds]
    lines = [f'if Occ_count_{zone} > 0']
    for threshold, name in names:
        lines += [f'if {zone}_OpT < {_number(threshold)}', f'set {name} = 1*ZoneTimeStep', 'else', f'set {name} = 0',
                  'endif']
    lines.append('else')
    lines += [f'set {name} = 0' for _, name in names]
    lines.append('endif')
    return lines


def _number(value: float) -> str:
    return str(int(value)) if float(value) == int(value) else repr(float(value))


def _program_lines(program) -> List[str]:
    return [str(value).strip() for value in program.fieldvalues[2:]]


def _insert_run_line(idf, zone: str, line: str, after: str) -> None:
    """Make RunACCIS_<zone> run a program right after another one (that it runs)."""
    from accim.sim.ems.inputs import RUN_PROGRAM_PREFIX
    from accim.sim.ems.programs import set_program_lines

    run_program = idf.getobject('EnergyManagementSystem:Program', f'{RUN_PROGRAM_PREFIX}{zone}')
    if run_program is None:
        return
    lines = _program_lines(run_program)
    if line in lines:
        return
    index = next((n + 1 for n, existing in enumerate(lines) if existing.lower() == after.lower()), None)
    if index is None:
        raise ValueError(f'The program {RUN_PROGRAM_PREFIX}{zone} does not run {after.split(" ", 1)[1]}.')
    set_program_lines(run_program, lines[:index] + [line] + lines[index:])


def _remove_run_line(idf, zone: str, line: str) -> None:
    from accim.sim.ems.inputs import RUN_PROGRAM_PREFIX
    from accim.sim.ems.programs import set_program_lines

    run_program = idf.getobject('EnergyManagementSystem:Program', f'{RUN_PROGRAM_PREFIX}{zone}')
    if run_program is not None:
        lines = _program_lines(run_program)
        if line in lines:
            set_program_lines(run_program, [existing for existing in lines if existing != line])


def _declared(idf) -> set:
    return {str(name).strip().upper() for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
            for name in g.fieldvalues[1:] if str(name).strip()}


def has_setpoint_limits(idf) -> bool:
    """True if a zone of the model has a floor of the heating setpoint or a ceiling of the cooling setpoint."""
    return any(p.Name.upper().startswith(PROGRAM_PREFIX.upper())
               for p in idf.idfobjects['EnergyManagementSystem:Program'])


def set_setpoint_limits_code(idf) -> None:
    """Write the programs ApplySetpointLimits_<zone> of the zones of a model (of accim 1.0.0 or later) with the inputs
    ``AHSTfloor`` or ``ACSTceil`` in their programs SetInputData_<zone>, with the lines of the inputs that they have
    (and the line that runs them in RunACCIS_<zone>, after SetAST), and remove those of the other zones; the EMS global
    variables AHSTfloor and ACSTceil are declared if a zone has them."""
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.programs import add_program, set_program_lines

    any_limits = False
    for zone, program in input_programs(idf).items():
        inputs = read_inputs(program)
        floor, ceiling = (name in inputs for name in INPUTS)
        name = f'{PROGRAM_PREFIX}{zone}'
        run_line = f'{_RUN_PREFIX}{name}'
        existing = idf.getobject('EnergyManagementSystem:Program', name)
        if floor or ceiling:
            any_limits = True
            lines = limit_program_lines(floor, ceiling)
            if existing is None:
                add_program(idf, name, lines)
            elif _program_lines(existing) != lines:
                set_program_lines(existing, lines)
            _insert_run_line(idf, zone, run_line, 'run SetAST')
        else:
            if existing is not None:
                idf.removeidfobject(existing)
            _remove_run_line(idf, zone, run_line)
    variables = [g for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
                 if [str(v).strip() for v in g.fieldvalues[1:] if str(v).strip()] == list(INPUTS)]
    if any_limits and not variables and not set(INPUTS) <= _declared(idf):
        idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                         **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(INPUTS, start=1)})
    elif not any_limits:
        for variable in variables:
            idf.removeidfobject(variable)


def set_hours_below_code(idf, thresholds: Iterable[float], frequencies: Sequence[str] = ()) -> None:
    """Add to a model with the ACCIS (of accim 1.0.0 or later) the occupied hours of each zone below some temperatures
    (``report_hours_below``): the program CountHoursBelow_<zone> (run by RunACCIS_<zone> after CountHoursNoApp_<zone>),
    the EMS global variables and the EMS output variables ``HoursBelow_<T>_<zone>`` (summed, in hours), with
    Output:Variable objects at the frequencies given. Without temperatures, nothing is added.

    :param thresholds: The temperatures (°C).
    :param frequencies: The reporting frequencies of their Output:Variable objects ('Hourly'...); none by default (the
        standard outputs of AddAccis add those of all the EMS output variables).
    :raises ValueError: If the temperatures are not valid, or the model has them already.
    """
    from accim.sim.ems.inputs import input_programs
    from accim.sim.ems.programs import add_program

    thresholds = check_hours_below(list(thresholds))
    if not thresholds:
        return
    zones = list(input_programs(idf))
    if any(idf.getobject('EnergyManagementSystem:Program', f'{HOURS_BELOW_PROGRAM_PREFIX}{zone}') is not None
           for zone in zones):
        raise ValueError('The model already has the hours below some temperatures (programs CountHoursBelow_<zone>).')
    declared = _declared(idf)
    for zone in zones:
        names = [hours_below_variable(threshold, zone) for threshold in thresholds]
        add_program(idf, f'{HOURS_BELOW_PROGRAM_PREFIX}{zone}', hours_below_lines(zone, thresholds))
        _insert_run_line(idf, zone, f'{_RUN_PREFIX}{HOURS_BELOW_PROGRAM_PREFIX}{zone}', f'run CountHoursNoApp_{zone}')
        new = [name for name in names if name.upper() not in declared]
        if new:
            idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                             **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(new, start=1)})
        for name in names:
            idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=name,
                             Type_of_Data_in_Variable='Summed', Update_Frequency='ZoneTimestep', Units='H')
            for frequency in frequencies:
                idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name,
                                 Reporting_Frequency=frequency, Schedule_Name='')


def zone_limits(idf) -> Dict[str, Dict[str, Optional[float]]]:
    """The floor and ceiling of each zone of a model: ``{zone: {'AHSTfloor': ..., 'ACSTceil': ...}}`` (None if the
    zone has none)."""
    from accim.sim.ems.inputs import input_programs, read_inputs

    return {zone: {name: read_inputs(program).get(name) for name in INPUTS}
            for zone, program in input_programs(idf).items()}
