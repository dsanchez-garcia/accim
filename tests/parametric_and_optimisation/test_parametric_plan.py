"""Tests for the simulation plan of run_parametric_simulation and the baseline of set_parameters.

- The ``idf`` column of a plan may name each IDF by identifier, file name or path, and it must
  only name loaded IDFs (before, with one IDF loaded, the column was dropped without warning).
- The results have one row per task, in the order of the plan, with one process or several, and
  repeated rows are simulated once but keep a row each (Morris and Sobol need one result per row).
- set_parameters writes the baseline of the custom model in every loaded IDF.
"""
import concurrent.futures

import pandas as pd
import pytest

import accim.utils
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


class _FakeIDF:
    def __init__(self, idfname):
        self.idfname = idfname


def _make_lightweight_parametric(epws=('Test.epw',)):
    sim = ParametricSimulation(
        buildings=None,
        epws=list(epws),
        parameters_type=None,
        bypass_addAccis=True,
    )
    sim.problem = _DummyProblem(inputs=['x'], outputs=['energy'])
    return sim


def _fake_worker(idf_path, epw, epwname, idf_basename, out_dir, problem_names_inputs,
                 problem_names_outputs, output_specs, add_output_specs, add_output_names,
                 row_dict, keep_dirs, keep_input, sim_files_extensions=None,
                 sim_files_policy='keep', additional_params=None):
    _fake_worker.calls.append((epwname, row_dict['x']))
    result = {problem_names_outputs[0]: float(row_dict['x']) * 10.0, 'epw': epwname, 'idf': idf_basename}
    if keep_input:
        result.update(row_dict)
    return result


class _InlineExecutor:
    """Runs each task when it is submitted, in this process."""

    def __init__(self, max_workers=None):
        self.max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def submit(self, fn, *args, **kwargs):
        future = concurrent.futures.Future()
        future.set_result(fn(*args, **kwargs))
        return future


@pytest.fixture
def fake_run(monkeypatch):
    _fake_worker.calls = []
    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _fake_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    return _fake_worker


@pytest.fixture
def parallel_finishing_in_reverse(monkeypatch):
    # Parallel simulations finish in any order: here, the last submitted finishes first.
    monkeypatch.setattr(concurrent.futures, 'ProcessPoolExecutor', _InlineExecutor)
    monkeypatch.setattr(
        concurrent.futures,
        'as_completed',
        lambda futures, *args, **kwargs: list(reversed(list(futures))),
    )


# ----------------------------------------------------------------------------- idf column

def test_plan_may_name_the_loaded_idf_by_identifier_file_name_or_path():
    sim = _make_lightweight_parametric()
    sim.buildings = [_FakeIDF('C:/models/office_a.idf')]
    sim.building = sim.buildings[0]
    plan = pd.DataFrame({'x': [1, 2, 3], 'idf': ['office_a', 'office_a.idf', 'models/office_a.idf']})

    grouped = sim._prepare_dataframe_for_buildings(df=plan, epws=['Test.epw'])

    assert list(grouped) == ['office_a']
    assert grouped['office_a']['x'].tolist() == [1, 2, 3]
    assert 'idf' not in grouped['office_a'].columns


def test_plan_naming_an_idf_that_is_not_loaded_raises_with_one_idf():
    sim = _make_lightweight_parametric()
    sim.buildings = [_FakeIDF('office_a.idf')]
    sim.building = sim.buildings[0]
    plan = pd.DataFrame({'x': [1, 2], 'idf': ['office_a', 'office_b.idf']})

    with pytest.raises(ValueError, match="office_b"):
        sim._prepare_dataframe_for_buildings(df=plan, epws=['Test.epw'])


def test_plan_with_several_idfs_groups_the_rows_by_identifier():
    sim = _make_lightweight_parametric()
    sim.buildings = [_FakeIDF('office_a.idf'), _FakeIDF('office_b.idf')]
    sim.building = sim.buildings[0]
    plan = pd.DataFrame({'x': [1, 2, 3], 'idf': ['office_b.idf', 'office_a', 'D:\\models\\office_b.idf']})

    grouped = sim._prepare_dataframe_for_buildings(df=plan, epws=['Test.epw'])

    assert sorted(grouped) == ['office_a', 'office_b']
    assert grouped['office_b']['x'].tolist() == [1, 3]
    assert grouped['office_a']['x'].tolist() == [2]


def test_plan_with_several_idfs_still_rejects_unknown_ones():
    sim = _make_lightweight_parametric()
    sim.buildings = [_FakeIDF('office_a.idf'), _FakeIDF('office_b.idf')]
    sim.building = sim.buildings[0]
    plan = pd.DataFrame({'x': [1], 'idf': ['office_c']})

    with pytest.raises(ValueError, match='office_c'):
        sim._prepare_dataframe_for_buildings(df=plan, epws=['Test.epw'])


# ----------------------------------------------------------------------------- order and repeated rows

def test_repeated_rows_are_simulated_once_and_keep_a_row_each(fake_run, tmp_path):
    sim = _make_lightweight_parametric()
    plan = pd.DataFrame({'x': [3, 1, 2, 1]})

    results = sim.run_parametric_simulation(
        df=plan, out_dir=str(tmp_path / 'out'), processes=1, keep_dirs=False, keep_input=True,
    )

    assert [x for (_, x) in fake_run.calls] == [3, 1, 2]
    assert results['x'].tolist() == [3, 1, 2, 1]
    assert results['energy'].tolist() == [30.0, 10.0, 20.0, 10.0]


def test_parallel_results_follow_the_order_of_the_plan(fake_run, parallel_finishing_in_reverse, tmp_path):
    sim = _make_lightweight_parametric()
    plan = pd.DataFrame({'x': [3, 1, 2, 4]})

    results = sim.run_parametric_simulation(
        df=plan, out_dir=str(tmp_path / 'out'), processes=2, keep_dirs=False, keep_input=True,
    )

    assert [x for (_, x) in fake_run.calls] == [3, 1, 2, 4]
    assert results['x'].tolist() == [3, 1, 2, 4]
    assert results['energy'].tolist() == [30.0, 10.0, 20.0, 40.0]


def test_parallel_results_keep_repeated_rows_in_place(fake_run, parallel_finishing_in_reverse, tmp_path):
    sim = _make_lightweight_parametric()
    plan = pd.DataFrame({'x': [5, 3, 5, 1, 3]})

    results = sim.run_parametric_simulation(
        df=plan, out_dir=str(tmp_path / 'out'), processes=3, keep_dirs=False, keep_input=True,
    )

    assert sorted(x for (_, x) in fake_run.calls) == [1, 3, 5]
    assert results['x'].tolist() == [5, 3, 5, 1, 3]


def test_results_of_several_epws_follow_the_tasks_of_each_epw(fake_run, parallel_finishing_in_reverse, tmp_path):
    sim = _make_lightweight_parametric(epws=('A.epw', 'B.epw'))
    plan = pd.DataFrame({'x': [2, 1, 3]})

    results = sim.run_parametric_simulation(
        df=plan, out_dir=str(tmp_path / 'out'), processes=2, keep_dirs=False, keep_input=True,
    )

    assert results['epw'].tolist() == ['A', 'A', 'A', 'B', 'B', 'B']
    assert results['x'].tolist() == [2, 1, 3, 2, 1, 3]


# ----------------------------------------------------------------------------- custom-model baseline

CUSTAST_SETTERS = [
    'modify_ComfStand', 'modify_ComfMod', 'modify_CAT',
    'modify_CustAST_m', 'modify_CustAST_n',
    'modify_CustAST_ASToffset', 'modify_CustAST_ASTaul', 'modify_CustAST_ASTall',
    'modify_CustAST_ACSToffset', 'modify_CustAST_AHSToffset',
    'modify_CustAST_ACSTaul', 'modify_CustAST_AHSTaul',
    'modify_CustAST_ACSTall', 'modify_CustAST_AHSTall',
]


def test_custom_model_baseline_is_written_in_every_building(monkeypatch):
    calls = []

    def _recorder(setter_name):
        return lambda building, value: calls.append((building.idfname, setter_name, value))

    for setter_name in CUSTAST_SETTERS:
        monkeypatch.setattr(main_module.bf_accim, setter_name, _recorder(setter_name))
    monkeypatch.setattr(
        accim.utils,
        'get_accim_args',
        lambda building: {'CustAST': {k: 0 for k in ['m', 'n', 'ACSToffset', 'AHSToffset', 'ACSTaul', 'AHSTaul', 'ACSTall', 'AHSTall']}},
    )

    sim = _make_lightweight_parametric()
    sim.parameters_type = 'accim custom model'
    sim.is_accim_custom_model = True
    sim.is_accim_predef_model = False
    sim.is_apmv_setpoints = False
    sim.buildings = [_FakeIDF('office_a.idf'), _FakeIDF('office_b.idf')]
    sim.building = sim.buildings[0]

    sim.set_parameters(accis_params_dict={
        'CustAST_m': (0.2, 0.6),
        'CustAST_n': (10.0, 20.0),
        'CustAST_ASToffset': (1.0, 4.0),
    })

    for idfname in ['office_a.idf', 'office_b.idf']:
        written = {(setter, value) for (name, setter, value) in calls if name == idfname}
        assert ('modify_ComfStand', 99) in written
        assert ('modify_ComfMod', 3) in written
        assert ('modify_CAT', 80) in written
        # Limits not among the parameters get the default values in both buildings.
        assert ('modify_CustAST_ACSTaul', 33.5) in written
        assert ('modify_CustAST_AHSTaul', 33.5) in written
        assert ('modify_CustAST_ACSTall', 10) in written
        assert ('modify_CustAST_AHSTall', 10) in written
        assert not any(setter == 'modify_CustAST_ACSToffset' for (setter, _) in written)
