"""Tests for the existing HVAC systems (ScriptType 'ex_ac' and 'ex_mm'): the thermostats that control the operative
temperature of the occupied zones, their availability, their outdoor temperature limits and the backup ideal loads air
systems (the arguments ``existing_hvac_*``), and the values of the schedules.

The adaptive setpoints are setpoints of the operative temperature, but the thermostats of EnergyPlus control the air
temperature unless a ZoneControl:Thermostat:OperativeTemperature object makes them control the operative temperature,
as accim does with the thermostats of its VRF systems. Until 2026-11-02, the existing thermostats kept controlling the
air temperature, and accim only gave the setpoints to the setpoint object of their first control: with the thermostats
of the example files of EnergyPlus (a single cooling, a single heating and a dual setpoint object, shared by all the
zones), the zones kept the setpoints of the model, and EnergyPlus stopped (the setpoint schedules of the EMS were
missing). In a year in Seville, the sample OSM office (air temperature thermostats, HVAC off from 19 to 23 h while
occupied) had 53 to 77 % of its occupied hours within the setpoints; with operative temperature control, 86 to 93 %;
and also always available, 100 %. The sample models of DesignBuilder already controlled the operative temperature
(without it, 31 to 79 %). The backup ideal loads air systems supply what the existing HVAC systems cannot (the cooling
of the model with radiators, the limits of the VAV terminals of the example file 5ZoneAirCooled...).
"""
import lzma
import subprocess
import warnings
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim.hvac import existing
from accim.sim.hvac.schedules import is_always_on, schedule_values
from accim.sim.idf_tools import idf_text

REPO = Path(__file__).resolve().parents[2]
INPUTS = REPO / 'tests' / 'core' / 'golden_master' / 'inputs'
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
ARGUMENTS = dict(output_type='simplified', output_frequencies=['hourly'], keep_existing_outputs=False,
                 setpoint_type='temperature', verbose=False)
OPERATIVE_TEMPERATURE = 'ZoneControl:Thermostat:OperativeTemperature'

pytestmark = pytest.mark.skipif(not (IDD_25_1.exists() and INPUTS.exists()),
                                reason='needs EnergyPlus 25.1 and the input models of the golden master')


def _model(tmp_path, name):
    """An input model of the golden master (EnergyPlus 25.1): 'exptac' (PTACs), 'exrad' (electric radiators),
    'exbeams' (cooled beams and convectors) or 'osmofficeex' (the OSM small office, with packaged heat pumps)."""
    from besos.eppy_funcs import get_building

    path = tmp_path / f'{name}.idf'
    path.write_bytes(lzma.decompress((INPUTS / f'{name}.idf.xz').read_bytes()))
    return get_building(str(path))


def _add(idf, script_type='ex_ac', **kwargs):
    """add_accis_to_idf; return the model and the messages of its UserWarnings."""
    from accim.sim.accis import add_accis_to_idf

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model = add_accis_to_idf(idf, script_type=script_type, **ARGUMENTS, **kwargs)
    return model, [str(w.message) for w in caught if w.category is UserWarning]


def _by_name(idf, object_type, name):
    return next(o for o in idf.idfobjects[object_type] if o.obj[1].upper() == name.upper())


def _example_file_thermostats(idf):
    """Thermostats as in the example files of EnergyPlus: three controls whose setpoint objects all the zones share,
    a control type schedule with heating only until March, and no operative temperature control."""
    for control in list(idf.idfobjects[OPERATIVE_TEMPERATURE]):
        idf.removeidfobject(control)
    idf.newidfobject('Schedule:Compact', Name='Zone Control Type Sched', Schedule_Type_Limits_Name='Any Number',
                     Field_1='Through: 3/31', Field_2='For: AllDays', Field_3='Until: 24:00,1',
                     Field_4='Through: 12/31', Field_5='For: AllDays', Field_6='Until: 24:00,4')
    heating, cooling = 'Block1:Zone1 Heating Setpoint Schedule', 'Block1:Zone1 Cooling Setpoint Schedule'
    idf.newidfobject('ThermostatSetpoint:SingleCooling', Name='CoolingSetPoint',
                     Setpoint_Temperature_Schedule_Name=cooling)
    idf.newidfobject('ThermostatSetpoint:SingleHeating', Name='HeatingSetPoint',
                     Setpoint_Temperature_Schedule_Name=heating)
    idf.newidfobject('ThermostatSetpoint:DualSetpoint', Name='DualSetPoint',
                     Heating_Setpoint_Temperature_Schedule_Name=heating,
                     Cooling_Setpoint_Temperature_Schedule_Name=cooling)
    controls = (('ThermostatSetpoint:SingleCooling', 'CoolingSetPoint'),
                ('ThermostatSetpoint:SingleHeating', 'HeatingSetPoint'),
                ('ThermostatSetpoint:DualSetpoint', 'DualSetPoint'))
    for thermostat in idf.idfobjects['ZoneControl:Thermostat']:
        thermostat.Control_Type_Schedule_Name = 'Zone Control Type Sched'
        for number, (object_type, name) in enumerate(controls, start=1):
            setattr(thermostat, f'Control_{number}_Object_Type', object_type)
            setattr(thermostat, f'Control_{number}_Name', name)
    return idf


# ----------------------------------------------------------------------------------------------------------
# Values of the schedules
# ----------------------------------------------------------------------------------------------------------

def test_the_values_of_the_schedules_leave_out_the_design_days(tmp_path):
    idf = _model(tmp_path, 'osmofficeex')
    idf.newidfobject('Schedule:Compact', Name='Off on the design days', Schedule_Type_Limits_Name='Any Number',
                     Field_1='Through: 12/31', Field_2='For: SummerDesignDay WinterDesignDay', Field_3='Until: 24:00,0',
                     Field_4='For: AllOtherDays', Field_5='Until: 24:00, 1')
    idf.newidfobject('Schedule:Compact', Name='Off at night', Schedule_Type_Limits_Name='Any Number',
                     Field_1='Through: 12/31', Field_2='For: AllDays', Field_3='Until: 7:00', Field_4='0',
                     Field_5='Until: 24:00', Field_6='1')
    idf.newidfobject('Schedule:Constant', Name='Zero', Hourly_Value=0)

    assert schedule_values(idf, 'Off on the design days') == {1.0}
    assert is_always_on(idf, 'Off on the design days') is True
    assert schedule_values(idf, 'off at night') == {0.0, 1.0}
    assert is_always_on(idf, 'Off at night') is False
    assert is_always_on(idf, 'Zero') is False
    # Schedule:Year, Schedule:Week:Daily and Schedule:Day:Interval objects: the HVAC system of the office is off at
    # night and on Sundays
    assert is_always_on(idf, 'OfficeSmall HVACOperationSchd') is False
    assert is_always_on(idf, 'Always On Discrete') is True
    # No schedule is always on; a schedule that is not in the model cannot be read
    assert is_always_on(idf, '') is True
    assert schedule_values(idf, 'Not a schedule') is None
    assert is_always_on(idf, 'Not a schedule') is None


# ----------------------------------------------------------------------------------------------------------
# Thermostats (existing_hvac_operative_temperature_control)
# ----------------------------------------------------------------------------------------------------------

def test_the_thermostat_of_each_occupied_zone_controls_its_operative_temperature_at_all_times(tmp_path):
    idf = _example_file_thermostats(_model(tmp_path, 'exptac'))

    _add(idf)

    duals = set()
    for thermostat in idf.idfobjects['ZoneControl:Thermostat']:
        ems_name = thermostat.Zone_or_ZoneList_Name.replace(':', '_')
        assert thermostat.Control_Type_Schedule_Name == 'Control type schedule: Always 4'
        assert [field for field in thermostat.obj[4:12] if field] == ['ThermostatSetpoint:DualSetpoint',
                                                                      thermostat.Control_1_Name]
        dual = _by_name(idf, 'ThermostatSetpoint:DualSetpoint', thermostat.Control_1_Name)
        assert dual.Heating_Setpoint_Temperature_Schedule_Name == f'AHST_Sch_{ems_name}'
        assert dual.Cooling_Setpoint_Temperature_Schedule_Name == f'ACST_Sch_{ems_name}'
        duals.add(dual.Name)
        control = _by_name(idf, OPERATIVE_TEMPERATURE, thermostat.Name)
        assert control.Radiative_Fraction_Input_Mode == 'Scheduled'
        assert control.Radiative_Fraction_Schedule_Name == 'TypOperativeTempControlSch'
    # Each zone has its own setpoint object, and those that the zones shared do not change
    assert len(duals) == 2
    assert _by_name(idf, 'ThermostatSetpoint:SingleCooling', 'CoolingSetPoint').Setpoint_Temperature_Schedule_Name \
        == 'Block1:Zone1 Cooling Setpoint Schedule'
    assert _by_name(idf, 'ThermostatSetpoint:SingleHeating', 'HeatingSetPoint').Setpoint_Temperature_Schedule_Name \
        == 'Block1:Zone1 Heating Setpoint Schedule'
    assert schedule_values(idf, 'Control type schedule: Always 4') == {4.0}


@pytest.mark.parametrize('name', ['exptac', 'exrad', 'exbeams'])
def test_the_models_whose_thermostats_already_control_the_operative_temperature_do_not_change(tmp_path, name):
    texts = []
    for control in (True, False):
        idf = _model(tmp_path, name)
        _add(idf, script_type='ex_mm', existing_hvac_operative_temperature_control=control)
        texts.append(idf_text(idf))

    assert texts[0] == texts[1]


def test_without_operative_temperature_control_the_thermostats_of_the_model_do_not_change(tmp_path):
    idf = _example_file_thermostats(_model(tmp_path, 'exptac'))

    _add(idf, existing_hvac_operative_temperature_control=False)

    assert not idf.idfobjects[OPERATIVE_TEMPERATURE]
    for thermostat in idf.idfobjects['ZoneControl:Thermostat']:
        assert thermostat.Control_Type_Schedule_Name == 'Zone Control Type Sched'
        assert (thermostat.Control_1_Name, thermostat.Control_2_Name, thermostat.Control_3_Name) == (
            'CoolingSetPoint', 'HeatingSetPoint', 'DualSetPoint')


def test_an_adaptive_comfort_model_of_energyplus_is_removed_from_the_operative_temperature_thermostats(tmp_path):
    idf = _model(tmp_path, 'exptac')
    for control in idf.idfobjects[OPERATIVE_TEMPERATURE]:
        control.Adaptive_Comfort_Model_Type = 'AdaptiveCEN15251CentralLine'

    _add(idf)

    assert {control.Adaptive_Comfort_Model_Type for control in idf.idfobjects[OPERATIVE_TEMPERATURE]} == {'None'}


def test_a_thermostat_of_a_zone_list_with_occupied_zones_is_rejected(tmp_path):
    idf = _model(tmp_path, 'exptac')
    thermostats = list(idf.idfobjects['ZoneControl:Thermostat'])
    idf.newidfobject('ZoneList', Name='Both zones', Zone_1_Name='Block1:Zone1', Zone_2_Name='Block1:Zone2')
    thermostats[0].Zone_or_ZoneList_Name = 'Both zones'
    idf.removeidfobject(thermostats[1])

    with pytest.raises(ValueError, match='ZoneList Both zones'):
        _add(idf)


def test_the_occupied_zones_without_a_thermostat_get_their_setpoint_schedules_and_a_warning(tmp_path):
    idf = _model(tmp_path, 'exptac')
    idf.removeidfobject(_by_name(idf, 'ZoneControl:Thermostat', 'Block1:Zone2 Thermostat'))
    idf.removeidfobject(next(c for c in idf.idfobjects[OPERATIVE_TEMPERATURE]
                             if c.Thermostat_Name == 'Block1:Zone2 Thermostat'))

    _, messages = _add(idf)

    assert any("['Block1:Zone2']" in m and 'have no thermostat' in m for m in messages)
    # The EMS actuates them
    assert {'AHST_Sch_Block1_Zone2', 'ACST_Sch_Block1_Zone2'} <= {s.Name for s in idf.idfobjects['Schedule:Compact']}


# ----------------------------------------------------------------------------------------------------------
# Availability (existing_hvac_availability_schedule)
# ----------------------------------------------------------------------------------------------------------

def test_the_availability_of_the_existing_hvac_systems_is_kept_with_a_warning(tmp_path):
    idf = _model(tmp_path, 'osmofficeex')

    _, messages = _add(idf)

    message = next(m for m in messages if 'may be unavailable at times' in m)
    assert "'OfficeSmall HVACOperationSchd'" in message
    assert 'AvailabilityManager:NightCycle' in message
    assert "existing_hvac_availability_schedule='On 24/7'" in message
    assert {u.Availability_Schedule_Name for u in idf.idfobjects['AirLoopHVAC:UnitarySystem']} == {
        'OfficeSmall HVACOperationSchd'}


def test_existing_hvac_availability_schedule_makes_them_available(tmp_path):
    idf = _model(tmp_path, 'osmofficeex')

    model, messages = _add(idf, existing_hvac_availability_schedule='On 24/7')

    assert not [m for m in messages if 'unavailable' in m]
    assert existing.availability_warning(model) is None
    assert {u.Availability_Schedule_Name for u in idf.idfobjects['AirLoopHVAC:UnitarySystem']} == {'On 24/7'}
    assert {f.Availability_Schedule_Name for f in idf.idfobjects['Fan:OnOff']} == {'On 24/7'}
    assert {loop.Availability_Manager_List_Name for loop in idf.idfobjects['AirLoopHVAC']} == {
        existing.AVAILABILITY_MANAGER_LIST}
    manager = _by_name(idf, 'AvailabilityManager:Scheduled', existing.AVAILABILITY_MANAGER)
    assert manager.Schedule_Name == 'On 24/7'
    assert is_always_on(idf, 'On 24/7') is True


def test_existing_hvac_availability_schedule_must_be_a_schedule_of_the_model(tmp_path):
    with pytest.raises(ValueError, match='is not a schedule of the model'):
        _add(_model(tmp_path, 'osmofficeex'), existing_hvac_availability_schedule='Not a schedule')
    with pytest.raises(ValueError, match='must be None or the name of a schedule'):
        _add(_model(tmp_path, 'osmofficeex'), existing_hvac_availability_schedule=True)


def test_the_plant_operation_schemes_with_one_scheme_follow_the_availability(tmp_path):
    def schemes(idf):
        idf.newidfobject('Schedule:Compact', Name='Summer only', Schedule_Type_Limits_Name='Any Number',
                         Field_1='Through: 4/30', Field_2='For: AllDays', Field_3='Until: 24:00,0',
                         Field_4='Through: 9/30', Field_5='For: AllDays', Field_6='Until: 24:00,1',
                         Field_7='Through: 12/31', Field_8='For: AllDays', Field_9='Until: 24:00,0')
        one = idf.newidfobject('PlantEquipmentOperationSchemes', Name='Chiller in summer',
                               Control_Scheme_1_Object_Type='PlantEquipmentOperation:CoolingLoad',
                               Control_Scheme_1_Name='Chiller', Control_Scheme_1_Schedule_Name='Summer only')
        # EnergyPlus uses the first scheme whose schedule is on
        two = idf.newidfobject('PlantEquipmentOperationSchemes', Name='Two chillers',
                               Control_Scheme_1_Object_Type='PlantEquipmentOperation:CoolingLoad',
                               Control_Scheme_1_Name='Chiller A', Control_Scheme_1_Schedule_Name='Summer only',
                               Control_Scheme_2_Object_Type='PlantEquipmentOperation:CoolingLoad',
                               Control_Scheme_2_Name='Chiller B', Control_Scheme_2_Schedule_Name='On 24/7')
        return one, two

    idf = _model(tmp_path, 'exptac')
    schemes(idf)
    _, messages = _add(idf)
    assert any("'Summer only'" in m and 'may be unavailable' in m for m in messages)

    idf = _model(tmp_path, 'exptac')
    one, two = schemes(idf)
    _add(idf, existing_hvac_availability_schedule='On 24/7')
    assert one.Control_Scheme_1_Schedule_Name == 'On 24/7'
    assert (two.Control_Scheme_1_Schedule_Name, two.Control_Scheme_2_Schedule_Name) == ('Summer only', 'On 24/7')


def test_the_hvac_objects_with_setpoint_schedules_of_their_own_get_a_warning(tmp_path):
    idf = _model(tmp_path, 'exptac')
    idf.newidfobject('ZoneHVAC:LowTemperatureRadiant:Electric', Name='Radiant floor', Zone_Name='Block1:Zone1')
    # The cooling panels with the control type of the load of the zone follow its thermostat
    idf.newidfobject('ZoneHVAC:CoolingPanel:RadiantConvective:Water', Name='Panel', Control_Type='ZoneTotalLoad')

    _, messages = _add(idf)

    message = next(m for m in messages if 'setpoint schedules of their own' in m)
    assert "'ZoneHVAC:LowTemperatureRadiant:Electric Radiant floor'" in message
    assert 'Panel' not in message
    assert 'AHST_Sch_<zone>' in message


def test_no_warnings_for_the_hvac_systems_that_are_always_available_and_without_limits(tmp_path):
    _, messages = _add(_model(tmp_path, 'exptac'))

    assert not [m for m in messages if 'existing HVAC systems' in m]


# ----------------------------------------------------------------------------------------------------------
# Outdoor temperature limits (existing_hvac_widen_outdoor_temperature_limits)
# ----------------------------------------------------------------------------------------------------------

def test_the_outdoor_temperature_limits_are_kept_with_a_warning_or_widened(tmp_path):
    idf = _model(tmp_path, 'osmofficeex')
    _, messages = _add(idf)
    message = next(m for m in messages if 'outdoor temperature limits' in m)
    # The heat pumps do not heat below -12.2 C, and their gas heaters do not heat above 4.4 C (ASHRAE 90.1)
    assert ("'Minimum Outdoor Dry-Bulb Temperature for Compressor Operation -12.2 C "
            "(5 Coil:Heating:DX:SingleSpeed)'") in message
    assert ("'Maximum Outdoor Dry-Bulb Temperature for Supplemental Heater Operation 4.44444 C "
            "(5 AirLoopHVAC:UnitarySystem)'") in message

    idf = _model(tmp_path, 'osmofficeex')
    _, messages = _add(idf, existing_hvac_widen_outdoor_temperature_limits=True)

    assert not [m for m in messages if 'outdoor temperature limits' in m]
    assert {c.Minimum_Outdoor_DryBulb_Temperature_for_Compressor_Operation
            for c in idf.idfobjects['Coil:Heating:DX:SingleSpeed']} == {-20}
    assert {u.Maximum_Outdoor_DryBulb_Temperature_for_Supplemental_Heater_Operation
            for u in idf.idfobjects['AirLoopHVAC:UnitarySystem']} == {80}


def test_the_widened_limits_respect_the_bounds_of_the_idd_and_the_wider_limits(tmp_path):
    idf = _model(tmp_path, 'exptac')
    supplemental = 'Maximum_Outdoor_DryBulb_Temperature_for_Supplemental_Heater_Operation'
    heat_pump = idf.newidfobject('ZoneHVAC:PackagedTerminalHeatPump', Name='Heat pump', **{supplemental: 4.44})
    # The defaults of EnergyPlus: cooling from -6 to 43 C, heating from -20 to 16 C
    vrf = idf.newidfobject('AirConditioner:VariableRefrigerantFlow', Heat_Pump_Name='VRF')
    coil = idf.newidfobject('Coil:Cooling:DX:SingleSpeed', Name='Coil')

    existing.widen_outdoor_temperature_limits(SimpleNamespace(idf=idf, log=lambda *lines: None))

    # The IDD limits it to 21 C
    assert getattr(heat_pump, supplemental) == 21
    limits = [f'{bound}_Condenser_Inlet_Node_Temperature_in_{mode}_Mode'
              for mode in ('Cooling', 'Heating') for bound in ('Minimum', 'Maximum')]
    assert [getattr(vrf, field) for field in limits] == [-20, 80, -20, 80]
    # The limits of the heat recovery mode, the defrost and the crankcase heaters do not change
    assert vrf.Minimum_Condenser_Inlet_Node_Temperature_in_Heat_Recovery_Mode == ''
    assert vrf.Maximum_Outdoor_Drybulb_Temperature_for_Defrost_Operation == 5
    # -25 C is wider than -20 C
    assert coil.Minimum_Outdoor_DryBulb_Temperature_for_Compressor_Operation == -25


# ----------------------------------------------------------------------------------------------------------
# Backup ideal loads air systems (existing_hvac_ideal_loads_backup)
# ----------------------------------------------------------------------------------------------------------

def _connections(idf, zone):
    return next(c for c in idf.idfobjects['ZoneHVAC:EquipmentConnections'] if c.Zone_Name == zone)


def _nodes(idf, name):
    """The nodes of a node or NodeList name."""
    nodes = next((n for n in idf.idfobjects['NodeList'] if n.Name.upper() == name.upper()), None)
    return [name] if nodes is None else [str(node) for node in nodes.obj[2:] if str(node)]


def test_the_backup_ideal_loads_air_systems_are_the_last_equipment_of_each_occupied_zone(tmp_path):
    idf = _model(tmp_path, 'exptac')

    model, _ = _add(idf, existing_hvac_ideal_loads_backup=True)

    assert sorted(model.ideal_loads_backups) == ['Block1:Zone1 ACCIS Backup Ideal Loads',
                                                 'Block1:Zone2 ACCIS Backup Ideal Loads']
    for zone in ('Block1:Zone1', 'Block1:Zone2'):
        name = f'{zone} ACCIS Backup Ideal Loads'
        connections = _connections(idf, zone)
        equipment = _by_name(idf, 'ZoneHVAC:EquipmentList', connections.Zone_Conditioning_Equipment_List_Name)
        assert equipment.Load_Distribution_Scheme == 'SequentialLoad'
        assert equipment.Zone_Equipment_1_Object_Type == 'ZoneHVAC:PackagedTerminalAirConditioner'
        assert (equipment.Zone_Equipment_2_Object_Type, equipment.Zone_Equipment_2_Name,
                equipment.Zone_Equipment_2_Cooling_Sequence, equipment.Zone_Equipment_2_Heating_or_NoLoad_Sequence) == (
            'ZoneHVAC:IdealLoadsAirSystem', name, 2, 2)
        backup = _by_name(idf, 'ZoneHVAC:IdealLoadsAirSystem', name)
        assert _nodes(idf, connections.Zone_Air_Inlet_Node_or_NodeList_Name) == [
            f'{zone} PTAC Supply Outlet', backup.Zone_Supply_Air_Node_Name]
        assert _nodes(idf, connections.Zone_Air_Exhaust_Node_or_NodeList_Name) == [
            f'{zone} PTAC Return', backup.Zone_Exhaust_Air_Node_Name]
        assert (backup.Heating_Limit, backup.Cooling_Limit, backup.Dehumidification_Control_Type) == (
            'NoLimit', 'NoLimit', 'None')
        outputs = {o.Variable_Name for o in idf.idfobjects['Output:Variable'] if o.Key_Value == name}
        assert outputs == {'Zone Ideal Loads Zone Sensible Heating Rate', 'Zone Ideal Loads Zone Sensible Cooling Rate'}


def test_the_backup_adds_its_nodes_to_those_of_the_zone_and_distributes_the_load_sequentially(tmp_path):
    idf = _model(tmp_path, 'exptac')
    connections = _connections(idf, 'Block1:Zone1')
    # A single inlet node instead of a NodeList, and the load distributed uniformly
    connections.Zone_Air_Inlet_Node_or_NodeList_Name = 'Block1:Zone1 PTAC Supply Outlet'
    equipment = _by_name(idf, 'ZoneHVAC:EquipmentList', connections.Zone_Conditioning_Equipment_List_Name)
    equipment.Load_Distribution_Scheme = 'UniformLoad'

    _add(idf, existing_hvac_ideal_loads_backup=True)

    assert connections.Zone_Air_Inlet_Node_or_NodeList_Name == 'Block1:Zone1 ACCIS Inlet Nodes'
    assert _nodes(idf, 'Block1:Zone1 ACCIS Inlet Nodes') == [
        'Block1:Zone1 PTAC Supply Outlet', 'Block1:Zone1 ACCIS Backup Ideal Loads Supply Inlet']
    assert equipment.Load_Distribution_Scheme == 'SequentialLoad'


def test_no_backup_for_the_occupied_zones_without_zone_hvac_equipment(tmp_path):
    idf = _model(tmp_path, 'exrad')
    idf.removeidfobject(_connections(idf, 'Block1:Zone2'))

    model, messages = _add(idf, existing_hvac_ideal_loads_backup=True)

    assert model.ideal_loads_backups == ['Block1:Zone1 ACCIS Backup Ideal Loads']
    assert any("['Block1:Zone2']" in m and 'no zone HVAC equipment' in m for m in messages)
    # The radiators have no inlet and exhaust nodes: those of the backup are the nodes of the zone
    connections = _connections(idf, 'Block1:Zone1')
    assert connections.Zone_Air_Inlet_Node_or_NodeList_Name == 'Block1:Zone1 ACCIS Backup Ideal Loads Supply Inlet'
    assert connections.Zone_Air_Exhaust_Node_or_NodeList_Name == 'Block1:Zone1 ACCIS Backup Ideal Loads Exhaust Outlet'


def _energyplus_25_1():
    folder = find_energyplus('25.1', required=False)
    return None if folder is None or not (folder / 'energyplus.exe').exists() else folder / 'energyplus.exe'


@pytest.mark.skipif(_energyplus_25_1() is None or not SAMPLE_EPW.exists(),
                    reason='needs EnergyPlus 25.1 and the sample EPW of the repository')
def test_the_backup_keeps_the_operative_temperature_of_a_zone_without_cooling_equipment_below_its_setpoint(tmp_path):
    """The model with electric radiators, three days of July in Seville: without cooling equipment, the operative
    temperature is far above the cooling setpoint; with the backup, it is not."""
    from accim.sim.accis import add_accis_to_idf

    exceedances = {}
    for backup in (False, True):
        idf = _model(tmp_path, 'exrad')
        add_accis_to_idf(idf, script_type='ex_ac', output_type='standard', output_frequencies=['hourly'],
                         keep_existing_outputs=False, setpoint_type='temperature', verbose=False,
                         existing_hvac_ideal_loads_backup=backup)
        run_period = idf.idfobjects['RunPeriod'][0]
        run_period.Begin_Month, run_period.Begin_Day_of_Month, run_period.End_Month, run_period.End_Day_of_Month = (
            7, 1, 7, 3)
        folder = tmp_path / f'backup_{backup}'
        folder.mkdir()
        idf.saveas(str(folder / 'model.idf'))
        result = subprocess.run([str(_energyplus_25_1()), '-d', str(folder), '-p', 'run', '-s', 'C', '-r',
                                 '-w', str(SAMPLE_EPW), str(folder / 'model.idf')], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout[-3000:]
        errors = (folder / 'run.err').read_text(errors='replace')
        assert '** Severe  **' not in errors
        results = pd.read_csv(folder / 'run.csv')
        for zone, ems_name in (('BLOCK1:ZONE1', 'Block1_Zone1'), ('BLOCK1:ZONE2', 'Block1_Zone2')):
            occupied = results[f'EMS:Occupied Hours_{ems_name} [H](Hourly)'] > 0
            operative = results[f'{zone}:Zone Operative Temperature [C](Hourly)']
            setpoint = results[f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{ems_name} [C](Hourly)']
            exceedances[backup, zone] = (operative - setpoint)[occupied].max()
        if backup:
            cooling = [c for c in results.columns
                       if 'ACCIS BACKUP IDEAL LOADS:Zone Ideal Loads Zone Sensible Cooling' in c]
            assert len(cooling) == 2 and all(results[c].max() > 0 for c in cooling)

    for zone in ('BLOCK1:ZONE1', 'BLOCK1:ZONE2'):
        assert exceedances[False, zone] > 2
        assert exceedances[True, zone] < 0.2
