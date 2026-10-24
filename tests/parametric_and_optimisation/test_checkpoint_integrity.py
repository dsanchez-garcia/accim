"""Checkpoint failures must not masquerade as successful partial recovery."""

from pathlib import Path

import pandas as pd
import pytest

import accim.parametric_and_optimisation.main as main
from .test_parametric_batch_checkpoint import _fake_worker, _make_lightweight_parametric
from .test_optimisation_checkpoint_resume import (
    _fake_build_full_outputs_df, _fake_set_evaluator, _make_fake_nsgaii,
    _make_lightweight_optimisation,
)


@pytest.fixture
def synthetic_identity(monkeypatch):
    """Fake evaluators have no physical IDF/EPW; production must not accept that."""
    monkeypatch.setattr(
        main.SimulationBase, '_checkpoint_evaluation_identity',
        lambda self, **kwargs: {'schema': 1, 'problem': getattr(self, 'test_identity', 'original')},
        raising=False,
    )
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda *args, **kwargs: None)


@pytest.fixture
def parametric_run(tmp_path, monkeypatch, synthetic_identity):
    calls = []

    def worker(*args, **kwargs):
        calls.append(args[10]['x'])
        return _fake_worker(*args, **kwargs)

    monkeypatch.setattr(main, '_run_single_evaluation_worker', worker)
    sim = _make_lightweight_parametric()
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2, 3, 4, 1]})
    out = tmp_path / 'run'
    options = dict(out_dir=str(out), processes=1, batch_size=2,
                   checkpoint_every_batch=True, keep_dirs=False)
    result = sim.run_parametric_simulation(**options)
    assert result['x'].tolist() == [1, 2, 3, 4, 1]
    calls.clear()
    checkpoint = out / 'outputs_param_simulation_checkpoint_latest.pkl'
    return sim, options, checkpoint, calls


@pytest.mark.parametrize('damage', ['missing', 'truncated', 'wrong_type', 'missing_column', 'changed_value'])
def test_damaged_chunks_reject_resume_without_overwriting_checkpoint(parametric_run, damage):
    sim, options, checkpoint, calls = parametric_run
    state = pd.read_pickle(checkpoint)
    chunk = Path(state['batch_pickles'][0])
    if damage == 'missing':
        chunk.unlink()
    elif damage == 'truncated':
        chunk.write_bytes(b'not a pickle')
    elif damage == 'wrong_type':
        pd.to_pickle({'not': 'a dataframe'}, chunk)
    else:
        frame = pd.read_pickle(chunk)
        if damage == 'missing_column':
            frame = frame.drop(columns='energy')
        else:
            frame.loc[0, 'energy'] = -999
        frame.to_pickle(chunk)
    original = checkpoint.read_bytes()
    with pytest.raises(ValueError, match='(?i)checkpoint|batch|fingerprint'):
        sim.run_parametric_simulation(**options, resume_from_checkpoint=True)
    assert calls == []
    assert checkpoint.read_bytes() == original


def test_changed_evaluation_identity_rejects_resume(parametric_run):
    sim, options, checkpoint, calls = parametric_run
    original = checkpoint.read_bytes()
    sim.test_identity = 'changed-model-or-reader'
    with pytest.raises(ValueError, match='(?i)fingerprint|identity|incompatible'):
        sim.run_parametric_simulation(**options, resume_from_checkpoint=True)
    assert calls == []
    assert checkpoint.read_bytes() == original


def test_corrupt_checkpoint_does_not_silently_restart(parametric_run):
    sim, options, checkpoint, calls = parametric_run
    checkpoint.write_bytes(b'incomplete checkpoint')
    with pytest.raises(ValueError, match='(?i)checkpoint'):
        sim.run_parametric_simulation(**options, resume_from_checkpoint=True)
    assert calls == []
    assert checkpoint.read_bytes() == b'incomplete checkpoint'


def test_unbacked_completed_signature_is_rejected(parametric_run):
    sim, options, checkpoint, calls = parametric_run
    state = pd.read_pickle(checkpoint)
    state['completed_signatures'].append('not-backed-by-a-result')
    state['completed_tasks'] += 1
    pd.to_pickle(state, checkpoint)
    with pytest.raises(ValueError, match='(?i)checkpoint|completed|signature'):
        sim.run_parametric_simulation(**options, resume_from_checkpoint=True)
    assert calls == []


def test_changed_checkpoint_input_plan_is_rejected(parametric_run):
    sim, options, checkpoint, calls = parametric_run
    state = pd.read_pickle(checkpoint)
    state['input_plan'].loc[0, 'x'] = 99
    pd.to_pickle(state, checkpoint)
    with pytest.raises(ValueError, match='input plan fingerprint'):
        sim.run_parametric_simulation(**options, resume_from_checkpoint=True)
    assert calls == []


def test_identical_resume_preserves_duplicates_and_full_order(parametric_run):
    sim, options, checkpoint, calls = parametric_run
    result = sim.run_parametric_simulation(**options, resume_from_checkpoint=True)
    assert calls == []
    assert result['x'].tolist() == [1, 2, 3, 4, 1]
    assert result['energy'].tolist() == [10, 20, 30, 40, 10]
    assert pd.read_pickle(checkpoint)['evaluation_identity']


def test_interrupted_run_resumes_only_unfinished_tasks(tmp_path, monkeypatch, synthetic_identity):
    sim = _make_lightweight_parametric()
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2, 3, 4, 1]})
    calls = []
    interrupt = True

    def worker(*args, **kwargs):
        value = args[10]['x']
        if interrupt and value == 3:
            raise RuntimeError('interrupted evaluation')
        calls.append(value)
        return _fake_worker(*args, **kwargs)

    monkeypatch.setattr(main, '_run_single_evaluation_worker', worker)
    options = dict(out_dir=str(tmp_path / 'partial'), processes=1, batch_size=2,
                   checkpoint_every_batch=True, keep_dirs=False)
    with pytest.raises(RuntimeError, match='interrupted evaluation'):
        sim.run_parametric_simulation(**options)
    assert calls == [1, 2]
    interrupt = False
    calls.clear()
    result = sim.run_parametric_simulation(**options, resume_from_checkpoint=True)
    assert calls == [3, 4]
    assert result['x'].tolist() == [1, 2, 3, 4, 1]


def test_final_merge_must_not_silently_drop_a_task(tmp_path, monkeypatch, synthetic_identity):
    sim = _make_lightweight_parametric()
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2]})
    monkeypatch.setattr(main, '_run_single_evaluation_worker', _fake_worker)
    original_merge = sim._merge_parametric_batch_pickles

    def incomplete_merge(*args, **kwargs):
        return original_merge(*args, **kwargs).iloc[:1].copy()

    monkeypatch.setattr(sim, '_merge_parametric_batch_pickles', incomplete_merge)
    with pytest.raises(ValueError, match='(?i)incomplete|missing|coverage'):
        sim.run_parametric_simulation(out_dir=str(tmp_path / 'partial'), processes=1, keep_dirs=False)
    assert not list((tmp_path / 'partial').glob('outputs_param_simulation_*.csv'))


@pytest.fixture
def optimisation_run(tmp_path, monkeypatch, synthetic_identity):
    monkeypatch.setattr(main.OptimisationSimulation, 'set_evaluator', _fake_set_evaluator)
    monkeypatch.setattr(main.OptimisationSimulation, '_build_full_optimisation_outputs_df', _fake_build_full_outputs_df)
    calls = []
    monkeypatch.setattr(main.optimizer, 'NSGAII', _make_fake_nsgaii(calls))
    sim = _make_lightweight_optimisation(['A.epw', 'B.epw'])
    options = dict(out_dir=str(tmp_path / 'optim'), processes=1, evaluations=2,
                   population_size=2, checkpoint_every_case=True, show_progress=False)
    sim.run_optimisation(**options)
    calls.clear()
    checkpoint = tmp_path / 'optim' / 'outputs_optimisation_checkpoint_latest.pkl'
    return sim, options, checkpoint, calls


@pytest.mark.parametrize('damage', ['empty_history', 'missing_objective', 'wrong_count', 'unknown_format', 'changed_value'])
def test_invalid_optimisation_cases_are_rejected(optimisation_run, damage):
    sim, options, checkpoint, calls = optimisation_run
    state = pd.read_pickle(checkpoint)
    case = next(iter(state['cases'].values()))
    if damage == 'empty_history':
        case['outputs_full'] = case['outputs_full'].iloc[:0]
    elif damage == 'missing_objective':
        case['outputs_full'] = case['outputs_full'].drop(columns='obj')
    elif damage == 'wrong_count':
        state['completed_cases'] += 1
    elif damage == 'changed_value':
        case['outputs_full'].loc[0, 'obj'] = -999
    else:
        state['checkpoint_format'] = 'future_unsupported'
    pd.to_pickle(state, checkpoint)
    original = checkpoint.read_bytes()
    with pytest.raises(ValueError, match='(?i)checkpoint|history|schema|format|case'):
        sim.run_optimisation(**options, resume_from_checkpoint=True)
    assert calls == []
    assert checkpoint.read_bytes() == original


def test_optimisation_changed_identity_does_not_reuse_cases(optimisation_run):
    sim, options, checkpoint, calls = optimisation_run
    sim.test_identity = 'changed-objective'
    original = checkpoint.read_bytes()
    with pytest.raises(ValueError, match='(?i)identity|fingerprint|incompatible'):
        sim.run_optimisation(**options, resume_from_checkpoint=True)
    assert calls == []
    assert checkpoint.read_bytes() == original


def test_fresh_variator_objects_have_compatible_resume_signatures(optimisation_run):
    from platypus import SBX
    sim, options, checkpoint, calls = optimisation_run
    # A fresh run intentionally replaces this test-owned checkpoint.
    sim.run_optimisation(**options, algorithm_options={'variator': SBX()})
    calls.clear()
    sim.run_optimisation(**options, algorithm_options={'variator': SBX()}, resume_from_checkpoint=True)
    assert calls == []


def test_noncheckpointed_run_does_not_require_variator_fingerprint(optimisation_run):
    import numpy as np
    sim, options, checkpoint, calls = optimisation_run

    class CustomVariator:
        def __init__(self):
            self.rng = np.random.default_rng(0)

    result = sim.run_optimisation(**dict(options, checkpoint_every_case=False),
                                 algorithm_options={'variator': CustomVariator()})
    assert len(result) == 2
    assert len(calls) == 2



