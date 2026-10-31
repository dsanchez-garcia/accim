"""Tests for accim.run.run.make_eplaunch_options, the options of eppy's runIDFs to run an IDF like EP-Launch.

Ported from the tests of the branch refactor/sim-v1 (tests/run/test_run.py): eppy finds the EnergyPlus
installation from the version of the IDF in the format 'X-X-X', so a version with two numbers is padded with a 0.
The names of the output files ('output_prefix' and 'output_directory') are tested in test_energyplus_api.py.
"""
from types import SimpleNamespace

import pytest

from accim.run import run


def _idf(version):
    return SimpleNamespace(idfname='model.idf', idfobjects={'version': [SimpleNamespace(Version_Identifier=version)]})


@pytest.mark.parametrize('version, ep_version', [('9.6.0', '9-6-0'), ('23.1', '23-1-0'), ('26.2', '26-2-0')])
def test_make_eplaunch_options_pads_the_version(version, ep_version):
    assert run.make_eplaunch_options(_idf(version), 'Seville.epw')['ep_version'] == ep_version


def test_make_eplaunch_options_runs_like_ep_launch():
    options = run.make_eplaunch_options(_idf('25.1'), 'Seville.epw')

    assert (options['output_suffix'], options['readvars'], options['expandobjects']) == ('C', True, True)
