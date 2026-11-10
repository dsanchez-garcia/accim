# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The minimum heating setpoint and the maximum cooling setpoint of the ACCIS, and the occupied hours below
some temperatures (proposal B5).

EN 16798-1:2019, Annex B: Table B.2 (B.2.1) gives the default design values of the indoor operative temperature of the
buildings with mechanical cooling systems (the minimum for heating, in winter, and the maximum for cooling, in summer,
:data:`accim.constants.EN16798_TABLE_B2`), and B.2.2 applies them in winter also to the buildings without mechanical
cooling systems, whose adaptive limits (Figure B.1) apply in summer and the mid-seasons. In accim, the applicability
limits change the equation of the setpoints (comfort modes 1, 2 and 3), but they do not bound them.

- ``heating_setpoint_minimum`` and ``cooling_setpoint_maximum`` (the inputs ``AHSTmin`` and ``ACSTmax`` of the program
  SetInputData_<zone>): the program ``ApplySetpointLimits_<zone>``, which RunACCIS_<zone> runs right after SetASTnoTol
  (so after SetAST, and after the program that gives the setpoints of a hook of the API backend to the zone,
  :mod:`accim.sim.ems.hook_setpoints`, if it has one), sets the heating setpoint AHST to AHSTmin if it is lower, and
  the cooling setpoint ACST to ACSTmax if it is higher, and then rounds them again as the subprograms of SetAST do
  (:data:`accim.sim.ems.setpoint_lines.ROUNDING`, with SetpointAcc): the setpoints of the thermostats are those of
  bounding AHST and ACST before their rounding, whatever the comfort standard and the comfort mode are, as the
  proposal designs it. The rounding is strict (the cooling setpoint downwards and the heating setpoint upwards), so
  the program sets the rounded setpoints to the maximum and the minimum when they bound them: otherwise, the cooling
  setpoint would be one step of SetpointAcc below the maximum (25.9999 °C with a maximum of 26 °C and the default
  accuracy, 10000: finding B5-2 of the review of 1.2.0), and the heating setpoint one step above a minimum whose product
  by SetpointAcc is not exact in binary (19.11 °C with a minimum of 19.1 °C and an accuracy of 100). The minimum and the
  maximum also bound the setpoints without the tolerance
  (AHSTnoTol and ACSTnoTol, the limits of the comfort band with which the hour counters of the ACCIS, the long-term
  discomfort and the hours below some temperatures count; finding B5-1): the minimum is a limit of the setpoint without
  the tolerance, so a heating setpoint without the tolerance of AHSTmin − AHSTtol (0.1 K below the minimum with the
  default tolerance) becomes AHSTmin: AHSTnoTol = max(AHST − AHSTtol, AHSTmin) and ACSTnoTol = min(ACST −
  ACSTtol, ACSTmax), with the setpoints AHST and ACST of SetAST, while the thermostats get max(AHST, AHSTmin) and
  min(ACST, ACSTmax), rounded (so, where the minimum or the maximum bounds them, the setpoints with and without the
  tolerance are the same). The ventilation setpoint (SetVST, in mixed mode) follows the minimum and maximum only where
  it comes from the rounded setpoints (``(roundedACST+roundedAHST)/2+VSToffset``, ``roundedAHST+VSToffset``, and
  MinOutTemp, ``roundedAHST - MinOToffset``): within the applicability limits, most comfort standards set it to the
  comfort temperature plus VSToffset (``ComfTemp+VSToffset``), and ESP CTE from 7 to 15 h to 22.5 °C plus VSToffset,
  which the minimum and the maximum do not bound (finding B5-3). The minimum only bounds the heating
  setpoint and the maximum the cooling setpoint: with a minimum above the cooling setpoint of the comfort model (or a
  maximum below its heating setpoint), the heating setpoint is above the cooling setpoint; a minimum not lower than the
  maximum raises a ValueError, and :func:`warn_crossed_setpoint_limits` warns when the minimum is above the upper
  applicability limit of the cooling setpoint of the comfort standard of the zone (ACSTaul) or the maximum below the
  lower applicability limit of its heating setpoint (AHSTall), as verdict 13 of the review of 1.2.0 asks. Only the
  zones with a minimum or a maximum have the program and the inputs, so the output IDFs without them do not change.
  During the development of 1.2.0, the arguments were ``heating_setpoint_floor`` and ``cooling_setpoint_ceiling``
  (the inputs ``AHSTfloor`` and ``ACSTceil``), names that could be read as a physical floor (decision 8 of block F,
  task H1 of the review of 1.2.0): the old names of the arguments keep working with a DeprecationWarning
  (:data:`accim.sim.arguments.DEPRECATED_ARGUMENT_NAMES`), and the models with the old inputs must be made again.
- ``report_hours_below``: the occupied hours with the operative temperature below each of some temperatures, the EMS
  outputs ``HoursBelow_<T>_<zone>`` (the program ``CountHoursBelow_<zone>``, which RunACCIS_<zone> runs after
  CountHoursNoApp_<zone>): in each timestep, the length of the timestep if the zone has occupants and its operative
  temperature is below T, and 0 otherwise. As in the other hour counters of the ACCIS, the EMS reads at the beginning of
  the timestep the occupants of the timestep and the operative temperature of the previous one.

The setpoints based on the PMV (:mod:`accim.sim.pmv_index`) have neither minimum nor maximum (decision D5 of the brief
of 1.2.0): their thermostats have setpoints of the PMV, not of the temperature.
"""

import numbers
import warnings
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from accim.sim.ems.erl import format_number
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
    'warn_crossed_setpoint_limits',
    'zone_limits',
]

#: The inputs of the minimum heating setpoint and the maximum cooling setpoint (SetInputData_<zone>)
INPUTS = ('AHSTmin', 'ACSTmax')
#: The program of the setpoint limits of each zone is this prefix and the name of the zone
PROGRAM_PREFIX = 'ApplySetpointLimits_'
#: The program of the hours below some temperatures of each zone
HOURS_BELOW_PROGRAM_PREFIX = 'CountHoursBelow_'
#: The EMS variables (and outputs) of the hours below a temperature T of a zone are HoursBelow_<T>_<zone>
HOURS_BELOW_PREFIX = 'HoursBelow_'
_RUN_PREFIX = 'run '


def check_setpoint_limits(minimum: Any, maximum: Any, where: str = '') -> None:
    """Check a minimum heating setpoint and a maximum cooling setpoint: numbers (in °C) or None, and the
    minimum lower than the maximum.

    :param where: The zone, for the messages.
    :raises ValueError: If they are not valid.
    """
    suffix = f' (zone {where!r})' if where else ''
    for name, value in (('heating_setpoint_minimum', minimum), ('cooling_setpoint_maximum', maximum)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, numbers.Real)):
            raise ValueError(f'{name} must be a number (°C) or None{suffix}, not {value!r}.')
    if minimum is not None and maximum is not None and not minimum < maximum:
        raise ValueError(f'heating_setpoint_minimum ({minimum}) must be lower than cooling_setpoint_maximum '
                         f'({maximum}){suffix}.')


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


def limit_program_lines(minimum: bool, maximum: bool) -> List[str]:
    """The lines of the program ApplySetpointLimits_<zone> (run after SetASTnoTol): the minimum heating setpoint
    and the maximum cooling setpoint (those of the zone) on the setpoints with the tolerance, which the
    thermostats get, the rounding of the setpoints, the minimum and the maximum as the rounded setpoints when they
    bound them (the rounding is strict, so the maximum would otherwise be one step of SetpointAcc below it, and a
    minimum whose product by SetpointAcc is not exact in binary, such as 19.1 °C with an accuracy of 100, one step
    above it: finding B5-2 of the review of 1.2.0), and the minimum and the maximum on the setpoints without the
    tolerance too (the comfort band of the hour counters: finding B5-1)."""
    lines: List[str] = []
    if minimum:
        lines += ['if AHST < AHSTmin', 'set AHST = AHSTmin', 'endif']
    if maximum:
        lines += ['if ACST > ACSTmax', 'set ACST = ACSTmax', 'endif']
    lines += list(ROUNDING)
    if minimum:
        lines += ['if AHST <= AHSTmin', 'set roundedAHST = AHSTmin', 'endif']
    if maximum:
        lines += ['if ACST >= ACSTmax', 'set roundedACST = ACSTmax', 'endif']
    if minimum:
        lines += ['if AHSTnoTol < AHSTmin', 'set AHSTnoTol = AHSTmin', 'endif']
    if maximum:
        lines += ['if ACSTnoTol > ACSTmax', 'set ACSTnoTol = ACSTmax', 'endif']
    return lines


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
    return format_number(value)


def _program_lines(program) -> List[str]:
    return [str(value).strip() for value in program.fieldvalues[2:]]


def _insert_run_line(idf, zone: str, line: str, after: str, move: bool = False) -> None:
    """Make RunACCIS_<zone> run a program right after another one (that it runs); with ``move``, a line that it
    has somewhere else is moved there."""
    from accim.sim.ems.inputs import RUN_PROGRAM_PREFIX
    from accim.sim.ems.programs import set_program_lines

    run_program = idf.getobject('EnergyManagementSystem:Program', f'{RUN_PROGRAM_PREFIX}{zone}')
    if run_program is None:
        return
    lines = _program_lines(run_program)
    if line in lines:
        position = lines.index(line)
        if not move or (position and lines[position - 1].lower() == after.lower()):
            return
        lines = [existing for existing in lines if existing != line]
    index = next((n + 1 for n, existing in enumerate(lines) if existing.lower() == after.lower()), None)
    if index is None:
        raise ValueError(f'The program {RUN_PROGRAM_PREFIX}{zone} does not run {after.split(" ", 1)[1]}.')
    set_program_lines(run_program, lines[:index] + [line] + lines[index:])


def _after_setpoints(idf, zone: str) -> str:
    """The line of RunACCIS_<zone> after which ApplySetpointLimits_<zone> runs: that of SetASTnoTol, which runs after
    SetAST and after the program that gives the setpoints of a hook to the zone (:mod:`accim.sim.ems.hook_setpoints`,
    if it has one), so that the minimum and maximum also bound the setpoints of the hook and those without the
    tolerance."""
    return 'run SetASTnoTol'


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
    """True if a zone of the model has a minimum heating setpoint or a maximum cooling setpoint."""
    return any(p.Name.upper().startswith(PROGRAM_PREFIX.upper())
               for p in idf.idfobjects['EnergyManagementSystem:Program'])


def set_setpoint_limits_code(idf) -> None:
    """Write the programs ApplySetpointLimits_<zone> of the zones of a model (of accim 1.0.0 or later) with the inputs
    ``AHSTmin`` or ``ACSTmax`` in their programs SetInputData_<zone>, with the lines of the inputs that they have
    (and the line that runs them in RunACCIS_<zone>, right after SetASTnoTol), and remove those of the other zones; the
    EMS global variables AHSTmin and ACSTmax are declared if a zone has them."""
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.programs import add_program, set_program_lines

    any_limits = False
    for zone, program in input_programs(idf).items():
        inputs = read_inputs(program)
        minimum, maximum = (name in inputs for name in INPUTS)
        name = f'{PROGRAM_PREFIX}{zone}'
        run_line = f'{_RUN_PREFIX}{name}'
        existing = idf.getobject('EnergyManagementSystem:Program', name)
        if minimum or maximum:
            any_limits = True
            lines = limit_program_lines(minimum, maximum)
            if existing is None:
                add_program(idf, name, lines)
            elif _program_lines(existing) != lines:
                set_program_lines(existing, lines)
            # The programs of the limits of accim 1.2.0 before its finding B5-1 ran right after SetAST
            _insert_run_line(idf, zone, run_line, _after_setpoints(idf, zone), move=True)
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
    """The minimum and maximum of each zone of a model: ``{zone: {'AHSTmin': ..., 'ACSTmax': ...}}`` (None if the
    zone has none)."""
    from accim.sim.ems.inputs import input_programs, read_inputs

    return {zone: {name: read_inputs(program).get(name) for name in INPUTS}
            for zone, program in input_programs(idf).items()}


def _applicability_limits(idf, program) -> Tuple[Optional[float], Optional[float]]:
    """The upper applicability limit of the cooling setpoint (ACSTaul) and the lower one of the heating setpoint
    (AHSTall) of the comfort standard of a zone: its program SetInputData_<zone> and the program SetAppLimits of the
    model run with the Erl interpreter of accim (:mod:`accim.sim.ems.erl`); None if they do not set them."""
    from accim.sim.ems.erl import ErlProgramSet, variables_in_programs

    app_limits = idf.getobject('EnergyManagementSystem:Program', 'SetAppLimits')
    if app_limits is None:
        return None, None
    programs = {'SetInputData': _program_lines(program), 'SetAppLimits': _program_lines(app_limits)}
    try:
        erl = ErlProgramSet(programs, global_variables=set().union(*variables_in_programs(programs).values()))
        erl.run('SetInputData')
        erl.run('SetAppLimits')
    except Exception:  # The warning is not given if the programs cannot run on their own
        return None, None
    return erl.get('ACSTaul'), erl.get('AHSTall')


def warn_crossed_setpoint_limits(idf) -> List[str]:
    """Warn about the zones of a model whose minimum heating setpoint is above the upper applicability limit of
    the cooling setpoint of their comfort standard (ACSTaul), or whose maximum cooling setpoint is below the
    lower applicability limit of their heating setpoint (AHSTall), as verdict 13 of the review of accim 1.2.0 asks
    (``notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md``, section 5): the minimum only bounds the heating setpoint and the
    maximum the cooling setpoint, so the heating setpoint can then be above the cooling setpoint, with which EnergyPlus
    gives warnings and meaningless results. The limits are those of the program SetAppLimits of the model for the
    inputs of the zone (its comfort standard and category); a minimum not lower than the maximum is a ValueError
    (:func:`check_setpoint_limits`).

    :return: The messages, which are also given as warnings.
    """
    from accim.sim.ems.inputs import input_programs, read_inputs

    messages = []
    for zone, program in input_programs(idf).items():
        minimum, maximum = (read_inputs(program).get(name) for name in INPUTS)
        if minimum is None and maximum is None:
            continue
        upper, lower = _applicability_limits(idf, program)
        if minimum is not None and upper is not None and minimum > upper:
            messages.append(f'The minimum heating setpoint of the zone {zone} ({_number(minimum)} °C) is above the '
                            f'upper applicability limit of the cooling setpoint of its comfort standard (ACSTaul, '
                            f'{_number(upper)} °C): its heating setpoint can be above its cooling setpoint.')
        if maximum is not None and lower is not None and maximum < lower:
            messages.append(f'The maximum cooling setpoint of the zone {zone} ({_number(maximum)} °C) is below '
                            f'the lower applicability limit of the heating setpoint of its comfort standard (AHSTall, '
                            f'{_number(lower)} °C): its cooling setpoint can be below its heating setpoint.')
    for message in messages:
        warnings.warn(message, stacklevel=2)
    return messages
