"""Tests for the links printed by AddAccis (addAccis in accim 0.x) when it starts.

Before, the link to the full example pointed to jupyter_notebooks/full_example/full_example.html,
which does not exist in the documentation (404); the page is full_example_IBPSA.
"""
import builtins
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import accim
from accim.sim import accis

DOCS_SOURCE = Path(__file__).resolve().parents[2] / 'docs' / 'source'
READTHEDOCS = 'https://accim.readthedocs.io/en/master/'
FULL_EXAMPLE = READTHEDOCS + 'jupyter_notebooks/full_example_IBPSA/full_example_IBPSA.html'


class _Reached(Exception):
    """Raised by the stubs: the function validated its arguments and started with the models."""


def _stub_load_idf(path, energyplus_version='auto'):
    raise _Reached()


def _stub_accim_model(*args, **kwargs):
    raise _Reached()


def test_banner_links_to_documentation_pages_that_exist():
    links = re.findall(re.escape(READTHEDOCS) + r'(jupyter_notebooks/[^\s\'"]+)\.html', accis.BANNER)

    assert 'jupyter_notebooks/full_example_IBPSA/full_example_IBPSA' in links
    for link in links:
        assert (DOCS_SOURCE / f'{link}.ipynb').exists(), link


def test_addaccis_prints_the_link_to_the_full_example(monkeypatch, capsys):
    monkeypatch.setattr(accis, 'load_idf', _stub_load_idf)
    monkeypatch.setattr(builtins, 'input', lambda prompt='': pytest.fail(f'Unexpected prompt: {prompt}'))

    with pytest.raises(_Reached):
        accis.AddAccis(
            idfs=['model.idf'], script_type='ex_ac', output_type='standard', output_freqs=['hourly'],
            output_keep_existing=False, temp_ctrl='temp',
        )

    out = capsys.readouterr().out
    assert FULL_EXAMPLE in out
    assert 'full_example/full_example.html' not in out
    assert f'v{accim.__version__}' in out


@pytest.mark.parametrize('verbose_mode', [True, False])
def test_add_accis_to_idf_prints_the_banner_in_verbose_mode(monkeypatch, capsys, verbose_mode):
    monkeypatch.setattr(accis, 'AccimModel', _stub_accim_model)

    with pytest.raises(_Reached):
        accis.add_accis_to_idf(SimpleNamespace(idd_version=(25, 1, 0)), script_type='ex_ac', output_type='standard',
                               output_freqs=['hourly'], temp_ctrl='temp', verbose_mode=verbose_mode)

    assert (FULL_EXAMPLE in capsys.readouterr().out) == verbose_mode
