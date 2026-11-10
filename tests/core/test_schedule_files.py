"""Tests for the Schedule:File objects of hourly values that accim writes (:mod:`accim.sim.schedule_files`, tasks H2
and H6 of the review of accim 1.2.0): the CSV file (a header row and one column, the values as repr writes them), in the
folder of the model, and the fields of the Schedule:File object (Input Output Reference 25.2, 1.8.13)."""
import shutil
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

from accim.energyplus import default_energyplus_folder
from accim.sim import schedule_files as sf

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')


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


def test_without_the_field_of_daylight_savings():
    # The IDDs of EnergyPlus 9.4 and 9.6 have no field Adjust Schedule for Daylight Savings

    class Schedule(SimpleNamespace):
        fieldnames = ['key', 'Name', 'Schedule_Type_Limits_Name', 'File_Name', 'Column_Number', 'Rows_to_Skip_at_Top',
                      'Number_of_Hours_of_Data', 'Column_Separator', 'Interpolate_to_Timestep', 'Minutes_per_Item']

    class Model:
        def __init__(self):
            self.objects = {}

        def getobject(self, key, name):
            return self.objects.get((key.upper(), name.upper()))

        def newidfobject(self, key, **fields):
            obj = Schedule(**fields)
            self.objects[(key.upper(), fields['Name'].upper())] = obj
            return obj

    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        model = Model()
        sf.write_schedule_file(model, 'S', [0.0] * 8760, 's.csv', folder=folder)
        schedule = model.getobject('Schedule:File', 'S')
        assert not hasattr(schedule, 'Adjust_Schedule_for_Daylight_Savings')
        assert schedule.Number_of_Hours_of_Data == 8760 and schedule.Minutes_per_Item == 60
