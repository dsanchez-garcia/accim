import os

import pandas as pd
import pytest

import accim.parametric_and_optimisation.main as main_module
from accim.parametric_and_optimisation.main import ParametricSimulation


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


def _make_lightweight_parametric(epw='Test.epw'):
    sim = ParametricSimulation(
        buildings=None,
        epws=[epw],
        parameters_type=None,
        bypass_addAccis=True,
    )
    sim.problem = _DummyProblem(inputs=['x'], outputs=['energy'])
    return sim


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
        problem_names_outputs[0]: float(row_dict['x']) * 10.0,
        'epw': epwname,
        'idf': idf_basename,
    }
    if keep_input:
        result.update(row_dict)
    if keep_dirs:
        result['output_dir'] = os.path.join(out_dir, f"sim_{row_dict['x']}")
    return result


def test_parametric_batch_checkpoint_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _fake_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)

    sim = _make_lightweight_parametric(epw='Test.epw')
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2, 3, 4, 5]})

    out_dir = tmp_path / 'param_out'
    results = sim.run_parametric_simulation(
        out_dir=str(out_dir),
        processes=1,
        batch_size=2,
        checkpoint_every_batch=True,
        keep_dirs=False,
        keep_input=True,
    )

    assert len(results) == 5
    assert '_accim_task_signature' not in results.columns

    checkpoint_path = out_dir / 'outputs_param_simulation_checkpoint_latest.pkl'
    assert checkpoint_path.exists()

    # The checkpoint is persisted in the 'state_v2' dict format (not a plain
    # DataFrame): completed task signatures + pointers to batch pickle files.
    checkpoint_state = sim._load_parametric_checkpoint_state(checkpoint_path=str(checkpoint_path))
    assert len(checkpoint_state['completed_signatures']) == 5

    merged_checkpoint_df = sim._merge_parametric_batch_pickles(
        batch_pickles=checkpoint_state['batch_pickles'],
    )
    assert '_accim_task_signature' in merged_checkpoint_df.columns
    assert len(merged_checkpoint_df) == 5


def test_parametric_resume_from_checkpoint_skips_completed_tasks(tmp_path, monkeypatch):
    calls = []

    def _counting_worker(*args, **kwargs):
        row_dict = args[10]
        calls.append(int(row_dict['x']))
        return _fake_worker(*args, **kwargs)

    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _counting_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)

    sim = _make_lightweight_parametric(epw='Test.epw')
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2, 3, 4]})

    out_dir = tmp_path / 'resume_out'
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = out_dir / 'outputs_param_simulation_checkpoint_latest.pkl'

    precomputed_rows = []
    for x_val in [1, 2]:
        row_dict = {'x': x_val}
        signature = sim._build_parametric_task_signature(
            idf_basename='unknown_idf_0',
            epw='Test.epw',
            problem_names_inputs=['x'],
            row_dict=row_dict,
        )
        precomputed_rows.append(
            {
                'energy': float(x_val) * 10.0,
                'x': x_val,
                'epw': 'Test',
                'idf': 'unknown_idf_0',
                '_accim_task_signature': signature,
            }
        )

    pd.DataFrame(precomputed_rows).to_pickle(checkpoint_path)

    results = sim.run_parametric_simulation(
        out_dir=str(out_dir),
        processes=1,
        batch_size=2,
        resume_from_checkpoint=True,
        checkpoint_every_batch=False,
        keep_dirs=False,
        keep_input=True,
    )

    assert sorted(calls) == [3, 4]
    assert len(results) == 4
    assert sorted(results['x'].tolist()) == [1, 2, 3, 4]

    # The checkpoint is persisted in the 'state_v2' dict format (not a plain
    # DataFrame): reconstruct the full results via the batch pickle pointers.
    refreshed_checkpoint_state = sim._load_parametric_checkpoint_state(checkpoint_path=str(checkpoint_path))
    assert len(refreshed_checkpoint_state['completed_signatures']) == 4

    refreshed_merged_df = sim._merge_parametric_batch_pickles(
        batch_pickles=refreshed_checkpoint_state['batch_pickles'],
    )
    assert len(refreshed_merged_df) == 4
    assert sorted(refreshed_merged_df['x'].tolist()) == [1, 2, 3, 4]


def test_parametric_batch_size_validation(tmp_path):
    sim = _make_lightweight_parametric(epw='Test.epw')
    sim.parameters_values_df = pd.DataFrame({'x': [1]})

    with pytest.raises(ValueError, match='batch_size'):
        sim.run_parametric_simulation(
            out_dir=str(tmp_path / 'invalid_batch'),
            processes=1,
            batch_size=0,
        )


def test_parametric_resume_missing_checkpoint_raises_when_path_is_explicit(tmp_path):
    sim = _make_lightweight_parametric(epw='Test.epw')
    sim.parameters_values_df = pd.DataFrame({'x': [1]})

    missing_path = tmp_path / 'missing_checkpoint.pkl'
    with pytest.raises(FileNotFoundError):
        sim.run_parametric_simulation(
            out_dir=str(tmp_path / 'resume_missing'),
            processes=1,
            batch_size=1,
            resume_from_checkpoint=str(missing_path),
        )


def test_parametric_plans_match_helper():
    sim = _make_lightweight_parametric(epw='Test.epw')
    a = pd.DataFrame({'x': [1.0, 2.0], 'y': [3.0, 4.0]})
    b = a.copy()
    assert sim._parametric_plans_match(a, b) is True

    different_values = pd.DataFrame({'x': [1.0, 9.0], 'y': [3.0, 4.0]})
    assert sim._parametric_plans_match(a, different_values) is False

    different_shape = pd.DataFrame({'x': [1.0, 2.0, 3.0], 'y': [3.0, 4.0, 5.0]})
    assert sim._parametric_plans_match(a, different_shape) is False

    assert sim._parametric_plans_match(a, None) is False
    assert sim._parametric_plans_match(None, None) is False


def test_parametric_resume_auto_reconciles_changed_sampling_plan(tmp_path, monkeypatch):
    """Reproduces re-running a non-deterministic sampler (e.g. sampling_lhs())
    in a new session: resume_from_checkpoint should still recognise previously
    completed tasks by transparently falling back to the ORIGINAL plan stored
    in the checkpoint (default resume_plan_source='auto')."""
    calls = []

    def _counting_worker(*args, **kwargs):
        row_dict = args[10]
        calls.append(float(row_dict['x']))
        return _fake_worker(*args, **kwargs)

    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _counting_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)

    sim = _make_lightweight_parametric(epw='Test.epw')
    original_plan = pd.DataFrame({'x': [1.0, 2.0, 3.0, 4.0]})

    out_dir = tmp_path / 'resume_reconcile_out'

    # First run: no prior checkpoint, everything is simulated and the ORIGINAL
    # plan is stored inside the checkpoint.
    sim.run_parametric_simulation(
        out_dir=str(out_dir),
        df=original_plan,
        processes=1,
        batch_size=2,
        checkpoint_every_batch=True,
        resume_from_checkpoint=True,
        keep_dirs=False,
        keep_input=True,
    )
    assert sorted(calls) == [1.0, 2.0, 3.0, 4.0]
    calls.clear()

    # Simulate a NEW session where a non-deterministic sampler produced a
    # completely different set of values.
    new_plan = pd.DataFrame({'x': [10.0, 20.0, 30.0, 40.0]})

    with pytest.warns(UserWarning, match='does not match the sampling plan'):
        results = sim.run_parametric_simulation(
            out_dir=str(out_dir),
            df=new_plan,
            processes=1,
            batch_size=2,
            checkpoint_every_batch=True,
            resume_from_checkpoint=True,
            keep_dirs=False,
            keep_input=True,
        )

    # Nothing should have been re-simulated: the checkpoint plan (original_plan)
    # was reused, so all 4 tasks were already completed.
    assert calls == []
    assert sorted(results['x'].tolist()) == [1.0, 2.0, 3.0, 4.0]


def test_parametric_resume_plan_source_provided_forces_new_plan(tmp_path, monkeypatch):
    """resume_plan_source='provided' is the explicit opt-out: the newly
    provided df is used even if it does not match the checkpoint, at the cost
    of not recognising previously completed tasks."""
    calls = []

    def _counting_worker(*args, **kwargs):
        row_dict = args[10]
        calls.append(float(row_dict['x']))
        return _fake_worker(*args, **kwargs)

    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _counting_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)

    sim = _make_lightweight_parametric(epw='Test.epw')
    original_plan = pd.DataFrame({'x': [1.0, 2.0, 3.0, 4.0]})

    out_dir = tmp_path / 'resume_provided_out'
    sim.run_parametric_simulation(
        out_dir=str(out_dir),
        df=original_plan,
        processes=1,
        batch_size=2,
        checkpoint_every_batch=True,
        resume_from_checkpoint=True,
        keep_dirs=False,
        keep_input=True,
    )
    calls.clear()

    new_plan = pd.DataFrame({'x': [10.0, 20.0, 30.0, 40.0]})
    with pytest.warns(UserWarning, match="resume_plan_source='provided'"):
        sim.run_parametric_simulation(
            out_dir=str(out_dir),
            df=new_plan,
            processes=1,
            batch_size=2,
            checkpoint_every_batch=True,
            resume_from_checkpoint=True,
            resume_plan_source='provided',
            keep_dirs=False,
            keep_input=True,
        )

    # With resume_plan_source='provided' the new plan wins, so none of its
    # task signatures match the checkpoint and all 4 tasks run again.
    assert sorted(calls) == [10.0, 20.0, 30.0, 40.0]


