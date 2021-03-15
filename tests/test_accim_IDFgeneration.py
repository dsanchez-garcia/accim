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


def test_inputdataSingleZone():
    from accim.sim import accim_IDFgeneration
    from eppy.modeleditor import IDF

    z = accim_Main.accimInstance.inputdataSingleZone()
    print(z.AdapStand_List)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')
    # todo to be developed

def test_inputdataMultipleZone():
    # todo to be developed
    pass

def test_genIDFSingleZone():
    # todo to be developed
    pass

def test_genIDFMultipleZone():
    # todo to be developed
    pass