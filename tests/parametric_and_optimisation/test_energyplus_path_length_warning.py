"""Tests for the EnergyPlus MAX_PATH pre-flight warning."""

import os
import warnings

import pytest

from accim.parametric_and_optimisation.main import SimulationBase

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows MAX_PATH check only')


def _collect(out_dir):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        SimulationBase._warn_if_out_dir_too_long_for_energyplus(out_dir, 'run_optimisation')
    return [w for w in caught if 'MAX_PATH' in str(w.message)]


def test_short_out_dir_does_not_warn():
    assert _collect(r'C:\results\exp_4_4') == []


def test_long_out_dir_warns():
    # Length of the failing OneDrive path reported by the user (257 chars).
    long_dir = 'D:\\' + 'x' * 254
    found = _collect(long_dir)
    assert len(found) == 1
    assert 'run_optimisation' in str(found[0].message)


def test_threshold_boundary():
    limit = SimulationBase._ENERGYPLUS_MAX_PATH - SimulationBase._ENERGYPLUS_OUT_SUFFIX_LEN - 1
    ok_dir = 'C:\\' + 'a' * (limit - 3)
    bad_dir = ok_dir + 'b'
    assert len(os.path.abspath(ok_dir)) == limit
    assert _collect(ok_dir) == []
    assert len(_collect(bad_dir)) == 1

