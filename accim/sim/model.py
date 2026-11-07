# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The model to which accim adds the ACCIS: its occupied zones, windows and HVAC systems."""

import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from accim.sim.arguments import MIXED_MODE_SCRIPT_TYPES
from accim.sim.targets import Target, resolve_targets, sanitize_ems_name
from accim.sim.windows import (
    afn_openings,
    control_ventilation_objects,
    release_occupant_ventilation_controls,
    remove_hybrid_ventilation_managers,
    simulates_air_distribution_with_windows,
    uses_airflow_network,
)
from accim.utils.people import get_people_objects

__all__ = ['AccimModel', 'ThermostatGroup']

#: Thermostat setpoint objects of the existing HVAC systems that accim controls
#: (ThermostatSetpoint:SingleHeatingOrCooling is not supported).
THERMOSTAT_SETPOINT_TYPES = (
    'ThermostatSetpoint:SingleHeating',
    'ThermostatSetpoint:SingleCooling',
    'ThermostatSetpoint:DualSetpoint',
)
#: The objects that name a thermostat (ZoneControl:Thermostat; the object-list ZoneControlThermostaticNames of the
#: IDD), and their field of its name: those of a ZoneList thermostat are copied for each zone of the list.
_THERMOSTAT_REFERENCES = (
    ('ZoneControl:Thermostat:OperativeTemperature', 'Thermostat_Name'),
    ('ZoneControl:Thermostat:TemperatureAndHumidity', 'Thermostat_Name'),
    ('FaultModel:ThermostatOffset', 'Thermostat_Name'),
)
#: The objects that name several thermostats ('Thermostat 1 Name'...): a ZoneList thermostat is replaced with those of
#: the zones of the list.
_THERMOSTAT_LISTS = ('DemandManager:Thermostats',)


def _replace_thermostat(manager, name: str, names: List[str]) -> None:
    """Replace a thermostat with others in the thermostats of an object ('Thermostat 1 Name'...)."""
    if 'Thermostat_1_Name' not in manager.fieldnames:
        return
    first = manager.fieldnames.index('Thermostat_1_Name')
    current = [str(value).strip() for value in manager.fieldvalues[first:] if str(value).strip()]
    if name.upper() not in {value.upper() for value in current}:
        return
    replaced = [new for value in current for new in (names if value.upper() == name.upper() else [value])]
    for number, value in enumerate(replaced, start=1):
        setattr(manager, f'Thermostat_{number}_Name', value)


def hvac_template_types(idf) -> List[str]:
    """The types of the HVACTemplate objects of a model (EnergyPlus expands them into HVAC objects when it runs with
    ExpandObjects)."""
    types = []
    for key in idf.idfobjects:
        objects = idf.idfobjects[key]
        if str(key).upper().startswith('HVACTEMPLATE:') and len(objects):
            types.append(objects[0].objidd[0].get('idfobj', key) if objects[0].objidd else key)
    return types


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


class AccimModel:
    """An EnergyPlus model (eppy or besos IDF object) to which accim adds the ACCIS.

    Scanning the model finds its occupied zones and, depending on the script type, the windows and
    doors that open for natural ventilation (which, without an AirflowNetwork, are the ventilation
    objects of the zones, controlled through new schedules) and the thermostats of the existing HVAC systems.

    :param idf: The eppy or besos IDF object. It is modified in place.
    :param script_type: 'vrf_ac', 'vrf_mm', 'ex_ac' or 'ex_mm'.
    :param setpoint_type: 'temperature' or 'pmv'.
    :param verbose: True to print the process.
    :param hvac_zone_map: Not used (deprecated since accim 1.0.0): 'ex_mm' no longer needs the zone of each existing
        HVAC object.
    :param name: The name of the model in the messages.
    :raises ValueError: If the model has no People or People:Instance objects.
    :ivar targets: The targets of the EMS (one per occupied zone).
    :ivar occupied_zones_orig: The names of the occupied zones.
    :ivar occupied_zones: The same names with '_' instead of ' ' and ':'.
    :ivar ems_names: The name of each target in the EMS objects.
    :ivar windows_orig: The names of the windows and doors that open (mixed mode only): the surfaces of the
        AirflowNetwork openings, or the virtual windows '<zone>_Win' of the scheduled natural ventilation (see
        :mod:`accim.sim.windows`).
    :ivar windows: The names of the windows and doors in the EMS objects (any character but letters, digits and '_'
        becomes '_').
    :ivar window_zones: The zone of each window or door.
    :ivar zones_orig: The names of the zones that accim controls.
    :ivar zones: The same names, as in the names of the EMS objects.
    :ivar ideal_loads_backups: The names of the backup ideal loads air systems that accim adds to the occupied zones
        (``existing_hvac_ideal_loads_backup``), whose outputs it adds.
    :ivar radiant_zones: The occupied zones whose radiant systems, ventilated slabs or cooling panels follow the
        setpoints of accim (``existing_hvac_radiant_setpoints``).
    :ivar not_working: True if accim cannot work with the model, so that AddAccis writes no output IDFs from it.
    """

    def __init__(
        self,
        idf,
        script_type: str,
        setpoint_type: str,
        verbose: bool = True,
        hvac_zone_map: Optional[Dict[str, str]] = None,
        name: Optional[str] = None,
    ):
        self.idf = idf
        self.script_type = script_type
        self.setpoint_type = setpoint_type
        self.verbose = verbose
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
        self.ideal_loads_backups: List[str] = []
        self.radiant_zones: List[str] = []

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
            self._check_hvac_templates()
            self._split_zone_list_thermostats()
            self._scan_thermostats()

    def log(self, *lines) -> None:
        """Print the lines if verbose is True."""
        if self.verbose:
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
        # The Space and SpaceList objects exist since EnergyPlus 9.6 (the keys of idfobjects are in capitals)
        self.uses_spaces = bool(self.idf.idfobjects.get('SPACELIST')) or bool(self.idf.idfobjects.get('SPACE'))

    def _scan_windows(self) -> None:
        """Find the windows and doors that open in the occupied zones, and give the EMS their control (see
        :mod:`accim.sim.windows`)."""
        idf = self.idf
        if idf.getobject('ScheduleTypeLimits', 'Fractional') is None:
            idf.newidfobject('ScheduleTypeLimits', Name='Fractional', Lower_Limit_Value=0, Upper_Limit_Value=1,
                             Numeric_Type='Continuous', Unit_Type='dimensionless')
        changes = []
        if uses_airflow_network(idf):
            self.natural_ventilation_type = 'AFN'
            for surface, zone in afn_openings(idf, self.occupied_zones_orig):
                self._add_window(surface, zone)
            released = release_occupant_ventilation_controls(idf, self.windows_orig)
            if released:
                changes.append(f'the occupant ventilation controls of the AirflowNetwork surfaces {released} have '
                               f'been removed')
            # The EMS actuators of the model on the same windows: the last program that runs gives their opening
            names = {window.upper() for window in self.windows_orig}
            actuators = [str(a.Name) for a in idf.idfobjects['EnergyManagementSystem:Actuator']
                         if str(a.Actuated_Component_Unique_Name).strip().upper() in names
                         and str(a.Actuated_Component_Type).strip().upper() == 'AIRFLOW NETWORK WINDOW/DOOR OPENING']
            if actuators:
                warnings.warn(f'The EMS actuators {actuators} of the model {self.name} also give the opening factors '
                              f'of windows that accim opens and closes: in each timestep, the opening is that of the '
                              f'last EMS program that sets it. Remove them, or their programs, for the mixed mode of '
                              f'accim.', stacklevel=4)
        else:
            # Without an AirflowNetwork, the ventilation objects of each zone open through a new schedule,
            # as a virtual window '<zone>_Win'
            self.natural_ventilation_type = 'Scheduled'

            def ventilation_schedule(zone):
                name = f'Vent_Sch_{zone}'
                if idf.getobject('Schedule:Constant', name) is None:
                    idf.newidfobject('Schedule:Constant', Name=name, Schedule_Type_Limits_Name='Fractional',
                                     Hourly_Value=0)
                return name

            controlled = control_ventilation_objects(idf, self.occupied_zones_orig, ventilation_schedule, self.log)
            for zone, schedule in controlled.items():
                window = f'{zone}_Win'
                self._add_window(window, zone)
                self.scheduled_ventilation[window] = schedule
        managers = remove_hybrid_ventilation_managers(idf) if self.windows else []
        if managers:
            changes.append(f'the AvailabilityManager:HybridVentilation objects {managers} have been removed')
        kept = [str(m.Name) for m in idf.idfobjects['AvailabilityManager:HybridVentilation']]
        if kept and simulates_air_distribution_with_windows(idf):
            warnings.warn(f'The AvailabilityManager:HybridVentilation objects {kept} of the model {self.name} stay, '
                          f'since its AirflowNetwork simulates the air distribution system together with the windows '
                          f'(MultizoneWithDistribution): they switch the air loops off when they let the windows open, '
                          f'and keep closed the windows that the EMS opens otherwise, so the windows open only when '
                          f'both allow it.', stacklevel=4)
        controls = idf.idfobjects['AirflowNetwork:SimulationControl']
        if self.windows and controls and str(controls[0].AirflowNetwork_Control).strip().upper() == \
                'MULTIZONEWITHDISTRIBUTIONONLYDURINGFANOPERATION':
            warnings.warn(f'The AirflowNetwork of the model {self.name} simulates the air distribution system only '
                          f'while its fans run (MultizoneWithDistributionOnlyDuringFanOperation), and EnergyPlus '
                          f'simulates the ZoneVentilation objects (the windows that accim opens and closes) only while '
                          f'they do not: the windows do not ventilate while the fans run, although the EMS opens them.',
                          stacklevel=4)
        if changes:
            warnings.warn(f'In mixed mode, accim opens and closes the windows of the model {self.name} with the EMS, '
                          f'so {"; and ".join(changes)}: they would override it.', stacklevel=4)
        with_windows = {zone.upper() for zone in self.window_zones}
        without = [zone for zone in self.occupied_zones_orig if zone.upper() not in with_windows]
        if without:
            kind = ('exterior windows, doors or glass doors with AirflowNetwork openings'
                    if self.natural_ventilation_type == 'AFN' else
                    'natural ventilation (ZoneVentilation:WindandStackOpenArea objects, or '
                    'ZoneVentilation:DesignFlowRate objects of the type Natural)')
            warnings.warn(f'The occupied zones {without} of the model {self.name} have no {kind}, so in mixed mode '
                          f'they are only air-conditioned: accim cannot open their windows.', stacklevel=4)

    def _add_window(self, window: str, zone: str) -> None:
        """Add a window or door that opens, with a name for the EMS objects that is valid and unique."""
        ems_name = sanitize_ems_name(window)
        used = {name.upper() for name in self.windows}
        number = 1
        while (ems_name if number == 1 else f'{ems_name}_{number}').upper() in used:
            number += 1
        self.windows_orig.append(window)
        self.windows.append(ems_name if number == 1 else f'{ems_name}_{number}')
        self.window_zones.append(zone)

    def _ems_name_of_zone(self, zone_name: str) -> str:
        zone_upper = zone_name.upper()
        for ems_zone, ems_name in zip(self.ems_zones, self.ems_names):
            if ems_zone.upper() == zone_upper:
                return ems_name
        if ':' in zone_name:
            return zone_upper.replace(':', '_')
        spaces = [s.Name.upper() for s in self.idf.idfobjects.get('SPACE', []) if s.Zone_Name.upper() == zone_upper]
        return spaces[0] if spaces else zone_upper.replace(':', '_').replace(' ', '_')

    def _check_hvac_templates(self) -> None:
        """Stop if the model has HVACTemplate objects: accim cannot change the thermostats and HVAC objects that
        EnergyPlus makes from them when it runs (AddAccis expands them before)."""
        types = hvac_template_types(self.idf)
        if types:
            raise ValueError(
                f'The model {self.name} has HVACTemplate objects ({", ".join(types)}), which EnergyPlus expands into '
                f'HVAC objects when it runs (ExpandObjects), so accim cannot give their thermostats the setpoints of '
                f'the ACCIS. Expand them first: accim.energyplus.expand_objects(path) writes the model with the HVAC '
                f'objects instead (AddAccis does it for its input IDFs).')

    def _split_zone_list_thermostats(self) -> None:
        """Give each zone of a ZoneList thermostat with occupied zones a thermostat of its own.

        accim controls each occupied zone with its own setpoints, so it needs a ZoneControl:Thermostat object for each
        one. Each thermostat (and staged thermostat, ZoneControl:Thermostat:StagedDualSetpoint) of a ZoneList with
        occupied zones is replaced with one thermostat per zone of the list, named '<zone> <thermostat>', as EnergyPlus
        names the thermostats of the zones of a ZoneList, with its controls;
        so are its ZoneControl:Thermostat:OperativeTemperature, ZoneControl:Thermostat:TemperatureAndHumidity and
        FaultModel:ThermostatOffset objects, and the demand managers (DemandManager:Thermostats) that name it name
        the thermostats of the zones instead. The thermostats of ZoneLists without occupied zones do not change.
        """
        idf = self.idf
        zone_lists = {str(z.Name).strip().upper(): [str(m).strip() for m in z.fieldvalues[2:] if str(m).strip()]
                      for z in idf.idfobjects['ZoneList']}
        occupied = {zone.upper() for zone in self.occupied_zones_orig}
        thermostats = [*idf.idfobjects['ZoneControl:Thermostat'],
                       *idf.idfobjects['ZoneControl:Thermostat:StagedDualSetpoint']]
        for thermostat in thermostats:
            name, zone_list = str(thermostat.Name).strip(), str(thermostat.Zone_or_ZoneList_Name).strip()
            zones = zone_lists.get(zone_list.upper())
            if not zones or not any(zone.upper() in occupied for zone in zones):
                continue
            staged = thermostat.key.upper() == 'ZONECONTROL:THERMOSTAT:STAGEDDUALSETPOINT'
            references = [] if staged else [
                (name_field, obj) for object_type, name_field in _THERMOSTAT_REFERENCES
                for obj in idf.idfobjects.get(object_type.upper(), [])
                if str(getattr(obj, name_field)).strip().upper() == name.upper()]
            for zone in zones:
                copy = idf.copyidfobject(thermostat)
                copy.Name = f'{zone} {name}'
                copy.Zone_or_ZoneList_Name = zone
                for name_field, reference in references:
                    reference_copy = idf.copyidfobject(reference)
                    setattr(reference_copy, name_field, copy.Name)
                    if 'Name' in reference_copy.fieldnames:
                        reference_copy.Name = f'{zone} {reference.Name}'
            for _, reference in references:
                idf.removeidfobject(reference)
            for object_type in [] if staged else _THERMOSTAT_LISTS:
                for manager in idf.idfobjects.get(object_type.upper(), []):
                    _replace_thermostat(manager, name, [f'{zone} {name}' for zone in zones])
            idf.removeidfobject(thermostat)
            self.log(f'The thermostat {name} of the ZoneList {zone_list} has been replaced with one thermostat per '
                     f'zone of the list ("<zone> {name}"), so that each occupied zone gets its own setpoints')

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
