"""Tests for accim.sim.pmv_index, the engine of the setpoints based on indices derived from the PMV, and for the
setpoints of the PMV (accim.sim.apmv.apply_pmv_setpoints).

apply_apmv_setpoints calls the engine with the index 'apmv'; the golden master (s07 and s08) checks that its output
IDFs did not change. The EMS programs are run with the Erl interpreter of accim (the rules of the EMS), and the last
test runs the PMV setpoints with both backends of EnergyPlus 25.1.
"""
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from accim.energyplus import find_energyplus
from accim.sim import apmv
from accim.sim.accis import load_idf
from accim.sim.ems.erl import ErlProgramSet
from accim.sim.energyplus_api import read_ems, run_simulations
from accim.sim.pmv_index import PMV_INDICES, apply_pmv_index_setpoints, get_pmv_index

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
ZONES = ('Block1_Zone1', 'Block1_Zone2')
TIMESTEP = 0.25


def _model(tmp_path):
    """The sample model with two zones (EnergyPlus 25.1), read by eppy."""
    if find_energyplus('25.1', required=False) is None or not SAMPLE_IDF.exists():
        pytest.skip('needs EnergyPlus 25.1 (its IDD) and the sample IDF of the repository')
    path = tmp_path / 'TestModel.idf'
    shutil.copy(SAMPLE_IDF, path)
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


def _timestep(erl, programs, day, pmv, occupants):
    """Run the programs of a timestep with the same PMV and occupants in both zones."""
    erl.set('DayOfYear', day)
    erl.set('ZoneTimeStep', TIMESTEP)
    for zone in ZONES:
        erl.set(f'PMV_{zone}', pmv)
        erl.set(f'People_Occupant_Count_{zone}', occupants)
    for program in programs:
        erl.run(program)


def test_the_indices():
    assert {'apmv', 'pmv'} <= set(PMV_INDICES)
    assert get_pmv_index('aPMV') is PMV_INDICES['apmv']
    with pytest.raises(ValueError, match="'athb' is not an index derived from the PMV"):
        get_pmv_index('athb')


def test_the_parameters_of_the_index_are_checked(tmp_path):
    building = _model(tmp_path)
    with pytest.raises(ValueError, match=r"\['lambda'\] are not parameters of the index 'apmv'"):
        apply_pmv_index_setpoints(building, 'apmv', {'lambda': 0.3}, verbose=False)
    with pytest.raises(ValueError, match="of the index 'pmv', whose parameters are none"):
        apply_pmv_index_setpoints(building, 'pmv', {'adaptive_coefficient_cooling': 0.3}, verbose=False)
    # Nothing was added to the model
    assert not building.idfobjects['EnergyManagementSystem:Program']


def test_apply_apmv_setpoints_is_the_engine_with_the_apmv(tmp_path):
    arguments = dict(output_frequencies=['hourly', 'timestep'], pmv_cooling_setpoint={'Block1:Zone2': 0.7},
                     heating_setpoint_tolerance_heating_season=0.2, cooling_season_start='01/06',
                     cooling_season_end='15/09', verbose=False)
    first = _model(tmp_path)
    apmv.apply_apmv_setpoints(first, adaptive_coefficient_cooling={'Block1:Zone1': 0.3},
                              adaptive_coefficient_heating=-0.2, **arguments)
    second = _model(tmp_path)
    apply_pmv_index_setpoints(second, 'apmv', dict(adaptive_coefficient_cooling={'Block1:Zone1': 0.3},
                                                   adaptive_coefficient_heating=-0.2), **arguments)

    assert first.idfstr() == second.idfstr()
    lines = _programs(first)['set_zone_input_data_Block1_Zone2']
    # The zones missing in the dictionaries take the default_* arguments
    assert lines[:4] == ['set adap_coeff_cooling_Block1_Zone2 = 0.4', 'set adap_coeff_heating_Block1_Zone2 = -0.2',
                         'set pmv_cooling_sp_Block1_Zone2 = 0.7', 'set pmv_heating_sp_Block1_Zone2 = -0.5']


def test_the_pmv_setpoints_have_the_ems_objects_of_the_pmv(tmp_path):
    building = _model(tmp_path)
    apmv.apply_pmv_setpoints(building, pmv_cooling_setpoint=0.7, pmv_heating_setpoint=-0.7, verbose=False)

    programs = _programs(building)
    # No monitor: the index is the PMV of the zone, its sensor. The zones are in the order of their People objects
    zones = [name[len('set_zone_input_data_'):] for name in programs if name.startswith('set_zone_input_data_')]
    assert sorted(zones) == sorted(ZONES)
    assert list(programs) == ['set_cooling_season_input_data', 'set_cooling_season'] + [
        name for zone in zones
        for name in (f'set_zone_input_data_{zone}', f'apply_PMV_{zone}', f'count_PMV_comfort_hours_{zone}')]
    assert programs['set_zone_input_data_Block1_Zone1'] == [
        'set pmv_cooling_sp_Block1_Zone1 = 0.7', 'set pmv_heating_sp_Block1_Zone1 = -0.7',
        'set tolerance_cooling_sp_cooling_season_Block1_Zone1 = -0.1',
        'set tolerance_cooling_sp_heating_season_Block1_Zone1 = -0.1',
        'set tolerance_heating_sp_cooling_season_Block1_Zone1 = 0.1',
        'set tolerance_heating_sp_heating_season_Block1_Zone1 = 0.1',
    ]
    apply_lines = programs['apply_PMV_Block1_Zone1']
    assert 'set PMV_H_SP_act_Block1_Zone1 = PMV_H_SP_Block1_Zone1' in apply_lines
    assert 'set PMV_C_SP_act_Block1_Zone1 = PMV_C_SP_Block1_Zone1' in apply_lines
    assert not any('adap_coeff' in line for line in apply_lines)
    assert programs['count_PMV_comfort_hours_Block1_Zone1'][0] == 'if PMV_Block1_Zone1 < PMV_H_SP_noTol_Block1_Zone1'
    global_variables = {gv.Erl_Variable_1_Name for gv in building.idfobjects['EnergyManagementSystem:GlobalVariable']}
    assert 'PMV_Block1_Zone1' not in global_variables and 'PMV_H_SP_noTol_Block1_Zone1' in global_variables
    outputs = {o.Name: o.EMS_Variable_Name for o in building.idfobjects['EnergyManagementSystem:OutputVariable']}
    assert outputs['PMV_Block1_Zone1'] == 'PMV_Block1_Zone1'
    assert outputs['PMV Cooling Setpoint No Tolerance_Block1_Zone1'] == 'PMV_C_SP_noTol_Block1_Zone1'
    assert not any(name.startswith(('Adaptive Coefficient', 'aPMV')) for name in outputs)
    managers = [m.Program_Name_1 for m in building.idfobjects['EnergyManagementSystem:ProgramCallingManager']]
    assert managers == list(programs)


def test_the_pmv_setpoints_are_those_of_the_apmv_with_adaptive_coefficients_of_0(tmp_path):
    apmv_model = _model(tmp_path)
    apmv.apply_apmv_setpoints(apmv_model, adaptive_coefficient_cooling=0, adaptive_coefficient_heating=0,
                              verbose=False)
    pmv_model = _model(tmp_path)
    apmv.apply_pmv_setpoints(pmv_model, verbose=False)
    erl_apmv, programs_apmv = _erl(apmv_model)
    erl_pmv, programs_pmv = _erl(pmv_model)

    for day in (30, 180):  # heating and cooling seasons
        for pmv in (-1.2, -0.45, 0.0, 0.45, 0.9):
            for occupants in (0.0, 2.0):
                _timestep(erl_apmv, programs_apmv, day, pmv, occupants)
                _timestep(erl_pmv, programs_pmv, day, pmv, occupants)
                for zone in ZONES:
                    for variable in ('PMV_H_SP_act', 'PMV_C_SP_act', 'comfhour', 'discomfhour_cold',
                                     'discomfhour_heat', 'discomfhour', 'occupied_hour'):
                        assert erl_pmv.get(f'{variable}_{zone}') == erl_apmv.get(f'{variable}_{zone}'), \
                            (day, pmv, occupants, zone, variable)
                    assert erl_pmv.get(f'PMV_C_SP_{zone}') == erl_apmv.get(f'aPMV_C_SP_{zone}')
                    # The PMV setpoints of the thermostats while the zone is occupied (with the tolerances) and not
                    expected = (-0.4, 0.4) if occupants else (-100, 100)
                    assert erl_pmv.get(f'PMV_H_SP_act_{zone}') == pytest.approx(expected[0])
                    assert erl_pmv.get(f'PMV_C_SP_act_{zone}') == pytest.approx(expected[1])
                    # Within the setpoints without tolerance (-0.5 and 0.5), or not
                    assert erl_pmv.get(f'comfhour_{zone}') == (TIMESTEP if abs(pmv) <= 0.5 else 0)


def test_the_setpoints_of_two_indices_are_not_applied_to_a_model(tmp_path):
    building = _model(tmp_path)
    apmv.apply_apmv_setpoints(building, verbose=False)
    with pytest.raises(ValueError, match='already has the setpoints of the aPMV'):
        apmv.apply_pmv_setpoints(building, verbose=False)


def test_the_parametric_modifiers_find_the_lines_by_the_names_of_their_variables(tmp_path):
    from accim.parametric_and_optimisation.funcs_for_besos import param_apmv

    building = _model(tmp_path)
    apmv.apply_pmv_setpoints(building, verbose=False)
    # Before, they wrote the lines 3 and 4, which are those of the aPMV setpoints
    param_apmv.change_pmv_setpoint_all_zones(building, 0.7)
    for zone in ZONES:
        assert _programs(building)[f'set_zone_input_data_{zone}'][:3] == [
            f'set pmv_cooling_sp_{zone} = 0.7', f'set pmv_heating_sp_{zone} = -0.7',
            f'set tolerance_cooling_sp_cooling_season_{zone} = -0.1']
    with pytest.raises(ValueError, match=r'has no line "set adap_coeff_cooling_Block1_Zone\d = \.\.\."'):
        param_apmv.change_adaptive_coeff_all_zones(building, 0.3)

    building = _model(tmp_path)
    apmv.apply_apmv_setpoints(building, verbose=False)
    param_apmv.change_adaptive_coeff_cooling_all_zones(building, 0.35)
    param_apmv.change_pmv_heating_setpoint_all_zones(building, -0.6)
    assert _programs(building)['set_zone_input_data_Block1_Zone1'][:4] == [
        'set adap_coeff_cooling_Block1_Zone1 = 0.35', 'set adap_coeff_heating_Block1_Zone1 = -0.293',
        'set pmv_cooling_sp_Block1_Zone1 = 0.5', 'set pmv_heating_sp_Block1_Zone1 = -0.6']


def _energyplus_with_api(version):
    folder = find_energyplus(version, required=False)
    return folder if folder is not None and (folder / 'pyenergyplus').is_dir() else None


def _column(results, text):
    columns = [c for c in results.columns if text in c]
    assert len(columns) == 1, (text, columns)
    return results[columns[0]]


@pytest.mark.skipif(not (_energyplus_with_api('25.1') and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')
def test_the_pmv_setpoints_give_the_same_results_with_both_backends(tmp_path):
    building = _model(tmp_path)
    apmv.add_vrf_system(building, verbose=False)
    apmv.apply_pmv_setpoints(building, output_frequencies=['timestep'], verbose=False)
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
    results = run_simulations([(model, SAMPLE_EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error

    ems_results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    # The setpoints and hours of the EMS programs are the same. With the thermal comfort thermostats, the results of
    # EnergyPlus differ by rounding (about 1e-10 C in the zone temperatures), as with accim 1.1.0 and the aPMV
    exact = [c for c in ems_results.columns
             if (c.startswith('EMS:') and not c.startswith('EMS:PMV_')) or 'Schedule Value' in c]
    assert len(exact) == 2 * 9 + 4
    pd.testing.assert_frame_equal(api_results[exact], ems_results[exact], check_exact=True)
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=False, rtol=1e-6, atol=1e-6)
    for zone, people in (('Block1_Zone1', 'BLOCK1:ZONE1'), ('Block1_Zone2', 'BLOCK1:ZONE2')):
        # The PMV of each zone, which the EMS reads at the beginning of each timestep, is that of the previous one
        reported = _column(ems_results, f'EMS:PMV_{zone} [')
        pmv = _column(ems_results, f'{people}:Zone Thermal Comfort Fanger Model PMV')
        pd.testing.assert_series_equal(reported.iloc[1:], pmv.shift(1).iloc[1:], check_names=False, rtol=1e-5)
        # While the zone is occupied, the PMV setpoints of its thermostat are -0.4 and 0.4 (with the tolerances)
        cooling = _column(ems_results, f'PMV_C_SP_{people}:Schedule Value')
        assert set(cooling.round(6)) <= {0.4, 100.0} and (cooling == 0.4).any()
