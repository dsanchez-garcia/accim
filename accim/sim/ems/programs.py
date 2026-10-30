# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""EMS programs of ACCIS and their program calling managers."""

from typing import List, Tuple

from accim.sim.ems import program_lines as pl
from accim.sim.ems.setast import master_program_lines, subprograms
from accim.sim.idf_tools import add_program
from accim.sim.model import AccimModel

__all__ = ['accis_programs', 'add_program_calling_managers', 'add_programs']

#: Programs that set the variables that the others read, which run first in each timestep
#: (as prefixes, since some programs are per zone).
_PRIORITY_PREFIXES = ('SetInputData', 'SetVOFinputData', 'SetAppLimits', 'ApplyCAT', 'SetGeoVar', 'SetComfTemp',
                      'CountHours_')
#: Programs that initialise variables once, at the beginning of each environment.
_NEW_ENVIRONMENT_PROGRAMS = ('InitASTvariables',)


def accis_programs(model: AccimModel) -> List[Tuple[str, List[str]]]:
    """Name and lines of the EMS programs of ACCIS for a model, in the order accim adds them.

    The programs SetAST_Master and SetAST_CS<n>_<chunk> are subprograms, which SetAST runs.
    """
    zones = model.ems_names
    programs = [('SetComfTemp', list(pl.SET_COMF_TEMP))]
    programs += [(f'CountHours_{z}', pl.format_lines(pl.COUNT_HOURS, zone=z)) for z in zones]
    programs += [('SetAppLimits', list(pl.SET_APP_LIMITS)), ('ApplyCAT', list(pl.APPLY_CAT))]
    programs += [('SetAST_Master', master_program_lines())]
    programs += list(subprograms().items())
    programs += [('SetAST', list(pl.SET_AST)), ('SetASTnoTol', list(pl.SET_AST_NO_TOL)),
                 ('InitASTvariables', list(pl.INIT_AST_VARIABLES))]
    for z in zones:
        programs += [(f'CountHoursNoApp_{z}', pl.format_lines(pl.COUNT_HOURS_NO_APP, zone=z)),
                     (f'SetGeoVar{z}', pl.format_lines(pl.SET_GEO_VAR, zone=z))]
    programs += [('SetInputData', list(pl.SET_INPUT_DATA))]
    if model.is_mixed_mode:
        programs += [('SetVOFinputData', list(pl.SET_VOF_INPUT_DATA)), ('SetVST', list(pl.SET_VST))]
        programs += [(f'ApplyAST_{z}', pl.format_lines(pl.APPLY_AST_MIXED_MODE, zone=z)) for z in zones]
        for w in model.windows:
            programs += [(f'SetMyVOF_{w}', pl.format_lines(pl.SET_MY_VOF, window=w)),
                         (f'SetWindowOperation_{w}', pl.format_lines(pl.SET_WINDOW_OPERATION, window=w))]
    else:
        programs += [(f'ApplyAST_{z}', pl.format_lines(pl.APPLY_AST_AIR_CONDITIONED, zone=z)) for z in zones]
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
    for index, prefix in enumerate(_PRIORITY_PREFIXES):
        if name.startswith(prefix):
            return index
    return len(_PRIORITY_PREFIXES)


def add_program_calling_managers(model: AccimModel) -> None:
    """Add a program calling manager for each program of ACCIS that is not a subprogram and has none.

    The programs of the model are not changed: those that have calling managers keep them, whatever their
    names. The calling managers of the same calling point run in the order of the IDF, so the programs that
    set the input data, the applicability limits, the offsets, the floor areas and the comfort
    temperature come first.
    """
    idf = model.idf
    accis = {name.upper() for name, _ in accis_programs(model)}
    programs = [p.Name for p in idf.idfobjects['EnergyManagementSystem:Program'] if p.Name.upper() in accis]
    managers = list(idf.idfobjects['EnergyManagementSystem:ProgramCallingManager'])
    manager_names = {m.Name.upper() for m in managers}
    called = {str(value).upper() for m in managers for value in m.obj[3:] if value}
    subroutines = {p for p in programs if p.startswith('SetAST_CS') or p == 'SetAST_Master'}
    for name in sorted((p for p in programs if p not in subroutines), key=_priority):
        if name.upper() in manager_names or name.upper() in called:
            model.log(f'Not added - {name} Program Calling Manager')
            continue
        calling_point = 'BeginNewEnvironment' if name in _NEW_ENVIRONMENT_PROGRAMS else 'BeginTimestepBeforePredictor'
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=name,
                         EnergyPlus_Model_Calling_Point=calling_point, Program_Name_1=name)
        model.log(f'Added - {name} Program Calling Manager')
