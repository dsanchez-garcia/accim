# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Constants used in the whole package."""

__all__ = [
    'ENERGYPLUS_VERSIONS_WITH_SPACES',
    'SUPPORTED_ENERGYPLUS_VERSIONS',
]

#: EnergyPlus versions that accim supports (the value 'auto' reads the version of each IDF).
SUPPORTED_ENERGYPLUS_VERSIONS = (
    '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1', '22.2', '23.1', '23.2', '24.1', '24.2', '25.1', '25.2',
    '26.1', '26.2',
)

#: EnergyPlus versions with Space and SpaceList objects.
ENERGYPLUS_VERSIONS_WITH_SPACES = (
    '9.6', '22.1', '22.2', '23.1', '23.2', '24.1', '24.2', '25.1', '25.2', '26.1', '26.2',
)
