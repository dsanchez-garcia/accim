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
p = accis_parameter("comfort_standard", [1, 2, 3])
p.name
'comfort_standard'
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
    p = accis_parameter("comfort_standard", [1, 2, 3])
    p.name
    'comfort_standard'
    q = accis_parameter("custom_slope", (0.0, 0.7))
    q.name
    'custom_slope'
    """
    desc_has_options = descriptor_has_options(values)

    name = params_dicts.resolve_parameter_name(parameter_name)
    if name not in params_dicts.all_params:
        raise KeyError(f'The parameter {parameter_name!r} does not exist. '
                       f'You need to choose one of the following list: {list(params_dicts.all_params)}')

    from besos.parameters import Parameter, GenericSelector, CategoryParameter, RangeParameter
    import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf
    import numpy as np

    if desc_has_options:
        parameter = Parameter(
            # NOTE: 'name' is intentionally NOT passed here: it's already set on
            # the value_descriptors below. Passing it in both places triggers a
            # spurious "This parameter's descriptor is already named ..." UserWarning
            # from besos (harmless, since both names are identical, but noisy).
            # selector=GenericSelector(set=change_adaptive_coeff),
            selector=GenericSelector(set=params_dicts.all_params[name]),
            # value_descriptors=RangeParameter(name='custom_slope', min_val=0, max_val=0.7),
            value_descriptors=CategoryParameter(
                name=name,
                options=values
            ),
        ),
    else:
        parameter = Parameter(
            # NOTE: see comment above; 'name' is set via value_descriptors only.
            # selector=GenericSelector(set=change_adaptive_coeff),
            selector=GenericSelector(set=params_dicts.all_params[name]),
            # value_descriptors=RangeParameter(name='custom_slope', min_val=0, max_val=0.7),
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
    >>> 'comfort_standard' in names
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
    >>> 'custom_slope' in names
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
    >>> 'pmv_setpoint' in names
    True
    """
    param_dict = [k for k in params_dicts.apmv_setpoints_params.keys()]
    return param_dict


def get_available_params_epmv_setpoints():
    """List available ePMV setpoint parameter names.

    Returns
    -------
    list[str]
        Parameter names that control the ePMV setpoints (the parameters type ``'epmv setpoints'``).

    Usage
    -----
    Use this helper before building ePMV-oriented parameter sweeps.

    Examples
    --------
    >>> names = get_available_params_epmv_setpoints()
    >>> 'expectancy_factor' in names
    True
    """
    param_dict = [k for k in params_dicts.epmv_setpoints_params.keys()]
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
    p = Parameter('comfort_standard')
    p.modify(idf, 1)
    """

    def __init__(self, parameter):
        """Initialize the parameter wrapper.

        Parameters
        ----------
        parameter : str
            Requested parameter name (case-insensitive): one of the parameters of the accim predefined and custom
            models, or its name in accim 0.x (``ComfStand``...), with a DeprecationWarning.

        Returns
        -------
        None
            Stores the canonical name in ``self.name``.

        Usage
        -----
        Construct once and reuse across multiple IDFs if needed.

        Examples
        --------
        p = Parameter('Comfort_Standard')
        p.name
        'comfort_standard'
        """
        parameters_accis = {**params_dicts.accim_predef_model_params, **params_dicts.accim_custom_model_params}
        name = params_dicts.resolve_parameter_name(parameter)
        if name not in parameters_accis:
            raise KeyError(f'The parameter {parameter!r} does not exist. '
                           f'You need to choose one of the following list: {list(parameters_accis)}')
        self.name = name

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
        p = Parameter('comfort_standard')
        p.modify(idf, 1)
        """
        params_dicts.all_params[self.name](idf, value)


# Add class/method docstrings for every ACCIS wrapper class below
# (ComfStand ... MultiplierVOF), each including:
# - class purpose + usage + example
# - __init__ usage + example
# - modify argument docs (idf, value) + usage + example
# Keep behavior unchanged.

class ComfStand:
    """OO wrapper for the ACCIS parameter ``comfort_standard`` (``ComfStand`` in accim 0.x).

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
        'comfort_standard'
        """
        self.name = 'comfort_standard'

    def modify(self, idf, value):
        """Apply parameter ``comfort_standard`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_cooling_upper_limit`` (``CustAST_ACSTaul`` in accim 0.x).

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
        'custom_cooling_upper_limit'
        """
        self.name = 'custom_cooling_upper_limit'

    def modify(self, idf, value):
        """Apply parameter ``custom_cooling_upper_limit`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_cooling_lower_limit`` (``CustAST_ACSTall`` in accim 0.x).

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
        'custom_cooling_lower_limit'
        """
        self.name = 'custom_cooling_lower_limit'

    def modify(self, idf, value):
        """Apply parameter ``custom_cooling_lower_limit`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_heating_upper_limit`` (``CustAST_AHSTaul`` in accim 0.x).

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
        'custom_heating_upper_limit'
        """
        self.name = 'custom_heating_upper_limit'

    def modify(self, idf, value):
        """Apply parameter ``custom_heating_upper_limit`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_heating_lower_limit`` (``CustAST_AHSTall`` in accim 0.x).

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
        'custom_heating_lower_limit'
        """
        self.name = 'custom_heating_lower_limit'

    def modify(self, idf, value):
        """Apply parameter ``custom_heating_lower_limit`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_upper_limit`` (``CustAST_ASTaul`` in accim 0.x).

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
        'custom_upper_limit'
        """
        self.name = 'custom_upper_limit'

    def modify(self, idf, value):
        """Apply parameter ``custom_upper_limit`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_lower_limit`` (``CustAST_ASTall`` in accim 0.x).

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
        'custom_lower_limit'
        """
        self.name = 'custom_lower_limit'

    def modify(self, idf, value):
        """Apply parameter ``custom_lower_limit`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_slope`` (``CustAST_m`` in accim 0.x).

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
        'custom_slope'
        """
        self.name = 'custom_slope'

    def modify(self, idf, value):
        """Apply parameter ``custom_slope`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_intercept`` (``CustAST_n`` in accim 0.x).

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
        'custom_intercept'
        """
        self.name = 'custom_intercept'

    def modify(self, idf, value):
        """Apply parameter ``custom_intercept`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_cooling_offset`` (``CustAST_ACSToffset`` in accim 0.x).

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
        'custom_cooling_offset'
        """
        self.name = 'custom_cooling_offset'

    def modify(self, idf, value):
        """Apply parameter ``custom_cooling_offset`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_heating_offset`` (``CustAST_AHSToffset`` in accim 0.x).

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
        'custom_heating_offset'
        """
        self.name = 'custom_heating_offset'

    def modify(self, idf, value):
        """Apply parameter ``custom_heating_offset`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``custom_offset`` (``CustAST_ASToffset`` in accim 0.x).

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
        'custom_offset'
        """
        self.name = 'custom_offset'

    def modify(self, idf, value):
        """Apply parameter ``custom_offset`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``category`` (``CAT`` in accim 0.x).

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
        'category'
        """
        self.name = 'category'

    def modify(self, idf, value):
        """Apply parameter ``category`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``category_cooling_offset`` (``CATcoolOffset`` in accim 0.x).

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
        'category_cooling_offset'
        """
        self.name = 'category_cooling_offset'

    def modify(self, idf, value):
        """Apply parameter ``category_cooling_offset`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``category_heating_offset`` (``CATheatOffset`` in accim 0.x).

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
        'category_heating_offset'
        """
        self.name = 'category_heating_offset'

    def modify(self, idf, value):
        """Apply parameter ``category_heating_offset`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``comfort_mode`` (``ComfMod`` in accim 0.x).

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
        'comfort_mode'
        """
        self.name = 'comfort_mode'

    def modify(self, idf, value):
        """Apply parameter ``comfort_mode`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``hvac_mode`` (``HVACmode`` in accim 0.x).

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
        'hvac_mode'
        """
        self.name = 'hvac_mode'

    def modify(self, idf, value):
        """Apply parameter ``hvac_mode`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``ventilation_control`` (``VentCtrl`` in accim 0.x).

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
        'ventilation_control'
        """
        self.name = 'ventilation_control'

    def modify(self, idf, value):
        """Apply parameter ``ventilation_control`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``ventilation_setpoint_offset`` (``VSToffset`` in accim 0.x).

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
        'ventilation_setpoint_offset'
        """
        self.name = 'ventilation_setpoint_offset'

    def modify(self, idf, value):
        """Apply parameter ``ventilation_setpoint_offset`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``min_outdoor_temp_offset`` (``MinOToffset`` in accim 0.x).

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
        'min_outdoor_temp_offset'
        """
        self.name = 'min_outdoor_temp_offset'

    def modify(self, idf, value):
        """Apply parameter ``min_outdoor_temp_offset`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``max_wind_speed`` (``MaxWindSpeed`` in accim 0.x).

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
        'max_wind_speed'
        """
        self.name = 'max_wind_speed'

    def modify(self, idf, value):
        """Apply parameter ``max_wind_speed`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``setpoint_tolerance`` (``ASTtol`` in accim 0.x).

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
        'setpoint_tolerance'
        """
        self.name = 'setpoint_tolerance'

    def modify(self, idf, value):
        """Apply parameter ``setpoint_tolerance`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``cooling_season_start`` (``CoolSeasonStart`` in accim 0.x).

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
        'cooling_season_start'
        """
        self.name = 'cooling_season_start'

    def modify(self, idf, value):
        """Apply parameter ``cooling_season_start`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``cooling_season_end`` (``CoolSeasonEnd`` in accim 0.x).

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
        'cooling_season_end'
        """
        self.name = 'cooling_season_end'

    def modify(self, idf, value):
        """Apply parameter ``cooling_season_end`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``setpoint_accuracy`` (``SetpointAcc`` in accim 0.x).

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
        'setpoint_accuracy'
        """
        self.name = 'setpoint_accuracy'

    def modify(self, idf, value):
        """Apply parameter ``setpoint_accuracy`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``opening_factor_max_temp_diff`` (``MaxTempDiffVOF`` in accim 0.x).

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
        'opening_factor_max_temp_diff'
        """
        self.name = 'opening_factor_max_temp_diff'

    def modify(self, idf, value):
        """Apply parameter ``opening_factor_max_temp_diff`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``opening_factor_min_temp_diff`` (``MinTempDiffVOF`` in accim 0.x).

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
        'opening_factor_min_temp_diff'
        """
        self.name = 'opening_factor_min_temp_diff'

    def modify(self, idf, value):
        """Apply parameter ``opening_factor_min_temp_diff`` to an IDF in place.

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
    """OO wrapper for the ACCIS parameter ``min_opening_factor`` (``MultiplierVOF`` in accim 0.x).

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
        'min_opening_factor'
        """
        self.name = 'min_opening_factor'

    def modify(self, idf, value):
        """Apply parameter ``min_opening_factor`` to an IDF in place.

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

