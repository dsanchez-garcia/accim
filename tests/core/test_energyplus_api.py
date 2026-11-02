"""Tests for accim.sim.energyplus_api, the backend that runs the EMS programs of the models in Python through
the API of EnergyPlus (pyenergyplus), and for run_ep(backend='api').

The unit tests use a fake API that records what the controller does at each calling point. The last test
runs an output IDF of AddAccis with both backends (EnergyPlus 25.1) and checks that the results are the same.
"""
import math
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from accim.energyplus import find_energyplus
from accim.run import run
from accim.sim.ems.erl import ErlRuntimeError
from accim.sim.energyplus_api import (
    MINIMUM_API_VERSION,
    ErlController,
    load_energyplus_api,
    objects_for_api,
    parse_idf,
    read_ems,
    render_idf,
    run_simulations,
)

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')

MODEL = """
Version, 25.1;
EnergyManagementSystem:Sensor,
    T_out,                   !- Name
    Environment,             !- Output:Variable or Output:Meter Index Key Name
    Site Outdoor Air Drybulb Temperature;  !- Output:Variable or Output:Meter Name
EnergyManagementSystem:Actuator, Heating_SP, Heating Schedule, Schedule:Constant, Schedule Value;
EnergyManagementSystem:GlobalVariable, Offset;
EnergyManagementSystem:Program, SetOffset, set Offset = 2;
EnergyManagementSystem:Program, SetSP,
    set Local = T_out + Offset,
    set Heating_SP = Local,
    set Day = DayOfYear,
    if T_out > 30,
    set Heating_SP = NULL,
    endif;
EnergyManagementSystem:ProgramCallingManager, Init, BeginNewEnvironment, SetOffset;
EnergyManagementSystem:ProgramCallingManager, Main, BeginTimestepBeforePredictor, SetSP;
EnergyManagementSystem:OutputVariable, Setpoint Local, Local, Averaged, ZoneTimestep, SetSP, C;
EnergyManagementSystem:OutputVariable, Heating Setpoint, Heating_SP, Averaged, ZoneTimestep, , C;
EnergyManagementSystem:OutputVariable, Offset Value, Offset, Averaged, ZoneTimestep, , C;
Schedule:Constant, Heating Schedule, , 20;
"""


def test_parse_and_render_idf():
    objects = parse_idf(MODEL)

    sensor = [o for o in objects if o.key == 'ENERGYMANAGEMENTSYSTEM:SENSOR'][0]
    assert sensor.fields == ['T_out', 'Environment', 'Site Outdoor Air Drybulb Temperature']
    assert sensor.field(5) == ''
    assert parse_idf(render_idf(objects)) == objects


def test_read_ems():
    ems = read_ems(parse_idf(MODEL))

    assert ems.version == '25.1'
    assert ems.sensors == [('T_OUT', 'Environment', 'Site Outdoor Air Drybulb Temperature')]
    assert ems.actuators == [('HEATING_SP', 'Heating Schedule', 'Schedule:Constant', 'Schedule Value')]
    assert ems.global_variables == ['OFFSET']
    assert list(ems.programs) == ['SETOFFSET', 'SETSP']
    assert ems.calling_managers == [('Init', 'BEGINNEWENVIRONMENT', ['SETOFFSET']),
                                    ('Main', 'BEGINTIMESTEPBEFOREPREDICTOR', ['SETSP'])]
    assert ems.reported_variables == [('ACCIMAPI_SETSP_LOCAL', 'LOCAL', 'SETSP'), ('HEATING_SP', 'HEATING_SP', ''),
                                      ('OFFSET', 'OFFSET', '')]
    assert ems.added_global_variables() == ['ACCIMAPI_SETSP_LOCAL', 'HEATING_SP']
    assert ems.has_programs and not ems.unsupported


def test_output_variables_of_programs_report_the_global_variables_of_the_same_name():
    # As FindEMSVariable of EnergyPlus: in the scope of a program, a name is the global variable, the sensor, the
    # actuator or the built-in variable of that name, if there is one, and otherwise a local variable of the program
    model = MODEL + '''
EnergyManagementSystem:OutputVariable, Offset In SetSP, Offset, Averaged, ZoneTimestep, SetSP, C;
EnergyManagementSystem:OutputVariable, Outdoor In SetSP, T_out, Averaged, ZoneTimestep, SetSP, C;
EnergyManagementSystem:OutputVariable, Hour In SetSP, CurrentTime, Averaged, ZoneTimestep, SetSP, ;
EnergyManagementSystem:OutputVariable, Actuator In SetSP, Heating_SP, Averaged, ZoneTimestep, SetSP, C;
'''
    ems = read_ems(parse_idf(model))
    objects = {o.fields[0]: o.fields for o in objects_for_api(parse_idf(model))
               if o.key == 'ENERGYMANAGEMENTSYSTEM:OUTPUTVARIABLE'}

    assert ems.reported_variables == [
        ('ACCIMAPI_SETSP_LOCAL', 'LOCAL', 'SETSP'), ('HEATING_SP', 'HEATING_SP', ''), ('OFFSET', 'OFFSET', ''),
        ('T_OUT', 'T_OUT', ''), ('CURRENTTIME', 'CURRENTTIME', '')]
    assert objects['Offset In SetSP'] == ['Offset In SetSP', 'Offset', 'Averaged', 'ZoneTimestep', '', 'C']
    assert objects['Outdoor In SetSP'][1] == 'T_out'
    assert objects['Hour In SetSP'][1] == 'CurrentTime'
    assert objects['Actuator In SetSP'][1] == 'Heating_SP'
    assert ems.added_global_variables() == ['ACCIMAPI_SETSP_LOCAL', 'HEATING_SP']


def test_objects_for_api_remove_the_programs_and_actuators():
    objects = objects_for_api(parse_idf(MODEL))

    keys = [o.key for o in objects]
    for key in ('ENERGYMANAGEMENTSYSTEM:PROGRAM', 'ENERGYMANAGEMENTSYSTEM:PROGRAMCALLINGMANAGER',
                'ENERGYMANAGEMENTSYSTEM:ACTUATOR'):
        assert key not in keys
    assert 'ENERGYMANAGEMENTSYSTEM:SENSOR' in keys
    outputs = {o.fields[0]: o.fields for o in objects if o.key == 'ENERGYMANAGEMENTSYSTEM:OUTPUTVARIABLE'}
    # The variables of programs are reported through new global variables, and the actuators through global
    # variables with their names
    assert outputs['Setpoint Local'] == ['Setpoint Local', 'ACCIMAPI_SETSP_LOCAL', 'Averaged', 'ZoneTimestep', '', 'C']
    assert outputs['Heating Setpoint'][1] == 'Heating_SP'
    assert objects[-1].type == 'EnergyManagementSystem:GlobalVariable'
    assert objects[-1].fields == ['ACCIMAPI_SETSP_LOCAL', 'HEATING_SP']


class _FakeFunctions:
    """The C functions of the API (exchange.api)."""

    def zoneTimeStep(self, state):  # noqa: N802 (the names of the API)
        return 1 / 6

    def numTimeStepsInHour(self, state):  # noqa: N802
        return 6

    def dayOfYear(self, state):  # noqa: N802
        return 182


class _FakeExchange:
    def __init__(self):
        self.api = _FakeFunctions()
        self.handles = {'T_OUT': 1, 'OFFSET': 2, 'ACCIMAPI_SETSP_LOCAL': 3, 'HEATING_SP': 4}
        self.values = {1: 20.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self.actuated = {}
        # The type and the variable of each actuator, which the API sets as setActuatorValue (datatransfer.cc)
        self.kinds = {}
        self.actuator_values = {}

    def get_ems_global_handle(self, state, name):
        return self.handles.get(name, 0)

    def get_ems_global_value(self, state, handle):
        return self.values[handle]

    def set_ems_global_value(self, state, handle, value):
        self.values[handle] = value

    def get_actuator_handle(self, state, component_type, control_type, unique_name):
        known = ('SCHEDULE:CONSTANT', 'SCHEDULE VALUE', 'HEATING SCHEDULE')
        return 7 if (component_type.upper(), control_type.upper(), unique_name.upper()) == known else -1

    def set_actuator_value(self, state, handle, value):
        kind = self.kinds.get(handle, 'real')
        if kind == 'integer':
            # std::lround: to the nearest integer, halves away from 0
            value = float(math.copysign(math.floor(abs(value) + 0.5), value))
        elif kind == 'logical':
            value = 1.0 if 0.99999 < value < 1.00001 else 0.0
        self.actuator_values[handle] = value
        self.actuated[handle] = value

    def get_actuator_value(self, state, handle):
        return self.actuator_values.get(handle, 0.0)

    def reset_actuator(self, state, handle):
        self.actuated[handle] = None

    def current_environment_num(self, state):
        return 1


class _FakeRuntime:
    def __init__(self):
        self.callbacks = {}
        self.stopped = False
        self.messages = []

    def __getattr__(self, name):
        if name.startswith('callback_'):
            return lambda state, function: self.callbacks.setdefault(name, []).append(function)
        raise AttributeError(name)

    def stop_simulation(self, state):
        self.stopped = True

    def issue_warning(self, state, message):
        self.messages.append(('warning', message))

    def issue_severe(self, state, message):
        self.messages.append(('severe', message))

    def fire(self, name):
        for function in self.callbacks[name]:
            function('state')


class _FakeAPI:
    def __init__(self):
        self.runtime = _FakeRuntime()
        self.exchange = _FakeExchange()


def _controller(model=MODEL, **kwargs):
    controller = ErlController(read_ems(parse_idf(model)), **kwargs)
    api = _FakeAPI()
    controller.register(api, 'state')
    return controller, api


def test_controller_runs_the_programs_at_their_calling_points():
    controller, api = _controller()
    exchange = api.exchange

    api.runtime.fire('callback_begin_new_environment')
    # The actuators begin released, and the global variables of the outputs are written
    assert controller.environments == 1
    assert exchange.actuated == {7: None}
    assert exchange.values[2] == 2.0

    api.runtime.fire('callback_begin_system_timestep_before_predictor')
    assert exchange.actuated == {7: 22.0}
    assert (exchange.values[3], exchange.values[4]) == (22.0, 22.0)
    # Day is a local variable of SetSP, and DayOfYear a built-in variable
    assert controller.get('Day', 'SetSP') == 182.0

    # A Null actuator releases the schedule
    exchange.values[1] = 35.0
    api.runtime.fire('callback_begin_system_timestep_before_predictor')
    assert exchange.actuated == {7: None}
    assert (exchange.values[3], exchange.values[4]) == (37.0, 0.0)
    assert controller.get('Local', 'SetSP') == 37.0


def test_actuators_with_values_that_are_not_null_are_actuated_with_their_number():
    # EnergyPlus only releases the actuators whose value is Null; Null + 1 is the number 0, which has not been set
    controller, api = _controller(MODEL.replace('set Heating_SP = NULL,', 'set Heating_SP = NULL + 1,'))
    exchange = api.exchange
    exchange.values[1] = 35.0

    api.runtime.fire('callback_begin_new_environment')
    api.runtime.fire('callback_begin_system_timestep_before_predictor')

    assert exchange.actuated == {7: 0.0}
    assert exchange.values[4] == 0.0


@pytest.mark.parametrize('kind, value, expected', [
    ('real', 22.7, 22.7),
    # The EMS rounds the integer actuators down (std::floor); the API alone would round 22.7 to 23 and -0.4 to 0
    ('integer', 22.7, 22.0),
    ('integer', -0.4, -1.0),
    ('integer', 3, 3.0),
    # The EMS only takes 1 as true; the API alone would take 1.000001 as true
    ('logical', 1, 1.0),
    ('logical', 1.000001, 0.0),
    ('logical', 2, 0.0),
])
def test_actuators_are_set_as_the_ems_sets_them(kind, value, expected):
    controller, api = _controller(MODEL.replace('set Heating_SP = Local,', f'set Heating_SP = {value},'))
    api.exchange.kinds[7] = kind

    api.runtime.fire('callback_begin_new_environment')
    api.runtime.fire('callback_begin_system_timestep_before_predictor')

    assert controller._actuator_kinds == {7: kind}
    assert api.exchange.actuated == {7: expected}


@pytest.mark.parametrize('kind, original', [('real', 2.5), ('integer', 3.0), ('logical', 1.0)])
def test_finding_the_type_of_an_actuator_does_not_change_it(kind, original):
    controller, api = _controller()
    exchange = api.exchange
    exchange.kinds[7] = kind
    exchange.actuator_values[7] = original

    assert controller._actuator_kind('state', 7) == kind
    assert exchange.actuator_values[7] == original
    assert exchange.actuated[7] is None


def test_hooks_can_read_and_change_the_variables():
    calls = []

    def add_one(controller, calling_point):
        calls.append(calling_point)
        if calling_point == 'BEGINTIMESTEPBEFOREPREDICTOR':
            controller.set('Heating_SP', controller.get('Heating_SP') + 1)

    controller, api = _controller(after_programs=[add_one])
    api.runtime.fire('callback_begin_new_environment')
    api.runtime.fire('callback_begin_system_timestep_before_predictor')

    assert calls == ['BEGINNEWENVIRONMENT', 'BEGINTIMESTEPBEFOREPREDICTOR']
    assert api.exchange.actuated == {7: 23.0}


def test_errors_of_the_programs_stop_the_simulation():
    model = MODEL.replace('set Local = T_out + Offset', 'set Local = T_out / 0')
    controller, api = _controller(model)

    api.runtime.fire('callback_begin_new_environment')
    api.runtime.fire('callback_begin_system_timestep_before_predictor')

    assert isinstance(controller.error, ErlRuntimeError)
    assert api.runtime.stopped


def test_messages_of_the_programs_go_to_the_error_file():
    controller, api = _controller(MODEL.replace('set Offset = 2;', 'set Offset = @SevereWarnEP 2;'))

    api.runtime.fire('callback_begin_new_environment')

    assert controller.get('Offset') == 2.0
    assert api.runtime.messages == [('severe', 'EMS user program issued severe warning with error code = 2.00')]


@pytest.mark.parametrize('extra, error, message', [
    ('EnergyManagementSystem:TrendVariable, Trend, T_out, 10;', NotImplementedError, 'does not support the objects'),
    ('EnergyManagementSystem:ProgramCallingManager, Udc, UserDefinedComponentModel, SetSP;', NotImplementedError,
     'does not support the calling point'),
    ('EnergyManagementSystem:ProgramCallingManager, Other, EndOfZoneSizing, Missing;', ValueError,
     'which are not in the model'),
])
def test_unsupported_models(extra, error, message):
    with pytest.raises(error, match=message):
        ErlController(read_ems(parse_idf(MODEL + extra)))


@pytest.mark.parametrize('version', ['9.4', '24.1'])
def test_the_api_backend_needs_energyplus_24_2(version):
    assert MINIMUM_API_VERSION == (24, 2)
    with pytest.raises(ValueError, match='needs EnergyPlus 24.2 or later'):
        load_energyplus_api(version)


def test_run_simulations_without_jobs():
    assert run_simulations([]) == []


@pytest.fixture
def run_folder(tmp_path, monkeypatch):
    (tmp_path / 'model[CS_INT EN16798[NS_X.idf').write_text('Version, 25.1;\n')
    (tmp_path / 'other.idf').write_text('Version, 25.1;\n')
    (tmp_path / 'Seville.epw').write_text('')
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_run_ep_with_the_api_backend(run_folder, monkeypatch):
    import accim.sim.energyplus_api as energyplus_api

    calls = []

    def fake_run_simulations(jobs, processes=2):
        calls.append((list(jobs), processes))
        return ['results']

    monkeypatch.setattr(energyplus_api, 'run_simulations', fake_run_simulations)

    assert run.run_ep(only_accim_idfs=True, confirm=False, backend='api') == []
    assert calls == []
    assert run.run_ep(only_accim_idfs=True, confirm=True, processes=3, backend='api') == ['results']
    assert calls == [([('model[CS_INT EN16798[NS_X.idf', 'Seville.epw',
                        {'output_directory': str(run_folder), 'output_prefix': 'model[CS_INT EN16798[NS_X[Seville'})],
                      3)]


def test_both_backends_name_the_simulations_alike(run_folder, monkeypatch):
    # Before, the EMS backend cut the name of the EPW at its first dot, so the results of 'Seville.2050.epw' and
    # 'Seville.2080.epw' had the same names
    import accim.sim.energyplus_api as energyplus_api

    (run_folder / 'Seville.epw').unlink()
    (run_folder / 'USA_CO_Golden-NREL.724666_TMY3.epw').write_text('')
    jobs = []
    monkeypatch.setattr(energyplus_api, 'run_simulations', lambda j, processes=2: jobs.extend(j) or [])
    run.run_ep(only_accim_idfs=True, confirm=True, backend='api')
    idf = SimpleNamespace(idfname=str(run_folder / 'model[CS_INT EN16798[NS_X.idf'),
                          idfobjects={'version': [SimpleNamespace(Version_Identifier='25.1')]})

    expected = 'model[CS_INT EN16798[NS_X[USA_CO_Golden-NREL.724666_TMY3'
    assert jobs[0][2]['output_prefix'] == expected
    assert run.make_eplaunch_options(idf, 'USA_CO_Golden-NREL.724666_TMY3.epw')['output_prefix'] == expected
    assert run.make_eplaunch_options(idf, 'USA_CO_Golden-NREL.724666_TMY3')['output_directory'] == str(run_folder)
    assert run.simulation_name('folder/model.IDF', 'Seville.2050.epw') == 'model[Seville.2050'


def test_run_ep_rejects_unknown_backends(run_folder):
    with pytest.raises(ValueError, match="'python' is not a valid backend"):
        run.run_ep(only_accim_idfs=True, confirm=False, backend='python')


def _energyplus_with_api(version):
    folder = find_energyplus(version, required=False)
    return folder if folder is not None and (folder / 'pyenergyplus').is_dir() else None


@pytest.mark.skipif(not (_energyplus_with_api('25.1') and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')
@pytest.mark.parametrize('zone_arguments', [
    None,
    # Each zone with its own arguments: INT ASHRAE 55 and natural ventilation in the zone 2
    {'Block1:Zone2': {'comfort_standard': 2, 'category': 80, 'comfort_mode': 3, 'hvac_mode': 1, 'ventilation_control': 1}},
])
def test_the_ems_and_api_backends_give_the_same_results(tmp_path, monkeypatch, zone_arguments):
    from accim.sim.accis import AddAccis

    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)
    AddAccis(script_type='vrf_mm', supply_air_temp_input_method='temperature difference', output_type='standard',
             output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto', setpoint_type='temperature',
             comfort_standard=[1], category=[3], comfort_mode=[3], hvac_mode=[2], ventilation_control=[0], confirm=True,
             verbose=False, zone_arguments=zone_arguments)
    output_idf = sorted(tmp_path.glob('TestModel[[]*.idf'))[0]
    # Three days of July, after the sizing of the design days
    objects = parse_idf(output_idf.read_bytes().decode('latin-1'))
    run_period = [o for o in objects if o.key == 'RUNPERIOD'][0]
    run_period.fields[1:7] = ['7', '1', '2002', '7', '3', '2002']
    model = tmp_path / 'model.idf'
    model.write_bytes(render_idf(objects).encode('latin-1'))

    energyplus = _energyplus_with_api('25.1') / 'energyplus.exe'
    ems = subprocess.run([str(energyplus), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-r', '-x',
                          '-w', str(SAMPLE_EPW), str(model)], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
    results = run_simulations([(model, SAMPLE_EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    # The callbacks of BeginNewEnvironment run for the run period (not while sizing)
    assert results[0].environments >= 1

    ems_results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    assert len(ems_results) == 3 * 24
    assert any('Adaptive Cooling Setpoint Temperature' in column for column in ems_results.columns)
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
    # The setpoints of each zone: the same in both zones, unless they have their own arguments
    zone1, zone2 = (ems_results[f'EMS:Adaptive Cooling Setpoint Temperature_Block1_{zone} [C](Hourly)']
                    for zone in ('Zone1', 'Zone2'))
    assert zone1.equals(zone2) is (zone_arguments is None)


def _shading_example():
    folder = _energyplus_with_api('25.1')
    if folder is None:
        return None
    idf = folder / 'ExampleFiles' / 'EMSWindowShadeControl.idf'
    epw = folder / 'WeatherData' / 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
    return (folder, idf, epw) if idf.exists() and epw.exists() else None


@pytest.mark.skipif(_shading_example() is None, reason='needs EnergyPlus 25.1 (with its Python API) and its examples')
def test_integer_actuators_are_set_as_with_the_ems(tmp_path):
    # The status of a window shading control is an integer actuator. The example of EnergyPlus sets it to 6 (interior
    # blind on); with 6.6, the EMS sets 6 (std::floor), and the API alone would set 7 (exterior blind on)
    folder, idf, epw = _shading_example()
    objects = parse_idf(idf.read_bytes().decode('latin-1'))
    program = [o for o in objects if o.key == 'ENERGYMANAGEMENTSYSTEM:PROGRAM'
               and o.fields[0].upper() == 'SET_SHADE_CONTROL_STATE'][0]
    line = 'Set Zn001_Wall001_Win001_Shading_Deploy_Status = Shade_Status_Interior_Blind_On'
    program.fields = [field + ' + 0.6' if field == line else field for field in program.fields]
    assert sum(field.endswith(' + 0.6') for field in program.fields) == 2
    run_period = [o for o in objects if o.key == 'RUNPERIOD'][0]
    run_period.fields[1:7] = ['7', '1', '', '7', '3', '']
    model = tmp_path / 'model.idf'
    model.write_bytes(render_idf(objects).encode('latin-1'))

    ems = subprocess.run([str(folder / 'energyplus.exe'), '-d', str(tmp_path / 'ems'), '-p', 'run', '-s', 'C', '-r',
                          '-x', '-w', str(epw), str(model)], capture_output=True, text=True)
    assert ems.returncode == 0, ems.stdout[-3000:]
    results = run_simulations([(model, epw, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error

    ems_results = pd.read_csv(tmp_path / 'ems' / 'run.csv')
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    shading = [c for c in ems_results.columns if 'Surface Shading Device Is On Time Fraction' in c]
    assert shading and (ems_results[shading] > 0).any().any()
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
