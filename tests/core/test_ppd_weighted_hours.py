"""Tests for Method C of CEN/TR 16798-2:2019, Annex D (the PPD-weighted hours) in the setpoints based on the PMV
(task H3 of the review of accim 1.2.0, decision 5 of its section 6: ``report_ppd_weighted_hours`` of
:mod:`accim.sim.pmv_index`).

The program ``count_ppd_weighted_hours_<zone>`` is run with the Erl interpreter of accim and compared with
``ppd_weighted_hours`` of :mod:`accim.data.postprocessing.long_term_discomfort` (D1), with the setpoints of each index
converted to the scale of the PMV; the last tests simulate the sample model with EnergyPlus 25.1 (both backends, and
check 3 of verify_accim_simulation).
"""
import shutil
import subprocess
import warnings
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest

from accim.data.postprocessing.long_term_discomfort import ppd_from_pmv, ppd_weighted_hours
from accim.energyplus import find_energyplus
from accim.sim import apmv
from accim.sim.ems.erl import ErlProgramSet
from accim.sim.pmv_index import (PMV_INDICES, PPD_WEIGHTED_HOURS_OUTPUTS, PPD_WEIGHTED_HOURS_PROGRAM,
                                 ppd_weighted_hours_lines, program_names, zone_outputs)

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
ZONES = ('Block1_Zone1', 'Block1_Zone2')
TIMESTEP = 0.25
FUNCTIONS = {'apmv': apmv.apply_apmv_setpoints, 'epmv': apmv.apply_epmv_setpoints, 'pmv': apmv.apply_pmv_setpoints}
# The options of each index (and the coefficients of its EMS variables): the aPMV by season and by the sign of the
# PMV, and the ePMV on the warm side and on both sides
VARIANTS = {
    'pmv': ('pmv', {}),
    'apmv season': ('apmv', {'adaptive_coefficient_by': 'season'}),
    'apmv pmv_sign': ('apmv', {'adaptive_coefficient_by': 'pmv_sign'}),
    'epmv': ('epmv', {'apply_to_heating': False, 'metabolic_correction': False}),
    'epmv apply_to_heating': ('epmv', {'apply_to_heating': True, 'metabolic_correction': False}),
}
COEFFICIENTS = {'adap_coeff_Z': 0.25, 'adap_coeff_cooling_Z': 0.293, 'adap_coeff_heating_Z': -0.293, 'e_Z': 0.7}


def _pmv_limit(key, options, side, setpoint):
    """The PMV whose index is a setpoint (the inverse of the index), with the coefficients of COEFFICIENTS."""
    if key == 'apmv':
        if options['adaptive_coefficient_by'] == 'pmv_sign':
            coefficient = COEFFICIENTS['adap_coeff_cooling_Z' if side == 'C' else 'adap_coeff_heating_Z']
        else:
            coefficient = COEFFICIENTS['adap_coeff_Z']
        return setpoint / (1 - coefficient * setpoint)
    if key == 'epmv' and (side == 'C' or options['apply_to_heating']):
        return setpoint / COEFFICIENTS['e_Z']
    return setpoint


def _run(key, options, pmv, occupants, heating=-0.5, cooling=0.5):
    name = PMV_INDICES[key].name
    variables = ['People_Occupant_Count_Z', 'PMV_Z', f'{name}_H_SP_noTol_Z', f'{name}_C_SP_noTol_Z',
                 'PpdWeightedHours_Z', *COEFFICIENTS]
    erl = ErlProgramSet({'method_c': ppd_weighted_hours_lines(PMV_INDICES[key], 'Z', options)},
                        global_variables=variables)
    erl.strict = True
    erl.set('ZoneTimeStep', TIMESTEP)
    for variable, value in COEFFICIENTS.items():
        erl.set(variable, value)
    erl.set('People_Occupant_Count_Z', occupants)
    erl.set('PMV_Z', pmv)
    erl.set(f'{name}_H_SP_noTol_Z', heating)
    erl.set(f'{name}_C_SP_noTol_Z', cooling)
    erl.run('method_c')
    return erl.get('PpdWeightedHours_Z')


def test_the_output_and_the_ppd_of_iso_7730():
    assert PPD_WEIGHTED_HOURS_OUTPUTS == {'PPD Weighted Hours': ('PpdWeightedHours', 'H', 'Summed')}
    # Only with report_ppd_weighted_hours
    for pmv_index in PMV_INDICES.values():
        assert 'PPD Weighted Hours' not in zone_outputs(pmv_index)
        assert list(zone_outputs(pmv_index, ppd_weighted_hours=True))[-1] == 'PPD Weighted Hours'
    # The PPD of the Erl lines is that of ISO 7730:2025, formula (5), as ppd_from_pmv of D1
    for pmv in (-3.0, -1.2, -0.5, 0.0, 0.3, 0.5, 2.0):
        erl = ErlProgramSet({'ppd': ppd_weighted_hours_lines(PMV_INDICES['pmv'], 'Z', {})},
                            global_variables=['People_Occupant_Count_Z', 'PMV_Z', 'PMV_H_SP_noTol_Z',
                                              'PMV_C_SP_noTol_Z', 'PpdWeightedHours_Z'])
        erl.set('ZoneTimeStep', 1.0)
        erl.set('People_Occupant_Count_Z', 1)
        erl.set('PMV_Z', pmv)
        # With the limits at 0 (PPD 5 %), the weighted hours are PPD/5 on either side
        erl.set('PMV_H_SP_noTol_Z', 0.0)
        erl.set('PMV_C_SP_noTol_Z', 0.0)
        erl.run('ppd')
        assert erl.get('PpdWeightedHours_Z') == pytest.approx(ppd_from_pmv(pmv) / 5.0, rel=1e-12)
    assert ppd_from_pmv(0.0) == pytest.approx(5.0)


@pytest.mark.parametrize('variant', list(VARIANTS))
@pytest.mark.parametrize('pmv, occupants', [
    (0.0, 1),     # within the range
    (0.45, 2),
    (0.9, 1),     # warm period
    (2.5, 3),
    (-0.9, 1),    # cold period
    (-3.0, 1),
    (1.5, 0),     # without occupants
    (-1.5, 0),
])
def test_the_program_is_method_c_of_d1(variant, pmv, occupants):
    key, options = VARIANTS[variant]
    lower, upper = _pmv_limit(key, options, 'H', -0.5), _pmv_limit(key, options, 'C', 0.5)
    expected = ppd_weighted_hours([pmv], [lower], [upper], occupied=[occupants], timestep_h=TIMESTEP)
    found = _run(key, options, pmv, occupants)
    assert found == pytest.approx(expected['hot_h'] + expected['cold_h'], abs=1e-12)
    if occupants and not lower <= pmv < upper:
        assert found > 0


def test_the_range_is_half_open():
    # A PMV equal to the upper limit is in the warm period, with wf = 1; one equal to the lower limit is within the
    # range (CEN/TR 16798-2, Annex D, as written; verdict #20 of the review of accim 1.2.0)
    assert _run('pmv', {}, 0.5, 1) == pytest.approx(TIMESTEP)
    assert _run('pmv', {}, -0.5, 1) == 0.0
    assert _run('pmv', {}, 0.4999, 1) == 0.0
    # A heating setpoint above the cooling setpoint: both periods, as in D1
    expected = ppd_weighted_hours([0.3], [0.4], [0.2], occupied=[1], timestep_h=TIMESTEP)
    assert expected['hot_h'] > 0 and expected['cold_h'] > 0
    assert _run('pmv', {}, 0.3, 1, heating=0.4, cooling=0.2) == pytest.approx(expected['hot_h'] + expected['cold_h'])


def test_the_lines_of_the_program():
    lines = ppd_weighted_hours_lines(PMV_INDICES['apmv'], 'Zone1', {'adaptive_coefficient_by': 'season'})
    assert lines[:2] == ['set PpdWeightedHours_Zone1 = 0', 'if People_Occupant_Count_Zone1 > 0']
    assert 'set ppd_upper_Zone1 = aPMV_C_SP_noTol_Zone1/(1-adap_coeff_Zone1*aPMV_C_SP_noTol_Zone1)' in lines
    assert 'set ppd_lower_Zone1 = aPMV_H_SP_noTol_Zone1/(1-adap_coeff_Zone1*aPMV_H_SP_noTol_Zone1)' in lines
    assert 'set ppd_exp_Zone1 = @Exp ppd_exp_Zone1' in lines
    # No minus sign after '*' or '/' (Erl rejects it)
    assert not any('*-' in line or '/-' in line for line in lines)
    assert program_names(PMV_INDICES['pmv'], ['Z'], ppd_weighted_hours=True)[-2:] == [
        'count_PMV_comfort_hours_Z', f'{PPD_WEIGHTED_HOURS_PROGRAM}Z']
    assert f'{PPD_WEIGHTED_HOURS_PROGRAM}Z' not in program_names(PMV_INDICES['pmv'], ['Z'])


# The model ---------------------------------------------------------------------------------------------------------

needs_idd = pytest.mark.skipif(find_energyplus('25.1', required=False) is None or not SAMPLE_IDF.exists(),
                               reason='needs EnergyPlus 25.1 (its IDD) and the sample IDF of the repository')


def _model(tmp_path, name='TestModel.idf'):
    from accim.sim.accis import load_idf

    path = tmp_path / name
    shutil.copy(SAMPLE_IDF, path)
    return load_idf(path)


def _programs(building):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
            for p in building.idfobjects['EnergyManagementSystem:Program']}


@needs_idd
@pytest.mark.parametrize('key', list(FUNCTIONS))
def test_the_setpoints_add_method_c(tmp_path, key):
    pmv_index = PMV_INDICES[key]
    building = _model(tmp_path)
    FUNCTIONS[key](building, output_frequencies=['hourly', 'timestep'], verbose=False, report_ppd_weighted_hours=True)
    programs = _programs(building)
    declared = {str(name).strip() for g in building.idfobjects['EnergyManagementSystem:GlobalVariable']
                for name in g.fieldvalues[1:] if str(name).strip()}
    ems_outputs = {o.Name: o for o in building.idfobjects['EnergyManagementSystem:OutputVariable']}
    requested = {(o.Variable_Name, o.Reporting_Frequency) for o in building.idfobjects['Output:Variable']}
    managers = [m.Name for m in building.idfobjects['EnergyManagementSystem:ProgramCallingManager']]
    for zone in ZONES:
        assert programs[f'{PPD_WEIGHTED_HOURS_PROGRAM}{zone}'] == ppd_weighted_hours_lines(
            pmv_index, zone, dict(pmv_index.options))
        assert f'PpdWeightedHours_{zone}' in declared
        found = ems_outputs[f'PPD Weighted Hours_{zone}']
        assert (found.EMS_Variable_Name, found.Type_of_Data_in_Variable, found.Update_Frequency, found.Units) == (
            f'PpdWeightedHours_{zone}', 'Summed', 'ZoneTimestep', 'H')
        assert {(f'PPD Weighted Hours_{zone}', 'Hourly'), (f'PPD Weighted Hours_{zone}', 'Timestep')} <= requested
        # After the hour counters of the zone, whose occupied hours it shares
        position = managers.index(f'{PPD_WEIGHTED_HOURS_PROGRAM}{zone}')
        assert managers[position - 1] == f'count_{pmv_index.name}_comfort_hours_{zone}'


@needs_idd
def test_without_the_argument_the_models_are_those_of_before(tmp_path):
    with_it = _model(tmp_path, 'with.idf')
    without = _model(tmp_path, 'without.idf')
    apmv.apply_apmv_setpoints(with_it, verbose=False, report_ppd_weighted_hours=True)
    apmv.apply_apmv_setpoints(without, verbose=False)
    text = without.idfstr()
    assert 'ppd_' not in text.lower().replace('ppd_weighted', '') and 'PPD Weighted Hours' not in text

    # The other objects are the same: Method C only adds its own
    def objects(building):
        return Counter((key.upper(), tuple(str(value) for value in obj.fieldvalues[1:]))
                       for key in building.idfobjects for obj in building.idfobjects[key])

    before, after = objects(without), objects(with_it)
    assert not before - after
    added = after - before
    assert added and all('ppd' in ' '.join(fields).lower() for _, fields in added)
    assert {key for key, _ in added} == {'ENERGYMANAGEMENTSYSTEM:PROGRAM',
                                         'ENERGYMANAGEMENTSYSTEM:PROGRAMCALLINGMANAGER',
                                         'ENERGYMANAGEMENTSYSTEM:GLOBALVARIABLE',
                                         'ENERGYMANAGEMENTSYSTEM:OUTPUTVARIABLE', 'OUTPUT:VARIABLE'}
    with pytest.raises(ValueError, match="report_ppd_weighted_hours must be True or False, not 'yes'"):
        apmv.apply_pmv_setpoints(_model(tmp_path, 'other.idf'), verbose=False, report_ppd_weighted_hours='yes')


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()
    return folder if ready else None


@pytest.mark.skipif(_energyplus_with_api() is None,
                    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')
@pytest.mark.parametrize('key, begin, end', [('apmv', (7, 1), (7, 7)), ('pmv', (1, 10), (1, 14))])
def test_method_c_in_energyplus_with_both_backends(tmp_path, capsys, key, begin, end):
    from accim.sim.energyplus_api import run_simulations
    from accim.utils.verification import verify_accim_simulation

    building = _model(tmp_path)
    apmv.add_vrf_system(building, verbose=False)
    FUNCTIONS[key](building, output_frequencies=['timestep'], verbose=False, report_ppd_weighted_hours=True)
    run_period = building.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    model = tmp_path / 'model.idf'
    building.saveas(str(model))
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    ems = subprocess.run([str(energyplus), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-r', '-x',
                          '-w', str(SAMPLE_EPW), str(model)], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
    api = run_simulations([(model, SAMPLE_EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                          processes=1)
    assert api[0].success, api[0].error
    results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    # The EMS outputs are the same with both backends, but those calculated from the PMV, which differ by rounding
    # (about 1e-12 of the PMV: the thermal comfort thermostats differ by rounding, about 1e-10 C, as in
    # test_pmv_index)
    name = PMV_INDICES[key].name
    from_pmv = [c for c in results.columns if c.startswith((f'EMS:{name}_', 'EMS:PPD Weighted Hours_'))]
    exact = [c for c in results.columns if c.startswith('EMS:') and c not in from_pmv]
    assert len(from_pmv) == 4 and len(exact) > 10
    pd.testing.assert_frame_equal(api_results[exact], results[exact], check_exact=True)
    pd.testing.assert_frame_equal(api_results[from_pmv], results[from_pmv], check_exact=False, rtol=1e-9, atol=1e-9)
    pd.testing.assert_frame_equal(api_results, results, check_exact=False, rtol=1e-6, atol=1e-6)

    # Check 3 of verify_accim_simulation
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        mismatches = verify_accim_simulation(str(tmp_path / 'ems' / 'run.eso'), str(model),
                                             eplus_install_dir=str(_energyplus_with_api()),
                                             calculation_tolerance=1e-6)
    output = capsys.readouterr().out
    assert mismatches.empty
    steps = len(results)
    for zone in ZONES:
        assert f"'{zone}' Check3_PpdWeightedHours (PPD(PMV)/PPD(PMV limit) times the occupied hours, Method C of " \
               f"CEN/TR 16798-2): 0 mismatch(es) in {steps - 1} timesteps" in output

    # The totals are those of the function of D1, with the PMV of the previous timestep, the setpoints of the index
    # without the tolerances on the scale of the PMV, and the occupied hours
    total = 0.0
    for zone in ZONES:
        people = zone.replace('_', ':').upper()
        [column] = [c for c in results.columns if f'{people}:Zone Thermal Comfort Fanger Model PMV' in c]
        pmv = results[column].shift(1)
        hours = results[f'EMS:Occupied hours_{zone} [H](TimeStep)']
        lower = results[f'EMS:{name} Heating Setpoint No Tolerance_{zone} [](TimeStep)']
        upper = results[f'EMS:{name} Cooling Setpoint No Tolerance_{zone} [](TimeStep)']
        if key == 'apmv':
            coefficient = results[f'EMS:Adaptive Coefficient_{zone} [](TimeStep)']
            lower, upper = lower / (1 - coefficient * lower), upper / (1 - coefficient * upper)
        rows = slice(1, None)
        expected = ppd_weighted_hours(pmv[rows], lower[rows], upper[rows], occupied=hours[rows],
                                      timestep_h=hours[rows])
        found = results[f'EMS:PPD Weighted Hours_{zone} [H](TimeStep)']
        assert found.iloc[1:].sum() == pytest.approx(expected['hot_h'] + expected['cold_h'], abs=1e-9)
        total += found.sum()
        # Outside the range only when the index is outside the setpoints (the discomfortable hours of the zone), or
        # with the PMV on the upper limit
        outside = found.iloc[1:] > 0
        discomfortable = results[f'EMS:Discomfortable Total Hours_{zone} [H](TimeStep)'].iloc[1:] > 0
        assert not (outside & ~discomfortable & (pmv[rows] != upper[rows])).any()
    # Something to weigh: the first occupied timesteps, before the thermostats bring the PMV within the setpoints
    assert total > 0
