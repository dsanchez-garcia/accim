"""Simulate a model with the EMS of EnergyPlus and with the Python API backend of accim, and compare the results.

accim runs the EMS programs of its output IDFs either with the EMS of EnergyPlus (``run_ep(backend='ems')``, the
command line of EnergyPlus) or in Python, with the Python API of EnergyPlus (``backend='api'``,
:mod:`accim.sim.energyplus_api`). Both must give the same results; this script checks it for one model::

    python tools/compare_backends.py MODEL.idf WEATHER.epw OUT_DIR [--days 6] [--start 7/1] [--tolerance 0]

With ``--days``, the run period is shortened to that many days from ``--start`` (month/day) in a copy of the model.
The hourly CSV files (``OUT_DIR/ems/run.csv`` and ``OUT_DIR/api/run.csv``) are compared column by column; the exit
code is 0 when no column differs by more than ``--tolerance``. The API backend needs EnergyPlus 24.2 or later,
installed where accim finds it. Run it with ``PYTHONPATH`` set to the folder of the accim to check (the root of
the repository, for instance).
"""
import argparse
import datetime
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

from accim.energyplus import find_energyplus, read_idf_version
from accim.sim.energyplus_api import parse_idf, render_idf, run_simulation


def shorten_run_period(idf, out, start, days):
    """A copy of the model in ``out`` whose RunPeriod objects cover ``days`` days from ``start`` (month/day)."""
    objects = parse_idf(Path(idf).read_bytes().decode('latin-1'))
    month, day = (int(x) for x in start.split('/'))
    begin = datetime.date(2001, month, day)
    end = begin + datetime.timedelta(days=days - 1)
    for obj in objects:
        if obj.key == 'RUNPERIOD':
            obj.fields.extend([''] * (7 - len(obj.fields)))
            # Name, Begin Month, Begin Day of Month, Begin Year, End Month, End Day of Month, End Year
            obj.fields[1:7] = [str(begin.month), str(begin.day), '', str(end.month), str(end.day), '']
    path = Path(out) / 'model.idf'
    path.write_bytes(render_idf(objects).encode('latin-1'))
    return path


def run_ems(idf, epw, out):
    """Run the model with the command line of EnergyPlus (EMS backend); return the time it took."""
    folder = find_energyplus(read_idf_version(idf))
    executable = folder / ('energyplus.exe' if sys.platform == 'win32' else 'energyplus')
    start = time.time()
    result = subprocess.run([str(executable), '-d', str(out), '-p', 'run', '-s', 'C', '-r', '-x', '-w', str(epw),
                             str(idf)], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-2000:], result.stderr[-2000:])
        raise SystemExit(f'EnergyPlus stopped (exit code {result.returncode}); see {out}')
    return time.time() - start


def compare_csv(a, b, tolerance=0.0):
    """Print the differences between two CSV files of EnergyPlus; return the number of columns that differ."""
    da, db = pd.read_csv(a), pd.read_csv(b)
    print(f'rows: EMS {len(da)}, API {len(db)}; columns: EMS {len(da.columns)}, API {len(db.columns)}')
    common = [c for c in da.columns if c in db.columns]
    only_ems = [c for c in da.columns if c not in db.columns]
    only_api = [c for c in db.columns if c not in da.columns]
    if only_ems or only_api:
        print('columns only with the EMS:', only_ems[:10])
        print('columns only with the API:', only_api[:10])
    if len(da) != len(db):
        print('the number of rows differs')
        return max(len(common), 1)
    worst = []
    for column in common:
        if column == 'Date/Time':
            if not (da[column] == db[column]).all():
                print('Date/Time differs')
                worst.append((float('inf'), column))
            continue
        x = pd.to_numeric(da[column], errors='coerce')
        y = pd.to_numeric(db[column], errors='coerce')
        diff = (x - y).abs().max()
        if diff > tolerance or (x.isna() != y.isna()).any():
            worst.append((diff, column))
    worst.sort(reverse=True)
    print(f'{len(common) - 1 - len(worst)} columns the same, {len(worst)} different (tolerance {tolerance})')
    for diff, column in worst[:15]:
        print(f'   {diff:.6g}  {column}')
    return len(worst) + len(only_ems) + len(only_api)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('idf')
    parser.add_argument('epw')
    parser.add_argument('out')
    parser.add_argument('--days', type=int, default=0, help='simulate this many days only (0: the run period)')
    parser.add_argument('--start', default='7/1', help='first day with --days, as month/day')
    parser.add_argument('--tolerance', type=float, default=0.0, help='largest absolute difference accepted')
    args = parser.parse_args(argv)
    out = Path(args.out)
    (out / 'ems').mkdir(parents=True, exist_ok=True)
    (out / 'api').mkdir(parents=True, exist_ok=True)
    idf = Path(args.idf)
    if args.days:
        idf = shorten_run_period(idf, out, args.start, args.days)
    epw = Path(args.epw)
    t_ems = run_ems(idf, epw, out / 'ems')
    start = time.time()
    result = run_simulation(idf, epw, out / 'api', output_prefix='run')
    t_api = time.time() - start
    print(f'EMS {t_ems:.1f} s, API {t_api:.1f} s, {result.environments} environments')
    return 1 if compare_csv(out / 'ems' / 'run.csv', out / 'api' / 'run.csv', args.tolerance) else 0


if __name__ == '__main__':
    sys.exit(main())
