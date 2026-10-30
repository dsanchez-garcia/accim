# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Add the Adaptive-Comfort-Control Implementation Script (ACCIS) to EnergyPlus models.

- :mod:`accim.sim.accis`: :class:`~accim.sim.accis.AddAccis` (IDF files) and
  :func:`~accim.sim.accis.add_accis_to_idf` (IDF objects).
- :mod:`accim.sim.apmv`: setpoints based on the adaptive predicted mean vote (aPMV).
- :mod:`accim.sim.energyplus_api`: runs the ACCIS with the Python API of EnergyPlus instead of its EMS.

The modules are imported when they are first used, so that ``import accim.sim`` is fast.
"""

import importlib

__all__ = ['AddAccis', 'add_accis_to_idf', 'gen_outputs_df', 'modify_accis']

_LAZY = {name: 'accim.sim.accis' for name in __all__}


def __getattr__(name):
    if name in _LAZY:
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
