# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Arguments of the functions that add the ACCIS: valid values, checks and old names."""

import math
import numbers
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union

from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS

__all__ = [
    'CustomRegime',
    'LEGACY_ARGUMENT_NAMES',
    'METRIC_CONDITIONS',
    'MIXED_MODE_SCRIPT_TYPES',
    'OUTPUT_FREQUENCIES',
    'OUTPUT_TYPES',
    'REGIME_CONDITIONS',
    'SCRIPT_TYPES',
    'SUPPLY_AIR_TEMP_INPUT_METHODS',
    'SETPOINT_TYPES',
    'check_choice',
    'check_choices',
    'check_custom_regimes',
    'is_mixed_mode',
    'normalise_energyplus_version',
    'normalise_setpoint_type',
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
#: The values of ``setpoint_type``: 'temperature' (or 'temp') for adaptive setpoint temperatures, 'pmv' for setpoints
#: based on the PMV of Fanger.
SETPOINT_TYPES = ('temperature', 'temp', 'pmv')

#: New name of each argument of accim 0.x (``accis.addAccis``, ``accis_single_idf_funcs.addAccis``,
#: ``modifyAccis``...), renamed in accim 1.0.0 to follow PEP 8 and to say what each argument is.
LEGACY_ARGUMENT_NAMES = {
    'ScriptType': 'script_type',
    'SupplyAirTempInputMethod': 'supply_air_temp_input_method',
    'Output_type': 'output_type',
    'Output_freqs': 'output_frequencies',
    'Output_keep_existing': 'keep_existing_outputs',
    'Output_gen_dataframe': 'make_outputs_dataframe',
    'Output_take_dataframe': 'outputs_dataframe',
    'EnergyPlus_version': 'energyplus_version',
    'TempCtrl': 'setpoint_type',
    'VRFschedule': 'vrf_availability_schedule',
    'ComfStand': 'comfort_standard',
    'CAT': 'category',
    'CATcoolOffset': 'category_cooling_offset',
    'CATheatOffset': 'category_heating_offset',
    'ComfMod': 'comfort_mode',
    'SetpointAcc': 'setpoint_accuracy',
    'CustAST_ACSTaul': 'custom_cooling_upper_limit',
    'CustAST_ACSTall': 'custom_cooling_lower_limit',
    'CustAST_AHSTaul': 'custom_heating_upper_limit',
    'CustAST_AHSTall': 'custom_heating_lower_limit',
    'CustAST_m': 'custom_slope',
    'CustAST_n': 'custom_intercept',
    'CustAST_ACSToffset': 'custom_cooling_offset',
    'CustAST_AHSToffset': 'custom_heating_offset',
    'CoolSeasonStart': 'cooling_season_start',
    'CoolSeasonEnd': 'cooling_season_end',
    'HVACmode': 'hvac_mode',
    'VentCtrl': 'ventilation_control',
    'MaxTempDiffVOF': 'opening_factor_max_temp_diff',
    'MinTempDiffVOF': 'opening_factor_min_temp_diff',
    'MultiplierVOF': 'min_opening_factor',
    'VSToffset': 'ventilation_setpoint_offset',
    'MinOToffset': 'min_outdoor_temp_offset',
    'MaxWindSpeed': 'max_wind_speed',
    'ASTtol_start': 'setpoint_tolerance_start',
    'ASTtol_end_input': 'setpoint_tolerance_end',
    'ASTtol_steps': 'setpoint_tolerance_step',
    'ASTtol': 'setpoint_tolerance',
    'NameSuffix': 'name_suffix',
    'verboseMode': 'verbose',
    'confirmGen': 'confirm',
    # The names of accim 0.x that 1.0.0 also renames
    'make_averages': 'add_building_averages',
    'debugging': 'debug_ems',
    'eer': 'vrf_eer',
    'cop': 'vrf_cop',
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


def normalise_setpoint_type(setpoint_type: str) -> str:
    """Return 'temperature' or 'pmv'."""
    check_choice('setpoint_type', setpoint_type.lower() if isinstance(setpoint_type, str) else setpoint_type,
                 SETPOINT_TYPES)
    return 'pmv' if setpoint_type.lower() == 'pmv' else 'temperature'


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


#: The conditions of the regimes of the custom comfort model (:class:`CustomRegime`) without a value: 'always' (only
#: the last regime); 'cooling_season' and 'heating_season', the days of the cooling season of the zone (from
#: ``cooling_season_start`` to the day before ``cooling_season_end``, as CoolingSeason of the setpoints) and the other
#: days; 'hvac_off' and 'hvac_on', in mixed mode only, whether the HVAC system of the zone neither heated nor cooled in
#: the previous timestep (the condition with which the program ApplyAST_<zone> of mixed mode opens the windows) or it
#: did.
REGIME_CONDITIONS = ('always', 'cooling_season', 'heating_season', 'hvac_off', 'hvac_on')
#: The conditions with a value, which compare the outdoor metric of the custom model of the zone (PMOT, or that of
#: ``custom_outdoor_metric``): ``('metric_below', x)``, lower than x; ``('metric_above', x)``, higher than x;
#: ``('metric_between', (x1, x2))``, from x1 to x2, both included (as the applicability limits of the ACCIS).
METRIC_CONDITIONS = ('metric_below', 'metric_above', 'metric_between')
_REGIME_NUMBERS = ('slope', 'intercept', 'cooling_offset', 'heating_offset', 'cooling_lower_limit',
                   'cooling_upper_limit', 'heating_lower_limit', 'heating_upper_limit')


def _is_number(value: Any) -> bool:
    return isinstance(value, numbers.Real) and not isinstance(value, bool) and math.isfinite(value)


def _regime_condition(condition: Any) -> Union[str, Tuple[str, Any]]:
    """The condition of a regime, checked: a name of :data:`REGIME_CONDITIONS` (in lower case), or a tuple
    ``(name, value)`` of :data:`METRIC_CONDITIONS` (``(x1, x2)``, with x1 lower than x2, for 'metric_between')."""
    valid = (f"one of {list(REGIME_CONDITIONS)}, or ('metric_below', x), ('metric_above', x) or "
             f"('metric_between', (x1, x2))")
    if isinstance(condition, str):
        name = condition.strip().lower()
        if name in REGIME_CONDITIONS:
            return name
        if name in METRIC_CONDITIONS:
            raise ValueError(f'The condition {condition!r} of a regime of the custom model needs a value: {valid}.')
    elif isinstance(condition, (list, tuple)) and len(condition) == 2 and isinstance(condition[0], str):
        name, value = condition[0].strip().lower(), condition[1]
        if name in ('metric_below', 'metric_above') and _is_number(value):
            return name, value
        if name == 'metric_between':
            if (isinstance(value, (list, tuple)) and len(value) == 2 and all(_is_number(v) for v in value)
                    and value[0] < value[1]):
                return name, (value[0], value[1])
            raise ValueError(f"The condition 'metric_between' of a regime of the custom model needs two numbers, the "
                             f"lower first, such as ('metric_between', (10, 20)), not {value!r}.")
    raise ValueError(f'{condition!r} is not a condition of a regime of the custom model: {valid}.')


@dataclass(frozen=True)
class CustomRegime:
    """A regime of the custom comfort model (comfort standard 99), the argument ``custom_regimes`` of
    :class:`accim.sim.accis.AddAccis` and :func:`accim.sim.accis.modify_accis` (proposal B2 of accim 1.2.0): the
    coefficients of the custom model while its condition holds. In each timestep, the first regime of the list whose
    condition holds sets the inputs of the custom model of the zone (decision D6 of the brief of 1.2.0, see
    :mod:`accim.sim.ems.custom_regimes`); if none holds, those of the scalar arguments (``custom_slope``...) apply, so
    the last regime is 'always' or the scalar arguments are the last regime.

    :ivar slope: The slope m of the comfort temperature (m · outdoor metric + n), as ``custom_slope``.
    :ivar intercept: The intercept n, as ``custom_intercept``.
    :ivar cooling_offset: The offset of the cooling setpoint from the comfort temperature, as
        ``custom_cooling_offset``.
    :ivar heating_offset: The offset of the heating setpoint, as ``custom_heating_offset``.
    :ivar cooling_lower_limit: The lower applicability limit of the cooling setpoint (of the outdoor metric), as
        ``custom_cooling_lower_limit``.
    :ivar cooling_upper_limit: The upper applicability limit of the cooling setpoint, as
        ``custom_cooling_upper_limit``.
    :ivar heating_lower_limit: The lower applicability limit of the heating setpoint, as
        ``custom_heating_lower_limit``.
    :ivar heating_upper_limit: The upper applicability limit of the heating setpoint, as
        ``custom_heating_upper_limit``.
    :ivar condition: When the regime applies: a name of :data:`REGIME_CONDITIONS` ('always' by default) or a tuple of
        :data:`METRIC_CONDITIONS`, such as ``('metric_below', 10)``.
    :ivar outdoor_metric: The outdoor metric of the regime; only None (the outdoor metric of the zone,
        ``custom_outdoor_metric``) in this version.
    :raises ValueError: If a coefficient is not a number, or the condition or the outdoor metric is not valid.
    """

    slope: float
    intercept: float
    cooling_offset: float
    heating_offset: float
    cooling_lower_limit: float
    cooling_upper_limit: float
    heating_lower_limit: float
    heating_upper_limit: float
    condition: Union[str, Tuple[str, Any]] = 'always'
    outdoor_metric: Optional[str] = None

    def __post_init__(self):
        for name in _REGIME_NUMBERS:
            if not _is_number(getattr(self, name)):
                raise ValueError(f'{name} of a regime of the custom model must be a number, not '
                                 f'{getattr(self, name)!r}.')
        object.__setattr__(self, 'condition', _regime_condition(self.condition))
        if self.outdoor_metric is not None:
            raise ValueError(f'outdoor_metric of a regime of the custom model must be None (its outdoor metric is that '
                             f'of the zone, custom_outdoor_metric): an outdoor metric for each regime is not '
                             f'available yet, not {self.outdoor_metric!r}.')


def check_custom_regimes(regimes: Any) -> Tuple[CustomRegime, ...]:
    """Check the argument ``custom_regimes``: a list of :class:`CustomRegime`, whose only regime with the condition
    'always' is the last one (the regimes after it would never apply); None (or an empty list) for none.

    :return: The regimes, as a tuple (empty for none).
    :raises ValueError: If it is not a list of regimes, or a regime 'always' is not the last one.
    """
    if regimes is None:
        return ()
    if isinstance(regimes, CustomRegime):
        regimes = [regimes]
    if not isinstance(regimes, (list, tuple)) or not all(isinstance(r, CustomRegime) for r in regimes):
        raise ValueError(f'custom_regimes must be a list of CustomRegime (accim.sim.arguments.CustomRegime), or '
                         f'None, not {regimes!r}.')
    always = [number for number, regime in enumerate(regimes, start=1) if regime.condition == 'always']
    if always and always[0] != len(regimes):
        raise ValueError(f"The regime {always[0]} of custom_regimes has the condition 'always', so the regimes after "
                         f"it would never apply: only the last regime can have it.")
    return tuple(regimes)
