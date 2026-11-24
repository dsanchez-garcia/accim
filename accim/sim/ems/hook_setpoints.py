# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The setpoints that a hook of the backend of the Python API of EnergyPlus gives to the ACCIS: those of the adaptive
thermal heat balance (ATHB) and of the standard effective temperature (SET) of :mod:`accim.sim.comfort_hooks` (task G1
of the review of accim 1.2.0, finding A4/A6-1 of ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md``).

The hooks run at the beginning of each timestep before the EMS programs (``before_programs`` of
:func:`accim.sim.energyplus_api.run_simulation`, as :func:`accim.run.run_ep` passes them), with the values of the
sensors of the timestep, and set for each zone the EMS global variables ``HookAHST_<zone>`` and ``HookACST_<zone>``
(their heating and cooling setpoints, the limits of their comfort band: setpoints without the tolerance) and
``HookSetpoints_<zone>`` (1; the hooks of the SET set it to -1 in the timesteps in which they give the zone no
setpoints, without the values of their sensors, so that the fallback of the EMS of comfort standard 24 does nothing in
them, :mod:`accim.sim.ems.set_feedback`). The program ``ApplyHookSetpoints_<zone>``, which ``RunACCIS_<zone>`` runs
right after SetAST, then sets the setpoints of the ACCIS to them as the subprograms of SetAST set the adaptive ones:
``AHST = HookAHST_<zone> + AHSTtol`` and ``ACST = HookACST_<zone> + ACSTtol`` (with the tolerance of the setpoints of
the zone), rounded with SetpointAcc (:data:`accim.sim.ems.setpoint_lines.ROUNDING`), and sets ``HookSetpoints_<zone>``
back to 0.
So everything that the ACCIS does after SetAST follows the setpoints of the hook: the minimum and maximum of the
setpoints (:mod:`accim.sim.ems.setpoint_limits`, whose program runs after this one), the setpoints without the tolerance
(SetASTnoTol: those of the hook), the hour counters (CountHours_<zone>, CountHoursNoApp_<zone>, and those of
:mod:`accim.sim.ems.long_term_discomfort`), the thermostats (ApplyAST_<zone>) and the outputs of the setpoints of the zone
(``Adaptive Cooling Setpoint Temperature_<zone>``, with and without the tolerance...). The comfort temperature
(``Comfort Temperature_<zone>``) and the applicability limits with which CountHours_<zone> splits its hours stay those of
the comfort standard of the zone. Without the hook (the EMS backend, or the backend of the API without it),
``HookSetpoints_<zone>`` is 0 (the program ``InitHookSetpoints`` sets it at the beginning of each environment), and the
setpoints are those of the ACCIS, but in the zones with the fallback of the EMS of comfort standard 24
(``apply_sun2026_setpoints(..., ems_fallback=True)``), whose program ``SetSETFeedback_<zone>`` gives them, as a hook,
right before ``ApplyHookSetpoints_<zone>``: those zones need no hook (``zones_needing_a_hook`` of
:mod:`accim.sim.ems.set_feedback`, with which :func:`accim.run.run_ep` and the backend of the API leave them out of
their error and their warning).

In mixed mode (the models with the program SetVST, script types 'vrf_mm' and 'ex_mm'; decision of the author of
2026-11-24, ``notes/decisions.md``), the windows follow the setpoints of the hook too. SetVST, which runs after these
programs, already takes them for the minimum outdoor temperature (``roundedAHST - MinOToffset``) and, with the
ventilation controls 1 and 3, for the ventilation setpoint (``roundedAHST + VSToffset``), and the programs of the
windows compare the operative temperature with ``roundedACST``. With the ventilation controls 0 and 2, SetVST sets the
ventilation setpoint to the comfort temperature of the comfort standard of the zone, which is not that of the hook: in
the timesteps in which the hook has given its setpoints, ``ApplyHookSetpoints_<zone>`` sets the global variable
``HookVST_<zone>`` to 1 (0 otherwise), and the program ``ApplyHookVST_<zone>``, which ``RunACCIS_<zone>`` runs right
after SetVST, sets the ventilation setpoint to the midpoint of the setpoints of the zone,
``(roundedACST + roundedAHST)/2 + VSToffset``, as SetVST does with the static setpoints of comfort standard 0 and out
of the applicability limits. The programs of the models with full air-conditioning do not change.
"""

import os
import re
from typing import List, Sequence, Tuple, Union

from accim.sim.ems.setpoint_lines import ROUNDING

__all__ = [
    'FLAG_PREFIX',
    'HEATING_PREFIX',
    'COOLING_PREFIX',
    'INIT_PROGRAM',
    'MissingHookWarning',
    'PROGRAM_PREFIX',
    'VENTILATION_FLAG_PREFIX',
    'VENTILATION_PROGRAM_PREFIX',
    'hook_zones',
    'hook_zones_of_file',
    'init_program_lines',
    'missing_hook_message',
    'program_lines',
    'set_hook_setpoints_code',
    'ventilation_program_lines',
    'zone_variables',
]

#: The program of each zone that gives the setpoints of the hook to the ACCIS is this prefix and the name of the zone
PROGRAM_PREFIX = 'ApplyHookSetpoints_'
#: The program that sets the variables of the hooks to 0 at the beginning of each environment
INIT_PROGRAM = 'InitHookSetpoints'
#: The EMS global variable of each zone that is 1 when the hook has given the setpoints of the timestep
FLAG_PREFIX = 'HookSetpoints_'
#: The EMS global variables of each zone with the heating and cooling setpoints of the hook (without the tolerance)
HEATING_PREFIX = 'HookAHST_'
COOLING_PREFIX = 'HookACST_'
#: In mixed mode, the program of each zone that sets its ventilation setpoint with the setpoints of the hook is this
#: prefix and the name of the zone
VENTILATION_PROGRAM_PREFIX = 'ApplyHookVST_'
#: In mixed mode, the EMS global variable of each zone that is 1 in the timesteps in which the hook has given its
#: setpoints (HookSetpoints_<zone> is set back to 0 before SetVST runs)
VENTILATION_FLAG_PREFIX = 'HookVST_'
#: The program of mixed mode that sets the ventilation setpoint, after which ApplyHookVST_<zone> runs
_VENTILATION_SETPOINT_PROGRAM = 'SetVST'
_RUN_PREFIX = 'run '


def zone_variables(zone: str) -> Tuple[str, str, str]:
    """The EMS global variables of the hook of a zone: (flag, heating setpoint, cooling setpoint)."""
    return f'{FLAG_PREFIX}{zone}', f'{HEATING_PREFIX}{zone}', f'{COOLING_PREFIX}{zone}'


def program_lines(zone: str, mixed_mode: bool = False) -> List[str]:
    """The lines of the program ApplyHookSetpoints_<zone>: the setpoints of the ACCIS are those of the hook, with the
    tolerance of the setpoints of the zone and rounded, if the hook has given them in this timestep. With
    ``mixed_mode``, it also tells ApplyHookVST_<zone> whether it has (``HookVST_<zone>``, 1 or 0)."""
    flag, heating, cooling = zone_variables(zone)
    lines = [f'if {flag} == 1', f'set AHST = {heating}+AHSTtol', f'set ACST = {cooling}+ACSTtol'] + list(ROUNDING)
    if mixed_mode:
        lines += [f'set {VENTILATION_FLAG_PREFIX}{zone} = 1', 'else', f'set {VENTILATION_FLAG_PREFIX}{zone} = 0']
    return lines + ['endif', f'set {flag} = 0']


def ventilation_program_lines(zone: str) -> List[str]:
    """The lines of the program ApplyHookVST_<zone> of mixed mode: with the ventilation controls 0 and 2, the
    ventilation setpoint is the midpoint of the setpoints of the zone (those of the hook) plus its offset, if the hook
    has given them in this timestep (see the module)."""
    return [f'if {VENTILATION_FLAG_PREFIX}{zone} == 1', 'if (VentCtrl == 0) || (VentCtrl == 2)',
            'set VST = (roundedACST+roundedAHST)/2+VSToffset', 'endif', 'endif']


def init_program_lines(zones: Sequence[str], mixed_mode: bool = False) -> List[str]:
    """The lines of the program InitHookSetpoints, run at the beginning of each environment."""
    lines = [f'set {name} = 0' for zone in zones for name in zone_variables(zone)]
    if mixed_mode:
        lines += [f'set {VENTILATION_FLAG_PREFIX}{zone} = 0' for zone in zones]
    return lines


def hook_zones(idf) -> List[str]:
    """The zones of a model whose setpoints a hook can set (those with the program ApplyHookSetpoints_<zone>)."""
    prefix = PROGRAM_PREFIX.upper()
    return [str(p.Name)[len(PROGRAM_PREFIX):] for p in idf.idfobjects['EnergyManagementSystem:Program']
            if str(p.Name).upper().startswith(prefix)]


class MissingHookWarning(UserWarning):
    """A model prepared for the setpoints of a hook is simulated with the backend of the Python API of EnergyPlus
    without a hook that runs before its EMS programs (finding A4 of the self-audit of 2026-11-11)."""


#: The programs ApplyHookSetpoints_<zone> in the text of an IDF file (their name follows the type of the object)
_PROGRAM_IN_FILE = re.compile(rf'^\s*EnergyManagementSystem:Program\s*,\s*{re.escape(PROGRAM_PREFIX)}([^,;!\s]+)\s*,',
                              re.IGNORECASE | re.MULTILINE)


def hook_zones_of_file(path: Union[str, os.PathLike]) -> List[str]:
    """The zones of the model of an IDF file whose setpoints a hook can set (those with the program
    ApplyHookSetpoints_<zone>, as :func:`hook_zones`), read from the text of the file, without eppy, so whatever its
    EnergyPlus version is; none if the file cannot be read.

    :param path: The path of the IDF file.
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
    except OSError:
        return []
    return _PROGRAM_IN_FILE.findall(text)


def missing_hook_message(models: Sequence[str], backend: str) -> str:
    """The message of the error of the EMS backend, or of the warning of the backend of the API, for the models
    prepared for the setpoints of a hook that are simulated without it (finding A4 of the self-audit of 2026-11-11,
    decided on 2026-11-12): without the hook, the model runs with the setpoints of the comfort standard of its zones,
    and the outputs of the hook (``SET_<zone>``, ``ATHB_PMV_<zone>``, ``HoursInCausalBand_<zone>``...) are 0.

    :param models: The names of the IDF files.
    :param backend: 'ems' (the models cannot be simulated) or 'api' (they are, without the setpoints of the hook).
    """
    names = ', '.join(str(model) for model in models)
    prepared = (f'prepared for the setpoints of a hook of the backend of the Python API of EnergyPlus (the programs '
                f'{PROGRAM_PREFIX}<zone> of accim.sim.comfort_hooks: apply_athb_setpoints, apply_set_setpoints or '
                f'apply_sun2026_setpoints)')
    effect = ('the setpoints of the comfort standard of their zones (those of the names of the output IDFs) and the '
              'outputs of the hook at 0')
    how = ("run_ep(backend='api', hooks=[hook]), with the hook that the function that prepared each model returned")
    # The models of comfort standard 24 can have a fallback in their EMS, with which they need no hook
    fallback = ("Those of comfort standard 24 can also be prepared with apply_sun2026_setpoints(..., "
                "ems_fallback=True), whose fallback of the EMS gives the setpoints without the hook.")
    if backend == 'ems':
        return (f'These models are {prepared}, which the EMS backend cannot run: {names}. They would be simulated '
                f'with {effect}. Simulate them with {how}. {fallback}')
    return (f'These models are {prepared}, and no hook runs before their EMS programs: {names}. They are simulated '
            f'with {effect}. Simulate them with {how} (the argument before_programs of run_simulation and '
            f'run_simulations). {fallback}')


def set_hook_setpoints_code(idf, zones: Sequence[str]) -> None:
    """Add to a model with the ACCIS (of accim 1.0.0 or later) the EMS objects with which a hook gives its setpoints to
    some zones (see the module): the global variables of each zone, its program ApplyHookSetpoints_<zone> and the line
    that runs it in RunACCIS_<zone> right after SetAST (before the program of the minimum and maximum of the setpoints,
    if the zone has it), and the program InitHookSetpoints with its program calling manager at the beginning of each
    environment. The objects that the model has already are kept (written again), so the hooks of the ATHB and of the
    SET share them. In mixed mode (a model with the program SetVST), also the global variable ``HookVST_<zone>`` and
    the program ApplyHookVST_<zone> of each zone, with the line that runs it in RunACCIS_<zone> right after SetVST
    (see the module).

    :param zones: The zones, by their names in the EMS objects (``Block1_Zone1``...).
    :raises ValueError: If the program RunACCIS_<zone> of a zone does not run SetAST.
    """
    from accim.sim.ems.programs import add_program, set_program_lines
    from accim.sim.ems.setpoint_limits import _declared, _insert_run_line

    zones = list(zones)
    declared = _declared(idf)
    mixed_mode = idf.getobject('EnergyManagementSystem:Program', _VENTILATION_SETPOINT_PROGRAM) is not None
    for zone in zones:
        names = list(zone_variables(zone)) + ([f'{VENTILATION_FLAG_PREFIX}{zone}'] if mixed_mode else [])
        new = [name for name in names if name.upper() not in declared]
        if new:
            idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                             **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(new, start=1)})
        name = f'{PROGRAM_PREFIX}{zone}'
        existing = idf.getobject('EnergyManagementSystem:Program', name)
        if existing is None:
            add_program(idf, name, program_lines(zone, mixed_mode))
        else:
            set_program_lines(existing, program_lines(zone, mixed_mode))
        _insert_run_line(idf, zone, f'{_RUN_PREFIX}{name}', 'run SetAST')
        if mixed_mode:
            name = f'{VENTILATION_PROGRAM_PREFIX}{zone}'
            existing = idf.getobject('EnergyManagementSystem:Program', name)
            if existing is None:
                add_program(idf, name, ventilation_program_lines(zone))
            else:
                set_program_lines(existing, ventilation_program_lines(zone))
            _insert_run_line(idf, zone, f'{_RUN_PREFIX}{name}', f'{_RUN_PREFIX}{_VENTILATION_SETPOINT_PROGRAM}')
    all_zones = hook_zones(idf)
    init = idf.getobject('EnergyManagementSystem:Program', INIT_PROGRAM)
    if init is None:
        add_program(idf, INIT_PROGRAM, init_program_lines(all_zones, mixed_mode))
    else:
        set_program_lines(init, init_program_lines(all_zones, mixed_mode))
    if idf.getobject('EnergyManagementSystem:ProgramCallingManager', INIT_PROGRAM) is None:
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=INIT_PROGRAM,
                         EnergyPlus_Model_Calling_Point='BeginNewEnvironment', Program_Name_1=INIT_PROGRAM)
