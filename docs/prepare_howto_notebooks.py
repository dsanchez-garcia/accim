"""Run the notebooks of the How-to Guides and export them for the documentation.

The notebooks of the How-to Guides (``using_addAccis``, ``using_rename_epw_files``, ``using_runEp``,
``using_Table``, ``full_example_IBPSA``, ``research_paper_case_study`` and ``using_apmv_setpoints``)
are kept, without outputs, in ``accim/sample_files/jupyter_notebooks/<folder>``, next to their IDF,
EPW and CSV files. That is the copy to edit. Read the Docs cannot run them (they need EnergyPlus),
so the documentation shows copies that were run beforehand, in
``docs/source/jupyter_notebooks/<folder>``.

Usage, from the root of the repository::

    # 1. run the notebooks in a working folder
    python docs/prepare_howto_notebooks.py run --run-dir <working folder>

    # 2. export the executed notebooks to the documentation
    python docs/prepare_howto_notebooks.py export --executed-dir <working folder>

``run`` copies the folder of each notebook to the working folder, so the sample files are not
modified, runs the notebook there and writes ``<name>_executed.ipynb`` in the working folder.
``--only`` limits the run to some notebooks (``--only using_runEp using_Table``). Use a short path
for the working folder (``D:\\runs``, for instance): EnergyPlus fails when the path of an output
file is longer than 260 characters, and the names of the output files of accim are long.

Some functions of accim ask questions: ``addAccis()`` when arguments are missing,
``rename_epw_files()``, and the figures of ``Table`` when the rows and columns are not renamed
with arguments. ``run`` answers them with the answers in ``ANSWERS``, which are the ones the
notebooks explain, and prints each question followed by its answer, as if it was typed. If a
notebook asks more questions than there are answers, or fewer, ``run`` reports it.
``rename_epw_files()`` also needs access to OpenStreetMap, and the package geopy.

``export`` takes the latest executed copy of each notebook (``--executed-dir`` can be repeated)
and writes it to the documentation, cleaned as in ``prepare_parametric_notebooks.py``: the paths
of this computer are replaced with relative or generic ones, progress bars are removed, long logs
are shortened and figures are scaled down. It refuses to export a notebook with errors, or one
whose code differs from the notebook in ``accim/sample_files``.

The notebooks import the installed accim. To run them with another copy, put its parent folder
first in ``PYTHONPATH``.
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_parametric_notebooks as parametric  # noqa: E402  (same cleaning of the outputs)

ROOT = parametric.ROOT
SAMPLES_DIR = ROOT / 'accim' / 'sample_files' / 'jupyter_notebooks'
DOCS_DIR = ROOT / 'docs' / 'source' / 'jupyter_notebooks'

# (folder in accim/sample_files/jupyter_notebooks, notebook, folder in docs/source/jupyter_notebooks)
NOTEBOOKS = [
    ('addAccis', 'using_addAccis', 'addAccis'),
    ('rename_epw_files', 'using_rename_epw_files', 'rename_epw_files'),
    ('runEp', 'using_runEp', 'runEp'),
    ('Table', 'using_Table', 'Table'),
    ('full_example_IBPSA', 'full_example_IBPSA', 'full_example_IBPSA'),
    ('research_paper_case_study_v0-7-3', 'research_paper_case_study', 'research_paper_case_study'),
    ('example_apmv_setpoints_paper', 'using_apmv_setpoints', 'example_apmv_setpoints_paper'),
]

# Answers to the questions of each notebook: {notebook: {text that identifies the cell: [answers]}}.
# An empty string means hitting enter.
_ADDACCIS_SHORT = [
    # first stage
    'vrf_mm', 'temperature difference', 'false', 'standard', 'hourly runperiod', 'false', 'auto',
    'temperature',
    # second stage; each answer is followed by the confirmation ('' accepts it)
    '1 14', '',  # ComfStand
    '1 2 3 80 90', '',  # CAT
    '0 0.1 0.2 0.3 0.4 0.5 1 1.1 1.2 1.3 1.4 1.5 2 3', '',  # ComfMod
    '100', '',  # SetpointAcc
    '0', '',  # CATcoolOffset
    '0', '',  # CATheatOffset
    '01/11', '',  # CoolSeasonStart
    '01/03', '',  # CoolSeasonEnd
    '2', '',  # HVACmode
    '2', '',  # VentCtrl
    '20', '',  # MaxTempDiffVOF
    '1', '',  # MinTempDiffVOF
    '0.2', '',  # MultiplierVOF
    '', '',  # VSToffset
    '', '',  # MinOToffset
    '', '',  # MaxWindSpeed
    '', '',  # ASTtol_start
    '', '',  # ASTtol_end_input
    '', '',  # ASTtol_steps
    'y',  # Do you still want to run ACCIS?
]
_CUSTOM_OUTPUTS = ('Zone Operative Temperature;Adaptive Cooling Setpoint Temperature_No Tolerance;'
                   'Adaptive Heating Setpoint Temperature_No Tolerance')
ANSWERS = {
    'using_addAccis': {
        'accis.addAccis()': _ADDACCIS_SHORT,
        "Output_type='custom'": ['keep', _CUSTOM_OUTPUTS, 'keep', _CUSTOM_OUTPUTS],
    },
    'using_rename_epw_files': {
        'rename_epw_files(\n    confirm_deletion=False,\n)': ['0 1', 'Aberdeen', 'London', '', 'y'],
        'rename_city_dict=rename_city_dict': ['', '', 'y'],
    },
    'using_Table': {
        "'WIP_scatterplot_RMOT'": ['n'],
        "'WIP_scatterplot_adap_vs_stat'": ['n', 'n'],
    },
    'full_example_IBPSA': {
        'rename_epw_files(': ['', ''],
    },
    'research_paper_case_study': {
        'rename_epw_files(': ['', ''],
    },
}

# Flushing before each question puts it in an output of its own, apart from a long log printed
# before it, which export may shorten.
_INPUT_PREFIX = (
    "def _scripted_input(prompt='', _answers={answers}):\n"
    "    answer = _answers.pop(0)\n"
    "    __import__('sys').stdout.flush()\n"
    "    print(f'{{prompt}}{{answer}}', flush=True)\n"
    "    return answer\n"
    "__import__('builtins').input = _scripted_input\n"
)


def _selected(only=None):
    if not only:
        return NOTEBOOKS
    return [entry for entry in NOTEBOOKS if any(entry[0].startswith(p) or entry[1].startswith(p) for p in only)]


def _client_class():
    from nbclient import NotebookClient
    from nbclient.util import ensure_async

    class ScriptedInputClient(NotebookClient):
        """Runs a notebook answering the questions of ``input()`` with scripted answers.

        The cell is run with a few lines before its code that replace ``input()`` with a function
        that takes the next answer; the notebook keeps the original code. The kernel restores
        ``input()`` at the end of the cell.
        """

        def __init__(self, nb, answers, **kwargs):
            super().__init__(nb, **kwargs)
            self.answers = answers
            self.problems = []

        async def async_execute_cell(self, cell, cell_index, execution_count=None, store_history=True):
            matches = [a for (key, a) in self.answers.items() if cell.cell_type == 'code' and key in cell.source]
            if not matches:
                return await super().async_execute_cell(cell, cell_index, execution_count, store_history)
            if len(matches) > 1:
                self.problems.append(f'cell {cell_index}: more than one set of answers matches it')
            source = cell.source
            cell.source = _INPUT_PREFIX.format(answers=json.dumps(matches[0])) + source
            try:
                cell = await super().async_execute_cell(cell, cell_index, execution_count, store_history)
            finally:
                cell.source = source
            left = await self._answers_left()
            if left:
                self.problems.append(f'cell {cell_index}: {left} answers were not used')
            return cell

        async def _answers_left(self):
            msg_id = await ensure_async(self.kc.execute(
                '', silent=True, store_history=False,
                user_expressions={'left': 'len(_scripted_input.__defaults__[1])'},
            ))
            reply = await self.async_wait_for_reply(msg_id)
            expression = (reply or {}).get('content', {}).get('user_expressions', {}).get('left', {})
            return int(expression.get('data', {}).get('text/plain', '0'))

    return ScriptedInputClient


def run(run_dir, only=None, timeout=7200):
    """Run the notebooks in copies of their folders within ``run_dir`` and report the errors."""
    import nbformat

    run_dir = Path(run_dir).absolute()
    run_dir.mkdir(parents=True, exist_ok=True)
    # export strips this folder from the outputs (warnings show the paths of accim's modules).
    (run_dir / parametric.RUN_INFO).write_text(
        json.dumps({'accim_root': parametric._accim_root()}, indent=1), encoding='utf-8'
    )
    client_class = _client_class()
    failed = []
    for (folder, name, _docs_folder) in _selected(only):
        work_dir = run_dir / folder
        if work_dir.exists():
            shutil.rmtree(work_dir)
        shutil.copytree(SAMPLES_DIR / folder, work_dir,
                        ignore=shutil.ignore_patterns('__pycache__', '.ipynb_checkpoints'))
        nb = nbformat.read(work_dir / f'{name}.ipynb', as_version=4)
        client = client_class(nb, ANSWERS.get(name, {}), timeout=timeout, kernel_name='python3',
                              allow_errors=True, resources={'metadata': {'path': str(work_dir)}})
        start = time.time()
        try:
            client.execute()
        except Exception as error:  # the kernel died or a cell timed out
            client.problems.append(f'{type(error).__name__}: {str(error)[:300]}')
        nbformat.write(nb, run_dir / f'{name}_executed.ipynb')
        problems = [f'cell {i}: {ename}: {evalue}' for (i, ename, evalue) in parametric._errors(nb)]
        problems += client.problems
        print(f'{name}: {time.time() - start:.0f} s, problems: {len(problems)}', flush=True)
        for problem in problems:
            print('   ', problem, flush=True)
        if problems:
            failed.append(name)
    return failed


def _merge_streams(outputs):
    """Join consecutive outputs of the same stream while the result is not a long log.

    Each question answered in ``run`` ends a stream output, so a cell with questions has many
    short outputs. They are joined up to the length from which ``export`` shortens logs, so the
    questions and answers are kept, and long logs are still shortened.
    """
    def text(output):
        return output['text'] if isinstance(output['text'], str) else ''.join(output['text'])

    merged = []
    for output in outputs:
        previous = merged[-1] if merged else None
        if (output.get('output_type') == 'stream' and previous is not None
                and previous.get('output_type') == 'stream' and previous.get('name') == output.get('name')
                and (text(previous) + text(output)).count('\n') <= parametric.LONG_STREAM_LINES):
            merged[-1] = {**previous, 'text': text(previous) + text(output)}
        else:
            merged.append(output)
    return merged


def export(executed_dirs, only=None, max_width=1400):
    """Write cleaned copies of the executed notebooks to the documentation."""
    executed_dirs = [Path(d).absolute() for d in executed_dirs]
    # The notebooks run in a subfolder of the working folder, which must also be removed from the paths.
    work_dirs = [d / folder for d in executed_dirs for (folder, _name, _docs) in NOTEBOOKS]
    replacements = parametric._path_replacements(executed_dirs + work_dirs)
    problems = []
    for (folder, name, docs_folder) in _selected(only):
        source_path = SAMPLES_DIR / folder / f'{name}.ipynb'
        candidates = [d / f'{name}_executed.ipynb' for d in executed_dirs]
        candidates = [c for c in candidates if c.exists()]
        if not candidates:
            problems.append(f'{name}: no executed copy')
            continue
        executed_path = max(candidates, key=lambda c: c.stat().st_mtime)
        executed = json.loads(executed_path.read_text(encoding='utf-8'))
        source = json.loads(source_path.read_text(encoding='utf-8'))
        if parametric._cell_sources(executed) != parametric._cell_sources(source):
            problems.append(f'{name}: the executed copy differs from the notebook; run it again')
            continue
        if parametric._errors(executed):
            problems.append(f'{name}: the executed copy has errors')
            continue
        for cell in executed['cells']:
            cell['source'] = cell['source'] if isinstance(cell['source'], str) else ''.join(cell['source'])
            if cell['cell_type'] == 'code':
                outputs = _merge_streams(cell.get('outputs', []))
                cell['outputs'] = parametric._clean_outputs(outputs, replacements, max_width)
        executed.get('metadata', {}).pop('widgets', None)
        text = json.dumps(executed, indent=1, ensure_ascii=False) + '\n'
        markers = parametric.PERSONAL_MARKERS + (str(Path.home()), Path.home().name)
        left = [marker for marker in markers if marker in text]
        if left:
            problems.append(f'{name}: personal paths left in the outputs: {left}')
            continue
        target = DOCS_DIR / docs_folder / f'{name}.ipynb'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        print(f'{target.relative_to(ROOT)}: {len(text.encode("utf-8")) / 1e6:.2f} MB (from {executed_path})')
    for problem in problems:
        print('NOT EXPORTED:', problem)
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    run_parser = sub.add_parser('run', help='run the notebooks in a working folder')
    run_parser.add_argument('--run-dir', required=True)
    run_parser.add_argument('--only', nargs='*', help='names of the notebooks or their folders (or their beginning)')
    run_parser.add_argument('--timeout', type=int, default=7200, help='timeout per cell, in seconds')
    export_parser = sub.add_parser('export', help='export executed notebooks to the documentation')
    export_parser.add_argument('--executed-dir', action='append', required=True)
    export_parser.add_argument('--only', nargs='*', help='names of the notebooks or their folders (or their beginning)')
    export_parser.add_argument('--max-width', type=int, default=1400, help='maximum width of the figures, in pixels')
    args = parser.parse_args(argv)
    if args.command == 'run':
        return 1 if run(args.run_dir, only=args.only, timeout=args.timeout) else 0
    return 1 if export(args.executed_dir, only=args.only, max_width=args.max_width) else 0


if __name__ == '__main__':
    sys.exit(main())
