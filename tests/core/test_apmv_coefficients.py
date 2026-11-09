"""Tests for the catalogue of adaptive coefficients of the aPMV and the choice of the coefficient by the sign of the PMV
(proposal A3): accim.constants.APMV_ADAPTIVE_COEFFICIENTS, accim.sim.apmv.get_adaptive_coefficients, the keys of the
catalogue in apply_apmv_setpoints, and adaptive_coefficient_by='pmv_sign'.

aPMV = PMV/(1 + λ·PMV) (Yao, Li and Liu, 2009), with λ of warm sensations (PMV >= 0) and of cool sensations
(PMV < 0); the coefficients are those of section 11.2 and proposal A3 of notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md
(Yao et al., 2009; GB/T 50785-2012; Zhang, Yao and Li, 2024, Table 6). The EMS programs run with the Erl interpreter of
accim; the last test runs a model with both backends of EnergyPlus 25.1.
"""
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.constants import APMV_ADAPTIVE_COEFFICIENTS
from accim.energyplus import find_energyplus
from accim.sim import apmv
from accim.sim.ems.erl import ErlProgramSet
from accim.sim.pmv_index import ADAPTIVE_COEFFICIENT_BY, resolve_adaptive_coefficients

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
ZONES = ('Block1_Zone1', 'Block1_Zone2')


def _model(tmp_path):
    """The sample model of EnergyPlus 25.1, read by eppy."""
    from accim.sim.accis import load_idf

    if find_energyplus('25.1', required=False) is None or not SAMPLE_IDF.exists():
        pytest.skip('needs EnergyPlus 25.1 (its IDD) and the sample IDFs of the repository')
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / SAMPLE_IDF.name
    shutil.copy(SAMPLE_IDF, path)
    return load_idf(path)


def _programs(building):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:] if str(line).strip()]
            for p in building.idfobjects['EnergyManagementSystem:Program']}


def test_the_catalogue():
    # Section 11.2 of the proposals: Yao et al. (2009) and GB/T 50785-2012 (lambda of PMV >= 0 / PMV < 0)
    expected = {'yao2009_chongqing_classrooms': (0.293, -0.125), 'gbt50785_cold_general': (0.24, -0.50),
                'gbt50785_cold_education': (0.21, -0.29), 'gbt50785_hscw_hsww_mild_general': (0.21, -0.49),
                'gbt50785_hscw_hsww_mild_education': (0.17, -0.28)}
    for key, (cooling, heating) in expected.items():
        entry = APMV_ADAPTIVE_COEFFICIENTS[key]
        assert (entry['cooling'], entry['heating'], entry['grade']) == (cooling, heating, 'standard')
    # Zhang, Yao and Li (2024), Table 6, lambda_N of the 14 Koppen zones (PMV < 0 / PMV > 0)
    zhang = {key: entry for key, entry in APMV_ADAPTIVE_COEFFICIENTS.items() if key.startswith('zhang2024_')}
    assert len(zhang) == 14 and {entry['grade'] for entry in zhang.values()} == {'literature'}
    assert (zhang['zhang2024_Am']['heating'], zhang['zhang2024_Am']['cooling']) == (-0.66, 0.46)
    assert (zhang['zhang2024_Aw']['heating'], zhang['zhang2024_Aw']['cooling']) == (None, 0.36)
    assert (zhang['zhang2024_Dwa']['heating'], zhang['zhang2024_Dwa']['cooling']) == (-0.66, -0.07)
    # The signs that contradict the adaptive mechanism, as the proposal lists them
    assert {key[10:] for key, entry in zhang.items() if entry['cooling'] < 0} == {'Cfb', 'Csc', 'Dfb', 'Dwa'}
    assert {key[10:] for key, entry in zhang.items()
            if entry['heating'] is not None and entry['heating'] > 0} == {'Af', 'Cfa'}
    for entry in APMV_ADAPTIVE_COEFFICIENTS.values():
        assert set(entry) == {'cooling', 'heating', 'grade', 'source', 'notes'} and entry['source']


def test_get_adaptive_coefficients():
    entry = apmv.get_adaptive_coefficients('gbt50785_cold_education')
    assert entry['cooling'] == 0.21 and entry['heating'] == -0.29
    entry['cooling'] = 1
    assert APMV_ADAPTIVE_COEFFICIENTS['gbt50785_cold_education']['cooling'] == 0.21
    with pytest.raises(ValueError, match="'unknown' is not a key of accim.constants.APMV_ADAPTIVE_COEFFICIENTS"):
        apmv.get_adaptive_coefficients('unknown')


def test_the_keys_of_the_catalogue_are_resolved():
    values = dict(adaptive_coefficient_cooling='yao2009_chongqing_classrooms',
                  adaptive_coefficient_heating={'Block1:Zone1': 'gbt50785_cold_general', 'Block1:Zone2': -0.2},
                  default_adaptive_coefficient_cooling=0.4, default_adaptive_coefficient_heating='gbt50785_cold_general',
                  pmv_cooling_setpoint=0.5)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        resolved = resolve_adaptive_coefficients(values)
    assert resolved == dict(adaptive_coefficient_cooling=0.293,
                            adaptive_coefficient_heating={'Block1:Zone1': -0.50, 'Block1:Zone2': -0.2},
                            default_adaptive_coefficient_cooling=0.4, default_adaptive_coefficient_heating=-0.50,
                            pmv_cooling_setpoint=0.5)
    # A key of the literature warns once
    with pytest.warns(UserWarning, match="'zhang2024_Csa' are of the grade 'literature'") as record:
        resolved = resolve_adaptive_coefficients(dict(adaptive_coefficient_cooling='zhang2024_Csa',
                                                      adaptive_coefficient_heating='zhang2024_Csa'))
    assert len(record) == 1 and resolved == dict(adaptive_coefficient_cooling=0.29, adaptive_coefficient_heating=-0.66)
    with pytest.raises(ValueError, match="have no heating coefficient"):
        resolve_adaptive_coefficients(dict(adaptive_coefficient_heating='zhang2024_Aw'))


def test_apply_apmv_setpoints_with_keys_of_the_catalogue(tmp_path):
    keys = _model(tmp_path / 'keys')
    apmv.apply_apmv_setpoints(keys, adaptive_coefficient_cooling='gbt50785_cold_general',
                              adaptive_coefficient_heating='gbt50785_cold_general', verbose=False)
    numbers = _model(tmp_path / 'numbers')
    apmv.apply_apmv_setpoints(numbers, adaptive_coefficient_cooling=0.24, adaptive_coefficient_heating=-0.5,
                              verbose=False)
    assert keys.idfstr() == numbers.idfstr()
    lines = _programs(keys)['set_zone_input_data_Block1_Zone1']
    assert 'set adap_coeff_cooling_Block1_Zone1 = 0.24' in lines and 'set adap_coeff_heating_Block1_Zone1 = -0.5' in lines
    # generate_df_from_args too
    table = apmv.generate_df_from_args(['Block1:Zone1'], ['Block1_Zone1'], 'yao2009_chongqing_classrooms',
                                       'yao2009_chongqing_classrooms', 0.5, -0.5, -0.1, -0.1, 0.1, 0.1, 0.4, -0.4,
                                       0.5, -0.5, -0.1, -0.1, 0.1, 0.1)
    assert table.loc['Block1:Zone1', 'adaptive_coefficient_cooling'] == 0.293
    assert table.loc['Block1:Zone1', 'adaptive_coefficient_heating'] == -0.125
    with pytest.raises(ValueError, match="adaptive_coefficient_by must be one of"):
        apmv.apply_apmv_setpoints(_model(tmp_path / 'other'), adaptive_coefficient_by='pmv', verbose=False)
    assert ADAPTIVE_COEFFICIENT_BY == ('season', 'pmv_sign')


def _erl(building):
    """The EMS programs of a model, compiled by the Erl interpreter, and those run at the beginning of each timestep,
    in their order."""
    from accim.sim.energyplus_api import read_ems

    ems = read_ems(building)
    erl = ErlProgramSet(ems.programs, global_variables=ems.global_names(), actuators=[a[0] for a in ems.actuators])
    erl.strict = True
    programs = [program for _, calling_point, names in ems.calling_managers
                if calling_point == 'BEGINTIMESTEPBEFOREPREDICTOR' for program in names]
    return erl, programs


def test_the_adaptive_coefficient_by_the_sign_of_the_pmv(tmp_path):
    building = _model(tmp_path)
    apmv.apply_apmv_setpoints(building, adaptive_coefficient_cooling=0.21, adaptive_coefficient_heating=-0.49,
                              cooling_setpoint_tolerance_cooling_season=0, cooling_setpoint_tolerance_heating_season=0,
                              heating_setpoint_tolerance_cooling_season=0, heating_setpoint_tolerance_heating_season=0,
                              adaptive_coefficient_by='pmv_sign', verbose=False)
    programs = _programs(building)
    # The program of the setpoints does not choose the coefficient by the season
    assert not any(line.startswith('set adap_coeff_Block1_Zone1 =') for line in programs['apply_aPMV_Block1_Zone1'])
    assert programs['monitor_aPMV_Block1_Zone1'][:5] == [
        'if PMV_Block1_Zone1 >= 0', 'set adap_coeff_Block1_Zone1 = adap_coeff_cooling_Block1_Zone1', 'else',
        'set adap_coeff_Block1_Zone1 = adap_coeff_heating_Block1_Zone1', 'endif']

    erl, run = _erl(building)
    for day in (30.0, 180.0):
        for pmv in (0.8, -0.8, 0.0):
            erl.set('DayOfYear', day)
            erl.set('ZoneTimeStep', 0.25)
            for zone in ZONES:
                erl.set(f'PMV_{zone}', pmv)
                erl.set(f'People_Occupant_Count_{zone}', 2.0)
            for program in run:
                erl.run(program)
            for zone in ZONES:
                coefficient = 0.21 if pmv >= 0 else -0.49
                assert erl.get(f'adap_coeff_{zone}') == pytest.approx(coefficient), (day, pmv)
                assert erl.get(f'aPMV_{zone}') == pytest.approx(pmv / (1 + coefficient * pmv)), (day, pmv)
                # Each setpoint with the coefficient of its side, whatever the PMV and the season
                assert erl.get(f'PMV_H_SP_act_{zone}') == pytest.approx(-0.5 / (1 - (-0.49) * -0.5))
                assert erl.get(f'PMV_C_SP_act_{zone}') == pytest.approx(0.5 / (1 - 0.21 * 0.5))


def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    return folder if folder is not None and (folder / 'pyenergyplus').is_dir() else None


@pytest.mark.skipif(not (_energyplus_with_api() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')
def test_the_adaptive_coefficient_by_the_sign_of_the_pmv_with_both_backends(tmp_path):
    from accim.sim.energyplus_api import run_simulations
    from accim.utils.verification import verify_accim_simulation

    building = _model(tmp_path)
    apmv.add_vrf_system(building, verbose=False)
    apmv.apply_apmv_setpoints(building, output_frequencies=['timestep'], adaptive_coefficient_cooling='gbt50785_cold_general',
                              adaptive_coefficient_heating='gbt50785_cold_general', adaptive_coefficient_by='pmv_sign',
                              verbose=False)
    # Three days around the beginning of the cooling season
    run_period = building.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 4, 30
    run_period.End_Month, run_period.End_Day_of_Month = 5, 2
    model = tmp_path / 'model.idf'
    building.saveas(str(model))

    energyplus = _energyplus_with_api() / 'energyplus.exe'
    ems = subprocess.run([str(energyplus), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-x',
                          '-w', str(SAMPLE_EPW), str(model)], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
    assert '** Severe' not in (tmp_path / 'ems' / 'run.err').read_text(errors='ignore')
    results = run_simulations([(model, SAMPLE_EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    ems_results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=False, rtol=1e-6, atol=1e-6)
    # Both coefficients are used, by the sign of the PMV
    coefficient = ems_results[[c for c in ems_results.columns if 'Adaptive Coefficient_Block1_Zone1' in c][0]]
    assert set(np.round(coefficient.dropna(), 6)) == {0.24, -0.5}
    # The aPMV is that of the PMV of the previous timestep, with the coefficient of its sign
    assert verify_accim_simulation(str(tmp_path / 'ems' / 'run.eso'), str(model),
                                   eplus_install_dir=str(_energyplus_with_api()), calculation_tolerance=1e-6).empty
