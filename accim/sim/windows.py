# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The windows and doors that accim opens and closes in mixed mode ('vrf_mm' and 'ex_mm').

With an AirflowNetwork that simulates the multizone airflows (AirflowNetwork Control MultizoneWithoutDistribution or
MultizoneWithDistribution), they are the windows, doors and glass doors of the exterior surfaces of the occupied zones
whose AirflowNetwork:MultiZone:Surface objects have an opening (an AirflowNetwork:MultiZone:Component:DetailedOpening,
SimpleOpening or HorizontalOpening), whatever their names: the EMS actuates their venting opening factor, which
replaces their venting control. The openings of the interior surfaces (doors between zones...) keep the control of the
model. An occupant ventilation control of these surfaces (AirflowNetwork:OccupantVentilationControl) would override
the EMS, so accim removes it from them.

Otherwise, the natural ventilation of the model is that of its ZoneVentilation:WindandStackOpenArea objects and of its
ZoneVentilation:DesignFlowRate objects of the type Natural (not those whose names contain 'infiltration'; the types
Exhaust, Intake and Balanced are fans, not windows): those of each occupied zone open with a schedule of the zone,
'Vent_Sch_<zone>', which the EMS actuates as a virtual window '<zone>_Win'. The EMS decides when they ventilate (with
the indoor and outdoor temperatures and the wind speed), so their own limits (minimum and maximum indoor and outdoor
temperatures, delta temperature, maximum wind speed) are removed: otherwise they would keep the windows closed when the
EMS opens them. The objects can be assigned to a zone, a space, or a ZoneList or SpaceList: those of a list with
occupied zones are replaced with one object per zone or space of the list ('<zone or space> <name>'), so that each zone
opens with its own schedule.

The AvailabilityManager:HybridVentilation objects also open and close the windows (and switch the HVAC systems on and
off), and override the EMS, so accim removes them in mixed mode if it opens and closes windows, unless the
AirflowNetwork simulates the air distribution system together with the windows (MultizoneWithDistribution): then they
stay, so that the air loops are off while the windows are open, and the windows open only when both the EMS and they
let them. With MultizoneWithDistributionOnlyDuringFanOperation, EnergyPlus simulates the ZoneVentilation objects only
while the fans of the distribution system are off.
"""

from typing import Callable, Dict, Iterable, List, Optional, Tuple

__all__ = [
    'OPENING_COMPONENTS',
    'VENTILATION_LIMITS',
    'VENTILATION_OBJECTS',
    'afn_openings',
    'control_ventilation_objects',
    'exterior_subsurface_zones',
    'is_natural_ventilation',
    'release_occupant_ventilation_controls',
    'remove_hybrid_ventilation_managers',
    'simulates_air_distribution_with_windows',
    'subsurface_zones',
    'uses_airflow_network',
]

#: The components of the AirflowNetwork:MultiZone:Surface objects that open (their venting opening factor).
OPENING_COMPONENTS = (
    'AirflowNetwork:MultiZone:Component:DetailedOpening',
    'AirflowNetwork:MultiZone:Component:SimpleOpening',
    'AirflowNetwork:MultiZone:Component:HorizontalOpening',
)
#: The ventilation objects of the scheduled natural ventilation, with the field of their schedule (names of eppy).
VENTILATION_OBJECTS = (
    ('ZoneVentilation:WindandStackOpenArea', 'Opening_Area_Fraction_Schedule_Name'),
    ('ZoneVentilation:DesignFlowRate', 'Schedule_Name'),
)
#: The limits of the ZoneVentilation objects (names of eppy) and the values that remove them (the defaults of the IDD):
#: the EMS decides when the windows open. The fields of their schedules are emptied.
VENTILATION_LIMITS = {
    'Minimum_Indoor_Temperature': -100,
    'Maximum_Indoor_Temperature': 100,
    'Delta_Temperature': -100,
    'Minimum_Outdoor_Temperature': -100,
    'Maximum_Outdoor_Temperature': 100,
    'Maximum_Wind_Speed': 40,
}
#: The base surfaces with the fields 'Zone Name' and 'Outside Boundary Condition'.
_DETAILED_SURFACES = ('BuildingSurface:Detailed', 'Wall:Detailed', 'RoofCeiling:Detailed', 'Floor:Detailed')
#: The base surfaces of the simplified geometry that face the outdoors.
_EXTERIOR_SURFACES = ('Wall:Exterior', 'Roof')
#: The other base surfaces of the simplified geometry.
_INTERIOR_SURFACES = ('Wall:Adiabatic', 'Wall:Underground', 'Wall:Interzone', 'Ceiling:Adiabatic', 'Ceiling:Interzone',
                      'Floor:GroundContact', 'Floor:Adiabatic', 'Floor:Interzone')
#: The windows, doors and glass doors (with the field 'Building Surface Name').
_SUBSURFACES = ('FenestrationSurface:Detailed', 'Window', 'Door', 'GlazedDoor', 'Window:Interzone', 'Door:Interzone',
                'GlazedDoor:Interzone')


def _objects(idf, object_type: str) -> list:
    """The objects of a type, or none if the IDD of the model does not have it (eppy and besos take the type in
    capitals)."""
    return list(idf.idfobjects.get(object_type.upper(), []))


def _text(value) -> str:
    return '' if value is None else str(value).strip()


def uses_airflow_network(idf) -> bool:
    """True if the windows of the model are those of its AirflowNetwork: it has an AirflowNetwork:SimulationControl
    object whose AirflowNetwork Control simulates the multizone airflows (MultizoneWithoutDistribution or
    MultizoneWithDistribution). With NoMultizoneOrDistribution (the default) and
    MultizoneWithDistributionOnlyDuringFanOperation, EnergyPlus does not simulate them, but the ZoneVentilation objects
    (the latter, while the fans are off)."""
    controls = _objects(idf, 'AirflowNetwork:SimulationControl')
    if not controls:
        return False
    control = _text(getattr(controls[0], 'AirflowNetwork_Control', '')) or 'NoMultizoneOrDistribution'
    return control.upper() in ('MULTIZONEWITHOUTDISTRIBUTION', 'MULTIZONEWITHDISTRIBUTION')


def exterior_subsurface_zones(idf) -> Dict[str, str]:
    """The zone of each window, door and glass door of an exterior surface (whose outside boundary condition is
    Outdoors): {name in capitals: zone}."""
    return {name: zone for name, (zone, exterior) in _subsurfaces(idf).items() if exterior}


def subsurface_zones(idf) -> Dict[str, str]:
    """The zone of each window, door and glass door (that of its base surface), exterior or not: {name in capitals:
    zone}."""
    return {name: zone for name, (zone, _) in _subsurfaces(idf).items()}


def _subsurfaces(idf) -> Dict[str, Tuple[str, bool]]:
    """The zone of each window, door and glass door, and whether its base surface is exterior: {name in capitals:
    (zone, exterior)}."""
    base: Dict[str, Tuple[str, bool]] = {}
    for object_type in _DETAILED_SURFACES:
        for surface in _objects(idf, object_type):
            exterior = _text(surface.Outside_Boundary_Condition).upper() == 'OUTDOORS'
            base[_text(surface.Name).upper()] = (_text(surface.Zone_Name), exterior)
    for object_type in _EXTERIOR_SURFACES:
        for surface in _objects(idf, object_type):
            base[_text(surface.Name).upper()] = (_text(surface.Zone_Name), True)
    for object_type in _INTERIOR_SURFACES:
        for surface in _objects(idf, object_type):
            base[_text(surface.Name).upper()] = (_text(surface.Zone_Name), False)
    subsurfaces: Dict[str, Tuple[str, bool]] = {}
    for object_type in _SUBSURFACES:
        for subsurface in _objects(idf, object_type):
            zone, exterior = base.get(_text(subsurface.Building_Surface_Name).upper(), ('', False))
            if zone:
                subsurfaces[_text(subsurface.Name).upper()] = (zone, exterior)
    return subsurfaces


def afn_openings(idf, zones: Iterable[str]) -> List[Tuple[str, str]]:
    """The windows and doors of the AirflowNetwork that open in some zones: (surface, zone) of each exterior window,
    door or glass door of these zones whose AirflowNetwork:MultiZone:Surface object has an opening component (see
    :data:`OPENING_COMPONENTS`), in the order of these objects. The zone is given as in ``zones``."""
    occupied = {zone.upper(): zone for zone in zones}
    components = {_text(c.Name).upper() for object_type in OPENING_COMPONENTS for c in _objects(idf, object_type)}
    subsurface_zones = exterior_subsurface_zones(idf)
    openings: List[Tuple[str, str]] = []
    seen = set()
    for surface in _objects(idf, 'AirflowNetwork:MultiZone:Surface'):
        if _text(surface.Leakage_Component_Name).upper() not in components:
            continue
        name = _text(surface.Surface_Name)
        zone = subsurface_zones.get(name.upper(), '')
        if zone.upper() not in occupied or name.upper() in seen:
            continue
        seen.add(name.upper())
        openings.append((name, occupied[zone.upper()]))
    return openings


def _members(idf) -> Callable[[str], List[Tuple[str, str]]]:
    """A function that gives the zones or spaces of a field 'Zone or ZoneList or Space or SpaceList Name': [(zone or
    space, its zone)]; one item for a zone or a space, one per member for a ZoneList or a SpaceList."""
    spaces = {_text(s.Name).upper(): _text(s.Zone_Name) for s in _objects(idf, 'Space')}
    space_lists = {_text(s.Name).upper(): [_text(m) for m in s.fieldvalues[2:] if _text(m)]
                   for s in _objects(idf, 'SpaceList')}
    zone_lists = {_text(z.Name).upper(): [_text(m) for m in z.fieldvalues[2:] if _text(m)]
                  for z in _objects(idf, 'ZoneList')}

    def members(name: str) -> List[Tuple[str, str]]:
        key = name.upper()
        if key in spaces:
            return [(name, spaces[key])]
        if key in space_lists:
            return [(space, spaces.get(space.upper(), space)) for space in space_lists[key]]
        if key in zone_lists:
            return [(zone, zone) for zone in zone_lists[key]]
        return [(name, name)]

    return members


def is_natural_ventilation(object_type: str, vent) -> bool:
    """True if a ZoneVentilation object is natural ventilation (windows): a ZoneVentilation:WindandStackOpenArea
    object, or a ZoneVentilation:DesignFlowRate object of the type Natural (the default) whose name does not contain
    'infiltration'."""
    if object_type.upper() != 'ZONEVENTILATION:DESIGNFLOWRATE':
        return True
    if 'infiltration' in _text(vent.Name).lower():
        return False
    kind = _text(getattr(vent, 'Ventilation_Type', '')) if 'Ventilation_Type' in vent.fieldnames else ''
    return kind.upper() in ('', 'NATURAL')


def _take_control(vent, schedule_field: str, schedule: str) -> List[str]:
    """Make a ZoneVentilation object open with a schedule, without limits of its own (see
    :data:`VENTILATION_LIMITS`); return the limits that it had."""
    setattr(vent, schedule_field, schedule)
    removed = []
    for field, value in VENTILATION_LIMITS.items():
        if field in vent.fieldnames:
            current = _text(getattr(vent, field))
            if current and current != str(value):
                try:
                    differs = float(current) != float(value)
                except ValueError:
                    differs = True
                if differs:
                    removed.append(f'{field} {current}')
            setattr(vent, field, value)
        schedule_name = f'{field}_Schedule_Name'
        if schedule_name in vent.fieldnames and _text(getattr(vent, schedule_name)):
            removed.append(f'{schedule_name} {_text(getattr(vent, schedule_name))}')
            setattr(vent, schedule_name, '')
    return removed


def control_ventilation_objects(idf, zones: Iterable[str], schedule: Callable[[str], str],
                                log: Optional[Callable[..., None]] = None) -> Dict[str, str]:
    """Make the natural ventilation objects of some zones open with the schedule of their zone, without limits of
    their own.

    The objects (see :data:`VENTILATION_OBJECTS` and :func:`is_natural_ventilation`) assigned to one of these zones,
    or to a space of one of them, get the schedule of the zone, and their limits are removed (see
    :data:`VENTILATION_LIMITS`). Those assigned to a ZoneList or SpaceList with some of these zones are replaced with
    one object per zone or space of the list, named '<zone or space> <name>' (as EnergyPlus names their instances), with
    the schedule of the zone and without limits if it is one of these zones, and as they were otherwise.

    :param zones: The zones (the occupied zones).
    :param schedule: The function that gives the schedule of a zone (and adds it to the model).
    :param log: The function that prints the changes.
    :return: The schedule of each zone whose ventilation objects open with it, in the order of the objects.
    """
    log = log or (lambda *lines: None)
    occupied = {zone.upper(): zone for zone in zones}
    members_of = _members(idf)
    controlled: Dict[str, str] = {}

    def control(object_type, vent, schedule_field, zone):
        controlled.setdefault(zone, schedule(zone))
        removed = _take_control(vent, schedule_field, controlled[zone])
        log(f'The {object_type} {_text(vent.Name)} opens with {controlled[zone]}'
            + (f', without its limits ({", ".join(removed)})' if removed else ''))

    for object_type, schedule_field in VENTILATION_OBJECTS:
        for vent in _objects(idf, object_type):
            if not is_natural_ventilation(object_type, vent):
                continue
            # The third field is the zone (its name depends on the EnergyPlus version: 'Zone Name', 'Zone or Space
            # Name', 'Zone or ZoneList Name', 'Zone or ZoneList or Space or SpaceList Name')
            zone_field = vent.fieldnames[2]
            container = _text(getattr(vent, zone_field))
            members = members_of(container)
            if not any(zone.upper() in occupied for _, zone in members):
                continue
            if len(members) == 1:
                control(object_type, vent, schedule_field, occupied[members[0][1].upper()])
                continue
            for member, zone in members:
                copy = idf.copyidfobject(vent)
                copy.Name = f'{member} {_text(vent.Name)}'
                setattr(copy, zone_field, member)
                if zone.upper() in occupied:
                    control(object_type, copy, schedule_field, occupied[zone.upper()])
            idf.removeidfobject(vent)
            log(f'The {object_type} {_text(vent.Name)} of {container} has been replaced with one object per zone or '
                f'space of {container}, so that each occupied zone opens with its own schedule')
    return controlled


def release_occupant_ventilation_controls(idf, surfaces: Iterable[str]) -> List[str]:
    """Free the AirflowNetwork surfaces of some windows and doors from the occupant ventilation controls
    (AirflowNetwork:OccupantVentilationControl), which override the opening factor of the EMS; return those that had
    one.

    A surface has the occupant ventilation control of its own field 'Occupant Ventilation Control Name', which is
    emptied, or else that of the AirflowNetwork:MultiZone:Zone object of its zone, which EnergyPlus gives to all the
    windows and doors of the zone without one of their own, whatever their ventilation control modes. That of the zone
    is then removed, and given to the other windows and doors of the zone (those that accim does not open and close,
    such as the doors between zones), so that they keep it."""
    names = {surface.upper() for surface in surfaces}
    afn_surfaces = _objects(idf, 'AirflowNetwork:MultiZone:Surface')
    zones_of = subsurface_zones(idf)
    released = []
    for surface in afn_surfaces:
        name = _text(surface.Surface_Name)
        if name.upper() in names and 'Occupant_Ventilation_Control_Name' in surface.fieldnames \
                and _text(surface.Occupant_Ventilation_Control_Name):
            surface.Occupant_Ventilation_Control_Name = ''
            released.append(name)
    zones_with_windows = {zones_of.get(name, '').upper() for name in names}
    for zone in _objects(idf, 'AirflowNetwork:MultiZone:Zone'):
        key = _text(zone.Zone_Name).upper()
        if key not in zones_with_windows or 'Occupant_Ventilation_Control_Name' not in zone.fieldnames:
            continue
        control = _text(zone.Occupant_Ventilation_Control_Name)
        if not control:
            continue
        for surface in afn_surfaces:
            name = _text(surface.Surface_Name)
            if zones_of.get(name.upper(), '').upper() != key:
                continue
            if name.upper() in names:
                if name not in released:
                    released.append(name)
            elif not _text(surface.Occupant_Ventilation_Control_Name):
                surface.Occupant_Ventilation_Control_Name = control
        zone.Occupant_Ventilation_Control_Name = ''
    return released


def simulates_air_distribution_with_windows(idf) -> bool:
    """True if the AirflowNetwork of the model simulates its air distribution system together with the windows
    (AirflowNetwork Control MultizoneWithDistribution): EnergyPlus may then fail to solve the airflows of open windows
    while the fans of the air loops run."""
    controls = _objects(idf, 'AirflowNetwork:SimulationControl')
    return bool(controls) and _text(getattr(controls[0], 'AirflowNetwork_Control', '')).upper() == \
        'MULTIZONEWITHDISTRIBUTION'


def remove_hybrid_ventilation_managers(idf) -> List[str]:
    """Remove the AvailabilityManager:HybridVentilation objects, which open and close the windows (those of an
    AirflowNetwork, or the ZoneVentilation objects of the zones of their air loops, not only the one they name) and
    switch the HVAC systems on and off, overriding the EMS of accim in mixed mode; return their names.

    They stay if the AirflowNetwork simulates the air distribution system together with the windows (see
    :func:`simulates_air_distribution_with_windows`): they then switch the air loops off when they let the windows open,
    and without them the EMS would open the windows while the fans run, which EnergyPlus may fail to solve (it stopped
    with the example file AirflowNetwork_MultiZone_SmallOffice_VAV: 'A diagonal entity is zero in AirflowNetwork
    matrix').
    """
    if simulates_air_distribution_with_windows(idf):
        return []
    managers = _objects(idf, 'AvailabilityManager:HybridVentilation')
    for manager in managers:
        idf.removeidfobject(manager)
    return [_text(manager.Name) for manager in managers]
