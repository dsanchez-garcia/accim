# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The size of the results of :func:`accim.run.run_ep`, estimated before running the simulations.

The output files of each simulation are estimated from the outputs of its IDF, without simulating it
(:func:`accim.sim.results_size.estimate_simulation_size`), or, with ``simulate=True``, measured in a simulation of the
IDF with the first EPW, run as run_ep runs it, which takes as long as that simulation but gives the size of the files
of that IDF and EPW. The IDFs whose output objects are the same give results of the same size (as the output IDFs of a
model of AddAccis, which differ in the arguments of the ACCIS), so only one IDF of each group is read or simulated:
the groups are made from the text of the IDFs, since eppy takes about a second to read each one.
"""

import hashlib
import os
import platform
import re
import subprocess
import tempfile
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pandas as pd

from accim.energyplus import find_energyplus, read_idf_version
from accim.run.run import _idf_names, get_iddfile_from_idfs, simulation_name
from accim.sim.results_size import SIZE_COLUMNS, SimulationSize, estimate_simulation_size, format_size

__all__ = ['RESULTS_SIZE_COLUMNS', 'estimate_results_size']

#: The columns of the table of :func:`estimate_results_size`.
RESULTS_SIZE_COLUMNS = ['idf', 'simulations', 'source', 'from_idf'] + SIZE_COLUMNS + ['total_mb', 'total_kept_mb']
#: The objects that decide the output files of a simulation.
_OUTPUT_OBJECTS = re.compile(r'(output:|outputcontrol:|sizingperiod:)|(runperiod|timestep|simulationcontrol|'
                             r'energymanagementsystem:outputvariable)$')
#: The objects in which the output IDFs of a model of AddAccis differ (the arguments of the ACCIS and the EMS code of
#: their comfort standards), which do not change the output files.
_ARGUMENT_OBJECTS = ('energymanagementsystem:program', 'energymanagementsystem:subroutine')
#: The output files of a simulation of run_ep, by the end of their names, and the size they are part of.
_FILES = {'.eso': 'eso', '.csv': 'csv', '.mtr': 'mtr', 'Meter.csv': 'meter_csv', '.sql': 'sql'}


def _outputs_signature(path: str) -> str:
    """A text that is the same for the IDFs whose simulations write output files of the same size: the objects that
    decide them (outputs, run and sizing periods, timesteps...) and the number of objects of each type (which decide
    the keys of the outputs).

    The IDF is read as text (fields separated by commas, objects ended by semicolons, comments after '!'), which is
    much faster than reading it with eppy, only to compare it with the others.
    """
    text = re.sub(r'!.*', '', Path(path).read_bytes().decode('latin-1'))
    outputs = []
    counts: Dict[str, int] = {}
    for obj in text.split(';'):
        fields = [field.strip().lower() for field in obj.split(',')]
        if not fields[0] or fields[0] in _ARGUMENT_OBJECTS:
            continue
        counts[fields[0]] = counts.get(fields[0], 0) + 1
        if _OUTPUT_OBJECTS.match(fields[0]):
            outputs.append(','.join(fields))
    signature = '\n'.join(sorted(outputs)) + '\n' + repr(sorted(counts.items()))
    return hashlib.sha256(signature.encode('utf-8', 'replace')).hexdigest()


def _csv_values(path: Path) -> int:
    """The cells of a CSV file of EnergyPlus: its rows times its columns (without the date)."""
    with open(path, 'rb') as file:
        columns = file.readline().count(b',')
        rows = sum(1 for _ in file)
    return rows * columns


def _simulate(idf: str, epw: str, version: str) -> SimulationSize:
    """Run a simulation as run_ep runs it (EnergyPlus with ReadVarsESO and ExpandObjects, the output files named
    'IDF name[EPW name'), in a temporary folder, and measure its output files."""
    folder = find_energyplus(version)
    program = folder / ('energyplus.exe' if platform.system() == 'Windows' else 'energyplus')
    prefix = simulation_name(idf, epw)
    with tempfile.TemporaryDirectory(prefix='accim_results_size_') as work:
        # ReadVarsESO also writes files with fixed names in the working folder
        arguments = ['-w', os.path.abspath(epw), '-d', work, '-p', prefix, '-s', 'C', '-r', '-x', os.path.abspath(idf)]
        result = subprocess.run([str(program)] + arguments, cwd=work, capture_output=True, text=True, errors='replace')
        files = {path.name[len(prefix):]: path for path in Path(work).iterdir()
                 if path.is_file() and path.name.startswith(prefix)}
        if result.returncode != 0 or ('.eso' not in files and '.csv' not in files):
            errors = files['.err'].read_text(errors='replace') if '.err' in files else result.stdout
            raise RuntimeError(f'EnergyPlus ended with exit code {result.returncode}: {errors.strip()[-1500:]}')
        size = SimulationSize()
        for ending, path in files.items():
            kind = _FILES.get(ending, 'other')
            setattr(size, kind, getattr(size, kind) + path.stat().st_size)
        if '.csv' in files:
            size.csv_values = _csv_values(files['.csv'])
    return size


def _estimate(idf: str) -> SimulationSize:
    from accim.sim.accis import load_idf

    return estimate_simulation_size(load_idf(idf))


def _summary(groups: List[List[str]], sizes: Dict[str, SimulationSize], sources: Dict[str, str], epws: List[str],
             simulate: bool) -> str:
    method = (f'measured in a simulation of one IDF of each group of IDFs with the same outputs, with '
              f'{os.path.basename(epws[0])}' if simulate else
              'estimated from the outputs of the IDFs, without simulating them (simulate=True measures them in a '
              'simulation)')
    lines = [f'The size of the results of run_ep, {method}:']
    total = kept = memory = 0.0
    idfs = 0
    notes = []
    for members in groups:
        size = sizes[members[0]]
        name = os.path.basename(members[0])
        others = f' and {_plural(len(members) - 1, "other IDF")} with the same outputs' if len(members) > 1 else ''
        series = size.describe_series()
        failed = ' (estimated: the simulation failed)' if sources[members[0]] != 'simulation' and simulate else ''
        lines.append(f'    {name}{others}: {size.describe()} each simulation{f"; {series}" if series else ""}'
                     f'{failed}')
        notes += [f'{name}: {note}' for note in size.notes]
        total += size.total * len(members) * len(epws)
        kept += size.kept * len(members) * len(epws)
        memory += size.csv_memory * len(members) * len(epws)
        idfs += len(members)
    if epws:
        simulations = idfs * len(epws)
        lines.append(f'{_plural(idfs, "IDF")} and {_plural(len(epws), "EPW")}: {_plural(simulations, "simulation")}, '
                     f'{format_size(total)} ({format_size(kept)} after accim.run.remove_files(), which keeps the ESO '
                     f'and CSV files); {format_size(memory)} of memory to read the values of their CSV files (8 bytes '
                     f'each).')
    else:
        lines.append(f'{_plural(idfs, "IDF")} and no EPWs: run_ep runs each IDF with each EPW of the working folder.')
    lines += [f'Note, {note}.' for note in notes]
    return '\n'.join(lines)


def _plural(number: int, noun: str) -> str:
    return f'{number} {noun}{"" if number == 1 else "s"}'


def estimate_results_size(
    simulate: bool = False,
    only_accim_idfs: Optional[bool] = None,
    idfs: Optional[Sequence[str]] = None,
    epws: Optional[Sequence[str]] = None,
    processes: int = 2,
    verbose: bool = True,
) -> pd.DataFrame:
    """Estimate the size of the results of the simulations of :func:`accim.run.run_ep`: those of the IDFs and EPWs
    of the working folder, by default, before running them.

    Without simulation (the default), the size of the output files of each simulation (ESO, CSV, MTR, Meter.csv, SQL
    and the other files) is estimated from the outputs of its IDF (:func:`accim.sim.results_size.
    estimate_simulation_size`), in a few seconds: within 10 % for the results of more than 5 MB in the simulations
    of the calibration, and with notes for what it cannot count. With ``simulate=True``, it is measured in a
    simulation of the IDF with the first EPW, run as run_ep runs it, in a temporary folder: it takes as long as that
    simulation, but the size is that of the files. Only one IDF of each group of IDFs with the same output objects
    (and objects of each type) is read or simulated, since their results are of the same size: one for all the output
    IDFs of a model of AddAccis. The other EPWs give files of about the same size.

    :param simulate: False to estimate the sizes from the outputs of the IDFs; True to measure them in a simulation.
    :param only_accim_idfs: As in :func:`accim.run.run_ep`: True for the output IDFs of accim only (those with '[' in
        the name), False for all the IDFs of the working folder; None to ask. Not used with ``idfs``.
    :param idfs: The IDF files, instead of those of the working folder.
    :param epws: The EPW files, instead of those of the working folder.
    :param processes: The simulations that run at the same time (with ``simulate=True`` and several groups of IDFs).
    :param verbose: True to print the sizes.
    :return: A row for each IDF: the number of its simulations (one with each EPW), how its size was found, the
        size of each file of each simulation in MB (of 10^6 bytes: 'eso_mb', 'csv_mb', 'mtr_mb', 'meter_csv_mb',
        'sql_mb', 'other_mb'), that of the whole simulation ('simulation_mb'), that of the files that
        :func:`accim.run.remove_files` keeps ('kept_mb', the ESO and CSV files), the memory to read the values of its
        CSV file ('csv_memory_mb', 8 bytes each) and the size of all its simulations ('total_mb', 'total_kept_mb').
    :raises ValueError: If there are no IDFs, or no EPWs with ``simulate=True``, or the IDFs are of several or
        unsupported EnergyPlus versions (see :func:`accim.run.run.get_iddfile_from_idfs`).
    """
    idfs = list(idfs) if idfs is not None else _idf_names(only_accim_idfs)
    epws = list(epws) if epws is not None else sorted(x for x in os.listdir() if x.endswith('.epw'))
    if not idfs:
        raise ValueError('There are no IDFs whose results to estimate.')
    if simulate and not epws:
        raise ValueError('simulate=True needs an EPW to run the simulations, and there are none.')
    # The IDFs of one supported version, as run_ep needs, which eppy reads with its IDD
    get_iddfile_from_idfs(idfs)
    signatures: Dict[str, List[str]] = {}
    for idf in idfs:
        signatures.setdefault(_outputs_signature(idf), []).append(idf)
    groups = list(signatures.values())
    first_idfs = [members[0] for members in groups]
    sources: Dict[str, str] = {}
    if simulate:
        version = read_idf_version(first_idfs[0])
        if verbose:
            print(f'Simulating {len(first_idfs)} IDF(s) with {os.path.basename(epws[0])}, one of each group of IDFs '
                  f'with the same outputs, as run_ep runs them: this takes as long as these simulations.')

        def measure(idf: str) -> SimulationSize:
            try:
                size = _simulate(idf, epws[0], version)
                sources[idf] = 'simulation'
                return size
            except Exception as error:  # noqa: BLE001 (the estimate without simulation is used instead)
                warnings.warn(f'The simulation of {os.path.basename(idf)} failed, so the size of its results is '
                              f'estimated from its outputs: {error}', stacklevel=3)
                sources[idf] = 'estimate (the simulation failed)'
                return _estimate(idf)

        with ThreadPoolExecutor(max_workers=max(1, processes)) as pool:
            sizes = dict(zip(first_idfs, pool.map(measure, first_idfs)))
    else:
        sizes = {idf: _estimate(idf) for idf in first_idfs}
        sources = dict.fromkeys(first_idfs, 'estimate')

    rows = []
    for members in groups:
        size = sizes[members[0]]
        megabytes = size.megabytes()
        for idf in members:
            rows.append({'idf': os.path.basename(idf), 'simulations': len(epws), 'source': sources[members[0]],
                         'from_idf': os.path.basename(members[0]), **megabytes,
                         'total_mb': megabytes['simulation_mb'] * len(epws),
                         'total_kept_mb': megabytes['kept_mb'] * len(epws)})
    if verbose:
        print(_summary(groups, sizes, sources, epws, simulate))
    return pd.DataFrame(rows, columns=RESULTS_SIZE_COLUMNS)
