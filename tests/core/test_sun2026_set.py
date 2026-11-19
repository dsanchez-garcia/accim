"""Tests for comfort standard 24, INT Sun2026 SET (task F1 of block F, ``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``,
with the decisions of the author of 2026-11-10): the causal SET model of Sun, Brager & Schiavon (2026), Energy and
Buildings 370, 118097 (Fig. 7a: TSV = 0.11·SET − 2.6; the band of TSV ±0.5 is 19.1 to 28.2 °C of SET, and the neutral
SET 23.6 °C), whose setpoints a hook of the backend of the Python API of EnergyPlus sets by inverting the SET of
pythermalcomfort (``pythermalcomfort.models.set_tmp``) by bisection, with the inputs of the People objects of the zones
and, by default, their mean radiant temperature (:mod:`accim.sim.comfort_hooks`).

The unit tests use a fake controller and the Erl interpreter of accim; the last tests simulate the sample model with
EnergyPlus 25.1, through its Python API, and compare the SET of the hook with that of the Pierce model of EnergyPlus
hour by hour (the differences measured are in ``notes/decisions.md``: F1, 2026-11-10, and the range of the setpoints,
2026-11-18; measured again on 2026-11-19, with the windows of the sample model closed on its design days, see
``MEASURED``; the test reproduces them).
"""
import re
import shutil
import warnings

import numpy as np
import pandas as pd
import pytest

from accim.sim import comfort_hooks as ch
from accim.sim import standards as st

from ._optional import pythermalcomfort_models
from .test_comfort_hooks import (CALLING_POINT, EPW, SAMPLE_IDF, STEPS, ZONES, _Controller, _given, _hook_erl,
                                 _hook_timestep, _model, needs_energyplus, needs_idd)

#: The activity level of the People objects of the sample model (W/person) and its metabolic rate (met)
ACTIVITY = 110.7
MET = ACTIVITY / (58.2 * 1.8)


def test_the_setpoints_of_the_set_of_comfort_standard_24():
    # The band of TSV ±0.5 of Sun, Brager & Schiavon (2026): SET = (∓0.5 + 2.6)/0.11, 19.09 and 28.18 °C
    heating, cooling = ch.sun2026_set_setpoints()
    assert (heating, cooling) == pytest.approx(((-0.5 + 2.6) / 0.11, (0.5 + 2.6) / 0.11), abs=1e-12)
    assert (round(heating, 2), round(cooling, 2)) == (19.09, 28.18)
    assert ch.causal_tsv(heating) == pytest.approx(-0.5) and ch.causal_tsv(cooling) == pytest.approx(0.5)
    assert ch.causal_tsv(np.array([heating, cooling])) == pytest.approx([-0.5, 0.5])
    # The neutral SET as the paper gives it (the equation gives 2.6/0.11 = 23.64 °C)
    assert ch.SUN2026_NEUTRAL_SET == 23.6 and abs(ch.causal_tsv(23.6)) < 0.005
    # Categories 80 and 90 give the same band; the comfort modes by number or name
    for arguments in (dict(category=80), dict(category=90), dict(comfort_mode='SET band'),
                      dict(comfort_mode=' set band '), dict(tsv_limit=0.5)):
        assert ch.sun2026_set_setpoints(**arguments) == (heating, cooling)
    for mode in (2, 'SET neutral +/- offset', 'SET neutral ± offset'):
        assert ch.sun2026_set_setpoints(mode, set_offset=2.0) == pytest.approx((21.6, 25.6))
    # 0.7 and 1.0 are a linear extrapolation of the published model, with a warning
    for limit in (0.7, 1.0):
        with pytest.warns(UserWarning, match='linear extrapolation of the causal SET model'):
            extrapolated = ch.sun2026_set_setpoints(tsv_limit=limit)
        assert ch.causal_tsv(np.array(extrapolated)) == pytest.approx([-limit, limit])
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        ch.sun2026_set_setpoints(category=90)
    for arguments, message in ((dict(tsv_limit=0.6), 'tsv_limit must be 0.5'),
                               (dict(category=85), 'category must be 80 or 90'),
                               (dict(category=True), 'category must be 80 or 90'),
                               (dict(comfort_mode=3), 'comfort_mode must be one of 1'),
                               (dict(comfort_mode='band'), 'comfort_mode must be one of 1'),
                               (dict(comfort_mode=True), 'comfort_mode must be one of 1'),
                               (dict(set_offset=2.0), 'set_offset is only used with comfort mode 2'),
                               (dict(comfort_mode=2), 'needs set_offset'),
                               (dict(comfort_mode=2, set_offset=0), 'set_offset must be greater than 0')):
        with pytest.raises(ValueError, match=message):
            ch.sun2026_set_setpoints(**arguments)


@needs_idd
def test_comfort_modes_0_and_3_of_comfort_standard_24_give_a_clear_error(tmp_path):
    # Verdict 16 of the review of 1.2.0 (task S5): comfort standard 24 has comfort modes 1 and 2 only; 0 (the static
    # setpoints of the other comfort standards) and 3 raise a ValueError that names the valid ones, also when the hook
    # is made and when the model is prepared (before it changes)
    message = r"comfort_mode must be one of 1 \('SET band'\), 2 \('SET neutral \+/- offset'\), not {}\."
    idf = _model(tmp_path)
    before = idf.idfstr()
    for mode in (0, 3, '0', 0.0):
        with pytest.raises(ValueError, match=message.format(re.escape(repr(mode)))):
            ch.sun2026_set_setpoints(mode)
        with pytest.raises(ValueError, match=message.format(re.escape(repr(mode)))):
            ch.Sun2026SetpointHook(ZONES, comfort_mode=mode)
        with pytest.raises(ValueError, match=message.format(re.escape(repr(mode)))):
            ch.apply_sun2026_setpoints(idf, comfort_mode=mode)
    assert idf.idfstr() == before
    assert list(st.get_comfort_standard(24).comfort_modes) == [1, 2]


def test_comfort_standard_24_has_no_ems_code():
    from accim.gui import forms
    from accim.sim.generation import GenerationArguments, zone_arguments_errors
    from accim.utils.ems_code import get_setpoint_ems_code

    standard = st.get_comfort_standard(24)
    assert (standard.label, standard.title) == ('INT Sun2026 SET',
                                                '24 = INT Sun, Brager & Schiavon 2026 (causal SET band)')
    assert list(standard.categories) == [80, 90]
    assert list(standard.comfort_modes) == list(ch.SUN2026_COMFORT_MODES) == [1, 2]
    assert st.HOOK_COMFORT_STANDARDS == {24: 'accim.sim.comfort_hooks.apply_sun2026_setpoints'}
    assert st.hook_comfort_standard_error(1) is None and st.hook_comfort_standard_error([24]) is None
    reason = st.hook_comfort_standard_error(24)
    assert reason.startswith('comfort standard 24 (24 = INT Sun, Brager & Schiavon 2026 (causal SET band)) has no '
                             'EMS code') and reason.endswith('apply_sun2026_setpoints')
    # AddAccis, modify_accis (the arguments of the zones), the EMS code and the GUI do not take it
    with pytest.raises(ValueError, match='AddAccis cannot write comfort standard 24'):
        GenerationArguments(comfort_standard=[1, 24], category=[80], comfort_mode=[1])
    errors = zone_arguments_errors(dict(comfort_standard=24, category=80, comfort_mode=1, hvac_mode=0,
                                        ventilation_control=0), mixed_mode=False)
    assert errors == [reason]
    with pytest.raises(ValueError, match='has no EMS code'):
        get_setpoint_ems_code(24, 80, 1)
    assert 24 not in [number for number, _ in forms.comfort_standard_choices()]
    assert 23 in [number for number, _ in forms.comfort_standard_choices()]


@pytest.mark.parametrize('clo', [0.5, 1.0])
@pytest.mark.parametrize('air_speed', [0.1, 0.8])
@pytest.mark.parametrize('humidity', [40.0, 70.0])
def test_the_inversion_of_the_set(clo, air_speed, humidity):
    set_tmp = pythermalcomfort_models().set_tmp
    targets = ch.sun2026_set_setpoints()
    # With the mean radiant temperature equal to the air temperature, and with that of the zone (20 °C)
    for tr_mode, radiant in (('equal_air', None), ('zone', 20.0)):
        hook = ch.Sun2026SetpointHook(['Z'], tr_mode=tr_mode)
        assert (hook.set_heating_setpoint, hook.set_cooling_setpoint) == targets and hook.tolerance_k == 0.05
        temperatures = hook.inverted_temperatures(humidity, radiant, met=1.1, clo=clo, air_speed=air_speed)
        assert 10 < temperatures[0] < temperatures[1] < 40
        for temperature, target in zip(temperatures, targets):
            found = float(set_tmp(tdb=temperature, tr=temperature if radiant is None else radiant, v=air_speed,
                                  rh=humidity, met=1.1, clo=clo, position='sitting', limit_inputs=False,
                                  round_output=False).set)
            # The SET of the solution is within 0.05 K of its target (the width of the last interval is 0.05 K or
            # less, and the SET grows less than the temperature)
            assert abs(found - target) <= 0.05, (tr_mode, temperature, found, target)
        operative = hook.operative_temperatures(humidity, radiant, met=1.1, clo=clo, air_speed=air_speed)
        if radiant is None:
            assert operative == temperatures
        else:
            # The air temperatures, given to the thermostats of the ACCIS as operative temperatures
            assert operative == pytest.approx(((temperatures[0] + 20) / 2, (temperatures[1] + 20) / 2), abs=1e-12)
    with pytest.raises(ValueError, match="With tr_mode='zone', the mean radiant temperature"):
        ch.Sun2026SetpointHook(['Z']).inverted_temperatures(humidity, None, met=1.1, clo=clo, air_speed=air_speed)
    with pytest.raises(ValueError, match='The hook reads met from the People objects'):
        ch.Sun2026SetpointHook(['Z']).inverted_temperatures(humidity, 20.0, clo=clo, air_speed=air_speed)


def _zone_values(zone, air, radiant, humidity=45.0, occupants=2.0, **people):
    values = {f'SET_RH_{zone}': humidity, f'SET_MAT_{zone}': air, f'SET_MRT_{zone}': radiant,
              f'SET_Act_{zone}': ACTIVITY, f'SET_Vel_{zone}': 0.137, f'Occ_count_{zone}': occupants}
    values.update({f'{name}_{zone}': value for name, value in people.items()})
    return values


def test_the_heating_setpoint_below_18_and_the_minimum():
    pythermalcomfort_models()
    # The inversion of SET 19 °C (the band of the paper, rounded) at 1.0 clo, 1.1 met, 0.1 m/s and 40 % of relative
    # humidity with the mean radiant temperature equal to the air temperature: 15.8 °C (section 2.3 of the proposal of
    # block F); with the band of TSV ±0.5 (19.09 °C), 15.9 °C sitting
    for position in ('standing', 'sitting'):
        rounded = ch.SetSetpointHook(['Z'], 28.0, 19.0, met=1.1, clo=1.0, air_speed=0.1, position=position,
                                     method='bisection', tolerance_k=0.05)
        assert round(rounded.operative_temperatures(40.0)[0], 1) == 15.8
    hook = ch.Sun2026SetpointHook(ZONES, tr_mode='equal_air', met=1.1, clo=1.0, air_speed=0.1,
                                  heating_minimums={ZONES[0]: 18.0})
    assert hook.heating_minimums == {ZONES[0]: 18.0, ZONES[1]: None}
    heating, cooling = hook.operative_temperatures(40.0)
    assert round(heating, 1) == 15.9
    controller = _Controller({'ZoneTimeStep': 0.25, **_zone_values(ZONES[0], 20.0, 20.0, 40.0),
                              **_zone_values(ZONES[1], 20.0, 20.0, 40.0)})
    # Without a minimum heating setpoint, the zone warns, naming the argument, once
    with pytest.warns(UserWarning) as record:
        hook(controller, CALLING_POINT)
    messages = [str(item.message) for item in record if 'comfort standard 24' in str(item.message)]
    assert len(messages) == 1 and f'zone {ZONES[1]} is 15.90 °C, below 18.0 °C' in messages[0]
    assert 'give heating_setpoint_minimum' in messages[0]
    assert hook.low_heating_setpoints == {ZONES[1]: heating}
    assert _given(controller, ZONES[0]) == _given(controller, ZONES[1]) == (heating, cooling)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        hook(controller, CALLING_POINT)
    # The minimum of B5 (18 °C) bounds it in the EMS after the hook: the setpoint without the tolerance is the minimum,
    # and the thermostat gets it with the tolerance (0.1 K; finding A19 of the self-audit of 2026-11-11); without the
    # minimum, the thermostats get the setpoint of the hook with the tolerance
    bounded = _hook_timestep(_hook_erl(heating_setpoint_minimum=18.0), setpoints=(heating, cooling))
    assert (bounded['AHST_Act_Zone1'], bounded['AHSTnoTol_Zone1']) == (18.0 + 0.1, 18.0)
    free = _hook_timestep(_hook_erl(), setpoints=(heating, cooling))
    assert free['AHST_Act_Zone1'] == pytest.approx(heating + 0.1, abs=1e-4) and free['AHST_Act_Zone1'] < 18


def test_the_heating_setpoint_of_comfort_standard_24_with_a_warm_mean_radiant_temperature():
    # The question of 2026-11-17 in notes/questions.md, decided by the author on 2026-11-18: with the inputs of the
    # People objects of the sample model in January (1.06 met, 1.0 clo, 0.137 m/s), 45 % of relative humidity and a
    # mean radiant temperature of 25 °C, the air temperature whose SET is the heating setpoint of the SET (19.09 °C) is
    # 4.9 °C, within the range of the bisection of the air temperature, −5 to 55 °C (that of the setpoints of the
    # thermostats, 10 to 40 °C), and the heating setpoint 15.0 °C. With the range of before, 10 to 40 °C for the air
    # temperature, it was at the limit, and the heating setpoint (10 + 25)/2 = 17.5 °C
    pythermalcomfort_models()
    hook = ch.Sun2026SetpointHook(['Z'])
    inputs = (45.0, 25.0, MET, 1.0, 0.137)
    air = hook.inverted_temperatures(*inputs)
    heating, cooling = hook.operative_temperatures(*inputs)
    assert hook._bisection_range(25.0) == (-5.0, 55.0) and -5.0 < air[0] < 10.0
    assert (heating, cooling) == ((air[0] + 25.0) / 2, (air[1] + 25.0) / 2) and round(heating, 1) == 15.0
    assert not hook.saturated(heating, cooling)
    # The SET of the air temperatures found is that of the setpoints of the SET, within the tolerance of the bisection
    for value, target in zip(air, hook.band):
        assert ch.standard_effective_temperature(value, 25.0, 0.137, 45.0, MET, 1.0, 'sitting') == pytest.approx(
            target, abs=0.02)
    # With the range from 18 °C, the heating setpoint is 18 °C, at the limit: the air temperature 2·18 − 25 = 11 °C
    narrow = ch.Sun2026SetpointHook(['Z'], temperature_range=(18.0, 40.0))
    assert narrow.inverted_temperatures(*inputs)[0] == 11.0 and narrow.operative_temperatures(*inputs)[0] == 18.0
    assert narrow.saturated(*narrow.operative_temperatures(*inputs))


def test_the_hook_of_comfort_standard_24_reads_the_people_objects():
    pythermalcomfort_models()
    hook = ch.Sun2026SetpointHook(ZONES, clothing_sources={ZONES[0]: 'schedule', ZONES[1]: 'method'})
    assert (hook.tr_mode, hook.met, hook.clo, hook.air_speed, hook.position) == ('zone', None, None, None, None)
    assert (hook.comfort_mode, hook.category, hook.tsv_limit, hook.method) == (1, 80, 0.5, 'bisection')
    assert hook.band == ch.sun2026_set_setpoints()
    # Zone 1: its clothing insulation schedule; zone 2: the calculation method schedule (2) chooses the clothing
    # insulation of the dynamic model. Zone 1 is warm enough not to warn; zone 2 warns once: with 0.8 clo and 31 °C of
    # mean radiant temperature, its heating setpoint is 15.7 °C (until the decision of 2026-11-18 on the range of the
    # setpoints, its air temperature was at the lower limit of 10 °C, and the setpoint (10 + 31)/2 = 20.5 °C)
    values = {'ZoneTimeStep': 1 / 6,
              **_zone_values(ZONES[0], 23.0, 24.0, SET_Clo=0.5),
              **_zone_values(ZONES[1], 30.0, 31.0, SET_Clo=0.5, SET_CloValue=0.8, SET_CloMethod=2.0)}
    controller = _Controller(values)
    with pytest.warns(UserWarning) as record:
        hook(controller, CALLING_POINT)
    messages = [str(item.message) for item in record]
    assert len(messages) == 1 and f'of the zone {ZONES[1]} is 15.73 °C, below 18.0 °C' in messages[0], messages
    expected = {}
    for zone, (air, radiant, clo) in zip(ZONES, ((23.0, 24.0, 0.5), (30.0, 31.0, 0.8))):
        found = hook.inverted_temperatures(45.0, radiant, MET, clo, 0.137)
        assert _given(controller, zone) == ((found[0] + radiant) / 2, (found[1] + radiant) / 2)
        # The SET, the causal TSV and the occupied hours within the band of the zone
        value = ch.standard_effective_temperature(air, radiant, 0.137, 45.0, MET, clo, 'sitting')
        expected[zone] = value
        assert controller.get(f'SET_{zone}') == value
        assert controller.get(f'TSV_causal_{zone}') == pytest.approx(0.11 * value - 2.6, abs=1e-12)
    assert hook.band[0] <= expected[ZONES[0]] <= hook.band[1] < expected[ZONES[1]]
    assert controller.get(f'HoursInCausalBand_{ZONES[0]}') == pytest.approx(1 / 6)
    assert controller.get(f'HoursInCausalBand_{ZONES[1]}') == 0
    # Unoccupied, no hours; the calculation method schedule 1 chooses the clothing insulation schedule
    controller.set(f'Occ_count_{ZONES[0]}', 0.0)
    controller.set(f'SET_CloMethod_{ZONES[1]}', 1.0)
    hook(controller, CALLING_POINT)
    assert controller.get(f'HoursInCausalBand_{ZONES[0]}') == 0
    assert controller.get(f'SET_{ZONES[1]}') == ch.standard_effective_temperature(30.0, 31.0, 0.137, 45.0, MET, 0.5,
                                                                                    'sitting')
    # The clothing insulation of the dynamic model is 0 until EnergyPlus calculates it, and the activity level and the
    # mean radiant temperature must have a value: no setpoints of the hook in that timestep
    for name, value in ((f'SET_CloMethod_{ZONES[1]}', 2.0), (f'SET_CloValue_{ZONES[1]}', 0.0)):
        controller.set(name, value)
    controller.set(f'SET_MRT_{ZONES[0]}', None)
    controller.set(f'HookSetpoints_{ZONES[0]}', 0.0)
    controller.set(f'HookSetpoints_{ZONES[1]}', 0.0)
    hook(controller, CALLING_POINT)
    assert _given(controller, ZONES[0]) is None and _given(controller, ZONES[1]) is None
    # The posture of the metabolic rate of each timestep: standing above 1.2 met
    assert hook.posture(1.2) == 'sitting' and hook.posture(1.3) == 'standing'
    assert ch.MET_ACTIVITY_LEVEL == pytest.approx(104.76)


def test_the_air_speed_of_the_heating_setpoint_with_the_fans_that_the_occupants_control():
    # The question of the validation study of F3 (2026-11-12, decided on 2026-11-13): one air speed converts both
    # limits of the band of the SET, so the fans raise the heating setpoint as well as the cooling one
    pythermalcomfort_models()
    limits = (28.18, 19.09)
    inputs = dict(met=1.1, clo=0.5, method='bisection', tolerance_k=0.01)
    still, fans = (ch.SetSetpointHook(['Z'], *limits, air_speed=speed, **inputs) for speed in (0.1, 1.2))
    assert [round(value, 1) for hook in (still, fans) for value in hook.operative_temperatures(50.0)] == [
        20.1, 28.9, 23.9, 32.5]
    assert still.air_speed_heating is None and still.heating_air_speed(0.7) == 0.7
    # With air_speed_heating, the heating setpoint is that of still air, and the cooling setpoint that of the fans
    both = ch.SetSetpointHook(['Z'], *limits, air_speed=1.2, air_speed_heating=0.1, **inputs)
    assert both.operative_temperatures(50.0) == (still.operative_temperatures(50.0)[0],
                                                 fans.operative_temperatures(50.0)[1])
    assert both.inverted_temperatures(50.0) == both.operative_temperatures(50.0)
    # With the mean radiant temperature of the zone, and by the table
    zone_still, zone_fans, zone_both = (
        ch.SetSetpointHook(['Z'], *limits, air_speed=speed, air_speed_heating=heating, tr_mode='zone', **inputs)
        for speed, heating in ((0.1, None), (1.2, None), (1.2, 0.1)))
    assert zone_both.operative_temperatures(50.0, 27.0) == (zone_still.operative_temperatures(50.0, 27.0)[0],
                                                            zone_fans.operative_temperatures(50.0, 27.0)[1])
    tables = [ch.SetSetpointHook(['Z'], *limits, met=1.1, clo=0.5, air_speed=speed, air_speed_heating=heating)
              for speed, heating in ((0.1, None), (1.2, None), (1.2, 0.1))]
    assert tables[2].setpoints_of_humidity(47.5) == (tables[0].setpoints_of_humidity(47.5)[0],
                                                     tables[1].setpoints_of_humidity(47.5)[1])
    # The air speed of the heating setpoint is not above that of the timestep (the fans do not slow the air down)
    assert both.heating_air_speed(1.2) == 0.1 and both.heating_air_speed(0.05) == 0.05
    np.testing.assert_array_equal(both.heating_air_speed(np.array([0.05, 0.1, 0.6])), [0.05, 0.1, 0.1])
    people = ch.Sun2026SetpointHook(['Z'], air_speed_heating=0.1)
    assert people.operative_temperatures(50.0, 27.0, 1.1, 0.5, 0.05) == ch.Sun2026SetpointHook(
        ['Z']).operative_temperatures(50.0, 27.0, 1.1, 0.5, 0.05)
    assert people.operative_temperatures(50.0, 27.0, 1.1, 0.5, 1.2)[0] == people.operative_temperatures(
        50.0, 27.0, 1.1, 0.5, 0.1)[0]

    # The SET of the zone is that of the occupants who have their fans only when they need them: that of still air
    # while it is not above the cooling setpoint of the SET, and that of the fans when it is
    for temperature in (18.0, 22.0, 28.0):
        assert both.zone_set(temperature, temperature, 50.0) == still.zone_set(temperature, temperature, 50.0) <= 28.18
    for temperature in (29.0, 33.0):
        assert still.zone_set(temperature, temperature, 50.0) > 28.18
        assert both.zone_set(temperature, temperature, 50.0) == fans.zone_set(temperature, temperature, 50.0)
    # At 22 °C, the SET with the fans is below the band of the causal SET model, and that of still air within it
    assert fans.zone_set(22.0, 22.0, 50.0) < 19.09 < still.zone_set(22.0, 22.0, 50.0)
    temperatures = np.array([18.0, 22.0, 28.0, 29.0, 33.0])
    np.testing.assert_array_equal(
        both.zone_set(temperatures, temperatures, 50.0),
        [(still if temperature < 28.5 else fans).zone_set(temperature, temperature, 50.0)
         for temperature in temperatures])
    assert 'air_speed_heating=0.1' in repr(both) and 'air_speed_heating=0.1' in repr(people)
    assert 'air_speed_heating=None' in repr(still)
    with pytest.raises(ValueError, match='air_speed_heating must be between 0.0 and None'):
        ch.SetSetpointHook(['Z'], *limits, air_speed=1.2, air_speed_heating=-0.1, **inputs)
    with pytest.raises(ValueError, match='air_speed_heating must be a number'):
        ch.Sun2026SetpointHook(['Z'], air_speed_heating='still')
    with pytest.warns(UserWarning, match='air_speed_heating = 2.5 is out of the range of the SET of pythermalcomfort'):
        ch.SetSetpointHook(['Z'], *limits, air_speed=1.2, air_speed_heating=2.5, **inputs)


def test_the_hook_of_comfort_standard_24_with_the_fans_that_the_occupants_control():
    pythermalcomfort_models()
    minimums = {zone: 18.0 for zone in ZONES}
    hook = ch.Sun2026SetpointHook(ZONES, air_speed_heating=0.1, heating_minimums=minimums)
    plain = ch.Sun2026SetpointHook(ZONES, heating_minimums=minimums)
    # The air velocity schedule of the People objects has the air speed of the fans, 1.2 m/s: zone 1 is at 23 °C
    # (and 24 °C of mean radiant temperature), and zone 2 at 30 °C (and 31 °C)
    conditions = dict(zip(ZONES, ((23.0, 24.0), (30.0, 31.0))))
    values = {'ZoneTimeStep': 1 / 6}
    for zone, (air, radiant) in conditions.items():
        values.update(_zone_values(zone, air, radiant, SET_Clo=0.5, SET_Vel=1.2))
    controller, plain_controller = _Controller(dict(values)), _Controller(dict(values))
    hook(controller, CALLING_POINT)
    plain(plain_controller, CALLING_POINT)
    found = {}
    for zone, (air, radiant) in conditions.items():
        # The heating setpoint is that of still air, and the cooling setpoint that of the fans
        still = plain.operative_temperatures(45.0, radiant, MET, 0.5, 0.1)
        fans = plain.operative_temperatures(45.0, radiant, MET, 0.5, 1.2)
        assert _given(controller, zone) == (still[0], fans[1])
        # Without air_speed_heating, the fans raise the heating setpoint too (decision 5 of 2026-11-10)
        assert _given(plain_controller, zone) == fans and fans[0] - still[0] > 3
        found[zone] = [ch.standard_effective_temperature(air, radiant, speed, 45.0, MET, 0.5, 'sitting')
                       for speed in (0.1, 1.2)]
    # Zone 1 needs no fans: its SET is that of still air, within the band (with the fans, it would be below it); zone
    # 2 is above the band without the fans, and within it with them
    (cool_still, cool_fans), (warm_still, warm_fans) = found[ZONES[0]], found[ZONES[1]]
    assert cool_fans < hook.band[0] <= cool_still <= hook.band[1]
    assert hook.band[0] <= warm_fans <= hook.band[1] < warm_still
    assert controller.get(f'SET_{ZONES[0]}') == cool_still and controller.get(f'SET_{ZONES[1]}') == warm_fans
    assert controller.get(f'TSV_causal_{ZONES[0]}') == pytest.approx(0.11 * cool_still - 2.6, abs=1e-12)
    assert [controller.get(f'HoursInCausalBand_{zone}') for zone in ZONES] == [pytest.approx(1 / 6)] * 2
    # The hook without it reports the SET with the air speed of the People objects
    assert plain_controller.get(f'SET_{ZONES[0]}') == cool_fans
    assert plain_controller.get(f'HoursInCausalBand_{ZONES[0]}') == 0


@needs_idd
def test_apply_sun2026_setpoints_prepares_the_model(tmp_path):
    from accim.sim.accis import modify_accis
    from accim.sim.people import PIERCE_SET_OUTPUT

    idf = _model(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        modify_accis(idf, zone_arguments={'Block1:Zone1': {'heating_setpoint_minimum': 18.0}})
    counts = len(idf.idfobjects['EnergyManagementSystem:Sensor'])
    # The arguments are checked before the model changes
    with pytest.raises(ValueError, match='tsv_limit must be 0.5'):
        ch.apply_sun2026_setpoints(idf, tsv_limit=0.6)
    assert len(idf.idfobjects['EnergyManagementSystem:Sensor']) == counts
    hook = ch.apply_sun2026_setpoints(idf, output_frequencies=['timestep'])
    assert isinstance(hook, ch.Sun2026SetpointHook) and sorted(hook.zones) == ZONES
    assert hook.heating_minimums == {'Block1_Zone1': 18.0, 'Block1_Zone2': None}
    assert hook.clothing_sources == {zone: 'schedule' for zone in ZONES}
    assert hook.keys == {zone: zone.replace('_', ':') for zone in ZONES}
    sensors = {s.Name: (s.OutputVariable_or_OutputMeter_Index_Key_Name, s.OutputVariable_or_OutputMeter_Name)
               for s in idf.idfobjects['EnergyManagementSystem:Sensor']}
    people = {p.Zone_or_ZoneList_or_Space_or_SpaceList_Name: p for p in idf.idfobjects['People']}
    ems_outputs = {o.Name: o for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    requested = {(o.Key_Value, o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']}
    for zone in ZONES:
        key = zone.replace('_', ':')
        occupants = people[key]
        assert sensors[f'SET_MRT_{zone}'] == (key, 'Zone Mean Radiant Temperature')
        assert sensors[f'SET_Act_{zone}'] == (occupants.Activity_Level_Schedule_Name, 'Schedule Value')
        assert sensors[f'SET_Clo_{zone}'] == (occupants.Clothing_Insulation_Schedule_Name, 'Schedule Value')
        assert sensors[f'SET_Vel_{zone}'] == (occupants.Air_Velocity_Schedule_Name, 'Schedule Value')
        assert f'SET_CloValue_{zone}' not in sensors and f'SET_CloMethod_{zone}' not in sensors
        # The Pierce model, and the output of its SET
        assert 'Pierce' in [getattr(occupants, f'Thermal_Comfort_Model_{n}_Type') for n in range(1, 8)]
        assert (str(occupants.Name), PIERCE_SET_OUTPUT, 'Timestep') in requested
        assert ch.sun2026_zone_outputs(zone) == [f'SET_{zone}', f'TSV_causal_{zone}', f'HoursInCausalBand_{zone}',
                                                 f'SETsaturated_{zone}']
        for name, kind, units in zip(ch.sun2026_zone_outputs(zone), ('Averaged', 'Averaged', 'Summed', 'Summed'),
                                     ('C', '', 'H', 'H')):
            output = ems_outputs[name]
            assert (output.Type_of_Data_in_Variable, output.Update_Frequency, output.Units) == (kind, 'ZoneTimestep',
                                                                                                units)
            assert ('*', name, 'Timestep') in requested
    # Once: the model has the objects of the hooks of the SET
    with pytest.raises(ValueError, match='already has the setpoints of the ATHB or of the SET'):
        ch.apply_sun2026_setpoints(idf)


@needs_idd
def test_the_inputs_of_the_people_objects_of_the_hooks_of_the_set(tmp_path):
    from accim.sim.people import set_clothing_method

    # The dynamic clothing model: the clothing insulation of the occupants of each zone (and their People objects
    # need no clothing insulation schedule)
    idf = _model(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        set_clothing_method(idf, 'DynamicClothingModelASHRAE55', verbose=False)
    hook = ch.apply_sun2026_setpoints(idf)
    assert hook.clothing_sources == {zone: 'dynamic' for zone in ZONES}
    sensors = {s.Name: (s.OutputVariable_or_OutputMeter_Index_Key_Name, s.OutputVariable_or_OutputMeter_Name)
               for s in idf.idfobjects['EnergyManagementSystem:Sensor']}
    for zone in ZONES:
        assert sensors[f'SET_CloValue_{zone}'] == (f"People {zone.replace('_', ':')}",
                                                   'Zone Thermal Comfort Clothing Value')
        assert f'SET_Clo_{zone}' not in sensors
    # The hook of the SET with the metabolic rate of the People objects only
    (tmp_path / 'set').mkdir()
    idf = _model(tmp_path / 'set')
    hook = ch.apply_set_setpoints(idf, 27, 21, met=None, clo=0.5, air_speed=0.1, method='bisection', tr_mode='zone')
    assert (hook.met, hook.clo, hook.tr_mode) == (None, 0.5, 'zone')
    names = {s.Name for s in idf.idfobjects['EnergyManagementSystem:Sensor']}
    assert {f'SET_Act_{zone}' for zone in ZONES} <= names
    assert not {name for name in names if name.startswith(('SET_Clo', 'SET_Vel'))}
    # The hook of the SET by the table needs its inputs, before the model changes
    (tmp_path / 'table').mkdir()
    idf = _model(tmp_path / 'table')
    counts = len(idf.idfobjects['EnergyManagementSystem:Sensor'])
    with pytest.raises(ValueError, match="method='table' needs met, clo and air_speed"):
        ch.apply_set_setpoints(idf, 27, 21, met=None, clo=0.5, air_speed=0.1)
    assert len(idf.idfobjects['EnergyManagementSystem:Sensor']) == counts
    # The Pierce model needs the work efficiency schedule; the People objects of a zone must agree
    for change, message in ((('Work_Efficiency_Schedule_Name', ''), 'have no Work Efficiency Schedule Name'),
                            (('Air_Velocity_Schedule_Name', ''), 'have no Air Velocity Schedule Name')):
        (tmp_path / change[0]).mkdir()
        idf = _model(tmp_path / change[0])
        setattr(idf.idfobjects['People'][0], *change)
        with pytest.raises(ValueError, match=message):
            ch.apply_sun2026_setpoints(idf)
    (tmp_path / 'two').mkdir()
    idf = _model(tmp_path / 'two')
    second = idf.copyidfobject(idf.idfobjects['People'][0])
    second.Name = 'Second People'
    second.Activity_Level_Schedule_Name = 'Activity Schedule 26'
    with pytest.raises(ValueError, match='have different values of Activity Level Schedule Name'):
        ch.apply_sun2026_setpoints(idf)


def test_the_set_of_the_results_needs_the_inputs_of_the_hook():
    hook = ch.Sun2026SetpointHook(ZONES)
    with pytest.raises(ValueError, match="reads \\['met', 'clo', 'air_speed'\\] from the People objects"):
        ch.set_of_results(pd.DataFrame(), hook)


def _mean_set(air_temperature, mean_radiant_temperature, air_speed, relative_humidity, met, clo, position='standing'):
    """A SET for the tests without pythermalcomfort (numba): the mean of the air and mean radiant temperatures."""
    value = (np.asarray(air_temperature, dtype=float) + np.asarray(mean_radiant_temperature, dtype=float)) / 2
    return float(value) if np.ndim(value) == 0 else value


def test_a_timestep_without_the_set_of_a_zone_has_no_hours_in_the_band(monkeypatch):
    # Finding A5 of the self-audit of 2026-11-11: when the hook calculates no SET for a zone in a timestep (no value of
    # a sensor, an activity level of 0, or no mean air temperature), the summed output HoursInCausalBand_<zone> is 0
    # (before, it kept the hours of the last timestep with the SET); SET_<zone> and TSV_causal_<zone> keep their values
    monkeypatch.setattr(ch, 'standard_effective_temperature', _mean_set)
    hook = ch.Sun2026SetpointHook(ZONES, clothing_sources={zone: 'schedule' for zone in ZONES})
    controller = _Controller({'ZoneTimeStep': 1 / 6, **_zone_values(ZONES[0], 23.0, 24.0, SET_Clo=0.5),
                              **_zone_values(ZONES[1], 25.0, 26.0, SET_Clo=0.5)})
    hook(controller, CALLING_POINT)
    assert [controller.get(f'HoursInCausalBand_{zone}') for zone in ZONES] == [pytest.approx(1 / 6)] * 2
    assert controller.get(f'SET_{ZONES[0]}') == 23.5
    for name, value in ((f'SET_Act_{ZONES[0]}', 0.0), (f'SET_RH_{ZONES[1]}', None)):
        controller.set(name, value)
    hook(controller, CALLING_POINT)
    assert [controller.get(f'HoursInCausalBand_{zone}') for zone in ZONES] == [0.0, 0.0]
    assert (controller.get(f'SET_{ZONES[0]}'), controller.get(f'TSV_causal_{ZONES[0]}')) == (
        23.5, pytest.approx(0.11 * 23.5 - 2.6))
    # The setpoints of the hook without the SET of the zone (no mean air temperature)
    controller.set(f'SET_Act_{ZONES[0]}', ACTIVITY)
    hook(controller, CALLING_POINT)
    assert controller.get(f'HoursInCausalBand_{ZONES[0]}') == pytest.approx(1 / 6)
    controller.set(f'SET_MAT_{ZONES[0]}', None)
    hook(controller, CALLING_POINT)
    assert _given(controller, ZONES[0]) is not None and controller.get(f'HoursInCausalBand_{ZONES[0]}') == 0.0


def test_the_setpoints_of_the_thermostats_are_within_temperature_range_with_the_mean_radiant_temperature(monkeypatch):
    # The decision of the author of 2026-11-18 (the question of 2026-11-17 in notes/questions.md): with tr_mode='zone',
    # temperature_range is the range of the setpoints given to the thermostats, (air + mean radiant temperature)/2, as
    # with 'equal_air', so the bisection looks for the air temperatures from 2·low − MRT to 2·high − MRT. With the SET
    # of the mean of the air and mean radiant temperatures, the SET of a setpoint is the setpoint itself
    monkeypatch.setattr(ch, 'standard_effective_temperature', _mean_set)
    inputs = dict(met=1.1, clo=0.5, air_speed=0.1, method='bisection')
    hook = ch.SetSetpointHook(['Z'], 28.0, 15.0, tr_mode='zone', temperature_range=(16.0, 40.0), tolerance_k=0.001,
                              **inputs)
    for radiant in (25.0, 5.0, -9.91):
        assert hook._bisection_range(radiant) == (2 * 16.0 - radiant, 2 * 40.0 - radiant)
        # The heating setpoint of the SET (15 °C) is below the range: the air temperature is at the lower limit of its
        # range, and the heating setpoint of the thermostat is the limit of temperature_range itself
        air = hook.inverted_temperatures(50.0, radiant)
        heating, cooling = hook.operative_temperatures(50.0, radiant)
        assert air[0] == 2 * 16.0 - radiant and heating == 16.0 and hook.saturated(heating, cooling)
        assert cooling == (air[1] + radiant) / 2 and cooling == pytest.approx(28.0, abs=1e-3)
    # With −9.91 °C, the mean of the air temperature at the limit and the mean radiant temperature is not 16 °C in
    # floating point, and saturated() compares the setpoints with the limits exactly
    assert (2 * 16.0 + 9.91 - 9.91) / 2 != 16.0
    # The cooling setpoint of the SET (28 °C) above the range: the air temperature at the upper limit of its range
    warm = ch.SetSetpointHook(['Z'], 28.0, 15.0, tr_mode='zone', temperature_range=(10.0, 26.0), **inputs)
    assert warm.inverted_temperatures(50.0, 30.0)[1] == 22.0 and warm.operative_temperatures(50.0, 30.0)[1] == 26.0
    # With 'equal_air', the range of the bisection is temperature_range itself
    equal = ch.SetSetpointHook(['Z'], 28.0, 15.0, temperature_range=(16.0, 40.0), **inputs)
    assert equal._bisection_range(None) == equal._bisection_range(25.0) == (16.0, 40.0)
    assert equal.operative_temperatures(50.0)[0] == 16.0


def _comfort_models(people):
    return [str(getattr(people, f'Thermal_Comfort_Model_{n}_Type')).strip() for n in range(1, 8)]


def _dynamic_clothing_model(folder):
    """The model of the hooks with the dynamic clothing model of ASHRAE 55 in its People objects."""
    from accim.sim.people import set_clothing_method

    folder.mkdir(parents=True, exist_ok=True)
    idf = _model(folder)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        set_clothing_method(idf, 'DynamicClothingModelASHRAE55', verbose=False)
    return idf


@needs_idd
def test_the_hook_of_the_set_with_the_dynamic_clothing_model_adds_the_pierce_model(tmp_path):
    # Finding A3 of the self-audit of 2026-11-11: EnergyPlus reports the clothing insulation of the dynamic clothing
    # model (Zone Thermal Comfort Clothing Value, which the sensors SET_CloValue_<zone> read) only for the People
    # objects with the Fanger, Pierce or KSU model, so apply_set_setpoints adds the Pierce model, as
    # apply_sun2026_setpoints does
    idf = _dynamic_clothing_model(tmp_path / 'dynamic')
    assert all(_comfort_models(people)[:3] == ['AdaptiveASH55', 'AdaptiveCEN15251', '']
               for people in idf.idfobjects['People'])
    hook = ch.apply_set_setpoints(idf, 27, 21, met=1.1, clo=None, air_speed=0.1, method='bisection')
    assert hook.clothing_sources == {zone: 'dynamic' for zone in ZONES}
    assert {s.Name for s in idf.idfobjects['EnergyManagementSystem:Sensor']} >= {f'SET_CloValue_{zone}'
                                                                                 for zone in ZONES}
    for people in idf.idfobjects['People']:
        assert _comfort_models(people)[:4] == ['AdaptiveASH55', 'AdaptiveCEN15251', 'Pierce', '']
    # With a model that reports it already (Fanger), or with the clothing insulation given, the People objects keep
    # their models
    idf = _dynamic_clothing_model(tmp_path / 'fanger')
    for people in idf.idfobjects['People']:
        people.Thermal_Comfort_Model_3_Type = 'Fanger'
    ch.apply_set_setpoints(idf, 27, 21, met=1.1, clo=None, air_speed=0.1, method='bisection')
    assert all(_comfort_models(people)[:4] == ['AdaptiveASH55', 'AdaptiveCEN15251', 'Fanger', '']
               for people in idf.idfobjects['People'])
    idf = _dynamic_clothing_model(tmp_path / 'given')
    ch.apply_set_setpoints(idf, 27, 21, met=None, clo=0.5, air_speed=0.1, method='bisection')
    assert all('Pierce' not in _comfort_models(people) for people in idf.idfobjects['People'])
    # The Pierce model needs the work efficiency schedule, before the model changes
    idf = _dynamic_clothing_model(tmp_path / 'work')
    idf.idfobjects['People'][0].Work_Efficiency_Schedule_Name = ''
    counts = len(idf.idfobjects['EnergyManagementSystem:Sensor'])
    with pytest.raises(ValueError, match='have no Work Efficiency Schedule Name, which the Pierce model'):
        ch.apply_set_setpoints(idf, 27, 21, met=1.1, clo=None, air_speed=0.1, method='bisection')
    assert len(idf.idfobjects['EnergyManagementSystem:Sensor']) == counts
    assert all('Pierce' not in _comfort_models(people) for people in idf.idfobjects['People'])


@needs_energyplus
def test_the_model_of_the_hook_of_the_set_with_the_dynamic_clothing_model_runs(tmp_path):
    # Finding A3: without the Pierce model, EnergyPlus stopped before the simulation (the sensors SET_CloValue_<zone>
    # of an output variable that it does not report); the model runs now, also without the hook (EMS backend)
    import subprocess

    idf = _dynamic_clothing_model(tmp_path / 'model')
    run_period = idf.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month, run_period.End_Month, run_period.End_Day_of_Month = (
        7, 15, 7, 15)
    ch.apply_set_setpoints(idf, 27, 21, met=1.1, clo=None, air_speed=0.1, method='bisection')
    idf.saveas(str(tmp_path / 'set.idf'))
    from .test_comfort_hooks import _energyplus_with_api

    energyplus = _energyplus_with_api() / 'energyplus.exe'
    result = subprocess.run([str(energyplus), '-d', str(tmp_path / 'out'), '-p', 'run', '-s', 'C', '-r', '-x', '-w',
                             str(EPW), str(tmp_path / 'set.idf')], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    [err] = (tmp_path / 'out').glob('*.err')
    assert 'ZONE THERMAL COMFORT CLOTHING VALUE' not in err.read_text(errors='replace').upper()


# EnergyPlus ---------------------------------------------------------------------------------------------------------

#: The hourly differences measured on 2026-11-10 between the SET of each zone that the hook reports (``SET_<zone>``,
#: hourly means) and the SET of the Pierce model of EnergyPlus (K): (mean, mean of the absolute values, maximum absolute
#: value), in 8-14 January and 15-21 July (``notes/decisions.md``, F1). Those of winter were measured again on
#: 2026-11-12: since finding A19 of the self-audit of 2026-11-11, the thermostat of Block1:Zone1 on its minimum of 18 °C
#: heats to 18.1 °C (the minimum plus the tolerance), which changed them from (-0.080, 0.081, 0.191) and (-0.082,
#: 0.083, 0.204); and again on 2026-11-18, with the range of the setpoints of the thermostats (the decision of the
#: author of that day: the heating setpoints are lower, though the zones stay far above them), which changed the
#: maximums from 0.187 and 0.204. All of them were measured again on 2026-11-19, with the windows of the sample model
#: closed on its design days (:mod:`accim.sim.ems.design_days`; until then, EnergyPlus sized its VRF systems with them
#: open, about 100 times too big, and the heat of their fans kept the zones warm), which changed them from (-0.080,
#: 0.081, 0.190) and (-0.082, 0.082, 0.205) in winter, and from (-0.156, 0.156, 0.262) and (-0.154, 0.154, 0.291) in
#: summer. The maximums are larger now: in the hours in which the windows of the model open (above 24 °C), the air
#: temperature of a zone changes fast (in January, it falls by up to 13.6 K in a timestep), and the SET of the hook,
#: with the air temperature of the previous timestep that its sensor reads, follows that of the Pierce model a
#: timestep later
MEASURED = {
    ('winter', 'Block1_Zone1'): (-0.016, 0.086, 0.631), ('winter', 'Block1_Zone2'): (-0.028, 0.087, 0.723),
    ('summer', 'Block1_Zone1'): (-0.140, 0.153, 0.417), ('summer', 'Block1_Zone2'): (-0.138, 0.148, 0.350),
}
#: The share of the timesteps of each week (after the first one) in which the air temperature whose SET is the heating
#: setpoint of the SET, with the mean radiant temperature of the zone, is below 10 °C, measured on 2026-11-19 with the
#: windows of the sample model closed on its design days. Until then (with the fans of its oversized VRF systems, the
#: zones and their mean radiant temperature were warmer: 25 instead of 22.5 to 22.9 °C on average in January), it was
#: below 10 °C in all the timesteps of January, and in 0.644 and 0.622 of those of July
BELOW_10 = {
    ('winter', 'Block1_Zone1'): 0.661, ('winter', 'Block1_Zone2'): 0.702,
    ('summer', 'Block1_Zone1'): 0.618, ('summer', 'Block1_Zone2'): 0.567,
}


def _sun2026_model(folder, monkeypatch, begin, end, fans=None, **hook_arguments):
    """The output IDF of AddAccis of the sample model (INT EN16798, category II, comfort mode 3, full air-conditioning,
    outputs at timestep frequency) from ``begin`` to ``end`` ((month, day)), with a minimum heating setpoint of 18 °C in
    Block1:Zone1, prepared for comfort standard 24 (with the other arguments of ``apply_sun2026_setpoints`` given), with
    programs that copy the values that the sensors of the hook read into reported variables; return its path and the
    hook. With ``fans``, the air velocity schedule of its People objects has that air speed (m/s) in all the hours."""
    from accim.sim.accis import AddAccis, load_idf, modify_accis
    from accim.sim.ems.programs import add_program
    from accim.utils.people import get_people_objects

    folder.mkdir(parents=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    model = load_idf(folder / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    model.save()
    monkeypatch.chdir(folder)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['timestep'], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', comfort_standard=[1], category=[2], comfort_mode=[3], confirm=True,
                 verbose=False)
    [path] = folder.glob('TestModel[[]*.idf')
    idf = load_idf(path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        modify_accis(idf, zone_arguments={'Block1:Zone1': {'heating_setpoint_minimum': 18.0}})
    if fans is not None:
        idf.newidfobject('Schedule:Compact', Name='Fans', Schedule_Type_Limits_Name='', Field_1='Through: 12/31',
                         Field_2='For: AllDays', Field_3='Until: 24:00', Field_4=fans)
        for people in get_people_objects(idf):
            people.Air_Velocity_Schedule_Name = 'Fans'
    hook = ch.apply_sun2026_setpoints(idf, output_frequencies=['timestep'], **hook_arguments)
    prefixes = ('MAT', 'MRT', 'RH', 'Act', 'Clo', 'Vel')
    for zone in ZONES:
        names = [f'Copy{prefix}_{zone}' for prefix in prefixes]
        idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                         **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(names, start=1)})
        add_program(idf, f'CopySensors_{zone}', [f'set Copy{prefix}_{zone} = SET_{prefix}_{zone}'
                                                 for prefix in prefixes])
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=f'CopySensors_{zone}',
                         EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor',
                         Program_Name_1=f'CopySensors_{zone}')
        for name in names:
            idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=name,
                             Type_of_Data_in_Variable='Averaged', Update_Frequency='ZoneTimestep', Units='')
            idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name, Reporting_Frequency='Timestep')
    idf.saveas(str(folder / 'sun.idf'))
    path.unlink()
    (folder / 'TestModel.idf').unlink()
    shutil.copy(EPW, folder / 'Seville.epw')
    return folder / 'sun.idf', hook


@needs_energyplus
@pytest.mark.parametrize('season, begin, end', [('winter', (1, 8), (1, 14)), ('summer', (7, 15), (7, 21))])
def test_comfort_standard_24_in_energyplus(tmp_path, monkeypatch, season, begin, end):
    from accim.run import run_ep
    from accim.sim.people import PIERCE_SET_OUTPUT

    pythermalcomfort_models()
    model, hook = _sun2026_model(tmp_path / season, monkeypatch, begin, end)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        [result] = run_ep(only_accim_idfs=False, confirm=True, processes=1, backend='api', hooks=[hook])
    assert result.success, result.error
    results = pd.read_csv(model.parent / 'sun[Seville.csv')
    assert len(results) == 7 * 24 * STEPS
    columns = list(results.columns)

    def column(start):
        return results[next(c for c in columns if c.upper().startswith(start.upper()))]

    for zone in ZONES:
        key = zone.replace('_', ':').upper()
        copied = {prefix: column(f'EMS:Copy{prefix}_{zone} [').iloc[1:].to_numpy()
                  for prefix in ('MAT', 'MRT', 'RH', 'Act', 'Clo', 'Vel')}
        met = copied['Act'] / ch.MET_ACTIVITY_LEVEL
        # The setpoints without the tolerance are those of the bisection with the values that the sensors read (the
        # air temperatures with the mean radiant temperature of the zone, as operative temperatures), bounded by the
        # minimum heating setpoint of 18 °C in Block1:Zone1
        rows = list(range(0, len(met), 25))
        expected = np.array([hook.operative_temperatures(copied['RH'][t], copied['MRT'][t], met[t], copied['Clo'][t],
                                                         copied['Vel'][t]) for t in rows])
        heating = column(f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()
        cooling = column(f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()
        minimum = 18.0 if zone == 'Block1_Zone1' else -np.inf
        np.testing.assert_allclose(heating[rows], np.maximum(expected[:, 0], minimum), atol=1e-6)
        np.testing.assert_allclose(cooling[rows], expected[:, 1], atol=1e-6)
        if season == 'winter':
            # The inverted heating setpoint falls below 18 °C (1.0 clo in winter): bounded in Block1:Zone1 only
            assert heating.min() < 18.0 if zone == 'Block1_Zone2' else heating.min() == 18.0
        # The SET, the causal TSV and the occupied hours within the band of TSV ±0.5 of the zone
        reported = column(f'EMS:SET_{zone} [').iloc[1:].to_numpy()
        np.testing.assert_allclose(reported, [hook.zone_set(copied['MAT'][t], copied['MRT'][t], copied['RH'][t],
                                                            met[t], copied['Clo'][t], copied['Vel'][t])
                                              for t in range(len(met))], atol=1e-6)
        tsv = column(f'EMS:TSV_causal_{zone} [').iloc[1:].to_numpy()
        np.testing.assert_allclose(tsv, 0.11 * reported - 2.6, atol=1e-6)
        # The hours at a limit of temperature_range, 10 to 40 °C (task A6): none in these weeks. With the mean radiant
        # temperature of the zone, the air temperature whose SET is the heating setpoint of the SET is below 10 °C in
        # most of the timesteps of both weeks (BELOW_10, measured), within the range of the bisection of the air
        # temperature, 2·10 − MRT to 2·40 − MRT, whose setpoints of the thermostats are within 10 to 40 °C (the
        # decision of the author of 2026-11-18; until then, that range was 10 to 40 °C, and the heating setpoints were
        # at its limit in those timesteps)
        inverted = [hook.inverted_temperatures(copied['RH'][t], copied['MRT'][t], met[t], copied['Clo'][t],
                                               copied['Vel'][t]) for t in range(len(met))]
        expected = np.array([hook.saturated(*hook._operative(temperatures, copied['MRT'][t]))
                             for t, temperatures in enumerate(inverted)])
        np.testing.assert_allclose(column(f'EMS:SETsaturated_{zone} [').iloc[1:].to_numpy(),
                                   np.where(expected, 1 / STEPS, 0.0), atol=1e-9)
        below = round(float(np.mean([temperatures[0] < 10 for temperatures in inverted])), 3)
        assert not expected.any() and below == pytest.approx(BELOW_10[season, zone], abs=1e-3), below
        occupied = column(f'EMS:Occupied Hours_{zone} [').iloc[1:].to_numpy() > 0
        hours = column(f'EMS:HoursInCausalBand_{zone} [').iloc[1:].to_numpy()
        inside = (reported >= hook.band[0]) & (reported <= hook.band[1])
        clear = np.minimum(np.abs(reported - hook.band[0]), np.abs(reported - hook.band[1])) > 1e-4
        np.testing.assert_allclose(hours[clear], np.where(inside & occupied, 1 / STEPS, 0.0)[clear], atol=1e-9)
        # The SET of the hook against that of the Pierce model of EnergyPlus, hour by hour (hourly means)
        pierce = column(f'PEOPLE {key}:{PIERCE_SET_OUTPUT} [').to_numpy()
        accim_hourly = column(f'EMS:SET_{zone} [').to_numpy().reshape(-1, STEPS).mean(axis=1)
        pierce_hourly = pierce.reshape(-1, STEPS).mean(axis=1)
        difference = (accim_hourly - pierce_hourly)[1:]
        measured = (round(float(difference.mean()), 3), round(float(np.abs(difference).mean()), 3),
                    round(float(np.abs(difference).max()), 3))
        assert measured == pytest.approx(MEASURED[season, zone], abs=1e-3), measured
        # The hour counters of the ACCIS follow the setpoints of the hook: occupied and comfortable if the operative
        # temperature of the previous timestep is within the setpoints without the tolerance (the rows within 1e-3 K
        # of a setpoint are not checked: the CSV has 6 significant digits)
        operative = column(f'{key}:Zone Operative Temperature').shift(1).iloc[1:].to_numpy()
        comfortable = column(f'EMS:Occupied Comfortable Hours_No Applicability_{zone} [').iloc[1:].to_numpy() > 0
        within = (operative <= cooling) & (operative >= heating)
        clear = np.minimum(np.abs(operative - heating), np.abs(operative - cooling)) > 1e-3
        assert occupied.any() and (comfortable[clear] == (within & occupied)[clear]).all()


@needs_energyplus
def test_comfort_standard_24_with_the_fans_that_the_occupants_control_in_energyplus(tmp_path, monkeypatch):
    # The question of the validation study of F3 (decided on 2026-11-13): three days of July of the sample model with
    # fans of 1.2 m/s in the air velocity schedule of its People objects, and the heating setpoint of still air
    from accim.run import run_ep

    pythermalcomfort_models()
    model, hook = _sun2026_model(tmp_path / 'fans', monkeypatch, (7, 15), (7, 17), fans=1.2, air_speed_heating=0.1)
    assert hook.air_speed_heating == 0.1
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        [result] = run_ep(only_accim_idfs=False, confirm=True, processes=1, backend='api', hooks=[hook])
    assert result.success, result.error
    results = pd.read_csv(model.parent / 'sun[Seville.csv')
    assert len(results) == 3 * 24 * STEPS
    columns = list(results.columns)

    def column(start):
        return results[next(c for c in columns if c.upper().startswith(start.upper()))]

    plain = ch.Sun2026SetpointHook(ZONES)
    for zone in ZONES:
        key = zone.replace('_', ':').upper()
        copied = {prefix: column(f'EMS:Copy{prefix}_{zone} [').iloc[1:].to_numpy()
                  for prefix in ('MAT', 'MRT', 'RH', 'Act', 'Clo', 'Vel')}
        assert (copied['Vel'] == 1.2).all()
        met = copied['Act'] / ch.MET_ACTIVITY_LEVEL
        rows = list(range(0, len(met), 25))
        # The cooling setpoint is that of the air speed of the fans, and the heating setpoint that of still air: with
        # the air speed of the fans (the hook without air_speed_heating), it would be more than 3 K above
        arguments = [(copied['RH'][t], copied['MRT'][t], met[t], copied['Clo'][t]) for t in rows]
        still = np.array([plain.operative_temperatures(*values, 0.1) for values in arguments])
        fans = np.array([plain.operative_temperatures(*values, 1.2) for values in arguments])
        heating = column(f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()
        cooling = column(f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()
        minimum = 18.0 if zone == 'Block1_Zone1' else -np.inf
        np.testing.assert_allclose(heating[rows], np.maximum(still[:, 0], minimum), atol=1e-6)
        np.testing.assert_allclose(cooling[rows], fans[:, 1], atol=1e-6)
        assert (fans[:, 0] - still[:, 0]).min() > 3 and (fans[:, 1] - still[:, 1]).min() > 1
        # The SET of the zone: that of still air while it is not above the upper limit of the band, and that of the
        # fans when it is; both happen in these days
        without = np.array([plain.zone_set(copied['MAT'][t], copied['MRT'][t], copied['RH'][t], met[t],
                                           copied['Clo'][t], 0.1) for t in range(len(met))])
        with_fans = np.array([plain.zone_set(copied['MAT'][t], copied['MRT'][t], copied['RH'][t], met[t],
                                             copied['Clo'][t], 1.2) for t in range(len(met))])
        reported = column(f'EMS:SET_{zone} [').iloc[1:].to_numpy()
        warm = without > hook.band[1]
        assert warm.any() and (~warm).any()
        np.testing.assert_allclose(reported, np.where(warm, with_fans, without), atol=1e-6)
        # The heating coil of the zone does not work in these days of July
        assert (column(f'{key} VRF INDOOR UNIT DX HEATING COIL:Heating Coil Heating Rate [').to_numpy() == 0).all()


@needs_energyplus
def test_the_setpoints_of_comfort_standard_24_at_the_limits_of_their_range_in_energyplus(tmp_path, monkeypatch):
    # Task A6 of the review of 1.2.0: two days of January of the sample model (1.0 clo), whose inverted heating setpoint
    # falls below 18 °C, with the range of the setpoints from 18 °C
    from accim.run import run_ep

    pythermalcomfort_models()
    model, hook = _sun2026_model(tmp_path / 'range', monkeypatch, (1, 8), (1, 9), temperature_range=(18.0, 40.0))
    assert hook.temperature_range == (18.0, 40.0)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        [result] = run_ep(only_accim_idfs=False, confirm=True, processes=1, backend='api', hooks=[hook])
    assert result.success, result.error
    results = pd.read_csv(model.parent / 'sun[Seville.csv')
    columns = list(results.columns)

    def column(start):
        return results[next(c for c in columns if c.upper().startswith(start.upper()))]

    for zone in ZONES:
        copied = {prefix: column(f'EMS:Copy{prefix}_{zone} [').iloc[1:].to_numpy()
                  for prefix in ('RH', 'MRT', 'Act', 'Clo', 'Vel')}
        met = copied['Act'] / ch.MET_ACTIVITY_LEVEL
        # The timesteps whose setpoints of the bisection, with the values that the sensors read, are at a limit of the
        # range: the output is the length of the timestep in them, and 0 in the others
        expected = np.array([hook.saturated(*hook.operative_temperatures(
            copied['RH'][t], copied['MRT'][t], met[t], copied['Clo'][t], copied['Vel'][t])) for t in range(len(met))])
        saturated = column(f'EMS:SETsaturated_{zone} [').iloc[1:].to_numpy()
        np.testing.assert_allclose(saturated, np.where(expected, 1 / STEPS, 0.0), atol=1e-9)
        assert expected.any()
        # Where it is, the heating setpoint of the hook is the limit, 18 °C (with the mean radiant temperature of the
        # zone, the air temperature of the bisection is at the limit of its range, 2·18 − MRT; the decision of the
        # author of 2026-11-18)
        heating = column(f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()
        np.testing.assert_allclose(heating[expected], 18.0, atol=1e-6)


@needs_idd
def test_the_fallback_of_the_ems_of_comfort_standard_24(tmp_path):
    # Way (a) of proposal A6 of v03 (the entry of TODO.md of task F1, done on 2026-11-18): with ems_fallback, the model
    # also gets a feedback of the setpoints on the SET of the Pierce model of EnergyPlus (accim.sim.ems.set_feedback)
    from accim.sim.ems import hook_setpoints as hs
    from accim.sim.ems import set_feedback as sf
    from accim.sim.ems.inputs import RUN_PROGRAM_PREFIX

    (tmp_path / 'a').mkdir()
    building = _model(tmp_path / 'a')
    hook = ch.apply_sun2026_setpoints(building, ems_fallback=True)
    people = {str(p.Zone_or_ZoneList_or_Space_or_SpaceList_Name).replace(':', '_'): str(p.Name)
              for p in building.idfobjects['People']}
    for zone in ZONES:
        sensor = building.getobject('EnergyManagementSystem:Sensor', f'SET_Pierce_{zone}')
        assert sensor.OutputVariable_or_OutputMeter_Name == ('Zone Thermal Comfort Pierce Model Standard Effective '
                                                             'Temperature')
        assert sensor.OutputVariable_or_OutputMeter_Index_Key_Name == people[zone]
        lines = [str(line).strip() for line in
                 building.getobject('EnergyManagementSystem:Program', f'{RUN_PROGRAM_PREFIX}{zone}').fieldvalues[2:]]
        position = lines.index('run SetAST')
        assert lines[position + 1:position + 3] == [f'run SetSETFeedback_{zone}', f'run ApplyHookSetpoints_{zone}']
        program = [str(line).strip() for line in
                   building.getobject('EnergyManagementSystem:Program', f'SetSETFeedback_{zone}').fieldvalues[2:]]
        # Without the SET of EnergyPlus, or with an activity level of 0 (as the hook), it does nothing
        assert program[:4] == [f'if HookSetpoints_{zone} == 0', f'if SET_Pierce_{zone} > 0 && SET_Act_{zone} > 0',
                               f'set EstimateAHST = {zone}_OpT+({hook.set_heating_setpoint!r}-SET_Pierce_{zone})/1.0',
                               f'set EstimateACST = {zone}_OpT+({hook.set_cooling_setpoint!r}-SET_Pierce_{zone})/1.0']
        assert f'set HookAHST_{zone} = HookAHST_{zone}+0.5*(EstimateAHST-HookAHST_{zone})' in program
    assert sorted(sf.feedback_zones(building)) == sorted(hs.hook_zones(building)) == ZONES
    building.saveas(str(tmp_path / 'fallback.idf'))
    assert sf.feedback_zones_of_file(tmp_path / 'fallback.idf') == hs.hook_zones_of_file(tmp_path / 'fallback.idf')
    assert sf.zones_needing_a_hook(ZONES, ZONES) == [] and sf.zones_needing_a_hook(ZONES, ZONES[:1]) == ZONES[1:]
    # Its arguments, checked before the model changes
    (tmp_path / 'b').mkdir()
    building = _model(tmp_path / 'b')
    objects = len(building.idfobjects['EnergyManagementSystem:Sensor'])
    with pytest.raises(ValueError, match="it needs tr_mode='zone'"):
        ch.apply_sun2026_setpoints(building, ems_fallback=True, tr_mode='equal_air')
    with pytest.raises(ValueError, match='it cannot take air_speed_heating'):
        ch.apply_sun2026_setpoints(building, ems_fallback=True, air_speed_heating=0.1)
    with pytest.raises(ValueError, match='ems_relaxation must be greater than 0 and not greater than 1'):
        ch.apply_sun2026_setpoints(building, ems_fallback=True, ems_relaxation=1.5)
    with pytest.raises(ValueError, match='ems_slope must be greater than 0'):
        ch.apply_sun2026_setpoints(building, ems_fallback=True, ems_slope=0)
    with pytest.raises(ValueError, match='give them with ems_fallback=True'):
        ch.apply_sun2026_setpoints(building, ems_slope=1.2)
    assert len(building.idfobjects['EnergyManagementSystem:Sensor']) == objects


def test_the_fallback_of_the_ems_does_nothing_where_a_hook_ran():
    # The review of 2026-11-18: in a timestep in which the hook gave a zone no setpoints (without the values of its
    # sensors, or with an activity level of 0), the flag stayed 0 and the feedback gave the setpoints, so the model with
    # the fallback did not give the results of the model without it. The hook of the SET now sets the flag to -1, and
    # the feedback also skips the timesteps with an activity level of 0 itself (finding A5, as the hook)
    from accim.sim.ems import hook_setpoints as hs
    from accim.sim.ems import set_feedback as sf
    from accim.sim.ems.erl import ErlProgramSet, variables_in_programs

    programs = {'SetSETFeedback_Z': sf.program_lines('Z', 19.09, 28.18, (19.09, 28.18), 0.5, 1.0, (10.0, 40.0), 0.11,
                                                     -2.6, activity='SET_Act_Z'),
                'ApplyHookSetpoints_Z': hs.program_lines('Z')}
    erl = ErlProgramSet(programs, global_variables=set().union(*variables_in_programs(programs).values()))
    erl.strict = True

    def timestep(flag, activity, pierce=24.0, operative=25.0):
        for name, value in dict(HookSetpoints_Z=flag, HookAHST_Z=20.0, HookACST_Z=27.0, SET_Pierce_Z=pierce,
                                SET_Act_Z=activity, Z_OpT=operative, Occ_count_Z=1.0, ZoneTimeStep=0.25,
                                SETsaturated_Z=0.25, HoursInCausalBand_Z=0.25, SET_Z=23.0, TSV_causal_Z=0.0,
                                AHST=18.0, ACST=26.0, AHSTtol=0.0, ACSTtol=0.0, SetpointAcc=10.0).items():
            erl.set(name, value)
        erl.run('SetSETFeedback_Z')
        flag = erl.get('HookSetpoints_Z')
        given = (erl.get('HookAHST_Z'), erl.get('HookACST_Z'))
        erl.run('ApplyHookSetpoints_Z')
        return flag, given, (erl.get('AHST'), erl.get('ACST')), erl.get('HookSetpoints_Z')

    # No hook (the EMS backend): the feedback moves the setpoints half the way to its estimates, as a hook
    flag, given, applied, reset = timestep(0.0, 110.7)
    assert flag == 1 and given == pytest.approx((20.0 + 0.5 * (25.0 + 19.09 - 24.0 - 20.0),
                                                 27.0 + 0.5 * (25.0 + 28.18 - 24.0 - 27.0)))
    assert applied == pytest.approx(given, abs=0.051) and reset == 0
    assert erl.get('SET_Z') == 24.0 and erl.get('HoursInCausalBand_Z') == 0.25
    # A hook that gave no setpoints (-1): the feedback does nothing, and the setpoints and outputs are those of the
    # ACCIS and of the hook; ApplyHookSetpoints_<zone> sets the flag back to 0
    flag, given, applied, reset = timestep(-1.0, 110.7)
    assert (flag, given, applied, reset) == (-1, (20.0, 27.0), (18.0, 26.0), 0)
    assert (erl.get('SET_Z'), erl.get('SETsaturated_Z'), erl.get('HoursInCausalBand_Z')) == (23.0, 0.25, 0.25)
    # An activity level of 0, without a hook: no setpoints of the feedback, no hours (summed), the SET kept (A5)
    flag, given, applied, reset = timestep(0.0, 0.0)
    assert (flag, given, applied, reset) == (0, (20.0, 27.0), (18.0, 26.0), 0)
    assert (erl.get('SET_Z'), erl.get('SETsaturated_Z'), erl.get('HoursInCausalBand_Z')) == (23.0, 0.0, 0.0)


def test_the_hooks_of_the_set_mark_the_zones_without_setpoints(monkeypatch):
    # The flag -1 of the review of 2026-11-18, for the fallback of the EMS (above)
    monkeypatch.setattr(ch, 'standard_effective_temperature', _mean_set)
    hook = ch.Sun2026SetpointHook(ZONES, clothing_sources={zone: 'schedule' for zone in ZONES})
    controller = _Controller({'ZoneTimeStep': 1 / 6, **_zone_values(ZONES[0], 23.0, 24.0, SET_Clo=0.5),
                              **_zone_values(ZONES[1], 25.0, 26.0, SET_Clo=0.5)})
    hook(controller, CALLING_POINT)
    assert [controller.get(f'HookSetpoints_{zone}') for zone in ZONES] == [1.0, 1.0]
    controller.set(f'SET_Act_{ZONES[0]}', 0.0)
    controller.set(f'SET_RH_{ZONES[1]}', None)
    hook(controller, CALLING_POINT)
    assert [controller.get(f'HookSetpoints_{zone}') for zone in ZONES] == [-1.0, -1.0]
    assert [_given(controller, zone) for zone in ZONES] == [None, None]


@needs_energyplus
def test_the_fallback_of_the_ems_of_comfort_standard_24_in_energyplus(tmp_path, monkeypatch):
    # Measured on 2026-11-18 (EnergyPlus 25.1, the sample model in Seville, 15 to 17 July): the model with the fallback
    # runs with the EMS backend, which gives the results of the backend of the API without the hook, exactly; with the
    # hook, the backend of the API gives those of the model without the fallback, exactly (the hook gives the setpoints
    # first, and the feedback does nothing); and the setpoints of the feedback follow those of the hook. Measured again
    # on 2026-11-19, with the windows of the sample model closed on its design days (its VRF systems were about 100
    # times too big before, and kept the zones warm): on 16 and 17 July, the cooling setpoints of the feedback are 0.18
    # and 0.20 K above those of the hook on average (0.40 and 0.42 K in absolute value; about 0.01 K before), the
    # heating setpoints 0.05 K above, and the operative temperatures within 0.39 K of those of the hook
    measured = {('Block1_Zone1', 'Cooling'): 0.183, ('Block1_Zone1', 'Heating'): 0.046,
                ('Block1_Zone2', 'Cooling'): 0.196, ('Block1_Zone2', 'Heating'): 0.051}
    from accim.run import run_ep
    from accim.sim.ems.hook_setpoints import MissingHookWarning
    from accim.sim.energyplus_api import run_simulations

    pythermalcomfort_models()
    hooked, hook = _sun2026_model(tmp_path / 'hook', monkeypatch, (7, 15), (7, 17))
    model, hook_of_model = _sun2026_model(tmp_path / 'fallback', monkeypatch, (7, 15), (7, 17), ems_fallback=True)
    # The EMS backend runs it (the folder of the model is the working folder)
    with warnings.catch_warnings():
        warnings.simplefilter('error', category=UserWarning)
        run_ep(only_accim_idfs=False, confirm=True, energyplus_version='auto', processes=0)
    ems = pd.read_csv(model.parent / 'sun[Seville.csv')
    with warnings.catch_warnings():
        warnings.simplefilter('error', category=MissingHookWarning)
        [api] = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                                processes=1)
    assert api.success, api.error
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / 'api' / 'run.csv'), ems, check_exact=True)
    results = {}
    for name, path, hook_ in (('hook', hooked, hook), ('both', model, hook_of_model)):
        [result] = run_simulations([(path, EPW, {'output_directory': tmp_path / name, 'output_prefix': 'run',
                                                 'before_programs': [hook_]})], processes=1)
        assert result.success, result.error
        results[name] = pd.read_csv(tmp_path / name / 'run.csv')
    pd.testing.assert_frame_equal(results['both'], results['hook'], check_exact=True)
    # The run period after its first day (the setpoints of the feedback begin with those of the comfort standard of the
    # zones, without the SET of a previous timestep)
    rows = ems['Date/Time'].str.strip().str.startswith(('07/16', '07/17'))
    for zone in ZONES:
        for kind, (low, high) in (('Cooling', (-0.2, 0.2)), ('Heating', (0.0, 0.8))):
            name = next(c for c in ems.columns
                        if c.startswith(f'EMS:Adaptive {kind} Setpoint Temperature_No Tolerance_{zone} ['))
            difference = ems.loc[rows, name] - results['hook'].loc[rows, name]
            assert low < difference.mean() < high, (zone, kind, difference.mean())
            assert difference.mean() == pytest.approx(measured[zone, kind], abs=0.01), (zone, kind, difference.mean())
            assert difference.abs().mean() < 0.6, (zone, kind, difference.abs().mean())
        operative = next(c for c in ems.columns if c.startswith(f'{zone.replace("_", ":").upper()}:Zone Operative '))
        assert (ems.loc[rows, operative] - results['hook'].loc[rows, operative]).abs().max() < 0.6
        # The outputs of the hook, from the SET of EnergyPlus
        pierce = next(c for c in ems.columns if 'Pierce Model Standard Effective Temperature' in c
                      and zone.replace('_', ':').upper() in c)
        reported = next(c for c in ems.columns if c.startswith(f'EMS:SET_{zone} ['))
        np.testing.assert_allclose(ems[reported].iloc[1:].to_numpy(), ems[pierce].shift(1).iloc[1:].to_numpy(),
                                   atol=1e-6)


@needs_energyplus
def test_without_the_hook_both_backends_give_the_same_results_with_comfort_standard_24(tmp_path, monkeypatch):
    # Finding A4 of the self-audit of 2026-11-11 (decided on 2026-11-12): a model prepared for comfort standard 24 and
    # simulated without its hook ran without an error or a warning, with the setpoints of the comfort standard of its
    # zones and the outputs of the hook at 0. Now run_ep raises with the EMS backend, which cannot run the hook, and
    # the backend of the API warns; EnergyPlus itself (its EMS, without accim) gives the results that the warning tells
    import subprocess

    from accim.run import run_ep
    from accim.sim.ems.hook_setpoints import MissingHookWarning
    from accim.sim.energyplus_api import run_simulations

    from .test_comfort_hooks import _energyplus_with_api

    model, _ = _sun2026_model(tmp_path / 'model', monkeypatch, (1, 8), (1, 10))
    # The model ('sun.idf') and the weather file are in the working folder
    with pytest.raises(ValueError, match=r'which the EMS backend cannot run: sun\.idf\. They would be simulated with '
                                         r'the setpoints of the comfort standard of their zones'):
        run_ep(only_accim_idfs=False, confirm=True, energyplus_version='auto')
    assert sorted(path.name for path in model.parent.iterdir()) == ['Seville.epw', 'sun.idf']
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    ems = subprocess.run([str(energyplus), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-r', '-x', '-w',
                          str(EPW), str(model)], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
    with pytest.warns(MissingHookWarning, match=r'no hook runs before their EMS programs: sun\.idf\.'):
        [result] = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                                   processes=1)
    assert result.success, result.error
    ems_results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
    # Without the hook, its outputs are 0 and the setpoints are those of the ACCIS (with the minimum of 18 °C)
    for zone in ZONES:
        for name in ch.sun2026_zone_outputs(zone):
            assert (ems_results[next(c for c in ems_results.columns if c.startswith(f'EMS:{name} ['))] == 0).all()
    assert (ems_results['EMS:Adaptive Heating Setpoint Temperature_No Tolerance_Block1_Zone1 [C](TimeStep)']
            .iloc[1:] >= 18.0).all()
