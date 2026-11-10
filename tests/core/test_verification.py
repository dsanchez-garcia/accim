"""Tests for the checks of verify_accim_simulation of the values that the EMS calculates (proposal E2): check 3, the
indices derived from the PMV of accim.sim.pmv_index (aPMV = PMV/(1 + λ·PMV), Yao et al., 2009; ePMV = e·PMV with
PMV > 0, Fanger and Toftum, 2002; the PMV) and the metabolic correction of the ePMV (1 − 0.067·PMV in the cooling
season), from the PMV of the previous timestep; and check 4, the setpoints of the output IDFs of AddAccis against
accim.sim.preview.compute_setpoints (E1).

The unit tests build the outputs that read_eso_using_readvarseso returns from made-up values; the last tests simulate
models with EnergyPlus 25.1 (the PMV of the occupants of the previous timestep, and of the current timestep the
occupants, were checked with simulations of the sample models on 2026-11-09).
"""
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import find_energyplus
from accim.utils.verification import (
    _compute_setpoints_arguments,
    _dates_and_times,
    _environment_starts,
    _pmv_index_mismatches,
    _setpoint_mismatches,
    _weighted_mean,
    verify_accim_simulation,
)

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
# One People object for the two floors (a SpaceList), as in OpenStudio models
RESIDENTIAL_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'example_epmv_setpoints'
                   / 'TestModel_TestResidentialUnit.idf')
EPW = REPO / 'Seville_Present.epw'
OTHER_EPW = REPO / 'Seville_ssp585_2080.epw'
ZONES = ('Block1_Zone1', 'Block1_Zone2')
FANGER_PMV = 'Zone Thermal Comfort Fanger Model PMV'


def _energyplus():
    return find_energyplus('25.1', required=False)


def _model(tmp_path, source=SAMPLE_IDF):
    """A model of EnergyPlus 25.1, read by eppy."""
    from accim.sim.accis import load_idf

    if _energyplus() is None or not source.exists():
        pytest.skip('needs EnergyPlus 25.1 (its IDD) and the sample IDFs of the repository')
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / source.name
    shutil.copy(source, path)
    return load_idf(path)


def _timestamps(begin='04/29', days=3, timesteps_per_hour=6, design_day=None):
    """The timestamps of the outputs at timestep frequency of a design day (if given) and a run period."""
    def day_rows(date):
        minutes = np.arange(1, 24 * timesteps_per_hour + 1) * 60 // timesteps_per_hour
        return [f' {date}  {m // 60:02d}:{m % 60:02d}:00' for m in minutes]

    rows = day_rows(design_day) if design_day else []
    start = pd.Timestamp(f'2007/{begin}')
    for day in range(days):
        rows += day_rows((start + pd.Timedelta(days=day)).strftime('%m/%d'))
    return rows


def _frame(timestamps, columns):
    """The outputs of read_eso_using_readvarseso of one frequency: {(key, variable, units): values}."""
    frame = pd.DataFrame({column: np.asarray(values, dtype=float) for column, values in columns.items()},
                         index=pd.Index(timestamps, name='Date/Time'))
    frame.columns = pd.MultiIndex.from_tuples(list(columns), names=['Area', 'Variable', 'Units'])
    return frame


def _previous(values, starts):
    result = np.r_[np.nan, values[:-1]]
    result[starts] = np.nan
    return result


def test_dates_and_times():
    datetimes, dates = _dates_and_times([' 01/21  00:10:00', ' 07/01  24:00:00', '12/31  24:00:00'])
    assert list(datetimes) == [pd.Timestamp('2007-01-21 00:10'), pd.Timestamp('2007-07-02 00:00'),
                               pd.Timestamp('2008-01-01 00:00')]
    # The date of the row is that of the timestamp, also at 24:00:00
    assert list(dates) == [pd.Timestamp('2007-01-21'), pd.Timestamp('2007-07-01'), pd.Timestamp('2007-12-31')]
    assert _dates_and_times([' 02/29  01:00:00'])[0][0] == pd.Timestamp('2008-02-29 01:00')
    with pytest.raises(ValueError, match='is not a date and time of the outputs of EnergyPlus'):
        _dates_and_times(['July'])


def test_environment_starts():
    timestamps = _timestamps(days=2, design_day='07/21')
    starts = _environment_starts(_dates_and_times(timestamps)[0])
    # The design day and the run period
    assert np.flatnonzero(starts).tolist() == [0, 144]
    assert _environment_starts(_dates_and_times(_timestamps(days=2, timesteps_per_hour=1))[0]).sum() == 1


def test_weighted_mean():
    values = [np.array([1.0, 1.0]), np.array([2.0, 2.0])]
    np.testing.assert_allclose(_weighted_mean(values, [np.array([3.0, 0.0]), np.array([1.0, 0.0])]), [1.25, 1.5])


def test_the_arguments_of_compute_setpoints():
    values = {'ComfStand': 1, 'CAT': 2, 'ComfMod': 3, 'HVACmode': 2, 'ACSTtol': -0.25, 'AHSTtol': 0.25,
              'CoolSeasonStart': 121, 'SetpointAcc': 1000, 'm': 0.31, 'MaxWindSpeed': 6}
    assert _compute_setpoints_arguments(values) == {
        'comfort_standard': 1, 'category': 2, 'comfort_mode': 3, 'setpoint_tolerance': 0.25,
        'cooling_season_start': 121, 'setpoint_accuracy': 1000, 'custom_slope': 0.31}
    with pytest.raises(ValueError, match='is not the opposite of AHSTtol'):
        _compute_setpoints_arguments({**values, 'ACSTtol': -0.1})


def _apmv_outputs(timestamps, pmv, coefficient):
    """Outputs of the aPMV setpoints of the sample model whose aPMV is that of the PMV of the previous timestep."""
    starts = _environment_starts(_dates_and_times(timestamps)[0])
    columns = {}
    for zone in ZONES:
        people = f'PEOPLE {zone.replace("_", ":").upper()}'
        columns[(people, FANGER_PMV, '')] = pmv[zone]
        previous = _previous(pmv[zone], starts)
        columns[('EMS', f'aPMV_{zone}', '')] = np.nan_to_num(previous / (1 + coefficient * previous))
        columns[('EMS', f'Adaptive Coefficient_{zone}', '')] = np.full(len(timestamps), coefficient)
    return columns


def test_the_apmv_of_the_pmv_of_the_previous_timestep(tmp_path):
    from accim.sim import apmv

    building = _model(tmp_path)
    apmv.apply_apmv_setpoints(building, output_frequencies=['timestep'], verbose=False)
    timestamps = _timestamps(design_day='07/21')
    rng = np.random.default_rng(1)
    pmv = {zone: rng.uniform(-1.5, 1.5, len(timestamps)) for zone in ZONES}
    columns = _apmv_outputs(timestamps, pmv, 0.293)

    rows, lines = _pmv_index_mismatches(building, _frame(timestamps, columns), 1e-6)
    assert rows == []
    # The first timestep of each environment is not checked
    assert lines == [f"  '{zone}' Check3_aPMV (aPMV = PMV/(1 + lambda*PMV)): 0 mismatch(es) in "
                     f"{len(timestamps) - 2} timesteps" for zone in ('Block1_Zone2', 'Block1_Zone1')]

    # The aPMV of the PMV of the same timestep is wrong
    same = dict(columns)
    same[('EMS', 'aPMV_Block1_Zone1', '')] = pmv['Block1_Zone1'] / (1 + 0.293 * pmv['Block1_Zone1'])
    rows, _ = _pmv_index_mismatches(building, _frame(timestamps, same), 1e-6)
    assert len(rows) > 400 and {row['zone_or_window'] for row in rows} == {'Block1_Zone1'}
    # One wrong value
    wrong = dict(columns)
    wrong[('EMS', 'aPMV_Block1_Zone2', '')] = columns[('EMS', 'aPMV_Block1_Zone2', '')].copy()
    wrong[('EMS', 'aPMV_Block1_Zone2', '')][200] += 0.01
    rows, _ = _pmv_index_mismatches(building, _frame(timestamps, wrong), 1e-3)
    assert [(row['timestep'], row['zone_or_window'], row['check']) for row in rows] == [
        (timestamps[200].strip(), 'Block1_Zone2', 'Check3_aPMV')]
    assert rows[0]['value_found'] - rows[0]['value_expected'] == pytest.approx(0.01)


def test_the_setpoints_based_on_the_pmv_need_the_outputs_at_timestep_frequency(tmp_path):
    from accim.sim import apmv

    building = _model(tmp_path)
    apmv.apply_apmv_setpoints(building, verbose=False)
    with pytest.warns(UserWarning, match="add 'timestep' to the output_frequencies"):
        rows, lines = _pmv_index_mismatches(building, None, 1e-3)
    assert rows == [] and lines[0].startswith('  Not checked.')
    # Without the outputs of a zone
    timestamps = _timestamps()
    columns = _apmv_outputs(timestamps, {zone: np.zeros(len(timestamps)) for zone in ZONES}, 0.293)
    del columns[('EMS', 'Adaptive Coefficient_Block1_Zone1', '')]
    rows, lines = _pmv_index_mismatches(building, _frame(timestamps, columns), 1e-3)
    assert "'Block1_Zone1' Check3_aPMV: not checked, without the output 'Adaptive Coefficient_Block1_Zone1'" in (
        lines[1])
    # The models without setpoints based on the PMV are not checked
    assert _pmv_index_mismatches(_model(tmp_path / 'other'), None, 1e-3) == ([], [])


@pytest.mark.parametrize('apply_to_heating', [False, True])
def test_the_epmv_and_the_pmv(tmp_path, apply_to_heating):
    from accim.sim import apmv

    timestamps = _timestamps()
    starts = _environment_starts(_dates_and_times(timestamps)[0])
    rng = np.random.default_rng(2)
    pmv = rng.uniform(-1.5, 1.5, len(timestamps))
    previous = np.nan_to_num(_previous(pmv, starts))
    columns = {('PEOPLE BLOCK1:ZONE1', FANGER_PMV, ''): pmv, ('PEOPLE BLOCK1:ZONE2', FANGER_PMV, ''): pmv}
    # Fanger and Toftum (2002): e*PMV with PMV > 0, also with PMV <= 0 with apply_to_heating
    epmv = np.where((previous > 0) | apply_to_heating, 0.7 * previous, previous)
    for zone in ZONES:
        columns[('EMS', f'ePMV_{zone}', '')] = epmv
        columns[('EMS', f'Expectancy Factor_{zone}', '')] = np.full(len(timestamps), 0.7)
    building = _model(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        apmv.apply_epmv_setpoints(building, output_frequencies=['timestep'], expectancy_factor=0.7,
                                  apply_to_heating=apply_to_heating, verbose=False)
    rows, lines = _pmv_index_mismatches(building, _frame(timestamps, columns), 1e-6)
    assert rows == [] and all('Check3_ePMV' in line for line in lines)
    # The ePMV of the other option is wrong where the PMV is negative
    other = dict(columns)
    other[('EMS', 'ePMV_Block1_Zone1', '')] = np.where((previous > 0) | (not apply_to_heating), 0.7 * previous,
                                                        previous)
    rows, _ = _pmv_index_mismatches(building, _frame(timestamps, other), 1e-6)
    assert len(rows) == ((previous < 0) & ~starts).sum()

    building = _model(tmp_path / 'pmv')
    apmv.apply_pmv_setpoints(building, output_frequencies=['timestep'], verbose=False)
    columns = {('PEOPLE BLOCK1:ZONE1', FANGER_PMV, ''): pmv, ('PEOPLE BLOCK1:ZONE2', FANGER_PMV, ''): pmv}
    for zone in ZONES:
        columns[('EMS', f'PMV_{zone}', '')] = previous
    rows, lines = _pmv_index_mismatches(building, _frame(timestamps, columns), 1e-6)
    assert rows == [] and all('Check3_PMV (PMV of the previous timestep)' in line for line in lines)


def test_the_metabolic_correction_of_a_people_object_of_several_zones(tmp_path):
    from accim.sim import apmv
    from accim.sim.pmv_index import metabolic_correction_names

    building = _model(tmp_path, RESIDENTIAL_IDF)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        apmv.apply_epmv_setpoints(building, output_frequencies=['timestep'], expectancy_factor=0.7,
                                  metabolic_correction=True, verbose=False)
    people = str(building.idfobjects['People'][0].Name)
    names = metabolic_correction_names(people)
    base_schedule = str(building.getobject('EnergyManagementSystem:Sensor', names['base'])
                        .OutputVariable_or_OutputMeter_Index_Key_Name)
    # Three days around the beginning of the cooling season (1 May)
    timestamps = _timestamps(begin='04/30')
    starts = _environment_starts(_dates_and_times(timestamps)[0])
    cooling = np.array([not stamp.strip().startswith('04/30') for stamp in timestamps])
    rng = np.random.default_rng(3)
    floors = ('FLOOR_1', 'FLOOR_2')
    pmv = {floor: rng.uniform(-0.5, 2.0, len(timestamps)) for floor in floors}
    occupants = {'FLOOR_1': rng.choice([0.0, 1.0, 3.0], len(timestamps)),
                 'FLOOR_2': rng.choice([0.0, 2.0], len(timestamps))}
    columns = {}
    previous = {}
    for floor in floors:
        key = f'{floor} RESIDENTIAL LIVING OCCUPANTS'
        zone = f'{floor.capitalize()}_Residential_Living_Occupants'
        previous[floor] = _previous(pmv[floor], starts)
        columns[(key, FANGER_PMV, '')] = pmv[floor]
        columns[(key, 'People Occupant Count', '')] = occupants[floor]
        epmv = np.nan_to_num(np.where(previous[floor] > 0, np.where(cooling, 0.7, 1) * previous[floor],
                                      previous[floor]))
        columns[('EMS', f'ePMV_{zone}', '')] = epmv
        columns[('EMS', f'Expectancy Factor_{zone}', '')] = np.where(cooling, 0.7, 1)
    # The PMV of the previous timestep, weighted by the occupants of the timestep
    mean = _weighted_mean([previous[floor] for floor in floors], [occupants[floor] for floor in floors])
    factor = np.nan_to_num(1 - 0.067 * np.clip(np.where(cooling, mean, 0), 0, 3), nan=1)
    suffix = 'Residential_Living_Occupants'
    columns[('EMS', f'Metabolic Correction Factor_{suffix}', '')] = factor
    columns[('EMS', f'Corrected Activity Level_{suffix}', '')] = 110 * factor
    columns[(base_schedule.upper(), 'Schedule Value', '')] = np.full(len(timestamps), 110.0)

    rows, lines = _pmv_index_mismatches(building, _frame(timestamps, columns), 1e-6)
    assert rows == [], rows[:3]
    # Every timestep is checked: in the heating season, the factor is 1 whatever the PMV
    assert f"  '{suffix}' Check3_MetabolicFactor (1 - 0.067*PMV in the cooling season): 0 mismatch(es) in " \
           f"{len(timestamps)} timesteps" in lines
    assert any(line.startswith(f"  '{suffix}' Check3_CorrectedActivity") for line in lines)
    # With the occupants of the previous timestep, the factor is wrong where they changed
    wrong = dict(columns)
    previous_occupants = [np.r_[0.0, occupants[floor][:-1]] for floor in floors]
    wrong_mean = _weighted_mean([previous[floor] for floor in floors], previous_occupants)
    wrong[('EMS', f'Metabolic Correction Factor_{suffix}', '')] = np.nan_to_num(
        1 - 0.067 * np.clip(np.where(cooling, wrong_mean, 0), 0, 3), nan=1)
    rows, _ = _pmv_index_mismatches(building, _frame(timestamps, wrong), 1e-6)
    assert len(rows) > 50 and {row['check'] for row in rows} == {'Check3_MetabolicFactor'}
    # Without the activity level without the correction
    del columns[(base_schedule.upper(), 'Schedule Value', '')]
    _, lines = _pmv_index_mismatches(building, _frame(timestamps, columns), 1e-6)
    assert (f"  '{suffix}' Check3_CorrectedActivity: not checked, without the output 'Schedule Value' of "
            f"'{base_schedule}' at timestep frequency.") in lines


def _add_accis(tmp_path, frequency, zone_arguments, **arguments):
    """An output IDF of AddAccis of the sample model."""
    import os
    from accim.sim.accis import AddAccis, load_idf

    if _energyplus() is None or not SAMPLE_IDF.exists():
        pytest.skip('needs EnergyPlus 25.1 and the sample IDFs of the repository')
    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                     output_type='standard', output_frequencies=[frequency], keep_existing_outputs=False,
                     energyplus_version='auto', setpoint_type='temperature', confirm=True, verbose=False,
                     zone_arguments=zone_arguments, **arguments)
    finally:
        os.chdir(cwd)
    return load_idf(sorted(tmp_path.glob('TestModel[[]*.idf'))[0])


def test_the_setpoints_against_compute_setpoints(tmp_path):
    from accim.sim.ems.objects import ZONE_SETPOINT_OUTPUT_VARIABLES
    from accim.sim.preview import SETPOINT_EMS_VARIABLES, compute_setpoints, energyplus_running_means

    building = _add_accis(tmp_path, 'hourly', {'Block1:Zone2': {'comfort_standard': 2, 'category': 80}},
                          comfort_standard=[1], category=[2], comfort_mode=[3])
    run_period = building.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 3, 10
    # The outputs that EnergyPlus would give: those of compute_setpoints, after a design day
    timestamps = _timestamps(begin='03/10', days=4, timesteps_per_hour=1, design_day='07/21')
    previews = {'Block1_Zone1': compute_setpoints(EPW, 1, 2, 3, start_date='10/03'),
                'Block1_Zone2': compute_setpoints(EPW, 2, 80, 3, start_date='10/03')}
    means = energyplus_running_means(EPW, start_date='10/03')
    columns = {}
    for zone, preview in previews.items():
        for output, (variable, _) in ZONE_SETPOINT_OUTPUT_VARIABLES.items():
            column = {v: c for c, v in SETPOINT_EMS_VARIABLES.items()}[variable]
            columns[('EMS', f'{output}_{zone}', 'C')] = np.r_[np.zeros(24), np.nan_to_num(preview[column][:96])]
    for people in ('PEOPLE BLOCK1:ZONE1', 'PEOPLE BLOCK1:ZONE2'):
        for column, variable in (('RMOT', 'CEN 15251'), ('PMOT', 'ASHRAE 55')):
            columns[(people, f'Zone Thermal Comfort {variable} Adaptive Model Running Average Outdoor Air '
                             f'Temperature', 'C')] = np.r_[np.zeros(24), np.repeat(means[column][:4], 24)]
    data = {'Hourly': _frame(timestamps, columns)}

    rows, lines = _setpoint_mismatches(building, data, str(EPW), 1e-9)
    assert rows == []
    assert lines[0] == f'  Hourly outputs from 10/03, 6 timesteps per hour, weather file {EPW}'
    assert len(lines) == 1 + 2 + 2 * 5 and all(line.endswith('0 mismatch(es) in 96 timesteps') for line in lines[1:])
    # Another weather file
    rows, _ = _setpoint_mismatches(building, data, str(OTHER_EPW), 1e-3)
    assert {row['check'] for row in rows} >= {'Check4_RMOT', 'Check4_PMOT', 'Check4_ACST', 'Check4_AHST'}
    # A .stat file next to the weather file: EnergyPlus would take PMOT from it, and the summary says so
    shutil.copy(EPW, tmp_path / 'weather.epw')
    (tmp_path / 'weather.stat').write_text('', encoding='utf-8')
    rows, lines = _setpoint_mismatches(building, data, str(tmp_path / 'weather.epw'), 1e-9)
    assert rows == [] and lines[1].startswith('  Note: weather.stat is next to the weather file')
    # Another run period
    run_period.Begin_Day_of_Month = 11
    rows, lines = _setpoint_mismatches(building, data, str(EPW), 1e-3)
    assert rows == [] and lines == ['  Not checked: the last environment of the outputs begins on 10/03, not on the '
                                    'first day of the RunPeriod (11/03).']
    # The zones whose setpoints a hook of the API backend sets are not checked (task G1 of the review of 1.2.0)
    from accim.sim.comfort_hooks import apply_athb_setpoints

    run_period.Begin_Day_of_Month = 10
    apply_athb_setpoints(building)
    rows, lines = _setpoint_mismatches(building, data, str(EPW), 1e-9)
    assert rows == [] and sorted(lines[3:]) == [
        f"  '{zone}': not checked (its setpoints are those of a hook of the API backend, ApplyHookSetpoints_{zone})."
        for zone in ('Block1_Zone1', 'Block1_Zone2')]


def _run_energyplus(tmp_path, building, begin, end):
    run_period = building.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    model = tmp_path / 'model.idf'
    building.saveas(str(model))
    result = subprocess.run([str(_energyplus() / 'energyplus.exe'), '-d', str(tmp_path / 'out'), '-p', 'run', '-s',
                             'C', '-x', '-w', str(EPW), str(model)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    return tmp_path / 'out' / 'run.eso', model


@pytest.mark.skipif(_energyplus() is None or not EPW.exists(),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_verify_accim_simulation_of_the_epmv_setpoints(tmp_path):
    from accim.sim import apmv

    building = _model(tmp_path)
    apmv.add_vrf_system(building, verbose=False)
    apmv.apply_epmv_setpoints(building, output_frequencies=['timestep'], expectancy_factor=0.7,
                              metabolic_correction=True, verbose=False)
    building.newidfobject('Output:Variable', Key_Value='*', Variable_Name='Schedule Value',
                          Reporting_Frequency='Timestep')
    # Three days around the beginning of the cooling season
    eso, model = _run_energyplus(tmp_path, building, (4, 30), (5, 2))
    result = verify_accim_simulation(str(eso), str(model), eplus_install_dir=str(_energyplus()),
                                     calculation_tolerance=1e-6)
    assert result.empty


@pytest.mark.skipif(_energyplus() is None or not EPW.exists() or not OTHER_EPW.exists(),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_verify_accim_simulation_against_compute_setpoints(tmp_path):
    building = _add_accis(tmp_path, 'timestep', {'Block1:Zone2': {'comfort_standard': 0}}, comfort_standard=[99],
                          category=[1], comfort_mode=[3], custom_slope=0.31, custom_intercept=17.8,
                          custom_cooling_offset=3.5, custom_heating_offset=-3.5, custom_cooling_upper_limit=33.5,
                          custom_cooling_lower_limit=10, custom_heating_upper_limit=33.5,
                          custom_heating_lower_limit=10)
    eso, model = _run_energyplus(tmp_path, building, (7, 1), (7, 3))
    result = verify_accim_simulation(str(eso), str(model), eplus_install_dir=str(_energyplus()), epw=str(EPW))
    assert not result['check'].str.startswith('Check4').any() if len(result) else True
    # With another weather file, the running means and the setpoints of the custom model (but not the static ones
    # of ESP CTE) are wrong
    result = verify_accim_simulation(str(eso), str(model), eplus_install_dir=str(_energyplus()), epw=str(OTHER_EPW))
    wrong = result[result['check'].str.startswith('Check4')]
    zones = set(wrong['zone_or_window'])
    assert 'Block1_Zone1' in zones and 'Block1_Zone2' not in zones
    assert {'Check4_RMOT', 'Check4_PMOT', 'Check4_ACST', 'Check4_AHST'} <= set(wrong['check'])
