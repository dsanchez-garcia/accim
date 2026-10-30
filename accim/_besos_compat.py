# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Patches for the versions of besos, dask, platypus and Python that besos does not support yet.

They are applied by :mod:`accim.parametric_and_optimisation`, the module that uses besos to run
parametric simulations and optimisations. Each patch is applied once.
"""

import sys
import types
import warnings
from typing import Any, Optional

__all__ = ['apply_besos_patches', 'patch_besos_read_eso', 'provide_imp_module']

_applied = set()


def _once(function):
    def wrapper():
        if function.__name__ not in _applied:
            _applied.add(function.__name__)
            function()
    wrapper.__name__ = function.__name__
    wrapper.__doc__ = function.__doc__
    return wrapper


@_once
def provide_imp_module() -> None:
    """Python 3.12 removed the module imp, which pyDOE2 (used by besos for the sampling) imports."""
    if sys.version_info >= (3, 12) and 'imp' not in sys.modules:
        sys.modules['imp'] = types.ModuleType('imp')


@_once
def _patch_dask_tokenizer() -> None:
    """dask 2024 and later tokenize the callables given to DataFrame.apply, and besos' EvaluatorEP cannot be
    tokenized (it holds IDF objects); its id is a stable token during a Python process."""
    try:
        from besos.evaluator import EvaluatorEP
        from dask.tokenize import normalize_token
    except (ImportError, AttributeError):
        return

    @normalize_token.register(EvaluatorEP)
    def _tokenize_evaluator_ep(obj):
        return str(id(obj))


@_once
def _patch_platypus_operators() -> None:
    """platypus 1.4 made PlatypusConfig.default_variator a method, which besos.optimizer.get_operator indexes."""
    try:
        import besos.optimizer
        import platypus
    except (ImportError, AttributeError):
        return
    if not callable(platypus.config.PlatypusConfig.default_variator):
        return

    def get_operator(problem, mutation=False):
        if mutation:
            operators = [platypus.config.PlatypusConfig.default_mutator(t.__class__) for t in problem.types]
            return platypus.CompoundMutation(*operators)
        operators = [platypus.config.PlatypusConfig.default_variator(t.__class__) for t in problem.types]
        return platypus.CompoundOperator(*operators)

    besos.optimizer.get_operator = get_operator
    # The algorithms of besos capture get_operator when they are wrapped
    for name in ('GeneticAlgorithm', 'EvolutionaryStrategy', 'NSGAII', 'EpsMOEA', 'GDE3', 'SPEA2', 'MOEAD', 'NSGAIII',
                 'ParticleSwarm', 'OMOPSO', 'SMPSO', 'CMAES', 'IBEA', 'PAES', 'PESA2', 'EpsNSGAII'):
        if hasattr(platypus, name) and hasattr(besos.optimizer, name):
            setattr(besos.optimizer, name, besos.optimizer._alg_t(getattr(platypus, name)))


@_once
def _patch_freeze() -> None:
    """platypus 1.4 passes the variables of the solutions as FixedLengthArray objects, which
    besos.evaluator._freeze does not take as iterables when it hashes them for its cache."""
    try:
        import besos.evaluator
    except (ImportError, AttributeError):
        return
    original = besos.evaluator._freeze

    def freeze(value):
        if type(value).__name__ == 'FixedLengthArray':
            return tuple(freeze(value[i]) for i in range(len(value)))
        return original(value)

    besos.evaluator._freeze = freeze


@_once
def patch_besos_read_eso() -> None:
    """besos cannot read some ESO files (empty units such as those of the PMV, repeated variables...).
    With this patch, it warns and returns None instead of raising an error, so that the simulation goes on."""
    try:
        import besos.objectives
    except ImportError:
        return
    original = besos.objectives.read_eso

    def read_eso(out_dir: str, file_name: str = 'eplusout.eso') -> Optional[Any]:
        try:
            return original(out_dir, file_name)
        except Exception as error:  # noqa: BLE001 (any error of the parser)
            warnings.warn(f"BESOS failed to read the results file '{file_name}' due to error: {error}. The simulation "
                          f"completed, but results could not be parsed by BESOS. Execution continues without output "
                          f"data.")
            return None

    besos.objectives.read_eso = read_eso


def apply_besos_patches() -> None:
    """Apply all the patches."""
    provide_imp_module()
    _patch_dask_tokenizer()
    _patch_platypus_operators()
    _patch_freeze()
    patch_besos_read_eso()
