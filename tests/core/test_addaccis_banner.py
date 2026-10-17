"""Tests for the links printed by addAccis when it starts.

Before, the link to the full example pointed to jupyter_notebooks/full_example/full_example.html,
which does not exist in the documentation (404); the page is full_example_IBPSA.
"""
import builtins
import inspect
import re
from pathlib import Path

import pytest

import accim.sim.accim_Main as accim_Main
from accim.sim import accis, accis_single_idf, accis_single_idf_funcs

DOCS_SOURCE = Path(__file__).resolve().parents[2] / 'docs' / 'source'
READTHEDOCS = 'https://accim.readthedocs.io/en/master/'


class _ReachedAccimJob(Exception):
    """Raised by the accimJob stub: addAccis validated its arguments and started with the IDFs."""


def _stub_accim_job(*args, **kwargs):
    raise _ReachedAccimJob()


@pytest.mark.parametrize('module', [accis, accis_single_idf, accis_single_idf_funcs])
def test_banner_links_to_documentation_pages_that_exist(module):
    links = re.findall(re.escape(READTHEDOCS) + r'(jupyter_notebooks/[^\s\'"]+)\.html', inspect.getsource(module))

    assert 'jupyter_notebooks/full_example_IBPSA/full_example_IBPSA' in links
    for link in links:
        assert (DOCS_SOURCE / f'{link}.ipynb').exists(), link


def test_addaccis_prints_the_link_to_the_full_example(monkeypatch, capsys):
    monkeypatch.setattr(accim_Main, 'accimJob', _stub_accim_job)
    monkeypatch.setattr(builtins, 'input', lambda prompt='': pytest.fail(f'Unexpected prompt: {prompt}'))

    with pytest.raises(_ReachedAccimJob):
        accis.addAccis(
            idfs=['model.idf'], ScriptType='ex_ac', Output_type='standard', Output_freqs=['hourly'],
            Output_keep_existing=False, TempCtrl='temp',
        )

    out = capsys.readouterr().out
    assert READTHEDOCS + 'jupyter_notebooks/full_example_IBPSA/full_example_IBPSA.html' in out
    assert 'full_example/full_example.html' not in out
