"""Compare the EnergyPlus executable with a resident Python API worker.

Developer experiment, not an ACCIM backend. Uses only the standard library and
pyenergyplus from the selected EnergyPlus installation (do not pip-install it).
Inputs are never edited; every invocation requires a NEW output directory.
Relative external model resources must be staged separately if required.
"""

import argparse
import csv
import hashlib
import importlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from contextlib import contextmanager
from itertools import zip_longest
from pathlib import Path


@contextmanager
def working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def load_api(home):
    """Load exactly one installation per process, keeping DLL state local."""
    sys.path.insert(0, str(home))
    try:
        module = importlib.import_module('pyenergyplus.api')
    finally:
        sys.path.pop(0)
    if Path(module.__file__).resolve().parents[1] != home.resolve():
        raise RuntimeError('Another pyenergyplus installation is already loaded; use a fresh process.')
    return module.EnergyPlusAPI()


def compare_csv(reference, actual):
    """Check the complete time series, allowing only numerical roundoff."""
    rows = 0
    numeric_cells = 0
    with reference.open(newline='', encoding='utf-8-sig') as left_file, actual.open(
        newline='', encoding='utf-8-sig'
    ) as right_file:
        left = csv.reader(left_file)
        right = csv.reader(right_file)
        left_header = next(left, None)
        right_header = next(right, None)
        if not left_header or left_header != right_header:
            raise ValueError(f'CSV headers differ or are missing: {actual}')
        for row_number, pair in enumerate(zip_longest(left, right), start=2):
            expected, observed = pair
            if expected is None or observed is None or len(expected) != len(observed):
                raise ValueError(f'CSV shape differs at row {row_number}: {actual}')
            if len(expected) != len(left_header):
                raise ValueError(f'Malformed CSV row {row_number}: {actual}')
            for col, (a, b) in enumerate(zip(expected, observed), start=1):
                try:
                    x, y = float(a), float(b)
                except ValueError:
                    equal = a.strip() == b.strip()
                else:
                    equal = math.isfinite(x) and math.isfinite(y) and math.isclose(
                        x, y, rel_tol=1e-10, abs_tol=1e-9
                    )
                    numeric_cells += 1
                if not equal:
                    raise ValueError(f'CSV values differ at row {row_number}, column {col}: {actual}')
            rows += 1
    if not rows or not numeric_cells:
        raise ValueError(f'No numerical time series to compare: {actual}')
    return {'rows': rows, 'numeric_cells': numeric_cells}


def compare_outputs(reference, actual):
    """Compare both variable and meter CSVs when emitted, not tabular timestamps."""
    names = ('eplusout.csv', 'eplusmtr.csv')
    expected = {name for name in names if (reference / name).is_file()}
    observed = {name for name in names if (actual / name).is_file()}
    if 'eplusout.csv' not in expected or expected != observed:
        raise ValueError(f'Missing or inconsistent time-series CSV files: {actual}')
    return {name: compare_csv(reference / name, actual / name) for name in sorted(expected)}


def run_case(backend, api, executable, args, directory):
    """Measure engine invocation including state lifecycle or child-process wait."""
    with working_directory(directory):
        started = time.perf_counter()
        if backend == 'cli':
            completed = subprocess.run(
                [str(executable), *args], stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False,
            )
            returncode = completed.returncode
        elif backend == 'api':
            state = api.state_manager.new_state()
            try:
                api.runtime.set_console_output_status(state, False)
                returncode = api.runtime.run_energyplus(state, args)
            finally:
                api.state_manager.delete_state(state)
        else:
            raise ValueError(f'Unknown backend: {backend}')
        elapsed = time.perf_counter() - started
    end = directory / 'eplusout.end'
    if returncode != 0 or not end.is_file() or 'EnergyPlus Completed Successfully' not in end.read_text(
        encoding='utf-8', errors='replace'
    ):
        raise RuntimeError(f'{backend} failed (exit {returncode}); inspect {directory / "eplusout.err"}')
    return elapsed


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def benchmark(home, idf, epw, output_dir, repeats=5, warmups=1, engine_flags=()):
    """Alternate paired trials; keep artifacts and separate one-time API setup."""
    if repeats < 1 or warmups < 0:
        raise ValueError('repeats must be positive and warmups must be nonnegative')
    home, idf, epw, output_dir = [Path(p).absolute() for p in (home, idf, epw, output_dir)]
    executable = home / ('energyplus.exe' if os.name == 'nt' else 'energyplus')
    for path in (executable, home / 'pyenergyplus' / 'api.py', idf, epw):
        if not path.is_file():
            raise FileNotFoundError(path)
    # Refuse reuse: never delete or mix in another run's artifacts.
    output_dir.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    api = load_api(home)
    setup_seconds = time.perf_counter() - started
    records = []
    reference = None
    comparisons = None
    for trial in range(warmups + repeats):
        backends = ('cli', 'api') if trial % 2 == 0 else ('api', 'cli')
        for backend in backends:
            directory = output_dir / f'{trial:02d}-{backend}'
            directory.mkdir()
            args = ['-d', str(directory), '-w', str(epw), '-r', *engine_flags, str(idf)]
            elapsed = run_case(backend, api, executable, args, directory)
            if reference is None:
                reference = directory
            comparisons = compare_outputs(reference, directory)
            records.append({
                'trial': trial, 'backend': backend, 'warmup': trial < warmups,
                'seconds': elapsed, 'output_dir': str(directory),
            })
    summaries = {}
    for backend in ('cli', 'api'):
        durations = [r['seconds'] for r in records if r['backend'] == backend and not r['warmup']]
        summaries[backend] = {
            'median_seconds': statistics.median(durations),
            'min_seconds': min(durations), 'max_seconds': max(durations),
        }
    result = {
        'scope': 'Serial resident-worker engine calls; not full BESOS/ACCIM throughput or Python callbacks.',
        'platform': platform.platform(), 'python': sys.version, 'energyplus_home': str(home),
        'energyplus_version': subprocess.check_output([str(executable), '--version'], text=True).strip(),
        'idf': str(idf), 'idf_sha256': fingerprint(idf), 'epw': str(epw), 'epw_sha256': fingerprint(epw),
        'engine_flags': ['-r', *engine_flags], 'repeats': repeats, 'warmups': warmups,
        'api_setup_seconds': setup_seconds, 'summary': summaries,
        'api_to_cli_median_ratio': summaries['api']['median_seconds'] / summaries['cli']['median_seconds'],
        'csv_parity_passed': True, 'compared_time_series': comparisons, 'trials': records,
        'limitations': [
            'One model, machine and EnergyPlus version per invocation; no concurrency or memory benchmark.',
            'API import/DLL setup is reported separately; CLI process startup remains in every trial.',
            'Fresh API state for every run; no reset-state, PythonPlugin, live callbacks or engine replacement.',
            'CSV equivalence does not prove arbitrary models or all other artifacts are equivalent.',
            'No change to ACCIM public APIs, EMS control, BESOS readers, checkpoints or storage policies.',
        ],
    }
    (output_dir / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--energyplus-home', required=True, type=Path)
    parser.add_argument('--idf', required=True, type=Path)
    parser.add_argument('--epw', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path, help='Must not already exist.')
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--warmups', type=int, default=1)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--annual', action='store_true')
    mode.add_argument('--design-day', action='store_true')
    parser.add_argument('--expandobjects', action='store_true')
    args = parser.parse_args()
    flags = []
    if args.annual:
        flags.append('-a')
    if args.design_day:
        flags.append('-D')
    if args.expandobjects:
        flags.append('-x')
    result = benchmark(
        args.energyplus_home, args.idf, args.epw, args.output_dir,
        repeats=args.repeats, warmups=args.warmups, engine_flags=flags,
    )
    print(json.dumps({key: result[key] for key in (
        'energyplus_version', 'summary', 'api_setup_seconds',
        'api_to_cli_median_ratio', 'csv_parity_passed', 'compared_time_series',
    )}, indent=2))


if __name__ == '__main__':
    main()

