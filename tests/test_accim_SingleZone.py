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

def test_addForscriptSchSingleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addForscriptSchSingleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    obj = ([x
            for x
            in idf1.idfobjects['Schedule:Compact']
            if x.Name == "FORSCRIPT_AHST"])
    assert obj[0].Name == "FORSCRIPT_AHST"
    assert obj[0].Schedule_Type_Limits_Name == "Any Number"
    assert obj[0].Field_1 == 'Through: 12/31'
    assert obj[0].Field_2 == 'For: AllDays'
    assert obj[0].Field_3 == 'Until: 24:00'
    assert obj[0].Field_4 == '20'

    obj = ([x
            for x
            in idf1.idfobjects['Schedule:Compact']
            if x.Name == "FORSCRIPT_ACST"])
    assert obj[0].Name == "FORSCRIPT_ACST"
    assert obj[0].Schedule_Type_Limits_Name == "Any Number"
    assert obj[0].Field_1 == 'Through: 12/31'
    assert obj[0].Field_2 == 'For: AllDays'
    assert obj[0].Field_3 == 'Until: 24:00'
    assert obj[0].Field_4 == '24'

    for x in [x for x in idf1.idfobjects['ThermostatSetpoint:DualSetpoint']]:
        assert x.Heating_Setpoint_Temperature_Schedule_Name == "FORSCRIPT_AHST"
        assert x.Cooling_Setpoint_Temperature_Schedule_Name == "FORSCRIPT_ACST"
