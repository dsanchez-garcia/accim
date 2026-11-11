"""Tests for the setpoints of the adaptive thermal heat balance (ATHB) in the backend of the Python API of EnergyPlus
(proposal A4 of accim 1.2.0, :mod:`accim.sim.comfort_hooks`).

The ATHB of pythermalcomfort (``pythermalcomfort.models.pmv_athb``, 4.8.1; Schweiker, 2022): met_adapted =
met − 0.234·trm/58.2, clo_adapted = 10^(−0.17168 − 0.000485·trm + 0.08176·met_adapted − 0.00527·trm·met_adapted), and
the ATHB_PMV of the thermal load of the PMV with them. The hook finds by bisection the operative temperatures whose
ATHB_PMV is the heating and cooling setpoints and gives them to the setpoint schedules of the ACCIS. The unit tests use
a fake controller; the last tests simulate an output IDF of AddAccis with EnergyPlus 25.1, through its Python API.
"""
import os
import pickle
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim import comfort_hooks as ch

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
ZONES = ['Block1_Zone1', 'Block1_Zone2']
CALLING_POINT = 'BEGINTIMESTEPBEFOREPREDICTOR'


def test_the_adapted_metabolic_rate_and_clothing():
    # The formulas of pythermalcomfort.models.pmv_athb (4.8.1), with trm = 18 °C and met = 1.1 (v03, A4, test 2)
    met_adapted = 1.1 - 0.234 * 18 / 58.2
    assert ch.athb_met(1.1, 18) == pytest.approx(met_adapted, abs=1e-15)
    assert ch.athb_clo(1.1, 18) == pytest.approx(
        10 ** (-0.17168 - 0.000485 * 18 + 0.08176 * met_adapted - 0.00527 * 18 * met_adapted), abs=1e-15)
    # Warmer running means: lower metabolic rate and less clothing
    assert ch.athb_met(1.1, 25) < ch.athb_met(1.1, 18) and ch.athb_clo(1.1, 25) < ch.athb_clo(1.1, 18)


def test_the_athb_of_pythermalcomfort():
    pmv_athb = pytest.importorskip('pythermalcomfort.models').pmv_athb
    for trm, met in ((10, 1.0), (18, 1.1), (26, 1.2)):
        athb = pmv_athb(tdb=25, tr=26, vr=0.1, rh=50, met=met, t_running_mean=trm).athb_pmv
        # The clothing of the behavioural adaptation of pythermalcomfort is that of athb_clo
        assert float(athb) == float(pmv_athb(tdb=25, tr=26, vr=0.1, rh=50, met=met, t_running_mean=trm,
                                             clo=ch.athb_clo(met, trm)).athb_pmv)
        assert ch.athb_pmv(25, 26, 0.1, 50, met, trm) == float(athb)
        assert ch.athb_pmv(25, 26, 0.1, 50, met, trm, clo=0.5) == float(
            pmv_athb(tdb=25, tr=26, vr=0.1, rh=50, met=met, t_running_mean=trm, clo=0.5).athb_pmv)


def test_the_bisection_brackets_the_setpoints():
    pytest.importorskip('pythermalcomfort')
    hook = ch.AthbSetpointHook(['Z'])
    for trm in (5, 12, 18, 24, 28):
        for humidity in (30, 50, 70):
            heating, cooling = hook.operative_temperatures(humidity, trm)
            assert 10 < heating < cooling < 30
            # The ATHB_PMV grows with the operative temperature, and the setpoint is the middle of an interval of
            # 0.1 K or less in which it crosses the setpoint of the ATHB
            for temperature, target in ((heating, -0.5), (cooling, 0.5)):
                below = ch.athb_pmv(temperature - 0.05, temperature - 0.05, 0.1, humidity, 1.1, trm)
                above = ch.athb_pmv(temperature + 0.05, temperature + 0.05, 0.1, humidity, 1.1, trm)
                assert below <= target <= above
    # The setpoints of the ATHB out of the range of the operative temperature give its limits
    wide = ch.AthbSetpointHook(['Z'], athb_cooling_setpoint=10, athb_heating_setpoint=-10)
    assert wide.operative_temperatures(50, 18) == (10.0, 30.0)
    narrow = ch.AthbSetpointHook(['Z'], temperature_range=(22.0, 24.0))
    assert narrow.operative_temperatures(50, 18) == (22.0, 24.0)


class _Controller:
    """A fake ErlController: get and set of the variables of a dictionary (in upper case, as Erl)."""

    def __init__(self, values, after_programs=()):
        self.values = {name.upper(): value for name, value in values.items()}
        self.after_programs = list(after_programs)

    def get(self, name, program=None):
        return self.values.get(name.upper())

    def set(self, name, value):
        self.values[name.upper()] = value


def _given(controller, zone):
    """The setpoints that a hook gave to the ACCIS of a zone (accim.sim.ems.hook_setpoints), or None."""
    if controller.get(f'HookSetpoints_{zone}') != 1:
        return None
    return controller.get(f'HookAHST_{zone}'), controller.get(f'HookACST_{zone}')


def test_the_hook_sets_the_setpoints_and_the_outputs():
    pytest.importorskip('pythermalcomfort')
    hook = ch.AthbSetpointHook(ZONES, athb_cooling_setpoint=0.7, athb_heating_setpoint=-0.7, met=1.2, air_speed=0.15)
    assert hook.runs_before_programs
    controller = _Controller({'RMOT': 21.0, 'ATHB_MAT_Block1_Zone1': 26.0, 'ATHB_MRT_Block1_Zone1': 27.0,
                              'ATHB_RH_Block1_Zone1': 55.0, 'ATHB_MAT_Block1_Zone2': 22.0,
                              'ATHB_MRT_Block1_Zone2': 21.5, 'ATHB_RH_Block1_Zone2': 40.0})
    # Only at the beginning of the timesteps, before the programs of the ACCIS
    hook(controller, 'BEGINNEWENVIRONMENT')
    assert _given(controller, 'Block1_Zone1') is None
    hook(controller, CALLING_POINT)
    for zone, (air, radiant, humidity) in {'Block1_Zone1': (26.0, 27.0, 55.0),
                                           'Block1_Zone2': (22.0, 21.5, 40.0)}.items():
        heating, cooling = hook.operative_temperatures(humidity, 21.0)
        # The setpoints go to the ACCIS (the program ApplyHookSetpoints_<zone>), not to the actuators
        assert _given(controller, zone) == (heating, cooling)
        assert controller.get(f'ACST_Act_{zone}') is None
        assert hook.setpoints[zone] == (heating, cooling)
        assert controller.get(f'ATHB_PMV_{zone}') == ch.athb_pmv(air, radiant, 0.15, humidity, 1.2, 21.0)
        assert controller.get(f'ATHB_clo_{zone}') == ch.athb_clo(1.2, 21.0)
        assert controller.get(f'ATHB_met_{zone}') == ch.athb_met(1.2, 21.0)
    # With a given clothing insulation, there is no behavioural adaptation
    fixed = ch.AthbSetpointHook(['Block1_Zone1'], clo=0.6)
    fixed(controller, CALLING_POINT)
    assert controller.get('ATHB_clo_Block1_Zone1') == 0.6
    # Without the values of the sensors, nothing is set
    empty = _Controller({'RMOT': 21.0})
    hook(empty, CALLING_POINT)
    assert empty.values == {'RMOT': 21.0}
    # After the programs, the ACCIS would not take its setpoints in the timestep
    late = _Controller({'RMOT': 21.0}, after_programs=[hook])
    with pytest.raises(RuntimeError, match='must run before the EMS programs'):
        hook(late, CALLING_POINT)


def test_the_hook_reports_the_setpoints_at_the_limits_of_their_range():
    pytest.importorskip('pythermalcomfort')
    # Up to 25 °C, the cooling setpoint of the ATHB (0.5) is out of the range in July in Seville
    hook = ch.AthbSetpointHook(ZONES, temperature_range=(10.0, 25.0))
    heating, cooling = hook.operative_temperatures(50.0, 24.0)
    assert cooling == 25.0 and hook.saturated(heating, cooling)
    assert not ch.AthbSetpointHook(ZONES).saturated(*ch.AthbSetpointHook(ZONES).operative_temperatures(50.0, 24.0))
    values = {'RMOT': 24.0, 'ZoneTimeStep': 1 / STEPS, 'WarmupFlag': 0.0}
    for zone in ZONES:
        values.update({f'ATHB_MAT_{zone}': 26.0, f'ATHB_MRT_{zone}': 26.5, f'ATHB_RH_{zone}': 50.0})
    controller = _Controller(dict(values))
    for _ in range(3):
        hook(controller, CALLING_POINT)
    # The output of each timestep, and the hours out of the warm-up days
    assert all(controller.get(f'ATHB_saturated_{zone}') == pytest.approx(1 / STEPS) for zone in ZONES)
    assert hook.saturated_hours == {zone: pytest.approx(3 / STEPS) for zone in ZONES}
    warmup = _Controller(dict(values, WarmupFlag=1.0))
    hook(warmup, CALLING_POINT)
    assert warmup.get('ATHB_saturated_Block1_Zone1') == pytest.approx(1 / STEPS)
    assert hook.saturated_hours['Block1_Zone1'] == pytest.approx(3 / STEPS)
    # A warning at the end of the simulation, and none without saturated setpoints
    with pytest.warns(UserWarning, match=r'The setpoints of the ATHB were at a limit of temperature_range '
                                         r'\(10.0, 25.0\) °C .* in Block1_Zone1: 0.50 h, Block1_Zone2: 0.50 h'):
        hook.finish()
    hook.prepare()
    assert hook.saturated_hours == {}
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        hook.finish()
        within = ch.AthbSetpointHook(ZONES)
        within(_Controller(dict(values)), CALLING_POINT)
        assert within.saturated_hours == {}
        within.finish()


class _Exchange:
    """The functions of the API of EnergyPlus that tell the kind of simulation and the warm-up days."""

    def __init__(self, kind, warmup):
        self.kind, self.warmup = kind, warmup

    def kind_of_sim(self, state):
        return self.kind

    def warmup_flag(self, state):
        return self.warmup


def test_the_saturated_hours_are_those_of_the_run_period_out_of_the_warm_up_days(monkeypatch):
    # Finding A7 of the self-audit of 2026-11-11: the controller updates the built-in variable WarmupFlag only for the
    # EMS programs that read it (none in the models of the ACCIS without the outdoor metric of the custom model or the
    # limiter of the drift), so the hook takes the warm-up days and the kind of simulation from the API of EnergyPlus:
    # neither the warm-up days nor the sizing periods (kind_of_sim 1, the design days) count
    from types import SimpleNamespace

    monkeypatch.setattr(ch, 'athb_pmv', lambda *arguments, **keywords: 0.0)
    hook = ch.AthbSetpointHook(ZONES, temperature_range=(10.0, 25.0))
    monkeypatch.setattr(hook, 'operative_temperatures', lambda humidity, t_running_mean: (20.0, 25.0))
    values = {'RMOT': 24.0, 'ZoneTimeStep': 1 / STEPS}
    for zone in ZONES:
        values.update({f'ATHB_MAT_{zone}': 26.0, f'ATHB_MRT_{zone}': 26.5, f'ATHB_RH_{zone}': 50.0})
    for kind, warmup, counted in ((3, True, 0), (1, False, 0), (1, True, 0), (2, False, 0), (3, False, 1)):
        controller = _Controller(dict(values))
        controller.api, controller.state = SimpleNamespace(exchange=_Exchange(kind, warmup)), object()
        assert controller.get('WarmupFlag') is None
        hook.prepare()
        hook(controller, CALLING_POINT)
        # The output of the timestep, in any case
        assert controller.get('ATHB_saturated_Block1_Zone1') == pytest.approx(1 / STEPS)
        assert hook.saturated_hours.get('Block1_Zone1', 0.0) == pytest.approx(counted / STEPS), (kind, warmup)


def test_the_hook_warns_out_of_the_ranges_of_the_pmv():
    # ISO 7730:2025, section 4: 0.8 to 4 met and a relative air speed up to 1 m/s
    from accim.constants import PMV_MET_RANGE

    assert PMV_MET_RANGE == (0.8, 4.0)
    for met in (0.5, 4.5):
        with pytest.warns(UserWarning, match=f'met is {met} met, out of the range of 0.8 to 4.0 met'):
            ch.AthbSetpointHook(ZONES, met=met)
    with pytest.warns(UserWarning, match='air_speed is 1.2 m/s, above the relative air speed of 1.0 m/s'):
        ch.AthbSetpointHook(ZONES, air_speed=1.2)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        for met, air_speed in ((0.8, 0.0), (4.0, 1.0), (1.1, 0.1)):
            ch.AthbSetpointHook(ZONES, met=met, air_speed=air_speed)
    # 1 met is 58.2 W/m2 times the body surface area of 1.8 m2 of EnergyPlus, about 104.8 W/person
    assert ch.MET_ACTIVITY_LEVEL == pytest.approx(104.76)


def test_the_arguments_of_the_hook_are_checked():
    for arguments, message in ((dict(zones=[]), 'zones must name at least one zone'),
                               (dict(athb_heating_setpoint=0.5), 'must be lower than athb_cooling_setpoint'),
                               (dict(met='1.1'), 'met must be a number'),
                               (dict(met=0), 'met must be greater than 0'),
                               (dict(air_speed=-0.1), 'air_speed must be between 0.0'),
                               (dict(clo='dynamic'), 'clo must be a number'),
                               (dict(tolerance_k=0), 'tolerance_k must be greater than 0'),
                               (dict(max_iterations=0), 'max_iterations must be a positive integer'),
                               (dict(temperature_range=(30, 10)), 'temperature_range must be')):
        values = dict(zones=['Z'])
        values.update(arguments)
        with pytest.raises(ValueError, match=message):
            ch.AthbSetpointHook(**values)


def test_the_hook_can_be_sent_to_the_processes_of_the_simulations():
    hook = ch.AthbSetpointHook(ZONES, athb_cooling_setpoint=0.4, clo=0.7)
    copy = pickle.loads(pickle.dumps(hook))
    assert (copy.zones, copy.athb_cooling_setpoint, copy.clo) == (ZONES, 0.4, 0.7)


def test_without_pythermalcomfort_the_athb_says_how_to_install_it(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, 'pythermalcomfort', None)
    monkeypatch.setitem(sys.modules, 'pythermalcomfort.models', None)
    with pytest.raises(ImportError, match=r'pip install accim\[comfort\]'):
        ch.athb_pmv(25, 25, 0.1, 50, 1.1, 18)


# The model ---------------------------------------------------------------------------------------------------------

def _model(tmp_path, script_type='vrf_ac'):
    from accim.sim.accis import add_accis_to_idf, load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    idf = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type=script_type, supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    return idf


@needs_idd
def test_apply_athb_setpoints_prepares_the_model(tmp_path):
    idf = _model(tmp_path)
    hook = ch.apply_athb_setpoints(idf, athb_cooling_setpoint=0.4, met=1.2, output_frequencies=['timestep', 'hourly'])
    # The frequencies of the outputs of the model by default (task H4 of the review of 1.2.0): hourly, those of _model
    (tmp_path / 'default').mkdir()
    default = _model(tmp_path / 'default')
    ch.apply_athb_setpoints(default)
    for name in ch.zone_outputs('Block1_Zone1'):
        assert sorted(o.Reporting_Frequency for o in default.idfobjects['Output:Variable']
                      if o.Variable_Name == name) == ['Hourly']
    assert isinstance(hook, ch.AthbSetpointHook)
    assert sorted(hook.zones) == ZONES and (hook.athb_cooling_setpoint, hook.met) == (0.4, 1.2)
    sensors = {s.Name: s for s in idf.idfobjects['EnergyManagementSystem:Sensor']}
    declared = {str(name) for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
                for name in g.fieldvalues[1:]}
    ems_outputs = {o.Name: o for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    requested = {(o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']}
    for zone in ZONES:
        key = sensors[f'{zone}_OpT'].OutputVariable_or_OutputMeter_Index_Key_Name
        for prefix, variable in (('ATHB_MAT', 'Zone Mean Air Temperature'),
                                 ('ATHB_MRT', 'Zone Mean Radiant Temperature'),
                                 ('ATHB_RH', 'Zone Air Relative Humidity')):
            sensor = sensors[f'{prefix}_{zone}']
            assert (sensor.OutputVariable_or_OutputMeter_Index_Key_Name,
                    sensor.OutputVariable_or_OutputMeter_Name) == (key, variable)
        assert ch.zone_outputs(zone) == [f'ATHB_PMV_{zone}', f'ATHB_clo_{zone}', f'ATHB_met_{zone}',
                                         f'ATHB_saturated_{zone}']
        for name, units, kind in zip(ch.zone_outputs(zone), ('', 'clo', 'met', 'H'),
                                     ('Averaged', 'Averaged', 'Averaged', 'Summed')):
            assert name in declared
            output = ems_outputs[name]
            assert (output.EMS_Variable_Name, output.Type_of_Data_in_Variable, output.Update_Frequency,
                    output.Units) == (name, kind, 'ZoneTimestep', units)
            assert {(name, 'Timestep'), (name, 'Hourly')} <= requested
    with pytest.raises(ValueError, match='already has the setpoints of the ATHB'):
        ch.apply_athb_setpoints(idf)
    # The SET would set the same thermostats
    with pytest.raises(ValueError, match='already has the setpoints of the ATHB or of the SET'):
        ch.apply_set_setpoints(idf, set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5, air_speed=0.1)


@needs_idd
def test_apply_athb_setpoints_needs_the_accis_with_full_air_conditioning(tmp_path):
    from accim.sim.accis import load_idf

    with pytest.raises(ValueError, match='need full air-conditioning'):
        ch.apply_athb_setpoints(_model(tmp_path, script_type='vrf_mm'))
    shutil.copy(SAMPLE_IDF, tmp_path / 'input.idf')
    with pytest.raises(ValueError, match='need the ACCIS of accim 1.0.0 or later'):
        ch.apply_athb_setpoints(load_idf(tmp_path / 'input.idf'))


def test_run_ep_runs_the_hooks_with_the_api_backend_only(tmp_path, monkeypatch):
    from accim.run import run_ep

    monkeypatch.chdir(tmp_path)
    with pytest.raises(NotImplementedError, match=r"hooks need run_ep\(backend='api'\)"):
        run_ep(only_accim_idfs=False, confirm=True, energyplus_version='auto', backend='ems',
               hooks=[ch.AthbSetpointHook(['Z'])])


def test_run_ep_runs_the_hooks_of_the_setpoints_before_the_programs(tmp_path, monkeypatch):
    import accim.sim.energyplus_api as energyplus_api
    from accim.run import run_ep

    calls = {}

    def fake_run_simulations(jobs, processes=2, **kwargs):
        calls.update(kwargs)
        return []

    def other_hook(controller, calling_point):
        return None

    monkeypatch.setattr(energyplus_api, 'run_simulations', fake_run_simulations)
    monkeypatch.chdir(tmp_path)
    hook = ch.AthbSetpointHook(['Z'])
    run_ep(only_accim_idfs=False, confirm=True, backend='api', hooks=[hook, other_hook])
    assert calls == {'before_programs': [hook], 'after_programs': [other_hook]}


def _program_lines(idf, name):
    program = idf.getobject('EnergyManagementSystem:Program', name)
    return None if program is None else [str(value).strip() for value in program.fieldvalues[2:]]


@needs_idd
def test_the_hooks_give_their_setpoints_to_the_accis_right_after_setast(tmp_path):
    from accim.sim.accis import modify_accis
    from accim.sim.ems import hook_setpoints as hs

    # The minimum and maximum of the setpoints given before the hook, and after it
    before = _model(tmp_path)
    modify_accis(before, heating_setpoint_minimum=21.0, cooling_setpoint_maximum=26.0)
    ch.apply_athb_setpoints(before)
    (tmp_path / 'after').mkdir()
    after = _model(tmp_path / 'after')
    ch.apply_set_setpoints(after, set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5, air_speed=0.1)
    modify_accis(after, heating_setpoint_minimum=21.0, cooling_setpoint_maximum=26.0)
    for idf in (before, after):
        assert sorted(hs.hook_zones(idf)) == ZONES
        declared = {str(name).upper() for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
                    for name in g.fieldvalues[1:]}
        for zone in ZONES:
            assert _program_lines(idf, f'ApplyHookSetpoints_{zone}') == hs.program_lines(zone)
            assert {name.upper() for name in hs.zone_variables(zone)} <= declared
            # The setpoints of the hook replace those of SetAST, and the minimum and maximum bound them, with and
            # without the tolerance (after SetASTnoTol, finding B5-1 of the review of 1.2.0)
            run = _program_lines(idf, f'RunACCIS_{zone}')
            position = run.index('run SetAST')
            assert run[position + 1:position + 4] == [f'run ApplyHookSetpoints_{zone}', 'run SetASTnoTol',
                                                      f'run ApplySetpointLimits_{zone}']
        assert sorted(_program_lines(idf, 'InitHookSetpoints')) == sorted(hs.init_program_lines(ZONES))
        manager = idf.getobject('EnergyManagementSystem:ProgramCallingManager', 'InitHookSetpoints')
        assert (manager.EnergyPlus_Model_Calling_Point, manager.Program_Name_1) == ('BeginNewEnvironment',
                                                                                     'InitHookSetpoints')
    # Written again, the objects are not repeated
    counts = {kind: len(before.idfobjects[kind]) for kind in ('EnergyManagementSystem:Program',
                                                             'EnergyManagementSystem:GlobalVariable',
                                                             'EnergyManagementSystem:ProgramCallingManager')}
    hs.set_hook_setpoints_code(before, ZONES)
    assert {kind: len(before.idfobjects[kind]) for kind in counts} == counts
    assert _program_lines(before, f'RunACCIS_{ZONES[0]}').count(f'run ApplyHookSetpoints_{ZONES[0]}') == 1


def _hook_erl(**arguments):
    """The programs of the ACCIS of one zone, Zone1 (INT EN16798, category II, comfort mode 3, a tolerance of the
    setpoints of 0.1 and full air-conditioning, with the long-term discomfort of C2), with the program that gives the
    setpoints of a hook to the zone and, with a minimum or a maximum, the program of the setpoint limits after
    SetASTnoTol, at the beginning of an environment; compiled by the Erl interpreter."""
    from types import SimpleNamespace

    from accim.sim.ems import hook_setpoints as hs, long_term_discomfort as ltd, setpoint_limits as sl
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
    programs['CountLongTermDiscomfort_Zone1'] = ltd.zone_lines('Zone1')
    run = list(programs['RunACCIS_Zone1'])
    run.insert(run.index('run SetAST') + 1, 'run ApplyHookSetpoints_Zone1')
    minimum, maximum = (values.get(name) is not None for name in sl.INPUTS)
    if minimum or maximum:
        programs['ApplySetpointLimits_Zone1'] = sl.limit_program_lines(minimum, maximum)
        run.insert(run.index('run SetASTnoTol') + 1, 'run ApplySetpointLimits_Zone1')
    run.insert(run.index('run CountHoursNoApp_Zone1') + 1, 'run CountLongTermDiscomfort_Zone1')
    programs['RunACCIS_Zone1'] = run
    erl = ErlProgramSet(programs, global_variables=set().union(*variables_in_programs(programs).values()))
    erl.strict = True
    erl.run('InitASTvariables')
    erl.run('InitHookSetpoints')
    return erl


def _hook_timestep(erl, setpoints=None, operative=26.5, occupants=1.0, outdoor=20.0):
    """A timestep of the ACCIS of Zone1 in which a hook gives it some setpoints (heating, cooling), or none."""
    for name, value in dict(RMOT=outdoor, PMOT=outdoor, DayOfYear=180.0, CurrentTime=12.0, ZoneTimeStep=0.25,
                            Zone1_OpT=operative, Occ_count_Zone1=occupants).items():
        erl.set(name, value)
    if setpoints is not None:
        erl.set('HookAHST_Zone1', setpoints[0])
        erl.set('HookACST_Zone1', setpoints[1])
        erl.set('HookSetpoints_Zone1', 1.0)
    erl.run('RunACCIS_Zone1')
    return {name: erl.get(name) for name in (
        'AHST_Act_Zone1', 'ACST_Act_Zone1', 'AHSTnoTol_Zone1', 'ACSTnoTol_Zone1', 'roundedAHST_Zone1',
        'roundedACST_Zone1', 'ComfHoursNoApp_Zone1', 'OccDiscomfHoursNoApp_Zone1', 'DiscomfAppHotHours_Zone1',
        'HoursAboveUpperLimit_Zone1', 'DegreeHoursAboveUpperLimit_Zone1', 'HookSetpoints_Zone1')}


def test_the_accis_follows_the_setpoints_of_the_hook():
    erl = _hook_erl()
    # Without the hook: the setpoints of INT EN16798, category II (28.4 and 21.4 °C without the tolerance with a
    # running mean of 20 °C), within which 26.5 °C is comfortable
    adaptive = _hook_timestep(erl)
    assert (adaptive['ACSTnoTol_Zone1'], adaptive['AHSTnoTol_Zone1']) == pytest.approx((28.4, 21.4))
    assert adaptive['ACST_Act_Zone1'] == pytest.approx(28.3) and adaptive['ComfHoursNoApp_Zone1'] == 0.25
    # With the setpoints 22 and 26 °C of a hook: the thermostats get them with the tolerance, the setpoints without it
    # are those of the hook, and the hour counters (also those of C2) follow them
    hooked = _hook_timestep(erl, setpoints=(22.0, 26.0))
    assert (hooked['AHST_Act_Zone1'], hooked['ACST_Act_Zone1']) == pytest.approx((22.1, 25.9))
    assert (hooked['AHSTnoTol_Zone1'], hooked['ACSTnoTol_Zone1']) == pytest.approx((22.0, 26.0))
    # Rounded as the setpoints of SetAST (those with the tolerance; the cooling one downwards, strictly)
    assert (hooked['roundedAHST_Zone1'], hooked['roundedACST_Zone1']) == pytest.approx((22.1, 25.8999))
    assert hooked['ComfHoursNoApp_Zone1'] == 0 and hooked['OccDiscomfHoursNoApp_Zone1'] == 0.25
    assert hooked['DiscomfAppHotHours_Zone1'] == 0.25
    assert hooked['HoursAboveUpperLimit_Zone1'] == 0.25
    assert hooked['DegreeHoursAboveUpperLimit_Zone1'] == pytest.approx(0.5 * 0.25)
    # The flag is used once: in the next timestep without the hook, the setpoints are those of the ACCIS again
    assert hooked['HookSetpoints_Zone1'] == 0
    assert _hook_timestep(erl) == adaptive


def test_the_minimum_and_maximum_bound_the_setpoints_of_the_hook():
    erl = _hook_erl(heating_setpoint_minimum=23.0, cooling_setpoint_maximum=25.0)
    hooked = _hook_timestep(erl, setpoints=(22.0, 26.0))
    # Exactly the minimum and the maximum (finding B5-2), with and without the tolerance (finding B5-1)
    assert (hooked['AHST_Act_Zone1'], hooked['ACST_Act_Zone1']) == (23.0, 25.0)
    assert (hooked['AHSTnoTol_Zone1'], hooked['ACSTnoTol_Zone1']) == (23.0, 25.0)


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')
STEPS = 6


def _athb_model(folder, monkeypatch, end_day=21, **arguments):
    """The output IDF of AddAccis of the sample model (INT EN16798, category II, comfort mode 3, full
    air-conditioning) for 15-21 July (or until ``end_day``), with the setpoints of the ATHB and the outputs of the zones
    at timestep frequency; return its path and the hook."""
    from accim.sim.accis import AddAccis, load_idf

    folder.mkdir(parents=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    model = load_idf(folder / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 7, 15
    run_period.End_Month, run_period.End_Day_of_Month = 7, end_day
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
    hook = ch.apply_athb_setpoints(idf, output_frequencies=['timestep'], **arguments)
    for variable in ('Zone Air Relative Humidity', 'Zone Mean Air Temperature', 'Zone Mean Radiant Temperature',
                     'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature'):
        idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=variable, Reporting_Frequency='Timestep')
    idf.saveas(str(folder / 'athb.idf'))
    path.unlink()
    (folder / 'TestModel.idf').unlink()
    return folder / 'athb.idf', hook


@needs_energyplus
def test_the_athb_setpoints_in_energyplus(tmp_path, monkeypatch):
    from accim.run import run_ep

    pytest.importorskip('pythermalcomfort')
    model, hook = _athb_model(tmp_path / 'athb', monkeypatch)
    shutil.copy(EPW, model.parent / 'Seville.epw')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        [result] = run_ep(only_accim_idfs=False, confirm=True, processes=1, backend='api', hooks=[hook])
    assert result.success, result.error
    results = pd.read_csv(model.parent / 'athb[Seville.csv')
    assert len(results) == 7 * 24 * STEPS
    columns = list(results.columns)

    def column(start):
        return results[next(c for c in columns if c.upper().startswith(start.upper()))]

    # The running mean that the sensor reads at the beginning of a timestep is that of the previous one (that of the
    # previous day at the first timestep of a day), and is 0 at the first timestep of the run period (as for the
    # ACCIS), which is not checked
    running_mean = column('PEOPLE BLOCK1:ZONE1:Zone Thermal Comfort CEN 15251 Adaptive Model Running Average').shift(1)
    for zone in ZONES:
        key = zone.replace('_', ':').upper()
        humidity = column(f'{key}:Zone Air Relative Humidity').shift(1)
        heating = column(f'AHST_SCH_{zone}:Schedule Value')
        cooling = column(f'ACST_SCH_{zone}:Schedule Value')
        expected = np.array([hook.operative_temperatures(humidity[t], running_mean[t]) for t in range(1, len(results))])
        # The setpoints without the tolerance are those of the bisection with the sensors of the zone (to its
        # tolerance), and the thermostats get them with the tolerance of the setpoints of the ACCIS (0.1 K)
        no_tolerance = np.column_stack([
            column(f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy(),
            column(f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()])
        assert np.abs(no_tolerance - expected).max() <= hook.tolerance_k
        np.testing.assert_allclose(heating.iloc[1:].to_numpy(), no_tolerance[:, 0] + 0.1, atol=1e-4)
        np.testing.assert_allclose(cooling.iloc[1:].to_numpy(), no_tolerance[:, 1] - 0.1, atol=1e-4)
        # The adapted clothing and metabolic rate of the running mean
        clo = column(f'EMS:ATHB_clo_{zone}').iloc[1:].to_numpy()
        met = column(f'EMS:ATHB_met_{zone}').iloc[1:].to_numpy()
        np.testing.assert_allclose(clo, [ch.athb_clo(1.1, value) for value in running_mean.iloc[1:]], atol=1e-5)
        np.testing.assert_allclose(met, [ch.athb_met(1.1, value) for value in running_mean.iloc[1:]], atol=1e-5)
        # The ATHB setpoints replace the adaptive setpoints of the ACCIS (category II of EN 16798-1) in its outputs
        adaptive = 0.33 * running_mean + 18.8 + 3
        reported = column(f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [')
        assert (np.abs(reported - adaptive).iloc[1:] > 0.1).mean() > 0.9
        pmv = column(f'EMS:ATHB_PMV_{zone}')
        assert pmv.iloc[1:].between(-3, 3).all()
        # The hour counters of the ACCIS follow the setpoints of the ATHB: occupied and comfortable if the operative
        # temperature of the previous timestep (that which the EMS reads) is within the setpoints without the
        # tolerance (the rows within 1e-3 K of a setpoint are not checked: the CSV has 6 significant digits)
        operative = column(f'{key}:Zone Operative Temperature').shift(1).iloc[1:].to_numpy()
        occupied = column(f'EMS:Occupied Hours_{zone} [').iloc[1:].to_numpy() > 0
        comfortable = column(f'EMS:Occupied Comfortable Hours_No Applicability_{zone} [').iloc[1:].to_numpy() > 0
        within = (operative <= no_tolerance[:, 1]) & (operative >= no_tolerance[:, 0])
        clear = np.minimum(np.abs(operative - no_tolerance[:, 0]), np.abs(operative - no_tolerance[:, 1])) > 1e-3
        assert occupied.any() and (comfortable[clear] == (within & occupied)[clear]).all()

        # The ATHB_PMV of the zone is that of its mean air and radiant temperatures and relative humidity of the
        # previous timestep: the sensors read their last values, and the outputs are the means of the system timesteps
        # of each timestep, so they differ by up to 0.02 in this week (task H4 of the review of 1.2.0, section 3.4)
        air = column(f'{key}:Zone Mean Air Temperature').to_numpy()
        radiant = column(f'{key}:Zone Mean Radiant Temperature').to_numpy()
        humid = column(f'{key}:Zone Air Relative Humidity').to_numpy()
        previous = np.asarray(ch.athb_pmv(air[:-1], radiant[:-1], hook.air_speed, humid[:-1], hook.met,
                                          running_mean.to_numpy()[1:]), dtype=float)
        difference = np.abs(pmv.to_numpy()[1:] - previous)[1:]
        assert np.median(difference) <= 0.01 and difference.max() <= 0.03
        # The scientific claim, bounded: in the occupied timesteps with the cooling coil on in the previous timestep,
        # the ATHB_PMV is at most 0.25 above the cooling setpoint of the ATHB in at least 95 % of them (all, in this
        # week: at most 0.68 with the setpoint 0.5)
        cooling_on = column(f'{key} VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate').to_numpy() > 0
        occupied_hours = column(f'EMS:Occupied Hours_{zone} [').to_numpy() > 0
        selected = np.zeros(len(results), dtype=bool)
        selected[2:] = occupied_hours[1:-1] & cooling_on[1:-1]
        assert selected.sum() > 100
        assert np.mean(pmv.to_numpy()[selected] <= hook.athb_cooling_setpoint + 0.25) >= 0.95
        # No setpoint at the limits of temperature_range (10 to 30 °C): the cooling setpoints were 27.4 to 28.4 °C
        assert (column(f'EMS:ATHB_saturated_{zone}') == 0).all()


@needs_energyplus
def test_the_saturated_setpoints_of_the_athb_in_energyplus(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations

    pytest.importorskip('pythermalcomfort')
    # Up to 27.5 °C, the cooling setpoints of the ATHB of these days (27.4 to 28.4 °C) are often out of the range
    model, hook = _athb_model(tmp_path / 'model', monkeypatch, end_day=16, temperature_range=(10.0, 27.5))
    [result] = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                               processes=1, before_programs=[hook])
    assert result.success, result.error
    results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    for zone in ZONES:
        saturated = results[f'EMS:ATHB_saturated_{zone} [H](TimeStep)']
        cooling = results[f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [C](TimeStep)']
        heating = results[f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone} [C](TimeStep)']
        at_limit = (cooling == 27.5) | (heating == 10.0)
        # The hours of the timesteps whose setpoints are at a limit (the first timestep, with trm = 0, too)
        assert 0 < at_limit.sum() < len(results)
        np.testing.assert_allclose(saturated.to_numpy(), np.where(at_limit, 1 / STEPS, 0.0), atol=1e-9)


class _RunPeriodProbe:
    """A hook that records, at the beginning of each timestep, whether the hooks count its hours
    (``comfort_hooks._in_run_period``) and what the API of EnergyPlus says, and writes them in a JSON file at the end
    of the simulation (which runs in another process)."""

    runs_before_programs = True

    def __init__(self, path):
        self.path, self.records = str(path), []

    def __call__(self, controller, calling_point):
        if calling_point == CALLING_POINT:
            exchange = controller.api.exchange
            self.records.append([ch._in_run_period(controller), exchange.kind_of_sim(controller.state),
                                 bool(exchange.warmup_flag(controller.state))])

    def finish(self):
        import json

        Path(self.path).write_text(json.dumps(self.records), encoding='utf-8')


@needs_energyplus
def test_the_hooks_count_the_hours_of_the_run_period_only(tmp_path, monkeypatch):
    # Finding A7 of the self-audit of 2026-11-11, with the controller of the API: the timesteps of the run period of
    # the weather file out of its warm-up days, and not those of the design days of the sizing nor of the warm-up days
    import json

    from accim.sim.energyplus_api import run_simulations

    model, _ = _athb_model(tmp_path / 'model', monkeypatch, end_day=16)
    probe = _RunPeriodProbe(tmp_path / 'records.json')
    [result] = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                               processes=1, before_programs=[probe])
    assert result.success, result.error
    records = json.loads((tmp_path / 'records.json').read_text(encoding='utf-8'))
    counted = [record for record in records if record[0]]
    # Two days of six timesteps per hour
    assert len(counted) == 2 * 24 * STEPS
    assert all(kind == 3 and not warmup for _, kind, warmup in counted)
    # The design days of the sizing (out of their warm-up days too) and the warm-up days are left out
    assert any(kind != 3 and not warmup for _, kind, warmup in records)
    assert any(kind == 3 and warmup for _, kind, warmup in records)


@needs_energyplus
def test_without_the_hook_both_backends_give_the_same_results(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations

    model, _ = _athb_model(tmp_path / 'model', monkeypatch)
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
    # Without the hook, nothing sets the outputs of the ATHB
    assert (ems_results['EMS:ATHB_PMV_Block1_Zone1 [](TimeStep)'] == 0).all()


# The standard effective temperature (SET), proposal A6 -------------------------------------------------------------

def test_the_standard_effective_temperature_of_pythermalcomfort():
    set_tmp = pytest.importorskip('pythermalcomfort.models').set_tmp
    for air, radiant, speed, humidity, met, clo in ((25, 25, 0.1, 50, 1.1, 0.5), (22, 24, 0.3, 40, 1.2, 1.0),
                                                     (28, 27, 0.8, 60, 1.0, 0.4)):
        expected = float(set_tmp(tdb=air, tr=radiant, v=speed, rh=humidity, met=met, clo=clo, limit_inputs=False,
                                 round_output=False).set)
        assert ch.standard_effective_temperature(air, radiant, speed, humidity, met, clo) == expected
        # Rounded to one decimal, it is that of pythermalcomfort with its limits of the inputs
        assert round(expected, 1) == pytest.approx(float(set_tmp(tdb=air, tr=radiant, v=speed, rh=humidity, met=met,
                                                                 clo=clo).set))
    sitting = ch.standard_effective_temperature(25, 25, 0.1, 50, 1.1, 0.5, position='sitting')
    assert sitting == float(set_tmp(tdb=25, tr=25, v=0.1, rh=50, met=1.1, clo=0.5, position='sitting',
                                    limit_inputs=False, round_output=False).set)


def test_the_bisection_of_the_set_brackets_its_setpoints():
    pytest.importorskip('pythermalcomfort')
    hook = ch.SetSetpointHook(['Z'], set_cooling_setpoint=27.0, set_heating_setpoint=21.0, met=1.1, clo=0.5,
                              air_speed=0.1)
    for humidity in (30, 50, 70):
        heating, cooling = hook.operative_temperatures(humidity)
        assert 10 < heating < cooling < 40
        # The SET grows with the operative temperature, and the setpoint is the middle of an interval of 0.1 K or less
        # in which it crosses the setpoint of the SET
        for temperature, target in ((heating, 21.0), (cooling, 27.0)):
            below = hook.zone_set(temperature - 0.05, temperature - 0.05, humidity)
            above = hook.zone_set(temperature + 0.05, temperature + 0.05, humidity)
            assert below <= target <= above
    wide = ch.SetSetpointHook(['Z'], set_cooling_setpoint=60, set_heating_setpoint=-10, met=1.1, clo=0.5,
                              air_speed=0.1)
    assert wide.operative_temperatures(50) == (10.0, 40.0)


def test_the_set_hook_sets_the_setpoints_of_its_table():
    pytest.importorskip('pythermalcomfort')
    hook = ch.SetSetpointHook(ZONES, set_cooling_setpoint=26.5, set_heating_setpoint=20.5, met=1.2, clo=0.7,
                              air_speed=0.2, position='sitting')
    # The table: the setpoints of each relative humidity from 0 to 100 %, and their linear interpolation
    assert len(hook.table) == 101
    assert hook.setpoints_of_humidity(40) == hook.operative_temperatures(40)
    middle = hook.setpoints_of_humidity(40.5)
    assert middle == pytest.approx(tuple((a + b) / 2 for a, b in zip(hook.table[40], hook.table[41])))
    assert all(abs(a - b) <= hook.tolerance_k for a, b in zip(middle, hook.operative_temperatures(40.5)))
    assert hook.setpoints_of_humidity(120) == hook.setpoints_of_humidity(100)
    controller = _Controller({'SET_RH_Block1_Zone1': 55.0, 'SET_RH_Block1_Zone2': 35.5})
    hook(controller, 'ENDOFZONETIMESTEPBEFOREZONEREPORTING')
    assert _given(controller, 'Block1_Zone1') is None
    hook(controller, CALLING_POINT)
    for zone, humidity in {'Block1_Zone1': 55.0, 'Block1_Zone2': 35.5}.items():
        heating, cooling = hook.setpoints_of_humidity(humidity)
        assert _given(controller, zone) == (heating, cooling)
        assert hook.setpoints[zone] == (heating, cooling)
    assert hook.runs_before_programs
    with pytest.raises(RuntimeError, match='must run before the EMS programs'):
        hook(_Controller({'SET_RH_Block1_Zone1': 55.0}, after_programs=[hook]), CALLING_POINT)
    copy = pickle.loads(pickle.dumps(hook))
    assert copy.position == 'sitting' and copy.table == hook.table


def test_the_arguments_of_the_set_hook_are_checked():
    values = dict(zones=['Z'], set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5, air_speed=0.1)
    for arguments, message in ((dict(set_heating_setpoint=27), 'must be lower than set_cooling_setpoint'),
                               (dict(met=-1), 'met must be between 0.0'),
                               (dict(clo='0.5'), 'clo must be a number'),
                               (dict(position='lying'), "position must be 'standing', 'sitting' or None"),
                               (dict(tolerance_k=-1), 'tolerance_k must be between 0.0'),
                               (dict(method='newton'), "method must be one of \\['table', 'bisection'\\]")):
        with pytest.raises(ValueError, match=message):
            ch.SetSetpointHook(**{**values, **arguments})
    # Out of the limits of the inputs of pythermalcomfort, it warns
    for arguments in (dict(met=0.8), dict(clo=2.0), dict(air_speed=2.5)):
        with pytest.warns(UserWarning, match='out of the range of the SET of pythermalcomfort'):
            ch.SetSetpointHook(**{**values, **arguments})
    # The metabolic rate, clothing insulation and air speed of the People objects (None) and the mean radiant
    # temperature of the zones need the bisection (task F1): the table depends on the relative humidity only
    for arguments in (dict(met=None), dict(clo=None), dict(air_speed=None), dict(tr_mode='zone')):
        with pytest.raises(ValueError, match="method='table' needs met, clo and air_speed"):
            ch.SetSetpointHook(**{**values, **arguments})
    with pytest.raises(ValueError, match="method='table' needs met, clo and air_speed"):
        ch.SetSetpointHook(['Z'], set_cooling_setpoint=27, set_heating_setpoint=21)
    with pytest.raises(ValueError, match="tr_mode must be one of \\['equal_air', 'zone'\\]"):
        ch.SetSetpointHook(**{**values, 'method': 'bisection', 'tr_mode': 'surfaces'})


def test_the_posture_of_the_set_hook_by_default():
    pytest.importorskip('pythermalcomfort')
    values = dict(zones=['Z'], set_cooling_setpoint=27, set_heating_setpoint=21, clo=0.5, air_speed=0.1,
                  method='bisection')
    # Sitting for sedentary occupants (1.2 met or less), standing above it
    assert [ch.SetSetpointHook(met=met, **values).position for met in (1.0, 1.2, 1.3)] == ['sitting', 'sitting',
                                                                                         'standing']
    assert ch.SetSetpointHook(met=1.1, position='standing', **values).position == 'standing'


def test_the_set_hook_by_bisection(monkeypatch):
    pytest.importorskip('pythermalcomfort')
    hook = ch.SetSetpointHook(ZONES, set_cooling_setpoint=27.0, set_heating_setpoint=21.0, met=1.1, clo=0.5,
                              air_speed=0.1, method='bisection')
    # No table: the setpoints of each humidity are those of the bisection
    assert hook.table is None and hook.position == 'sitting'
    assert hook.setpoints_of_humidity(47.3) == hook.operative_temperatures(47.3)
    controller = _Controller({'SET_RH_Block1_Zone1': 55.0, 'SET_MAT_Block1_Zone1': 25.5, 'SET_MRT_Block1_Zone1': 26.5,
                              'SET_RH_Block1_Zone2': 35.5})
    hook(controller, CALLING_POINT)
    assert _given(controller, 'Block1_Zone1') == hook.operative_temperatures(55.0)
    assert _given(controller, 'Block1_Zone2') == hook.operative_temperatures(35.5)
    # The SET of each zone, from its mean air and radiant temperatures and humidity (not without them)
    assert controller.get('SET_Block1_Zone1') == ch.standard_effective_temperature(25.5, 26.5, 0.1, 55.0, 1.1, 0.5,
                                                                                    'sitting')
    assert controller.get('SET_Block1_Zone2') is None
    # prepare() calls the SET with numbers and with arrays of two values, as the bisection does (also with the mean
    # radiant temperature of the zone, a number, task F1); not with the table
    table = ch.SetSetpointHook(['Z'], set_cooling_setpoint=27.0, set_heating_setpoint=21.0, met=1.1, clo=0.5,
                               air_speed=0.1)
    calls = []
    monkeypatch.setattr(ch, 'standard_effective_temperature', lambda *args: calls.append(np.shape(args[0])))
    hook.prepare()
    assert calls == [(), (2,), (2,)]
    calls.clear()
    table.prepare()
    assert calls == []
    copy = pickle.loads(pickle.dumps(hook))
    assert copy.method == 'bisection' and copy.table is None


def test_run_simulation_prepares_the_hooks():
    from accim.sim.energyplus_api import prepare_hooks

    prepared = []

    class Prepared:
        def prepare(self):
            prepared.append(self)

        def __call__(self, controller, calling_point):
            return None

    hooks = [Prepared(), lambda controller, calling_point: None, Prepared()]
    prepare_hooks(hooks)
    assert prepared == [hooks[0], hooks[2]]


def test_the_set_of_the_results_of_a_simulation(tmp_path):
    pytest.importorskip('pythermalcomfort')
    hook = ch.SetSetpointHook(ZONES, set_cooling_setpoint=27.0, set_heating_setpoint=21.0, met=1.2, clo=0.6,
                              air_speed=0.2, method='bisection')
    hook.keys = {'Block1_Zone1': 'Block1:Zone1', 'Block1_Zone2': 'Block1:Zone2'}
    results = pd.DataFrame({
        'Date/Time': [' 07/15  01:00:00', ' 07/15  02:00:00', ' 07/15  03:00:00'],
        'BLOCK1:ZONE1:Zone Mean Air Temperature [C](Hourly)': [24.0, 25.0, np.nan],
        'BLOCK1:ZONE1:Zone Mean Radiant Temperature [C](Hourly)': [25.0, 26.5, 26.0],
        'BLOCK1:ZONE1:Zone Air Relative Humidity [%](Hourly)': [50.0, 60.0, 55.0],
        'BLOCK1:ZONE2:Zone Mean Air Temperature [C](Hourly)': [22.0, 23.0, 24.0],
        'BLOCK1:ZONE2:Zone Mean Radiant Temperature [C](Hourly)': [21.0, 22.5, 23.0],
        'BLOCK1:ZONE2:Zone Air Relative Humidity [%](Hourly)': [40.0, 45.0, 50.0],
    })
    found = ch.set_of_results(results, hook)
    assert list(found.columns) == ['SET_Block1_Zone1', 'SET_Block1_Zone2']
    for zone, number in (('Block1_Zone1', 1), ('Block1_Zone2', 2)):
        key = f'BLOCK1:ZONE{number}'
        for row in range(3):
            air = results[f'{key}:Zone Mean Air Temperature [C](Hourly)'][row]
            if np.isnan(air):
                assert np.isnan(found[f'SET_{zone}'][row])
                continue
            expected = ch.standard_effective_temperature(
                air, results[f'{key}:Zone Mean Radiant Temperature [C](Hourly)'][row], 0.2,
                results[f'{key}:Zone Air Relative Humidity [%](Hourly)'][row], 1.2, 0.6, 'sitting')
            assert found[f'SET_{zone}'][row] == pytest.approx(expected, abs=1e-9)
    # From the CSV file, and with the keys of the zones by default
    results.to_csv(tmp_path / 'results.csv', index=False)
    hook.keys = {}
    pd.testing.assert_frame_equal(ch.set_of_results(tmp_path / 'results.csv', hook), found)
    with pytest.raises(ValueError, match=r"Zone Mean Radiant Temperature.*Block1_Zone2"):
        ch.set_of_results(results.drop(columns='BLOCK1:ZONE2:Zone Mean Radiant Temperature [C](Hourly)'), hook)


@needs_idd
def test_apply_set_setpoints_prepares_the_model(tmp_path):
    idf = _model(tmp_path)
    counts = {kind: len(idf.idfobjects[kind]) for kind in ('EnergyManagementSystem:GlobalVariable',
                                                          'EnergyManagementSystem:OutputVariable')}
    hook = ch.apply_set_setpoints(idf, set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5,
                                  air_speed=0.1)
    assert isinstance(hook, ch.SetSetpointHook) and sorted(hook.zones) == ZONES and hook.method == 'table'
    assert hook.keys == {'Block1_Zone1': 'Block1:Zone1', 'Block1_Zone2': 'Block1:Zone2'}
    # The sensors and the variables of the setpoints of the hook (one global variable object for each zone,
    # accim.sim.ems.hook_setpoints): no output of the SET with the table
    counts['EnergyManagementSystem:GlobalVariable'] += len(ZONES)
    assert {kind: len(idf.idfobjects[kind]) for kind in counts} == counts
    sensors = {s.Name: s for s in idf.idfobjects['EnergyManagementSystem:Sensor']}
    ems_outputs = {o.Name for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    # The outputs of EnergyPlus of the SET of each zone, at the frequency of the outputs of the ACCIS of the model
    requested = {(o.Key_Value, o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']}
    for zone in ZONES:
        key = hook.keys[zone]
        for prefix, variable in (('SET_MAT', 'Zone Mean Air Temperature'), ('SET_MRT', 'Zone Mean Radiant Temperature'),
                                 ('SET_RH', 'Zone Air Relative Humidity')):
            sensor = sensors[f'{prefix}_{zone}']
            assert (sensor.OutputVariable_or_OutputMeter_Index_Key_Name,
                    sensor.OutputVariable_or_OutputMeter_Name) == (key, variable)
            assert (key, variable, 'Hourly') in requested
        assert f'SET_{zone}' not in ems_outputs
    # The ATHB and the SET would set the same thermostats
    with pytest.raises(ValueError, match='already has the setpoints of the ATHB or of the SET'):
        ch.apply_athb_setpoints(idf)
    with pytest.raises(ValueError, match='already has the setpoints of the ATHB or of the SET'):
        ch.apply_set_setpoints(idf, set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5, air_speed=0.1)
    with pytest.raises(ValueError, match='The setpoints of the SET need full air-conditioning'):
        (tmp_path / 'mm').mkdir()
        ch.apply_set_setpoints(_model(tmp_path / 'mm', script_type='vrf_mm'), set_cooling_setpoint=27,
                               set_heating_setpoint=21, met=1.1, clo=0.5, air_speed=0.1)
    # With the bisection, the output of the SET of each zone, at the frequencies given
    (tmp_path / 'bisection').mkdir()
    other = _model(tmp_path / 'bisection')
    hook = ch.apply_set_setpoints(other, set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5,
                                  air_speed=0.1, method='bisection', output_frequencies=['timestep'])
    assert hook.method == 'bisection'
    declared = {str(name) for g in other.idfobjects['EnergyManagementSystem:GlobalVariable'] for name in g.fieldvalues[1:]}
    ems_outputs = {o.Name: o for o in other.idfobjects['EnergyManagementSystem:OutputVariable']}
    requested = {(o.Key_Value, o.Variable_Name, o.Reporting_Frequency) for o in other.idfobjects['Output:Variable']}
    for zone in ZONES:
        output = ems_outputs[f'SET_{zone}']
        assert f'SET_{zone}' in declared
        assert (output.EMS_Variable_Name, output.Type_of_Data_in_Variable, output.Units) == (f'SET_{zone}', 'Averaged',
                                                                                              'C')
        assert ('*', f'SET_{zone}', 'Timestep') in requested
        assert (hook.keys[zone], 'Zone Mean Radiant Temperature', 'Timestep') in requested


@needs_energyplus
def test_the_set_setpoints_in_energyplus(tmp_path, monkeypatch):
    from accim.run import run_ep
    from accim.sim.accis import load_idf

    pytest.importorskip('pythermalcomfort')
    model, athb = _athb_model(tmp_path / 'set', monkeypatch)
    # The same model with the setpoints of the SET instead of those of the ATHB
    idf = load_idf(model)
    for prefix in ('ATHB_MAT', 'ATHB_MRT', 'ATHB_RH'):
        for zone in athb.zones:
            idf.removeidfobject(idf.getobject('EnergyManagementSystem:Sensor', f'{prefix}_{zone}'))
    hook = ch.apply_set_setpoints(idf, set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5,
                                  air_speed=0.1)
    idf.save()
    shutil.copy(EPW, model.parent / 'Seville.epw')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        [result] = run_ep(only_accim_idfs=False, confirm=True, processes=1, backend='api', hooks=[hook])
    assert result.success, result.error
    results = pd.read_csv(model.parent / 'athb[Seville.csv')
    columns = list(results.columns)

    def column(start):
        return results[next(c for c in columns if c.upper().startswith(start.upper()))]

    for zone in ZONES:
        humidity = column(f'{zone.replace("_", ":").upper()}:Zone Air Relative Humidity').shift(1)
        interpolated = np.array([hook.setpoints_of_humidity(humidity[t]) for t in range(1, len(results))])
        exact = np.array([hook.operative_temperatures(humidity[t]) for t in range(1, len(results), 50)])
        heating = column(f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()
        cooling = column(f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()
        # The setpoints of the table of the hook, interpolated with the humidity of the previous timestep (that which
        # the sensor reads), within the tolerance of the bisection of the exact setpoints
        assert np.abs(heating - interpolated[:, 0]).max() <= 1e-3
        assert np.abs(cooling - interpolated[:, 1]).max() <= 1e-3
        assert np.abs(heating[::50] - exact[:, 0]).max() <= hook.tolerance_k + 1e-3
        assert np.abs(cooling[::50] - exact[:, 1]).max() <= hook.tolerance_k + 1e-3
        # The thermostats get them with the tolerance of the setpoints of the ACCIS (0.1 K)
        np.testing.assert_allclose(column(f'AHST_SCH_{zone}:Schedule Value').iloc[1:].to_numpy(), heating + 0.1,
                                   atol=1e-4)
        np.testing.assert_allclose(column(f'ACST_SCH_{zone}:Schedule Value').iloc[1:].to_numpy(), cooling - 0.1,
                                   atol=1e-4)


@needs_energyplus
def test_the_set_setpoints_by_bisection_in_energyplus(tmp_path, monkeypatch):
    from accim.run import run_ep
    from accim.sim.accis import load_idf

    pytest.importorskip('pythermalcomfort')
    model, athb = _athb_model(tmp_path / 'set', monkeypatch, end_day=16)
    idf = load_idf(model)
    for prefix in ('ATHB_MAT', 'ATHB_MRT', 'ATHB_RH'):
        for zone in athb.zones:
            idf.removeidfobject(idf.getobject('EnergyManagementSystem:Sensor', f'{prefix}_{zone}'))
    hook = ch.apply_set_setpoints(idf, set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5,
                                  air_speed=0.1, method='bisection')
    # The values that the sensors of the hook read (those of the end of the previous timestep, while the outputs of
    # EnergyPlus of a timestep are its means), copied by a program into reported variables
    from accim.sim.ems.programs import add_program

    for zone in ZONES:
        names = [f'Copy{prefix}_{zone}' for prefix in ('MAT', 'MRT', 'RH')]
        idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                         **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(names, start=1)})
        add_program(idf, f'CopySensors_{zone}', [f'set Copy{prefix}_{zone} = SET_{prefix}_{zone}'
                                                 for prefix in ('MAT', 'MRT', 'RH')])
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=f'CopySensors_{zone}',
                         EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor',
                         Program_Name_1=f'CopySensors_{zone}')
        for name in names:
            idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=name,
                             Type_of_Data_in_Variable='Averaged', Update_Frequency='ZoneTimestep', Units='')
            idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name, Reporting_Frequency='Timestep')
    idf.save()
    shutil.copy(EPW, model.parent / 'Seville.epw')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        [result] = run_ep(only_accim_idfs=False, confirm=True, processes=1, backend='api', hooks=[hook])
    # set_tmp runs in the callbacks: run_simulation calls hook.prepare() in the process of the simulation before it loads
    # the library of the API of EnergyPlus (otherwise, its first call stopped the process with an access violation in
    # Python 3.14, see the DEVLOG)
    assert result.success, result.error
    results = pd.read_csv(model.parent / 'athb[Seville.csv')
    assert len(results) == 2 * 24 * STEPS
    columns = list(results.columns)

    def column(start):
        return results[next(c for c in columns if c.upper().startswith(start.upper()))]

    found = ch.set_of_results(results, hook)
    for zone in ZONES:
        air, radiant, humidity = (column(f'EMS:Copy{prefix}_{zone} [').iloc[1:].to_numpy()
                                  for prefix in ('MAT', 'MRT', 'RH'))
        # The setpoints without the tolerance are those of the bisection with the humidity that the sensor reads
        rows = list(range(0, len(air), 25))
        expected = np.array([hook.operative_temperatures(humidity[t]) for t in rows])
        heating = column(f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()[rows]
        cooling = column(f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [').iloc[1:].to_numpy()[rows]
        np.testing.assert_allclose(heating, expected[:, 0], atol=1e-6)
        np.testing.assert_allclose(cooling, expected[:, 1], atol=1e-6)
        # The SET of the zone, from the mean air and radiant temperatures and the humidity that its sensors read
        reported = column(f'EMS:SET_{zone} [').iloc[1:].to_numpy()
        np.testing.assert_allclose(reported, hook.zone_set(air, radiant, humidity), atol=1e-6)
        # set_of_results gives the SET of the outputs of each row (their means in the timestep): close to that of the
        # next row, whose sensors read the values of the end of the timestep
        difference = np.abs(found[f'SET_{zone}'].shift(1).iloc[1:].to_numpy() - reported)
        assert np.median(difference) < 0.05, np.median(difference)


class _ConstantHook:
    """A hook of the setpoints (as those of accim.sim.comfort_hooks) that gives constant setpoints to the zones."""

    runs_before_programs = True

    def __init__(self, zones, heating, cooling):
        self.zones, self.heating, self.cooling = list(zones), heating, cooling

    def __call__(self, controller, calling_point):
        if calling_point == CALLING_POINT:
            for zone in self.zones:
                ch._give_setpoints(controller, zone, self.heating, self.cooling)


@needs_energyplus
def test_the_setpoints_of_a_hook_are_the_same_with_both_backends(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf
    from accim.sim.ems.programs import set_program_lines
    from accim.sim.energyplus_api import run_simulations

    model, _ = _athb_model(tmp_path / 'model', monkeypatch)
    # The EMS backend cannot run the hook: the programs of the model give the same setpoints (21.5 and 26.5 °C) at the
    # beginning of RunACCIS_<zone>, as the hook does before the programs with the backend of the API
    emulated = load_idf(model)
    for zone in ZONES:
        program = emulated.getobject('EnergyManagementSystem:Program', f'RunACCIS_{zone}')
        lines = [str(value).strip() for value in program.fieldvalues[2:]]
        set_program_lines(program, [f'set HookAHST_{zone} = 21.5', f'set HookACST_{zone} = 26.5',
                                    f'set HookSetpoints_{zone} = 1'] + lines)
    emulated.saveas(str(tmp_path / 'emulated.idf'))
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    ems = subprocess.run([str(energyplus), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-r', '-x', '-w',
                          str(EPW), str(tmp_path / 'emulated.idf')], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
    [result] = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                               processes=1, before_programs=[_ConstantHook(ZONES, 21.5, 26.5)])
    assert result.success, result.error
    ems_results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
    # The applied setpoints, the setpoints without the tolerance and the hour counters follow those of the hook
    for zone in ZONES:
        assert (ems_results[f'ACST_SCH_{zone.upper()}:Schedule Value [](TimeStep)'].iloc[1:] == 26.4).all()
        assert (ems_results[f'AHST_SCH_{zone.upper()}:Schedule Value [](TimeStep)'].iloc[1:] == 21.6).all()
        no_tolerance = ems_results[f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [C](TimeStep)']
        assert (no_tolerance.iloc[1:] == 26.5).all()
        key = zone.replace('_', ':').upper()
        operative = ems_results[f'{key}:Zone Operative Temperature [C](TimeStep)'].shift(1).iloc[1:]
        occupied = ems_results[f'EMS:Occupied Hours_{zone} [H](TimeStep)'].iloc[1:] > 0
        comfortable = ems_results[f'EMS:Occupied Comfortable Hours_No Applicability_{zone} [H](TimeStep)'].iloc[1:] > 0
        within = (operative <= 26.5) & (operative >= 21.5)
        clear = (np.minimum(np.abs(operative - 21.5), np.abs(operative - 26.5)) > 1e-3).to_numpy()
        assert (comfortable[clear] == (within & occupied)[clear]).all()