"""Resilience tests for hourly post-processing when simulation CSV files are missing.

The hourly methods (get_hourly_df, get_daily_df, get_monthly_df, get_runperiod_df and
get_hourly_df_columns of ParametricSimulation and OptimisationSimulation, and
compute_hourly_indicators / get_hourly_series_by_epw of the hourly plotting mixin) read the
eplusout.csv file of each simulation, located with the 'simulation_output_csv_path',
'simulation_directory' or 'output_dir' column of the results. Storage policies can remove those
files: keep_dirs=False and sim_files_extensions / sim_files_policy in
run_parametric_simulation(), and keep_sim_files='non-dominated' / 'none' (which delete the
folders and clear their paths) and the same extension policy in run_optimisation(). These
tests pin that:

- run_parametric_simulation() warns before a cleanup policy removes the CSV files, and the
  files are then really removed;
- the path resolver explains which storage options remove the files of a simulation, and the
  CSV reader names the missing file;
- when no selected simulation has its CSV file, every hourly method raises an error that lists
  the missing files (or why their paths are unknown) and the storage options of the run, and
  stores no table (before, a generic "No hourly columns were detected" message, a message about
  arguments that do not exist, or "AttributeError: 'float' object has no attribute 'strip'");
- when only some files are missing, the simulations whose CSV is available are expanded with
  their own values and a warning names the others (before, they were left out silently).
"""
import datetime
import os
import re
import shutil
import warnings

import numpy as np
import pandas as pd
import pytest

import accim.parametric_and_optimisation.main as main_module
from accim.parametric_and_optimisation.file_cleanup import (
    normalize_sim_file_cleanup_options,
    prune_simulation_output_files,
)
from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation, SimulationBase
from accim.parametric_and_optimisation.utils import expand_to_hourly_dataframe, identify_hourly_columns

HOURS = 48
ENERGY = 'Heating:Electricity [J](Hourly)'
TEMPERATURE = 'BLOCK1:ZONE1:Zone Operative Temperature [C](Hourly)'
RETRIEVAL_METHODS = ['get_hourly_df', 'get_daily_df', 'get_monthly_df', 'get_runperiod_df']
STORAGE_DIAGNOSTIC = (
    "CSV path cannot be resolved for this simulation. If you used keep_sim_files='non-dominated' "
    'and this is a dominated simulation, the files were deleted to save space. Also check whether '
    'sim_files_extensions/sim_files_policy removed this file extension.'
)
STORAGE_OPTIONS = ('keep_dirs', 'keep_sim_files', 'sim_files_extensions/sim_files_policy')


class _DummyProblem:
    def __init__(self, inputs, outputs):
        self._inputs = list(inputs)
        self._outputs = list(outputs)
        self.minimize_outputs = [True] * len(self._outputs)

    def names(self, typ):
        if typ == 'inputs':
            return list(self._inputs)
        if typ == 'outputs':
            return list(self._outputs)
        if typ == 'constraints':
            return []
        raise KeyError(typ)


def _energyplus_timestamps(hours):
    labels = []
    for index in range(hours):
        (day_index, hour) = divmod(index, 24)
        date = datetime.date(2023, 1, 1) + datetime.timedelta(days=day_index)
        labels.append(f' {date.month:02d}/{date.day:02d}  {hour + 1:02d}:00:00')
    return labels


def _hourly_energy(scale):
    return [scale * 3.6e6 * (hour + 1) for hour in range(HOURS)]


def _write_simulation_files(sim_dir, scale):
    os.makedirs(sim_dir, exist_ok=True)
    pd.DataFrame({
        'Date/Time': _energyplus_timestamps(HOURS),
        ENERGY: _hourly_energy(scale),
        TEMPERATURE: [20.0 + scale] * HOURS,
    }).to_csv(os.path.join(sim_dir, 'eplusout.csv'), index=False)
    for file_name in ('eplusout.eso', 'eplusout.err'):
        with open(os.path.join(sim_dir, file_name), 'w', encoding='utf-8') as handle:
            handle.write('dummy\n')


def _fake_worker(idf_path, epw, epwname, idf_basename, out_dir, problem_names_inputs,
                 problem_names_outputs, output_specs, add_output_specs, add_output_names,
                 row_dict, keep_dirs, keep_input, sim_files_extensions=None,
                 sim_files_policy='keep', additional_params=None):
    sim_dir = os.path.join(out_dir, f"sim_{epwname}_{int(row_dict['x'])}")
    _write_simulation_files(sim_dir, scale=float(row_dict['x']))
    result = {
        problem_names_outputs[0]: sum(_hourly_energy(float(row_dict['x']))),
        'epw': epwname,
        'idf': idf_basename,
    }
    if keep_input:
        result.update(row_dict)
    if keep_dirs:
        result['output_dir'] = sim_dir
    return result


def _run_parametric(monkeypatch, tmp_path, **run_kwargs):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _fake_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    sim = ParametricSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.problem = _DummyProblem(inputs=['x'], outputs=['Heating:Electricity'])
    sim.run_parametric_simulation(
        df=pd.DataFrame({'x': [1, 2]}),
        out_dir=str(tmp_path / 'param'),
        processes=1,
        keep_input=True,
        **run_kwargs,
    )
    return sim


def _run_parametric_with_csv_cleanup(monkeypatch, tmp_path):
    with pytest.warns(UserWarning, match=r"may remove '\.csv' files during run_parametric_simulation"):
        return _run_parametric(
            monkeypatch, tmp_path, keep_dirs=True, sim_files_extensions=['eso', 'err'], sim_files_policy='keep',
        )


def _missing_parametric_csv_paths(sim):
    return [os.path.join(sim_dir, 'eplusout.csv') for sim_dir in sim.outputs_param_simulation['output_dir']]


def _optimisation_session(tmp_path, keep_sim_files='all'):
    rows = []
    for (x, pareto_optimal) in [(1.0, True), (2.0, False), (3.0, True)]:
        sim_dir = str(tmp_path / 'optim' / f'sim_{int(x)}')
        _write_simulation_files(sim_dir, scale=x)
        rows.append({
            'x': x,
            'Heating:Electricity': sum(_hourly_energy(x)),
            'epw': 'Seville',
            'idf': 'office_a',
            'pareto-optimal': pareto_optimal,
            'simulation_directory': sim_dir,
            'simulation_output_csv_path': os.path.join(sim_dir, 'eplusout.csv'),
        })
    results = pd.DataFrame(rows)
    # Same storage policy as run_optimisation(): delete the folders and clear their paths.
    if keep_sim_files == 'non-dominated':
        for (idx, row) in results[~results['pareto-optimal']].iterrows():
            shutil.rmtree(row['simulation_directory'])
            results.at[idx, 'simulation_directory'] = pd.NA
            results.at[idx, 'simulation_output_csv_path'] = pd.NA
    elif keep_sim_files == 'none':
        shutil.rmtree(str(tmp_path / 'optim'))
        results['simulation_directory'] = pd.NA
        results['simulation_output_csv_path'] = pd.NA
    sim = OptimisationSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.problem = _DummyProblem(inputs=['x'], outputs=['Heating:Electricity'])
    sim.outputs_optimisation = results
    sim.last_run_type = 'optimisation'
    return sim


def _optimisation_session_after_csv_cleanup(tmp_path):
    sim = _optimisation_session(tmp_path)
    (extensions, policy) = normalize_sim_file_cleanup_options(sim_files_extensions=['eso'], sim_files_policy='keep')
    stats = SimulationBase._cleanup_simulation_output_directories(
        sim_dirs=sim.outputs_optimisation['simulation_directory'].tolist(),
        sim_files_extensions=extensions,
        sim_files_policy=policy,
    )
    assert stats['removed_files'] == 6  # eplusout.csv and eplusout.err of 3 simulations
    return sim


# ----------------------------------------------------------------------------- storage policies

@pytest.mark.parametrize(
    ('extensions', 'policy'),
    [(['eso', 'err'], 'keep'), (['csv'], 'delete')],
    ids=['keep_eso_and_err', 'delete_csv'],
)
def test_parametric_run_warns_before_its_cleanup_policy_removes_the_csv_files(
        monkeypatch, tmp_path, extensions, policy):
    with pytest.warns(UserWarning) as record:
        sim = _run_parametric(
            monkeypatch, tmp_path, keep_dirs=True, sim_files_extensions=extensions, sim_files_policy=policy,
        )

    messages = [str(warning.message) for warning in record]
    assert any(
        "may remove '.csv' files during run_parametric_simulation" in message
        and 'get_hourly_df/get_monthly_df' in message
        for message in messages
    )
    for sim_dir in sim.outputs_param_simulation['output_dir']:
        assert sorted(os.listdir(sim_dir)) == ['eplusout.err', 'eplusout.eso']


@pytest.mark.parametrize(
    'row',
    [
        {'simulation_directory': pd.NA, 'simulation_output_csv_path': pd.NA},
        {'simulation_directory': None, 'simulation_output_csv_path': None},
        {'epw': 'Seville'},
    ],
    ids=['paths_cleared_by_keep_sim_files', 'evaluation_without_folder', 'no_path_columns'],
)
def test_path_resolver_explains_which_storage_options_remove_the_files(row):
    with pytest.raises(ValueError) as exc_info:
        SimulationBase._resolve_simulation_file_path(row=pd.Series(row, dtype=object), file_source='csv')

    assert STORAGE_DIAGNOSTIC in str(exc_info.value)


def test_csv_reader_names_the_file_removed_by_the_cleanup_policy(monkeypatch, tmp_path):
    sim = _run_parametric_with_csv_cleanup(monkeypatch, tmp_path)
    missing = _missing_parametric_csv_paths(sim)[0]

    with pytest.raises(FileNotFoundError) as exc_info:
        sim._extract_hourly_outputs_from_file(row=sim.outputs_param_simulation.iloc[0], file_source='csv')

    assert str(exc_info.value) == f'Simulation output file not found: {missing}'


# ----------------------------------------------------------------------------- parametric hourly methods

ALL_FILES_MISSING = 'The CSV files of the selected simulations cannot be read, so there are no hourly values to expand'
SOME_FILES_MISSING = 'Simulations left out of the hourly table because their CSV file cannot be read'


def _assert_names_the_missing_files_and_the_storage_options(message, missing_paths):
    for path in missing_paths:
        assert f'Simulation output file not found: {path}' in message
    for option in STORAGE_OPTIONS:
        assert option in message


@pytest.mark.parametrize('method', RETRIEVAL_METHODS)
def test_parametric_hourly_methods_name_the_csv_files_removed_by_the_cleanup_policy(monkeypatch, tmp_path, method):
    sim = _run_parametric_with_csv_cleanup(monkeypatch, tmp_path)

    with pytest.raises(ValueError) as exc_info:
        getattr(sim, method)(skip_confirmation=True)

    message = str(exc_info.value)
    assert message.startswith(ALL_FILES_MISSING)
    _assert_names_the_missing_files_and_the_storage_options(message, _missing_parametric_csv_paths(sim))
    assert sim.outputs_param_simulation_hourly is None
    assert sim.outputs_param_simulation_daily is None
    assert sim.outputs_param_simulation_monthly is None
    assert sim.outputs_param_simulation_runperiod is None


def test_parametric_hourly_table_without_kept_simulation_folders_points_to_keep_dirs(monkeypatch, tmp_path):
    sim = _run_parametric(monkeypatch, tmp_path, keep_dirs=False)
    assert 'output_dir' not in sim.outputs_param_simulation.columns

    with pytest.raises(ValueError) as exc_info:
        sim.get_hourly_df(skip_confirmation=True)

    message = str(exc_info.value)
    assert message.startswith(ALL_FILES_MISSING)
    assert f'rows 0, 1: {STORAGE_DIAGNOSTIC}' in message
    assert 'keep_dirs (run_parametric_simulation)' in message
    assert sim.outputs_param_simulation_hourly is None


def test_parametric_hourly_table_keeps_the_simulations_whose_csv_is_available_and_names_the_others(
        monkeypatch, tmp_path):
    sim = _run_parametric(monkeypatch, tmp_path, keep_dirs=True)
    missing = _missing_parametric_csv_paths(sim)[0]
    # For example a folder cleaned afterwards with another extension policy.
    prune_simulation_output_files(sim.outputs_param_simulation['output_dir'].iloc[0], ['csv'], 'delete')

    with pytest.warns(UserWarning, match=re.escape(f'row 0: Simulation output file not found: {missing}')) as record:
        hourly = sim.get_hourly_df(skip_confirmation=True)

    message = next(str(warning.message) for warning in record if SOME_FILES_MISSING in str(warning.message))
    assert '(1 of 2)' in message
    assert all(option in message for option in STORAGE_OPTIONS)
    assert hourly['x'].unique().tolist() == [2]
    assert hourly['hour'].tolist() == list(range(1, HOURS + 1))
    assert hourly[ENERGY].tolist() == pytest.approx(_hourly_energy(2.0))
    assert hourly[TEMPERATURE].tolist() == pytest.approx([22.0] * HOURS)
    # The table of the remaining simulations can be aggregated (its 'datetime' column used to become
    # an object column with pandas >= 3).
    assert pd.api.types.is_datetime64_any_dtype(hourly['datetime'])
    daily = sim.get_daily_df()
    assert daily['day'].astype(str).tolist() == ['2023-01-01', '2023-01-02']
    assert daily[ENERGY].tolist() == pytest.approx([sum(_hourly_energy(2.0)[:24]), sum(_hourly_energy(2.0)[24:])])


# ----------------------------------------------------------------------------- optimisation hourly methods

def test_optimisation_pareto_hourly_table_is_built_when_dominated_files_were_not_kept(tmp_path):
    sim = _optimisation_session(tmp_path, keep_sim_files='non-dominated')

    with warnings.catch_warnings():
        warnings.simplefilter('error', UserWarning)
        hourly = sim.get_hourly_df(skip_confirmation=True)

    assert sorted(hourly['x'].unique().tolist()) == [1.0, 3.0]
    for x in (1.0, 3.0):
        rows = hourly[hourly['x'] == x].sort_values('hour')
        assert rows[ENERGY].tolist() == pytest.approx(_hourly_energy(x))


def test_optimisation_hourly_table_of_every_simulation_names_the_dominated_ones_without_files(tmp_path):
    sim = _optimisation_session(tmp_path, keep_sim_files='non-dominated')

    with pytest.warns(UserWarning, match=re.escape(f'row 1: {STORAGE_DIAGNOSTIC}')) as record:
        hourly = sim.get_hourly_df(only_pareto_optimal=False, skip_confirmation=True)

    assert any(f'{SOME_FILES_MISSING} (1 of 3)' in str(warning.message) for warning in record)
    assert sorted(hourly['x'].unique().tolist()) == [1.0, 3.0]


@pytest.mark.parametrize(
    ('keep_sim_files', 'kwargs', 'rows'),
    [('non-dominated', {'simulation_indices': [1]}, 'row 1'), ('none', {}, 'rows 0, 2')],
    ids=['dominated_simulation_of_non_dominated_policy', 'pareto_simulations_of_none_policy'],
)
def test_optimisation_hourly_table_of_simulations_whose_files_were_not_kept_explains_why(
        tmp_path, keep_sim_files, kwargs, rows):
    # Their paths are missing values, which used to raise "AttributeError: 'float' object has no attribute 'strip'".
    sim = _optimisation_session(tmp_path, keep_sim_files=keep_sim_files)

    with pytest.raises(ValueError) as exc_info:
        sim.get_hourly_df(skip_confirmation=True, **kwargs)

    message = str(exc_info.value)
    assert message.startswith(ALL_FILES_MISSING)
    assert f'{rows}: {STORAGE_DIAGNOSTIC}' in message
    assert sim.outputs_optimisation_hourly is None


@pytest.mark.parametrize('method', RETRIEVAL_METHODS)
def test_optimisation_hourly_methods_name_the_csv_files_removed_by_the_cleanup_policy(tmp_path, method):
    sim = _optimisation_session_after_csv_cleanup(tmp_path)
    pareto_optimal = sim.outputs_optimisation[sim.outputs_optimisation['pareto-optimal']]

    with pytest.raises(ValueError) as exc_info:
        getattr(sim, method)(skip_confirmation=True)

    message = str(exc_info.value)
    assert message.startswith(ALL_FILES_MISSING)
    _assert_names_the_missing_files_and_the_storage_options(message, pareto_optimal['simulation_output_csv_path'])
    assert 'file_output_columns' not in message and 'include_file_outputs' not in message
    assert sim.outputs_optimisation_hourly is None
    assert sim.outputs_optimisation_daily is None
    assert sim.outputs_optimisation_monthly is None
    assert sim.outputs_optimisation_runperiod is None


# ----------------------------------------------------------------------------- other hourly readers

@pytest.mark.parametrize('source', ['parametric', 'optimisation'])
def test_hourly_column_discovery_names_the_csv_files_it_could_not_find(monkeypatch, tmp_path, source):
    if source == 'parametric':
        sim = _run_parametric_with_csv_cleanup(monkeypatch, tmp_path)
        missing = _missing_parametric_csv_paths(sim)
    else:
        sim = _optimisation_session_after_csv_cleanup(tmp_path)
        missing = sim.outputs_optimisation['simulation_output_csv_path'].tolist()

    with pytest.raises(FileNotFoundError, match='Could not find any valid (parametric )?simulation output CSV files') as exc_info:
        sim.get_hourly_df_columns()

    _assert_names_the_missing_files_and_the_storage_options(str(exc_info.value), missing)


def test_hourly_column_discovery_reads_the_csv_files_when_the_results_have_missing_values(monkeypatch, tmp_path):
    sim = _run_parametric(monkeypatch, tmp_path, keep_dirs=True)
    # A failed objective, for example, used to raise "AttributeError: 'float' object has no attribute 'strip'".
    sim.outputs_param_simulation.loc[0, 'Heating:Electricity'] = np.nan

    assert sim.get_hourly_df_columns() == [ENERGY, TEMPERATURE]


def test_hourly_column_detection_ignores_missing_values():
    table = pd.DataFrame({'x': [1.0, np.nan], 'epw': ['Seville', None], 'hourly': [[1.0, 2.0], [3.0, 4.0]]})

    assert identify_hourly_columns(table) == ['hourly']
    assert identify_hourly_columns(table.drop(columns='hourly')) == []


def test_expansion_without_hourly_columns_refers_to_the_real_arguments():
    with pytest.raises(ValueError) as exc_info:
        expand_to_hourly_dataframe(df=pd.DataFrame({'x': [1.0, np.nan]}), parameter_columns=['x'])

    message = str(exc_info.value)
    assert 'check the output_columns names (see get_hourly_df_columns())' in message
    assert 'keep_dirs / keep_sim_files / sim_files_extensions / sim_files_policy' in message
    assert 'file_output_columns' not in message and 'include_file_outputs' not in message


def test_hourly_indicators_name_the_missing_csv_file(monkeypatch, tmp_path):
    sim = _run_parametric_with_csv_cleanup(monkeypatch, tmp_path)
    missing = _missing_parametric_csv_paths(sim)[0]

    with pytest.raises(FileNotFoundError) as exc_info:
        sim.compute_hourly_indicators(
            df_source='parametric',
            running_mean=None,
            energy={'heating': 'Heating:Electricity'},
            verbose=False,
        )

    assert f'Simulation CSV not found: {missing}.' in str(exc_info.value)
    assert 'path_replacements' in str(exc_info.value)


def test_hourly_series_by_epw_reports_the_missing_csv_file(monkeypatch, tmp_path):
    sim = _run_parametric_with_csv_cleanup(monkeypatch, tmp_path)
    missing = _missing_parametric_csv_paths(sim)[0]

    with pytest.raises(FileNotFoundError) as exc_info:
        sim.get_hourly_series_by_epw('Zone Operative Temperature', df_source='parametric')

    assert exc_info.value.filename == missing
