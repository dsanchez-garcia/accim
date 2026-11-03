"""Tests for the executed notebooks that the documentation shows (docs/source/jupyter_notebooks).

Read the Docs does not run the notebooks: it shows the outputs saved in these copies, which
docs/prepare_howto_notebooks.py and docs/prepare_parametric_notebooks.py export. The export drops
the state of the widgets (metadata.widgets), without which nbsphinx shows their views as empty
outputs: the page of tutorial 10 showed two empty outputs, the progress bars of tqdm of its
robustness analysis.
"""
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PAGES = sorted((REPO / 'docs' / 'source' / 'jupyter_notebooks').rglob('*.ipynb'))
EXPORT_SCRIPT = REPO / 'docs' / 'prepare_parametric_notebooks.py'
WIDGET_VIEW = 'application/vnd.jupyter.widget-view+json'


def _outputs(page):
    notebook = json.loads(page.read_text(encoding='utf-8'))
    return [
        (index, output)
        for (index, cell) in enumerate(notebook['cells']) if cell['cell_type'] == 'code'
        for output in cell.get('outputs', [])
    ]


def _export_module():
    pytest.importorskip('numpy')
    spec = importlib.util.spec_from_file_location('prepare_parametric_notebooks', EXPORT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not PAGES, reason='needs the documentation of the repository')
@pytest.mark.parametrize('page', PAGES, ids=[p.relative_to(REPO / 'docs' / 'source').as_posix() for p in PAGES])
def test_the_pages_show_every_output(page):
    outputs = _outputs(page)
    widgets = [index for (index, output) in outputs if WIDGET_VIEW in output.get('data', {})]
    errors = [index for (index, output) in outputs if output.get('output_type') == 'error']
    empty = [
        index for (index, output) in outputs
        if output.get('output_type') == 'stream'
        and not (output['text'] if isinstance(output['text'], str) else ''.join(output['text'])).strip()
    ]

    assert not widgets, f'cells with views of widgets, shown as empty outputs: {widgets}'
    assert not errors, f'cells with errors: {errors}'
    assert not empty, f'cells with empty streams: {empty}'


@pytest.mark.skipif(not EXPORT_SCRIPT.exists(), reason='needs the scripts of the documentation')
def test_the_export_drops_the_views_of_widgets():
    export = _export_module()
    progress_bar = {
        'output_type': 'display_data', 'metadata': {},
        'data': {WIDGET_VIEW: {'model_id': 'a', 'version_major': 2, 'version_minor': 0},
                 'text/plain': 'Executing:   0%|          | 0/1 [00:00<?, ?row/s]'},
    }
    other_widget = {
        'output_type': 'display_data', 'metadata': {},
        'data': {WIDGET_VIEW: {'model_id': 'b', 'version_major': 2, 'version_minor': 0},
                 'text/html': '<b>Done</b>', 'text/plain': 'Done'},
    }
    log = {'output_type': 'stream', 'name': 'stdout', 'text': 'Running EnergyPlus...\n'}

    cleaned = export._clean_outputs([log, progress_bar, other_widget], replacements=[], max_width=1400)

    assert cleaned[0] == log
    assert len(cleaned) == 2
    assert cleaned[1]['data'] == {'text/html': '<b>Done</b>', 'text/plain': 'Done'}
