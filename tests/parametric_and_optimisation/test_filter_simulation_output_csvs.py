"""Tests for SimulationBase.filter_simulation_output_csvs (no EnergyPlus runs)."""
import os
from pathlib import Path

import pandas as pd
import pytest

from accim.parametric_and_optimisation.main import (
    OptimisationSimulation,
    ParametricSimulation,
)

OP_LIVING = 'LIVING:Zone Operative Temperature [C](Hourly)'
OP_BEDROOM = 'BEDROOM:Zone Operative Temperature [C](Hourly)'
RAOT = 'LIVING:Running Average Outdoor Air Temperature [C](Hourly)'
HVAC = 'Electricity:HVAC [J](Hourly)'
ORIGINAL_COLUMNS = [' Date/Time ', OP_LIVING, OP_BEDROOM, RAOT, HVAC]


def _write_eplus_csv(sim_dir, n_rows=5, time_header=' Date/Time ', crlf=True):
    """Write a small EnergyPlus-like CSV with raw text values."""
    sim_dir.mkdir(parents=True, exist_ok=True)
    header = [time_header, OP_LIVING, OP_BEDROOM, RAOT, HVAC]
    lines = [','.join(header)]
    for i in range(n_rows):
        lines.append(','.join([
            f' 01/01  {i + 1:02d}:00:00',
            f'{21.0 + i:.6f}',  # trailing zeros must be preserved verbatim
            f'{20.5 + i}',
            '1.2E-03',
            '0.0',
        ]))
    newline = '\r\n' if crlf else '\n'
    path = sim_dir / 'eplusout.csv'
    path.write_bytes((newline.join(lines) + newline).encode('utf-8'))
    return path


def _read_raw(path):
    return path.read_bytes().decode('utf-8')


def _parametric_session(tmp_path, n_sims=2):
    rows = []
    for i in range(n_sims):
        sim_dir = tmp_path / 'BESOS_Output' / f'SIM{i}'
        _write_eplus_csv(sim_dir)
        rows.append({'CustAST_m': 0.1 * i, 'epw': 'Seville', 'output_dir': str(sim_dir)})
    sim = ParametricSimulation(parameters_type=None)
    sim.outputs_param_simulation = pd.DataFrame(rows)
    sim.last_run_type = 'parametric'
    return sim


def test_parametric_session_keep_columns_partial_match(tmp_path):
    sim = _parametric_session(tmp_path)
    report = sim.filter_simulation_output_csvs(keep_columns=['zone operative temperature'], verbose=False)

    assert len(report) == 2
    assert list(report['status']) == ['written', 'written']
    for _, rec in report.iterrows():
        dest = rec['destination_path']
        assert os.path.basename(dest) == 'eplusout_filtered.csv'
        assert os.path.dirname(dest) == os.path.dirname(rec['source_path'])
        df = pd.read_csv(dest, dtype=str, keep_default_na=False)
        assert list(df.columns) == [' Date/Time ', OP_LIVING, OP_BEDROOM]
        assert rec['rows'] == 5
        assert rec['original_columns'] == 5
        assert rec['kept_columns'] == 3
        assert rec['destination_size_bytes'] < rec['source_size_bytes']
        assert rec['reduction_pct'] > 0
        # originals untouched
        assert os.path.exists(rec['source_path'])
    # session paths are not modified
    assert all('filtered' not in p for p in sim.outputs_param_simulation['output_dir'])


def test_values_rows_and_line_endings_preserved_verbatim(tmp_path):
    src = _write_eplus_csv(tmp_path / 'a', crlf=True)
    sim = ParametricSimulation(parameters_type=None)
    report = sim.filter_simulation_output_csvs(keep_columns=[OP_LIVING, RAOT], csv_paths=[src], verbose=False)

    dest = report.loc[0, 'destination_path']
    raw = _read_raw(Path(dest))
    lines = raw.split('\r\n')
    assert lines[0] == f' Date/Time ,{OP_LIVING},{RAOT}'
    assert lines[1] == ' 01/01  01:00:00,21.000000,1.2E-03'
    assert lines[5] == ' 01/01  05:00:00,25.000000,1.2E-03'
    assert '\n' not in raw.replace('\r\n', '')


def test_drop_columns_exact_and_time_column_protected(tmp_path):
    src = _write_eplus_csv(tmp_path / 'a', time_header='date/time')
    sim = ParametricSimulation(parameters_type=None)
    report = sim.filter_simulation_output_csvs(
        drop_columns=[HVAC, 'Date/Time', 'Running Average'],
        csv_paths=str(src),
        verbose=False,
    )
    rec = report.iloc[0]
    assert rec['status'] == 'written'
    assert rec['unmatched_patterns'] == []
    df = pd.read_csv(rec['destination_path'], dtype=str)
    assert list(df.columns) == ['date/time', OP_LIVING, OP_BEDROOM]


def test_chunked_processing_matches_full_read(tmp_path):
    src_a = _write_eplus_csv(tmp_path / 'a', n_rows=23)
    sim = ParametricSimulation(parameters_type=None)
    full = sim.filter_simulation_output_csvs(
        keep_columns=['Operative'], csv_paths=[src_a], output_dir=tmp_path / 'full', verbose=False)
    chunked = sim.filter_simulation_output_csvs(
        keep_columns=['Operative'], csv_paths=[src_a], output_dir=tmp_path / 'chunked', chunksize=4, verbose=False)
    assert chunked.loc[0, 'rows'] == 23
    with open(full.loc[0, 'destination_path'], 'rb') as f1, open(chunked.loc[0, 'destination_path'], 'rb') as f2:
        assert f1.read() == f2.read()


def test_duplicate_paths_processed_once(tmp_path):
    src = _write_eplus_csv(tmp_path / 'a')
    alt = os.path.join(str(tmp_path), 'a', '..', 'a', 'eplusout.csv')
    sim = ParametricSimulation(parameters_type=None)
    report = sim.filter_simulation_output_csvs(keep_columns='Operative', csv_paths=[src, str(src), alt], verbose=False)
    assert len(report) == 1
    assert report.loc[0, 'status'] == 'written'


def test_output_dir_avoids_name_collisions(tmp_path):
    src_1 = _write_eplus_csv(tmp_path / 'run1' / 'SIM')
    src_2 = _write_eplus_csv(tmp_path / 'run2' / 'SIM')  # same parent name and file name
    src_3 = _write_eplus_csv(tmp_path / 'run1' / 'OTHER')
    out = tmp_path / 'filtered'
    sim = ParametricSimulation(parameters_type=None)
    report = sim.filter_simulation_output_csvs(
        keep_columns='Operative', csv_paths=[src_1, src_2, src_3], output_dir=out, verbose=False)
    names = [os.path.basename(p) for p in report['destination_path']]
    assert names == ['SIM_eplusout_filtered.csv', 'SIM_eplusout_filtered_2.csv', 'OTHER_eplusout_filtered.csv']
    assert all(report['status'] == 'written')
    assert len(set(report['destination_path'])) == 3


def test_existing_destination_not_overwritten_unless_requested(tmp_path):
    src = _write_eplus_csv(tmp_path / 'a')
    existing = tmp_path / 'a' / 'eplusout_filtered.csv'
    existing.write_text('sentinel', encoding='utf-8')
    sim = ParametricSimulation(parameters_type=None)

    report = sim.filter_simulation_output_csvs(keep_columns='Operative', csv_paths=[src], verbose=False)
    assert report.loc[0, 'status'] == 'skipped_existing'
    assert existing.read_text(encoding='utf-8') == 'sentinel'

    report = sim.filter_simulation_output_csvs(keep_columns='Operative', csv_paths=[src], overwrite=True, verbose=False)
    assert report.loc[0, 'status'] == 'written'
    assert existing.read_text(encoding='utf-8').startswith(' Date/Time ,')
    assert [p.name for p in (tmp_path / 'a').iterdir() if p.suffix == '.tmp'] == []


def test_missing_files_reported_and_processing_continues(tmp_path):
    good = _write_eplus_csv(tmp_path / 'good')
    missing = tmp_path / 'gone' / 'eplusout.csv'
    sim = ParametricSimulation(parameters_type=None)
    report = sim.filter_simulation_output_csvs(keep_columns='Operative', csv_paths=[missing, good], verbose=False)
    assert list(report['status']) == ['missing', 'written']
    assert not (tmp_path / 'gone').exists()


def test_unmatched_patterns_warn_and_no_outputs_writes_nothing(tmp_path):
    src = _write_eplus_csv(tmp_path / 'a')
    sim = ParametricSimulation(parameters_type=None)

    with pytest.warns(UserWarning, match='Not In File'):
        report = sim.filter_simulation_output_csvs(
            keep_columns=['Operative', 'Not In File'], csv_paths=[src], verbose=False)
    assert report.loc[0, 'status'] == 'written'
    assert report.loc[0, 'unmatched_patterns'] == ['Not In File']

    with pytest.warns(UserWarning, match='Not In File'):
        report = sim.filter_simulation_output_csvs(
            keep_columns=['Date/Time', 'Not In File'], csv_paths=[src], output_dir=tmp_path / 'out', verbose=False)
    assert report.loc[0, 'status'] == 'no_outputs'
    assert report.loc[0, 'destination_path'] is None
    assert not (tmp_path / 'out').exists() or list((tmp_path / 'out').iterdir()) == []


def test_optimisation_session_includes_all_evaluations(tmp_path):
    pareto = _write_eplus_csv(tmp_path / 'opt' / 'P1')
    dominated = _write_eplus_csv(tmp_path / 'opt' / 'D1')
    opt = OptimisationSimulation(parameters_type=None)
    opt._set_optimisation_outputs(pd.DataFrame([
        {'x': 1.0, 'epw': 'Seville', 'pareto-optimal': True, 'simulation_output_csv_path': str(pareto)},
        {'x': 2.0, 'epw': 'Seville', 'pareto-optimal': False, 'simulation_output_csv_path': str(dominated)},
        {'x': 3.0, 'epw': 'Seville', 'pareto-optimal': False, 'simulation_output_csv_path': pd.NA},
    ]))
    opt.last_run_type = 'optimisation'

    report = opt.filter_simulation_output_csvs(drop_columns=['Electricity:HVAC'], verbose=False)

    statuses = dict(zip(report['source_path'].fillna('<none>'), report['status']))
    assert statuses[os.path.abspath(str(pareto))] == 'written'
    assert statuses[os.path.abspath(str(dominated))] == 'written'
    assert statuses['<none>'] == 'unresolved'
    assert len(report) == 3  # cached path lists did not duplicate entries
    df = pd.read_csv(report.loc[report['status'] == 'written', 'destination_path'].iloc[0])
    assert HVAC not in df.columns and len(df.columns) == 4


@pytest.mark.parametrize('cls', [ParametricSimulation, OptimisationSimulation])
@pytest.mark.parametrize('kwargs, exc', [
    ({}, ValueError),
    ({'keep_columns': 'a', 'drop_columns': 'b'}, ValueError),
    ({'keep_columns': []}, ValueError),
    ({'keep_columns': ['ok', '']}, ValueError),
    ({'keep_columns': 'a', 'chunksize': 0}, ValueError),
    ({'keep_columns': 'a', 'chunksize': True}, ValueError),
    ({'keep_columns': 'a', 'suffix': ''}, ValueError),
    ({'keep_columns': 'a', 'suffix': 'x/y'}, ValueError),
    ({'keep_columns': 'a', 'encoding': 'no-such-codec'}, ValueError),
    ({'keep_columns': 'a', 'csv_paths': []}, ValueError),
])
def test_invalid_global_arguments_raise_before_writing(tmp_path, cls, kwargs, exc):
    src = _write_eplus_csv(tmp_path / 'a')
    kwargs = dict(kwargs)
    kwargs.setdefault('csv_paths', [src])
    sim = cls(parameters_type=None)
    with pytest.raises(exc):
        sim.filter_simulation_output_csvs(verbose=False, **kwargs)
    assert sorted(p.name for p in (tmp_path / 'a').iterdir()) == ['eplusout.csv']


@pytest.mark.parametrize('cls', [ParametricSimulation, OptimisationSimulation])
def test_no_session_results_without_csv_paths_raises(cls):
    sim = cls(parameters_type=None)
    with pytest.raises(ValueError, match='csv_paths'):
        sim.filter_simulation_output_csvs(keep_columns='Operative', verbose=False)


def test_output_dir_pointing_to_file_raises(tmp_path):
    src = _write_eplus_csv(tmp_path / 'a')
    not_a_dir = tmp_path / 'file.txt'
    not_a_dir.write_text('x', encoding='utf-8')
    sim = OptimisationSimulation(parameters_type=None)
    with pytest.raises(ValueError, match='not a directory'):
        sim.filter_simulation_output_csvs(keep_columns='Operative', csv_paths=[src], output_dir=not_a_dir, verbose=False)
