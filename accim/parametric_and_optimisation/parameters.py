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

"""Utilities for defining ACCIM/BESOS parametric inputs.

This module exposes factory helpers and OO wrappers to build parameter
specifications and to apply parameter values directly to IDF objects.

Usage
-----
Typical workflows are:
1. Build BESOS parameters with :func:`accis_parameter`.
2. Inspect available parameter names with ``get_available_*`` helpers.
3. Apply one parameter directly to an IDF with wrapper classes.

Examples
--------
p = accis_parameter("ComfStand", [1, 2, 3])
p.name
'ComfStand'
ComfStand().modify(idf, 1)
"""

from accim.parametric_and_optimisation.funcs_for_besos import param_accis, param_apmv
import accim.parametric_and_optimisation.params_dicts as params_dicts
from accim.parametric_and_optimisation.utils import descriptor_has_options


def accis_parameter(parameter_name, values):
    """Build one BESOS parameter descriptor from an ACCIM parameter name.

    Parameters
    ----------
    parameter_name : str
        Name of the parameter to map. Matching is case-insensitive and must
        exist in ``params_dicts.all_params``.
    values : sequence
        Parameter domain definition. If it has categorical options,
        ``CategoryParameter`` is used; otherwise, ``RangeParameter`` is used
        with ``values[0]`` and ``values[1]``.

    Returns
    -------
    besos.parameters.Parameter
        Configured BESOS parameter object ready to be passed to an
        ``EPProblem`` input list.

    Usage
    -----
    Use this helper when defining parametric or optimisation problems through
    BESOS.

    Examples
    --------
    p = accis_parameter("ComfStand", [1, 2, 3])
    p.name
    'ComfStand'
    q = accis_parameter("CustAST_m", (0.0, 0.7))
    q.name
    'CustAST_m'
    """
    desc_has_options = descriptor_has_options(values)

    # all_params = {
    #     # accim predefined models parameters
    #     'ComfStand': param_accis.modify_ComfStand,
    #     'CAT': param_accis.modify_CAT,
    #     'CATcoolOffset': param_accis.modify_CATcoolOffset,
    #     'CATheatOffset': param_accis.modify_CATheatOffset,
    #     'ComfMod': param_accis.modify_ComfMod,
    #     'SetpointAcc': param_accis.modify_SetpointAcc,
    #     'CoolSeasonStart': param_accis.modify_CoolSeasonStart,
    #     'CoolSeasonEnd': param_accis.modify_CoolSeasonEnd,
    #     'HVACmode': param_accis.modify_HVACmode,
    #     'VentCtrl': param_accis.modify_VentCtrl,
    #     'MaxTempDiffVOF': param_accis.modify_MaxTempDiffVOF,
    #     'MinTempDiffVOF': param_accis.modify_MinTempDiffVOF,
    #     'MultiplierVOF': param_accis.modify_MultiplierVOF,
    #     'VSToffset': param_accis.modify_VSToffset,
    #     'MinOToffset': param_accis.modify_MinOToffset,
    #     'MaxWindSpeed': param_accis.modify_MaxWindSpeed,
    #     'ASTtol': param_accis.modify_ASTtol,
    #     # accim custom models parameters
    #     'CustAST_ACSTaul': param_accis.modify_CustAST_ACSTaul,
    #     'CustAST_ACSTall': param_accis.modify_CustAST_ACSTall,
    #     'CustAST_AHSTaul': param_accis.modify_CustAST_AHSTaul,
    #     'CustAST_AHSTall': param_accis.modify_CustAST_AHSTall,
    #     'CustAST_ASTaul': param_accis.modify_CustAST_ASTaul,
    #     'CustAST_ASTall': param_accis.modify_CustAST_ASTall,
    #     'CustAST_m': param_accis.modify_CustAST_m,
    #     'CustAST_n': param_accis.modify_CustAST_n,
    #     'CustAST_ACSToffset': param_accis.modify_CustAST_ACSToffset,
    #     'CustAST_AHSToffset': param_accis.modify_CustAST_AHSToffset,
    #     'CustAST_ASToffset': param_accis.modify_CustAST_ASToffset,
    #     #apmv setpoints parameters
    #     'Adaptive coefficient': param_apmv.change_adaptive_coeff_all_zones,
    #     'Adaptive cooling coefficient': param_apmv.change_adaptive_coeff_cooling_all_zones,
    #     'Adaptive heating coefficient': param_apmv.change_adaptive_coeff_heating_all_zones,
    #     'PMV setpoint': param_apmv.change_pmv_setpoint_all_zones,
    #     'PMV cooling setpoint': param_apmv.change_pmv_cooling_setpoint_all_zones,
    #     'PMV heating setpoint': param_apmv.change_pmv_heating_setpoint_all_zones,
    # }


    if parameter_name.lower() not in [k.lower() for k in params_dicts.all_params.keys()]:
        raise KeyError(f'Parameter do not exist.'
                       f'You need to chose one of the following list: {params_dicts.all_params.keys()}')

    name = [i for i in params_dicts.all_params.keys() if i.lower() == parameter_name.lower()][0]

    from besos.parameters import Parameter, GenericSelector, CategoryParameter, RangeParameter
    import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf
    import numpy as np

    if desc_has_options:
        parameter = Parameter(
            name=name,
            # selector=GenericSelector(set=change_adaptive_coeff),
            selector=GenericSelector(set=params_dicts.all_params[name]),
            # value_descriptors=RangeParameter(name='CustAST_m', min_val=0, max_val=0.7),
            value_descriptors=CategoryParameter(
                name=name,
                options=values
            ),
        ),
    else:
        parameter = Parameter(
            name=name,
            # selector=GenericSelector(set=change_adaptive_coeff),
            selector=GenericSelector(set=params_dicts.all_params[name]),
            # value_descriptors=RangeParameter(name='CustAST_m', min_val=0, max_val=0.7),
            value_descriptors=RangeParameter(
                name=name,
                min_val=values[0],
                max_val=values[1],
            ),
        ),

    return parameter[0]

def get_available_params_accim_predef_models():
    """List available ACCIM predefined-model parameter names.

    Returns
    -------
    list[str]
        Parameter names available for predefined ACCIM models.

    Usage
    -----
    Call this helper to validate user input before creating descriptors with
    :func:`accis_parameter`.

    Examples
    --------
    >>> names = get_available_params_accim_predef_models()
    >>> 'ComfStand' in names
    True
    """
    param_dict = [k for k in params_dicts.accim_predef_model_params.keys()]
    return param_dict


def get_available_params_accim_custom_models():
    """List available ACCIM custom-model parameter names.

    Returns
    -------
    list[str]
        Parameter names available for custom ACCIM models.

    Usage
    -----
    Use this list to restrict UI/API inputs to valid custom-model parameters.

    Examples
    --------
    >>> names = get_available_params_accim_custom_models()
    >>> 'CustAST_m' in names
    True
    """
    param_dict = [k for k in params_dicts.accim_custom_model_params.keys()]
    return param_dict


def get_available_params_apmv_setpoints():
    """List available APMV setpoint parameter names.

    Returns
    -------
    list[str]
        Parameter names that control APMV setpoints.

    Usage
    -----
    Use this helper before building APMV-oriented parameter sweeps.

    Examples
    --------
    >>> names = get_available_params_apmv_setpoints()
    >>> 'PMV setpoint' in names
    True
    """
    param_dict = [k for k in params_dicts.apmv_setpoints_params.keys()]
    return param_dict


class Parameter:
    """Legacy OO wrapper that resolves one ACCIS parameter by name.

    The class stores the canonical parameter name and exposes ``modify`` to
    apply a value to an IDF.

    Usage
    -----
    Instantiate with a supported parameter name and call :meth:`modify`.

    Examples
    --------
    p = Parameter('ComfStand')
    p.modify(idf, 1)
    """

    def __init__(self, parameter):
        """Initialize the parameter wrapper.

        Parameters
        ----------
        parameter : str
            Requested parameter name (case-insensitive).

        Returns
        -------
        None
            Stores the canonical name in ``self.name``.

        Usage
        -----
        Construct once and reuse across multiple IDFs if needed.

        Examples
        --------
        p = Parameter('comfstand')
        p.name
        'ComfStand'
        """
        parameters_accis = {
            'ComfStand': param_accis.modify_ComfStand,
            'CAT': param_accis.modify_CAT,
            'CATcoolOffset': param_accis.modify_CATcoolOffset,
            'CATheatOffset': param_accis.modify_CATheatOffset,
            'ComfMod': param_accis.modify_ComfMod,
            'SetpointAcc': param_accis.modify_SetpointAcc,
            'CustAST_ACSTaul': param_accis.modify_CustAST_ACSTaul,
            'CustAST_ACSTall': param_accis.modify_CustAST_ACSTall,
            'CustAST_AHSTaul': param_accis.modify_CustAST_AHSTaul,
            'CustAST_AHSTall': param_accis.modify_CustAST_AHSTall,
            'CustAST_m': param_accis.modify_CustAST_m,
            'CustAST_n': param_accis.modify_CustAST_n,
            'CustAST_ACSToffset': param_accis.modify_CustAST_ACSToffset,
            'CustAST_AHSToffset': param_accis.modify_CustAST_AHSToffset,
            'CoolSeasonStart': param_accis.modify_CoolSeasonStart,
            'CoolSeasonEnd': param_accis.modify_CoolSeasonEnd,
            'HVACmode': param_accis.modify_HVACmode,
            'VentCtrl': param_accis.modify_VentCtrl,
            'MaxTempDiffVOF': param_accis.modify_MaxTempDiffVOF,
            'MinTempDiffVOF': param_accis.modify_MinTempDiffVOF,
            'MultiplierVOF': param_accis.modify_MultiplierVOF,
            'VSToffset': param_accis.modify_VSToffset,
            'MinOToffset': param_accis.modify_MinOToffset,
            'MaxWindSpeed': param_accis.modify_MaxWindSpeed,
            'ASTtol': param_accis.modify_ASTtol,
        }

        if parameter.lower() not in [k.lower() for k in parameters_accis.keys()]:
            raise KeyError(f'Parameter do not exist.'
                           f'You need to chose one of the following list: {parameters_accis.keys()}')

        self.name = [i for i in parameters_accis.keys() if i.lower() == parameter.lower()][0]

    def modify(self, idf, value):
        """Apply the configured parameter value into an IDF.

        Parameters
        ----------
        idf : besos.IDF_class
            Target eppy/BESOS IDF instance.
        value : Any
            Value to be passed to ACCIS modifier functions.

        Returns
        -------
        None
            Modifies the ``idf`` object in place.

        Usage
        -----
        Use this legacy wrapper when a parameter is selected dynamically as a
        string.

        Examples
        --------
        p = Parameter('ComfStand')
        p.modify(idf, 1)
        """
        parameters_accis = {
            'ComfStand': param_accis.modify_ComfStand(idf, value),
            'CAT': param_accis.modify_CAT(idf, value),
            'CATcoolOffset': param_accis.modify_CATcoolOffset(idf, value),
            'CATheatOffset': param_accis.modify_CATheatOffset(idf, value),
            'ComfMod': param_accis.modify_ComfMod(idf, value),
            'SetpointAcc': param_accis.modify_SetpointAcc(idf, value),
            'CustAST_ACSTaul': param_accis.modify_CustAST_ACSTaul(idf, value),
            'CustAST_ACSTall': param_accis.modify_CustAST_ACSTall(idf, value),
            'CustAST_AHSTaul': param_accis.modify_CustAST_AHSTaul(idf, value),
            'CustAST_AHSTall': param_accis.modify_CustAST_AHSTall(idf, value),
            'CustAST_m': param_accis.modify_CustAST_m(idf, value),
            'CustAST_n': param_accis.modify_CustAST_n(idf, value),
            'CustAST_ACSToffset': param_accis.modify_CustAST_ACSToffset(idf, value),
            'CustAST_AHSToffset': param_accis.modify_CustAST_AHSToffset(idf, value),
            'CoolSeasonStart': param_accis.modify_CoolSeasonStart(idf, value),
            'CoolSeasonEnd': param_accis.modify_CoolSeasonEnd(idf, value),
            'HVACmode': param_accis.modify_HVACmode(idf, value),
            'VentCtrl': param_accis.modify_VentCtrl(idf, value),
            'MaxTempDiffVOF': param_accis.modify_MaxTempDiffVOF(idf, value),
            'MinTempDiffVOF': param_accis.modify_MinTempDiffVOF(idf, value),
            'MultiplierVOF': param_accis.modify_MultiplierVOF(idf, value),
            'VSToffset': param_accis.modify_VSToffset(idf, value),
            'MinOToffset': param_accis.modify_MinOToffset(idf, value),
            'MaxWindSpeed': param_accis.modify_MaxWindSpeed(idf, value),
            'ASTtol': param_accis.modify_ASTtol(idf, value),
        }

        parameters_accis[self.name]


# Add class/method docstrings for every ACCIS wrapper class below
# (ComfStand ... MultiplierVOF), each including:
# - class purpose + usage + example
# - __init__ usage + example
# - modify argument docs (idf, value) + usage + example
# Keep behavior unchanged.

class ComfStand:
    """OO wrapper for ACCIS parameter ``ComfStand``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = ComfStand()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        ComfStand().name
        'ComfStand'
        """
        self.name = 'ComfStand'

    def modify(self, idf, value):
        """Apply parameter ``ComfStand`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_ComfStand``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        ComfStand().modify(idf, 1)
        """
        param_accis.modify_ComfStand(idf, value)

class CustAST_ACSTaul:
    """OO wrapper for ACCIS parameter ``CustAST_ACSTaul``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_ACSTaul()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_ACSTaul().name
        'CustAST_ACSTaul'
        """
        self.name = 'CustAST_ACSTaul'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_ACSTaul`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_ACSTaul``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_ACSTaul().modify(idf, 1)
        """
        param_accis.modify_CustAST_ACSTaul(idf, value)

class CustAST_ACSTall:
    """OO wrapper for ACCIS parameter ``CustAST_ACSTall``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_ACSTall()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_ACSTall().name
        'CustAST_ACSTall'
        """
        self.name = 'CustAST_ACSTall'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_ACSTall`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_ACSTall``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_ACSTall().modify(idf, 1)
        """
        param_accis.modify_CustAST_ACSTall(idf, value)

class CustAST_AHSTaul:
    """OO wrapper for ACCIS parameter ``CustAST_AHSTaul``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_AHSTaul()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_AHSTaul().name
        'CustAST_AHSTaul'
        """
        self.name = 'CustAST_AHSTaul'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_AHSTaul`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_AHSTaul``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_AHSTaul().modify(idf, 1)
        """
        param_accis.modify_CustAST_AHSTaul(idf, value)

class CustAST_AHSTall:
    """OO wrapper for ACCIS parameter ``CustAST_AHSTall``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_AHSTall()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_AHSTall().name
        'CustAST_AHSTall'
        """
        self.name = 'CustAST_AHSTall'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_AHSTall`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_AHSTall``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_AHSTall().modify(idf, 1)
        """
        param_accis.modify_CustAST_AHSTall(idf, value)

class CustAST_ASTaul:
    """OO wrapper for ACCIS parameter ``CustAST_ASTaul``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_ASTaul()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_ASTaul().name
        'CustAST_ASTaul'
        """
        self.name = 'CustAST_ASTaul'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_ASTaul`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_ASTaul``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_ASTaul().modify(idf, 1)
        """
        param_accis.modify_CustAST_ASTaul(idf, value)

class CustAST_ASTall:
    """OO wrapper for ACCIS parameter ``CustAST_ASTall``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_ASTall()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_ASTall().name
        'CustAST_ASTall'
        """
        self.name = 'CustAST_ASTall'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_ASTall`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_ASTall``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_ASTall().modify(idf, 1)
        """
        param_accis.modify_CustAST_ASTall(idf, value)

class CustAST_m:
    """OO wrapper for ACCIS parameter ``CustAST_m``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_m()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_m().name
        'CustAST_m'
        """
        self.name = 'CustAST_m'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_m`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_m``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_m().modify(idf, 1)
        """
        param_accis.modify_CustAST_m(idf, value)

class CustAST_n:
    """OO wrapper for ACCIS parameter ``CustAST_n``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_n()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_n().name
        'CustAST_n'
        """
        self.name = 'CustAST_n'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_n`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_n``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_n().modify(idf, 1)
        """
        param_accis.modify_CustAST_n(idf, value)

class CustAST_ACSToffset:
    """OO wrapper for ACCIS parameter ``CustAST_ACSToffset``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_ACSToffset()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_ACSToffset().name
        'CustAST_ACSToffset'
        """
        self.name = 'CustAST_ACSToffset'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_ACSToffset`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_ACSToffset``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_ACSToffset().modify(idf, 1)
        """
        param_accis.modify_CustAST_ACSToffset(idf, value)

class CustAST_AHSToffset:
    """OO wrapper for ACCIS parameter ``CustAST_AHSToffset``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_AHSToffset()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_AHSToffset().name
        'CustAST_AHSToffset'
        """
        self.name = 'CustAST_AHSToffset'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_AHSToffset`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_AHSToffset``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_AHSToffset().modify(idf, 1)
        """
        param_accis.modify_CustAST_AHSToffset(idf, value)

class CustAST_ASToffset:
    """OO wrapper for ACCIS parameter ``CustAST_ASToffset``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_ASToffset()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_ASToffset().name
        'CustAST_ASToffset'
        """
        self.name = 'CustAST_ASToffset'

    def modify(self, idf, value):
        """Apply parameter ``CustAST_ASToffset`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CustAST_ASToffset``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_ASToffset().modify(idf, 1)
        """
        param_accis.modify_CustAST_ASToffset(idf, value)

class CAT:
    """OO wrapper for ACCIS parameter ``CAT``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CAT()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CAT().name
        'CAT'
        """
        self.name = 'CAT'

    def modify(self, idf, value):
        """Apply parameter ``CAT`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CAT``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CAT().modify(idf, 1)
        """
        param_accis.modify_CAT(idf, value)

class CATcoolOffset:
    """OO wrapper for ACCIS parameter ``CATcoolOffset``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CATcoolOffset()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CATcoolOffset().name
        'CATcoolOffset'
        """
        self.name = 'CATcoolOffset'

    def modify(self, idf, value):
        """Apply parameter ``CATcoolOffset`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CATcoolOffset``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CATcoolOffset().modify(idf, 1)
        """
        param_accis.modify_CATcoolOffset(idf, value)

class CATheatOffset:
    """OO wrapper for ACCIS parameter ``CATheatOffset``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CATheatOffset()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CATheatOffset().name
        'CATheatOffset'
        """
        self.name = 'CATheatOffset'

    def modify(self, idf, value):
        """Apply parameter ``CATheatOffset`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CATheatOffset``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CATheatOffset().modify(idf, 1)
        """
        param_accis.modify_CATheatOffset(idf, value)

class ComfMod:
    """OO wrapper for ACCIS parameter ``ComfMod``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = ComfMod()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        ComfMod().name
        'ComfMod'
        """
        self.name = 'ComfMod'

    def modify(self, idf, value):
        """Apply parameter ``ComfMod`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_ComfMod``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        ComfMod().modify(idf, 1)
        """
        param_accis.modify_ComfMod(idf, value)

class HVACmode:
    """OO wrapper for ACCIS parameter ``HVACmode``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = HVACmode()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        HVACmode().name
        'HVACmode'
        """
        self.name = 'HVACmode'

    def modify(self, idf, value):
        """Apply parameter ``HVACmode`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_HVACmode``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        HVACmode().modify(idf, 1)
        """
        param_accis.modify_HVACmode(idf, value)

class VentCtrl:
    """OO wrapper for ACCIS parameter ``VentCtrl``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = VentCtrl()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        VentCtrl().name
        'VentCtrl'
        """
        self.name = 'VentCtrl'

    def modify(self, idf, value):
        """Apply parameter ``VentCtrl`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_VentCtrl``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        VentCtrl().modify(idf, 1)
        """
        param_accis.modify_VentCtrl(idf, value)

class VSToffset:
    """OO wrapper for ACCIS parameter ``VSToffset``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = VSToffset()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        VSToffset().name
        'VSToffset'
        """
        self.name = 'VSToffset'

    def modify(self, idf, value):
        """Apply parameter ``VSToffset`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_VSToffset``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        VSToffset().modify(idf, 1)
        """
        param_accis.modify_VSToffset(idf, value)

class MinOToffset:
    """OO wrapper for ACCIS parameter ``MinOToffset``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = MinOToffset()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        MinOToffset().name
        'MinOToffset'
        """
        self.name = 'MinOToffset'

    def modify(self, idf, value):
        """Apply parameter ``MinOToffset`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_MinOToffset``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        MinOToffset().modify(idf, 1)
        """
        param_accis.modify_MinOToffset(idf, value)

class MaxWindSpeed:
    """OO wrapper for ACCIS parameter ``MaxWindSpeed``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = MaxWindSpeed()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        MaxWindSpeed().name
        'MaxWindSpeed'
        """
        self.name = 'MaxWindSpeed'

    def modify(self, idf, value):
        """Apply parameter ``MaxWindSpeed`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_MaxWindSpeed``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        MaxWindSpeed().modify(idf, 1)
        """
        param_accis.modify_MaxWindSpeed(idf, value)

class ASTtol:
    """OO wrapper for ACCIS parameter ``ASTtol``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = ASTtol()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        ASTtol().name
        'ASTtol'
        """
        self.name = 'ASTtol'

    def modify(self, idf, value):
        """Apply parameter ``ASTtol`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_ASTtol``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        ASTtol().modify(idf, 1)
        """
        param_accis.modify_ASTtol(idf, value)

class CoolSeasonStart:
    """OO wrapper for ACCIS parameter ``CoolSeasonStart``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CoolSeasonStart()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CoolSeasonStart().name
        'CoolSeasonStart'
        """
        self.name = 'CoolSeasonStart'

    def modify(self, idf, value):
        """Apply parameter ``CoolSeasonStart`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CoolSeasonStart``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CoolSeasonStart().modify(idf, 1)
        """
        param_accis.modify_CoolSeasonStart(idf, value)

class CoolSeasonEnd:
    """OO wrapper for ACCIS parameter ``CoolSeasonEnd``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CoolSeasonEnd()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CoolSeasonEnd().name
        'CoolSeasonEnd'
        """
        self.name = 'CoolSeasonEnd'

    def modify(self, idf, value):
        """Apply parameter ``CoolSeasonEnd`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_CoolSeasonEnd``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CoolSeasonEnd().modify(idf, 1)
        """
        param_accis.modify_CoolSeasonEnd(idf, value)

class SetpointAcc:
    """OO wrapper for ACCIS parameter ``SetpointAcc``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = SetpointAcc()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        SetpointAcc().name
        'SetpointAcc'
        """
        self.name = 'SetpointAcc'

    def modify(self, idf, value):
        """Apply parameter ``SetpointAcc`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_SetpointAcc``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        SetpointAcc().modify(idf, 1)
        """
        param_accis.modify_SetpointAcc(idf, value)

class MaxTempDiffVOF:
    """OO wrapper for ACCIS parameter ``MaxTempDiffVOF``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = MaxTempDiffVOF()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        MaxTempDiffVOF().name
        'MaxTempDiffVOF'
        """
        self.name = 'MaxTempDiffVOF'

    def modify(self, idf, value):
        """Apply parameter ``MaxTempDiffVOF`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_MaxTempDiffVOF``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        MaxTempDiffVOF().modify(idf, 1)
        """
        param_accis.modify_MaxTempDiffVOF(idf, value)

class MinTempDiffVOF:
    """OO wrapper for ACCIS parameter ``MinTempDiffVOF``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = MinTempDiffVOF()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        MinTempDiffVOF().name
        'MinTempDiffVOF'
        """
        self.name = 'MinTempDiffVOF'

    def modify(self, idf, value):
        """Apply parameter ``MinTempDiffVOF`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_MinTempDiffVOF``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        MinTempDiffVOF().modify(idf, 1)
        """
        param_accis.modify_MinTempDiffVOF(idf, value)

class MultiplierVOF:
    """OO wrapper for ACCIS parameter ``MultiplierVOF``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = MultiplierVOF()
    p.modify(idf, 1)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        MultiplierVOF().name
        'MultiplierVOF'
        """
        self.name = 'MultiplierVOF'

    def modify(self, idf, value):
        """Apply parameter ``MultiplierVOF`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : Any
            Value written by ``param_accis.modify_MultiplierVOF``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        MultiplierVOF().modify(idf, 1)
        """
        param_accis.modify_MultiplierVOF(idf, value)

