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

from accim.sim.ems.inputs import input_programs, read_inputs, set_inputs

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
#: The coefficients of the custom comfort model, by their names in the parametric module, and their EMS variables
CUSTOM_MODEL_VARIABLES = {
    'm': 'm',
    'n': 'n',
    'ACSToffset': 'CustAST_ACSToffset',
    'AHSToffset': 'CustAST_AHSToffset',
    'ACSTaul': 'CustAST_ACSTaul',
    'ACSTall': 'CustAST_ACSTall',
    'AHSTaul': 'CustAST_AHSTaul',
    'AHSTall': 'CustAST_AHSTall',
}


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
    """The coefficients of the custom comfort model (ComfStand 99) of a model, by their names in the parametric
    module (``{'m': 0.31, 'n': 17.8, 'ACSToffset': 3.5...}``): those of its first zone, or those of the programs of
    the models of earlier versions of accim."""
    zone_programs = input_programs(idf)
    if zone_programs:
        values = read_inputs(next(iter(zone_programs.values())))
        return {name: values.get(variable, 0) for name, variable in CUSTOM_MODEL_VARIABLES.items()}
    from accim.utils import get_accim_args
    arguments = get_accim_args(idf).get('CustAST')
    if not isinstance(arguments, dict):
        return {name: 0 for name in CUSTOM_MODEL_VARIABLES}
    return {name: arguments.get(name, 0) for name in CUSTOM_MODEL_VARIABLES}

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
    """List the allowed `(CAT, ComfMod)` options per `ComfStand` value.

    Parameters
    ----------
    None
        This helper returns a static compatibility mapping.

    Returns
    -------
    dict
        Dictionary keyed by `ComfStand` with two lists:
        `[valid_CAT_values, valid_ComfMod_values]`.

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
    }

    return CS_CA_CM_list_dict

def drop_invalid_param_combinations(samples_df):
    """Filter sampled rows that violate ACCIS parameter compatibility rules.

    Parameters
    ----------
    samples_df : pandas.DataFrame
        Dataframe with sampled ACCIS parameters (for example `ComfStand`,
        `CAT`, `ComfMod`, `HVACmode`).

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
    }

    samples_df['valid'] = True
    for i in samples_df.index:
        # Each rule is checked if the plan has its columns: a missing column (or a ComfStand that is not in
        # valid_params, such as 99) only skips that rule
        try:
            if samples_df.loc[i, 'CAT'] not in valid_params[samples_df.loc[i, 'ComfStand']][0]:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass

        try:
            if samples_df.loc[i, 'ComfMod'] not in valid_params[samples_df.loc[i, 'ComfStand']][1]:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass

        try:
            if samples_df.loc[i, 'VentCtrl'] != 0 and samples_df.loc[i, 'HVACmode'] == 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass

        try:
            if samples_df.loc[i, 'VSToffset'] != 0 and samples_df.loc[i, 'HVACmode'] == 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass

        try:
            if samples_df.loc[i, 'MinOToffset'] != 0 and samples_df.loc[i, 'HVACmode'] == 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass

        try:
            if samples_df.loc[i, 'MaxWindSpeed'] != 0 and samples_df.loc[i, 'HVACmode'] == 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass

        try:
            if samples_df.loc[i, 'SetpointAcc'] < 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass
        try:
            if samples_df.loc[i, 'MaxTempDiffVOF'] <= 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass

        try:
            if samples_df.loc[i, 'MinTempDiffVOF'] <= 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass
        try:
            if samples_df.loc[i, 'MinTempDiffVOF'] >= samples_df.loc[i, 'MaxTempDiffVOF']:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass

        try:
            if samples_df.loc[i, 'MultiplierVOF'] < 0 or samples_df.loc[i, 'MultiplierVOF'] > 1:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            pass


    samples_cleaned = samples_df[samples_df['valid'] == True].drop(columns=['valid'])

    return samples_cleaned


def modify_ComfStand(idf: besos.IDF_class, value: int):
    """Modifies the ComfStand argument to match the entered value.
    
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
    _set_inputs(idf, {'ComfStand': value})


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

