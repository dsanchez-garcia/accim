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

"""ACCIS parameter-modifier helpers used by BESOS problem definitions.

This module provides:

- IDF EMS line modifiers (``modify_*``), which set an argument of the ACCIS in all the zones of a model (in the
  programs ``SetInputData_<zone>``, or in the programs of the models of earlier versions of accim), and
- utilities to validate/drop invalid combinations for ACCIS parameters.

Usage
-----
Use `<module>` within ACCIM parametric and optimisation workflows.

Examples
--------
result = <module>()
"""

import besos.IDF_class
import pandas as pd

from accim._deprecation import deprecated_alias
from accim.sim.ems.inputs import input_programs, read_inputs, set_inputs
from accim.sim.ems.programs import add_comfort_standard_code, set_program_lines
from accim.sim.ems.setpoint_limits import check_setpoint_limits, set_setpoint_limits_code
from accim.sim.ems.static_setpoints import (
    DEFAULTS as STATIC_DEFAULTS,
    INPUTS as STATIC_INPUTS,
    check_static_setpoints,
    has_static_setpoints,
)

#: The program, line and variable of each input of the ACCIS in the models of earlier versions of accim, which have
#: one program SetInputData for all the zones and other inputs in SetAST, ApplyCAT, SetAppLimits and
#: SetVOFinputData: {EMS variable of SetInputData_<zone>: (program, line number, variable of the line)}.
_EARLIER_VERSION_LINES = {
    'ComfStand': ('SetInputData', 1, 'ComfStand'),
    'CAT': ('SetInputData', 2, 'CAT'),
    'ComfMod': ('SetInputData', 3, 'ComfMod'),
    'HVACmode': ('SetInputData', 4, 'HVACmode'),
    'VentCtrl': ('SetInputData', 5, 'VentCtrl'),
    'VSToffset': ('SetInputData', 6, 'VSToffset'),
    'MinOToffset': ('SetInputData', 7, 'MinOToffset'),
    'MaxWindSpeed': ('SetInputData', 8, 'MaxWindSpeed'),
    'ACSTtol': ('SetInputData', 9, 'ACSTtol'),
    'AHSTtol': ('SetInputData', 10, 'AHSTtol'),
    'CoolSeasonStart': ('SetInputData', 11, 'CoolSeasonStart'),
    'CoolSeasonEnd': ('SetInputData', 12, 'CoolSeasonEnd'),
    'SetpointAcc': ('SetAST', 1, 'SetpointAcc'),
    'm': ('SetAST', 2, 'm'),
    'n': ('SetAST', 3, 'n'),
    'CATcoolOffset': ('ApplyCAT', 1, 'CATcoolOffset'),
    'CATheatOffset': ('ApplyCAT', 2, 'CATheatOffset'),
    'CustAST_ACSToffset': ('ApplyCAT', 4, 'ACSToffset'),
    'CustAST_AHSToffset': ('ApplyCAT', 5, 'AHSToffset'),
    'CustAST_ACSTaul': ('SetAppLimits', 2, 'ACSTaul'),
    'CustAST_ACSTall': ('SetAppLimits', 3, 'ACSTall'),
    'CustAST_AHSTaul': ('SetAppLimits', 4, 'AHSTaul'),
    'CustAST_AHSTall': ('SetAppLimits', 5, 'AHSTall'),
    'MaxTempDiffVOF': ('SetVOFinputData', 1, 'MaxTempDiffVOF'),
    'MinTempDiffVOF': ('SetVOFinputData', 2, 'MinTempDiffVOF'),
    'MultiplierVOF': ('SetVOFinputData', 3, 'MultiplierVOF'),
}
#: The coefficients of the custom comfort model: their parameter names -> (their EMS variables in the programs
#: SetInputData_<zone>, their names in the arguments that accim.utils.get_accim_args reads from the models of
#: earlier versions of accim)
CUSTOM_MODEL_VARIABLES = {
    'custom_slope': ('m', 'm'),
    'custom_intercept': ('n', 'n'),
    'custom_cooling_offset': ('CustAST_ACSToffset', 'ACSToffset'),
    'custom_heating_offset': ('CustAST_AHSToffset', 'AHSToffset'),
    'custom_cooling_upper_limit': ('CustAST_ACSTaul', 'ACSTaul'),
    'custom_cooling_lower_limit': ('CustAST_ACSTall', 'ACSTall'),
    'custom_heating_upper_limit': ('CustAST_AHSTaul', 'AHSTaul'),
    'custom_heating_lower_limit': ('CustAST_AHSTall', 'AHSTall'),
}
#: The comfort standards whose setpoints do not depend on some parameters (ESP CTE: the category and the comfort mode;
#: INT ISO7730: the comfort mode), so that drop_invalid_param_combinations keeps their rows only with the first value
#: of these parameters in the plan
_INDEPENDENT_OF = {0: ('category', 'comfort_mode'), 22: ('comfort_mode',)}


def _set_inputs(idf, values: dict) -> None:
    """Set some inputs of the ACCIS ({EMS variable: value}) in all the zones of a model: in its programs
    SetInputData_<zone> or, in the models of earlier versions of accim, in the lines where they are.

    :raises ValueError: If the model does not have one of these inputs (those of the venting opening factor without
        natural ventilation, for instance).
    """
    zone_programs = input_programs(idf)
    if zone_programs:
        missing = set(values)
        for program in zone_programs.values():
            missing &= set(set_inputs(program, values))
        if missing:
            raise ValueError(f'The ACCIS of the model has no inputs {sorted(missing)} (the models without natural '
                             f'ventilation have no inputs of the venting opening factor).')
        return
    programs = {p.Name: p for p in idf.idfobjects['EnergyManagementSystem:Program']}
    for variable, value in values.items():
        name, line, written = _EARLIER_VERSION_LINES[variable]
        if name not in programs:
            raise ValueError(f'The model has no EMS program {name}, which sets {variable} in the models of earlier '
                             f'versions of accim.')
        setattr(programs[name], f'Program_Line_{line}', f'set {written} = {value}')


def get_custom_model_arguments(idf) -> dict:
    """The coefficients of the custom comfort model (comfort_standard 99) of a model, by their parameter names
    (``{'custom_slope': 0.31, 'custom_intercept': 17.8, 'custom_cooling_offset': 3.5...}``): those of its first
    zone, or those of the programs of the models of earlier versions of accim."""
    zone_programs = input_programs(idf)
    if zone_programs:
        values = read_inputs(next(iter(zone_programs.values())))
        return {name: values.get(variable, 0) for name, (variable, _) in CUSTOM_MODEL_VARIABLES.items()}
    from accim.utils import get_accim_args
    arguments = get_accim_args(idf).get('CustAST')
    if not isinstance(arguments, dict):
        return {name: 0 for name in CUSTOM_MODEL_VARIABLES}
    return {name: arguments.get(key, 0) for name, (_, key) in CUSTOM_MODEL_VARIABLES.items()}

# def modify_VSToffset(building, value):
#     import accim.sim.accis_single_idf_funcs as accis
#     accis.modifyAccis(
#         idf=building,
#         ComfStand=1,
#         CAT=3,
#         ComfMod=3,
#         # SetpointAcc=1000,
#         HVACmode=2,
#         VentCtrl=0,
#         CoolSeasonStart='01/02',
#         CoolSeasonEnd='01/03',
#         VSToffset=value,
#         # MinOToffset=50,
#         # MaxWindSpeed=50
#     )
#     return


def get_valid_param_combinations():
    """List the allowed `(category, comfort_mode)` options per `comfort_standard` value.

    Parameters
    ----------
    None
        This helper returns a static compatibility mapping.

    Returns
    -------
    dict
        Dictionary keyed by `comfort_standard` with two lists:
        `[valid_category_values, valid_comfort_mode_values]`.

    Usage
    -----
    Use this map to validate sampled parameter grids before simulation.

    Examples
    --------
    valid_map = get_valid_param_combinations()
    """

    # CS_CA_CM_list_dict = {
    #     0:{
    #         'name': '0 = ESP CTE',
    #         'CAT': ['n/a'],
    #         'ComfMod': ['n/a'],
    #     },
    #     0: {
    #         'name': ,
    #         'CAT': ,
    #         'ComfMod': ,
    #     },
    #
    # }
    #     '0 = ESP CTE': [, ],
    #     '1 = INT EN16798-1': [[1, 2, 3], [0, 1, 2, 3]],
    #     '2 = INT ASHRAE55': [[80, 90], [0, 1, 2, 3]],
    #     '3 = JPN Rijal': [[80, 90], [0, 1, 2, 3]],
    #     '4 = CHN GBT50785 Cold': [[1, 2], [3]],
    #     '5 = CHN GBT50785 HotMild': [[1, 2], [3]],
    #     '6 = CHN Yang': [[80, 90], [0, 1, 2, 3]],
    #     '7 = IND IMAC C NV': [[80, 85, 90], [0, 1, 2, 3]],
    #     '8 = IND IMAC C MM': [[80, 85, 90], [0, 1, 2, 3]],
    #     '9 = IND IMAC R 7DRM': [[80, 90], [0, 1, 2, 3]],
    #     '10 = IND IMAC R 30DRM': [[80, 90], [0, 1, 2, 3]],
    #     '11 = IND Dhaka': [[80, 90], [0, 1, 2, 3]],
    #     '12 = ROM Udrea': [[80, 90], [0, 1, 2, 3]],
    #     '13 = AUS Williamson': [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
    #     '14 = AUS DeDear': [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
    #     '15 = BRA Rupp NV': [[80, 90], [0, 1, 2, 3]],
    #     '16 = BRA Rupp AC': [[80, 90], [0, 1, 2, 3]],
    #     '17 = MEX Oropeza Arid': [[80, 90], [0, 1, 2, 3]],
    #     '18 = MEX Oropeza DryTropic': [[80, 90], [0, 1, 2, 3]],
    #     '19 = MEX Oropeza Temperate': [[80, 90], [0, 1, 2, 3]],
    #     '20 = MEX Oropeza HumTropic': [[80, 90], [0, 1, 2, 3]],
    #     '21 = CHL Perez-Fargallo': [[80, 90], [2, 3]],
    #     '22 = INT ISO7730': [[1, 2, 3], [0]],
    # }

    CS_CA_CM_list_dict = {
        0: [['n/a'], ['n/a']],
        1: [[1, 2, 3], [0, 1, 2, 3]],
        2: [[80, 90], [0, 1, 2, 3]],
        3: [[80, 90], [0, 1, 2, 3]],
        4: [[1, 2], [3]],
        5: [[1, 2], [3]],
        6: [[80, 90], [0, 1, 2, 3]],
        7: [[80, 85, 90], [0, 1, 2, 3]],
        8: [[80, 85, 90], [0, 1, 2, 3]],
        9: [[80, 90], [0, 1, 2, 3]],
        10: [[80, 90], [0, 1, 2, 3]],
        11: [[80, 90], [0, 1, 2, 3]],
        12: [[80, 90], [0, 1, 2, 3]],
        13: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        14: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        15: [[80, 90], [0, 1, 2, 3]],
        16: [[80, 90], [0, 1, 2, 3]],
        17: [[80, 90], [0, 1, 2, 3]],
        18: [[80, 90], [0, 1, 2, 3]],
        19: [[80, 90], [0, 1, 2, 3]],
        20: [[80, 90], [0, 1, 2, 3]],
        21: [[80, 90], [2, 3]],
        22: [[1, 2, 3], [0]],
        23: [[80, 90], [0, 1, 2, 3]],
    }
    # The comfort standards defined by their data (accim.sim.standards): their categories and comfort modes
    CS_CA_CM_list_dict.update(_registered_param_combinations())

    return CS_CA_CM_list_dict


def _registered_param_combinations() -> dict:
    """The categories and comfort modes of the registered comfort standards (:mod:`accim.sim.standards`), as in
    :func:`get_valid_param_combinations`."""
    from accim.sim.standards import registered_comfort_standards

    return {number: [list(definition.standard.categories), list(definition.standard.comfort_modes)]
            for number, definition in registered_comfort_standards().items()}

def drop_invalid_param_combinations(samples_df):
    """Filter sampled rows that violate ACCIS parameter compatibility rules.

    The setpoints of ESP CTE (`comfort_standard` 0) depend neither on the category nor on the comfort mode, and those
    of INT ISO7730 (22) not on the comfort mode, so a full set would simulate the same model once for each of their
    values: their rows keep only the first value of these columns in the plan (one row for each combination of the
    other parameters). Before accim 1.0.0, the rows of ESP CTE were dropped when the plan had `category` or
    `comfort_mode`, and those of INT ISO7730 kept only `comfort_mode` 0. Since accim 1.2.0, the rows whose minimum
    heating setpoint is not lower than the maximum cooling setpoint (`heating_setpoint_minimum` and
    `cooling_setpoint_maximum`, which the modifiers reject) are dropped too, and so are those whose static heating
    setpoint of JPN Aqilah 2025 is not lower than its static cooling setpoint (`static_heating_setpoint` and
    `static_cooling_setpoint`), and, since the self-audit of 2026-11-11 (finding A9), those whose window of the limiter
    of the drift of the setpoints (`drift_mode` 'window' or 2) is narrower than twice the tolerance of the setpoints
    (`delta_heat` + `delta_cool` < 2·`setpoint_tolerance`, which crosses the setpoints of the thermostats). The
    columns can have the names of accim 0.x and those of the development of accim 1.2.0 (`heating_setpoint_floor` and
    `cooling_setpoint_ceiling`, finding A23 of the same self-audit), which are kept.

    Parameters
    ----------
    samples_df : pandas.DataFrame
        Dataframe with sampled ACCIS parameters (for example `comfort_standard`,
        `category`, `comfort_mode`, `hvac_mode`; the names of accim 0.x, such as
        `ComfStand`, are also accepted).

    Returns
    -------
    pandas.DataFrame
        Cleaned dataframe containing only valid parameter combinations.

    Usage
    -----
    Run this helper before dispatching batch simulations from sampled inputs.

    Examples
    --------
    samples_clean = drop_invalid_param_combinations(samples_df)
    """
    samples_df = samples_df.dropna()

    valid_params = {
        0: [['n/a'], ['n/a']],
        1: [[1, 2, 3], [0, 1, 2, 3]],
        2: [[80, 90], [0, 1, 2, 3]],
        3: [[80, 90], [0, 1, 2, 3]],
        4: [[1, 2], [3]],
        5: [[1, 2], [3]],
        6: [[80, 90], [0, 1, 2, 3]],
        7: [[80, 85, 90], [0, 1, 2, 3]],
        8: [[80, 85, 90], [0, 1, 2, 3]],
        9: [[80, 90], [0, 1, 2, 3]],
        10: [[80, 90], [0, 1, 2, 3]],
        11: [[80, 90], [0, 1, 2, 3]],
        12: [[80, 90], [0, 1, 2, 3]],
        13: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        14: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        15: [[80, 90], [0, 1, 2, 3]],
        16: [[80, 90], [0, 1, 2, 3]],
        17: [[80, 90], [0, 1, 2, 3]],
        18: [[80, 90], [0, 1, 2, 3]],
        19: [[80, 90], [0, 1, 2, 3]],
        20: [[80, 90], [0, 1, 2, 3]],
        21: [[80, 90], [2, 3]],
        22: [[1, 2, 3], [0]],
        23: [[80, 90], [0, 1, 2, 3]],
    }
    valid_params.update(_registered_param_combinations())

    # The columns of the parameters: their names since accim 1.0.0, or those of accim 0.x
    legacy_names = {
        'comfort_standard': 'ComfStand', 'category': 'CAT', 'comfort_mode': 'ComfMod', 'hvac_mode': 'HVACmode',
        'ventilation_control': 'VentCtrl', 'ventilation_setpoint_offset': 'VSToffset',
        'min_outdoor_temp_offset': 'MinOToffset', 'max_wind_speed': 'MaxWindSpeed', 'setpoint_accuracy': 'SetpointAcc',
        'opening_factor_max_temp_diff': 'MaxTempDiffVOF', 'opening_factor_min_temp_diff': 'MinTempDiffVOF',
        'min_opening_factor': 'MultiplierVOF',
        # The parameters of accim 1.2.0 have no names of accim 0.x, but those of its development renamed before its
        # release (finding A23 of the self-audit of 2026-11-11: before, their rule was skipped)
        'heating_setpoint_minimum': 'heating_setpoint_floor', 'cooling_setpoint_maximum': 'cooling_setpoint_ceiling',
        'static_heating_setpoint': 'static_heating_setpoint', 'static_cooling_setpoint': 'static_cooling_setpoint',
        'drift_mode': 'drift_mode', 'delta_heat': 'delta_heat', 'delta_cool': 'delta_cool',
        'setpoint_tolerance': 'ASTtol',
    }
    columns = {new: (old if old in samples_df.columns and new not in samples_df.columns else new)
               for new, old in legacy_names.items()}
    # The first value of the columns of the category and the comfort mode in the plan, which the rows of the comfort
    # standards whose setpoints do not depend on them keep
    first = {name: pd.unique(samples_df[columns[name]])[0] for name in ('category', 'comfort_mode')
             if columns[name] in samples_df.columns and len(samples_df) > 0}

    def not_valid(name, position):
        def rule(v):
            standard = v('comfort_standard')
            if name in _INDEPENDENT_OF.get(standard, ()):
                return v(name) != first[name]
            return v(name) not in valid_params[standard][position]
        return rule

    def narrow_window(v):
        try:
            window = _drift_mode_code(v('drift_mode')) == 2
        except ValueError:
            return False
        return window and v('delta_heat') + v('delta_cool') < 2 * abs(v('setpoint_tolerance'))

    # The rules that make a combination not valid: each one is checked if the plan has its columns (a missing column,
    # or a comfort_standard that is not in valid_params, such as 99, only skips that rule)
    rules = (
        not_valid('category', 0),
        not_valid('comfort_mode', 1),
        lambda v: v('ventilation_control') != 0 and v('hvac_mode') == 0,
        lambda v: v('ventilation_setpoint_offset') != 0 and v('hvac_mode') == 0,
        lambda v: v('min_outdoor_temp_offset') != 0 and v('hvac_mode') == 0,
        lambda v: v('max_wind_speed') != 0 and v('hvac_mode') == 0,
        lambda v: v('setpoint_accuracy') < 0,
        lambda v: v('opening_factor_max_temp_diff') <= 0,
        lambda v: v('opening_factor_min_temp_diff') <= 0,
        lambda v: v('opening_factor_min_temp_diff') >= v('opening_factor_max_temp_diff'),
        lambda v: v('min_opening_factor') < 0 or v('min_opening_factor') > 1,
        lambda v: v('heating_setpoint_minimum') >= v('cooling_setpoint_maximum'),
        lambda v: v('static_heating_setpoint') >= v('static_cooling_setpoint'),
        # The window of the limiter of the drift narrower than twice the tolerance of the setpoints (finding A9 of the
        # self-audit of 2026-11-11, accim.sim.ems.drift_limiter.check_window_width)
        narrow_window,
    )
    samples_df['valid'] = True
    for i in samples_df.index:
        def value(name, i=i):
            return samples_df.loc[i, columns[name]]

        for rule in rules:
            try:
                if rule(value):
                    samples_df.loc[i, 'valid'] = False
            except KeyError:
                pass

    samples_cleaned = samples_df[samples_df['valid'] == True].drop(columns=['valid'])

    return samples_cleaned


def modify_ComfStand(idf: besos.IDF_class, value: int):
    """Modifies the ComfStand argument to match the entered value.

    The model gets the EMS code of this comfort standard if it does not have it (the output IDFs of ``AddAccis`` only
    have that of the comfort standards of their zones). With a comfort standard of the registry
    (:mod:`accim.sim.standards`), the zones also get its outdoor metric (and its EMS code, if the EMS calculates it),
    and its regimes if it has several (:func:`accim.sim.ems.custom_regimes.set_standard_regimes`, which removes them
    from the zones when they get another comfort standard).
    With IND IMAC R 7DRM (9), the zones get its outdoor metric, the arithmetic mean of the 7 previous days, and the EMS
    code that calculates it (it begins with the running mean of ASHRAE 55 of EnergyPlus, with a warning, unless the
    programs of the outdoor metric of the model begin with the values of a weather file).
    With JPN Aqilah 2025 (23), the zones get its static setpoints (20 and 28 °C, unless a parameter
    ``static_heating_setpoint`` or ``static_cooling_setpoint`` gave them before), and the running mean of EN 16798-1
    with α = 0.8 if the programs of the outdoor metric of the model begin with the values of a weather file (AddAccis
    or ``modify_accis`` with ``epw``), or the RMOT of EnergyPlus otherwise.
    The models of earlier versions of accim do not have the comfort standards defined by their data (JPN Aqilah 2025,
    23, and those of the registry): a ``ValueError`` says so.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_ComfStand` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_ComfStand(idf=..., value=...)
    """
    from accim.sim.standards import definition_of

    if not input_programs(idf) and definition_of(value) is not None:
        raise ValueError(f'The model has the ACCIS of an earlier version of accim, which does not have the EMS code of '
                         f'the comfort standard {value}. Add the ACCIS with this version of accim to the model without '
                         f'it.')
    from accim.sim.ems.custom_regimes import set_standard_regimes

    previous = {zone: read_inputs(program).get('ComfStand') for zone, program in input_programs(idf).items()}
    _set_inputs(idf, {'ComfStand': value})
    if input_programs(idf):
        # The regimes of the comfort standards of the registry with regimes, before their outdoor metric
        regimes_changed = set_standard_regimes(idf, previous)
        add_comfort_standard_code(idf, [value])
        # The outdoor metric of the comfort standards with their own: those of the registry, and IND IMAC R 7DRM (9),
        # the mean of the 7 previous days that the EMS calculates
        from accim.sim.ems.standard_lines import left_metric_inputs, own_metric_inputs

        own_metric = own_metric_inputs(value)
        if own_metric is not None:
            _set_outdoor_metric_inputs(idf, own_metric)
        else:
            # The zones that leave IND IMAC R 7DRM (9) with its outdoor metric do not keep it (the custom model would
            # inherit the mean of the 7 previous days): 'pmot', unless a parameter of the outdoor metric gave them
            # another one before
            left = False
            for zone, program in input_programs(idf).items():
                inputs = left_metric_inputs(previous.get(zone), value, read_inputs(program))
                if inputs is not None:
                    set_inputs(program, inputs)
                    left = True
            if left or regimes_changed:
                _refresh_outdoor_metric_code(idf)
        if has_static_setpoints(value):
            # The static setpoints of JPN Aqilah 2025 that the zones do not have yet (a parameter of the static
            # setpoints applied before keeps its value), and the outdoor metric of the weather file of the model
            for program in input_programs(idf).values():
                current = read_inputs(program)
                missing = [f'set {name} = {default}' for name, default in zip(STATIC_INPUTS, STATIC_DEFAULTS)
                           if name not in current]
                if missing:
                    set_program_lines(program, [str(line).strip() for line in program.fieldvalues[2:]] + missing)
            _refresh_outdoor_metric_code(idf)


def _refresh_outdoor_metric_code(idf) -> None:
    """Write the EMS code of the outdoor metric where the model needs it, keeping its programs if they can be kept
    (:func:`accim.sim.ems.outdoor_metric.outdoor_metric_needed`): JPN Aqilah 2025 uses the outdoor metric of the weather
    file if the programs of the model begin with its values (:func:`accim.sim.accis.modify_accis` or AddAccis with
    ``epw``)."""
    from accim.sim.ems.outdoor_metric import has_outdoor_metric_code, outdoor_metric_needed, set_outdoor_metric_code
    from accim.sim.ems.programs import code_comfort_standards

    enabled = outdoor_metric_needed(idf, code_comfort_standards(idf))
    if enabled or has_outdoor_metric_code(idf):
        set_outdoor_metric_code(idf, enabled)


def _set_static_setpoint(idf, variable: str, value: float) -> None:
    """Set the static heating (StaticAHST) or cooling (StaticACST) setpoint of JPN Aqilah 2025 in all the zones of a
    model of accim 1.0.0 or later, adding the line to the programs SetInputData_<zone> that do not have it
    (:mod:`accim.sim.ems.static_setpoints`). The zones of the other comfort standards ignore it, and keep it if a
    parameter ``comfort_standard`` applied after it gives them JPN Aqilah 2025.

    :raises ValueError: If the model has the ACCIS of an earlier version, the value is not a number, or the static
        heating setpoint of a zone would not be lower than its static cooling setpoint.
    """
    zone_programs = input_programs(idf)
    if not zone_programs:
        raise ValueError('The model has the ACCIS of an earlier version of accim, which does not have JPN Aqilah 2025, '
                         'whose static setpoints these are. Add the ACCIS with this version of accim to the model '
                         'without it.')
    for zone, program in zone_programs.items():
        current = read_inputs(program)
        values = {name: current.get(name, default) for name, default in zip(STATIC_INPUTS, STATIC_DEFAULTS)}
        values[variable] = value
        check_static_setpoints(*(values[name] for name in STATIC_INPUTS), where=zone)
    for program in zone_programs.values():
        if set_inputs(program, {variable: value}):
            set_program_lines(program, [str(line).strip() for line in program.fieldvalues[2:]]
                              + [f'set {variable} = {value}'])


def modify_StaticAHST(idf: besos.IDF_class, value: float):
    """Modifies the static heating setpoint of JPN Aqilah 2025 (``static_heating_setpoint``, the input StaticAHST) of
    all the zones (°C): its setpoint in comfort mode 0, and out of the applicability limits in comfort mode 1 (decision
    D2 of accim 1.2.0, :mod:`accim.sim.ems.static_setpoints`). The other comfort standards ignore it.

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The static heating setpoint (°C).

    Usage
    -----
    Use `modify_StaticAHST` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_StaticAHST(idf=..., value=19)
    """
    _set_static_setpoint(idf, 'StaticAHST', value)


def modify_StaticACST(idf: besos.IDF_class, value: float):
    """Modifies the static cooling setpoint of JPN Aqilah 2025 (``static_cooling_setpoint``, the input StaticACST) of
    all the zones (°C), as :func:`modify_StaticAHST`.

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The static cooling setpoint (°C).

    Usage
    -----
    Use `modify_StaticACST` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_StaticACST(idf=..., value=27)
    """
    _set_static_setpoint(idf, 'StaticACST', value)


def _set_setpoint_limit(idf, variable: str, value: float) -> None:
    """Set the minimum heating setpoint (AHSTmin) or the maximum cooling setpoint (ACSTmax) of all the
    zones of a model of accim 1.0.0 or later, adding the lines that their programs SetInputData_<zone> do not have,
    and the programs ApplySetpointLimits_<zone> (:mod:`accim.sim.ems.setpoint_limits`).

    :raises ValueError: If the model has the ACCIS of an earlier version, the value is not a number, or the minimum of a
        zone would not be lower than its maximum.
    """
    zone_programs = input_programs(idf)
    if not zone_programs:
        raise ValueError('The model has the ACCIS of an earlier version of accim, whose setpoints have neither minimum '
                         'nor maximum. Add the ACCIS with this version of accim to the model without it.')
    for zone, program in zone_programs.items():
        limits = {name: read_inputs(program).get(name) for name in ('AHSTmin', 'ACSTmax')}
        limits[variable] = value
        check_setpoint_limits(limits['AHSTmin'], limits['ACSTmax'], where=zone)
    for program in zone_programs.values():
        if set_inputs(program, {variable: value}):
            set_program_lines(program, [str(line).strip() for line in program.fieldvalues[2:]]
                              + [f'set {variable} = {value}'])
    set_setpoint_limits_code(idf)


def modify_AHSTmin(idf: besos.IDF_class, value: float):
    """Modifies the minimum heating setpoint (``heating_setpoint_minimum``, the input AHSTmin) of all the zones:
    their heating setpoint is not lower than the value (°C), whatever the comfort standard and the comfort mode are
    (EN 16798-1:2019 applies in winter the minimums of its Table B.2, ``accim.constants.EN16798_TABLE_B2``).

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The minimum (°C).

    Usage
    -----
    Use `modify_AHSTmin` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_AHSTmin(idf=..., value=20)
    """
    _set_setpoint_limit(idf, 'AHSTmin', value)


def modify_ACSTmax(idf: besos.IDF_class, value: float):
    """Modifies the maximum cooling setpoint (``cooling_setpoint_maximum``, the input ACSTmax) of all the zones:
    their cooling setpoint is not higher than the value (°C), whatever the comfort standard and the comfort mode are
    (the maximums of Table B.2 of EN 16798-1:2019).

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The maximum (°C).

    Usage
    -----
    Use `modify_ACSTmax` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_ACSTmax(idf=..., value=26)
    """
    _set_setpoint_limit(idf, 'ACSTmax', value)


# The names of the development of accim 1.2.0, renamed before its release (decision 8 of block F)
modify_AHSTfloor = deprecated_alias(modify_AHSTmin, 'param_accis.modify_AHSTfloor', 'param_accis.modify_AHSTmin',
                                    version='1.2.0')
modify_ACSTceil = deprecated_alias(modify_ACSTmax, 'param_accis.modify_ACSTceil', 'param_accis.modify_ACSTmax',
                                   version='1.2.0')


def _set_outdoor_metric_input(idf, variable: str, value) -> None:
    """Set an input of the outdoor metric of the custom model (``CustAST_metric``, ``CustAST_alpha`` or
    ``CustAST_days``) in all the zones of a model of accim 1.0.0 or later, adding the line to the programs
    SetInputData_<zone> that do not have it, and write the EMS code of the outdoor metric where the model needs it, as
    :func:`accim.sim.accis.modify_accis` does (:func:`accim.sim.ems.outdoor_metric.set_outdoor_metric_code`): the
    programs of the model are kept if they can be (with the values of the weather file with which they begin, if
    ``modify_accis`` gave them ``epw``); otherwise they begin with the running mean of ASHRAE 55 of EnergyPlus, with a
    warning, and 'monthly_mean' raises a ValueError.

    The parametric module applies the parameters of a sample one after the other: while the metric of the zones is
    'pmot' and the model has no EMS code of the outdoor metric, the inputs stay in SetInputData_<zone> (as local
    variables of the program, which Erl does not need to declare), so that a ``custom_alpha`` or ``custom_days`` given
    before ``custom_outdoor_metric`` is kept when the metric gets the code.

    :raises ValueError: If the model has the ACCIS of an earlier version, or a value is not valid.
    """
    _set_outdoor_metric_inputs(idf, {variable: value})


def _set_outdoor_metric_inputs(idf, inputs: dict) -> None:
    """Set some inputs of the outdoor metric (``{EMS variable: value}``) in all the zones of a model, and write the EMS
    code of the outdoor metric where the model needs it (see :func:`_set_outdoor_metric_input`)."""
    from accim.sim.ems.outdoor_metric import check_outdoor_metric_arguments

    zone_programs = input_programs(idf)
    if not zone_programs:
        raise ValueError('The model has the ACCIS of an earlier version of accim, whose custom model only has the '
                         "outdoor metric 'pmot'. Add the ACCIS with this version of accim to the model without it.")
    defaults = {'CustAST_metric': 'pmot', 'CustAST_alpha': 0.8, 'CustAST_days': 30}
    for zone, program in zone_programs.items():
        values = {name: read_inputs(program).get(name, default) for name, default in defaults.items()}
        values.update(inputs)
        check_outdoor_metric_arguments(values['CustAST_metric'], values['CustAST_alpha'], values['CustAST_days'],
                                       where=zone)
    for program in zone_programs.values():
        missing = set_inputs(program, inputs)
        if missing:
            set_program_lines(program, [str(line).strip() for line in program.fieldvalues[2:]]
                              + [f'set {variable} = {inputs[variable]}' for variable in inputs if variable in missing])
    _refresh_outdoor_metric_code(idf)


def modify_CustAST_metric(idf: besos.IDF_class, value):
    """Modifies the outdoor metric of the custom model (``custom_outdoor_metric``, the input CustAST_metric) of all the
    zones: its name or its code (:data:`accim.sim.ems.outdoor_metric.OUTDOOR_METRICS`: 'pmot' 0, 'rmot' 1,
    'rmot_alpha' 2, 'rmot_7day' 3, 'daily_mean' 4, 'ndrm' 5, 'monthly_mean' 6, 'te_ref_nl' 7), such as the options of
    the parametric module (numbers). The model gets the EMS code of the outdoor metric if a zone needs it (proposal
    B1); the metrics that the EMS calculates begin with the running mean of ASHRAE 55 of EnergyPlus (with a warning),
    unless the model has the programs of the outdoor metric with the values of a weather file
    (:func:`accim.sim.accis.modify_accis` with ``epw``), and 'monthly_mean' needs them. T0 of 'te_ref_nl' is that of the
    day itself only in the models whose programs read the Schedule:File object of the weather file (those made with
    'te_ref_nl' and ``epw``); otherwise it is that of the previous day, and programs that begin with the values of a
    weather file without that object are written again, beginning with PMOT (task H2 of the review of accim 1.2.0).

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The name or the code of the metric.

    Usage
    -----
    Use `modify_CustAST_metric` within ACCIM parametric and optimisation workflows (parameters type 'accim custom
    model').

    Examples
    --------
    result = modify_CustAST_metric(idf=..., value=2)
    """
    from accim.sim.ems.outdoor_metric import metric_code

    _set_outdoor_metric_input(idf, 'CustAST_metric', metric_code(value))


def modify_CustAST_alpha(idf: besos.IDF_class, value: float):
    """Modifies the alpha of the running mean of the outdoor metric 'rmot_alpha' of the custom model (``custom_alpha``,
    the input CustAST_alpha) of all the zones: between 0 and 1 (not included); it warns outside 0.6 to 0.9 with
    'rmot_alpha' (ASHRAE 55-2020, 5.4.2.1; EN 16798-1 recommends 0.8).

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The alpha.

    Usage
    -----
    Use `modify_CustAST_alpha` within ACCIM parametric and optimisation workflows (parameters type 'accim custom
    model').

    Examples
    --------
    result = modify_CustAST_alpha(idf=..., value=0.7)
    """
    _set_outdoor_metric_input(idf, 'CustAST_alpha', value)


def modify_CustAST_days(idf: besos.IDF_class, value: float):
    """Modifies the number of previous days of the outdoor metric 'ndrm' of the custom model (``custom_days``, the
    input CustAST_days) of all the zones, rounded to the nearest integer (the samples of a range of the parametric
    module are not integers); it warns outside 7 to 30 days with 'ndrm' (ASHRAE 55-2020, 5.4.2.1).

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The number of days.

    Usage
    -----
    Use `modify_CustAST_days` within ACCIM parametric and optimisation workflows (parameters type 'accim custom
    model').

    Examples
    --------
    result = modify_CustAST_days(idf=..., value=7)
    """
    import numbers

    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f'custom_days must be a number of days, not {value!r}.')
    _set_outdoor_metric_input(idf, 'CustAST_days', int(round(value)))


def modify_custom_regime(idf: besos.IDF_class, value: float, regime: int, field: str):
    """Modifies a coefficient of a regime of the custom model (``custom_regimes``, proposal B2 of accim 1.2.0) in all
    the zones that have the regimes (their programs SelectCustomRegime_<zone>, see
    :mod:`accim.sim.ems.custom_regimes`), as the parameters ``custom_regime_<regime>_<field>`` and the classes of
    ``custom_regime_parameters`` (:mod:`accim.parametric_and_optimisation.parameters`) do: the model must have the
    regimes already (``custom_regimes`` of :func:`accim.sim.accis.modify_accis`), and each regime keeps its condition.

    :param idf: The eppy or besos IDF class instance, with the regimes of the custom model.
    :param value: The value of the coefficient.
    :param regime: The number of the regime, from 1 (in the order of priority of the regimes).
    :param field: The coefficient: a field of :class:`accim.sim.arguments.CustomRegime` ('slope', 'intercept',
        'cooling_offset', 'heating_offset', 'cooling_lower_limit', 'cooling_upper_limit', 'heating_lower_limit' or
        'heating_upper_limit').
    :raises ValueError: If the field is not a coefficient, the model has no regimes, or a zone has fewer regimes.

    Usage
    -----
    Use `modify_custom_regime` within ACCIM parametric and optimisation workflows (parameters type 'accim custom
    model'), through the parameters ``custom_regime_<regime>_<field>``.

    Examples
    --------
    result = modify_custom_regime(idf=..., value=0.33, regime=1, field='slope')
    """
    import dataclasses

    from accim.sim.ems.custom_regimes import (REGIME_INPUTS, custom_regimes_of, set_zone_custom_regimes,
                                              standard_regimes)

    if field not in REGIME_INPUTS:
        raise ValueError(f'{field!r} is not a coefficient of a regime of the custom model: {list(REGIME_INPUTS)}.')
    # The regimes of the comfort standards of the registry with regimes are those of their definitions
    standards = {zone: read_inputs(program).get('ComfStand') for zone, program in input_programs(idf).items()}
    regimes_by_zone = {zone: regimes for zone, regimes in custom_regimes_of(idf).items()
                       if standard_regimes(standards.get(zone)) is None}
    if not regimes_by_zone:
        raise ValueError('The model has no regimes of the custom model: give them first with custom_regimes '
                         '(accim.sim.accis.modify_accis).')
    for zone, regimes in regimes_by_zone.items():
        if isinstance(regime, bool) or not isinstance(regime, int) or not 1 <= regime <= len(regimes):
            raise ValueError(f'The zone {zone!r} has {len(regimes)} regimes of the custom model, so it has no regime '
                             f'{regime!r}.')
    for zone, regimes in regimes_by_zone.items():
        changed = list(regimes)
        changed[regime - 1] = dataclasses.replace(changed[regime - 1], **{field: value})
        set_zone_custom_regimes(idf, zone, changed)


def modify_CustAST_ACSTaul(idf: besos.IDF_class, value: float):
    """Modifies the CustAST_ACSTaul argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_ACSTaul` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_ACSTaul(idf=..., value=...)
    """
    _set_inputs(idf, {'CustAST_ACSTaul': value})


def modify_CustAST_ACSTall(idf: besos.IDF_class, value: float):
    """Modifies the CustAST_ACSTall argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_ACSTall` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_ACSTall(idf=..., value=...)
    """
    _set_inputs(idf, {'CustAST_ACSTall': value})


def modify_CustAST_AHSTaul(idf: besos.IDF_class, value: float):
    """Modifies the CustAST_AHSTaul argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_AHSTaul` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_AHSTaul(idf=..., value=...)
    """
    _set_inputs(idf, {'CustAST_AHSTaul': value})


def modify_CustAST_AHSTall(idf: besos.IDF_class, value: float):
    """Modifies the CustAST_AHSTall argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_AHSTall` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_AHSTall(idf=..., value=...)
    """
    _set_inputs(idf, {'CustAST_AHSTall': value})


def modify_CustAST_ASTall(idf: besos.IDF_class, value: float):
    """Modifies the CustAST_ACSTall and CustAST_AHSTall arguments to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_ASTall` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_ASTall(idf=..., value=...)
    """
    _set_inputs(idf, {'CustAST_ACSTall': value, 'CustAST_AHSTall': value})


def modify_CustAST_ASTaul(idf: besos.IDF_class, value: float):
    """Modifies the CustAST_ACSTaul and CustAST_AHSTaul arguments to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_ASTaul` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_ASTaul(idf=..., value=...)
    """
    _set_inputs(idf, {'CustAST_ACSTaul': value, 'CustAST_AHSTaul': value})


def modify_CustAST_m(idf: besos.IDF_class, value: float):
    """Modifies the CustAST_m argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_m` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_m(idf=..., value=...)
    """
    _set_inputs(idf, {'m': value})


def modify_CustAST_n(idf: besos.IDF_class, value: float):
    """Modifies the CustAST_n argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_n` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_n(idf=..., value=...)
    """
    _set_inputs(idf, {'n': value})


def modify_CustAST_ACSToffset(idf: besos.IDF_class, value: float):
    """Modifies the ACSToffset argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_ACSToffset` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_ACSToffset(idf=..., value=...)
    """
    _set_inputs(idf, {'CustAST_ACSToffset': value})


def modify_CustAST_AHSToffset(idf: besos.IDF_class, value: float):
    """Modifies the AHSToffset argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_AHSToffset` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_AHSToffset(idf=..., value=...)
    """
    _set_inputs(idf, {'CustAST_AHSToffset': value})


def modify_CustAST_ASToffset(idf: besos.IDF_class, value: float):
    """Modifies the ACSToffset and AHSToffset arguments symmetrically to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CustAST_ASToffset` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CustAST_ASToffset(idf=..., value=...)
    """
    _set_inputs(idf, {'CustAST_ACSToffset': value, 'CustAST_AHSToffset': -value})


def modify_CAT(idf: besos.IDF_class, value: int):
    """Modifies the CAT argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CAT` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CAT(idf=..., value=...)
    """
    _set_inputs(idf, {'CAT': value})


def modify_CATcoolOffset(idf: besos.IDF_class, value: float):
    """Modifies the CATcoolOffset argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CATcoolOffset` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CATcoolOffset(idf=..., value=...)
    """
    _set_inputs(idf, {'CATcoolOffset': value})


def modify_CATheatOffset(idf: besos.IDF_class, value: float):
    """Modifies the CATheatOffset argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_CATheatOffset` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CATheatOffset(idf=..., value=...)
    """
    _set_inputs(idf, {'CATheatOffset': value})


def modify_ComfMod(idf: besos.IDF_class, value: float):
    """Modifies the ComfMod argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_ComfMod` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_ComfMod(idf=..., value=...)
    """
    _set_inputs(idf, {'ComfMod': value})


def modify_HVACmode(idf: besos.IDF_class, value: int):
    """Modifies the HVACmode argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_HVACmode` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_HVACmode(idf=..., value=...)
    """
    _set_inputs(idf, {'HVACmode': value})


def modify_VentCtrl(idf: besos.IDF_class, value: int):
    """Modifies the VentCtrl argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_VentCtrl` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_VentCtrl(idf=..., value=...)
    """
    _set_inputs(idf, {'VentCtrl': value})


def modify_VSToffset(idf: besos.IDF_class, value: float):
    """Modifies the VSToffset argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_VSToffset` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_VSToffset(idf=..., value=...)
    """
    _set_inputs(idf, {'VSToffset': value})


def modify_MinOToffset(idf: besos.IDF_class, value: float):
    """Modifies the MinOToffset argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_MinOToffset` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_MinOToffset(idf=..., value=...)
    """
    _set_inputs(idf, {'MinOToffset': value})


def modify_MaxWindSpeed(idf: besos.IDF_class, value: float):
    """Modifies the MaxWindSpeed argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_MaxWindSpeed` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_MaxWindSpeed(idf=..., value=...)
    """
    _set_inputs(idf, {'MaxWindSpeed': value})


def modify_ASTtol(idf: besos.IDF_class, value: float):
    """Modifies the ACSTtol and AHSTtol arguments symmetrically to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_ASTtol` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_ASTtol(idf=..., value=...)
    """
    _set_inputs(idf, {'ACSTtol': -value, 'AHSTtol': value})


def modify_CoolSeasonStart(idf: besos.IDF_class, value: any):
    """Modifies the CoolSeasonStart argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument. Can be an integer representing the day of the year, or the
        date in format dd/mm.
    :return:
    
    Usage
    -----
    Use `modify_CoolSeasonStart` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CoolSeasonStart(idf=..., value=...)
    """
    if type(value) is str:
        from accim.utils import transform_ddmm_to_int
        value = transform_ddmm_to_int(value)
    _set_inputs(idf, {'CoolSeasonStart': value})


def modify_CoolSeasonEnd(idf: besos.IDF_class, value: any):
    """Modifies the CoolSeasonEnd argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument. Can be an integer representing the day of the year, or the
        date in format dd/mm.
    :return:
    
    Usage
    -----
    Use `modify_CoolSeasonEnd` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_CoolSeasonEnd(idf=..., value=...)
    """
    if type(value) is str:
        from accim.utils import transform_ddmm_to_int
        value = transform_ddmm_to_int(value)
    _set_inputs(idf, {'CoolSeasonEnd': value})


def modify_SetpointAcc(idf: besos.IDF_class, value: float):
    """Modifies the SetpointAcc argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_SetpointAcc` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_SetpointAcc(idf=..., value=...)
    """
    _set_inputs(idf, {'SetpointAcc': value})


def modify_MaxTempDiffVOF(idf: besos.IDF_class, value: float):
    """Modifies the MaxTempDiffVOF argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_MaxTempDiffVOF` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_MaxTempDiffVOF(idf=..., value=...)
    """
    _set_inputs(idf, {'MaxTempDiffVOF': value})


def modify_MinTempDiffVOF(idf: besos.IDF_class, value: float):
    """Modifies the MinTempDiffVOF argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_MinTempDiffVOF` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_MinTempDiffVOF(idf=..., value=...)
    """
    _set_inputs(idf, {'MinTempDiffVOF': value})


def modify_MultiplierVOF(idf: besos.IDF_class, value: int):
    """Modifies the MultiplierVOF argument to match the entered value.
    
    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    
    Usage
    -----
    Use `modify_MultiplierVOF` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = modify_MultiplierVOF(idf=..., value=...)
    """
    _set_inputs(idf, {'MultiplierVOF': value})


# The limiter of the drift of the setpoints (task F2 of block F, accim.sim.ems.drift_limiter) ----------------------

def _drift_mode_code(value) -> int:
    """The code of a mode of the limiter of the drift (the input DriftMode): 1 or 'rate', 2 or 'window', and 0 for
    none (0, None, NaN or 'none')."""
    import math

    from accim.sim.ems.drift_limiter import DRIFT_MODES

    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ('', 'none'):
            return 0
        if text in DRIFT_MODES:
            return DRIFT_MODES[text]
    elif not isinstance(value, bool) and value in (0, 1, 2):
        return int(value)
    raise ValueError(f"drift_mode must be 0 or 'none', 1 or 'rate', or 2 or 'window', not {value!r}.")


def _set_drift_input(idf, variable: str, value) -> None:
    """Set an input of the limiter of the drift of the setpoints (:mod:`accim.sim.ems.drift_limiter`) in all the zones
    of a model of accim 1.0.0 or later, adding the line to the programs SetInputData_<zone> that do not have it, and
    write the EMS code of the limiter of the zones with DriftMode (the other inputs wait in the zones without it for a
    parameter ``drift_mode``, which can come later in the plan).

    :raises ValueError: If the model has the ACCIS of an earlier version.
    """
    from accim.sim.ems.drift_limiter import set_drift_limiter_code
    from accim.sim.accis import _ems_output_frequencies

    zone_programs = input_programs(idf)
    if not zone_programs:
        raise ValueError('The model has the ACCIS of an earlier version of accim, which has no limiter of the drift of '
                         'the setpoints. Add the ACCIS with this version of accim to the model without it.')
    for program in zone_programs.values():
        if set_inputs(program, {variable: value}):
            set_program_lines(program, [str(line).strip() for line in program.fieldvalues[2:]]
                              + [f'set {variable} = {value}'])
    set_drift_limiter_code(idf, _ems_output_frequencies(idf))


def modify_DriftMode(idf: besos.IDF_class, value):
    """Modifies the limiter of the drift of the setpoints (``drift_mode``, the input DriftMode) of all the zones (task
    F2 of block F, :mod:`accim.sim.ems.drift_limiter`): its code or its name, 1 or 'rate', 2 or 'window', and 0 or
    'none' for none (the zones keep the program of the limiter, inactive), such as the options of the parametric module
    (numbers). The zones that get it have the other arguments of the limiter given before by other parameters, or their
    defaults (0.5 K/day, 0.8, 1.0 K and 1.0 K).

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The code or the name of the mode.

    Usage
    -----
    Use `modify_DriftMode` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_DriftMode(idf=..., value=1)
    """
    from accim.sim.ems.drift_limiter import ARGUMENTS, DEFAULTS, INPUTS

    code = _drift_mode_code(value)
    zone_programs = input_programs(idf)
    if code == 0 and not any('DriftMode' in read_inputs(program) for program in zone_programs.values()):
        return
    _set_drift_input(idf, 'DriftMode', code)
    # The other inputs of the zones that get the limiter now, with their defaults
    for program in zone_programs.values():
        current = read_inputs(program)
        missing = [f'set {variable} = {DEFAULTS[argument]}' for argument, variable in zip(ARGUMENTS[1:5], INPUTS[1:5])
                   if variable not in current]
        if missing:
            set_program_lines(program, [str(line).strip() for line in program.fieldvalues[2:]] + missing)


def modify_MaxDriftRate(idf: besos.IDF_class, value: float):
    """Modifies the largest change of the setpoints from one day to the next of the limiter of the drift in the mode
    'rate' (``max_drift_rate``, the input MaxDriftRate, K/day, greater than 0) of all the zones.

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The rate (K/day).

    Usage
    -----
    Use `modify_MaxDriftRate` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_MaxDriftRate(idf=..., value=0.25)
    """
    from accim.sim.ems.drift_limiter import check_drift_arguments

    check_drift_arguments(max_drift_rate=value)
    _set_drift_input(idf, 'MaxDriftRate', value)


def modify_AlphaIndoor(idf: besos.IDF_class, value: float):
    """Modifies the weight of the running mean of the day before of the limiter of the drift in the mode 'window'
    (``alpha_indoor``, the input AlphaIndoor, from 0 to 1, 1 excluded) of all the zones.

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The alpha.

    Usage
    -----
    Use `modify_AlphaIndoor` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_AlphaIndoor(idf=..., value=0.9)
    """
    from accim.sim.ems.drift_limiter import check_drift_arguments

    check_drift_arguments(alpha_indoor=value)
    _set_drift_input(idf, 'AlphaIndoor', value)


def modify_DeltaCool(idf: besos.IDF_class, value: float):
    """Modifies the largest distance of the setpoints above the running mean of the limiter of the drift in the mode
    'window' (``delta_cool``, the input DeltaCool, K, 0 or more) of all the zones.

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The distance (K).

    Usage
    -----
    Use `modify_DeltaCool` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_DeltaCool(idf=..., value=1.5)
    """
    from accim.sim.ems.drift_limiter import check_drift_arguments

    check_drift_arguments(delta_cool=value)
    _set_drift_input(idf, 'DeltaCool', value)


def modify_DeltaHeat(idf: besos.IDF_class, value: float):
    """Modifies the largest distance of the setpoints below the running mean of the limiter of the drift in the mode
    'window' (``delta_heat``, the input DeltaHeat, K, 0 or more) of all the zones.

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The distance (K).

    Usage
    -----
    Use `modify_DeltaHeat` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_DeltaHeat(idf=..., value=1.5)
    """
    from accim.sim.ems.drift_limiter import check_drift_arguments

    check_drift_arguments(delta_heat=value)
    _set_drift_input(idf, 'DeltaHeat', value)


def modify_InitTrmIn(idf: besos.IDF_class, value: float):
    """Modifies the first running mean of the limiter of the drift in the mode 'window' (``initial_T_rm_in``, the input
    InitTrmIn, °C) of all the zones, with which the limiter is active from the first day.

    :param idf: The eppy or besos IDF class instance, with the ACCIS of accim 1.0.0 or later.
    :param value: The running mean (°C).

    Usage
    -----
    Use `modify_InitTrmIn` within ACCIM parametric and optimisation workflows.

    Examples
    --------
    result = modify_InitTrmIn(idf=..., value=24)
    """
    from accim.sim.ems.drift_limiter import check_drift_arguments

    check_drift_arguments(initial_T_rm_in=value)
    _set_drift_input(idf, 'InitTrmIn', value)
