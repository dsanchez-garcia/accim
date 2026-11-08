# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Utilities for the EnergyPlus models and simulations.

The functions are in submodules, which are imported when a function is used (some of them need besos,
which takes long to import):

- :mod:`accim.utils.people`: the occupants, zones and spaces of the models.
- :mod:`accim.utils.editing`: functions that edit the models (timesteps, occupancy, run period...).
- :mod:`accim.utils.accim_args`: the arguments of the ACCIS of a model.
- :mod:`accim.utils.ems_code`: the EMS code with which the ACCIS calculates the setpoints of a comfort standard,
  category and comfort mode, to read it before adding the ACCIS to a model (``print_setpoint_ems_code``).
- :mod:`accim.utils.versions`: the IDD files and the transition of IDF files to newer EnergyPlus versions.
- :mod:`accim.utils.outputs`: the outputs available in a model, and the ESO files.
- :mod:`accim.utils.verification`: verification of the simulations of the models of accim.
- :mod:`accim.utils.workspace`: cleaning of the files that the simulations write.
- :mod:`accim.utils.session`: sessions saved in a pickle file, to resume them, and in a JSON file, to read them
  (``save_session`` and ``load_session``).

All the functions can be imported from :mod:`accim.utils`, as in accim 0.x
(for instance, ``from accim.utils import reduce_runtime``).
"""

import importlib
from typing import Any, List

#: The submodule of each function
_SUBMODULES = {
    'get_people_objects': 'people',
    'is_people_instance': 'people',
    'get_people_definition': 'people',
    'SURFACE_OBJECTS_WITH_SPACE_NAME': 'people',
    'get_energyplus_spaces': 'people',
    'get_people_instances': 'people',
    'get_people_hierarchy': 'people',
    'get_people_names_for_ems': 'people',
    'get_idf_hierarchy': 'people',
    'get_idf_hierarchy_with_people': 'people',
    'get_spaces_from_spacelist': 'people',
    'modify_timesteps': 'editing',
    'modify_timesteps_path': 'editing',
    'set_occupancy_to_always': 'editing',
    'set_occupancy_to_always_path': 'editing',
    'reduce_runtime': 'editing',
    'amend_idf_version_from_dsb': 'editing',
    'transform_ddmm_to_int': 'editing',
    'remove_accents': 'editing',
    'remove_accents_in_idf': 'editing',
    'get_available_fields': 'editing',
    'convert_standard_to_comfort_thermostats': 'editing',
    'inspect_thermostat_objects': 'editing',
    'set_operative_temp_control': 'editing',
    'get_accim_args': 'accim_args',
    'get_accim_args_flattened': 'accim_args',
    'get_setpoint_ems_code': 'ems_code',
    'print_setpoint_ems_code': 'ems_code',
    'get_idd_path_from_ep_version': 'versions',
    'update_idf_version': 'versions',
    'print_available_outputs_mod': 'outputs',
    'read_eso_using_readvarseso': 'outputs',
    'identify_variable_key_pattern': 'outputs',
    'verify_accim_simulation': 'verification',
    'AccimSimulationVerifier': 'verification',
    'WorkspaceArtifactCleaner': 'workspace',
    'save_session': 'session',
    'load_session': 'session',
}
#: Functions of besos that accim 0.x imported in this module, which some scripts import from it
_BESOS_FUNCTIONS = {
    'get_building': 'besos.eppy_funcs',
    'run_building': 'besos.eplus_funcs',
    'get_idf_version': 'besos.eplus_funcs',
}

__all__ = sorted(_SUBMODULES)


def __getattr__(name: str) -> Any:
    if name in _SUBMODULES:
        value = getattr(importlib.import_module(f'accim.utils.{_SUBMODULES[name]}'), name)
    elif name in _BESOS_FUNCTIONS:
        value = getattr(importlib.import_module(_BESOS_FUNCTIONS[name]), name)
    else:
        raise AttributeError(f"module 'accim.utils' has no attribute {name!r}")
    globals()[name] = value
    return value


def __dir__() -> List[str]:
    return sorted(set(globals()) | set(__all__) | set(_BESOS_FUNCTIONS))
