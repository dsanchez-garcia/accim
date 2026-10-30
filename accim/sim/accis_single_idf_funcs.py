# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Deprecated module of accim 0.x: use :mod:`accim.sim.accis` (``add_accis_to_idf``, ``modify_accis`` and
``gen_outputs_df``), whose arguments follow PEP 8. These functions accept the old argument names."""

from accim._deprecation import rename_legacy_kwargs, warn_deprecated
from accim.sim import accis as _accis
from accim.sim.arguments import LEGACY_ARGUMENT_NAMES

__all__ = ['addAccis', 'gen_outputs_df', 'modifyAccis', 'modify_param']

_MODIFY_PARAMETERS = (
    'ComfStand', 'CAT', 'ComfMod', 'SetpointAcc', 'CoolSeasonStart', 'CoolSeasonEnd', 'HVACmode', 'VentCtrl',
    'MaxTempDiffVOF', 'MinTempDiffVOF', 'MultiplierVOF', 'VSToffset', 'MinOToffset', 'MaxWindSpeed', 'ASTtol',
)


def addAccis(idf=None, *args, **kwargs):  # noqa: N802 (the name of accim 0.x)
    """Deprecated: use :func:`accim.sim.accis.add_accis_to_idf`."""
    warn_deprecated('accim.sim.accis_single_idf_funcs.addAccis', 'accim.sim.accis.add_accis_to_idf')
    kwargs = rename_legacy_kwargs(kwargs, LEGACY_ARGUMENT_NAMES, 'addAccis')
    return _accis.add_accis_to_idf(idf, *args, **kwargs)


def gen_outputs_df(idf=None, *args, **kwargs):
    """Deprecated: use :func:`accim.sim.accis.gen_outputs_df`."""
    warn_deprecated('accim.sim.accis_single_idf_funcs.gen_outputs_df', 'accim.sim.accis.gen_outputs_df')
    kwargs = rename_legacy_kwargs(kwargs, LEGACY_ARGUMENT_NAMES, 'gen_outputs_df')
    return _accis.gen_outputs_df(idf, *args, **kwargs)


def modifyAccis(idf, *args, **kwargs):  # noqa: N802 (the name of accim 0.x)
    """Deprecated: use :func:`accim.sim.accis.modify_accis`."""
    warn_deprecated('accim.sim.accis_single_idf_funcs.modifyAccis', 'accim.sim.accis.modify_accis')
    kwargs = rename_legacy_kwargs(kwargs, LEGACY_ARGUMENT_NAMES, 'modifyAccis')
    return _accis.modify_accis(idf, *args, **kwargs)


def modify_param(idf, parameter: str, value) -> None:
    """Deprecated: set one argument of the ACCIS of a model with :func:`accim.sim.accis.modify_accis`, or
    with the functions of :mod:`accim.parametric_and_optimisation.funcs_for_besos.param_accis`.

    It only checks the name of the parameter, as in accim 0.x.
    """
    warn_deprecated('accim.sim.accis_single_idf_funcs.modify_param', 'accim.sim.accis.modify_accis')
    if parameter.lower() not in [p.lower() for p in _MODIFY_PARAMETERS]:
        raise ValueError(f'The {parameter} parameter you have entered is not valid. Valid parameters are '
                         f'{list(_MODIFY_PARAMETERS)}')
