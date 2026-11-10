# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The static setpoints of the comfort standards whose standard does not give them (proposal B4 of accim 1.2.0,
decision D2 of its brief, and section 6.2 of ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md``).

The setpoints of JPN Aqilah 2025 (comfort standard 23) are static in comfort mode 0, and out of the applicability limits
in comfort mode 1; its paper gives no static setpoints (Aqilah, Rijal, Yoshida & Nicol, 2025), so they are a choice of
the user (decision D2): 20 °C for heating and 28 °C for cooling by default. They are the inputs ``StaticAHST`` and
``StaticACST`` of the program SetInputData_<zone> of its zones (the arguments ``static_heating_setpoint`` and
``static_cooling_setpoint`` of :class:`accim.sim.accis.AddAccis`, :func:`accim.sim.accis.modify_accis` and
``zone_arguments``, and the parameters of the same names of the parametric module), which its subprograms
SetAST_CS23_<chunk> read: ``set ACST = StaticACST+ACSTtol`` and ``set AHST = StaticAHST+AHSTtol``.

The other comfort standards have the static setpoints of their standards (or those of the YAML file of a comfort
standard defined by its data, :mod:`accim.sim.standards`), so they ignore these arguments, and their zones do not have
these inputs: their output IDFs do not change. The models with the EMS code of JPN Aqilah 2025 (its subprograms) declare
the EMS global variables StaticAHST and StaticACST (:func:`set_static_setpoint_variables`).
"""

import numbers
from typing import Any, Dict, Iterable, Optional

__all__ = [
    'ARGUMENTS',
    'COMFORT_STANDARDS',
    'DEFAULTS',
    'INPUTS',
    'check_static_setpoints',
    'has_static_setpoints',
    'set_static_setpoint_variables',
    'static_setpoint_values',
]

#: The inputs of the static heating and cooling setpoints (SetInputData_<zone>)
INPUTS = ('StaticAHST', 'StaticACST')
#: Their arguments
ARGUMENTS = ('static_heating_setpoint', 'static_cooling_setpoint')
#: Their defaults (°C): those of decision D2 of the brief of 1.2.0 for JPN Aqilah 2025
DEFAULTS = (20.0, 28.0)
#: The comfort standards whose static setpoints are these inputs: those whose standard does not give them
COMFORT_STANDARDS = frozenset({23})
_SUBPROGRAM_PREFIX = 'SetAST_CS'


def has_static_setpoints(comfort_standard: Any) -> bool:
    """True if the static setpoints of a comfort standard are the inputs StaticAHST and StaticACST of its zones."""
    try:
        return int(comfort_standard) in COMFORT_STANDARDS
    except (TypeError, ValueError):
        return False


def check_static_setpoints(heating: Any, cooling: Any, where: str = '') -> None:
    """Check the static heating and cooling setpoints: numbers (°C), and the heating one lower than the cooling one, as
    in the static setpoints of the comfort standards defined by their data.

    :param where: The zone, for the messages.
    :raises ValueError: If they are not valid.
    """
    suffix = f' (zone {where!r})' if where else ''
    for name, value in zip(ARGUMENTS, (heating, cooling)):
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValueError(f'{name} must be a number (°C){suffix}, not {value!r}.')
    if not heating < cooling:
        raise ValueError(f'static_heating_setpoint ({heating}) must be lower than static_cooling_setpoint '
                         f'({cooling}){suffix}.')


def static_setpoint_values(arguments: Dict[str, Any], current: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The values of the inputs StaticAHST and StaticACST of a zone: those of ``arguments`` (by argument name), those
    of ``current`` (the inputs that the zone has, by EMS variable) or the defaults."""
    current = current or {}
    return {variable: arguments.get(argument) if arguments.get(argument) is not None
            else current.get(variable, default)
            for variable, argument, default in zip(INPUTS, ARGUMENTS, DEFAULTS)}


def _declared(idf) -> set:
    return {str(name).strip().upper() for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
            for name in g.fieldvalues[1:] if str(name).strip()}


def _has_code(idf, comfort_standards: Iterable[int]) -> bool:
    """True if the model has the subprograms SetAST_CS<n>_<chunk> of one of some comfort standards."""
    prefixes = tuple(f'{_SUBPROGRAM_PREFIX}{number}_'.upper() for number in comfort_standards)
    return any(str(program.Name).upper().startswith(prefixes)
               for program in idf.idfobjects['EnergyManagementSystem:Program'])


def set_static_setpoint_variables(idf) -> None:
    """Declare the EMS global variables StaticAHST and StaticACST (in one object) if the model has the EMS code of a
    comfort standard whose static setpoints are inputs (its subprograms), and remove that object otherwise."""
    objects = [g for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
               if [str(v).strip() for v in g.fieldvalues[1:] if str(v).strip()] == list(INPUTS)]
    if _has_code(idf, COMFORT_STANDARDS):
        if not objects and not {name.upper() for name in INPUTS} <= _declared(idf):
            idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                             **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(INPUTS, start=1)})
    else:
        for obj in objects:
            idf.removeidfobject(obj)
