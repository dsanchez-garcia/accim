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

from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS
from accim.sim.arguments import MIXED_MODE_SCRIPT_TYPES, OUTPUT_FREQUENCIES, SUPPLY_AIR_TEMP_INPUT_METHODS
from accim.sim.ems.inputs import ZONE_ARGUMENTS, check_zone_arguments
from accim.sim.standards import COMFORT_STANDARDS

__all__ = [
    'ADD_ACCIS_DEFAULTS',
    'APMV_DEFAULTS',
    'APMV_SETPOINT_FIELDS',
    'BACKENDS',
    'CUSTOM_MODEL_FIELDS',
    'CUSTOM_MODEL_PARAMETERS',
    'ENERGYPLUS_VERSIONS',
    'FIGURE_COLORS',
    'FIGURE_TYPES',
    'FormError',
    'HVAC_MODES',
    'OUTPUT_FREQUENCIES',
    'OUTPUT_TYPES',
    'PARAMETRIC_DEFAULTS',
    'PARAMETRIC_SCRIPT_TYPES',
    'PARAMETERS_TYPES',
    'PMV_INPUT_FIELDS',
    'PREDEFINED_MODEL_PARAMETERS',
    'RENAME_EPWS_DEFAULTS',
    'RUN_DEFAULTS',
    'SAMPLINGS',
    'SCRIPT_TYPES',
    'SETPOINT_TYPES',
    'SUPPLY_AIR_TEMP_INPUT_METHODS',
    'TABLE_DEFAULTS',
    'TABLE_FREQUENCIES',
    'TABLE_TYPES',
    'VENTILATION_CONTROLS',
    'ZONE_ARGUMENTS',
    'add_accis_arguments',
    'apmv_arguments',
    'categories_hint',
    'comfort_modes_hint',
    'comfort_standard_choices',
    'epw_files',
    'figure_arguments',
    'idf_files',
    'input_idfs',
    'output_idf_count',
    'parametric_arguments',
    'parametric_simulation_count',
    'parse_mapping',
    'parse_number',
    'parse_numbers',
    'parse_parameter_values',
    'parse_zone_arguments',
    'rename_epws_arguments',
    'run_ep_arguments',
    'simulation_csvs',
    'simulations',
    'table_arguments',
    'zone_arguments',
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
#: The initial values of the form of AddAccis (the texts of the lists are separated by commas or spaces).
ADD_ACCIS_DEFAULTS = {
    'script_type': 'vrf_mm',
    'supply_air_temp_input_method': 'temperature difference',
    'setpoint_type': 'temperature',
    'energyplus_version': 'auto',
    'output_type': 'standard',
    'output_frequencies': ['hourly'],
    'keep_existing_outputs': False,
    'add_building_averages': False,
    'comfort_standard': [1],
    'category': '3',
    'comfort_mode': '3',
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
}
#: The initial values of the form of run_ep.
RUN_DEFAULTS = {'only_accim_idfs': True, 'processes': '2', 'energyplus_version': 'auto', 'backend': 'ems'}

#: The setpoints of the aPMV (the arguments of apply_apmv_setpoints): argument -> label.
APMV_SETPOINT_FIELDS = {
    'adaptive_coefficient_cooling': 'Adaptive coefficient λ, cooling season',
    'adaptive_coefficient_heating': 'Adaptive coefficient λ, heating season',
    'pmv_cooling_setpoint': 'aPMV setpoint for cooling',
    'pmv_heating_setpoint': 'aPMV setpoint for heating',
    'cooling_setpoint_tolerance_cooling_season': 'Tolerance of the cooling setpoint, cooling season',
    'cooling_setpoint_tolerance_heating_season': 'Tolerance of the cooling setpoint, heating season',
    'heating_setpoint_tolerance_cooling_season': 'Tolerance of the heating setpoint, cooling season',
    'heating_setpoint_tolerance_heating_season': 'Tolerance of the heating setpoint, heating season',
}
#: The inputs of the PMV of the People objects (the arguments of set_pmv_input_parameters): argument -> label.
PMV_INPUT_FIELDS = {
    'activity_level': 'Activity level (W/person)',
    'clothing_insulation': 'Clothing insulation (clo)',
    'air_velocity': 'Air velocity (m/s)',
    'work_efficiency': 'Work efficiency (0 to 1)',
}
#: The initial values of the form of the aPMV setpoints (the defaults of apply_apmv_setpoints; the inputs of the PMV,
#: empty, keep those of the model).
APMV_DEFAULTS = {
    'idf': '',
    'output_idf': '',
    'energyplus_version': 'auto',
    'add_vrf_system': True,
    'supply_air_temp_input_method': 'temperature difference',
    'always_occupied': False,
    'output_frequencies': ['hourly'],
    'other_pmv_related_outputs': True,
    'adaptive_coefficient_cooling': '0.293',
    'adaptive_coefficient_heating': '-0.293',
    'pmv_cooling_setpoint': '0.5',
    'pmv_heating_setpoint': '-0.5',
    'cooling_setpoint_tolerance_cooling_season': '-0.1',
    'cooling_setpoint_tolerance_heating_season': '-0.1',
    'heating_setpoint_tolerance_cooling_season': '0.1',
    'heating_setpoint_tolerance_heating_season': '0.1',
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
)
CUSTOM_MODEL_PARAMETERS = (
    'custom_cooling_upper_limit', 'custom_cooling_lower_limit', 'custom_heating_upper_limit',
    'custom_heating_lower_limit', 'custom_upper_limit', 'custom_lower_limit', 'custom_slope', 'custom_intercept',
    'custom_cooling_offset', 'custom_heating_offset', 'custom_offset',
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
    """The comfort standards, as (comfort_standard, '1 = INT EN16798')."""
    return [(number, standard.title) for number, standard in COMFORT_STANDARDS.items()]


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


def parse_zone_arguments(text: Any, zone: str = '') -> Dict[str, Any]:
    """The arguments of a zone, from a text such as ``'comfort_standard=2, category=80, hvac_mode=0'``: pairs
    ``name=value`` separated by commas, semicolons or new lines, with the arguments of
    :func:`accim.sim.accis.modify_accis` (one value each; the dates of the cooling season can be 'dd/mm').

    :raises FormError: If an argument is not one of a zone, is repeated, or its value is not valid.
    """
    label = f'zone_arguments of {zone!r}' if zone else 'zone_arguments'
    arguments: Dict[str, Any] = {}
    for item in re.split(r'[,;\n]+', str(text)):
        item = item.strip()
        if not item:
            continue
        if '=' not in item:
            raise FormError(f'{label}: write each argument as name=value, not {item!r}.')
        name, value = (part.strip() for part in item.split('=', 1))
        if name not in ZONE_ARGUMENTS:
            raise FormError(f'{label}: {name!r} is not an argument of a zone (they are {", ".join(ZONE_ARGUMENTS)}).')
        if name in arguments:
            raise FormError(f'{label}: {name} is given twice.')
        arguments[name] = _day_value(value, name) if name in _DAY_ARGUMENTS else _number(value, f'{label}: {name}')
    if not arguments:
        raise FormError(f'{label}: give at least one argument (name=value).')
    return arguments


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


def add_accis_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :class:`accim.sim.accis.AddAccis` from the values of its form.

    :param form: The values of the form: ``folder`` and ``idfs`` (the selected input IDFs of the folder), the
        choices (``script_type``, ``supply_air_temp_input_method``, ``setpoint_type``, ``energyplus_version``,
        ``output_type``), the lists of the checked boxes or selected items (``output_frequencies``,
        ``comfort_standard``, ``hvac_mode``, ``ventilation_control``), the booleans (``keep_existing_outputs``,
        ``add_building_averages``), the texts of the other fields (lists of numbers separated by commas or
        spaces, or numbers), as in :data:`ADD_ACCIS_DEFAULTS`, and ``zone_arguments``, the rows of the table of the
        zones (see :func:`zone_arguments`; none by default).
    :return: The keyword arguments of AddAccis, with all the arguments that it would otherwise ask in the prompt,
        ``confirm=True`` and ``idfs`` (the names of the selected input IDFs, to run in the folder).
    :raises FormError: If a value is missing or not valid.
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
        name_suffix=str(form.get('name_suffix', '')).strip(),
        confirm=True,
        verbose=True,
    )
    comfort_standard = [int(number) for number in form.get('comfort_standard') or []]
    if not comfort_standard:
        raise FormError('comfort_standard: select at least one comfort standard.')
    arguments.update(
        comfort_standard=comfort_standard,
        category=parse_numbers(form.get('category', ''), 'category'),
        comfort_mode=parse_numbers(form.get('comfort_mode', ''), 'comfort_mode'),
        cooling_season_start=_day(form, 'cooling_season_start'),
        cooling_season_end=_day(form, 'cooling_season_end'),
    )
    if 99 in comfort_standard:
        arguments.update({name: parse_number(form.get(name, ''), name) for name in CUSTOM_MODEL_FIELDS})
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
    zones = zone_arguments(form.get('zone_arguments') or [])
    if zones:
        if setpoint_type != 'temperature':
            raise FormError('zone_arguments: the arguments of each zone need the adaptive setpoint temperatures '
                            '(setpoint_type temperature).')
        arguments['zone_arguments'] = zones
    return arguments


#: The arguments of AddAccis that give the output IDFs of each input IDF.
_GENERATION_ARGUMENTS = (
    'comfort_standard', 'category', 'comfort_mode', 'hvac_mode', 'ventilation_control', 'ventilation_setpoint_offset',
    'min_outdoor_temp_offset', 'max_wind_speed', 'setpoint_tolerance_start', 'setpoint_tolerance_end',
    'setpoint_tolerance_step', 'cooling_season_start', 'cooling_season_end',
)


def output_idf_count(arguments: Mapping[str, Any]) -> int:
    """The number of output IDFs that AddAccis writes for each input IDF with these arguments (those of
    :func:`add_accis_arguments`), without the combinations that have no setpoints."""
    from accim.sim.generation import GenerationArguments, combinations

    kwargs = {name: arguments[name] for name in _GENERATION_ARGUMENTS if name in arguments}
    if arguments['script_type'] in MIXED_MODE_SCRIPT_TYPES:
        generation = GenerationArguments(**kwargs)
    else:
        generation = GenerationArguments.air_conditioned(**kwargs)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return sum(1 for _ in combinations(generation, arguments['setpoint_type']))


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


def apmv_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of the aPMV setpoints (:mod:`accim.sim.apmv`) from the values of their form (as in
    :data:`APMV_DEFAULTS`, with ``folder``).

    :return: ``idf`` and ``output_idf`` (the names of the input IDF and of the IDF to write, by default
        '<input IDF>_aPMV.idf'), ``energyplus_version``, ``add_vrf_system`` and ``supply_air_temp_input_method``
        (:func:`accim.sim.apmv.add_vrf_system`), ``always_occupied``
        (:func:`accim.sim.apmv.set_zones_always_occupied`), ``apmv`` (the keyword arguments of
        :func:`accim.sim.apmv.apply_apmv_setpoints`) and ``pmv_inputs`` (those of
        :func:`accim.sim.apmv.set_pmv_input_parameters` that are given; empty to keep those of the model).
    :raises FormError: If a value is missing or not valid.
    """
    folder = _folder(form, 'the input IDF')
    idf = _file_of_folder(form, 'idf', input_idfs(folder), 'the input IDF')
    output_idf = str(form.get('output_idf', '')).strip() or f'{os.path.splitext(idf)[0]}_aPMV.idf'
    if not output_idf.lower().endswith('.idf') or os.path.basename(output_idf) != output_idf:
        raise FormError('output_idf: enter the name of an IDF file of the folder (ending in .idf).')
    if output_idf.lower() == idf.lower():
        raise FormError('output_idf: the name must differ from that of the input IDF.')
    output_frequencies = [f for f in OUTPUT_FREQUENCIES if f in (form.get('output_frequencies') or [])]
    if not output_frequencies:
        raise FormError('output_frequencies: check at least one output frequency.')
    apmv = dict(output_frequencies=output_frequencies,
                other_pmv_related_outputs=bool(form.get('other_pmv_related_outputs')),
                **{name: parse_number(form.get(name, ''), name) for name in APMV_SETPOINT_FIELDS},
                cooling_season_start=_day(form, 'cooling_season_start'),
                cooling_season_end=_day(form, 'cooling_season_end'),
                verbose=True)
    pmv_inputs = {name: parse_number(form.get(name), name) for name in PMV_INPUT_FIELDS
                  if str(form.get(name, '')).strip()}
    return dict(
        idf=idf,
        output_idf=output_idf,
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
        results), ``processes`` and ``out_dir`` (the folder of the results, in the working folder).
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
    return dict(idf=idf, epws=epws, parameters_type=parameters_type,
                script_type=_choice(form, 'script_type', PARAMETRIC_SCRIPT_TYPES),
                accis_params_dict=accis_params_dict, sampling=sampling, samples=samples, meters=meters,
                processes=_processes(form), out_dir=out_dir)


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

