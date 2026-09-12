import os

import pandas as pd

import accim.parametric_and_optimisation.main as main_module
from accim.parametric_and_optimisation.file_cleanup import normalize_sim_file_cleanup_options
from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation


class _DummyParamProblem:
    def names(self, typ):
        if typ == 'inputs':
            return ['x']
        if typ == 'outputs':
            return ['energy']
        if typ == 'constraints':
            return []
        raise KeyError(typ)


class _DummyBuilding:
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


def _write_mock_simulation_files(sim_dir: str) -> None:
    os.makedirs(sim_dir, exist_ok=True)
    for filename in ['eplusout.csv', 'eplusout.eso', 'in.idf', 'eplusout.err']:
        with open(os.path.join(sim_dir, filename), 'w', encoding='utf-8') as handle:
            handle.write('dummy\n')


def _fake_param_worker(
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
    sim_dir = os.path.join(out_dir, f"sim_{int(row_dict['x'])}")
    _write_mock_simulation_files(sim_dir)

    result = {
        problem_names_outputs[0]: float(row_dict['x']) * 10.0,
        'epw': epwname,
        'idf': idf_basename,
    }
    if keep_input:
        result.update(row_dict)
    if keep_dirs:
        result['output_dir'] = sim_dir
    return result


def _fake_set_optim_evaluator(self, epw, out_dir, building=None):
    return _DummyOptimEvaluator(epw=epw, out_dir=out_dir)


def _fake_build_optim_full_outputs_df(self, evaluator, epwname):
    sim_dir = os.path.join(evaluator.out_dir, f'sim_{epwname}')
    _write_mock_simulation_files(sim_dir)
    objective = float(getattr(evaluator, '_fake_objective', 1.0))
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


def _make_fake_nsgaii(call_log):
    def _fake_nsgaii(evaluator, evaluations, population_size, **kwargs):
        evaluator._fake_objective = 1.0
        call_log.append(
            {
                'extensions': getattr(evaluator, '_sim_files_extensions', None),
                'policy': getattr(evaluator, '_sim_files_policy', None),
            }
        )
        return pd.DataFrame([{'x': 1.0, 'obj': 1.0}])

    return _fake_nsgaii


def test_run_parametric_simulation_applies_extension_cleanup(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _fake_param_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)

    sim = ParametricSimulation(
        buildings=None,
        epws=['Test.epw'],
        parameters_type=None,
        bypass_addAccis=True,
    )
    sim.problem = _DummyParamProblem()
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2]})

    results = sim.run_parametric_simulation(
        out_dir=str(tmp_path / 'param_cleanup'),
        processes=1,
        keep_dirs=True,
        keep_input=True,
        sim_files_extensions=['csv'],
        sim_files_policy='keep',
    )

    assert len(results) == 2
    for sim_dir in results['output_dir'].tolist():
        remaining_files = sorted(os.listdir(sim_dir))
        assert remaining_files == ['eplusout.csv']


def test_run_optimisation_applies_extension_cleanup(tmp_path, monkeypatch):
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    monkeypatch.setattr(OptimisationSimulation, 'set_evaluator', _fake_set_optim_evaluator)
    monkeypatch.setattr(OptimisationSimulation, '_build_full_optimisation_outputs_df', _fake_build_optim_full_outputs_df)

    calls = []
    monkeypatch.setattr(main_module.optimizer, 'NSGAII', _make_fake_nsgaii(calls))

    sim = OptimisationSimulation(
        buildings=None,
        epws=['A.epw'],
        parameters_type=None,
        bypass_addAccis=True,
    )
    sim.buildings = [_DummyBuilding('dummy.idf')]
    sim.building = sim.buildings[0]
    sim.problem = _DummyOptimProblem()

    results = sim.run_optimisation(
        out_dir=str(tmp_path / 'optim_cleanup'),
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1,
        keep_sim_files='all',
        sim_files_extensions=['.csv'],
        sim_files_policy='keep',
    )

    assert len(calls) == 1
    assert calls[0]['extensions'] == ('.csv',)
    assert calls[0]['policy'] == 'keep'

    sim_dir = str(results.iloc[0]['simulation_directory'])
    remaining_files = sorted(os.listdir(sim_dir))
    assert remaining_files == ['eplusout.csv']


def test_normalize_sim_file_cleanup_options_supports_common_formats():
    extensions, policy = normalize_sim_file_cleanup_options(
        sim_files_extensions=['csv', '*.ESO', '.idf'],
        sim_files_policy='delete',
    )
    assert extensions == ('.csv', '.eso', '.idf')
    assert policy == 'delete'

