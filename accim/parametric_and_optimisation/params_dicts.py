# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Mappings between public parameter names and IDF modifier callables.

Exports dictionaries for predefined ACCIM models, custom ACCIM models,
APMV setpoints, and a merged `all_params` dictionary.

The names of the parameters are those of the arguments of :mod:`accim.sim` (``comfort_standard``, ``category``,
``comfort_mode``...). The names of accim 0.x (``ComfStand``, ``CAT``, ``ComfMod``...), and those of the development
of accim 1.2.0 (``heating_setpoint_floor`` and ``cooling_setpoint_ceiling``, now ``heating_setpoint_minimum`` and
``cooling_setpoint_maximum``), in :data:`LEGACY_PARAMETER_NAMES`, keep working with a DeprecationWarning (see
:func:`resolve_parameter_name`). The
modifier functions keep the names of the EMS variables that they set (``modify_ComfStand``...).

Usage
-----
Import this module when building parameter descriptors that need a stable
lookup from public parameter names to callable modifier functions.

Examples
--------
modifier = all_params['comfort_standard']
"""

import functools
import re
import warnings

from accim.parametric_and_optimisation.funcs_for_besos import param_accis, param_apmv
from accim.sim.arguments import DEPRECATED_ARGUMENT_NAMES
from accim.sim.ems.custom_regimes import REGIME_INPUTS

accim_predef_model_params = {
    # accim predefined models parameters
    'comfort_standard': param_accis.modify_ComfStand,
    'category': param_accis.modify_CAT,
    'category_cooling_offset': param_accis.modify_CATcoolOffset,
    'category_heating_offset': param_accis.modify_CATheatOffset,
    'comfort_mode': param_accis.modify_ComfMod,
    'setpoint_accuracy': param_accis.modify_SetpointAcc,
    'cooling_season_start': param_accis.modify_CoolSeasonStart,
    'cooling_season_end': param_accis.modify_CoolSeasonEnd,
    'hvac_mode': param_accis.modify_HVACmode,
    'ventilation_control': param_accis.modify_VentCtrl,
    'opening_factor_max_temp_diff': param_accis.modify_MaxTempDiffVOF,
    'opening_factor_min_temp_diff': param_accis.modify_MinTempDiffVOF,
    'min_opening_factor': param_accis.modify_MultiplierVOF,
    'ventilation_setpoint_offset': param_accis.modify_VSToffset,
    'min_outdoor_temp_offset': param_accis.modify_MinOToffset,
    'max_wind_speed': param_accis.modify_MaxWindSpeed,
    'setpoint_tolerance': param_accis.modify_ASTtol,
    # The minimum heating setpoint and the maximum cooling setpoint (accim 1.2.0)
    'heating_setpoint_minimum': param_accis.modify_AHSTmin,
    'cooling_setpoint_maximum': param_accis.modify_ACSTmax,
    # The static setpoints of JPN Aqilah 2025 (accim 1.2.0; the other comfort standards ignore them)
    'static_heating_setpoint': param_accis.modify_StaticAHST,
    'static_cooling_setpoint': param_accis.modify_StaticACST,
}
accim_custom_model_params = {
    # accim custom models parameters
    'custom_cooling_upper_limit': param_accis.modify_CustAST_ACSTaul,
    'custom_cooling_lower_limit': param_accis.modify_CustAST_ACSTall,
    'custom_heating_upper_limit': param_accis.modify_CustAST_AHSTaul,
    'custom_heating_lower_limit': param_accis.modify_CustAST_AHSTall,
    'custom_upper_limit': param_accis.modify_CustAST_ASTaul,
    'custom_lower_limit': param_accis.modify_CustAST_ASTall,
    'custom_slope': param_accis.modify_CustAST_m,
    'custom_intercept': param_accis.modify_CustAST_n,
    'custom_cooling_offset': param_accis.modify_CustAST_ACSToffset,
    'custom_heating_offset': param_accis.modify_CustAST_AHSToffset,
    'custom_offset': param_accis.modify_CustAST_ASToffset,
    # The minimum heating setpoint and the maximum cooling setpoint (accim 1.2.0)
    'heating_setpoint_minimum': param_accis.modify_AHSTmin,
    'cooling_setpoint_maximum': param_accis.modify_ACSTmax,
    # The outdoor metric of the custom model (accim 1.2.0; custom_outdoor_metric takes the codes of the metrics)
    'custom_outdoor_metric': param_accis.modify_CustAST_metric,
    'custom_alpha': param_accis.modify_CustAST_alpha,
    'custom_days': param_accis.modify_CustAST_days,
}
apmv_setpoints_params = {
    # apmv setpoints parameters
    'adaptive_coefficient': param_apmv.change_adaptive_coeff_all_zones,
    'adaptive_coefficient_cooling': param_apmv.change_adaptive_coeff_cooling_all_zones,
    'adaptive_coefficient_heating': param_apmv.change_adaptive_coeff_heating_all_zones,
    'pmv_setpoint': param_apmv.change_pmv_setpoint_all_zones,
    'pmv_cooling_setpoint': param_apmv.change_pmv_cooling_setpoint_all_zones,
    'pmv_heating_setpoint': param_apmv.change_pmv_heating_setpoint_all_zones,
    # The inputs of the PMV of the occupants (accim 1.2.0)
    'clothing_insulation': param_apmv.change_clothing_insulation_all_zones,
    'activity_level': param_apmv.change_activity_level_all_zones,
    'air_velocity': param_apmv.change_air_velocity_all_zones,
}
epmv_setpoints_params = {
    # epmv setpoints parameters (the setpoints are on the ePMV scale)
    'expectancy_factor': param_apmv.change_expectancy_factor_all_zones,
    'pmv_setpoint': param_apmv.change_pmv_setpoint_all_zones,
    'pmv_cooling_setpoint': param_apmv.change_pmv_cooling_setpoint_all_zones,
    'pmv_heating_setpoint': param_apmv.change_pmv_heating_setpoint_all_zones,
    # The inputs of the PMV of the occupants (accim 1.2.0)
    'clothing_insulation': param_apmv.change_clothing_insulation_all_zones,
    'activity_level': param_apmv.change_activity_level_all_zones,
    'air_velocity': param_apmv.change_air_velocity_all_zones,
}

all_params = {}
all_params.update(accim_predef_model_params)
all_params.update(accim_custom_model_params)
all_params.update(apmv_setpoints_params)
all_params.update(epmv_setpoints_params)

#: The coefficients of each regime of the custom model (``custom_regimes``, accim 1.2.0) that are parameters of the
#: accim custom models: ``custom_regime_<regime>_<field>``, such as ``custom_regime_1_slope``, with these fields of
#: :class:`accim.sim.arguments.CustomRegime` (see :func:`custom_regime_parameter`)
CUSTOM_REGIME_FIELDS = tuple(REGIME_INPUTS)
_CUSTOM_REGIME_PARAMETER = re.compile(rf"^custom_regime_([1-9]\d*)_({'|'.join(CUSTOM_REGIME_FIELDS)})$",
                                      re.IGNORECASE)


def custom_regime_parameter(name):
    """The regime (from 1) and the field of a parameter of the coefficients of the regimes of the custom model
    (``custom_regime_<regime>_<field>``, such as ``custom_regime_1_slope``), or None if the name is not one of them.

    The number of regimes depends on the model, so these parameters are not in :data:`all_params`: their modifier is
    :func:`custom_regime_modifier`.
    """
    match = _CUSTOM_REGIME_PARAMETER.match(name) if isinstance(name, str) else None
    return (int(match.group(1)), match.group(2).lower()) if match else None


def custom_regime_modifier(name):
    """The modifier of a parameter of the coefficients of the regimes of the custom model
    (:func:`custom_regime_parameter`): ``modify_custom_regime`` of
    :mod:`accim.parametric_and_optimisation.funcs_for_besos.param_accis` with its regime and field (a
    ``functools.partial``, which can be sent to other processes).

    :raises KeyError: If the name is not one of these parameters.
    """
    found = custom_regime_parameter(name)
    if found is None:
        raise KeyError(f'{name!r} is not a parameter of the regimes of the custom model '
                       f'(custom_regime_<regime>_<field>, with the fields {list(CUSTOM_REGIME_FIELDS)}).')
    return functools.partial(param_accis.modify_custom_regime, regime=found[0], field=found[1])

#: The names of the parameters in accim 0.x -> their names since accim 1.0.0
LEGACY_PARAMETER_NAMES = {
    'ComfStand': 'comfort_standard',
    'CAT': 'category',
    'CATcoolOffset': 'category_cooling_offset',
    'CATheatOffset': 'category_heating_offset',
    'ComfMod': 'comfort_mode',
    'SetpointAcc': 'setpoint_accuracy',
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
    'ASTtol': 'setpoint_tolerance',
    'CustAST_ACSTaul': 'custom_cooling_upper_limit',
    'CustAST_ACSTall': 'custom_cooling_lower_limit',
    'CustAST_AHSTaul': 'custom_heating_upper_limit',
    'CustAST_AHSTall': 'custom_heating_lower_limit',
    'CustAST_ASTaul': 'custom_upper_limit',
    'CustAST_ASTall': 'custom_lower_limit',
    'CustAST_m': 'custom_slope',
    'CustAST_n': 'custom_intercept',
    'CustAST_ACSToffset': 'custom_cooling_offset',
    'CustAST_AHSToffset': 'custom_heating_offset',
    'CustAST_ASToffset': 'custom_offset',
    'Adaptive coefficient': 'adaptive_coefficient',
    'Adaptive cooling coefficient': 'adaptive_coefficient_cooling',
    'Adaptive heating coefficient': 'adaptive_coefficient_heating',
    'PMV setpoint': 'pmv_setpoint',
    'PMV cooling setpoint': 'pmv_cooling_setpoint',
    'PMV heating setpoint': 'pmv_heating_setpoint',
    # The names of the development of accim 1.2.0, renamed before its release (deprecated since accim 1.2.0)
    **DEPRECATED_ARGUMENT_NAMES,
}
_LEGACY_BY_LOWER = {old.lower(): new for old, new in LEGACY_PARAMETER_NAMES.items()}
#: The version of accim since which each old name is deprecated (1.0.0 for the names of accim 0.x)
_LEGACY_VERSIONS = {old.lower(): '1.2.0' for old in DEPRECATED_ARGUMENT_NAMES}
_NEW_BY_LOWER = {new.lower(): new for new in all_params}


def legacy_parameter_name(name):
    """The current name of an old parameter name (of accim 0.x, or of the development of accim 1.2.0;
    case-insensitive), or None if it is not one."""
    if not isinstance(name, str) or name.lower() in _NEW_BY_LOWER:
        return None
    return _LEGACY_BY_LOWER.get(name.lower())


def resolve_parameter_name(name, stacklevel: int = 3):
    """The name of a parameter: its name in :data:`all_params` (case-insensitive), or the new name of a name of
    accim 0.x, with a DeprecationWarning. Other names (those of the additional parameters, for instance) are
    returned unchanged.

    :param name: The name of the parameter.
    :param stacklevel: The stack level of the warning (that of the caller of the public function by default).
    """
    if not isinstance(name, str):
        return name
    if name.lower() in _NEW_BY_LOWER:
        return _NEW_BY_LOWER[name.lower()]
    new = legacy_parameter_name(name)
    if new is None:
        return name
    version = _LEGACY_VERSIONS.get(name.lower(), '1.0.0')
    warnings.warn(f'The parameter name {name!r} is deprecated since accim {version} and will be removed in a future '
                  f'version; use {new!r} instead.', DeprecationWarning, stacklevel=stacklevel)
    return new


def rename_legacy_parameter_columns(df, context: str = 'The DataFrame', category=DeprecationWarning,
                                    stacklevel: int = 3):
    """The DataFrame with the columns named as the parameters of accim 0.x renamed to their names since accim
    1.0.0 (the same DataFrame if it has none), with a warning.

    :param df: The DataFrame (a plan of simulations or their results).
    :param context: The description of the DataFrame in the warning.
    :param category: The category of the warning (DeprecationWarning for the plans given in the code, UserWarning
        for the results of earlier versions read from files).
    :param stacklevel: The stack level of the warning.
    """
    columns = getattr(df, 'columns', None)
    if columns is None:
        return df
    renamed = {}
    for column in columns:
        new = legacy_parameter_name(column) if isinstance(column, str) else None
        # A column with the new name already present wins: the old one is kept as it is
        if new is not None and new not in columns and new not in renamed.values():
            renamed[column] = new
    attrs = dict(getattr(df, 'attrs', {}) or {})
    names = attrs.get('parameters_names')
    if isinstance(names, (list, tuple)):
        attrs['parameters_names'] = [legacy_parameter_name(n) or n for n in names]
    if not renamed and attrs.get('parameters_names') == names:
        return df
    if renamed:
        if any(column.lower() in _LEGACY_VERSIONS for column in renamed):
            message = (f'{context}: the columns {list(renamed)} have old names of the parameters (of accim 0.x, or of '
                       f'the development of accim 1.2.0), so they are renamed to {list(renamed.values())} (their '
                       f'current names).')
        else:
            message = (f'{context}: the columns {list(renamed)} have the names of the parameters in accim 0.x, so they '
                       f'are renamed to {list(renamed.values())} (their names since accim 1.0.0).')
        warnings.warn(message, category, stacklevel=stacklevel)
    out = df.rename(columns=renamed)
    # The attributes of the DataFrame (the names of the parameters and outputs of the results...)
    out.attrs = attrs
    return out
