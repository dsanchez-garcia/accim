import pytest
from accim.sim import accim_Main

@pytest.fixture()
def IDFobject():
    from eppy.modeleditor import IDF

    iddfile = 'C:/EnergyPlusV9-1-0/Energy+.idd'
    IDF.setiddname(iddfile)

    z = accim_Main.accimJob(
        filename_temp='TestModel_MultipleZone',
        ScriptType='mz',
        EnergyPlus_version='ep91',
        verboseMode=False)
    return z


def test_addDetHVACobjEp91(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addDetHVACobjEp91(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')
    
    zonenames_orig = ([zone.Name for zone in idf1.idfobjects['ZONE']])

    for zonename in zonenames_orig:
        VRFobj = ([x
                   for x
                   in idf1.idfobjects['AirConditioner:VariableRefrigerantFlow']
                   if x.Heat_Pump_Name == 'VRF Outdoor Unit_' + zonename])
        assert VRFobj[0].Heat_Pump_Name == 'VRF Outdoor Unit_' + zonename
        assert VRFobj[0].Availability_Schedule_Name == 'On 24/7'
        assert VRFobj[0].Gross_Rated_Total_Cooling_Capacity == 'autosize'
        assert VRFobj[0].Gross_Rated_Cooling_COP == 2
        assert VRFobj[0].Minimum_Outdoor_Temperature_in_Cooling_Mode == -6
        assert VRFobj[0].Maximum_Outdoor_Temperature_in_Cooling_Mode == 43
        assert VRFobj[0].Cooling_Capacity_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name == 'VRFCoolCapFT'
        assert VRFobj[0].Cooling_Capacity_Ratio_Boundary_Curve_Name == 'VRFCoolCapFTBoundary'
        assert VRFobj[0].Cooling_Capacity_Ratio_Modifier_Function_of_High_Temperature_Curve_Name == 'VRFCoolCapFTHi'
        assert VRFobj[0].Cooling_Energy_Input_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name == 'VRFCoolEIRFT'
        assert VRFobj[0].Cooling_Energy_Input_Ratio_Boundary_Curve_Name == 'VRFCoolEIRFTBoundary'
        assert VRFobj[0].Cooling_Energy_Input_Ratio_Modifier_Function_of_High_Temperature_Curve_Name == 'VRFCoolEIRFTHi'
        assert VRFobj[0].Cooling_Energy_Input_Ratio_Modifier_Function_of_Low_PartLoad_Ratio_Curve_Name == 'CoolingEIRLowPLR'
        assert VRFobj[0].Cooling_Energy_Input_Ratio_Modifier_Function_of_High_PartLoad_Ratio_Curve_Name == 'CoolingEIRHiPLR'
        assert VRFobj[0].Cooling_Combination_Ratio_Correction_Factor_Curve_Name == 'CoolingCombRatio'
        assert VRFobj[0].Cooling_PartLoad_Fraction_Correlation_Curve_Name == 'VRFCPLFFPLR'
        assert VRFobj[0].Gross_Rated_Heating_Capacity == 'autosize'
        assert VRFobj[0].Rated_Heating_Capacity_Sizing_Ratio == 1
        assert VRFobj[0].Gross_Rated_Heating_COP == 2.1
        assert VRFobj[0].Minimum_Outdoor_Temperature_in_Heating_Mode == -20
        assert VRFobj[0].Maximum_Outdoor_Temperature_in_Heating_Mode == 40
        assert VRFobj[0].Heating_Capacity_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name == 'VRFHeatCapFT'
        assert VRFobj[0].Heating_Capacity_Ratio_Boundary_Curve_Name == 'VRFHeatCapFTBoundary'
        assert VRFobj[0].Heating_Capacity_Ratio_Modifier_Function_of_High_Temperature_Curve_Name == 'VRFHeatCapFTHi'
        assert VRFobj[0].Heating_Energy_Input_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name == 'VRFHeatEIRFT'
        assert VRFobj[0].Heating_Energy_Input_Ratio_Boundary_Curve_Name == 'VRFHeatEIRFTBoundary'
        assert VRFobj[0].Heating_Energy_Input_Ratio_Modifier_Function_of_High_Temperature_Curve_Name == 'VRFHeatEIRFTHi'
        assert VRFobj[0].Heating_Performance_Curve_Outdoor_Temperature_Type == 'WetBulbTemperature'
        assert VRFobj[0].Heating_Energy_Input_Ratio_Modifier_Function_of_Low_PartLoad_Ratio_Curve_Name == 'HeatingEIRLowPLR'
        assert VRFobj[0].Heating_Energy_Input_Ratio_Modifier_Function_of_High_PartLoad_Ratio_Curve_Name == 'HeatingEIRHiPLR'
        assert VRFobj[0].Heating_Combination_Ratio_Correction_Factor_Curve_Name == 'HeatingCombRatio'
        assert VRFobj[0].Heating_PartLoad_Fraction_Correlation_Curve_Name == 'VRFCPLFFPLR'
        assert VRFobj[0].Minimum_Heat_Pump_PartLoad_Ratio == 0.2
        assert VRFobj[0].Zone_Name_for_Master_Thermostat_Location == ''
        assert VRFobj[0].Master_Thermostat_Priority_Control_Type == 'LoadPriority'
        assert VRFobj[0].Thermostat_Priority_Schedule_Name == ''
        assert VRFobj[0].Zone_Terminal_Unit_List_Name == 'VRF Outdoor Unit_' + zonename + ' Zone List'
        assert VRFobj[0].Heat_Pump_Waste_Heat_Recovery == 'Yes'
        assert VRFobj[0].Equivalent_Piping_Length_used_for_Piping_Correction_Factor_in_Cooling_Mode == 50
        assert VRFobj[0].Vertical_Height_used_for_Piping_Correction_Factor == 15
        assert VRFobj[0].Piping_Correction_Factor_for_Length_in_Cooling_Mode_Curve_Name == 'CoolingLengthCorrectionFactor'
        assert VRFobj[0].Piping_Correction_Factor_for_Height_in_Cooling_Mode_Coefficient == 0
        assert VRFobj[0].Equivalent_Piping_Length_used_for_Piping_Correction_Factor_in_Heating_Mode == 50
        assert VRFobj[0].Piping_Correction_Factor_for_Length_in_Heating_Mode_Curve_Name == 'VRF Piping Correction Factor for Length in Heating Mode'
        assert VRFobj[0].Piping_Correction_Factor_for_Height_in_Heating_Mode_Coefficient == 0
        assert VRFobj[0].Crankcase_Heater_Power_per_Compressor == 15
        assert VRFobj[0].Number_of_Compressors == 2
        assert VRFobj[0].Ratio_of_Compressor_Size_to_Total_Compressor_Capacity == 0.5
        assert VRFobj[0].Maximum_Outdoor_DryBulb_Temperature_for_Crankcase_Heater == 5
        assert VRFobj[0].Defrost_Strategy == 'Resistive'
        assert VRFobj[0].Defrost_Control == 'Timed'
        assert VRFobj[0].Defrost_Energy_Input_Ratio_Modifier_Function_of_Temperature_Curve_Name == ''
        assert VRFobj[0].Defrost_Time_Period_Fraction == 0
        assert VRFobj[0].Resistive_Defrost_Heater_Capacity == 'autosize'
        assert VRFobj[0].Maximum_Outdoor_Drybulb_Temperature_for_Defrost_Operation == 5
        assert VRFobj[0].Condenser_Type == 'AirCooled'
        assert VRFobj[0].Condenser_Inlet_Node_Name == 'VRF Outdoor Unit_' + zonename + ' Outdoor Air Node'
        assert VRFobj[0].Condenser_Outlet_Node_Name == ''
        assert VRFobj[0].Water_Condenser_Volume_Flow_Rate == 'autosize'
        assert VRFobj[0].Evaporative_Condenser_Effectiveness == 0.9
        assert VRFobj[0].Evaporative_Condenser_Air_Flow_Rate == 'autosize'
        assert VRFobj[0].Evaporative_Condenser_Pump_Rated_Power_Consumption == 'autosize'
        assert VRFobj[0].Supply_Water_Storage_Tank_Name == ''
        assert VRFobj[0].Basin_Heater_Capacity == 0
        assert VRFobj[0].Basin_Heater_Setpoint_Temperature == 2
        assert VRFobj[0].Basin_Heater_Operating_Schedule_Name == 'On 24/7'
        assert VRFobj[0].Fuel_Type == 'Electricity'
        assert VRFobj[0].Minimum_Outdoor_Temperature_in_Heat_Recovery_Mode == -10
        assert VRFobj[0].Maximum_Outdoor_Temperature_in_Heat_Recovery_Mode == 40
        assert VRFobj[0].Heat_Recovery_Cooling_Capacity_Modifier_Curve_Name == 'VRF Heat Recovery Cooling Capacity Modifier'
        assert VRFobj[0].Initial_Heat_Recovery_Cooling_Capacity_Fraction == 0.5
        assert VRFobj[0].Heat_Recovery_Cooling_Capacity_Time_Constant == 0.15
        assert VRFobj[0].Heat_Recovery_Cooling_Energy_Modifier_Curve_Name == 'VRF Heat Recovery Cooling Energy Modifier'
        assert VRFobj[0].Initial_Heat_Recovery_Cooling_Energy_Fraction == 1
        assert VRFobj[0].Heat_Recovery_Cooling_Energy_Time_Constant == 0
        assert VRFobj[0].Heat_Recovery_Heating_Capacity_Modifier_Curve_Name == 'VRF Heat Recovery Heating Capacity Modifier'
        assert VRFobj[0].Initial_Heat_Recovery_Heating_Capacity_Fraction == 1
        assert VRFobj[0].Heat_Recovery_Heating_Capacity_Time_Constant == 0.15
        assert VRFobj[0].Heat_Recovery_Heating_Energy_Modifier_Curve_Name == 'VRF Heat Recovery Heating Energy Modifier'
        assert VRFobj[0].Initial_Heat_Recovery_Heating_Energy_Fraction == 1
        assert VRFobj[0].Heat_Recovery_Heating_Energy_Time_Constant == 0

    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['OutdoorAir:NodeList']
               if i.Node_or_NodeList_Name_1 == ('VRF Outdoor Unit_'
                                                + zonename
                                                + ' Outdoor Air Node')]
        assert obj[0].Node_or_NodeList_Name_1 == ('VRF Outdoor Unit_'
                                                  + zonename
                                                  + ' Outdoor Air Node')
    
    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['ZoneTerminalUnitList']
               if i.Zone_Terminal_Unit_List_Name == ('VRF Outdoor Unit_'
                                                     + zonename
                                                     + ' Zone List')]
        assert obj[0].Zone_Terminal_Unit_List_Name == ('VRF Outdoor Unit_'
                                                  + zonename
                                                  + ' Zone List')
        assert obj[0].Zone_Terminal_Unit_Name_1 == zonename + ' VRF Indoor Unit'

    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['ZoneControl:Thermostat']
               if i.Name == zonename + ' Thermostat']
        assert obj[0].Name == zonename + ' Thermostat'
        assert obj[0].Zone_or_ZoneList_Name == zonename
        assert obj[0].Control_Type_Schedule_Name == 'Control type schedule: Always 4'
        assert obj[0].Control_1_Object_Type == 'ThermostatSetpoint:DualSetpoint'
        assert obj[0].Control_1_Name == zonename + ' Dual SP'

        for zonename in zonenames_orig:
            obj = [i
                   for i
                   in idf1.idfobjects['Sizing:Zone']
                   if i.Zone_or_ZoneList_Name == zonename]
            assert obj[0].Zone_or_ZoneList_Name == zonename
            assert obj[0].Zone_Cooling_Design_Supply_Air_Temperature_Input_Method == 'SupplyAirTemperature'
            assert obj[0].Zone_Cooling_Design_Supply_Air_Temperature == 14
            assert obj[0].Zone_Cooling_Design_Supply_Air_Temperature_Difference == 5
            assert obj[0].Zone_Heating_Design_Supply_Air_Temperature_Input_Method == 'SupplyAirTemperature'
            assert obj[0].Zone_Heating_Design_Supply_Air_Temperature == 50
            assert obj[0].Zone_Heating_Design_Supply_Air_Temperature_Difference == 15
            assert obj[0].Zone_Cooling_Design_Supply_Air_Humidity_Ratio == 0.009
            assert obj[0].Zone_Heating_Design_Supply_Air_Humidity_Ratio == 0.004
            assert obj[0].Design_Specification_Outdoor_Air_Object_Name == zonename+' Design Specification Outdoor Air Object'
            assert obj[0].Zone_Heating_Sizing_Factor == 1.25
            assert obj[0].Zone_Cooling_Sizing_Factor == 1.15
            assert obj[0].Cooling_Design_Air_Flow_Method == 'DesignDay'
            assert obj[0].Cooling_Design_Air_Flow_Rate == 0
            assert obj[0].Cooling_Minimum_Air_Flow_per_Zone_Floor_Area == 0.00076
            assert obj[0].Cooling_Minimum_Air_Flow == 0
            assert obj[0].Cooling_Minimum_Air_Flow_Fraction == 0
            assert obj[0].Heating_Design_Air_Flow_Method == 'DesignDay'
            assert obj[0].Heating_Design_Air_Flow_Rate == 0
            assert obj[0].Heating_Maximum_Air_Flow_per_Zone_Floor_Area == 0.00203
            assert obj[0].Heating_Maximum_Air_Flow == 0.14158
            assert obj[0].Heating_Maximum_Air_Flow_Fraction == 0.3
            assert obj[0].Design_Specification_Zone_Air_Distribution_Object_Name == zonename+' Design Specification Zone Air Distribution Object'
            assert obj[0].Account_for_Dedicated_Outdoor_Air_System == 'Yes'
            assert obj[0].Dedicated_Outdoor_Air_System_Control_Strategy == 'NeutralSupplyAir'
            assert obj[0].Dedicated_Outdoor_Air_Low_Setpoint_Temperature_for_Design == 'autosize'
            assert obj[0].Dedicated_Outdoor_Air_High_Setpoint_Temperature_for_Design == 'autosize'

    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['DesignSpecification:OutdoorAir']
               if i.Name == zonename + ' Design Specification Outdoor Air Object']
        assert obj[0].Name == zonename + ' Design Specification Outdoor Air Object'
        assert obj[0].Outdoor_Air_Method == 'Flow/Person'
        assert obj[0].Outdoor_Air_Flow_per_Person == 0.00944
        assert obj[0].Outdoor_Air_Flow_per_Zone_Floor_Area == 0
        assert obj[0].Outdoor_Air_Flow_per_Zone == 0
        assert obj[0].Outdoor_Air_Flow_Air_Changes_per_Hour == 0
        assert obj[0].Outdoor_Air_Schedule_Name == 'On 24/7'
    
    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['DesignSpecification:ZoneAirDistribution']
               if i.Name == zonename + ' Design Specification Zone Air Distribution Object']
        assert obj[0].Name == zonename + ' Design Specification Zone Air Distribution Object'
        assert obj[0].Zone_Air_Distribution_Effectiveness_in_Cooling_Mode == 1
        assert obj[0].Zone_Air_Distribution_Effectiveness_in_Heating_Mode == 1
        assert obj[0].Zone_Air_Distribution_Effectiveness_Schedule_Name == ''
        assert obj[0].Zone_Secondary_Recirculation_Fraction == 0
    
    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['NodeList']
               if i.Name == zonename+' Air Inlet Node List']
        assert obj[0].Name == zonename + ' Air Inlet Node List'
        assert obj[0].Node_1_Name == zonename + ' VRF Indoor Unit Supply Outlet'
    
        obj = [i
               for i
               in idf1.idfobjects['NodeList']
               if i.Name == zonename+' Air Exhaust Node List']
        assert obj[0].Name == zonename + ' Air Exhaust Node List'
        assert obj[0].Node_1_Name == zonename + ' VRF Indoor Unit Return'

    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['ZoneHVAC:EquipmentConnections']
               if i.Zone_Name == zonename]
        assert obj[0].Zone_Name == zonename
        assert obj[0].Zone_Conditioning_Equipment_List_Name == zonename + ' Equipment'
        assert obj[0].Zone_Air_Inlet_Node_or_NodeList_Name == zonename + ' Air Inlet Node List'
        assert obj[0].Zone_Air_Exhaust_Node_or_NodeList_Name == zonename + ' Air Exhaust Node List'
        assert obj[0].Zone_Air_Node_Name == zonename + ' Zone Air Node'
        assert obj[0].Zone_Return_Air_Node_or_NodeList_Name == zonename + ' Return Outlet'
        
    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['ZoneHVAC:EquipmentList']
               if i.Name == zonename + ' Equipment']
        # assert obj[0].defaultvalues == False
        assert obj[0].Name == zonename + ' Equipment'
        assert obj[0].Load_Distribution_Scheme == 'SequentialLoad'
        assert obj[0].Zone_Equipment_1_Object_Type == 'ZoneHVAC:TerminalUnit:VariableRefrigerantFlow'
        assert obj[0].Zone_Equipment_1_Name == zonename + ' VRF Indoor Unit'
        assert obj[0].Zone_Equipment_1_Cooling_Sequence == 1
        assert obj[0].Zone_Equipment_1_Heating_or_NoLoad_Sequence == 1
        assert obj[0].Zone_Equipment_1_Sequential_Cooling_Fraction == ''
        assert obj[0].Zone_Equipment_1_Sequential_Heating_Fraction == ''

    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['ZoneHVAC:TerminalUnit:VariableRefrigerantFlow']
               if i.Zone_Terminal_Unit_Name == zonename + ' VRF Indoor Unit']
        assert obj[0].Zone_Terminal_Unit_Name == zonename + ' VRF Indoor Unit'
        assert obj[0].Terminal_Unit_Availability_Schedule == 'On 24/7'
        assert obj[0].Terminal_Unit_Air_Inlet_Node_Name == zonename + ' VRF Indoor Unit Return'
        assert obj[0].Terminal_Unit_Air_Outlet_Node_Name == zonename + ' VRF Indoor Unit Supply Outlet'
        assert obj[0].Cooling_Supply_Air_Flow_Rate == 'autosize'
        assert obj[0].No_Cooling_Supply_Air_Flow_Rate == 'autosize'
        assert obj[0].Heating_Supply_Air_Flow_Rate == 'autosize'
        assert obj[0].No_Heating_Supply_Air_Flow_Rate == 'autosize'
        assert obj[0].Cooling_Outdoor_Air_Flow_Rate == 0
        assert obj[0].Heating_Outdoor_Air_Flow_Rate == 0
        assert obj[0].No_Load_Outdoor_Air_Flow_Rate == 0
        assert obj[0].Supply_Air_Fan_Operating_Mode_Schedule_Name == 'On 24/7'
        assert obj[0].Supply_Air_Fan_Placement == 'DrawThrough'
        assert obj[0].Supply_Air_Fan_Object_Type == 'Fan:ConstantVolume'
        assert obj[0].Supply_Air_Fan_Object_Name == zonename + ' VRF Indoor Unit Supply Fan'
        assert obj[0].Outside_Air_Mixer_Object_Type == ''
        assert obj[0].Outside_Air_Mixer_Object_Name == ''
        assert obj[0].Cooling_Coil_Object_Type == 'Coil:Cooling:DX:VariableRefrigerantFlow'
        assert obj[0].Cooling_Coil_Object_Name == zonename + ' VRF Indoor Unit DX Cooling Coil'
        assert obj[0].Heating_Coil_Object_Type == 'Coil:Heating:DX:VariableRefrigerantFlow'
        assert obj[0].Heating_Coil_Object_Name == zonename + ' VRF Indoor Unit DX Heating Coil'
        assert obj[0].Zone_Terminal_Unit_On_Parasitic_Electric_Energy_Use == 30
        assert obj[0].Zone_Terminal_Unit_Off_Parasitic_Electric_Energy_Use == 20
        assert obj[0].Rated_Heating_Capacity_Sizing_Ratio == ''
        assert obj[0].Availability_Manager_List_Name == ''

    for zonename in zonenames_orig:
        obj = [i
               for i
               in idf1.idfobjects['Coil:Cooling:DX:VariableRefrigerantFlow']
               if i.Name == zonename + ' VRF Indoor Unit DX Cooling Coil']
        assert obj[0].Name == zonename + ' VRF Indoor Unit DX Cooling Coil'
        assert obj[0].Availability_Schedule_Name == 'On 24/7'
        assert obj[0].Gross_Rated_Total_Cooling_Capacity == 'autosize'
        assert obj[0].Gross_Rated_Sensible_Heat_Ratio == 'autosize'
        assert obj[0].Rated_Air_Flow_Rate == 'autosize'
        assert obj[0].Cooling_Capacity_Ratio_Modifier_Function_of_Temperature_Curve_Name == 'VRFTUCoolCapFT'
        assert obj[0].Cooling_Capacity_Modifier_Curve_Function_of_Flow_Fraction_Name == 'VRFACCoolCapFFF'
        assert obj[0].Coil_Air_Inlet_Node == zonename + ' VRF Indoor Unit Return'
        assert obj[0].Coil_Air_Outlet_Node == zonename + ' VRF Indoor Unit DX Cooling Coil Outlet'
        assert obj[0].Name_of_Water_Storage_Tank_for_Condensate_Collection == ''

    for zonename in zonenames_orig:                                       
        obj = [i                                                          
               for i                                                      
               in idf1.idfobjects['Coil:Heating:DX:VariableRefrigerantFlow']               
               if i.Name == zonename + ' VRF Indoor Unit DX Heating Coil']
        assert obj[0].Name == zonename + ' VRF Indoor Unit DX Heating Coil'
        assert obj[0].Availability_Schedule == 'On 24/7'
        assert obj[0].Gross_Rated_Heating_Capacity == 'autosize'
        assert obj[0].Rated_Air_Flow_Rate == 'autosize'
        assert obj[0].Coil_Air_Inlet_Node == zonename + ' VRF Indoor Unit DX Cooling Coil Outlet'
        assert obj[0].Coil_Air_Outlet_Node == zonename + ' VRF Indoor Unit DX Heating Coil Outlet'
        assert obj[0].Heating_Capacity_Ratio_Modifier_Function_of_Temperature_Curve_Name == 'VRFTUHeatCapFT'
        assert obj[0].Heating_Capacity_Modifier_Function_of_Flow_Fraction_Curve_Name == 'VRFACCoolCapFFF'
        
    for zonename in zonenames_orig:                                       
        obj = [i                                                          
               for i                                                      
               in idf1.idfobjects['Fan:ConstantVolume']               
               if i.Name == zonename + ' VRF Indoor Unit Supply Fan']
        assert obj[0].Name == zonename + ' VRF Indoor Unit Supply Fan'
        assert obj[0].Availability_Schedule_Name == 'On 24/7'
        assert obj[0].Fan_Total_Efficiency == 0.7
        assert obj[0].Pressure_Rise == 100
        assert obj[0].Maximum_Flow_Rate == 'autosize'
        assert obj[0].Motor_Efficiency == 0.9
        assert obj[0].Motor_In_Airstream_Fraction == 1
        assert obj[0].Air_Inlet_Node_Name == zonename + ' VRF Indoor Unit DX Heating Coil Outlet'
        assert obj[0].Air_Outlet_Node_Name == zonename + ' VRF Indoor Unit Supply Outlet'
        assert obj[0].EndUse_Subcategory == 'General'
