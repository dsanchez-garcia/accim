"""Tests for accim.sim.apmv.set_pmv_input_parameters with the values by season of the activity level and the clothing
insulation, and the dynamic clothing model of ASHRAE 55 (proposal A5 after accim 1.1.0), and for
accim.sim.people.set_clothing_method, the method of the clothing insulation of the People objects.

A dictionary {'heating_season': x, 'cooling_season': y} gives a Schedule:Compact with the value of the cooling season
from cooling_season_start to the day before cooling_season_end, as the EMS program set_cooling_season of the PMV-based
setpoints, and that of the heating season the rest of the year; 'dynamic_ashrae55' sets the Clothing Insulation
Calculation Method DynamicClothingModelASHRAE55 of the People objects. The ``schedule`` of set_clothing_method is the
clothing insulation schedule, and ``calculation_method_schedule`` that of the method CalculationMethodSchedule (the
choice of the author). The tests that simulate run the sample model with EnergyPlus 25.1. The People:Instance objects
of EnergyPlus 26.2 are tested in test_people_instance.py and test_energyplus_versions.py.
"""
import shutil
import subprocess
import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import find_energyplus
from accim.sim import apmv
from accim.sim.accis import load_idf
from accim.sim.people import set_clothing_method
from accim.sim.pmv_index import metabolic_correction_names

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
# One People object for the two floors (a SpaceList)
RESIDENTIAL_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'example_apmv_setpoints_paper'
                   / 'TestModel_TestResidentialUnit.idf')
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
ZONES = ('Block1:Zone1', 'Block1:Zone2')
# The clothing insulation of the heating and cooling seasons of the design criteria of EN 16798-1 and ISO 7730
CLOTHING = {'heating_season': 1.0, 'cooling_season': 0.5}
ACTIVITY = {'heating_season': 120, 'cooling_season': 100}


def _model(tmp_path, source=SAMPLE_IDF):
    """A model of EnergyPlus 25.1, read by eppy."""
    if find_energyplus('25.1', required=False) is None or not source.exists():
        pytest.skip('needs EnergyPlus 25.1 (its IDD) and the sample IDFs of the repository')
    path = tmp_path / source.name
    shutil.copy(source, path)
    return load_idf(path)


def _people(building, zone):
    """The People object of a zone of the sample model, and the name of its schedules."""
    return building.getobject('People', f'People {zone}'), f'People_{zone.replace(":", "_")}'


def _fields(building, name):
    """The fields of a Schedule:Compact object after its type limits."""
    return [str(field) for field in building.getobject('Schedule:Compact', name).fieldvalues[3:] if str(field)]


def _periods(*periods):
    """The fields of a Schedule:Compact object with a value until each date."""
    return [field for (through, value) in periods
            for field in (f'Through: {through}', 'For: AllDays', f'Until: 24:00,{value}')]


def _value(building, name, day_of_year):
    """The value of a Schedule:Compact object of set_pmv_input_parameters on a day of a year that is not a leap year."""
    day = date(2007, 1, 1) + timedelta(days=day_of_year - 1)
    fields = _fields(building, name)
    for through, days, until in zip(fields[0::3], fields[1::3], fields[2::3]):
        assert days == 'For: AllDays' and until.startswith('Until: 24:00,')
        month, day_of_month = (int(n) for n in through.replace('Through:', '').split('/'))
        if (day.month, day.day) <= (month, day_of_month):
            return float(until.split(',')[1])
    raise AssertionError(f'{name} has no value for the day {day_of_year}')


def test_the_clothing_insulation_and_the_activity_level_by_season(tmp_path):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation=CLOTHING, activity_level=ACTIVITY, verbose=False)

    for zone in ZONES:
        people, name = _people(building, zone)
        assert people.Clothing_Insulation_Schedule_Name == f'Sch_Clo_{name}'
        assert people.Activity_Level_Schedule_Name == f'Sch_Act_{name}'
        assert people.Clothing_Insulation_Calculation_Method == 'ClothingInsulationSchedule'
        assert people.Thermal_Comfort_Model_1_Type == 'Fanger'
        # The cooling season of the setpoints by default: from the day 121 (1 May) to the day 273 (30 September)
        assert _fields(building, f'Sch_Clo_{name}') == _periods(('4/30', 1.0), ('9/30', 0.5), ('12/31', 1.0))
        days = (120, 121, 273, 274, 275)
        assert [_value(building, f'Sch_Clo_{name}', day) for day in days] == [1.0, 0.5, 0.5, 1.0, 1.0]
        assert [_value(building, f'Sch_Act_{name}', day) for day in days] == [120, 100, 100, 120, 120]


@pytest.mark.parametrize('start, end', [('01/11', '01/03'), (305, 60)])
def test_a_cooling_season_that_goes_on_into_the_next_year(tmp_path, start, end):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation=CLOTHING, cooling_season_start=start,
                                  cooling_season_end=end, verbose=False)

    name = 'Sch_Clo_People_Block1_Zone1'
    assert _fields(building, name) == _periods(('2/28', 0.5), ('10/31', 1.0), ('12/31', 0.5))
    assert [_value(building, name, day) for day in (1, 59, 60, 304, 305, 365)] == [0.5, 0.5, 1.0, 1.0, 0.5, 0.5]


@pytest.mark.parametrize('start, end, periods', [
    (1, 274, [('9/30', 0.5), ('12/31', 1.0)]),
    (121, 366, [('4/30', 1.0), ('12/31', 0.5)]),
    (305, 1, [('10/31', 1.0), ('12/31', 0.5)]),
])
def test_a_cooling_season_from_the_beginning_or_to_the_end_of_the_year(tmp_path, start, end, periods):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation=CLOTHING, cooling_season_start=start,
                                  cooling_season_end=end, verbose=False)

    assert _fields(building, 'Sch_Clo_People_Block1_Zone1') == _periods(*periods)


def test_the_dynamic_clothing_model_of_ashrae_55(tmp_path):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation=0.5, verbose=False)
    apmv.set_pmv_input_parameters(building, clothing_insulation='Dynamic_ASHRAE55', verbose=False)

    for zone in ZONES:
        people, name = _people(building, zone)
        assert people.Clothing_Insulation_Calculation_Method == 'DynamicClothingModelASHRAE55'
        assert people.Thermal_Comfort_Model_1_Type == 'Fanger'
        # EnergyPlus does not read the clothing insulation schedule, which does not change
        assert people.Clothing_Insulation_Schedule_Name == f'Sch_Clo_{name}'
        assert _fields(building, f'Sch_Clo_{name}') == _periods(('12/31', 0.5))

    # A number (or a dictionary by season) sets the method of the clothing insulation schedule again
    apmv.set_pmv_input_parameters(building, clothing_insulation=0.7, verbose=False)
    for zone in ZONES:
        people, name = _people(building, zone)
        assert people.Clothing_Insulation_Calculation_Method == 'ClothingInsulationSchedule'
        assert _fields(building, f'Sch_Clo_{name}') == _periods(('12/31', 0.7))


def test_a_new_call_writes_the_new_values(tmp_path):
    # Before accim 1.2.0, a new call kept the schedule of the first one, with its value
    building = _model(tmp_path)
    name = 'Sch_Clo_People_Block1_Zone1'
    for clothing, periods in [(0.5, [('12/31', 0.5)]), (1.0, [('12/31', 1.0)]),
                              (CLOTHING, [('4/30', 1.0), ('9/30', 0.5), ('12/31', 1.0)]), (0.6, [('12/31', 0.6)])]:
        apmv.set_pmv_input_parameters(building, clothing_insulation=clothing, verbose=False)
        assert _fields(building, name) == _periods(*periods)
    assert sorted(s.Name for s in building.idfobjects['Schedule:Compact'] if s.Name.startswith('Sch_Clo_')) == [
        'Sch_Clo_People_Block1_Zone1', 'Sch_Clo_People_Block1_Zone2']


def test_the_values_by_zone(tmp_path):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation={'Block1:Zone1': 'dynamic_ashrae55',
                                                                  'Block1:Zone2': CLOTHING},
                                  activity_level={'Block1:Zone1': ACTIVITY, 'Block1:Zone2': 110}, verbose=False)

    zone1, name1 = _people(building, 'Block1:Zone1')
    zone2, name2 = _people(building, 'Block1:Zone2')
    assert zone1.Clothing_Insulation_Calculation_Method == 'DynamicClothingModelASHRAE55'
    assert zone2.Clothing_Insulation_Calculation_Method == 'ClothingInsulationSchedule'
    assert [_value(building, f'Sch_Clo_{name2}', day) for day in (120, 121)] == [1.0, 0.5]
    assert [_value(building, f'Sch_Act_{name1}', day) for day in (120, 121)] == [120, 100]
    assert _fields(building, f'Sch_Act_{name2}') == _periods(('12/31', 110))


@pytest.mark.parametrize('arguments, message', [
    (dict(activity_level='dynamic_ashrae55'), 'is a value of clothing_insulation, not of activity_level'),
    (dict(clothing_insulation={'heating_season': 1.0}),
     "must have the keys 'heating_season' and 'cooling_season' only"),
    (dict(clothing_insulation={'Block1:Zone1': {'heating_season': 1.0, 'summer': 0.5}}),
     "must have the keys 'heating_season' and 'cooling_season' only"),
    (dict(activity_level={'heating_season': '120', 'cooling_season': 100}), 'must be numbers'),
    (dict(clothing_insulation=CLOTHING, cooling_season_start=0), 'cooling_season_start must be a day of the year'),
    (dict(clothing_insulation=CLOTHING, cooling_season_end='31/02'), 'cooling_season_end must be a day of the year'),
    (dict(clothing_insulation=CLOTHING, cooling_season_start='01/05', cooling_season_end=121),
     'must be different days'),
])
def test_the_wrong_values_stop_before_changing_the_model(tmp_path, arguments, message):
    building = _model(tmp_path)
    before = building.idfstr()

    with pytest.raises(ValueError, match=message):
        apmv.set_pmv_input_parameters(building, verbose=False, **arguments)
    assert building.idfstr() == before


def test_a_people_object_of_several_zones(tmp_path):
    building = _model(tmp_path, RESIDENTIAL_IDF)
    floors = apmv.get_available_target_names(building)
    people = building.idfobjects['People'][0]

    # A People object has one schedule: with different values for its zones, that of the first zone, with a warning
    with pytest.warns(UserWarning, match=f"different values of clothing_insulation.*'{floors[0]}' is used"):
        apmv.set_pmv_input_parameters(building, clothing_insulation={floors[0]: CLOTHING,
                                                                      floors[1]: 'dynamic_ashrae55'}, verbose=False)
    assert people.Clothing_Insulation_Calculation_Method != 'DynamicClothingModelASHRAE55'
    assert [_value(building, people.Clothing_Insulation_Schedule_Name, day) for day in (120, 121)] == [1.0, 0.5]

    # The same values for both zones, without warnings
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        apmv.set_pmv_input_parameters(building, clothing_insulation={floors[0]: CLOTHING, floors[1]: dict(CLOTHING)},
                                      verbose=False)
    assert not [w for w in caught if 'different values' in str(w.message)]


def test_the_metabolic_correction_copies_the_activity_level_by_season(tmp_path):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, activity_level=ACTIVITY, verbose=False)
    apmv.apply_epmv_setpoints(building, metabolic_correction=True, verbose=False)

    for zone in ZONES:
        people, name = _people(building, zone)
        names = metabolic_correction_names(people.Name)
        assert people.Activity_Level_Schedule_Name == names['schedule']
        # The copy that the EMS sets has the values by season, and the sensor of the activity level without the
        # correction reads the schedule of set_pmv_input_parameters
        assert _fields(building, names['schedule']) == _fields(building, f'Sch_Act_{name}')
        sensor = building.getobject('EnergyManagementSystem:Sensor', names['base'])
        assert sensor.OutputVariable_or_OutputMeter_Index_Key_Name == f'Sch_Act_{name}'


def _energyplus():
    """The executable of EnergyPlus 25.1, or None."""
    folder = find_energyplus('25.1', required=False)
    if folder is None:
        return None
    return next((folder / name for name in ('energyplus.exe', 'energyplus') if (folder / name).exists()), None)


def _column(results, text):
    columns = [c for c in results.columns if text in c]
    assert len(columns) == 1, (text, columns)
    return results[columns[0]]


def _simulate(tmp_path, building, periods, variables):
    """Runs the model with EnergyPlus 25.1 in the run periods ((month, day), (month, day)) of 2002, with the output
    variables (key, name) at each timestep, and returns the results with their date and time."""
    run_period = building.idfobjects['RunPeriod'][0]
    for n, ((begin_month, begin_day), (end_month, end_day)) in enumerate(periods):
        period = run_period if n == 0 else building.copyidfobject(run_period)
        period.Name = f'Run period {n + 1}'
        period.Begin_Month, period.Begin_Day_of_Month, period.Begin_Year = begin_month, begin_day, 2002
        period.End_Month, period.End_Day_of_Month, period.End_Year = end_month, end_day, 2002
    for key, variable in variables:
        building.newidfobject('Output:Variable', Key_Value=key, Variable_Name=variable, Reporting_Frequency='Timestep')
    model = tmp_path / 'model.idf'
    building.saveas(str(model))
    process = subprocess.run([str(_energyplus()), '-d', str(tmp_path / 'out'), '-p', 'run', '-s', 'C', '-r', '-x',
                              '-w', str(SAMPLE_EPW), str(model)], capture_output=True, text=True)
    assert process.returncode == 0, process.stdout[-3000:]
    assert '** Severe' not in (tmp_path / 'out' / 'run.err').read_text(errors='ignore')
    results = pd.read_csv(tmp_path / 'out' / 'run.csv')
    date_time = results['Date/Time'].str.strip()
    return results.assign(date=date_time.str[:5], time=date_time.str[-8:])


@pytest.mark.skipif(not (_energyplus() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_energyplus_changes_the_values_by_season_on_the_days_of_the_cooling_season_of_the_setpoints(tmp_path):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation=CLOTHING, activity_level=ACTIVITY, verbose=False)
    apmv.add_vrf_system(building, verbose=False)
    apmv.apply_epmv_setpoints(building, expectancy_factor=0.7, output_frequencies=['timestep'], verbose=False)
    results = _simulate(tmp_path, building, [((4, 30), (5, 1)), ((9, 30), (10, 2))],
                        [('Sch_Clo_People_Block1_Zone1', 'Schedule Value'),
                         ('Sch_Act_People_Block1_Zone1', 'Schedule Value')])

    # The values at noon of the days 120, 121, 273, 274 and 275. EnergyPlus applies the schedules in the local time
    # of the daylight saving time of the model (from the last Sunday of March to the last Sunday of October), so in
    # the standard time of the results they change at 23:00 of the day before
    noon = results[results['time'] == '12:00:00'].set_index('date').loc[['04/30', '05/01', '09/30', '10/01', '10/02']]
    assert _column(noon, 'SCH_CLO_PEOPLE_BLOCK1_ZONE1:Schedule Value').tolist() == [1.0, 0.5, 0.5, 1.0, 1.0]
    assert _column(noon, 'SCH_ACT_PEOPLE_BLOCK1_ZONE1:Schedule Value').tolist() == [120, 100, 100, 120, 120]
    # The cooling season of the setpoints: the expectancy factor of the ePMV, which is 1 in the heating season
    assert _column(noon, 'Expectancy Factor_Block1_Zone1').tolist() == [1.0, 0.7, 0.7, 1.0, 1.0]


def _ashrae55_clothing(temperature):
    """The clothing insulation of the dynamic model of ASHRAE 55 (Schiavon and Lee, 2013), in clo, from the outdoor air
    temperature at 6 a.m., in °C."""
    if temperature < -5:
        return 1.0
    if temperature < 5:
        return 0.818 - 0.0364 * temperature
    if temperature < 26:
        return 10 ** (-0.1635 - 0.0066 * temperature)
    return 0.46


@pytest.mark.skipif(not (_energyplus() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_energyplus_calculates_the_dynamic_clothing_of_ashrae_55(tmp_path):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation='dynamic_ashrae55', verbose=False)
    results = _simulate(tmp_path, building, [((1, 1), (1, 3)), ((7, 1), (7, 3))],
                        [('People Block1:Zone1', 'Zone Thermal Comfort Clothing Value'),
                         ('Environment', 'Site Outdoor Air Drybulb Temperature')])
    clothing = _column(results, 'PEOPLE BLOCK1:ZONE1:Zone Thermal Comfort Clothing Value')
    outdoor = _column(results, 'Site Outdoor Air Drybulb Temperature')

    temperatures = []
    for day, rows in results.groupby('date'):
        # EnergyPlus takes the outdoor air temperature of the first timestep after 6 a.m., and keeps the clothing
        # insulation of that day until then on the next day
        after_six = rows.index[rows['time'] > '06:00:00']
        temperature = outdoor[after_six[0]]
        np.testing.assert_allclose(clothing[after_six], _ashrae55_clothing(temperature), rtol=1e-6)
        temperatures.append(temperature)
    # Three of the four ranges of the model: from -5 to 5 °C, from 5 to 26 °C and above 26 °C
    assert len(temperatures) == 6
    assert min(temperatures) < 5 and any(5 <= t < 26 for t in temperatures) and max(temperatures) >= 26


def _method_schedule(building, values=(1, 2, 1), name='Clothing method'):
    """A schedule of the clothing insulation calculation method: the first value until 30 April, the second one until
    30 September and the third one until the end of the year."""
    building.newidfobject('Schedule:Compact', Name=name, Schedule_Type_Limits_Name='Any Number',
                          **dict(zip([f'Field_{n}' for n in range(1, 10)],
                                     _periods(('4/30', values[0]), ('9/30', values[1]), ('12/31', values[2])))))
    return name


@pytest.mark.parametrize('method', ['ClothingInsulationSchedule', 'DynamicClothingModelASHRAE55',
                                    'CalculationMethodSchedule', 'dynamicclothingmodelashrae55'])
def test_set_clothing_method_sets_the_method_of_every_people_object(tmp_path, method):
    building = _model(tmp_path)
    schedules = {people.Name: people.Clothing_Insulation_Schedule_Name for people in building.idfobjects['People']}
    arguments = {'calculation_method_schedule': _method_schedule(building)} if method.startswith('Calc') else {}

    set_clothing_method(building, method, verbose=False, **arguments)

    for people in building.idfobjects['People']:
        # The method as in the IDD, in any case
        assert people.Clothing_Insulation_Calculation_Method.upper() == method.upper()
        assert people.Clothing_Insulation_Calculation_Method in ('ClothingInsulationSchedule',
                                                                 'DynamicClothingModelASHRAE55',
                                                                 'CalculationMethodSchedule')
        # Without schedule, the People objects keep their clothing insulation schedules
        assert people.Clothing_Insulation_Schedule_Name == schedules[people.Name]
        assert people.Clothing_Insulation_Calculation_Method_Schedule_Name == arguments.get(
            'calculation_method_schedule', '')


def test_set_clothing_method_sets_the_schedules(tmp_path):
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation=CLOTHING, verbose=False)
    method_schedule = _method_schedule(building)

    set_clothing_method(building, 'ClothingInsulationSchedule', schedule='Sch_Clo_People_Block1_Zone1', verbose=False)
    assert {p.Clothing_Insulation_Schedule_Name for p in building.idfobjects['People']} == {
        'Sch_Clo_People_Block1_Zone1'}

    # The calculation method schedule, and the clothing insulation schedule of the periods of the method 1
    set_clothing_method(building, 'CalculationMethodSchedule', schedule='Sch_Clo_People_Block1_Zone2',
                        calculation_method_schedule=method_schedule, verbose=False)
    for people in building.idfobjects['People']:
        assert people.Clothing_Insulation_Calculation_Method == 'CalculationMethodSchedule'
        assert people.Clothing_Insulation_Calculation_Method_Schedule_Name == method_schedule
        assert people.Clothing_Insulation_Schedule_Name == 'Sch_Clo_People_Block1_Zone2'


@pytest.mark.parametrize('arguments, message', [
    (dict(method='Dynamic'), 'method must be one of'),
    (dict(method='CalculationMethodSchedule'), 'needs calculation_method_schedule'),
    (dict(method='ClothingInsulationSchedule', calculation_method_schedule='Clothing method'),
     "only used with the method 'CalculationMethodSchedule'"),
    (dict(method='DynamicClothingModelASHRAE55', schedule='Clothing method'),
     'does not read the clothing insulation schedule'),
    (dict(method='ClothingInsulationSchedule', schedule='Missing schedule'), r"\['Missing schedule'\] are not in"),
    (dict(method='CalculationMethodSchedule', calculation_method_schedule='Wrong method'),
     r'must have the values 1 .* not \[1.0, 3.0\]'),
])
def test_set_clothing_method_stops_before_changing_the_model(tmp_path, arguments, message):
    building = _model(tmp_path)
    _method_schedule(building)
    _method_schedule(building, values=(1, 3, 1), name='Wrong method')
    before = building.idfstr()

    with pytest.raises(ValueError, match=message):
        set_clothing_method(building, verbose=False, **arguments)
    assert building.idfstr() == before


def test_set_clothing_method_warns_about_a_people_object_without_a_clothing_insulation_schedule(tmp_path):
    building = _model(tmp_path)
    people, _ = _people(building, 'Block1:Zone1')
    people.Clothing_Insulation_Schedule_Name = ''

    with pytest.warns(UserWarning, match="'People Block1:Zone1' has no clothing insulation schedule"):
        set_clothing_method(building, 'ClothingInsulationSchedule', verbose=False)
    # The dynamic model does not need it
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        set_clothing_method(building, 'DynamicClothingModelASHRAE55', verbose=False)


@pytest.mark.skipif(not (_energyplus() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_energyplus_with_the_calculation_method_schedule(tmp_path):
    # The clothing insulation schedule (1 clo) in the heating season and the dynamic model in the cooling season
    building = _model(tmp_path)
    apmv.set_pmv_input_parameters(building, clothing_insulation=1.0, verbose=False)
    set_clothing_method(building, 'CalculationMethodSchedule', calculation_method_schedule=_method_schedule(building),
                        verbose=False)
    results = _simulate(tmp_path, building, [((1, 1), (1, 2)), ((7, 1), (7, 2))],
                        [('People Block1:Zone1', 'Zone Thermal Comfort Clothing Value'),
                         ('Environment', 'Site Outdoor Air Drybulb Temperature')])
    clothing = _column(results, 'PEOPLE BLOCK1:ZONE1:Zone Thermal Comfort Clothing Value')
    outdoor = _column(results, 'Site Outdoor Air Drybulb Temperature')

    # With the method 1, EnergyPlus reports the clothing insulation of the schedule
    assert set(clothing[results['date'].str.startswith('01/')]) == {1.0}
    for day in ('07/01', '07/02'):
        rows = results[results['date'] == day]
        after_six = rows.index[rows['time'] > '06:00:00']
        np.testing.assert_allclose(clothing[after_six], _ashrae55_clothing(outdoor[after_six[0]]), rtol=1e-6)
