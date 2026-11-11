"""Tests for comfort standard 24, INT Sun2026 SET (task F1 of block F, ``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``,
with the decisions of the author of 2026-11-10): the causal SET model of Sun, Brager & Schiavon (2026), Energy and
Buildings 370, 118097 (Fig. 7a: TSV = 0.11·SET − 2.6; the band of TSV ±0.5 is 19.1 to 28.2 °C of SET, and the neutral
SET 23.6 °C), whose setpoints a hook of the backend of the Python API of EnergyPlus sets by inverting the SET of
pythermalcomfort (``pythermalcomfort.models.set_tmp``) by bisection, with the inputs of the People objects of the zones
and, by default, their mean radiant temperature (:mod:`accim.sim.comfort_hooks`).

The unit tests use a fake controller and the Erl interpreter of accim; the last tests simulate the sample model with
EnergyPlus 25.1, through its Python API, and compare the SET of the hook with that of the Pierce model of EnergyPlus
hour by hour (the differences measured are in ``notes/decisions.md``, F1, 2026-11-10; the test reproduces them).
"""
import re
import shutil
import warnings

import numpy as np
import pandas as pd
import pytest

from accim.sim import comfort_hooks as ch
from accim.sim import standards as st

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
    set_tmp = pytest.importorskip('pythermalcomfort.models').set_tmp
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
    pytest.importorskip('pythermalcomfort')
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
    # The minimum of B5 (18 °C) bounds it in the EMS after the hook, with and without the tolerance; without it, the
    # thermostats get the setpoint of the hook with the tolerance (0.1 K)
    bounded = _hook_timestep(_hook_erl(heating_setpoint_minimum=18.0), setpoints=(heating, cooling))
    assert (bounded['AHST_Act_Zone1'], bounded['AHSTnoTol_Zone1']) == (18.0, 18.0)
    free = _hook_timestep(_hook_erl(), setpoints=(heating, cooling))
    assert free['AHST_Act_Zone1'] == pytest.approx(heating + 0.1, abs=1e-4) and free['AHST_Act_Zone1'] < 18


def test_the_hook_of_comfort_standard_24_reads_the_people_objects():
    pytest.importorskip('pythermalcomfort')
    hook = ch.Sun2026SetpointHook(ZONES, clothing_sources={ZONES[0]: 'schedule', ZONES[1]: 'method'})
    assert (hook.tr_mode, hook.met, hook.clo, hook.air_speed, hook.position) == ('zone', None, None, None, None)
    assert (hook.comfort_mode, hook.category, hook.tsv_limit, hook.method) == (1, 80, 0.5, 'bisection')
    assert hook.band == ch.sun2026_set_setpoints()
    # Zone 1: its clothing insulation schedule; zone 2: the calculation method schedule (2) chooses the clothing
    # insulation of the dynamic model; warm enough not to warn
    values = {'ZoneTimeStep': 1 / 6,
              **_zone_values(ZONES[0], 23.0, 24.0, SET_Clo=0.5),
              **_zone_values(ZONES[1], 30.0, 31.0, SET_Clo=0.5, SET_CloValue=0.8, SET_CloMethod=2.0)}
    controller = _Controller(values)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        hook(controller, CALLING_POINT)
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
        for name, kind, units in zip(ch.sun2026_zone_outputs(zone), ('Averaged', 'Averaged', 'Summed'),
                                     ('C', '', 'H')):
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


# EnergyPlus ---------------------------------------------------------------------------------------------------------

#: The hourly differences measured on 2026-11-10 between the SET of each zone that the hook reports (``SET_<zone>``,
#: hourly means) and the SET of the Pierce model of EnergyPlus (K): (mean, mean of the absolute values, maximum absolute
#: value), in 8-14 January and 15-21 July (``notes/decisions.md``, F1)
MEASURED = {
    ('winter', 'Block1_Zone1'): (-0.080, 0.081, 0.191), ('winter', 'Block1_Zone2'): (-0.082, 0.083, 0.204),
    ('summer', 'Block1_Zone1'): (-0.156, 0.156, 0.262), ('summer', 'Block1_Zone2'): (-0.154, 0.154, 0.291),
}


def _sun2026_model(folder, monkeypatch, begin, end):
    """The output IDF of AddAccis of the sample model (INT EN16798, category II, comfort mode 3, full air-conditioning,
    outputs at timestep frequency) from ``begin`` to ``end`` ((month, day)), with a minimum heating setpoint of 18 °C in
    Block1:Zone1, prepared for comfort standard 24, with programs that copy the values that the sensors of the hook
    read into reported variables; return its path and the hook."""
    from accim.sim.accis import AddAccis, load_idf, modify_accis
    from accim.sim.ems.programs import add_program

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
    hook = ch.apply_sun2026_setpoints(idf, output_frequencies=['timestep'])
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

    pytest.importorskip('pythermalcomfort')
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
def test_without_the_hook_both_backends_give_the_same_results_with_comfort_standard_24(tmp_path, monkeypatch):
    import subprocess

    from accim.sim.energyplus_api import run_simulations

    from .test_comfort_hooks import _energyplus_with_api

    model, _ = _sun2026_model(tmp_path / 'model', monkeypatch, (1, 8), (1, 10))
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    ems = subprocess.run([str(energyplus), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-r', '-x', '-w',
                          str(EPW), str(model)], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
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
