# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Run the models of accim with the Python API of EnergyPlus (pyenergyplus), as an alternative to its EMS.

The output IDFs of accim control the setpoints with EMS programs, which EnergyPlus runs with its EMS.
This backend runs the same programs in Python, in the callbacks of the Python API of EnergyPlus, with
the rules of the EMS (see :mod:`accim.sim.ems.erl` and :mod:`accim.sim.energyplus_api.controller`),
so the results are the same, and Python code can read and change the variables of the programs
during the simulation::

    from accim.sim.energyplus_api import run_simulation

    def raise_cooling_setpoints(controller, calling_point):
        if calling_point == 'BEGINTIMESTEPBEFOREPREDICTOR':
            for name in ('ACST_ACT_BLOCK1_ZONE1',):
                controller.set(name, controller.get(name) + 1)

    run_simulation('model[CS_INT EN16798[...].idf', 'weather.epw', after_programs=[raise_cooling_setpoints])

:func:`accim.run.run_ep` runs the IDFs and EPWs of a folder with ``backend='api'``.
"""

from accim.sim.energyplus_api.controller import CALLING_POINTS, ErlController
from accim.sim.energyplus_api.idf import EmsDefinition, objects_for_api, parse_idf, read_ems, read_idf, render_idf
from accim.sim.energyplus_api.runner import SimulationResult, run_simulation, run_simulations
from accim.sim.energyplus_api.runtime import MINIMUM_API_VERSION, load_energyplus_api

__all__ = [
    'CALLING_POINTS',
    'EmsDefinition',
    'ErlController',
    'MINIMUM_API_VERSION',
    'SimulationResult',
    'load_energyplus_api',
    'objects_for_api',
    'parse_idf',
    'read_ems',
    'read_idf',
    'render_idf',
    'run_simulation',
    'run_simulations',
]
