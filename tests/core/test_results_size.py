"""Tests for the size of the results of the simulations, estimated before running them: accim.sim.results_size,
accim.run.estimate_results_size and the estimate that AddAccis prints before writing the output IDFs.

On 2026-11-08 the author asked for a way to know the size of the results of the simulations of run_ep, like the
estimate of the parametric module, without simulation or, more exactly, with a simulation, and to know it when the
output IDFs are generated, to choose their outputs. An output IDF of the sample model with the standard hourly outputs
writes about 30 MB in each simulation (ESO 16.3 MB, CSV 11.3 MB, MTR and Meter.csv 2.0 MB, other files 0.5 MB), so
140 output IDFs with 6 EPWs take about 25 GB.
"""
import builtins
import lzma
import os
import warnings
from pathlib import Path

import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.run import results_size as run_results_size
from accim.sim import results_size

REPO = Path(__file__).resolve().parents[2]
INPUTS = REPO / 'tests' / 'core' / 'golden_master' / 'inputs'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and INPUTS.exists()),
                               reason='needs EnergyPlus 25.1 (its IDD) and the input models of the golden master')
needs_energyplus = pytest.mark.skipif(find_energyplus('25.1', required=False) is None or not SAMPLE_EPW.exists(),
                                      reason='needs EnergyPlus 25.1 and the sample EPW files')

_MODEL = """
Version, 25.1;
Timestep, 4;
SimulationControl, No, No, No, {sizing}, Yes;
RunPeriod, Year, 1, 1, {year}, 12, 31, {year};
SizingPeriod:DesignDay, Summer, 7, 21, SummerDesignDay;
SizingPeriod:DesignDay, Winter, 1, 21, WinterDesignDay;
Zone, Zone1;
Zone, Zone2;
People, People Zone1, Zone1, Always On, People, 1;
People, People Zone2, Zone2, Always On, People, 1;
EnergyManagementSystem:OutputVariable, Comfort Temperature, ComfTemp, Averaged, ZoneTimestep;
Output:Variable, *, Zone Operative Temperature, Hourly;
Output:Variable, Zone1, Zone Operative Temperature, Hourly;
Output:Variable, *, Zone Thermal Comfort Fanger Model PMV, Hourly;
Output:Variable, *, Site Outdoor Air Drybulb Temperature, Timestep;
Output:Variable, *, Facility Total HVAC Electric Demand Power, Hourly;
Output:Variable, *, Facility Total HVAC Electricity Demand Rate, Hourly;
Output:Variable, *, AFN Zone Ventilation Volume, Hourly;
Output:Variable, *, Comfort Temperature, Hourly;
Output:Variable, *, Some Variable Unknown To Accim, Daily;
Output:Variable, AHST_Sch_Zone1, Schedule Value, Hourly;
Output:Variable, ACST_Sch_Zone1, Schedule Value, Hourly;
Output:Meter, Electricity:Facility, Hourly;
Output:Meter, DistrictHeating:Facility, Hourly;
Output:Meter:MeterFileOnly, Electricity:Facility, Monthly;
{extra}
"""


def _model(tmp_path, sizing='No', year=2001, extra=''):
    from accim.sim.accis import load_idf

    path = tmp_path / 'model.idf'
    path.write_text(_MODEL.format(sizing=sizing, year=year, extra=extra))
    return load_idf(path)


@needs_idd
def test_the_series_are_the_keys_of_the_variables_and_the_meters_at_each_frequency(tmp_path):
    size = results_size.estimate_simulation_size(_model(tmp_path))

    # Hourly: Zone Operative Temperature of the 2 zones ('*', which includes Zone1), PMV of the 2 People objects, the
    # facility demand (its old name, which accim also requests, is not counted), the EMS output variable, the 2
    # schedules and the meter (not DistrictHeating:Facility, without district heating); none of AFN without an
    # AirflowNetwork. Monthly: the meter of the MTR file only
    assert size.series == {'timestep': 1, 'hourly': 9, 'daily': 1, 'monthly': 1, 'runperiod': 0, 'annual': 0}
    assert size.describe_series() == '1 values every timestep, 9 every hour, 1 every day, 1 every month'
    assert size.notes == ["the keys of the variables ['Some Variable Unknown To Accim'], requested with the key *, "
                          "were counted as one each"]


@needs_idd
def test_the_sizes_follow_the_values_that_the_files_report(tmp_path):
    size = results_size.estimate_simulation_size(_model(tmp_path))
    leap_year = results_size.estimate_simulation_size(_model(tmp_path, year=2024))

    # 365 days, 4 timesteps per hour: in the CSV file a row for each timestep, with the 11 series of the ESO file
    # (8 hourly variables and the hourly meter, the timestep variable and the daily one)
    assert size.csv_values == 365 * 24 * 4 * 11
    assert leap_year.csv_values == 366 * 24 * 4 * 11
    assert leap_year.eso == pytest.approx(size.eso * 366 / 365, rel=0.01)
    # The values of the ESO and CSV files are most of the results
    assert size.eso > size.csv > size.mtr > 0 and size.meter_csv > 0
    assert size.kept == size.eso + size.csv
    assert size.total == pytest.approx(size.eso + size.csv + size.mtr + size.meter_csv + size.other)
    assert size.csv_memory == size.csv_values * 8
    assert size.sql == 0


@needs_idd
def test_the_design_days_are_in_the_csv_file_unless_energyplus_writes_it(tmp_path):
    without = results_size.estimate_simulation_size(_model(tmp_path))
    design_days = results_size.estimate_simulation_size(_model(tmp_path, sizing='Yes'))
    direct_csv = results_size.estimate_simulation_size(_model(tmp_path, sizing='Yes',
                                                              extra='OutputControl:Files, Yes;'))

    # Two design days of 24 hours more in the ESO file; ReadVarsESO writes them in the CSV file, and EnergyPlus,
    # with 'Output CSV' (OutputControl:Files, which AddAccis adds), only the run periods
    assert design_days.eso > without.eso
    assert design_days.csv_values == (365 + 2) * 24 * 4 * 11
    assert direct_csv.eso == design_days.eso
    assert direct_csv.csv == without.csv


@needs_idd
def test_the_sql_file_and_the_notes(tmp_path):
    simple = results_size.estimate_simulation_size(_model(tmp_path, extra='Output:SQLite, Simple;'))
    tabular = results_size.estimate_simulation_size(_model(
        tmp_path, extra='Output:SQLite, SimpleAndTabular; Output:Table:SummaryReports, AllSummary;'))
    debug = results_size.estimate_simulation_size(_model(
        tmp_path, extra='Output:EnergyManagementSystem, Verbose, Verbose, Verbose; '
                        'Output:Variable, *, Zone Air Temperature, Detailed;'))

    assert tabular.sql > simple.sql > 0
    assert any('EDD file is not included' in note for note in debug.notes)
    assert any('Detailed' in note for note in debug.notes)
    assert 'SQL' in simple.describe()


def test_format_size():
    assert [results_size.format_size(size) for size in (512, 2_500, 30_083_748, 25.3e9)] == [
        '512 bytes', '2.5 kB', '30.1 MB', '25.3 GB']


def test_the_idfs_with_the_same_outputs_are_one_group(tmp_path):
    text = _MODEL.format(sizing='No', year=2001, extra='EnergyManagementSystem:Program, SetInputData_Zone1, '
                                                       'set ComfStand = 1;')
    for name, idf_text in [('a.idf', text), ('b.idf', text.replace('set ComfStand = 1', 'set ComfStand = 2')),
                           ('c.idf', text + 'Output:Variable, *, Zone Mean Air Temperature, Hourly;')]:
        (tmp_path / name).write_text(idf_text)

    signature = run_results_size._outputs_signature
    # The output IDFs of a model of AddAccis differ in their arguments (EMS programs), not in their outputs
    assert signature(tmp_path / 'a.idf') == signature(tmp_path / 'b.idf')
    assert signature(tmp_path / 'a.idf') != signature(tmp_path / 'c.idf')


def test_estimate_results_size_needs_idfs_and_for_a_simulation_an_epw(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match='There are no IDFs'):
        run_results_size.estimate_results_size(only_accim_idfs=True)
    (tmp_path / 'model[CS_X.idf').write_text(_MODEL.format(sizing='No', year=2001, extra=''))
    with pytest.raises(ValueError, match='simulate=True needs an EPW'):
        run_results_size.estimate_results_size(simulate=True, only_accim_idfs=True)


@needs_idd
def test_a_failed_simulation_gives_the_estimate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'model[CS_X.idf').write_text(_MODEL.format(sizing='No', year=2001, extra=''))
    (tmp_path / 'weather.epw').write_text('')

    def fail(*args):
        raise RuntimeError('EnergyPlus ended with exit code 1')

    monkeypatch.setattr(run_results_size, '_simulate', fail)
    with pytest.warns(UserWarning, match='The simulation of model\\[CS_X.idf failed'):
        df = run_results_size.estimate_results_size(simulate=True, only_accim_idfs=True, verbose=False)

    assert df['source'].tolist() == ['estimate (the simulation failed)']
    assert df['simulation_mb'].iloc[0] > 0


def _output_idf(tmp_path, days=31):
    """An output IDF of the sample model in mixed mode, with the standard hourly outputs, for some days of January."""
    from accim.sim.accis import add_accis_to_idf, load_idf

    source = tmp_path / 'source.idf'
    source.write_bytes(lzma.decompress((INPUTS / 'vrf2zones.idf.xz').read_bytes()))
    idf = load_idf(source)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type='vrf_mm', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    run_period = idf.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 1, 1
    run_period.End_Month, run_period.End_Day_of_Month = 1, days
    folder = tmp_path / 'run'
    folder.mkdir()
    path = folder / 'TestModel[CS_INT EN16798[CA_2[CM_3[HM_2.idf'
    idf.saveas(str(path))
    (folder / 'Seville.epw').write_bytes(SAMPLE_EPW.read_bytes())
    source.unlink()
    return folder, path


@needs_idd
@needs_energyplus
def test_the_estimate_is_close_to_the_files_of_a_simulation(tmp_path, monkeypatch, capsys):
    folder, path = _output_idf(tmp_path)
    monkeypatch.chdir(folder)

    estimate = run_results_size.estimate_results_size(only_accim_idfs=True, verbose=False)
    measured = run_results_size.estimate_results_size(simulate=True, only_accim_idfs=True)

    # The simulation ran in a temporary folder
    assert sorted(os.listdir(folder)) == ['Seville.epw', path.name]
    assert measured['source'].tolist() == ['simulation'] and estimate['source'].tolist() == ['estimate']
    for column in ('eso_mb', 'csv_mb', 'kept_mb'):
        assert estimate[column].iloc[0] == pytest.approx(measured[column].iloc[0], rel=0.15), column
    # With 31 days, the other files (about 0.5 MB, estimated more roughly) are a larger part of the results
    assert estimate['simulation_mb'].iloc[0] == pytest.approx(measured['simulation_mb'].iloc[0], rel=0.3)
    assert estimate['csv_memory_mb'].iloc[0] == measured['csv_memory_mb'].iloc[0]
    assert measured['total_mb'].iloc[0] == measured['simulation_mb'].iloc[0]
    assert 'measured in a simulation of one IDF of each group' in capsys.readouterr().out


@needs_idd
def test_addaccis_prints_the_estimated_size_before_writing_the_output_idfs(tmp_path, monkeypatch, capsys):
    from accim.sim.accis import AddAccis

    (tmp_path / 'TestModel.idf').write_bytes(lzma.decompress((INPUTS / 'vrf2zones.idf.xz').read_bytes()))
    monkeypatch.chdir(tmp_path)
    printed_before_asking = []

    def answer(question):
        printed_before_asking.append(capsys.readouterr().out)
        return 'n'

    monkeypatch.setattr(builtins, 'input', answer)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        addaccis = AddAccis(idfs=['TestModel.idf'], script_type='vrf_mm',
                            supply_air_temp_input_method='temperature difference', output_type='standard',
                            output_frequencies=['hourly'], keep_existing_outputs=False, make_outputs_dataframe=False,
                            setpoint_type='temperature', comfort_standard=[1], category=[2], comfort_mode=[2, 3],
                            hvac_mode=[2], ventilation_control=[0], verbose=False)

    # The estimate, before the question, so that other outputs can be chosen; no output IDFs were written
    assert len(printed_before_asking) == 1
    assert 'The estimated size of the results of each simulation of the output IDFs' in printed_before_asking[0]
    assert 'TestModel (2 output IDFs): 30.2 MB' in printed_before_asking[0]
    assert sorted(os.listdir(tmp_path)) == ['TestModel.idf']
    row = addaccis.results_size.iloc[0]
    assert (row['idf'], row['output_idfs']) == ('TestModel', 2)
    assert row['simulation_mb'] == pytest.approx(30.2, abs=0.1)
    assert row['total_mb'] == pytest.approx(2 * row['simulation_mb'])
