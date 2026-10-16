"""Tests for the normalisation state of each results table.

- The plotting methods check whether the table they plot was normalised by normalize_outputs(),
  not the global flag outputs_normalized, which stays False while any other loaded table is not
  normalised. Before, a table already in kWh/m2 was divided by 3.6e6 again and labelled kWh.
- A new simulation, or results loaded from a file, reset the state of the tables they replace.
  Before, normalize_outputs() skipped the new results as if they were already normalised.
"""
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pytest

matplotlib.use('Agg')

import accim.parametric_and_optimisation.main as main_module
from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation


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


def _hourly_table():
    # Loaded and not normalised: the global flag outputs_normalized stays False.
    return pd.DataFrame({
        'epw': ['Seville'] * 3,
        'hour': [1, 2, 3],
        'datetime': pd.date_range('2024-01-01 01:00', periods=3, freq='h'),
        'Heating:Electricity [J]': [3.6e6, 7.2e6, 3.6e6],
    })


def _parametric_normalised_with_hourly_table_not_normalised():
    sim = ParametricSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.building_floor_area = 100.0
    # 3.6e8 J over 100 m2 is 1 kWh/m2.
    sim.outputs_param_simulation = pd.DataFrame({
        'ComfStand': [1, 2, 3, 4],
        'epw': ['Seville'] * 4,
        'Heating:Electricity [J]': [3.6e8, 7.2e8, 3.6e8, 7.2e8],
    })
    sim.outputs_param_simulation_hourly = _hourly_table()
    sim.normalize_outputs(df_types=['parametric'])
    assert sim.outputs_normalized is False
    return sim


def _capture_subplots(monkeypatch):
    figures = []
    original_subplots = plt.subplots

    def _subplots(*args, **kwargs):
        (fig, axes) = original_subplots(*args, **kwargs)
        figures.append(fig)
        return (fig, axes)

    monkeypatch.setattr(plt, 'subplots', _subplots)
    return figures


# ----------------------------------------------------------------------------- plots (bug 1)

def test_boxplots_of_a_normalised_table_are_not_divided_again(tmp_path):
    sim = _parametric_normalised_with_hourly_table_not_normalised()

    grid = sim.plot_categorical_boxplots(
        df_source='parametric',
        y_vars=['Heating:Electricity [kWh/m2]'],
        show_points=False,
        out_dir=str(tmp_path),
    )

    assert sorted(grid.data['Energy_Value'].unique()) == [1.0, 2.0]
    assert grid.axes.flat[0].get_ylabel() == 'Energy (kWh/m2)'


def test_boxplots_of_a_table_not_normalised_are_still_converted(tmp_path):
    sim = _parametric_normalised_with_hourly_table_not_normalised()

    grid = sim.plot_categorical_boxplots(
        df_source='parametric_hourly',
        y_vars=['Heating:Electricity [J]'],
        show_points=False,
        out_dir=str(tmp_path),
    )

    assert sorted(grid.data['Energy_Value'].unique()) == [1.0, 2.0]
    assert grid.axes.flat[0].get_ylabel() == 'Energy (kWh)'


def test_scatter_of_a_normalised_table_is_not_divided_again(tmp_path):
    sim = _parametric_normalised_with_hourly_table_not_normalised()

    grid = sim.plot_parametric_scatter(
        x='ComfStand',
        y='Heating:Electricity [kWh/m2]',
        df_source='parametric',
        out_dir=str(tmp_path),
    )

    plotted_y = sorted(set(grid.ax.collections[0].get_offsets()[:, 1].tolist()))
    assert plotted_y == [1.0, 2.0]
    assert grid.ax.get_ylabel() == 'Heating:Electricity [kWh/m2] (kWh/m2)'


def test_mcdm_plot_of_a_normalised_optimisation_table_is_not_divided_again(monkeypatch, tmp_path):
    sim = OptimisationSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.last_run_type = 'optimisation'
    sim.building_floor_area = 100.0
    sim.problem = _DummyProblem(inputs=['x'], outputs=['Heating:Electricity', 'Cooling:Electricity'])
    sim.outputs_optimisation = pd.DataFrame({
        'x': [0.1, 0.5, 0.9],
        'Heating:Electricity': [3.6e8, 7.2e8, 10.8e8],
        'Cooling:Electricity': [10.8e8, 7.2e8, 3.6e8],
        'pareto-optimal': [True, True, True],
        'epw': ['Seville'] * 3,
    })
    sim.outputs_optimisation_hourly = _hourly_table()
    sim.normalize_outputs(df_types=['optimisation'])
    assert sim.outputs_normalized is False
    figures = _capture_subplots(monkeypatch)

    sim.plot_best_compromise_solutions(out_dir=str(tmp_path), mcdm_configs=[{'method': 'topsis'}])

    ax = figures[0].axes[0]
    pareto_points = ax.collections[1].get_offsets()
    assert sorted(pareto_points[:, 0].tolist()) == [1.0, 2.0, 3.0]
    assert ax.get_xlabel() == 'Heating:Electricity_kWh/m2 (kWh/m2)'
    assert ax.get_ylabel() == 'Cooling:Electricity_kWh/m2 (kWh/m2)'


# ----------------------------------------------------------------------------- new results (bug 7)

def _worker_returning_heating(idf_path, epw, epwname, idf_basename, out_dir, problem_names_inputs,
                              problem_names_outputs, output_specs, add_output_specs, add_output_names,
                              row_dict, keep_dirs, keep_input, sim_files_extensions=None,
                              sim_files_policy='keep', additional_params=None):
    # 3.6e8 J per unit of x, that is 1 kWh/m2 per unit of x over 100 m2.
    result = {problem_names_outputs[0]: float(row_dict['x']) * 3.6e8, 'epw': epwname, 'idf': idf_basename}
    if keep_input:
        result.update(row_dict)
    return result


@pytest.fixture
def parametric_with_fake_worker(monkeypatch):
    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _worker_returning_heating)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    sim = ParametricSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.problem = _DummyProblem(inputs=['x'], outputs=['Heating:Electricity'])
    sim.building_floor_area = 100.0
    return sim


def test_a_new_parametric_run_resets_the_state_of_its_table(parametric_with_fake_worker, tmp_path):
    sim = parametric_with_fake_worker
    sim.run_parametric_simulation(
        df=pd.DataFrame({'x': [1, 2]}), out_dir=str(tmp_path / 'first'),
        processes=1, keep_dirs=False, keep_input=True,
    )
    sim.normalize_outputs(df_types=['parametric'])
    assert sim.outputs_param_simulation['Heating:Electricity_kWh/m2'].tolist() == [1.0, 2.0]

    sim.run_parametric_simulation(
        df=pd.DataFrame({'x': [3]}), out_dir=str(tmp_path / 'second'),
        processes=1, keep_dirs=False, keep_input=True,
    )

    assert not sim._is_df_type_normalized('parametric')
    sim.normalize_outputs(df_types=['parametric'])
    assert sim.outputs_param_simulation['Heating:Electricity_kWh/m2'].tolist() == [3.0]


def test_a_new_parametric_run_keeps_the_state_of_the_other_tables(parametric_with_fake_worker, tmp_path):
    sim = parametric_with_fake_worker
    sim.outputs_param_simulation_hourly = _hourly_table()
    sim.normalize_outputs(df_types=['parametric_hourly'])

    sim.run_parametric_simulation(
        df=pd.DataFrame({'x': [1]}), out_dir=str(tmp_path / 'out'),
        processes=1, keep_dirs=False, keep_input=True,
    )

    # The hourly table was not replaced: it is still in kWh/m2 and must not be divided again.
    assert sim._is_df_type_normalized('parametric_hourly')


def test_loaded_parametric_results_reset_the_state_of_their_tables(tmp_path):
    sim = _parametric_normalised_with_hourly_table_not_normalised()
    sim.normalize_outputs(df_types=['parametric_hourly'])
    results_csv = tmp_path / 'results.csv'
    hourly_csv = tmp_path / 'hourly.csv'
    pd.DataFrame({'ComfStand': [1], 'epw': ['Seville'], 'Heating:Electricity [J]': [3.6e8]}).to_csv(results_csv, index=False)
    _hourly_table().to_csv(hourly_csv, index=False)

    sim.load_outputs_parametric(csv_path=str(results_csv), hourly_csv_path=str(hourly_csv))

    assert not sim._is_df_type_normalized('parametric')
    assert not sim._is_df_type_normalized('parametric_hourly')
    sim.normalize_outputs(df_types=['parametric'])
    assert sim.outputs_param_simulation['Heating:Electricity [kWh/m2]'].tolist() == [1.0]


def test_loaded_optimisation_results_reset_the_state_of_their_table(tmp_path):
    sim = OptimisationSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.building_floor_area = 100.0
    results = pd.DataFrame({
        'x': [1.0],
        'Heating:Electricity [J]': [3.6e8],
        'pareto-optimal': [True],
        'epw': ['Seville'],
    })
    sim.outputs_optimisation = results.copy()
    sim.normalize_outputs(df_types=['optimisation'])
    results_csv = tmp_path / 'optimisation.csv'
    results.to_csv(results_csv, index=False)

    sim.load_outputs_optimisation(csv_path=str(results_csv))

    assert not sim._is_df_type_normalized('optimisation')
    sim.normalize_outputs(df_types=['optimisation'])
    assert sim.outputs_optimisation['Heating:Electricity [kWh/m2]'].tolist() == [1.0]
