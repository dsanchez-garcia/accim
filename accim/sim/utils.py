# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

def scan_zones(self):
    """
    Used to scan the occupied zones in an idf.

    The occupied zones are those of the People objects and, in EnergyPlus 26.2, of the People:Instance
    objects, which have their thermal comfort models in the People:Definition objects they reference.

    :raises ValueError: If the idf has no People or People:Instance objects.
    """
    from accim.sim.apmv_setpoints import _resolve_targets
    from accim.utils import get_people_objects

    if len(get_people_objects(self.idf1)) == 0:
        raise ValueError(
            'The model has no People objects or People:Instance objects (EnergyPlus 26.2 and later). '
            'accim finds the occupied zones in these objects and adds the thermal comfort models to them '
            '(to the People:Definition objects of the People:Instance objects), so the model needs at least one.'
        )

    target_data = _resolve_targets(self.idf1)

    self.occupiedZones_orig = list(set([t['zone_name'] for t in target_data]))
    self.occupiedZones = [i.replace(' ', '_').replace(':', '_') for i in self.occupiedZones_orig]

    self.ems_objs_name = [t['ems_suffix'] for t in target_data]
    self.ems_objs_key = [t['sensor_key'] for t in target_data]
    self.ems_zonenames = [t['zone_name'] for t in target_data]
    # The occupancy of a zone with several occupant instances is the 'Zone People Occupant Count' of the zone
    self.ems_occupancy_keys = [t['occupancy_key'] for t in target_data]
    self.ems_occupancy_variables = [t['occupancy_variable'] for t in target_data]
    self.ems_zonenames_underscore = [i.replace(' ', '_').replace(':', '_') for i in self.ems_zonenames]

    self.spacelist_use = False
    try:
        if len(self.idf1.idfobjects['SPACELIST']) > 0 or len(self.idf1.idfobjects['SPACE']) > 0:
            self.spacelist_use = True
    except KeyError:
        pass

    self.origin_dsb = not self.spacelist_use

    self.spacenames_for_ems_uniquekey_people = self.ems_objs_key
    self.spacenames_for_ems_name = self.ems_objs_name
    self.spacenames_for_ems_uniquekey = self.ems_objs_key


def add_vrf_system(
        z,
        TempCtrl,
        verboseMode,
        EnergyPlus_version,
        SupplyAirTempInputMethod,
        eer,
        cop,
        VRFschedule
):
    if TempCtrl.lower() == 'temperature' or TempCtrl.lower() == 'temp':
        z.addOpTempTherm(verboseMode=verboseMode)
    elif TempCtrl.lower() == 'pmv':
        z.setPMVsetpoint(verboseMode=verboseMode)
    z.addBaseSchedules(verboseMode=verboseMode)
    z.setAvailSchOn(verboseMode=verboseMode)
    z.addVRFsystemSch(verboseMode=verboseMode)
    z.addCurveObj(verboseMode=verboseMode)
    z.addDetHVACobj(
        EnergyPlus_version=EnergyPlus_version,
        verboseMode=verboseMode,
        SupplyAirTempInputMethod=SupplyAirTempInputMethod,
        eer=eer,
        cop=cop,
        VRFschedule=VRFschedule
    )
