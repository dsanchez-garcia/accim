# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Deprecated module of accim 0.x: use :mod:`accim.sim.apmv`."""

import warnings

from accim._besos_compat import patch_besos_read_eso
from accim.sim.apmv import *  # noqa: F401,F403
from accim.sim.apmv import __all__, _resolve_targets, _sanitize_ems_name  # noqa: F401

warnings.warn('accim.sim.apmv_setpoints is deprecated since accim 1.0.0; use accim.sim.apmv instead.',
              DeprecationWarning, stacklevel=2)
# accim 0.x patched besos when this module was imported
patch_besos_read_eso()
