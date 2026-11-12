# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Constants used in the whole package."""

__all__ = [
    'APMV_ADAPTIVE_COEFFICIENTS',
    'ASHRAE55_MAX_CLOTHING_INSULATION',
    'EN16798_SEASON_RUNNING_MEANS',
    'EN16798_TABLE_B2',
    'EN16798_TABLE_B5',
    'ENERGYPLUS_VERSIONS_WITH_SPACES',
    'EPMV_EXPECTANCY_RANGES',
    'EPMV_MET_REDUCTION_PER_PMV',
    'PMV_BODY_SURFACE_AREA',
    'PMV_INPUT_RANGES',
    'PMV_MET_RANGE',
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

#: The body surface area (m²) with which the metabolic rate per person is divided to get it per unit of area: the
#: commonly accepted mean value of ISO 7730:2025 (section 4), A_Du = 1.8 m², which the Engineering Reference of
#: EnergyPlus gives for all its thermal comfort models (25.2, section 19.1) and its Fanger and KSU models take; the code
#: of its Pierce model divides the activity level by 1.8258 m² (``BodySurfAreaPierce``, ThermalComfort.hh of EnergyPlus
#: 25.1), 1.4 % less met from the same schedule (task E-F1 of accim 1.2.0, measured again on 2026-11-12).
PMV_BODY_SURFACE_AREA = 1.8

#: The ranges of the inputs of the PMV within which ISO 7730:2025 (section 4) uses the PMV: the metabolic rate,
#: 46 to 232 W/m² (0.8 to 4 met), here per person, as the activity level of the People objects of EnergyPlus
#: (W/person), with :data:`PMV_BODY_SURFACE_AREA` (82.8 to 417.6 W/person); the clothing insulation, 0 to 2 clo
#: (0 to 0.310 m²·K/W); and the relative air velocity, 0 to 1 m/s. The parameters ``activity_level``,
#: ``clothing_insulation`` and ``air_velocity`` of the parametric module warn outside them (proposal C1).
PMV_INPUT_RANGES = {
    'activity_level': (46 * PMV_BODY_SURFACE_AREA, 232 * PMV_BODY_SURFACE_AREA),
    'clothing_insulation': (0.0, 2.0),
    'air_velocity': (0.0, 1.0),
}

#: The range of the metabolic rate (met) within which ISO 7730:2025 (section 4) uses the PMV, as it gives it in met
#: (46 to 232 W/m², 1 met being 58.2 W/m²): the hook of the ATHB (:class:`accim.sim.comfort_hooks.AthbSetpointHook`)
#: warns outside it (task H4 of the review of accim 1.2.0, finding A4-3).
PMV_MET_RANGE = (0.8, 4.0)

#: The largest clothing insulation (clo) with which ASHRAE 55-2020 uses the PMV (section 11.3 of
#: ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md``): the parameter ``clothing_insulation`` of the parametric module
#: warns above it.
ASHRAE55_MAX_CLOTHING_INSULATION = 1.5

#: The default design values of the indoor operative temperature (°C) of EN 16798-1:2019, Table B.2, for buildings
#: with mechanical cooling systems, by type of building and category: (minimum for heating, in winter, about 1.0 clo;
#: maximum for cooling, in summer, about 0.5 clo), with sedentary activity (about 1.2 met), 50 % of relative humidity
#: and air speeds below 0.1 m/s. 'residential' are the living spaces of residential buildings (bedrooms, living
#: rooms...), and 'office' the offices and spaces with similar activity (meeting rooms, auditoria, cafeterias,
#: restaurants, classrooms...). B.2.2 applies them in winter also to the buildings without mechanical cooling systems,
#: whose adaptive limits (Figure B.1) apply in summer and the mid-seasons. They are the arguments
#: ``heating_setpoint_minimum`` and ``cooling_setpoint_maximum`` of :class:`accim.sim.accis.AddAccis` (proposal B5 of
#: ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md``).
EN16798_TABLE_B2 = {
    ('residential', 1): (21.0, 25.5),
    ('residential', 2): (20.0, 26.0),
    ('residential', 3): (18.0, 27.0),
    ('residential', 4): (16.0, 28.0),
    ('office', 1): (21.0, 25.5),
    ('office', 2): (20.0, 26.0),
    ('office', 3): (19.0, 27.0),
    ('office', 4): (18.0, 28.0),
}

#: The temperature ranges (°C) for the hourly calculation of the heating and cooling energy of EN 16798-1:2019, Table
#: B.5 (B.2.4), by type of building and category: ((lower, upper) of the heating seasons, with about 1.0 clo; (lower,
#: upper) of the cooling seasons, with about 0.5 clo), with sedentary activity (about 1.2 met), air speeds below 0.1
#: m/s and a relative humidity of about 40 % in the heating season and 60 % in the cooling season. 'residential' are
#: the living spaces of the residential buildings, and 'office' the offices and spaces with similar activity, as in
#: :data:`EN16798_TABLE_B2`, whose minimums for heating and maximums for cooling they have as the lower limit of the
#: heating season and the upper limit of the cooling season, but in category IV (17.0 °C in both types of building;
#: 16.0 and 18.0 °C in Table B.2). Read in UNE-EN 16798-1:2020, p. 54, on 2026-11-12 (finding A15 of the self-audit of
#: 2026-11-11): the seasonal range of the long-term discomfort, ``long_term_range=('en16798_seasonal', category,
#: building_type)`` (:mod:`accim.sim.ems.long_term_discomfort`).
EN16798_TABLE_B5 = {
    ('residential', 1): ((21.0, 25.0), (23.5, 25.5)),
    ('residential', 2): ((20.0, 25.0), (23.0, 26.0)),
    ('residential', 3): ((18.0, 25.0), (22.0, 27.0)),
    ('residential', 4): ((17.0, 25.0), (21.0, 28.0)),
    ('office', 1): ((21.0, 23.0), (23.5, 25.5)),
    ('office', 2): ((20.0, 24.0), (23.0, 26.0)),
    ('office', 3): ((19.0, 25.0), (22.0, 27.0)),
    ('office', 4): ((17.0, 25.0), (21.0, 28.0)),
}

#: The running mean outdoor temperatures (°C) between which the note of Table B.5 of EN 16798-1:2019 places the
#: intervals between the heating and cooling seasons (θrm between 10 and 15 °C, in which "temperature limits that lie
#: within the winter and summer values" can be used): the heating season below the first one and the cooling season
#: above the second one (CEN/TR 16798-2:2019, 7.2.2 and the remarks on its Figure B.1, applies the criteria of the
#: heating season below a running mean of 10 °C; the decision of 2026-11-12 on finding A15, ``notes/decisions.md``).
EN16798_SEASON_RUNNING_MEANS = (10.0, 15.0)

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
