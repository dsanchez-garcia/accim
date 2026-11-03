"""Tests for the graphical user interface of accim (accim.gui).

The forms (accim.gui.forms) are tested without a display; the window (accim.gui.app) only where tkinter can open one
(the tests of the window are skipped otherwise, as on a server without a display). AddAccis runs with the arguments
of a form, to check that they are complete: the interface cannot answer the questions of the prompt.
"""
import builtins
import inspect
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

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
        output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
        make_outputs_dataframe=False, energyplus_version='auto', setpoint_type='temperature',
        add_building_averages=False, name_suffix='', confirm=True, verbose=True, comfort_standard=[1], category=[3],
        comfort_mode=[3], cooling_season_start=121, cooling_season_end=274, hvac_mode=[2], ventilation_control=[0],
        ventilation_setpoint_offset=[0], min_outdoor_temp_offset=[50], max_wind_speed=[50],
        opening_factor_max_temp_diff=6, opening_factor_min_temp_diff=1, min_opening_factor=0.25,
        setpoint_tolerance_start=0.1, setpoint_tolerance_end=0.1, setpoint_tolerance_step=0.1)
    assert forms.output_idf_count(arguments) == 1


def test_arguments_that_depend_on_the_script_type_and_the_comfort_standards(tmp_path):
    # Full air-conditioning: HVAC mode 0, whatever the boxes of mixed mode
    arguments = forms.add_accis_arguments(_form(tmp_path, script_type='vrf_ac', hvac_mode=[], ventilation_control=[]))
    assert (arguments['hvac_mode'], arguments['ventilation_control']) == ([0], [0])
    assert 'ventilation_setpoint_offset' not in arguments
    assert not any(name.startswith('existing_hvac') for name in arguments)
    # The custom model, with its coefficients; a date for the cooling season
    arguments = forms.add_accis_arguments(_form(tmp_path, comfort_standard=[1, 99], custom_slope='0.4',
                                                cooling_season_start='01/06'))
    assert arguments['custom_slope'] == 0.4 and arguments['custom_heating_offset'] == -3.5
    assert arguments['cooling_season_start'] == '01/06'


def test_arguments_of_the_existing_hvac_systems(tmp_path):
    from accim.sim.accis import AddAccis

    # The defaults of the form are those of AddAccis (an empty availability schedule is None)
    parameters = inspect.signature(AddAccis).parameters
    defaults = {name: parameters[name].default for name in forms.EXISTING_HVAC_DEFAULTS}
    for script_type in ('ex_ac', 'ex_mm'):
        arguments = forms.add_accis_arguments(_form(tmp_path, script_type=script_type))
        assert {name: arguments[name] for name in defaults} == defaults
    arguments = forms.add_accis_arguments(_form(
        tmp_path, script_type='ex_mm', existing_hvac_operative_temperature_control=False,
        existing_hvac_radiant_setpoints=False, existing_hvac_widen_outdoor_temperature_limits=True,
        existing_hvac_ideal_loads_backup=True, existing_hvac_availability_schedule=' Office Hours '))
    assert {name: arguments[name] for name in defaults} == dict(
        existing_hvac_operative_temperature_control=False, existing_hvac_radiant_setpoints=False,
        existing_hvac_widen_outdoor_temperature_limits=True, existing_hvac_ideal_loads_backup=True,
        existing_hvac_availability_schedule='Office Hours')
    for schedule in ('On; 24/7', 'a,b', 'On!'):
        with pytest.raises(FormError, match='existing_hvac_availability_schedule: enter the name of a schedule'):
            forms.add_accis_arguments(_form(tmp_path, script_type='ex_ac',
                                            existing_hvac_availability_schedule=schedule))


def test_number_of_output_idfs(tmp_path):
    arguments = forms.add_accis_arguments(_form(tmp_path, category='1 2 3', hvac_mode=[0, 2],
                                                ventilation_control=[0, 1]))
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


def test_arguments_of_each_zone(tmp_path):
    assert forms.parse_zone_arguments('comfort_standard=2, category=80;hvac_mode=0\ncooling_season_start=01/06') == {
        'comfort_standard': 2, 'category': 80, 'hvac_mode': 0, 'cooling_season_start': '01/06'}
    rows = [('Block1:Zone2', 'comfort_standard=2, category=80'), ('Block1:Zone1', 'setpoint_tolerance=0.25')]

    arguments = forms.add_accis_arguments(_form(tmp_path, zone_arguments=rows))

    assert arguments['zone_arguments'] == {'Block1:Zone2': {'comfort_standard': 2, 'category': 80},
                                           'Block1:Zone1': {'setpoint_tolerance': 0.25}}
    assert 'zone_arguments' not in forms.add_accis_arguments(_form(tmp_path))


@pytest.mark.parametrize('rows, message', [
    ([('Zone1', 'comfort_standard 2')], 'write each argument as name=value'),
    ([('Zone1', 'comf_stand=2')], "'comf_stand' is not an argument of a zone"),
    ([('Zone1', 'category=80, category=90')], 'category is given twice'),
    ([('Zone1', 'category=eighty')], "'eighty' is not a number"),
    ([('Zone1', '')], 'give at least one argument'),
    ([('', 'category=80')], 'a row has no zone'),
    ([('Zone1', 'category=80'), ('ZONE1', 'category=90')], "the zone 'ZONE1' is given twice"),
])
def test_wrong_arguments_of_a_zone(tmp_path, rows, message):
    with pytest.raises(FormError, match=message):
        forms.add_accis_arguments(_form(tmp_path, zone_arguments=rows))


def test_the_arguments_of_each_zone_need_temperature_setpoints(tmp_path):
    with pytest.raises(FormError, match='need the adaptive setpoint temperatures'):
        forms.add_accis_arguments(_form(tmp_path, setpoint_type='pmv', zone_arguments=[('Zone1', 'category=80')]))


def _apmv_form(folder, **values):
    return dict(dict(forms.APMV_DEFAULTS, folder=str(folder), idf='model.idf'), **values)


def test_arguments_of_the_apmv_setpoints(tmp_path):
    (tmp_path / 'model.idf').write_text('')

    arguments = forms.apmv_arguments(_apmv_form(tmp_path))

    assert arguments == dict(
        idf='model.idf', output_idf='model_aPMV.idf', energyplus_version='auto', add_vrf_system=True,
        supply_air_temp_input_method='temperature difference', always_occupied=False,
        apmv=dict(output_frequencies=['hourly'], other_pmv_related_outputs=True, adaptive_coefficient_cooling=0.293,
                  adaptive_coefficient_heating=-0.293, pmv_cooling_setpoint=0.5, pmv_heating_setpoint=-0.5,
                  cooling_setpoint_tolerance_cooling_season=-0.1, cooling_setpoint_tolerance_heating_season=-0.1,
                  heating_setpoint_tolerance_cooling_season=0.1, heating_setpoint_tolerance_heating_season=0.1,
                  cooling_season_start=121, cooling_season_end=274, verbose=True),
        pmv_inputs={})
    # The defaults of the form are those of apply_apmv_setpoints
    from accim.sim.apmv import apply_apmv_setpoints

    defaults = inspect.signature(apply_apmv_setpoints).parameters
    for name, value in arguments['apmv'].items():
        if name not in ('output_frequencies', 'verbose'):
            assert defaults[name].default == value, name
    arguments = forms.apmv_arguments(_apmv_form(tmp_path, output_idf='new.idf', air_velocity='0.2',
                                                activity_level=' '))
    assert arguments['output_idf'] == 'new.idf' and arguments['pmv_inputs'] == {'air_velocity': 0.2}


@pytest.mark.parametrize('values, message', [
    (dict(idf=''), 'idf: choose the input IDF'),
    (dict(idf='other.idf'), "'other.idf' is not in the folder"),
    (dict(output_idf='model.idf'), 'must differ from that of the input IDF'),
    (dict(output_idf='results/new.idf'), 'enter the name of an IDF file'),
    (dict(output_idf='new.txt'), 'enter the name of an IDF file'),
    (dict(output_frequencies=[]), 'check at least one output frequency'),
    (dict(pmv_cooling_setpoint='high'), "'high' is not a number"),
    (dict(cooling_season_end='31/13'), 'cooling_season_end must be a date'),
])
def test_wrong_arguments_of_the_apmv_setpoints(tmp_path, values, message):
    (tmp_path / 'model.idf').write_text('')
    with pytest.raises(FormError, match=message):
        forms.apmv_arguments(_apmv_form(tmp_path, **values))


def test_arguments_of_rename_epw_files(tmp_path):
    for name in ('a.epw', 'b.epw'):
        (tmp_path / name).write_text('')
    form = dict(forms.RENAME_EPWS_DEFAULTS, folder=str(tmp_path), epws=['a.epw'],
                cities='seville = Sevilla\n\nmad = Madrid', countries='Spain = Sevilla, Madrid')

    assert forms.rename_epws_arguments(form) == dict(
        filelist=['a.epw'], rename_city_dict={'seville': 'Sevilla', 'mad': 'Madrid'},
        country_to_city_dict={'Spain': ['Sevilla', 'Madrid']}, confirm_renaming=True, confirm_deletion=False)
    arguments = forms.rename_epws_arguments(dict(form, cities='', countries='\n', delete_originals=True))
    assert arguments['rename_city_dict'] is None and arguments['country_to_city_dict'] is None
    assert arguments['confirm_deletion'] is True
    for values, message in [(dict(epws=[]), 'select at least one EPW'), (dict(epws=['c.epw']), 'not in the folder'),
                            (dict(cities='Sevilla'), 'write each line as key = value'),
                            (dict(cities='seville = A\nseville = B'), "'seville' is given twice")]:
        with pytest.raises(FormError, match=message):
            forms.rename_epws_arguments(dict(form, **values))


def test_arguments_of_table(tmp_path):
    for name in ('model.idf', 'model[CS_INT EN16798[CA_3.idf', 'model[CS_INT EN16798[CA_3[Seville.csv',
                 'model[CS_INT EN16798[CA_3[SevilleTable.csv', 'model[CS_INT EN16798[CA_3[SevilleMeter.csv',
                 'notes.csv'):
        (tmp_path / name).write_text('')
    form = dict(forms.TABLE_DEFAULTS, folder=str(tmp_path), idf_path='model.idf',
                level_excluded_zones='Zone1, Zone2')

    assert forms.simulation_csvs(tmp_path) == ['model[CS_INT EN16798[CA_3[Seville.csv']
    assert forms.idf_files(tmp_path) == ['model.idf', 'model[CS_INT EN16798[CA_3.idf']
    assert forms.table_arguments(form) == dict(table=dict(
        datasets=['model[CS_INT EN16798[CA_3[Seville.csv'], source_frequency='hourly', frequency='runperiod',
        frequency_agg_func='sum', standard_outputs=True, level=['building'], level_agg_func=['sum'],
        level_excluded_zones=['Zone1', 'Zone2'], split_epw_names=False, idf_path='model.idf'), type_of_table='all')
    for values, message in [(dict(idf_path=''), 'idf_path: choose an IDF'),
                            (dict(source_frequency='daily', frequency='hourly'), 'cannot be shorter'),
                            (dict(level=[]), 'level: check'), (dict(level_agg_func=[]), 'level_agg_func: check'),
                            (dict(type_of_table='mine'), 'type_of_table: choose one of')]:
        with pytest.raises(FormError, match=message):
            forms.table_arguments(dict(form, **values))
    (tmp_path / 'empty').mkdir()
    with pytest.raises(FormError, match='no CSV files of simulations'):
        forms.table_arguments(dict(form, folder=str(tmp_path / 'empty')))


def test_arguments_of_the_figures():
    form = dict(forms.TABLE_DEFAULTS, vars_to_gather_rows=['ComfMod'], vars_to_gather_cols=['EPW'],
                data_on_x_axis='RMOT (C)', data_on_y_main_axis=['Cooling (kWh/m2)', 'Heating (kWh/m2)'],
                y_axis_label='Energy (kWh/m2)')

    assert forms.figure_arguments(form) == dict(figure_type='scatter', kwargs=dict(
        vars_to_gather_rows=['ComfMod'], vars_to_gather_cols=['EPW'],
        data_on_y_main_axis=[['Energy (kWh/m2)', ['Cooling (kWh/m2)', 'Heating (kWh/m2)']]],
        colorlist_y_main_axis=[['Energy (kWh/m2)', ['tab:blue', 'tab:orange']]], figname='accim_figure', figsize=4,
        ratio_height_to_width=0.75, dpi=150, confirm_graph=True, data_on_x_axis='RMOT (C)', supxlabel='RMOT (C)'))
    time_plot = forms.figure_arguments(dict(form, figure_type='time', data_on_x_axis='', figsize='6.5',
                                            table_frequency='monthly'))
    assert time_plot['figure_type'] == 'time' and 'data_on_x_axis' not in time_plot['kwargs']
    assert (time_plot['kwargs']['figsize'], time_plot['kwargs']['ratio_height_to_width']) == (6.5, 0.5)
    for values, message in [(dict(vars_to_gather_rows=[]), 'select at least one variable'),
                            (dict(vars_to_gather_cols=['ComfMod']), 'cannot be in the rows and the columns'),
                            (dict(data_on_y_main_axis=[]), 'select at least one column for the y axis'),
                            (dict(data_on_x_axis=''), 'choose the column of the x axis'),
                            (dict(figname='a/b'), 'figname'), (dict(dpi='20'), 'at least 50'),
                            (dict(figsize='0.5'), 'figsize'),
                            (dict(figure_type='time', table_frequency='runperiod'), 'the time plot needs')]:
        with pytest.raises(FormError, match=message):
            forms.figure_arguments(dict(form, **values))
    # More columns than colours: the colours repeat
    many = forms.figure_arguments(dict(form, data_on_y_main_axis=[f'c{i}' for i in range(12)]))
    assert many['kwargs']['colorlist_y_main_axis'][0][1][10:] == ['tab:blue', 'tab:orange']


def test_values_of_the_parameters():
    assert forms.parse_parameter_values('1, 2 3', 'comfort_standard') == [1, 2, 3]
    assert forms.parse_parameter_values('0.2 to 0.6', 'custom_slope') == (0.2, 0.6)
    for text, message in [('0.6 to 0.2', 'from a lower to a higher value'), ('1, 1', 'an option is repeated'),
                          ('', 'enter at least one number'), ('a to b', "'a' is not a number")]:
        with pytest.raises(FormError, match=message):
            forms.parse_parameter_values(text, 'x')


def test_the_parameters_of_the_form_are_those_of_the_parametric_module():
    from accim.parametric_and_optimisation import params_dicts

    assert list(forms.PREDEFINED_MODEL_PARAMETERS) == list(params_dicts.accim_predef_model_params)
    assert list(forms.CUSTOM_MODEL_PARAMETERS) == list(params_dicts.accim_custom_model_params)


def _parametric_form(folder, **values):
    for name in ('model.idf', 'a.epw', 'b.epw'):
        (Path(folder) / name).write_text('')
    return dict(dict(forms.PARAMETRIC_DEFAULTS, folder=str(folder), idf='model.idf', epws=['a.epw', 'b.epw'],
                     parameters=[('comfort_standard', '1, 2'), ('category', '1 2 3')]), **values)


def test_arguments_of_the_parametric_study(tmp_path):
    arguments = forms.parametric_arguments(_parametric_form(tmp_path))

    assert arguments == dict(idf='model.idf', epws=['a.epw', 'b.epw'], parameters_type='accim predefined model',
                             script_type='vrf_mm',
                             accis_params_dict={'comfort_standard': [1, 2], 'category': [1, 2, 3]},
                             sampling='full set', samples=0, meters=['Heating:Electricity', 'Cooling:Electricity'],
                             processes=2, out_dir='gui_parametric_results', existing_hvac={})
    assert forms.parametric_simulation_count(arguments) == 2 * 3 * 2
    custom = forms.parametric_arguments(_parametric_form(
        tmp_path, parameters_type='accim custom model', sampling='lhs', samples='8',
        parameters=[('custom_slope', '0.2 to 0.6'), ('custom_offset', '2 to 4')]))
    assert custom['accis_params_dict'] == {'custom_slope': (0.2, 0.6), 'custom_offset': (2, 4)}
    assert forms.parametric_simulation_count(custom) == 8 * 2


def test_the_parametric_study_with_the_existing_hvac_systems(tmp_path):
    arguments = forms.parametric_arguments(_parametric_form(
        tmp_path, script_type='ex_ac', existing_hvac_ideal_loads_backup=True,
        existing_hvac_availability_schedule='On 24/7'))

    assert arguments['existing_hvac'] == dict(
        existing_hvac_operative_temperature_control=True, existing_hvac_radiant_setpoints=True,
        existing_hvac_widen_outdoor_temperature_limits=False, existing_hvac_ideal_loads_backup=True,
        existing_hvac_availability_schedule='On 24/7')


@pytest.mark.parametrize('values, message', [
    (dict(parameters=[]), 'add at least one parameter'),
    (dict(parameters=[('ComfStand', '1, 2')]), "'ComfStand' is not a parameter of the accim predefined model"),
    (dict(parameters=[('category', '1'), ('category', '2')]), 'category is given twice'),
    (dict(parameters=[('category', '1 to 3')]), 'the full set needs options'),
    (dict(sampling='lhs', parameters=[('category', '1 to 3')]), 'the predefined models need options'),
    (dict(parameters_type='accim custom model', sampling='lhs', parameters=[('custom_slope', '0.3, 0.4')]),
     'needs ranges'),
    (dict(parameters_type='accim custom model', sampling='lhs', samples='0',
          parameters=[('custom_slope', '0.2 to 0.4')]), 'samples: enter a whole number'),
    (dict(epws=[]), 'select at least one EPW'),
    (dict(meters=' , '), 'enter at least one meter'),
    (dict(out_dir='C:/results'), 'out_dir'),
    (dict(processes='0'), 'processes'),
    (dict(script_type='ex_ac', existing_hvac_availability_schedule='On, 24/7'), 'existing_hvac_availability_schedule'),
])
def test_wrong_arguments_of_the_parametric_study(tmp_path, values, message):
    with pytest.raises(FormError, match=message):
        forms.parametric_arguments(_parametric_form(tmp_path, **values))


# Tasks ---------------------------------------------------------------------------------------------------------------

def test_the_occupied_zones_of_an_idf(monkeypatch):
    from accim.gui import tasks
    from accim.sim import accis, targets

    monkeypatch.setattr(accis, 'load_idf', lambda idf, version: 'BUILDING')
    monkeypatch.setattr(targets, 'resolve_targets',
                        lambda building: [SimpleNamespace(zone_name=zone) for zone in ('Z1', 'Z2', 'Z1')])

    assert tasks.occupied_zones('model.idf') == ['Z1', 'Z2']


class _Building:
    saved = None

    def saveas(self, path):
        self.saved = path


def test_the_task_of_the_apmv_setpoints(tmp_path, monkeypatch):
    from accim.gui import tasks
    from accim.sim import accis, apmv

    calls, building = [], _Building()
    monkeypatch.setattr(accis, 'load_idf', lambda idf, version: calls.append(('load', idf, version)) or building)
    for name in ('set_zones_always_occupied', 'add_vrf_system', 'apply_apmv_setpoints', 'set_pmv_input_parameters'):
        monkeypatch.setattr(apmv, name, lambda b, _name=name, **kwargs: calls.append((_name, kwargs)))
    (tmp_path / 'model.idf').write_text('')
    arguments = forms.apmv_arguments(_apmv_form(tmp_path, always_occupied=True, air_velocity='0.2'))

    assert tasks.apply_apmv(arguments) == 'model_aPMV.idf' and building.saved == 'model_aPMV.idf'
    assert [call[0] for call in calls] == ['load', 'set_zones_always_occupied', 'add_vrf_system',
                                           'apply_apmv_setpoints', 'set_pmv_input_parameters']
    assert calls[2][1] == {'supply_air_temp_input_method': 'temperature difference'}
    assert calls[3][1] == arguments['apmv'] and calls[4][1] == {'air_velocity': 0.2}


@needs_energyplus
def test_the_apmv_setpoints_of_the_form_on_the_sample_model(tmp_path, monkeypatch):
    from accim.gui import tasks

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)

    assert tasks.apply_apmv(forms.apmv_arguments(_apmv_form(tmp_path))) == 'model_aPMV.idf'
    text = (tmp_path / 'model_aPMV.idf').read_text(encoding='latin-1')
    assert 'apply_aPMV_' in text and 'set_zone_input_data_' in text


def test_the_task_of_rename_epw_files(tmp_path, monkeypatch):
    import accim.data.preprocessing as preprocessing
    from accim.gui import tasks

    received = {}

    def rename_epw_files(**kwargs):
        received.update(kwargs)
        (tmp_path / 'Spain_Sevilla_Present.epw').write_text('')

    monkeypatch.setattr(preprocessing, 'rename_epw_files', rename_epw_files)
    monkeypatch.chdir(tmp_path)

    assert tasks.rename_epws({'filelist': ['a.epw']}) == ['Spain_Sevilla_Present.epw']
    assert received == {'filelist': ['a.epw']}


def test_the_tasks_of_table(tmp_path, monkeypatch):
    import accim.data.postprocessing.main as postprocessing
    from accim.gui import tasks

    made = {}

    class FakeTable:
        def __init__(self, **kwargs):
            made['table'] = kwargs
            self.formatted = []

        def format_table(self, type_of_table):
            self.formatted.append(type_of_table)

        def scatter_plot(self, **kwargs):
            made['scatter'] = kwargs
            Path(kwargs['figname'] + '.png').write_text('')

        def time_plot(self, **kwargs):
            made['time'] = kwargs

    monkeypatch.setattr(postprocessing, 'Table', FakeTable)
    monkeypatch.chdir(tmp_path)

    table = tasks.make_table({'table': {'datasets': ['a.csv']}, 'type_of_table': 'energy demand'})
    assert made['table'] == {'datasets': ['a.csv']} and table.formatted == ['energy demand']
    path = tasks.make_figure(table, {'figure_type': 'scatter', 'kwargs': {'figname': 'figure', 'dpi': 150}})
    assert path == str(tmp_path / 'figure.png') and made['scatter'] == {'figname': 'figure', 'dpi': 150}
    tasks.make_figure(table, {'figure_type': 'time', 'kwargs': {'figname': 'other'}})
    assert made['time'] == {'figname': 'other'}
    import matplotlib

    assert matplotlib.get_backend().lower() == 'agg'


def test_the_task_of_the_parametric_study(tmp_path, monkeypatch):
    import accim.parametric_and_optimisation.main as main_module
    from accim.gui import tasks
    from accim.sim import accis

    calls = []

    class FakeSimulation:
        def __init__(self, **kwargs):
            calls.append(('init', kwargs))
            self.parameters_values_df = pd.DataFrame({'x': [1, 2]})

        def __getattr__(self, name):
            def method(**kwargs):
                calls.append((name, kwargs))
                return {'meters': 'METERS'} if name == 'select_outputs' else 'RESULTS'
            return method

    monkeypatch.setattr(main_module, 'ParametricSimulation', FakeSimulation)
    monkeypatch.setattr(accis, 'load_idf', lambda idf, version: 'BUILDING')

    arguments = forms.parametric_arguments(_parametric_form(tmp_path, epws=['a.epw']))
    assert tasks.parametric_study(arguments) == 'RESULTS'
    assert [call[0] for call in calls] == ['init', 'discover_available_outputs', 'select_outputs',
                                           'apply_outputs_preflight', 'set_output_readers', 'set_parameters',
                                           'set_problem', 'sampling_full_set', 'run_parametric_simulation']
    assert calls[0][1] == dict(buildings=['BUILDING'], epws=['a.epw'], parameters_type='accim predefined model',
                               output_frequencies=['hourly'], script_type='vrf_mm')
    assert calls[2][1]['meters'] == ['Heating:Electricity', 'Cooling:Electricity']
    assert calls[4][1] == {'df_output_meter': 'METERS'}
    assert calls[5][1] == dict(accis_params_dict={'comfort_standard': [1, 2], 'category': [1, 2, 3]},
                               use_default_values=True)
    assert calls[-1][1]['out_dir'] == 'gui_parametric_results' and calls[-1][1]['processes'] == 2
    lhs = forms.parametric_arguments(_parametric_form(
        tmp_path, epws=['a.epw'], parameters_type='accim custom model', sampling='lhs', samples='3',
        parameters=[('custom_slope', '0.2 to 0.6')]))
    calls.clear()
    tasks.parametric_study(lhs)
    assert ('sampling_lhs', {'num_samples': 3}) in calls
    # The existing HVAC systems get their arguments
    existing = forms.parametric_arguments(_parametric_form(
        tmp_path, epws=['a.epw'], script_type='ex_ac', existing_hvac_widen_outdoor_temperature_limits=True))
    calls.clear()
    tasks.parametric_study(existing)
    assert calls[0][1] == dict(buildings=['BUILDING'], epws=['a.epw'], parameters_type='accim predefined model',
                               output_frequencies=['hourly'], script_type='ex_ac', **existing['existing_hvac'])
    assert calls[0][1]['existing_hvac_widen_outdoor_temperature_limits'] is True


def test_the_parametric_simulation_accepts_the_arguments_of_the_existing_hvac_systems():
    from accim.parametric_and_optimisation.main import ParametricSimulation

    parameters = inspect.signature(ParametricSimulation).parameters
    assert all(parameters[name].default == (None if default == '' else default)
               for name, default in forms.EXISTING_HVAC_DEFAULTS.items())


@needs_energyplus
@pytest.mark.parametrize('script_type', ['vrf_ac', 'vrf_mm', 'ex_mm'])
def test_add_accis_runs_with_the_arguments_of_the_form(tmp_path, monkeypatch, script_type):
    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    arguments = forms.add_accis_arguments(_form(tmp_path, script_type=script_type, category='2 3',
                                                output_type='simplified'))

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
    root = None
    # Tcl sometimes fails to read its library files on Windows when many windows are opened in one process: another
    # attempt opens it
    for attempt in range(3):
        try:
            root = tk.Tk()
            break
        except tk.TclError as error:
            reason = error
    if root is None:
        pytest.skip(f'tkinter cannot open a window here: {reason}')
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
    assert all(widget.instate(['disabled']) for widget in tab.existing_hvac_widgets)
    assert str(tab.availability_combo.cget('state')) == 'disabled'
    tab.vars['script_type'].set('ex_mm')
    assert not tab.mixed_mode_widgets[0].instate(['disabled']) and tab.supply_air.instate(['disabled'])
    assert not any(widget.instate(['disabled']) for widget in tab.existing_hvac_widgets)
    # Any schedule of the model can be typed
    assert str(tab.availability_combo.cget('state')) == 'normal'
    assert tab.custom_widgets[0].instate(['disabled'])
    tab.standard_list.selection_set(len(tab.standards) - 1)
    tab.update_state()
    assert tab.selected_standards() == [1, 99] and not tab.custom_widgets[0].instate(['disabled'])
    assert '99 = CUSTOM' in tab.categories.cget('text')
    # The options of the setpoints need the adaptive setpoint temperatures
    tab.vars['setpoint_type'].set('pmv')
    assert all(widget.instate(['disabled']) for widget in tab.existing_hvac_temperature_widgets)
    assert not tab.existing_hvac_widgets[-1].instate(['disabled'])


def test_the_window_gives_the_arguments_of_the_existing_hvac_systems(app, tmp_path):
    (tmp_path / 'model.idf').write_text('')
    app.folder.set(str(tmp_path))
    tab = app.add_accis

    tab.vars['script_type'].set('ex_ac')
    tab.vars['existing_hvac_ideal_loads_backup'].set(True)
    tab.vars['existing_hvac_availability_schedule'].set('On 24/7')
    arguments = forms.add_accis_arguments(tab.form())
    assert arguments['existing_hvac_ideal_loads_backup'] is True
    assert arguments['existing_hvac_availability_schedule'] == 'On 24/7'
    assert arguments['existing_hvac_operative_temperature_control'] is True


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


def test_the_tabs_of_the_window(app):
    assert [app.notebook.tab(tab, 'text') for tab in app.notebook.tabs()] == [
        '1. Add the ACCIS', '2. aPMV setpoints', '3. Rename the EPWs', '4. Run the simulations',
        '5. Hours within the setpoints', '6. Table and figures', '7. Parametric study']


def test_the_table_of_the_arguments_of_each_zone(app, tmp_path):
    (tmp_path / 'model.idf').write_text('')
    app.folder.set(str(tmp_path))
    tab = app.add_accis

    tab.zone_name.set('Block1:Zone2')
    tab.zone_text.set('comfort_standard=2, category=80')
    assert tab.set_zone()
    tab.zone_text.set('comfort_standard=2, category=90')
    assert tab.set_zone() and tab.zone_rows() == [('Block1:Zone2', 'comfort_standard=2, category=90')]
    tab.zone_text.set('comf_stand=2')
    assert not tab.set_zone() and "'comf_stand' is not an argument" in app.errors[-1]
    assert forms.add_accis_arguments(tab.form())['zone_arguments'] == {
        'Block1:Zone2': {'comfort_standard': 2, 'category': 90}}
    # With PMV setpoints, the arguments of the zones are disabled and not given
    tab.vars['setpoint_type'].set('pmv')
    assert tab.zone_combo.instate(['disabled']) and tab.form()['zone_arguments'] == []
    tab.vars['setpoint_type'].set('temperature')
    assert not tab.zone_combo.instate(['disabled']) and not tab.zone_combo.instate(['readonly'])
    tab.zone_tree.selection_set(tab.zone_tree.get_children())
    tab.remove_zones()
    assert tab.zone_rows() == []
    # Finding the zones needs a selected input IDF
    tab.idf_list.selection_clear(0, 'end')
    assert tab.find_zones() is False and app.errors[-1] == 'Select an input IDF first.'


def test_the_tab_of_the_apmv_setpoints(app, tmp_path):
    (tmp_path / 'model.idf').write_text('')
    app.folder.set(str(tmp_path))
    tab = app.apmv

    assert tab.vars['idf'].get() == 'model.idf'
    assert forms.apmv_arguments(tab.form()) == forms.apmv_arguments(_apmv_form(tmp_path))
    tab.vars['add_vrf_system'].set(False)
    tab.update_state()
    assert tab.supply_air.instate(['disabled'])
    tab.vars['pmv_cooling_setpoint'].set('x')
    assert tab.apply() is False and "'x' is not a number" in app.errors[-1]


def test_the_tab_of_rename_epw_files(app, tmp_path, monkeypatch):
    from accim.gui import tasks

    for name in ('a.epw', 'b.epw'):
        (tmp_path / name).write_text('')
    app.folder.set(str(tmp_path))
    tab = app.rename_epws
    tab.cities.insert('1.0', 'a = Sevilla')

    form = tab.form()
    assert form['epws'] == ['a.epw', 'b.epw']
    assert forms.rename_epws_arguments(form)['rename_city_dict'] == {'a': 'Sevilla'}
    # The task answers the questions of rename_epw_files that the interface knows, and stops at the others
    captured = {}
    monkeypatch.setattr(app, 'run_task', lambda title, folder, function, on_done=None, answers=None:
                        captured.update(answers=answers) or True)
    app.answers = [True]
    assert tab.rename() and captured['answers'] == tasks.RENAME_EPWS_ANSWERS

    def task():
        print('answers', [input('\nIf any of the city or subcountry names needs some amendment (...): '),
                          input('\nIf you want to exclude some EPWs from renaming, (...): ')])
        input('Please enter the city or subcountry: ')

    app.execute('Rename the EPWs', str(tmp_path), task, answers=tasks.RENAME_EPWS_ANSWERS)
    app.process_messages()
    assert "answers ['', '']" in app.log.get('1.0', 'end')
    assert 'Please enter the city or subcountry' in app.errors[-1]


def test_the_tab_of_table(app, tmp_path, monkeypatch):
    from accim.gui import tasks

    (tmp_path / 'model.idf').write_text('')
    (tmp_path / 'model[CS_INT EN16798[CA_3[Seville.csv').write_text('')
    app.folder.set(str(tmp_path))
    tab = app.table

    assert tab.vars['idf_path'].get() == 'model.idf' and tab.summary.get().startswith('1 CSV files')
    assert forms.table_arguments(tab.form())['table']['datasets'] == ['model[CS_INT EN16798[CA_3[Seville.csv']
    assert tab.make_figure() is False and app.errors[-1] == 'Make the table first.'
    table = SimpleNamespace(
        df=pd.DataFrame({'ComfMod': ['CM_0', 'CM_3'], 'EPW': ['A', 'A'], 'Cooling (kWh/m2)': [1.0, 2.0],
                         'RMOT (C)': [10.0, 20.0]}),
        cols_for_multiindex=['ComfMod', 'EPW'], val_cols=['Cooling (kWh/m2)', 'RMOT (C)'],
        suggested_vars_dict={'ComfMod': ['CM_0', 'CM_3']})
    tab.show_table(table)
    assert len(tab.tree.get_children()) == 2 and 'ComfMod: CM_0, CM_3' in tab.summary.get()
    tab.rows_list.selection_set(0)
    tab.cols_list.selection_set(1)
    tab.y_list.selection_set(0)
    kwargs = forms.figure_arguments(tab.form())['kwargs']
    assert (kwargs['vars_to_gather_rows'], kwargs['vars_to_gather_cols']) == (['ComfMod'], ['EPW'])
    assert kwargs['data_on_x_axis'] == 'Cooling (kWh/m2)'
    assert kwargs['data_on_y_main_axis'] == [['Value', ['Cooling (kWh/m2)']]]
    # The task of the figure answers its questions (whether to rename the rows and the columns of the subplots)
    captured = {}
    monkeypatch.setattr(app, 'run_task', lambda title, folder, function, on_done=None, answers=None:
                        captured.update(answers=answers) or True)
    assert tab.make_figure() and captured['answers'] == tasks.FIGURE_ANSWERS
    tab.vars['figure_type'].set('time')
    assert tab.x_combo.instate(['disabled'])


def test_the_tab_of_the_parametric_study(app, tmp_path):
    for name in ('model.idf', 'a.epw'):
        (tmp_path / name).write_text('')
    app.folder.set(str(tmp_path))
    tab = app.parametric

    assert tab.samples_entry.instate(['disabled'])
    assert all(widget.instate(['disabled']) for widget in tab.existing_hvac_widgets)
    tab.vars['script_type'].set('ex_ac')
    assert not any(widget.instate(['disabled']) for widget in tab.existing_hvac_widgets)
    assert str(tab.availability_combo.cget('state')) == 'normal'
    tab.vars['existing_hvac_radiant_setpoints'].set(False)
    assert forms.parametric_arguments(dict(tab.form(), parameters=[('category', '1')]))['existing_hvac'][
        'existing_hvac_radiant_setpoints'] is False
    tab.vars['script_type'].set('vrf_mm')
    tab.parameter_name.set('comfort_standard')
    tab.parameter_values.set('1, 2')
    assert tab.set_parameter()
    tab.parameter_values.set('1 to 2')
    assert tab.set_parameter() and tab.parameter_rows() == [('comfort_standard', '1 to 2')]
    assert tab.run() is False and 'the full set needs options' in app.errors[-1]
    tab.parameter_values.set('one')
    assert not tab.set_parameter() and "'one' is not a number" in app.errors[-1]
    tab.vars['parameters_type'].set('accim custom model')
    assert tab.parameter_name.get() == forms.CUSTOM_MODEL_PARAMETERS[0]
    tab.vars['sampling'].set('lhs')
    assert not tab.samples_entry.instate(['disabled'])
    form = tab.form()
    assert (form['idf'], form['epws']) == ('model.idf', ['a.epw'])
    with pytest.raises(FormError, match="'comfort_standard' is not a parameter of the accim custom model"):
        forms.parametric_arguments(form)
    tab.show_results(pd.DataFrame({'custom_slope': [0.3, 0.4], 'Heating:Electricity': [1.0, 2.0]}))
    assert len(tab.tree.get_children()) == 2 and tab.count.get().startswith('2 simulations')
