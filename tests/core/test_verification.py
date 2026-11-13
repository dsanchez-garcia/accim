"""Tests for the checks of verify_accim_simulation of the values that the EMS calculates (proposal E2): check 3, the
indices derived from the PMV of accim.sim.pmv_index (aPMV = PMV/(1 + λ·PMV), Yao et al., 2009; ePMV = e·PMV with
PMV > 0, Fanger and Toftum, 2002; the PMV) and the metabolic correction of the ePMV (1 − 0.067·PMV in the cooling
season), from the PMV of the previous timestep; and check 4, the setpoints of the output IDFs of AddAccis against
accim.sim.preview.compute_setpoints (E1).

And for checks 1 and 2 (2026-11-13), which verify_accim_simulation and AccimSimulationVerifier share: check 1, the
timesteps in which the HVAC system of a zone is on and the zone is beyond its setpoint, which are reported apart from
the mismatches; and check 2, the opening factor of each window in mixed mode against that of its EMS programs, with
the values that they read (those of the previous timestep, for the operative temperature and the HVAC system).

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
    AccimSimulationVerifier,
    _compute_setpoints_arguments,
    _dates_and_times,
    _environment_starts,
    _find_column,
    _key_and_variable,
    _pmv_index_mismatches,
    _setpoint_mismatches,
    _weighted_mean,
    _window_opening,
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
# A model with radiators (existing HVAC systems), one of the inputs of the golden master
RADIATORS = REPO / 'tests' / 'core' / 'golden_master' / 'inputs' / 'exrad.idf.xz'
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
    values = dict(script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                  output_type='standard', output_frequencies=[frequency], keep_existing_outputs=False,
                  energyplus_version='auto', setpoint_type='temperature', confirm=True, verbose=False,
                  zone_arguments=zone_arguments)
    values.update(arguments)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            AddAccis(**values)
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

# ─────────────────────────────────────────────────────────────────────────────
# CHECKS 1 AND 2: THE SETPOINTS WHILE THE SYSTEMS ARE ON, AND THE OPERATION OF THE WINDOWS
# ─────────────────────────────────────────────────────────────────────────────

def test_the_key_and_the_variable_of_a_column():
    # The key of an output is the text before the last ':'. Checks 1 and 2 split the names at the first one, so the
    # key of the zone 'Block1:Zone1' was 'BLOCK1', and they skipped the zones and the windows of the models whose
    # names have ':', as those of DesignBuilder (an entry of TODO.md of 2026-11-09)
    assert _key_and_variable('Block1:Zone1:Zone Operative Temperature') == ('BLOCK1:ZONE1',
                                                                            'ZONE OPERATIVE TEMPERATURE')
    assert _key_and_variable('Environment:Site Wind Speed') == ('ENVIRONMENT', 'SITE WIND SPEED')
    # The columns of the CSV files of EnergyPlus, with the units and the frequency
    assert _key_and_variable(' BLOCK1:ZONE1 VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate '
                             '[W](TimeStep)') == ('BLOCK1:ZONE1 VRF INDOOR UNIT DX COOLING COIL',
                                                  'COOLING COIL TOTAL COOLING RATE')
    assert _key_and_variable('ACST_SCH_BLOCK1_ZONE1:Schedule Value [](Hourly)') == ('ACST_SCH_BLOCK1_ZONE1',
                                                                                    'SCHEDULE VALUE')
    assert _key_and_variable('EMS:Ventilation Setpoint Temperature_Block1_Zone1 [C](Hourly)') == (
        'EMS', 'VENTILATION SETPOINT TEMPERATURE_BLOCK1_ZONE1')
    # Without ':', no key
    assert _key_and_variable('Date/Time') == ('', 'DATE/TIME')


def test_the_column_of_a_key_and_a_variable():
    columns = ['BLOCK1:ZONE10:Zone Operative Temperature', 'BLOCK1:ZONE1:Zone Operative Temperature',
               'BLOCK1:ZONE1:Zone Thermostat Operative Temperature',
               'BLOCK1:ZONE10 VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate',
               'BLOCK1:ZONE1 VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate',
               'VRF OUTDOOR UNIT_BLOCK1:ZONE1:VRF Heat Pump Cooling Electricity Energy',
               'EMS:People Occupant Count_Block1_Zone10', 'EMS:People Occupant Count_Block1_Zone1',
               'ACST_SCH_BLOCK1_ZONE1:Schedule Value', 'Environment:Site Outdoor Air Drybulb Temperature', 'Date/Time']
    # The key with its ':', and the outputs of the zone itself, not those of 'Block1:Zone10', which are first
    assert _find_column(columns, 'Block1:Zone1', 'Operative Temperature') == columns[1]
    assert _find_column(columns, 'Block1:Zone10', 'Operative Temperature') == columns[0]
    # A key that has the zone as whole words (its coil, its outdoor unit), not within a longer name
    assert _find_column(columns, 'Block1:Zone1', 'Cooling Coil Total Cooling Rate') == columns[4]
    assert _find_column(columns, 'Block1:Zone1', 'VRF Heat Pump Cooling Electricity') == columns[5]
    # The closest variable too
    assert _find_column(columns, 'EMS', 'People Occupant Count_Block1_Zone1') == columns[7]
    assert _find_column(columns, 'ACST_Sch_Block1_Zone1', 'Schedule Value') == columns[8]
    assert _find_column(columns, 'environment', 'Drybulb') == columns[9]
    # Within a longer name, if nothing is closer (as before)
    assert _find_column(columns[:1], 'Block1:Zone1', 'Operative Temperature') == columns[0]
    assert _find_column(columns, 'Block1:Zone', 'Thermostat Operative') == columns[2]
    # Without one of the fragments, none
    assert _find_column(columns, 'Block1:Zone3', 'Operative Temperature') is None
    assert _find_column(columns, 'Block1:Zone1', 'Mean Air Temperature') is None
    # A column without a key is taken by its variable alone only if asked
    assert _find_column(columns, 'Block1:Zone1', 'Date/Time') is None
    assert _find_column(columns, 'Block1:Zone1', 'Date/Time', keyless=True) == 'Date/Time'
    # The columns of the CSV files of EnergyPlus
    csv = ['Date/Time', 'BLOCK1:ZONE10:Zone Operative Temperature [C](Hourly)',
           'BLOCK1:ZONE1:Zone Operative Temperature [C](Hourly)']
    assert _find_column(csv, 'Block1:Zone1', 'Zone Operative Temperature') == csv[2]


def _zone_columns(rows, keys=('BLOCK1:ZONE2', 'BLOCK1:ZONE1'), coils='VRF INDOOR UNIT DX'):
    """Outputs of checks 1 and 2 of the zones of the sample model, at 25 °C with setpoints of 20 and 27 °C and their
    coils off, after those of another zone, 'Block1:Zone10', which is cooled and far above them. With occupants, an
    outdoor air at 18 °C and a ventilation setpoint of 23 °C, the windows of mixed mode are open."""
    columns = {('BLOCK1:ZONE10', 'Zone Operative Temperature', 'C'): np.full(rows, 40.0),
               (f'BLOCK1:ZONE10 {coils} COOLING COIL', 'Cooling Coil Total Cooling Rate', 'W'): np.full(rows, 5000.0),
               (f'BLOCK1:ZONE10 {coils} HEATING COIL', 'Heating Coil Heating Rate', 'W'): np.full(rows, 5000.0),
               ('Environment', 'Site Outdoor Air Drybulb Temperature', 'C'): np.full(rows, 18.0),
               ('Environment', 'Site Wind Speed', 'm/s'): np.full(rows, 3.0)}
    for key in keys:
        zone = key.replace(':', '_').title()
        columns[(key, 'Zone Operative Temperature', 'C')] = np.full(rows, 25.0)
        columns[(key, 'Zone Outdoor Air Drybulb Temperature', 'C')] = np.full(rows, 18.0)
        columns[(key, 'Zone Outdoor Air Wind Speed', 'm/s')] = np.full(rows, 3.0)
        columns[(f'ACST_SCH_{zone.upper()}', 'Schedule Value', '')] = np.full(rows, 27.0)
        columns[(f'AHST_SCH_{zone.upper()}', 'Schedule Value', '')] = np.full(rows, 20.0)
        columns[(f'{key} {coils} COOLING COIL', 'Cooling Coil Total Cooling Rate', 'W')] = np.zeros(rows)
        columns[(f'{key} {coils} HEATING COIL', 'Heating Coil Heating Rate', 'W')] = np.zeros(rows)
        columns[('EMS', f'People Occupant Count_{zone}', '')] = np.full(rows, 2.0)
        columns[('EMS', f'Adaptive Cooling Setpoint Temperature_{zone}', 'C')] = np.full(rows, 27.0)
        columns[('EMS', f'Adaptive Cooling Setpoint Temperature_No Tolerance_{zone}', 'C')] = np.full(rows, 27.1)
        columns[('EMS', f'Ventilation Setpoint Temperature_{zone}', 'C')] = np.full(rows, 23.0)
        columns[('EMS', f'Minimum Outdoor Temperature for ventilation_{zone}', 'C')] = np.full(rows, 10.0)
    return columns


def _verify_outputs(monkeypatch, tmp_path, frames, **arguments):
    """verify_accim_simulation of the output IDF of tmp_path with made-up outputs ({frequency: (timestamps,
    columns)}): its result, and its warnings."""
    data = {'data': {frequency: _frame(timestamps, columns) for frequency, (timestamps, columns) in frames.items()},
            'metadata': {}}
    monkeypatch.setattr('accim.utils.verification.read_eso_using_readvarseso', lambda **keywords: data)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = verify_accim_simulation(str(tmp_path / 'run.eso'), str(sorted(tmp_path.glob('TestModel[[]*.idf'))[0]),
                                         **arguments)
    return result, [str(warning.message) for warning in caught if issubclass(warning.category, UserWarning)]


def test_check_1_reports_the_setpoints_that_the_systems_do_not_hold_apart(tmp_path, monkeypatch, capsys):
    # The zones of the sample model are 'Block1:Zone1' and 'Block1:Zone2': until 2026-11-13 check 1 skipped them with
    # the warning "No 'Operative Temperature' column found" (an entry of TODO.md of 2026-11-09)
    _add_accis(tmp_path, 'hourly', None, comfort_standard=[1], category=[2], comfort_mode=[3])
    timestamps = _timestamps(begin='07/01', days=1, timesteps_per_hour=1)
    # Zone 2 with the coils of the VRF system of accim, which its EMS sensors read; zone 1 with other coils, found by
    # their names (the key of the zone in theirs)
    columns = {**_zone_columns(len(timestamps), keys=('BLOCK1:ZONE2',)),
               **_zone_columns(len(timestamps), keys=('BLOCK1:ZONE1',), coils='PTAC')}
    temperature = columns[('BLOCK1:ZONE2', 'Zone Operative Temperature', 'C')]
    cooling = columns[('BLOCK1:ZONE2 VRF INDOOR UNIT DX COOLING COIL', 'Cooling Coil Total Cooling Rate', 'W')]
    heating = columns[('BLOCK1:ZONE2 VRF INDOOR UNIT DX HEATING COIL', 'Heating Coil Heating Rate', 'W')]
    # Zone 2: heated and below its heating setpoint by more than the tolerance (0.1 °C) at 4:00, and within it at 5:00
    temperature[[3, 4]], heating[[3, 4]] = [19.5, 19.95], 500
    # Cooled and above its cooling setpoint by more than the tolerance at 11:00 and 12:00, and within it at 13:00;
    # above it but not cooled at 14:00
    temperature[[10, 11, 12, 13]], cooling[[10, 11, 12]] = [27.5, 28.0, 27.05, 29.0], 1000
    # Zone 1: cooled and above its setpoint at 16:00
    columns[('BLOCK1:ZONE1', 'Zone Operative Temperature', 'C')][15] = 27.4
    columns[('BLOCK1:ZONE1 PTAC COOLING COIL', 'Cooling Coil Total Cooling Rate', 'W')][15] = 800
    result, messages = _verify_outputs(monkeypatch, tmp_path, {'Hourly': (timestamps, columns)})
    output = capsys.readouterr().out
    assert not [message for message in messages if 'Skipping' in message or 'not found' in message]
    # They are not mismatches of the EMS: the result is empty, and its attribute has them
    assert result.empty and 'All checks passed. No mismatches detected.' in output
    not_met = result.attrs['setpoints_not_met']
    assert list(not_met.columns) == ['timestep', 'zone_or_window', 'check', 'description', 'value_found',
                                     'value_expected']
    assert not_met[['timestep', 'zone_or_window', 'check', 'value_found']].values.tolist() == [
        [timestamps[3].strip(), 'Block1_Zone2', 'Check1_Heating', 19.5],
        [timestamps[10].strip(), 'Block1_Zone2', 'Check1_Cooling', 27.5],
        [timestamps[11].strip(), 'Block1_Zone2', 'Check1_Cooling', 28.0],
        [timestamps[15].strip(), 'Block1_Zone1', 'Check1_Cooling', 27.4]]
    assert not_met['description'].iloc[1] == ('Cooling active (rate=1000.00 W) but OpT (27.50 °C) > ACST (27.00 °C) + '
                                              'tolerance (0.1 °C)')
    assert not_met['value_expected'].tolist() == ['>= 19.90 °C', '<= 27.10 °C', '<= 27.10 °C', '<= 27.10 °C']
    summary = "  '{}' Check1_{} ({} setpoint by more than 0.1 °C): {} of 24 hours"
    assert summary.format('Block1_Zone2', 'Cooling', 'cooled and above its cooling', 2) in output
    assert summary.format('Block1_Zone2', 'Heating', 'heated and below its heating', 1) in output
    # Zone 1 with its own outputs, not with those of 'Block1:Zone10', which are first
    assert summary.format('Block1_Zone1', 'Cooling', 'cooled and above its cooling', 1) in output
    assert ("4 timestep(s) with the HVAC system of a zone on and the zone beyond its setpoint (check 1): they are not "
            "mismatches of the EMS, and they are in attrs['setpoints_not_met'] of the result.") in output

    # setpoints_not_met=True adds them to the result, as until accim 1.2.0
    result, _ = _verify_outputs(monkeypatch, tmp_path, {'Hourly': (timestamps, columns)}, setpoints_not_met=True)
    pd.testing.assert_frame_equal(result, not_met)
    # With another tolerance
    result, _ = _verify_outputs(monkeypatch, tmp_path, {'Hourly': (timestamps, columns)}, tolerance=0.45)
    assert result.attrs['setpoints_not_met']['timestep'].tolist() == [timestamps[i].strip() for i in (3, 10, 11)]

    # The outputs at timestep frequency first: those of each hour repeated, but for one timestep of zone 1
    steps = _timestamps(begin='07/01', days=1, timesteps_per_hour=6)
    fine = {column: np.repeat(values, 6) for column, values in columns.items()}
    fine[('BLOCK1:ZONE1', 'Zone Operative Temperature', 'C')][90:96] = [27.4, 27.4, 25.0, 27.4, 27.4, 27.4]
    result, _ = _verify_outputs(monkeypatch, tmp_path, {'Hourly': (timestamps, columns), 'Timestep': (steps, fine)})
    output = capsys.readouterr().out
    assert len(result.attrs['setpoints_not_met']) == 6 * 3 + 5 and '  Timestep outputs' in output
    assert "'Block1_Zone1' Check1_Cooling (cooled and above its cooling setpoint by more than 0.1 °C): 5 of 144 " \
        "timesteps" in output


WINDOW_CASES = [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3)]


@pytest.mark.parametrize('script_type', ['vrf_mm', 'ex_mm'])
@pytest.mark.parametrize('hvac_mode, ventilation_control', WINDOW_CASES)
def test_the_opening_factor_of_check_2_is_that_of_the_ems_programs(script_type, hvac_mode, ventilation_control):
    # The programs SetMyVOF_<window> and SetWindowOperation_<window> of accim, run by the Erl interpreter with random
    # values of what they read, against the opening factor that check 2 expects from them: with the VRF systems of
    # accim (the coils) and with the existing HVAC systems (the load to the setpoints), in the HVAC modes and the
    # ventilation controls of mixed mode
    from types import SimpleNamespace

    from accim.sim.ems.erl import ErlProgramSet, variables_in_programs
    from accim.sim.ems.inputs import input_lines, input_values
    from accim.sim.ems.programs import accis_programs

    window = 'Zone1_Win'
    model = SimpleNamespace(script_type=script_type, ems_names=['Zone1'], ems_zones=['Zone1'], is_mixed_mode=True,
                            windows=[window], window_zones=['Zone1'])
    programs = dict(accis_programs(model))
    arguments = dict(comfort_standard=1, category=2, comfort_mode=3, hvac_mode=hvac_mode,
                     ventilation_control=ventilation_control, setpoint_tolerance=0.1, max_wind_speed=4.0)
    programs['SetInputData_Zone1'] = input_lines(input_values(arguments), mixed_mode=True)
    erl = ErlProgramSet(programs, global_variables=set().union(*variables_in_programs(programs).values()))
    erl.strict = True
    erl.run('InitASTvariables')
    steps = 1500
    rng = np.random.default_rng(20261113)
    read = {name: np.empty(steps) for name in (
        'operative', 'outdoor', 'wind', 'occupants', 'cooling_setpoint', 'cooling_setpoint_no_tolerance',
        'ventilation_setpoint', 'minimum_outdoor', 'design_day')}
    read['hvac_off'] = np.empty(steps, dtype=bool)
    found = np.empty(steps)
    for step in range(steps):
        operative, outdoor, wind = rng.uniform(14, 34), rng.uniform(-8, 38), rng.uniform(0, 8)
        occupants, design_day = float(rng.integers(0, 3)), float(rng.random() < 0.05)
        # A negative load to the setpoints is a cooling coil that cools, and a positive one a heating coil that heats
        load = float(rng.choice([0.0, 0.0, -400.0, 300.0]))
        for name in ('Zone1', window):
            for suffix, value in (('_OpT', operative), ('_OutT', outdoor), ('_WindSpeed', wind),
                                  ('_LoadToSetpoint', load), ('_CoolCoil', max(-load, 0.0)),
                                  ('_HeatCoil', max(load, 0.0))):
                erl.set(name + suffix, value)
        running_mean = rng.uniform(5, 32)
        for name, value in dict(RMOT=running_mean, PMOT=running_mean, DayOfYear=180.0, CurrentTime=12.0,
                                ZoneTimeStep=0.25, Occ_count_Zone1=occupants, Zone1_Win_Occ_count=occupants,
                                DesignDay=design_day).items():
            erl.set(name, value)
        erl.run('RunACCIS_Zone1')
        found[step] = erl.get(f'{window}_VentOpenFact')
        for name, variable in (('cooling_setpoint', 'roundedACST'), ('cooling_setpoint_no_tolerance', 'ACSTnoTol'),
                               ('ventilation_setpoint', 'VST'), ('minimum_outdoor', 'MinOutTemp')):
            read[name][step] = erl.get(variable)
        for name, value in (('operative', operative), ('outdoor', outdoor), ('wind', wind), ('occupants', occupants),
                            ('design_day', design_day), ('hvac_off', load == 0)):
            read[name][step] = value
    for name in ('MaxWindSpeed', 'MultiplierVOF', 'MinTempDiffVOF', 'MaxTempDiffVOF'):
        read[name] = float(erl.get(name))
    assert read['MaxWindSpeed'] == 4.0

    np.testing.assert_array_equal(_window_opening(hvac_mode, ventilation_control, read), found)
    # The cases have open and closed windows (but the full air-conditioning), and partly open ones where the program
    # gives the opening factor of SetMyVOF_<window>
    assert bool((found > 0).any()) == (hvac_mode != 0) and (found == 0).sum() > steps / 2
    partly_open = hvac_mode == 1 or (hvac_mode == 2 and ventilation_control in (2, 3))
    assert bool(((found > 0) & (found < 1)).any()) == partly_open
    # Without the operative temperature of the previous timestep (the first timestep of an environment), not checked
    read['operative'][0] = np.nan
    assert np.isnan(_window_opening(hvac_mode, ventilation_control, read)[0])


def test_the_opening_factor_of_a_ventilation_control_that_the_program_has_not():
    # The program of HVAC mode 1 has the ventilation controls 0 and 1 only
    assert _window_opening(1, 2, {}) is None and _window_opening(3, 0, {}) is None


def _window_surfaces(building):
    """The surface of each window of a model in mixed mode with the AirflowNetwork, by its name in the EMS."""
    return {actuator.Name[:-len('_VentOpenFact')]: str(actuator.Actuated_Component_Unique_Name)
            for actuator in building.idfobjects['EnergyManagementSystem:Actuator']
            if actuator.Name.endswith('_VentOpenFact')}


def test_check_2_compares_the_opening_factor_of_each_window_with_that_of_its_programs(tmp_path, monkeypatch, capsys):
    # The windows of the sample model are 'Block1:Zone1_Wall_2_0_0_0_0_0_Win'... (their surfaces, the keys of their
    # outputs), and 'Block1_Zone1_Wall_2_0_0_0_0_0_Win'... in the EMS: until 2026-11-13 check 2 skipped them
    building = _add_accis(tmp_path, 'timestep', None, script_type='vrf_mm', comfort_standard=[1], category=[2],
                          comfort_mode=[3], hvac_mode=[2], ventilation_control=[0])
    surfaces = _window_surfaces(building)
    assert len(surfaces) == 6 and all(':' in surface and ':' not in window for window, surface in surfaces.items())
    timestamps = _timestamps(begin='05/01', days=1, timesteps_per_hour=6)
    rows = len(timestamps)
    columns = _zone_columns(rows)
    # Zone 1: what the programs of its windows read, and the opening factor that they give (1 or 0, with
    # ventilation_control 0): the zone at 25 °C, between the ventilation setpoint (23 °C) and the cooling one (27 °C),
    # occupied, with an outdoor air at 18 °C (above the minimum, 10 °C), a wind speed of 3 m/s and the coils off
    opening = np.ones(rows)
    columns[('EMS', 'People Occupant Count_Block1_Zone1', '')][20:26] = 0        # no occupants: closed
    opening[20:26] = 0
    coil = ('BLOCK1:ZONE1 VRF INDOOR UNIT DX COOLING COIL', 'Cooling Coil Total Cooling Rate', 'W')
    columns[coil][40] = 500                                                      # cooled in the timestep before
    opening[41] = 0
    temperature = columns[('BLOCK1:ZONE1', 'Zone Operative Temperature', 'C')]
    temperature[60], temperature[80] = 22.5, 27.5      # in the timestep before: below the ventilation setpoint...
    opening[[61, 81]] = 0                              # ...and above the cooling setpoint
    columns[('BLOCK1:ZONE1', 'Zone Outdoor Air Drybulb Temperature', 'C')][100:103] = 26   # warmer than the zone
    opening[100:103] = 0
    columns[('BLOCK1:ZONE1', 'Zone Outdoor Air Wind Speed', 'm/s')][110] = 60    # above the maximum (50 m/s)
    opening[110] = 0
    columns[('BLOCK1:ZONE1', 'Zone Outdoor Air Drybulb Temperature', 'C')][120] = 5        # below the minimum
    opening[120] = 0
    for window, surface in surfaces.items():
        factor = opening.copy() if window.startswith('Block1_Zone1_') else np.ones(rows)
        columns[(surface.upper(), 'AFN Surface Venting Window or Door Opening Factor', '')] = factor
    # The second window of zone 1 is open after a timestep in which its zone was cooled, and closed in a timestep
    # in which its program opens it
    wrong = sorted(window for window in surfaces if window.startswith('Block1_Zone1_'))[1]
    factor = columns[(surfaces[wrong].upper(), 'AFN Surface Venting Window or Door Opening Factor', '')]
    factor[41], factor[50] = 1, 0
    result, messages = _verify_outputs(monkeypatch, tmp_path, {'Timestep': (timestamps, columns)})
    output = capsys.readouterr().out
    assert not [message for message in messages if 'Skipping' in message or 'not found' in message]
    assert result[['timestep', 'zone_or_window', 'check', 'value_found', 'value_expected']].values.tolist() == [
        [timestamps[41].strip(), wrong, 'Check2_OpeningFactor', 1.0, 0.0],
        [timestamps[50].strip(), wrong, 'Check2_OpeningFactor', 0.0, 1.0]]
    assert result['description'].iloc[0] == (
        f'The opening factor of {wrong} is 1.000000 instead of 0.000000, that of its EMS programs (operative '
        f'temperature of the previous timestep 25.00 °C, cooling setpoint 27.00 °C, ventilation setpoint 23.00 °C, '
        f'outdoor air 18.00 °C (minimum 10.00 °C), wind speed 3.00 m/s (maximum 50 m/s), occupants 2, HVAC system on '
        f'in the previous timestep)')
    assert 'HVAC system off in the previous timestep' in result['description'].iloc[1]
    # Each window with the opening factor of its own surface; the first timestep is not checked
    for window in surfaces:
        open_in = int(columns[(surfaces[window].upper(), 'AFN Surface Venting Window or Door Opening Factor',
                               '')].sum())
        assert (f"  '{window}' Check2_OpeningFactor (its opening factor against that of its EMS programs): "
                f"{2 if window == wrong else 0} mismatch(es) in {rows - 1} timesteps; open in {open_in}") in output
    assert 'Note: the outputs lack the outdoor air temperature' not in output

    # Without the outdoor air temperature and the wind speed of the zones, those of the site, and a note: with all
    # the windows open, a wind speed of the site above the maximum (when that of the zones is not) gives mismatches
    # that are not so
    columns = _zone_columns(rows)
    for key in ('BLOCK1:ZONE1', 'BLOCK1:ZONE2'):
        del columns[(key, 'Zone Outdoor Air Drybulb Temperature', 'C')]
        del columns[(key, 'Zone Outdoor Air Wind Speed', 'm/s')]
    for surface in surfaces.values():
        columns[(surface.upper(), 'AFN Surface Venting Window or Door Opening Factor', '')] = np.ones(rows)
    result, _ = _verify_outputs(monkeypatch, tmp_path, {'Timestep': (timestamps, columns)})
    output = capsys.readouterr().out
    assert result.empty
    assert "  Note: the outputs lack the outdoor air temperature and the wind speed of the zones of the windows, " \
        "which their programs read ('Zone Outdoor Air Drybulb Temperature' and 'Zone Outdoor Air Wind Speed', which " \
        "output_type='detailed' adds): those of the site are taken instead, so a mismatch may be the difference " \
        "between them." in output
    columns[('Environment', 'Site Wind Speed', 'm/s')][130] = 60
    result, _ = _verify_outputs(monkeypatch, tmp_path, {'Timestep': (timestamps, columns)})
    capsys.readouterr()
    assert result['timestep'].tolist() == [timestamps[130].strip()] * 6
    assert set(result['check']) == {'Check2_OpeningFactor'} and set(result['zone_or_window']) == set(surfaces)

    # It needs the outputs at timestep frequency
    hours = _timestamps(begin='05/01', days=1, timesteps_per_hour=1)
    result, _ = _verify_outputs(monkeypatch, tmp_path, {'Hourly': (hours, {
        column: values[::6] for column, values in columns.items()})})
    output = capsys.readouterr().out
    assert result.empty and ('  Not checked: it needs the outputs at timestep frequency, since the EMS opens and '
                             'closes each window with the operative temperature and the HVAC system of the previous '
                             'timestep.') in output


def test_the_detailed_outputs_of_mixed_mode_have_what_the_programs_of_the_windows_read(tmp_path):
    def outputs(folder, **arguments):
        building = _add_accis(folder, 'timestep', None, comfort_standard=[1], category=[2], comfort_mode=[3],
                              **arguments)
        return sorted((str(output.Key_Value), str(output.Variable_Name), str(output.Reporting_Frequency))
                      for output in building.idfobjects['Output:Variable']
                      if str(output.Variable_Name).startswith('Zone Outdoor Air'))

    mixed_mode = dict(script_type='vrf_mm', hvac_mode=[2], ventilation_control=[0])
    for name in ('standard', 'detailed', 'full'):
        (tmp_path / name).mkdir()
    # The outdoor air temperature and the wind speed of the zones of the windows, which check 2 needs to be exact
    assert outputs(tmp_path / 'detailed', output_type='detailed', **mixed_mode) == [
        (zone, variable, 'Timestep') for zone in ('Block1:Zone1', 'Block1:Zone2')
        for variable in ('Zone Outdoor Air Drybulb Temperature', 'Zone Outdoor Air Wind Speed')]
    # Not with the standard outputs, nor without mixed mode
    assert outputs(tmp_path / 'standard', **mixed_mode) == []
    assert outputs(tmp_path / 'full', output_type='detailed') == []


@pytest.mark.skipif(_energyplus() is None or not EPW.exists(),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_check_1_of_a_simulation_of_the_sample_model(tmp_path, capsys):
    building = _add_accis(tmp_path, 'timestep', None, comfort_standard=[1], category=[2], comfort_mode=[3])
    eso, model = _run_energyplus(tmp_path, building, (7, 1), (7, 2))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = verify_accim_simulation(str(eso), str(model), eplus_install_dir=str(_energyplus()))
    output = capsys.readouterr().out
    assert not [warning for warning in caught if 'Skipping' in str(warning.message)]
    # The timesteps of check 1 are those in which a zone is cooled (or heated) and its operative temperature is beyond
    # its setpoint by more than the tolerance (0.1 °C), in the CSV file that ReadVarsESO leaves next to the ESO file;
    # they are not mismatches
    outputs = pd.read_csv(tmp_path / 'out' / 'run.csv')
    outputs.columns = [column.strip() for column in outputs.columns]
    assert len(outputs) == 2 * 24 * 6 and result.empty
    not_met = result.attrs['setpoints_not_met']
    for zone in ZONES:
        key = zone.replace('_', ':').upper()
        temperature = outputs[f'{key}:Zone Operative Temperature [C](TimeStep)']
        cooled = outputs[f'{key} VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate [W](TimeStep)'] > 0
        heated = outputs[f'{key} VRF INDOOR UNIT DX HEATING COIL:Heating Coil Heating Rate [W](TimeStep)'] > 0
        too_hot = cooled & (temperature > outputs[f'ACST_SCH_{zone.upper()}:Schedule Value [](TimeStep)'] + 0.1)
        too_cold = heated & (temperature < outputs[f'AHST_SCH_{zone.upper()}:Schedule Value [](TimeStep)'] - 0.1)
        for check, expected, state in (('Check1_Cooling', too_hot, 'cooled and above its cooling'),
                                       ('Check1_Heating', too_cold, 'heated and below its heating')):
            rows = not_met[(not_met['zone_or_window'] == zone) & (not_met['check'] == check)]
            assert rows['timestep'].tolist() == [text.strip() for text in outputs.loc[expected, 'Date/Time']]
            assert f"  '{zone}' {check} ({state} setpoint by more than 0.1 °C): {expected.sum()} of 288 timesteps" \
                in output
    # The system of the sample model, cooling, does not hold the cooling setpoint in the afternoons of July
    assert (not_met['check'] == 'Check1_Cooling').sum() > 0 and not (not_met['check'] == 'Check1_Heating').any()


@pytest.mark.skipif(_energyplus() is None or not EPW.exists(),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
@pytest.mark.parametrize('output_type, hvac_mode, ventilation_control', [
    ('detailed', 2, 0), ('standard', 2, 0), ('detailed', 2, 2), ('detailed', 1, 0)])
def test_check_2_of_a_simulation_of_the_sample_model_in_mixed_mode(tmp_path, capsys, monkeypatch, output_type,
                                                                   hvac_mode, ventilation_control):
    import accim.utils.verification as verification

    building = _add_accis(tmp_path, 'timestep', None, script_type='vrf_mm', output_type=output_type,
                          comfort_standard=[1], category=[2], comfort_mode=[3], hvac_mode=[hvac_mode],
                          ventilation_control=[ventilation_control])
    surfaces = _window_surfaces(building)
    eso, model = _run_energyplus(tmp_path, building, (4, 29), (5, 1))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = verify_accim_simulation(str(eso), str(model), eplus_install_dir=str(_energyplus()))
    output = capsys.readouterr().out
    assert not [warning for warning in caught if 'Skipping' in str(warning.message)]
    # The opening factor of each window is that of its EMS programs in every timestep but the first one: with the
    # outdoor air temperature and the wind speed of its zone (the detailed outputs), or with those of the site (the
    # standard outputs; the maximum wind speed, 50 m/s, is not reached)
    assert result.empty and len(surfaces) == 6
    outputs = pd.read_csv(tmp_path / 'out' / 'run.csv')
    outputs.columns = [column.strip() for column in outputs.columns]
    for window, surface in surfaces.items():
        factor = outputs[f'{surface.upper()}:AFN Surface Venting Window or Door Opening Factor [](TimeStep)']
        assert (factor > 0).any() and (factor == 0).any()
        # Fully open, or with the opening factor of SetMyVOF_<window>
        assert bool(((factor > 0.001) & (factor < 0.999)).any()) == (hvac_mode == 1 or ventilation_control == 2)
        assert (f"  '{window}' Check2_OpeningFactor (its opening factor against that of its EMS programs): 0 "
                f"mismatch(es) in 431 timesteps; open in {(factor > 0).sum()}") in output
    assert ('Note: the outputs lack the outdoor air temperature' in output) == (output_type == 'standard')

    # AccimSimulationVerifier has the same checks (it raised a ValueError with these zones), and reads the CSV file
    # that ReadVarsESO left next to the ESO file
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        verifier = AccimSimulationVerifier(str(eso), str(model), eplus_install_dir=str(_energyplus()))
    printed = capsys.readouterr().out
    assert 'Reading CSV file directly' in printed and verifier.summary in printed
    assert len(verifier.violations['window']) == 0 and len(verifier.summary_table_window) == 0
    assert verifier.summary.splitlines()[-1] == '0 mismatch(es) of the operation of the windows.'
    pd.testing.assert_frame_equal(verifier.violations['setpoint'], result.attrs['setpoints_not_met'])
    for window in surfaces:
        assert f"  '{window}' Check2_OpeningFactor" in verifier.summary

    # A window that is open in a timestep in which its program closes it is a mismatch
    window, surface = sorted(surfaces.items())[0]
    column = next(c for c in verification.read_eso_using_readvarseso(
        eso_file_path=str(eso), eplus_install_dir=str(_energyplus()), only_run_period=True, cleanup=False,
    )['data']['Timestep'].columns if c[0].upper() == surface.upper() and 'Opening Factor' in c[1])

    def changed_outputs(**arguments):
        data = read(**arguments)
        frame = data['data']['Timestep']
        closed = np.flatnonzero(frame[column].to_numpy() == 0)
        frame.iloc[closed[10], frame.columns.get_loc(column)] = 1.0
        return data

    read = verification.read_eso_using_readvarseso
    monkeypatch.setattr(verification, 'read_eso_using_readvarseso', changed_outputs)
    result = verify_accim_simulation(str(eso), str(model), eplus_install_dir=str(_energyplus()))
    assert result[['zone_or_window', 'check', 'value_found', 'value_expected']].values.tolist() == [
        [window, 'Check2_OpeningFactor', 1.0, 0.0]]


@pytest.mark.skipif(_energyplus() is None or not EPW.exists() or not RADIATORS.exists(),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_check_2_of_a_simulation_with_existing_hvac_systems_in_mixed_mode(tmp_path, capsys, monkeypatch):
    import lzma

    from accim.sim.accis import add_accis_to_idf, load_idf, modify_accis
    from accim.sim.hvac.existing import LOAD_TO_SETPOINT_OUTPUT

    path = tmp_path / 'radiators.idf'
    path.write_bytes(lzma.decompress(RADIATORS.read_bytes()))
    building = load_idf(path)
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(building, script_type='ex_mm', output_type='detailed', output_frequencies=['timestep'],
                         keep_existing_outputs=False, setpoint_type='temperature', verbose=False)
        modify_accis(building, comfort_standard=1, category=2, comfort_mode=3, hvac_mode=2, ventilation_control=0)
    # With 'ex_mm' the programs of the windows read the load to the setpoints that the thermostat of their zone asks
    # for (not the coils of a VRF system): the detailed outputs have it, with the outdoor air temperature and the
    # wind speed of the zones of the windows
    read_by_the_programs = (LOAD_TO_SETPOINT_OUTPUT, 'Zone Outdoor Air Drybulb Temperature',
                            'Zone Outdoor Air Wind Speed')
    assert sorted((str(output.Key_Value), str(output.Variable_Name), str(output.Reporting_Frequency))
                  for output in building.idfobjects['Output:Variable']
                  if output.Variable_Name in read_by_the_programs) == sorted(
        (zone, variable, 'Timestep') for zone in ('Block1:Zone1', 'Block1:Zone2') for variable in read_by_the_programs)
    surfaces = _window_surfaces(building)
    eso, model = _run_energyplus(tmp_path, building, (4, 29), (5, 5))
    result = verify_accim_simulation(str(eso), str(model), eplus_install_dir=str(_energyplus()))
    output = capsys.readouterr().out

    # The opening factor of each window is that of its EMS programs in every timestep but the first one
    assert result.empty and len(surfaces) == 6
    assert 'Note: the outputs lack the outdoor air temperature' not in output
    outputs = pd.read_csv(tmp_path / 'out' / 'run.csv')
    outputs.columns = [column.strip() for column in outputs.columns]
    for window, surface in surfaces.items():
        factor = outputs[f'{surface.upper()}:AFN Surface Venting Window or Door Opening Factor [](TimeStep)']
        assert (factor > 0).any() and (factor == 0).any()
        assert (f"  '{window}' Check2_OpeningFactor (its opening factor against that of its EMS programs): 0 "
                f"mismatch(es) in 1007 timesteps; open in {(factor > 0).sum()}") in output
    # The thermostats ask for a load in some timesteps and for none in others
    for zone in ('BLOCK1:ZONE1', 'BLOCK1:ZONE2'):
        load = outputs[f'{zone}:{LOAD_TO_SETPOINT_OUTPUT} [W](TimeStep)']
        assert (load != 0).any() and (load == 0).any()
