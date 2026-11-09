# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Constants used in the whole package."""

__all__ = [
    'ENERGYPLUS_VERSIONS_WITH_SPACES',
    'EPMV_EXPECTANCY_RANGES',
    'EPMV_MET_REDUCTION_PER_PMV',
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

#: The expectancy factor e of the ePMV for each expectation of the occupants of buildings without air-conditioning
#: in warm climates (Fanger and Toftum, 2002, Table 1): high, in regions where air-conditioned buildings are common
#: and the warm periods are brief, in summer; moderate, in regions with some air-conditioned buildings and a warm
#: summer; low, in regions with few air-conditioned buildings and warm weather in all seasons. In their validation,
#: e was 0.6 in Bangkok, 0.7 in Singapore and Athens, and 0.9 in Brisbane (Table 2).
EPMV_EXPECTANCY_RANGES = {'high': (0.9, 1.0), 'moderate': (0.7, 0.9), 'low': (0.5, 0.7)}

#: The reduction of the metabolic rate for each unit of PMV above neutral (Fanger and Toftum, 2002): the PMV is
#: calculated again with the activity level multiplied by 1 - 0.067·PMV.
EPMV_MET_REDUCTION_PER_PMV = 0.067
