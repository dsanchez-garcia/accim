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
``HookSetpoints_<zone>`` (1). The program ``ApplyHookSetpoints_<zone>``, which ``RunACCIS_<zone>`` runs right after
SetAST, then sets the setpoints of the ACCIS to them as the subprograms of SetAST set the adaptive ones: ``AHST =
HookAHST_<zone> + AHSTtol`` and ``ACST = HookACST_<zone> + ACSTtol`` (with the tolerance of the setpoints of the zone),
rounded with SetpointAcc (:data:`accim.sim.ems.setpoint_lines.ROUNDING`), and sets ``HookSetpoints_<zone>`` back to 0.
So everything that the ACCIS does after SetAST follows the setpoints of the hook: the floor and ceiling of the
setpoints (:mod:`accim.sim.ems.setpoint_limits`, whose program runs after this one), the setpoints without the tolerance
(SetASTnoTol: those of the hook), the hour counters (CountHours_<zone>, CountHoursNoApp_<zone>, and those of
:mod:`accim.sim.ems.long_term_discomfort`), the thermostats (ApplyAST_<zone>) and the outputs of the setpoints of the zone
(``Adaptive Cooling Setpoint Temperature_<zone>``, with and without the tolerance...). The comfort temperature
(``Comfort Temperature_<zone>``) and the applicability limits with which CountHours_<zone> splits its hours stay those of
the comfort standard of the zone. Without the hook (the EMS backend, or the backend of the API without it),
``HookSetpoints_<zone>`` is 0 (the program ``InitHookSetpoints`` sets it at the beginning of each environment), and the
setpoints are those of the ACCIS.
"""

from typing import List, Sequence, Tuple

from accim.sim.ems.setpoint_lines import ROUNDING

__all__ = [
    'FLAG_PREFIX',
    'HEATING_PREFIX',
    'COOLING_PREFIX',
    'INIT_PROGRAM',
    'PROGRAM_PREFIX',
    'hook_zones',
    'init_program_lines',
    'program_lines',
    'set_hook_setpoints_code',
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
_RUN_PREFIX = 'run '


def zone_variables(zone: str) -> Tuple[str, str, str]:
    """The EMS global variables of the hook of a zone: (flag, heating setpoint, cooling setpoint)."""
    return f'{FLAG_PREFIX}{zone}', f'{HEATING_PREFIX}{zone}', f'{COOLING_PREFIX}{zone}'


def program_lines(zone: str) -> List[str]:
    """The lines of the program ApplyHookSetpoints_<zone>: the setpoints of the ACCIS are those of the hook, with the
    tolerance of the setpoints of the zone and rounded, if the hook has given them in this timestep."""
    flag, heating, cooling = zone_variables(zone)
    return ([f'if {flag} == 1', f'set AHST = {heating}+AHSTtol', f'set ACST = {cooling}+ACSTtol']
            + list(ROUNDING) + ['endif', f'set {flag} = 0'])


def init_program_lines(zones: Sequence[str]) -> List[str]:
    """The lines of the program InitHookSetpoints, run at the beginning of each environment."""
    return [f'set {name} = 0' for zone in zones for name in zone_variables(zone)]


def hook_zones(idf) -> List[str]:
    """The zones of a model whose setpoints a hook can set (those with the program ApplyHookSetpoints_<zone>)."""
    prefix = PROGRAM_PREFIX.upper()
    return [str(p.Name)[len(PROGRAM_PREFIX):] for p in idf.idfobjects['EnergyManagementSystem:Program']
            if str(p.Name).upper().startswith(prefix)]


def set_hook_setpoints_code(idf, zones: Sequence[str]) -> None:
    """Add to a model with the ACCIS (of accim 1.0.0 or later) the EMS objects with which a hook gives its setpoints to
    some zones (see the module): the global variables of each zone, its program ApplyHookSetpoints_<zone> and the line
    that runs it in RunACCIS_<zone> right after SetAST (before the program of the floor and ceiling of the setpoints,
    if the zone has it), and the program InitHookSetpoints with its program calling manager at the beginning of each
    environment. The objects that the model has already are kept (written again), so the hooks of the ATHB and of the
    SET share them.

    :param zones: The zones, by their names in the EMS objects (``Block1_Zone1``...).
    :raises ValueError: If the program RunACCIS_<zone> of a zone does not run SetAST.
    """
    from accim.sim.ems.programs import add_program, set_program_lines
    from accim.sim.ems.setpoint_limits import _declared, _insert_run_line

    zones = list(zones)
    declared = _declared(idf)
    for zone in zones:
        new = [name for name in zone_variables(zone) if name.upper() not in declared]
        if new:
            idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                             **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(new, start=1)})
        name = f'{PROGRAM_PREFIX}{zone}'
        existing = idf.getobject('EnergyManagementSystem:Program', name)
        if existing is None:
            add_program(idf, name, program_lines(zone))
        else:
            set_program_lines(existing, program_lines(zone))
        _insert_run_line(idf, zone, f'{_RUN_PREFIX}{name}', 'run SetAST')
    all_zones = hook_zones(idf)
    init = idf.getobject('EnergyManagementSystem:Program', INIT_PROGRAM)
    if init is None:
        add_program(idf, INIT_PROGRAM, init_program_lines(all_zones))
    else:
        set_program_lines(init, init_program_lines(all_zones))
    if idf.getobject('EnergyManagementSystem:ProgramCallingManager', INIT_PROGRAM) is None:
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=INIT_PROGRAM,
                         EnergyPlus_Model_Calling_Point='BeginNewEnvironment', Program_Name_1=INIT_PROGRAM)
