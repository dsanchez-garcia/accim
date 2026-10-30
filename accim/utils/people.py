# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The occupants, zones and spaces of the models: the People and People:Instance objects, and the
instances, spaces and hierarchies that EnergyPlus creates from them.

These functions read the IDF objects of eppy or besos, and do not import besos."""

from typing import Any, Dict, List, Optional, Tuple, Union

__all__ = [
    'SURFACE_OBJECTS_WITH_SPACE_NAME',
    'get_energyplus_spaces',
    'get_idf_hierarchy',
    'get_idf_hierarchy_with_people',
    'get_people_definition',
    'get_people_hierarchy',
    'get_people_instances',
    'get_people_names_for_ems',
    'get_people_objects',
    'get_spaces_from_spacelist',
    'is_people_instance',
]

#: The IDF object of a model (eppy or besos)
IDF = Any


def get_people_objects(idf: IDF) -> List[Any]:
    """
    Returns the objects that place the occupants in the model: the People objects and the
    People:Instance objects, which EnergyPlus 26.2 introduced.

    A People:Instance object has the fields of a People object that accim reads: the name, the
    Zone, ZoneList, Space or SpaceList, and the schedules (occupancy, activity, work efficiency,
    clothing insulation and air velocity). EnergyPlus also names their outputs in the same way, so
    accim handles both alike. The number of people and the thermal comfort models of a
    People:Instance object are in the People:Definition object it references
    (see `get_people_definition`).

    Args:
        idf (IDF): The IDF model object.

    Returns:
        List[Any]: The People objects, followed by the People:Instance objects.
    """
    people_objs = list(idf.idfobjects['PEOPLE'])
    try:
        people_objs.extend(idf.idfobjects['PEOPLE:INSTANCE'])
    except KeyError:
        # The IDDs before EnergyPlus 26.2 have no People:Instance objects
        pass
    return people_objs


def is_people_instance(people_obj: Any) -> bool:
    """
    Returns True if the object is a People:Instance object (EnergyPlus 26.2 and later), and False
    if it is a People object.

    Args:
        people_obj (Any): An object returned by `get_people_objects`.
    """
    return str(getattr(people_obj, 'key', '')).upper() == 'PEOPLE:INSTANCE'


def get_people_definition(idf: IDF, people_instance: Any) -> Optional[Any]:
    """
    Returns the People:Definition object referenced by a People:Instance object
    (EnergyPlus 26.2 and later).

    Args:
        idf (IDF): The IDF model object.
        people_instance (Any): A People:Instance object of the model.

    Returns:
        Optional[Any]: The People:Definition object, or None if the model has none with that name.
    """
    definition_name = str(people_instance.People_Definition_Name).strip().upper()
    for definition in idf.idfobjects['PEOPLE:DEFINITION']:
        if str(definition.Name).strip().upper() == definition_name:
            return definition
    return None


# Classes of heat transfer surfaces with a 'Space Name' field. In a zone with Space objects, EnergyPlus
# creates the space '<Zone Name>-Remainder' for the surfaces of these classes without a Space Name.
# Subsurfaces take the space of their base surface, and InternalMass and shading surfaces do not count.
SURFACE_OBJECTS_WITH_SPACE_NAME = (
    'BuildingSurface:Detailed', 'Wall:Detailed', 'RoofCeiling:Detailed', 'Floor:Detailed',
    'Wall:Exterior', 'Wall:Adiabatic', 'Wall:Underground', 'Wall:Interzone', 'Roof',
    'Ceiling:Adiabatic', 'Ceiling:Interzone', 'Floor:GroundContact', 'Floor:Adiabatic', 'Floor:Interzone',
)


def _get_objects_if_in_idd(idf: IDF, object_type: str) -> List[Any]:
    """Returns the objects of a class, or an empty list if the IDD of the model does not have the class."""
    try:
        return list(idf.idfobjects[object_type.upper()])
    except KeyError:
        return []


def _get_field(obj: Any, field_name: str) -> str:
    """Returns a field of an object as a stripped string, or '' if the object does not have the field."""
    try:
        value = obj[field_name]
    except Exception:
        value = getattr(obj, field_name, '')
    return '' if value is None else str(value).strip()


def get_energyplus_spaces(idf: IDF) -> Dict[str, Dict[str, Any]]:
    """
    Returns the spaces of each zone, as EnergyPlus creates them.

    A zone without Space objects has a default space named like the zone. In a zone with Space
    objects, EnergyPlus also creates a space named '<Zone Name>-Remainder' when some of its heat
    transfer surfaces have a Space Name and others do not (see SURFACE_OBJECTS_WITH_SPACE_NAME;
    subsurfaces, InternalMass and shading surfaces do not count). The IDDs before EnergyPlus
    9.6 have no Space objects, so each zone has its default space.

    Args:
        idf (IDF): The IDF model object.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary whose keys are the zone names in uppercase, and whose
                                   values have the keys 'zone' (the name of the zone), 'spaces' (the
                                   names of its spaces, in the order of the Space objects, with the
                                   remainder space at the end), 'explicit' (True if the zone has
                                   Space objects) and 'remainder' (the name of the remainder space,
                                   or None).
    """
    zones: Dict[str, Dict[str, Any]] = {}

    def zone_entry(zone_name: str) -> Dict[str, Any]:
        key = zone_name.upper()
        if key not in zones:
            zones[key] = {'zone': zone_name, 'spaces': [], 'explicit': False, 'remainder': None}
        return zones[key]

    for zone in _get_objects_if_in_idd(idf, 'Zone'):
        zone_entry(_get_field(zone, 'Name'))
    for space in _get_objects_if_in_idd(idf, 'Space'):
        entry = zone_entry(_get_field(space, 'Zone_Name'))
        entry['spaces'].append(_get_field(space, 'Name'))
        entry['explicit'] = True

    # Zones with heat transfer surfaces with a Space Name, and zones with surfaces without one
    zones_with_space_surfaces = set()
    zones_without_space_surfaces = set()
    for object_type in SURFACE_OBJECTS_WITH_SPACE_NAME:
        for surface in _get_objects_if_in_idd(idf, object_type):
            zone_key = _get_field(surface, 'Zone_Name').upper()
            if _get_field(surface, 'Space_Name'):
                zones_with_space_surfaces.add(zone_key)
            else:
                zones_without_space_surfaces.add(zone_key)

    for key, entry in zones.items():
        if not entry['explicit']:
            entry['spaces'] = [entry['zone']]
        elif key in zones_with_space_surfaces and key in zones_without_space_surfaces:
            entry['remainder'] = f"{entry['zone']}-Remainder"
            entry['spaces'].append(entry['remainder'])
    return zones


def get_people_instances(idf: IDF) -> List[Dict[str, Any]]:
    """
    Returns the instances that EnergyPlus creates for the People objects (and the People:Instance
    objects of EnergyPlus 26.2), with the names it gives them. These names are the keys of their
    outputs, such as 'People Occupant Count' or 'Zone Thermal Comfort Fanger Model PMV', so they
    are the keys that the EMS sensors need.

    EnergyPlus names the instances following the Input Output Reference ('Specifying Applicable
    Zone(s) or Space(s)'), as checked with EnergyPlus 25.2 and 26.2:

    - assigned to a Space: '<People Name>';
    - assigned to a Zone: '<People Name>' if the zone has one space, or else
      '<Space Name> <People Name>' for each space of the zone;
    - assigned to a SpaceList or a ZoneList: '<Space Name> <People Name>' for each space.

    The spaces of a zone are those of `get_energyplus_spaces`: the default space of a zone without
    Space objects is named like the zone, and the remainder space is included. A People:Instance
    object gives its own name to its instances, never the name of its People:Definition.

    Args:
        idf (IDF): The IDF model object.

    Returns:
        List[Dict[str, Any]]: One dictionary per instance, in the order EnergyPlus creates them, with the keys:
            - 'name': the name EnergyPlus gives the instance;
            - 'people': the name of the People (or People:Instance) object;
            - 'space': the space of the instance (a Space object, the default space or the remainder space);
            - 'zone': the zone of the space;
            - 'space_kind': 'explicit' (a Space object), 'default' or 'remainder';
            - 'prefixed': True if the name starts with the name of the space;
            - 'assignment': 'Space', 'SpaceList', 'Zone' or 'ZoneList';
            - 'container': the name in the Zone or ZoneList or Space or SpaceList Name field;
            - 'object': the People (or People:Instance) object.
    """
    zones = get_energyplus_spaces(idf)
    space_to_zone = {
        _get_field(s, 'Name').upper(): _get_field(s, 'Zone_Name') for s in _get_objects_if_in_idd(idf, 'Space')
    }
    space_lists = {_get_field(sl, 'Name').upper(): sl for sl in _get_objects_if_in_idd(idf, 'SpaceList')}
    zone_lists = {_get_field(zl, 'Name').upper(): zl for zl in _get_objects_if_in_idd(idf, 'ZoneList')}

    def list_members(list_obj: Any) -> List[str]:
        # The members of a ZoneList or SpaceList are its fields after the name
        return [str(m).strip() for m in list_obj.obj[2:] if str(m).strip()]

    def zone_spaces(zone_name: str) -> List[Tuple[str, str]]:
        # (space, kind) of each space of a zone. The default space keeps the zone name as written where the
        # zone is referenced, and a zone unknown to the model is handled as a zone without Space objects.
        entry = zones.get(zone_name.upper())
        if entry is None or not entry['explicit']:
            return [(zone_name, 'default')]
        return [(s, 'remainder' if s == entry['remainder'] else 'explicit') for s in entry['spaces']]

    instances = []
    for people in get_people_objects(idf):
        p_name = _get_field(people, 'Name')
        # The name of the field depends on the version of EnergyPlus
        container = ''
        for field_name in ['Zone_or_ZoneList_or_Space_or_SpaceList_Name', 'Zone_or_ZoneList_Name', 'Zone_Name']:
            container = _get_field(people, field_name)
            if container:
                break
        if not container:
            continue
        c_upper = container.upper()

        # (space, zone, kind) of each instance
        if c_upper in space_to_zone:
            assignment = 'Space'
            resolved = [(container, space_to_zone[c_upper], 'explicit')]
            prefixed = False
        elif c_upper in space_lists:
            assignment = 'SpaceList'
            resolved = [(s, space_to_zone.get(s.upper(), s), 'explicit') for s in list_members(space_lists[c_upper])]
            prefixed = True
        elif c_upper in zone_lists:
            assignment = 'ZoneList'
            resolved = [(s, z, kind) for z in list_members(zone_lists[c_upper]) for s, kind in zone_spaces(z)]
            prefixed = True
        else:
            assignment = 'Zone'
            resolved = [(s, container, kind) for s, kind in zone_spaces(container)]
            prefixed = len(resolved) > 1

        for space_name, zone_name, kind in resolved:
            instances.append({
                'name': f'{space_name} {p_name}' if prefixed else p_name,
                'people': p_name,
                'space': space_name,
                'zone': zone_name,
                'space_kind': kind,
                'prefixed': prefixed,
                'assignment': assignment,
                'container': container,
                'object': people,
            })
    return instances


def get_people_hierarchy(idf: IDF) -> Dict[str, Any]:
    """
    Extracts the relationship between People objects and the physical Spaces they occupy.

    Since a 'People' object can reference a Zone, a ZoneList, a Space, or a SpaceList,
    this function resolves all these references down to a list of specific Space names,
    as EnergyPlus does (see `get_people_instances`): the default space of a zone without
    Space objects is named like the zone, and the remainder space of a zone is included.
    The People:Instance objects of EnergyPlus 26.2 are included in the same way.

    Args:
        idf (Union[IDF, IDF_class]): The IDF model object.

    Returns:
        Dict[str, Any]: A dictionary where keys are the names of the People and People:Instance
                        objects and values contain the target reference and the resolved list of spaces.
                        Example:
                        {
                            "Residential Living Occupants": {
                                "target_ref": "Residential - Living Space",
                                "inferred_type": "SpaceList",
                                "affected_spaces": ["Floor_1", "Floor_2"]
                            }
                        }
    """
    # Group the instances by the People object they come from
    instances_by_people: Dict[int, List[Dict[str, Any]]] = {}
    for instance in get_people_instances(idf):
        instances_by_people.setdefault(id(instance['object']), []).append(instance)

    people_hierarchy = {}
    for person in get_people_objects(idf):
        instances = instances_by_people.get(id(person), [])
        people_hierarchy[person.Name] = {
            "target_ref": instances[0]['container'] if instances else _get_field(
                person, 'Zone_or_ZoneList_or_Space_or_SpaceList_Name'),
            "inferred_type": instances[0]['assignment'] if instances else "Unknown",
            "affected_spaces": [i['space'] for i in instances]
        }

    return people_hierarchy


def get_people_names_for_ems(
        idf: IDF,
        output_format: str = 'list'
) -> Union[List[str], Dict[str, List[str]]]:
    """
    Returns the names EnergyPlus gives the instances of the People objects (and the People:Instance
    objects of EnergyPlus 26.2), which are the keys of their outputs in EMS sensors
    (see `get_people_instances`).

    Naming Pattern: "{PeopleName}" for People assigned to a Space or to a Zone of one space,
    and "{SpaceName} {PeopleName}" for each space otherwise.
    Example: "Floor_1 Residential Living Occupants"

    Args:
        idf (IDF): The BESOS IDF model object.
        output_format (str): Controls the structure of the return value.
                             - 'list' (Default): Returns a flat list of all instance names.
                             - 'dict': Returns a dictionary {PeopleName: [InstanceNames]}.

    Returns:
        Union[List[str], Dict[str, List[str]]]: A flat list or a dictionary depending on output_format.
    """
    instances = get_people_instances(idf)

    if output_format == 'dict':
        names_by_people: Dict[int, List[str]] = {}
        for instance in instances:
            names_by_people.setdefault(id(instance['object']), []).append(instance['name'])
        return {person.Name: names_by_people.get(id(person), []) for person in get_people_objects(idf)}
    else:
        return [instance['name'] for instance in instances]


def get_idf_hierarchy(idf: IDF) -> Dict[str, Any]:
    """
    Parses an EnergyPlus IDF model object (from eppy or besos) to extract the
    hierarchical relationship between Zones and Spaces, as well as grouping lists.

    This function is designed to be Case-Preserving for output keys (keeping the
    original IDF capitalization) while remaining Case-Insensitive for internal
    logic (robustly linking Spaces to Zones regardless of capitalization).

    Args:
        idf (Union[IDF, IDF_class]): The IDF model object to be parsed.
                                     Accepts both eppy's IDF and besos's IDF_class.

    Returns:
        Dict[str, Any]: A dictionary representing the model structure:
            {
                "zones": {
                    "ZoneName_Original": {
                        "object_type": "Zone",
                        "spaces": ["Space1", "Space2"]
                    },
                    ...
                },
                "groups": {
                    "zone_lists": { "ListName": ["Zone1", "Zone2"] },
                    "space_lists": { "ListName": ["Space1", "Space2"] }
                }
            }
    """

    # Initialize the master dictionary structure to hold the results
    hierarchy: Dict[str, Any] = {
        "zones": {},
        "groups": {
            "zone_lists": {},
            "space_lists": {}
        }
    }

    # Internal lookup map to handle EnergyPlus case-insensitivity.
    # Structure: { "UPPERCASE_NAME": "Original_Name" }
    zone_lookup_map: Dict[str, str] = {}

    # --- 1. Process ZONES (Parent Objects) ---
    # Both eppy and besos allow accessing objects via .idfobjects['TYPE']
    zones = idf.idfobjects['ZONE']

    for zone in zones:
        z_name_original = zone.Name

        # We store the UPPERCASE version to allow robust searching later,
        # ensuring "Zone1" matches "zone1" as EnergyPlus expects.
        z_name_upper = str(z_name_original).upper()
        zone_lookup_map[z_name_upper] = z_name_original

        # Initialize the entry in the result dict using the ORIGINAL name for readability
        hierarchy["zones"][z_name_original] = {
            "object_type": "Zone",
            "spaces": []  # List to hold children (Spaces)
        }

    # --- 2. Process SPACES (Child Objects) ---
    spaces = idf.idfobjects['SPACE']

    # Note: If 'spaces' is empty, it might be a legacy IDF (pre-v9.6) or a simplified model.
    for space in spaces:
        s_name = space.Name

        # Get the reference to the parent Zone.
        # We convert to string and uppercase to query our lookup map safely.
        parent_ref_upper = str(space.Zone_Name).upper()

        # Link Space to Zone using the lookup map
        if parent_ref_upper in zone_lookup_map:
            # Retrieve the correct original casing of the zone name
            real_zone_name = zone_lookup_map[parent_ref_upper]

            # Append the space name to the correct zone entry
            hierarchy["zones"][real_zone_name]["spaces"].append(s_name)
        else:
            # Log warning for orphan spaces (spaces pointing to non-existent zones)
            print(f"WARNING: Space '{s_name}' references an unknown Zone: '{space.Zone_Name}'")

    # --- 3. Process Grouping Lists (ZoneList & SpaceList) ---

    # Process ZoneList
    for z_list in idf.idfobjects['ZONELIST']:
        # In eppy/besos, the .obj property is a list: ['ZoneList', 'Name', 'Member1', 'Member2'...]
        # Slicing from index 2 ([2:]) retrieves all members dynamically, regardless of list length.
        members: List[str] = [m for m in z_list.obj[2:]]
        hierarchy["groups"]["zone_lists"][z_list.Name] = members

    # Process SpaceList
    for s_list in idf.idfobjects['SPACELIST']:
        # Same logic applied to SpaceLists
        members: List[str] = [m for m in s_list.obj[2:]]
        hierarchy["groups"]["space_lists"][s_list.Name] = members

    return hierarchy


def get_idf_hierarchy_with_people(idf: IDF) -> Dict[str, Any]:
    """
    Parses an EnergyPlus IDF model to extract the hierarchy of Zones and Spaces.

    Structure changes in this version:
    - 'spaces' is a list of dictionaries.
    - Each space dictionary contains:
        - "name": The name of the space (str).
        - "people": The name of the associated People object (str) or None.

    The spaces are those that EnergyPlus creates (see `get_energyplus_spaces`): the Space
    objects, the default space of each zone without Space objects, named like the zone, and the
    remainder spaces. The function resolves the 'People' object assignment regardless of whether
    it is assigned to a Space, a Zone, a SpaceList, or a ZoneList, as EnergyPlus does
    (see `get_people_instances`). The People:Instance objects of EnergyPlus 26.2 are handled as
    People objects.

    Args:
        idf (IDF): The BESOS IDF model object.

    Returns:
        Dict[str, Any]: Structure:
            {
                "zones": {
                    "ZoneName": {
                        "object_type": "Zone",
                        "spaces": [
                            {
                                "name": "SpaceName",
                                "people": "PeopleObjectName" (or None)
                            },
                            ...
                        ]
                    }
                },
                "groups": { ... }
            }
    """

    hierarchy: Dict[str, Any] = {
        "zones": {},
        "groups": {
            "zone_lists": {},
            "space_lists": {}
        }
    }

    # --- LOOKUP MAPS (For internal logic) ---
    # 1. Map UPPERCASE Zone Name -> Original Name
    zone_name_map: Dict[str, str] = {}

    # 2. Map (UPPERCASE Zone Name, UPPERCASE Space Name) -> The specific Space Dictionary
    space_obj_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

    # --- STEP 1: PROCESS ZONES ---
    zones = idf.idfobjects['ZONE']
    for zone in zones:
        z_name_original = zone.Name
        z_name_upper = str(z_name_original).upper()

        zone_name_map[z_name_upper] = z_name_original

        hierarchy["zones"][z_name_original] = {
            "object_type": "Zone",
            "spaces": []
        }

    # --- STEP 2: PROCESS SPACES ---
    for z_name_upper, zone_spaces in get_energyplus_spaces(idf).items():
        if z_name_upper not in zone_name_map:
            for s_name in zone_spaces['spaces']:
                print(f"WARNING: Space '{s_name}' references unknown Zone: '{zone_spaces['zone']}'")
            continue
        real_zone_name = zone_name_map[z_name_upper]

        for s_name in zone_spaces['spaces']:
            # Create the Space Dictionary
            # 'people' is initialized as None. It will be a string if found later.
            space_dict = {
                "name": s_name,
                "people": None
            }

            # Add to the main hierarchy, and index it for direct access later
            hierarchy["zones"][real_zone_name]["spaces"].append(space_dict)
            space_obj_map[(z_name_upper, str(s_name).upper())] = space_dict

    # --- STEP 3: PROCESS LISTS ---
    for sl in _get_objects_if_in_idd(idf, 'SpaceList'):
        hierarchy["groups"]["space_lists"][sl.Name] = [m for m in sl.obj[2:]]

    for zl in _get_objects_if_in_idd(idf, 'ZoneList'):
        hierarchy["groups"]["zone_lists"][zl.Name] = [m for m in zl.obj[2:]]

    # --- STEP 4: PROCESS PEOPLE AND PEOPLE:INSTANCE (Inject into Space Dicts) ---
    # Each instance that EnergyPlus creates for a People object is in one space
    for instance in get_people_instances(idf):
        s_dict = space_obj_map.get((instance['zone'].upper(), instance['space'].upper()))
        if s_dict is not None:
            # We assign the string directly.
            # If multiple people objects point to the same space, the last one processed wins.
            s_dict["people"] = instance['people']

    return hierarchy


def get_spaces_from_spacelist(idf: IDF, spacelist_name: str) -> List[str]:
    """
    Retrieves the list of Space names belonging to a specific SpaceList object.

    Performs a case-insensitive search for the SpaceList name to ensure robustness.

    Args:
        idf (Union[IDF, IDF_class]): The IDF model object.
        spacelist_name (str): The name of the SpaceList to query (e.g. "Residential - Living Space").

    Returns:
        List[str]: A list of space names contained in that SpaceList.
                   Returns an empty list [] if the SpaceList is not found.
    """

    # Normalize the target name to uppercase for case-insensitive comparison
    target_name_upper = spacelist_name.upper()

    # Iterate through all SPACELIST objects in the IDF
    for s_list in idf.idfobjects['SPACELIST']:

        # Check if this is the list we are looking for
        if s_list.Name.upper() == target_name_upper:
            # In eppy/besos, .obj is a list: ['SpaceList', 'Name', 'Space1', 'Space2'...]
            # Slicing from index 2 ([2:]) retrieves only the members (the spaces).
            members = [space_name for space_name in s_list.obj[2:]]

            return members

    # If the loop finishes without finding the list, return an empty list or handle error
    print(f"WARNING: SpaceList '{spacelist_name}' not found in the IDF.")
    return []
