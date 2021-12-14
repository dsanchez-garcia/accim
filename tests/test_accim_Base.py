import pytest
from accim.sim import accim_Main

@pytest.fixture()
def IDFobject():
    from eppy.modeleditor import IDF

    iddfile = 'C:/EnergyPlusV9-5-0/Energy+.idd'
    IDF.setiddname(iddfile)

    z = accim_Main.accimJob(
        filename_temp='TestModel_SingleZone',
        ScriptType='sz',
        EnergyPlus_version='ep95',
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


