"""Tests for the limiter of the drift of the setpoints by the indoor thermal history (task F2 of block F of accim 1.2.0,
``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, with the decisions of the author of 2026-11-10;
:mod:`accim.sim.ems.drift_limiter`): after Parkinson, de Dear & Brager (2020), Energy and Buildings 206, 109559.

- ``drift_mode='rate'``: |setpoint(d) − applied(d − 1)| <= max_drift_rate (0.5 K/day by default); the first occupied day
  without limit, and then the state is the mean of the setpoints applied in the occupied timesteps of the last day with
  occupants (decision 13 of the review of 1.2.0, task S3).
- ``drift_mode='window'``: the setpoints within [T_rm_in − delta_heat, T_rm_in + delta_cool] (1.0 K), with T_rm_in(d) =
  (1 − alpha_indoor)·T_occ_mean(d − 1) + alpha_indoor·T_rm_in(d − 1) (0.8), inactive until one full occupied day, which
  starts it, unless ``initial_T_rm_in`` is given.

The unit tests run the programs of one zone with the Erl interpreter of accim; the last tests simulate the sample model
with EnergyPlus 25.1 (both backends) and compare T_rm_in with a pandas computation from the outputs.
"""
import shutil
import subprocess
import warnings
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from accim.sim.ems import drift_limiter as dl

from .test_comfort_hooks import EPW, SAMPLE_IDF, ZONES, _energyplus_with_api, _model, needs_energyplus, needs_idd


def test_the_arguments_of_the_limiter_are_checked():
    dl.check_drift_arguments()
    dl.check_drift_arguments('rate', 0.5, 0.8, 1.0, 1.0, 24)
    dl.check_drift_arguments('window', alpha_indoor=0, delta_cool=0, delta_heat=0)
    for arguments, message in ((dict(drift_mode='rates'), "drift_mode must be None, 'rate' or 'window'"),
                               (dict(drift_mode=1), "drift_mode must be None, 'rate' or 'window'"),
                               (dict(max_drift_rate=0), r'max_drift_rate must be in \(0, None\]'),
                               (dict(max_drift_rate='0.5'), 'max_drift_rate must be a number'),
                               (dict(alpha_indoor=1), r'alpha_indoor must be in \[0, 1\)'),
                               (dict(alpha_indoor=-0.1), r'alpha_indoor must be in \[0, 1\)'),
                               (dict(delta_cool=-1), r'delta_cool must be in \[0, None\]'),
                               (dict(delta_heat=True), 'delta_heat must be a number'),
                               (dict(initial_T_rm_in='24'), 'initial_T_rm_in must be a number')):
        with pytest.raises(ValueError, match=message):
            dl.check_drift_arguments(**arguments)
    with pytest.raises(ValueError, match="zone 'Z'"):
        dl.check_drift_arguments(max_drift_rate=-1, where='Z')
    # The inputs of a zone: none without drift_mode; with it, the arguments given, those of the zone, or the defaults
    assert dl.drift_inputs({'max_drift_rate': 0.3}) == {}
    assert dl.drift_inputs({'drift_mode': 'rate'}) == {'DriftMode': 1, 'MaxDriftRate': 0.5, 'AlphaIndoor': 0.8,
                                                       'DeltaCool': 1.0, 'DeltaHeat': 1.0}
    assert dl.drift_inputs({'drift_mode': 'window', 'initial_T_rm_in': 24, 'delta_cool': 2}) == {
        'DriftMode': 2, 'MaxDriftRate': 0.5, 'AlphaIndoor': 0.8, 'DeltaCool': 2, 'DeltaHeat': 1.0, 'InitTrmIn': 24}
    current = {'DriftMode': 2, 'MaxDriftRate': 0.3, 'AlphaIndoor': 0.9, 'DeltaCool': 1.5, 'DeltaHeat': 1.0}
    assert dl.drift_inputs({'delta_heat': 2.0}, current) == dict(current, DeltaHeat=2.0)
    assert dl.drift_inputs({'drift_mode': 'rate'}, current) == dict(current, DriftMode=1)
    assert dl.zone_outputs('Z') == ['T_rm_in_Z', 'DriftTargetAHST_Z', 'DriftTargetACST_Z', 'DriftAppliedAHST_Z',
                                    'DriftAppliedACST_Z', 'DriftLimitedHours_Z']


def _drift_erl(**arguments):
    """The programs of the ACCIS of one zone, Zone1 (INT EN16798, category II, comfort mode 3, a tolerance of 0.1 K,
    full air-conditioning), with the program of the setpoints of a hook (which gives the targets of the tests) and the
    limiter of the drift of the arguments, compiled by the Erl interpreter at the beginning of an environment."""
    from accim.sim.ems import hook_setpoints as hs
    from accim.sim.ems import setpoint_limits as sl
    from accim.sim.ems.erl import ErlProgramSet, variables_in_programs
    from accim.sim.ems.inputs import input_lines, input_values
    from accim.sim.ems.programs import accis_programs

    model = SimpleNamespace(ems_names=['Zone1'], ems_zones=['Zone1'], is_mixed_mode=False, windows=[],
                            window_zones=[])
    programs = dict(accis_programs(model))
    values = input_values(dict(dict(comfort_standard=1, category=2, comfort_mode=3, setpoint_tolerance=0.1),
                               **arguments))
    programs['SetInputData_Zone1'] = input_lines(values, mixed_mode=False)
    programs['ApplyHookSetpoints_Zone1'] = hs.program_lines('Zone1')
    programs['InitHookSetpoints'] = hs.init_program_lines(['Zone1'])
    run = list(programs['RunACCIS_Zone1'])
    run.insert(run.index('run SetAST') + 1, 'run ApplyHookSetpoints_Zone1')
    if 'DriftMode' in values:
        programs[f'{dl.PROGRAM_PREFIX}Zone1'] = dl.program_lines('Zone1', initial='InitTrmIn' in values)
        programs[dl.INIT_PROGRAM] = dl.init_program_lines(['Zone1'])
        run.insert(run.index('run SetASTnoTol'), f'run {dl.PROGRAM_PREFIX}Zone1')
    minimum, maximum = (values.get(name) is not None for name in sl.INPUTS)
    if minimum or maximum:
        programs['ApplySetpointLimits_Zone1'] = sl.limit_program_lines(minimum, maximum)
        run.insert(run.index('run SetASTnoTol') + 1, 'run ApplySetpointLimits_Zone1')
    programs['RunACCIS_Zone1'] = run
    erl = ErlProgramSet(programs, global_variables=set().union(*variables_in_programs(programs).values()))
    erl.strict = True
    erl.run('InitASTvariables')
    erl.run('InitHookSetpoints')
    if 'DriftMode' in values:
        erl.run(dl.INIT_PROGRAM)
    return erl


def _day(erl, day, targets, operative=24.0, occupied_hours=range(8, 18), warmup=False):
    """The 24 hourly timesteps of a day (ZoneTimeStep 1 h) in which a hook gives the targets (heating, cooling) of the
    setpoints (a pair, or a list of 24 pairs, one for each hour); the operative temperature of the zone is ``operative``
    (a number, or one for each hour), and the zone is occupied in ``occupied_hours``. Return the variables of the ACCIS
    of each timestep."""
    rows = []
    for hour in range(24):
        temperature = operative[hour] if isinstance(operative, (list, tuple)) else operative
        heating, cooling = targets[hour] if isinstance(targets, list) else targets
        for name, value in dict(RMOT=20.0, PMOT=20.0, DayOfYear=float(day), CurrentTime=float(hour + 1),
                                ZoneTimeStep=1.0, WarmupFlag=1.0 if warmup else 0.0, Zone1_OpT=temperature,
                                Occ_count_Zone1=1.0 if hour in occupied_hours else 0.0).items():
            erl.set(name, value)
        erl.set('HookAHST_Zone1', heating)
        erl.set('HookACST_Zone1', cooling)
        erl.set('HookSetpoints_Zone1', 1.0)
        erl.run('RunACCIS_Zone1')
        rows.append({name: erl.get(name) for name in (
            'AHST_Act_Zone1', 'ACST_Act_Zone1', 'AHSTnoTol_Zone1', 'ACSTnoTol_Zone1', 'T_rm_in_Zone1',
            'DriftTargetAHST_Zone1', 'DriftTargetACST_Zone1', 'DriftAppliedAHST_Zone1', 'DriftAppliedACST_Zone1',
            'DriftLimitedHours_Zone1')})
    return rows


def _all(rows, name, value):
    """True if the variable has the value (to 1e-9) in all the rows."""
    return all(row[name] == pytest.approx(value, abs=1e-9) for row in rows)


def test_the_rate_reaches_a_step_of_5_k_in_10_days():
    # Without the tolerance, the arithmetic of the setpoints is exact in binary
    erl = _drift_erl(drift_mode='rate', setpoint_tolerance=0)
    # The first occupied day: the targets without limit
    first = _day(erl, 100, (20.0, 26.0))
    assert {(row['AHSTnoTol_Zone1'], row['ACSTnoTol_Zone1']) for row in first} == {(20.0, 26.0)}
    assert sum(row['DriftLimitedHours_Zone1'] for row in first) == 0
    # A step of 5 K of the targets: 0.5 K a day, so the setpoints reach them after 10 days
    for day in range(1, 13):
        rows = _day(erl, 100 + day, (25.0, 31.0))
        expected = (min(20.0 + 0.5 * day, 25.0), min(26.0 + 0.5 * day, 31.0))
        assert {(row['AHSTnoTol_Zone1'], row['ACSTnoTol_Zone1']) for row in rows} == {expected}, day
        # The thermostats get them (rounded, exactly)
        assert {(row['AHST_Act_Zone1'], row['ACST_Act_Zone1']) for row in rows} == {expected}, day
        assert {(row['DriftTargetAHST_Zone1'], row['DriftTargetACST_Zone1']) for row in rows} == {(25.0, 31.0)}
        # The occupied hours with the limiter active (10 a day) until the targets are reached on day 10
        assert sum(row['DriftLimitedHours_Zone1'] for row in rows) == (10 if day < 10 else 0), day
    # Downwards, the same
    rows = _day(erl, 113, (19.0, 25.0))
    assert {(row['AHSTnoTol_Zone1'], row['ACSTnoTol_Zone1']) for row in rows} == {(24.5, 30.5)}
    # With the tolerance (0.1 K), the thermostats get the setpoints of the limiter with it
    erl = _drift_erl(drift_mode='rate')
    _day(erl, 100, (20.0, 26.0))
    rows = _day(erl, 101, (25.0, 31.0))
    assert _all(rows, 'AHSTnoTol_Zone1', 20.5) and _all(rows, 'ACSTnoTol_Zone1', 26.5)
    assert _all(rows, 'AHST_Act_Zone1', 20.6) and _all(rows, 'ACST_Act_Zone1', 26.4)


def test_the_rate_starts_after_the_first_occupied_day_and_skips_the_warm_up():
    erl = _drift_erl(drift_mode='rate', max_drift_rate=1.0, setpoint_tolerance=0)
    # The warm-up days do not count, nor the days without occupants before the first occupied one
    _day(erl, 100, (20.0, 26.0), warmup=True)
    _day(erl, 100, (21.0, 27.0), warmup=True)
    unoccupied = _day(erl, 100, (18.0, 24.0), occupied_hours=())
    assert {(row['AHSTnoTol_Zone1'], row['ACSTnoTol_Zone1']) for row in unoccupied} == {(18.0, 24.0)}
    occupied = _day(erl, 101, (23.0, 29.0))
    assert {(row['AHSTnoTol_Zone1'], row['ACSTnoTol_Zone1']) for row in occupied} == {(23.0, 29.0)}
    limited = _day(erl, 102, (26.0, 32.0), occupied_hours=())
    assert {(row['AHSTnoTol_Zone1'], row['ACSTnoTol_Zone1']) for row in limited} == {(24.0, 30.0)}
    # Without occupants, no hours with the limiter active
    assert sum(row['DriftLimitedHours_Zone1'] for row in limited) == 0
    # A day without occupied timesteps keeps the state of the last occupied day (decisions 13 and 14 of the review of
    # 1.2.0, task S3): the setpoints of day 103 are within 1 K of those of day 101, not of those applied on day 102
    assert {(row['AHSTnoTol_Zone1'], row['ACSTnoTol_Zone1']) for row in _day(erl, 103, (26.0, 32.0))} == {
        (24.0, 30.0)}
    assert {(row['AHSTnoTol_Zone1'], row['ACSTnoTol_Zone1']) for row in _day(erl, 104, (26.0, 32.0))} == {
        (25.0, 31.0)}


def test_the_rate_takes_the_mean_of_the_setpoints_applied_in_the_occupied_timesteps():
    # Decision 13 of the review of 1.2.0 (task S3): the state of the rate is the mean of the setpoints applied in the
    # occupied timesteps of the previous day (8 to 17 h), not the setpoint of its last timestep: the setpoints of a hook
    # that rise 0.25 K an hour (exact in binary, as the setpoints without the tolerance)
    erl = _drift_erl(drift_mode='rate', setpoint_tolerance=0)
    rising = [(20.0 + 0.25 * hour, 26.0 + 0.25 * hour) for hour in range(24)]
    occupied = list(range(8, 18))
    first = _day(erl, 100, rising)
    # The first occupied day, without limit: its last timestep has 25.75 and 31.75 degC, its occupied ones a mean of
    # 23.125 and 29.125 degC
    applied = np.array([(row['DriftAppliedAHST_Zone1'], row['DriftAppliedACST_Zone1']) for row in first])
    np.testing.assert_array_equal(applied, rising)
    reference = applied[occupied].mean(axis=0)
    assert tuple(reference) == (23.125, 29.125) and tuple(applied[-1]) == (25.75, 31.75)
    for day in (101, 102, 103):
        rows = _day(erl, day, rising)
        expected = np.clip(np.array(rising), reference - 0.5, reference + 0.5)
        applied = np.array([(row['DriftAppliedAHST_Zone1'], row['DriftAppliedACST_Zone1']) for row in rows])
        np.testing.assert_allclose(applied, expected, rtol=0, atol=1e-12)
        np.testing.assert_allclose([(row['AHSTnoTol_Zone1'], row['ACSTnoTol_Zone1']) for row in rows], expected,
                                   rtol=0, atol=1e-4)
        # The hours of the limiter: the occupied hours with a limited setpoint
        limited = (np.abs(expected - np.array(rising)) > 1e-12).any(axis=1)
        assert sum(row['DriftLimitedHours_Zone1'] for row in rows) == sum(limited[hour] for hour in occupied)
        reference = applied[occupied].mean(axis=0)
    # The state is not the setpoint of the last timestep, which would have allowed 25.25 to 26.25 degC on day 101
    assert reference[0] < 23.7


def test_the_window_follows_the_running_mean_of_the_occupied_hours():
    erl = _drift_erl(drift_mode='window')
    # Day 1: inactive, the targets; T_rm_in starts with the mean operative temperature of its occupied hours
    temperatures = [20.0] * 8 + [23.0, 24.0, 25.0, 26.0, 25.0, 24.0, 23.0, 24.0, 25.0, 26.0] + [20.0] * 6
    first = _day(erl, 10, (20.0, 27.0), operative=temperatures)
    assert _all(first, 'AHSTnoTol_Zone1', 20.0) and _all(first, 'ACSTnoTol_Zone1', 27.0)
    assert sum(row['DriftLimitedHours_Zone1'] for row in first) == 0
    # The mean of the values of the sensor of the operative temperature in the occupied timesteps (8 to 17; in a
    # simulation, the sensor reads that of the previous timestep)
    trm = float(np.mean(temperatures[8:18]))
    rows = _day(erl, 11, (20.0, 27.0), operative=26.0)
    assert _all(rows, 'T_rm_in_Zone1', trm)
    # The targets clipped to the window T_rm_in ± 1 K
    assert _all(rows, 'AHSTnoTol_Zone1', trm - 1.0) and _all(rows, 'ACSTnoTol_Zone1', trm + 1.0)
    assert _all(rows, 'DriftAppliedAHST_Zone1', trm - 1.0) and _all(rows, 'DriftTargetAHST_Zone1', 20.0)
    assert sum(row['DriftLimitedHours_Zone1'] for row in rows) == 10
    # The next day: (1 − 0.8)·T_occ_mean + 0.8·T_rm_in, the occupied hours of day 11 at 26 °C
    trm = 0.2 * 26.0 + 0.8 * trm
    rows = _day(erl, 12, (20.0, 27.0), operative=26.0)
    assert _all(rows, 'T_rm_in_Zone1', trm)
    # A day without occupants does not change it
    trm = 0.2 * 26.0 + 0.8 * trm
    unoccupied = _day(erl, 13, (20.0, 27.0), operative=30.0, occupied_hours=())
    rows = _day(erl, 14, (20.0, 27.0), operative=26.0)
    assert _all(unoccupied + rows, 'T_rm_in_Zone1', trm)
    # The targets within the window are not changed
    erl = _drift_erl(drift_mode='window', delta_cool=5.0, delta_heat=5.0)
    _day(erl, 10, (20.0, 27.0), operative=24.0)
    rows = _day(erl, 11, (20.0, 27.0), operative=24.0)
    assert _all(rows, 'AHSTnoTol_Zone1', 20.0) and _all(rows, 'ACSTnoTol_Zone1', 27.0)
    assert sum(row['DriftLimitedHours_Zone1'] for row in rows) == 0


def test_the_window_with_the_initial_running_mean_and_the_minimum():
    # initial_T_rm_in: active from the first day, and the first update is that of the formula
    erl = _drift_erl(drift_mode='window', initial_T_rm_in=24.0, delta_heat=2.0, delta_cool=0.5)
    first = _day(erl, 10, (20.0, 27.0), operative=25.0)
    assert _all(first, 'T_rm_in_Zone1', 24.0)
    assert _all(first, 'AHSTnoTol_Zone1', 22.0) and _all(first, 'ACSTnoTol_Zone1', 24.5)
    second = _day(erl, 11, (20.0, 27.0), operative=25.0)
    assert _all(second, 'T_rm_in_Zone1', 0.2 * 25.0 + 0.8 * 24.0)
    # The minimum of B5 bounds the setpoints after the limiter
    erl = _drift_erl(drift_mode='window', initial_T_rm_in=18.0, heating_setpoint_minimum=19.0)
    rows = _day(erl, 10, (16.0, 27.0), operative=18.0)
    assert _all(rows, 'DriftAppliedAHST_Zone1', 17.0) and _all(rows, 'DriftAppliedACST_Zone1', 19.0)
    assert _all(rows, 'AHSTnoTol_Zone1', 19.0) and _all(rows, 'ACSTnoTol_Zone1', 19.0)


@needs_idd
def test_without_drift_mode_the_output_idfs_do_not_change(tmp_path, monkeypatch):
    from accim.sim.accis import AddAccis

    texts = {}
    for name, arguments in (('default', {}), ('none', dict(drift_mode=None, max_drift_rate=0.3, alpha_indoor=0.9,
                                                           delta_cool=2.0, delta_heat=2.0, initial_T_rm_in=None))):
        folder = tmp_path / name
        folder.mkdir()
        shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
        monkeypatch.chdir(folder)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                     output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                     energyplus_version='auto', setpoint_type='temperature', comfort_standard=[1, 2],
                     category=[2, 80], comfort_mode=[3], confirm=True, verbose=False, **arguments)
        texts[name] = {path.name: path.read_bytes() for path in folder.glob('TestModel[[]*.idf')}
    assert texts['default'] == texts['none'] and len(texts['default']) == 2
    assert not any(b'Drift' in text or b'T_rm_in' in text for text in texts['default'].values())


@needs_idd
def test_addaccis_and_modify_accis_add_the_limiter(tmp_path, monkeypatch):
    from accim.sim.accis import AddAccis, load_idf, modify_accis
    from accim.sim.comfort_hooks import apply_set_setpoints
    from accim.sim.ems.inputs import input_programs, read_inputs

    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', comfort_standard=[1], category=[2], comfort_mode=[3], confirm=True,
                 verbose=False, drift_mode='window', heating_setpoint_minimum=18,
                 zone_arguments={'Block1:Zone2': {'drift_mode': 'rate', 'max_drift_rate': 0.3}})
    [path] = tmp_path.glob('TestModel[[]*.idf')
    idf = load_idf(path)
    inputs = {zone: read_inputs(program) for zone, program in input_programs(idf).items()}
    assert {name: inputs['Block1_Zone1'][name] for name in dl.INPUTS[:5]} == {
        'DriftMode': 2, 'MaxDriftRate': 0.5, 'AlphaIndoor': 0.8, 'DeltaCool': 1.0, 'DeltaHeat': 1.0}
    assert (inputs['Block1_Zone2']['DriftMode'], inputs['Block1_Zone2']['MaxDriftRate']) == (1, 0.3)
    programs = {p.Name: [str(v).strip() for v in p.fieldvalues[2:]]
                for p in idf.idfobjects['EnergyManagementSystem:Program']}
    for zone in ZONES:
        assert programs[f'{dl.PROGRAM_PREFIX}{zone}'] == dl.program_lines(zone)
        run = programs[f'RunACCIS_{zone}']
        # After SetAST, before SetASTnoTol and the minimum of B5
        position = run.index('run SetAST')
        assert run[position + 1:position + 4] == [f'run {dl.PROGRAM_PREFIX}{zone}', 'run SetASTnoTol',
                                                  f'run ApplySetpointLimits_{zone}']
    assert sorted(programs[dl.INIT_PROGRAM]) == sorted(dl.init_program_lines(ZONES))
    manager = idf.getobject('EnergyManagementSystem:ProgramCallingManager', dl.INIT_PROGRAM)
    assert (manager.EnergyPlus_Model_Calling_Point, manager.Program_Name_1) == ('BeginNewEnvironment',
                                                                                dl.INIT_PROGRAM)
    declared = {str(name) for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
                for name in g.fieldvalues[1:]}
    ems_outputs = {o.Name: o for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    requested = {(o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']}
    assert set(dl.INPUTS) <= declared
    for zone in ZONES:
        for name, (prefix, (units, kind)) in zip(dl.zone_outputs(zone), dl.OUTPUTS.items()):
            assert name in declared and (name, 'Hourly') in requested
            assert (ems_outputs[name].Units, ems_outputs[name].Type_of_Data_in_Variable) == (units, kind)
    # A hook runs before the limiter
    apply_set_setpoints(idf, 27, 21, met=1.1, clo=0.5, air_speed=0.1)
    run = [str(v).strip() for v in idf.getobject('EnergyManagementSystem:Program', 'RunACCIS_Block1_Zone1').fieldvalues[2:]]
    position = run.index('run SetAST')
    assert run[position + 1:position + 3] == ['run ApplyHookSetpoints_Block1_Zone1',
                                              f'run {dl.PROGRAM_PREFIX}Block1_Zone1']
    # modify_accis: None keeps the arguments; the others change those of the zones with the limiter
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        modify_accis(idf, delta_cool=2.0, initial_T_rm_in=23.5)
    inputs = {zone: read_inputs(program) for zone, program in input_programs(idf).items()}
    assert (inputs['Block1_Zone1']['DriftMode'], inputs['Block1_Zone1']['DeltaCool'],
            inputs['Block1_Zone1']['InitTrmIn']) == (2, 2.0, 23.5)
    assert (inputs['Block1_Zone2']['MaxDriftRate'], inputs['Block1_Zone2']['DeltaCool']) == (0.3, 2.0)
    assert ([str(v).strip() for v in idf.getobject('EnergyManagementSystem:Program',
                                                   f'{dl.PROGRAM_PREFIX}Block1_Zone1').fieldvalues[2:]]
            == dl.program_lines('Block1_Zone1', initial=True))
    # The programs are not repeated
    assert sum(p.Name == f'{dl.PROGRAM_PREFIX}Block1_Zone1' for p in idf.idfobjects['EnergyManagementSystem:Program']) == 1


@needs_idd
def test_the_errors_of_the_arguments_of_the_limiter(tmp_path, monkeypatch):
    from accim.sim.accis import AddAccis, modify_accis

    idf = _model(tmp_path)
    with pytest.raises(ValueError, match='need drift_mode: no zone has the limiter'):
        modify_accis(idf, max_drift_rate=0.3)
    with pytest.raises(ValueError, match="drift_mode must be None, 'rate' or 'window'"):
        modify_accis(idf, drift_mode='fast')
    with pytest.raises(ValueError, match=r"alpha_indoor must be in \[0, 1\) \(zone 'Block1_Zone1'\)"):
        modify_accis(idf, drift_mode='window', zone_arguments={'Block1:Zone1': {'alpha_indoor': 1.5}})
    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="drift_mode needs setpoint_type 'temperature'"):
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='pmv', comfort_standard=[1], category=[2], comfort_mode=[3], confirm=True,
                 verbose=False, drift_mode='rate')
    with pytest.raises(ValueError, match=r'max_drift_rate must be in \(0, None\]'):
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', comfort_standard=[1], category=[2], comfort_mode=[3], confirm=True,
                 verbose=False, drift_mode='rate', max_drift_rate=0)


def test_the_window_cannot_be_narrower_than_twice_the_tolerance(tmp_path, monkeypatch):
    # Finding A9 of the self-audit of 2026-11-11: where both setpoints reach the limits of the window, the thermostats
    # get them with the tolerance (the heating one raised, the cooling one lowered), so a window narrower than twice
    # the tolerance crosses them
    from accim.sim.accis import AddAccis, modify_accis
    from accim.sim.ems.inputs import input_programs, read_inputs

    message = r"With drift_mode='window', delta_heat \+ delta_cool \({} K\) must be at least twice the tolerance"
    with pytest.raises(ValueError, match=message.format('0.15') + r' of the setpoints \(0.1 K\):'):
        dl.check_window_width(0.05, 0.1, 0.1)
    for arguments in ((0.1, 0.1, 0.1), (0.1, 0.1, -0.1), (None, 0.1, 0.1), (0.0, 0.0, 0.0)):
        dl.check_window_width(*arguments)
    idf = _model(tmp_path)
    before = idf.idfstr()
    # The tolerance of modify_accis (0.1 K by default), or that of a zone
    with pytest.raises(ValueError, match=message.format('0.1') + r".*\(zone 'Block1_Zone[12]'\)"):
        modify_accis(idf, drift_mode='window', delta_cool=0.0, delta_heat=0.1)
    with pytest.raises(ValueError, match=message.format('1') + r" of the setpoints \(0.6 K\) \(zone 'Block1_Zone2'\)"):
        modify_accis(idf, drift_mode='window', delta_cool=0.5, delta_heat=0.5,
                     zone_arguments={'Block1:Zone2': {'setpoint_tolerance': 0.6}})
    assert idf.idfstr() == before
    # A zone with the window keeps its deltas: a larger tolerance later is checked against them
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        modify_accis(idf, drift_mode='window', delta_cool=0.3, delta_heat=0.3)
    assert all(read_inputs(p)['DriftMode'] == 2 for p in input_programs(idf).values())
    with pytest.raises(ValueError, match=message.format('0.6') + r' of the setpoints \(0.5 K\)'):
        modify_accis(idf, setpoint_tolerance=0.5)
    # AddAccis, with the largest tolerance of the output IDFs
    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)
    arguments = dict(script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                     output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                     energyplus_version='auto', setpoint_type='temperature', comfort_standard=[1], category=[2],
                     comfort_mode=[3], confirm=True, verbose=False)
    with pytest.raises(ValueError, match=message.format('0') + r' of the setpoints \(0.1 K\)'):
        AddAccis(**arguments, drift_mode='window', delta_cool=0.0, delta_heat=0.0)
    with pytest.raises(ValueError, match=message.format('0.5') + r' of the setpoints \(0.3 K\)'):
        AddAccis(**arguments, drift_mode='window', delta_cool=0.25, delta_heat=0.25, setpoint_tolerance_start=0.1,
                 setpoint_tolerance_end=0.3)
    with pytest.raises(ValueError, match=message.format('0.4') + r".*\(zone 'Block1:Zone1'\)"):
        AddAccis(**arguments, drift_mode='rate', zone_arguments={'Block1:Zone1': {'drift_mode': 'window',
                                                                                 'delta_cool': 0.2, 'delta_heat': 0.2,
                                                                                 'setpoint_tolerance': 0.25}})
    assert not list(tmp_path.glob('TestModel[[]*.idf'))


def test_addaccis_warns_of_the_arguments_of_the_limiter_without_drift_mode(tmp_path, monkeypatch):
    # Finding A11 of the self-audit of 2026-11-11: without drift_mode in any zone, the other arguments of the limiter
    # are not used (the output IDFs have no limiter, as before), so AddAccis warns of them (modify_accis raises)
    from pathlib import Path

    from accim.sim.accis import AddAccis

    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)
    arguments = dict(script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                     output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                     energyplus_version='auto', setpoint_type='temperature', comfort_standard=[1], category=[2],
                     comfort_mode=[3], confirm=True, verbose=False)
    message = (r"The arguments of the limiter of the drift of the setpoints \['max_drift_rate', 'delta_cool "
               r"\(Block1:Zone2\)'\] are not used: no zone has drift_mode")
    with pytest.warns(UserWarning, match=message):
        result = AddAccis(**arguments, max_drift_rate=0.3, zone_arguments={'Block1:Zone2': {'delta_cool': 1.5}})
    [path] = result.output_idfs.paths.values()
    assert 'DriftMode' not in Path(path).read_text()
    # Not with drift_mode, nor with the defaults
    for extra in (dict(drift_mode='rate', max_drift_rate=0.3), {}):
        for output in tmp_path.glob('TestModel[[]*.idf'):
            output.unlink()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            AddAccis(**arguments, **extra)
        assert not [w for w in caught if 'are not used: no zone has drift_mode' in str(w.message)], extra


def test_the_ems_code_of_the_limiter():
    from accim.sim.preview import compute_setpoints
    from accim.utils.ems_code import get_setpoint_ems_code, get_setpoint_ems_programs

    code = get_setpoint_ems_code(1, 2, 3, drift_mode='window', initial_T_rm_in=24)
    assert '! --- ApplyDriftLimiter_<zone>: after the setpoints, the limiter of their drift ---' in code
    assert code.index('ApplyDriftLimiter_<zone>: after') < code.index('! --- SetASTnoTol')
    assert 'set DriftMode = 2' in code and 'set InitTrmIn = 24' in code and 'set T_rm_in_<zone> = InitTrmIn' in code
    assert 'DriftMode' not in get_setpoint_ems_code(1, 2, 3)
    programs = get_setpoint_ems_programs(1, 2, 3, drift_mode='rate')
    assert list(programs)[0] == dl.INIT_PROGRAM
    assert list(programs)[-2:] == [f'{dl.PROGRAM_PREFIX}<zone>', 'SetASTnoTol']
    with pytest.raises(ValueError, match="drift_mode must be None, 'rate' or 'window'"):
        get_setpoint_ems_code(1, 2, 3, drift_mode='both')
    with pytest.raises(ValueError, match='compute_setpoints cannot calculate the limiter of the drift'):
        compute_setpoints(EPW, 1, 2, 3, drift_mode='rate')


def test_the_fields_of_the_limiter_in_the_graphical_user_interface(tmp_path):
    from accim.gui import forms

    assert list(forms.DRIFT_FIELDS) == list(dl.ARGUMENTS) and forms.ADD_ACCIS_DEFAULTS['drift_mode'] == ''
    form = dict(forms.ADD_ACCIS_DEFAULTS, folder=str(tmp_path), idfs=['model.idf'])
    # Without drift_mode, no limiter (the other fields are not used)
    assert forms.drift_arguments(form) == {}
    assert not set(dl.ARGUMENTS) & set(forms.add_accis_arguments(form))
    form.update(drift_mode='window', initial_T_rm_in='24', delta_cool='1.5')
    assert forms.drift_arguments(form) == dict(drift_mode='window', max_drift_rate=0.5, alpha_indoor=0.8,
                                               delta_cool=1.5, delta_heat=1.0, initial_T_rm_in=24)
    arguments = forms.add_accis_arguments(form)
    assert {name: arguments[name] for name in dl.ARGUMENTS} == forms.drift_arguments(form)
    # The EMS code of the form has the limiter
    calls = forms.setpoint_ems_code_calls(dict(form, comfort_standard=[1], category='2', comfort_mode='3'))
    assert all(kwargs['drift_mode'] == 'window' for _, kwargs in calls)
    for values, message in ((dict(setpoint_type='pmv'), 'the PMV-based setpoints have no limiter'),
                            (dict(max_drift_rate='0'), r'max_drift_rate must be in \(0, None\]'),
                            (dict(drift_mode='fast'), "drift_mode must be None, 'rate' or 'window'"),
                            (dict(alpha_indoor='x'), "alpha_indoor: 'x' is not a number")):
        with pytest.raises(forms.FormError, match=message):
            forms.drift_arguments(dict(form, **values))


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _drift_model(folder, monkeypatch, begin=(4, 1), end=(4, 21)):
    """The output IDF of AddAccis of the sample model (INT EN16798, category II, comfort mode 3, full air-conditioning,
    outputs at timestep frequency) with the window in Block1:Zone1 and the rate in Block1:Zone2."""
    from accim.sim.accis import AddAccis, load_idf

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
                 verbose=False, drift_mode='window', zone_arguments={'Block1:Zone2': {'drift_mode': 'rate'}})
    [path] = folder.glob('TestModel[[]*.idf')
    shutil.copy(path, folder / 'drift.idf')
    return folder / 'drift.idf'


@needs_energyplus
def test_the_limiter_in_energyplus_with_both_backends(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations
    from accim.utils.verification import verify_accim_simulation

    model = _drift_model(tmp_path / 'model', monkeypatch)
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    ems = subprocess.run([str(energyplus), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-r', '-x', '-w',
                          str(EPW), str(model)], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
    [result] = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                               processes=1)
    assert result.success, result.error
    results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / 'api' / 'run.csv'), results, check_exact=True)
    steps = 6
    assert len(results) == 21 * 24 * steps
    days = np.arange(len(results)) // (24 * steps)
    for zone in ZONES:
        key = zone.replace('_', ':').upper()

        def column(name):
            return results[next(c for c in results.columns if c.startswith(name))].to_numpy()

        # T_rm_in from the outputs, in pandas: the operative temperature of the previous timestep (which the EMS reads)
        # in the timesteps with occupants (the outputs of the occupants of the ACCIS)
        operative = pd.Series(column(f'{key}:Zone Operative Temperature [C]')).shift(1).to_numpy()
        occupied = column(f'EMS:Occupied Hours_{zone} [') > 0
        frame = pd.DataFrame({'day': days, 'operative': np.where(occupied, operative, np.nan)})
        means = frame.groupby('day')['operative'].mean()
        expected, trm = {}, None
        for day in range(1, days.max() + 1):
            mean = means.get(day - 1)
            if mean is not None and not np.isnan(mean):
                trm = mean if trm is None else 0.2 * mean + 0.8 * trm
            expected[day] = trm
        reported = column(f'EMS:T_rm_in_{zone} [')
        for day, value in expected.items():
            assert reported[days == day] == pytest.approx(value, abs=1e-4), (zone, day)
        target_heating, target_cooling = column(f'EMS:DriftTargetAHST_{zone} ['), column(f'EMS:DriftTargetACST_{zone} [')
        heating = column(f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone} [')
        cooling = column(f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [')
        active = days >= 1
        if zone == 'Block1_Zone1':
            # The window: the targets clipped to T_rm_in ± 1 K (the setpoints of the thermostats are rounded)
            low, high = reported - 1.0, reported + 1.0
            np.testing.assert_allclose(heating[active], np.clip(target_heating, low, high)[active], atol=1e-3)
            np.testing.assert_allclose(cooling[active], np.clip(target_cooling, low, high)[active], atol=1e-3)
            assert (heating[active] > target_heating[active] + 1).any()
        else:
            # The rate: within 0.5 K of the mean of the setpoints applied in the occupied timesteps of the last day with
            # occupants (decision 13 of the review of 1.2.0, task S3). The setpoints of the ACCIS are constant in the
            # occupied timesteps of each day (the first timestep of a day, with the running mean of the previous day,
            # is not occupied in this office), so that mean is the setpoint of the end of the day, the state before
            applied = column(f'EMS:DriftAppliedAHST_{zone} [')
            reference = None
            for day in range(days.max() + 1):
                if reference is not None:
                    assert np.abs(applied[days == day] - reference).max() <= 0.5 + 1e-6, day
                today = (days == day) & occupied
                if today.any():
                    assert np.ptp(applied[today]) < 1e-9, day
                    reference = applied[today].mean()
                    assert reference == pytest.approx(applied[days == day][-1], abs=1e-9), day
        np.testing.assert_allclose(heating[~active], target_heating[~active], atol=1e-3)
    # verify_accim_simulation checks the targets of the limiter, not the setpoints applied
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        report = verify_accim_simulation(str(tmp_path / 'ems' / 'run.eso'), str(model), epw=str(EPW))
    assert report.empty


class _RisingHook:
    """A hook of the setpoints (as those of :mod:`accim.sim.comfort_hooks`, run before the EMS programs) whose setpoints
    change within the day: 20 + 0.25·h and 26 + 0.25·h °C in the hour h (0 to 23) of the day."""

    runs_before_programs = True

    def __init__(self, zones):
        self.zones = list(zones)

    def __call__(self, controller, calling_point):
        from accim.sim.comfort_hooks import _give_setpoints
        from accim.sim.energyplus_api.controller import _DYNAMIC_BUILT_INS

        if calling_point.upper() == 'BEGINTIMESTEPBEFOREPREDICTOR':
            # The hour of the API, as the controller gives the built-in variable Hour to the programs that read it
            # (it updates only those, and no program of this model reads Hour)
            hour = _DYNAMIC_BUILT_INS['HOUR'](controller.api.exchange.api, controller.state)
            for zone in self.zones:
                _give_setpoints(controller, zone, 20 + 0.25 * hour, 26 + 0.25 * hour)


@needs_energyplus
def test_the_rate_with_the_setpoints_of_a_hook_that_change_within_the_day(tmp_path, monkeypatch):
    # Decision 13 of the review of 1.2.0 (task S3), with both backends: the setpoints of a hook that rise 0.25 K an hour
    # (with the backend of the API) and the same setpoints given by the programs of the model at the beginning of
    # RunACCIS_<zone> (with the EMS backend, which cannot run the hook), and the rate in both zones, from Monday 1 to
    # Tuesday 9 April 2002 (a weekend without occupants in the office of the sample model)
    from accim.sim.accis import load_idf, modify_accis
    from accim.sim.ems.hook_setpoints import set_hook_setpoints_code
    from accim.sim.ems.programs import set_program_lines
    from accim.sim.energyplus_api import run_simulations

    model_path = _drift_model(tmp_path / 'model', monkeypatch, end=(4, 9))
    model = load_idf(model_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        modify_accis(model, drift_mode='rate')
    set_hook_setpoints_code(model, ZONES)
    model.save()
    emulated = load_idf(model_path)
    for zone in ZONES:
        program = emulated.getobject('EnergyManagementSystem:Program', f'RunACCIS_{zone}')
        lines = [str(value).strip() for value in program.fieldvalues[2:]]
        set_program_lines(program, [f'set HookAHST_{zone} = 20+0.25*Hour', f'set HookACST_{zone} = 26+0.25*Hour',
                                    f'set HookSetpoints_{zone} = 1'] + lines)
    emulated.saveas(str(tmp_path / 'emulated.idf'))
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    ems = subprocess.run([str(energyplus), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-r', '-x', '-w',
                          str(EPW), str(tmp_path / 'emulated.idf')], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
    [result] = run_simulations([(model_path, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                               processes=1, before_programs=[_RisingHook(ZONES)])
    assert result.success, result.error
    results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / 'api' / 'run.csv'), results, check_exact=True)
    steps = 6
    assert len(results) == 9 * 24 * steps
    days = np.arange(len(results)) // (24 * steps)
    hours = (np.arange(len(results)) // steps) % 24

    def column(name):
        return results[next(c for c in results.columns if c.startswith(name))].to_numpy()

    for zone in ZONES:
        target = column(f'EMS:DriftTargetAHST_{zone} [')
        applied = column(f'EMS:DriftAppliedAHST_{zone} [')
        occupied = column(f'EMS:Occupied Hours_{zone} [') > 0
        # The targets are the setpoints of the hook
        np.testing.assert_allclose(target, 20 + 0.25 * hours, rtol=0, atol=1e-4)
        # The state of each day is the mean of the setpoints applied in the occupied timesteps of the last day with
        # occupants: the first day without limit, and the weekend keeps the state of Friday
        reference, limited = None, 0
        for day in range(days.max() + 1):
            today = days == day
            expected = target[today] if reference is None else np.clip(target[today], reference - 0.5,
                                                                         reference + 0.5)
            np.testing.assert_allclose(applied[today], expected, rtol=0, atol=1e-4, err_msg=f'{zone}, day {day}')
            limited += int((np.abs(applied[today] - target[today]) > 1e-4).sum())
            if (today & occupied).any():
                reference = applied[today & occupied].mean()
        assert limited > 0
        # On Tuesday, the setpoints are within 0.5 K of the mean of the occupied timesteps of Monday (6 to 18 h in
        # standard time, the 7 to 19 h of the schedule of the office with the daylight saving time of the model: 22.875
        # degC), not of its last timestep (25.75 degC)
        tuesday = applied[days == 1]
        assert tuesday.max() == pytest.approx(23.375, abs=1e-4) and tuesday.min() == pytest.approx(22.375, abs=1e-4)
