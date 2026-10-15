"""Tests for the worker that runs each evaluation of run_parametric_simulation.

The real worker is called with a fake BESOS evaluator (no EnergyPlus run) that follows
the BESOS contract: it returns the objectives, followed by the simulation folder when
keep_dirs=True, and records the add_outputs in problem.add_outputs_list only when that
list exists.
"""
import os

import pandas as pd
import pytest

import accim.parametric_and_optimisation.main as main_module

ADD_OUTPUT_NAMES = ['Heating:Electricity', 'Cooling:Electricity']


class _FakeEvaluatorEP:
    created = []

    def __init__(self, problem, building, epw, out_dir=None, **kwargs):
        self.problem = problem
        self.out_dir = out_dir
        self.wrapper_existed = None
        if out_dir is not None:
            wrapper = os.path.join(str(out_dir), 'BESOS_Output')
            self.wrapper_existed = os.path.isdir(wrapper)
            # Same check as BESOS: os.makedirs raises if another worker created the folder
            # between the check and the call.
            if not os.path.exists(wrapper):
                os.makedirs(wrapper)
        _FakeEvaluatorEP.created.append(self)

    def __call__(self, values, keep_dirs=False):
        if self.problem.add_outputs_list is not None:
            self.problem.add_outputs_list.append(list(values) + [11.0, 22.0])
        result = (5.0,)
        if keep_dirs:
            sim_dir = os.path.join(str(self.out_dir), 'BESOS_Output', 'RUN1')
            os.makedirs(sim_dir, exist_ok=True)
            result = result + (sim_dir,)
        return result


@pytest.fixture
def fake_besos(monkeypatch):
    import besos.evaluator
    import accim.utils

    _FakeEvaluatorEP.created = []
    monkeypatch.setattr(besos.evaluator, 'EvaluatorEP', _FakeEvaluatorEP)
    monkeypatch.setattr(accim.utils, 'get_building', lambda path: object())
    monkeypatch.setattr(main_module, '_ensure_run_energyplus_copies_in_idf', lambda: None)
    return _FakeEvaluatorEP


def _run_worker(out_dir, keep_dirs, with_add_outputs=False):
    meter = {'kind': 'meter', 'key_name': 'Electricity:HVAC', 'frequency': 'Hourly', 'output_name': 'energy'}
    add_specs = [
        {'kind': 'meter', 'key_name': name, 'frequency': 'Hourly', 'output_name': name}
        for name in ADD_OUTPUT_NAMES
    ] if with_add_outputs else []
    return main_module._run_single_evaluation_worker(
        'model.idf',
        'weather.epw',
        'weather',
        'model',
        str(out_dir),
        ['x'],
        ['energy'],
        [meter],
        add_specs,
        list(ADD_OUTPUT_NAMES) if with_add_outputs else [],
        {'x': 1.0},
        keep_dirs,
        True,
        None,
        'keep',
    )


def test_worker_without_keep_dirs_lets_besos_use_a_temporary_folder(fake_besos, tmp_path):
    out_dir = tmp_path / 'results'
    result = _run_worker(out_dir, keep_dirs=False)

    evaluator = fake_besos.created[-1]
    assert evaluator.out_dir is None
    assert not (out_dir / 'BESOS_Output').exists()
    assert result['energy'] == 5.0
    assert 'output_dir' not in result
    assert result['epw'] == 'weather'
    assert result['x'] == 1.0


def test_worker_with_keep_dirs_creates_the_besos_folder_before_the_evaluator(fake_besos, tmp_path):
    out_dir = tmp_path / 'results'
    result = _run_worker(out_dir, keep_dirs=True)

    evaluator = fake_besos.created[-1]
    assert evaluator.out_dir == str(out_dir)
    assert evaluator.wrapper_existed is True
    assert result['output_dir'] == os.path.join(str(out_dir), 'BESOS_Output', 'RUN1')


def test_worker_tolerates_a_besos_folder_created_by_another_worker(fake_besos, tmp_path):
    out_dir = tmp_path / 'results'
    (out_dir / 'BESOS_Output').mkdir(parents=True)

    result = _run_worker(out_dir, keep_dirs=True)

    assert result['energy'] == 5.0
    assert result['output_dir'] == os.path.join(str(out_dir), 'BESOS_Output', 'RUN1')


@pytest.mark.parametrize('keep_dirs', [False, True])
def test_worker_reads_the_add_outputs_recorded_by_besos(fake_besos, tmp_path, keep_dirs):
    out_dir = tmp_path / 'results'
    result = _run_worker(out_dir, keep_dirs=keep_dirs, with_add_outputs=True)

    assert result['energy'] == 5.0
    assert result['Heating:Electricity'] == 11.0
    assert result['Cooling:Electricity'] == 22.0
    if keep_dirs:
        assert result['output_dir'] == os.path.join(str(out_dir), 'BESOS_Output', 'RUN1')
    else:
        assert 'output_dir' not in result


def test_worker_without_add_outputs_reports_none(fake_besos, tmp_path):
    result = _run_worker(tmp_path / 'results', keep_dirs=True)

    assert not any(name in result for name in ADD_OUTPUT_NAMES)
    assert not pd.isna(result['output_dir'])
