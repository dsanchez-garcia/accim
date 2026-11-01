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
"""

from typing import Dict, List, Optional, Tuple

from accim.sim.ems import program_lines as pl
from accim.sim.ems.inputs import INPUT_PROGRAM_PREFIX, RUN_PROGRAM_PREFIX, input_lines
from accim.sim.ems.setast import master_program_lines, subprograms
from accim.sim.idf_tools import add_program
from accim.sim.model import AccimModel

__all__ = [
    'ZONE_RESULT_VARIABLES',
    'ZONE_STATE_VARIABLES',
    'accis_programs',
    'add_program_calling_managers',
    'add_programs',
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
    """Name and lines of the EMS programs of ACCIS for a model, in the order accim adds them.

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
        programs += [('SetVST', list(pl.SET_VST))]
        programs += [(f'ApplyAST_{z}', pl.format_lines(pl.APPLY_AST_MIXED_MODE, zone=z)) for z in zones]
        for w in model.windows:
            programs += [(f'SetMyVOF_{w}', pl.format_lines(pl.SET_MY_VOF, window=w)),
                         (f'SetWindowOperation_{w}', pl.format_lines(pl.SET_WINDOW_OPERATION, window=w))]
        windows = windows_by_zone(model)
    else:
        programs += [(f'ApplyAST_{z}', pl.format_lines(pl.APPLY_AST_AIR_CONDITIONED, zone=z)) for z in zones]
    programs += [(f'{RUN_PROGRAM_PREFIX}{z}', _run_program_lines(z, windows.get(z, []), mixed_mode)) for z in zones]
    return programs


def add_programs(model: AccimModel) -> None:
    """Add the EMS programs of ACCIS that the model does not have yet."""
    existing = {p.Name for p in model.idf.idfobjects['EnergyManagementSystem:Program']}
    master_existed = 'SetAST_Master' in existing
    for name, lines in accis_programs(model):
        # SetAST, its master program and subprograms are added together
        is_setast = name in ('SetAST', 'SetAST_Master') or name.startswith('SetAST_CS')
        if (is_setast and master_existed) or name in existing:
            model.log(f'Not added - {name} Program')
            continue
        add_program(model.idf, name, lines)
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
    called = {str(value).upper() for m in managers for value in m.obj[3:] if value}
    for name in sorted(programs, key=_priority):
        if name.upper() in manager_names or name.upper() in called:
            model.log(f'Not added - {name} Program Calling Manager')
            continue
        calling_point = 'BeginNewEnvironment' if name in _NEW_ENVIRONMENT_PROGRAMS else 'BeginTimestepBeforePredictor'
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=name,
                         EnergyPlus_Model_Calling_Point=calling_point, Program_Name_1=name)
        model.log(f'Added - {name} Program Calling Manager')
