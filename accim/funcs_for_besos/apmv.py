def change_adaptive_coeff_all_zones(building, value):
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in building.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in building.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}',
        program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}',
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}',
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}',
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}',
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}',
    return

def change_adaptive_coeff_cooling_all_zones(building, value):
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in building.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in building.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}',
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}',
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}',
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}',
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}',
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}',
    return

def change_adaptive_coeff_heating_all_zones(building, value):
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in building.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in building.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}',
        program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}',
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}',
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}',
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}',
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}',
    return

def change_pmv_setpoint_all_zones(building, value):
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in building.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in building.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}',
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}',
        program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}',
        program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {-value}',
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}',
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}',
    return

def change_pmv_cooling_setpoint_all_zones(building, value):
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in building.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in building.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}',
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}',
        program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}',
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}',
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}',
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}',
    return

def change_pmv_heating_setpoint_all_zones(building, value):
    ppl_temp = [people.Zone_or_ZoneList_Name.replace(':', '_') for people in building.idfobjects['People']]

    for zonename in ppl_temp:
        program = [p
                   for p
                   in building.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name
                   and zonename.lower() in p.Name.lower()
                   ][0]
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}',
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}',
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}',
        program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}',
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}',
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}',
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}',
    return
