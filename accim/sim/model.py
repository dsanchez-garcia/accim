# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The model to which accim adds the ACCIS: its occupied zones, windows and HVAC systems."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from accim.sim.arguments import MIXED_MODE_SCRIPT_TYPES
from accim.sim.idf_tools import try_objects
from accim.sim.targets import Target, resolve_targets
from accim.utils.people import get_people_objects

__all__ = ['AccimModel', 'ExistingHvacGroup', 'ThermostatGroup']

#: Thermostat setpoint objects of the existing HVAC systems that accim controls
#: (ThermostatSetpoint:SingleHeatingOrCooling is not supported).
THERMOSTAT_SETPOINT_TYPES = (
    'ThermostatSetpoint:SingleHeating',
    'ThermostatSetpoint:SingleCooling',
    'ThermostatSetpoint:DualSetpoint',
)


@dataclass
class ThermostatGroup:
    """The zones whose ZoneControl:Thermostat objects use one type of thermostat setpoint object.

    :ivar setpoint_type: The type of the thermostat setpoint objects.
    :ivar zones: The names of the zones, in upper case.
    :ivar ems_names: The names of the zones in the EMS objects.
    :ivar setpoint_names: The names of the thermostat setpoint objects.
    """

    setpoint_type: str
    zones: List[str] = field(default_factory=list)
    ems_names: List[str] = field(default_factory=list)
    setpoint_names: List[str] = field(default_factory=list)


@dataclass
class ExistingHvacGroup:
    """The objects of one type of existing HVAC equipment and the zones they serve.

    An object that serves several zones appears once per zone.

    :ivar hvac_type: The type of the objects (e.g. 'Coil:Cooling:DX:SingleSpeed').
    :ivar object_names: The names of the objects.
    :ivar zones_orig: The names of their zones, in upper case.
    :ivar zones: The names of their zones in the EMS objects.
    :ivar windows: The windows and doors of their zones.
    """

    hvac_type: str
    object_names: List[str] = field(default_factory=list)
    zones_orig: List[str] = field(default_factory=list)
    zones: List[str] = field(default_factory=list)
    windows: List[str] = field(default_factory=list)


class AccimModel:
    """An EnergyPlus model (eppy or besos IDF object) to which accim adds the ACCIS.

    Scanning the model finds its occupied zones and, depending on the script type, the windows and
    doors that open for natural ventilation (which, without an AirflowNetwork, are the ventilation
    objects of the zones, controlled through new schedules) and the existing HVAC systems.

    :param idf: The eppy or besos IDF object. It is modified in place.
    :param script_type: 'vrf_ac', 'vrf_mm', 'ex_ac' or 'ex_mm'.
    :param temp_ctrl: 'temperature' or 'pmv'.
    :param verbose_mode: True to print the process.
    :param hvac_zone_map: Optional zone of each existing HVAC object, {'HVAC object name': 'Zone name'},
        for the objects whose zone cannot be found automatically (ScriptType 'ex_mm').
    :param name: The name of the model in the messages.
    :raises ValueError: If the model has no People or People:Instance objects.
    :ivar targets: The targets of the EMS (one per occupied zone).
    :ivar occupied_zones_orig: The names of the occupied zones.
    :ivar occupied_zones: The same names with '_' instead of ' ' and ':'.
    :ivar ems_names: The name of each target in the EMS objects.
    :ivar windows_orig: The names of the windows and doors that open (mixed mode only).
    :ivar windows: The same names with '_' instead of ':'.
    :ivar window_zones: The zone of each window or door.
    :ivar zones_orig: The names of the zones that accim controls.
    :ivar zones: The same names, as in the names of the EMS objects.
    :ivar not_working: True if accim cannot work with the model (an existing HVAC object of an unknown zone).
    """

    def __init__(
        self,
        idf,
        script_type: str,
        temp_ctrl: str,
        verbose_mode: bool = True,
        hvac_zone_map: Optional[Dict[str, str]] = None,
        name: Optional[str] = None,
    ):
        self.idf = idf
        self.script_type = script_type
        self.temp_ctrl = temp_ctrl
        self.verbose_mode = verbose_mode
        self.hvac_zone_map = hvac_zone_map
        self.name = name if name is not None else str(idf)
        self.not_working = False
        self.is_mixed_mode = script_type in MIXED_MODE_SCRIPT_TYPES

        self.windows_orig: List[str] = []
        self.windows: List[str] = []
        self.window_zones: List[str] = []
        self.natural_ventilation_type: Optional[str] = None
        self.scheduled_ventilation: Dict[str, str] = {}
        self.thermostat_groups: List[ThermostatGroup] = []
        self.existing_hvac: List[ExistingHvacGroup] = []
        self.coil_sensor_names: List[str] = []

        self._scan_zones()
        self.log(f'The occupied zones in the model {self.name} are:', *self.occupied_zones_orig)
        if self.is_mixed_mode:
            self._scan_windows()
            self.log(f'The windows and doors in the model {self.name} are:', *self.windows)
        if script_type.startswith('vrf'):
            self.zones = list(self.occupied_zones)
            self.zones_orig = list(self.occupied_zones_orig)
            self.log(f'The zones in the model {self.name} are:', *self.zones)
        else:
            self._scan_thermostats()
            if script_type == 'ex_mm':
                from accim.sim.hvac.existing import scan_existing_hvac
                scan_existing_hvac(self)

    def log(self, *lines) -> None:
        """Print the lines if verbose_mode is True."""
        if self.verbose_mode:
            print(*lines, sep='\n')

    @property
    def energyplus_version(self) -> str:
        """The EnergyPlus version of the IDD of the model (for instance '25.1')."""
        return '.'.join(str(i) for i in self.idf.idd_version[:2])

    def _scan_zones(self) -> None:
        if len(get_people_objects(self.idf)) == 0:
            raise ValueError(
                'The model has no People objects or People:Instance objects (EnergyPlus 26.2 and later). '
                'accim finds the occupied zones in these objects and adds the thermal comfort models to them '
                '(to the People:Definition objects of the People:Instance objects), so the model needs at least one.'
            )
        self.targets: List[Target] = resolve_targets(self.idf)
        # In the order of the targets, so that the output IDFs are the same in every run
        self.occupied_zones_orig = list(dict.fromkeys(t.zone_name for t in self.targets))
        self.occupied_zones = [z.replace(' ', '_').replace(':', '_') for z in self.occupied_zones_orig]
        self.ems_names = [t.ems_suffix for t in self.targets]
        self.ems_keys = [t.sensor_key for t in self.targets]
        self.ems_zones = [t.zone_name for t in self.targets]
        # The occupancy of a zone with several occupant instances is the 'Zone People Occupant Count' of the zone
        self.occupancy_keys = [t.occupancy_key for t in self.targets]
        self.occupancy_variables = [t.occupancy_variable for t in self.targets]
        self.uses_spaces = len(try_objects(self.idf, 'SPACELIST')) > 0 or len(try_objects(self.idf, 'SPACE')) > 0

    def _scan_windows(self) -> None:
        idf = self.idf
        if not any(stl.Name.lower() == 'fractional' for stl in idf.idfobjects['ScheduleTypeLimits']):
            idf.newidfobject('ScheduleTypeLimits', Name='Fractional', Lower_Limit_Value=0, Upper_Limit_Value=1,
                             Numeric_Type='Continuous', Unit_Type='dimensionless')
        if len(idf.idfobjects['AirflowNetwork:SimulationControl']) > 0:
            self.natural_ventilation_type = 'AFN'
            openings = [w.Name for w in idf.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening']
                        if w.Name.endswith('_Win') or w.Name.endswith('_Door')]
            for opening in openings:
                for zone in self.occupied_zones_orig:
                    if opening.split('_')[0].lower() == zone.lower():
                        self.windows_orig.append(opening)
            self.windows = [w.replace(':', '_') for w in self.windows_orig]
            self.window_zones = [w.split('_')[0] for w in self.windows_orig]
            return

        # Without an AirflowNetwork, the ventilation objects of each zone open through a new schedule,
        # as a virtual window '<zone>_Win'
        self.natural_ventilation_type = 'Scheduled'
        schedules = idf.idfobjects['Schedule:Constant']

        def ventilation_schedule(zone):
            name = f'Vent_Sch_{zone}'
            if not any(s.Name == name for s in schedules):
                idf.newidfobject('Schedule:Constant', Name=name, Schedule_Type_Limits_Name='Fractional',
                                 Hourly_Value=0)
            return name

        def add_virtual_window(zone, schedule, always):
            window = f'{zone}_Win'
            if always or window not in self.windows_orig:
                self.windows_orig.append(window)
                self.windows.append(window.replace(':', '_'))
                self.window_zones.append(zone)
                self.scheduled_ventilation[window] = schedule

        for vent in idf.idfobjects['ZoneVentilation:WindandStackOpenArea']:
            for zone in self.occupied_zones_orig:
                if vent.Zone_or_Space_Name.lower() == zone.lower():
                    vent.Opening_Area_Fraction_Schedule_Name = ventilation_schedule(zone)
                    add_virtual_window(zone, vent.Opening_Area_Fraction_Schedule_Name, always=True)
        for vent in idf.idfobjects['ZoneVentilation:DesignFlowRate']:
            for zone in self.occupied_zones_orig:
                if vent.Zone_or_Space_Name.lower() == zone.lower():
                    if 'infiltration' in vent.Name.lower():
                        continue
                    vent.Schedule_Name = ventilation_schedule(zone)
                    add_virtual_window(zone, vent.Schedule_Name, always=False)

    def _ems_name_of_zone(self, zone_name: str) -> str:
        zone_upper = zone_name.upper()
        for ems_zone, ems_name in zip(self.ems_zones, self.ems_names):
            if ems_zone.upper() == zone_upper:
                return ems_name
        if ':' in zone_name:
            return zone_upper.replace(':', '_')
        spaces = [s.Name.upper() for s in try_objects(self.idf, 'SPACE') if s.Zone_Name.upper() == zone_upper]
        return spaces[0] if spaces else zone_upper.replace(':', '_').replace(' ', '_')

    def _scan_thermostats(self) -> None:
        thermostats = list(self.idf.idfobjects['ZONECONTROL:THERMOSTAT'])
        for setpoint_type in THERMOSTAT_SETPOINT_TYPES:
            group = ThermostatGroup(setpoint_type)
            if len(self.idf.idfobjects[setpoint_type]) > 0:
                for thermostat in thermostats:
                    if thermostat.Control_1_Object_Type in setpoint_type:
                        group.zones.append(thermostat.Zone_or_ZoneList_Name.upper())
                        group.ems_names.append(self._ems_name_of_zone(thermostat.Zone_or_ZoneList_Name))
                        group.setpoint_names.append(thermostat.Control_1_Name)
            self.thermostat_groups.append(group)
        for group in self.thermostat_groups:
            if len(group.setpoint_names) == 0:
                self.log(f'There are no {group.setpoint_type} objects in the model')
            else:
                self.log(f'Regarding {group.setpoint_type} objects:',
                         f'The zones with {group.setpoint_type} are:', *group.zones,
                         f'And the existing ThermostatSetpoint objects related to {group.setpoint_type} are:',
                         *group.setpoint_names)
        # All zones with thermostats, regardless of the type of thermostat setpoint object
        self.zones_orig = list(dict.fromkeys(z for group in self.thermostat_groups for z in group.zones))
        if self.uses_spaces:
            self.zones = [z.replace(' ', '_') for z in self.zones_orig]
        else:
            self.zones = [z.replace(':', '_') for z in self.zones_orig]
