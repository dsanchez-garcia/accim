"""Tests for the Schedule:File objects of hourly values that accim writes (:mod:`accim.sim.schedule_files`, tasks H2
and H6 of the review of accim 1.2.0): the CSV file (a header row and one column, the values as repr writes them), in the
folder of the model, the fields of the Schedule:File object (Input Output Reference 25.2, 1.8.13), and the paths
relative to the folder of the model, with which a model can be moved with its files (run_ep, with both backends, gives
the copies of the models it simulates the absolute paths)."""
import os
import platform
import re
import shutil
import subprocess
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim import schedule_files as sf

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
needs_energyplus = pytest.mark.skipif(
    find_energyplus('25.1', required=False) is None or not (SAMPLE_IDF.exists() and EPW.exists()),
    reason='needs EnergyPlus 25.1 and the sample files of the repository')


def _model(folder):
    from accim.sim.accis import load_idf

    shutil.copy(SAMPLE_IDF, folder / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return load_idf(folder / 'model.idf')


@needs_idd
def test_write_schedule_file(tmp_path):
    idf = _model(tmp_path)
    values = [float(hour % 24) + 0.1 for hour in range(8760)]
    path = sf.write_schedule_file(idf, 'My Schedule', values, 'my_schedule.csv')
    # In the folder of the model, with the absolute path in the object
    assert path == tmp_path / 'my_schedule.csv' and path.is_file()
    lines = path.read_text(encoding='utf-8').splitlines()
    assert lines[0] == 'My Schedule' and [float(line) for line in lines[1:]] == values
    assert lines[1:3] == ['0.1', '1.1']
    schedule = idf.getobject('Schedule:File', 'My Schedule')
    assert (schedule.Schedule_Type_Limits_Name, schedule.File_Name, schedule.Column_Number,
            schedule.Rows_to_Skip_at_Top, schedule.Number_of_Hours_of_Data, schedule.Column_Separator,
            schedule.Interpolate_to_Timestep, schedule.Minutes_per_Item,
            schedule.Adjust_Schedule_for_Daylight_Savings) == (
        sf.SCHEDULE_TYPE_LIMITS, str(path), 1, 1, 8760, 'Comma', 'No', 60, 'No')
    assert sf.schedule_file_path(idf, 'My Schedule') == str(path)
    # The same values: the file is not written again; other values: it is, and the object is updated, once
    stamp = path.stat().st_mtime_ns
    sf.write_schedule_file(idf, 'My Schedule', values, 'my_schedule.csv')
    assert path.stat().st_mtime_ns == stamp
    leap = values + values[:24]
    sf.write_schedule_file(idf, 'My Schedule', leap, 'my_schedule.csv', folder=tmp_path / 'other')
    assert len(idf.idfobjects['Schedule:File']) == 1
    assert schedule.Number_of_Hours_of_Data == 8784 and schedule.File_Name == str(tmp_path / 'other' /
                                                                                  'my_schedule.csv')
    with pytest.raises(ValueError, match='needs 8760 or 8784 hourly values'):
        sf.write_schedule_file(idf, 'Short', values[:-1], 'short.csv')
    assert idf.getobject('Schedule:File', 'Short') is None and not (tmp_path / 'short.csv').exists()
    # The CSV file stays when the object is removed
    sf.remove_schedule_file(idf, 'My Schedule')
    assert idf.getobject('Schedule:File', 'My Schedule') is None and sf.schedule_file_path(idf, 'My Schedule') is None
    assert (tmp_path / 'other' / 'my_schedule.csv').is_file()
    sf.remove_schedule_file(idf, 'My Schedule')


@needs_idd
def test_the_schedule_type_limits_are_added_if_missing(tmp_path):
    idf = _model(tmp_path)
    idf.removeidfobject(idf.getobject('ScheduleTypeLimits', sf.SCHEDULE_TYPE_LIMITS))
    sf.write_schedule_file(idf, 'My Schedule', [1.0] * 8760, 'my_schedule.csv')
    limits = idf.getobject('ScheduleTypeLimits', sf.SCHEDULE_TYPE_LIMITS)
    assert limits is not None and str(limits.Lower_Limit_Value) == '' and str(limits.Upper_Limit_Value) == ''


def test_the_folder_of_a_model(tmp_path, monkeypatch):
    assert sf.model_folder(SimpleNamespace(idfname=str(tmp_path / 'a' / 'model.idf'))) == tmp_path / 'a'
    # A model in memory (as those of AddAccis), in the current folder
    monkeypatch.chdir(tmp_path)
    assert sf.model_folder(SimpleNamespace(idfname=None)) == tmp_path
    assert sf.model_folder(SimpleNamespace()) == tmp_path


def _same_file(path, other):
    return os.path.samefile(path, other)


@needs_idd
def test_the_relative_and_absolute_paths_of_the_schedule_files(tmp_path, monkeypatch):
    # Since accim 1.2.0 (the pending option of decision 7 of the review of accim 1.2.0): the paths relative to the
    # folder of the model of the files in that folder or in its subfolders, with '/'; the others keep their paths
    (tmp_path / 'm').mkdir()
    idf = _model(tmp_path / 'm')
    values = [1.0] * 8760
    inside = sf.write_schedule_file(idf, 'Inside', values, 'inside.csv')
    below = sf.write_schedule_file(idf, 'Below', values, 'below.csv', folder=tmp_path / 'm' / 'schedules')
    elsewhere = sf.write_schedule_file(idf, 'Elsewhere', values, 'elsewhere.csv', folder=tmp_path / 'other')
    idf.newidfobject('Schedule:File', Name='Given', File_Name='given.csv')
    with pytest.warns(UserWarning, match=r'The files of the Schedule:File objects Elsewhere \(.*elsewhere\.csv\) are '
                                         r'not in the folder of the model \(.*\) or in its subfolders: the objects '
                                         r'keep their absolute paths'):
        changed = sf.relative_schedule_files(idf)
    assert changed == {'Inside': 'inside.csv', 'Below': 'schedules/below.csv'}
    paths = {str(s.Name): str(s.File_Name) for s in idf.idfobjects['Schedule:File']}
    assert paths == {'Inside': 'inside.csv', 'Below': 'schedules/below.csv', 'Elsewhere': str(elsewhere),
                     'Given': 'given.csv'}
    assert sf.schedule_file_path(idf, 'Below') == 'schedules/below.csv'
    # Relative to another folder: that of the model is a subfolder of it
    with pytest.warns(UserWarning, match='Elsewhere'):
        assert sf.relative_schedule_files(idf) == {}
    # Back: the current folder has not the files, the folder of the model has them; the others do not change
    monkeypatch.chdir(tmp_path)
    changed = sf.absolute_schedule_files(idf)
    assert sorted(changed) == ['Below', 'Inside']
    assert _same_file(changed['Inside'], inside) and _same_file(changed['Below'], below)
    assert os.path.isabs(changed['Inside']) and os.path.isabs(changed['Below'])
    assert idf.getobject('Schedule:File', 'Given').File_Name == 'given.csv'
    assert idf.getobject('Schedule:File', 'Elsewhere').File_Name == str(elsewhere)
    assert sf.absolute_schedule_files(idf) == {}
    # The current folder first, as EnergyPlus: a file with the same path there is taken instead
    with pytest.warns(UserWarning, match='Elsewhere'):
        sf.relative_schedule_files(idf)
    (tmp_path / 'cwd').mkdir()
    shutil.copy(inside, tmp_path / 'cwd' / 'inside.csv')
    monkeypatch.chdir(tmp_path / 'cwd')
    changed = sf.absolute_schedule_files(idf)
    assert _same_file(changed['Inside'], tmp_path / 'cwd' / 'inside.csv') and _same_file(changed['Below'], below)
    # That file is not in the folder of the model: its path stays absolute
    with pytest.warns(UserWarning, match=r'Schedule:File objects Inside \(.*cwd.inside\.csv\), Elsewhere'):
        assert sf.relative_schedule_files(idf) == {'Below': 'schedules/below.csv'}
    # The folders given, in their order
    idf.getobject('Schedule:File', 'Inside').File_Name = 'inside.csv'
    changed = sf.absolute_schedule_files(idf, folders=[tmp_path / 'm', tmp_path / 'cwd'])
    assert _same_file(changed['Inside'], inside) and _same_file(changed['Below'], below)
    # A path written on Windows, with '\' between its folders
    idf.getobject('Schedule:File', 'Below').File_Name = 'schedules\\below.csv'
    assert _same_file(sf.absolute_schedule_files(idf, folders=[tmp_path / 'm'])['Below'], below)


@needs_idd
def test_the_paths_of_the_schedule_files_of_an_idf_file(tmp_path):
    # The path of an IDF file: it is read, and saved again only if a path changes
    (tmp_path / 'm').mkdir()
    idf = _model(tmp_path / 'm')
    path = sf.write_schedule_file(idf, 'Inside', [1.0] * 8760, 'inside.csv')
    idf.save()
    model = tmp_path / 'm' / 'model.idf'
    assert sf.relative_schedule_files(model) == {'Inside': 'inside.csv'}
    assert 'inside.csv,' in model.read_text(encoding='latin-1') and str(path) not in model.read_text(encoding='latin-1')
    stamp = model.stat().st_mtime_ns
    assert sf.relative_schedule_files(str(model)) == {}
    assert model.stat().st_mtime_ns == stamp
    changed = sf.absolute_schedule_files(model)
    assert _same_file(changed['Inside'], path) and changed['Inside'] in model.read_text(encoding='latin-1')


@pytest.mark.skipif(os.name != 'nt', reason='drives are those of Windows')
def test_a_file_on_another_drive_is_not_in_the_folder(tmp_path):
    drive = 'Q:' if not str(tmp_path).upper().startswith('Q:') else 'R:'
    assert sf._relative_path(f'{drive}\\schedules\\a.csv', tmp_path) is None
    assert sf._relative_path(str(tmp_path / 'a.csv'), tmp_path) == 'a.csv'
    assert sf._relative_path(str(tmp_path), tmp_path) is None
    assert sf._relative_path(str(tmp_path.parent / 'a.csv'), tmp_path) is None


def _probe_model(folder):
    """The sample model in ``folder``, simulated on 1 and 2 January, with the Schedule:File objects Probe (its file in
    the folder) and Probe 2 (in the subfolder schedules) of the hour of the year (0 to 8759, and plus 0.5), their
    hourly outputs Schedule Value, and their paths relative to the folder."""
    idf = _model(folder)
    run_period = idf.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 1, 1
    run_period.End_Month, run_period.End_Day_of_Month = 1, 2
    values = [float(hour) for hour in range(8760)]
    sf.write_schedule_file(idf, 'Probe', values, 'probe.csv')
    sf.write_schedule_file(idf, 'Probe 2', [value + 0.5 for value in values], 'probe.csv', folder=folder / 'schedules')
    for name in ('Probe', 'Probe 2'):
        idf.newidfobject('Output:Variable', Key_Value=name, Variable_Name='Schedule Value',
                         Reporting_Frequency='Hourly')
    assert sf.relative_schedule_files(idf) == {'Probe': 'probe.csv', 'Probe 2': 'schedules/probe.csv'}
    idf.save()


def _moved_probe_model(tmp_path):
    """The folder of the probe model, moved with its files to another folder."""
    (tmp_path / 'A').mkdir()
    _probe_model(tmp_path / 'A')
    shutil.copytree(tmp_path / 'A', tmp_path / 'B')
    shutil.rmtree(tmp_path / 'A')
    return tmp_path / 'B'


def _probe_outputs(csv):
    """The hourly values of Probe and Probe 2 in a CSV file of the outputs of EnergyPlus."""
    import pandas as pd

    results = pd.read_csv(csv)
    return [results[[c for c in results.columns if c.upper().startswith(f'{name}:SCHEDULE VALUE')][0]].tolist()
            for name in ('PROBE', 'PROBE 2')]


#: The values of Probe and Probe 2 on 1 and 2 January
_HOURS = [[float(hour) for hour in range(48)], [hour + 0.5 for hour in range(48)]]


@needs_energyplus
def test_energyplus_finds_the_files_of_relative_paths_next_to_the_idf_file(tmp_path):
    # Measured on 2026-11-18 with EnergyPlus 25.1: a model moved with its files finds them from another current folder
    # (the folder of the IDF file), also those of '/' between folders on Windows, and a file with the same path in the
    # current folder is read instead (the current folder first)
    folder = _moved_probe_model(tmp_path)
    program = find_energyplus('25.1') / ('energyplus.exe' if platform.system() == 'Windows' else 'energyplus')
    (tmp_path / 'cwd').mkdir()
    for run, values in (('first', _HOURS), ('second', [[value + 1000 for value in _HOURS[0]], _HOURS[1]])):
        result = subprocess.run([str(program), '-d', str(tmp_path / run), '-r', '-w', str(EPW),
                                 str(folder / 'model.idf')], cwd=tmp_path / 'cwd', capture_output=True, text=True)
        assert result.returncode == 0, result.stdout[-2000:]
        assert _probe_outputs(tmp_path / run / 'eplusout.csv') == values
        (tmp_path / 'cwd' / 'probe.csv').write_text(
            'Probe\n' + '\n'.join(repr(float(hour) + 1000) for hour in range(8760)) + '\n', encoding='utf-8')


@needs_energyplus
@pytest.mark.parametrize('backend', ['ems', 'api'])
def test_run_ep_simulates_a_model_moved_with_its_schedule_files(tmp_path, monkeypatch, backend):
    # Both backends simulate a copy of the model in other folders (eppy in a temporary folder, with the model in
    # multi_runs; the API in a temporary folder): the copy gets the absolute paths of the files (since accim 1.2.0)
    from eppy.runner.run_functions import EnergyPlusRunError

    from accim.run import run_ep

    folder = _moved_probe_model(tmp_path)
    shutil.copy(EPW, folder / EPW.name)
    monkeypatch.chdir(folder)
    text = (folder / 'model.idf').read_text(encoding='latin-1')
    run_ep(only_accim_idfs=False, confirm=True, energyplus_version='auto', backend=backend, processes=0)
    outputs = folder / 'model[Seville_Present.csv'
    assert _probe_outputs(outputs) == _HOURS
    # The IDF file keeps its relative paths
    assert (folder / 'model.idf').read_text(encoding='latin-1') == text
    # Without the absolute paths in the copy (as before accim 1.2.0), EnergyPlus does not find the files, even in the
    # folder of the model
    outputs.unlink()
    monkeypatch.setattr(sf, 'absolute_schedule_files', lambda idf, folders=None: {})
    not_found = r'Schedule:File="PROBE", File Name: "probe\.csv" not found'
    if backend == 'ems':
        with pytest.raises(EnergyPlusRunError, match=not_found):
            run_ep(only_accim_idfs=False, confirm=True, energyplus_version='auto', backend=backend, processes=0)
    else:
        with pytest.warns(RuntimeWarning, match='1 of 1 simulations failed: model.idf'):
            [result] = run_ep(only_accim_idfs=False, confirm=True, energyplus_version='auto', backend=backend,
                              processes=0)
        assert not result.success
        assert re.search(not_found, Path(result.err_file).read_text(errors='replace'))
    assert not outputs.exists()


def _weather_file(path, daylight_saving):
    """A weather file (its header only) with the daylight saving period given ('4/1', '10/31'), or none."""
    start, end = daylight_saving or ('0', '0')
    lines = ['LOCATION,X', 'DESIGN CONDITIONS,0', 'TYPICAL/EXTREME PERIODS,0', 'GROUND TEMPERATURES,0',
             f'HOLIDAYS/DAYLIGHT SAVINGS,No,{start},{end},0', 'COMMENTS 1,', 'COMMENTS 2,',
             'DATA PERIODS,1,1,Data,Sunday, 1/ 1,12/31']
    path.write_text('\n'.join(lines) + '\n', encoding='latin-1')
    return path


def test_without_the_field_of_daylight_savings(tmp_path):
    # The IDDs of EnergyPlus 9.4 and 9.6 have no field Adjust Schedule for Daylight Savings: with daylight saving time,
    # EnergyPlus shifts the values of the Schedule:File objects by one hour while it is active, and accim warns

    class Schedule(SimpleNamespace):
        fieldnames = ['key', 'Name', 'Schedule_Type_Limits_Name', 'File_Name', 'Column_Number', 'Rows_to_Skip_at_Top',
                      'Number_of_Hours_of_Data', 'Column_Separator', 'Interpolate_to_Timestep', 'Minutes_per_Item']

    class Model:
        def __init__(self, idfobjects):
            self.objects = {}
            self.idfobjects = idfobjects

        def getobject(self, key, name):
            return self.objects.get((key.upper(), name.upper()))

        def newidfobject(self, key, **fields):
            obj = Schedule(**fields)
            self.objects[(key.upper(), fields['Name'].upper())] = obj
            return obj

    model = Model({'RunPeriod': [SimpleNamespace(Use_Weather_File_Daylight_Saving_Period='No')]})
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        sf.write_schedule_file(model, 'S', [0.0] * 8760, 's.csv', folder=tmp_path)
    schedule = model.getobject('Schedule:File', 'S')
    assert not hasattr(schedule, 'Adjust_Schedule_for_Daylight_Savings')
    assert schedule.Number_of_Hours_of_Data == 8760 and schedule.Minutes_per_Item == 60
    # With a RunPeriodControl:DaylightSavingTime object
    model = Model({'RunPeriodControl:DaylightSavingTime': [SimpleNamespace(Start_Date='Last Sunday in March',
                                                                            End_Date='Last Sunday in October')]})
    with pytest.warns(UserWarning, match=r'The Schedule:File object S reads its values from s\.csv, and the IDD of the '
                                         r'model has not the field Adjust Schedule for Daylight Savings \(EnergyPlus '
                                         r'9\.4 and 9\.6\): while the daylight saving time of the model is active '
                                         r'\(RunPeriodControl:DaylightSavingTime, from Last Sunday in March to Last '
                                         r'Sunday in October\), EnergyPlus shifts the values'):
        sf.write_schedule_file(model, 'S', [0.0] * 8760, 's.csv', folder=tmp_path)
    # With the daylight saving period of the weather file, which a RunPeriod uses (Yes, the default)
    epw = _weather_file(tmp_path / 'dst.epw', ('4/1', '10/31'))
    for value in ('Yes', ''):
        model = Model({'RunPeriod': [SimpleNamespace(Use_Weather_File_Daylight_Saving_Period=value)]})
        with pytest.warns(UserWarning, match=r'\(that of the weather file dst\.epw, from 4/1 to 10/31\)'):
            sf.write_schedule_file(model, 'S', [0.0] * 8760, 's.csv', folder=tmp_path, epw=epw)
    # Without it, or without the weather file: no warning
    model = Model({'RunPeriod': [SimpleNamespace(Use_Weather_File_Daylight_Saving_Period='Yes')]})
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        sf.write_schedule_file(model, 'S', [0.0] * 8760, 's.csv', folder=tmp_path,
                               epw=_weather_file(tmp_path / 'none.epw', None))
        sf.write_schedule_file(model, 'S', [0.0] * 8760, 's.csv', folder=tmp_path)


@needs_idd
def test_the_daylight_saving_period_of_a_model(tmp_path):
    # The sample model has a RunPeriodControl:DaylightSavingTime object, and its RunPeriod does not use the daylight
    # saving period of the weather file
    idf = _model(tmp_path)
    assert sf.daylight_saving_period(idf) == ('RunPeriodControl:DaylightSavingTime, from Last Sunday in March to '
                                              'Last Sunday in October')
    idf.removeidfobject(idf.idfobjects['RunPeriodControl:DaylightSavingTime'][0])
    epw = _weather_file(tmp_path / 'dst.epw', ('4/1', '10/31'))
    assert sf.daylight_saving_period(idf, epw) is None
    idf.idfobjects['RunPeriod'][0].Use_Weather_File_Daylight_Saving_Period = 'Yes'
    assert sf.daylight_saving_period(idf, epw) == 'that of the weather file dst.epw, from 4/1 to 10/31'
    assert sf.daylight_saving_period(idf, _weather_file(tmp_path / 'none.epw', None)) is None
    assert sf.daylight_saving_period(idf, REPO / 'Seville_Present.epw') is None
    assert sf.daylight_saving_period(idf) is None


@needs_idd
def test_accim_gives_the_weather_file_to_its_schedule_files(tmp_path, monkeypatch):
    # The warning of the daylight saving time reads the daylight saving period of the weather file: modify_accis (T0 of
    # 'te_ref_nl' with epw, as AddAccis: the next test) and set_pmv_input_parameters (a function of the clothing
    # insulation) give it to write_schedule_file
    import numpy as np

    from accim.sim import apmv
    from accim.sim.accis import add_accis_to_idf, modify_accis

    epw = REPO / 'Seville_Present.epw'
    given = []
    original = sf.write_schedule_file

    def recording(*args, **kwargs):
        given.append(kwargs.get('epw'))
        return original(*args, **kwargs)

    monkeypatch.setattr(sf, 'write_schedule_file', recording)
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation=lambda rmot: np.clip(1.2 - 0.03 * rmot, 0.4, 1.0),
                                  epw=epw, verbose=False)
    assert given and all(str(value) == str(epw) for value in given)
    given.clear()
    (tmp_path / 'accis').mkdir()
    idf = _model(tmp_path / 'accis')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
        modify_accis(idf, comfort_standard=99, comfort_mode=3, custom_outdoor_metric='te_ref_nl', epw=str(epw))
    assert given == [str(epw)]


#: The Schedule:File object of T0 of 'te_ref_nl' of the custom model with the weather file, in the sample model of a
#: version of EnergyPlus, three days of July, with its daylight saving time (in a new process, since eppy sets one IDD
#: per process): the warnings of AddAccis about the daylight saving time, and the values of the schedule against the
#: CSV file, as JSON
_DAYLIGHT_SAVING_SCRIPT = """
import json, os, subprocess, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from accim.energyplus import find_energyplus
from accim.sim.accis import AddAccis, load_idf

folder, sample, epw, version = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
model = load_idf(sample)
run_period = model.idfobjects['RunPeriod'][0]
run_period.Begin_Month, run_period.Begin_Day_of_Month, run_period.End_Month, run_period.End_Day_of_Month = 7, 14, 7, 16
model.saveas(str(folder / 'TestModel.idf'))
os.chdir(folder)
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
             output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
             setpoint_type='temperature', comfort_standard=[99], category=[1], comfort_mode=[3], confirm=True,
             verbose=False, custom_outdoor_metric='te_ref_nl', epw=epw, custom_slope=0.33, custom_intercept=18.8,
             custom_cooling_offset=2, custom_heating_offset=-3, custom_cooling_upper_limit=30,
             custom_cooling_lower_limit=10, custom_heating_upper_limit=30, custom_heating_lower_limit=10)
[output_idf] = folder.glob('TestModel[[]*.idf')
idf = load_idf(output_idf)
[schedule] = idf.idfobjects['Schedule:File']
idf.newidfobject('Output:Variable', Key_Value=str(schedule.Name), Variable_Name='Schedule Value',
                 Reporting_Frequency='Hourly')
idf.saveas(str(folder / 'model.idf'))
result = subprocess.run([str(find_energyplus(version) / 'energyplus.exe'), '-d', str(folder / 'out'), '-r', '-x',
                         '-w', epw, str(folder / 'model.idf')], capture_output=True, text=True)
values = pd.read_csv(str(schedule.File_Name)).iloc[:, 0].to_numpy()
results = pd.read_csv(folder / 'out' / 'eplusout.csv')
[column] = [c for c in results.columns if str(schedule.Name).upper() in c.upper() and 'Schedule Value' in c]
found = results[column].to_numpy()
hours = 24 * 194 + np.arange(len(found))
print(json.dumps({'returncode': result.returncode, 'rows': len(found),
                  'warnings': [str(w.message) for w in caught if 'Daylight' in str(w.message)],
                  'same': bool(np.allclose(found, values[hours])), 'next': bool(np.allclose(found, values[hours + 1])),
                  'last_hours': found[23::24].tolist(), 'next_days': values[24 * 195::24][:3].tolist()}))
"""


@pytest.mark.parametrize('version', ['9.6', '25.1'])
def test_the_values_of_a_schedule_file_with_daylight_saving_time_in_energyplus(tmp_path, version):
    # Findings A22 and A26 of the self-audit of 2026-11-11, measured on 2026-11-18: with the IDD of EnergyPlus 9.6,
    # which has no field Adjust Schedule for Daylight Savings, AddAccis warns, and EnergyPlus 9.6 gives each hour of
    # July (with the daylight saving time of the sample model) the value of the next hour of the file, so T0 of the last
    # hour of each day is that of the next day; with EnergyPlus 25.1 (the field No), no warning and no shift (the test
    # of H2 in a week with daylight saving time)
    import json
    import os
    import subprocess
    import sys

    from accim.energyplus import find_energyplus

    suffix = {'9.6': 'V960', '25.1': 'V2510'}[version]
    sample = SAMPLE_IDF.with_name(f'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_{suffix}.idf')
    epw = REPO / 'Seville_Present.epw'
    if find_energyplus(version, required=False) is None or not (sample.exists() and epw.exists()):
        pytest.skip(f'needs EnergyPlus {version} and the sample files of the repository')
    pythonpath = [str(REPO)] + ([os.environ['PYTHONPATH']] if os.environ.get('PYTHONPATH') else [])
    result = subprocess.run([sys.executable, '-c', _DAYLIGHT_SAVING_SCRIPT, str(tmp_path), str(sample), str(epw),
                             version], capture_output=True, text=True, timeout=900,
                            env=dict(os.environ, PYTHONPATH=os.pathsep.join(pythonpath)))
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]
    found = json.loads(result.stdout.strip().splitlines()[-1])
    assert found['returncode'] == 0 and found['rows'] == 72
    if version == '9.6':
        assert len(found['warnings']) == 1 and ('while the daylight saving time of the model is active '
                                                '(RunPeriodControl:DaylightSavingTime, from Last Sunday in March to '
                                                'Last Sunday in October)') in found['warnings'][0]
        assert found['next'] and not found['same'] and found['last_hours'] == found['next_days']
    else:
        assert found['warnings'] == [] and found['same'] and not found['next']
