import pytest
from accim.sim import accim_Main

@pytest.fixture()
def IDFobject():
    from eppy.modeleditor import IDF

    iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
    IDF.setiddname(iddfile)

    z = accim_Main.accimInstance(
        filename_temp='TestModel_SingleZone',
        ScriptType='sz',
        EnergyPlus_version='ep94',
        verboseMode=False)
    return z

def test_setComfFieldsPeople(IDFobject):
    from eppy.modeleditor import IDF
    
    IDFobject.setComfFieldsPeople(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    peoplelist = ([people for people in idf1.idfobjects['PEOPLE']])
    for i in range(len(peoplelist)):
        assert peoplelist[i].Name == peoplelist[i].Name
        assert peoplelist[i].Zone_or_ZoneList_Name == peoplelist[i].Zone_or_ZoneList_Name
        assert peoplelist[i].Number_of_People_Schedule_Name == peoplelist[i].Number_of_People_Schedule_Name
        assert peoplelist[i].Number_of_People_Calculation_Method == peoplelist[i].Number_of_People_Calculation_Method
        assert peoplelist[i].Number_of_People == peoplelist[i].Number_of_People
        assert peoplelist[i].People_per_Zone_Floor_Area == peoplelist[i].People_per_Zone_Floor_Area
        assert peoplelist[i].Zone_Floor_Area_per_Person == peoplelist[i].Zone_Floor_Area_per_Person
        assert peoplelist[i].Fraction_Radiant == peoplelist[i].Fraction_Radiant
        assert peoplelist[i].Sensible_Heat_Fraction == peoplelist[i].Sensible_Heat_Fraction
        assert peoplelist[i].Activity_Level_Schedule_Name == peoplelist[i].Activity_Level_Schedule_Name
        assert peoplelist[i].Carbon_Dioxide_Generation_Rate == peoplelist[i].Carbon_Dioxide_Generation_Rate
        assert peoplelist[i].Enable_ASHRAE_55_Comfort_Warnings == peoplelist[i].Enable_ASHRAE_55_Comfort_Warnings
        assert peoplelist[i].Mean_Radiant_Temperature_Calculation_Type == peoplelist[i].Mean_Radiant_Temperature_Calculation_Type
        assert peoplelist[i].Surface_NameAngle_Factor_List_Name == peoplelist[i].Surface_NameAngle_Factor_List_Name
        assert peoplelist[i].Work_Efficiency_Schedule_Name == peoplelist[i].Work_Efficiency_Schedule_Name
        assert peoplelist[i].Clothing_Insulation_Calculation_Method == peoplelist[i].Clothing_Insulation_Calculation_Method
        assert peoplelist[i].Clothing_Insulation_Calculation_Method_Schedule_Name == peoplelist[i].Clothing_Insulation_Calculation_Method_Schedule_Name
        assert peoplelist[i].Clothing_Insulation_Schedule_Name == peoplelist[i].Clothing_Insulation_Schedule_Name
        assert peoplelist[i].Air_Velocity_Schedule_Name == peoplelist[i].Air_Velocity_Schedule_Name
        assert peoplelist[i].Thermal_Comfort_Model_1_Type == 'AdaptiveASH55'
        assert peoplelist[i].Thermal_Comfort_Model_2_Type == 'AdaptiveCEN15251'
        assert peoplelist[i].Thermal_Comfort_Model_3_Type == ''
        assert peoplelist[i].Thermal_Comfort_Model_4_Type == ''
        assert peoplelist[i].Thermal_Comfort_Model_5_Type == ''


def test_addOpTempTherm(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addOpTempTherm(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    zonenames_orig = ([zone.Name for zone in idf1.idfobjects['ZONE']])
    for zonename_orig in zonenames_orig:
        ZoneControl = ([x
                        for x
                        in idf1.idfobjects['ZoneControl:Thermostat:OperativeTemperature']
                        if x.Thermostat_Name == zonename_orig+" Thermostat"])
        assert ZoneControl[0].Thermostat_Name == zonename_orig + " Thermostat"
        assert ZoneControl[0].Radiative_Fraction_Input_Mode == "Scheduled"
        assert ZoneControl[0].Fixed_Radiative_Fraction == ''
        assert ZoneControl[0].Radiative_Fraction_Schedule_Name == 'TypOperativeTempControlSch'


def test_addBaseSchedules(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addBaseSchedules(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    sch = ([x
            for x
            in idf1.idfobjects['Schedule:Compact']
            if x.Name == 'On'])
    assert sch[0].Name == "On"
    assert sch[0].Schedule_Type_Limits_Name == "Any Number"
    assert sch[0].Field_1 == 'Through: 12/31'
    assert sch[0].Field_2 == 'For: AllDays'
    assert sch[0].Field_3 == 'Until: 24:00'
    assert sch[0].Field_4 == '1'


def test_setAvailSchOn(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.setAvailSchOn(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    for schedule in [i for i in idf1.idfobjects['ZoneHVAC:IdealLoadsAirSystem']]:
        assert schedule.Heating_Availability_Schedule_Name == 'On'
        assert schedule.Cooling_Availability_Schedule_Name == 'On'
