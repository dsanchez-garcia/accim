"""Tests for the methods of accim.data.postprocessing.main.Table that prepare the tables: format_table,
gather_vars_query and custom_order, and for the concatenated CSV file of Table and the energy units.

The tables are those of the sample CSV files of the repository (accim/sample_files/sample_CSVs: the hourly results
of the sample TestModel for a year with the comfort modes CM_0 and CM_3, category CA_3, in Aberdeen and London).
A fake IDF with the zones, occupants and thermostats of TestModel.idf replaces the IDF that Table reads.
"""
import copy
import shutil
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import accim.sim.accis
from accim.data.postprocessing.main import Table

REPO = Path(__file__).resolve().parents[2]
SAMPLE_CSVS = sorted((REPO / 'accim' / 'sample_files' / 'sample_CSVs').glob('*.csv'))
COOLING = 'Building_Total_Cooling Energy Demand (kWh/m2) (summed)'
VARIABLES = ['Model', 'ComfStand', 'CAT', 'ComfMod', 'HVACmode', 'VentCtrl', 'VSToffset', 'MinOToffset',
             'MaxWindSpeed', 'ASTtol', 'NameSuffix', 'EPW', 'Source']
EPW_VARIABLES = ['EPW_Country_name', 'EPW_City_or_subcountry', 'EPW_Scenario-Year', 'EPW_Scenario', 'EPW_Year']

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


@pytest.fixture(scope='module')
def sample_folder(tmp_path_factory):
    folder = tmp_path_factory.mktemp('sample_csvs')
    for csv in SAMPLE_CSVS:
        shutil.copy(csv, folder)
    return folder


def _sample_table(folder, **kwargs):
    arguments = dict(
        datasets=[csv.name for csv in SAMPLE_CSVS], source_frequency='hourly', frequency='runperiod',
        frequency_agg_func='sum', standard_outputs=True, level=['building'], level_agg_func=['sum', 'mean'],
        level_excluded_zones=[], split_epw_names=True, idf_path='TestModel.idf',
    )
    arguments.update(kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(folder)
        monkeypatch.setattr(accim.sim.accis, 'load_idf', lambda idf_path: _sample_building())
        return Table(**arguments)


@pytest.fixture(scope='module')
def runperiod(sample_folder):
    return _sample_table(sample_folder)


@pytest.fixture(scope='module')
def monthly(sample_folder):
    return _sample_table(sample_folder, frequency='monthly')


@pytest.fixture
def table(runperiod):
    """A copy of the run period table, which the test can change."""
    return copy.deepcopy(runperiod)


ENERGY_DEMAND = [
    'Block1:Zone2_Cooling Energy Demand (kWh/m2)', 'Block1:Zone1_Cooling Energy Demand (kWh/m2)',
    'Block1:Zone2_Heating Energy Demand (kWh/m2)', 'Block1:Zone1_Heating Energy Demand (kWh/m2)',
    'Block1:Zone2_Total Energy Demand (kWh/m2) (summed)', 'Block1:Zone1_Total Energy Demand (kWh/m2) (summed)',
    'Building_Total_Cooling Energy Demand (kWh/m2) (summed)', 'Building_Total_Cooling Energy Demand (kWh/m2) (mean)',
    'Building_Total_Heating Energy Demand (kWh/m2) (summed)', 'Building_Total_Heating Energy Demand (kWh/m2) (mean)',
    'Building_Total_Total Energy Demand (kWh/m2) (summed)', 'Building_Total_Total Energy Demand (kWh/m2) (mean)',
]
TEMPERATURE = [
    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    'Building_Total_Zone Operative Temperature (°C) (mean)',
    'Building_Total_Cooling Energy Demand (kWh/m2) (summed)', 'Building_Total_Cooling Energy Demand (kWh/m2) (mean)',
    'Building_Total_Heating Energy Demand (kWh/m2) (summed)', 'Building_Total_Heating Energy Demand (kWh/m2) (mean)',
]


def test_format_table_energy_demand(table):
    table.format_table(type_of_table='energy demand')

    assert table.val_cols == ENERGY_DEMAND
    assert list(table.df.columns) == table.indexcols + ENERGY_DEMAND
    assert table.indexcols == VARIABLES + EPW_VARIABLES
    assert len(table.df) == 4


def test_format_table_comfort_hours_selects_the_hours(table):
    table.format_table(type_of_table='comfort hours')

    hours = [c for c in table.df_backup.columns if '(h)' in c]
    assert len(hours) == 28
    assert sorted(table.val_cols) == sorted(hours)
    assert list(table.df.columns) == table.indexcols + table.val_cols


def test_format_table_temperature(table):
    table.format_table(type_of_table='temperature')

    # The setpoints, the operative temperature and the energy demand of the building, and one running mean
    # outdoor temperature (the first of the columns: here, that of ASHRAE 55 of Block1:Zone2)
    assert table.val_cols[:-1] == TEMPERATURE
    assert 'Running mean outdoor temperature' in table.val_cols[-1]
    assert list(table.df.columns) == table.indexcols + table.val_cols


def test_format_table_custom_and_all_start_from_the_whole_table(table):
    table.format_table(type_of_table='custom',
                       custom_cols=['Building_Total_Cooling Energy Demand', 'block1:zone1_heating energy demand'])
    assert table.val_cols == [COOLING, 'Building_Total_Cooling Energy Demand (kWh/m2) (mean)',
                              'Block1:Zone1_Heating Energy Demand (kWh/m2)']
    assert list(table.df.columns) == table.indexcols + table.val_cols

    table.format_table(type_of_table='all')
    assert table.val_cols == []
    assert list(table.df.columns) == list(table.df_backup.columns)


def test_format_table_custom_without_columns_raises(table):
    with pytest.raises(ValueError, match='You have not selected any column'):
        table.format_table(type_of_table='custom', custom_cols=['__no_such_column__'])


def test_index_columns_of_monthly_tables(monthly):
    table = copy.deepcopy(monthly)

    table.format_table(type_of_table='custom', custom_cols=[COOLING])

    assert table.indexcols == ['Date/time'] + VARIABLES + ['Month'] + EPW_VARIABLES
    assert table.df['Month'].tolist() == [f'{m:02d}' for m in range(1, 13)] * 4


def test_gather_vars_query_prints_the_variables_and_their_combinations(table, capsys):
    columns = list(table.df.columns)

    assert table.gather_vars_query(vars_to_gather=['ComfMod', 'EPW_City_or_subcountry']) is None

    out = capsys.readouterr().out.splitlines()
    assert "ComfMod: ['CM_0', 'CM_3']" in out
    assert "EPW_City_or_subcountry: ['Aberdeen', 'London']" in out
    assert out[-4:] == ['CM_0[Aberdeen', 'CM_0[London', 'CM_3[Aberdeen', 'CM_3[London']
    assert list(table.df.columns) == columns
    assert table.suggested_vars_dict == {'ComfMod': ['CM_0', 'CM_3'], 'EPW_City_or_subcountry': ['Aberdeen', 'London']}
    assert table.cols_for_multiindex == ['ComfMod', 'EPW_City_or_subcountry']


def test_custom_order_orders_the_values_of_a_column(table):
    table.format_table(type_of_table='custom', custom_cols=[COOLING])

    table.custom_order(ordered_list=['London', 'Aberdeen'], column_to_order='EPW_City_or_subcountry')

    dtype = table.df['EPW_City_or_subcountry'].dtype
    assert isinstance(dtype, pd.CategoricalDtype)
    assert dtype.ordered
    assert list(dtype.categories) == ['London', 'Aberdeen']
    assert table.df.sort_values('EPW_City_or_subcountry')['EPW_City_or_subcountry'].tolist() == \
        ['London', 'London', 'Aberdeen', 'Aberdeen']
    assert table.df[COOLING].tolist() == table.df_backup[COOLING].tolist()


def test_concatenated_csv_gives_the_same_table(tmp_path, monthly, monkeypatch):
    name = 'roundtrip[srcfreq-hourly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv'
    for csv in SAMPLE_CSVS:
        shutil.copy(csv, tmp_path)

    # With concatenated_csv_name, Table only writes the concatenated CSV file
    written = _sample_table(tmp_path, frequency='monthly', concatenated_csv_name='roundtrip')
    assert not hasattr(written, 'df')
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted([csv.name for csv in SAMPLE_CSVS] + [name])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(accim.sim.accis, 'load_idf', lambda idf_path: _sample_building())
    table = Table(source_concatenated_csv_filepath=name, level=['building'], level_agg_func=['sum', 'mean'],
                  level_excluded_zones=[], split_epw_names=True, idf_path='TestModel.idf')

    # The frequencies are read from the name of the file
    assert table.frequency == 'monthly'
    assert sorted(table.df.columns) == sorted(monthly.df.columns)
    for column in monthly.df.columns:
        if column in ['Day', 'Hour', 'Minute', 'Second']:
            # The first values of each month, unused with monthly frequencies, come back as numbers
            assert pd.to_numeric(table.df[column]).tolist() == pd.to_numeric(monthly.df[column]).tolist(), column
        elif pd.api.types.is_numeric_dtype(monthly.df[column]):
            assert table.df[column].tolist() == pytest.approx(monthly.df[column].tolist(), rel=1e-12), column
        else:
            assert table.df[column].tolist() == monthly.df[column].tolist(), column


def test_energy_units_without_normalisation_and_in_wh(sample_folder, runperiod):
    table = _sample_table(sample_folder, normalised_energy_units=False, energy_units_in_kwh=False)

    assert not [c for c in table.df.columns if 'kWh' in c]
    area = runperiod.df['Building_Total_Zone Floor Area (m2) (summed)']
    assert table.df['Building_Total_Cooling Energy Demand (Wh) (summed)'].tolist() == \
        pytest.approx((runperiod.df[COOLING] * 1000 * area).tolist())
    for zone in ['Block1:Zone1', 'Block1:Zone2']:
        zone_area = runperiod.df[f'{zone}_Zone Floor Area (m2)']
        assert table.df[f'{zone}_Heating Energy Demand (Wh)'].tolist() == \
            pytest.approx((runperiod.df[f'{zone}_Heating Energy Demand (kWh/m2)'] * 1000 * zone_area).tolist())


def test_occupied_zones_and_blocks_are_in_the_order_of_the_model(runperiod):
    # They came from sets of strings, whose order changes from one Python session to another
    assert runperiod.occupied_zone_list == ['Block1:Zone2', 'Block1:Zone1']
    assert runperiod.block_list == ['Block1']
