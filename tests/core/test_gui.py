"""Tests for the graphical user interface of accim (accim.gui).

The forms (accim.gui.forms) are tested without a display; the window (accim.gui.app) only where tkinter can open one
(the tests of the window are skipped otherwise, as on a server without a display). AddAccis runs with the arguments
of a form, to check that they are complete: the interface cannot answer the questions of the prompt.
"""
import builtins
import copy
import inspect
import json
import os
import re
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
        add_building_averages=False, debug_ems=False, name_suffix='', confirm=True, verbose=True,
        vrf_availability_schedule='On 24/7', vrf_eer=2, vrf_cop=2.1, comfort_standard=[1], category=[3],
        comfort_mode=[3], category_cooling_offset=0, category_heating_offset=0, setpoint_accuracy=10000,
        cooling_season_start=121, cooling_season_end=274, hvac_mode=[2], ventilation_control=[0],
        ventilation_setpoint_offset=[0], min_outdoor_temp_offset=[50], max_wind_speed=[50],
        opening_factor_max_temp_diff=6, opening_factor_min_temp_diff=1, min_opening_factor=0.25,
        setpoint_tolerance_start=0.1, setpoint_tolerance_end=0.1, setpoint_tolerance_step=0.1)
    assert forms.output_idf_count(arguments) == 1
    # The defaults of the form are those of AddAccis
    from accim.sim.accis import AddAccis

    parameters = inspect.signature(AddAccis).parameters
    for name in ('vrf_availability_schedule', 'vrf_eer', 'vrf_cop', 'category_cooling_offset',
                 'category_heating_offset', 'setpoint_accuracy', 'debug_ems', 'add_building_averages'):
        assert arguments[name] == parameters[name].default, name


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
    (dict(vrf_eer='0'), 'vrf_eer: enter a number greater than 0'),
    (dict(vrf_cop='-1'), 'vrf_cop: enter a number greater than 0'),
    (dict(vrf_availability_schedule=' '), 'vrf_availability_schedule: enter the name of a schedule'),
    (dict(vrf_availability_schedule='On; 24/7'), 'vrf_availability_schedule: enter the name of a schedule'),
    (dict(setpoint_accuracy='0'), 'setpoint_accuracy: enter a number greater than 0'),
    (dict(category_cooling_offset='x'), "category_cooling_offset: 'x' is not a number"),
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


def test_arguments_of_the_size_of_the_results(tmp_path):
    from accim.run import estimate_results_size

    form = dict(forms.RUN_DEFAULTS, folder=str(tmp_path))

    assert forms.results_size_arguments(form) == dict(simulate=False, only_accim_idfs=True, processes=2)
    assert forms.results_size_arguments(dict(form, simulate=True, only_accim_idfs=False)) == dict(
        simulate=True, only_accim_idfs=False, processes=2)
    assert inspect.signature(estimate_results_size).parameters['simulate'].default is False
    with pytest.raises(FormError, match='processes'):
        forms.results_size_arguments(dict(form, processes='0'))


def test_the_task_of_the_size_of_the_results(monkeypatch):
    import accim.run
    from accim.gui import tasks

    table = pd.DataFrame({'idf': ['a.idf', 'b.idf'], 'simulations': [2, 2], 'total_mb': [60.0, 60.0],
                          'total_kept_mb': [50.0, 50.0]})
    received = []
    monkeypatch.setattr(accim.run, 'estimate_results_size', lambda **kwargs: received.append(kwargs) or table)

    result, sentence = tasks.results_size(dict(simulate=False, only_accim_idfs=True, processes=2))

    assert result is table and received == [dict(simulate=False, only_accim_idfs=True, processes=2)]
    assert sentence == ('The results of the 2 IDFs with the 2 EPWs of the folder (estimated from their outputs): '
                        '120.0 MB, 100.0 MB after "Remove the simulation files".')


def test_the_zones_of_the_hours_within_the_setpoints():
    assert forms.hours_zones(' Building ') == 'building' and forms.hours_zones('all') == 'all'
    assert forms.hours_zones('Zone1, zone2;') == ['Zone1', 'zone2']
    with pytest.raises(FormError, match='enter building, all, or the zones'):
        forms.hours_zones(' , ')


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


def test_the_other_arguments_of_add_accis(tmp_path):
    arguments = forms.add_accis_arguments(_form(
        tmp_path, vrf_availability_schedule=' Office Hours ', vrf_eer='3.2', vrf_cop='4', category_cooling_offset='0.5',
        category_heating_offset='-0.5', setpoint_accuracy='2', debug_ems=True))

    assert {name: arguments[name] for name in ('vrf_availability_schedule', 'vrf_eer', 'vrf_cop',
                                               'category_cooling_offset', 'category_heating_offset',
                                               'setpoint_accuracy', 'debug_ems')} == dict(
        vrf_availability_schedule='Office Hours', vrf_eer=3.2, vrf_cop=4, category_cooling_offset=0.5,
        category_heating_offset=-0.5, setpoint_accuracy=2, debug_ems=True)
    # The VRF systems only with their script types
    arguments = forms.add_accis_arguments(_form(tmp_path, script_type='ex_ac', vrf_eer='0'))
    assert not any(name.startswith('vrf_') for name in arguments)


def test_the_fields_of_the_table_of_the_zones():
    fields = {'comfort_standard': '2 = INT ASHRAE55', 'category': '80', 'comfort_mode': '',
              'hvac_mode': '0 = Full air-conditioning', 'ventilation_control': ''}

    text = forms.zone_row_text(fields, ' cooling_season_start=01/06 ', 'Zone1')

    assert text == 'comfort_standard=2, category=80, hvac_mode=0, cooling_season_start=01/06'
    assert forms.split_zone_arguments(text) == (fields, 'cooling_season_start=01/06')
    assert forms.zone_row_text({}, 'comfort_mode=3') == 'comfort_mode=3'
    with pytest.raises(FormError, match='category is given twice'):
        forms.zone_row_text({'category': '80'}, 'category=90')
    with pytest.raises(FormError, match='give at least one argument'):
        forms.zone_row_text({'category': ''}, '')
    # The choices: the categories and comfort modes of the comfort standard of the zone, or of all of them
    assert forms.zone_field_choices('category', '2 = INT ASHRAE55') == ['', '80', '90']
    assert forms.zone_field_choices('comfort_mode', '22') == ['', '0']
    assert forms.zone_field_choices('category')[:4] == ['', '1', '2', '3']
    assert forms.zone_field_choices('comfort_standard')[:2] == ['', '0 = ESP CTE']
    assert forms.zone_field_choices('hvac_mode') == ['', '0 = Full air-conditioning', '1 = Natural ventilation only',
                                                     '2 = Mixed mode']
    with pytest.raises(KeyError):
        forms.zone_field_choices('setpoint_tolerance')


def test_the_arguments_of_the_zones_are_checked_with_the_output_idfs(tmp_path):
    # ASHRAE 55 has no category 3, the category of the output IDF
    with pytest.raises(FormError, match=r'Zone1: category 3 is not a category of comfort_standard 2 \(valid: \[80, '
                                        r'90\]\) \(in 1 output IDF, such as model\[CS_INT EN16798\[CA_3'):
        forms.add_accis_arguments(_form(tmp_path, zone_arguments=[('Zone1', 'comfort_standard=2')]))
    arguments = forms.add_accis_arguments(_form(tmp_path, category='1 2 3',
                                                zone_arguments=[('Zone1', 'comfort_standard=2, category=80')]))
    assert forms.zone_arguments_problems(arguments) == []
    assert forms.zone_arguments_problems(forms.add_accis_arguments(_form(tmp_path))) == []
    # The arguments of mixed mode only with vrf_mm and ex_mm
    with pytest.raises(FormError, match='hvac_mode 2 is not valid with this script type'):
        forms.add_accis_arguments(_form(tmp_path, script_type='vrf_ac', zone_arguments=[('Zone1', 'hvac_mode=2')]))
    # The same problem in several output IDFs is given once
    arguments = forms.add_accis_arguments(_form(tmp_path, setpoint_tolerance_end='0.3'))
    problems = forms.zone_arguments_problems(dict(arguments, zone_arguments={'Zone1': {'comfort_standard': 2}}))
    assert len(problems) == 1 and '(in 3 output IDFs, such as model[CS_INT EN16798[CA_3[CM_3' in problems[0]


def test_the_ems_code_of_the_setpoints_of_the_form(tmp_path):
    from accim.gui import tasks

    form = _form(tmp_path, comfort_standard=[0, 2, 99], category='3 80', comfort_mode='3',
                 zone_arguments=[('Zone1', 'comfort_standard=1, category=2'), ('Zone2', 'setpoint_tolerance=0.2')])

    calls = forms.setpoint_ems_code_calls(form)

    # The category and comfort mode of the form if a comfort standard has only one of them; otherwise all
    assert [title for title, _ in calls] == [
        '0 = ESP CTE: category (all), comfort mode (all)', '2 = INT ASHRAE55: category 80, comfort mode 3',
        '99 = CUSTOM: category (all), comfort mode 3', 'Zone Zone1, 1 = INT EN16798: category 2, comfort mode 3']
    kwargs = dict(calls)
    assert kwargs['99 = CUSTOM: category (all), comfort mode 3']['custom_slope'] == 0.31
    ashrae = kwargs['2 = INT ASHRAE55: category 80, comfort mode 3']
    assert 'custom_slope' not in ashrae and ashrae['setpoint_tolerance'] == 0.1 and ashrae['setpoint_accuracy'] == 10000
    text = tasks.setpoint_ems_code(calls)
    assert all(title in text for title, _ in calls) and 'ComfStand' in text
    assert '! No EMS code: comfort_standard 21 has no setpoints with comfort_mode 0' in tasks.setpoint_ems_code(
        [('CHL', dict(comfort_standard=21, category=80, comfort_mode=0))])
    with pytest.raises(FormError, match='the EMS code of the setpoints is that of the adaptive setpoint temperatures'):
        forms.setpoint_ems_code_calls(_form(tmp_path, setpoint_type='pmv'))


def test_the_outdoor_metric_of_the_custom_model_in_the_form(tmp_path):
    from accim.sim.ems.outdoor_metric import OUTDOOR_METRICS

    # The metrics of the list are those of accim, in the order of their codes
    assert list(forms.CUSTOM_OUTDOOR_METRICS) == list(OUTDOOR_METRICS)
    # Only with the custom model; 'pmot' and the defaults of AddAccis by default, without a weather file
    assert 'custom_outdoor_metric' not in forms.add_accis_arguments(_form(tmp_path))
    arguments = forms.add_accis_arguments(_form(tmp_path, comfort_standard=[99]))
    assert {name: arguments[name] for name in ('custom_outdoor_metric', 'custom_alpha', 'custom_days')} == dict(
        custom_outdoor_metric='pmot', custom_alpha=0.8, custom_days=30)
    assert 'epw' not in arguments
    from accim.sim.accis import AddAccis

    parameters = inspect.signature(AddAccis).parameters
    assert all(arguments[name] == parameters[name].default
               for name in ('custom_outdoor_metric', 'custom_alpha', 'custom_days'))
    # The weather file, relative to the folder
    (tmp_path / 'weather.epw').write_text('')
    arguments = forms.add_accis_arguments(_form(tmp_path, comfort_standard=[99], custom_outdoor_metric='monthly_mean',
                                                epw='weather.epw', custom_alpha='0.7', custom_days='7'))
    assert (arguments['custom_outdoor_metric'], arguments['custom_alpha'], arguments['custom_days']) == (
        'monthly_mean', 0.7, 7)
    assert arguments['epw'] == os.path.join(str(tmp_path), 'weather.epw')
    for values, message in ((dict(custom_outdoor_metric='monthly_mean'), "epw: the outdoor metric 'monthly_mean'"),
                            (dict(epw='missing.epw'), 'is not a file'),
                            (dict(custom_outdoor_metric='weekly'), 'custom_outdoor_metric: choose one of'),
                            (dict(custom_alpha='1.5'), 'custom_alpha: enter a number between 0 and 1'),
                            (dict(custom_days='7.5'), 'custom_days: enter an integer')):
        with pytest.raises(FormError, match=message):
            forms.add_accis_arguments(_form(tmp_path, comfort_standard=[99], **values))
    # In the table of the zones, by name or by code
    assert forms.parse_zone_arguments('custom_outdoor_metric=rmot_alpha, custom_alpha=0.7') == dict(
        custom_outdoor_metric='rmot_alpha', custom_alpha=0.7)
    assert forms.parse_zone_arguments('custom_outdoor_metric=5') == dict(custom_outdoor_metric='ndrm')
    with pytest.raises(FormError, match="'weekly' is not an outdoor metric of the custom model"):
        forms.parse_zone_arguments('custom_outdoor_metric=weekly')
    # The EMS code of the form, with the outdoor metric of the custom model only
    calls = dict(forms.setpoint_ems_code_calls(_form(tmp_path, comfort_standard=[1, 99], category='2',
                                                     custom_outdoor_metric='rmot_alpha')))
    custom = next(kwargs for title, kwargs in calls.items() if title.startswith('99'))
    en16798 = next(kwargs for title, kwargs in calls.items() if title.startswith('1 '))
    assert custom['custom_outdoor_metric'] == 'rmot_alpha' and 'custom_outdoor_metric' not in en16798
    from accim.gui import tasks

    assert '! --- SetOutdoorMetric_<zone>: the outdoor metric of the zone, Tout_metric ---' in tasks.setpoint_ems_code(
        [('99', custom)])


def test_the_floor_and_ceiling_of_the_setpoints_in_the_form(tmp_path):
    from accim.constants import EN16798_TABLE_B2
    from accim.gui import tasks

    # None by default (empty fields), as in AddAccis
    arguments = forms.add_accis_arguments(_form(tmp_path))
    assert not {'heating_setpoint_floor', 'cooling_setpoint_ceiling', 'report_hours_below'} & set(arguments)
    # The choices of Table B.2 of EN 16798-1 are its values
    assert list(forms.EN16798_TABLE_B2_CHOICES.values()) == list(EN16798_TABLE_B2.values())
    assert forms.EN16798_TABLE_B2_CHOICES['Residential, category II: 20.0 / 26.0 °C'] == (20.0, 26.0)
    arguments = forms.add_accis_arguments(_form(tmp_path, heating_setpoint_floor='20', cooling_setpoint_ceiling=' 26 ',
                                                report_hours_below='18, 17.5 16'))
    assert (arguments['heating_setpoint_floor'], arguments['cooling_setpoint_ceiling']) == (20, 26)
    assert arguments['report_hours_below'] == [18, 17.5, 16]
    arguments = forms.add_accis_arguments(_form(tmp_path, cooling_setpoint_ceiling='25.5'))
    assert arguments['cooling_setpoint_ceiling'] == 25.5 and 'heating_setpoint_floor' not in arguments
    # The occupied hours below some temperatures also with the PMV-based setpoints, which have no floor nor ceiling
    arguments = forms.add_accis_arguments(_form(tmp_path, setpoint_type='pmv', report_hours_below='18'))
    assert arguments['report_hours_below'] == [18]
    for values, message in ((dict(heating_setpoint_floor='27', cooling_setpoint_ceiling='26'), 'must be lower than'),
                            (dict(heating_setpoint_floor='x'), "heating_setpoint_floor: 'x' is not a number"),
                            (dict(setpoint_type='pmv', cooling_setpoint_ceiling='26'), 'PMV-based setpoints have '
                                                                                       'neither floor nor ceiling'),
                            (dict(report_hours_below='18 18'), 'repeated temperatures')):
        with pytest.raises(FormError, match=message):
            forms.add_accis_arguments(_form(tmp_path, **values))
    # In the table of the zones, and in the EMS code of the form and of the zones
    assert forms.parse_zone_arguments('heating_setpoint_floor=21, cooling_setpoint_ceiling=25.5') == dict(
        heating_setpoint_floor=21, cooling_setpoint_ceiling=25.5)
    calls = dict(forms.setpoint_ems_code_calls(_form(
        tmp_path, category='2', heating_setpoint_floor='20', report_hours_below='18',
        zone_arguments=[('Zone1', 'comfort_standard=2, category=80, cooling_setpoint_ceiling=25')])))
    en16798, zone = (next(kwargs for title, kwargs in calls.items() if title.startswith(start))
                     for start in ('1 ', 'Zone Zone1'))
    assert en16798['heating_setpoint_floor'] == 20 and 'cooling_setpoint_ceiling' not in en16798
    assert (zone['heating_setpoint_floor'], zone['cooling_setpoint_ceiling']) == (20, 25)
    assert 'report_hours_below' not in en16798
    text = tasks.setpoint_ems_code([('1', en16798)])
    assert '! --- ApplySetpointLimits_<zone>' in text and 'set AHST = AHSTfloor' in text
    assert 'set ACST = ACSTceil' not in text


def test_the_regimes_of_the_custom_model_in_the_form(tmp_path):
    from accim.gui import tasks
    from accim.sim.arguments import CustomRegime

    text = 'metric_below 10: 0.31 17.8 3.5 -3.5 10 33.5 10 33.5;\n Always: 0.33, 18.8, 2, -3, 10, 30, 10, 30'
    regimes = [CustomRegime(0.31, 17.8, 3.5, -3.5, 10, 33.5, 10, 33.5, ('metric_below', 10)),
               CustomRegime(0.33, 18.8, 2, -3, 10, 30, 10, 30)]
    assert forms.parse_custom_regimes(text) == regimes
    assert forms.parse_custom_regimes(' ') == [] and forms.parse_custom_regimes(None) == []
    assert forms.parse_custom_regimes('metric_between -2 7.5: 0.3 17 2 -2 10 30 10 30\nhvac_off: 1 2 3 -3 4 5 6 7') == [
        CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, ('metric_between', (-2, 7.5))),
        CustomRegime(1, 2, 3, -3, 4, 5, 6, 7, 'hvac_off')]
    for wrong, message in (('0.31 17.8 3.5 -3.5 10 33.5 10 33.5', 'as its condition, a colon and its 8 coefficients'),
                           ('winter: 0.31 17.8 3.5 -3.5 10 33.5 10 33.5', "'winter' \\(regime 1\\) is not a condition"),
                           ('metric_below: 0.31 17.8 3.5 -3.5 10 33.5 10 33.5', 'is not a condition'),
                           ('always 3: 0.31 17.8 3.5 -3.5 10 33.5 10 33.5', 'is not a condition'),
                           ('always: 0.31 17.8', 'the regime 1 needs 8 coefficients'),
                           ('metric_between 20 10: 1 2 3 -3 4 5 6 7', 'regime 1: The condition .metric_between.'),
                           ('always: 1 2 3 -3 4 5 6 7; cooling_season: 1 2 3 -3 4 5 6 7', 'only the last regime'),
                           ('metric_above x: 1 2 3 -3 4 5 6 7', "custom_regimes: 'x' is not a number")):
        with pytest.raises(FormError, match=message):
            forms.parse_custom_regimes(wrong)
    # Only with the custom model, and none by default (an empty field), as in AddAccis
    assert 'custom_regimes' not in forms.add_accis_arguments(_form(tmp_path, comfort_standard=[99]))
    assert 'custom_regimes' not in forms.add_accis_arguments(_form(tmp_path, custom_regimes=text))
    arguments = forms.add_accis_arguments(_form(tmp_path, comfort_standard=[1, 99], custom_regimes=text))
    assert arguments['custom_regimes'] == regimes
    for values, message in ((dict(script_type='vrf_ac', custom_regimes='hvac_on: 1 2 3 -3 4 5 6 7'),
                             'the conditions hvac_off and hvac_on need mixed mode'),
                            (dict(setpoint_type='pmv', custom_regimes=text), 'do not use the custom model')):
        with pytest.raises(FormError, match=message):
            forms.add_accis_arguments(_form(tmp_path, comfort_standard=[99], **values))
    # The EMS code of the form: the regimes of the custom model only, with the script type
    calls = dict(forms.setpoint_ems_code_calls(_form(tmp_path, comfort_standard=[1, 99], category='2',
                                                     custom_regimes=f'hvac_off: 1 2 3 -3 4 5 6 7; {text}')))
    custom = next(kwargs for title, kwargs in calls.items() if title.startswith('99'))
    en16798 = next(kwargs for title, kwargs in calls.items() if title.startswith('1 '))
    assert custom['custom_regimes'][1:] == regimes and custom['script_type'] == 'vrf_mm'
    assert 'custom_regimes' not in en16798 and 'script_type' not in en16798
    text = tasks.setpoint_ems_code([('99', custom)])
    assert ('! --- SelectCustomRegime_<zone>: the regime of the custom model of the timestep (1 = hvac_off, '
            '2 = metric_below 10, 3 = always), which sets its inputs ---') in text
    assert 'if <zone>_CoolCoil==0' in text.split('\n')


def _apmv_form(folder, **values):
    return dict(dict(forms.APMV_DEFAULTS, folder=str(folder), idf='model.idf'), **values)


def test_arguments_of_the_apmv_setpoints(tmp_path):
    (tmp_path / 'model.idf').write_text('')

    arguments = forms.apmv_arguments(_apmv_form(tmp_path))

    assert arguments == dict(
        idf='model.idf', output_idf='model_aPMV.idf', index='apmv', energyplus_version='auto', add_vrf_system=True,
        supply_air_temp_input_method='temperature difference', always_occupied=False,
        apmv=dict(output_frequencies=['hourly'], other_pmv_related_outputs=True, adaptive_coefficient_cooling=0.293,
                  adaptive_coefficient_heating=-0.293, pmv_cooling_setpoint=0.5, pmv_heating_setpoint=-0.5,
                  cooling_setpoint_tolerance_cooling_season=-0.1, cooling_setpoint_tolerance_heating_season=-0.1,
                  heating_setpoint_tolerance_cooling_season=0.1, heating_setpoint_tolerance_heating_season=0.1,
                  cooling_season_start=121, cooling_season_end=274, verbose=True, adaptive_coefficient_by='season'),
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


def test_the_apmv_setpoints_of_each_zone(tmp_path):
    (tmp_path / 'model.idf').write_text('')
    rows = [('Block1:Zone1', 'pmv_cooling_setpoint=0.7, cooling_setpoint_tolerance_cooling_season=-0.2'),
            ('Block1:Zone2', 'adaptive_coefficient_cooling=0.3')]

    apmv = forms.apmv_arguments(_apmv_form(tmp_path, zone_setpoints=rows))['apmv']

    # The setpoints that some zones change are dictionaries, with the value of the form for the other zones
    assert apmv['pmv_cooling_setpoint'] == {'Block1:Zone1': 0.7} and apmv['default_pmv_cooling_setpoint'] == 0.5
    assert apmv['cooling_setpoint_tolerance_cooling_season'] == {'Block1:Zone1': -0.2}
    assert apmv['default_cooling_setpoint_tolerance_cooling_season'] == -0.1
    assert apmv['adaptive_coefficient_cooling'] == {'Block1:Zone2': 0.3}
    assert apmv['default_adaptive_coefficient_cooling'] == 0.293
    assert apmv['pmv_heating_setpoint'] == -0.5 and 'default_pmv_heating_setpoint' not in apmv
    fields = {'adaptive_coefficient_cooling': '', 'adaptive_coefficient_heating': '', 'pmv_cooling_setpoint': '0.7',
              'pmv_heating_setpoint': '', 'expectancy_factor': ''}
    text = forms.apmv_zone_row_text(fields, 'cooling_setpoint_tolerance_cooling_season=-0.2')
    assert text == rows[0][1]
    assert forms.split_apmv_zone_setpoints(text) == (fields, 'cooling_setpoint_tolerance_cooling_season=-0.2')
    with pytest.raises(FormError, match="'activity_level' is not a PMV-based setpoint of a zone"):
        forms.apmv_arguments(_apmv_form(tmp_path, zone_setpoints=[('Z', 'activity_level=100')]))
    with pytest.raises(FormError, match="the zone 'z' is given twice"):
        forms.apmv_arguments(_apmv_form(tmp_path, zone_setpoints=[('Z', 'pmv_cooling_setpoint=1'),
                                                                  ('z', 'pmv_cooling_setpoint=1')]))


def test_the_epmv_and_pmv_setpoints_of_the_form(tmp_path):
    from accim.sim.apmv import apply_epmv_setpoints

    (tmp_path / 'model.idf').write_text('')

    arguments = forms.apmv_arguments(_apmv_form(tmp_path, index='epmv'))
    # Only the setpoints of the ePMV, with its options; the defaults of the form are those of apply_epmv_setpoints
    assert arguments['index'] == 'epmv' and arguments['output_idf'] == 'model_ePMV.idf'
    apmv = arguments['apmv']
    assert 'adaptive_coefficient_cooling' not in apmv and 'adaptive_coefficient_heating' not in apmv
    defaults = inspect.signature(apply_epmv_setpoints).parameters
    for name in ('expectancy_factor', 'pmv_cooling_setpoint', 'apply_to_heating', 'metabolic_correction',
                 'heating_setpoint_tolerance_heating_season', 'cooling_season_start'):
        assert apmv[name] == defaults[name].default, name
    apmv = forms.apmv_arguments(_apmv_form(tmp_path, index='epmv', metabolic_correction=True,
                                           zone_setpoints=[('Block1:Zone1', 'expectancy_factor=0.6')]))['apmv']
    assert apmv['metabolic_correction'] is True and apmv['apply_to_heating'] is False
    assert apmv['expectancy_factor'] == {'Block1:Zone1': 0.6} and apmv['default_expectancy_factor'] == 0.8

    arguments = forms.apmv_arguments(_apmv_form(tmp_path, index='pmv'))
    assert arguments['output_idf'] == 'model_PMV.idf'
    assert not {'adaptive_coefficient_cooling', 'expectancy_factor', 'metabolic_correction'} & set(arguments['apmv'])
    # The forms of the sessions of accim 1.1.0 have no index: the aPMV
    form = _apmv_form(tmp_path)
    del form['index']
    assert forms.apmv_arguments(form)['index'] == 'apmv'


@pytest.mark.parametrize('values, message', [
    (dict(index='athb'), "index: choose one of"),
    (dict(index='epmv', expectancy_factor='0.4'), 'expectancy_factor: 0.4 is not between 0.5 and 1.0'),
    (dict(index='epmv', zone_setpoints=[('Z', 'expectancy_factor=1.2')]), '1.2 is not between 0.5 and 1.0'),
    (dict(index='epmv', zone_setpoints=[('Z', 'adaptive_coefficient_cooling=0.3')]),
     r"zone_setpoints of 'Z': \['adaptive_coefficient_cooling'\] are not setpoints of the ePMV"),
    (dict(index='apmv', zone_setpoints=[('Z', 'expectancy_factor=0.7')]), 'are not setpoints of the aPMV'),
    (dict(index='pmv', zone_setpoints=[('Z', 'expectancy_factor=0.7')]), 'are not setpoints of the PMV'),
])
def test_wrong_arguments_of_the_epmv_and_pmv_setpoints(tmp_path, values, message):
    (tmp_path / 'model.idf').write_text('')
    with pytest.raises(FormError, match=message):
        forms.apmv_arguments(_apmv_form(tmp_path, **values))


def test_the_indices_of_the_form_are_those_of_accim():
    from accim.sim import apmv
    from accim.sim.pmv_index import PMV_INDICES

    assert set(forms.PMV_INDEX_FUNCTIONS) == set(PMV_INDICES) == set(forms.PMV_INDEX_NAMES)
    for index, pmv_index in PMV_INDICES.items():
        assert forms.PMV_INDEX_NAMES[index] == pmv_index.name
        assert forms.PMV_INDEX_PARAMETERS[index] == tuple(p.argument for p in pmv_index.parameters)
        function = getattr(apmv, forms.PMV_INDEX_FUNCTIONS[index])
        assert set(forms.index_setpoint_fields(index)) <= set(inspect.signature(function).parameters)
    assert set(forms.EPMV_OPTIONS) == set(PMV_INDICES['epmv'].options)
    assert set(forms.APMV_OPTIONS) == set(PMV_INDICES['apmv'].options)
    from accim.sim.pmv_index import ADAPTIVE_COEFFICIENT_BY
    assert forms.ADAPTIVE_COEFFICIENT_BY == ADAPTIVE_COEFFICIENT_BY


def test_the_adaptive_coefficients_of_the_form(tmp_path):
    from accim.constants import APMV_ADAPTIVE_COEFFICIENTS

    (tmp_path / 'model.idf').write_text('')
    apmv = forms.apmv_arguments(_apmv_form(tmp_path, adaptive_coefficient_by='pmv_sign'))['apmv']
    assert apmv['adaptive_coefficient_by'] == 'pmv_sign'
    assert 'adaptive_coefficient_by' not in forms.apmv_arguments(_apmv_form(tmp_path, index='epmv'))['apmv']
    with pytest.raises(FormError, match='adaptive_coefficient_by: choose one of'):
        forms.apmv_arguments(_apmv_form(tmp_path, adaptive_coefficient_by='sign'))
    # The catalogue fills the fields of the coefficients
    assert forms.adaptive_coefficient_choices() == [''] + list(APMV_ADAPTIVE_COEFFICIENTS)
    assert forms.adaptive_coefficient_entry('') == ('', '', '')
    cooling, heating, description = forms.adaptive_coefficient_entry('gbt50785_cold_general')
    assert (cooling, heating) == ('0.24', '-0.5') and 'GB/T 50785-2012' in description
    assert description.endswith('grade standard.')
    cooling, heating, description = forms.adaptive_coefficient_entry('zhang2024_Aw')
    assert (cooling, heating) == ('0.36', '') and 'grade literature: check the coefficients' in description
    assert 'no coefficient for heating' in description
    with pytest.raises(FormError, match="'Aw' is not in the catalogue"):
        forms.adaptive_coefficient_entry('Aw')


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


def test_the_long_term_discomfort_indicators_of_the_table_form(tmp_path):
    for name in ('model.idf', 'model[CS_INT EN16798[CA_3[Seville.csv'):
        (tmp_path / name).write_text('')
    form = dict(forms.TABLE_DEFAULTS, folder=str(tmp_path), idf_path='model.idf')
    # Not by default (the arguments of Table are those of before)
    assert 'long_term_indicators' not in forms.table_arguments(form)['table']
    table = forms.table_arguments(dict(form, frequency='hourly', long_term_indicators=True))['table']
    assert table['long_term_indicators'] is True and table['frequency'] == 'hourly'
    with pytest.raises(FormError, match="long_term_indicators: the indicators need a table of timesteps or hours"):
        forms.table_arguments(dict(form, long_term_indicators=True))


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
    # The inputs of the PMV are set before the setpoints (the metabolic correction of the ePMV reads them)
    assert [call[0] for call in calls] == ['load', 'set_zones_always_occupied', 'add_vrf_system',
                                           'set_pmv_input_parameters', 'apply_apmv_setpoints']
    assert calls[2][1] == {'supply_air_temp_input_method': 'temperature difference'}
    assert calls[3][1] == {'air_velocity': 0.2} and calls[4][1] == arguments['apmv']


@needs_energyplus
def test_the_apmv_setpoints_of_the_form_on_the_sample_model(tmp_path, monkeypatch):
    from accim.gui import tasks

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)

    assert tasks.apply_apmv(forms.apmv_arguments(_apmv_form(tmp_path))) == 'model_aPMV.idf'
    text = (tmp_path / 'model_aPMV.idf').read_text(encoding='latin-1')
    assert 'apply_aPMV_' in text and 'set_zone_input_data_' in text


def test_the_task_of_the_epmv_setpoints(tmp_path, monkeypatch):
    from accim.gui import tasks
    from accim.sim import accis, apmv

    calls, building = [], _Building()
    monkeypatch.setattr(accis, 'load_idf', lambda idf, version: building)
    for name in ('add_vrf_system', 'apply_apmv_setpoints', 'apply_epmv_setpoints', 'apply_pmv_setpoints'):
        monkeypatch.setattr(apmv, name, lambda b, _name=name, **kwargs: calls.append((_name, kwargs)))
    (tmp_path / 'model.idf').write_text('')

    for index, function in (('epmv', 'apply_epmv_setpoints'), ('pmv', 'apply_pmv_setpoints')):
        arguments = forms.apmv_arguments(_apmv_form(tmp_path, index=index))
        assert tasks.apply_apmv(arguments) == arguments['output_idf'] == building.saved
        assert calls[-1] == (function, arguments['apmv'])


@needs_energyplus
def test_the_epmv_setpoints_with_the_metabolic_correction_on_the_sample_model(tmp_path, monkeypatch):
    from accim.gui import tasks

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)

    # The activity level of the form is that which the metabolic correction reduces
    assert tasks.apply_apmv(forms.apmv_arguments(_apmv_form(tmp_path, index='epmv', metabolic_correction=True,
                                                            activity_level='110'))) == 'model_ePMV.idf'
    text = (tmp_path / 'model_ePMV.idf').read_text(encoding='latin-1')
    assert 'apply_ePMV_' in text and 'correct_activity_People_Block1_Zone1' in text
    assert re.search(r'Activity_base_People_Block1_Zone1,\s*!- Name\s*Sch_Act_People_Block1_Zone1,', text)


def test_the_zones_of_the_apmv_setpoints_get_their_keys_in_the_model(monkeypatch):
    from accim.gui import tasks
    from accim.sim import targets

    monkeypatch.setattr(targets, 'resolve_targets', lambda building: [
        SimpleNamespace(zone_name='Zone1', df_key='Zone1'), SimpleNamespace(zone_name='Zone2', df_key='Space2 People2')])

    # By the name of the zone or its key, in any case
    assert tasks.apmv_target_keys('BUILDING', {'pmv_cooling_setpoint': {'zone1': 0.7, 'ZONE2': 0.6},
                                               'adaptive_coefficient_cooling': {'space2 people2': 0.3}}) == {
        'pmv_cooling_setpoint': {'Zone1': 0.7, 'Space2 People2': 0.6},
        'adaptive_coefficient_cooling': {'Space2 People2': 0.3}}
    with pytest.raises(ValueError, match='Zone3 is not an occupied zone of model.idf: they are Zone1, Zone2'):
        tasks.apmv_target_keys('BUILDING', {'pmv_cooling_setpoint': {'Zone3': 0.7}}, 'model.idf')


@needs_energyplus
def test_the_apmv_setpoints_of_each_zone_on_the_sample_model(tmp_path, monkeypatch):
    import re

    from accim.gui import tasks

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)

    tasks.apply_apmv(forms.apmv_arguments(_apmv_form(tmp_path, zone_setpoints=[('block1:zone1',
                                                                                'pmv_cooling_setpoint=0.7')])))

    text = (tmp_path / 'model_aPMV.idf').read_text(encoding='latin-1')
    assert sorted(re.findall(r'set pmv_cooling_sp_(\w+) = ([-\d.]+)', text)) == [('Block1_Zone1', '0.7'),
                                                                                  ('Block1_Zone2', '0.5')]


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


def test_the_tasks_of_the_sessions(tmp_path, monkeypatch):
    from accim.gui import tasks
    from accim.utils import save_session

    monkeypatch.chdir(tmp_path)
    objects = {tasks.SESSION_FORMS: {'folder': str(tmp_path), 'run': {'processes': '3'}},
               'parametric_results': pd.DataFrame({'custom_slope': [0.3], 'Heating:Electricity': [1.0]})}

    paths = tasks.save_session(str(tmp_path / 'gui_session.pkl'), objects)

    assert paths == (str(tmp_path / 'gui_session.pkl'), str(tmp_path / 'gui_session.json'))
    session = tasks.open_session(paths[0])
    assert session[tasks.SESSION_FORMS] == objects[tasks.SESSION_FORMS]
    pd.testing.assert_frame_equal(session['parametric_results'], objects['parametric_results'])
    # The sessions saved in Python are not those of the interface
    save_session('python_session', csvs=['a.csv'])
    with pytest.raises(ValueError, match='is a session saved in Python, with csvs, not by the interface'):
        tasks.open_session(str(tmp_path / 'python_session.pkl'))


def test_the_tasks_that_save_and_open_tables(monkeypatch):
    import accim.data.postprocessing.main as postprocessing
    from accim.gui import tasks

    calls = []

    class FakeTable:
        type_of_table, custom_cols = 'custom', ['Cooling']

        def save(self, path):
            calls.append(('save', path))
            return 'table.pkl', 'table.json'

        def format_table(self, **kwargs):
            calls.append(('format_table', kwargs))

        @classmethod
        def load(cls, path):
            calls.append(('load', path))
            return cls()

    monkeypatch.setattr(postprocessing, 'Table', FakeTable)

    assert tasks.save_table(FakeTable(), 'table.pkl') == ('table.pkl', 'table.json')
    # The table that is opened gets the columns that it had (its rows may have been filtered by a figure)
    assert isinstance(tasks.open_table('table.pkl'), FakeTable)
    assert calls == [('save', 'table.pkl'), ('load', 'table.pkl'),
                     ('format_table', {'type_of_table': 'custom', 'custom_cols': ['Cooling']})]
    assert tasks.table_format(SimpleNamespace()) == {'type_of_table': 'all'}
    assert tasks.table_format(SimpleNamespace(type_of_table='energy demand', custom_cols=[])) == {
        'type_of_table': 'energy demand'}


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


def test_the_window_gives_the_outdoor_metric_of_the_custom_model(app, tmp_path, monkeypatch):
    from tkinter import filedialog

    (tmp_path / 'model.idf').write_text('')
    (tmp_path / 'weather.epw').write_text('')
    app.folder.set(str(tmp_path))
    tab = app.add_accis
    # Disabled without the custom model
    assert all(widget.instate(['disabled']) for widget in (tab.epw_entry, tab.epw_button))
    assert str(tab.metric_combo.cget('state')) == 'disabled'
    tab.standard_list.selection_set(len(tab.standards) - 1)
    tab.update_state()
    assert str(tab.metric_combo.cget('state')) == 'readonly' and not tab.epw_button.instate(['disabled'])
    assert list(tab.metric_combo.cget('values')) == list(forms.CUSTOM_OUTDOOR_METRICS)
    # The description of the metric chosen
    tab.vars['custom_outdoor_metric'].set('te_ref_nl')
    assert tab.metric_description.cget('text') == forms.CUSTOM_OUTDOOR_METRICS['te_ref_nl']
    monkeypatch.setattr(filedialog, 'askopenfilename', lambda **kwargs: str(tmp_path / 'weather.epw'))
    assert tab.choose_epw() is True
    arguments = forms.add_accis_arguments(tab.form())
    assert (arguments['custom_outdoor_metric'], arguments['epw']) == ('te_ref_nl', str(tmp_path / 'weather.epw'))


def test_the_window_gives_the_floor_and_ceiling_of_the_setpoints(app, tmp_path):
    (tmp_path / 'model.idf').write_text('')
    app.folder.set(str(tmp_path))
    tab = app.add_accis

    # The values of Table B.2 of EN 16798-1 fill both fields
    assert list(tab.table_b2_combo.cget('values')) == ['', *forms.EN16798_TABLE_B2_CHOICES]
    tab.table_b2.set('Office, category III: 19.0 / 27.0 °C')
    assert (tab.vars['heating_setpoint_floor'].get(), tab.vars['cooling_setpoint_ceiling'].get()) == ('19.0', '27.0')
    tab.vars['report_hours_below'].set('18 17')
    arguments = forms.add_accis_arguments(tab.form())
    assert (arguments['heating_setpoint_floor'], arguments['cooling_setpoint_ceiling']) == (19.0, 27.0)
    assert arguments['report_hours_below'] == [18, 17]
    # The PMV-based setpoints have neither floor nor ceiling: their fields are disabled and left out
    tab.vars['setpoint_type'].set('pmv')
    assert all(widget.instate(['disabled']) for widget in tab.limit_widgets[1:])
    assert str(tab.table_b2_combo.cget('state')) == 'disabled'
    arguments = forms.add_accis_arguments(tab.form())
    assert 'heating_setpoint_floor' not in arguments and arguments['report_hours_below'] == [18, 17]
    tab.vars['setpoint_type'].set('temperature')
    assert not tab.limit_widgets[1].instate(['disabled'])


def test_the_window_gives_the_regimes_of_the_custom_model(app, tmp_path):
    from accim.sim.arguments import CustomRegime

    (tmp_path / 'model.idf').write_text('')
    app.folder.set(str(tmp_path))
    tab = app.add_accis
    regimes = tab.custom_widgets[-1]
    # Disabled without the custom model
    assert regimes.instate(['disabled'])
    tab.standard_list.selection_set(len(tab.standards) - 1)
    tab.update_state()
    assert not regimes.instate(['disabled'])
    tab.vars['custom_regimes'].set('cooling_season: 0.33 18.8 2 -3 10 30 10 30')
    arguments = forms.add_accis_arguments(tab.form())
    assert arguments['custom_regimes'] == [CustomRegime(0.33, 18.8, 2, -3, 10, 30, 10, 30, 'cooling_season')]
    # The PMV-based setpoints do not use the custom model: the field is disabled and left out
    tab.vars['setpoint_type'].set('pmv')
    assert regimes.instate(['disabled']) and tab.form()['custom_regimes'] == ''
    tab.vars['setpoint_type'].set('temperature')


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
        '1. Add the ACCIS', '2. PMV-based setpoints', '3. Rename the EPWs', '4. Run the simulations',
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


def test_the_fields_of_the_table_of_the_zones_in_the_window(app, tmp_path):
    (tmp_path / 'model.idf').write_text('')
    app.folder.set(str(tmp_path))
    tab = app.add_accis
    table = tab.zone_table

    table.zone.set('Block1:Zone1')
    table.vars['comfort_standard'].set('2 = INT ASHRAE55')
    # The categories and comfort modes are those of the comfort standard of the zone
    assert list(table.fields['category'].cget('values')) == ['', '80', '90']
    table.vars['category'].set('80')
    table.vars['comfort_mode'].set('3')
    table.other.set('setpoint_tolerance=0.25')
    assert tab.set_zone()
    assert tab.zone_rows() == [('Block1:Zone1', 'comfort_standard=2, category=80, comfort_mode=3, '
                                                'setpoint_tolerance=0.25')]
    # Selecting a row fills the fields
    table.clear_fields()
    tab.zone_tree.selection_set(tab.zone_tree.get_children()[0])
    table._selected()
    assert table.vars['comfort_standard'].get() == '2 = INT ASHRAE55' and table.vars['category'].get() == '80'
    assert table.other.get() == 'setpoint_tolerance=0.25'
    table.other.set('category=90')
    assert not tab.set_zone() and 'category is given twice' in app.errors[-1]
    # The HVAC mode and the ventilation control only in mixed mode, and they are not given otherwise
    tab.vars['script_type'].set('vrf_ac')
    assert table.fields['hvac_mode'].instate(['disabled']) and not table.fields['category'].instate(['disabled'])
    table.other.set('')
    table.vars['hvac_mode'].set('2 = Mixed mode')
    assert tab.set_zone() and 'hvac_mode' not in tab.zone_rows()[0][1]
    # Preview checks the zones with the output IDFs
    tab.vars['script_type'].set('vrf_mm')
    table.set_rows([('Block1:Zone1', 'comfort_standard=2')])
    tab.preview()
    assert 'category 3 is not a category of comfort_standard 2' in app.errors[-1]
    # The button of the comfort models shows the table of the zones
    tab.zone_button.invoke()


def test_add_accis_asks_after_the_estimated_size_of_the_results(app, tmp_path, monkeypatch):
    from accim.sim import accis

    (tmp_path / 'model.idf').write_text('')
    app.folder.set(str(tmp_path))
    _synchronous(app)
    received, questions, answers = [], [], [True, False]

    class FakeAddAccis:
        def __init__(self, **kwargs):
            received.append(kwargs)
            print('The list of output IDFs is going to be:\nmodel[CS_INT EN16798.idf')
            print('And the total number of output IDFs is going to be 1')
            print('The estimated size of the results of each simulation of the output IDFs, from their outputs '
                  '(without simulating them):\n    model (1 output IDF): 30.0 MB per simulation')
            written = input('Do you still want to run ACCIS? [y/n]: ') == 'y'
            self.output_idfs = {'model[CS_INT EN16798.idf': 'path'} if written else {}

    monkeypatch.setattr(accis, 'AddAccis', FakeAddAccis)
    app.ask_yes_no = lambda title, message: questions.append(message) or answers.pop(0)

    assert app.add_accis.add()

    # The window asks after AddAccis has printed the estimated size of the results
    assert received[0]['confirm'] is None and len(questions) == 1
    assert questions[0].startswith('And the total number of output IDFs is going to be 1\nThe estimated size')
    assert '30.0 MB per simulation' in questions[0]
    assert questions[0].endswith(f'Write the output IDFs in {tmp_path}?')
    assert app.infos == ['1 output IDFs have been written.']
    # The answer no writes nothing
    assert app.add_accis.add()
    log = app.log.get('1.0', 'end')
    assert len(app.infos) == 1 and 'No output IDF has been written.' in log
    assert 'Do you still want to run ACCIS? [y/n]: n' in log


def test_a_task_asks_in_the_window_and_waits_for_the_answer(app):
    import threading

    app.answers = [True]
    results = []
    thread = threading.Thread(target=lambda: results.append(app.ask_from_task('Question', 'Go on?')))
    thread.start()
    for _ in range(500):
        app.process_messages()
        thread.join(0.01)
        if not thread.is_alive():
            break

    assert results == [True] and app.answers == []


def test_the_question_before_writing_the_output_idfs():
    pytest.importorskip('tkinter')
    from accim.gui.app import _write_question

    printed = ('Starting with file:\nAnd the total number of output IDFs is going to be 2\nThe estimated size:\n'
               '    m (2 output IDFs): 30 MB\n')
    assert _write_question(printed, 'C:/work', 2) == ('And the total number of output IDFs is going to be 2\nThe '
                                                     'estimated size:\n    m (2 output IDFs): 30 MB\n\nWrite the '
                                                     'output IDFs in C:/work?')
    assert _write_question('', 'C:/work', 3) == ('AddAccis is going to write 3 output IDFs.\n\nWrite the output IDFs '
                                                 'in C:/work?')
    many = 'And the total number of output IDFs is going to be 1\n' + '\n'.join(f'line {i}' for i in range(50))
    assert _write_question(many, 'C:/work', 1).splitlines()[30] == '... (see the log)'


def test_the_ems_code_of_the_setpoints_in_a_window(app, tmp_path):
    app.folder.set(str(tmp_path))
    _synchronous(app)
    tab = app.add_accis

    assert tab.show_ems_code()

    window = tab.ems_code_window
    assert '1 = INT EN16798: category 3, comfort mode 3' in window.text.get('1.0', 'end')
    assert window.save(str(tmp_path / 'code.txt'))
    assert (tmp_path / 'code.txt').read_text(encoding='utf-8') == window.content and 'ComfStand' in window.content
    window.window.destroy()
    tab.vars['setpoint_type'].set('pmv')
    assert tab.ems_code_button.instate(['disabled'])
    assert tab.show_ems_code() is False and 'adaptive setpoint temperatures' in app.errors[-1]


def test_the_size_of_the_results_in_the_window(app, tmp_path, monkeypatch):
    from accim.gui import tasks

    app.folder.set(str(tmp_path))
    _synchronous(app)
    received = []
    monkeypatch.setattr(tasks, 'results_size', lambda arguments: received.append(arguments) or (None, 'About 30 MB.'))
    app.run.vars['simulate'].set(True)

    assert app.run.estimate_size()

    assert received == [dict(simulate=True, only_accim_idfs=True, processes=2)]
    assert app.run.size.get() == 'About 30 MB.'
    # Another folder or other IDFs forget it
    app.folder_changed()
    assert app.run.size.get() == ''


def test_the_hours_within_the_setpoints_of_some_zones(app, tmp_path):
    summary = _hours_summary(tmp_path / 'hours')

    app.hours.zones.set('zone1')
    app.hours.show(summary, 75)

    assert app.hours.result.get().startswith('1 of the 2 simulations reach 75') and '(zone1)' in app.hours.result.get()
    assert app.hours.shown['zones'] == ['zone1']
    app.hours.zones.set(' , ')
    app.hours.show(summary, 75)
    assert 'enter building, all, or the zones' in app.errors[-1]


def test_the_window_explains_the_energyplus_version_of_eppy(app, tmp_path):
    def task():
        raise ValueError('eppy is already using the IDD ... Use a new Python session for the models of other '
                         'EnergyPlus versions.')

    app.execute('Task', str(tmp_path), task)
    app.process_messages()

    assert 'save the session, close the window, open it again and open the session' in app.errors[-1]


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
    tab.vars['pmv_cooling_setpoint'].set('0.5')
    # The setpoints of some zones
    tab.zone_table.zone.set('Block1:Zone1')
    tab.zone_table.vars['pmv_cooling_setpoint'].set('0.7')
    tab.zone_table.other.set('cooling_setpoint_tolerance_cooling_season=-0.2')
    assert tab.zone_table.set_zone()
    assert tab.state()['zone_setpoints'] == [('Block1:Zone1', 'pmv_cooling_setpoint=0.7, '
                                                              'cooling_setpoint_tolerance_cooling_season=-0.2')]
    arguments = forms.apmv_arguments(tab.form())
    assert arguments['apmv']['pmv_cooling_setpoint'] == {'Block1:Zone1': 0.7}
    assert arguments['apmv']['default_pmv_cooling_setpoint'] == 0.5
    tab.zone_table.other.set('activity_level=100')
    assert not tab.zone_table.set_zone() and "'activity_level' is not a PMV-based setpoint of a zone" in app.errors[-1]
    tab.vars['idf'].set('')
    assert tab.find_zones() is False and app.errors[-1] == 'Choose the input IDF first.'


def test_the_tab_enables_the_fields_of_the_index(app, tmp_path):
    (tmp_path / 'model.idf').write_text('')
    app.folder.set(str(tmp_path))
    tab = app.apmv

    def enabled(widget):
        return not widget.instate(['disabled'])

    assert enabled(tab.setpoint_entries['adaptive_coefficient_cooling'])
    assert not enabled(tab.setpoint_entries['expectancy_factor']) and not any(map(enabled, tab.epmv_checks))
    assert all(map(enabled, tab.apmv_combos))
    # An entry of the catalogue fills the coefficients
    tab.vars['adaptive_coefficients'].set('yao2009_chongqing_classrooms')
    tab.fill_coefficients()
    assert tab.vars['adaptive_coefficient_cooling'].get() == '0.293'
    assert tab.vars['adaptive_coefficient_heating'].get() == '-0.125'
    assert 'Chongqing' in tab.coefficients_note.cget('text')
    tab.vars['adaptive_coefficient_by'].set('pmv_sign')
    assert forms.apmv_arguments(tab.form())['apmv']['adaptive_coefficient_by'] == 'pmv_sign'
    tab.vars['index'].set('epmv')
    tab.update_state()
    assert not any(map(enabled, tab.apmv_combos))
    assert not enabled(tab.setpoint_entries['adaptive_coefficient_heating'])
    assert enabled(tab.setpoint_entries['expectancy_factor']) and all(map(enabled, tab.epmv_checks))
    assert enabled(tab.setpoint_entries['pmv_cooling_setpoint'])
    # The table of the zones: the fields of the index only
    assert not enabled(tab.zone_table.fields['adaptive_coefficient_cooling'])
    assert enabled(tab.zone_table.fields['expectancy_factor'])
    tab.zone_table.zone.set('Block1:Zone1')
    tab.zone_table.vars['expectancy_factor'].set('0.6')
    assert tab.zone_table.set_zone()
    tab.vars['metabolic_correction'].set(True)
    arguments = forms.apmv_arguments(tab.form())
    assert arguments['output_idf'] == 'model_ePMV.idf' and arguments['apmv']['metabolic_correction'] is True
    assert arguments['apmv']['expectancy_factor'] == {'Block1:Zone1': 0.6}
    tab.vars['index'].set('pmv')
    tab.update_state()
    assert not enabled(tab.setpoint_entries['expectancy_factor']) and not any(map(enabled, tab.epmv_checks))
    assert tab.state()['index'] == 'pmv'


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
    # The long-term discomfort indicators of a table are shown in the log
    tab.vars['long_term_indicators'].set(True)
    tab.vars['frequency'].set('hourly')
    assert forms.table_arguments(tab.form())['table']['long_term_indicators'] is True
    logged = []
    monkeypatch.setattr(app, 'log_text', logged.append)
    table.long_term_indicators = pd.DataFrame({'Source': ['model[Seville'], 'Building_Occupied Hours (h)': [10.0]})
    tab.show_table(table)
    assert 'long-term discomfort indicators of CEN/TR 16798-2' in logged[-1]
    assert 'Building_Occupied Hours (h)' in logged[-1] and 'model[Seville' in logged[-1]


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

# Sessions ------------------------------------------------------------------------------------------------------------

def _synchronous(app):
    """Run the tasks of the window at once, in the thread of the test (they run in another thread otherwise)."""
    def run_task(title, folder, function, on_done=None, answers=None):
        app.execute(title, folder, function, on_done, answers)
        app.process_messages()
        return True

    app.run_task = run_task


def _hours_summary(folder):
    """The hours within the setpoints of two simulations: 100 % and 50 % of their occupied hours."""
    folder.mkdir()
    for name, within in (('a.csv', [1.0, 1.0]), ('b.csv', [1.0, 0.0])):
        pd.DataFrame({'Date/Time': ['01/01 01:00:00', '01/01 02:00:00'],
                      'EMS:Occupied Hours_ZONE1 [H](Hourly)': [1.0, 1.0],
                      'EMS:Occupied Comfortable Hours_No Applicability_ZONE1 [H](Hourly)': within}).to_csv(
            folder / name, index=False)
    from accim.data.postprocessing.setpoint_hours import hours_within_setpoints

    return hours_within_setpoints(str(folder))


def test_the_menu_of_the_sessions(app):
    assert app.menu.entrycget(0, 'label') == 'Session'
    sessions = app.root.nametowidget(app.menu.entrycget(0, 'menu'))
    assert [sessions.entrycget(index, 'label') for index in range(2)] == ['Open a session...', 'Save the session...']


def test_a_session_of_the_window_is_saved_and_opened_again(app, tmp_path, monkeypatch):
    import accim.gui.app as app_module

    folder = tmp_path / 'work'
    folder.mkdir()
    for name in ('model.idf', 'other.idf', 'a.epw', 'b.epw'):
        (folder / name).write_text('')
    app.folder.set(str(folder))
    _synchronous(app)
    add, rename, hours, table_tab, parametric = app.add_accis, app.rename_epws, app.hours, app.table, app.parametric
    # Values in the forms of all the tabs, and results in three of them
    add.idf_list.selection_clear(0, 'end')
    add.idf_list.selection_set(1)
    add.vars['script_type'].set('ex_mm')
    add.vars['category'].set('1 2')
    add.vars['existing_hvac_ideal_loads_backup'].set(True)
    add.frequencies['daily'].set(True)
    add.hvac_modes[0].set(True)
    add.standard_list.selection_set(2)
    add.zone_name.set('Block1:Zone2')
    add.zone_text.set('comfort_standard=2, category=80')
    assert add.set_zone()
    app.apmv.vars['output_idf'].set('model_aPMV_2.idf')
    app.apmv.frequencies['monthly'].set(True)
    app.apmv.zone_table.zone.set('Block1:Zone1')
    app.apmv.zone_table.vars['pmv_cooling_setpoint'].set('0.7')
    assert app.apmv.zone_table.set_zone()
    rename.epw_list.selection_clear(0, 'end')
    rename.epw_list.selection_set(1)
    rename.cities.insert('1.0', 'b = Sevilla')
    rename.delete_originals.set(True)
    app.run.vars['processes'].set('3')
    app.run.vars['only_accim_idfs'].set(False)
    hours.zones.set('all')
    hours.show(_hours_summary(tmp_path / 'hours'), 75)
    table = SimpleNamespace(
        df=pd.DataFrame({'ComfMod': ['CM_0', 'CM_3'], 'EPW': ['A', 'B'], 'Cooling (kWh/m2)': [1.0, 2.0],
                         'RMOT (C)': [10.0, 20.0]}),
        cols_for_multiindex=['ComfMod', 'EPW'], val_cols=['Cooling (kWh/m2)', 'RMOT (C)'],
        suggested_vars_dict={'ComfMod': ['CM_0', 'CM_3'], 'EPW': ['A', 'B']}, frequency='runperiod')
    table_tab.show_table(table)
    table_tab.rows_list.selection_set(0)
    table_tab.cols_list.selection_set(1)
    table_tab.y_list.selection_set(0, 1)
    table_tab.vars['data_on_x_axis'].set('RMOT (C)')
    table_tab.vars['figname'].set('my_figure')
    table_tab.levels['block'].set(True)
    parametric.vars['parameters_type'].set('accim custom model')
    parametric.vars['sampling'].set('lhs')
    parametric.parameter_name.set('custom_slope')
    parametric.parameter_values.set('0.2 to 0.6')
    assert parametric.set_parameter()
    parametric.epw_list.selection_clear(0, 'end')
    parametric.epw_list.selection_set(1)
    parametric.show_results(pd.DataFrame({'custom_slope': [0.3, 0.4], 'Heating:Electricity': [1.0, 2.0]}))
    saved = {key: tab.state() for key, tab in app.tabs().items()}

    monkeypatch.setattr(app_module.filedialog, 'asksaveasfilename', lambda **kwargs: str(tmp_path / 'session.pkl'))
    assert app.save_session()

    assert 'The session has been saved in' in app.log.get('1.0', 'end') and not app.errors
    readable = json.loads((tmp_path / 'session.json').read_text(encoding='utf-8'))['objects']
    assert sorted(readable) == ['gui_forms', 'hours_within_setpoints', 'parametric_results', 'table']
    forms_json = readable['gui_forms']['value']
    assert forms_json['folder'] == str(folder) and forms_json['run']['processes'] == '3'
    assert forms_json['add_accis']['zone_arguments'] == [['Block1:Zone2', 'comfort_standard=2, category=80']]
    assert forms_json['apmv']['zone_setpoints'] == [['Block1:Zone1', 'pmv_cooling_setpoint=0.7']]
    assert readable['parametric_results']['value']['data'] == {'custom_slope': [0.3, 0.4],
                                                               'Heating:Electricity': [1.0, 2.0]}

    # Another session: other values, another folder and no results; and an EPW is no longer in the folder
    add.vars['script_type'].set('vrf_ac')
    add.zone_tree.delete(*add.zone_tree.get_children())
    app.apmv.zone_table.set_rows([])
    rename.cities.delete('1.0', 'end')
    app.run.vars['processes'].set('1')
    hours.clear()
    table_tab.clear()
    parametric.clear_results()
    (folder / 'b.epw').unlink()
    (tmp_path / 'other').mkdir()
    app.folder.set(str(tmp_path / 'other'))
    monkeypatch.setattr(app_module.filedialog, 'askopenfilename', lambda **kwargs: str(tmp_path / 'session.pkl'))

    assert app.open_session()

    assert app.folder.get() == str(folder) and not app.errors
    expected = copy.deepcopy(saved)
    expected['rename_epws']['epws'] = expected['parametric']['epws'] = []
    assert {key: tab.state() for key, tab in app.tabs().items()} == expected
    log = app.log.get('1.0', 'end')
    assert 'EPWs of "3. Rename the EPWs": b.epw not found.' in log
    assert 'EPWs of "7. Parametric study": b.epw not found.' in log
    assert hours.result.get().startswith('1 of the 2 simulations reach 75') and not hours.export_button.instate(
        ['disabled'])
    assert table_tab.table is not None and len(table_tab.tree.get_children()) == 2
    assert not table_tab.figure_button.instate(['disabled'])
    assert parametric.results is not None and len(parametric.tree.get_children()) == 2


def test_a_session_without_results_clears_those_of_the_window(app, tmp_path):
    from accim.gui import tasks
    from accim.utils import save_session

    _synchronous(app)
    app.parametric.show_results(pd.DataFrame({'custom_slope': [0.3]}))
    app.table.show_table(SimpleNamespace(df=pd.DataFrame({'ComfMod': ['CM_0'], 'Cooling': [1.0]}),
                                         cols_for_multiindex=['ComfMod'], val_cols=['Cooling'],
                                         suggested_vars_dict={}))
    save_session(tmp_path / 'empty', **{tasks.SESSION_FORMS: {'folder': str(tmp_path / 'missing')}})

    assert app.open_session(str(tmp_path / 'empty.pkl'))

    assert app.parametric.results is None and not app.parametric.tree.get_children()
    assert app.table.table is None and app.table.save_button.instate(['disabled'])
    assert f'The working folder of the session, {tmp_path / "missing"}, does not exist' in app.log.get('1.0', 'end')
    # The sessions saved in Python are not those of the window
    save_session(tmp_path / 'python', csvs=['a.csv'])
    assert app.open_session(str(tmp_path / 'python.pkl')) and 'not by the interface' in app.errors[-1]


def test_the_tab_of_table_saves_and_opens_tables(app, tmp_path, monkeypatch):
    import accim.gui.app as app_module
    from .test_table_methods import SAMPLE_CSVS, _sample_table

    if len(SAMPLE_CSVS) != 4:
        pytest.skip('needs the sample CSV files of the repository')
    for csv in SAMPLE_CSVS:
        shutil.copy(csv, tmp_path)
    table = _sample_table(tmp_path)
    table.format_table(type_of_table='custom', custom_cols=['Building_Total_Cooling Energy Demand'])
    table.save(tmp_path / 'python_table')
    app.folder.set(str(tmp_path))
    _synchronous(app)
    tab = app.table

    assert tab.save_table() is False and app.errors[-1] == 'Make the table first.'
    # A table saved in Python, with the columns that it had
    monkeypatch.setattr(app_module.filedialog, 'askopenfilename', lambda **kwargs: str(tmp_path / 'python_table.pkl'))
    assert tab.open_table()
    opened = tab.table
    assert opened.type_of_table == 'custom' and list(opened.df.columns) == opened.indexcols + opened.val_cols
    assert tab.summary.get().startswith(f'Table of {tmp_path / "python_table.pkl"} (runperiod): 4 rows')
    assert len(tab.tree.get_children()) == 4 and not tab.save_button.instate(['disabled'])
    # Saved by the tab, with its JSON file
    monkeypatch.setattr(app_module.filedialog, 'asksaveasfilename', lambda **kwargs: str(tmp_path / 'gui_table.pkl'))
    assert tab.save_table()
    assert json.loads((tmp_path / 'gui_table.json').read_text(encoding='utf-8'))['type_of_table'] == 'custom'
    tab.clear()
    assert tab.table is None and tab.save_button.instate(['disabled']) and tab.summary.get().startswith('4 CSV')
    assert tab.open_table(str(tmp_path / 'gui_table.pkl'))
    pd.testing.assert_frame_equal(tab.table.df, opened.df)
    # Other files are not tables
    pd.to_pickle(pd.DataFrame(), tmp_path / 'frame.pkl')
    assert tab.open_table(str(tmp_path / 'frame.pkl')) and 'does not have a table saved with Table.save' in \
        app.errors[-1]
    assert tab.table is not None


def test_the_files_of_the_window_can_have_relative_paths(app, tmp_path, monkeypatch):
    from accim.gui import tasks

    # The tasks run in the folder of the file: the relative paths are made absolute before
    (tmp_path / 'sub').mkdir()
    monkeypatch.chdir(tmp_path)
    _synchronous(app)
    app.run.vars['processes'].set('5')

    assert app.save_session(os.path.join('sub', 'session.pkl'))
    app.run.vars['processes'].set('1')
    assert app.open_session(os.path.join('sub', 'session.pkl'))

    assert not app.errors and (tmp_path / 'sub' / 'session.json').is_file()
    assert app.run.vars['processes'].get() == '5' and Path(os.getcwd()) == tmp_path
    paths = []
    table = SimpleNamespace(df=pd.DataFrame({'ComfMod': ['CM_0'], 'Cooling': [1.0]}), cols_for_multiindex=['ComfMod'],
                            val_cols=['Cooling'], suggested_vars_dict={},
                            save=lambda path: paths.append(path) or (path, path))
    app.table.show_table(table)
    monkeypatch.setattr(tasks, 'open_table', lambda path: paths.append(path) or table)
    assert app.table.save_table(os.path.join('sub', 'table.pkl'))
    assert app.table.open_table(os.path.join('sub', 'table.pkl'))
    assert paths == [str(tmp_path / 'sub' / 'table.pkl')] * 2 and not app.errors
