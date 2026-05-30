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

    """
    from accim.sim.apmv import _resolve_targets

    target_data = _resolve_targets(self.idf1)

    self.occupiedZones_orig = list(set([t['zone_name'] for t in target_data]))
    self.occupiedZones = [i.replace(' ', '_').replace(':', '_') for i in self.occupiedZones_orig]

    self.ems_objs_name = [t['ems_suffix'] for t in target_data]
    self.ems_objs_key = [t['sensor_key'] for t in target_data]
    self.ems_zonenames = [t['zone_name'] for t in target_data]
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
        temp_control,
        verbose,
        energyplus_version,
        supply_air_temp_method,
        eer,
        cop,
        vrf_schedule
):
    if temp_control.lower() == 'temperature' or temp_control.lower() == 'temp':
        z.add_operative_temp_thermostat(verbose=verbose)
    elif temp_control.lower() == 'pmv':
        z.set_pmv_setpoint(verbose=verbose)
    z.add_base_schedules(verbose=verbose)
    z.set_availability_schedule_on(verbose=verbose)
    z.add_vrf_system_schedule(verbose=verbose)
    z.add_curve_objects(verbose=verbose)
    z.add_detailed_hvac_objects(
        energyplus_version=energyplus_version,
        verbose=verbose,
        supply_air_temp_method=supply_air_temp_method,
        eer=eer,
        cop=cop,
        vrf_schedule=vrf_schedule
    )
