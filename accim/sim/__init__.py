# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Add the Adaptive-Comfort-Control Implementation Script (ACCIS) to EnergyPlus models.

- :mod:`accim.sim.accis`: :class:`~accim.sim.accis.AddAccis` (IDF files) and
  :func:`~accim.sim.accis.add_accis_to_idf` (IDF objects).
- :mod:`accim.sim.apmv`: setpoints based on the adaptive predicted mean vote (aPMV) and the PMV.
- :mod:`accim.sim.pmv_index`: the engine of the setpoints based on indices derived from the PMV.
- :mod:`accim.sim.preview`: the setpoints of the ACCIS and the outdoor temperatures of reference of the adaptive
  comfort models, calculated from a weather file without EnergyPlus.
- :mod:`accim.sim.energyplus_api`: runs the ACCIS with the Python API of EnergyPlus instead of its EMS.
- :mod:`accim.sim.standards`: the comfort standards, and those defined by their data
  (:func:`~accim.sim.standards.load_comfort_standards` and :func:`~accim.sim.standards.register_comfort_standard`).

The modules are imported when they are first used, so that ``import accim.sim`` is fast.
"""

import importlib

__all__ = ['AddAccis', 'ComfortStandardDefinition', 'CustomRegime', 'add_accis_to_idf', 'gen_outputs_df',
           'load_comfort_standards', 'modify_accis', 'register_comfort_standard']

_LAZY = {name: 'accim.sim.accis' for name in ('AddAccis', 'add_accis_to_idf', 'gen_outputs_df', 'modify_accis')}
_LAZY['CustomRegime'] = 'accim.sim.arguments'
_LAZY.update(dict.fromkeys(('ComfortStandardDefinition', 'load_comfort_standards', 'register_comfort_standard'),
                           'accim.sim.standards'))


def __getattr__(name):
    if name in _LAZY:
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
