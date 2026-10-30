# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Lists of accim 0.x, kept for compatibility: use :mod:`accim.constants`."""

from accim.constants import ENERGYPLUS_VERSIONS_WITH_SPACES, SUPPORTED_ENERGYPLUS_VERSIONS

#: The EnergyPlus versions that accim supports, and 'auto'
fullEPversionsList = list(SUPPORTED_ENERGYPLUS_VERSIONS) + ['auto']
#: The EnergyPlus versions with Space and SpaceList objects
epvers_space_objs = list(ENERGYPLUS_VERSIONS_WITH_SPACES)
