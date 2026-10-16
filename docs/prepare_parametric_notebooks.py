"""Run the parametric_and_optimisation example notebooks and export them for the documentation.

Read the Docs cannot run these notebooks (they need EnergyPlus), so the documentation shows
copies that were run beforehand, with their outputs, in
``docs/source/jupyter_notebooks/parametric_and_optimisation_examples``.

Usage, from the root of the repository::

    # 1. run the notebooks in a working folder (tutorials 00-10 in order, then wf1-wf5)
    python docs/prepare_parametric_notebooks.py run --run-dir <working folder>

    # 2. export the executed notebooks to the documentation
    python docs/prepare_parametric_notebooks.py export --executed-dir <working folder>

``run`` copies the notebooks and the sample IDF and EPW files to the working folder, runs each
notebook with nbconvert and writes ``<name>_executed.ipynb`` next to it. ``--only`` limits the
run to some notebooks (``--only wf1 06``); tutorials 09 and 10 read the results of 02 and 07, so
run those first. ``export`` takes the latest executed copy of each notebook (``--executed-dir``
can be repeated) and, before writing it to the documentation:

- replaces the absolute paths of the run (working folder, Python, temporary folder, home folder)
  with relative or generic ones;
- removes progress bars and shortens long logs;
- scales the figures down to ``--max-width`` pixels and, when it does not change them visibly,
  reduces them to 256 colours.

It refuses to export a notebook with errors, or one whose code differs from the notebook in
``accim/sample_files``.

The notebooks import the installed accim. To run them with another copy (for example the code
of a commit while the working copy has other changes), put its parent folder first in
``PYTHONPATH``; ``run`` records which copy it used, and ``export`` strips its path as well.
"""
import argparse
import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
DOCS_DIR = ROOT / 'docs' / 'source' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
INPUT_SUFFIXES = ('.idf', '.epw')
RUN_INFO = 'prepare_parametric_notebooks_run.json'
PROGRESS_BAR = re.compile(r'\d+%\|[^|]*\|')
PALETTE_MAX_ERROR = 8
LONG_STREAM_LINES = 100
KEEP_HEAD, KEEP_TAIL = 30, 15
PERSONAL_MARKERS = ('\\Users\\', '/Users/', 'AppData', 'OneDrive')


def _notebooks(only=None):
    tutorials = sorted(SOURCE_DIR.glob('[01][0-9]_*.ipynb'))
    workflows = sorted(SOURCE_DIR.glob('wf[0-9]_*.ipynb'))
    notebooks = tutorials + workflows
    if only:
        notebooks = [p for p in notebooks if any(p.name.startswith(prefix) for prefix in only)]
    return notebooks


def _cell_sources(nb):
    return [
        (cell['cell_type'], cell['source'] if isinstance(cell['source'], str) else ''.join(cell['source']))
        for cell in nb['cells']
    ]


def _accim_root():
    """Folder of the accim package that the notebooks import (it can be set with PYTHONPATH)."""
    import importlib.util

    spec = importlib.util.find_spec('accim')
    return str(Path(spec.origin).resolve().parents[1]) if spec and spec.origin else None


def run(run_dir, only=None, timeout=7200):
    """Run the notebooks in ``run_dir`` and report the errors of each one."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    # export strips this folder from the outputs (warnings show the paths of accim's modules).
    (run_dir / RUN_INFO).write_text(json.dumps({'accim_root': _accim_root()}, indent=1), encoding='utf-8')
    for path in SOURCE_DIR.iterdir():
        if path.suffix.lower() in INPUT_SUFFIXES:
            shutil.copy2(path, run_dir / path.name)
    failed = []
    for nb_path in _notebooks(only):
        shutil.copy2(nb_path, run_dir / nb_path.name)
        start = time.time()
        subprocess.run(
            [sys.executable, '-m', 'jupyter', 'nbconvert', '--to', 'notebook', '--execute', '--allow-errors',
             f'--ExecutePreprocessor.timeout={timeout}', '--output', f'{nb_path.stem}_executed.ipynb', nb_path.name],
            cwd=run_dir, capture_output=True, text=True, encoding='utf-8', errors='replace',
        )
        executed = run_dir / f'{nb_path.stem}_executed.ipynb'
        errors = _errors(json.loads(executed.read_text(encoding='utf-8'))) if executed.exists() else ['not executed']
        print(f'{nb_path.name}: {time.time() - start:.0f} s, errors: {len(errors)}', flush=True)
        for error in errors:
            print('   ', error, flush=True)
        if errors:
            failed.append(nb_path.name)
    return failed


def _errors(nb):
    return [
        (index, output.get('ename'), str(output.get('evalue', ''))[:200])
        for (index, cell) in enumerate(nb['cells'])
        for output in cell.get('outputs', [])
        if output.get('output_type') == 'error'
    ]


def _path_replacements(run_dirs):
    """Absolute paths of this machine and their replacements, longest first."""
    pairs = []
    for run_dir in run_dirs:
        pairs.append((str(Path(run_dir).resolve()) + os.sep, ''))
        pairs.append((str(Path(run_dir).resolve()), '.'))
        pairs.append((str(Path(run_dir).absolute()) + os.sep, ''))
        info_path = Path(run_dir) / RUN_INFO
        if info_path.exists():
            accim_root = json.loads(info_path.read_text(encoding='utf-8')).get('accim_root')
            if accim_root:
                pairs.append((accim_root + os.sep, ''))
    pairs.append((str(ROOT) + os.sep, ''))
    pairs.append((sysconfig.get_paths()['purelib'] + os.sep, 'site-packages' + os.sep))
    pairs.append((sys.base_prefix + os.sep, 'python' + os.sep))
    pairs.append((tempfile.gettempdir() + os.sep, 'tmp' + os.sep))
    pairs.append((str(Path.home()) + os.sep, '~' + os.sep))
    expanded = []
    for (old, new) in pairs:
        expanded.append((old, new))
        expanded.append((old.replace('\\', '/'), new.replace('\\', '/')))
        expanded.append((old.replace('\\', '\\\\'), new.replace('\\', '\\\\')))
    unique = {old: new for (old, new) in expanded if old}
    return sorted(unique.items(), key=lambda item: len(item[0]), reverse=True)


def _replace_paths(text, replacements):
    for (old, new) in replacements:
        text = text.replace(old, new)
    return text


def _clean_stream(text):
    lines = [line for line in text.replace('\r\n', '\n').split('\n') if not PROGRESS_BAR.search(line)]
    if len(lines) > LONG_STREAM_LINES:
        omitted = len(lines) - KEEP_HEAD - KEEP_TAIL
        lines = lines[:KEEP_HEAD] + [f'[... {omitted} lines not shown in the documentation ...]'] + lines[-KEEP_TAIL:]
    return '\n'.join(lines)


def _shrink_png(data, max_width):
    """Scale a PNG down to ``max_width`` and reduce it to 256 colours; keep it if that is not smaller."""
    from PIL import Image

    raw = base64.b64decode(data)
    image = Image.open(io.BytesIO(raw))
    if image.width > max_width:
        height = round(image.height * max_width / image.width)
        image = image.resize((max_width, height), Image.LANCZOS)
    # Transparent areas go white: dropping the alpha channel alone could leave them black.
    rgba = image.convert('RGBA')
    flat = Image.new('RGB', rgba.size, (255, 255, 255))
    flat.paste(rgba, mask=rgba.getchannel('A'))
    # Scaling smooths the edges with many intermediate colours, which compress badly; a palette
    # of 256 colours keeps most plots sharp and makes the files much smaller. Figures with wide
    # colour gradients (heatmaps, semi-transparent points) would show bands, so they keep their
    # colours when the palette changes more than 1 % of the pixels by over PALETTE_MAX_ERROR.
    mediancut = getattr(getattr(Image, 'Quantize', None), 'MEDIANCUT', 0)
    no_dither = getattr(getattr(Image, 'Dither', None), 'NONE', 0)
    paletted = flat.quantize(colors=256, method=mediancut, dither=no_dither)
    error = np.abs(np.asarray(flat, dtype=np.int16) - np.asarray(paletted.convert('RGB'), dtype=np.int16)).max(axis=2)
    image = paletted if np.percentile(error, 99) <= PALETTE_MAX_ERROR else flat
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    if len(buffer.getvalue()) >= len(raw):
        return data
    return base64.b64encode(buffer.getvalue()).decode('ascii') + '\n'


def _clean_outputs(outputs, replacements, max_width):
    cleaned = []
    for output in outputs:
        kind = output.get('output_type')
        if kind == 'stream':
            text = output['text'] if isinstance(output['text'], str) else ''.join(output['text'])
            text = _clean_stream(_replace_paths(text, replacements))
            if text.strip():
                cleaned.append({**output, 'text': text})
        elif kind in ('display_data', 'execute_result'):
            data = dict(output.get('data', {}))
            for (mime, value) in list(data.items()):
                if mime == 'image/png':
                    data[mime] = _shrink_png(value if isinstance(value, str) else ''.join(value), max_width)
                elif mime.startswith('text/'):
                    value = value if isinstance(value, str) else ''.join(value)
                    data[mime] = _replace_paths(value, replacements)
            output = {**output, 'data': data}
            if 'image/png' in data:
                output['metadata'] = {}
            cleaned.append(output)
        else:
            cleaned.append(output)
    return cleaned


def export(executed_dirs, only=None, max_width=1400):
    """Write sanitized copies of the executed notebooks to the documentation."""
    executed_dirs = [Path(d) for d in executed_dirs]
    replacements = _path_replacements(executed_dirs)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    problems = []
    for nb_path in _notebooks(only):
        candidates = [d / f'{nb_path.stem}_executed.ipynb' for d in executed_dirs]
        candidates = [c for c in candidates if c.exists()]
        if not candidates:
            problems.append(f'{nb_path.name}: no executed copy')
            continue
        executed_path = max(candidates, key=lambda c: c.stat().st_mtime)
        executed = json.loads(executed_path.read_text(encoding='utf-8'))
        source = json.loads(nb_path.read_text(encoding='utf-8'))
        if _cell_sources(executed) != _cell_sources(source):
            problems.append(f'{nb_path.name}: the executed copy differs from the notebook; run it again')
            continue
        if _errors(executed):
            problems.append(f'{nb_path.name}: the executed copy has errors')
            continue
        for cell in executed['cells']:
            cell['source'] = cell['source'] if isinstance(cell['source'], str) else ''.join(cell['source'])
            if cell['cell_type'] == 'code':
                cell['outputs'] = _clean_outputs(cell.get('outputs', []), replacements, max_width)
        executed.get('metadata', {}).pop('widgets', None)
        text = json.dumps(executed, indent=1, ensure_ascii=False) + '\n'
        markers = PERSONAL_MARKERS + (str(Path.home()), Path.home().name)
        left = [marker for marker in markers if marker in text]
        if left:
            problems.append(f'{nb_path.name}: personal paths left in the outputs: {left}')
            continue
        target = DOCS_DIR / nb_path.name
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
    run_parser.add_argument('--only', nargs='*', help='name prefixes of the notebooks to run (e.g. 05 wf1)')
    run_parser.add_argument('--timeout', type=int, default=7200, help='timeout per cell, in seconds')
    export_parser = sub.add_parser('export', help='export executed notebooks to the documentation')
    export_parser.add_argument('--executed-dir', action='append', required=True)
    export_parser.add_argument('--only', nargs='*', help='name prefixes of the notebooks to export')
    export_parser.add_argument('--max-width', type=int, default=1400, help='maximum width of the figures, in pixels')
    args = parser.parse_args(argv)
    if args.command == 'run':
        return 1 if run(args.run_dir, only=args.only, timeout=args.timeout) else 0
    return 1 if export(args.executed_dir, only=args.only, max_width=args.max_width) else 0


if __name__ == '__main__':
    sys.exit(main())
