# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Constants used in the whole package."""

__all__ = [
    'APMV_ADAPTIVE_COEFFICIENTS',
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

_ZHANG_2024 = '10.1016/j.buildenv.2024.111481 (Zhang, Yao and Li, 2024), Table 6 (lambda_N)'
_GB_T_50785 = 'GB/T 50785-2012, via 10.1016/j.buildenv.2024.111481 (Zhang, Yao and Li, 2024), Table 1'


def _zhang_2024(koppen: str, heating, cooling) -> dict:
    return {'cooling': cooling, 'heating': heating, 'grade': 'literature', 'source': _ZHANG_2024,
            'notes': f'Koppen {koppen}: naturally ventilated buildings of the ASHRAE Global Thermal Comfort Database II'}


#: The adaptive coefficients λ of the aPMV, aPMV = PMV/(1 + λ·PMV) (Yao, Li and Liu, 2009), of the literature, by key:
#: ``cooling``, the λ of warm sensations (PMV >= 0), and ``heating``, that of cool sensations (PMV < 0), which
#: :func:`accim.sim.apmv.apply_apmv_setpoints` takes as ``adaptive_coefficient_cooling`` and
#: ``adaptive_coefficient_heating`` (in the cooling and heating seasons, or by the sign of the PMV with
#: ``adaptive_coefficient_by='pmv_sign'``); ``grade``, 'standard' (Yao et al., 2009, and the Chinese standard
#: GB/T 50785-2012) or 'literature' (the λN of each Köppen zone of Zhang, Yao and Li, 2024, fitted to the ASHRAE Global
#: Thermal Comfort Database II: many saturate at the limit ±0.66 of the fit, and some signs contradict the adaptive
#: mechanism, so accim warns when they are used); ``source`` and ``notes``. The Köppen zone Aw has no λ of cool
#: sensations (None). From section 11.2 and proposal A3 of ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md``.
APMV_ADAPTIVE_COEFFICIENTS = {
    'yao2009_chongqing_classrooms': {
        'cooling': 0.293, 'heating': -0.125, 'grade': 'standard', 'source': '10.1016/j.buildenv.2009.02.014',
        'notes': 'Free-running classrooms, Chongqing (Yao, Li and Liu, 2009, Building and Environment 44, 2089-2096)'},
    'gbt50785_cold_general': {
        'cooling': 0.24, 'heating': -0.50, 'grade': 'standard', 'source': _GB_T_50785,
        'notes': 'Severe cold and cold zones; residential, commercial, hotel and office buildings'},
    'gbt50785_cold_education': {
        'cooling': 0.21, 'heating': -0.29, 'grade': 'standard', 'source': _GB_T_50785,
        'notes': 'Severe cold and cold zones; educational buildings'},
    'gbt50785_hscw_hsww_mild_general': {
        'cooling': 0.21, 'heating': -0.49, 'grade': 'standard', 'source': _GB_T_50785,
        'notes': 'Hot summer and cold winter, hot summer and warm winter, and mild zones; residential, commercial, '
                 'hotel and office buildings'},
    'gbt50785_hscw_hsww_mild_education': {
        'cooling': 0.17, 'heating': -0.28, 'grade': 'standard', 'source': _GB_T_50785,
        'notes': 'Hot summer and cold winter, hot summer and warm winter, and mild zones; educational buildings'},
    'zhang2024_Af': _zhang_2024('Af', 0.66, 0.66),
    'zhang2024_Am': _zhang_2024('Am', -0.66, 0.46),
    'zhang2024_Aw': _zhang_2024('Aw', None, 0.36),
    'zhang2024_BSh': _zhang_2024('BSh', -0.56, 0.66),
    'zhang2024_BSk': _zhang_2024('BSk', -0.66, 0.09),
    'zhang2024_BWh': _zhang_2024('BWh', -0.66, 0.34),
    'zhang2024_Cfa': _zhang_2024('Cfa', 0.1, 0.41),
    'zhang2024_Cfb': _zhang_2024('Cfb', -0.41, -0.23),
    'zhang2024_Csa': _zhang_2024('Csa', -0.66, 0.29),
    'zhang2024_Csb': _zhang_2024('Csb', -0.25, 0.55),
    'zhang2024_Csc': _zhang_2024('Csc', -0.66, -0.66),
    'zhang2024_Cwb': _zhang_2024('Cwb', -0.66, 0.55),
    'zhang2024_Dfb': _zhang_2024('Dfb', -0.66, -0.66),
    'zhang2024_Dwa': _zhang_2024('Dwa', -0.66, -0.07),
}
