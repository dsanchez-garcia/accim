"""Tests for Table.wrangled_table(reshaping='pivot').

Before (accim 0.x and 1.0.0 until 2026-10-31), the pivot passed ``index=self.indexcols.remove('col_to_pivot')``,
which is None, to pandas.DataFrame.pivot_table, so:
- the rows of the table were the value columns, and the values of all the variables that change other than
  vars_to_gather (such as the cities) were summed: with the tables below, 1600 Wh of cooling for CM_0, the sum
  of Aberdeen (600) and London (1000);
- with monthly (or shorter) frequencies, the columns were named '<value>_<month>[Month', but the baseline was
  looked for without the month and the comparisons used '<value>_<month>_Month': wrangled_table asked for the
  baseline again, and then stopped with KeyError;
- it added 'col_to_pivot' to self.df and self.indexcols, and left it in self.df when it failed;
- the variables entered when asked (vars_to_gather not available) were not used (also with 'unstack').

The CSV files have the names of the outputs of the VRF system of accim, and made-up values. A fake IDF replaces
the IDF that Table reads.
"""
import builtins
from types import SimpleNamespace

import pandas as pd
import pytest

import accim.sim.accis
from accim.data.postprocessing.main import Table

pytestmark = pytest.mark.filterwarnings('ignore::pandas.errors.PerformanceWarning')

ZONE = 'Block1:Zone1'
OUTPUTS = [f'{ZONE.upper()} VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate [W](Hourly)',
           f'{ZONE.upper()} VRF INDOOR UNIT DX HEATING COIL:Heating Coil Heating Rate [W](Hourly)']
COOLING = 'Building_Total_Cooling Energy Demand (Wh) (summed)'
HEATING = 'Building_Total_Heating Energy Demand (Wh) (summed)'
# Two hours of January and one of February
DATES = [' 01/15  01:00:00', ' 01/15  02:00:00', ' 02/15  01:00:00']
# The cooling and heating rates (W) of each hour, with each comfort mode, in the present weather of each city
VALUES = {
    ('CM_0', 'Aberdeen'): ([100.0, 200.0, 300.0], [500.0, 300.0, 200.0]),
    ('CM_3', 'Aberdeen'): ([50.0, 50.0, 100.0], [100.0, 100.0, 50.0]),
    ('CM_0', 'London'): ([400.0, 400.0, 200.0], [100.0, 100.0, 200.0]),
    ('CM_3', 'London'): ([100.0, 300.0, 100.0], [50.0, 50.0, 100.0]),
}
HVAC = 'HM_2[VC_0[VO_0[MT_50[MW_50'


class _Obj(SimpleNamespace):
    """An eppy-like object: its fields can be read as attributes or as items."""

    def __getitem__(self, field):
        return getattr(self, field)


class _ObjectClasses(dict):
    """The idfobjects of eppy: the class names do not depend on the case, and missing classes raise KeyError."""

    def __getitem__(self, key):
        return super().__getitem__(key.upper())


def _building():
    """The IDF that Table reads: one occupied zone, with its occupants and its thermostat."""
    objects = _ObjectClasses({c: [] for c in ['ZONE', 'SPACE', 'SPACELIST', 'PEOPLE', 'ZONECONTROL:THERMOSTAT']})
    objects['ZONE'].append(_Obj(key='ZONE', Name=ZONE))
    objects['PEOPLE'].append(
        _Obj(key='PEOPLE', Name=f'People {ZONE}', Zone_or_ZoneList_or_Space_or_SpaceList_Name=ZONE))
    objects['ZONECONTROL:THERMOSTAT'].append(
        _Obj(key='ZONECONTROL:THERMOSTAT', Name=f'{ZONE} Thermostat', Zone_or_ZoneList_Name=ZONE))
    return SimpleNamespace(idfobjects=objects)


def _csv_name(comf_mod, city, scenario='Present', hvac=HVAC):
    return f'Model[CS_INT EN16798[CA_3[{comf_mod}[{hvac}[AT_0.1[NS_X[United-Kingdom_{city}_{scenario}.csv'


def _files(cities=('Aberdeen', 'London'), scenarios=('Present',)):
    """{CSV name: (cooling, heating)}; the rates of a future scenario are twice those of the present weather."""
    files = {}
    for (comf_mod, city), (cooling, heating) in VALUES.items():
        if city in cities:
            for factor, scenario in enumerate(scenarios, start=1):
                files[_csv_name(comf_mod, city, scenario)] = ([factor * v for v in cooling],
                                                              [factor * v for v in heating])
    return files


def _table(tmp_path, monkeypatch, files=None, frequency='runperiod'):
    """A Table of the CSV files, with the building totals of cooling and heating as values (format_table)."""
    files = _files() if files is None else files
    for name, values in files.items():
        lines = [','.join(['Date/Time', *OUTPUTS])]
        lines += [','.join([date, *(str(v[hour]) for v in values)]) for hour, date in enumerate(DATES)]
        (tmp_path / name).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(accim.sim.accis, 'load_idf', lambda idf_path: _building())
    table = Table(
        datasets=sorted(files), source_frequency='hourly', frequency=frequency, frequency_agg_func='sum',
        standard_outputs=True, level=['building'], level_agg_func=['sum'], level_excluded_zones=[],
        split_epw_names=True, normalised_energy_units=False, energy_units_in_kwh=False, idf_path='model.idf',
    )
    table.format_table(type_of_table='custom',
                       custom_cols=['Building_Total_Cooling Energy Demand', 'Building_Total_Heating Energy Demand'])
    assert table.val_cols == [COOLING, HEATING]
    return table


def _answers(monkeypatch, *answers):
    """Answer the questions of Table with answers, and fail if it asks more; return the questions asked."""
    remaining = list(answers)
    asked = []

    def ask(prompt=''):
        asked.append(prompt)
        if not remaining:
            pytest.fail(f'Unexpected question: {prompt}')
        return remaining.pop(0)

    monkeypatch.setattr(builtins, 'input', ask)
    return asked


def _assert_columns(df, expected):
    """The columns of df, in order, and their values (rounded to 2 decimals as wrangled_table does)."""
    assert list(df.columns) == list(expected)
    for column, values in expected.items():
        assert df[column].tolist() == pytest.approx(values), column


def test_pivot_has_a_row_per_city_and_the_comfort_modes_and_comparisons_in_columns(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch)
    _answers(monkeypatch)

    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'], baseline='CM_0',
                         comparison_mode=['others compared to baseline', 'baseline compared to others'],
                         comparison_cols=['relative', 'absolute'])

    pivoted = table.wrangled_df_pivoted
    assert pivoted.index.name == 'EPW_City_or_subcountry'
    assert list(pivoted.index) == ['Aberdeen', 'London']
    assert list(pivoted.columns.names) == [None, 'col_to_pivot']
    # Aberdeen: 600 Wh of cooling with CM_0 and 200 Wh with CM_3; London: 1000 and 500
    _assert_columns(pivoted, {
        (COOLING, 'CM_0'): [600.0, 1000.0],
        (COOLING, 'CM_3'): [200.0, 500.0],
        (COOLING, '1-(CM_3/CM_0)'): [0.67, 0.5],
        (COOLING, 'CM_0 - CM_3'): [400.0, 500.0],
        (COOLING, '1-(CM_0/CM_3)'): [-2.0, -1.0],
        (COOLING, 'CM_3 - CM_0'): [-400.0, -500.0],
        (HEATING, 'CM_0'): [1000.0, 400.0],
        (HEATING, 'CM_3'): [250.0, 200.0],
        (HEATING, '1-(CM_3/CM_0)'): [0.75, 0.5],
        (HEATING, 'CM_0 - CM_3'): [750.0, 200.0],
        (HEATING, '1-(CM_0/CM_3)'): [-3.0, -1.0],
        (HEATING, 'CM_3 - CM_0'): [-750.0, -200.0],
    })


def test_pivot_does_not_change_the_table(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch)
    df, indexcols, val_cols = table.df.copy(), list(table.indexcols), list(table.val_cols)
    arguments = dict(reshaping='pivot', vars_to_gather=['ComfMod'], baseline='CM_0', comparison_cols=['absolute'])

    table.wrangled_table(**arguments)
    first = table.wrangled_df_pivoted
    table.wrangled_table(**arguments)

    pd.testing.assert_frame_equal(table.wrangled_df_pivoted, first)
    pd.testing.assert_frame_equal(table.df, df)
    assert table.indexcols == indexcols
    assert table.val_cols == val_cols
    # unstack, after the pivot, gives the same values
    table.wrangled_table(reshaping='unstack', vars_to_gather=['ComfMod'])
    for value in [COOLING, HEATING]:
        for comf_mod in ['CM_0', 'CM_3']:
            assert table.wrangled_df_unstacked[(value, comf_mod)].tolist() == first[(value, comf_mod)].tolist()


def test_pivot_of_a_monthly_table_has_the_months_and_the_run_period_in_columns(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch, frequency='monthly')
    _answers(monkeypatch)

    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'], baseline='CM_0',
                         comparison_cols=['relative', 'absolute'])

    pivoted = table.wrangled_df_pivoted
    assert list(pivoted.index) == ['Aberdeen', 'London']
    _assert_columns(pivoted, {
        (COOLING, 'CM_0_01_Month'): [300.0, 800.0],
        (COOLING, 'CM_0_02_Month'): [300.0, 200.0],
        (COOLING, 'CM_3_01_Month'): [100.0, 400.0],
        (COOLING, 'CM_3_02_Month'): [100.0, 100.0],
        (COOLING, 'CM_0_Runperiod_Total'): [600.0, 1000.0],
        (COOLING, 'CM_3_Runperiod_Total'): [200.0, 500.0],
        (COOLING, '1-(CM_3/CM_0)_01_Month'): [0.67, 0.5],
        (COOLING, 'CM_0 - CM_3_01_Month'): [200.0, 400.0],
        (COOLING, '1-(CM_3/CM_0)_02_Month'): [0.67, 0.5],
        (COOLING, 'CM_0 - CM_3_02_Month'): [200.0, 100.0],
        (COOLING, '1-(CM_3/CM_0)_Runperiod_Total'): [0.67, 0.5],
        (COOLING, 'CM_0 - CM_3_Runperiod_Total'): [400.0, 500.0],
        (HEATING, 'CM_0_01_Month'): [800.0, 200.0],
        (HEATING, 'CM_0_02_Month'): [200.0, 200.0],
        (HEATING, 'CM_3_01_Month'): [200.0, 100.0],
        (HEATING, 'CM_3_02_Month'): [50.0, 100.0],
        (HEATING, 'CM_0_Runperiod_Total'): [1000.0, 400.0],
        (HEATING, 'CM_3_Runperiod_Total'): [250.0, 200.0],
        (HEATING, '1-(CM_3/CM_0)_01_Month'): [0.75, 0.5],
        (HEATING, 'CM_0 - CM_3_01_Month'): [600.0, 100.0],
        (HEATING, '1-(CM_3/CM_0)_02_Month'): [0.75, 0.5],
        (HEATING, 'CM_0 - CM_3_02_Month'): [150.0, 100.0],
        (HEATING, '1-(CM_3/CM_0)_Runperiod_Total'): [0.75, 0.5],
        (HEATING, 'CM_0 - CM_3_Runperiod_Total'): [750.0, 200.0],
    })


def test_pivot_of_an_hourly_table_sums_the_hours_of_each_month(tmp_path, monkeypatch):
    (tmp_path / 'monthly').mkdir()
    (tmp_path / 'hourly').mkdir()
    monthly = _table(tmp_path / 'monthly', monkeypatch, frequency='monthly')
    hourly = _table(tmp_path / 'hourly', monkeypatch, frequency='hourly')
    arguments = dict(reshaping='pivot', vars_to_gather=['ComfMod'], baseline='CM_0', comparison_cols=['relative'])

    monthly.wrangled_table(**arguments)
    hourly.wrangled_table(**arguments)

    assert len(hourly.df) == 3 * len(_files())
    pd.testing.assert_frame_equal(hourly.wrangled_df_pivoted, monthly.wrangled_df_pivoted)


def test_pivot_of_the_months(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch, frequency='monthly')

    table.wrangled_table(reshaping='pivot', vars_to_gather=['Month'], baseline='01', comparison_cols=['absolute'])

    pivoted = table.wrangled_df_pivoted
    # The dates are not rows: they have the month
    assert list(pivoted.index.names) == ['ComfMod', 'EPW_City_or_subcountry']
    assert list(pivoted.index) == [('CM_0', 'Aberdeen'), ('CM_0', 'London'), ('CM_3', 'Aberdeen'), ('CM_3', 'London')]
    _assert_columns(pivoted, {
        (COOLING, '01'): [300.0, 800.0, 100.0, 400.0],
        (COOLING, '02'): [300.0, 200.0, 100.0, 100.0],
        (COOLING, '01 - 02'): [0.0, 600.0, 0.0, 300.0],
        (HEATING, '01'): [800.0, 200.0, 200.0, 100.0],
        (HEATING, '02'): [200.0, 200.0, 50.0, 100.0],
        (HEATING, '01 - 02'): [600.0, 0.0, 150.0, 0.0],
    })


def test_pivot_without_other_variables_has_a_row_per_value_column(tmp_path, monkeypatch):
    # As shown in the sample notebook of Table: nothing but the comfort mode changes
    table = _table(tmp_path, monkeypatch, files=_files(cities=['London']))

    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'], baseline='CM_0',
                         comparison_mode=['others compared to baseline'], comparison_cols=['relative', 'absolute'])

    pivoted = table.wrangled_df_pivoted
    assert list(pivoted.index) == [COOLING, HEATING]
    assert pivoted.columns.name == 'col_to_pivot'
    _assert_columns(pivoted, {
        'CM_0': [1000.0, 400.0],
        'CM_3': [500.0, 200.0],
        '1-(CM_3/CM_0)': [0.5, 0.5],
        'CM_0 - CM_3': [500.0, 200.0],
    })


def test_pivot_of_two_gathered_variables(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch)

    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod', 'EPW_City_or_subcountry'],
                         baseline='CM_0[London', comparison_cols=['absolute'])

    pivoted = table.wrangled_df_pivoted
    assert list(pivoted.index) == [COOLING, HEATING]
    _assert_columns(pivoted, {
        'CM_0[Aberdeen': [600.0, 1000.0],
        'CM_0[London': [1000.0, 400.0],
        'CM_3[Aberdeen': [200.0, 250.0],
        'CM_3[London': [500.0, 200.0],
        'CM_0[London - CM_0[Aberdeen': [400.0, -600.0],
        'CM_0[London - CM_3[Aberdeen': [800.0, 150.0],
        'CM_0[London - CM_3[London': [500.0, 200.0],
    })


def test_pivot_keeps_the_variables_of_vars_to_keep_and_sums_the_others(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch, files=_files(scenarios=('Present', 'RCP85-2050')))

    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'])
    # All the variables that change are in the rows
    assert list(table.wrangled_df_pivoted.index.names) == ['EPW_City_or_subcountry', 'EPW_Scenario', 'EPW_Year']
    assert list(table.wrangled_df_pivoted.index) == [('Aberdeen', 'Present', 'Present'), ('Aberdeen', 'RCP85', '2050'),
                                                     ('London', 'Present', 'Present'), ('London', 'RCP85', '2050')]
    assert table.wrangled_df_pivoted[(COOLING, 'CM_0')].tolist() == [600.0, 1200.0, 1000.0, 2000.0]

    # The cooling of the present weather and of RCP85-2050 (twice the present one), summed
    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'], vars_to_keep=['EPW_City_or_subcountry'])
    by_city = table.wrangled_df_pivoted
    assert list(by_city.index) == ['Aberdeen', 'London']
    _assert_columns(by_city, {
        (COOLING, 'CM_0'): [1800.0, 3000.0],
        (COOLING, 'CM_3'): [600.0, 1500.0],
        (HEATING, 'CM_0'): [3000.0, 1200.0],
        (HEATING, 'CM_3'): [750.0, 600.0],
    })

    # The same variables, chosen when asked
    asked = _answers(monkeypatch, 'y', 'EPW_City_or_subcountry')
    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'], check_index_and_cols=True)
    assert len(asked) == 2
    pd.testing.assert_frame_equal(table.wrangled_df_pivoted, by_city)


def test_pivot_leaves_out_the_arguments_that_do_not_apply(tmp_path, monkeypatch):
    # Mixed mode (HM_2) and air conditioning (HM_0), whose ventilation arguments are 'X': VentCtrl, VSToffset,
    # MinOToffset and MaxWindSpeed change with HVACmode, so they are not rows of the table
    files = {}
    for (comf_mod, city), (cooling, heating) in VALUES.items():
        hvac = 'HM_2[VC_0[VO_0[MT_50[MW_50' if comf_mod == 'CM_0' else 'HM_0[VC_X[VO_X[MT_X[MW_X'
        files[_csv_name('CM_3', city, hvac=hvac)] = (cooling, heating)
    table = _table(tmp_path, monkeypatch, files=files)

    table.wrangled_table(reshaping='pivot', vars_to_gather=['HVACmode'], baseline='HM_2', comparison_cols=['absolute'])

    pivoted = table.wrangled_df_pivoted
    assert list(pivoted.index) == ['Aberdeen', 'London']
    _assert_columns(pivoted, {
        (COOLING, 'HM_0'): [200.0, 500.0],
        (COOLING, 'HM_2'): [600.0, 1000.0],
        (COOLING, 'HM_2 - HM_0'): [400.0, 500.0],
        (HEATING, 'HM_0'): [250.0, 200.0],
        (HEATING, 'HM_2'): [1000.0, 400.0],
        (HEATING, 'HM_2 - HM_0'): [750.0, 200.0],
    })


def test_pivot_asks_for_the_baseline_only_to_compare(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch)

    # Without comparisons, no baseline is needed
    _answers(monkeypatch)
    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'])
    assert [c[1] for c in table.wrangled_df_pivoted.columns] == ['CM_0', 'CM_3', 'CM_0', 'CM_3']

    # A baseline that is not one of the comfort modes is asked again
    asked = _answers(monkeypatch, 'CM_3')
    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'], baseline='CM_9', comparison_cols=['absolute'])
    assert len(asked) == 1
    assert table.wrangled_df_pivoted[(COOLING, 'CM_3 - CM_0')].tolist() == [-400.0, -500.0]


@pytest.mark.parametrize('reshaping', ['pivot', 'unstack'])
def test_wrangled_table_uses_the_variables_entered_when_asked(tmp_path, monkeypatch, reshaping):
    table = _table(tmp_path, monkeypatch)
    asked = _answers(monkeypatch, 'ComfMod')

    table.wrangled_table(reshaping=reshaping, vars_to_gather=['Comfort mode'])

    assert len(asked) == 1
    result = table.wrangled_df_pivoted if reshaping == 'pivot' else table.wrangled_df_unstacked
    assert result[(COOLING, 'CM_0')].tolist() == [600.0, 1000.0]
    assert result[(COOLING, 'CM_3')].tolist() == [200.0, 500.0]


def test_pivot_with_rename_dict_and_transpose(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch)

    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'], baseline='CM_0',
                         comparison_cols=['relative', 'absolute'],
                         rename_dict={'CM_0': 'Static', 'CM_3': 'Adaptive'}, transpose=True)

    pivoted = table.wrangled_df_pivoted
    assert list(pivoted.columns) == ['Aberdeen', 'London']
    assert list(pivoted.index) == [(value, label) for value in [COOLING, HEATING]
                                   for label in ['Static', 'Adaptive', '1-(Adaptive/Static)', 'Static - Adaptive']]
    assert pivoted.loc[(HEATING, 'Static - Adaptive')].tolist() == [750.0, 200.0]


def test_pivot_follows_the_custom_order(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch)
    table.custom_order(ordered_list=['London', 'Aberdeen'], column_to_order='EPW_City_or_subcountry')
    table.custom_order(ordered_list=['CM_3', 'CM_0'], column_to_order='ComfMod')

    table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'], baseline='CM_0', comparison_cols=['absolute'])

    pivoted = table.wrangled_df_pivoted
    assert list(pivoted.index) == ['London', 'Aberdeen']
    _assert_columns(pivoted, {
        (COOLING, 'CM_3'): [500.0, 200.0],
        (COOLING, 'CM_0'): [1000.0, 600.0],
        (COOLING, 'CM_0 - CM_3'): [500.0, 400.0],
        (HEATING, 'CM_3'): [200.0, 250.0],
        (HEATING, 'CM_0'): [400.0, 1000.0],
        (HEATING, 'CM_0 - CM_3'): [200.0, 750.0],
    })


def test_pivot_explains_what_it_needs(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match='needs vars_to_gather'):
        table.wrangled_table(reshaping='pivot')
    table.format_table(type_of_table='all')
    with pytest.raises(ValueError, match='call format_table first'):
        table.wrangled_table(reshaping='pivot', vars_to_gather=['ComfMod'])
