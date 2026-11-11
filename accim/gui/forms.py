# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The forms of the graphical user interface of accim: their choices and defaults, and the arguments of the functions
of accim that they give, checked.

This module does not use tkinter, so that the forms can be tested without a display: :mod:`accim.gui.app` reads the
values of its widgets into a dictionary (texts, booleans and lists of the selected choices) and passes it to these
functions; :mod:`accim.gui.tasks` runs accim with the arguments that they give.
"""

import os
import re
import warnings
from typing import Any, Dict, Iterable, List, Mapping, Tuple, Union

from accim.constants import APMV_ADAPTIVE_COEFFICIENTS, EN16798_TABLE_B2, SUPPORTED_ENERGYPLUS_VERSIONS
from accim.sim.arguments import (DEPRECATED_ARGUMENT_NAMES, MIXED_MODE_SCRIPT_TYPES, OUTPUT_FREQUENCIES,
                                 REGIME_CONDITIONS, SUPPLY_AIR_TEMP_INPUT_METHODS)
from accim.sim.ems.inputs import ZONE_ARGUMENTS, check_zone_arguments
from accim.sim.standards import COMFORT_STANDARDS, HOOK_COMFORT_STANDARDS

__all__ = [
    'ADAPTIVE_COEFFICIENT_BY',
    'ADD_ACCIS_DEFAULTS',
    'APMV_DEFAULTS',
    'APMV_OPTIONS',
    'APMV_SETPOINT_FIELDS',
    'APMV_ZONE_FIELDS',
    'BACKENDS',
    'CUSTOM_MODEL_FIELDS',
    'CUSTOM_OUTDOOR_METRICS',
    'CUSTOM_OUTDOOR_METRIC_FIELDS',
    'CUSTOM_MODEL_PARAMETERS',
    'CUSTOM_REGIMES_HINT',
    'ENERGYPLUS_VERSIONS',
    'EN16798_TABLE_B2_CHOICES',
    'EPMV_OPTIONS',
    'EXISTING_HVAC_AVAILABILITY',
    'EXISTING_HVAC_DEFAULTS',
    'EXISTING_HVAC_OPTIONS',
    'FIGURE_COLORS',
    'FIGURE_TYPES',
    'FormError',
    'HVAC_MODES',
    'OUTPUT_FREQUENCIES',
    'OUTPUT_TYPES',
    'PARAMETRIC_DEFAULTS',
    'PARAMETRIC_SCRIPT_TYPES',
    'PARAMETERS_TYPES',
    'PMV_INDEX_FUNCTIONS',
    'PMV_INDEX_NAMES',
    'PMV_INDEX_PARAMETERS',
    'PMV_INPUT_FIELDS',
    'PREDEFINED_MODEL_PARAMETERS',
    'RENAME_EPWS_DEFAULTS',
    'RUN_DEFAULTS',
    'SAMPLINGS',
    'SCRIPT_TYPES',
    'DRIFT_FIELDS',
    'SETPOINT_LIMIT_FIELDS',
    'SETPOINT_TYPES',
    'STATIC_SETPOINT_FIELDS',
    'STATIC_SETPOINT_STANDARDS',
    'SUPPLY_AIR_TEMP_INPUT_METHODS',
    'TABLE_DEFAULTS',
    'TABLE_FREQUENCIES',
    'TABLE_TYPES',
    'VENTILATION_CONTROLS',
    'VRF_AVAILABILITY',
    'ZONE_ARGUMENTS',
    'ZONE_FIELDS',
    'adaptive_coefficient_choices',
    'adaptive_coefficient_entry',
    'current_names',
    'add_accis_arguments',
    'apmv_arguments',
    'apmv_zone_row_text',
    'apmv_zone_setpoints',
    'categories_hint',
    'comfort_modes_hint',
    'comfort_standard_choices',
    'custom_regime_arguments',
    'epw_files',
    'existing_hvac_arguments',
    'figure_arguments',
    'hours_zones',
    'idf_files',
    'index_setpoint_fields',
    'input_idfs',
    'output_idf_count',
    'parametric_arguments',
    'parametric_simulation_count',
    'parse_apmv_zone_setpoints',
    'parse_custom_regimes',
    'parse_mapping',
    'parse_number',
    'parse_numbers',
    'parse_parameter_values',
    'parse_zone_arguments',
    'registered_metric_standards',
    'rename_epws_arguments',
    'results_size_arguments',
    'run_ep_arguments',
    'setpoint_ems_code_calls',
    'drift_arguments',
    'setpoint_limit_arguments',
    'simulation_csvs',
    'simulations',
    'split_apmv_zone_setpoints',
    'split_zone_arguments',
    'static_setpoint_arguments',
    'table_arguments',
    'weather_file_arguments',
    'weather_file_standards',
    'zone_arguments',
    'zone_arguments_problems',
    'zone_field_choices',
    'zone_row_text',
]

Number = Union[int, float]

#: The script types, with their descriptions.
SCRIPT_TYPES = {
    'vrf_ac': 'VRF systems added by accim, full air-conditioning',
    'vrf_mm': 'VRF systems added by accim, mixed mode (air-conditioning and natural ventilation)',
    'ex_ac': 'Existing HVAC systems of the model, full air-conditioning',
    'ex_mm': 'Existing HVAC systems of the model, mixed mode (air-conditioning and natural ventilation)',
}
#: The output types (not 'custom', which asks in the prompt which outputs to keep).
OUTPUT_TYPES = ('standard', 'simplified', 'detailed')
#: The values of setpoint_type, with their descriptions.
SETPOINT_TYPES = {'temperature': 'Adaptive setpoint temperatures', 'pmv': 'PMV-based setpoints (Fanger)'}
ENERGYPLUS_VERSIONS = ('auto',) + tuple(SUPPORTED_ENERGYPLUS_VERSIONS)
HVAC_MODES = {0: 'Full air-conditioning', 1: 'Natural ventilation only', 2: 'Mixed mode'}
#: The values of ventilation_control, with their descriptions.
VENTILATION_CONTROLS = {
    0: 'Above the comfort temperature; windows fully open',
    1: 'Above the lower comfort limit; windows fully open',
    2: 'Above the comfort temperature; opening factor',
    3: 'Above the lower comfort limit; opening factor',
}
BACKENDS = {'ems': 'Energy Management System of EnergyPlus', 'api': 'Python API of EnergyPlus (24.2 or later)'}
#: The arguments of the custom comfort model (comfort_standard 99): argument -> (label, default). The defaults are
#: those of ASHRAE 55 with 80 % acceptability, as in the parametric module.
CUSTOM_MODEL_FIELDS = {
    'custom_slope': ('Slope m (comfort temperature = m·T + n)', '0.31'),
    'custom_intercept': ('Intercept n', '17.8'),
    'custom_cooling_offset': ('Offset of the cooling setpoint (°C)', '3.5'),
    'custom_heating_offset': ('Offset of the heating setpoint (°C)', '-3.5'),
    'custom_cooling_upper_limit': ('Upper applicability limit, cooling (°C)', '33.5'),
    'custom_cooling_lower_limit': ('Lower applicability limit, cooling (°C)', '10'),
    'custom_heating_upper_limit': ('Upper applicability limit, heating (°C)', '33.5'),
    'custom_heating_lower_limit': ('Lower applicability limit, heating (°C)', '10'),
}
#: The outdoor metrics of the custom comfort model (custom_outdoor_metric, accim.sim.ems.outdoor_metric), with their
#: descriptions, in the order of their codes.
CUSTOM_OUTDOOR_METRICS = {
    'pmot': 'Running mean of ASHRAE 55 that EnergyPlus calculates (as before accim 1.2.0)',
    'rmot': 'Running mean of CEN 15251 that EnergyPlus calculates',
    'rmot_alpha': 'Running mean of EN 16798-1 (B.1), with the alpha below',
    'rmot_7day': 'Running mean of EN 16798-1, approximate formula (B.2): 7 days',
    'daily_mean': 'Daily mean outdoor temperature of the previous day',
    'ndrm': 'Mean of the daily means of the days below (ASHRAE 55-2020, 5.4.2.1)',
    'monthly_mean': 'Monthly mean of the weather file (it needs the weather file)',
    'te_ref_nl': 'Te,ref of the Dutch ATG (van der Linden et al., 2006)',
}
#: The numbers of the outdoor metric of the custom model: argument -> (label, default).
CUSTOM_OUTDOOR_METRIC_FIELDS = {
    'custom_alpha': ('Alpha of rmot_alpha (0.6 to 0.9; EN 16798-1: 0.8)', '0.8'),
    'custom_days': ('Days of ndrm (7 to 30)', '30'),
}
#: How the field of the regimes of the custom model (custom_regimes, accim.sim.ems.custom_regimes) is written.
CUSTOM_REGIMES_HINT = (
    'Regimes (empty: none), in their order of priority, separated by semicolons: condition: slope intercept '
    'cooling-offset heating-offset cooling-lower-limit cooling-upper-limit heating-lower-limit heating-upper-limit. '
    'Conditions: always (the last one), cooling_season, heating_season, hvac_off, hvac_on (mixed mode), '
    'metric_below x, metric_above x, metric_between x1 x2 (of the outdoor metric of the zone). If none holds, the '
    'coefficients above apply. A regime can have its own outdoor metric after the coefficients: '
    'outdoor_metric=name, and alpha=x (rmot_alpha) or days=n (ndrm). For instance: '
    'metric_below 10: 0.31 17.8 3.5 -3.5 10 33.5 10 33.5 outdoor_metric=rmot_alpha alpha=0.7; '
    'always: 0.33 18.8 2 -3 10 30 10 30'
)
#: The options of a regime of the custom model in its field, after the coefficients (``name=value``)
_REGIME_OPTIONS = ('outdoor_metric', 'alpha', 'days')
#: The minimum heating setpoint and the maximum cooling setpoint (accim.sim.ems.setpoint_limits), which
#: are None if their fields are empty: argument -> (label, default).
SETPOINT_LIMIT_FIELDS = {
    'heating_setpoint_minimum': ('Minimum heating setpoint (°C; empty: none)', ''),
    'cooling_setpoint_maximum': ('Maximum cooling setpoint (°C; empty: none)', ''),
}
#: The limiter of the drift of the setpoints (accim.sim.ems.drift_limiter, task F2 of block F): argument -> (label,
#: default); with drift_mode empty, there is no limiter and the other fields are not used.
DRIFT_FIELDS = {
    'drift_mode': ('Limiter of the drift (empty: none; rate or window)', ''),
    'max_drift_rate': ('rate: largest change from one day to the next (K/day)', '0.5'),
    'alpha_indoor': ('window: alpha of the running mean T_rm_in', '0.8'),
    'delta_cool': ('window: distance above T_rm_in (K)', '1.0'),
    'delta_heat': ('window: distance below T_rm_in (K)', '1.0'),
    'initial_T_rm_in': ('window: first T_rm_in (°C; empty: the first occupied day)', ''),
}
#: The static setpoints of JPN Aqilah 2025 (accim.sim.ems.static_setpoints), whose paper gives none: argument ->
#: (label, default).
STATIC_SETPOINT_FIELDS = {
    'static_heating_setpoint': ('Static heating setpoint of JPN Aqilah 2025 (°C)', '20'),
    'static_cooling_setpoint': ('Static cooling setpoint of JPN Aqilah 2025 (°C)', '28'),
}
#: The comfort standards whose static setpoints are those of STATIC_SETPOINT_FIELDS
STATIC_SETPOINT_STANDARDS = (23,)
_ROMAN = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}
#: The minimum operative temperature for heating and the maximum for cooling of Table B.2 of EN 16798-1:2019
#: (accim.constants.EN16798_TABLE_B2), which fill the fields of the minimum and maximum: description -> (minimum,
#: maximum).
EN16798_TABLE_B2_CHOICES = {
    f'{building.capitalize()}, category {_ROMAN.get(category, category)}: {minimum} / {maximum} °C': (minimum, maximum)
    for (building, category), (minimum, maximum) in EN16798_TABLE_B2.items()
}
#: The constant ranges of the long-term discomfort (``long_term_range`` of AddAccis, the limits of EN 16798-1, Table
#: B.2): the label of :data:`EN16798_TABLE_B2_CHOICES` -> ``('en16798', category, building type)``.
LONG_TERM_RANGE_CHOICES = {
    label: ('en16798', category, building)
    for label, (building, category) in zip(EN16798_TABLE_B2_CHOICES, EN16798_TABLE_B2)
}
#: The options of the existing HVAC systems (script types 'ex_ac' and 'ex_mm') that are booleans: argument -> label.
EXISTING_HVAC_OPTIONS = {
    'existing_hvac_operative_temperature_control': 'The thermostats control the operative temperature',
    'existing_hvac_radiant_setpoints': 'The radiant systems, ventilated slabs and cooling panels follow the setpoints',
    'existing_hvac_widen_outdoor_temperature_limits': 'Widen the outdoor temperature limits (to -20 and 80 °C)',
    'existing_hvac_ideal_loads_backup': 'Backup ideal loads air systems (the loads that the HVAC system does not meet)',
}
#: The suggested availability schedules of the existing HVAC systems ('' keeps the availability of the model).
EXISTING_HVAC_AVAILABILITY = ('', 'On 24/7')
#: The suggested availability schedules of the VRF systems of accim (any schedule of the model can be typed).
VRF_AVAILABILITY = ('On 24/7',)
#: The arguments of a zone that have a field of their own in the table of the zones of the window (the others are
#: written as pairs name=value).
ZONE_FIELDS = ('comfort_standard', 'category', 'comfort_mode', 'hvac_mode', 'ventilation_control')
#: The initial values of the options of the existing HVAC systems (the defaults of AddAccis; the availability schedule
#: '' is None).
EXISTING_HVAC_DEFAULTS = {
    'existing_hvac_operative_temperature_control': True,
    'existing_hvac_radiant_setpoints': True,
    'existing_hvac_widen_outdoor_temperature_limits': False,
    'existing_hvac_ideal_loads_backup': False,
    'existing_hvac_availability_schedule': '',
}
#: The initial values of the form of AddAccis (the texts of the lists are separated by commas or spaces).
ADD_ACCIS_DEFAULTS = {
    'script_type': 'vrf_mm',
    'supply_air_temp_input_method': 'temperature difference',
    'vrf_availability_schedule': 'On 24/7',
    'vrf_eer': '2',
    'vrf_cop': '2.1',
    'setpoint_type': 'temperature',
    'energyplus_version': 'auto',
    'output_type': 'standard',
    'output_frequencies': ['hourly'],
    'keep_existing_outputs': False,
    'add_building_averages': False,
    'debug_ems': False,
    'comfort_standard': [1],
    'category': '3',
    'comfort_mode': '3',
    'category_cooling_offset': '0',
    'category_heating_offset': '0',
    'setpoint_accuracy': '10000',
    'cooling_season_start': '121',
    'cooling_season_end': '274',
    'hvac_mode': [2],
    'ventilation_control': [0],
    'ventilation_setpoint_offset': '0',
    'min_outdoor_temp_offset': '50',
    'max_wind_speed': '50',
    'opening_factor_max_temp_diff': '6',
    'opening_factor_min_temp_diff': '1',
    'min_opening_factor': '0.25',
    'setpoint_tolerance_start': '0.1',
    'setpoint_tolerance_end': '0.1',
    'setpoint_tolerance_step': '0.1',
    'name_suffix': '',
    **{name: default for name, (_, default) in CUSTOM_MODEL_FIELDS.items()},
    'custom_outdoor_metric': 'pmot',
    **{name: default for name, (_, default) in CUSTOM_OUTDOOR_METRIC_FIELDS.items()},
    'epw': '',
    'custom_regimes': '',
    **{name: default for name, (_, default) in SETPOINT_LIMIT_FIELDS.items()},
    **{name: default for name, (_, default) in STATIC_SETPOINT_FIELDS.items()},
    **{name: default for name, (_, default) in DRIFT_FIELDS.items()},
    'report_hours_below': '',
    'report_long_term_discomfort': False,
    'long_term_range': '',
    **EXISTING_HVAC_DEFAULTS,
}
#: The initial values of the form of run_ep (``simulate``: estimate the size of the results with a simulation).
RUN_DEFAULTS = {'only_accim_idfs': True, 'processes': '2', 'energyplus_version': 'auto', 'backend': 'ems',
                'simulate': False}

#: The indices of the PMV-based setpoints, and the functions of accim.sim.apmv that apply them: index -> function.
PMV_INDEX_FUNCTIONS = {'apmv': 'apply_apmv_setpoints', 'epmv': 'apply_epmv_setpoints', 'pmv': 'apply_pmv_setpoints'}
#: The name of each index (in the EMS objects, and in the name of the output IDF, '<input IDF>_<name>.idf').
PMV_INDEX_NAMES = {'apmv': 'aPMV', 'epmv': 'ePMV', 'pmv': 'PMV'}
#: The setpoints of each index that the other indices do not have (those of accim.sim.pmv_index.PMV_INDICES).
PMV_INDEX_PARAMETERS = {'apmv': ('adaptive_coefficient_cooling', 'adaptive_coefficient_heating'),
                        'epmv': ('expectancy_factor',), 'pmv': ()}
#: The setpoints of the PMV-based setpoints (the arguments of apply_apmv_setpoints, apply_epmv_setpoints and
#: apply_pmv_setpoints): argument -> label.
APMV_SETPOINT_FIELDS = {
    'adaptive_coefficient_cooling': 'Adaptive coefficient λ, cooling season or PMV >= 0 (aPMV)',
    'adaptive_coefficient_heating': 'Adaptive coefficient λ, heating season or PMV < 0 (aPMV)',
    'expectancy_factor': 'Expectancy factor e, cooling season (ePMV)',
    'pmv_cooling_setpoint': 'Setpoint for cooling (aPMV, ePMV or PMV)',
    'pmv_heating_setpoint': 'Setpoint for heating (aPMV, ePMV or PMV)',
    'cooling_setpoint_tolerance_cooling_season': 'Tolerance of the cooling setpoint, cooling season',
    'cooling_setpoint_tolerance_heating_season': 'Tolerance of the cooling setpoint, heating season',
    'heating_setpoint_tolerance_cooling_season': 'Tolerance of the heating setpoint, cooling season',
    'heating_setpoint_tolerance_heating_season': 'Tolerance of the heating setpoint, heating season',
}
#: The setpoints that have a field of their own in the table of the zones of the window (the tolerances are
#: written as pairs name=value).
APMV_ZONE_FIELDS = ('adaptive_coefficient_cooling', 'adaptive_coefficient_heating', 'pmv_cooling_setpoint',
                    'pmv_heating_setpoint', 'expectancy_factor')
#: The options of the ePMV setpoints (the arguments of apply_epmv_setpoints): argument -> label.
EPMV_OPTIONS = {
    'apply_to_heating': 'The expectancy factor also on the heating setpoint (apply_to_heating)',
    'metabolic_correction': 'Metabolic correction of the activity level (metabolic_correction)',
}
#: The options of the aPMV setpoints (the arguments of apply_apmv_setpoints): argument -> label.
APMV_OPTIONS = {'adaptive_coefficient_by': 'Adaptive coefficient by (aPMV):'}
#: The ways of choosing the adaptive coefficient of the aPMV (accim.sim.pmv_index.ADAPTIVE_COEFFICIENT_BY): by the
#: season, or by the sign of the PMV of the previous timestep.
ADAPTIVE_COEFFICIENT_BY = ('season', 'pmv_sign')
#: The inputs of the PMV of the People objects (the arguments of set_pmv_input_parameters): argument -> label.
PMV_INPUT_FIELDS = {
    'activity_level': 'Activity level (W/person)',
    'clothing_insulation': 'Clothing insulation (clo)',
    'air_velocity': 'Air velocity (m/s)',
    'work_efficiency': 'Work efficiency (0 to 1)',
}
#: The initial values of the form of the PMV-based setpoints (the defaults of apply_apmv_setpoints and
#: apply_epmv_setpoints; the inputs of the PMV, empty, keep those of the model).
APMV_DEFAULTS = {
    'idf': '',
    'output_idf': '',
    'energyplus_version': 'auto',
    'add_vrf_system': True,
    'supply_air_temp_input_method': 'temperature difference',
    'always_occupied': False,
    'output_frequencies': ['hourly'],
    'other_pmv_related_outputs': True,
    'report_ppd_weighted_hours': False,
    'index': 'apmv',
    'adaptive_coefficients': '',
    'adaptive_coefficient_by': 'season',
    'adaptive_coefficient_cooling': '0.293',
    'adaptive_coefficient_heating': '-0.293',
    'expectancy_factor': '0.8',
    'pmv_cooling_setpoint': '0.5',
    'pmv_heating_setpoint': '-0.5',
    'cooling_setpoint_tolerance_cooling_season': '-0.1',
    'cooling_setpoint_tolerance_heating_season': '-0.1',
    'heating_setpoint_tolerance_cooling_season': '0.1',
    'heating_setpoint_tolerance_heating_season': '0.1',
    'apply_to_heating': False,
    'metabolic_correction': False,
    'cooling_season_start': '121',
    'cooling_season_end': '274',
    **{name: '' for name in PMV_INPUT_FIELDS},
}
#: The initial values of the form of rename_epw_files.
RENAME_EPWS_DEFAULTS = {'epws': [], 'cities': '', 'countries': '', 'delete_originals': False}

#: The frequencies of Table.
TABLE_FREQUENCIES = ('timestep', 'hourly', 'daily', 'monthly', 'runperiod')
#: The predefined tables of Table.format_table.
TABLE_TYPES = ('all', 'energy demand', 'comfort hours', 'temperature')
#: The initial values of the form of Table.
TABLE_DEFAULTS = {
    'idf_path': '',
    'source_frequency': 'hourly',
    'frequency': 'runperiod',
    'frequency_agg_func': 'sum',
    'standard_outputs': True,
    'level': ['building'],
    'level_agg_func': ['sum'],
    'level_excluded_zones': '',
    'split_epw_names': False,
    'long_term_indicators': False,
    'indoor_adaptation_indicators': False,
    'type_of_table': 'all',
    'figure_type': 'scatter',
    'y_axis_label': '',
    'figname': 'accim_figure',
    'figsize': '4',
    'dpi': '150',
}
#: The figures of Table that the interface makes.
FIGURE_TYPES = {'scatter': 'Scatter plot (x axis: a column of the table)',
                'time': 'Time plot (x axis: the date and time)'}
#: The colours of the columns of the y axis of the figures, in order (those of matplotlib by default).
FIGURE_COLORS = ('tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray',
                 'tab:olive', 'tab:cyan')

#: The parameters of the accim predefined models and of the accim custom models of the parametric module (those of
#: accim.parametric_and_optimisation.params_dicts, which imports besos: the interface does not import it to start).
PREDEFINED_MODEL_PARAMETERS = (
    'comfort_standard', 'category', 'category_cooling_offset', 'category_heating_offset', 'comfort_mode',
    'setpoint_accuracy', 'cooling_season_start', 'cooling_season_end', 'hvac_mode', 'ventilation_control',
    'opening_factor_max_temp_diff', 'opening_factor_min_temp_diff', 'min_opening_factor',
    'ventilation_setpoint_offset', 'min_outdoor_temp_offset', 'max_wind_speed', 'setpoint_tolerance',
    'heating_setpoint_minimum', 'cooling_setpoint_maximum', 'static_heating_setpoint', 'static_cooling_setpoint',
    'drift_mode', 'max_drift_rate', 'alpha_indoor', 'delta_cool', 'delta_heat', 'initial_T_rm_in',
)
CUSTOM_MODEL_PARAMETERS = (
    'custom_cooling_upper_limit', 'custom_cooling_lower_limit', 'custom_heating_upper_limit',
    'custom_heating_lower_limit', 'custom_upper_limit', 'custom_lower_limit', 'custom_slope', 'custom_intercept',
    'custom_cooling_offset', 'custom_heating_offset', 'custom_offset', 'heating_setpoint_minimum',
    'cooling_setpoint_maximum', 'custom_outdoor_metric', 'custom_alpha', 'custom_days', 'drift_mode', 'max_drift_rate',
    'alpha_indoor', 'delta_cool', 'delta_heat', 'initial_T_rm_in',
)
PARAMETERS_TYPES = {'accim predefined model': PREDEFINED_MODEL_PARAMETERS,
                    'accim custom model': CUSTOM_MODEL_PARAMETERS}
#: The script types of the parametric module.
PARAMETRIC_SCRIPT_TYPES = ('vrf_mm', 'vrf_ac', 'ex_ac')
#: The samplings of the plan of the parametric study.
SAMPLINGS = {'full set': 'every combination of the options of the parameters',
             'lhs': 'a Latin hypercube sample of the ranges of the parameters'}
#: The initial values of the form of the parametric study.
PARAMETRIC_DEFAULTS = {
    'idf': '',
    'epws': [],
    'parameters_type': 'accim predefined model',
    'script_type': 'vrf_mm',
    'sampling': 'full set',
    'samples': '10',
    'meters': 'Heating:Electricity, Cooling:Electricity',
    'processes': '2',
    'out_dir': 'gui_parametric_results',
    **EXISTING_HVAC_DEFAULTS,
}

_SEPARATORS = re.compile(r'[\s,;]+')
_DAY_ARGUMENTS = ('cooling_season_start', 'cooling_season_end')


class FormError(ValueError):
    """A value of a form is missing or not valid; the message says which and why."""


def _number(token: str, name: str) -> Number:
    try:
        return int(token) if re.fullmatch(r'[+-]?\d+', token) else float(token)
    except ValueError:
        raise FormError(f'{name}: {token!r} is not a number.') from None


def parse_number(text: Any, name: str) -> Number:
    """The number of a text field (an integer if it has no decimal point).

    :raises FormError: If the text is empty or not a number.
    """
    text = str(text).strip()
    if not text:
        raise FormError(f'{name}: enter a number.')
    return _number(text, name)


def parse_numbers(text: Any, name: str, integers: bool = False) -> List[Number]:
    """The numbers of a text field, separated by commas, semicolons or spaces ('1, 2 3' gives [1, 2, 3]).

    :raises FormError: If the text has no numbers, or a value is not a number (or not an integer, with
        ``integers``).
    """
    tokens = [token for token in _SEPARATORS.split(str(text).strip()) if token]
    if not tokens:
        raise FormError(f'{name}: enter at least one number.')
    numbers = [_number(token, name) for token in tokens]
    if integers and not all(isinstance(number, int) for number in numbers):
        raise FormError(f'{name}: enter whole numbers.')
    return numbers


def comfort_standard_choices() -> List[Tuple[int, str]]:
    """The comfort standards with EMS code, which AddAccis writes, as (comfort_standard, '1 = INT EN16798'): not those
    whose setpoints a hook of the API backend sets (:data:`accim.sim.standards.HOOK_COMFORT_STANDARDS`, comfort standard
    24, task F1)."""
    return [(number, standard.title) for number, standard in COMFORT_STANDARDS.items()
            if number not in HOOK_COMFORT_STANDARDS]


def _hint(standards: Iterable[int], attribute: str, empty: str) -> str:
    lines = []
    for number in standards:
        standard = COMFORT_STANDARDS.get(number)
        if standard is None:
            continue
        values = getattr(standard, attribute)
        lines.append(f'{standard.title}: ' + (', '.join(str(value) for value in values) if values else empty))
    return '\n'.join(lines)


def categories_hint(standards: Iterable[int]) -> str:
    """The categories of each comfort standard, one line each."""
    return _hint(standards, 'categories', 'no categories (any value)')


def comfort_modes_hint(standards: Iterable[int]) -> str:
    """The comfort modes of each comfort standard, one line each."""
    return _hint(standards, 'comfort_modes', 'no comfort modes (any value)')


def _names(folder: Union[str, os.PathLike]) -> List[str]:
    try:
        return sorted(os.listdir(folder))
    except OSError:
        return []


def input_idfs(folder: Union[str, os.PathLike]) -> List[str]:
    """The IDF files of a folder that AddAccis takes as input: not the output IDFs of accim ('[' in the name) nor its
    intermediate files ('_pymod')."""
    return [name for name in _names(folder)
            if name.lower().endswith('.idf') and '[' not in name and '_pymod' not in name]


def idf_files(folder: Union[str, os.PathLike]) -> List[str]:
    """All the IDF files of a folder (the input IDFs and the output IDFs of accim)."""
    return [name for name in _names(folder) if name.lower().endswith('.idf')]


def epw_files(folder: Union[str, os.PathLike]) -> List[str]:
    """The EPW files of a folder."""
    return [name for name in _names(folder) if name.lower().endswith('.epw')]


def simulation_csvs(folder: Union[str, os.PathLike]) -> List[str]:
    """The CSV files of the results of the simulations of a folder, as :class:`Table` reads them: the files of
    :func:`accim.run.run_ep` ('[' in the name), without the tables, meters and sizing results of EnergyPlus and the
    files that Table writes."""
    excluded = ('Table.csv', 'Meter.csv', 'Zsz.csv', '[CSVconcatenated.csv', '[Rows_not_corr_agg.csv',
                '[Rows_with_NaNs.csv')
    return [name for name in _names(folder)
            if name.lower().endswith('.csv') and '[' in name and not any(e in name for e in excluded)]


def _choice(form: Mapping[str, Any], name: str, choices: Iterable[str]) -> str:
    value = str(form.get(name, '')).strip()
    choices = list(choices)
    if value not in choices:
        raise FormError(f'{name}: choose one of {choices}.')
    return value


def _day_value(text: Any, name: str) -> Union[int, str]:
    from accim.sim.arguments import to_day_of_year

    text = str(text).strip()
    value: Union[int, str] = int(text) if text.isdigit() else text
    try:
        to_day_of_year(value, name)
    except ValueError as error:
        raise FormError(str(error)) from None
    return value


def _day(form: Mapping[str, Any], name: str) -> Union[int, str]:
    return _day_value(form.get(name, ''), name)


def _folder(form: Mapping[str, Any], what: str) -> str:
    folder = str(form.get('folder', '')).strip()
    if not folder or not os.path.isdir(folder):
        raise FormError(f'folder: choose the folder of {what}.')
    return folder


def _pairs(text: Any, label: str, allowed: Iterable[str], what: str) -> Dict[str, Any]:
    """The arguments of a text of pairs ``name=value`` separated by commas, semicolons or new lines, one value each
    (the dates of the cooling season can be 'dd/mm').

    :param label: The name of the field, for the messages.
    :param allowed: The names of the arguments that the text can have.
    :param what: What these arguments are, for the messages ('an argument of a zone').
    :raises FormError: If an argument is not one of ``allowed``, is repeated, or its value is not valid.
    """
    allowed = tuple(allowed)
    arguments: Dict[str, Any] = {}
    for item in re.split(r'[,;\n]+', str(text)):
        item = item.strip()
        if not item:
            continue
        if '=' not in item:
            raise FormError(f'{label}: write each argument as name=value, not {item!r}.')
        name, value = (part.strip() for part in item.split('=', 1))
        if name not in allowed and DEPRECATED_ARGUMENT_NAMES.get(name) in allowed:
            # The names of the development of accim 1.2.0, in the session files saved with them
            name = DEPRECATED_ARGUMENT_NAMES[name]
        if name not in allowed:
            raise FormError(f'{label}: {name!r} is not {what} (they are {", ".join(allowed)}).')
        if name in arguments:
            raise FormError(f'{label}: {name} is given twice.')
        if name in _DAY_ARGUMENTS:
            arguments[name] = _day_value(value, name)
        elif name == 'custom_outdoor_metric':
            arguments[name] = _metric_value(value, f'{label}: {name}')
        else:
            arguments[name] = _number(value, f'{label}: {name}')
    if not arguments:
        raise FormError(f'{label}: give at least one argument (name=value).')
    return arguments


def _metric_value(text: Any, label: str) -> str:
    """The name of an outdoor metric of the custom model (:data:`CUSTOM_OUTDOOR_METRICS`), from its name or its code
    (0 to 7)."""
    text = str(text).strip()
    names = list(CUSTOM_OUTDOOR_METRICS)
    if text in CUSTOM_OUTDOOR_METRICS:
        return text
    if text.isdigit() and int(text) < len(names):
        return names[int(text)]
    raise FormError(f'{label}: {text!r} is not an outdoor metric of the custom model ({", ".join(names)}).')


def current_names(values: Mapping[str, Any]) -> Dict[str, Any]:
    """The values of a form (or of a session file) with the names of the arguments that accim 1.2.0 renamed during
    its development (``heating_setpoint_floor`` and ``cooling_setpoint_ceiling``,
    :data:`accim.sim.arguments.DEPRECATED_ARGUMENT_NAMES`) replaced by their names, unless the values have them
    too."""
    current = dict(values)
    for old, new in DEPRECATED_ARGUMENT_NAMES.items():
        if old in current:
            value = current.pop(old)
            current.setdefault(new, value)
    return current


def _pairs_text(arguments: Mapping[str, Any]) -> str:
    """The text of some arguments, as :func:`_pairs` reads it."""
    return ', '.join(f'{name}={value}' for name, value in arguments.items())


def _field_value(text: Any) -> str:
    """The value of a field of a table of the zones: its text, without the description of the choice ('2 = INT
    ASHRAE55' is '2')."""
    return str(text if text is not None else '').split(' = ', 1)[0].strip()


def parse_zone_arguments(text: Any, zone: str = '') -> Dict[str, Any]:
    """The arguments of a zone, from a text such as ``'comfort_standard=2, category=80, hvac_mode=0'``: pairs
    ``name=value`` separated by commas, semicolons or new lines, with the arguments of
    :func:`accim.sim.accis.modify_accis` (one value each; the dates of the cooling season can be 'dd/mm').

    :raises FormError: If an argument is not one of a zone, is repeated, or its value is not valid.
    """
    label = f'zone_arguments of {zone!r}' if zone else 'zone_arguments'
    return _pairs(text, label, ZONE_ARGUMENTS, 'an argument of a zone')


def zone_field_choices(name: str, comfort_standard: Any = '') -> List[str]:
    """The choices of a field of the table of the zones of AddAccis (:data:`ZONE_FIELDS`), after an empty one (the
    value of each output IDF): the comfort standards ('2 = INT ASHRAE55'); the categories or comfort modes of the
    comfort standard of the zone (those of all the comfort standards, without it); the HVAC modes and the ventilation
    controls ('2 = Mixed mode').

    :param comfort_standard: The comfort standard of the zone, for the categories and comfort modes ('' for all).
    """
    if name == 'comfort_standard':
        values = [title for _, title in comfort_standard_choices()]
    elif name in ('category', 'comfort_mode'):
        number = _field_value(comfort_standard)
        standards = ([COMFORT_STANDARDS[int(number)]] if number.isdigit() and int(number) in COMFORT_STANDARDS
                     else list(COMFORT_STANDARDS.values()))
        found: List[Number] = []
        for standard in standards:
            found += [value for value in getattr(standard, 'categories' if name == 'category' else 'comfort_modes')
                      if value not in found]
        values = [str(value) for value in sorted(found)]
    elif name == 'hvac_mode':
        values = [f'{mode} = {label}' for mode, label in HVAC_MODES.items()]
    elif name == 'ventilation_control':
        values = [f'{control} = {label}' for control, label in VENTILATION_CONTROLS.items()]
    else:
        raise KeyError(f'{name!r} is not a field of the table of the zones ({", ".join(ZONE_FIELDS)}).')
    return [''] + values


def _choice_text(name: str, value: Any) -> str:
    """The text of a value in its field of the table of the zones, with the description of the choice."""
    if name == 'comfort_standard' and value in COMFORT_STANDARDS:
        return COMFORT_STANDARDS[value].title
    if name == 'hvac_mode' and value in HVAC_MODES:
        return f'{value} = {HVAC_MODES[value]}'
    if name == 'ventilation_control' and value in VENTILATION_CONTROLS:
        return f'{value} = {VENTILATION_CONTROLS[value]}'
    return str(value)


def _row_text(fields: Mapping[str, Any], other: Any, field_names: Iterable[str], parse, zone: str) -> str:
    pairs = [f'{name}={_field_value(fields.get(name))}' for name in field_names if _field_value(fields.get(name))]
    other = str(other or '').strip()
    return _pairs_text(parse(', '.join(pairs + ([other] if other else [])), zone))


def _split_row(text: Any, field_names: Iterable[str], parse, zone: str) -> Tuple[Dict[str, str], str]:
    arguments = parse(text, zone)
    fields = {name: _choice_text(name, arguments.pop(name)) if name in arguments else '' for name in field_names}
    return fields, _pairs_text(arguments)


def zone_row_text(fields: Mapping[str, Any], other: Any = '', zone: str = '') -> str:
    """The text of the arguments of a zone (as :func:`parse_zone_arguments` reads it) from the fields of the table of
    the zones of the window: those of :data:`ZONE_FIELDS` (empty: the value of each output IDF; the choices can keep
    their descriptions, such as '2 = INT ASHRAE55') and the other arguments, as pairs name=value.

    :raises FormError: If an argument is not valid, or it is in a field and in the other arguments.
    """
    return _row_text(fields, other, ZONE_FIELDS, parse_zone_arguments, zone)


def split_zone_arguments(text: Any, zone: str = '') -> Tuple[Dict[str, str], str]:
    """The fields of the table of the zones (those of :data:`ZONE_FIELDS`, with the descriptions of the choices) and
    the other arguments (pairs name=value) of the text of the arguments of a zone: the reverse of
    :func:`zone_row_text`.

    :raises FormError: If the text is not valid.
    """
    return _split_row(text, ZONE_FIELDS, parse_zone_arguments, zone)


def zone_arguments(rows: Iterable[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
    """The argument ``zone_arguments`` of AddAccis from the rows of the table of the zones: (zone, text of its
    arguments, as in :func:`parse_zone_arguments`).

    :raises FormError: If a zone is missing or repeated, or its arguments are not valid.
    """
    result: Dict[str, Dict[str, Any]] = {}
    for zone, text in rows:
        zone = str(zone).strip()
        if not zone:
            raise FormError('zone_arguments: a row has no zone.')
        if zone.upper() in (name.upper() for name in result):
            raise FormError(f'zone_arguments: the zone {zone!r} is given twice.')
        result[zone] = parse_zone_arguments(text, zone)
    try:
        check_zone_arguments(result)
    except ValueError as error:
        raise FormError(f'zone_arguments: {error}') from None
    return result


def _schedule(text: Any, name: str, empty: str) -> str:
    """The name of a schedule of a field (empty if the field is), without the characters that EnergyPlus does not
    accept in names.

    :param empty: What an empty field means, for the message.
    """
    schedule = str(text or '').strip()
    if re.search(r'[,;!]', schedule):
        raise FormError(f'{name}: enter the name of a schedule of the model, or On 24/7, without commas, semicolons '
                        f'or exclamation marks ({empty}).')
    return schedule


def existing_hvac_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of the existing HVAC systems (those of :data:`EXISTING_HVAC_DEFAULTS`) from the values of a form:
    the booleans of :data:`EXISTING_HVAC_OPTIONS` and ``existing_hvac_availability_schedule``, the name of a schedule
    of the model or 'On 24/7' (None if it is empty: the availability of the model).

    :raises FormError: If the name of the schedule has a character that EnergyPlus does not accept in names.
    """
    schedule = _schedule(form.get('existing_hvac_availability_schedule', ''), 'existing_hvac_availability_schedule',
                         'empty: the availability of the model')
    arguments = {name: bool(form.get(name, EXISTING_HVAC_DEFAULTS[name])) for name in EXISTING_HVAC_OPTIONS}
    arguments['existing_hvac_availability_schedule'] = schedule or None
    return arguments


def add_accis_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :class:`accim.sim.accis.AddAccis` from the values of its form.

    :param form: The values of the form: ``folder`` and ``idfs`` (the selected input IDFs of the folder), the
        choices (``script_type``, ``supply_air_temp_input_method``, ``setpoint_type``, ``energyplus_version``,
        ``output_type``), the lists of the checked boxes or selected items (``output_frequencies``,
        ``comfort_standard``, ``hvac_mode``, ``ventilation_control``), the booleans (``keep_existing_outputs``,
        ``add_building_averages``, ``debug_ems`` and those of :data:`EXISTING_HVAC_OPTIONS`), the texts of the other
        fields (lists of numbers separated by commas or spaces, or numbers, ``vrf_availability_schedule`` and
        ``existing_hvac_availability_schedule``), as in :data:`ADD_ACCIS_DEFAULTS`, and ``zone_arguments``, the rows
        of the table of the zones (see :func:`zone_arguments`; none by default).
    :return: The keyword arguments of AddAccis, with all the arguments that it would otherwise ask in the prompt,
        ``confirm=True`` and ``idfs`` (the names of the selected input IDFs, to run in the folder); with the VRF
        systems ('vrf_ac' and 'vrf_mm'), also their availability schedule, EER and COP; with the existing HVAC
        systems ('ex_ac' and 'ex_mm'), their arguments (:func:`existing_hvac_arguments`); the minimum and maximum of
        the setpoints and ``report_hours_below``, if their fields are not empty (:func:`setpoint_limit_arguments`);
        and ``report_long_term_discomfort=True`` if its box (the boolean ``report_long_term_discomfort`` of the form)
        is checked, with its ``long_term_range`` if the field ``long_term_range`` (a label of
        :data:`LONG_TERM_RANGE_CHOICES`) is not empty.
    :raises FormError: If a value is missing or not valid, the arguments of a zone give no setpoints in some
        output IDFs (:func:`zone_arguments_problems`), ``report_long_term_discomfort`` is checked with the
        PMV-based setpoints, or ``long_term_range`` is chosen without it.
    """
    _folder(form, 'the input IDFs')
    idfs = list(form.get('idfs') or [])
    if not idfs:
        raise FormError('idfs: select at least one input IDF.')
    script_type = _choice(form, 'script_type', SCRIPT_TYPES)
    setpoint_type = _choice(form, 'setpoint_type', SETPOINT_TYPES)
    output_frequencies = [f for f in OUTPUT_FREQUENCIES if f in (form.get('output_frequencies') or [])]
    if not output_frequencies:
        raise FormError('output_frequencies: check at least one output frequency.')
    arguments: Dict[str, Any] = dict(
        idfs=idfs,
        script_type=script_type,
        supply_air_temp_input_method=_choice(form, 'supply_air_temp_input_method', SUPPLY_AIR_TEMP_INPUT_METHODS),
        output_type=_choice(form, 'output_type', OUTPUT_TYPES),
        output_frequencies=output_frequencies,
        keep_existing_outputs=bool(form.get('keep_existing_outputs')),
        make_outputs_dataframe=False,
        energyplus_version=_choice(form, 'energyplus_version', ENERGYPLUS_VERSIONS),
        setpoint_type=setpoint_type,
        add_building_averages=bool(form.get('add_building_averages')),
        debug_ems=bool(form.get('debug_ems')),
        name_suffix=str(form.get('name_suffix', '')).strip(),
        confirm=True,
        verbose=True,
    )
    if script_type.startswith('vrf'):
        schedule = _schedule(form.get('vrf_availability_schedule', ADD_ACCIS_DEFAULTS['vrf_availability_schedule']),
                             'vrf_availability_schedule', 'On 24/7: always available')
        if not schedule:
            raise FormError('vrf_availability_schedule: enter the name of a schedule of the model, or On 24/7.')
        arguments.update(vrf_availability_schedule=schedule,
                         **{name: _positive(form, name) for name in ('vrf_eer', 'vrf_cop')})
    comfort_standard = [int(number) for number in form.get('comfort_standard') or []]
    if not comfort_standard:
        raise FormError('comfort_standard: select at least one comfort standard.')
    arguments.update(
        comfort_standard=comfort_standard,
        category=parse_numbers(form.get('category', ''), 'category'),
        comfort_mode=parse_numbers(form.get('comfort_mode', ''), 'comfort_mode'),
        **{name: parse_number(form.get(name, ADD_ACCIS_DEFAULTS[name]), name)
           for name in ('category_cooling_offset', 'category_heating_offset')},
        setpoint_accuracy=_positive(form, 'setpoint_accuracy'),
        cooling_season_start=_day(form, 'cooling_season_start'),
        cooling_season_end=_day(form, 'cooling_season_end'),
    )
    if 99 in comfort_standard:
        arguments.update({name: parse_number(form.get(name, ''), name) for name in CUSTOM_MODEL_FIELDS})
        arguments.update(custom_outdoor_metric_arguments(form))
        arguments.update(custom_regime_arguments(form, script_type))
    elif weather_file_standards(comfort_standard):
        # The outdoor metric of the comfort standards defined by their data that the EMS calculates begins with it,
        # and JPN Aqilah 2025 uses the running mean of EN 16798-1 with it
        arguments.update(weather_file_arguments(form))
    if script_type in MIXED_MODE_SCRIPT_TYPES:
        hvac_mode = sorted(int(mode) for mode in form.get('hvac_mode') or [])
        ventilation_control = sorted(int(control) for control in form.get('ventilation_control') or [])
        if not hvac_mode:
            raise FormError('hvac_mode: check at least one HVAC mode.')
        if not ventilation_control:
            raise FormError('ventilation_control: check at least one ventilation control.')
        arguments.update(
            hvac_mode=hvac_mode,
            ventilation_control=ventilation_control,
            **{name: parse_numbers(form.get(name, ''), name)
               for name in ('ventilation_setpoint_offset', 'min_outdoor_temp_offset', 'max_wind_speed')},
            **{name: parse_number(form.get(name, ''), name)
               for name in ('opening_factor_max_temp_diff', 'opening_factor_min_temp_diff', 'min_opening_factor')},
        )
    else:
        arguments.update(hvac_mode=[0], ventilation_control=[0])
    arguments.update({name: parse_number(form.get(name, ''), name)
                      for name in ('setpoint_tolerance_start', 'setpoint_tolerance_end', 'setpoint_tolerance_step')})
    if arguments['setpoint_tolerance_step'] <= 0:
        raise FormError('setpoint_tolerance_step: enter a number greater than 0.')
    arguments.update(setpoint_limit_arguments(form))
    arguments.update(drift_arguments(form))
    if form.get('report_long_term_discomfort'):
        if setpoint_type != 'temperature':
            raise FormError('report_long_term_discomfort: the long-term discomfort needs the adaptive setpoint '
                            'temperatures (setpoint_type temperature); uncheck it.')
        arguments['report_long_term_discomfort'] = True
    long_term_range = str(form.get('long_term_range') or '').strip()
    if long_term_range:
        if long_term_range not in LONG_TERM_RANGE_CHOICES:
            raise FormError(f'long_term_range: choose a range of EN 16798-1, Table B.2, or none, not '
                            f'{long_term_range!r}.')
        if not arguments.get('report_long_term_discomfort'):
            raise FormError('long_term_range: the range of the long-term discomfort needs its box '
                            '(report_long_term_discomfort) checked; check it or choose no range.')
        arguments['long_term_range'] = LONG_TERM_RANGE_CHOICES[long_term_range]
    zones = zone_arguments(form.get('zone_arguments') or [])
    if zones:
        if setpoint_type != 'temperature':
            raise FormError('zone_arguments: the arguments of each zone need the adaptive setpoint temperatures '
                            '(setpoint_type temperature).')
        arguments['zone_arguments'] = zones
        problems = zone_arguments_problems(arguments)
        if problems:
            raise FormError('zone_arguments: the arguments of some zones give no setpoints in some output IDFs (give '
                            'the comfort standard, category and comfort mode of each of these zones, and the HVAC '
                            'mode and ventilation control of mixed mode only with vrf_mm and ex_mm):\n'
                            + '\n'.join(problems))
    # The static setpoints of JPN Aqilah 2025, if an output IDF or a zone has it
    if setpoint_type == 'temperature' and (
            set(comfort_standard) & set(STATIC_SETPOINT_STANDARDS)
            or any(values.get('comfort_standard') in STATIC_SETPOINT_STANDARDS for values in zones.values())):
        arguments.update(static_setpoint_arguments(form))
    if script_type.startswith('ex'):
        arguments.update(existing_hvac_arguments(form))
    return arguments


def _positive(form: Mapping[str, Any], name: str) -> Number:
    """A number greater than 0 of a field (its default of :data:`ADD_ACCIS_DEFAULTS` if the form does not have it)."""
    number = parse_number(form.get(name, ADD_ACCIS_DEFAULTS.get(name, '')), name)
    if number <= 0:
        raise FormError(f'{name}: enter a number greater than 0.')
    return number


def custom_outdoor_metric_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of the outdoor metric of the custom model of :class:`accim.sim.accis.AddAccis` from the values of
    its form: ``custom_outdoor_metric`` (a name of :data:`CUSTOM_OUTDOOR_METRICS`), ``custom_alpha`` and
    ``custom_days`` (their defaults of :data:`ADD_ACCIS_DEFAULTS` if the form does not have them) and, if the form
    has it, ``epw``, the weather file of the simulations (relative to the ``folder`` of the form).

    :raises FormError: If a value is not valid, the weather file does not exist, or 'monthly_mean' has none.
    """
    metric = str(form.get('custom_outdoor_metric') or ADD_ACCIS_DEFAULTS['custom_outdoor_metric']).strip()
    if metric not in CUSTOM_OUTDOOR_METRICS:
        raise FormError(f'custom_outdoor_metric: choose one of {list(CUSTOM_OUTDOOR_METRICS)}.')
    arguments: Dict[str, Any] = dict(custom_outdoor_metric=metric)
    arguments.update({name: parse_number(form.get(name, ADD_ACCIS_DEFAULTS[name]), name)
                      for name in CUSTOM_OUTDOOR_METRIC_FIELDS})
    if not 0 < arguments['custom_alpha'] < 1:
        raise FormError('custom_alpha: enter a number between 0 and 1 (not included).')
    if not isinstance(arguments['custom_days'], int) or arguments['custom_days'] < 1:
        raise FormError('custom_days: enter an integer of at least 1.')
    epw = weather_file_arguments(form)
    arguments.update(epw)
    if not epw and metric == 'monthly_mean':
        raise FormError("epw: the outdoor metric 'monthly_mean' needs the weather file of the simulations, whose "
                        "monthly means the EMS programs keep.")
    return arguments


def weather_file_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """``epw``, the weather file of the simulations (relative to the ``folder`` of the form), with which the outdoor
    metric of the custom model, and that of the comfort standards defined by their data that the EMS calculates
    (:func:`registered_metric_standards`), begin; nothing if the form has none.

    :raises FormError: If the weather file does not exist.
    """
    epw = str(form.get('epw') or '').strip()
    if not epw:
        return {}
    if not os.path.isabs(epw) and form.get('folder'):
        epw = os.path.join(str(form['folder']), epw)
    if not os.path.isfile(epw):
        raise FormError(f'epw: {epw} is not a file (the weather file of the simulations).')
    return {'epw': epw}


def registered_metric_standards(standards: Iterable[Any]) -> List[int]:
    """The comfort standards defined by their data (:mod:`accim.sim.standards`) among some, whose outdoor metric the
    EMS calculates (as that of the custom model): the weather file of the simulations (``epw``) begins it."""
    from accim.sim.ems.standard_lines import outdoor_metric_standards

    found = outdoor_metric_standards()
    return [int(number) for number in standards if isinstance(number, (int, float)) and int(number) in found]


def weather_file_standards(standards: Iterable[Any]) -> List[int]:
    """The comfort standards among some whose outdoor metric the weather file of the simulations (``epw``) begins:
    those of :func:`registered_metric_standards`, and JPN Aqilah 2025 (23), whose running mean is then that of EN
    16798-1 with α = 0.8 that the EMS calculates (:data:`accim.sim.ems.standard_lines.WEATHER_FILE_METRICS`)."""
    from accim.sim.ems.standard_lines import WEATHER_FILE_METRICS

    standards = list(standards)
    found = set(registered_metric_standards(standards))
    return [int(number) for number in standards if isinstance(number, (int, float))
            and (int(number) in found or int(number) in WEATHER_FILE_METRICS)]


def static_setpoint_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The static setpoints of JPN Aqilah 2025 (``static_heating_setpoint`` and ``static_cooling_setpoint``,
    :mod:`accim.sim.ems.static_setpoints`) from the values of the form (their defaults of :data:`ADD_ACCIS_DEFAULTS`
    if the form does not have them).

    :raises FormError: If a value is not a number, or the heating setpoint is not lower than the cooling setpoint.
    """
    from accim.sim.ems.static_setpoints import check_static_setpoints

    arguments = {name: parse_number(form.get(name, ADD_ACCIS_DEFAULTS[name]), name) for name in STATIC_SETPOINT_FIELDS}
    try:
        check_static_setpoints(*arguments.values())
    except ValueError as error:
        raise FormError(str(error)) from None
    return arguments


def parse_custom_regimes(text: Any) -> List[Any]:
    """The regimes of the custom model (:class:`accim.sim.arguments.CustomRegime`) of the text of its field
    (:data:`CUSTOM_REGIMES_HINT`): one regime for each line, or separated by semicolons, written as
    ``condition: slope intercept cooling_offset heating_offset cooling_lower_limit cooling_upper_limit
    heating_lower_limit heating_upper_limit``, where the condition is one of
    :data:`accim.sim.arguments.REGIME_CONDITIONS`, ``metric_below x``, ``metric_above x`` or ``metric_between x1 x2``;
    the coefficients can be followed by the outdoor metric of the regime, ``outdoor_metric=name`` (a name or code of
    :data:`accim.sim.ems.outdoor_metric.OUTDOOR_METRICS`), with ``alpha=x`` and ``days=n`` (task H5 of the review of
    accim 1.2.0).

    :return: The regimes, in their order of priority (an empty list if the text is empty).
    :raises FormError: If a regime is not valid, or a regime 'always' is not the last one.
    """
    from accim.sim.arguments import CustomRegime, check_custom_regimes

    regimes = []
    parts = [part.strip() for part in re.split(r'[;\n]', str(text or '')) if part.strip()]
    for number, part in enumerate(parts, start=1):
        condition_text, colon, coefficients_text = part.partition(':')
        tokens = condition_text.split()
        if not colon or not tokens:
            raise FormError(f'custom_regimes: write the regime {number} ({part!r}) as its condition, a colon and its '
                            f'8 coefficients, such as "metric_below 10: 0.31 17.8 3.5 -3.5 10 33.5 10 33.5".')
        name = tokens[0].lower()
        values = [_number(token, 'custom_regimes') for token in tokens[1:]]
        expected = {'metric_below': 1, 'metric_above': 1, 'metric_between': 2}.get(name, 0)
        if (name not in REGIME_CONDITIONS and not expected) or len(values) != expected:
            raise FormError(f'custom_regimes: {condition_text.strip()!r} (regime {number}) is not a condition: '
                            f'{", ".join(REGIME_CONDITIONS)}, metric_below x, metric_above x or metric_between x1 '
                            f'x2.')
        condition = name if not expected else (name, values[0] if expected == 1 else tuple(values))
        # The options of the regime (its outdoor metric) after the coefficients
        options: Dict[str, Any] = {}
        numbers_text = []
        for token in re.split(r'[\s,]+', coefficients_text.strip()):
            if '=' not in token:
                numbers_text.append(token)
                continue
            option, _, value = token.partition('=')
            option = option.strip().lower()
            if option not in _REGIME_OPTIONS or not value.strip() or option in options:
                raise FormError(f'custom_regimes: {token!r} (regime {number}) is not an option of a regime: '
                                f'{", ".join(f"{name}=..." for name in _REGIME_OPTIONS)}, once each.')
            if option == 'outdoor_metric':
                # A name or a code of the metrics, as in the arguments of the zones
                options[option] = int(value.strip()) if value.strip().isdigit() else value.strip()
            else:
                options[option] = _number(value, 'custom_regimes')
        coefficients = parse_numbers(' '.join(numbers_text), 'custom_regimes')
        if len(coefficients) != 8:
            raise FormError(f'custom_regimes: the regime {number} needs 8 coefficients (slope, intercept, cooling '
                            f'and heating offsets, lower and upper limits of cooling and of heating), not '
                            f'{len(coefficients)}.')
        try:
            regimes.append(CustomRegime(*coefficients, condition=condition, **options))
        except ValueError as error:
            raise FormError(f'custom_regimes: regime {number}: {error}') from None
    try:
        check_custom_regimes(regimes)
    except ValueError as error:
        raise FormError(f'custom_regimes: {error}') from None
    return regimes


def custom_regime_arguments(form: Mapping[str, Any], script_type: str) -> Dict[str, Any]:
    """The argument ``custom_regimes`` of :class:`accim.sim.accis.AddAccis` from the values of its form, if its field
    is not empty (:func:`parse_custom_regimes`).

    :param script_type: The script type of the form: the conditions 'hvac_off' and 'hvac_on' need mixed mode.
    :raises FormError: If the regimes are not valid, or are given with the PMV-based setpoints, or a condition
        'hvac_off' or 'hvac_on' is given without mixed mode.
    """
    from accim.sim.ems.custom_regimes import uses_hvac_conditions

    regimes = parse_custom_regimes(form.get('custom_regimes', ''))
    if not regimes:
        return {}
    if form.get('setpoint_type', ADD_ACCIS_DEFAULTS['setpoint_type']) != 'temperature':
        raise FormError('custom_regimes: the PMV-based setpoints do not use the custom model (leave this field empty).')
    if uses_hvac_conditions(regimes) and script_type not in MIXED_MODE_SCRIPT_TYPES:
        raise FormError('custom_regimes: the conditions hvac_off and hvac_on need mixed mode (script type vrf_mm or '
                        'ex_mm).')
    return {'custom_regimes': regimes}


def setpoint_limit_arguments(form: Mapping[str, Any], hours_below: bool = True) -> Dict[str, Any]:
    """The minimum heating setpoint and the maximum cooling setpoint of :class:`accim.sim.accis.AddAccis`
    (``heating_setpoint_minimum`` and ``cooling_setpoint_maximum``, :mod:`accim.sim.ems.setpoint_limits`) and the
    temperatures of ``report_hours_below`` from the values of its form: only those of the fields that are not empty.

    :param hours_below: False to leave out ``report_hours_below`` (the EMS code of the setpoints does not have it).
    :raises FormError: If a value is not valid, the minimum is not lower than the maximum, or the minimum or the
        maximum is given with the PMV-based setpoints (setpoint_type 'pmv'), which have neither of them.
    """
    from accim.sim.ems.setpoint_limits import check_hours_below, check_setpoint_limits

    arguments: Dict[str, Any] = {}
    for name in SETPOINT_LIMIT_FIELDS:
        text = str(form.get(name, ADD_ACCIS_DEFAULTS[name]) or '').strip()
        if text:
            arguments[name] = parse_number(text, name)
    if arguments and form.get('setpoint_type', ADD_ACCIS_DEFAULTS['setpoint_type']) != 'temperature':
        raise FormError('heating_setpoint_minimum, cooling_setpoint_maximum: the PMV-based setpoints have neither '
                        'minimum nor maximum (leave these fields empty).')
    try:
        check_setpoint_limits(arguments.get('heating_setpoint_minimum'), arguments.get('cooling_setpoint_maximum'))
    except ValueError as error:
        raise FormError(str(error)) from None
    text = str(form.get('report_hours_below', '') or '').strip()
    if hours_below and text:
        temperatures = parse_numbers(text, 'report_hours_below')
        try:
            arguments['report_hours_below'] = check_hours_below(temperatures)
        except ValueError as error:
            raise FormError(str(error)) from None
    return arguments


def drift_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of the limiter of the drift of the setpoints of :class:`accim.sim.accis.AddAccis`
    (:mod:`accim.sim.ems.drift_limiter`) from the values of its form: none if ``drift_mode`` is empty; otherwise
    ``drift_mode`` and the numbers of the other fields (``initial_T_rm_in`` only if it is not empty).

    :raises FormError: If a value is not valid, or the limiter is given with the PMV-based setpoints (setpoint_type
        'pmv'), whose setpoints are not temperatures.
    """
    from accim.sim.ems.drift_limiter import check_drift_arguments

    mode = str(form.get('drift_mode', ADD_ACCIS_DEFAULTS['drift_mode']) or '').strip().lower()
    if not mode:
        return {}
    if form.get('setpoint_type', ADD_ACCIS_DEFAULTS['setpoint_type']) != 'temperature':
        raise FormError('drift_mode: the PMV-based setpoints have no limiter of the drift (leave this field empty).')
    arguments: Dict[str, Any] = {'drift_mode': mode}
    for name in ('max_drift_rate', 'alpha_indoor', 'delta_cool', 'delta_heat', 'initial_T_rm_in'):
        text = str(form.get(name, ADD_ACCIS_DEFAULTS[name]) or '').strip()
        if text:
            arguments[name] = parse_number(text, name)
    try:
        check_drift_arguments(**arguments)
    except ValueError as error:
        raise FormError(str(error)) from None
    return arguments


def _generation(arguments: Mapping[str, Any]):
    """The arguments of the output IDFs (:class:`accim.sim.generation.GenerationArguments`) of AddAccis with these
    arguments (those of :func:`add_accis_arguments`), as AddAccis makes them."""
    import dataclasses

    from accim.sim.generation import GenerationArguments

    names = {item.name for item in dataclasses.fields(GenerationArguments)}
    kwargs = {name: value for name, value in arguments.items() if name in names}
    if arguments['script_type'] in MIXED_MODE_SCRIPT_TYPES:
        return GenerationArguments(**kwargs)
    return GenerationArguments.air_conditioned(**kwargs)


def _combinations(arguments: Mapping[str, Any], generation) -> list:
    from accim.sim.generation import combinations

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return list(combinations(generation, arguments['setpoint_type']))


def output_idf_count(arguments: Mapping[str, Any]) -> int:
    """The number of output IDFs that AddAccis writes for each input IDF with these arguments (those of
    :func:`add_accis_arguments`), without the combinations that have no setpoints."""
    return len(_combinations(arguments, _generation(arguments)))


def zone_arguments_problems(arguments: Mapping[str, Any]) -> List[str]:
    """The zones of ``zone_arguments`` whose arguments give no setpoints in some output IDFs, as AddAccis checks them
    before writing the output IDFs (for instance, a zone with another comfort standard and the categories of the
    output IDFs, which that comfort standard does not have): one message for each zone and reason, with the number
    of output IDFs and the name of the first one (with 'model' as the name of the input IDF).

    :param arguments: The arguments of AddAccis (those of :func:`add_accis_arguments`).
    """
    from accim.sim.generation import output_name, zone_arguments_errors, zone_input_arguments

    zones = arguments.get('zone_arguments') or {}
    if not zones:
        return []
    generation = _generation(arguments)
    combinations = _combinations(arguments, generation)
    mixed_mode = arguments['script_type'] in MIXED_MODE_SCRIPT_TYPES
    problems = []
    for zone, zone_input in zones.items():
        found: Dict[str, List[str]] = {}
        for combination in combinations:
            reasons = zone_arguments_errors(zone_input_arguments(generation, combination, zone_input), mixed_mode)
            if reasons:
                found.setdefault('; '.join(reasons), []).append(
                    output_name('model', combination, generation.name_suffix))
        for reasons, names in found.items():
            count = f'{len(names)} output IDF{"" if len(names) == 1 else "s"}'
            problems.append(f'{zone}: {reasons} (in {count}, such as {names[0]})')
    return problems


def _single(values: List[Number], standard, attribute: str) -> Union[Number, None]:
    """The value of a list of the form for a comfort standard, if it has only one of its values (any value, if the
    comfort standard has none); otherwise None (all of them)."""
    allowed = getattr(standard, attribute) if standard is not None else {}
    valid = [value for value in values if not allowed or value in allowed]
    return valid[0] if len(valid) == 1 else None


#: The arguments of :func:`accim.utils.get_setpoint_ems_code` other than the comfort standard, category and comfort
#: mode, which a zone of the table of the zones can give.
_EMS_CODE_ARGUMENTS = ('setpoint_tolerance', 'setpoint_accuracy', 'cooling_season_start', 'cooling_season_end',
                       'category_cooling_offset', 'category_heating_offset', *CUSTOM_MODEL_FIELDS,
                       'custom_outdoor_metric', *CUSTOM_OUTDOOR_METRIC_FIELDS, *SETPOINT_LIMIT_FIELDS,
                       *STATIC_SETPOINT_FIELDS, *DRIFT_FIELDS)
#: Those of the custom model only
_CUSTOM_EMS_CODE_ARGUMENTS = (*CUSTOM_MODEL_FIELDS, 'custom_outdoor_metric', *CUSTOM_OUTDOOR_METRIC_FIELDS, 'epw',
                              'custom_regimes', 'script_type')


def setpoint_ems_code_calls(form: Mapping[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """The calls of :func:`accim.utils.get_setpoint_ems_code` that show the EMS code of the setpoints of the form of
    AddAccis (the input IDFs are not needed): one for each selected comfort standard, with the category and the
    comfort mode of the form if it has only one of them for that comfort standard (otherwise None: the code of all of
    them), and one for each zone of the table of the zones with its own comfort standard (with its category and
    comfort mode, or those of the form).

    :return: The title and the keyword arguments of each call.
    :raises FormError: If a value is missing or not valid, or the setpoints are not the adaptive setpoint
        temperatures.
    """
    if _choice(form, 'setpoint_type', SETPOINT_TYPES) != 'temperature':
        raise FormError('setpoint_type: the EMS code of the setpoints is that of the adaptive setpoint temperatures; '
                        'the PMV-based setpoints are those of the thermostats of EnergyPlus.')
    standards = [int(number) for number in form.get('comfort_standard') or []]
    if not standards:
        raise FormError('comfort_standard: select at least one comfort standard.')
    categories = parse_numbers(form.get('category', ''), 'category')
    comfort_modes = parse_numbers(form.get('comfort_mode', ''), 'comfort_mode')
    zones = zone_arguments(form.get('zone_arguments') or [])
    common: Dict[str, Any] = dict(
        setpoint_tolerance=parse_number(form.get('setpoint_tolerance_start', ''), 'setpoint_tolerance_start'),
        setpoint_accuracy=_positive(form, 'setpoint_accuracy'),
        cooling_season_start=_day(form, 'cooling_season_start'),
        cooling_season_end=_day(form, 'cooling_season_end'),
        **{name: parse_number(form.get(name, ADD_ACCIS_DEFAULTS[name]), name)
           for name in ('category_cooling_offset', 'category_heating_offset')},
    )
    # The minimum and maximum of the setpoints, and the limiter of their drift, if they are given
    common.update(setpoint_limit_arguments(form, hours_below=False))
    common.update(drift_arguments(form))
    if 99 in standards or any(values.get('comfort_standard') == 99 for values in zones.values()):
        common.update({name: parse_number(form.get(name, ''), name) for name in CUSTOM_MODEL_FIELDS})
        # With the weather file, the code of the outdoor metric begins with its values on 1 January
        common.update(custom_outdoor_metric_arguments(form))
        # The regimes of the custom model, with the script type (the conditions of its HVAC systems)
        script_type = _choice(form, 'script_type', SCRIPT_TYPES)
        regimes = custom_regime_arguments(form, script_type)
        if regimes:
            common.update(regimes, script_type=script_type)
    elif weather_file_standards(standards + [values.get('comfort_standard') for values in zones.values()]):
        # The outdoor metric of the comfort standards defined by their data that the EMS calculates, and that of JPN
        # Aqilah 2025 with the weather file
        common.update(weather_file_arguments(form))
    # The static setpoints of JPN Aqilah 2025
    if set(standards + [values.get('comfort_standard') for values in zones.values()]) & set(STATIC_SETPOINT_STANDARDS):
        common.update(static_setpoint_arguments(form))

    def call(title: str, number: int, category, comfort_mode, extra: Mapping[str, Any]) -> Tuple[str, Dict[str, Any]]:
        if number == 0:
            # ESP CTE has neither categories nor comfort modes
            category = comfort_mode = None
        kwargs = dict(common, comfort_standard=number, category=category, comfort_mode=comfort_mode, **extra)
        if number != 99:
            # The weather file also begins the outdoor metric of the comfort standards defined by their data, and
            # that of JPN Aqilah 2025
            kept = ('epw',) if weather_file_standards([number]) else ()
            for name in _CUSTOM_EMS_CODE_ARGUMENTS:
                if name not in kept:
                    kwargs.pop(name, None)
        described = ', '.join(f'{name.replace("_", " ")} {"(all)" if kwargs[name] is None else kwargs[name]}'
                              for name in ('category', 'comfort_mode'))
        return f'{title}: {described}', kwargs

    calls = []
    for number in standards:
        standard = COMFORT_STANDARDS.get(number)
        calls.append(call(standard.title if standard else str(number), number,
                          _single(categories, standard, 'categories'),
                          _single(comfort_modes, standard, 'comfort_modes'), {}))
    for zone, values in zones.items():
        if 'comfort_standard' not in values:
            continue
        number = values['comfort_standard']
        standard = COMFORT_STANDARDS.get(number)
        category = values.get('category', _single(categories, standard, 'categories'))
        comfort_mode = values.get('comfort_mode', _single(comfort_modes, standard, 'comfort_modes'))
        extra = {name: value for name, value in values.items() if name in _EMS_CODE_ARGUMENTS}
        calls.append(call(f'Zone {zone}, {standard.title if standard else number}', number, category, comfort_mode,
                          extra))
    return calls


def run_ep_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :func:`accim.run.run_ep` from the values of its form (``folder``, ``only_accim_idfs``,
    ``processes``, ``energyplus_version`` and ``backend``), with ``confirm=True``.

    :raises FormError: If a value is missing or not valid.
    """
    _folder(form, 'the IDFs and EPWs')
    return dict(
        only_accim_idfs=bool(form.get('only_accim_idfs')),
        confirm=True,
        processes=_processes(form),
        energyplus_version=_choice(form, 'energyplus_version', ENERGYPLUS_VERSIONS),
        backend=_choice(form, 'backend', BACKENDS),
    )


def _processes(form: Mapping[str, Any]) -> int:
    processes = parse_number(form.get('processes', ''), 'processes')
    if not isinstance(processes, int) or processes < 1:
        raise FormError('processes: enter a whole number greater than 0.')
    return processes


def results_size_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :func:`accim.run.estimate_results_size` from the values of the form of run_ep (``folder``,
    ``only_accim_idfs``, ``processes`` and ``simulate``: True to measure the size in a simulation of an IDF of each
    group with the same outputs).

    :raises FormError: If a value is missing or not valid.
    """
    _folder(form, 'the IDFs and EPWs')
    return dict(simulate=bool(form.get('simulate')), only_accim_idfs=bool(form.get('only_accim_idfs')),
                processes=_processes(form))


def simulations(folder: Union[str, os.PathLike], only_accim_idfs: bool) -> List[Tuple[str, str]]:
    """The simulations that :func:`accim.run.run_ep` runs in a folder: (IDF, EPW) for each IDF (only the output IDFs
    of accim, with '[' in the name, if ``only_accim_idfs``) and each EPW."""
    names = _names(folder)
    idfs = [name for name in names if name.endswith('.idf') and ('[' in name or not only_accim_idfs)]
    epws = [name for name in names if name.endswith('.epw')]
    return [(idf, epw) for idf in idfs for epw in epws]


def _file_of_folder(form: Mapping[str, Any], name: str, choices: Iterable[str], what: str) -> str:
    value = str(form.get(name, '')).strip()
    if not value:
        raise FormError(f'{name}: choose {what}.')
    if value not in list(choices):
        raise FormError(f'{name}: {value!r} is not in the folder.')
    return value


def parse_apmv_zone_setpoints(text: Any, zone: str = '') -> Dict[str, Number]:
    """The PMV-based setpoints of a zone, from a text such as
    ``'pmv_cooling_setpoint=0.7, pmv_heating_setpoint=-0.7'``: pairs ``name=value`` separated by commas, semicolons or
    new lines, with the names of :data:`APMV_SETPOINT_FIELDS`.

    :raises FormError: If a name is not one of them, is repeated, or its value is not a number.
    """
    label = f'zone_setpoints of {zone!r}' if zone else 'zone_setpoints'
    return _pairs(text, label, APMV_SETPOINT_FIELDS, 'a PMV-based setpoint of a zone')


def apmv_zone_row_text(fields: Mapping[str, Any], other: Any = '', zone: str = '') -> str:
    """The text of the PMV-based setpoints of a zone (as :func:`parse_apmv_zone_setpoints` reads it) from the fields of the
    table of the zones of the window (those of :data:`APMV_ZONE_FIELDS`; empty: the value of all the zones) and the
    other setpoints (the tolerances), as pairs name=value.

    :raises FormError: If a value is not valid, or it is in a field and in the other setpoints.
    """
    return _row_text(fields, other, APMV_ZONE_FIELDS, parse_apmv_zone_setpoints, zone)


def split_apmv_zone_setpoints(text: Any, zone: str = '') -> Tuple[Dict[str, str], str]:
    """The fields of the table of the zones of the PMV-based setpoints (:data:`APMV_ZONE_FIELDS`) and the other setpoints
    of the text of a zone: the reverse of :func:`apmv_zone_row_text`."""
    return _split_row(text, APMV_ZONE_FIELDS, parse_apmv_zone_setpoints, zone)


def apmv_zone_setpoints(rows: Iterable[Tuple[str, str]]) -> Dict[str, Dict[str, Number]]:
    """The PMV-based setpoints of some zones from the rows of their table: (zone, text of its setpoints, as in
    :func:`parse_apmv_zone_setpoints`), by zone.

    :raises FormError: If a zone is missing or repeated, or its setpoints are not valid.
    """
    result: Dict[str, Dict[str, Number]] = {}
    for zone, text in rows:
        zone = str(zone).strip()
        if not zone:
            raise FormError('zone_setpoints: a row has no zone.')
        if zone.upper() in (name.upper() for name in result):
            raise FormError(f'zone_setpoints: the zone {zone!r} is given twice.')
        result[zone] = parse_apmv_zone_setpoints(text, zone)
    return result


def _zone_values(zones: Mapping[str, Mapping[str, Number]]) -> Dict[str, Dict[str, Number]]:
    """The setpoints that some zones change, each one as a dictionary {zone: value} (in the order of
    :data:`APMV_SETPOINT_FIELDS`)."""
    values = {name: {zone: setpoints[name] for zone, setpoints in zones.items() if name in setpoints}
              for name in APMV_SETPOINT_FIELDS}
    return {name: by_zone for name, by_zone in values.items() if by_zone}


def hours_zones(text: Any) -> Union[str, List[str]]:
    """The argument ``zones`` of :func:`accim.data.postprocessing.setpoint_hours.filter_by_hours_within_setpoints`
    from its field: 'building' (the percentage of the whole building), 'all' (that of every zone), or the zones,
    separated by commas.

    :raises FormError: If the field is empty.
    """
    text = str(text).strip()
    if text.lower() in ('building', 'all'):
        return text.lower()
    zones = [zone.strip() for zone in re.split(r'[,;\n]+', text) if zone.strip()]
    if not zones:
        raise FormError('zones: enter building, all, or the zones separated by commas.')
    return zones


def index_setpoint_fields(index: str) -> List[str]:
    """The setpoints of :data:`APMV_SETPOINT_FIELDS` that an index of :data:`PMV_INDEX_FUNCTIONS` takes: its own
    parameters and those that all the indices take (the setpoints and their tolerances)."""
    others = {name for key, names in PMV_INDEX_PARAMETERS.items() if key != index for name in names}
    return [name for name in APMV_SETPOINT_FIELDS if name not in others]


def adaptive_coefficient_choices() -> List[str]:
    """The choices of the catalogue of adaptive coefficients of the aPMV in the form: an empty one (the coefficients
    typed in the form) and the keys of :data:`accim.constants.APMV_ADAPTIVE_COEFFICIENTS`."""
    return [''] + list(APMV_ADAPTIVE_COEFFICIENTS)


def adaptive_coefficient_entry(key: str) -> Tuple[str, str, str]:
    """The adaptive coefficients of the aPMV of a key of :data:`accim.constants.APMV_ADAPTIVE_COEFFICIENTS`, as the
    texts of the fields for cooling and heating of the form (that of heating empty if the entry has none), and a
    description of the entry: its grade, its notes and its source (three empty texts for the empty key).

    :raises FormError: If the key is not in the catalogue.
    """
    if not key:
        return '', '', ''
    if key not in APMV_ADAPTIVE_COEFFICIENTS:
        raise FormError(f'adaptive_coefficients: {key!r} is not in the catalogue of adaptive coefficients.')
    entry = APMV_ADAPTIVE_COEFFICIENTS[key]
    grade = entry['grade']
    if grade == 'literature':
        grade += ': check the coefficients before using them (section 4.8 of the documentation)'
    heating = '' if entry['heating'] is None else str(entry['heating'])
    description = f"{entry['notes']} ({entry['source']}); grade {grade}."
    if entry['heating'] is None:
        description += ' It has no coefficient for heating (cool sensations).'
    return str(entry['cooling']), heating, description


def apmv_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of the PMV-based setpoints (:mod:`accim.sim.apmv`) from the values of their form (as in
    :data:`APMV_DEFAULTS`, with ``folder``, and ``zone_setpoints``, the rows of the table of the zones with other
    setpoints, see :func:`apmv_zone_setpoints`; none by default).

    :return: ``idf`` and ``output_idf`` (the names of the input IDF and of the IDF to write, by default
        '<input IDF>_<index>.idf', such as '<input IDF>_aPMV.idf'), ``index`` (the index of the setpoints, a key of
        :data:`PMV_INDEX_FUNCTIONS`; 'apmv' if the form has none), ``energyplus_version``, ``add_vrf_system`` and
        ``supply_air_temp_input_method`` (:func:`accim.sim.apmv.add_vrf_system`), ``always_occupied``
        (:func:`accim.sim.apmv.set_zones_always_occupied`), ``apmv`` (the keyword arguments of the function of the
        index, such as :func:`accim.sim.apmv.apply_apmv_setpoints`, with the setpoints of the index
        (:func:`index_setpoint_fields`), ``report_ppd_weighted_hours=True`` if its box is checked (Method C of
        CEN/TR 16798-2) and, for the ePMV, the options of :data:`EPMV_OPTIONS`: each setpoint that
        some zones of the table change is a dictionary ``{zone: value}``, with the value of the form as its
        ``default_*`` argument, for the other zones; :func:`accim.gui.tasks.apply_apmv` gives these dictionaries the
        keys of the zones in the model) and ``pmv_inputs`` (those of :func:`accim.sim.apmv.set_pmv_input_parameters`
        that are given; empty to keep those of the model).
    :raises FormError: If a value is missing or not valid.
    """
    from accim.constants import EPMV_EXPECTANCY_RANGES

    folder = _folder(form, 'the input IDF')
    idf = _file_of_folder(form, 'idf', input_idfs(folder), 'the input IDF')
    index = _choice({'index': form.get('index') or 'apmv'}, 'index', PMV_INDEX_FUNCTIONS)
    output_idf = (str(form.get('output_idf', '')).strip()
                  or f'{os.path.splitext(idf)[0]}_{PMV_INDEX_NAMES[index]}.idf')
    if not output_idf.lower().endswith('.idf') or os.path.basename(output_idf) != output_idf:
        raise FormError('output_idf: enter the name of an IDF file of the folder (ending in .idf).')
    if output_idf.lower() == idf.lower():
        raise FormError('output_idf: the name must differ from that of the input IDF.')
    output_frequencies = [f for f in OUTPUT_FREQUENCIES if f in (form.get('output_frequencies') or [])]
    if not output_frequencies:
        raise FormError('output_frequencies: check at least one output frequency.')
    fields = index_setpoint_fields(index)
    apmv = dict(output_frequencies=output_frequencies,
                other_pmv_related_outputs=bool(form.get('other_pmv_related_outputs')),
                **{name: parse_number(form.get(name, ''), name) for name in fields},
                cooling_season_start=_day(form, 'cooling_season_start'),
                cooling_season_end=_day(form, 'cooling_season_end'),
                verbose=True)
    if form.get('report_ppd_weighted_hours'):
        apmv['report_ppd_weighted_hours'] = True
    if index == 'epmv':
        apmv.update({name: bool(form.get(name)) for name in EPMV_OPTIONS})
    if index == 'apmv':
        apmv['adaptive_coefficient_by'] = _choice(
            {'adaptive_coefficient_by': form.get('adaptive_coefficient_by') or 'season'}, 'adaptive_coefficient_by',
            ADAPTIVE_COEFFICIENT_BY)
    pmv_inputs = {name: parse_number(form.get(name), name) for name in PMV_INPUT_FIELDS
                  if str(form.get(name, '')).strip()}
    zones = apmv_zone_setpoints(form.get('zone_setpoints') or [])
    for zone, setpoints in zones.items():
        other = [name for name in setpoints if name not in fields]
        if other:
            raise FormError(f'zone_setpoints of {zone!r}: {other} are not setpoints of the {PMV_INDEX_NAMES[index]}.')
    for name, values in _zone_values(zones).items():
        apmv[f'default_{name}'] = apmv[name]
        apmv[name] = values
    if 'expectancy_factor' in apmv:
        low = min(limits[0] for limits in EPMV_EXPECTANCY_RANGES.values())
        high = max(limits[1] for limits in EPMV_EXPECTANCY_RANGES.values())
        given = apmv['expectancy_factor']
        for value in (given.values() if isinstance(given, Mapping) else [given]):
            if not low <= value <= high:
                raise FormError(f'expectancy_factor: {value} is not between {low} and {high}.')
    return dict(
        idf=idf,
        output_idf=output_idf,
        index=index,
        energyplus_version=_choice(form, 'energyplus_version', ENERGYPLUS_VERSIONS),
        add_vrf_system=bool(form.get('add_vrf_system')),
        supply_air_temp_input_method=_choice(form, 'supply_air_temp_input_method', SUPPLY_AIR_TEMP_INPUT_METHODS),
        always_occupied=bool(form.get('always_occupied')),
        apmv=apmv,
        pmv_inputs=pmv_inputs,
    )


def parse_mapping(text: Any, name: str) -> Dict[str, str]:
    """A dictionary from a text with a pair ``key = value`` on each line (the empty lines are skipped).

    :raises FormError: If a line has no '=', or a key is empty or repeated.
    """
    mapping: Dict[str, str] = {}
    for line in str(text).splitlines():
        line = line.strip()
        if not line:
            continue
        if '=' not in line:
            raise FormError(f'{name}: write each line as key = value, not {line!r}.')
        key, value = (part.strip() for part in line.split('=', 1))
        if not key or not value:
            raise FormError(f'{name}: {line!r} needs a key and a value.')
        if key in mapping:
            raise FormError(f'{name}: {key!r} is given twice.')
        mapping[key] = value
    return mapping


def rename_epws_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :class:`accim.data.preprocessing.rename_epw_files` from the values of its form: ``folder``,
    ``epws`` (the selected EPWs), ``cities`` (lines 'text in the name of the EPW = city'), ``countries`` (lines
    'country = city, city...') and ``delete_originals``.

    :raises FormError: If a value is missing or not valid.
    """
    folder = _folder(form, 'the EPWs')
    epws = list(form.get('epws') or [])
    if not epws:
        raise FormError('epws: select at least one EPW.')
    missing = [epw for epw in epws if epw not in epw_files(folder)]
    if missing:
        raise FormError(f'epws: {missing} are not in the folder.')
    cities = parse_mapping(form.get('cities', ''), 'cities')
    countries = {country: [city.strip() for city in cities_text.split(',') if city.strip()]
                 for country, cities_text in parse_mapping(form.get('countries', ''), 'countries').items()}
    return dict(filelist=epws, rename_city_dict=cities or None, country_to_city_dict=countries or None,
                confirm_renaming=True, confirm_deletion=bool(form.get('delete_originals')))


def table_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :class:`accim.data.postprocessing.main.Table` from the values of its form (as in
    :data:`TABLE_DEFAULTS`, with ``folder``).

    :return: ``table`` (the keyword arguments of Table, with ``datasets``, the CSV files of the simulations of the
        folder) and ``type_of_table`` (that of :meth:`Table.format_table`).
    :raises FormError: If a value is missing or not valid.
    """
    folder = _folder(form, 'the CSV files of the simulations')
    datasets = simulation_csvs(folder)
    if not datasets:
        raise FormError('folder: it has no CSV files of simulations (run them first).')
    idf_path = _file_of_folder(form, 'idf_path', idf_files(folder), 'an IDF of the simulated building, to find '
                                                                    'its zones')
    level = [level for level in ('block', 'building') if level in (form.get('level') or [])]
    level_agg_func = [func for func in ('sum', 'mean') if func in (form.get('level_agg_func') or [])]
    if not level:
        raise FormError('level: check block, building or both.')
    if not level_agg_func:
        raise FormError('level_agg_func: check sum, mean or both.')
    excluded = [zone for zone in re.split(r'[,;\n]+', str(form.get('level_excluded_zones', ''))) if zone.strip()]
    table = dict(
        datasets=datasets,
        source_frequency=_choice(form, 'source_frequency', TABLE_FREQUENCIES),
        frequency=_choice(form, 'frequency', TABLE_FREQUENCIES),
        frequency_agg_func=_choice(form, 'frequency_agg_func', ('sum', 'mean')),
        standard_outputs=bool(form.get('standard_outputs')),
        level=level,
        level_agg_func=level_agg_func,
        level_excluded_zones=[zone.strip() for zone in excluded],
        split_epw_names=bool(form.get('split_epw_names')),
        idf_path=idf_path,
    )
    if TABLE_FREQUENCIES.index(table['frequency']) < TABLE_FREQUENCIES.index(table['source_frequency']):
        raise FormError('frequency: it cannot be shorter than the frequency of the CSV files (source_frequency).')
    if form.get('long_term_indicators'):
        # The indicators of the long-term thermal discomfort of CEN/TR 16798-2 (accim.data.postprocessing.
        # long_term_discomfort), from the rows of each timestep or hour
        if table['frequency'] not in ('timestep', 'hourly'):
            raise FormError("long_term_indicators: the indicators need a table of timesteps or hours (frequency "
                            "'timestep' or 'hourly').")
        table['long_term_indicators'] = True
    if form.get('indoor_adaptation_indicators'):
        # The indicators of the adaptation to the indoor climate (block F, task F3; accim.data.postprocessing.
        # indoor_adaptation), from the rows of each timestep or hour
        if table['frequency'] not in ('timestep', 'hourly'):
            raise FormError("indoor_adaptation_indicators: the indicators need a table of timesteps or hours "
                            "(frequency 'timestep' or 'hourly').")
        table['indoor_adaptation_indicators'] = True
    return dict(table=table, type_of_table=_choice(form, 'type_of_table', TABLE_TYPES))


def figure_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of a figure of :class:`Table` (:meth:`Table.scatter_plot` or :meth:`Table.time_plot`) from the
    values of its form: ``figure_type``, ``vars_to_gather_rows`` and ``vars_to_gather_cols`` (the categorical columns
    of the subplots), ``data_on_x_axis`` (the column of the x axis of the scatter plot), ``data_on_y_main_axis`` (the
    columns of the y axis), ``y_axis_label``, ``figname``, ``figsize`` (the width of each subplot, in inches), ``dpi``
    and ``table_frequency`` (the frequency of the table, if it is made).

    :return: ``figure_type`` and the keyword arguments of the method (``kwargs``), without asking for confirmation.
    :raises FormError: If a value is missing or not valid.
    """
    figure_type = _choice(form, 'figure_type', FIGURE_TYPES)
    if figure_type == 'time' and form.get('table_frequency') == 'runperiod':
        raise FormError('figure_type: the time plot needs a table with another frequency than runperiod.')
    rows = list(form.get('vars_to_gather_rows') or [])
    cols = list(form.get('vars_to_gather_cols') or [])
    if not rows or not cols:
        raise FormError('vars_to_gather: select at least one variable for the rows and one for the columns of the '
                        'subplots (the variables whose values differ between the simulations).')
    if set(rows) & set(cols):
        raise FormError(f'vars_to_gather: {sorted(set(rows) & set(cols))} cannot be in the rows and the columns.')
    y_columns = list(form.get('data_on_y_main_axis') or [])
    if not y_columns:
        raise FormError('data_on_y_main_axis: select at least one column for the y axis.')
    figname = str(form.get('figname', '')).strip()
    if not figname or re.search(r'[\\/:*?"<>|]', figname):
        raise FormError('figname: enter a name for the file of the figure (without folders or extension).')
    dpi = parse_number(form.get('dpi', ''), 'dpi')
    if not isinstance(dpi, int) or dpi < 50:
        raise FormError('dpi: enter a whole number of at least 50.')
    figsize = parse_number(form.get('figsize', TABLE_DEFAULTS['figsize']), 'figsize')
    if not 1 <= figsize <= 20:
        raise FormError('figsize: enter the width of each subplot, in inches, from 1 to 20.')
    y_label = str(form.get('y_axis_label', '')).strip() or 'Value'
    kwargs: Dict[str, Any] = dict(
        vars_to_gather_rows=rows,
        vars_to_gather_cols=cols,
        data_on_y_main_axis=[[y_label, y_columns]],
        colorlist_y_main_axis=[[y_label, [FIGURE_COLORS[i % len(FIGURE_COLORS)] for i in range(len(y_columns))]]],
        figname=figname,
        figsize=figsize,
        ratio_height_to_width=0.75 if figure_type == 'scatter' else 0.5,
        dpi=dpi,
        confirm_graph=True,
    )
    if figure_type == 'scatter':
        x_column = str(form.get('data_on_x_axis', '')).strip()
        if not x_column:
            raise FormError('data_on_x_axis: choose the column of the x axis.')
        kwargs['data_on_x_axis'] = x_column
        kwargs['supxlabel'] = x_column
    return dict(figure_type=figure_type, kwargs=kwargs)


def parse_parameter_values(text: Any, name: str) -> Union[List[Number], Tuple[Number, Number]]:
    """The values of a parameter of the parametric study: options separated by commas or spaces ('1, 2, 3' gives
    the list [1, 2, 3]), or a range 'minimum to maximum' ('0.2 to 0.6' gives the tuple (0.2, 0.6)).

    :raises FormError: If the values are not numbers, or the range is not increasing.
    """
    text = str(text).strip()
    match = re.fullmatch(r'(\S+)\s+to\s+(\S+)', text, flags=re.IGNORECASE)
    if match:
        low, high = _number(match.group(1), name), _number(match.group(2), name)
        if low >= high:
            raise FormError(f'{name}: the range {text!r} must go from a lower to a higher value.')
        return low, high
    values = parse_numbers(text, name)
    if len(set(values)) != len(values):
        raise FormError(f'{name}: an option is repeated.')
    return values


def parametric_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of a basic parametric study (:class:`accim.parametric_and_optimisation.main.ParametricSimulation`)
    from the values of its form (as in :data:`PARAMETRIC_DEFAULTS`, with ``folder``, ``epws``, the selected EPWs, and
    ``parameters``, the rows (name, values) of the table of the parameters; see :func:`parse_parameter_values`).

    :return: ``idf``, ``epws``, ``parameters_type``, ``script_type``, ``accis_params_dict`` (the argument of
        ``set_parameters``), ``sampling`` ('full set' or 'lhs'), ``samples``, ``meters`` (the outputs, read as the
        results), ``processes``, ``out_dir`` (the folder of the results, in the working folder) and
        ``existing_hvac`` (with 'ex_ac', the arguments of the existing HVAC systems, :func:`existing_hvac_arguments`;
        otherwise empty).
    :raises FormError: If a value is missing or not valid.
    """
    folder = _folder(form, 'the IDF and the EPWs')
    idf = _file_of_folder(form, 'idf', input_idfs(folder), 'the input IDF')
    epws = list(form.get('epws') or [])
    if not epws:
        raise FormError('epws: select at least one EPW.')
    missing = [epw for epw in epws if epw not in epw_files(folder)]
    if missing:
        raise FormError(f'epws: {missing} are not in the folder.')
    parameters_type = _choice(form, 'parameters_type', PARAMETERS_TYPES)
    available = PARAMETERS_TYPES[parameters_type]
    accis_params_dict: Dict[str, Any] = {}
    for name, text in form.get('parameters') or []:
        name = str(name).strip()
        if name not in available:
            raise FormError(f'parameters: {name!r} is not a parameter of the {parameters_type} (they are '
                            f'{", ".join(available)}).')
        if name in accis_params_dict:
            raise FormError(f'parameters: {name} is given twice.')
        accis_params_dict[name] = parse_parameter_values(text, name)
    if not accis_params_dict:
        raise FormError('parameters: add at least one parameter, with its values.')
    ranges = [name for name, values in accis_params_dict.items() if isinstance(values, tuple)]
    sampling = _choice(form, 'sampling', SAMPLINGS)
    samples = 0
    if sampling == 'full set':
        if ranges:
            raise FormError(f'parameters: the full set needs options (such as 1, 2), not ranges: {ranges}.')
    else:
        if len(ranges) != len(accis_params_dict):
            options = [name for name in accis_params_dict if name not in ranges]
            raise FormError(f'parameters: the Latin hypercube sample needs ranges (such as 0.2 to 0.6), not options: '
                            f'{options}.')
        if parameters_type == 'accim predefined model':
            raise FormError('sampling: the predefined models need options (the full set).')
        samples = parse_number(form.get('samples', ''), 'samples')
        if not isinstance(samples, int) or samples < 1:
            raise FormError('samples: enter a whole number greater than 0.')
    meters = [meter.strip() for meter in re.split(r'[,;\n]+', str(form.get('meters', ''))) if meter.strip()]
    if not meters:
        raise FormError('meters: enter at least one meter of EnergyPlus (such as Heating:Electricity).')
    out_dir = str(form.get('out_dir', '')).strip()
    if not out_dir or re.search(r'[\\/:*?"<>|]', out_dir):
        raise FormError('out_dir: enter the name of a folder for the results (inside the working folder).')
    script_type = _choice(form, 'script_type', PARAMETRIC_SCRIPT_TYPES)
    return dict(idf=idf, epws=epws, parameters_type=parameters_type, script_type=script_type,
                accis_params_dict=accis_params_dict, sampling=sampling, samples=samples, meters=meters,
                processes=_processes(form), out_dir=out_dir,
                existing_hvac=existing_hvac_arguments(form) if script_type.startswith('ex') else {})


def parametric_simulation_count(arguments: Mapping[str, Any]) -> int:
    """The number of simulations of a parametric study (those of :func:`parametric_arguments`): at most, before the
    invalid combinations of the predefined models are dropped."""
    if arguments['sampling'] == 'full set':
        plans = 1
        for values in arguments['accis_params_dict'].values():
            plans *= len(values)
    else:
        plans = arguments['samples']
    return plans * len(arguments['epws'])

