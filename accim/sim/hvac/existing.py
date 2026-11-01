# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Existing HVAC systems (ScriptType 'ex_ac' and 'ex_mm'): their setpoint schedules and, in mixed mode, the sensors
that tell whether they heat or cool each zone.

In mixed mode, the windows of a zone open only when its HVAC system is off. With the existing HVAC systems, whatever
their equipment (zone equipment, air loops, baseboards, radiant systems, beams...), accim reads it from the
thermostat of the zone: the load to the setpoints that it asks the HVAC system for (the EnergyPlus output 'Zone
Predicted Sensible Load to Setpoint Heat Transfer Rate', in W), which is 0 when the temperature of the zone is between
its heating and cooling setpoints.
"""

from accim.sim.model import AccimModel

__all__ = [
    'LOAD_TO_SETPOINT_OUTPUT',
    'add_load_sensors',
    'add_setpoint_schedules',
]

#: The EnergyPlus output that the sensors of the zones and windows read (in mixed mode).
LOAD_TO_SETPOINT_OUTPUT = 'Zone Predicted Sensible Load to Setpoint Heat Transfer Rate'


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


def add_load_sensors(model: AccimModel) -> None:
    """Add the EMS sensors of the load to the setpoints of the zone of each occupied zone (``<zone>_LoadToSetpoint``)
    and of each window or door (``<window>_LoadToSetpoint``), which the programs ApplyAST_<zone> and
    SetWindowOperation_<window> read (ScriptType 'ex_mm')."""
    existing = {s.Name.upper() for s in model.idf.idfobjects['EnergyManagementSystem:Sensor']}
    for name, zone in [*zip(model.ems_names, model.ems_zones), *zip(model.windows, model.window_zones)]:
        sensor = f'{name}_LoadToSetpoint'
        if sensor.upper() in existing:
            model.log(f'Not added - {sensor} Sensor')
            continue
        model.idf.newidfobject('EnergyManagementSystem:Sensor', Name=sensor,
                               OutputVariable_or_OutputMeter_Index_Key_Name=zone,
                               OutputVariable_or_OutputMeter_Name=LOAD_TO_SETPOINT_OUTPUT)
        existing.add(sensor.upper())
        model.log(f'Added - {sensor} Sensor')
