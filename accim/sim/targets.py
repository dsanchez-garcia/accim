# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Targets of the EMS: the occupied zones of a model, and the occupant instances of each one."""

import re
import warnings
from dataclasses import dataclass
from typing import Dict, List, Tuple

from accim.utils.people import get_energyplus_spaces, get_people_instances

__all__ = ['Target', 'resolve_targets', 'sanitize_ems_name']


def sanitize_ems_name(name: str) -> str:
    """Make a name valid for the EMS variables: any character but A-Z, a-z, 0-9 and '_' becomes '_'.

    :param name: The name of an IDF object (e.g. 'Zone 1: Space-A').
    :return: The sanitised name (e.g. 'Zone_1__Space_A').
    """
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


@dataclass(frozen=True)
class Target:
    """An occupied zone, which the EMS controls.

    EnergyPlus creates one occupant instance for each space a People object (or People:Instance
    object of EnergyPlus 26.2) applies to; see :func:`accim.utils.get_people_instances`.

    :ivar df_key: The key of the target in the dictionaries of arguments (e.g. 'Space1 People1').
    :ivar ems_suffix: The suffix of the EMS objects of the target (e.g. 'Space1_People1').
    :ivar sensor_key: The key of the outputs of the (first) occupant instance.
    :ivar zone_name: The name of the zone (schedules and thermostats are zone-based).
    :ivar occupancy_key: The key of the occupancy sensor (the instance, or the zone if it has several).
    :ivar occupancy_variable: 'People Occupant Count' or 'Zone People Occupant Count'.
    :ivar instance_keys: The keys of all the occupant instances of the zone.
    :ivar people_names: The names of the People objects of these instances.
    """

    df_key: str
    ems_suffix: str
    sensor_key: str
    zone_name: str
    occupancy_key: str
    occupancy_variable: str
    instance_keys: Tuple[str, ...]
    people_names: Tuple[str, ...]

    def as_dict(self) -> Dict:
        """The target as a dictionary (the format of accim 0.x)."""
        return {
            'df_key': self.df_key,
            'ems_suffix': self.ems_suffix,
            'sensor_key': self.sensor_key,
            'zone_name': self.zone_name,
            'occupancy_key': self.occupancy_key,
            'occupancy_variable': self.occupancy_variable,
            'instance_keys': list(self.instance_keys),
            'people_names': list(self.people_names),
        }


def resolve_targets(building) -> List[Target]:
    """Find the targets of the EMS: one per occupied zone.

    1. A zone with ONE occupant instance (the usual case: People assigned to each zone, or to a
       SpaceList with one space per zone, as in OpenStudio models): the key and the suffix are the
       zone name if the People object is assigned to a zone without Space objects, and
       '<Space Name> <People Name>' otherwise; the occupancy is the 'People Occupant Count' of the
       instance.
    2. A zone with SEVERAL instances (a zone of several spaces, a SpaceList or ZoneList that covers
       several spaces of the zone, a remainder space, or several People objects in the zone): the key
       and the suffix are the zone name, and the occupancy is the 'Zone People Occupant Count' of the
       zone, which adds up the occupants of all its instances.

    :param building: The eppy or besos IDF object.
    """
    instances = get_people_instances(building)
    zones = get_energyplus_spaces(building)

    # Group the instances by zone, in the order EnergyPlus creates them
    instances_by_zone: Dict[str, List[Dict]] = {}
    for instance in instances:
        instances_by_zone.setdefault(instance['zone'].upper(), []).append(instance)

    targets = []
    for zone_upper, zone_instances in instances_by_zone.items():
        people_names = tuple(dict.fromkeys(i['people'] for i in zone_instances))
        if len(zone_instances) == 1:
            instance = zone_instances[0]
            if not instance['prefixed'] and instance['space_kind'] == 'default':
                # Assigned directly to a zone without spaces: the user identifies it by the zone name
                df_key = instance['container']
                ems_suffix = sanitize_ems_name(df_key)
            else:
                # '<Space Name> <People Name>', also when EnergyPlus names the instance after the People object
                df_key = f"{instance['space']} {instance['people']}"
                ems_suffix = sanitize_ems_name(f"{instance['space']}_{instance['people']}")
            targets.append(Target(
                df_key=df_key,
                ems_suffix=ems_suffix,
                sensor_key=instance['name'],
                zone_name=instance['zone'],
                occupancy_key=instance['name'],
                occupancy_variable='People Occupant Count',
                instance_keys=(instance['name'],),
                people_names=people_names,
            ))
        else:
            zone_name = zones[zone_upper]['zone'] if zone_upper in zones else zone_instances[0]['zone']
            if any(i['space_kind'] == 'remainder' for i in zone_instances):
                warnings.warn(
                    f"Some surfaces of zone '{zone_name}' have a Space Name and others do not, so EnergyPlus "
                    f"creates the space '{zones[zone_upper]['remainder']}' for the latter and splits the "
                    f"occupants of the zone among its spaces ({', '.join(i['name'] for i in zone_instances)}). "
                    f"accim takes all of them into account. To avoid the remainder space, assign every "
                    f"surface of the zone to a Space."
                )
            targets.append(Target(
                df_key=zone_name,
                ems_suffix=sanitize_ems_name(zone_name),
                sensor_key=zone_instances[0]['name'],
                zone_name=zone_name,
                occupancy_key=zone_name,
                occupancy_variable='Zone People Occupant Count',
                instance_keys=tuple(i['name'] for i in zone_instances),
                people_names=people_names,
            ))
    return targets
