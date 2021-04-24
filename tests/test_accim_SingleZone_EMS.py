import pytest
from accim.sim import accim_Main

@pytest.fixture()
def IDFobject():
    from eppy.modeleditor import IDF

    iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
    IDF.setiddname(iddfile)

    z = accim_Main.accimJob(
        filename_temp='TestModel_SingleZone',
        ScriptType='sz',
        EnergyPlus_version='ep94',
        verboseMode=False)
    return z

def test_addGlobVarListSingleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addGlobVarListSingleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:GlobalVariable']])
    assert obj[0].Erl_Variable_1_Name == 'ACST'
    assert obj[0].Erl_Variable_2_Name == 'AHST'
    assert obj[0].Erl_Variable_3_Name == 'ACSTnoTol'
    assert obj[0].Erl_Variable_4_Name == 'AHSTnoTol'
    assert obj[0].Erl_Variable_5_Name == 'AdapStand'
    assert obj[0].Erl_Variable_6_Name == 'ACSTaul'
    assert obj[0].Erl_Variable_7_Name == 'ACSTall'
    assert obj[0].Erl_Variable_8_Name == 'AHSTaul'
    assert obj[0].Erl_Variable_9_Name == 'AHSTall'
    assert obj[0].Erl_Variable_10_Name == 'CAT'
    assert obj[0].Erl_Variable_11_Name == 'ACSToffset'
    assert obj[0].Erl_Variable_12_Name == 'AHSToffset'
    assert obj[0].Erl_Variable_13_Name == 'ComfMod'
    assert obj[0].Erl_Variable_14_Name == 'ComfTemp'
    assert obj[0].Erl_Variable_15_Name == 'ACSTtol'
    assert obj[0].Erl_Variable_16_Name == 'AHSTtol'

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

def test_addEMSSensorsSingleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addEMSSensorsSingleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

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

def test_addEMSActuatorsSingleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addEMSActuatorsSingleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:Actuator']
            if x.Name == 'FORSCRIPT_AHST_Schedule'])
    assert obj[0].Name == 'FORSCRIPT_AHST_Schedule'
    assert obj[0].Actuated_Component_Unique_Name == 'FORSCRIPT_AHST'
    assert obj[0].Actuated_Component_Type == 'Schedule:Compact'
    assert obj[0].Actuated_Component_Control_Type == 'Schedule Value'

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:Actuator']
            if x.Name == 'FORSCRIPT_ACST_Schedule'])
    assert obj[0].Name == 'FORSCRIPT_ACST_Schedule'
    assert obj[0].Actuated_Component_Unique_Name == 'FORSCRIPT_ACST'
    assert obj[0].Actuated_Component_Type == 'Schedule:Compact'
    assert obj[0].Actuated_Component_Control_Type == 'Schedule Value'

def test_addEMSProgramsSingleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addEMSProgramsSingleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')
    
    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:Program']
            if x.Name == 'SetInputData'])
    assert obj[0].Name == 'SetInputData'
    assert obj[0].Program_Line_1 == 'set AdapStand = 1'
    assert obj[0].Program_Line_2 == 'set CAT = 1'
    assert obj[0].Program_Line_3 == 'set ComfMod = 1'
    assert obj[0].Program_Line_4 == 'set ACSTtol = -0.25'
    assert obj[0].Program_Line_5 == 'set AHSTtol = 0.25'

    obj = ([x
            for x
            in idf1.idfobjects['EnergyManagementSystem:Program']
            if x.Name == 'ApplyAST'])
    assert obj[0].Name == 'ApplyAST'
    assert obj[0].Program_Line_1 == 'Set FORSCRIPT_ACST_Schedule = ACST'
    assert obj[0].Program_Line_2 == 'Set FORSCRIPT_AHST_Schedule = AHST'

def test_addOutputVariablesSingleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addOutputVariablesSingleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    outputvariablelist = ([program.Name
                           for program
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
        'VRF Heat Pump Heating Electricity Energy'
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

    obj = ([x
            for x
            in idf1.idfobjects['Output:Variable']
            if x.Variable_Name == 'Site Outdoor Air Drybulb Temperature'])
    assert obj[0].Key_Value == 'Environment'
    assert obj[0].Variable_Name == 'Site Outdoor Air Drybulb Temperature'
    assert obj[0].Reporting_Frequency == 'Hourly'
    assert obj[0].Schedule_Name == ''

    obj = ([x
            for x
            in idf1.idfobjects['Output:Variable']
            if x.Key_Value == 'FORSCRIPT_AHST'])
    assert obj[0].Key_Value == 'FORSCRIPT_AHST'
    assert obj[0].Variable_Name == 'Schedule Value'
    assert obj[0].Reporting_Frequency == 'Hourly'
    assert obj[0].Schedule_Name == ''

    obj = ([x
            for x
            in idf1.idfobjects['Output:Variable']
            if x.Key_Value == 'FORSCRIPT_ACST'])
    assert obj[0].Key_Value == 'FORSCRIPT_ACST'
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
