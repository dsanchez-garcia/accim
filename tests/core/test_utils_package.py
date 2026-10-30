"""Tests for the package accim.utils, which was a single module before accim 1.0.0.

Its functions are in submodules that are imported when a function is used, so that accim.sim does not
import besos (which takes long to import) to read the occupants of the models. All the functions can still
be imported from accim.utils.
"""
import subprocess
import sys
from pathlib import Path

import pytest

import accim.utils
from accim.utils import get_idd_path_from_ep_version

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('name', accim.utils.__all__)
def test_every_name_can_be_imported_from_accim_utils(name):
    value = getattr(accim.utils, name)

    module = sys.modules[f'accim.utils.{accim.utils._SUBMODULES[name]}']
    assert getattr(module, name) is value


def test_functions_of_besos_that_accim_0x_imported():
    from accim.utils import get_building

    assert get_building.__module__ == 'besos.eppy_funcs'


def test_unknown_names():
    with pytest.raises(AttributeError, match="has no attribute 'nothing'"):
        accim.utils.nothing
    with pytest.raises(ImportError):
        from accim.utils import nothing  # noqa: F401


def test_accim_sim_does_not_import_besos():
    script = ('import sys, accim.sim.accis, accim.utils.people; '
              'print(sorted(m for m in ("besos", "geomeppy", "matplotlib") if m in sys.modules))')
    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, cwd=REPO, timeout=120)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '[]'


def test_get_idd_path_from_ep_version_accepts_the_old_argument_name():
    assert get_idd_path_from_ep_version('25.1') == 'C:/EnergyPlusV25-1-0/Energy+.idd'
    with pytest.warns(DeprecationWarning, match='EnergyPlus_version -> energyplus_version'):
        assert get_idd_path_from_ep_version(EnergyPlus_version='26.2') == 'C:/EnergyPlusV26-2-0/Energy+.idd'
