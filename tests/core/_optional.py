"""The optional dependencies of the tests of tests/core: a test that needs one is skipped without it, never failed,
as rule 1 of the instructions of the repository asks for besos and the versions of EnergyPlus
(``notes/COPILOT_SIGUIENTE_SESION.md`` §2)."""
import importlib

import pytest


def pythermalcomfort_models():
    """The module ``pythermalcomfort.models``, or skip the test that needs it (with the reason).

    pythermalcomfort imports without numba, which compiles the functions of its models when ``pythermalcomfort.models``
    is imported, so ``pytest.importorskip('pythermalcomfort')`` does not tell whether the models (the SET of
    ``set_tmp`` and the ATHB of ``pmv_athb``, which the hooks of :mod:`accim.sim.comfort_hooks` use) can be used: on
    the server of session 3 of the review of accim 1.2.0, Windows Smart App Control blocked the DLLs of numba
    (2026-11-11 and 2026-11-12), the import of the models raised an ImportError, and the tests that took the package
    for the models failed. That ImportError is not a ModuleNotFoundError, which ``pytest.importorskip`` skips only
    with ``exc_type=ImportError`` from pytest 9.1 on (pytest 8.2 to 9.0 warn), and the tests take pytest 8.0 or
    later, without ``exc_type``.
    """
    try:
        return importlib.import_module('pythermalcomfort.models')
    except ImportError as error:
        pytest.skip(f'needs pythermalcomfort.models (pythermalcomfort, with numba, which compiles its models): '
                    f'{error}')
