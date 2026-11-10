# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The limiter of the drift of the setpoints by the indoor thermal history (task F2 of block F of accim 1.2.0,
``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, sections 4 and 6).

Parkinson, de Dear & Brager (2020), *Nudging the adaptive thermal comfort model*, Energy and Buildings 206, 109559:
the occupants adapt to the mean indoor temperature they are exposed to (Fig. 6), and the changes of the setpoints
should be spread over days to weeks (section 4.3.2). The limiter, an option of the ACCIS for each zone, limits the
setpoints of the comfort standard of the zone (adaptive, static, or those of a hook of the API backend, such as those
of the SET of comfort standard 24), with the decisions of the author of 2026-11-10 (section 6 of the proposal of block
F, copied in ``notes/decisions.md``):

- ``drift_mode=None`` (the default): no limiter; the output IDFs and the results of every comfort standard are those of
  the ACCIS without it.
- ``drift_mode='rate'``: the setpoints of each day d are those of the comfort standard (the targets), within
  ``max_drift_rate`` (K/day, 0.5 by default) of the setpoints applied the day before, |setpoint(d) − applied(d − 1)| ≤
  max_drift_rate: on the first occupied day, the targets are applied without limit, and from then on the state is the
  setpoint applied at the end of the previous day (the heating and the cooling setpoint, each one).
- ``drift_mode='window'``: the targets are clipped to [T_rm_in − ``delta_heat``, T_rm_in + ``delta_cool``] (1.0 K
  each by default), where T_rm_in is the exponentially weighted daily running mean of the operative temperature of the
  zone in its occupied hours, T_rm_in(d) = (1 − alpha_indoor)·T_occ_mean(d − 1) + alpha_indoor·T_rm_in(d − 1)
  (``alpha_indoor`` 0.8 by default, as the running mean of EN 16798-1); the limiter is inactive until one full
  occupied day has been accumulated, and T_rm_in starts with the mean of that day, unless ``initial_T_rm_in`` gives
  its start (then the limiter is active from the first day). The days without occupied hours do not change T_rm_in.

The EMS calculates it without TrendVariable objects, so that the backend of the Python API also runs it: the program
``ApplyDriftLimiter_<zone>`` of each zone, which RunACCIS_<zone> runs right after the setpoints of the comfort standard
(SetAST) and of a hook (``ApplyHookSetpoints_<zone>``, if the zone has it), and before SetASTnoTol and the minimum and
maximum of the setpoints of B5 (:mod:`accim.sim.ems.setpoint_limits`), out of the warm-up days of EnergyPlus
(``WarmupFlag``): in each timestep, it adds the operative temperature of the zone (``<zone>_OpT``) to the accumulators
``sum_T_occ_<zone>`` and ``n_occ_<zone>`` if the zone has occupants (``Occ_count_<zone>``; as in the hour counters of
the ACCIS, the EMS reads at the beginning of the timestep its occupants and the operative temperature of the previous
timestep), and flushes them at the change of DayOfYear, when it updates T_rm_in and the state of the rate. The targets
are the setpoints without the tolerance (AHST − AHSTtol and ACST − ACSTtol); where the limiter changes them, it sets
AHST and ACST to the limited setpoints plus the tolerance and rounds them again
(:data:`accim.sim.ems.setpoint_lines.ROUNDING`), so the thermostats, the setpoints without the tolerance, the hour
counters and the outputs of the ACCIS follow them. The program ``InitDriftLimiter`` resets its variables at the
beginning of each environment. The outputs of each zone: ``T_rm_in_<zone>`` (°C), the targets
``DriftTargetAHST_<zone>`` and ``DriftTargetACST_<zone>`` and the setpoints applied by the limiter
``DriftAppliedAHST_<zone>`` and ``DriftAppliedACST_<zone>`` (°C, without the tolerance, before the minimum and maximum
of B5), averaged, and ``DriftLimitedHours_<zone>``, the occupied hours in which the limiter changed a setpoint (h,
summed).

The inputs of each zone (its program SetInputData_<zone>, only in the zones with the limiter, so the output IDFs
without it do not change): ``DriftMode`` (1, 'rate'; 2, 'window'; 0, none), ``MaxDriftRate``, ``AlphaIndoor``,
``DeltaCool``, ``DeltaHeat`` and, with ``initial_T_rm_in``, ``InitTrmIn``. The setpoints based on the PMV (the
thermostats of the PMV of :mod:`accim.sim.pmv_index`) have no limiter: their setpoints are not temperatures.
"""

import numbers
from typing import Any, Dict, List, Mapping, Optional

from accim.sim.ems.setpoint_lines import ROUNDING

__all__ = [
    'ARGUMENTS',
    'DEFAULTS',
    'DRIFT_MODES',
    'INIT_PROGRAM',
    'INPUTS',
    'OUTPUTS',
    'PROGRAM_PREFIX',
    'check_drift_arguments',
    'drift_inputs',
    'has_drift_limiter',
    'init_program_lines',
    'program_lines',
    'set_drift_limiter_code',
    'zone_outputs',
]

#: The modes of the limiter and their codes in the input DriftMode (0, none)
DRIFT_MODES = {'rate': 1, 'window': 2}
#: The arguments of the limiter (of AddAccis, modify_accis and zone_arguments), and their inputs
ARGUMENTS = ('drift_mode', 'max_drift_rate', 'alpha_indoor', 'delta_cool', 'delta_heat', 'initial_T_rm_in')
INPUTS = ('DriftMode', 'MaxDriftRate', 'AlphaIndoor', 'DeltaCool', 'DeltaHeat', 'InitTrmIn')
#: The defaults of the arguments of the limiter (decision 6 of the author of 2026-11-10)
DEFAULTS = {'drift_mode': None, 'max_drift_rate': 0.5, 'alpha_indoor': 0.8, 'delta_cool': 1.0, 'delta_heat': 1.0,
            'initial_T_rm_in': None}
#: The program of the limiter of each zone is this prefix and the name of the zone
PROGRAM_PREFIX = 'ApplyDriftLimiter_'
#: The program that resets the variables of the limiter at the beginning of each environment
INIT_PROGRAM = 'InitDriftLimiter'
#: The EMS output variables of each zone: prefix -> (units, type of data)
OUTPUTS = {
    'T_rm_in': ('C', 'Averaged'),
    'DriftTargetAHST': ('C', 'Averaged'),
    'DriftTargetACST': ('C', 'Averaged'),
    'DriftAppliedAHST': ('C', 'Averaged'),
    'DriftAppliedACST': ('C', 'Averaged'),
    'DriftLimitedHours': ('H', 'Summed'),
}
#: The other EMS global variables of each zone: the accumulators of the day, its DayOfYear, the number of occupied
#: days, and the setpoints applied in the last timestep and at the end of the previous day (the state of the rate)
_STATE = ('sum_T_occ', 'n_occ', 'DriftDay', 'DriftOccDays', 'DriftLastAHST', 'DriftLastACST', 'DriftRefAHST',
          'DriftRefACST')
_RUN_PREFIX = 'run '


def _number(name: str, value: Any, low: Optional[float] = None, high: Optional[float] = None,
            low_open: bool = False, high_open: bool = False, where: str = '') -> float:
    suffix = f' (zone {where!r})' if where else ''
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f'{name} must be a number{suffix}, not {value!r}.')
    below = low is not None and (value <= low if low_open else value < low)
    above = high is not None and (value >= high if high_open else value > high)
    if below or above:
        interval = f'{"(" if low_open else "["}{low}, {high}{")" if high_open else "]"}'
        raise ValueError(f'{name} must be in {interval}{suffix}, not {value!r}.')
    return float(value)


def check_drift_arguments(drift_mode: Any = None, max_drift_rate: Any = None, alpha_indoor: Any = None,
                          delta_cool: Any = None, delta_heat: Any = None, initial_T_rm_in: Any = None,  # noqa: N803
                          where: str = '') -> None:
    """Check the arguments of the limiter (those that are not None): ``drift_mode`` 'rate' or 'window';
    ``max_drift_rate`` greater than 0 (K/day); ``alpha_indoor`` from 0 to 1, 1 excluded; ``delta_cool`` and
    ``delta_heat`` 0 or more (K); ``initial_T_rm_in`` a number (°C).

    :param where: The zone, for the messages.
    :raises ValueError: If they are not valid.
    """
    if drift_mode is not None and drift_mode not in DRIFT_MODES:
        suffix = f' (zone {where!r})' if where else ''
        raise ValueError(f"drift_mode must be None, 'rate' or 'window'{suffix}, not {drift_mode!r}.")
    if max_drift_rate is not None:
        _number('max_drift_rate', max_drift_rate, 0, None, low_open=True, where=where)
    if alpha_indoor is not None:
        _number('alpha_indoor', alpha_indoor, 0, 1, high_open=True, where=where)
    for name, value in (('delta_cool', delta_cool), ('delta_heat', delta_heat)):
        if value is not None:
            _number(name, value, 0, None, where=where)
    if initial_T_rm_in is not None:
        _number('initial_T_rm_in', initial_T_rm_in, where=where)


def drift_inputs(arguments: Mapping[str, Any], current: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """The inputs of the limiter of a zone: none if it has no ``drift_mode`` (given in ``arguments``, or its input in
    ``current``, the inputs that the zone has); otherwise, those of the arguments given, or those of the zone, or the
    defaults (``InitTrmIn`` only with ``initial_T_rm_in``).

    :param arguments: The arguments of the zone (``{'drift_mode': 'rate', 'max_drift_rate': 0.3...}``; None is not
        given).
    :param current: The inputs that the zone has (:func:`accim.sim.ems.inputs.read_inputs`).
    """
    current = dict(current or {})
    mode = arguments.get('drift_mode')
    if mode is None and 'DriftMode' not in current:
        return {}
    values = {'DriftMode': DRIFT_MODES[mode] if mode is not None else current['DriftMode']}
    for argument, variable in zip(ARGUMENTS[1:], INPUTS[1:]):
        value = arguments.get(argument)
        if value is None:
            value = current.get(variable, DEFAULTS[argument])
        if value is not None:
            values[variable] = value
    return values


def zone_outputs(zone: str) -> List[str]:
    """The names of the outputs of the limiter of a zone."""
    return [f'{prefix}_{zone}' for prefix in OUTPUTS]


def program_lines(zone: str, initial: bool = False) -> List[str]:
    """The lines of the program ApplyDriftLimiter_<zone> (see the module).

    :param initial: True if the zone has ``initial_T_rm_in`` (the input InitTrmIn): the running mean starts with it, and
        the window is active from the first day.
    """
    z = zone
    lines = [
        f'set DriftTargetAHST_{z} = AHST-AHSTtol',
        f'set DriftTargetACST_{z} = ACST-ACSTtol',
        f'set DriftAppliedAHST_{z} = DriftTargetAHST_{z}',
        f'set DriftAppliedACST_{z} = DriftTargetACST_{z}',
        'if WarmupFlag == 0',
        f'if DayOfYear <> DriftDay_{z}',
        f'if DriftDay_{z} > 0',
        f'set DriftRefAHST_{z} = DriftLastAHST_{z}',
        f'set DriftRefACST_{z} = DriftLastACST_{z}',
        f'if n_occ_{z} > 0',
    ]
    if initial:
        lines += [f'set T_rm_in_{z} = (1-AlphaIndoor)*sum_T_occ_{z}/n_occ_{z}+AlphaIndoor*T_rm_in_{z}']
    else:
        lines += [f'if DriftOccDays_{z} == 0', f'set T_rm_in_{z} = sum_T_occ_{z}/n_occ_{z}', 'else',
                  f'set T_rm_in_{z} = (1-AlphaIndoor)*sum_T_occ_{z}/n_occ_{z}+AlphaIndoor*T_rm_in_{z}', 'endif']
    lines += [f'set DriftOccDays_{z} = DriftOccDays_{z}+1', 'endif']
    if initial:
        lines += ['else', f'set T_rm_in_{z} = InitTrmIn']
    lines += [
        'endif',
        f'set sum_T_occ_{z} = 0',
        f'set n_occ_{z} = 0',
        f'set DriftDay_{z} = DayOfYear',
        'endif',
        f'if Occ_count_{z} > 0',
        f'set sum_T_occ_{z} = sum_T_occ_{z}+{z}_OpT',
        f'set n_occ_{z} = n_occ_{z}+1',
        'endif',
        f'if (DriftMode == 1) && (DriftOccDays_{z} > 0)',
    ]
    for setpoint in ('AHST', 'ACST'):
        applied, reference = f'DriftApplied{setpoint}_{z}', f'DriftRef{setpoint}_{z}'
        lines += [f'if {applied} > {reference}+MaxDriftRate', f'set {applied} = {reference}+MaxDriftRate',
                  f'elseif {applied} < {reference}-MaxDriftRate', f'set {applied} = {reference}-MaxDriftRate',
                  'endif']
    lines.append('elseif DriftMode == 2' if initial else f'elseif (DriftMode == 2) && (DriftOccDays_{z} > 0)')
    for setpoint in ('AHST', 'ACST'):
        applied = f'DriftApplied{setpoint}_{z}'
        lines += [f'if {applied} > T_rm_in_{z}+DeltaCool', f'set {applied} = T_rm_in_{z}+DeltaCool',
                  f'elseif {applied} < T_rm_in_{z}-DeltaHeat', f'set {applied} = T_rm_in_{z}-DeltaHeat', 'endif']
    lines += [
        'endif',
        'endif',
        f'if (DriftAppliedAHST_{z} <> DriftTargetAHST_{z}) || (DriftAppliedACST_{z} <> DriftTargetACST_{z})',
        f'set AHST = DriftAppliedAHST_{z}+AHSTtol',
        f'set ACST = DriftAppliedACST_{z}+ACSTtol',
        *ROUNDING,
        f'if Occ_count_{z} > 0',
        f'set DriftLimitedHours_{z} = 1*ZoneTimeStep',
        'else',
        f'set DriftLimitedHours_{z} = 0',
        'endif',
        'else',
        f'set DriftLimitedHours_{z} = 0',
        'endif',
        f'set DriftLastAHST_{z} = DriftAppliedAHST_{z}',
        f'set DriftLastACST_{z} = DriftAppliedACST_{z}',
    ]
    return lines


def init_program_lines(zones) -> List[str]:
    """The lines of the program InitDriftLimiter, run at the beginning of each environment: the variables of the
    limiter of the zones are 0."""
    return [f'set {prefix}_{zone} = 0' for zone in zones for prefix in (*_STATE, *OUTPUTS)]


def _variables(zone: str) -> List[str]:
    return [f'{prefix}_{zone}' for prefix in (*_STATE, *OUTPUTS)]


def has_drift_limiter(idf) -> bool:
    """True if a zone of the model has the limiter of the drift of the setpoints."""
    return any(str(p.Name).upper().startswith(PROGRAM_PREFIX.upper())
               for p in idf.idfobjects['EnergyManagementSystem:Program'])


def _insert_before(idf, zone: str, line: str, before: str) -> None:
    """Make RunACCIS_<zone> run a program right before another one (that it runs), once."""
    from accim.sim.ems.inputs import RUN_PROGRAM_PREFIX
    from accim.sim.ems.programs import set_program_lines

    run_program = idf.getobject('EnergyManagementSystem:Program', f'{RUN_PROGRAM_PREFIX}{zone}')
    if run_program is None:
        return
    lines = [str(value).strip() for value in run_program.fieldvalues[2:]]
    lines = [existing for existing in lines if existing.lower() != line.lower()]
    index = next((n for n, existing in enumerate(lines) if existing.lower() == before.lower()), None)
    if index is None:
        raise ValueError(f'The program {RUN_PROGRAM_PREFIX}{zone} does not run {before.split(" ", 1)[1]}.')
    set_program_lines(run_program, lines[:index] + [line] + lines[index:])


def set_drift_limiter_code(idf, frequencies=()) -> None:
    """Write the EMS code of the limiter of the zones of a model (of accim 1.0.0 or later) with the input DriftMode in
    their programs SetInputData_<zone> (see the module): the program ApplyDriftLimiter_<zone> (and the line that runs
    it in RunACCIS_<zone>, right before SetASTnoTol), the EMS global variables, the EMS output variables of the zone
    (with Output:Variable objects at the frequencies given) and the program InitDriftLimiter with its program calling
    manager at the beginning of each environment; the EMS global variables of the inputs are declared. The zones without
    the limiter have none of its objects (and nothing is added to a model without it).

    :param frequencies: The reporting frequencies of the Output:Variable objects of its outputs ('Hourly'...).
    """
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.programs import add_program, set_program_lines
    from accim.sim.ems.setpoint_limits import _declared

    zones = {zone: read_inputs(program) for zone, program in input_programs(idf).items()
             if 'DriftMode' in read_inputs(program)}
    if not zones:
        return
    declared = _declared(idf)
    new_inputs = [name for name in INPUTS if name.upper() not in declared]
    if new_inputs:
        idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                         **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(new_inputs, start=1)})
    ems_outputs = {str(o.Name).upper() for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    requested = {(str(o.Variable_Name).upper(), str(o.Reporting_Frequency).upper())
                 for o in idf.idfobjects['Output:Variable']}
    for zone, inputs in zones.items():
        new = [name for name in _variables(zone) if name.upper() not in declared]
        for start in range(0, len(new), 10):
            idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                             **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(new[start:start + 10],
                                                                                         start=1)})
        name = f'{PROGRAM_PREFIX}{zone}'
        lines = program_lines(zone, initial='InitTrmIn' in inputs)
        existing = idf.getobject('EnergyManagementSystem:Program', name)
        if existing is None:
            add_program(idf, name, lines)
        else:
            set_program_lines(existing, lines)
        _insert_before(idf, zone, f'{_RUN_PREFIX}{name}', 'run SetASTnoTol')
        for prefix, (units, kind) in OUTPUTS.items():
            output = f'{prefix}_{zone}'
            if output.upper() not in ems_outputs:
                idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=output, EMS_Variable_Name=output,
                                 Type_of_Data_in_Variable=kind, Update_Frequency='ZoneTimestep', Units=units)
            for frequency in frequencies:
                if (output.upper(), str(frequency).upper()) not in requested:
                    idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=output,
                                     Reporting_Frequency=str(frequency).capitalize(), Schedule_Name='')
    all_zones = [str(p.Name)[len(PROGRAM_PREFIX):] for p in idf.idfobjects['EnergyManagementSystem:Program']
                 if str(p.Name).upper().startswith(PROGRAM_PREFIX.upper())]
    init = idf.getobject('EnergyManagementSystem:Program', INIT_PROGRAM)
    if init is None:
        add_program(idf, INIT_PROGRAM, init_program_lines(all_zones))
    else:
        set_program_lines(init, init_program_lines(all_zones))
    if idf.getobject('EnergyManagementSystem:ProgramCallingManager', INIT_PROGRAM) is None:
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=INIT_PROGRAM,
                         EnergyPlus_Model_Calling_Point='BeginNewEnvironment', Program_Name_1=INIT_PROGRAM)
