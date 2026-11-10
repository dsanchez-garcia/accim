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
        exist in ``params_dicts.all_params``, or be a coefficient of a regime
        of the custom model, ``custom_regime_<regime>_<field>`` (see
        :func:`custom_regime_parameters`).
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
    regime = params_dicts.custom_regime_parameter(name)
    if regime is not None:
        # A coefficient of a regime of the custom model (custom_regime_<regime>_<field>)
        name = f'custom_regime_{regime[0]}_{regime[1]}'
        modifier = params_dicts.custom_regime_modifier(name)
    elif name not in params_dicts.all_params:
        raise KeyError(f'The parameter {parameter_name!r} does not exist. '
                       f'You need to choose one of the following list: {list(params_dicts.all_params)}')
    else:
        modifier = params_dicts.all_params[name]

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
            selector=GenericSelector(set=modifier),
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
            selector=GenericSelector(set=modifier),
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


class HeatingSetpointFloor:
    """OO wrapper for the ACCIS parameter ``heating_setpoint_floor`` (the input ``AHSTfloor``, accim 1.2.0): the
    heating setpoint of all the zones is not lower than the value (°C), whatever the comfort standard and the comfort
    mode are (EN 16798-1:2019 applies in winter the minimums of its Table B.2, ``accim.constants.EN16798_TABLE_B2``).

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = HeatingSetpointFloor()
    p.modify(idf, 20)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        HeatingSetpointFloor().name
        'heating_setpoint_floor'
        """
        self.name = 'heating_setpoint_floor'

    def modify(self, idf, value):
        """Apply parameter ``heating_setpoint_floor`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit, with the ACCIS of accim 1.0.0 or later.
        value : float
            The floor of the heating setpoint (°C), written by ``param_accis.modify_AHSTfloor``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        HeatingSetpointFloor().modify(idf, 20)
        """
        param_accis.modify_AHSTfloor(idf, value)


class CoolingSetpointCeiling:
    """OO wrapper for the ACCIS parameter ``cooling_setpoint_ceiling`` (the input ``ACSTceil``, accim 1.2.0): the
    cooling setpoint of all the zones is not higher than the value (°C), whatever the comfort standard and the comfort
    mode are (the maximums of Table B.2 of EN 16798-1:2019, ``accim.constants.EN16798_TABLE_B2``).

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CoolingSetpointCeiling()
    p.modify(idf, 26)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CoolingSetpointCeiling().name
        'cooling_setpoint_ceiling'
        """
        self.name = 'cooling_setpoint_ceiling'

    def modify(self, idf, value):
        """Apply parameter ``cooling_setpoint_ceiling`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit, with the ACCIS of accim 1.0.0 or later.
        value : float
            The ceiling of the cooling setpoint (°C), written by ``param_accis.modify_ACSTceil``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CoolingSetpointCeiling().modify(idf, 26)
        """
        param_accis.modify_ACSTceil(idf, value)


class StaticHeatingSetpoint:
    """OO wrapper for the ACCIS parameter ``static_heating_setpoint`` (the input ``StaticAHST``, accim 1.2.0): the
    static heating setpoint (°C) of JPN Aqilah 2025 (comfort standard 23) in all the zones, in comfort mode 0 and out
    of the applicability limits in comfort mode 1 (its paper gives no static setpoints: decision D2 of the brief of
    1.2.0, 20 °C by default). The other comfort standards ignore it (:mod:`accim.sim.ems.static_setpoints`).

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = StaticHeatingSetpoint()
    p.modify(idf, 19)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        StaticHeatingSetpoint().name
        'static_heating_setpoint'
        """
        self.name = 'static_heating_setpoint'

    def modify(self, idf, value):
        """Apply parameter ``static_heating_setpoint`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit, with the ACCIS of accim 1.0.0 or later.
        value : float
            The static heating setpoint (°C), written by ``param_accis.modify_StaticAHST``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        StaticHeatingSetpoint().modify(idf, 19)
        """
        param_accis.modify_StaticAHST(idf, value)


class StaticCoolingSetpoint:
    """OO wrapper for the ACCIS parameter ``static_cooling_setpoint`` (the input ``StaticACST``, accim 1.2.0): the
    static cooling setpoint (°C) of JPN Aqilah 2025 (comfort standard 23) in all the zones, 28 °C by default, as
    :class:`StaticHeatingSetpoint`.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = StaticCoolingSetpoint()
    p.modify(idf, 27)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        StaticCoolingSetpoint().name
        'static_cooling_setpoint'
        """
        self.name = 'static_cooling_setpoint'

    def modify(self, idf, value):
        """Apply parameter ``static_cooling_setpoint`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit, with the ACCIS of accim 1.0.0 or later.
        value : float
            The static cooling setpoint (°C), written by ``param_accis.modify_StaticACST``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        StaticCoolingSetpoint().modify(idf, 27)
        """
        param_accis.modify_StaticACST(idf, value)


class Clo:
    """OO wrapper for the parameter ``clothing_insulation``: the clothing insulation of all the People objects (clo),
    with :func:`accim.sim.apmv.set_pmv_input_parameters` (the schedules ``Sch_Clo_<people>``); it warns outside 0 to 2
    clo (ISO 7730:2025, section 4) and above 1.5 clo (ASHRAE 55-2020). A parameter of the parameters types
    ``'apmv setpoints'`` and ``'epmv setpoints'`` (accim 1.2.0).

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = Clo()
    p.modify(idf, 0.5)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        Clo().name
        'clothing_insulation'
        """
        self.name = 'clothing_insulation'

    def modify(self, idf, value):
        """Apply parameter ``clothing_insulation`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : float
            The clothing insulation (clo). Written by ``param_apmv.change_clothing_insulation_all_zones``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        Clo().modify(idf, 0.5)
        """
        param_apmv.change_clothing_insulation_all_zones(idf, value)


class Met:
    """OO wrapper for the parameter ``activity_level``: the activity level of all the People objects (W/person, as in
    EnergyPlus), with :func:`accim.sim.apmv.set_pmv_input_parameters` (the schedules ``Sch_Act_<people>``); it warns
    outside 82.8 to 417.6 W/person, the 0.8 to 4 met (46 to 232 W/m²) of ISO 7730:2025 (section 4) with a body surface
    area of 1.8 m². A parameter of the parameters types ``'apmv setpoints'`` and ``'epmv setpoints'`` (accim 1.2.0).

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = Met()
    p.modify(idf, 126)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        Met().name
        'activity_level'
        """
        self.name = 'activity_level'

    def modify(self, idf, value):
        """Apply parameter ``activity_level`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : float
            The activity level (W/person). Written by ``param_apmv.change_activity_level_all_zones``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        Met().modify(idf, 126)
        """
        param_apmv.change_activity_level_all_zones(idf, value)


class AirVelocity:
    """OO wrapper for the parameter ``air_velocity``: the air velocity of all the People objects (m/s), with
    :func:`accim.sim.apmv.set_pmv_input_parameters` (the schedules ``Sch_Vel_<people>``); it warns outside 0 to 1 m/s
    (ISO 7730:2025, section 4). A parameter of the parameters types ``'apmv setpoints'`` and ``'epmv setpoints'`` (accim
    1.2.0).

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = AirVelocity()
    p.modify(idf, 0.2)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        AirVelocity().name
        'air_velocity'
        """
        self.name = 'air_velocity'

    def modify(self, idf, value):
        """Apply parameter ``air_velocity`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : float
            The air velocity (m/s). Written by ``param_apmv.change_air_velocity_all_zones``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        AirVelocity().modify(idf, 0.2)
        """
        param_apmv.change_air_velocity_all_zones(idf, value)


class ExpectancyFactor:
    """OO wrapper for the parameter ``expectancy_factor``: the expectancy factor of the ePMV setpoints of all the zones
    (:func:`accim.sim.apmv.apply_epmv_setpoints`), between 0.5 and 1 (Fanger and Toftum, 2002). A parameter of the
    parameters type ``'epmv setpoints'``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = ExpectancyFactor()
    p.modify(idf, 0.7)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        ExpectancyFactor().name
        'expectancy_factor'
        """
        self.name = 'expectancy_factor'

    def modify(self, idf, value):
        """Apply parameter ``expectancy_factor`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : float
            The expectancy factor. Written by ``param_apmv.change_expectancy_factor_all_zones``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        ExpectancyFactor().modify(idf, 0.7)
        """
        param_apmv.change_expectancy_factor_all_zones(idf, value)


class AdaptiveCoefficientCooling:
    """OO wrapper for the parameter ``adaptive_coefficient_cooling``: the adaptive coefficient of the aPMV setpoints of
    all the zones in the cooling season (or with PMV >= 0, with ``adaptive_coefficient_by='pmv_sign'``). A parameter of
    the parameters type ``'apmv setpoints'``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = AdaptiveCoefficientCooling()
    p.modify(idf, 0.293)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        AdaptiveCoefficientCooling().name
        'adaptive_coefficient_cooling'
        """
        self.name = 'adaptive_coefficient_cooling'

    def modify(self, idf, value):
        """Apply parameter ``adaptive_coefficient_cooling`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : float
            The adaptive coefficient. Written by ``param_apmv.change_adaptive_coeff_cooling_all_zones``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        AdaptiveCoefficientCooling().modify(idf, 0.293)
        """
        param_apmv.change_adaptive_coeff_cooling_all_zones(idf, value)


class AdaptiveCoefficientHeating:
    """OO wrapper for the parameter ``adaptive_coefficient_heating``: the adaptive coefficient of the aPMV setpoints of
    all the zones in the heating season (or with PMV < 0, with ``adaptive_coefficient_by='pmv_sign'``). A parameter of
    the parameters type ``'apmv setpoints'``.

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = AdaptiveCoefficientHeating()
    p.modify(idf, -0.125)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        AdaptiveCoefficientHeating().name
        'adaptive_coefficient_heating'
        """
        self.name = 'adaptive_coefficient_heating'

    def modify(self, idf, value):
        """Apply parameter ``adaptive_coefficient_heating`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : float
            The adaptive coefficient. Written by ``param_apmv.change_adaptive_coeff_heating_all_zones``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        AdaptiveCoefficientHeating().modify(idf, -0.125)
        """
        param_apmv.change_adaptive_coeff_heating_all_zones(idf, value)


class CustAST_metric:
    """OO wrapper for the parameter ``custom_outdoor_metric``: the outdoor metric of the custom model of all the zones
    (the input ``CustAST_metric``): its name or its code (:data:`accim.sim.ems.outdoor_metric.OUTDOOR_METRICS`, 0 to 7;
    the options of the parametric module are numbers). A parameter of the parameters type ``'accim custom model'``
    (accim 1.2.0).

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_metric()
    p.modify(idf, 2)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_metric().name
        'custom_outdoor_metric'
        """
        self.name = 'custom_outdoor_metric'

    def modify(self, idf, value):
        """Apply parameter ``custom_outdoor_metric`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : int or str
            The code or the name of the metric. Written by ``param_accis.modify_CustAST_metric``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_metric().modify(idf, 2)
        """
        param_accis.modify_CustAST_metric(idf, value)


class CustAST_alpha:
    """OO wrapper for the parameter ``custom_alpha``: the alpha of the outdoor metric 'rmot_alpha' of the custom model
    of all the zones (the input ``CustAST_alpha``); it warns outside 0.6 to 0.9 with 'rmot_alpha' (ASHRAE 55-2020,
    5.4.2.1). A parameter of the parameters type ``'accim custom model'`` (accim 1.2.0).

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_alpha()
    p.modify(idf, 0.8)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_alpha().name
        'custom_alpha'
        """
        self.name = 'custom_alpha'

    def modify(self, idf, value):
        """Apply parameter ``custom_alpha`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : float
            The alpha, between 0 and 1. Written by ``param_accis.modify_CustAST_alpha``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_alpha().modify(idf, 0.8)
        """
        param_accis.modify_CustAST_alpha(idf, value)


class CustAST_days:
    """OO wrapper for the parameter ``custom_days``: the days of the outdoor metric 'ndrm' of the custom model of all
    the zones (the input ``CustAST_days``), rounded to the nearest integer; it warns outside 7 to 30 days with 'ndrm'
    (ASHRAE 55-2020, 5.4.2.1). A parameter of the parameters type ``'accim custom model'`` (accim 1.2.0).

    Usage
    -----
    Instantiate the class and call :meth:`modify` with ``idf`` and ``value``.

    Examples
    --------
    p = CustAST_days()
    p.modify(idf, 7)
    """

    def __init__(self):
        """Initialize the wrapper and expose the canonical parameter name.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustAST_days().name
        'custom_days'
        """
        self.name = 'custom_days'

    def modify(self, idf, value):
        """Apply parameter ``custom_days`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit.
        value : float
            The number of days. Written by ``param_accis.modify_CustAST_days``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustAST_days().modify(idf, 7)
        """
        param_accis.modify_CustAST_days(idf, value)


#: The class names of the coefficients of each regime of the custom model (``CustAST_<name>_<regime>``, as the
#: parameters of the scalar custom model in accim 0.x) -> the field of :class:`accim.sim.arguments.CustomRegime`
CUSTOM_REGIME_CLASS_NAMES = {
    'm': 'slope',
    'n': 'intercept',
    'ACSToffset': 'cooling_offset',
    'AHSToffset': 'heating_offset',
    'ACSTall': 'cooling_lower_limit',
    'ACSTaul': 'cooling_upper_limit',
    'AHSTall': 'heating_lower_limit',
    'AHSTaul': 'heating_upper_limit',
}


class CustomRegimeParameter:
    """OO wrapper for a coefficient of a regime of the custom model (``custom_regimes``, proposal B2 of accim 1.2.0):
    the parameter ``custom_regime_<regime>_<field>`` of the parameters type ``'accim custom model'``, which sets the
    field of the regime in all the zones that have the regimes (``param_accis.modify_custom_regime``). The model must
    have the regimes already (``custom_regimes`` of :func:`accim.sim.accis.modify_accis`).

    Usage
    -----
    Instantiate the class with the regime and the field (or use the classes of :func:`custom_regime_parameters`) and
    call :meth:`modify` with ``idf`` and ``value``; :func:`accis_parameter` builds the BESOS parameter of its
    ``name``.

    Examples
    --------
    p = CustomRegimeParameter(1, 'slope')
    p.name
    'custom_regime_1_slope'
    p.modify(idf, 0.33)
    """

    def __init__(self, regime, field):
        """Initialize the wrapper and expose the canonical parameter name.

        Parameters
        ----------
        regime : int
            The number of the regime, from 1 (in the order of priority of the regimes).
        field : str
            The coefficient: 'slope', 'intercept', 'cooling_offset', 'heating_offset', 'cooling_lower_limit',
            'cooling_upper_limit', 'heating_lower_limit' or 'heating_upper_limit'.

        Usage
        -----
        Use the instance ``name`` attribute for logging or mapping checks.

        Examples
        --------
        CustomRegimeParameter(2, 'intercept').name
        'custom_regime_2_intercept'
        """
        name = f'custom_regime_{regime}_{field}'
        if (isinstance(regime, bool) or not isinstance(regime, int)
                or params_dicts.custom_regime_parameter(name) is None):
            raise ValueError(f'The regime must be a number from 1, and the field one of '
                             f'{list(params_dicts.CUSTOM_REGIME_FIELDS)}, not {regime!r} and {field!r}.')
        self.regime = regime
        self.field = field
        self.name = name

    def modify(self, idf, value):
        """Apply parameter ``custom_regime_<regime>_<field>`` to an IDF in place.

        Parameters
        ----------
        idf : besos.IDF_class
            Target building model to edit, with the regimes of the custom model.
        value : float
            The value of the coefficient. Written by ``param_accis.modify_custom_regime``.

        Returns
        -------
        None
            The function edits ``idf`` in place.

        Usage
        -----
        Call this method before executing parametric or optimisation runs.

        Examples
        --------
        CustomRegimeParameter(1, 'slope').modify(idf, 0.33)
        """
        param_accis.modify_custom_regime(idf, value, self.regime, self.field)


def custom_regime_parameters(n_regimes):
    """The wrapper classes of the coefficients of the first ``n_regimes`` regimes of the custom model (the factory of
    the proposal B2 of accim 1.2.0): ``CustAST_m_1``, ``CustAST_n_1``, ``CustAST_ACSToffset_1``,
    ``CustAST_AHSToffset_1``, ``CustAST_ACSTall_1``, ``CustAST_ACSTaul_1``, ``CustAST_AHSTall_1``,
    ``CustAST_AHSTaul_1``, ``CustAST_m_2``... (:data:`CUSTOM_REGIME_CLASS_NAMES`), subclasses of
    :class:`CustomRegimeParameter` that take no arguments, as the other wrapper classes. Their ``name`` is the
    parameter that :func:`accis_parameter` and ``set_parameters`` of the parametric module take for the parameters
    type ``'accim custom model'``, such as ``custom_regime_1_slope``.

    Parameters
    ----------
    n_regimes : int
        The number of regimes (at least 1).

    Returns
    -------
    dict
        The classes, by name, in the order of the regimes and of their coefficients.

    Usage
    -----
    Build the classes for the regimes of a model, and use them as the other wrapper classes.

    Examples
    --------
    classes = custom_regime_parameters(2)
    classes['CustAST_m_2']().name
    'custom_regime_2_slope'
    classes['CustAST_n_1']().modify(idf, 17.8)
    """
    if isinstance(n_regimes, bool) or not isinstance(n_regimes, int) or n_regimes < 1:
        raise ValueError(f'n_regimes must be a number of regimes of at least 1, not {n_regimes!r}.')
    classes = {}
    for regime in range(1, n_regimes + 1):
        for short, field in CUSTOM_REGIME_CLASS_NAMES.items():
            class_name = f'CustAST_{short}_{regime}'

            def __init__(self, _regime=regime, _field=field):
                CustomRegimeParameter.__init__(self, _regime, _field)

            classes[class_name] = type(class_name, (CustomRegimeParameter,), {
                '__init__': __init__,
                '__module__': __name__,
                '__doc__': f'OO wrapper for the parameter ``custom_regime_{regime}_{field}``: the {field} of the '
                           f'regime {regime} of the custom model (see :class:`CustomRegimeParameter`).',
            })
    return classes
