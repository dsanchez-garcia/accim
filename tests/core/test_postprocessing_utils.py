"""Tests for accim.data.postprocessing.utils: preview_table_cols and gen_csv_concatenated (and their names before
accim 1.0.0, preview_Table_cols and genCSVconcatenated).

The CSV files are the sample CSV files of the repository (accim/sample_files/sample_CSVs), or their first 48 hours.
Before (found on 2026-10-31), the concatenated CSV file of gen_csv_concatenated had the index of each part as one
more column, which Table read as an output ('UNNAMED: 0'), and its parts were joined in the order of os.listdir.
"""
import shutil
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import accim.sim.accis
from accim.data.postprocessing.main import Table
from accim.data.postprocessing.utils import gen_csv_concatenated, genCSVconcatenated, preview_table_cols, \
    preview_Table_cols

REPO = Path(__file__).resolve().parents[2]
SAMPLE_CSVS = sorted((REPO / 'accim' / 'sample_files' / 'sample_CSVs').glob('*.csv'))
HOURS = 48
CONCATENATED = 'gen[srcfreq-hourly[freq-runperiod[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv'
# Files in the folder of the results that are not results of a simulation
NOT_RESULTS = ['TestModelTable.csv', 'TestModelMeter.csv', 'TestModelZsz.csv', 'old[CSVconcatenated.csv',
               'old[Rows_not_corr_agg.csv', 'old[Rows_with_NaNs.csv']

pytestmark = [pytest.mark.filterwarnings('ignore::pandas.errors.PerformanceWarning'),
              pytest.mark.skipif(len(SAMPLE_CSVS) != 4, reason='needs the sample CSV files of the repository')]


class _Obj(SimpleNamespace):
    """An eppy-like object: its fields can be read as attributes or as items."""

    def __getitem__(self, field):
        return getattr(self, field)


class _ObjectClasses(dict):
    """The idfobjects of eppy: the class names do not depend on the case, and missing classes raise KeyError."""

    def __getitem__(self, key):
        return super().__getitem__(key.upper())


def _sample_building():
    """The zones, occupants and thermostats of TestModel.idf, in its order."""
    objects = _ObjectClasses({c: [] for c in ['ZONE', 'SPACE', 'SPACELIST', 'PEOPLE', 'ZONECONTROL:THERMOSTAT']})
    for zone in ['Block1:Zone2', 'Block1:Zone1']:
        objects['ZONE'].append(_Obj(key='ZONE', Name=zone))
        objects['PEOPLE'].append(
            _Obj(key='PEOPLE', Name=f'People {zone}', Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone))
        objects['ZONECONTROL:THERMOSTAT'].append(
            _Obj(key='ZONECONTROL:THERMOSTAT', Name=f'{zone} Thermostat', Zone_or_ZoneList_Name=zone))
    return SimpleNamespace(idfobjects=objects)


def _copy_results(folder, csvs=SAMPLE_CSVS, hours=HOURS):
    """Copy the first hours (all, if hours is None) of the sample CSV files to folder; return their names."""
    for csv in csvs:
        if hours is None:
            shutil.copy(csv, folder)
        else:
            lines = csv.read_bytes().splitlines(keepends=True)
            (folder / csv.name).write_bytes(b''.join(lines[:hours + 1]))
    return [csv.name for csv in csvs]


def _write_not_results(folder):
    for name in NOT_RESULTS:
        (folder / name).write_text('Date/Time,Something else\n 01/01  01:00:00,1\n', encoding='utf-8')


def _header(csv):
    return list(pd.read_csv(csv, nrows=0).columns)


def test_preview_table_cols_of_the_results_in_the_folder(tmp_path, monkeypatch):
    # One result, so that the first one does not depend on the order of the files
    _copy_results(tmp_path, SAMPLE_CSVS[-1:])
    _write_not_results(tmp_path)
    monkeypatch.chdir(tmp_path)

    columns = preview_table_cols()

    assert columns == _header(SAMPLE_CSVS[-1])
    assert columns[0] == 'Date/Time'
    assert len(columns) == 52


def test_preview_table_cols_of_the_datasets(tmp_path, monkeypatch):
    names = _copy_results(tmp_path)
    _write_not_results(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert preview_table_cols(datasets=NOT_RESULTS + names[1:]) == _header(SAMPLE_CSVS[1])


def test_gen_csv_concatenated_gives_the_table_of_all_the_results(tmp_path, monkeypatch):
    # The whole year, so that Table writes no file of rows not correctly aggregated
    names = _copy_results(tmp_path, hours=None)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(accim.sim.accis, 'load_idf', lambda idf_path: _sample_building())

    # Two parts: three results and one
    gen_csv_concatenated(datasets=names, source_frequency='hourly', frequency='runperiod',
                         concatenated_csv_name='gen', datasets_per_chunk=3)

    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(names + [CONCATENATED])
    arguments = dict(level=['building'], level_agg_func=['sum', 'mean'], level_excluded_zones=[],
                     split_epw_names=True, idf_path='TestModel.idf')
    concatenated = Table(source_concatenated_csv_filepath=CONCATENATED, **arguments)
    direct = Table(datasets=names, source_frequency='hourly', frequency='runperiod', frequency_agg_func='sum',
                   standard_outputs=True, **arguments)
    assert concatenated.frequency == 'runperiod'
    # One row per result, in the order of the datasets, and the columns of Table, in the same order (found on
    # 2026-10-31: the last column was moved to the beginning, and the parts of the dates were read as numbers)
    assert concatenated.df['Source'].tolist() == [name[:-4] for name in names]
    assert list(concatenated.df.columns) == list(direct.df.columns)
    for column in ['Month/day', 'Month', 'Day', 'Hour', 'Minute', 'Second']:
        assert concatenated.df[column].tolist() == direct.df[column].tolist(), column
    for column in ['Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                   'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
                   'Building_Total_Comfortable Hours_No Applicability (h) (summed)',
                   'Block1:Zone1_Zone Operative Temperature (°C)']:
        assert concatenated.df[column].tolist() == pytest.approx(direct.df[column].tolist(), rel=1e-12), column


def test_names_before_accim_1_0_0(tmp_path, monkeypatch):
    names = _copy_results(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.warns(DeprecationWarning, match='preview_Table_cols is deprecated'):
        assert preview_Table_cols(datasets=names) == _header(SAMPLE_CSVS[0])
    with pytest.warns(DeprecationWarning, match='genCSVconcatenated is deprecated'):
        genCSVconcatenated(datasets=names, source_frequency='hourly', frequency='runperiod',
                           concatenated_csv_name='gen', datasets_per_chunk=4)
    assert pd.read_csv(tmp_path / CONCATENATED, index_col=0)['Source'].tolist() == names
