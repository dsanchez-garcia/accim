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

    checkpoint_df = pd.read_pickle(checkpoint_path)
    assert '_accim_task_signature' in checkpoint_df.columns
    assert len(checkpoint_df) == 5


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

