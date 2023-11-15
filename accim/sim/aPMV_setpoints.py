# todo calculate number of occupied hours from occupancy schedules

def set_zones_always_occupied(
        building,
        verboseMode: bool = True
):

    sch_comp_objs = [i.Name for i in building.idfobjects['schedule:compact']]

    if 'On' in sch_comp_objs:
        if verboseMode:
            print(f"On Schedule already was in the model")
    else:
        building.newidfobject(
            'Schedule:Compact',
            Name='On',
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00,1'
        )
        if verboseMode:
            print(f"On Schedule has been added")

    for i in [j for j in building.idfobjects['people']]:
        i.Number_of_People_Schedule_Name = 'On'


def add_apmv_ems_code(
        building,
        Outputs_freq: list = ['hourly'],
        other_PMV_related_outputs: bool = True,
        adaptive_coefficient: float = 0.293,
        pmv_heating_setpoint: float = -0.5,
        pmv_cooling_setpoint: float = 0.5,
        setpoint_tolerance: float = 0.1,
        verboseMode: bool = True,
):

    # Scanning occupied zones

    ppl_temp = [[people.Zone_or_ZoneList_Name, people.Name] for people in building.idfobjects['People']]
    zones_with_ppl_colon = [ppl[0] for ppl in ppl_temp]
    ppl_names = [ppl[1] for ppl in ppl_temp]
    zones_with_ppl_underscore = [z.replace(':', '_') for z in zones_with_ppl_colon]

    # Adding PMV schedules and setting them in ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint objects

    sch_comp_objs = [i.Name for i in building.idfobjects['Schedule:Compact']]

    for i in ['PMV_H_SP', 'PMV_C_SP']:
        for zone in zones_with_ppl_underscore:
            if f'{i}_{zone}' in sch_comp_objs:
                if verboseMode:
                    print(f"{i}_{zone} Schedule already was in the model")
            else:
                building.newidfobject(
                    'Schedule:Compact',
                    Name=f'{i}_{zone}',
                    Schedule_Type_Limits_Name="Any Number",
                    Field_1='Through: 12/31',
                    Field_2='For: AllDays',
                    Field_3='Until: 24:00,1'
                )
                if verboseMode:
                    print(f"{i}_{zone} Schedule has been added")

    comf_fanger_dualsps = [i for i in building.idfobjects['ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint']]

    for i in comf_fanger_dualsps:
        for j in range(len(zones_with_ppl_colon)):
            if zones_with_ppl_colon[j] in i.Name:
                i.Fanger_Thermal_Comfort_Heating_Schedule_Name = f'PMV_H_SP_{zones_with_ppl_underscore[j]}'
                i.Fanger_Thermal_Comfort_Cooling_Schedule_Name = f'PMV_C_SP_{zones_with_ppl_underscore[j]}'

    # EMS

    # Adding sensors
    sensornamelist = ([sensor.Name for sensor in building.idfobjects['EnergyManagementSystem:Sensor']])

    for i in range(len(zones_with_ppl_underscore)):
        if f'PMV_{zones_with_ppl_underscore[i]}' in sensornamelist:
            if verboseMode:
                print(f'Not added - PMV_{zones_with_ppl_underscore[i]} Sensor')
        else:
            building.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=f'PMV_{zones_with_ppl_underscore[i]}',
                OutputVariable_or_OutputMeter_Index_Key_Name=ppl_names[i],
                OutputVariable_or_OutputMeter_Name='Zone Thermal Comfort Fanger Model PMV'
            )
            if verboseMode:
                print(f'Added - PMV_{zones_with_ppl_underscore[i]} Sensor')

        if f'People_Occupant_Count_{zones_with_ppl_underscore[i]}' in sensornamelist:
            if verboseMode:
                print(f'Not added - People_Occupant_Count_{zones_with_ppl_underscore[i]} Sensor')
        else:
            building.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=f'People_Occupant_Count_{zones_with_ppl_underscore[i]}',
                OutputVariable_or_OutputMeter_Index_Key_Name=ppl_names[i],
                OutputVariable_or_OutputMeter_Name='People Occupant Count'
            )
            if verboseMode:
                print(f'Added - People_Occupant_Count_{zones_with_ppl_underscore[i]} Sensor')

    # Adding actuators
    actuatornamelist = [actuator.Name for actuator in building.idfobjects['EnergyManagementSystem:Actuator']]

    for i in ['PMV_H_SP', 'PMV_C_SP']:
        for zone in zones_with_ppl_underscore:
            if f'{i}_act_{zone}' in actuatornamelist:
                if verboseMode:
                    print(f'Not added - {i}_act_{zone} Actuator')
            else:
                building.newidfobject(
                    'EnergyManagementSystem:Actuator',
                    Name=f'{i}_act_{zone}',
                    Actuated_Component_Unique_Name=f'{i}_{zone}',
                    Actuated_Component_Type='Schedule:Compact',
                    Actuated_Component_Control_Type='Schedule Value',
                )
                if verboseMode:
                    print(f'Added - {i}_act_{zone} Actuator')

    # Adding GlobalVariables

    globalvariablenames = [
        'tol',
        'adap_coeff'
    ]
    globalvariablezonenames = []
    for i in [
        'aPMV',
        'comfhour',
        'discomfhour',
        'discomfhour_heat',
        'discomfhour_cold',
        'aPMV_H_SP',
        'aPMV_C_SP',
        'aPMV_H_SP_noTol',
        'aPMV_C_SP_noTol',
    ]:
        for zone in zones_with_ppl_underscore:
            globalvariablezonenames.append(f'{i}_{zone}')

    allgvs = globalvariablenames + globalvariablezonenames

    for gv in allgvs:
        building.newidfobject(
            'EnergyManagementSystem:GlobalVariable',
            Erl_Variable_1_Name=gv,
        )
        if verboseMode:
            print(f'Added - {gv} GlobalVariable object')

    # Programs
    programlist = [
        program.Name
        for program
        in building.idfobjects['EnergyManagementSystem:Program']
    ]

    for zonename in zones_with_ppl_underscore:
        if f'apply_aPMV_{zonename}' in programlist:
            if verboseMode:
                print(f'Not added - apply_aPMV_{zonename} Program')
        else:
            building.newidfobject(
                'EnergyManagementSystem:Program',
                Name=f'apply_aPMV_{zonename}',
                # Do not override
                Program_Line_1=f'set adap_coeff = {adaptive_coefficient}',
                Program_Line_2='set PMV_H_SP_' + zonename + f' = {pmv_heating_setpoint}',
                Program_Line_3='set PMV_C_SP_' + zonename + f' = {pmv_cooling_setpoint}',
                Program_Line_4=f'set tol = {setpoint_tolerance}',

                # Override below if needs update
                Program_Line_5='set aPMV_H_SP_noTol_' + zonename + ' = PMV_H_SP_' + zonename + '/(1+adap_coeff*PMV_H_SP_' + zonename + ')',
                Program_Line_6='set aPMV_C_SP_noTol_' + zonename + ' = PMV_C_SP_' + zonename + '/(1+adap_coeff*PMV_C_SP_' + zonename + ')',
                Program_Line_7='set aPMV_H_SP_' + zonename + ' = aPMV_H_SP_noTol_' + zonename + '+tol',
                Program_Line_8='set aPMV_C_SP_' + zonename + ' = aPMV_C_SP_noTol_' + zonename + '-tol',
                Program_Line_9='if People_Occupant_Count_' + zonename + ' > 0',
                Program_Line_10='if aPMV_H_SP_' + zonename + ' < 0',
                Program_Line_11='set PMV_H_SP_act_' + zonename + ' = aPMV_H_SP_' + zonename + '',
                Program_Line_12='else',
                Program_Line_13='set PMV_H_SP_act_' + zonename + ' = 0',
                Program_Line_14='endif',
                Program_Line_15='if aPMV_C_SP_' + zonename + ' > 0',
                Program_Line_16='set PMV_C_SP_act_' + zonename + ' = aPMV_C_SP_' + zonename + '',
                Program_Line_17='else',
                Program_Line_18='set PMV_C_SP_act_' + zonename + ' = 0',
                Program_Line_19='endif',
                Program_Line_20='else',
                Program_Line_21='set PMV_H_SP_act_' + zonename + ' = -100',
                Program_Line_22='set PMV_C_SP_act_' + zonename + ' = 100',
                Program_Line_23='endif',
            )
            if verboseMode:
                print(f'Added - apply_aPMV_{zonename} Program')

    for zonename in zones_with_ppl_underscore:
        if 'monitor_aPMV_' + zonename in programlist:
            if verboseMode:
                print('Not added - monitor_aPMV_' + zonename + ' Program')
        else:
            building.newidfobject(
                'EnergyManagementSystem:Program',
                Name='monitor_aPMV_' + zonename,
                Program_Line_1='set aPMV_' + zonename + ' = PMV_' + zonename + '/(1+adap_coeff*PMV_' + zonename + ')',
            )
            if verboseMode:
                print('Added - monitor_aPMV_' + zonename + ' Program')

        if 'count_aPMV_comfort_hours_' + zonename in programlist:
            if verboseMode:
                print('Not added - count_aPMV_comfort_hours_' + zonename + ' Program')
        else:
            building.newidfobject(
                'EnergyManagementSystem:Program',
                Name='count_aPMV_comfort_hours_' + zonename,
                Program_Line_1='if aPMV_' + zonename + ' < aPMV_H_SP_noTol_' + zonename + '',
                Program_Line_2='set comfhour_' + zonename + ' = 0',
                Program_Line_3='set discomfhour_cold_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_4='set discomfhour_heat_' + zonename + ' = 0',
                Program_Line_5='elseif aPMV_' + zonename + ' > aPMV_C_SP_noTol_' + zonename + '',
                Program_Line_6='set comfhour_' + zonename + ' = 0',
                Program_Line_7='set discomfhour_cold_' + zonename + ' = 0',
                Program_Line_8='set discomfhour_heat_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_9='else',
                Program_Line_10='set comfhour_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_11='set discomfhour_cold_' + zonename + ' = 0',
                Program_Line_12='set discomfhour_heat_' + zonename + ' = 0',
                Program_Line_13='endif',
                Program_Line_14='set discomfhour_' + zonename + ' = discomfhour_cold_' + zonename + ' + discomfhour_heat_' + zonename + '',
            )
            if verboseMode:
                print('Added - count_aPMV_comfort_hours_' + zonename + ' Program')

    programlist = ([program.Name
                    for program
                    in building.idfobjects['EnergyManagementSystem:Program']])
    pcmlist = ([pcm.Name
                for pcm
                in building.idfobjects['EnergyManagementSystem:ProgramCallingManager']])

    for i in programlist:
        if i in pcmlist:
            if verboseMode:
                print('Not added - ' + i + ' Program Calling Manager')
        else:
            building.newidfobject(
                'EnergyManagementSystem:ProgramCallingManager',
                Name=i,
                EnergyPlus_Model_Calling_Point="BeginTimestepBeforePredictor",
                Program_Name_1=i
            )
            if verboseMode:
                print('Added - ' + i + ' Program Calling Manager')

    # EMS:OutputVariable

    EMSOutputVariableAvg_dict = {
        'Adaptive Coefficient (Lambda value)': ['adap_coeff', ''],
    }

    outputvariablelist = [
        outvar.Name
        for outvar
        in building.idfobjects['EnergyManagementSystem:OutputVariable']
    ]

    for i in EMSOutputVariableAvg_dict:
        if i in outputvariablelist:
            if verboseMode:
                print('Not added - ' + i + ' Output Variable')
        else:
            building.newidfobject(
                'EnergyManagementSystem:OutputVariable',
                Name=i,
                EMS_Variable_Name=EMSOutputVariableAvg_dict[i][0],
                Type_of_Data_in_Variable='Averaged',
                Update_Frequency='ZoneTimestep',
                EMS_Program_or_Subroutine_Name='',
                Units=EMSOutputVariableAvg_dict[i][1]
            )
            if verboseMode:
                print('Added - ' + i + ' Output Variable')

    EMSOutputVariableZone_dict = {
        # 'Adaptive Predicted Mean Vote': ['aPMV', '', 'Averaged'],
        # 'Adaptive Predicted Mean Vote Heating Setpoint': ['aPMV_H_SP', '', 'Averaged'],
        # 'Adaptive Predicted Mean Vote Cooling Setpoint': ['aPMV_C_SP', '', 'Averaged'],
        # 'Adaptive Predicted Mean Vote Heating Setpoint No Tolerance': ['aPMV_H_SP_noTol', '', 'Averaged'],
        # 'Adaptive Predicted Mean Vote Cooling Setpoint No Tolerance': ['aPMV_C_SP_noTol', '', 'Averaged'],

        'aPMV': ['aPMV', '', 'Averaged'],
        'aPMV Heating Setpoint': ['aPMV_H_SP', '', 'Averaged'],
        'aPMV Cooling Setpoint': ['aPMV_C_SP', '', 'Averaged'],
        'aPMV Heating Setpoint No Tolerance': ['aPMV_H_SP_noTol', '', 'Averaged'],
        'aPMV Cooling Setpoint No Tolerance': ['aPMV_C_SP_noTol', '', 'Averaged'],

        'Comfortable Hours': ['comfhour', 'H', 'Summed'],
        'Discomfortable Hot Hours': ['discomfhour_heat', 'H', 'Summed'],
        'Discomfortable Cold Hours': ['discomfhour_cold', 'H', 'Summed'],
        'Discomfortable Total Hours': ['discomfhour', 'H', 'Summed'],
        'People Occupant Count': ['People_Occupant_Count', '', 'Averaged'],
        # 'Zone Floor Area': ['ZoneFloorArea', 'm2', 'Averaged'],
        # 'Zone Air Volume': ['ZoneAirVolume', 'm3', 'Averaged'],
    }

    for i in EMSOutputVariableZone_dict:
        for zonename in zones_with_ppl_underscore:
            if i + '_' + zonename in outputvariablelist:
                if verboseMode:
                    print('Not added - ' + i + '_'
                          + zonename + ' Output Variable')
            else:
                building.newidfobject(
                    'EnergyManagementSystem:OutputVariable',
                    Name=i + '_' + zonename,
                    EMS_Variable_Name=EMSOutputVariableZone_dict[i][0] + '_'
                                      + zonename,
                    Type_of_Data_in_Variable=EMSOutputVariableZone_dict[i][2],
                    Update_Frequency='ZoneTimestep',
                    EMS_Program_or_Subroutine_Name='',
                    Units=EMSOutputVariableZone_dict[i][1]
                )
                if verboseMode:
                    print('Added - ' + i + '_'
                          + zonename + ' Output Variable')

    # Output:Variable

    EMSoutputvariablenamelist = [
        outputvariable.Name
        for outputvariable
        in building.idfobjects['EnergyManagementSystem:OutputVariable']
    ]

    for freq in Outputs_freq:
        outputnamelist = (
            [
                output.Variable_Name
                for output
                in building.idfobjects['Output:Variable']
                if output.Reporting_Frequency == freq.capitalize()
            ]
        )
        for outputvariable in EMSoutputvariablenamelist:
            if outputvariable in outputnamelist:
                if verboseMode:
                    print('Not added - ' + outputvariable + ' Reporting Frequency ' + freq.capitalize() + ' Output:Variable data')
            elif outputvariable.startswith("WIP"):
                if verboseMode:
                    print('Not added - ' + outputvariable + ' Output:Variable data because its WIP')
            else:
                building.newidfobject(
                    'Output:Variable',
                    Key_Value='*',
                    Variable_Name=outputvariable,
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                )
                if verboseMode:
                    print('Added - ' + outputvariable + ' Reporting Frequency ' + freq.capitalize() + ' Output:Variable data')

    addittionaloutputs = [
        # 'Zone Thermostat Operative Temperature',
        'Zone Operative Temperature',
        'Zone Thermal Comfort Clothing Surface Temperature',
        'Zone Thermal Comfort Clothing Value',
        'Zone Thermal Comfort Control Fanger High Setpoint PMV',
        'Zone Thermal Comfort Control Fanger Low Setpoint PMV',
        'Zone Thermal Comfort Fanger Model PMV',
        'Zone Thermal Comfort Fanger Model PPD',
        'Zone Thermal Comfort Mean Radiant Temperature',
        'Zone Mean Air Humidity Ratio',
        'Zone Mean Air Temperature',
        'Cooling Coil Total Cooling Rate',
        'Heating Coil Heating Rate',
        'Facility Total HVAC Electric Demand Power',
        'Facility Total HVAC Electricity Demand Rate',
        'AFN Surface Venting Window or Door Opening Factor',
        'AFN Zone Infiltration Air Change Rate',
        'AFN Zone Infiltration Volume',
        'AFN Zone Ventilation Air Change Rate',
        'AFN Zone Ventilation Volume',
    ]

    if other_PMV_related_outputs:
        for addittionaloutput in addittionaloutputs:
            if addittionaloutput in outputnamelist:
                if verboseMode:
                    print('Not added - ' + addittionaloutput + ' Reporting Frequency ' + freq.capitalize() + ' Output:Variable data')
            else:
                building.newidfobject(
                    'Output:Variable',
                    Key_Value='*',
                    Variable_Name=addittionaloutput,
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                )
                if verboseMode:
                    print('Added - ' + addittionaloutput + ' Reporting Frequency ' + freq.capitalize() + ' Output:Variable data')

        for i in ['PMV_H_SP', 'PMV_C_SP']:
            for zone in zones_with_ppl_underscore:
                building.newidfobject(
                    'Output:Variable',
                    Key_Value=f'{i}_{zone}',
                    Variable_Name='Schedule Value',
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                )
                if verboseMode:
                    print(f'Added - {i}_' + zone + ' Reporting Frequency ' + freq.capitalize() + ' Output:Variable data')

        air_velocity_schs = list(set([i.Air_Velocity_Schedule_Name for i in building.idfobjects['people']]))

        for i in air_velocity_schs:
            if i in outputnamelist:
                if verboseMode:
                    print('Not added - ' + i + ' Reporting Frequency ' + freq.capitalize() + ' Output:Variable data')
            else:
                building.newidfobject(
                    'Output:Variable',
                    Key_Value=i,
                    Variable_Name='Schedule Value',
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                )
                if verboseMode:
                    print(f'Added - {i}' + ' Reporting Frequency ' + freq.capitalize() + ' Output:Variable data')


def change_adaptive_coeff(building, value):
    program = [p for p in building.idfobjects['EnergyManagementSystem:Program'] if 'apply_aPMV' in p.Name][0]
    program.Program_Line_1 = f'set adap_coeff = {value}'
    return

def change_pmv_setpoints(building, value):
    programs = [p for p in building.idfobjects['EnergyManagementSystem:Program'] if 'apply_aPMV' in p.Name]
    for p in programs:
        zone = p.Program_Line_2.split('set PMV_H_SP_')[1].split(' ')[0]
        p.Program_Line_2 = f'set PMV_H_SP_{zone} = {-value}'
        p.Program_Line_3 = f'set PMV_C_SP_{zone} = {value}'
    return

def change_pmv_heating_setpoint(building, value):
    programs = [p for p in building.idfobjects['EnergyManagementSystem:Program'] if 'apply_aPMV' in p.Name]
    for p in programs:
        zone = p.Program_Line_2.split('set PMV_H_SP_')[1].split(' ')[0]
        p.Program_Line_2 = f'set PMV_H_SP_{zone} = {value}'
    return

def change_pmv_cooling_setpoint(building, value):
    programs = [p for p in building.idfobjects['EnergyManagementSystem:Program'] if 'apply_aPMV' in p.Name]
    for p in programs:
        zone = p.Program_Line_2.split('set PMV_H_SP_')[1].split(' ')[0]
        p.Program_Line_3 = f'set PMV_C_SP_{zone} = {value}'
    return


# class map_idf_objects:
#     def __init__(self, building):
#         self.peoplelist = ([zone.Name for zone in building.idfobjects['Zone']])
#         self.zonelist = ([zone.Name for zone in building.idfobjects['Zone']])
#         self.sensorlist = ([sensor.Name for sensor in building.idfobjects['EnergyManagementSystem:Sensor']])
#
# class apply_aPMV_setpoints:
#     def __init__(
#             self,
#             building,
#             adaptive_coeff: list,
#     ):
#
#         pass