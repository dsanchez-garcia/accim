import os
import json

import pandas as pd
import pytest

import accim.parametric_and_optimisation.main as main_module
from accim.parametric_and_optimisation.main import ParametricSimulation, OptimisationSimulation


class _DummyProblem:
    def __init__(self, inputs, outputs):
        self._inputs = inputs
        self._outputs = outputs

    def names(self, typ):
        if typ == 'inputs':
            return self._inputs
        if typ == 'outputs':
            return self._outputs
        if typ == 'constraints':
            return []
        raise KeyError(typ)


def _make_summary_sim(epw='Test.epw'):
    return ParametricSimulation(
        buildings=None,
        epws=[epw],
        parameters_type=None,
        bypass_addAccis=True,
    )


def _fake_worker(
    idf_path,
    epw,
    epwname,
    idf_basename,
    out_dir,
    problem_names_inputs,
    problem_names_outputs,
    output_specs,
    add_output_specs,
    add_output_names,
    row_dict,
    keep_dirs,
    keep_input,
    sim_files_extensions=None,
    sim_files_policy='keep',
):
    result = {
        problem_names_outputs[0]: float(row_dict['x']) * 100.0,
        'epw': epwname,
        'idf': idf_basename,
    }
    if keep_input:
        result.update(row_dict)
    if keep_dirs:
        result['output_dir'] = os.path.join(out_dir, f"sim_{row_dict['x']}")
    return result


class _DummyOptimBuilding:
    def __init__(self, idfname: str):
        self.idfname = idfname
        self.idfobjects = {}

    def savecopy(self, backup_path: str):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        with open(backup_path, 'w', encoding='utf-8') as handle:
            handle.write('Version,9.6;\n')


class _DummyOptimProblem:
    def __init__(self):
        self.minimize_outputs = [True]
        self.add_outputs = []

    def names(self, typ):
        if typ == 'inputs':
            return ['x']
        if typ == 'outputs':
            return ['obj']
        if typ == 'constraints':
            return []
        raise KeyError(typ)


class _DummyOptimEvaluator:
    def __init__(self, epw: str, out_dir: str):
        self.epw = epw
        self.out_dir = out_dir
        self.problem = _DummyOptimProblem()
        self._building = type('BldProxy', (), {'idfobjects': {}})()


def _make_summary_optim_sim(epws):
    sim = OptimisationSimulation(
        buildings=None,
        epws=epws,
        parameters_type=None,
        bypass_addAccis=True,
    )
    sim.buildings = [_DummyOptimBuilding('dummy.idf')]
    sim.building = sim.buildings[0]
    sim.problem = _DummyOptimProblem()
    return sim


def _fake_set_optim_evaluator(self, epw, out_dir, building=None):
    return _DummyOptimEvaluator(epw=epw, out_dir=out_dir)


def _fake_build_optim_full_outputs_df(self, evaluator, epwname):
    objective = float(getattr(evaluator, '_fake_objective', 1.0))
    sim_dir = os.path.join(evaluator.out_dir, f'sim_{epwname}')
    return pd.DataFrame(
        [
            {
                'x': objective,
                'obj': objective,
                'simulation_directory': sim_dir,
                'simulation_output_csv_path': os.path.join(sim_dir, 'eplusout.csv'),
                'epw': epwname,
            }
        ]
    )


def _fake_nsgaii_for_summary(evaluator, evaluations, population_size, **kwargs):
    evaluator._fake_objective = 1.25
    return pd.DataFrame([{'x': 1.25, 'obj': 1.25}])


def test_build_simulation_summary_uses_mapping_rules():
    sim = _make_summary_sim()
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'idf': ['idf_a', 'idf_a', 'idf_b', 'idf_b'],
            'epw': ['sev_2024', 'sev_2025', 'mad_2024', 'mad_2025'],
            'output_dir': ['r1', 'r2', 'r3', 'r4'],
            'weather_type': ['long-term', 'long-term', 'long-term', 'tmy'],
            'city': ['seville', 'seville', 'madrid', 'madrid'],
            'building_type': ['office', 'office', 'school', 'school'],
            'performance': ['high', 'low', 'high', 'low'],
            'HVAC energy': [10.0, 11.0, 12.0, 13.0],
        }
    )
    sim.epw_mapping_rules = {
        'weather_type': {'long-term': ['hist'], 'tmy': ['tmy']},
        'city': {'seville': ['sev'], 'madrid': ['mad']},
        'unused_epw_category': {'x': ['x']},
    }
    sim.idf_mapping_rules = {
        'building_type': {'office': ['office'], 'school': ['school']},
        'performance': {'high': ['high'], 'low': ['low']},
    }

    summary = sim.build_simulation_summary(df_source='parametric')

    assert summary['total_rows'] == 4
    assert summary['n_unique']['idf'] == 2
    assert summary['n_unique']['epw'] == 4
    assert summary['detected_category_columns'] == [
        'weather_type',
        'city',
        'building_type',
        'performance',
    ]
    assert summary['category_counts']['weather_type']['long-term'] == 3


def test_build_simulation_summary_without_rules_infers_categories():
    sim = _make_summary_sim()
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'idf': ['idf_a', 'idf_a', 'idf_b'],
            'epw': ['clim_a', 'clim_b', 'clim_a'],
            'output_dir': ['run_1', 'run_2', 'run_3'],
            'scenario_label': ['base', 'base', 'retrofit'],
            'retrofit_stage': ['low', 'medium', 'high'],
            'HVAC energy [kWh]': [95.0, 88.0, 77.0],
            'peak_load_kw': [4.2, 4.0, 3.8],
        }
    )

    summary = sim.build_simulation_summary(df_source='parametric')

    detected = summary['detected_category_columns']
    assert 'scenario_label' in detected
    assert 'retrofit_stage' in detected
    assert 'output_dir' not in detected
    assert 'HVAC energy [kWh]' in summary['numeric_columns']
    assert 'HVAC energy [kWh]' in summary['energy_columns']


def test_build_simulation_summary_invalid_category_columns():
    sim = _make_summary_sim()
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'cluster': ['A', 'B'],
            'score': [1.0, 2.0],
        }
    )

    with pytest.raises(ValueError) as excinfo:
        sim.build_simulation_summary(
            df_source='parametric',
            category_columns=['cluster', 'missing_category'],
        )

    message = str(excinfo.value)
    assert 'missing_category' in message
    assert 'Available columns' in message
    assert 'Automatically detected categories' in message


def test_load_outputs_parametric_updates_simulation_summary(tmp_path):
    df = pd.DataFrame(
        {
            'idf': ['idf_a', 'idf_b'],
            'epw': ['sev_2024', 'mad_2024'],
            'output_dir': ['run_a', 'run_b'],
            'custom_split': ['training', 'validation'],
            'HVAC energy': [120.0, 115.0],
        }
    )
    pickle_path = tmp_path / 'outputs_param_simulation.pkl'
    df.to_pickle(pickle_path)

    sim = _make_summary_sim()
    loaded = sim.load_outputs_parametric(pickle_path=str(pickle_path))

    assert len(loaded) == 2
    assert isinstance(sim.simulation_summary, dict)
    assert sim.simulation_summary['df_source'] == 'parametric'
    assert sim.simulation_summary['total_rows'] == 2


def test_run_parametric_simulation_updates_simulation_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _fake_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)

    sim = _make_summary_sim(epw='Test.epw')
    sim.problem = _DummyProblem(inputs=['x'], outputs=['HVAC energy'])
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2, 3]})

    out_dir = tmp_path / 'param_out'
    results = sim.run_parametric_simulation(
        out_dir=str(out_dir),
        processes=1,
        keep_dirs=True,
        keep_input=True,
    )

    assert len(results) == 3
    assert isinstance(sim.simulation_summary, dict)
    assert sim.simulation_summary['df_source'] == 'parametric'
    assert sim.simulation_summary['total_rows'] == 3
    assert sim.simulation_summary['n_unique']['output_dir'] == 3
    assert 'HVAC energy' in sim.simulation_summary['energy_columns']


def test_build_simulation_summary_detects_nonstandard_category_names():
    sim = _make_summary_sim()
    sim.outputs_optimisation = pd.DataFrame(
        {
            'idf': ['idf_a', 'idf_a', 'idf_b'],
            'epw': ['met_a', 'tmy_a', 'met_a'],
            'archetype_bucket': ['A', 'A', 'B'],
            'retrofit_package': ['pack_1', None, 'pack_2'],
            'objective_1': [1.2, 1.1, 0.9],
            'objective_2': [45.0, 41.0, 39.0],
        }
    )

    summary = sim.build_simulation_summary(df_source='optimisation', include_na=True)

    assert summary['df_source'] == 'optimisation'
    assert 'archetype_bucket' in summary['detected_category_columns']
    assert 'retrofit_package' in summary['detected_category_columns']
    assert '<NA>' in summary['category_counts']['retrofit_package']


def test_export_simulation_summary_json(tmp_path):
    sim = _make_summary_sim()
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'idf': ['idf_a', 'idf_b'],
            'epw': ['sev_2024', 'mad_2024'],
            'output_dir': ['run_a', 'run_b'],
            'scenario': ['base', 'retrofit'],
            'HVAC energy': [120.0, 115.0],
        }
    )
    sim.build_simulation_summary(df_source='parametric')

    json_path = tmp_path / 'summary_parametric.json'
    exported = sim.export_simulation_summary_json(
        json_path=str(json_path),
        df_source='parametric',
    )

    assert os.path.isfile(exported)
    with open(exported, 'r', encoding='utf-8') as handle:
        payload = json.load(handle)

    assert payload['df_source'] == 'parametric'
    assert payload['summary_json_path'] == os.path.abspath(str(json_path))
    assert 'exported_at' in payload


def test_run_optimisation_updates_simulation_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    monkeypatch.setattr(OptimisationSimulation, 'set_evaluator', _fake_set_optim_evaluator)
    monkeypatch.setattr(OptimisationSimulation, '_build_full_optimisation_outputs_df', _fake_build_optim_full_outputs_df)
    monkeypatch.setattr(main_module.optimizer, 'NSGAII', _fake_nsgaii_for_summary)

    sim = _make_summary_optim_sim(epws=['A.epw'])
    results = sim.run_optimisation(
        out_dir=str(tmp_path / 'optim_summary'),
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1,
    )

    assert len(results) == 1
    assert isinstance(sim.simulation_summary, dict)
    assert sim.simulation_summary['df_source'] == 'optimisation'
    assert sim.simulation_summary['total_rows'] == 1
    assert 'obj' in sim.simulation_summary['numeric_columns']


def test_load_outputs_optimisation_updates_simulation_summary(tmp_path):
    df = pd.DataFrame(
        {
            'idf': ['idf_a', 'idf_b'],
            'epw': ['A', 'B'],
            'obj': [10.0, 9.5],
            'pareto-optimal': [True, False],
            'simulation_output_csv_path': [None, None],
        }
    )
    pickle_path = tmp_path / 'outputs_optimisation.pkl'
    df.to_pickle(pickle_path)

    sim = OptimisationSimulation(
        buildings=None,
        epws=['A.epw'],
        parameters_type=None,
        bypass_addAccis=True,
    )
    loaded = sim.load_outputs_optimisation(pickle_path=str(pickle_path))

    assert len(loaded) == 2
    assert isinstance(sim.simulation_summary, dict)
    assert sim.simulation_summary['df_source'] == 'optimisation'
    assert sim.simulation_summary['total_rows'] == 2


def test_run_parametric_simulation_auto_exports_summary_json(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _fake_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)

    sim = _make_summary_sim(epw='Test.epw')
    sim.problem = _DummyProblem(inputs=['x'], outputs=['HVAC energy'])
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2]})

    out_dir = tmp_path / 'param_auto_summary'
    summary_json_path = tmp_path / 'summary_parametric_auto.json'
    results = sim.run_parametric_simulation(
        out_dir=str(out_dir),
        processes=1,
        keep_dirs=False,
        keep_input=True,
        export_summary_json=True,
        summary_json_path=str(summary_json_path),
    )

    assert len(results) == 2
    assert os.path.isfile(summary_json_path)
    with open(summary_json_path, 'r', encoding='utf-8') as handle:
        payload = json.load(handle)

    assert payload['df_source'] == 'parametric'
    assert payload['summary_json_path'] == os.path.abspath(str(summary_json_path))


def test_run_optimisation_auto_exports_summary_json(tmp_path, monkeypatch):
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    monkeypatch.setattr(OptimisationSimulation, 'set_evaluator', _fake_set_optim_evaluator)
    monkeypatch.setattr(OptimisationSimulation, '_build_full_optimisation_outputs_df', _fake_build_optim_full_outputs_df)
    monkeypatch.setattr(main_module.optimizer, 'NSGAII', _fake_nsgaii_for_summary)

    sim = _make_summary_optim_sim(epws=['A.epw'])
    summary_json_path = tmp_path / 'summary_optimisation_auto.json'
    results = sim.run_optimisation(
        out_dir=str(tmp_path / 'optim_auto_summary'),
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1,
        export_summary_json=True,
        summary_json_path=str(summary_json_path),
    )

    assert len(results) == 1
    assert os.path.isfile(summary_json_path)
    with open(summary_json_path, 'r', encoding='utf-8') as handle:
        payload = json.load(handle)

    assert payload['df_source'] == 'optimisation'
    assert payload['summary_json_path'] == os.path.abspath(str(summary_json_path))


