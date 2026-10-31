# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""VRF systems (ScriptType 'vrf_ac' and 'vrf_mm'): one VRF system for each occupied zone."""

from typing import Mapping

from accim.sim.arguments import SUPPLY_AIR_TEMP_INPUT_METHODS
from accim.sim.hvac import vrf_data
from accim.sim.idf_tools import remove_objects
from accim.sim.model import AccimModel

__all__ = [
    'add_base_schedules',
    'add_coil_sensors',
    'add_curves',
    'add_operative_temperature_thermostats',
    'add_setpoint_schedules',
    'add_vrf_objects',
    'add_vrf_schedules',
    'add_vrf_system',
    'check_ventilation',
    'set_pmv_setpoints',
]

_VRF_SCHEDULES = {
    'On 24/7': 'Until: 24:00,1',
    'Control type schedule: Always 4': 'Until: 24:00,4',
    'Relative humidity setpoint schedule: Always 50.00': 'Until: 24:00,50',
    'Heating Fanger comfort setpoint: Always -0.5': 'Until: 24:00,-0.5',
    'Cooling Fanger comfort setpoint: Always  0.1': 'Until: 24:00, 0.1',
    'Zone CO2 setpoint: Always 900ppm': 'Until: 24:00, 900',
    'Min CO2 concentration: Always 600ppm': 'Until: 24:00, 600',
    'Generic contaminant setpoint: Always 0.5ppm': 'Until: 24:00, 0.5',
    'Air distribution effectiveness (always 1)': 'Until: 24:00, 1',
}
_FANGER_SETPOINTS = {
    'Cooling Fanger comfort setpoint: Always 0.5': '0.5',
    'Heating Fanger comfort setpoint: Always -0.5': '-0.5',
}


def _fields(template: Mapping, zone: str = '', **params) -> dict:
    """The fields of an object of vrf_data, for a zone and the arguments."""
    params['zone'] = zone
    fields = {}
    for key, value in template.items():
        if isinstance(value, vrf_data.Param):
            fields[key] = params[value.name]
        elif isinstance(value, str):
            fields[key] = value.replace('{zone}', zone)
        else:
            fields[key] = value
    return fields


def _add_compact_schedule(model: AccimModel, name: str, *fields: str, type_limits: str = 'Any Number') -> None:
    if name in [s.Name for s in model.idf.idfobjects['Schedule:Compact']]:
        model.log(f'{name} Schedule already was in the model')
        return
    numbered = {f'Field_{n}': value for n, value in enumerate(fields, start=1)}
    model.idf.newidfobject('Schedule:Compact', Name=name, Schedule_Type_Limits_Name=type_limits, **numbered)
    model.log(f'{name} Schedule has been added')


def add_operative_temperature_thermostats(model: AccimModel) -> None:
    """Add a ZoneControl:Thermostat:OperativeTemperature object to each zone."""
    for zone in model.zones_orig:
        name = f'{zone} Thermostat'
        if name in [t.Thermostat_Name for t in model.idf.idfobjects['ZoneControl:Thermostat:OperativeTemperature']]:
            model.log(f'{name} already was in the model')
            continue
        model.idf.newidfobject('ZoneControl:Thermostat:OperativeTemperature', Thermostat_Name=name,
                               Radiative_Fraction_Input_Mode='Scheduled', Fixed_Radiative_Fraction='',
                               Radiative_Fraction_Schedule_Name='TypOperativeTempControlSch')
        model.log(f'{name} has been added')


def set_pmv_setpoints(model: AccimModel) -> None:
    """Control the zones with Fanger PMV setpoints (-0.5 and 0.5) instead of operative temperature."""
    idf = model.idf
    remove_objects(idf, 'ZoneControl:Thermostat:OperativeTemperature')
    for name, value in _FANGER_SETPOINTS.items():
        if name in [s.Name for s in idf.idfobjects['Schedule:Compact']]:
            model.log(f'{name} Schedule already was in the model')
            continue
        idf.newidfobject('Schedule:Compact', Name=name, Schedule_Type_Limits_Name='Any Number',
                         Field_1='Through: 12/31', Field_2='For: AllDays', Field_3='Until: 24:00,' + value)
        model.log(f'{name} Schedule has been added')
    for zone in model.zones_orig:
        control = f'{zone} Comfort Control'
        if control in [i.Name for i in idf.idfobjects['ZoneControl:Thermostat:ThermalComfort']]:
            model.log(f'{control} ZoneControl:Thermostat:ThermalComfort already was in the model')
        else:
            idf.newidfobject(
                'ZoneControl:Thermostat:ThermalComfort',
                Name=control,
                Zone_or_ZoneList_Name=zone,
                Averaging_Method='PeopleAverage',
                Minimum_DryBulb_Temperature_Setpoint=12.8,
                Maximum_DryBulb_Temperature_Setpoint=40.0,
                Thermal_Comfort_Control_Type_Schedule_Name='Zone Comfort Control Type Sched',
                Thermal_Comfort_Control_1_Object_Type='ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint',
                Thermal_Comfort_Control_1_Name=f'{zone} Dual Comfort Setpoint',
            )
            model.log(f'{control} ZoneControl:Thermostat:ThermalComfort has been added')
        setpoint = f'{zone} Dual Comfort Setpoint'
        if setpoint in [i.Name for i in idf.idfobjects['ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint']]:
            model.log(f'{setpoint} ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint already was in the model')
        else:
            idf.newidfobject(
                'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint',
                Name=setpoint,
                Fanger_Thermal_Comfort_Heating_Schedule_Name='Heating Fanger comfort setpoint: Always -0.5',
                Fanger_Thermal_Comfort_Cooling_Schedule_Name='Cooling Fanger comfort setpoint: Always 0.5',
            )
            model.log(f'{setpoint} ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint has been added')


def add_base_schedules(model: AccimModel) -> None:
    """Add the schedules 'On' and 'TypOperativeTempControlSch' if they are not in the model."""
    _add_compact_schedule(model, 'On', 'Through: 12/31', 'For: AllDays', 'Until: 24:00,1')
    _add_compact_schedule(model, 'TypOperativeTempControlSch', 'Through: 12/31',
                          'For: SummerDesignDay WinterDesignDay', 'Until: 24:00,0', 'For: AllOtherDays',
                          'Until: 24:00, 0.5', type_limits='Temperature')


def add_vrf_schedules(model: AccimModel) -> None:
    """Add the schedules of the VRF systems (except the setpoint schedules)."""
    for name, until in _VRF_SCHEDULES.items():
        _add_compact_schedule(model, name, 'Through: 12/31', 'For: AllDays', until)
    _add_compact_schedule(model, 'VRF Heating Cooling (Northern Hemisphere)',
                          'Through: 31 Mar', 'For: AllDays', 'Until: 24:00, 0',
                          'Through: 30 Sep', 'For: AllDays', 'Until: 24:00, 1',
                          'Through: 31 Dec', 'For: AllDays', 'Until: 24:00, 0')


def add_curves(model: AccimModel) -> None:
    """Add the performance curves of the VRF systems if they are not in the model."""
    for object_type, fields in vrf_data.CURVES:
        name = fields['Name']
        if name in [c.Name for c in model.idf.idfobjects[object_type]]:
            model.log(f'{name} {object_type} Object already was in the model')
            continue
        model.idf.newidfobject(object_type, **fields)
        model.log(f'{name} {object_type} Object has been added')


def add_vrf_objects(
    model: AccimModel,
    supply_air_temp_input_method: str,
    eer: float = 2,
    cop: float = 2.1,
    vrf_schedule: str = 'On 24/7',
) -> None:
    """Add the outdoor unit, indoor unit, thermostat, sizing and node objects of the VRF system of each zone.

    The objects of these types that the model had are removed, and so are its ZoneHVAC:IdealLoadsAirSystem
    objects, which no zone equipment list refers to once the VRF systems replace them.
    """
    idf = model.idf
    for system in list(idf.idfobjects['ZoneHVAC:IdealLoadsAirSystem']):
        idf.removeidfobject(system)
        model.log(f'{system.Name} ZoneHVAC:IdealLoadsAirSystem Object has been removed')
    params = dict(eer=eer, cop=cop, vrf_schedule=vrf_schedule,
                  supply_air_temp_input_method=SUPPLY_AIR_TEMP_INPUT_METHODS[supply_air_temp_input_method])

    for zone in model.zones_orig:
        name = f'VRF Outdoor Unit_{zone}'
        if name in [i.Heat_Pump_Name for i in idf.idfobjects['AirConditioner:VariableRefrigerantFlow']]:
            model.log(f'{name} AirConditioner:VariableRefrigerantFlow Object already was in the model')
            continue
        # The names of the temperature limits changed in EnergyPlus 22.2
        probe = idf.newidfobject('AirConditioner:VariableRefrigerantFlow')
        condenser_inlet = 'Minimum_Condenser_Inlet_Node_Temperature_in_Cooling_Mode' in probe.fieldnames
        idf.removeidfobject(probe)
        limits = (vrf_data.OUTDOOR_UNIT_CONDENSER_INLET if condenser_inlet
                  else vrf_data.OUTDOOR_UNIT_OUTDOOR_TEMPERATURE)
        idf.newidfobject('AirConditioner:VariableRefrigerantFlow',
                         **_fields(vrf_data.OUTDOOR_UNIT, zone, **params), **limits)
        model.log(f'{name} AirConditioner:VariableRefrigerantFlow Object has been added')

    remove_objects(idf, 'OutdoorAir:NodeList')
    remove_objects(idf, 'ZoneTerminalUnitList')
    for zone in model.zones_orig:
        idf.newidfobject('OutdoorAir:NodeList', **_fields(vrf_data.OUTDOOR_AIR_NODE_LIST, zone))
        model.log(f'VRF Outdoor Unit_{zone} Outdoor Air Node Object has been added')
        idf.newidfobject('ZoneTerminalUnitList', **_fields(vrf_data.ZONE_TERMINAL_UNIT_LIST, zone))
        model.log(f'VRF Outdoor Unit_{zone} Zone List Object has been added')

    per_zone = [
        ('ZoneControl:Thermostat', (vrf_data.THERMOSTAT,), None),
        ('Sizing:Zone', (vrf_data.SIZING_ZONE,), 'Sizing:Zone Object'),
        ('DesignSpecification:OutdoorAir', (vrf_data.DESIGN_SPECIFICATION_OUTDOOR_AIR,),
         'Design Specification Outdoor Air Object'),
        ('DesignSpecification:ZoneAirDistribution', (vrf_data.DESIGN_SPECIFICATION_ZONE_AIR_DISTRIBUTION,),
         'Design Specification Zone Air Distribution Object'),
        ('NodeList', vrf_data.NODE_LISTS, 'Nodelist Objects'),
        ('ZoneHVAC:EquipmentConnections', (vrf_data.EQUIPMENT_CONNECTIONS,), 'ZoneHVAC:EquipmentConnections Objects'),
        ('ZoneHVAC:EquipmentList', (vrf_data.EQUIPMENT_LIST,), 'ZoneHVAC:EquipmentList Objects'),
        ('ZoneHVAC:TerminalUnit:VariableRefrigerantFlow', (vrf_data.TERMINAL_UNIT,),
         'ZoneHVAC:TerminalUnit:VariableRefrigerantFlow Object'),
        ('Coil:Cooling:DX:VariableRefrigerantFlow', (vrf_data.COOLING_COIL,),
         'Coil:Cooling:DX:VariableRefrigerantFlow Object'),
        ('Coil:Heating:DX:VariableRefrigerantFlow', (vrf_data.HEATING_COIL,),
         'Coil:Heating:DX:VariableRefrigerantFlow Object'),
        ('Fan:ConstantVolume', (vrf_data.SUPPLY_FAN,), 'Fan:ConstantVolume Object'),
    ]
    for object_type, templates, message in per_zone:
        remove_objects(idf, object_type)
        for zone in model.zones_orig:
            for template in templates:
                idf.newidfobject(object_type, **_fields(template, zone, **params))
            if message:
                model.log(f'{zone} {message} has been added')


def add_setpoint_schedules(model: AccimModel) -> None:
    """Add the setpoint schedules of each zone (AHST_Sch_<zone>, ACST_Sch_<zone>), which the EMS actuates,
    and the ThermostatSetpoint:DualSetpoint objects that use them (instead of those of the model)."""
    idf = model.idf
    for ems_name in model.ems_names:
        _add_compact_schedule(model, f'AHST_Sch_{ems_name}', 'Through: 12/31', 'For: AllDays', 'Until: 24:00,20')
        _add_compact_schedule(model, f'ACST_Sch_{ems_name}', 'Through: 12/31', 'For: AllDays', 'Until: 24:00,24')
    remove_objects(idf, 'ThermostatSetpoint:DualSetpoint')
    for zone, ems_name in zip(model.ems_zones, model.ems_names):
        idf.newidfobject('ThermostatSetpoint:DualSetpoint', Name=f'{zone} Dual SP',
                         Heating_Setpoint_Temperature_Schedule_Name=f'AHST_Sch_{ems_name}',
                         Cooling_Setpoint_Temperature_Schedule_Name=f'ACST_Sch_{ems_name}')


def check_ventilation(model: AccimModel) -> None:
    """Make the AirflowNetwork windows ('_Win') and doors ('_Door') open with the EMS (mixed mode)."""
    idf = model.idf
    _add_compact_schedule(model, 'Vent_SP_temp', 'Through: 12/31', 'For: AllDays', 'Until: 24:00,24')
    openings = idf.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening']
    surfaces = idf.idfobjects['AirflowNetwork:MultiZone:Surface']
    for window in [w for w in openings if w.Name.endswith('_Win')]:
        window.Height_Factor_for_Opening_Factor_1 = 1
        window.Start_Height_Factor_for_Opening_Factor_1 = 0
        window.Width_Factor_for_Opening_Factor_2 = 1
        window.Height_Factor_for_Opening_Factor_2 = 1
        window.Start_Height_Factor_for_Opening_Factor_2 = 0
    for surface in [s for s in surfaces if s.Surface_Name.endswith('_Win')]:
        surface.Ventilation_Control_Mode = 'Temperature'
        surface.Ventilation_Control_Zone_Temperature_Setpoint_Schedule_Name = 'Vent_SP_temp'
        surface.Venting_Availability_Schedule_Name = 'On'
    # The internal doors are always open
    for door in [d for d in openings if d.Name.endswith('_Door')]:
        door.Width_Factor_for_Opening_Factor_2 = 1
    for surface in [s for s in surfaces if s.Surface_Name.endswith('_Door')]:
        surface.Venting_Availability_Schedule_Name = 'On'


def _add_sensor(model: AccimModel, sensors: list, name: str, key: str, variable: str) -> None:
    if name in sensors:
        model.log(f'Not added - {name} Sensor')
        return
    model.idf.newidfobject('EnergyManagementSystem:Sensor', Name=name,
                           OutputVariable_or_OutputMeter_Index_Key_Name=key,
                           OutputVariable_or_OutputMeter_Name=variable)
    model.log(f'Added - {name} Sensor')


def add_coil_sensors(model: AccimModel) -> None:
    """Add the EMS sensors of the cooling and heating coils of the VRF system of each zone (and window)."""
    sensors = [s.Name for s in model.idf.idfobjects['EnergyManagementSystem:Sensor']]
    for ems_name, zone in zip(model.ems_names, model.ems_zones):
        _add_sensor(model, sensors, f'{ems_name}_CoolCoil', f'{zone} VRF Indoor Unit DX Cooling Coil',
                    'Cooling Coil Total Cooling Rate')
        _add_sensor(model, sensors, f'{ems_name}_HeatCoil', f'{zone} VRF Indoor Unit DX Heating Coil',
                    'Heating Coil Heating Rate')
    if model.script_type == 'vrf_mm':
        for window, zone in zip(model.windows, model.window_zones):
            _add_sensor(model, sensors, f'{window}_CoolCoil', f'{zone} VRF Indoor Unit DX Cooling Coil',
                        'Cooling Coil Total Cooling Rate')
            _add_sensor(model, sensors, f'{window}_HeatCoil', f'{zone} VRF Indoor Unit DX Heating Coil',
                        'Heating Coil Heating Rate')


def add_vrf_system(
    model: AccimModel,
    supply_air_temp_input_method: str = 'supply air temperature',
    eer: float = 2,
    cop: float = 2.1,
    vrf_schedule: str = 'On 24/7',
) -> None:
    """Add a VRF system to each zone, with operative temperature or PMV thermostats (``model.temp_ctrl``)."""
    if model.temp_ctrl == 'pmv':
        set_pmv_setpoints(model)
    else:
        add_operative_temperature_thermostats(model)
    add_base_schedules(model)
    add_vrf_schedules(model)
    add_curves(model)
    add_vrf_objects(model, supply_air_temp_input_method, eer=eer, cop=cop, vrf_schedule=vrf_schedule)
