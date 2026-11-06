"""Characterization (golden-file) tests for accim.data.postprocessing.main.Table.

Table builds its tables from the sample CSV files of the repository (accim/sample_files/sample_CSVs: the hourly
results of the sample TestModel for a year with the comfort modes CM_0 and CM_3, category CA_3, in Aberdeen and
London), and the tables are compared with the golden files of tests/core/golden/table: gzip CSV files, with the
numbers written with 6 decimals and, for Table.df, the columns sorted. After an intended change, write them again
and review the change:

    python -m pytest tests/core/test_table_characterization.py -q -p no:cacheprovider --update-golden

The golden files were written with accim 1.0.0 (those of the branch refactor/sim-v1 were written with an older
Table). A fake IDF with the zones, occupants and thermostats of TestModel.idf (the model of the sample notebook of
Table) replaces the IDF that Table reads, so that EnergyPlus is not needed; with the real IDF, Table gives the same
tables (checked on 2026-10-31).
"""
import copy
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

import accim.sim.accis
from accim.data.postprocessing.main import Table

from ._golden import check_golden

REPO = Path(__file__).resolve().parents[2]
SAMPLE_CSVS = sorted((REPO / 'accim' / 'sample_files' / 'sample_CSVs').glob('*.csv'))
GOLDEN = Path(__file__).parent / 'golden' / 'table'
ENERGY = ['Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
          'Building_Total_Heating Energy Demand (kWh/m2) (summed)']
HOURS = ['Building_Total_Comfortable Hours_No Applicability (h) (summed)',
         'Building_Total_Discomfortable Applicable Hot Hours (h) (summed)']

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


def _sample_table(folder, frequency):
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(folder)
        monkeypatch.setattr(accim.sim.accis, 'load_idf', lambda idf_path: _sample_building())
        return Table(
            datasets=[csv.name for csv in SAMPLE_CSVS], source_frequency='hourly', frequency=frequency,
            frequency_agg_func='sum', standard_outputs=True, level=['building'], level_agg_func=['sum', 'mean'],
            level_excluded_zones=[], split_epw_names=True, idf_path='TestModel.idf',
        )


@pytest.fixture(scope='module')
def runperiod_table(sample_folder):
    return _sample_table(sample_folder, 'runperiod')


@pytest.fixture(scope='module')
def monthly_table(sample_folder):
    return _sample_table(sample_folder, 'monthly')


def _csv(df):
    """The CSV text of a table, the same in every platform."""
    return df.to_csv(float_format='%.6f', lineterminator='\n').encode('utf-8')


@pytest.mark.parametrize('frequency', ['runperiod', 'monthly'])
def test_table_of_the_sample_results(frequency, request, update_golden):
    table = request.getfixturevalue(f'{frequency}_table')

    assert len(table.df) == {'runperiod': 4, 'monthly': 48}[frequency]
    check_golden(GOLDEN / f'table_{frequency}.csv.gz', _csv(table.df.reindex(sorted(table.df.columns), axis=1)),
                 update_golden, what=f'Table.df ({frequency})')


def test_unstacked_table_of_the_sample_results(runperiod_table, update_golden):
    table = copy.deepcopy(runperiod_table)
    table.format_table(type_of_table='energy demand')

    table.wrangled_table(reshaping='unstack', vars_to_gather=['ComfMod'], baseline='CM_0',
                         comparison_mode=['baseline compared to others'], comparison_cols=['relative', 'absolute'])

    unstacked = table.wrangled_df_unstacked
    assert list(unstacked.index) == ['Aberdeen', 'London']
    check_golden(GOLDEN / 'table_unstack_runperiod.csv.gz', _csv(unstacked), update_golden,
                 what='Table.wrangled_df_unstacked (runperiod)')


def test_pivoted_table_of_the_sample_results_has_the_values_of_the_unstacked_one(runperiod_table):
    pivoted = copy.deepcopy(runperiod_table)
    unstacked = copy.deepcopy(runperiod_table)
    arguments = dict(vars_to_gather=['ComfMod'], baseline='CM_0', comparison_mode=['others compared to baseline'],
                     comparison_cols=['relative', 'absolute'])
    for table in [pivoted, unstacked]:
        table.format_table(type_of_table='custom', custom_cols=ENERGY + HOURS)

    pivoted.wrangled_table(reshaping='pivot', **arguments)
    unstacked.wrangled_table(reshaping='unstack', **arguments)

    result = pivoted.wrangled_df_pivoted
    assert list(result.index) == ['Aberdeen', 'London']
    assert [c for c in result.columns] == [(value, label) for value in ENERGY + HOURS
                                           for label in ['CM_0', 'CM_3', '1-(CM_3/CM_0)', 'CM_0 - CM_3']]
    for column in result.columns:
        assert result[column].tolist() == unstacked.wrangled_df_unstacked[column].tolist(), column
    # The cooling demand of each city and comfort mode, as in Table.df
    df = runperiod_table.df
    for city in ['Aberdeen', 'London']:
        for comf_mod in ['CM_0', 'CM_3']:
            rows = df[(df['EPW_City_or_subcountry'] == city) & (df['ComfMod'] == comf_mod)]
            assert result.loc[city, (ENERGY[0], comf_mod)] == pytest.approx(rows[ENERGY[0]].item(), abs=0.005)


def test_monthly_pivoted_table_of_the_sample_results_adds_up_to_the_run_period(runperiod_table, monthly_table):
    table = copy.deepcopy(monthly_table)
    table.format_table(type_of_table='custom', custom_cols=ENERGY + HOURS)

    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'], baseline='CM_0',
                         comparison_cols=['relative', 'absolute'])

    result = table.wrangled_df_pivoted
    months = [f'{m:02d}' for m in range(1, 13)]
    df = runperiod_table.df
    for value in ENERGY + HOURS:
        labels = [label for label in result[value].columns]
        assert labels[:24] == [f'{c}_{m}_Month' for c in ['CM_0', 'CM_3'] for m in months]
        assert labels[24:26] == ['CM_0_Runperiod_Total', 'CM_3_Runperiod_Total']
        assert len(labels) == 26 + 2 * 13
        for city in ['Aberdeen', 'London']:
            for comf_mod in ['CM_0', 'CM_3']:
                year = df[(df['EPW_City_or_subcountry'] == city) & (df['ComfMod'] == comf_mod)][value].item()
                assert result.loc[city, (value, f'{comf_mod}_Runperiod_Total')] == pytest.approx(year, abs=0.005)
            assert result.loc[city, (value, 'CM_0 - CM_3_Runperiod_Total')] == pytest.approx(
                result.loc[city, (value, 'CM_0_Runperiod_Total')] - result.loc[city, (value, 'CM_3_Runperiod_Total')],
                abs=0.011)
