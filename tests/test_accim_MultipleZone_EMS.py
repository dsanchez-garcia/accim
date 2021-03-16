import pytest
from accim.sim import accim_Main

@pytest.fixture()
def IDFobject():
    from eppy.modeleditor import IDF

    iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
    IDF.setiddname(iddfile)

    z = accim_Main.accimInstance(
        filename_temp='TestModel_MultipleZone',
        ScriptType='mz',
        EnergyPlus_version='ep94',
        verboseMode=False)
    return z

def test_addGlobVarListMultipleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addGlobVarListMultipleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')
    
    gloVar = ([x
               for x
               in idf1.idfobjects['ENERGYMANAGEMENTSYSTEM:GLOBALVARIABLE']])
    assert gloVar[0].Erl_Variable_1_Name == 'ACST'
    assert gloVar[0].Erl_Variable_2_Name == 'AHST'
    assert gloVar[0].Erl_Variable_3_Name == 'ACSTnoTol'
    assert gloVar[0].Erl_Variable_4_Name == 'AHSTnoTol'
    assert gloVar[0].Erl_Variable_5_Name == 'AdapStand'
    assert gloVar[0].Erl_Variable_6_Name == 'ACSTaul'
    assert gloVar[0].Erl_Variable_7_Name == 'ACSTall'
    assert gloVar[0].Erl_Variable_8_Name == 'AHSTaul'
    assert gloVar[0].Erl_Variable_9_Name == 'AHSTall'
    assert gloVar[0].Erl_Variable_10_Name == 'CAT'
    assert gloVar[0].Erl_Variable_11_Name == 'ACSToffset'
    assert gloVar[0].Erl_Variable_12_Name == 'AHSToffset'
    assert gloVar[0].Erl_Variable_13_Name == 'ComfMod'
    assert gloVar[0].Erl_Variable_14_Name == 'ComfTemp'
    assert gloVar[0].Erl_Variable_15_Name == 'ACSTtol'
    assert gloVar[0].Erl_Variable_16_Name == 'AHSTtol'
    assert gloVar[0].Erl_Variable_17_Name == 'VST'
    assert gloVar[0].Erl_Variable_18_Name == 'VSToffset'
    assert gloVar[0].Erl_Variable_19_Name == 'MaxWindSpeed'
    assert gloVar[0].Erl_Variable_20_Name == 'VentCtrl'
    assert gloVar[0].Erl_Variable_21_Name == 'HVACmode'
    assert gloVar[0].Erl_Variable_22_Name == 'MinOutTemp'
    assert gloVar[0].Erl_Variable_23_Name == 'MinOToffset'
    
    zonenames = ([sub.replace(':', '_')
                  for sub
                  in ([zone.Name for zone in idf1.idfobjects['ZONE']])])
    for zonename in zonenames:
        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:GlobalVariable']
                if x.Erl_Variable_1_Name == 'ComfHours_'+zonename])
        assert obj[0].Erl_Variable_1_Name == 'ComfHours_'+zonename
        assert obj[0].Erl_Variable_2_Name == 'DiscomfAppHotHours_'+zonename
        assert obj[0].Erl_Variable_3_Name == 'DiscomfAppColdHours_'+zonename
        assert obj[0].Erl_Variable_4_Name == 'DiscomfNonAppHotHours_'+zonename
        assert obj[0].Erl_Variable_5_Name == 'DiscomfNonAppColdHours_'+zonename
        assert obj[0].Erl_Variable_6_Name == 'ComfHoursNoApp_'+zonename


def test_addEMSSensorsMultipleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addEMSSensorsMultipleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')

    zonenames_orig = ([zone.Name for zone in idf1.idfobjects['ZONE']])
    zonenames = ([sub.replace(':', '_') for sub in ([zone.Name for zone in idf1.idfobjects['ZONE']])])

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:Sensor']
            if x.Name == 'RMOT'])
    assert obj[0].Name == 'RMOT'
    assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == 'People ' + zonenames_orig[0]
    assert obj[0].OutputVariable_or_OutputMeter_Name == 'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature'

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:Sensor']
            if x.Name == 'PMOT'])
    assert obj[0].Name == 'PMOT'
    assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == 'People ' + zonenames_orig[0]
    assert obj[0].OutputVariable_or_OutputMeter_Name == 'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature'

    for i in range(len(zonenames)):
        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Sensor']
                if x.Name == zonenames[i] + '_OpT'])
        assert obj[0].Name == zonenames[i] + '_OpT'
        assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == zonenames_orig[i]
        assert obj[0].OutputVariable_or_OutputMeter_Name == 'Zone Operative Temperature'

        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Sensor']
                if x.Name == zonenames[i] + '_CoolCoil'])
        assert obj[0].Name == zonenames[i] + '_CoolCoil'
        assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == zonenames_orig[i] + ' VRF Indoor Unit DX Cooling Coil'
        assert obj[0].OutputVariable_or_OutputMeter_Name == 'Cooling Coil Total Cooling Rate'

        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Sensor']
                if x.Name == zonenames[i] + '_HeatCoil'])
        assert obj[0].Name == zonenames[i] + '_HeatCoil'
        assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == zonenames_orig[i] + ' VRF Indoor Unit DX Heating Coil'
        assert obj[0].OutputVariable_or_OutputMeter_Name == 'Heating Coil Heating Rate'

        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Sensor']
                if x.Name == zonenames[i] + '_WindSpeed'])
        assert obj[0].Name == zonenames[i] + '_WindSpeed'
        assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == zonenames_orig[i]
        assert obj[0].OutputVariable_or_OutputMeter_Name == 'Zone Outdoor Air Wind Speed'

        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Sensor']
                if x.Name == zonenames[i] + '_OutT'])
        assert obj[0].Name == zonenames[i] + '_OutT'
        assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == zonenames_orig[i]
        assert obj[0].OutputVariable_or_OutputMeter_Name == 'Zone Outdoor Air Drybulb Temperature'

        windownamelist_orig = ([window.Name
                                for window
                                in idf1.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening']
                                if window.Name.endswith('_Win')])
        windownamelist_orig_split = ([i.split('_') for i in windownamelist_orig])
        windownamelist = ([sub.replace(':', '_')
                           for sub
                           in ([window.Name
                                for window
                                in idf1.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening']
                                if window.Name.endswith('_Win')])])


        for i in range(len(windownamelist)):
            obj = ([x
                    for x
                    in idf1.idfobjects['EnergyManagementSystem:Sensor']
                    if x.Name == windownamelist[i]+'_OpT'])
            assert obj[0].Name == windownamelist[i] + '_OpT'
            assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == windownamelist_orig_split[i][0]
            assert obj[0].OutputVariable_or_OutputMeter_Name == 'Zone Operative Temperature'
            
            obj = ([x
                    for x
                    in idf1.idfobjects['EnergyManagementSystem:Sensor']
                    if x.Name == windownamelist[i] + '_CoolCoil'])
            assert obj[0].Name == windownamelist[i] + '_CoolCoil'
            assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == windownamelist_orig_split[i][0] + ' VRF Indoor Unit DX Cooling Coil'
            assert obj[0].OutputVariable_or_OutputMeter_Name == 'Cooling Coil Total Cooling Rate'

            obj = ([x
                    for x
                    in idf1.idfobjects['EnergyManagementSystem:Sensor']
                    if x.Name == windownamelist[i] + '_HeatCoil'])
            assert obj[0].Name == windownamelist[i] + '_HeatCoil'
            assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == windownamelist_orig_split[i][0] + ' VRF Indoor Unit DX Heating Coil'
            assert obj[0].OutputVariable_or_OutputMeter_Name == 'Heating Coil Heating Rate'

            obj = ([x
                    for x
                    in idf1.idfobjects['EnergyManagementSystem:Sensor']
                    if x.Name == windownamelist[i] + '_WindSpeed'])
            assert obj[0].Name == windownamelist[i] + '_WindSpeed'
            assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == windownamelist_orig_split[i][0]
            assert obj[0].OutputVariable_or_OutputMeter_Name == 'Zone Outdoor Air Wind Speed'

            obj = ([x
                    for x
                    in idf1.idfobjects['EnergyManagementSystem:Sensor']
                    if x.Name == windownamelist[i] + '_OutT'])
            assert obj[0].Name == windownamelist[i] + '_OutT'
            assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == windownamelist_orig_split[i][0]
            assert obj[0].OutputVariable_or_OutputMeter_Name == 'Zone Outdoor Air Drybulb Temperature'

        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Sensor']
                if x.Name == 'OutT'])
        assert obj[0].Name == 'OutT'
        assert obj[0].OutputVariable_or_OutputMeter_Index_Key_Name == 'Environment'
        assert obj[0].OutputVariable_or_OutputMeter_Name == 'Site Outdoor Air Drybulb Temperature'


def test_addEMSActuatorsMultipleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addEMSActuatorsMultipleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')

    zonenames = ([sub.replace(':', '_')
                  for sub
                  in ([zone.Name for zone in idf1.idfobjects['ZONE']])])
    for zonename in zonenames:
        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Actuator']
                if x.Name == 'FORSCRIPT_AHST_Sch_' + zonename])
        assert obj[0].Name == 'FORSCRIPT_AHST_Sch_' + zonename
        assert obj[0].Actuated_Component_Unique_Name == 'FORSCRIPT_AHST_' + zonename
        assert obj[0].Actuated_Component_Type == 'Schedule:Compact'
        assert obj[0].Actuated_Component_Control_Type == 'Schedule Value'
        
        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Actuator']
                if x.Name == 'FORSCRIPT_ACST_Sch_' + zonename])
        assert obj[0].Name == 'FORSCRIPT_ACST_Sch_' + zonename
        assert obj[0].Actuated_Component_Unique_Name == 'FORSCRIPT_ACST_' + zonename
        assert obj[0].Actuated_Component_Type == 'Schedule:Compact'
        assert obj[0].Actuated_Component_Control_Type == 'Schedule Value'

    windownamelist = ([sub.replace(':', '_') for sub in (
    [window.Name for window in idf1.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening'] if
     window.Name.endswith('_Win')])])
    windownamelist_orig = (
    [window.Name for window in idf1.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening'] if
     window.Name.endswith('_Win')])

    for i in range(len(windownamelist)):
        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Actuator']
                if x.Name == windownamelist[i] + '_VentOpenFact'])
        assert obj[0].Name == windownamelist[i] + '_VentOpenFact'
        assert obj[0].Actuated_Component_Unique_Name == windownamelist_orig[i]
        assert obj[0].Actuated_Component_Type == 'AirFlow Network Window/Door Opening'
        assert obj[0].Actuated_Component_Control_Type == 'Venting Opening Factor'


def test_addEMSProgramsMultipleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addEMSProgramsMultipleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:Program']
            if x.Name == 'SetInputData'])
    assert obj[0].Name == 'SetInputData'
    assert obj[0].Program_Line_1 == 'set AdapStand = 1'
    assert obj[0].Program_Line_2 == 'set CAT = 1'
    assert obj[0].Program_Line_3 == 'set ComfMod = 2'
    assert obj[0].Program_Line_4 == 'set HVACmode = 2'
    assert obj[0].Program_Line_5 == 'set VentCtrl = 0'
    assert obj[0].Program_Line_6 == 'set VSToffset = 0'
    assert obj[0].Program_Line_7 == 'set MinOToffset = 7'
    assert obj[0].Program_Line_8 == 'set MaxWindSpeed = 6'
    assert obj[0].Program_Line_9 == 'set ACSTtol = -0.25'
    assert obj[0].Program_Line_10 == 'set AHSTtol = 0.25'

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:Program']
            if x.Name == 'SetVST'])
    assert obj[0].Name == 'SetVST'
    assert obj[0].Program_Line_1 == 'set MinOutTemp = AHST - MinOToffset'
    assert obj[0].Program_Line_2 == 'if AdapStand == 0'
    assert obj[0].Program_Line_3 == 'if (CurrentTime < 7)'
    assert obj[0].Program_Line_4 == 'set VST = (ACST+AHST)/2+VSToffset'
    assert obj[0].Program_Line_5 == 'elseif (CurrentTime < 15)'
    assert obj[0].Program_Line_6 == 'set VST = 22.5+VSToffset'
    assert obj[0].Program_Line_7 == 'elseif (CurrentTime < 23)'
    assert obj[0].Program_Line_8 == 'set VST = (ACST+AHST)/2+VSToffset'
    assert obj[0].Program_Line_9 == 'elseif (CurrentTime < 24)'
    assert obj[0].Program_Line_10 == 'set VST = (ACST+AHST)/2+VSToffset'
    assert obj[0].Program_Line_11 == 'endif'
    assert obj[0].Program_Line_12 == 'elseif AdapStand == 1'
    assert obj[0].Program_Line_13 == 'if (RMOT >= AHSTall) && (RMOT <= ACSTaul)'
    assert obj[0].Program_Line_14 == 'set VST = ComfTemp+VSToffset'
    assert obj[0].Program_Line_15 == 'else'
    assert obj[0].Program_Line_16 == 'set VST = (ACST+AHST)/2+VSToffset'
    assert obj[0].Program_Line_17 == 'endif'
    assert obj[0].Program_Line_18 == 'elseif AdapStand == 2'
    assert obj[0].Program_Line_19 == 'if (PMOT >= AHSTall) && (PMOT <= ACSTaul)'
    assert obj[0].Program_Line_20 == 'set VST = ComfTemp+VSToffset'
    assert obj[0].Program_Line_21 == 'else'
    assert obj[0].Program_Line_22 == 'set VST = (ACST+AHST)/2+VSToffset'
    assert obj[0].Program_Line_23 == 'endif'
    assert obj[0].Program_Line_24 == 'endif'
    
    zonenames = ([sub.replace(':', '_')
                  for sub
                  in ([zone.Name for zone in idf1.idfobjects['ZONE']])])
    for zonename in zonenames:
        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Program']
                if x.Name == 'ApplyAST_MultipleZone_' + zonename])
        assert obj[0].Name == 'ApplyAST_MultipleZone_' + zonename
        assert obj[0].Program_Line_1 == 'if (' + zonename + '_OpT>VST)&&(' + zonename + '_OutT < VST)'
        assert obj[0].Program_Line_2 == 'if ' + zonename + '_CoolCoil==0'
        assert obj[0].Program_Line_3 == 'if ' + zonename + '_HeatCoil==0'
        assert obj[0].Program_Line_4 == 'if (' + zonename + '_OpT<ACST)&&(' + zonename + '_OutT>MinOutTemp)'
        assert obj[0].Program_Line_5 == 'if ' + zonename + '_WindSpeed <= MaxWindSpeed'
        assert obj[0].Program_Line_6 == 'set Ventilates_HVACmode2_' + zonename + ' = 1'
        assert obj[0].Program_Line_7 == 'else'
        assert obj[0].Program_Line_8 == 'set Ventilates_HVACmode2_' + zonename + ' = 0'
        assert obj[0].Program_Line_9 == 'endif'
        assert obj[0].Program_Line_10 == 'else'
        assert obj[0].Program_Line_11 == 'set Ventilates_HVACmode2_' + zonename + ' = 0'
        assert obj[0].Program_Line_12 == 'endif'
        assert obj[0].Program_Line_13 == 'else'
        assert obj[0].Program_Line_14 == 'set Ventilates_HVACmode2_' + zonename + ' = 0'
        assert obj[0].Program_Line_15 == 'endif'
        assert obj[0].Program_Line_16 == 'else'
        assert obj[0].Program_Line_17 == 'set Ventilates_HVACmode2_' + zonename + ' = 0'
        assert obj[0].Program_Line_18 == 'endif'
        assert obj[0].Program_Line_19 == 'else'
        assert obj[0].Program_Line_20 == 'set Ventilates_HVACmode2_' + zonename + ' = 0'
        assert obj[0].Program_Line_21 == 'endif'
        assert obj[0].Program_Line_22 == 'if VentCtrl == 0'
        assert obj[0].Program_Line_23 == 'if ' + zonename + '_OutT < ' + zonename + '_OpT'
        assert obj[0].Program_Line_24 == 'if ' + zonename + '_OutT>MinOutTemp'
        assert obj[0].Program_Line_25 == 'if ' + zonename + '_OpT > VST'
        assert obj[0].Program_Line_26 == 'if ' + zonename + '_WindSpeed <= MaxWindSpeed'
        assert obj[0].Program_Line_27 == 'set Ventilates_HVACmode1_' + zonename + ' = 1'
        assert obj[0].Program_Line_28 == 'else'
        assert obj[0].Program_Line_29 == 'set Ventilates_HVACmode1_' + zonename + ' = 0'
        assert obj[0].Program_Line_30 == 'endif'
        assert obj[0].Program_Line_31 == 'else'
        assert obj[0].Program_Line_32 == 'set Ventilates_HVACmode1_' + zonename + ' = 0'
        assert obj[0].Program_Line_33 == 'endif'
        assert obj[0].Program_Line_34 == 'else'
        assert obj[0].Program_Line_35 == 'set Ventilates_HVACmode1_' + zonename + ' = 0'
        assert obj[0].Program_Line_36 == 'endif'
        assert obj[0].Program_Line_37 == 'else'
        assert obj[0].Program_Line_38 == 'set Ventilates_HVACmode1_' + zonename + ' = 0'
        assert obj[0].Program_Line_39 == 'endif'
        assert obj[0].Program_Line_40 == 'elseif VentCtrl == 1'
        assert obj[0].Program_Line_41 == 'if ' + zonename + '_OutT<' + zonename + '_OpT'
        assert obj[0].Program_Line_42 == 'if ' + zonename + '_OutT>MinOutTemp'
        assert obj[0].Program_Line_43 == 'if ' + zonename + '_OpT > ACSTnoTol'
        assert obj[0].Program_Line_44 == 'if ' + zonename + '_WindSpeed <= MaxWindSpeed'
        assert obj[0].Program_Line_45 == 'set Ventilates_HVACmode1_' + zonename + ' = 1'
        assert obj[0].Program_Line_46 == 'else'
        assert obj[0].Program_Line_47 == 'set Ventilates_HVACmode1_' + zonename + ' = 0'
        assert obj[0].Program_Line_48 == 'endif'
        assert obj[0].Program_Line_49 == 'else'
        assert obj[0].Program_Line_50 == 'set Ventilates_HVACmode1_' + zonename + ' = 0'
        assert obj[0].Program_Line_51 == 'endif'
        assert obj[0].Program_Line_52 == 'else'
        assert obj[0].Program_Line_53 == 'set Ventilates_HVACmode1_' + zonename + ' = 0'
        assert obj[0].Program_Line_54 == 'endif'
        assert obj[0].Program_Line_55 == 'else'
        assert obj[0].Program_Line_56 == 'set Ventilates_HVACmode1_' + zonename + ' = 0'
        assert obj[0].Program_Line_57 == 'endif'
        assert obj[0].Program_Line_58 == 'endif'
        assert obj[0].Program_Line_59 == 'if HVACmode == 0'
        assert obj[0].Program_Line_60 == 'set FORSCRIPT_ACST_Sch_' + zonename + ' = ACST'
        assert obj[0].Program_Line_61 == 'set FORSCRIPT_AHST_Sch_' + zonename + ' = AHST'
        assert obj[0].Program_Line_62 == 'elseif HVACmode == 1'
        assert obj[0].Program_Line_63 == 'Set FORSCRIPT_ACST_Sch_' + zonename + ' = 100'
        assert obj[0].Program_Line_64 == 'Set FORSCRIPT_AHST_Sch_' + zonename + ' = -100'
        assert obj[0].Program_Line_65 == 'elseif HVACmode == 2'
        assert obj[0].Program_Line_66 == 'if Ventilates_HVACmode2_' + zonename + ' == 0'
        assert obj[0].Program_Line_67 == 'set FORSCRIPT_ACST_Sch_' + zonename + ' = ACST'
        assert obj[0].Program_Line_68 == 'set FORSCRIPT_AHST_Sch_' + zonename + ' = AHST'
        assert obj[0].Program_Line_69 == 'endif'
        assert obj[0].Program_Line_70 == 'endif'

    windownamelist = ([sub.replace(':', '_') for sub in (
    [window.Name for window in idf1.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening'] if
     window.Name.endswith('_Win')])])

    for windowname in windownamelist:
        obj = ([x
                for x
                in idf1.idfobjects['EnergyManagementSystem:Program']
                if x.Name == 'SetWindowOperation_' + windowname])
        assert obj[0].Name == 'SetWindowOperation_' + windowname
        assert obj[0].Program_Line_1 == 'if (' + windowname + '_OpT>VST)&&(' + windowname + '_OutT < VST)'
        assert obj[0].Program_Line_2 == 'if ' + windowname + '_CoolCoil==0'
        assert obj[0].Program_Line_3 == 'if ' + windowname + '_HeatCoil==0'
        assert obj[0].Program_Line_4 == 'if (' + windowname + '_OpT<ACST)&&(' + windowname + '_OutT>MinOutTemp)'
        assert obj[0].Program_Line_5 == 'if ' + windowname + '_WindSpeed <= MaxWindSpeed'
        assert obj[0].Program_Line_6 == 'set Ventilates_HVACmode2_' + windowname + ' = 1'
        assert obj[0].Program_Line_7 == 'else'
        assert obj[0].Program_Line_8 == 'set Ventilates_HVACmode2_' + windowname + ' = 0'
        assert obj[0].Program_Line_9 == 'endif'
        assert obj[0].Program_Line_10 == 'else'
        assert obj[0].Program_Line_11 == 'set Ventilates_HVACmode2_' + windowname + ' = 0'
        assert obj[0].Program_Line_12 == 'endif'
        assert obj[0].Program_Line_13 == 'else'
        assert obj[0].Program_Line_14 == 'set Ventilates_HVACmode2_' + windowname + ' = 0'
        assert obj[0].Program_Line_15 == 'endif'
        assert obj[0].Program_Line_16 == 'else'
        assert obj[0].Program_Line_17 == 'set Ventilates_HVACmode2_' + windowname + ' = 0'
        assert obj[0].Program_Line_18 == 'endif'
        assert obj[0].Program_Line_19 == 'else'
        assert obj[0].Program_Line_20 == 'set Ventilates_HVACmode2_' + windowname + ' = 0'
        assert obj[0].Program_Line_21 == 'endif'
        assert obj[0].Program_Line_22 == 'if VentCtrl == 0'
        assert obj[0].Program_Line_23 == 'if ' + windowname + '_OutT < ' + windowname + '_OpT'
        assert obj[0].Program_Line_24 == 'if ' + windowname + '_OutT>MinOutTemp'
        assert obj[0].Program_Line_25 == 'if ' + windowname + '_OpT > VST'
        assert obj[0].Program_Line_26 == 'if ' + windowname + '_WindSpeed <= MaxWindSpeed'
        assert obj[0].Program_Line_27 == 'set Ventilates_HVACmode1_' + windowname + ' = 1'
        assert obj[0].Program_Line_28 == 'else'
        assert obj[0].Program_Line_29 == 'set Ventilates_HVACmode1_' + windowname + ' = 0'
        assert obj[0].Program_Line_30 == 'endif'
        assert obj[0].Program_Line_31 == 'else'
        assert obj[0].Program_Line_32 == 'set Ventilates_HVACmode1_' + windowname + ' = 0'
        assert obj[0].Program_Line_33 == 'endif'
        assert obj[0].Program_Line_34 == 'else'
        assert obj[0].Program_Line_35 == 'set Ventilates_HVACmode1_' + windowname + ' = 0'
        assert obj[0].Program_Line_36 == 'endif'
        assert obj[0].Program_Line_37 == 'else'
        assert obj[0].Program_Line_38 == 'set Ventilates_HVACmode1_' + windowname + ' = 0'
        assert obj[0].Program_Line_39 == 'endif'
        assert obj[0].Program_Line_40 == 'elseif VentCtrl == 1'
        assert obj[0].Program_Line_41 == 'if ' + windowname + '_OutT<' + windowname + '_OpT'
        assert obj[0].Program_Line_42 == 'if ' + windowname + '_OutT>MinOutTemp'
        assert obj[0].Program_Line_43 == 'if ' + windowname + '_OpT > ACSTnoTol'
        assert obj[0].Program_Line_44 == 'if ' + windowname + '_WindSpeed <= MaxWindSpeed'
        assert obj[0].Program_Line_45 == 'set Ventilates_HVACmode1_' + windowname + ' = 1'
        assert obj[0].Program_Line_46 == 'else'
        assert obj[0].Program_Line_47 == 'set Ventilates_HVACmode1_' + windowname + ' = 0'
        assert obj[0].Program_Line_48 == 'endif'
        assert obj[0].Program_Line_49 == 'else'
        assert obj[0].Program_Line_50 == 'set Ventilates_HVACmode1_' + windowname + ' = 0'
        assert obj[0].Program_Line_51 == 'endif'
        assert obj[0].Program_Line_52 == 'else'
        assert obj[0].Program_Line_53 == 'set Ventilates_HVACmode1_' + windowname + ' = 0'
        assert obj[0].Program_Line_54 == 'endif'
        assert obj[0].Program_Line_55 == 'else'
        assert obj[0].Program_Line_56 == 'set Ventilates_HVACmode1_' + windowname + ' = 0'
        assert obj[0].Program_Line_57 == 'endif'
        assert obj[0].Program_Line_58 == 'endif'
        assert obj[0].Program_Line_59 == 'if HVACmode == 0'
        assert obj[0].Program_Line_60 == 'set ' + windowname + '_VentOpenFact = 0'
        assert obj[0].Program_Line_61 == 'elseif HVACmode == 1'
        assert obj[0].Program_Line_62 == 'if Ventilates_HVACmode1_' + windowname + ' == 1'
        assert obj[0].Program_Line_63 == 'set ' + windowname + '_VentOpenFact = 1'
        assert obj[0].Program_Line_64 == 'else'
        assert obj[0].Program_Line_65 == 'set ' + windowname + '_VentOpenFact = 0'
        assert obj[0].Program_Line_66 == 'endif'
        assert obj[0].Program_Line_67 == 'elseif HVACmode == 2'
        assert obj[0].Program_Line_68 == 'if Ventilates_HVACmode2_' + windowname + ' == 1'
        assert obj[0].Program_Line_69 == 'set ' + windowname + '_VentOpenFact = 1'
        assert obj[0].Program_Line_70 == 'else'
        assert obj[0].Program_Line_71 == 'set ' + windowname + '_VentOpenFact = 0'
        assert obj[0].Program_Line_72 == 'endif'
        assert obj[0].Program_Line_73 == 'endif'


def test_addEMSOutputVariableMultipleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addEMSOutputVariableMultipleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:OutputVariable']
            if x.Name == 'Ventilation Setpoint Temperature'])
    assert obj[0].Name == 'Ventilation Setpoint Temperature'
    assert obj[0].EMS_Variable_Name == 'VST'
    assert obj[0].Type_of_Data_in_Variable == 'Averaged'
    assert obj[0].Update_Frequency == 'ZoneTimestep'
    assert obj[0].EMS_Program_or_Subroutine_Name == ''
    assert obj[0].Units == 'C'

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:OutputVariable']
            if x.Name == 'Minimum Outdoor Temperature for MultipleZone ventilation'])
    assert obj[0].Name == 'Minimum Outdoor Temperature for MultipleZone ventilation'
    assert obj[0].EMS_Variable_Name == 'MinOutTemp'
    assert obj[0].Type_of_Data_in_Variable == 'Averaged'
    assert obj[0].Update_Frequency == 'ZoneTimestep'
    assert obj[0].EMS_Program_or_Subroutine_Name == ''
    assert obj[0].Units == 'C'


def test_addOutputVariablesMultipleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addOutputVariablesMultipleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')

    outputvariablelist = ([outputvariable.Name
                           for outputvariable
                           in idf1.idfobjects['EnergyManagementSystem:OutputVariable']])

    for outputvariable in outputvariablelist:
        obj = ([x
                for x
                in idf1.idfobjects['Output:Variable']
                if x.Variable_Name == outputvariable])
        assert obj[0].Key_Value == '*'
        assert obj[0].Variable_Name == outputvariable
        assert obj[0].Reporting_Frequency == 'Hourly'
        assert obj[0].Schedule_Name == ''
        
    addittionaloutputs = [
        'Zone Thermostat Operative Temperature',
        'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature',
        'Cooling Coil Total Cooling Rate',
        'Heating Coil Heating Rate',
        'Facility Total HVAC Electric Demand Power',
        'Facility Total HVAC Electricity Demand Rate',
        'VRF Heat Pump Cooling Electricity Energy',
        'VRF Heat Pump Heating Electricity Energy',
        'AFN Surface Venting Window or Door Opening Factor',
        'AFN Zone Infiltration Air Change Rate',
        'AFN Zone Infiltration Volume'
        ]

    for addittionaloutput in addittionaloutputs:
        obj = ([x
                for x
                in idf1.idfobjects['Output:Variable']
                if x.Variable_Name == addittionaloutput])
        assert obj[0].Key_Value == '*'
        assert obj[0].Variable_Name == addittionaloutput
        assert obj[0].Reporting_Frequency == 'Hourly'
        assert obj[0].Schedule_Name == ''
        
    zonenames = ([sub.replace(':', '_')
                  for sub
                  in ([zone.Name for zone in idf1.idfobjects['ZONE']])])
    for zonename in zonenames:
        obj = ([x
                for x
                in idf1.idfobjects['Output:Variable']
                if x.Key_Value == 'FORSCRIPT_AHST_' + zonename])
        assert obj[0].Key_Value == 'FORSCRIPT_AHST_'+zonename
        assert obj[0].Variable_Name == 'Schedule Value'
        assert obj[0].Reporting_Frequency == 'Hourly'
        assert obj[0].Schedule_Name == ''
        
        obj = ([x
                for x
                in idf1.idfobjects['Output:Variable']
                if x.Key_Value == 'FORSCRIPT_ACST_' + zonename])
        assert obj[0].Key_Value == 'FORSCRIPT_ACST_'+zonename
        assert obj[0].Variable_Name == 'Schedule Value'
        assert obj[0].Reporting_Frequency == 'Hourly'
        assert obj[0].Schedule_Name == ''

    zonenames_orig = ([zone.Name for zone in idf1.idfobjects['ZONE']])
    
    for zonename in zonenames_orig:
        obj = ([x
                for x
                in idf1.idfobjects['Output:Variable']
                if x.Key_Value == zonename
                and x.Variable_Name == 'Zone Operative Temperature'])
        assert obj[0].Key_Value == zonename
        assert obj[0].Variable_Name == 'Zone Operative Temperature'
        assert obj[0].Reporting_Frequency == 'Hourly'
        assert obj[0].Schedule_Name == ''

        obj = ([x
                for x
                in idf1.idfobjects['Output:Variable']
                if x.Key_Value == zonename+' VRF Indoor Unit DX Cooling Coil'
                and x.Variable_Name == 'Cooling Coil Total Cooling Rate'])
        assert obj[0].Key_Value == zonename+' VRF Indoor Unit DX Cooling Coil'
        assert obj[0].Variable_Name == 'Cooling Coil Total Cooling Rate'
        assert obj[0].Reporting_Frequency == 'Hourly'
        assert obj[0].Schedule_Name == ''

        obj = ([x
                for x
                in idf1.idfobjects['Output:Variable']
                if x.Key_Value == zonename + ' VRF Indoor Unit DX Heating Coil'
                and x.Variable_Name == 'Heating Coil Heating Rate'])
        assert obj[0].Key_Value == zonename+' VRF Indoor Unit DX Heating Coil'
        assert obj[0].Variable_Name == 'Heating Coil Heating Rate'
        assert obj[0].Reporting_Frequency == 'Hourly'
        assert obj[0].Schedule_Name == ''

        obj = ([x
                for x
                in idf1.idfobjects['Output:Variable']
                if x.Key_Value == zonename
                and x.Variable_Name == 'Zone Outdoor Air Wind Speed'])
        assert obj[0].Key_Value == zonename
        assert obj[0].Variable_Name == 'Zone Outdoor Air Wind Speed'
        assert obj[0].Reporting_Frequency == 'Hourly'
        assert obj[0].Schedule_Name == ''
