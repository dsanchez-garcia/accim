# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Existing HVAC systems (ScriptType 'ex_ac' and 'ex_mm'): their thermostats, availability, outdoor temperature limits
and backup ideal loads air systems and, in mixed mode, the sensors that tell whether they heat or cool each zone.

Thermostats. The adaptive setpoints are setpoints of the operative temperature, but the thermostats of EnergyPlus
(ZoneControl:Thermostat) control the air temperature unless a ZoneControl:Thermostat:OperativeTemperature object
makes them control the operative temperature, as accim does with the thermostats of its VRF systems. With
``existing_hvac_operative_temperature_control=True`` (the default), the thermostat of each occupied zone controls the
operative temperature of the zone between its setpoints at all times, as those of the VRF systems: it gets a
ThermostatSetpoint:DualSetpoint object of its own with the setpoint schedules of the zone (AHST_Sch_<zone> and
ACST_Sch_<zone>, which the EMS actuates), a control type schedule that always selects it (4, dual setpoint), and a
ZoneControl:Thermostat:OperativeTemperature object if it has none (:func:`set_operative_temperature_thermostats`).
Otherwise, as in accim 0.x, the thermostats keep controlling the air temperature, and the setpoint object of the
first control of each thermostat gets the setpoint schedules of its zone (:func:`add_setpoint_schedules`).

Availability. An HVAC system that is not available cannot keep the zones between the setpoints.
``existing_hvac_availability_schedule`` makes the existing HVAC systems available with a schedule
(:func:`make_available`); by default, their availability does not change, and accim warns if it can switch them off
(:func:`warn_availability`).

Operating limits and capacity. The compressors of the DX coils and VRF systems, and the supplemental heaters, do not
work with some outdoor temperatures (those of the VRF systems in cooling mode, above 43 °C by default in EnergyPlus,
for instance). ``existing_hvac_widen_outdoor_temperature_limits`` widens these limits to those of the VRF systems of
accim (:func:`widen_outdoor_temperature_limits`); by default, they do not change, and accim warns if they are
narrower (:func:`warn_outdoor_temperature_limits`). Whatever the existing HVAC system, it may also lack capacity, have
controls that do not reach the setpoints (the supply air temperatures of an air loop...), or have no equipment that
cools or heats: ``existing_hvac_ideal_loads_backup`` adds to each occupied zone a backup ideal loads air system that
supplies the load to the setpoints that the existing HVAC system does not meet (:func:`add_ideal_loads_backups`). The
radiant systems, ventilated slabs and cooling panels follow setpoint schedules of their own, not the thermostats, so
accim warns about them (:func:`warn_own_setpoints`).

Mixed mode. The windows of a zone open only when its HVAC system is off. With the existing HVAC systems, whatever
their equipment (zone equipment, air loops, baseboards, radiant systems, beams...), accim reads it from the
thermostat of the zone: the load to the setpoints that it asks the HVAC system for (the EnergyPlus output 'Zone
Predicted Sensible Load to Setpoint Heat Transfer Rate', in W), which is 0 when the temperature of the zone is between
its heating and cooling setpoints.
"""

import re
import warnings
from typing import Dict, Iterator, List, Optional, Tuple

from accim.sim.hvac.schedules import (
    ALWAYS_ON_SCHEDULE,
    DUAL_SETPOINT_CONTROL_SCHEDULE,
    RADIATIVE_FRACTION_SCHEDULE,
    add_compact_schedule,
    add_radiative_fraction_schedule,
    is_always_on,
)
from accim.sim.idf_tools import try_objects
from accim.sim.model import AccimModel
from accim.sim.outputs import _model_label

__all__ = [
    'AVAILABILITY_MANAGER',
    'AVAILABILITY_MANAGER_LIST',
    'IDEAL_LOADS_BACKUP',
    'LOAD_TO_SETPOINT_OUTPUT',
    'OUTDOOR_TEMPERATURE_LIMITS',
    'add_ideal_loads_backups',
    'add_load_sensors',
    'add_setpoint_schedules',
    'availability_warning',
    'make_available',
    'outdoor_temperature_limits_warning',
    'own_setpoints_warning',
    'set_operative_temperature_thermostats',
    'warn_availability',
    'warn_outdoor_temperature_limits',
    'warn_own_setpoints',
    'widen_outdoor_temperature_limits',
]

#: The EnergyPlus output that the sensors of the zones and windows read (in mixed mode).
LOAD_TO_SETPOINT_OUTPUT = 'Zone Predicted Sensible Load to Setpoint Heat Transfer Rate'
#: The availability manager (AvailabilityManager:Scheduled) and the list of the air and plant loops with
#: ``existing_hvac_availability_schedule``.
AVAILABILITY_MANAGER = 'ACCIS Availability Manager'
AVAILABILITY_MANAGER_LIST = 'ACCIS Availability Manager List'
#: The end of the names of the backup ideal loads air systems ('<zone> ACCIS Backup Ideal Loads').
IDEAL_LOADS_BACKUP = 'ACCIS Backup Ideal Loads'
#: The outdoor temperature limits of the VRF systems of accim (°C), which
#: ``existing_hvac_widen_outdoor_temperature_limits`` gives to the existing HVAC systems.
OUTDOOR_TEMPERATURE_LIMITS = (-20, 80)

_DUAL_SETPOINT = 'ThermostatSetpoint:DualSetpoint'
_OPERATIVE_TEMPERATURE = 'ZoneControl:Thermostat:OperativeTemperature'
#: The HVAC objects whose field 'Availability Schedule Name' gives the availability of the HVAC systems (by the
#: beginning of their types): the zone equipment, air terminals, unitary systems, fans, coils, coil systems, VRF
#: systems and evaporative coolers. Not the exhaust fans, the units that supply outdoor air (energy recovery
#: ventilators, outdoor air units, dedicated outdoor air systems), the dehumidifiers and the refrigeration chillers,
#: which do not keep the zones at their setpoints.
_AVAILABILITY_TYPES = ('ZONEHVAC:', 'AIRTERMINAL:', 'AIRLOOPHVAC:', 'FAN:', 'COIL:', 'COILSYSTEM:', 'AIRCONDITIONER:',
                       'EVAPORATIVECOOLER:')
_NOT_AVAILABILITY_TYPES = {'FAN:ZONEEXHAUST', 'ZONEHVAC:ENERGYRECOVERYVENTILATOR', 'ZONEHVAC:OUTDOORAIRUNIT',
                           'AIRLOOPHVAC:DEDICATEDOUTDOORAIRSYSTEM', 'ZONEHVAC:DEHUMIDIFIER:DX',
                           'ZONEHVAC:EXHAUSTCONTROL', 'ZONEHVAC:REFRIGERATIONCHILLERSET'}
#: The loops whose availability managers give their availability.
_LOOPS = ('AIRLOOPHVAC', 'PLANTLOOP')
#: The operation schemes of the plant and condenser loops: EnergyPlus uses the first scheme whose schedule is on, so
#: the equipment of an object with one scheme is not available while its schedule is 0.
_OPERATION_SCHEMES = ('PlantEquipmentOperationSchemes', 'CondenserEquipmentOperationSchemes')
#: The HVAC objects that heat or cool the zones with setpoint schedules of their own, not with the thermostats of the
#: zones (the cooling panels follow the thermostat with the control types of the loads of the zone).
_OWN_SETPOINT_TYPES = ('ZONEHVAC:LOWTEMPERATURERADIANT:VARIABLEFLOW', 'ZONEHVAC:LOWTEMPERATURERADIANT:CONSTANTFLOW',
                       'ZONEHVAC:LOWTEMPERATURERADIANT:ELECTRIC', 'ZONEHVAC:HIGHTEMPERATURERADIANT',
                       'ZONEHVAC:VENTILATEDSLAB', 'ZONEHVAC:COOLINGPANEL:RADIANTCONVECTIVE:WATER')
_LOAD_CONTROL_TYPES = ('ZONETOTALLOAD', 'ZONECONVECTIVELOAD')
#: The availability managers that can switch a loop off: those that follow a schedule (with the field of the
#: schedule) and those that switch it off with some temperatures (None).
_SWITCHING_OFF_MANAGERS = {
    'AVAILABILITYMANAGER:SCHEDULED': 'Schedule_Name',
    'AVAILABILITYMANAGER:SCHEDULEDOFF': 'Schedule_Name',
    'AVAILABILITYMANAGER:NIGHTCYCLE': 'Fan_Schedule_Name',
    'AVAILABILITYMANAGER:OPTIMUMSTART': 'Fan_Schedule_Name',
    'AVAILABILITYMANAGER:LOWTEMPERATURETURNOFF': None,
    'AVAILABILITYMANAGER:HIGHTEMPERATURETURNOFF': None,
    'AVAILABILITYMANAGER:DIFFERENTIALTHERMOSTAT': None,
}
#: The names that the warnings list of each kind.
_LISTED_NAMES = 5
#: The HVAC objects whose outdoor temperature limits existing_hvac_widen_outdoor_temperature_limits widens (by the
#: beginning of their types), and their fields of these limits (with the names of eppy).
_LIMIT_TYPES = ('ZONEHVAC:', 'AIRLOOPHVAC:', 'COIL:', 'COILSYSTEM:', 'AIRCONDITIONER:', 'HEATPUMP:')
_LIMIT_FIELD = re.compile(r'^(Minimum|Maximum)_(Outdoor|Condenser_Inlet_Node)_\w*Temperature')
_NOT_LIMIT_WORDS = ('Crankcase', 'Defrost', 'Heat_Recovery', 'Schedule', 'Wet')


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
    and use them in the existing thermostat setpoint objects (with
    ``existing_hvac_operative_temperature_control=False``, as in accim 0.x).

    Only the setpoint object of the first control of each thermostat gets them, and the thermostats keep controlling
    the air temperature, with their control type schedules."""
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


def _controls(thermostat) -> List[Tuple[str, str]]:
    """The object type and name of each control of a ZoneControl:Thermostat object."""
    controls = []
    for number in range(1, 5):
        object_type = str(getattr(thermostat, f'Control_{number}_Object_Type', '') or '').strip()
        if object_type:
            controls.append((object_type, str(getattr(thermostat, f'Control_{number}_Name', '') or '').strip()))
    return controls


def _own_dual_setpoint(model: AccimModel, thermostat, zone: str):
    """The ThermostatSetpoint:DualSetpoint object of a thermostat that no other thermostat uses (one of its controls,
    or '<zone> Dual SP'), or a new one."""
    idf = model.idf
    duals = {d.Name.upper(): d for d in idf.idfobjects[_DUAL_SETPOINT]}
    used_by_others = {name.upper() for other in idf.idfobjects['ZoneControl:Thermostat']
                      if other.Name.upper() != thermostat.Name.upper()
                      for object_type, name in _controls(other) if object_type.upper() == _DUAL_SETPOINT.upper()}
    candidates = [name for object_type, name in _controls(thermostat) if object_type.upper() == _DUAL_SETPOINT.upper()]
    for name in [*candidates, f'{zone} Dual SP']:
        if name.upper() in duals and name.upper() not in used_by_others:
            return duals[name.upper()]
    name, number = f'{zone} Dual SP', 1
    while name.upper() in duals:
        number += 1
        name = f'{zone} Dual SP {number}'
    model.log(f'{name} {_DUAL_SETPOINT} has been added')
    return idf.newidfobject(_DUAL_SETPOINT, Name=name)


def _use_dual_setpoint(thermostat, dual) -> None:
    """Make a thermostat use only its dual setpoint object, at all times."""
    if thermostat.Control_Type_Schedule_Name != DUAL_SETPOINT_CONTROL_SCHEDULE:
        thermostat.Control_Type_Schedule_Name = DUAL_SETPOINT_CONTROL_SCHEDULE
    if (thermostat.Control_1_Object_Type, thermostat.Control_1_Name) != (_DUAL_SETPOINT, dual.Name):
        thermostat.Control_1_Object_Type = _DUAL_SETPOINT
        thermostat.Control_1_Name = dual.Name
    for number in range(2, 5):
        for field in (f'Control_{number}_Object_Type', f'Control_{number}_Name'):
            if str(getattr(thermostat, field, '') or '').strip():
                setattr(thermostat, field, '')


def _control_operative_temperature(model: AccimModel, thermostat) -> None:
    """Add a ZoneControl:Thermostat:OperativeTemperature object to a thermostat that has none."""
    idf = model.idf
    controls = [c for c in idf.idfobjects[_OPERATIVE_TEMPERATURE]
                if c.Thermostat_Name.upper() == thermostat.Name.upper()]
    if not controls:
        add_radiative_fraction_schedule(model)
        idf.newidfobject(_OPERATIVE_TEMPERATURE, Thermostat_Name=thermostat.Name,
                         Radiative_Fraction_Input_Mode='Scheduled', Fixed_Radiative_Fraction='',
                         Radiative_Fraction_Schedule_Name=RADIATIVE_FRACTION_SCHEDULE)
        model.log(f'{thermostat.Name} {_OPERATIVE_TEMPERATURE} has been added')
        return
    model.log(f'{thermostat.Name} {_OPERATIVE_TEMPERATURE} already was in the model')
    for control in controls:
        # An adaptive comfort model of EnergyPlus would replace the cooling setpoint of accim with its own
        adaptive = str(getattr(control, 'Adaptive_Comfort_Model_Type', '') or '').strip()
        if adaptive and adaptive.upper() != 'NONE':
            control.Adaptive_Comfort_Model_Type = 'None'
            model.log(f'Modified - {thermostat.Name} {_OPERATIVE_TEMPERATURE}: Adaptive Comfort Model Type '
                      f'{adaptive} replaced with None, so that the setpoints are those of accim')


def set_operative_temperature_thermostats(model: AccimModel) -> None:
    """Make the thermostat of each occupied zone control the operative temperature of the zone between its setpoints
    at all times, as the thermostats of the VRF systems (``existing_hvac_operative_temperature_control=True``).

    Each occupied zone gets its setpoint schedules (AHST_Sch_<zone>, ACST_Sch_<zone>), which the EMS actuates. Its
    thermostat (ZoneControl:Thermostat):

    - uses only a ThermostatSetpoint:DualSetpoint object with these schedules: one it had, or the one named '<zone>
      Dual SP', if no other thermostat uses it, or a new one (the other setpoint objects do not change);
    - always uses it: its control type schedule is 'Control type schedule: Always 4' (dual setpoint);
    - controls the operative temperature: a ZoneControl:Thermostat:OperativeTemperature object, if it has none, with
      the radiative fraction of 'TypOperativeTempControlSch' (0.5, as in the output 'Zone Operative Temperature', and 0
      on the design days, so that the sizing calculations do not change), as with the VRF systems. If it has one,
      its radiative fraction does not change, but an adaptive comfort model of EnergyPlus in it is removed, since it
      would replace the cooling setpoint of accim.

    The thermostats of the zones without occupants do not change. A warning lists the occupied zones without a
    thermostat, whose operative temperature accim cannot keep between the setpoints.

    :raises ValueError: If the thermostat of an occupied zone controls the zones of a ZoneList: accim needs a
        thermostat for each occupied zone.
    """
    idf = model.idf
    occupied = {zone.upper(): (zone, ems_name) for zone, ems_name in zip(model.ems_zones, model.ems_names)}
    zone_lists = {z.Name.upper(): [str(name).strip().upper() for name in z.obj[2:]]
                  for z in try_objects(idf, 'ZoneList')}
    existing = {s.Name for s in idf.idfobjects['Schedule:Compact']}
    controlled = set()
    for thermostat in list(idf.idfobjects['ZoneControl:Thermostat']):
        key = thermostat.Zone_or_ZoneList_Name.upper()
        if key not in occupied:
            listed = [occupied[zone][0] for zone in zone_lists.get(key, []) if zone in occupied]
            if listed:
                raise ValueError(
                    f'The thermostat {thermostat.Name} of the model {_model_label(model)} controls the zones of the '
                    f'ZoneList {thermostat.Zone_or_ZoneList_Name}, including the occupied zones {listed}: accim needs '
                    f'a ZoneControl:Thermostat object for each occupied zone, to control it with its own setpoints. '
                    f'Give each zone its own thermostat.')
            continue
        zone, ems_name = occupied[key]
        _add_schedule(model, existing, f'AHST_Sch_{ems_name}', 20)
        _add_schedule(model, existing, f'ACST_Sch_{ems_name}', 24)
        dual = _own_dual_setpoint(model, thermostat, zone)
        dual.Heating_Setpoint_Temperature_Schedule_Name = f'AHST_Sch_{ems_name}'
        dual.Cooling_Setpoint_Temperature_Schedule_Name = f'ACST_Sch_{ems_name}'
        if not controlled:
            add_compact_schedule(model, DUAL_SETPOINT_CONTROL_SCHEDULE, 'Through: 12/31', 'For: AllDays',
                                 'Until: 24:00,4')
        _use_dual_setpoint(thermostat, dual)
        _control_operative_temperature(model, thermostat)
        controlled.add(key)
        model.log(f'The thermostat {thermostat.Name} controls the operative temperature of {zone} between its '
                  f'setpoints, with {dual.Name}')
    # The EMS actuates the setpoint schedules of all the occupied zones
    missing = []
    for zone, ems_name in zip(model.ems_zones, model.ems_names):
        if zone.upper() not in controlled:
            missing.append(zone)
            _add_schedule(model, existing, f'AHST_Sch_{ems_name}', 20)
            _add_schedule(model, existing, f'ACST_Sch_{ems_name}', 24)
    if missing:
        warnings.warn(
            f'The occupied zones {missing} of the model {_model_label(model)} have no thermostat '
            f'(ZoneControl:Thermostat), so their existing HVAC systems do not follow the setpoints of accim, which '
            f'cannot keep their operative temperature between them.',
            stacklevel=3,
        )


def _availability_objects(idf) -> Iterator:
    """The HVAC objects with a field 'Availability Schedule Name' (see _AVAILABILITY_TYPES)."""
    for object_type in idf.idfobjects:
        upper = object_type.upper()
        if not upper.startswith(_AVAILABILITY_TYPES) or upper in _NOT_AVAILABILITY_TYPES:
            continue
        for obj in idf.idfobjects[object_type]:
            if 'Availability_Schedule_Name' in obj.fieldnames:
                yield obj


def _objects_with_availability_managers(idf) -> Iterator:
    """The loops and zone equipment with a list of availability managers (except _NOT_AVAILABILITY_TYPES)."""
    for object_type in idf.idfobjects:
        upper = object_type.upper()
        if (upper not in _LOOPS and not upper.startswith('ZONEHVAC:')) or upper in _NOT_AVAILABILITY_TYPES:
            continue
        for obj in idf.idfobjects[object_type]:
            if 'Availability_Manager_List_Name' in obj.fieldnames and str(obj.Availability_Manager_List_Name).strip():
                yield obj


def _schedule_names(idf) -> set:
    return {s.Name.upper() for object_type in ('Schedule:Year', 'Schedule:Compact', 'Schedule:Constant',
                                               'Schedule:File') for s in try_objects(idf, object_type)}


def _single_operation_schemes(idf) -> Iterator[Tuple[object, str]]:
    """The plant and condenser operation schemes objects with one scheme, and the field of its schedule."""
    for object_type in _OPERATION_SCHEMES:
        for schemes in try_objects(idf, object_type):
            fields = [f'Control_Scheme_{number}_Schedule_Name' for number in range(1, 9)
                      if str(getattr(schemes, f'Control_Scheme_{number}_Object_Type', '') or '').strip()]
            if len(fields) == 1:
                yield schemes, fields[0]


def make_available(model: AccimModel, schedule: str) -> None:
    """Make the existing HVAC systems available with a schedule (``existing_hvac_availability_schedule``).

    - The HVAC objects that heat or cool the zones get the schedule as their availability schedule (the field
      'Availability Schedule Name' of the zone equipment, air terminals, unitary systems, fans, coils, coil systems,
      VRF systems and evaporative coolers; not that of the exhaust fans, the units that supply outdoor air (energy
      recovery ventilators, outdoor air units, dedicated outdoor air systems), the dehumidifiers and the refrigeration
      chillers).
    - The air and plant loops with availability managers (AirLoopHVAC and PlantLoop objects with an
      AvailabilityManagerAssignmentList) get one AvailabilityManager:Scheduled object with the schedule instead
      ('ACCIS Availability Manager', in 'ACCIS Availability Manager List'), so that they do not switch off at night,
      with the outdoor temperature...; the zone equipment, whose availability schedule is the schedule, loses its
      availability managers.
    - The plant and condenser operation schemes objects with one scheme get the schedule as the schedule of their
      scheme, so that their equipment works whenever the loop is available (those with several schemes, for
      different times, do not change: EnergyPlus uses the first scheme whose schedule is on).

    The availability managers of the model stay in it, without a loop that uses them. The
    AvailabilityManager:HybridVentilation objects do not change.

    :param schedule: The name of a schedule of the model, or 'On 24/7', which accim adds if the model does not have it
        (always 1).
    :raises ValueError: If the model has no schedule with that name.
    """
    idf = model.idf
    if not isinstance(schedule, str) or not schedule.strip():
        raise ValueError(f'existing_hvac_availability_schedule must be the name of a schedule, not {schedule!r}.')
    if schedule.upper() not in _schedule_names(idf):
        if schedule != ALWAYS_ON_SCHEDULE:
            raise ValueError(
                f'existing_hvac_availability_schedule {schedule!r} is not a schedule of the model '
                f'{_model_label(model)}: give the name of one of its schedules, or {ALWAYS_ON_SCHEDULE!r}, which '
                f'accim adds (always 1).')
        add_compact_schedule(model, ALWAYS_ON_SCHEDULE, 'Through: 12/31', 'For: AllDays', 'Until: 24:00,1')
    for obj in _availability_objects(idf):
        if obj.Availability_Schedule_Name != schedule:
            obj.Availability_Schedule_Name = schedule
            model.log(f'Modified - {_object_type(obj)} {obj.Name}: availability schedule {schedule}')
    for schemes, field in list(_single_operation_schemes(idf)):
        if getattr(schemes, field) != schedule:
            setattr(schemes, field, schedule)
            model.log(f'Modified - {_object_type(schemes)} {schemes.Name}: schedule of the operation scheme {schedule}')
    managed = list(_objects_with_availability_managers(idf))
    if any(obj.key.upper() in _LOOPS for obj in managed):
        manager = next((m for m in idf.idfobjects['AvailabilityManager:Scheduled']
                        if m.Name.upper() == AVAILABILITY_MANAGER.upper()), None)
        if manager is None:
            idf.newidfobject('AvailabilityManager:Scheduled', Name=AVAILABILITY_MANAGER, Schedule_Name=schedule)
            model.log(f'Added - {AVAILABILITY_MANAGER} AvailabilityManager:Scheduled, with the schedule {schedule}')
        else:
            manager.Schedule_Name = schedule
        if AVAILABILITY_MANAGER_LIST.upper() not in {lst.Name.upper() for lst in
                                                     idf.idfobjects['AvailabilityManagerAssignmentList']}:
            idf.newidfobject('AvailabilityManagerAssignmentList', Name=AVAILABILITY_MANAGER_LIST,
                             Availability_Manager_1_Object_Type='AvailabilityManager:Scheduled',
                             Availability_Manager_1_Name=AVAILABILITY_MANAGER)
    for obj in managed:
        if obj.key.upper() in _LOOPS:
            obj.Availability_Manager_List_Name = AVAILABILITY_MANAGER_LIST
            model.log(f'Modified - {_object_type(obj)} {obj.Name}: availability managers {AVAILABILITY_MANAGER_LIST}')
        else:
            obj.Availability_Manager_List_Name = ''
            model.log(f'Modified - {_object_type(obj)} {obj.Name}: no availability managers')


def _listed(names: List[str]) -> str:
    shown = ', '.join(repr(name) for name in names[:_LISTED_NAMES])
    return shown + (f' and {len(names) - _LISTED_NAMES} more' if len(names) > _LISTED_NAMES else '')


def availability_warning(model: AccimModel) -> Optional[str]:
    """The warning about the availability of the existing HVAC systems, or None if they are always available.

    They can be unavailable at times if the availability schedule of one of their HVAC objects (see
    :func:`make_available`) or of the only operation scheme of one of their plant or condenser loops is 0 at times (on
    the days of the run periods; or if accim cannot read its values), or if one of their loops or zone equipment has
    an availability manager that can switch it off (with a schedule that is 0 at times, or with the temperatures), or
    if the model has AvailabilityManager:HybridVentilation objects.
    """
    idf = model.idf
    schedules: Dict[str, int] = {}
    names = [str(obj.Availability_Schedule_Name).strip() for obj in _availability_objects(idf)]
    names += [str(getattr(schemes, field)).strip() for schemes, field in _single_operation_schemes(idf)]
    for name in names:
        if is_always_on(idf, name) is not True:
            schedules[name] = schedules.get(name, 0) + 1
    lists = {lst.Name.upper(): lst for lst in try_objects(idf, 'AvailabilityManagerAssignmentList')}
    used = dict.fromkeys(str(obj.Availability_Manager_List_Name).strip().upper()
                         for obj in _objects_with_availability_managers(idf))
    managers: List[str] = []
    for list_name in used:
        lst = lists.get(list_name)
        if lst is None:
            continue
        for object_type, name in zip(lst.obj[2::2], lst.obj[3::2]):
            kind = str(object_type).upper()
            if kind not in _SWITCHING_OFF_MANAGERS:
                continue
            field = _SWITCHING_OFF_MANAGERS[kind]
            if field is not None:
                manager = next((m for m in try_objects(idf, str(object_type))
                                if m.Name.upper() == str(name).upper()), None)
                if manager is None or is_always_on(idf, getattr(manager, field)) is True:
                    continue
            label = f'{object_type} {name}'
            if label not in managers:
                managers.append(label)
    managers += [f'AvailabilityManager:HybridVentilation {m.Name}'
                 for m in try_objects(idf, 'AvailabilityManager:HybridVentilation')]
    if not schedules and not managers:
        return None
    reasons = []
    if schedules:
        reasons.append(f'the availability schedules {_listed(list(schedules))} of {sum(schedules.values())} HVAC '
                       f'objects are 0 at times, or accim cannot read their values')
    if managers:
        reasons.append(f'the availability managers {_listed(managers)} can switch them off')
    return (f'The existing HVAC systems of the model {_model_label(model)} may be unavailable at times: '
            f'{"; ".join(reasons)}. While they are unavailable, they cannot keep the operative temperature between '
            f'the setpoints. existing_hvac_availability_schedule={ALWAYS_ON_SCHEDULE!r} makes them always '
            f'available, and existing_hvac_ideal_loads_backup=True supplies the loads that they do not meet.')


def warn_availability(model: AccimModel) -> None:
    """Warn if the existing HVAC systems may be unavailable at times (see :func:`availability_warning`)."""
    message = availability_warning(model)
    if message is not None:
        warnings.warn(message, stacklevel=3)


def _outdoor_temperature_limits(idf) -> Iterator[Tuple[object, str, float, float]]:
    """The outdoor temperature limits of the HVAC objects that are narrower than OUTDOOR_TEMPERATURE_LIMITS (within
    the bounds of the IDD): (object, field, current value, widened value)."""
    for object_type in idf.idfobjects:
        upper = object_type.upper()
        if not upper.startswith(_LIMIT_TYPES):
            continue
        for obj in idf.idfobjects[object_type]:
            for field in obj.fieldnames:
                if not _LIMIT_FIELD.match(field) or any(word in field for word in _NOT_LIMIT_WORDS):
                    continue
                idd = obj.getfieldidd(field)
                value = str(getattr(obj, field, '') or '').strip() or (idd.get('default') or [''])[0]
                try:
                    current = float(value)
                except ValueError:
                    continue
                if field.startswith('Minimum'):
                    widened = float(OUTDOOR_TEMPERATURE_LIMITS[0])
                    if 'minimum' in idd:
                        widened = max(widened, float(idd['minimum'][0]))
                    if 'minimum>' in idd:
                        widened = max(widened, float(idd['minimum>'][0]) + 0.01)
                    narrower = current > widened
                else:
                    widened = float(OUTDOOR_TEMPERATURE_LIMITS[1])
                    if 'maximum' in idd:
                        widened = min(widened, float(idd['maximum'][0]))
                    if 'maximum<' in idd:
                        widened = min(widened, float(idd['maximum<'][0]) - 0.01)
                    narrower = current < widened
                if narrower:
                    yield obj, field, current, widened


def _object_name(obj) -> str:
    return str(obj.obj[1]) if len(obj.obj) > 1 else ''


def _object_type(obj) -> str:
    """The type of an object as in the IDD (eppy gives the type of a new object in capitals)."""
    return obj.objidd[0].get('idfobj', obj.key) if obj.objidd else obj.key


def widen_outdoor_temperature_limits(model: AccimModel) -> None:
    """Widen the outdoor temperature limits of the existing HVAC systems to those of the VRF systems of accim
    (``existing_hvac_widen_outdoor_temperature_limits``): -20 and 80 °C (:data:`OUTDOOR_TEMPERATURE_LIMITS`), or the
    bounds of the IDD if they are narrower.

    The limits are the fields 'Minimum/Maximum Outdoor ... Temperature ...' and 'Minimum/Maximum Condenser Inlet Node
    Temperature in ... Mode' of the HVAC objects (the outdoor temperatures that lock out the compressors of the DX
    coils, the VRF systems in cooling and heating mode and the supplemental heaters), except those of the defrost,
    crankcase heaters and heat recovery mode. Only the limits that are narrower change.
    """
    for obj, field, current, widened in list(_outdoor_temperature_limits(model.idf)):
        setattr(obj, field, widened)
        model.log(f'Modified - {_object_type(obj)} {_object_name(obj)}: {field} {current:g} -> {widened:g}')


def outdoor_temperature_limits_warning(model: AccimModel) -> Optional[str]:
    """The warning about the outdoor temperature limits of the existing HVAC systems that are narrower than those of
    the VRF systems of accim (see :func:`widen_outdoor_temperature_limits`), or None if there are none."""
    groups: Dict[Tuple[str, str, float], int] = {}
    for obj, field, current, _ in _outdoor_temperature_limits(model.idf):
        key = (_object_type(obj), obj.getfieldidd(field)['field'][0], current)
        groups[key] = groups.get(key, 0) + 1
    if not groups:
        return None
    limits = [f'{label} {value:g} C ({count} {object_type})' for (object_type, label, value), count in groups.items()]
    return (f'The existing HVAC systems of the model {_model_label(model)} do not heat or cool with some outdoor '
            f'temperatures: the outdoor temperature limits {_listed(limits)} switch off their compressors or heaters '
            f'outside them, and then they may not keep the operative temperature between the setpoints. '
            f'existing_hvac_widen_outdoor_temperature_limits=True widens them to those of the VRF systems of accim '
            f'({OUTDOOR_TEMPERATURE_LIMITS[0]} and {OUTDOOR_TEMPERATURE_LIMITS[1]} C), and '
            f'existing_hvac_ideal_loads_backup=True supplies the loads that they do not meet.')


def warn_outdoor_temperature_limits(model: AccimModel) -> None:
    """Warn if some outdoor temperature limits of the existing HVAC systems are narrower than those of the VRF systems
    of accim (see :func:`outdoor_temperature_limits_warning`)."""
    message = outdoor_temperature_limits_warning(model)
    if message is not None:
        warnings.warn(message, stacklevel=3)


def own_setpoints_warning(model: AccimModel) -> Optional[str]:
    """The warning about the HVAC objects that heat or cool the zones with setpoint schedules of their own, not with
    the thermostats of the zones (radiant systems, cooling panels, ventilated slabs), which do not follow the
    setpoints of accim, or None if the model has none."""
    objects = []
    for object_type in model.idf.idfobjects:
        if object_type.upper() not in _OWN_SETPOINT_TYPES:
            continue
        for obj in model.idf.idfobjects[object_type]:
            if str(getattr(obj, 'Control_Type', '') or '').strip().upper() in _LOAD_CONTROL_TYPES:
                continue
            objects.append(f'{_object_type(obj)} {_object_name(obj)}')
    if not objects:
        return None
    return (f'The HVAC objects {_listed(objects)} of the model {_model_label(model)} heat or cool the zones with '
            f'setpoint schedules of their own, not with the thermostats of the zones, so they do not follow the '
            f'setpoints of accim. To make them follow them, give them the setpoint schedules of their zones '
            f'(AHST_Sch_<zone> for heating and ACST_Sch_<zone> for cooling, which the EMS actuates) and the operative '
            f'temperature as their control temperature, or the control type ZoneTotalLoad to the cooling panels.')


def warn_own_setpoints(model: AccimModel) -> None:
    """Warn if the existing HVAC systems have objects with setpoint schedules of their own (see
    :func:`own_setpoints_warning`)."""
    message = own_setpoints_warning(model)
    if message is not None:
        warnings.warn(message, stacklevel=3)


def _add_node(idf, connections, field: str, node: str, node_list: str) -> None:
    """Add a node to the inlet or exhaust nodes of a zone (field of its ZoneHVAC:EquipmentConnections object): to its
    NodeList, or to a new NodeList with the node it had."""
    current = str(getattr(connections, field) or '').strip()
    if not current:
        setattr(connections, field, node)
        return
    nodes = next((n for n in idf.idfobjects['NodeList'] if n.Name.upper() == current.upper()), None)
    if nodes is None:
        nodes = idf.newidfobject('NodeList', Name=node_list, Node_1_Name=current)
        setattr(connections, field, node_list)
    names = [str(name).strip() for name in nodes.obj[2:] if str(name).strip()]
    setattr(nodes, f'Node_{len(names) + 1}_Name', node)


def add_ideal_loads_backups(model: AccimModel) -> None:
    """Add a backup ideal loads air system to each occupied zone, after its existing HVAC equipment
    (``existing_hvac_ideal_loads_backup``).

    The ZoneHVAC:IdealLoadsAirSystem object '<zone> ACCIS Backup Ideal Loads' is the last equipment of the zone in the
    cooling and heating sequences of its ZoneHVAC:EquipmentList, whose load distribution scheme is SequentialLoad, so
    the existing equipment supplies the load to the setpoints that it can, and the backup supplies the rest: the load
    that the existing HVAC system does not meet, because of its capacity, its controls, its operating limits or its
    availability, or because it has no equipment that heats or cools. The backup has no limits of capacity and no
    outdoor air, only meets the sensible load (no humidity control), and has inlet and exhaust nodes of its own.
    EnergyPlus reports its energy as district heating and cooling, apart from that of the existing HVAC system, and
    accim adds the outputs 'Zone Ideal Loads Zone Sensible Heating Rate' and 'Zone Ideal Loads Zone Sensible Cooling
    Rate' of the backups to the output types 'simplified' and 'standard'.

    A warning lists the occupied zones without zone HVAC equipment (ZoneHVAC:EquipmentConnections), which get no
    backup.
    """
    idf = model.idf
    connections = {c.Zone_Name.upper(): c for c in idf.idfobjects['ZoneHVAC:EquipmentConnections']}
    equipment_lists = {e.Name.upper(): e for e in idf.idfobjects['ZoneHVAC:EquipmentList']}
    ideal_loads = {i.Name.upper() for i in idf.idfobjects['ZoneHVAC:IdealLoadsAirSystem']}
    missing = []
    for zone in dict.fromkeys(model.ems_zones):
        zone_connections = connections.get(zone.upper())
        equipment = None if zone_connections is None else equipment_lists.get(
            str(zone_connections.Zone_Conditioning_Equipment_List_Name).strip().upper())
        if equipment is None:
            missing.append(zone)
            continue
        name = f'{zone} {IDEAL_LOADS_BACKUP}'
        if name.upper() in ideal_loads:
            model.log(f'{name} ZoneHVAC:IdealLoadsAirSystem already was in the model')
            continue
        supply, exhaust = f'{name} Supply Inlet', f'{name} Exhaust Outlet'
        _add_node(idf, zone_connections, 'Zone_Air_Inlet_Node_or_NodeList_Name', supply, f'{zone} ACCIS Inlet Nodes')
        _add_node(idf, zone_connections, 'Zone_Air_Exhaust_Node_or_NodeList_Name', exhaust,
                  f'{zone} ACCIS Exhaust Nodes')
        idf.newidfobject('ZoneHVAC:IdealLoadsAirSystem', Name=name, Zone_Supply_Air_Node_Name=supply,
                         Zone_Exhaust_Air_Node_Name=exhaust, Dehumidification_Control_Type='None',
                         Humidification_Control_Type='None')
        scheme = str(getattr(equipment, 'Load_Distribution_Scheme', '') or '').strip()
        if scheme and scheme.upper() != 'SEQUENTIALLOAD':
            equipment.Load_Distribution_Scheme = 'SequentialLoad'
            model.log(f'Modified - {equipment.Name} ZoneHVAC:EquipmentList: Load Distribution Scheme {scheme} -> '
                      f'SequentialLoad, so that the backup only supplies the load that the existing equipment does '
                      f'not')
        count = 0
        while str(getattr(equipment, f'Zone_Equipment_{count + 1}_Object_Type', '') or '').strip():
            count += 1
        number = count + 1
        setattr(equipment, f'Zone_Equipment_{number}_Object_Type', 'ZoneHVAC:IdealLoadsAirSystem')
        setattr(equipment, f'Zone_Equipment_{number}_Name', name)
        setattr(equipment, f'Zone_Equipment_{number}_Cooling_Sequence', number)
        setattr(equipment, f'Zone_Equipment_{number}_Heating_or_NoLoad_Sequence', number)
        model.ideal_loads_backups.append(name)
        model.log(f'Added - {name} ZoneHVAC:IdealLoadsAirSystem, after the {count} equipment of {zone}')
    if missing:
        warnings.warn(
            f'The occupied zones {missing} of the model {_model_label(model)} have no zone HVAC equipment '
            f'(ZoneHVAC:EquipmentConnections), so accim adds no backup ideal loads air system to them.',
            stacklevel=3,
        )


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
