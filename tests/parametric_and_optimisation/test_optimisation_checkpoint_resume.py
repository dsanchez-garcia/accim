import os
import json
import hashlib

import pandas as pd

import accim.parametric_and_optimisation.main as main_module
from accim.parametric_and_optimisation.main import OptimisationSimulation


class _DummyBuilding:
    def __init__(self, idfname: str):
        self.idfname = idfname
        self.idfobjects = {}

    def savecopy(self, backup_path: str):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        with open(backup_path, 'w', encoding='utf-8') as handle:
            handle.write('Version,9.6;\n')


class _DummyProblem:
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


class _DummyEvaluator:
    def __init__(self, epw: str, out_dir: str):
        self.epw = epw
        self.out_dir = out_dir
        self.problem = _DummyProblem()
        self._building = type('BldProxy', (), {'idfobjects': {}})()


def _make_lightweight_optimisation(epws):
    sim = OptimisationSimulation(
        buildings=None,
        epws=epws,
        parameters_type=None,
        bypass_addAccis=True,
    )
    sim.buildings = [_DummyBuilding('dummy.idf')]
    sim.building = sim.buildings[0]
    sim.problem = _DummyProblem()
    return sim


def _fake_set_evaluator(self, epw, out_dir, building=None):
    return _DummyEvaluator(epw=epw, out_dir=out_dir)


def _fake_build_full_outputs_df(self, evaluator, epwname):
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


def _make_fake_nsgaii(call_log):
    def _fake_nsgaii(evaluator, evaluations, population_size, **kwargs):
        objective = float(len(call_log) + 1)
        evaluator._fake_objective = objective
        call_log.append(
            {
                'epw': evaluator.epw,
                'evaluations': evaluations,
                'population_size': population_size,
                'store_in_memory': bool(getattr(evaluator, '_store_optimisation_records_in_memory', True)),
            }
        )
        return pd.DataFrame([{'x': objective, 'obj': objective}])

    return _fake_nsgaii


def _build_resume_signature(evaluations: int, population_size: int = 2) -> str:
    payload = {
        'algorithm': 'NSGAII',
        'evaluations': int(evaluations),
        'population_size': int(population_size),
        'algorithm_options': {},
        'pareto_separate_by_epw': True,
        'pareto_separate_by_idf': False,
        'keep_df': 'all',
    }
    return hashlib.sha1(
        json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str).encode('utf-8')
    ).hexdigest()


def test_optimisation_checkpoint_resume_reuses_completed_cases(tmp_path, monkeypatch):
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    monkeypatch.setattr(OptimisationSimulation, 'set_evaluator', _fake_set_evaluator)
    monkeypatch.setattr(OptimisationSimulation, '_build_full_optimisation_outputs_df', _fake_build_full_outputs_df)

    first_calls = []
    monkeypatch.setattr(main_module.optimizer, 'NSGAII', _make_fake_nsgaii(first_calls))

    out_dir = tmp_path / 'optim_checkpoint'
    sim = _make_lightweight_optimisation(epws=['A.epw', 'B.epw'])
    first_results = sim.run_optimisation(
        out_dir=str(out_dir),
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1,
        checkpoint_every_case=True,
    )

    assert len(first_calls) == 2
    assert len(first_results) == 2

    checkpoint_path = out_dir / 'outputs_optimisation_checkpoint_latest.pkl'
    assert checkpoint_path.exists()

    second_calls = []
    monkeypatch.setattr(main_module.optimizer, 'NSGAII', _make_fake_nsgaii(second_calls))

    sim_resume = _make_lightweight_optimisation(epws=['A.epw', 'B.epw'])
    resumed_results = sim_resume.run_optimisation(
        out_dir=str(out_dir),
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1,
        resume_from_checkpoint=True,
    )

    assert len(second_calls) == 0
    assert len(resumed_results) == 2
    assert resumed_results.attrs.get('checkpoint_path') == os.path.abspath(str(checkpoint_path))


def test_optimisation_disables_in_memory_records_when_keep_sim_files_all(tmp_path, monkeypatch):
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    monkeypatch.setattr(OptimisationSimulation, 'set_evaluator', _fake_set_evaluator)
    monkeypatch.setattr(OptimisationSimulation, '_build_full_optimisation_outputs_df', _fake_build_full_outputs_df)

    calls = []
    monkeypatch.setattr(main_module.optimizer, 'NSGAII', _make_fake_nsgaii(calls))

    sim = _make_lightweight_optimisation(epws=['A.epw'])
    sim.run_optimisation(
        out_dir=str(tmp_path / 'optim_memory_mode'),
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1,
        keep_sim_files='all',
    )

    assert len(calls) == 1
    assert calls[0]['store_in_memory'] is False


def test_optimisation_resume_ignores_incompatible_checkpoint_signature(tmp_path, monkeypatch):
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    monkeypatch.setattr(OptimisationSimulation, 'set_evaluator', _fake_set_evaluator)
    monkeypatch.setattr(OptimisationSimulation, '_build_full_optimisation_outputs_df', _fake_build_full_outputs_df)

    first_calls = []
    monkeypatch.setattr(main_module.optimizer, 'NSGAII', _make_fake_nsgaii(first_calls))

    out_dir = tmp_path / 'optim_signature_check'
    sim = _make_lightweight_optimisation(epws=['A.epw'])
    sim.run_optimisation(
        out_dir=str(out_dir),
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1,
        checkpoint_every_case=True,
    )
    assert len(first_calls) == 1

    checkpoint_payload = pd.read_pickle(out_dir / 'outputs_optimisation_checkpoint_latest.pkl')
    checkpoint_signature = checkpoint_payload.get('resume_signature')
    assert checkpoint_signature == _build_resume_signature(evaluations=2, population_size=2)
    assert checkpoint_signature != _build_resume_signature(evaluations=4, population_size=2)

    second_calls = []
    monkeypatch.setattr(main_module.optimizer, 'NSGAII', _make_fake_nsgaii(second_calls))

    sim_changed = _make_lightweight_optimisation(epws=['A.epw'])
    sim_changed.run_optimisation(
        out_dir=str(out_dir),
        algorithm='NSGAII',
        evaluations=4,
        population_size=2,
        processes=1,
        resume_from_checkpoint=True,
    )

    assert len(second_calls) == 1


