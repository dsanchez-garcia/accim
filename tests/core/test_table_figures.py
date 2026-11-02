"""Tests for the figures of Table, with the arguments that the graphical user interface gives them.

Found on 2026-11-02 by running the tab "Table and figures" of the GUI on simulations of the sample model: the figures
of a table of the run period (the default frequency of the tab) stopped with "'Series' object has no attribute
'columns'" (without dates, unstacking the simulations gave a Series); and the arguments of the GUI lacked the colours
of the y axis (``colorlist_y_main_axis``, IndexError) and answered no question of the figures (they ask whether to
rename the rows and the columns of the subplots). The first test of the GUI used a fake Table.

The CSV files have the names of the columns that accim and EnergyPlus give the outputs, and made-up values (those of
``test_table_columns.py``). A fake IDF replaces the IDF that Table reads.
"""
import builtins
from pathlib import Path

import besos.eppy_funcs
import matplotlib.pyplot as plt
import pytest

from accim.gui import forms, tasks

from .test_table_columns import DESIGNBUILDER, _outputs

CSV_NAMES = [f'Model[CS_INT EN16798[CA_{category}[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X[Seville.csv'
             for category in (2, 3)]


@pytest.fixture
def simulations(tmp_path, monkeypatch):
    """Two simulations of the DesignBuilder model, with categories 2 and 3, of two hours each; the figures answer
    only the questions that the GUI answers."""
    columns = _outputs(DESIGNBUILDER['building'], DESIGNBUILDER['ems_suffixes'])
    for offset, name in enumerate(CSV_NAMES):
        lines = [','.join(['Date/Time', *columns])]
        for hour in range(2):
            lines.append(','.join([f' 01/01  0{hour + 1}:00:00', *(str(v[hour] + offset) for v in columns.values())]))
        (tmp_path / name).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(besos.eppy_funcs, 'get_building', lambda idf_path: DESIGNBUILDER['building'])

    def answer(prompt=''):
        question = str(prompt).strip()
        for beginning, value in tasks.FIGURE_ANSWERS.items():
            if question.startswith(beginning):
                return value
        raise AssertionError(f'The figure asked {question!r}')

    monkeypatch.setattr(builtins, 'input', answer)
    return tmp_path


def _table(frequency):
    return tasks.make_table({'table': dict(
        datasets=CSV_NAMES, source_frequency='hourly', frequency=frequency, frequency_agg_func='sum',
        standard_outputs=True, level=['building'], level_agg_func=['sum'], level_excluded_zones=[],
        split_epw_names=False, idf_path='model.idf'), 'type_of_table': 'all'})


def _figure_form(table, figure_type, frequency):
    columns = [str(c) for c in table.df.columns]
    return dict(forms.TABLE_DEFAULTS, figure_type=figure_type, vars_to_gather_rows=['CAT'],
                vars_to_gather_cols=['EPW'],
                data_on_y_main_axis=[c for c in columns if 'Zone Operative Temperature' in c][:2],
                data_on_x_axis=next(c for c in columns if 'Outdoor Air Drybulb' in c),
                figname=f'figure_{figure_type}_{frequency}', figsize='2', dpi='50', table_frequency=frequency)


@pytest.mark.parametrize('frequency, figure_type', [('runperiod', 'scatter'), ('hourly', 'scatter'),
                                                    ('hourly', 'time')])
def test_the_figures_of_the_gui_with_a_real_table(simulations, frequency, figure_type):
    table = _table(frequency)
    arguments = forms.figure_arguments(_figure_form(table, figure_type, frequency))

    path = tasks.make_figure(table, arguments)

    assert Path(path) == simulations / f'figure_{figure_type}_{frequency}.png' and Path(path).stat().st_size > 0


def test_scatter_plot_of_a_run_period_table(simulations):
    table = _table('runperiod')
    assert len(table.df) == 2
    form = _figure_form(table, 'scatter', 'runperiod')
    y_columns = form['data_on_y_main_axis']

    table.scatter_plot(vars_to_gather_rows=['CAT'], vars_to_gather_cols=['EPW'],
                       data_on_x_axis=form['data_on_x_axis'], data_on_y_main_axis=[['Temperature', y_columns]],
                       colorlist_y_main_axis=[['Temperature', ['b', 'r'][:len(y_columns)]]],
                       rows_renaming_dict={'CA_2': 'Category 2', 'CA_3': 'Category 3'},
                       cols_renaming_dict={'Seville': 'Seville'}, figname='run_period', dpi=50, confirm_graph=True)
    plt.close('all')

    # One row: a column for each output and simulation, with numbers
    assert len(table.df_for_graph) == 1
    assert table.df_for_graph[[c for c in table.df_for_graph.columns if y_columns[0] in c]].shape[1] == 2
    assert all(dtype.kind == 'f' for dtype in table.df_for_graph[
        [c for c in table.df_for_graph.columns if 'Temperature' in c]].dtypes)
    assert (simulations / 'run_period.png').is_file()


def test_the_time_plot_of_a_run_period_table_is_not_allowed(simulations):
    table = _table('runperiod')

    with pytest.raises(forms.FormError, match='the time plot needs a table with another frequency'):
        forms.figure_arguments(_figure_form(table, 'time', 'runperiod'))
