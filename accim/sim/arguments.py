# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Arguments of the functions that add the ACCIS: valid values, checks and old names."""

from datetime import date
from typing import Any, Iterable, List, Optional, Sequence

from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS

__all__ = [
    'LEGACY_ARGUMENT_NAMES',
    'MIXED_MODE_SCRIPT_TYPES',
    'OUTPUT_FREQUENCIES',
    'OUTPUT_TYPES',
    'SCRIPT_TYPES',
    'SUPPLY_AIR_TEMP_INPUT_METHODS',
    'TEMP_CTRL_VALUES',
    'check_choice',
    'check_choices',
    'is_mixed_mode',
    'normalise_energyplus_version',
    'normalise_temp_ctrl',
    'to_bool',
    'to_day_of_year',
]

#: 'vrf_ac' and 'vrf_mm' add a VRF system to each occupied zone, with full air-conditioning or mixed mode;
#: 'ex_ac' and 'ex_mm' use the existing HVAC systems of the model.
SCRIPT_TYPES = ('vrf_ac', 'vrf_mm', 'ex_mm', 'ex_ac')
MIXED_MODE_SCRIPT_TYPES = ('vrf_mm', 'ex_mm')
#: Supply air temperature input methods of the Sizing:Zone objects of the VRF systems, and their IDF values.
SUPPLY_AIR_TEMP_INPUT_METHODS = {
    'supply air temperature': 'SupplyAirTemperature',
    'temperature difference': 'TemperatureDifference',
}
OUTPUT_TYPES = ('standard', 'simplified', 'detailed', 'custom')
OUTPUT_FREQUENCIES = ('timestep', 'hourly', 'daily', 'monthly', 'runperiod')
#: 'temperature' (or 'temp') for adaptive setpoint temperatures, 'pmv' for Fanger PMV setpoints.
TEMP_CTRL_VALUES = ('temperature', 'temp', 'pmv')

#: New name of each argument of accim 0.x (``accis.addAccis``, ``accis_single_idf_funcs.addAccis``,
#: ``modifyAccis``...), renamed to follow PEP 8 in accim 1.0.0.
LEGACY_ARGUMENT_NAMES = {
    'ScriptType': 'script_type',
    'SupplyAirTempInputMethod': 'supply_air_temp_input_method',
    'Output_type': 'output_type',
    'Output_freqs': 'output_freqs',
    'Output_keep_existing': 'output_keep_existing',
    'Output_gen_dataframe': 'output_gen_dataframe',
    'Output_take_dataframe': 'output_take_dataframe',
    'EnergyPlus_version': 'energyplus_version',
    'TempCtrl': 'temp_ctrl',
    'VRFschedule': 'vrf_schedule',
    'ComfStand': 'comf_stand',
    'CAT': 'cat',
    'CATcoolOffset': 'cat_cool_offset',
    'CATheatOffset': 'cat_heat_offset',
    'ComfMod': 'comf_mod',
    'SetpointAcc': 'setpoint_acc',
    'CustAST_ACSTaul': 'cust_ast_acst_aul',
    'CustAST_ACSTall': 'cust_ast_acst_all',
    'CustAST_AHSTaul': 'cust_ast_ahst_aul',
    'CustAST_AHSTall': 'cust_ast_ahst_all',
    'CustAST_m': 'cust_ast_m',
    'CustAST_n': 'cust_ast_n',
    'CustAST_ACSToffset': 'cust_ast_acst_offset',
    'CustAST_AHSToffset': 'cust_ast_ahst_offset',
    'CoolSeasonStart': 'cool_season_start',
    'CoolSeasonEnd': 'cool_season_end',
    'HVACmode': 'hvac_mode',
    'VentCtrl': 'vent_ctrl',
    'MaxTempDiffVOF': 'max_temp_diff_vof',
    'MinTempDiffVOF': 'min_temp_diff_vof',
    'MultiplierVOF': 'multiplier_vof',
    'VSToffset': 'vst_offset',
    'MinOToffset': 'min_ot_offset',
    'MaxWindSpeed': 'max_wind_speed',
    'ASTtol_start': 'ast_tol_start',
    'ASTtol_end_input': 'ast_tol_end_input',
    'ASTtol_steps': 'ast_tol_steps',
    'ASTtol': 'ast_tol',
    'NameSuffix': 'name_suffix',
    'verboseMode': 'verbose_mode',
    'confirmGen': 'confirm_gen',
}


def is_mixed_mode(script_type: str) -> bool:
    """True for the script types with natural ventilation (mixed mode)."""
    return script_type in MIXED_MODE_SCRIPT_TYPES


def check_choice(name: str, value: Any, choices: Iterable, hint: str = '') -> None:
    """Raise a ValueError if value is not one of the choices."""
    choices = list(choices)
    if value not in choices:
        raise ValueError(f'{value!r} is not a valid {name}. {hint}Valid values: {choices}.')


def check_choices(name: str, values: Sequence, choices: Iterable) -> None:
    """Raise a ValueError if values is not a list whose items are all in choices."""
    choices = list(choices)
    if isinstance(values, str) or not isinstance(values, (list, tuple)):
        raise ValueError(f'{name} must be a list, for instance {choices[:2]}. Valid values: {choices}.')
    invalid = [v for v in values if v not in choices]
    if invalid:
        raise ValueError(f'{invalid} are not valid {name}. Valid values: {choices}.')


def normalise_temp_ctrl(temp_ctrl: str) -> str:
    """Return 'temperature' or 'pmv'."""
    check_choice('temp_ctrl', temp_ctrl.lower() if isinstance(temp_ctrl, str) else temp_ctrl, TEMP_CTRL_VALUES)
    return 'pmv' if temp_ctrl.lower() == 'pmv' else 'temperature'


def normalise_energyplus_version(energyplus_version: Optional[str]) -> str:
    """Return a supported EnergyPlus version ('9.1'...'26.2') or 'auto' (None means 'auto')."""
    if energyplus_version is None or str(energyplus_version).lower() == 'auto':
        return 'auto'
    version = str(energyplus_version)
    check_choice('energyplus_version', version, list(SUPPORTED_ENERGYPLUS_VERSIONS) + ['auto'])
    return version


def to_bool(value: Any, name: str) -> bool:
    """Accept booleans and the strings 'true' and 'false' (which the prompts return)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    raise ValueError(f'{name} must be True or False, not {value!r}.')


def to_day_of_year(value: Any, name: str = 'day') -> int:
    """Day of the year of a date in 'dd/mm' format, or of a day of the year (1 to 366)."""
    message = f'{name} must be a date in dd/mm format or a day of the year, not {value!r}.'
    if isinstance(value, str):
        parts = value.split('/')
        try:
            if len(parts) == 1:
                day = int(parts[0])
            elif len(parts) == 2:
                day = date(2007, int(parts[1]), int(parts[0])).timetuple().tm_yday
            else:
                raise ValueError(message)
        except ValueError:
            raise ValueError(message) from None
    elif isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
        raise ValueError(message)
    else:
        day = int(value)
    if not 1 <= day <= 366:
        raise ValueError(f'{name} must be between 1 and 366 (it is {day}).')
    return day


def as_list(value: Any) -> List:
    """A single value as a list of one value; lists and tuples as lists."""
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]
