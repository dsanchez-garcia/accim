# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The forms of the graphical user interface of accim: their choices and defaults, and the arguments of the functions
of accim that they give, checked.

This module does not use tkinter, so that the forms can be tested without a display: :mod:`accim.gui.app` reads the
values of its widgets into a dictionary (texts, booleans and lists of the selected choices) and passes it to these
functions.
"""

import os
import re
import warnings
from typing import Any, Dict, Iterable, List, Mapping, Tuple, Union

from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS
from accim.sim.arguments import MIXED_MODE_SCRIPT_TYPES, OUTPUT_FREQUENCIES, SUPPLY_AIR_TEMP_INPUT_METHODS
from accim.sim.standards import COMFORT_STANDARDS

__all__ = [
    'ADD_ACCIS_DEFAULTS',
    'BACKENDS',
    'CUSTOM_MODEL_FIELDS',
    'ENERGYPLUS_VERSIONS',
    'FormError',
    'HVAC_MODES',
    'OUTPUT_FREQUENCIES',
    'OUTPUT_TYPES',
    'RUN_DEFAULTS',
    'SCRIPT_TYPES',
    'SUPPLY_AIR_TEMP_INPUT_METHODS',
    'TEMP_CTRLS',
    'VENT_CTRLS',
    'add_accis_arguments',
    'categories_hint',
    'comfort_modes_hint',
    'comfort_standard_choices',
    'input_idfs',
    'output_idf_count',
    'parse_number',
    'parse_numbers',
    'run_ep_arguments',
    'simulations',
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
TEMP_CTRLS = {'temperature': 'Adaptive setpoint temperatures', 'pmv': 'PMV-based setpoints (Fanger)'}
ENERGYPLUS_VERSIONS = ('auto',) + tuple(SUPPORTED_ENERGYPLUS_VERSIONS)
HVAC_MODES = {0: 'Full air-conditioning', 1: 'Natural ventilation only', 2: 'Mixed mode'}
VENT_CTRLS = {
    0: 'Above the comfort temperature; windows fully open',
    1: 'Above the lower comfort limit; windows fully open',
    2: 'Above the comfort temperature; opening factor',
    3: 'Above the lower comfort limit; opening factor',
}
BACKENDS = {'ems': 'Energy Management System of EnergyPlus', 'api': 'Python API of EnergyPlus (24.2 or later)'}
#: The arguments of the custom comfort model (ComfStand 99): argument -> (label, default). The defaults are those of
#: ASHRAE 55 with 80 % acceptability, as in the parametric module.
CUSTOM_MODEL_FIELDS = {
    'cust_ast_m': ('Slope m (comfort temperature = m·T + n)', '0.31'),
    'cust_ast_n': ('Intercept n', '17.8'),
    'cust_ast_acst_offset': ('Offset of the cooling setpoint (°C)', '3.5'),
    'cust_ast_ahst_offset': ('Offset of the heating setpoint (°C)', '-3.5'),
    'cust_ast_acst_aul': ('Upper applicability limit, cooling (°C)', '33.5'),
    'cust_ast_acst_all': ('Lower applicability limit, cooling (°C)', '10'),
    'cust_ast_ahst_aul': ('Upper applicability limit, heating (°C)', '33.5'),
    'cust_ast_ahst_all': ('Lower applicability limit, heating (°C)', '10'),
}
#: The initial values of the form of AddAccis (the texts of the lists are separated by commas or spaces).
ADD_ACCIS_DEFAULTS = {
    'script_type': 'vrf_mm',
    'supply_air_temp_input_method': 'temperature difference',
    'temp_ctrl': 'temperature',
    'energyplus_version': 'auto',
    'output_type': 'standard',
    'output_freqs': ['hourly'],
    'output_keep_existing': False,
    'make_averages': False,
    'comf_stand': [1],
    'cat': '3',
    'comf_mod': '3',
    'cool_season_start': '121',
    'cool_season_end': '274',
    'hvac_mode': [2],
    'vent_ctrl': [0],
    'vst_offset': '0',
    'min_ot_offset': '50',
    'max_wind_speed': '50',
    'max_temp_diff_vof': '6',
    'min_temp_diff_vof': '1',
    'multiplier_vof': '0.25',
    'ast_tol_start': '0.1',
    'ast_tol_end_input': '0.1',
    'ast_tol_steps': '0.1',
    'name_suffix': '',
    **{name: default for name, (_, default) in CUSTOM_MODEL_FIELDS.items()},
}
#: The initial values of the form of run_ep.
RUN_DEFAULTS = {'run_only_accim': True, 'num_cpus': '2', 'energyplus_version': 'auto', 'backend': 'ems'}

_SEPARATORS = re.compile(r'[\s,;]+')


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
    """The comfort standards, as (ComfStand, '1 = INT EN16798')."""
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
    """The categories (CAT) of each comfort standard, one line each."""
    return _hint(standards, 'categories', 'no categories (any value)')


def comfort_modes_hint(standards: Iterable[int]) -> str:
    """The comfort modes (ComfMod) of each comfort standard, one line each."""
    return _hint(standards, 'comfort_modes', 'no comfort modes (any value)')


def input_idfs(folder: Union[str, os.PathLike]) -> List[str]:
    """The IDF files of a folder that AddAccis takes as input: not the output IDFs of accim ('[' in the name) nor its
    intermediate files ('_pymod')."""
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    return sorted(name for name in names
                  if name.lower().endswith('.idf') and '[' not in name and '_pymod' not in name)


def _choice(form: Mapping[str, Any], name: str, choices: Iterable[str]) -> str:
    value = str(form.get(name, '')).strip()
    choices = list(choices)
    if value not in choices:
        raise FormError(f'{name}: choose one of {choices}.')
    return value


def _day(form: Mapping[str, Any], name: str) -> Union[int, str]:
    from accim.sim.arguments import to_day_of_year

    text = str(form.get(name, '')).strip()
    value: Union[int, str] = int(text) if text.isdigit() else text
    try:
        to_day_of_year(value, name)
    except ValueError as error:
        raise FormError(str(error)) from None
    return value


def add_accis_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :class:`accim.sim.accis.AddAccis` from the values of its form.

    :param form: The values of the form: ``folder`` and ``idfs`` (the selected input IDFs of the folder), the
        choices (``script_type``, ``supply_air_temp_input_method``, ``temp_ctrl``, ``energyplus_version``,
        ``output_type``), the lists of the checked boxes or selected items (``output_freqs``, ``comf_stand``,
        ``hvac_mode``, ``vent_ctrl``), the booleans (``output_keep_existing``, ``make_averages``) and the texts of
        the other fields (lists of numbers separated by commas or spaces, or numbers), as in
        :data:`ADD_ACCIS_DEFAULTS`.
    :return: The keyword arguments of AddAccis, with all the arguments that it would otherwise ask in the prompt,
        ``confirm_gen=True`` and ``idfs`` (the names of the selected input IDFs, to run in the folder).
    :raises FormError: If a value is missing or not valid.
    """
    folder = str(form.get('folder', '')).strip()
    if not folder or not os.path.isdir(folder):
        raise FormError('folder: choose the folder of the input IDFs.')
    idfs = list(form.get('idfs') or [])
    if not idfs:
        raise FormError('idfs: select at least one input IDF.')
    script_type = _choice(form, 'script_type', SCRIPT_TYPES)
    temp_ctrl = _choice(form, 'temp_ctrl', TEMP_CTRLS)
    output_freqs = [f for f in OUTPUT_FREQUENCIES if f in (form.get('output_freqs') or [])]
    if not output_freqs:
        raise FormError('output_freqs: check at least one output frequency.')
    arguments: Dict[str, Any] = dict(
        idfs=idfs,
        script_type=script_type,
        supply_air_temp_input_method=_choice(form, 'supply_air_temp_input_method', SUPPLY_AIR_TEMP_INPUT_METHODS),
        output_type=_choice(form, 'output_type', OUTPUT_TYPES),
        output_freqs=output_freqs,
        output_keep_existing=bool(form.get('output_keep_existing')),
        output_gen_dataframe=False,
        energyplus_version=_choice(form, 'energyplus_version', ENERGYPLUS_VERSIONS),
        temp_ctrl=temp_ctrl,
        make_averages=bool(form.get('make_averages')),
        name_suffix=str(form.get('name_suffix', '')).strip(),
        confirm_gen=True,
        verbose_mode=True,
    )
    comf_stand = [int(number) for number in form.get('comf_stand') or []]
    if not comf_stand:
        raise FormError('comf_stand: select at least one comfort standard.')
    arguments.update(
        comf_stand=comf_stand,
        cat=parse_numbers(form.get('cat', ''), 'cat'),
        comf_mod=parse_numbers(form.get('comf_mod', ''), 'comf_mod'),
        cool_season_start=_day(form, 'cool_season_start'),
        cool_season_end=_day(form, 'cool_season_end'),
    )
    if 99 in comf_stand:
        arguments.update({name: parse_number(form.get(name, ''), name) for name in CUSTOM_MODEL_FIELDS})
    if script_type in MIXED_MODE_SCRIPT_TYPES:
        hvac_mode = sorted(int(mode) for mode in form.get('hvac_mode') or [])
        vent_ctrl = sorted(int(control) for control in form.get('vent_ctrl') or [])
        if not hvac_mode:
            raise FormError('hvac_mode: check at least one HVAC mode.')
        if not vent_ctrl:
            raise FormError('vent_ctrl: check at least one ventilation control.')
        arguments.update(
            hvac_mode=hvac_mode,
            vent_ctrl=vent_ctrl,
            vst_offset=parse_numbers(form.get('vst_offset', ''), 'vst_offset'),
            min_ot_offset=parse_numbers(form.get('min_ot_offset', ''), 'min_ot_offset'),
            max_wind_speed=parse_numbers(form.get('max_wind_speed', ''), 'max_wind_speed'),
            max_temp_diff_vof=parse_number(form.get('max_temp_diff_vof', ''), 'max_temp_diff_vof'),
            min_temp_diff_vof=parse_number(form.get('min_temp_diff_vof', ''), 'min_temp_diff_vof'),
            multiplier_vof=parse_number(form.get('multiplier_vof', ''), 'multiplier_vof'),
        )
    else:
        arguments.update(hvac_mode=[0], vent_ctrl=[0])
    arguments.update(
        ast_tol_start=parse_number(form.get('ast_tol_start', ''), 'ast_tol_start'),
        ast_tol_end_input=parse_number(form.get('ast_tol_end_input', ''), 'ast_tol_end_input'),
        ast_tol_steps=parse_number(form.get('ast_tol_steps', ''), 'ast_tol_steps'),
    )
    if arguments['ast_tol_steps'] <= 0:
        raise FormError('ast_tol_steps: enter a number greater than 0.')
    return arguments


#: The arguments of AddAccis that give the output IDFs of each input IDF.
_GENERATION_ARGUMENTS = (
    'comf_stand', 'cat', 'comf_mod', 'hvac_mode', 'vent_ctrl', 'vst_offset', 'min_ot_offset', 'max_wind_speed',
    'ast_tol_start', 'ast_tol_end_input', 'ast_tol_steps', 'cool_season_start', 'cool_season_end',
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
        return sum(1 for _ in combinations(generation, arguments['temp_ctrl']))


def run_ep_arguments(form: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :func:`accim.run.run_ep` from the values of its form (``folder``, ``run_only_accim``,
    ``num_cpus``, ``energyplus_version`` and ``backend``), with ``confirm_run=True``.

    :raises FormError: If a value is missing or not valid.
    """
    folder = str(form.get('folder', '')).strip()
    if not folder or not os.path.isdir(folder):
        raise FormError('folder: choose the folder of the IDFs and EPWs.')
    num_cpus = parse_number(form.get('num_cpus', ''), 'num_cpus')
    if not isinstance(num_cpus, int) or num_cpus < 1:
        raise FormError('num_cpus: enter a whole number greater than 0.')
    return dict(
        run_only_accim=bool(form.get('run_only_accim')),
        confirm_run=True,
        num_cpus=num_cpus,
        energyplus_version=_choice(form, 'energyplus_version', ENERGYPLUS_VERSIONS),
        backend=_choice(form, 'backend', BACKENDS),
    )


def simulations(folder: Union[str, os.PathLike], run_only_accim: bool) -> List[Tuple[str, str]]:
    """The simulations that :func:`accim.run.run_ep` runs in a folder: (IDF, EPW) for each IDF (only the output IDFs
    of accim, with '[' in the name, if ``run_only_accim``) and each EPW."""
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    idfs = [name for name in names if name.endswith('.idf') and ('[' in name or not run_only_accim)]
    epws = [name for name in names if name.endswith('.epw')]
    return [(idf, epw) for idf in idfs for epw in epws]
