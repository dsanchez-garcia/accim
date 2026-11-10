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

    def __init__(self, values):
        self.values = {name.upper(): value for name, value in values.items()}

    def get(self, name, program=None):
        return self.values.get(name.upper())

    def set(self, name, value):
        self.values[name.upper()] = value


def test_the_hook_sets_the_setpoints_and_the_outputs():
    pytest.importorskip('pythermalcomfort')
    hook = ch.AthbSetpointHook(ZONES, athb_cooling_setpoint=0.7, athb_heating_setpoint=-0.7, met=1.2, air_speed=0.15)
    controller = _Controller({'RMOT': 21.0, 'ATHB_MAT_Block1_Zone1': 26.0, 'ATHB_MRT_Block1_Zone1': 27.0,
                              'ATHB_RH_Block1_Zone1': 55.0, 'ATHB_MAT_Block1_Zone2': 22.0,
                              'ATHB_MRT_Block1_Zone2': 21.5, 'ATHB_RH_Block1_Zone2': 40.0})
    # Only at the beginning of the timesteps, after the programs of the ACCIS
    hook(controller, 'BEGINNEWENVIRONMENT')
    assert 'ACST_ACT_BLOCK1_ZONE1' not in controller.values
    hook(controller, CALLING_POINT)
    for zone, (air, radiant, humidity) in {'Block1_Zone1': (26.0, 27.0, 55.0),
                                           'Block1_Zone2': (22.0, 21.5, 40.0)}.items():
        heating, cooling = hook.operative_temperatures(humidity, 21.0)
        assert (controller.get(f'AHST_Act_{zone}'), controller.get(f'ACST_Act_{zone}')) == (heating, cooling)
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


def test_the_arguments_of_the_hook_are_checked():
    for arguments, message in ((dict(zones=[]), 'zones must name at least one zone'),
                               (dict(athb_heating_setpoint=0.5), 'must be lower than athb_cooling_setpoint'),
                               (dict(met='1.1'), 'met must be a number'),
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
        assert ch.zone_outputs(zone) == [f'ATHB_PMV_{zone}', f'ATHB_clo_{zone}', f'ATHB_met_{zone}']
        for name, units in zip(ch.zone_outputs(zone), ('', 'clo', 'met')):
            assert name in declared
            output = ems_outputs[name]
            assert (output.EMS_Variable_Name, output.Type_of_Data_in_Variable, output.Update_Frequency,
                    output.Units) == (name, 'Averaged', 'ZoneTimestep', units)
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


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')
STEPS = 6


def _athb_model(folder, monkeypatch, **arguments):
    """The output IDF of AddAccis of the sample model (INT EN16798, category II, comfort mode 3, full
    air-conditioning) for 15-21 July, with the setpoints of the ATHB and the outputs of the zones at timestep frequency;
    return its path and the hook."""
    from accim.sim.accis import AddAccis, load_idf

    folder.mkdir(parents=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    model = load_idf(folder / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 7, 15
    run_period.End_Month, run_period.End_Day_of_Month = 7, 21
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
    for variable in ('Zone Air Relative Humidity', 'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average '
                                                   'Outdoor Air Temperature'):
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
        # The setpoints of the schedules are those of the bisection with the sensors of the zone (to its tolerance)
        assert np.abs(heating.iloc[1:].to_numpy() - expected[:, 0]).max() <= hook.tolerance_k
        assert np.abs(cooling.iloc[1:].to_numpy() - expected[:, 1]).max() <= hook.tolerance_k
        # The adapted clothing and metabolic rate of the running mean
        clo = column(f'EMS:ATHB_clo_{zone}').iloc[1:].to_numpy()
        met = column(f'EMS:ATHB_met_{zone}').iloc[1:].to_numpy()
        np.testing.assert_allclose(clo, [ch.athb_clo(1.1, value) for value in running_mean.iloc[1:]], atol=1e-5)
        np.testing.assert_allclose(met, [ch.athb_met(1.1, value) for value in running_mean.iloc[1:]], atol=1e-5)
        # The ATHB setpoints replace the adaptive setpoints of the ACCIS (category II of EN 16798-1)
        adaptive = column(f'EMS:Adaptive Cooling Setpoint Temperature_{zone} [')
        assert (np.abs(cooling - adaptive).iloc[1:] > 0.1).mean() > 0.9
        pmv = column(f'EMS:ATHB_PMV_{zone}')
        assert pmv.iloc[1:].between(-3, 3).all()


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
            below = ch.standard_effective_temperature(temperature - 0.05, temperature - 0.05, 0.1, humidity, 1.1, 0.5)
            above = ch.standard_effective_temperature(temperature + 0.05, temperature + 0.05, 0.1, humidity, 1.1, 0.5)
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
    assert 'ACST_ACT_BLOCK1_ZONE1' not in controller.values
    hook(controller, CALLING_POINT)
    for zone, humidity in {'Block1_Zone1': 55.0, 'Block1_Zone2': 35.5}.items():
        heating, cooling = hook.setpoints_of_humidity(humidity)
        assert (controller.get(f'AHST_Act_{zone}'), controller.get(f'ACST_Act_{zone}')) == (heating, cooling)
        assert hook.setpoints[zone] == (heating, cooling)
    copy = pickle.loads(pickle.dumps(hook))
    assert copy.position == 'sitting' and copy.table == hook.table


def test_the_arguments_of_the_set_hook_are_checked():
    values = dict(zones=['Z'], set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5, air_speed=0.1)
    for arguments, message in ((dict(set_heating_setpoint=27), 'must be lower than set_cooling_setpoint'),
                               (dict(met=-1), 'met must be between 0.0'),
                               (dict(clo='0.5'), 'clo must be a number'),
                               (dict(position='lying'), "position must be 'standing' or 'sitting'"),
                               (dict(tolerance_k=-1), 'tolerance_k must be between 0.0')):
        with pytest.raises(ValueError, match=message):
            ch.SetSetpointHook(**{**values, **arguments})
    # Out of the limits of the inputs of pythermalcomfort, it warns
    for arguments in (dict(met=0.8), dict(clo=2.0), dict(air_speed=2.5)):
        with pytest.warns(UserWarning, match='out of the range of the SET of pythermalcomfort'):
            ch.SetSetpointHook(**{**values, **arguments})
    with pytest.raises(TypeError):
        ch.SetSetpointHook(['Z'], set_cooling_setpoint=27, set_heating_setpoint=21)


@needs_idd
def test_apply_set_setpoints_prepares_the_model(tmp_path):
    idf = _model(tmp_path)
    counts = {kind: len(idf.idfobjects[kind]) for kind in ('EnergyManagementSystem:GlobalVariable',
                                                          'EnergyManagementSystem:OutputVariable', 'Output:Variable')}
    hook = ch.apply_set_setpoints(idf, set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5,
                                  air_speed=0.1)
    assert isinstance(hook, ch.SetSetpointHook) and sorted(hook.zones) == ZONES
    # Only the sensors of the relative humidity: no global variables or outputs of the SET
    assert {kind: len(idf.idfobjects[kind]) for kind in counts} == counts
    sensors = {s.Name: s for s in idf.idfobjects['EnergyManagementSystem:Sensor']}
    ems_outputs = {o.Name for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    for zone in ZONES:
        sensor = sensors[f'SET_RH_{zone}']
        assert sensor.OutputVariable_or_OutputMeter_Name == 'Zone Air Relative Humidity'
        assert f'SET_MAT_{zone}' not in sensors and f'SET_{zone}' not in ems_outputs
    # The ATHB and the SET would set the same thermostats
    with pytest.raises(ValueError, match='already has the setpoints of the ATHB or of the SET'):
        ch.apply_athb_setpoints(idf)
    with pytest.raises(ValueError, match='already has the setpoints of the ATHB or of the SET'):
        ch.apply_set_setpoints(idf, set_cooling_setpoint=27, set_heating_setpoint=21, met=1.1, clo=0.5, air_speed=0.1)
    with pytest.raises(ValueError, match='The setpoints of the SET need full air-conditioning'):
        (tmp_path / 'mm').mkdir()
        ch.apply_set_setpoints(_model(tmp_path / 'mm', script_type='vrf_mm'), set_cooling_setpoint=27,
                               set_heating_setpoint=21, met=1.1, clo=0.5, air_speed=0.1)


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
        heating = column(f'AHST_SCH_{zone}:Schedule Value').iloc[1:].to_numpy()
        cooling = column(f'ACST_SCH_{zone}:Schedule Value').iloc[1:].to_numpy()
        # The setpoints of the table of the hook, interpolated with the humidity of the previous timestep (that which
        # the sensor reads), within the tolerance of the bisection of the exact setpoints
        assert np.abs(heating - interpolated[:, 0]).max() <= 1e-3
        assert np.abs(cooling - interpolated[:, 1]).max() <= 1e-3
        assert np.abs(heating[::50] - exact[:, 0]).max() <= hook.tolerance_k + 1e-3
        assert np.abs(cooling[::50] - exact[:, 1]).max() <= hook.tolerance_k + 1e-3