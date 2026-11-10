"""Tests for the comfort standards defined by their data (proposal B3 of accim 1.2.0, :mod:`accim.sim.standards`) in
the parametric module: the parameter ``comfort_standard`` takes their numbers (``param_accis.modify_ComfStand`` gives
the zones their outdoor metric, and the model their EMS code), the plans keep their categories and comfort modes only,
and the workers of the parallel simulations, which are new processes without the registry of the main process, get
them.
"""
import pickle
import shutil
import warnings
from pathlib import Path

import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder
from accim.parametric_and_optimisation.funcs_for_besos import param_accis
from accim.parametric_and_optimisation.main import ParametricSimulation
from accim.parametric_and_optimisation.patches import _register_comfort_standards
from accim.sim import standards as st

REPO = Path(__file__).resolve().parents[2]
AQILAH = REPO / 'accim' / 'sample_files' / 'comfort_standards' / 'jpn_aqilah2025_fr.yaml'
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists() and EPW.exists()),
                               reason='needs EnergyPlus 25.1 and the sample files of the repository')


@pytest.fixture
def aqilah():
    """JPN Aqilah 2025 (101) in the registry during the test."""
    [definition] = st.load_comfort_standards(AQILAH)
    yield definition
    for number in list(st.registered_comfort_standards()):
        st.unregister_comfort_standard(number)


def _inputs(building):
    from accim.sim.ems.inputs import input_programs, read_inputs

    return [read_inputs(program) for program in input_programs(building).values()]


def test_the_valid_combinations_of_the_registry(aqilah):
    assert param_accis.get_valid_param_combinations()[101] == [[90, 80], [0, 1, 2, 3]]
    plan = pd.DataFrame({'comfort_standard': [101, 101, 101, 1], 'category': [80, 1, 90, 1],
                         'comfort_mode': [1, 1, 3, 3]})
    kept = param_accis.drop_invalid_param_combinations(plan)
    assert kept.values.tolist() == [[101, 80, 1], [101, 90, 3], [1, 1, 3]]
    st.unregister_comfort_standard(101)
    assert 101 not in param_accis.get_valid_param_combinations()


def test_the_workers_register_the_comfort_standards(aqilah):
    # The workers receive them pickled
    definitions = pickle.loads(pickle.dumps(list(st.registered_comfort_standards().values())))
    assert definitions == [aqilah]
    st.unregister_comfort_standard(101)
    _register_comfort_standards(definitions)
    assert st.comfort_standard_definition(101) == aqilah
    # Again (each evaluation of the optimisation), or none: nothing changes
    _register_comfort_standards(definitions)
    _register_comfort_standards(None)
    assert list(st.registered_comfort_standards()) == [101]


class _Evaluator:
    """An evaluator of BESOS with the attribute that run_optimisation gives it, as a process of platypus receives it
    (pickled)."""
    out_dir = None

    def __init__(self):
        from types import SimpleNamespace

        self._accim_comfort_standards = list(st.registered_comfort_standards().values())
        self.problem = SimpleNamespace(add_outputs_list=None)
        self.found = None

    def __call__(self, values, keep_dirs=False):
        self.found = st.comfort_standard_definition(values[0])
        return (1.0,)

    def package_for_platypus(self, results):
        return results


def test_the_evaluations_of_the_optimisation_register_the_comfort_standards(aqilah):
    from accim.parametric_and_optimisation.patches import _patched_eval_func

    evaluator = pickle.loads(pickle.dumps(_Evaluator()))
    # A new process has no registry
    st.unregister_comfort_standard(101)
    assert _patched_eval_func(evaluator, [101]) == (1.0,)
    assert evaluator.found == aqilah


def _model(tmp_path):
    from accim.sim.accis import add_accis_to_idf, load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(building, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    return building


@needs_idd
def test_modify_comf_stand_with_a_comfort_standard_of_the_registry(tmp_path, aqilah):
    from accim.sim.ems.outdoor_metric import has_outdoor_metric_code

    # A model with the ACCIS of the built-in comfort standards only
    building = _model(tmp_path)
    with pytest.warns(UserWarning, match='begins with the running mean of ASHRAE 55'):
        param_accis.modify_ComfStand(building, 101)
    assert all((inputs['ComfStand'], inputs['CustAST_metric'], inputs['CustAST_alpha']) == (101, 2, 0.8)
               for inputs in _inputs(building))
    assert has_outdoor_metric_code(building)
    programs = {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
                for p in building.idfobjects['EnergyManagementSystem:Program']}
    assert 'set ComfTemp = Tout_metric*0.38+16.9' in programs['SetComfTemp']
    assert {'SetAST_CS101_0', 'SetAST_CS101_1', 'SetAST_CS1_0'} <= set(programs)
    # Back to a built-in comfort standard
    param_accis.modify_ComfStand(building, 1)
    assert all(inputs['ComfStand'] == 1 for inputs in _inputs(building))


@needs_idd
def test_a_plan_with_a_comfort_standard_of_the_registry(tmp_path, monkeypatch, aqilah):
    from besos.evaluator import EvaluatorEP

    from accim.sim.accis import load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)
    building = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        simulation = ParametricSimulation(buildings=[building], epws=[str(EPW)],
                                          parameters_type='accim predefined model', output_frequencies=['hourly'],
                                          verbose=False)
        simulation.set_parameters({'comfort_standard': [1, 101], 'category': [1, 80], 'comfort_mode': [1]})
    simulation.set_problem()
    simulation.sampling_full_set()
    plan = simulation.parameters_values_df
    assert plan[['comfort_standard', 'category', 'comfort_mode']].values.tolist() == [[1, 1, 1], [101, 80, 1]]
    # The IDFs of the plan, as the simulations of the parametric module get them (without running EnergyPlus)
    evaluator = EvaluatorEP(problem=simulation.problem, building=simulation.building, epw=str(EPW))
    for row in range(len(plan)):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            evaluator.generate_building(plan, row, str(tmp_path / f'design_{row}'))
        found = _inputs(load_idf(tmp_path / f'design_{row}.idf'))
        expected = tuple(plan.iloc[row][['comfort_standard', 'category', 'comfort_mode']])
        assert all((inputs['ComfStand'], inputs['CAT'], inputs['ComfMod']) == expected for inputs in found)
        if expected[0] == 101:
            assert all(inputs['CustAST_metric'] == 2 for inputs in found)
    # The workers of the parallel simulations get the comfort standards of the registry
    tasks = list(simulation._iter_parametric_task_blueprints(
        grouped_dfs={'model': plan}, epws=[str(EPW)], out_dir=str(tmp_path / 'out'),
        problem_names_inputs=['comfort_standard', 'category', 'comfort_mode'], problem_names_outputs=[],
        output_specs=[], add_output_specs=[], add_output_names=[], keep_dirs=False, keep_input=True))
    assert len(tasks) == 2 and all(task['worker_kwargs']['comfort_standards'] == [aqilah] for task in tasks)
    pickle.dumps(tasks[0]['worker_kwargs'])
