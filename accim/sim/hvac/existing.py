# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Existing HVAC systems (ScriptType 'ex_ac' and 'ex_mm'): their setpoint schedules and coil sensors."""

from typing import List

from accim.sim.hvac.resolver import resolve_hvac_zone_map
from accim.sim.model import AccimModel, ExistingHvacGroup

__all__ = [
    'EXISTING_HVAC_OUTPUTS',
    'add_coil_initialisation',
    'add_coil_sensors',
    'add_setpoint_schedules',
    'scan_existing_hvac',
]

#: Supported equipment of the existing HVAC systems, and the output that tells whether it is
#: heating or cooling. Other equipment, such as low temperature radiant systems, ventilated slabs
#: and the other air terminal units, is not supported.
EXISTING_HVAC_OUTPUTS = {
    # Heating and cooling coils
    'Coil:Cooling:Water': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:Water:DetailedGeometry': 'Cooling Coil Total Cooling Rate',
    'CoilSystem:Cooling:Water': 'Coil System Water Total Cooling Rate',
    'Coil:Heating:Water': 'Heating Coil Heating Energy',
    'Coil:Heating:Steam': 'Heating Coil Heating Energy',
    'Coil:Heating:Electric': 'Heating Coil Heating Energy',
    'Coil:Heating:Electric:MultiStage': 'Heating Coil Heating Energy',
    'Coil:Heating:Desuperheater': 'Heating Coil Heating Energy',
    'Coil:Cooling:DX:VariableRefrigerantFlow': 'Cooling Coil Total Cooling Rate',
    'Coil:Heating:DX:VariableRefrigerantFlow': 'Heating Coil Heating Energy',
    'Coil:Cooling:DX:VariableRefrigerantFlow:FluidTemperatureControl': 'Cooling Coil Total Cooling Rate',
    'Coil:Heating:DX:VariableRefrigerantFlow:FluidTemperatureControl': 'Heating Coil Heating Energy',
    'Coil:Heating:Fuel': 'Heating Coil Heating Energy',
    'Coil:Heating:Gas:MultiStage': 'Heating Coil Heating Energy',
    'Coil:Cooling:DX:SingleSpeed': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:DX:TwoSpeed': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:DX:TwoStageWithHumidityControlMode': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:DX:MultiSpeed': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:DX:VariableSpeed': 'Cooling Coil Total Cooling Rate',
    'Coil:Heating:DX:SingleSpeed': 'Heating Coil Heating Energy',
    'Coil:Heating:DX:MultiSpeed': 'Heating Coil Heating Energy',
    'Coil:Heating:DX:VariableSpeed': 'Heating Coil Heating Energy',
    'Coil:WaterHeating:Desuperheater': 'Water Heater Heating Energy',
    'Coil:Cooling:WaterToAirHeatPump:ParameterEstimation': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:WaterToAirHeatPump:EquationFit': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:WaterToAirHeatPump:VariableSpeedEquationFit': 'Cooling Coil Total Cooling Rate',
    'Coil:Heating:WaterToAirHeatPump:ParameterEstimation': 'Heating Coil Heating Energy',
    'Coil:Heating:WaterToAirHeatPump:EquationFit': 'Heating Coil Heating Energy',
    'Coil:Heating:WaterToAirHeatPump:VariableSpeedEquationFit': 'Heating Coil Heating Energy',
    'Coil:Cooling:DX:SingleSpeed:ThermalStorage': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:DX': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:DX:CurveFit:Performance': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:DX:CurveFit:OperatingMode': 'Cooling Coil Total Cooling Rate',
    'Coil:Cooling:DX:CurveFit:Speed': 'Cooling Coil Total Cooling Rate',
    # Radiative and convective units
    'ZoneHVAC:Baseboard:RadiantConvective:Water': 'Baseboard Total Heating Rate',
    'ZoneHVAC:Baseboard:RadiantConvective:Steam': 'Baseboard Total Heating Rate',
    'ZoneHVAC:Baseboard:RadiantConvective:Electric': 'Baseboard Total Heating Rate',
    'ZoneHVAC:CoolingPanel:RadiantConvective:Water': 'Cooling Panel Total Cooling Rate',
    'ZoneHVAC:Baseboard:Convective:Water': 'Baseboard Total Heating Rate',
    'ZoneHVAC:Baseboard:Convective:Electric': 'Baseboard Total Heating Rate',
    # Air terminal units
    'AirTerminal:SingleDuct:ConstantVolume:CooledBeam': 'Zone Air Terminal Beam Chilled Water Energy',
}


def scan_existing_hvac(model: AccimModel) -> None:
    """Find the existing HVAC equipment of the model and the zones it serves (ScriptType 'ex_mm').

    Sets ``model.not_working`` if some equipment serves a zone that accim does not control.
    """
    idf = model.idf
    for hvac_type, output in EXISTING_HVAC_OUTPUTS.items():
        try:
            objects = idf.idfobjects[hvac_type]
        except KeyError:
            model.log(f'{hvac_type} HVAC SYSTEM IS NOT SUPPORTED')
            continue
        object_names = [o.Name for o in objects]
        if not object_names:
            continue
        zone_map = resolve_hvac_zone_map(
            idf=idf, hvac_type=hvac_type, hvac_obj_names=object_names, user_map=model.hvac_zone_map,
            verbose_mode=model.verbose_mode,
        )
        group = ExistingHvacGroup(hvac_type)
        # An object that serves several zones (an air loop) appears once per zone
        for object_name, zones in zone_map.items():
            for zone in zones:
                group.object_names.append(object_name)
                group.zones_orig.append(zone.upper())
                separator = ':' if ':' in zone else ' '
                group.zones.append(zone.upper().replace(separator, '_'))
        group.windows = [window for zone in group.zones for window in model.windows if zone.lower() in window.lower()]
        model.existing_hvac.append(group)

    for group in model.existing_hvac:
        for zone, object_name in zip(group.zones_orig, group.object_names):
            if zone not in model.zones_orig:
                model.log(
                    f'"{zone}" is not a valid zone. \n'
                    f'The HVAC object "{object_name}" ({group.hvac_type}) could not be mapped to any occupied zone. \n'
                    f'If automatic detection failed, supply the correct mapping via '
                    f'hvac_zone_map={{"\'{object_name}\'": "correct_zone_name"}}.'
                )
                model.not_working = True
    for group in model.existing_hvac:
        model.log(f'The names of the existing {group.hvac_type} objects are:', *group.object_names,
                  f'The zones related to these {group.hvac_type} objects are', *group.zones_orig,
                  f'And the windows related to these {group.hvac_type} objects are:', *group.windows)


def _add_schedule(model: AccimModel, existing: set, name: str, value: int) -> None:
    if name in existing:
        model.log(f'{name} Schedule already was in the model')
        return
    model.idf.newidfobject('Schedule:Compact', Name=name, Schedule_Type_Limits_Name='Any Number',
                           Field_1='Through: 12/31', Field_2='For: AllDays', Field_3=f'Until: 24:00,{value}')
    existing.add(name)
    model.log(f'{name} Schedule has been added')


def add_setpoint_schedules(model: AccimModel) -> None:
    """Add the setpoint schedules of each zone (AHST_Sch_<zone>, ACST_Sch_<zone>), which the EMS actuates,
    and use them in the existing thermostat setpoint objects."""
    idf = model.idf
    existing = {s.Name for s in idf.idfobjects['Schedule:Compact']}
    for group in model.thermostat_groups:
        if not group.setpoint_names:
            continue
        for ems_name in group.ems_names:
            if group.setpoint_type in ('ThermostatSetpoint:DualSetpoint', 'ThermostatSetpoint:SingleHeating'):
                _add_schedule(model, existing, f'AHST_Sch_{ems_name}', 20)
            if group.setpoint_type in ('ThermostatSetpoint:DualSetpoint', 'ThermostatSetpoint:SingleCooling'):
                _add_schedule(model, existing, f'ACST_Sch_{ems_name}', 24)

    for group in model.thermostat_groups:
        setpoints = idf.idfobjects[group.setpoint_type]
        for setpoint_name, ems_name in zip(group.setpoint_names, group.ems_names):
            for setpoint in [s for s in setpoints if s.Name.upper() == setpoint_name.upper()]:
                if group.setpoint_type == 'ThermostatSetpoint:SingleHeating':
                    setpoint.Setpoint_Temperature_Schedule_Name = f'AHST_Sch_{ems_name}'
                elif group.setpoint_type == 'ThermostatSetpoint:SingleCooling':
                    setpoint.Setpoint_Temperature_Schedule_Name = f'ACST_Sch_{ems_name}'
                else:
                    setpoint.Heating_Setpoint_Temperature_Schedule_Name = f'AHST_Sch_{ems_name}'
                    setpoint.Cooling_Setpoint_Temperature_Schedule_Name = f'ACST_Sch_{ems_name}'


def _add_coil_sensor(model: AccimModel, sensors: List[str], name: str, key: str, variable: str) -> None:
    if name in sensors:
        model.log(f'Not added - {name} Sensor')
        return
    model.idf.newidfobject('EnergyManagementSystem:Sensor', Name=name,
                           OutputVariable_or_OutputMeter_Index_Key_Name=key,
                           OutputVariable_or_OutputMeter_Name=variable)
    sensors.append(name)
    model.log(f'Added - {name} Sensor')


def add_coil_sensors(model: AccimModel) -> None:
    """Add the EMS sensors that tell whether the existing HVAC equipment of each zone and window is
    cooling (``<name>_CoolCoil``) or heating (``<name>_HeatCoil``)."""
    sensors = [s.Name for s in model.idf.idfobjects['EnergyManagementSystem:Sensor']]
    for group in model.existing_hvac:
        variable = EXISTING_HVAC_OUTPUTS[group.hvac_type]
        for object_name, zone in zip(group.object_names, group.zones):
            for kind, suffix in (('Cool', '_CoolCoil'), ('Heating', '_HeatCoil')):
                if kind not in object_name and kind not in variable:
                    continue
                ems_names = [name for ems_zone, name in zip(model.ems_zones, model.ems_names)
                             if ems_zone.upper() == zone.upper()] or [zone]
                for ems_name in ems_names:
                    _add_coil_sensor(model, sensors, ems_name + suffix, object_name, variable)
                for window in group.windows:
                    if zone.lower() in window.lower():
                        _add_coil_sensor(model, sensors, window + suffix, object_name, variable)
    # The coil sensors, initialised at the beginning of each environment (see add_coil_initialisation)
    model.coil_sensor_names = [s for s in sensors if s.endswith('_CoolCoil') or s.endswith('_HeatCoil')]


def add_coil_initialisation(model: AccimModel) -> None:
    """Add a program that sets the coil sensors to 0 at the beginning of each environment.

    Before the HVAC systems have run, the coil sensors have no values, and EnergyPlus stops at the first
    timestep ('variable not initialized').
    """
    idf = model.idf
    name = 'InitExisHVACCoils'
    if name in [p.Name for p in idf.idfobjects['EnergyManagementSystem:Program']]:
        model.log(f'Not added - {name} Program (already exists)')
        return
    sensors = model.coil_sensor_names or [n + suffix for n in model.ems_names for suffix in ('_CoolCoil', '_HeatCoil')]
    if not sensors:
        model.log(f'No coil sensors found, skipping {name}')
        return
    lines = {f'Program_Line_{n}': f'SET {sensor} = 0' for n, sensor in enumerate(sensors, start=1)}
    idf.newidfobject('EnergyManagementSystem:Program', Name=name, **lines)
    model.log(f'Added - {name} Program ({len(sensors)} coil variables initialised)')
    if name not in [p.Name for p in idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']]:
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=name,
                         EnergyPlus_Model_Calling_Point='BeginNewEnvironment', Program_Name_1=name)
        model.log(f'Added - {name} ProgramCallingManager (BeginNewEnvironment)')
