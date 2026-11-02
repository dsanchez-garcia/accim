"""Tests for the graphical user interface of accim (accim.gui).

The forms (accim.gui.forms) are tested without a display; the window (accim.gui.app) only where tkinter can open one
(the tests of the window are skipped otherwise, as on a server without a display). AddAccis runs with the arguments
of a form, to check that they are complete: the interface cannot answer the questions of the prompt.
"""
import builtins
import os
import shutil
from pathlib import Path

import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder
from accim.gui import forms
from accim.gui.forms import FormError

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_energyplus = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                                      reason='needs EnergyPlus 25.1 and the sample IDF of the repository')


def _form(folder, **values):
    return dict(dict(forms.ADD_ACCIS_DEFAULTS, folder=str(folder), idfs=['model.idf']), **values)


# Forms ---------------------------------------------------------------------------------------------------------------

def test_numbers_of_the_text_fields():
    assert forms.parse_numbers('1, 2 3;4', 'category') == [1, 2, 3, 4]
    values = forms.parse_numbers(' 0.1  3 ', 'comfort_mode')
    assert values == [0.1, 3] and isinstance(values[1], int)
    assert forms.parse_number('-3.5', 'offset') == -3.5
    with pytest.raises(FormError, match='category: enter at least one number'):
        forms.parse_numbers(' , ', 'category')
    with pytest.raises(FormError, match="category: 'x' is not a number"):
        forms.parse_numbers('1 x', 'category')
    with pytest.raises(FormError, match='enter whole numbers'):
        forms.parse_numbers('1.5', 'num', integers=True)


def test_arguments_of_the_default_form(tmp_path):
    arguments = forms.add_accis_arguments(_form(tmp_path))

    assert arguments == dict(
        idfs=['model.idf'], script_type='vrf_mm', supply_air_temp_input_method='temperature difference',
        output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False, make_outputs_dataframe=False,
        energyplus_version='auto', setpoint_type='temperature', add_building_averages=False, name_suffix='', confirm=True,
        verbose=True, comfort_standard=[1], category=[3], comfort_mode=[3], cooling_season_start=121, cooling_season_end=274,
        hvac_mode=[2], ventilation_control=[0], ventilation_setpoint_offset=[0], min_outdoor_temp_offset=[50], max_wind_speed=[50], opening_factor_max_temp_diff=6,
        opening_factor_min_temp_diff=1, min_opening_factor=0.25, setpoint_tolerance_start=0.1, setpoint_tolerance_end=0.1, setpoint_tolerance_step=0.1)
    assert forms.output_idf_count(arguments) == 1


def test_arguments_that_depend_on_the_script_type_and_the_comfort_standards(tmp_path):
    # Full air-conditioning: HVAC mode 0, whatever the boxes of mixed mode
    arguments = forms.add_accis_arguments(_form(tmp_path, script_type='vrf_ac', hvac_mode=[], ventilation_control=[]))
    assert (arguments['hvac_mode'], arguments['ventilation_control']) == ([0], [0])
    assert 'ventilation_setpoint_offset' not in arguments
    # The custom model, with its coefficients; a date for the cooling season
    arguments = forms.add_accis_arguments(_form(tmp_path, comfort_standard=[1, 99], custom_slope='0.4',
                                                cooling_season_start='01/06'))
    assert arguments['custom_slope'] == 0.4 and arguments['custom_heating_offset'] == -3.5
    assert arguments['cooling_season_start'] == '01/06'


def test_number_of_output_idfs(tmp_path):
    arguments = forms.add_accis_arguments(_form(tmp_path, category='1 2 3', hvac_mode=[0, 2], ventilation_control=[0, 1]))
    # For each category: HVAC mode 0, and HVAC mode 2 with two ventilation controls
    assert forms.output_idf_count(arguments) == 3 * (1 + 2)
    arguments = forms.add_accis_arguments(_form(tmp_path, script_type='ex_ac', category='1 2 3'))
    assert forms.output_idf_count(arguments) == 3
    # The combinations without setpoints are not counted (INT EN16798 has no category 80)
    arguments = forms.add_accis_arguments(_form(tmp_path, category='80'))
    assert forms.output_idf_count(arguments) == 0


@pytest.mark.parametrize('values, message', [
    (dict(idfs=[]), 'select at least one input IDF'),
    (dict(comfort_standard=[]), 'select at least one comfort standard'),
    (dict(category='one'), "category: 'one' is not a number"),
    (dict(output_frequencies=[]), 'check at least one output frequency'),
    (dict(hvac_mode=[]), 'check at least one HVAC mode'),
    (dict(ventilation_control=[]), 'check at least one ventilation control'),
    (dict(setpoint_tolerance_step='0'), 'setpoint_tolerance_step: enter a number greater than 0'),
    (dict(cooling_season_end='31/13'), 'cooling_season_end must be a date'),
    (dict(script_type='vrf'), 'script_type: choose one of'),
    (dict(comfort_standard=[99], custom_intercept=''), 'custom_intercept: enter a number'),
])
def test_wrong_values_of_the_form(tmp_path, values, message):
    with pytest.raises(FormError, match=message):
        forms.add_accis_arguments(_form(tmp_path, **values))


def test_the_folder_must_exist(tmp_path):
    with pytest.raises(FormError, match='choose the folder of the input IDFs'):
        forms.add_accis_arguments(_form(tmp_path / 'missing'))


def test_files_of_the_folder(tmp_path):
    for name in ('model.idf', 'model[CS_INT EN16798[CA_3.idf', 'model_pymod.idf', 'Seville.epw', 'notes.txt'):
        (tmp_path / name).write_text('')

    assert forms.input_idfs(tmp_path) == ['model.idf']
    assert forms.simulations(tmp_path, only_accim_idfs=True) == [('model[CS_INT EN16798[CA_3.idf', 'Seville.epw')]
    assert len(forms.simulations(tmp_path, only_accim_idfs=False)) == 3
    assert forms.input_idfs(tmp_path / 'missing') == [] and forms.simulations(tmp_path / 'missing', True) == []


def test_arguments_of_run_ep(tmp_path):
    form = dict(forms.RUN_DEFAULTS, folder=str(tmp_path))

    assert forms.run_ep_arguments(form) == dict(only_accim_idfs=True, confirm=True, processes=2,
                                                energyplus_version='auto', backend='ems')
    for processes in ('0', '1.5', 'two'):
        with pytest.raises(FormError, match='processes'):
            forms.run_ep_arguments(dict(form, processes=processes))
    with pytest.raises(FormError, match='backend: choose one of'):
        forms.run_ep_arguments(dict(form, backend='eppy'))


def test_hints_of_the_categories_and_comfort_modes():
    assert forms.categories_hint([1, 99]) == '1 = INT EN16798: 1, 2, 3\n99 = CUSTOM: no categories (any value)'
    assert forms.comfort_modes_hint([22]) == '22 = INT ISO7730: 0'
    assert forms.comfort_standard_choices()[:2] == [(0, '0 = ESP CTE'), (1, '1 = INT EN16798')]


@needs_energyplus
@pytest.mark.parametrize('script_type', ['vrf_ac', 'vrf_mm'])
def test_add_accis_runs_with_the_arguments_of_the_form(tmp_path, monkeypatch, script_type):
    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    arguments = forms.add_accis_arguments(_form(tmp_path, script_type=script_type, category='2 3', output_type='simplified'))

    def prompt(text=''):
        raise AssertionError(f'AddAccis asked {text!r}')

    monkeypatch.setattr(builtins, 'input', prompt)
    monkeypatch.chdir(tmp_path)
    from accim.sim.accis import AddAccis

    written = AddAccis(**arguments).output_idfs
    assert len(written) == forms.output_idf_count(arguments) == 2
    assert all(name.startswith('model[CS_INT EN16798[CA_') for name in written)


# The window ----------------------------------------------------------------------------------------------------------

@pytest.fixture
def app():
    tk = pytest.importorskip('tkinter')
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f'tkinter cannot open a window here: {error}')
    root.withdraw()
    from accim.gui.app import AccimApp

    app = AccimApp(root)
    app.errors, app.infos, app.answers = [], [], []
    app.show_error = lambda title, message: app.errors.append(message)
    app.show_info = lambda title, message: app.infos.append(message)
    app.ask_yes_no = lambda title, message: app.answers.pop(0) if app.answers else False
    yield app
    app.close()


def test_the_window_gives_the_values_of_its_form(app, tmp_path):
    (tmp_path / 'model.idf').write_text('')

    app.folder.set(str(tmp_path))

    # The input IDFs of the new folder are listed and selected
    form = app.add_accis.form()
    assert form['folder'] == str(tmp_path) and form['idfs'] == ['model.idf']
    assert forms.add_accis_arguments(form) == forms.add_accis_arguments(_form(tmp_path))
    assert app.run.form()['folder'] == str(tmp_path)


def test_the_fields_follow_the_script_type_and_the_comfort_standards(app):
    tab = app.add_accis

    tab.vars['script_type'].set('vrf_ac')
    assert tab.mixed_mode_widgets[0].instate(['disabled']) and not tab.supply_air.instate(['disabled'])
    tab.vars['script_type'].set('ex_mm')
    assert not tab.mixed_mode_widgets[0].instate(['disabled']) and tab.supply_air.instate(['disabled'])
    assert tab.custom_widgets[0].instate(['disabled'])
    tab.standard_list.selection_set(len(tab.standards) - 1)
    tab.update_state()
    assert tab.selected_standards() == [1, 99] and not tab.custom_widgets[0].instate(['disabled'])
    assert '99 = CUSTOM' in tab.categories.cget('text')


def test_wrong_values_are_shown_and_nothing_runs(app, tmp_path):
    app.folder.set(str(tmp_path))  # no input IDFs

    assert app.add_accis.add() is False
    assert app.errors == ['idfs: select at least one input IDF.']
    assert app.run.run() is False and 'no IDFs or no EPWs' in app.errors[-1]


def test_the_tasks_print_in_the_log_and_cannot_ask_in_the_prompt(app, tmp_path):
    results, cwd = [], os.getcwd()

    def task():
        print('Hello from', os.path.basename(os.getcwd()))
        return 42

    app.execute('Task', str(tmp_path), task, on_done=results.append)
    app.execute('Question', str(tmp_path), lambda: input('Do you want to proceed? '))
    app.process_messages()

    log = app.log.get('1.0', 'end')
    assert f'Hello from {tmp_path.name}' in log and results == [42]
    assert len(app.errors) == 1 and 'cannot answer' in app.errors[0] and 'Do you want to proceed?' in app.errors[0]
    assert os.getcwd() == cwd and not app.busy
    # One task at a time
    app.busy = True
    assert app.run_task('Another task', str(tmp_path), task) is False and app.infos


def test_the_table_of_the_hours_within_the_setpoints(app, tmp_path):
    for name, within in (('a.csv', [1.0, 1.0]), ('b.csv', [1.0, 0.0])):
        pd.DataFrame({'Date/Time': ['01/01 01:00:00', '01/01 02:00:00'],
                      'EMS:Occupied Hours_ZONE1 [H](Hourly)': [1.0, 1.0],
                      'EMS:Occupied Comfortable Hours_No Applicability_ZONE1 [H](Hourly)': within}).to_csv(
            tmp_path / name, index=False)
    from accim.data.postprocessing.setpoint_hours import hours_within_setpoints

    app.hours.show(hours_within_setpoints(str(tmp_path)), 75)

    rows = [app.hours.tree.item(item, 'values') for item in app.hours.tree.get_children()]
    assert [row[1:] for row in rows] == [('100.0', '100.0', 'yes'), ('50.0', '50.0', 'no')]
    assert app.hours.result.get().startswith('1 of the 2 simulations reach 75')
    assert list(app.hours.summary.columns) == ['Source', 'Occupied Hours Within Setpoints_ZONE1 [%]',
                                               'Occupied Hours Within Setpoints_Building [%]', 'Reaches the minimum']
