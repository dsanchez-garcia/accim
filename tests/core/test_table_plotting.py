"""Tests for the figures of accim.data.postprocessing.main.Table: generate_fig_data, scatter_plot,
scatter_plot_with_baseline, and the names of the subplots of time_plot (its dates are tested in
tests/core/test_table_time_plot.py).

The table has the first 48 hours of the sample CSV files of the repository (accim/sample_files/sample_CSVs: the
sample TestModel with the comfort modes CM_0 and CM_3, category CA_3, in Aberdeen and London). A fake IDF with the
zones, occupants and thermostats of TestModel.idf replaces the IDF that Table reads. The figures are drawn with the
Agg backend and checked through their axes: the titles and labels of the subplots, and the points and lines drawn.

Before (found on 2026-10-31), time_plot named the columns of subplots after the renamed columns only if the rows
were renamed too, and stopped with AttributeError ('cols_new_names') when only the rows were renamed.
"""
import builtins
import copy
from pathlib import Path
from types import SimpleNamespace

import besos.eppy_funcs
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.lines import Line2D

from accim.data.postprocessing.main import Table

REPO = Path(__file__).resolve().parents[2]
SAMPLE_CSVS = sorted((REPO / 'accim' / 'sample_files' / 'sample_CSVs').glob('*.csv'))
HOURS = 48
RMOT = 'Block1:Zone2_EN16798-1 Running mean outdoor temperature (°C)'
COOLING_SETPOINT = 'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)'
OPERATIVE = 'Building_Total_Zone Operative Temperature (°C) (mean)'
HEATING = 'Building_Total_Heating Energy Demand (kWh/m2) (summed)'
STATIC_ADAPTIVE = {'CM_0': 'Static', 'CM_3': 'Adaptive'}
CITIES = {'Aberdeen': 'Aberdeen', 'London': 'London'}

pytestmark = [pytest.mark.filterwarnings('ignore::pandas.errors.PerformanceWarning'),
              pytest.mark.filterwarnings('ignore:FigureCanvasAgg is non-interactive:UserWarning'),
              pytest.mark.filterwarnings("ignore:The 'generic' unit for NumPy timedelta:DeprecationWarning"),
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
    """The first 48 hours of the sample CSV files."""
    folder = tmp_path_factory.mktemp('first_hours')
    for csv in SAMPLE_CSVS:
        lines = csv.read_bytes().splitlines(keepends=True)
        (folder / csv.name).write_bytes(b''.join(lines[:HOURS + 1]))
    return folder


def _hourly_table(folder):
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(folder)
        monkeypatch.setattr(besos.eppy_funcs, 'get_building', lambda idf_path: _sample_building())
        return Table(
            datasets=[csv.name for csv in SAMPLE_CSVS], source_frequency='hourly', frequency='hourly',
            frequency_agg_func='sum', standard_outputs=True, level=['building'], level_agg_func=['sum', 'mean'],
            level_excluded_zones=[], split_epw_names=True, idf_path='TestModel.idf',
        )


@pytest.fixture(scope='module')
def hourly(sample_folder):
    return _hourly_table(sample_folder)


@pytest.fixture
def table(hourly, tmp_path, monkeypatch):
    """A copy of the hourly table, which the test can change; the figures are saved in tmp_path."""
    monkeypatch.chdir(tmp_path)
    yield copy.deepcopy(hourly)
    plt.close('all')


def _no_questions(monkeypatch):
    monkeypatch.setattr(builtins, 'input', lambda prompt='': pytest.fail(f'Unexpected question: {prompt}'))


def _new_figure(draw):
    """Draw a figure with draw() and return it."""
    before = set(plt.get_fignums())
    draw()
    new = sorted(set(plt.get_fignums()) - before)
    assert len(new) == 1
    return plt.figure(new[0])


def _rows(table, comf_mod, city):
    df = table.df
    return df[(df['ComfMod'] == comf_mod) & (df['EPW_City_or_subcountry'] == city)]


def _offsets(collection):
    return np.asarray(collection.get_offsets())


def test_hourly_table_of_the_first_two_days(hourly):
    assert len(hourly.df) == 4 * HOURS
    first = hourly.df.iloc[:HOURS]
    assert first['Month'].unique().tolist() == ['01']
    assert first['Day'].tolist() == ['01'] * 24 + ['02'] * 24
    # EnergyPlus gives the end of each hour (01:00 to 24:00); Table gives its start
    assert first['Hour'].tolist() == [f'{h:02d}' for h in range(24)] * 2
    assert first['Date/time'].iloc[[0, 23, 24]].tolist() == [' 01/01  01:00:00', ' 01/01  24:00:00',
                                                             ' 01/02  01:00:00']
    assert sorted(hourly.suggested_vars_dict) == ['ComfMod', 'Day', 'EPW_City_or_subcountry', 'Hour']


def test_generate_fig_data_gathers_the_data_of_each_subplot(table, monkeypatch):
    _no_questions(monkeypatch)

    table.generate_fig_data(
        vars_to_gather_rows=['ComfMod'], vars_to_gather_cols=['EPW_City_or_subcountry'],
        custom_cols_order=['London', 'Aberdeen'], data_on_x_axis=RMOT,
        data_on_y_main_axis=[['Temperature (°C)', [COOLING_SETPOINT, OPERATIVE]]],
        colorlist_y_main_axis=[['Temperature (°C)', ['b', 'r']]],
        best_fit_deg_y_main_axis=[['Temperature (°C)', [False, True]]],
        data_on_y_sec_axis=[['Energy (kWh/m2)', [HEATING]]], colorlist_y_sec_axis=[['Energy (kWh/m2)', ['g']]],
        rows_renaming_dict=STATIC_ADAPTIVE, cols_renaming_dict={'London': 'LDN', 'Aberdeen': 'ABZ'},
    )

    assert table.rows == ['CM_0', 'CM_3']
    assert table.cols == ['London', 'Aberdeen']
    assert table.rows_new_names == ['Static', 'Adaptive']
    assert table.cols_new_names == ['LDN', 'ABZ']
    # The figures do not change rename_cols of the Table, which format_table reads (before, they set it to 'y' or
    # 'n')
    assert (table.rename_rows, table.rename_subplot_cols, table.rename_cols) == ('y', 'y', True)
    assert len(table.df_for_graph) == HOURS
    for i, comf_mod in enumerate(table.rows):
        for j, city in enumerate(table.cols):
            rows = _rows(table, comf_mod, city)
            position, title, x = table.x_list[i][j]
            assert (position, title) == ([i, j], f'{comf_mod}_{city}')
            assert x.shape == (HOURS, 1)
            assert x.iloc[:, 0].tolist() == rows[RMOT].tolist()
            main = table.y_list_main[i][j]
            assert len(main) == 1
            assert main[0]['label'] == [COOLING_SETPOINT, OPERATIVE]
            assert main[0]['color'] == ['b', 'r']
            # True and False are degrees 1 and 0
            assert main[0]['best fit line deg'] == [0, 1]
            assert [d.iloc[:, 0].tolist() for d in main[0]['dataframe']] == \
                [rows[COOLING_SETPOINT].tolist(), rows[OPERATIVE].tolist()]
            secondary = table.y_list_sec[i][j]
            assert [d.iloc[:, 0].tolist() for d in secondary[0]['dataframe']] == [rows[HEATING].tolist()]
            assert secondary[0]['best fit line deg'] == [0]


def test_scatter_plot_draws_a_subplot_per_row_and_column(table, monkeypatch, tmp_path):
    _no_questions(monkeypatch)

    fig = _new_figure(lambda: table.scatter_plot(
        vars_to_gather_rows=['ComfMod'], vars_to_gather_cols=['EPW_City_or_subcountry'], data_on_x_axis=RMOT,
        data_on_y_main_axis=[['Temperature (°C)', [COOLING_SETPOINT, OPERATIVE]]],
        colorlist_y_main_axis=[['Temperature (°C)', ['b', 'r']]],
        best_fit_deg_y_main_axis=[['Temperature (°C)', [0, 1]]],
        data_on_y_sec_axis=[['Energy (kWh/m2)', [HEATING]]], colorlist_y_sec_axis=[['Energy (kWh/m2)', ['g']]],
        rows_renaming_dict=STATIC_ADAPTIVE, cols_renaming_dict=CITIES,
        supxlabel='Running mean outdoor temperature (°C)', figname='scatter', figsize=3, dpi=50, confirm_graph=True,
    ))

    assert (tmp_path / 'scatter.png').exists()
    # Two rows (comfort modes) and two columns (cities) of subplots, each with a secondary y-axis
    main, secondary = fig.axes[:4], fig.axes[4:]
    assert len(secondary) == 4
    assert [ax.get_title() for ax in main] == ['Aberdeen', 'London', '', '']
    assert [ax.get_ylabel() for ax in main] == ['Static', '', 'Adaptive', '']
    assert [t.get_text() for t in fig.texts] == ['Running mean outdoor temperature (°C)', 'Temperature (°C)',
                                                 'Energy (kWh/m2)']
    assert [t.get_text() for t in fig.legends[0].get_texts()] == [COOLING_SETPOINT, OPERATIVE, HEATING]
    for ax, twin, (comf_mod, city) in zip(main, secondary, [(m, c) for m in ['CM_0', 'CM_3']
                                                             for c in ['Aberdeen', 'London']]):
        assert twin.get_position().bounds == ax.get_position().bounds
        rows = _rows(table, comf_mod, city)
        x = rows[RMOT].to_numpy()
        assert len(ax.collections) == 2
        for collection, column in zip(ax.collections, [COOLING_SETPOINT, OPERATIVE]):
            np.testing.assert_allclose(_offsets(collection), np.column_stack([x, rows[column].to_numpy()]))
        # The best fit line of the operative temperature (degree 1)
        assert len(ax.lines) == 1
        assert ax.lines[0].get_xdata().tolist() == x.tolist()
        assert len(twin.collections) == 1
        np.testing.assert_allclose(_offsets(twin.collections[0]), np.column_stack([x, rows[HEATING].to_numpy()]))


def test_scatter_plot_with_baseline_compares_each_column_with_the_baseline(table, monkeypatch, tmp_path):
    _no_questions(monkeypatch)

    fig = _new_figure(lambda: table.scatter_plot_with_baseline(
        vars_to_gather_rows=['EPW_City_or_subcountry'], vars_to_gather_cols=['ComfMod'],
        data_on_y_axis_baseline_plot=[OPERATIVE, HEATING], baseline='CM_0', colorlist_baseline_plot_data=['r', 'b'],
        best_fit_deg=[1, 0], rows_renaming_dict=CITIES,
        # The baseline is on the x-axis, so the only column is CM_3
        cols_renaming_dict={'CM_3': 'Adaptive'},
        supxlabel='Static', supylabel='Adaptive', figname='baseline', figsize=3, dpi=50, confirm_graph=True,
    ))

    assert (tmp_path / 'baseline.png').exists()
    assert (table.rows, table.cols) == (['Aberdeen', 'London'], ['CM_3'])
    assert len(fig.axes) == 2
    assert [ax.get_title() for ax in fig.axes] == ['Adaptive', '']
    assert [ax.get_ylabel() for ax in fig.axes] == ['Aberdeen', 'London']
    assert [t.get_text() for t in fig.texts] == ['Static', 'Adaptive']
    assert [t.get_text() for t in fig.legends[0].get_texts()] == [OPERATIVE, HEATING]
    largest = max(table.df[OPERATIVE].max(), table.df[HEATING].max())
    assert table.max_value == largest
    for ax, city in zip(fig.axes, ['Aberdeen', 'London']):
        assert ax.get_xlim() == ax.get_ylim() == (0, largest)
        baseline, adaptive = _rows(table, 'CM_0', city), _rows(table, 'CM_3', city)
        # Each point is an hour: its value with the baseline (CM_0) and with CM_3
        assert len(ax.collections) == 2
        for collection, column in zip(ax.collections, [OPERATIVE, HEATING]):
            np.testing.assert_allclose(_offsets(collection),
                                       np.column_stack([baseline[column].to_numpy(), adaptive[column].to_numpy()]))
        lines = [child for child in ax.get_children() if isinstance(child, Line2D)]
        # The lines of the ratios 1, 2, 4, 1/2 and 1/4, and the best fit line of the operative temperature
        ends = sorted((line.get_xdata()[-1], line.get_ydata()[-1]) for line in lines[:5])
        assert ends == sorted([(largest, largest), (largest / 2, largest), (largest / 4, largest),
                               (largest, largest / 2), (largest, largest / 4)])
        assert len(lines) == 6
        assert lines[5].get_xdata().tolist() == baseline[OPERATIVE].tolist()


@pytest.mark.parametrize('renamed', ['rows', 'cols'])
def test_time_plot_names_the_rows_and_columns_of_subplots(table, monkeypatch, renamed):
    # The names that are not given are not changed (answer 'n' when asked)
    monkeypatch.setattr(builtins, 'input', lambda prompt='': 'n')
    renaming = {'rows_renaming_dict': STATIC_ADAPTIVE} if renamed == 'rows' else \
        {'cols_renaming_dict': {'Aberdeen': 'Aberdeen (UK)', 'London': 'London (UK)'}}

    fig = _new_figure(lambda: table.time_plot(
        vars_to_gather_rows=['ComfMod'], vars_to_gather_cols=['EPW_City_or_subcountry'],
        data_on_y_main_axis=[['Temperature (°C)', [OPERATIVE]]], colorlist_y_main_axis=[['Temperature (°C)', ['g']]],
        figname='time_plot', figsize=2, dpi=50, confirm_graph=True, **renaming,
    ))

    titles = [ax.get_title() for ax in fig.axes[:2]]
    labels = [ax.get_ylabel() for ax in fig.axes[::2]]
    if renamed == 'rows':
        assert (titles, labels) == (['Aberdeen', 'London'], ['Static', 'Adaptive'])
    else:
        assert (titles, labels) == (['Aberdeen (UK)', 'London (UK)'], ['CM_0', 'CM_3'])


@pytest.mark.parametrize('figure', ['scatter_plot', 'time_plot'])
def test_the_figures_of_one_row_name_their_row_and_columns(table, monkeypatch, figure):
    # Found on 2026-10-31: the figures of one row and several columns had no titles or row labels
    _no_questions(monkeypatch)
    kwargs = dict(
        vars_to_gather_rows=['ComfMod'], detailed_rows=['CM_3'], vars_to_gather_cols=['EPW_City_or_subcountry'],
        data_on_y_main_axis=[['Temperature (°C)', [OPERATIVE]]], colorlist_y_main_axis=[['Temperature (°C)', ['g']]],
        rows_renaming_dict={'CM_3': 'Adaptive'}, cols_renaming_dict=CITIES, figname='one_row', figsize=2, dpi=50,
        confirm_graph=True)
    if figure == 'scatter_plot':
        kwargs['data_on_x_axis'] = RMOT

    fig = _new_figure(lambda: getattr(table, figure)(**kwargs))

    assert len(fig.axes) == 2
    assert [ax.get_title() for ax in fig.axes] == ['Aberdeen', 'London']
    assert [ax.get_ylabel() for ax in fig.axes] == ['Adaptive', '']
