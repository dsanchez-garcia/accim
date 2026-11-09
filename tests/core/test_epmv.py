"""Tests for the setpoints based on the ePMV of Fanger and Toftum (2002), accim.sim.apmv.apply_epmv_setpoints (the
index 'epmv' of accim.sim.pmv_index), and their metabolic correction.

ePMV = e*PMV, with the expectancy factor e in the cooling season and on the warm side of the scale only (also on the
cool side with apply_to_heating); the PMV setpoint of the cooling thermostat is ePMV/e. The metabolic correction reduces
the activity level by 6.7 % for each unit of PMV above neutral, with the PMV of the previous timestep. The EMS programs
run with the Erl interpreter of accim; the last test runs the sample model with both backends of EnergyPlus 25.1.
"""
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import find_energyplus
from accim.sim import apmv
from accim.sim.accis import load_idf
from accim.sim.ems.erl import ErlProgramSet
from accim.sim.energyplus_api import read_ems, run_simulations
from accim.sim.pmv_index import metabolic_correction_names

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
# One People object for the two floors (a SpaceList), with a Schedule:Year of activity level, as in OpenStudio models
RESIDENTIAL_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'example_apmv_setpoints_paper'
                   / 'TestModel_TestResidentialUnit.idf')
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
ZONES = ('Block1_Zone1', 'Block1_Zone2')
TIMESTEP = 0.25
COOLING_DAY, HEATING_DAY = 180.0, 30.0
NO_TOLERANCES = dict(cooling_setpoint_tolerance_cooling_season=0, cooling_setpoint_tolerance_heating_season=0,
                     heating_setpoint_tolerance_cooling_season=0, heating_setpoint_tolerance_heating_season=0)


def _model(tmp_path, source=SAMPLE_IDF):
    """A model of EnergyPlus 25.1, read by eppy."""
    if find_energyplus('25.1', required=False) is None or not source.exists():
        pytest.skip('needs EnergyPlus 25.1 (its IDD) and the sample IDFs of the repository')
    path = tmp_path / source.name
    shutil.copy(source, path)
    return load_idf(path)


def _programs(building):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
            for p in building.idfobjects['EnergyManagementSystem:Program']}


def _erl(building):
    """The EMS programs of a model, compiled by the Erl interpreter, and those run at the beginning of each timestep,
    in their order."""
    ems = read_ems(building)
    erl = ErlProgramSet(ems.programs, global_variables=ems.global_names(), actuators=[a[0] for a in ems.actuators])
    erl.strict = True
    programs = [program for _, calling_point, names in ems.calling_managers
                if calling_point == 'BEGINTIMESTEPBEFOREPREDICTOR' for program in names]
    return erl, programs


def _timestep(erl, programs, day, pmv, occupants=2.0, zones=ZONES, **sensors):
    """Run the programs of a timestep: ``pmv`` and ``occupants`` are those of every zone, or dicts by zone."""
    erl.set('DayOfYear', day)
    erl.set('ZoneTimeStep', TIMESTEP)
    for zone in zones:
        erl.set(f'PMV_{zone}', pmv[zone] if isinstance(pmv, dict) else pmv)
        erl.set(f'People_Occupant_Count_{zone}', occupants[zone] if isinstance(occupants, dict) else occupants)
    for name, value in sensors.items():
        erl.set(name, value)
    for program in programs:
        erl.run(program)


@pytest.mark.parametrize('arguments, message', [
    (dict(expectancy_factor=0.4), 'expectancy_factor must be between 0.5 and 1.0'),
    (dict(expectancy_factor=1.1), 'expectancy_factor must be between 0.5 and 1.0'),
    (dict(expectancy_factor={'Block1:Zone1': 0.3}), 'not 0.3'),
    (dict(default_expectancy_factor=1.2), 'default_expectancy_factor must be between'),
    (dict(expectancy_factor='high'), "not 'high'"),
    (dict(apply_to_heating='yes'), "apply_to_heating must be True or False, not 'yes'"),
    (dict(metabolic_correction=1), 'metabolic_correction must be True or False, not 1'),
])
def test_the_arguments_of_the_epmv_are_checked(tmp_path, arguments, message):
    building = _model(tmp_path)
    with pytest.raises(ValueError, match=message):
        apmv.apply_epmv_setpoints(building, verbose=False, **arguments)
    # Nothing was added to the model
    assert not building.idfobjects['EnergyManagementSystem:Program']


def test_applying_the_expectancy_factor_to_the_heating_setpoint_warns(tmp_path):
    building = _model(tmp_path)
    with pytest.warns(UserWarning, match=r'Fanger and Toftum \(2002\) apply the expectancy factor of the ePMV only to '
                                         r'the upper limit'):
        apmv.apply_epmv_setpoints(building, apply_to_heating=True, verbose=False)


def test_the_ems_objects_of_the_epmv_setpoints(tmp_path):
    building = _model(tmp_path)
    apmv.apply_epmv_setpoints(building, expectancy_factor={'Block1:Zone1': 0.7}, verbose=False)

    programs = _programs(building)
    zone = 'Block1_Zone1'
    assert programs[f'set_zone_input_data_{zone}'][0] == f'set expectancy_factor_{zone} = 0.7'
    # The zones missing in the dictionary take default_expectancy_factor
    assert programs['set_zone_input_data_Block1_Zone2'][0] == 'set expectancy_factor_Block1_Zone2 = 0.8'
    lines = programs[f'apply_ePMV_{zone}']
    assert lines[:2] == ['if CoolingSeason == 1', f'set e_{zone} = expectancy_factor_{zone}']
    assert f'set e_{zone} = 1' in lines
    # Only the cooling setpoint is divided by e
    assert f'set PMV_C_SP_act_{zone} = ePMV_C_SP_{zone}/e_{zone}' in lines
    assert f'set PMV_H_SP_act_{zone} = ePMV_H_SP_{zone}' in lines
    assert programs[f'monitor_ePMV_{zone}'] == [f'if PMV_{zone} > 0', f'set ePMV_{zone} = e_{zone}*PMV_{zone}', 'else',
                                                 f'set ePMV_{zone} = PMV_{zone}', 'endif']
    assert programs[f'count_ePMV_comfort_hours_{zone}'][0] == f'if ePMV_{zone} < ePMV_H_SP_noTol_{zone}'
    assert not any(name.startswith('correct_activity_') for name in programs)
    outputs = {o.Name: o.EMS_Variable_Name for o in building.idfobjects['EnergyManagementSystem:OutputVariable']}
    assert outputs[f'Expectancy Factor_{zone}'] == f'e_{zone}' and outputs[f'ePMV_{zone}'] == f'ePMV_{zone}'
    assert outputs[f'ePMV Cooling Setpoint_{zone}'] == f'ePMV_C_SP_{zone}'
    global_variables = {gv.Erl_Variable_1_Name for gv in building.idfobjects['EnergyManagementSystem:GlobalVariable']}
    assert {f'e_{zone}', f'expectancy_factor_{zone}', f'ePMV_{zone}'} <= global_variables

    building = _model(tmp_path)
    apmv.apply_epmv_setpoints(building, apply_to_heating=True, verbose=False)
    programs = _programs(building)
    assert f'set PMV_H_SP_act_{zone} = ePMV_H_SP_{zone}/e_{zone}' in programs[f'apply_ePMV_{zone}']
    assert programs[f'monitor_ePMV_{zone}'] == [f'set ePMV_{zone} = e_{zone}*PMV_{zone}']


@pytest.mark.parametrize('apply_to_heating', [False, True])
def test_the_pmv_setpoints_of_the_thermostats_and_the_epmv(tmp_path, apply_to_heating):
    building = _model(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        apmv.apply_epmv_setpoints(building, expectancy_factor={'Block1:Zone1': 0.7}, apply_to_heating=apply_to_heating,
                                  verbose=False, **NO_TOLERANCES)
    erl, programs = _erl(building)
    zone, e = 'Block1_Zone1', 0.7

    # Cooling season: ePMV setpoints of -0.5 and 0.5; the PMV setpoints are 0.5/e and -0.5 (or -0.5/e)
    _timestep(erl, programs, COOLING_DAY, 0.6)
    assert erl.get(f'e_{zone}') == e and erl.get('e_Block1_Zone2') == 0.8
    assert erl.get(f'PMV_C_SP_act_{zone}') == pytest.approx(0.5 / e) == pytest.approx(0.7142857)
    assert erl.get(f'PMV_H_SP_act_{zone}') == pytest.approx(-0.5 / e if apply_to_heating else -0.5)
    assert erl.get(f'ePMV_{zone}') == pytest.approx(e * 0.6)
    assert erl.get(f'comfhour_{zone}') == TIMESTEP
    _timestep(erl, programs, COOLING_DAY, 0.8)
    assert erl.get(f'ePMV_{zone}') == pytest.approx(0.56) and erl.get(f'discomfhour_heat_{zone}') == TIMESTEP
    _timestep(erl, programs, COOLING_DAY, -0.6)
    assert erl.get(f'ePMV_{zone}') == pytest.approx(e * -0.6 if apply_to_heating else -0.6)
    assert erl.get(f'discomfhour_cold_{zone}') == (0 if apply_to_heating else TIMESTEP)
    # Heating season: e is 1, so the setpoints and the index are those of the PMV
    _timestep(erl, programs, HEATING_DAY, 0.6)
    assert erl.get(f'e_{zone}') == 1
    assert (erl.get(f'PMV_H_SP_act_{zone}'), erl.get(f'PMV_C_SP_act_{zone}')) == (-0.5, 0.5)
    assert erl.get(f'ePMV_{zone}') == 0.6 and erl.get(f'discomfhour_heat_{zone}') == TIMESTEP
    # Unoccupied
    _timestep(erl, programs, COOLING_DAY, 0.6, occupants=0.0)
    assert (erl.get(f'PMV_H_SP_act_{zone}'), erl.get(f'PMV_C_SP_act_{zone}')) == (-100, 100)


def test_with_an_expectancy_factor_of_1_the_epmv_setpoints_are_the_pmv_setpoints(tmp_path):
    epmv_model = _model(tmp_path)
    apmv.apply_epmv_setpoints(epmv_model, expectancy_factor=1, verbose=False)
    pmv_model = _model(tmp_path)
    apmv.apply_pmv_setpoints(pmv_model, verbose=False)
    erl_epmv, programs_epmv = _erl(epmv_model)
    erl_pmv, programs_pmv = _erl(pmv_model)

    for day in (HEATING_DAY, COOLING_DAY):
        for pmv in (-1.2, -0.45, 0.0, 0.45, 0.9):
            for occupants in (0.0, 2.0):
                _timestep(erl_epmv, programs_epmv, day, pmv, occupants)
                _timestep(erl_pmv, programs_pmv, day, pmv, occupants)
                for zone in ZONES:
                    for variable in ('PMV_H_SP_act', 'PMV_C_SP_act', 'comfhour', 'discomfhour_cold',
                                     'discomfhour_heat', 'discomfhour', 'occupied_hour'):
                        assert erl_epmv.get(f'{variable}_{zone}') == erl_pmv.get(f'{variable}_{zone}'), \
                            (day, pmv, occupants, zone, variable)
                    assert erl_epmv.get(f'ePMV_{zone}') == pmv


def test_the_metabolic_correction(tmp_path):
    building = _model(tmp_path)
    schedules = {str(p.Name): str(p.Activity_Level_Schedule_Name) for p in building.idfobjects['People']}
    apmv.apply_epmv_setpoints(building, expectancy_factor=0.7, metabolic_correction=True, verbose=False)

    programs = _programs(building)
    managers = [m.Program_Name_1 for m in building.idfobjects['EnergyManagementSystem:ProgramCallingManager']]
    for people_name, base in schedules.items():
        names = metabolic_correction_names(people_name)
        # The People object reads a copy of its activity level schedule, which the EMS sets
        people = building.getobject('People', people_name)
        assert people.Activity_Level_Schedule_Name == names['schedule']
        original, copy = building.getobject('Schedule:Compact', base), building.getobject('Schedule:Compact',
                                                                                             names['schedule'])
        assert copy.fieldvalues[2:] == original.fieldvalues[2:]
        sensor = building.getobject('EnergyManagementSystem:Sensor', names['base'])
        assert (sensor.OutputVariable_or_OutputMeter_Index_Key_Name, sensor.OutputVariable_or_OutputMeter_Name) == (
            base, 'Schedule Value')
        actuator = building.getobject('EnergyManagementSystem:Actuator', names['actuator'])
        assert (actuator.Actuated_Component_Unique_Name, actuator.Actuated_Component_Type) == (names['schedule'],
                                                                                               'Schedule:Compact')
        assert names['program'] in programs and names['program'] in managers[-2:]
    outputs = {o.Name: o.EMS_Variable_Name for o in building.idfobjects['EnergyManagementSystem:OutputVariable']}
    assert outputs['Metabolic Correction Factor_People_Block1_Zone1'] == 'metabolic_factor_People_Block1_Zone1'
    assert outputs['Corrected Activity Level_People_Block1_Zone1'] == 'Activity_act_People_Block1_Zone1'

    erl, run = _erl(building)
    base = {f'Activity_base_People_{zone}': 120.0 for zone in ZONES}
    for day, pmv, factor in ((COOLING_DAY, 1.0, 1 - 0.067), (COOLING_DAY, 1.5, 1 - 0.067 * 1.5),
                             (COOLING_DAY, -0.8, 1), (COOLING_DAY, 4.2, 1 - 0.067 * 3), (HEATING_DAY, 1.5, 1)):
        _timestep(erl, run, day, pmv, **base)
        for zone in ZONES:
            assert erl.get(f'metabolic_factor_People_{zone}') == pytest.approx(factor), (day, pmv)
            assert erl.get(f'Activity_act_People_{zone}') == pytest.approx(120 * factor), (day, pmv)

    # Applied again: warnings, and nothing is added
    count = len(building.idfobjects['EnergyManagementSystem:Program'])
    with pytest.warns(UserWarning, match="already has the metabolic correction"):
        apmv.apply_epmv_setpoints(building, expectancy_factor=0.7, metabolic_correction=True, verbose=False)
    assert len(building.idfobjects['EnergyManagementSystem:Program']) == count


def test_the_metabolic_correction_of_a_people_object_of_several_zones(tmp_path):
    building = _model(tmp_path, RESIDENTIAL_IDF)
    people = building.idfobjects['People'][0]
    base = str(people.Activity_Level_Schedule_Name)
    with pytest.warns(UserWarning, match="applies to several zones .* the mean PMV of its occupants"):
        apmv.apply_epmv_setpoints(building, metabolic_correction=True, verbose=False)

    names = metabolic_correction_names(people.Name)
    assert building.getobject('Schedule:Year', names['schedule']) is not None
    actuator = building.getobject('EnergyManagementSystem:Actuator', names['actuator'])
    assert actuator.Actuated_Component_Type == 'Schedule:Year'
    erl, run = _erl(building)
    zones = [f'Floor_{n}_Residential_Living_Occupants' for n in (1, 2)]
    sensors = {names['base']: 100.0}
    # The PMV of each floor, weighted by its occupants
    _timestep(erl, run, COOLING_DAY, {zones[0]: 1.0, zones[1]: 2.0}, {zones[0]: 3.0, zones[1]: 1.0}, zones, **sensors)
    assert erl.get(names['factor']) == pytest.approx(1 - 0.067 * 1.25)
    # Unoccupied: the simple mean
    _timestep(erl, run, COOLING_DAY, {zones[0]: 1.0, zones[1]: 2.0}, 0.0, zones, **sensors)
    assert erl.get(names['factor']) == pytest.approx(1 - 0.067 * 1.5)
    assert erl.get(names['actuator']) == pytest.approx(100 * (1 - 0.067 * 1.5))
    assert base != names['schedule']


def test_the_activity_level_is_set_before_the_metabolic_correction(tmp_path):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, activity_level=100, verbose=False)
    apmv.apply_epmv_setpoints(building, metabolic_correction=True, verbose=False)
    # The correction reads the activity level of set_pmv_input_parameters
    sensor = building.getobject('EnergyManagementSystem:Sensor', 'Activity_base_People_Block1_Zone1')
    assert sensor.OutputVariable_or_OutputMeter_Index_Key_Name == 'Sch_Act_People_Block1_Zone1'

    # Afterwards, a new activity level would remove the correction
    with pytest.raises(ValueError, match="has the metabolic correction of the ePMV setpoints .* before applying"):
        apmv.set_pmv_input_parameters(building, activity_level={'Block1:Zone1': 120}, verbose=False)
    assert building.getobject('People', 'People Block1:Zone1').Activity_Level_Schedule_Name == (
        'ePMV_Activity_People_Block1_Zone1')
    # The other inputs of the PMV can still be set
    apmv.set_pmv_input_parameters(building, air_velocity=0.2, verbose=False)


def test_the_parametric_modifier_of_the_expectancy_factor(tmp_path):
    from accim.parametric_and_optimisation.funcs_for_besos import param_apmv

    building = _model(tmp_path)
    apmv.apply_epmv_setpoints(building, verbose=False)
    param_apmv.change_expectancy_factor_all_zones(building, 0.6)
    param_apmv.change_pmv_cooling_setpoint_all_zones(building, 0.7)
    for zone in ZONES:
        assert _programs(building)[f'set_zone_input_data_{zone}'][:2] == [f'set expectancy_factor_{zone} = 0.6',
                                                                         f'set pmv_cooling_sp_{zone} = 0.7']
    with pytest.raises(ValueError, match='between 0.5 and 1.0, not 0.4'):
        param_apmv.change_expectancy_factor_all_zones(building, 0.4)
    # A model with the setpoints of another index has no expectancy factor
    building = _model(tmp_path)
    apmv.apply_apmv_setpoints(building, verbose=False)
    with pytest.raises(ValueError, match='has no line "set expectancy_factor_'):
        param_apmv.change_expectancy_factor_all_zones(building, 0.6)


def _energyplus_with_api(version):
    folder = find_energyplus(version, required=False)
    return folder if folder is not None and (folder / 'pyenergyplus').is_dir() else None


def _column(results, text):
    columns = [c for c in results.columns if text in c]
    assert len(columns) == 1, (text, columns)
    return results[columns[0]]


@pytest.mark.skipif(not (_energyplus_with_api('25.1') and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')
def test_the_epmv_setpoints_with_both_backends(tmp_path):
    building = _model(tmp_path)
    apmv.add_vrf_system(building, verbose=False)
    apmv.apply_epmv_setpoints(building, output_frequencies=['timestep'], expectancy_factor=0.7,
                              metabolic_correction=True, verbose=False)
    for variable in ('People Total Heating Rate', 'People Occupant Count'):
        building.newidfobject('Output:Variable', Key_Value='*', Variable_Name=variable, Reporting_Frequency='Timestep')
    # Three days of July, after the sizing of the design days
    run_period = building.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month, run_period.Begin_Year = 7, 1, 2002
    run_period.End_Month, run_period.End_Day_of_Month, run_period.End_Year = 7, 3, 2002
    model = tmp_path / 'model.idf'
    building.saveas(str(model))

    energyplus = _energyplus_with_api('25.1') / 'energyplus.exe'
    ems = subprocess.run([str(energyplus), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-r', '-x',
                          '-w', str(SAMPLE_EPW), str(model)], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
    assert '** Severe' not in (tmp_path / 'ems' / 'run.err').read_text(errors='ignore')
    results = run_simulations([(model, SAMPLE_EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error

    ems_results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    # The setpoints, the ePMV and the corrected activity levels are those of the PMV of the same previous timestep;
    # the results of EnergyPlus differ by rounding, as with the other indices (see test_pmv_index.py)
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=False, rtol=1e-6, atol=1e-6)
    # The run period (ReadVarsESO also writes the design days)
    days = ems_results[ems_results['Date/Time'].str.strip().str.startswith('07/0')]
    for zone, people in (('Block1_Zone1', 'BLOCK1:ZONE1'), ('Block1_Zone2', 'BLOCK1:ZONE2')):
        previous = _column(days, f'{people}:Zone Thermal Comfort Fanger Model PMV').shift(1).iloc[1:]
        epmv = _column(days, f'EMS:ePMV_{zone} [').iloc[1:]
        np.testing.assert_allclose(epmv, np.where(previous > 0, 0.7 * previous, previous), atol=1e-6)
        factor = _column(days, f'Metabolic Correction Factor_People_{zone}').iloc[1:]
        np.testing.assert_allclose(factor, 1 - 0.067 * previous.clip(0, 3), atol=1e-6)
        assert factor.min() < 0.99
        # While the zone is occupied, the PMV setpoint of the cooling thermostat is 0.4/e (with the tolerance)
        cooling = _column(days, f'PMV_C_SP_{people}:Schedule Value')
        assert set(cooling.round(6)) <= {round(0.4 / 0.7, 6), 100.0} and (cooling < 1).any()
        # The heat gains of the occupants follow the corrected activity level from the next timestep
        activity = _column(days, f'Corrected Activity Level_People_{zone}')
        occupants = _column(days, f'PEOPLE {people}:People Occupant Count')
        gains = _column(days, f'PEOPLE {people}:People Total Heating Rate')
        occupied = (occupants > 0).iloc[1:]
        np.testing.assert_allclose(gains.iloc[1:][occupied], (occupants * activity.shift(1)).iloc[1:][occupied],
                                   rtol=1e-6)
