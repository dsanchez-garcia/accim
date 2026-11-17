"""Tests for the rows of the run period of the outputs of the simulations (accim.utils.outputs): read_csv_outputs and
read_eso_using_readvarseso with ``only_run_period=True``, the default, which verify_accim_simulation and the
parametric module use.

Until accim 1.2.0 (an entry of TODO.md of 2026-11-09, found with B1), read_csv_outputs told the sizing periods apart
from the run period by a jump back of the month of their dates, and cut a file without such a jump and with more than
8800 rows to its last 8760 rows (those of an hourly year). Measured with EnergyPlus 25.1 on 2026-11-17: the outputs at
timestep frequency of a run period of more than about 61 days lost their first days, and the sizing period of 15
January of the sample model was taken as the first day of a run period that begins on 1 January. The environments are
now told apart by the dates and times of the rows, which follow each other within an environment, and by the first
date and time of the run period of the ESO file.
"""
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import find_energyplus
from accim.utils.outputs import (_csv_environment_starts, _eso_run_period_start, read_csv_outputs,
                                 read_eso_using_readvarseso)

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
TEMPERATURE = 'Environment:Site Outdoor Air Drybulb Temperature [C]'
_MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _days(month, day, count, leap=False):
    """The (month, day) of ``count`` days from a date."""
    lengths = list(_MONTH_DAYS)
    if leap:
        lengths[1] = 29
    days = []
    for _ in range(count):
        days.append((month, day))
        day += 1
        if day > lengths[month - 1]:
            month, day = month % 12 + 1, 1
    return days


def _stamps(days, steps_per_hour=1):
    """The dates and times of the rows of the timesteps of some days, as ReadVarsESO writes them (the end of each
    timestep: ' 01/01  00:10:00' to ' 01/01  24:00:00')."""
    minutes = 60 // steps_per_hour
    return [f' {month:02d}/{day:02d}  {step * minutes // 60:02d}:{step * minutes % 60:02d}:00'
            for month, day in days for step in range(1, 24 * steps_per_hour + 1)]


#: The sizing periods of the sample model, in their order: three summer design days and a winter one
DESIGN_DAYS = [(7, 15), (8, 15), (9, 15), (1, 15)]


def test_the_environments_of_the_rows_of_the_outputs():
    # The sizing periods of the sample model and a run period from 1 January: five environments
    stamps = _stamps(DESIGN_DAYS + _days(1, 1, 73))
    assert _csv_environment_starts(stamps) == [0, 24, 48, 72, 96]
    # With timesteps of 10 minutes
    assert _csv_environment_starts(_stamps(DESIGN_DAYS + _days(1, 1, 3), 6)) == [0, 144, 288, 432, 576]
    # A run period across the end of the year, and February with and without 29 February: one environment
    for days in (_days(12, 30, 4), _days(2, 27, 3), _days(2, 27, 4, leap=True)):
        assert _csv_environment_starts(_stamps(days)) == [0]
    assert [stamp[1:6] for stamp in _stamps(_days(2, 27, 4, leap=True))[::24]] == [
        '02/27', '02/28', '02/29', '03/01']
    # A missing day, a new environment on the day on which the previous one ends, and one that does not begin with
    # the first hour of its day
    assert _csv_environment_starts(_stamps([(2, 1), (2, 3)])) == [0, 24]
    assert _csv_environment_starts(_stamps([(7, 15), (7, 15)])) == [0, 24]
    assert _csv_environment_starts(_stamps([(1, 1)]) + _stamps([(1, 2)])[1:]) == [0, 24]
    # The rows without a date and time are skipped, and the rows of the same date and time follow each other
    stamps = ['', 'January', ' 01/01'] + _stamps([(7, 15)]) + [' 07/15  24:00:00'] + _stamps([(1, 1)])
    assert _csv_environment_starts(stamps) == [3, 28]
    assert _csv_environment_starts([]) == [] and _csv_environment_starts(['', 'simdays=1']) == []


def _csv(path, stamps, hourly=True):
    """A CSV file of ReadVarsESO with the outdoor air temperature of each row at timestep frequency (its position),
    and, in the rows that end an hour, at hourly frequency (its position plus 0.5)."""
    values = np.arange(len(stamps), dtype=float)
    columns = {'Date/Time': stamps, f'{TEMPERATURE}(TimeStep)': values}
    if hourly:
        columns[f'{TEMPERATURE}(Hourly)'] = np.where([stamp.endswith(':00:00') for stamp in stamps], values + 0.5,
                                                     np.nan)
    pd.DataFrame(columns).to_csv(path, index=False)
    return str(path)


def test_read_csv_outputs_keeps_the_whole_run_period(tmp_path):
    # 74 days at timestep frequency without sizing periods (10656 rows): before accim 1.2.0, the last 8760, from 14
    # January (as in the finding of B1)
    stamps = _stamps(_days(1, 1, 74), 6)
    data = read_csv_outputs(_csv(tmp_path / 'long.csv', stamps))['data']
    assert len(data['Timestep']) == 74 * 144 and data['Timestep'].index[0] == ' 01/01  00:10:00'
    assert len(data['Hourly']) == 74 * 24 and data['Hourly'].index[0] == ' 01/01  01:00:00'
    np.testing.assert_array_equal(data['Timestep'].iloc[:, 0].to_numpy(), np.arange(74 * 144))

    # With the sizing periods of the sample model before a run period from 1 January: before accim 1.2.0, the run
    # period began with the winter design day, 15 January (the month does not jump back)
    sizing = len(DESIGN_DAYS) * 144
    stamps = _stamps(DESIGN_DAYS + _days(1, 1, 74), 6)
    path = _csv(tmp_path / 'sizing.csv', stamps)
    data = read_csv_outputs(path)['data']
    assert len(data['Timestep']) == 74 * 144 and data['Timestep'].index[0] == ' 01/01  00:10:00'
    assert data['Timestep'].iloc[0, 0] == sizing and data['Hourly'].iloc[0, 0] == sizing + 5.5
    assert len(read_csv_outputs(path, only_run_period=False)['data']['Timestep']) == sizing + 74 * 144

    # A sizing period that ends the day before the run period begins (15 January, and the run period from 16
    # January) is not told apart from it by the dates: the first date and time of the run period (that of the ESO
    # file, in read_eso_using_readvarseso) tells it
    stamps = _stamps(DESIGN_DAYS + _days(1, 16, 3), 6)
    path = _csv(tmp_path / 'next_day.csv', stamps)
    assert read_csv_outputs(path)['data']['Timestep'].index[0] == ' 01/15  00:10:00'
    data = read_csv_outputs(path, run_period_start=' 01/16  00:10:00')['data']
    assert len(data['Timestep']) == 3 * 144 and data['Timestep'].index[0] == ' 01/16  00:10:00'
    # A first date and time that is not there changes nothing
    assert len(read_csv_outputs(path, run_period_start=' 02/01  00:10:00')['data']['Timestep']) == 4 * 144


def test_the_first_date_and_time_of_the_run_period_in_the_eso_file(tmp_path):
    dictionary = [
        'Program Version,EnergyPlus, Version 25.1.0-1c11a3d85f, YMD=2026.11.17 17:24',
        '1,5,Environment Title[],Latitude[deg],Longitude[deg],Time Zone[],Elevation[m]',
        '2,8,Day of Simulation[],Month[],Day of Month[],DST Indicator[1=yes 0=no],Hour[],StartMinute[],EndMinute[],'
        'DayType',
        '7,1,Environment,Site Outdoor Air Drybulb Temperature [C] !TimeStep',
        'End of Data Dictionary',
    ]
    records = [
        '1,SUMMER DESIGN DAY IN UNTITLED (01-01:31-12) JUL,  37.42,  -5.90,   1.00,  31.00',
        '2,1, 7,15, 1, 1, 0.00,10.00,SummerDesignDay', '7,23.675',
        '1,UNTITLED (01-01:31-12),  37.42,  -5.90,   1.00,  31.00',
        '2,1, 1,16, 0, 1, 0.00,10.00,Thursday', '7,8.43', '2,1, 1,16, 0, 1,10.00,20.00,Thursday', '7,8.97',
        'End of Data',
    ]
    path = tmp_path / 'run.eso'
    path.write_text('\n'.join(dictionary + records) + '\n', encoding='utf-8')
    assert _eso_run_period_start(str(path)) == ' 01/16  00:10:00'
    # An hourly first record: the hour that ends at the minute 60
    path.write_text('\n'.join(dictionary + [records[3], '2,1, 1, 1, 0, 1, 0.00,60.00,Sunday', '7,8.4']) + '\n',
                    encoding='utf-8')
    assert _eso_run_period_start(str(path)) == ' 01/01  01:00:00'
    # Without environments (the dictionary has the lines of the records 1 and 2 too)
    path.write_text('\n'.join(dictionary + ['End of Data']) + '\n', encoding='utf-8')
    assert _eso_run_period_start(str(path)) is None


def _energyplus():
    return find_energyplus('25.1', required=False)


@pytest.mark.skipif(_energyplus() is None or not SAMPLE_IDF.exists() or not EPW.exists(),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_the_run_period_of_a_simulation_with_its_sizing_periods(tmp_path):
    from accim.sim.accis import load_idf

    # The sample model with its four sizing periods in the outputs (15 July, August and September, and 15 January),
    # and a run period of 75 days from 16 January, the day after the last one; the outdoor air temperature at each
    # frequency (ReadVarsESO writes the days, months and run periods in the row of their last timestep)
    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    model = load_idf(tmp_path / 'model.idf')
    model.idfobjects['SimulationControl'][0].Run_Simulation_for_Sizing_Periods = 'Yes'
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month, run_period.End_Month, run_period.End_Day_of_Month = (
        1, 16, 3, 31)
    for output in list(model.idfobjects['Output:Variable']):
        model.removeidfobject(output)
    for frequency in ('Timestep', 'Hourly', 'Daily', 'Monthly', 'RunPeriod'):
        model.newidfobject('Output:Variable', Key_Value='*', Variable_Name='Site Outdoor Air Drybulb Temperature',
                           Reporting_Frequency=frequency)
    assert [(day.Month, day.Day_of_Month) for day in model.idfobjects['SizingPeriod:DesignDay']] == DESIGN_DAYS
    model.save()
    result = subprocess.run([str(_energyplus() / 'energyplus.exe'), '-d', str(tmp_path / 'out'), '-p', 'run', '-s',
                             'C', '-w', str(EPW), str(tmp_path / 'model.idf')], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    eso = tmp_path / 'out' / 'run.eso'

    data = read_eso_using_readvarseso(eso_file_path=str(eso), eplus_install_dir=str(_energyplus()),
                                      cleanup=False)['data']
    rows = {frequency: len(frame) for frequency, frame in data.items()}
    assert rows == {'Timestep': 75 * 144, 'Hourly': 75 * 24, 'Daily': 75, 'Monthly': 3, 'Runperiod': 1}
    assert [data['Timestep'].index[i] for i in (0, -1)] == [' 01/16  00:10:00', ' 03/31  24:00:00']
    assert list(data['Monthly'].index) == [' 01/31  24:00:00', ' 02/28  24:00:00', ' 03/31  24:00:00']
    # The values of the rows of the run period, the last ones of the CSV file
    csv = pd.read_csv(tmp_path / 'out' / 'run.csv')
    assert len(csv) == (len(DESIGN_DAYS) + 75) * 144
    np.testing.assert_array_equal(data['Timestep'].iloc[:, 0].to_numpy(),
                                  csv[f'{TEMPERATURE}(TimeStep)'].to_numpy()[-75 * 144:])
    # The dates alone take the winter design day, the day before, for the first day of the run period; the first
    # date and time of the ESO file tells them apart
    assert _eso_run_period_start(str(eso)) == ' 01/16  00:10:00'
    assert len(read_csv_outputs(str(tmp_path / 'out' / 'run.csv'))['data']['Timestep']) == 76 * 144
    all_rows = read_eso_using_readvarseso(eso_file_path=str(eso), eplus_install_dir=str(_energyplus()),
                                          only_run_period=False)['data']
    assert len(all_rows['Timestep']) == (len(DESIGN_DAYS) + 75) * 144
