"""Tests for the SET of pythermalcomfort with the inputs of the occupants of the People objects (task S4 of the review
of accim 1.2.0, option (ii), decided on 2026-11-12, ``notes/decisions.md``).

The SET of pythermalcomfort is the reference SET of the causal band of comfort standard 24. Its hook reads the
metabolic rate, the clothing insulation and the air speed of the People object of each zone in each timestep;
:func:`accim.sim.comfort_hooks.set_of_results` and ``table_indicators(..., pythermalcomfort_set='people')`` of
:mod:`accim.data.postprocessing.indoor_adaptation` read them from the results of any simulation, with the outputs that
``add_thermal_comfort_outputs(building, occupant_inputs=True)`` requests. The unit tests use a SET of their own
(``_fake_set``), so they do not need pythermalcomfort; the last one simulates the sample model with comfort standard 24
(EnergyPlus 25.1, the backend of the Python API) and compares the SET of the results with that of its hook.
"""
import shutil
import warnings

import numpy as np
import pandas as pd
import pytest

from accim.data.postprocessing import indoor_adaptation as ia
from accim.sim import comfort_hooks as ch

from .test_comfort_hooks import ZONES, _model, needs_energyplus, needs_idd
from .test_indoor_adaptation import (CSV_NAME, OCCUPIED, _add_set_conditions, _band, _fake_set, _indicator_columns,
                                     _indicator_table)
from .test_table_pmv_index import DESIGNBUILDER, _FakeIDF, _Obj, _zone

#: The schedules of the People objects of the sample model: zone -> (activity level, clothing insulation)
SCHEDULES = {'Block1_Zone1': ('Activity Schedule 26', 'Clothing Schedule 26'),
             'Block1_Zone2': ('Activity Schedule 19', 'Clothing Schedule 19')}
AIR_VELOCITY = 'Default Air Velocity for Comfort Calculations'
CLOTHING_VALUE = 'Zone Thermal Comfort Clothing Value'
ZONE_OUTPUTS = ('Zone Mean Air Temperature', 'Zone Mean Radiant Temperature', 'Zone Air Relative Humidity')


def _requested(idf):
    return [(str(o.Key_Value), str(o.Variable_Name), str(o.Reporting_Frequency))
            for o in idf.idfobjects['Output:Variable']]


@needs_idd
def test_the_people_inputs_of_a_model(tmp_path):
    idf = _model(tmp_path)
    found = ch.people_inputs(idf)
    # The occupied zones, in the order of the People objects of the model
    assert sorted(found) == ZONES
    for zone, (activity, clothing) in SCHEDULES.items():
        values = found[zone]
        assert (values['activity'], values['clothing'], values['air_speed']) == (activity, clothing, AIR_VELOCITY)
        assert values['clothing_source'] == 'schedule'
        # The keys of the outputs of the zone and of its occupants
        assert values['key'] == zone.replace('_', ':')
        assert values['occupants'].upper() == f"PEOPLE {zone.replace('_', ':')}".upper()
    assert list(ch.people_inputs(idf, ['Block1_Zone2'])) == ['Block1_Zone2']
    with pytest.raises(ValueError, match='The zone Block9_Zone9 has no People object'):
        ch.people_inputs(idf, ['Block9_Zone9'])
    people = idf.idfobjects['People'][0]
    people.Activity_Level_Schedule_Name = ''
    with pytest.raises(ValueError, match='have no Activity Level Schedule Name'):
        ch.people_inputs(idf)


@needs_idd
def test_the_outputs_of_the_inputs_of_the_occupants(tmp_path):
    from accim.sim.people import add_thermal_comfort_model, add_thermal_comfort_outputs, set_clothing_method

    idf = _model(tmp_path)
    before = _requested(idf)
    assert ch.add_people_input_outputs(idf) == ch.people_inputs(idf)
    added = _requested(idf)[len(before):]
    # At the frequency of the EMS outputs of the model: the conditions of each zone, and the schedules of its People
    # objects (the air velocity schedule of both zones, once)
    schedules = [name for pair in SCHEDULES.values() for name in pair] + [AIR_VELOCITY]
    assert sorted(added) == sorted(
        [(zone.replace('_', ':'), output, 'Hourly') for zone in ZONES for output in ZONE_OUTPUTS]
        + [(schedule, 'Schedule Value', 'Hourly') for schedule in schedules])
    # Once
    ch.add_people_input_outputs(idf)
    assert len(_requested(idf)) == len(before) + len(added)
    ch.add_people_input_outputs(idf, ['timestep'])
    assert len(_requested(idf)) == len(before) + 2 * len(added)

    # add_thermal_comfort_outputs requests them with occupant_inputs, with the outputs of its models
    (tmp_path / 'other').mkdir()
    other = _model(tmp_path / 'other')
    add_thermal_comfort_outputs(other, 'Pierce')
    without = _requested(other)
    add_thermal_comfort_outputs(other, 'Pierce', occupant_inputs=True)
    assert sorted(_requested(other)[len(without):]) == sorted(added)

    # The dynamic clothing model of ASHRAE 55: its clothing insulation is an output of the occupants, which
    # EnergyPlus reports with the Fanger, Pierce or KSU model
    (tmp_path / 'dynamic').mkdir()
    dynamic = _model(tmp_path / 'dynamic')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        set_clothing_method(dynamic, 'DynamicClothingModelASHRAE55', verbose=False)
    unchanged = dynamic.idfstr()
    with pytest.raises(ValueError, match='reports for the People objects with the Fanger, Pierce or KSU model'):
        ch.add_people_input_outputs(dynamic)
    with pytest.raises(ValueError, match="add 'Pierce' or 'Fanger' to models"):
        add_thermal_comfort_outputs(dynamic, 'CoolingEffectASH55', occupant_inputs=True)
    assert dynamic.idfstr() == unchanged
    add_thermal_comfort_model(dynamic, 'Pierce')
    start = len(_requested(dynamic))
    inputs = ch.add_people_input_outputs(dynamic)
    assert {values['clothing_source'] for values in inputs.values()} == {'dynamic'}
    requested = _requested(dynamic)[start:]
    assert sorted((key.upper(), name) for key, name, _ in requested if name == CLOTHING_VALUE) == sorted(
        (f"PEOPLE {zone.replace('_', ':')}".upper(), CLOTHING_VALUE) for zone in ZONES)
    # Not the clothing insulation schedules, which the dynamic model does not read
    assert sorted(key for key, name, _ in requested if name == 'Schedule Value') == sorted(
        [activity for activity, _ in SCHEDULES.values()] + [AIR_VELOCITY])


#: The rows of the results of the unit tests: the conditions of the zone, and the schedules of its People object. The
#: activity levels are 1.0, 1.2, 1.3 and 0 met (the last one, a row without a SET, as in the hook)
ROWS = pd.DataFrame({
    'Z1:Zone Mean Air Temperature [C](Hourly)': [20.0, 22.0, 24.0, 26.0, 21.0],
    'Z1:Zone Mean Radiant Temperature [C](Hourly)': [21.0, 22.5, 25.0, 27.0, 21.5],
    'Z1:Zone Air Relative Humidity [%](Hourly)': [40.0, 45.0, 50.0, 55.0, 60.0],
    'ACT:Schedule Value [](Hourly)': [ch.MET_ACTIVITY_LEVEL, 1.2 * ch.MET_ACTIVITY_LEVEL, 1.3 * ch.MET_ACTIVITY_LEVEL,
                                      0.0, 1.1 * ch.MET_ACTIVITY_LEVEL],
    'CLO:Schedule Value [](Hourly)': [1.0, 1.0, 0.5, 0.5, 0.7],
    'VEL:Schedule Value [](Hourly)': [0.1, 0.1, 0.6, 0.6, 0.3],
    'PEOPLE Z1:Zone Thermal Comfort Clothing Value [clo](Hourly)': [0.9, 0.0, 0.6, 0.6, 0.8],
    'METHOD:Schedule Value [](Hourly)': [1.0, 2.0, 2.0, 1.0, 1.0],
})
PEOPLE = {'Z1': {'activity': 'Act', 'clothing': 'Clo', 'clothing_method_schedule': 'Method', 'air_speed': 'Vel',
                 'clothing_source': 'schedule', 'occupants': 'People Z1', 'key': 'Z1'}}
AIR, RADIANT, HUMIDITY = (ROWS[name].to_numpy() for name in list(ROWS.columns)[:3])
MET = np.array([1.0, 1.2, 1.3, np.nan, 1.1])


def _expected(met, clo, air_speed, sitting):
    """The SET of the test of each row, with the posture of each row (NaN where an input is missing)."""
    values = np.full(len(ROWS), np.nan)
    for row in range(len(ROWS)):
        if not np.isnan([met[row], clo[row], air_speed[row]]).any():
            values[row] = _fake_set(AIR[row], RADIANT[row], air_speed[row], HUMIDITY[row], met[row], clo[row],
                                    'sitting' if sitting[row] else 'standing')
    return values


def test_the_set_of_the_results_with_the_inputs_of_the_people_objects(monkeypatch):
    monkeypatch.setattr(ch, 'standard_effective_temperature', _fake_set)
    hook = ch.SetSetpointHook(['Z1'], 28.0, 19.0, method='bisection')
    clo, speed = ROWS['CLO:Schedule Value [](Hourly)'].to_numpy(), ROWS['VEL:Schedule Value [](Hourly)'].to_numpy()
    # The schedules of the People object in each row; sitting with 1.2 met or less, as the hook; no SET with an
    # activity level of 0
    found = ch.set_of_results(ROWS, hook, people=PEOPLE)['SET_Z1'].to_numpy()
    np.testing.assert_allclose(found, _expected(MET, clo, speed, MET <= 1.2), rtol=0, atol=1e-12)
    assert np.isnan(found[3]) and not np.isnan(found[[0, 1, 2, 4]]).any()
    # The schedules of the hook (those that apply_set_setpoints and apply_sun2026_setpoints give it)
    hook.people = dict(PEOPLE)
    np.testing.assert_allclose(ch.set_of_results(ROWS, hook)['SET_Z1'].to_numpy(), found, rtol=0, atol=0)
    # The posture of the hook, and inputs of its own
    standing = ch.SetSetpointHook(['Z1'], 28.0, 19.0, method='bisection', position='standing')
    np.testing.assert_allclose(ch.set_of_results(ROWS, standing, people=PEOPLE)['SET_Z1'].to_numpy(),
                               _expected(MET, clo, speed, np.zeros(5, dtype=bool)), rtol=0, atol=1e-12)
    mixed = ch.SetSetpointHook(['Z1'], 28.0, 19.0, method='bisection', clo=0.6)
    np.testing.assert_allclose(ch.set_of_results(ROWS, mixed, people=PEOPLE)['SET_Z1'].to_numpy(),
                               _expected(MET, np.full(5, 0.6), speed, MET <= 1.2), rtol=0, atol=1e-12)
    # The clothing insulation of the dynamic clothing model (no SET where it is 0, as in the hook), or one of them as
    # the calculation method schedule says (2, the dynamic model)
    value = ROWS['PEOPLE Z1:Zone Thermal Comfort Clothing Value [clo](Hourly)'].to_numpy()
    dynamic = np.where(value > 0, value, np.nan)
    people = {'Z1': dict(PEOPLE['Z1'], clothing_source='dynamic')}
    np.testing.assert_allclose(ch.set_of_results(ROWS, hook, people=people)['SET_Z1'].to_numpy(),
                               _expected(MET, dynamic, speed, MET <= 1.2), rtol=0, atol=1e-12)
    people = {'Z1': dict(PEOPLE['Z1'], clothing_source='method')}
    method = np.where(ROWS['METHOD:Schedule Value [](Hourly)'].to_numpy() == 2, dynamic, clo)
    np.testing.assert_allclose(ch.set_of_results(ROWS, hook, people=people)['SET_Z1'].to_numpy(),
                               _expected(MET, method, speed, MET <= 1.2), rtol=0, atol=1e-12)
    # A hook with its own inputs does not read them
    own = ch.SetSetpointHook(['Z1'], 28.0, 19.0, method='bisection', met=1.2, clo=0.6, air_speed=0.2)
    np.testing.assert_allclose(ch.set_of_results(ROWS[list(ROWS.columns)[:3]], own, keys={'Z1': 'Z1'})['SET_Z1'],
                               _fake_set(AIR, RADIANT, 0.2, HUMIDITY, 1.2, 0.6, 'sitting'), rtol=0, atol=1e-12)


def test_the_set_of_the_results_with_the_fans_that_the_occupants_control(monkeypatch):
    # The question of the validation study of F3 (decided on 2026-11-13): with air_speed_heating, the air speed of the
    # People objects is that of the fans, which the occupants have only when they need it. The SET of each row is that
    # with air_speed_heating (not above the air speed of the row) while it is not above the cooling setpoint of the
    # SET of the hook, and that with the fans when it is
    monkeypatch.setattr(ch, 'standard_effective_temperature', _fake_set)
    clo, speed = ROWS['CLO:Schedule Value [](Hourly)'].to_numpy(), ROWS['VEL:Schedule Value [](Hourly)'].to_numpy()
    with_fans = _expected(MET, clo, speed, MET <= 1.2)
    without_fans = _expected(MET, clo, np.minimum(speed, 0.1), MET <= 1.2)
    np.testing.assert_allclose(with_fans, [21.3, 23.7, 23.3, np.nan, 21.1], rtol=0, atol=1e-12)
    np.testing.assert_allclose(without_fans, [21.3, 23.7, 24.3, np.nan, 21.5], rtol=0, atol=1e-12)
    hook = ch.SetSetpointHook(['Z1'], 24.0, 19.0, method='bisection', air_speed_heating=0.1)
    found = ch.set_of_results(ROWS, hook, people=PEOPLE)['SET_Z1'].to_numpy()
    # The third row is above 24 °C of SET without the fans (0.6 m/s): with them; the last one (0.3 m/s) is not
    np.testing.assert_allclose(found, [21.3, 23.7, 23.3, np.nan, 21.5], rtol=0, atol=1e-12)
    # With a cooling setpoint of the SET that no row reaches, no row has the fans; without air_speed_heating, all
    never = ch.SetSetpointHook(['Z1'], 28.0, 19.0, method='bisection', air_speed_heating=0.1)
    np.testing.assert_allclose(ch.set_of_results(ROWS, never, people=PEOPLE)['SET_Z1'].to_numpy(), without_fans,
                               rtol=0, atol=1e-12)
    always = ch.SetSetpointHook(['Z1'], 24.0, 19.0, method='bisection')
    np.testing.assert_allclose(ch.set_of_results(ROWS, always, people=PEOPLE)['SET_Z1'].to_numpy(), with_fans,
                               rtol=0, atol=1e-12)
    # A hook with its own inputs: its air speed is that of the fans (0.8 m/s), and that of still air 0.2 m/s
    own = ch.SetSetpointHook(['Z1'], 24.0, 19.0, method='bisection', met=1.2, clo=0.6, air_speed=0.8,
                             air_speed_heating=0.2)
    still = _fake_set(AIR, RADIANT, 0.2, HUMIDITY, 1.2, 0.6, 'sitting')
    assert (still > 24.0).any() and (still <= 24.0).any()
    np.testing.assert_allclose(ch.set_of_results(ROWS[list(ROWS.columns)[:3]], own, keys={'Z1': 'Z1'})['SET_Z1'],
                               np.where(still > 24.0, _fake_set(AIR, RADIANT, 0.8, HUMIDITY, 1.2, 0.6, 'sitting'),
                                        still), rtol=0, atol=1e-12)


def test_the_errors_of_the_set_of_the_results_with_the_inputs_of_the_people_objects(monkeypatch):
    monkeypatch.setattr(ch, 'standard_effective_temperature', _fake_set)
    hook = ch.SetSetpointHook(['Z1'], 28.0, 19.0, method='bisection')
    with pytest.raises(ValueError, match=r"reads \['met', 'clo', 'air_speed'\] from the People objects of the zones in "
                                         r"each timestep: give the schedules of the People objects of the zones "
                                         r"\['Z1'\]"):
        ch.set_of_results(ROWS, hook)
    # Without the output of a schedule: a clear error, which says how to request it
    without = ROWS.drop(columns=['CLO:Schedule Value [](Hourly)', 'VEL:Schedule Value [](Hourly)'])
    with pytest.raises(ch.MissingOccupantInputs, match=r"have not the outputs of the inputs of the occupants of the "
                                                       r"zone Z1 \(Schedule Value of 'Clo'; Schedule Value of 'Vel'\)"
                                                       r".*occupant_inputs=True") as error:
        ch.set_of_results(without, hook, people=PEOPLE)
    assert isinstance(error.value, ValueError)
    # The outputs of the zone, as before
    with pytest.raises(ValueError, match=r"have not the outputs \['Zone Air Relative Humidity'\] of the zone Z1"):
        ch.set_of_results(ROWS.drop(columns=['Z1:Zone Air Relative Humidity [%](Hourly)']), hook, people=PEOPLE)


def _people(zone, number):
    return _Obj(key='PEOPLE', Name=f'People {zone}', Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone,
                Activity_Level_Schedule_Name=f'Act {number}', Work_Efficiency_Schedule_Name='Work',
                Clothing_Insulation_Calculation_Method='ClothingInsulationSchedule',
                Clothing_Insulation_Calculation_Method_Schedule_Name='',
                Clothing_Insulation_Schedule_Name=f'Clo {number}', Air_Velocity_Schedule_Name='Vel')


#: The model of the tests of the indicators, with the schedules of its People objects
MODEL = dict(DESIGNBUILDER, building=_FakeIDF(*_zone('Block1:Zone1'), *_zone('Block1:Zone2'),
                                              _people('Block1:Zone1', 1), _people('Block1:Zone2', 2)))
#: The model of the simulation of the table (the name of its CSV file up to its weather file)
MODEL_NAME = CSV_NAME[:-len('.csv')].rsplit('[', 1)[0] + '.idf'
#: The values of the schedules in each hour of the two days of the table: the first day, 1.05 met (sitting), 1.0 clo
#: and 0.1 m/s; the second one, 1.25 met (standing), 0.5 clo and 0.6 m/s in Block1:Zone1, and those of the first day
#: in Block1:Zone2
FIRST_DAY = np.arange(48) < 24
INPUTS = {
    'Block1:Zone1': dict(met=np.where(FIRST_DAY, 1.05, 1.25), clo=np.where(FIRST_DAY, 1.0, 0.5)),
    'Block1:Zone2': dict(met=np.full(48, 1.05), clo=np.full(48, 1.0)),
}
SPEED = np.where(FIRST_DAY, 0.1, 0.6)


def _people_table(tmp_path, monkeypatch, schedules=True):
    columns, zones = _indicator_columns(MODEL)
    conditions = _add_set_conditions(columns, MODEL, {zone: data['top'] for zone, data in zones.items()})
    if schedules:
        for number, values in enumerate(INPUTS.values(), start=1):
            columns[f'ACT {number}:Schedule Value [](Hourly)'] = list(values['met'] * ch.MET_ACTIVITY_LEVEL)
            columns[f'CLO {number}:Schedule Value [](Hourly)'] = list(values['clo'])
        columns['VEL:Schedule Value [](Hourly)'] = list(SPEED)
    table = _indicator_table(tmp_path, monkeypatch, MODEL, columns, indoor_adaptation_indicators=False)
    monkeypatch.setattr(ch, 'standard_effective_temperature', _fake_set)
    return table, conditions


def _set_of_zone(conditions, zone, met=None, clo=None, speed=None, position=None):
    air, radiant, humidity = conditions[zone]
    met = INPUTS[zone]['met'] if met is None else np.full(48, met)
    clo = INPUTS[zone]['clo'] if clo is None else np.full(48, clo)
    speed = SPEED if speed is None else np.full(48, speed)
    sitting = met <= 1.2 if position is None else np.full(48, position == 'sitting')
    return np.array([_fake_set(air[row], radiant[row], speed[row], humidity[row], met[row], clo[row],
                               'sitting' if sitting[row] else 'standing') for row in range(48)])


def test_the_indicators_with_the_inputs_of_the_people_objects(tmp_path, monkeypatch):
    table, conditions = _people_table(tmp_path, monkeypatch)
    df, occupied = table.df, table.occupied_zone_list
    # The model of the simulation, in the folder of the table: the name of its CSV file up to its weather file
    (tmp_path / MODEL_NAME).write_text('', encoding='utf-8')
    default = ia.table_indicators(df, occupied)
    found = ia.table_indicators(df, occupied, pythermalcomfort_set='people')
    pd.testing.assert_frame_equal(found[list(default.columns)], default)
    row = found.iloc[0]
    for zone in occupied:
        for title, value in _band(_set_of_zone(conditions, zone), OCCUPIED).items():
            assert row[f'{zone}_{title}'] == pytest.approx(value), (zone, title)
    # The same with each input, and with the capitals of 'People'
    same = ia.table_indicators(df, occupied, pythermalcomfort_set={'met': 'People', 'clo': 'people',
                                                                 'air_speed': 'PEOPLE'})
    pd.testing.assert_frame_equal(same, found)
    # Some inputs of the People objects and others given, with a posture
    row = ia.table_indicators(df, occupied, pythermalcomfort_set={'met': 'people', 'clo': 0.6, 'air_speed': 'people',
                                                                'position': 'standing'}).iloc[0]
    for zone in occupied:
        for title, value in _band(_set_of_zone(conditions, zone, clo=0.6, position='standing'), OCCUPIED).items():
            assert row[f'{zone}_{title}'] == pytest.approx(value), (zone, title)
    # The model of the key 'idf', for all the simulations
    (tmp_path / MODEL_NAME).unlink()
    (tmp_path / 'other.idf').write_text('', encoding='utf-8')
    other = ia.table_indicators(df, occupied, pythermalcomfort_set={'met': 'people', 'clo': 'people',
                                                                  'air_speed': 'people', 'idf': 'other.idf'})
    pd.testing.assert_frame_equal(other, found)
    # A hook of the SET that reads them, with the schedules of the People objects of its model (no file is read)
    (tmp_path / 'other.idf').unlink()
    hook = ch.SetSetpointHook(['Block1_Zone1', 'Block1_Zone2'], 28.0, 19.0, method='bisection')
    hook.people = ch.people_inputs(MODEL['building'])
    pd.testing.assert_frame_equal(ia.table_indicators(df, occupied, pythermalcomfort_set=hook), found)


def test_the_indicators_with_the_fans_that_the_occupants_control(tmp_path, monkeypatch):
    from .test_indoor_adaptation import BAND

    table, conditions = _people_table(tmp_path, monkeypatch)
    df, occupied = table.df, table.occupied_zone_list
    (tmp_path / MODEL_NAME).write_text('', encoding='utf-8')
    # The air velocity schedule has 0.1 m/s the first day and 0.6 m/s, the fans, the second one: with
    # 'air_speed_heating', the SET of each row is that of 0.1 m/s while it is not above the upper limit of the causal
    # band, and that of the fans when it is
    inputs = {'met': 'people', 'clo': 'people', 'air_speed': 'people', 'air_speed_heating': 0.1}
    row = ia.table_indicators(df, occupied, pythermalcomfort_set=inputs).iloc[0]
    people = ia.table_indicators(df, occupied, pythermalcomfort_set='people').iloc[0]
    differ = []
    for zone in occupied:
        without_fans, with_fans = _set_of_zone(conditions, zone, speed=0.1), _set_of_zone(conditions, zone)
        controlled = np.where(without_fans > BAND[1], with_fans, without_fans)
        for title, value in _band(controlled, OCCUPIED).items():
            assert row[f'{zone}_{title}'] == pytest.approx(value), (zone, title)
        # Occupied hours with the fans and without them, the second day: where the occupants do not need the fans,
        # their SET is above that of the air speed of the People objects
        on = (OCCUPIED > 0) & ~FIRST_DAY & (without_fans > BAND[1])
        off = (OCCUPIED > 0) & ~FIRST_DAY & ~on
        differ.append((bool(on.any()), bool(off.any())))
        mean, mean_people = (found[f'{zone}_Mean SET_pythermalcomfort (°C)'] for found in (row, people))
        assert mean > mean_people if off.any() else mean == mean_people
    # The occupants of the first zone do not need the fans in any occupied hour of the second day, and those of the
    # second zone need them in all
    assert differ == [(False, True), (True, False)]
    # A hook of the SET with it: the fans are on above its own cooling setpoint of the SET
    hook = ch.SetSetpointHook(['Block1_Zone1', 'Block1_Zone2'], 26.0, 19.0, method='bisection', air_speed_heating=0.1)
    hook.people = ch.people_inputs(MODEL['building'])
    row = ia.table_indicators(df, occupied, pythermalcomfort_set=hook).iloc[0]
    for zone in occupied:
        without_fans, with_fans = _set_of_zone(conditions, zone, speed=0.1), _set_of_zone(conditions, zone)
        for title, value in _band(np.where(without_fans > 26.0, with_fans, without_fans), OCCUPIED).items():
            assert row[f'{zone}_{title}'] == pytest.approx(value), (zone, title)
    # The upper limit of the band of tsv_limit, without its warning again
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        made = [ia._pythermalcomfort_hook(inputs, occupied, limit)[0] for limit in (None, 1.0)]
    assert [(item.set_heating_setpoint, item.set_cooling_setpoint) for item in made] == [
        pytest.approx(BAND), pytest.approx((1.6 / 0.11, 3.6 / 0.11))]
    assert [item.air_speed_heating for item in made] == [0.1, 0.1]
    assert ia._pythermalcomfort_hook('people', occupied)[0].air_speed_heating is None
    for value, message in (({**inputs, 'air_speed_heating': 'people'}, 'air_speed_heating must be a number'),
                           ({**inputs, 'air_speed_cooling': 0.6},
                            r"takes \['met', 'clo', 'air_speed', 'position', 'air_speed_heating'\] \(and 'idf'\), not "
                            r"\['air_speed_cooling'\]")):
        with pytest.raises(ValueError, match=message):
            ia.table_indicators(df, occupied, pythermalcomfort_set=value)


def test_the_errors_of_the_indicators_with_the_inputs_of_the_people_objects(tmp_path, monkeypatch):
    table, _ = _people_table(tmp_path, monkeypatch, schedules=False)
    df, occupied = table.df, table.occupied_zone_list
    # The model of the simulation is not in the folder
    with pytest.raises(ValueError, match=r'the name of the CSV file of the simulation up to its weather file\) is not '
                                         r'a file of the current folder'):
        ia.table_indicators(df, occupied, pythermalcomfort_set='people')
    with pytest.raises(ValueError, match=r"'missing.idf' \(its key idf\) is not a file"):
        ia.table_indicators(df, occupied, pythermalcomfort_set={'met': 'people', 'clo': 0.5, 'air_speed': 0.1,
                                                              'idf': 'missing.idf'})
    # The CSV file has not the outputs of the schedules: an error that says how to request them, not NaN
    (tmp_path / MODEL_NAME).write_text('', encoding='utf-8')
    with pytest.raises(ch.MissingOccupantInputs, match=r"Schedule Value of 'Act 1'.*occupant_inputs=True"):
        ia.table_indicators(df, occupied, pythermalcomfort_set='people')
    # A zone of the table without People objects in the model
    with pytest.raises(ValueError, match=r"The zones \['Block1:Zone9'\] of the table have no People objects"):
        ia._pythermalcomfort_set_of_rows(df, df['Source'].iloc[0], ia._pythermalcomfort_hook('people', occupied)[0],
                                         ['Block1:Zone9'])
    for value, message in (('occupants', 'pythermalcomfort_set must be None, a dict'),
                           ({'met': 'people', 'clo': 0.6}, r"needs the metabolic rate.*or 'people' for those of the "
                                                           r"People objects.*\['air_speed'\]: they are not given"),
                           ({'met': 'people', 'clo': 'schedule', 'air_speed': 0.1}, 'clo must be a number'),
                           # A hook that reads them without the schedules of the People objects of its model
                           (ch.SetSetpointHook(['Block1_Zone1'], 28.0, 19.0, method='bisection'),
                            r"\['met', 'clo', 'air_speed'\]: the hook reads them from the People objects, and has "
                            r"not their schedules")):
        with pytest.raises(ValueError, match=message):
            ia.table_indicators(df, occupied, pythermalcomfort_set=value)


# EnergyPlus ---------------------------------------------------------------------------------------------------------

@needs_energyplus
def test_the_set_of_the_results_is_that_of_the_hook_of_comfort_standard_24(tmp_path, monkeypatch):
    # A summer week of the sample model with comfort standard 24 (the backend of the API and its hook), with the
    # outputs of the inputs of the occupants: the SET of pythermalcomfort of each row of the results, with the
    # schedules of the People objects, against the SET that the hook reports (that of the values of its sensors, those
    # of the previous timestep), and the indicators of the causal band of both
    pytest.importorskip('pythermalcomfort.models')
    from accim.data.postprocessing.main import Table
    from accim.run import run_ep
    from accim.sim.accis import load_idf
    from accim.sim.people import add_thermal_comfort_outputs

    from .test_sun2026_set import STEPS, _sun2026_model

    model, hook = _sun2026_model(tmp_path / 'model', monkeypatch, (7, 15), (7, 21))
    idf = load_idf(model)
    before = len(_requested(idf))
    add_thermal_comfort_outputs(idf, 'Pierce', output_frequencies=['timestep'], occupant_inputs=True)
    # The model of the hook requests the conditions of the zones and the SET of the Pierce model already: the new
    # outputs are the PMV of the Pierce model and the schedules of the People objects
    added = _requested(idf)[before:]
    schedules = [name for pair in SCHEDULES.values() for name in pair] + [AIR_VELOCITY]
    assert sorted(key for key, name, frequency in added if name == 'Schedule Value') == sorted(schedules)
    assert {(name, frequency) for _, name, frequency in added} == {
        ('Schedule Value', 'Timestep'), ('Zone Thermal Comfort Pierce Model Standard Effective Temperature PMV',
                                         'Timestep')}
    idf.save()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        [result] = run_ep(only_accim_idfs=False, confirm=True, processes=1, backend='api', hooks=[hook])
    assert result.success, result.error
    results = pd.read_csv(model.parent / 'sun[Seville.csv')
    assert len(results) == 7 * 24 * STEPS

    def column(start):
        return results[next(c for c in results.columns if c.upper().startswith(start.upper()))].to_numpy(dtype=float)

    # The schedules of the hook (apply_sun2026_setpoints gives them to it), or those of the model
    found = ch.set_of_results(results, hook)
    pd.testing.assert_frame_equal(ch.set_of_results(results, hook, people=ch.people_inputs(load_idf(model))), found)
    # At the beginning of each timestep, the sensors of the hook read the mean air temperature and the relative
    # humidity of the previous timestep (those of the previous row) and the mean radiant temperature that EnergyPlus
    # has calculated for the timestep (that of the row itself); the schedules are those of the timestep. With them,
    # the SET of the results is that of the hook (the CSV file has 6 significant digits)
    shifted = results.copy()
    for zone in ZONES:
        for name in ('Zone Mean Air Temperature', 'Zone Air Relative Humidity'):
            key = f"{zone.replace('_', ':')}:{name} [".upper()
            [name_of_column] = [c for c in results.columns if c.upper().startswith(key)]
            shifted[name_of_column] = results[name_of_column].shift(1)
    as_the_hook = ch.set_of_results(shifted, hook)
    for zone in ZONES:
        reported = column(f'EMS:SET_{zone} [')
        np.testing.assert_allclose(as_the_hook[f'SET_{zone}'].to_numpy()[1:], reported[1:], rtol=0, atol=1e-3)
        # With the conditions of each row (the means of its timestep), as set_of_results and the indicators take
        # them, it is within 0.02 K of that of the hook on average (measured: 0.012 and 0.013 K, at most 0.14 K)
        computed = found[f'SET_{zone}'].to_numpy()
        assert not np.isnan(computed).any()
        difference = np.abs(reported - computed)[1:]
        assert difference.mean() < 0.02 and difference.max() < 0.2, (zone, difference.mean(), difference.max())
    # The indicators of the causal band with the inputs of the People objects, in the folder of the simulation (the
    # model of 'sun[Seville.csv' is 'sun.idf'), against the outputs of the hook
    monkeypatch.chdir(model.parent)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        table = Table(datasets=['sun[Seville.csv'], source_frequency='timestep', frequency='timestep',
                      frequency_agg_func='sum', standard_outputs=True, level=['building'],
                      level_agg_func=['sum', 'mean'], level_excluded_zones=[], idf_path='sun.idf')
        row = ia.table_indicators(table.df, table.occupied_zone_list, pythermalcomfort_set='people').iloc[0]
    assert sorted(name.upper() for name in table.occupied_zone_list) == [zone.replace('_', ':').upper()
                                                                         for zone in ZONES]
    for zone in ZONES:
        [name] = [name for name in table.occupied_zone_list if name.upper() == zone.replace('_', ':').upper()]
        hours = column(f'EMS:Occupied Hours_{zone} [')
        reported = column(f'EMS:SET_{zone} [')
        in_band = column(f'EMS:HoursInCausalBand_{zone} [').sum()
        # With the rows of each timestep, the hours within the band are those of the hook (measured: 27.8 and 34.3 of
        # the 60 occupied hours of each zone; one timestep of margin), and the mean SET differs by 0.001 K
        assert row[f'{name}_Mean SET_pythermalcomfort (°C)'] == pytest.approx(
            (reported * hours).sum() / hours.sum(), abs=0.005)
        assert row[f'{name}_Hours In Causal Band_pythermalcomfort (h)'] == pytest.approx(in_band, abs=1 / STEPS + 1e-6)
        assert 0 < in_band < hours.sum()
        # The SET of the Pierce model of EnergyPlus, which the indicators without pythermalcomfort_set take, is 0.2 K
        # higher in this week (1.06 met, 0.5 clo), and has 3.2 hours less within the band
        assert (row[f'{name}_Mean SET_Pierce (°C)'] - row[f'{name}_Mean SET_pythermalcomfort (°C)']
                ) == pytest.approx(0.2, abs=0.05)
        assert in_band - row[f'{name}_Hours In Causal Band (h)'] == pytest.approx(3.17, abs=0.5)
