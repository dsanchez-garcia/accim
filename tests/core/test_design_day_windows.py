"""Tests for the windows and doors of full air-conditioning on the design days (:mod:`accim.sim.ems.design_days`).

In full air-conditioning ('vrf_ac' and 'ex_ac', and the VRF systems of ``add_vrf_system``), the windows of the model
keep its own control. Until 2026-11-19 they kept it on the design days too, so EnergyPlus sized the HVAC systems with
the windows that the model opens there: those of the sample model of accim open on its winter design day (the venting
setpoint of their schedule 20001 is 0 °C on the WinterDesignDays), and its VRF systems were sized for the outdoor air
at −4 °C through them: design heating loads of 303 and 357 kW, indoor units of 62 and 73 m³/s, coils of 1.0 and 1.2 MW
and constant fans of 8.9 and 10.5 kW, whose heat kept the zones at 22.6 to 26.6 °C in January. Since then, the windows
and doors that the EMS of mixed mode would open and close are closed on the design days (the decision of 2026-11-19 of
``notes/decisions.md``) and keep the control of the model on the other days. The names of the instances of the
ZoneVentilation objects (the unique names of their actuators) were checked against the actuators that EnergyPlus 25.1
and 9.6 make available (their EDD files) on 2026-11-19; a wrong one stops EnergyPlus ('Actuator ... not found').
"""
import lzma
import re
import subprocess
import warnings
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim import windows
from accim.sim.ems.design_days import PROGRAM

REPO = Path(__file__).resolve().parents[2]
INPUTS = REPO / 'tests' / 'core' / 'golden_master' / 'inputs'
EXAMPLES = default_energyplus_folder('25.1') / 'ExampleFiles'
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
ARGUMENTS = dict(supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['hourly'], keep_existing_outputs=False, setpoint_type='temperature',
                 verbose=False)
#: The windows of the occupied zones of the sample model, in the order of its AirflowNetwork surfaces
SAMPLE_WINDOWS = ['Block1:Zone2_Wall_3_0_0_0_0_0_Win', 'Block1:Zone2_Wall_4_0_0_0_0_0_Win',
                  'Block1:Zone2_Wall_5_0_0_0_0_0_Win', 'Block1:Zone1_Wall_2_0_0_0_0_0_Win',
                  'Block1:Zone1_Wall_3_0_0_0_0_0_Win', 'Block1:Zone1_Wall_5_0_0_0_0_0_Win']

pytestmark = pytest.mark.skipif(not INPUTS.exists(), reason='needs the input models of the golden master')


def _input_model(tmp_path, name):
    from ._optional import read_model

    path = tmp_path / f'{name}.idf'
    path.write_bytes(lzma.decompress((INPUTS / f'{name}.idf.xz').read_bytes()))
    return read_model(str(path))


def _example(tmp_path, name):
    from ._optional import read_model

    if not (EXAMPLES / name).exists():
        pytest.skip(f'needs the example file {name} of EnergyPlus 25.1')
    path = tmp_path / name
    path.write_bytes((EXAMPLES / name).read_bytes())
    return read_model(str(path))


def _add(idf, script_type='vrf_ac'):
    """add_accis_to_idf; return the model and the messages of its UserWarnings."""
    from accim.sim.accis import add_accis_to_idf

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model = add_accis_to_idf(idf, script_type=script_type, **ARGUMENTS)
    return model, [str(w.message) for w in caught if w.category is UserWarning]


def _program_lines(idf):
    program = idf.getobject('EnergyManagementSystem:Program', PROGRAM)
    return None if program is None else [str(line).strip() for line in program.fieldvalues[2:] if str(line).strip()]


def _actuators(idf):
    """The actuators of the windows on the design days: their names end with '_DesignDayVOF' or '_DesignDayFlow' (and
    '_2', '_3'... if another EMS object had the name)."""
    return [(str(a.Name), str(a.Actuated_Component_Unique_Name), str(a.Actuated_Component_Type),
             str(a.Actuated_Component_Control_Type)) for a in idf.idfobjects['EnergyManagementSystem:Actuator']
            if re.search(r'_DesignDay(VOF|Flow)(_\d+)?$', str(a.Name))]


def _surface_controls(idf):
    """The ventilation control mode, the setpoint schedule of the venting and the availability schedule of each
    AirflowNetwork surface."""
    return {str(s.Surface_Name): (str(s.Ventilation_Control_Mode),
                                  str(s.Ventilation_Control_Zone_Temperature_Setpoint_Schedule_Name),
                                  str(s.Venting_Availability_Schedule_Name))
            for s in idf.idfobjects['AirflowNetwork:MultiZone:Surface']}


@pytest.mark.parametrize('name, script_type', [('vrf2zones', 'vrf_ac'), ('exptac', 'ex_ac')])
def test_full_air_conditioning_closes_the_windows_of_the_airflow_network_on_the_design_days(tmp_path, name,
                                                                                           script_type):
    """The windows of the occupied zones (6 of the 8 of the model with PTACs, whose third zone has no occupants) get
    an actuator of their opening factor, which the program sets to 0 on the design days and to Null on the other days;
    their own control does not change."""
    idf = _input_model(tmp_path, name)
    before = _surface_controls(idf)

    _add(idf, script_type)

    names = [f'{w.replace(":", "_")}_DesignDayVOF' for w in SAMPLE_WINDOWS]
    assert _actuators(idf) == [(n, w, 'AirFlow Network Window/Door Opening', 'Venting Opening Factor')
                               for n, w in zip(names, SAMPLE_WINDOWS)]
    assert _program_lines(idf) == (['if DesignDay == 1'] + [f'set {n} = 0' for n in names] + ['else']
                                   + [f'set {n} = Null' for n in names] + ['endif'])
    managers = list(idf.idfobjects['EnergyManagementSystem:ProgramCallingManager'])
    manager = next(m for m in managers if m.Name == PROGRAM)
    assert (manager.EnergyPlus_Model_Calling_Point, manager.Program_Name_1) == ('BeginTimestepBeforePredictor',
                                                                               PROGRAM)
    sensor = idf.getobject('EnergyManagementSystem:Sensor', 'DesignDay')
    assert (sensor.OutputVariable_or_OutputMeter_Index_Key_Name, sensor.OutputVariable_or_OutputMeter_Name) == (
        'ACCIS Design Days', 'Schedule Value')
    schedule = idf.getobject('Schedule:Compact', 'ACCIS Design Days')
    assert [str(f) for f in schedule.fieldvalues[3:8]] == ['Through: 12/31', 'For: SummerDesignDay WinterDesignDay',
                                                           'Until: 24:00,1', 'For: AllOtherDays', 'Until: 24:00,0']
    # The windows keep the control of the model on the other days
    assert _surface_controls(idf) == before
    assert {control[1] for w, control in before.items() if w in SAMPLE_WINDOWS} == {'20001'}


@pytest.mark.parametrize('name, script_type', [('vrf2zones', 'vrf_mm'), ('exptac', 'ex_mm'),
                                               ('osmofficeex', 'ex_ac'), ('osmres', 'vrf_ac')])
def test_mixed_mode_and_the_models_without_windows_do_not_get_the_program(tmp_path, name, script_type):
    """Mixed mode closes the windows on the design days in their own programs; the models without windows that open
    (no AirflowNetwork openings or natural ventilation objects) do not change, nor do their output IDFs."""
    idf = _input_model(tmp_path, name)

    model, _ = _add(idf, script_type)

    assert _program_lines(idf) is None and not _actuators(idf)
    assert PROGRAM not in [m.Name for m in idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']]
    has_sensor = idf.getobject('EnergyManagementSystem:Sensor', 'DesignDay') is not None
    assert has_sensor is model.is_mixed_mode


def test_the_natural_ventilation_objects_are_closed_with_the_flow_rate_of_their_instances(tmp_path):
    """Without an AirflowNetwork, the instances of the natural ventilation objects of the occupied zones; the objects
    keep their schedules and limits, which control them on the other days."""
    idf = _input_model(tmp_path, 'osmresschvent')
    before = [v.obj[:] for v in idf.idfobjects['ZoneVentilation:WindandStackOpenArea']]

    _add(idf)

    vents = ['Zone Ventilation Wind and Stack Open Area', 'Zone Ventilation Wind and Stack Open Area 1']
    assert _actuators(idf) == [(f'{v.replace(" ", "_")}_DesignDayFlow', v, 'Zone Ventilation', 'Air Exchange Flow Rate')
                               for v in vents]
    assert [v.obj[:] for v in idf.idfobjects['ZoneVentilation:WindandStackOpenArea']] == before


def test_add_vrf_system_closes_the_windows_on_the_design_days(tmp_path):
    """The VRF systems of add_vrf_system (the setpoints of the PMV) are those of full air-conditioning: the same
    program."""
    from accim.sim.apmv import add_vrf_system

    idf = _input_model(tmp_path, 'vrf2zones')
    before = _surface_controls(idf)

    add_vrf_system(idf, verbose=False)

    assert [a[1] for a in _actuators(idf)] == SAMPLE_WINDOWS
    assert _program_lines(idf)[0] == 'if DesignDay == 1'
    assert _surface_controls(idf) == before


def _two_space_variant(idf):
    """The model with natural ventilation of the golden master (two zones of one space each, Floor_1 and Floor_2, and
    the SpaceList 'Residential - Living Space' of both), with a zone of two spaces (one wall of Floor_1_Zone in the
    space Floor_1b), a ZoneList of both zones and ZoneVentilation:DesignFlowRate objects of the ZoneList, of the
    SpaceList, of a space (named with a digit first, so that its actuator begins with 'Vent_') and of a zone."""
    idf.newidfobject('Space', Name='Floor_1b', Zone_Name='Floor_1_Zone')
    walls = [s for s in idf.idfobjects['BuildingSurface:Detailed']
             if s.Zone_Name == 'Floor_1_Zone' and s.Surface_Type.upper() == 'WALL']
    walls[0].Space_Name = 'Floor_1b'
    idf.newidfobject('ZoneList', Name='All Zones', Zone_1_Name='Floor_1_Zone', Zone_2_Name='Floor_2_Zone')
    for name, target in (('ListVent', 'All Zones'), ('SpaceListVent', 'Residential - Living Space'),
                         ('9 SpaceVent', 'Floor_2'), ('ZoneVent', 'Floor_2_Zone')):
        idf.newidfobject('ZoneVentilation:DesignFlowRate', Name=name,
                         Zone_or_ZoneList_or_Space_or_SpaceList_Name=target,
                         Schedule_Name='Always On Discrete hvac_library',
                         Design_Flow_Rate_Calculation_Method='Flow/Zone', Design_Flow_Rate=0.05,
                         Ventilation_Type='Natural')
    return idf


#: The actuators of the instances of the ventilation objects of _two_space_variant that EnergyPlus 25.1 made available
#: (its EDD file, 2026-11-19), in the order of accim
TWO_SPACE_INSTANCES = ['Floor_1 Zone Ventilation Wind and Stack Open Area',
                       'Floor_1b Zone Ventilation Wind and Stack Open Area',
                       'Zone Ventilation Wind and Stack Open Area 1',
                       'Floor_1 ListVent', 'Floor_1b ListVent', 'Floor_2 ListVent', 'Floor_1 SpaceListVent',
                       'Floor_2 SpaceListVent', '9 SpaceVent', 'ZoneVent']


def test_the_instances_of_the_ventilation_objects_are_named_as_energyplus_names_them(tmp_path):
    """EnergyPlus 25.1: an object of a zone of several spaces, a ZoneList or a SpaceList has one instance per space,
    '<space> <name>'; one of a space or a zone of one space, its name. Those of other zones are left out."""
    idf = _two_space_variant(_input_model(tmp_path, 'osmresschvent'))

    instances = windows.ventilation_instances(idf, ['Floor_1_Zone', 'Floor_2_Zone'])

    assert [i[0] for i in instances] == TWO_SPACE_INSTANCES
    assert [i[2] for i in instances] == ['Floor_1_Zone'] * 2 + ['Floor_2_Zone'] + ['Floor_1_Zone'] * 2 + [
        'Floor_2_Zone', 'Floor_1_Zone', 'Floor_2_Zone', 'Floor_2_Zone', 'Floor_2_Zone']
    assert [i[0] for i in windows.ventilation_instances(idf, ['FLOOR_2_ZONE'])] == [
        'Zone Ventilation Wind and Stack Open Area 1', 'Floor_2 ListVent', 'Floor_2 SpaceListVent', '9 SpaceVent',
        'ZoneVent']


class _Object(SimpleNamespace):
    def __getitem__(self, field):
        return getattr(self, field)


def test_the_instances_of_the_ventilation_objects_before_the_spaces():
    """Where the field of the zone does not take spaces ('Zone or ZoneList Name' of ZoneVentilation:DesignFlowRate and
    'Zone Name' of ZoneVentilation:WindandStackOpenArea, as in EnergyPlus 9.6, which made '<zone> <name>' available for
    the instances of a ZoneList on 2026-11-19), whatever the Space objects of the model."""
    def vent(object_type, name, zone_field, zone):
        return _Object(key=object_type.upper(), Name=name, fieldnames=['key', 'Name', zone_field], **{zone_field: zone},
                       Ventilation_Type='Natural')

    objects = {
        'ZONE': [_Object(key='ZONE', Name='Block1:Zone1'), _Object(key='ZONE', Name='Block1:Zone2')],
        'ZONELIST': [_Object(key='ZONELIST', Name='All Zones', fieldvalues=['ZoneList', 'All Zones', 'Block1:Zone1',
                                                                            'Block1:Zone2'])],
        'ZONEVENTILATION:DESIGNFLOWRATE': [
            vent('ZoneVentilation:DesignFlowRate', 'ListVent', 'Zone_or_ZoneList_Name', 'All Zones'),
            vent('ZoneVentilation:DesignFlowRate', 'Zone 1 Infiltration', 'Zone_or_ZoneList_Name', 'Block1:Zone1')],
        'ZONEVENTILATION:WINDANDSTACKOPENAREA': [
            vent('ZoneVentilation:WindandStackOpenArea', 'WindStack', 'Zone_Name', 'Block1:Zone2')],
    }
    idf = SimpleNamespace(idfobjects=objects)

    instances = windows.ventilation_instances(idf, ['Block1:Zone1', 'Block1:Zone2'])

    assert instances == [('WindStack', 'ZoneVentilation:WindandStackOpenArea', 'Block1:Zone2'),
                         ('Block1:Zone1 ListVent', 'ZoneVentilation:DesignFlowRate', 'Block1:Zone1'),
                         ('Block1:Zone2 ListVent', 'ZoneVentilation:DesignFlowRate', 'Block1:Zone2')]


def test_the_windows_with_an_occupant_ventilation_control_are_left_out_with_a_warning(tmp_path):
    """The example file AirflowNetworkOccupantVentilationControl: the occupant ventilation control of the zone of
    Window1 (AirflowNetwork:MultiZone:Zone) overrides the EMS, and full air-conditioning keeps it (mixed mode removes
    it), so Window1 is not closed on the design days."""
    idf = _example(tmp_path, 'AirflowNetworkOccupantVentilationControl.idf')
    zones = {str(z.Zone_Name): str(z.Occupant_Ventilation_Control_Name)
             for z in idf.idfobjects['AirflowNetwork:MultiZone:Zone']}

    model, messages = _add(idf, 'ex_ac')

    controlled = windows.occupant_controlled_surfaces(idf, [w for w, _ in windows.afn_openings(
        idf, model.occupied_zones_orig)])
    assert 'Window1' in controlled
    assert 'Window1' not in [a[1] for a in _actuators(idf)]
    assert any('occupant ventilation control' in m and "'Window1'" in m and 'cannot close them on the design days' in m
               for m in messages)
    # The controls of the model do not change
    assert {str(z.Zone_Name): str(z.Occupant_Ventilation_Control_Name)
            for z in idf.idfobjects['AirflowNetwork:MultiZone:Zone']} == zones


def test_the_windows_that_the_ems_of_the_model_opens_are_left_out_with_a_warning(tmp_path):
    """The example file EMSAirflowNetworkOpeningControlByHumidity opens a window with an EMS program of its own: an
    actuator of accim on it would release it on the other days (EnergyPlus applies the actuators of a window one after
    the other), so it keeps the EMS of the model."""
    idf = _example(tmp_path, 'EMSAirflowNetworkOpeningControlByHumidity.idf')

    _, messages = _add(idf, 'ex_ac')

    assert 'Zn001:Wall001:Win001' not in [a[1] for a in _actuators(idf)]
    assert any("EMS actuators ['MyOpenFactor']" in m and 'does not close them on the design days' in m
               for m in messages)


def test_the_names_of_the_actuators_are_unique_and_the_program_is_added_once(tmp_path):
    """An EMS variable of the model with the name of an actuator: the actuator gets '_2'. A model that already has the
    program does not get it again."""
    from accim.sim.ems.design_days import close_windows_on_design_days

    idf = _input_model(tmp_path, 'vrf2zones')
    idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                     Erl_Variable_1_Name='Block1_Zone2_Wall_3_0_0_0_0_0_Win_DesignDayVOF')
    model, _ = _add(idf)

    assert [a[0] for a in _actuators(idf)][:2] == ['Block1_Zone2_Wall_3_0_0_0_0_0_Win_DesignDayVOF_2',
                                                  'Block1_Zone2_Wall_4_0_0_0_0_0_Win_DesignDayVOF']
    objects = {object_type: len(idf.idfobjects[object_type]) for object_type in (
        'EnergyManagementSystem:Actuator', 'EnergyManagementSystem:Program', 'EnergyManagementSystem:Sensor',
        'EnergyManagementSystem:ProgramCallingManager')}
    assert close_windows_on_design_days(model) == []
    assert {object_type: len(idf.idfobjects[object_type]) for object_type in objects} == objects


def test_the_names_that_do_not_begin_with_a_letter_get_a_prefix(tmp_path):
    """EnergyPlus stops with the names of EMS variables that do not begin with a letter, so the actuators of such
    windows begin with 'Win_' (and those of such ventilation objects with 'Vent_', which EnergyPlus runs in
    test_energyplus_finds_the_instances_of_the_ventilation_objects_and_closes_them). The review of 2026-11-19 found it:
    a window named '3F ...' stopped the models in full air-conditioning, which had no EMS names of windows before."""
    idf = _input_model(tmp_path, 'vrf2zones')
    old, new = 'Block1:Zone2_Wall_3_0_0_0_0_0_Win', '3F Block1:Zone2 South Win'
    [window] = [w for w in idf.idfobjects['FenestrationSurface:Detailed'] if w.Name == old]
    [surface] = [s for s in idf.idfobjects['AirflowNetwork:MultiZone:Surface'] if s.Surface_Name == old]
    window.Name = surface.Surface_Name = new

    _add(idf)

    assert _actuators(idf)[0][:2] == ('Win_3F_Block1_Zone2_South_Win_DesignDayVOF', new)


@pytest.mark.parametrize('kind', ['global variable', 'sensor'])
def test_the_sensor_of_the_design_days_does_not_take_a_name_of_the_model(tmp_path, kind):
    """A global variable of the model named DesignDay stopped EnergyPlus (two EMS variables of one name), and a sensor
    of the model with that name (here, of the outdoor air temperature) was taken for that of the design days, so no
    window was closed (the review of 2026-11-19): the program reads a sensor of its own, DesignDay_2."""
    idf = _input_model(tmp_path, 'vrf2zones')
    if kind == 'sensor':
        idf.newidfobject('EnergyManagementSystem:Sensor', Name='DesignDay',
                         OutputVariable_or_OutputMeter_Index_Key_Name='Environment',
                         OutputVariable_or_OutputMeter_Name='Site Outdoor Air Drybulb Temperature')
    else:
        idf.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name='DesignDay')

    _add(idf)

    assert _program_lines(idf)[0] == 'if DesignDay_2 == 1'
    sensor = idf.getobject('EnergyManagementSystem:Sensor', 'DesignDay_2')
    assert (sensor.OutputVariable_or_OutputMeter_Index_Key_Name, sensor.OutputVariable_or_OutputMeter_Name) == (
        'ACCIS Design Days', 'Schedule Value')
    if kind == 'sensor':
        own = idf.getobject('EnergyManagementSystem:Sensor', 'DesignDay')
        assert own.OutputVariable_or_OutputMeter_Name == 'Site Outdoor Air Drybulb Temperature'


def test_a_zone_list_named_like_a_zone_is_not_taken_for_it(tmp_path):
    """EnergyPlus takes the name of a zone before that of a ZoneList (it warns that the list is a duplicate of the
    zone), and ZoneVentilation:WindandStackOpenArea takes no lists, so the instances keep their names: accim took the
    list, and EnergyPlus stopped ('Actuator ... not found'; the review of 2026-11-19)."""
    idf = _input_model(tmp_path, 'osmresschvent')
    idf.newidfobject('ZoneList', Name='Floor_2_Zone', Zone_1_Name='Floor_1_Zone', Zone_2_Name='Floor_2_Zone')

    instances = windows.ventilation_instances(idf, ['Floor_1_Zone', 'Floor_2_Zone'])

    assert [(i[0], i[2]) for i in instances] == [('Zone Ventilation Wind and Stack Open Area', 'Floor_1_Zone'),
                                                 ('Zone Ventilation Wind and Stack Open Area 1', 'Floor_2_Zone')]


def test_a_model_with_python_plugins_gets_no_program(tmp_path):
    """The example file PythonPluginAirflowNetworkOpeningControlByHumidity opens a window with a Python plugin, which
    EnergyPlus runs before it applies the EMS actuators: an actuator of accim, Null on the other days, released the
    window (its opening differed from that of the plugin by 0.43 on average in three days of July; the review of
    2026-11-19). accim cannot see what the plugins actuate, so the model gets no program, with a warning."""
    idf = _example(tmp_path, 'PythonPluginAirflowNetworkOpeningControlByHumidity.idf')

    _, messages = _add(idf, 'ex_ac')

    assert _program_lines(idf) is None and not _actuators(idf)
    assert any('PythonPlugin:Instance' in m and 'does not close its windows on the design days' in m
               for m in messages)


def test_ex_ac_also_closes_the_windows_of_the_zones_with_thermostats_without_occupants(tmp_path):
    """The existing HVAC systems also condition the zones with thermostats without occupants, and EnergyPlus sizes them
    too: without the People object of Block1:Zone1 of the model with PTACs, its PTAC was still sized with its windows
    open (a design heating load of 237 kW, 2.0 kW with them closed; the review of 2026-11-19)."""
    idf = _input_model(tmp_path, 'exptac')
    idf.removeidfobject(next(p for p in idf.idfobjects['People'] if p.Name == 'People Block1:Zone1'))

    model, _ = _add(idf, 'ex_ac')

    assert [zone.upper() for zone in model.occupied_zones_orig] == ['BLOCK1:ZONE2']
    assert [a[1] for a in _actuators(idf)] == SAMPLE_WINDOWS


def test_the_program_closes_the_windows_on_the_design_days_and_releases_them_on_the_other_days(tmp_path):
    from accim.sim.ems.erl import ErlProgramSet
    from accim.sim.energyplus_api.idf import read_ems

    idf = _input_model(tmp_path, 'vrf2zones')
    _add(idf)
    ems = read_ems(idf)
    erl = ErlProgramSet(ems.programs, global_variables=ems.global_names(), actuators=[a[0] for a in ems.actuators])
    erl.strict = True
    names = [a[0] for a in _actuators(idf)]

    for design_day in (1.0, 0.0, 1.0):
        erl.set('DesignDay', design_day)
        erl.run(PROGRAM)
        values = [erl.value(name) for name in names]
        if design_day:
            assert values == [0.0] * 6
        else:
            assert all(value is not None and value.type == 'Null' for value in values)


def _two_days_of_january(idf):
    run_period = idf.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 1, 8
    run_period.End_Month, run_period.End_Day_of_Month = 1, 9


def _report_the_design_days(idf):
    """Report the schedule of the design days (1 on them), which tells their rows in the outputs: ReadVarsESO sorts
    the rows of all the environments by their dates (the design days of the sample model, 15 January, and 15 July,
    August and September, are not the first rows), and merges those of the same date."""
    idf.newidfobject('Output:Variable', Key_Value='ACCIS Design Days', Variable_Name='Schedule Value',
                     Reporting_Frequency='Hourly')


def _design_day_rows(results):
    [column] = [c for c in results.columns if c.upper().startswith('ACCIS DESIGN DAYS:SCHEDULE VALUE')]
    return results[column] == 1


def _energyplus(version):
    folder = find_energyplus(version, required=False)
    return None if folder is None or not (folder / 'energyplus.exe').exists() else folder / 'energyplus.exe'


def _sizing(eio: Path):
    """The zone sizing lines of an EIO file (zone, heating or cooling, calculated design load in W), and the design
    supply air flow rates of the VRF terminal units (m³/s)."""
    rows = [line.split(',') for line in eio.read_text(errors='replace').splitlines()]
    loads = {(f[1].strip(), f[2].strip()): float(f[3]) for f in rows if f[0] == ' Zone Sizing Information'}
    flows = {f[2].strip(): float(f[4]) for f in rows if f[0] == ' Component Sizing Information'
             and f[3].strip() == 'Design Size Cooling Supply Air Flow Rate [m3/s]'}
    return loads, flows


@pytest.mark.skipif(_energyplus('25.1') is None or not SAMPLE_EPW.exists(),
                    reason='needs EnergyPlus 25.1 and the sample EPW of the repository')
def test_energyplus_sizes_the_vrf_systems_of_the_sample_model_with_the_windows_closed(tmp_path):
    """'vrf_ac' with the defaults of add_accis_to_idf (comfort standard 1, category 1, comfort mode 2), 8-9 January
    in Seville, with the simulation of the design days: the design heating loads of the zones are about 1.9 and 2.2 kW
    (330 and 390 kW with the windows open), the indoor units about 0.64 and 0.82 m³/s (68 and 80), the windows are
    closed in every hour of the design days, and the model opens them on the other days. The backend of the Python API
    gives the same sizing."""
    idf = _input_model(tmp_path, 'vrf2zones')
    _add(idf)
    _two_days_of_january(idf)
    # The design days are also simulated after the sizing, with their outputs
    idf.idfobjects['SimulationControl'][0].Run_Simulation_for_Sizing_Periods = 'Yes'
    idf.newidfobject('Output:Variable', Key_Value='*',
                     Variable_Name='AFN Surface Venting Window or Door Opening Factor', Reporting_Frequency='Hourly')
    _report_the_design_days(idf)
    folder = tmp_path / 'run'
    folder.mkdir()
    idf.saveas(str(folder / 'model.idf'))
    result = subprocess.run([str(_energyplus('25.1')), '-d', str(folder / 'ems'), '-r', '-w', str(SAMPLE_EPW),
                             str(folder / 'model.idf')], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]

    loads, flows = _sizing(folder / 'ems' / 'eplusout.eio')
    for zone in ('BLOCK1:ZONE1', 'BLOCK1:ZONE2'):
        assert 1000 < loads[zone, 'Heating'] < 2500, loads
        assert 2500 < loads[zone, 'Cooling'] < 5000, loads
        assert 0.4 < flows[f'{zone} VRF INDOOR UNIT'] < 1.0, flows
    results = pd.read_csv(folder / 'ems' / 'eplusout.csv')
    factors = results[[c for c in results.columns if 'Opening Factor' in c]]
    design_days = _design_day_rows(results)
    assert factors.shape[1] == 6 and design_days.sum() == 4 * 24
    assert (factors[design_days] == 0).all().all()
    assert (factors[~design_days] > 0).any().all()

    from accim.sim.energyplus_api import run_simulations

    [api] = run_simulations([(folder / 'model.idf', SAMPLE_EPW, {'output_directory': folder / 'api'})], processes=1)
    assert api.error is None
    assert _sizing(next((folder / 'api').glob('*.eio'))) == (loads, flows)


@pytest.mark.skipif(_energyplus('25.1') is None or not SAMPLE_EPW.exists(),
                    reason='needs EnergyPlus 25.1 and the sample EPW of the repository')
def test_energyplus_finds_the_instances_of_the_ventilation_objects_and_closes_them(tmp_path):
    """The model of test_the_instances_of_the_ventilation_objects_are_named_as_energyplus_names_them in 'vrf_ac':
    EnergyPlus finds the actuators of all the instances (it stops with a wrong one), and they are closed on the design
    days (the flow rates of the ventilation of the zones in their hours are 0) and ventilate on the other days."""
    idf = _two_space_variant(_input_model(tmp_path, 'osmresschvent'))
    _add(idf)
    assert [a[1] for a in _actuators(idf)] == TWO_SPACE_INSTANCES
    assert 'Vent_9_SpaceVent_DesignDayFlow' in [a[0] for a in _actuators(idf)]
    idf.newidfobject('Output:EnergyManagementSystem', Actuator_Availability_Dictionary_Reporting='Verbose',
                     Internal_Variable_Availability_Dictionary_Reporting='None',
                     EMS_Runtime_Language_Debug_Output_Level='None')
    _two_days_of_january(idf)
    idf.newidfobject('Output:Variable', Key_Value='*',
                     Variable_Name='Zone Ventilation Current Density Volume Flow Rate', Reporting_Frequency='Hourly')
    _report_the_design_days(idf)
    folder = tmp_path / 'run'
    folder.mkdir()
    idf.saveas(str(folder / 'model.idf'))
    result = subprocess.run([str(_energyplus('25.1')), '-d', str(folder), '-r', '-w', str(SAMPLE_EPW),
                             str(folder / 'model.idf')], capture_output=True, text=True)
    err = (folder / 'eplusout.err').read_text(errors='replace')
    assert result.returncode == 0 and '** Severe  **' not in err, err[-3000:]

    edd = (folder / 'eplusout.edd').read_text(errors='replace')
    available = {m.group(1).strip().upper() for m in re.finditer(
        r'EnergyManagementSystem:Actuator Available,([^,]*),Zone Ventilation,Air Exchange Flow Rate', edd)}
    assert available == {name.upper() for name in TWO_SPACE_INSTANCES}
    loads, _ = _sizing(folder / 'eplusout.eio')
    assert all(load < 2500 for (_, kind), load in loads.items() if kind == 'Heating'), loads
    results = pd.read_csv(folder / 'eplusout.csv')
    flows = results[[c for c in results.columns if 'Ventilation Current Density Volume Flow Rate' in c]]
    design_days = _design_day_rows(results)
    # ReadVarsESO also merges the rows of the design days of the same date (its 7 design days have 2 dates)
    dates = {(int(d.Month), int(d.Day_of_Month)) for d in idf.idfobjects['SizingPeriod:DesignDay']}
    assert flows.shape[1] == 2 and design_days.sum() == len(dates) * 24 == 48
    assert (flows[design_days] == 0).all().all()
    assert (flows[~design_days] > 0).any().all()
