# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""EMS programs of ACCIS and their program calling managers.

Each occupied zone has a program SetInputData_<zone> with its arguments (see :mod:`accim.sim.ems.inputs`) and a
program RunACCIS_<zone>, which runs in each timestep: SetInputData_<zone>; SetAppLimits, ApplyCAT and SetComfTemp
(the applicability limits, the offsets of the category and the comfort temperature); SetAST (which runs
SetAST_Master and the subprograms of the comfort standard) and SetASTnoTol; CountHours_<zone> and
CountHoursNoApp_<zone> (the hour counters, with the setpoints of the timestep); in mixed mode, SetVST;
ApplyAST_<zone>; and, in mixed mode, the programs of the windows of the zone. This is the order in which the programs
of accim 0.x ran for all the zones at once, except that CountHours ran before SetAST, with the setpoints of the
previous timestep.

The programs that do not belong to a zone (SetAppLimits, ApplyCAT, SetComfTemp, SetAST, SetASTnoTol and SetVST) use
the variables of the zone that is running (ComfStand, ACST...). Some of these variables keep their value from one
timestep to the next, so RunACCIS_<zone> restores those of the zone before running these programs and stores them
after (``ACST_<zone>``...), together with the setpoints of the zone (``roundedACST_<zone>``...), which are its
outputs. A model whose zones have the same arguments gives the same setpoints as with the programs of accim 0.x.

The programs SetComfTemp, SetAppLimits, ApplyCAT, CountHours_<zone> and SetAST_Master, and the subprograms of
SetAST, have the code of every comfort standard, so that the comfort standard of a zone can be changed in its program
SetInputData_<zone> (as the parametric module does). The output IDFs of :class:`accim.sim.accis.AddAccis` only have
the code of the comfort standards of their zones (:func:`set_comfort_standard_code`); the functions that set the
comfort standard add its code if the model does not have it (:func:`add_comfort_standard_code`).

The lines of the programs are indented inside the blocks IF and WHILE (:func:`indent_lines`).
"""

from typing import Dict, Iterable, List, Optional, Tuple

from accim.sim.ems import program_lines as pl
from accim.sim.ems.inputs import INPUT_PROGRAM_PREFIX, RUN_PROGRAM_PREFIX, input_lines
from accim.sim.ems.setast import master_program_lines, subprogram_comfort_standards, subprograms
from accim.sim.model import AccimModel

__all__ = [
    'INDENTATION',
    'ZONE_RESULT_VARIABLES',
    'ZONE_STATE_VARIABLES',
    'accis_programs',
    'add_comfort_standard_code',
    'add_program',
    'add_program_calling_managers',
    'add_programs',
    'indent_lines',
    'indent_programs',
    'set_comfort_standard_code',
    'set_program_lines',
    'windows_by_zone',
    'zone_variables',
]

#: Variables of the programs that do not belong to a zone that keep their value from one timestep to the next: the
#: static setpoints of some comfort standards keep their value at the end of the day, SetComfTemp does not set the
#: comfort temperature of some comfort standards, and SetAST_Master does not set the cooling season if it starts and
#: ends on the same day. Their values at the beginning of each environment: the setpoints are Null, so that a comfort
#: standard without setpoints for the comfort mode of the zone stops EnergyPlus (as when they were not set), instead
#: of using those of another zone; Null is reported as 0, as the variables that are not set.
ZONE_STATE_VARIABLES = {'ACST': 'Null', 'AHST': 'Null', 'ComfTemp': 'Null', 'CoolingSeason': '0'}
#: The other variables that each zone keeps, for its outputs (VST and MinOutTemp, in mixed mode only).
ZONE_RESULT_VARIABLES = ('ACSTnoTol', 'AHSTnoTol', 'roundedACST', 'roundedAHST', 'VST', 'MinOutTemp')
#: The number of ZONE_RESULT_VARIABLES of the models with full air-conditioning.
_AIR_CONDITIONED_RESULTS = 4
#: The programs of ACCIS with a calling manager at BeginTimestepBeforePredictor, in their order (as prefixes); the
#: other programs are run by RunACCIS_<zone>.
_CALLED_PREFIXES = ('SetGeoVar', RUN_PROGRAM_PREFIX)
#: Programs that initialise variables once, at the beginning of each environment.
_NEW_ENVIRONMENT_PROGRAMS = ('InitASTvariables',)
_WINDOW_PROGRAM_PREFIXES = ('SetMyVOF_', 'SetWindowOperation_')
#: The spaces before a line of an EMS program for each block IF or WHILE that contains it.
INDENTATION = '    '
_OPENING_KEYWORDS = ('IF', 'ELSEIF', 'ELSE', 'WHILE')
_CLOSING_KEYWORDS = ('ELSEIF', 'ELSE', 'ENDIF', 'ENDWHILE')
#: The programs whose lines are a chain ``if ComfStand == ... endif`` (and CountHours_<zone>, of each zone).
_COMFORT_STANDARD_PROGRAMS = {'SetComfTemp': pl.SET_COMF_TEMP, 'SetAppLimits': pl.SET_APP_LIMITS,
                              'ApplyCAT': pl.APPLY_CAT}
_COUNT_HOURS_PREFIX = 'CountHours_'


def indent_lines(lines: Iterable[str]) -> List[str]:
    """The lines of an EMS program, indented inside the blocks IF ... ELSEIF ... ELSE ... ENDIF and
    WHILE ... ENDWHILE.

    EnergyPlus ignores the spaces at the beginning of each line: they only show where each block begins and ends.
    """
    indented = []
    level = 0
    for line in lines:
        line = str(line).strip()
        keyword = line.split(' ', 1)[0].upper()
        if keyword in _CLOSING_KEYWORDS:
            level = max(level - 1, 0)
        indented.append(INDENTATION * level + line)
        if keyword in _OPENING_KEYWORDS:
            level += 1
    return indented


def add_program(idf, name: str, lines: Iterable[str]):
    """Add an EMS program with its lines (the fields Program_Line_1, Program_Line_2... of eppy), indented."""
    fields = {f'Program_Line_{number}': line for number, line in enumerate(indent_lines(lines), start=1)}
    return idf.newidfobject('EnergyManagementSystem:Program', Name=name, **fields)


def set_program_lines(program, lines: Iterable[str]) -> None:
    """Replace the lines of an EMS program, which are the values of its fields after its name, indented."""
    del program.fieldvalues[2:]
    for number, line in enumerate(indent_lines(lines), start=1):
        program[f'Program_Line_{number}'] = line


def indent_programs(idf) -> None:
    """Indent the lines of all the EMS programs and subroutines of a model.

    eppy removes the spaces at the beginning of the fields when it reads an IDF, so the programs of a model read from
    a file have no indentation.
    """
    for object_type in ('EnergyManagementSystem:Program', 'EnergyManagementSystem:Subroutine'):
        for program in idf.idfobjects[object_type]:
            program.fieldvalues[2:] = indent_lines(program.fieldvalues[2:])


def set_comfort_standard_code(idf, comfort_standards: Optional[Iterable[int]] = None) -> None:
    """Write in the EMS programs of ACCIS of a model the code of some comfort standards only (of all of them with
    None).

    These are the programs that depend on the comfort standard: SetComfTemp, SetAppLimits, ApplyCAT and
    CountHours_<zone> keep their branches of these comfort standards (see
    :func:`accim.sim.ems.program_lines.for_comfort_standards`), SetAST_Master runs their subprograms, and the model has
    the subprograms SetAST_CS<n>_<chunk> of these comfort standards only (at the end of its programs). A program that
    has nothing to do for these comfort standards only returns (SetComfTemp and ApplyCAT with ESP CTE and INT ISO7730,
    which use neither the comfort temperature nor the offsets of the categories). With these comfort standards, the
    programs do the same as with the code of all of them; with another one, they do not set its setpoints, and
    EnergyPlus stops.
    """
    if comfort_standards is not None:
        # The models can have them as numbers with decimals (set ComfStand = 1.0)
        comfort_standards = {int(n) for n in comfort_standards}

    def lines_for(lines) -> List[str]:
        if comfort_standards is None:
            return list(lines)
        return pl.for_comfort_standards(lines, comfort_standards) or ['return']

    programs = idf.idfobjects['EnergyManagementSystem:Program']
    for name, lines in _COMFORT_STANDARD_PROGRAMS.items():
        program = idf.getobject('EnergyManagementSystem:Program', name)
        if program is not None:
            set_program_lines(program, lines_for(lines))
    for program in programs:
        if program.Name.upper().startswith(_COUNT_HOURS_PREFIX.upper()):
            zone = program.Name[len(_COUNT_HOURS_PREFIX):]
            set_program_lines(program, lines_for(pl.format_lines(pl.COUNT_HOURS, zone=zone)))
    master = idf.getobject('EnergyManagementSystem:Program', 'SetAST_Master')
    if master is None:
        return
    set_program_lines(master, master_program_lines(comfort_standards))
    for program in [p for p in programs if p.Name.upper().startswith('SETAST_CS')]:
        idf.removeidfobject(program)
    for name, lines in subprograms(comfort_standards).items():
        add_program(idf, name, lines)


def add_comfort_standard_code(idf, comfort_standards: Iterable[int]) -> None:
    """Add to the EMS programs of ACCIS of a model the code of some comfort standards, if it does not have it (the
    output IDFs of :class:`accim.sim.accis.AddAccis` only have that of the comfort standards of their zones), and keep
    that of the others (see :func:`set_comfort_standard_code`)."""
    with_code = subprogram_comfort_standards(idf)
    wanted = {int(n) for n in comfort_standards}
    if not wanted <= with_code:
        set_comfort_standard_code(idf, with_code | wanted)


def zone_variables(mixed_mode: bool) -> Tuple[str, ...]:
    """The variables that each zone keeps as ``<variable>_<zone>`` (global variables of the EMS)."""
    results = ZONE_RESULT_VARIABLES if mixed_mode else ZONE_RESULT_VARIABLES[:_AIR_CONDITIONED_RESULTS]
    return tuple(ZONE_STATE_VARIABLES) + results


def windows_by_zone(model: AccimModel) -> Dict[Optional[str], List[str]]:
    """The windows and doors that open in each zone (mixed mode), by the name of the zone in the EMS objects.

    The windows whose zone is not an occupied zone (which accim does not find) are under the key None: their
    programs keep their own calling managers.
    """
    ems_names = {zone.upper(): name for zone, name in zip(model.ems_zones, model.ems_names)}
    windows: Dict[Optional[str], List[str]] = {}
    for window, zone in zip(model.windows, model.window_zones):
        windows.setdefault(ems_names.get(zone.upper()), []).append(window)
    return windows


def _run_program_lines(zone: str, windows: List[str], mixed_mode: bool) -> List[str]:
    """Lines of RunACCIS_<zone>, which runs the ACCIS of a zone."""
    lines = [f'run {INPUT_PROGRAM_PREFIX}{zone}']
    lines += [f'set {variable} = {variable}_{zone}' for variable in ZONE_STATE_VARIABLES]
    lines += ['run SetAppLimits', 'run ApplyCAT', 'run SetComfTemp', 'run SetAST', 'run SetASTnoTol',
              f'run CountHours_{zone}', f'run CountHoursNoApp_{zone}']
    if mixed_mode:
        lines.append('run SetVST')
    lines.append(f'run ApplyAST_{zone}')
    for window in windows:
        lines += [f'run {prefix}{window}' for prefix in _WINDOW_PROGRAM_PREFIXES]
    lines += [f'set {variable}_{zone} = {variable}' for variable in zone_variables(mixed_mode)]
    return lines


def _init_program_lines(zones: List[str]) -> List[str]:
    """Lines of InitASTvariables, which initialises the variables that each zone keeps, at each new environment."""
    return [f'set {variable}_{zone} = {value}' for zone in zones for variable, value in ZONE_STATE_VARIABLES.items()]


def accis_programs(model: AccimModel) -> List[Tuple[str, List[str]]]:
    """Name and lines of the EMS programs of ACCIS for a model, in the order accim adds them, with the code of all the
    comfort standards.

    The programs SetAST_Master and SetAST_CS<n>_<chunk> are subprograms, which SetAST runs. SetInputData_<zone> has
    the default arguments of :func:`accim.sim.accis.add_accis_to_idf`.
    """
    zones = model.ems_names
    mixed_mode = model.is_mixed_mode
    programs = [('SetComfTemp', list(pl.SET_COMF_TEMP))]
    programs += [(f'CountHours_{z}', pl.format_lines(pl.COUNT_HOURS, zone=z)) for z in zones]
    programs += [('SetAppLimits', list(pl.SET_APP_LIMITS)), ('ApplyCAT', list(pl.APPLY_CAT))]
    programs += [('SetAST_Master', master_program_lines())]
    programs += list(subprograms().items())
    programs += [('SetAST', list(pl.SET_AST)), ('SetASTnoTol', list(pl.SET_AST_NO_TOL)),
                 ('InitASTvariables', _init_program_lines(zones))]
    for z in zones:
        programs += [(f'CountHoursNoApp_{z}', pl.format_lines(pl.COUNT_HOURS_NO_APP, zone=z)),
                     (f'SetGeoVar{z}', pl.format_lines(pl.SET_GEO_VAR, zone=z))]
    programs += [(f'{INPUT_PROGRAM_PREFIX}{z}', input_lines(mixed_mode=mixed_mode)) for z in zones]
    windows: Dict[Optional[str], List[str]] = {}
    if mixed_mode:
        # The existing HVAC systems (ex_mm) are off when the thermostat of the zone asks for no load; the VRF
        # systems of accim (vrf_mm), when their coils are off
        existing_hvac = getattr(model, 'script_type', None) == 'ex_mm'
        apply_ast = pl.APPLY_AST_MIXED_MODE_EXISTING_HVAC if existing_hvac else pl.APPLY_AST_MIXED_MODE
        window_operation = pl.SET_WINDOW_OPERATION_EXISTING_HVAC if existing_hvac else pl.SET_WINDOW_OPERATION
        programs += [('SetVST', list(pl.SET_VST))]
        programs += [(f'ApplyAST_{z}', pl.format_lines(apply_ast, zone=z)) for z in zones]
        for w in model.windows:
            programs += [(f'SetMyVOF_{w}', pl.format_lines(pl.SET_MY_VOF, window=w)),
                         (f'SetWindowOperation_{w}', pl.format_lines(window_operation, window=w))]
        windows = windows_by_zone(model)
    else:
        programs += [(f'ApplyAST_{z}', pl.format_lines(pl.APPLY_AST_AIR_CONDITIONED, zone=z)) for z in zones]
    programs += [(f'{RUN_PROGRAM_PREFIX}{z}', _run_program_lines(z, windows.get(z, []), mixed_mode)) for z in zones]
    return programs


def add_programs(model: AccimModel) -> None:
    """Add the EMS programs of ACCIS that the model does not have yet."""
    idf = model.idf
    # SetAST, its master program and subprograms are added together
    master_existed = idf.getobject('EnergyManagementSystem:Program', 'SetAST_Master') is not None
    for name, lines in accis_programs(model):
        is_setast = name in ('SetAST', 'SetAST_Master') or name.startswith('SetAST_CS')
        if (is_setast and master_existed) or idf.getobject('EnergyManagementSystem:Program', name) is not None:
            model.log(f'Not added - {name} Program')
            continue
        add_program(idf, name, lines)
        model.log(f'Added - {name} Program')


def _priority(name: str) -> int:
    for index, prefix in enumerate(_CALLED_PREFIXES):
        if name.startswith(prefix):
            return index
    return len(_CALLED_PREFIXES)


def _called_programs(model: AccimModel) -> set:
    """The names (in upper case) of the programs of ACCIS that have calling managers: SetGeoVar<zone>,
    RunACCIS_<zone>, InitASTvariables and the programs of the windows that are not in an occupied zone."""
    names = {name for zone in model.ems_names for name in (f'SetGeoVar{zone}', f'{RUN_PROGRAM_PREFIX}{zone}')}
    names.update(_NEW_ENVIRONMENT_PROGRAMS)
    if model.is_mixed_mode:
        names.update(f'{prefix}{window}' for window in windows_by_zone(model).get(None, [])
                     for prefix in _WINDOW_PROGRAM_PREFIXES)
    return {name.upper() for name in names}


def add_program_calling_managers(model: AccimModel) -> None:
    """Add a program calling manager for each program of ACCIS that is run by EnergyPlus and has none.

    EnergyPlus runs SetGeoVar<zone> and then RunACCIS_<zone> of each zone at the beginning of each timestep, and
    InitASTvariables at the beginning of each environment; RunACCIS_<zone> runs the other programs. The programs of
    the model are not changed: those that have calling managers keep them, whatever their names. The calling
    managers of the same calling point run in the order of the IDF.
    """
    idf = model.idf
    called_programs = _called_programs(model)
    programs = [p.Name for p in idf.idfobjects['EnergyManagementSystem:Program'] if p.Name.upper() in called_programs]
    managers = list(idf.idfobjects['EnergyManagementSystem:ProgramCallingManager'])
    manager_names = {m.Name.upper() for m in managers}
    called = {str(value).upper() for m in managers for value in m.fieldvalues[3:] if value}
    for name in sorted(programs, key=_priority):
        if name.upper() in manager_names or name.upper() in called:
            model.log(f'Not added - {name} Program Calling Manager')
            continue
        calling_point = 'BeginNewEnvironment' if name in _NEW_ENVIRONMENT_PROGRAMS else 'BeginTimestepBeforePredictor'
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=name,
                         EnergyPlus_Model_Calling_Point=calling_point, Program_Name_1=name)
        model.log(f'Added - {name} Program Calling Manager')
