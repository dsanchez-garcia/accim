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

import besos
def change_adaptive_coeff_all_zones(idf: besos.IDF_class, value: float):
    """
    Modifies the adap_coeff_cooling and adap_coeff_heating arguments for all zones to match the entered value.

    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    """
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in idf.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in idf.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

def change_adaptive_coeff_cooling_all_zones(idf: besos.IDF_class, value: float):
    """
    Modifies the adap_coeff_cooling argument for all zones to match the entered value.

    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    """
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in idf.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in idf.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

def change_adaptive_coeff_heating_all_zones(idf: besos.IDF_class, value: float):
    """
    Modifies the adap_coeff_heating argument for all zones to match the entered value.

    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    """
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in idf.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in idf.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

def change_pmv_setpoint_all_zones(idf: besos.IDF_class, value: float):
    """
    Modifies the pmv_cooling_sp and pmv_heating_sp arguments symmetrically
    for all zones to match the entered value.

    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    """
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in idf.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in idf.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {-value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

def change_pmv_cooling_setpoint_all_zones(idf: besos.IDF_class, value: float):
    """
    Modifies the pmv_cooling_sp argument for all zones to match the entered value.

    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    """
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in idf.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in idf.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

def change_pmv_heating_setpoint_all_zones(idf: besos.IDF_class, value: float):
    """
    Modifies the pmv_heating_sp argument for all zones to match the entered value.

    :param idf: The eppy or besos IDF class instance.
    :param value: The value to be applied in the argument.
    :return:
    """
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in idf.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in idf.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return
