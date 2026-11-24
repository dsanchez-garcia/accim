"""Tests of the cases of the script of the validation study of F3 (``tools/indoor_adaptation_study.py``), without
simulations. Since the decisions of the author of 2026-11-19 (``notes/decisions.md``), the study is narrowed to what
the paper of the causal SET model specifies: one case of that model with the clothing insulation, the activity level
and the air speed of the People objects of the model (``iii_model``), besides the static reference (b) and the adaptive
setpoints of case (ii); the script runs the cases of the study by default (``--cases study``), and ``--cases all``
still runs all of them. Since those of 2026-11-24, the study also has the PMV setpoints of category II as temperature
setpoints (``i_pmv``, the static reference (a), with a hook), five cases, and runs in mixed mode by default."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / 'tools' / 'indoor_adaptation_study.py'


def _script():
    spec = importlib.util.spec_from_file_location('indoor_adaptation_study', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_cases_of_the_study():
    study = _script()
    cases = study.cases()

    assert study.STUDY_CASES == ('i_pmv', 'i_fixed', 'ii_en16798', 'ii_ashrae55', 'iii_model')
    assert set(study.STUDY_CASES) <= set(cases)
    # The causal SET model with the inputs of the occupants of the model: no options that change the clothing or the air
    # speed (fans), nor the limiter of the drift; the hook reads them from the People objects
    assert cases['iii_model'][1:] == (1, 2, 3, {'set': True})
    assert study.fans(cases['iii_model'], 0.1) is None
    # The PMV setpoints of category II, with the inputs of the occupants of the model too, and a hook of their own
    assert cases['i_pmv'][1:] == (1, 2, 3, {'pmv': True}) and study.PMV_LIMIT == 0.5
    # The comfort temperature of the fixed setpoints is their midpoint (the ventilation setpoint of mixed mode)
    static = study.FIXED_SETPOINTS['static_setpoints']
    assert study.FIXED_SETPOINTS['comfort_temperature'] == {
        'slope': 0.0, 'intercept': (static['heating'] + static['cooling']) / 2}
    # The other cases stay, for sensitivities
    assert {'iii_seasonal', 'iii_dynamic', 'iv_v12', 'v_iii_dynamic_r025'} <= set(cases)


def test_list_marks_the_cases_of_the_study(tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path), '--list'], capture_output=True, text=True,
                            env={**os.environ, 'PYTHONPATH': str(REPO)})

    assert result.returncode == 0, result.stderr
    assert [line.split(':')[0] for line in result.stdout.splitlines() if line.endswith('(study)')] == [
        'i_pmv', 'i_fixed', 'ii_en16798', 'ii_ashrae55', 'iii_model']


def test_the_models_are_in_mixed_mode_by_default():
    study = _script()

    # Mixed mode with the VRF systems of accim: the HVAC mode and the ventilation control of the study
    assert study.accis_arguments('vrf_mm', 2, 2) == {
        'script_type': 'vrf_mm', 'supply_air_temp_input_method': 'temperature difference', 'hvac_mode': [2],
        'ventilation_control': [2], 'ventilation_setpoint_offset': [0], 'min_outdoor_temp_offset': [50],
        'max_wind_speed': [50]}
    # Full air-conditioning as before 2026-11-24, and the HVAC systems of the model (no supply air temperature)
    assert study.accis_arguments('vrf_ac', 2, 2) == {
        'script_type': 'vrf_ac', 'supply_air_temp_input_method': 'temperature difference'}
    assert study.accis_arguments('ex_mm', 0, 3, 1, 7, 6) == {
        'script_type': 'ex_mm', 'hvac_mode': [0], 'ventilation_control': [3], 'ventilation_setpoint_offset': [1],
        'min_outdoor_temp_offset': [7], 'max_wind_speed': [6]}
    assert study.accis_arguments('ex_ac', 2, 2) == {'script_type': 'ex_ac'}


def test_the_blocks_of_the_zones_without_the_pattern_of_designbuilder():
    study = _script()

    # The occupied zones of the model, by their names: those of DesignBuilder need no block
    assert study.block_zone_hierarchy(['Block1:Zone1', 'Block1:Zone2']) is None
    assert study.block_zone_hierarchy(['Core_ZN', 'Block1:Zone1', 'Perimeter_ZN_1']) == {
        'Building': ['Core_ZN', 'Perimeter_ZN_1']}


class _Model:
    """A model with its SimulationControl objects only (as that of eppy: idfobjects and newidfobject)."""

    def __init__(self, *controls):
        self.idfobjects = {'SimulationControl': list(controls)}

    def newidfobject(self, key, **fields):
        self.idfobjects[key].append(SimpleNamespace(**fields))


def _control(sizing_periods, run_periods):
    return SimpleNamespace(Do_Zone_Sizing_Calculation='Yes', Run_Simulation_for_Sizing_Periods=sizing_periods,
                           Run_Simulation_for_Weather_File_Run_Periods=run_periods)


def test_the_models_simulate_the_run_periods_and_not_the_sizing_periods():
    study = _script()

    def simulated(model):
        return [(control.Run_Simulation_for_Sizing_Periods, control.Run_Simulation_for_Weather_File_Run_Periods)
                for control in model.idfobjects['SimulationControl']]

    # The example files of EnergyPlus simulate their design days only: found on 2026-11-24 with the small office of the
    # DOE, whose results from 15 to 16 July were the 48 hours of its design days of 21 January and 21 July. Their
    # sizing calculations stay
    design_days = _Model(_control('YES', 'NO'))
    assert study.simulate_run_periods(design_days) and simulated(design_days) == [('No', 'Yes')]
    assert design_days.idfobjects['SimulationControl'][0].Do_Zone_Sizing_Calculation == 'Yes'
    # Both: the rows of the design days would be among those of the results
    both = _Model(_control('Yes', 'Yes'))
    assert study.simulate_run_periods(both) and simulated(both) == [('No', 'Yes')]
    # A model that simulates the run periods only does not change (nor the text of its fields), as the sample model
    same = _Model(_control('no', 'YES'))
    assert not study.simulate_run_periods(same) and simulated(same) == [('no', 'YES')]
    # Without the object, EnergyPlus would simulate both
    without = _Model()
    assert study.simulate_run_periods(without) and simulated(without) == [('No', 'Yes')]
