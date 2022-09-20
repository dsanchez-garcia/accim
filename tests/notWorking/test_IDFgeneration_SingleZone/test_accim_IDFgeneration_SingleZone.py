import pytest
from accim.sim import accim_Main

def test_genIDFSingleZone():
    pass
    from eppy.modeleditor import IDF
    from os import listdir
    import numpy

    iddfile = 'C:/EnergyPlusV9-5-0/Energy+.idd'
    IDF.setiddname(iddfile)

    z = accim_Main.accimJob(
        filename_temp='TestModel_SingleZone',
        ScriptType='sz',
        EnergyPlus_version='ep95',
        verboseMode=False)

    z.addEMSProgramsSingleZone(verboseMode=False)
    z.saveaccim(verboseMode=False)

    idf1 = IDF('TestModel_SingleZone_pymod.idf')
    SetInputData = (
        [program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetInputData'])

    z.genIDFSingleZone(
        AdapStand=[1, 2],
        CAT=[1, 80],
        ComfMod=[1, 80],
        ASTtol_start=0.1,
        ASTtol_end_input=0.2,
        ASTtol_steps=0.1,
        NameSuffix='whatever',
        verboseMode=False,
        confirmGen=True
    )

    filelist_pymod = ([file for file in listdir() if file.endswith('_pymod.idf')])
    filelist_pymod = ([file.split('.idf')[0] for file in filelist_pymod])
    print(filelist_pymod)

    AdapStand_List = [1]
    CAT_List = [1, 80]
    ComfMod_List = [1, 80]
    ASTtol_value_from = 0.1
    ASTtol_value_to = 0.2
    ASTtol_value_steps = 0.1
    suffix = 'whatever'

    for file in filelist_pymod:
        filename = file
        fname1 = filename + '.idf'
        idf1 = IDF(fname1)
        SetInputData = (
        [program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetInputData'])
        for AdapStand_value in AdapStand_List:
            assert SetInputData[0].Program_Line_1 == 'set ComfStand  =  ' + repr(AdapStand_value)
            if AdapStand_value == 0:
                assert SetInputData[0].Program_Line_2 == 'set CAT = 1'
                assert SetInputData[0].Program_Line_3 == 'set ComfMod = 0'
                for ASTtol_value in numpy.arange(ASTtol_value_from, ASTtol_value_to, ASTtol_value_steps):
                    assert SetInputData[0].Program_Line_4 == 'set ACSTtol = ' + repr(-ASTtol_value)
                    assert SetInputData[0].Program_Line_5 == 'set AHSTtol = ' + repr(ASTtol_value)
                    outputname = (
                            filename
                            + '[AS_CTE'
                            + '[CA_X'
                            + '[CM_X'
                            + '[AT_' + repr(ASTtol_value)
                            + suffix
                            + '.idf'
                    )
                    assert outputname == filename
                    # idf1.savecopy(outputname)
            elif AdapStand_value == 1:
                for CAT_value in CAT_List:
                    if CAT_value not in range(0, 4):
                        continue
                    else:
                        assert SetInputData[0].Program_Line_2 == 'set CAT = ' + repr(CAT_value)
                        for ComfMod_value in ComfMod_List:
                            assert SetInputData[0].Program_Line_3 == 'set ComfMod = ' + repr(ComfMod_value)
                            for ASTtol_value in numpy.arange(ASTtol_value_from, ASTtol_value_to,
                                                             ASTtol_value_steps):
                                assert SetInputData[0].Program_Line_4 == 'set ACSTtol = ' + repr(-ASTtol_value)
                                assert SetInputData[0].Program_Line_5 == 'set AHSTtol = ' + repr(ASTtol_value)
                                outputname = (
                                        filename
                                        + '[AS_EN16798'
                                        + '[CA_' + repr(CAT_value)
                                        + '[CM_' + repr(ComfMod_value)
                                        + '[AT_' + repr(ASTtol_value)
                                        + suffix
                                        + '.idf'
                                )
                                assert outputname == filename
                                # idf1.savecopy(outputname)
            elif AdapStand_value == 2:
                for CAT_value in CAT_List:
                    if CAT_value not in range(80, 91, 10):
                        continue
                    else:
                        assert SetInputData[0].Program_Line_2 == 'set CAT = ' + repr(CAT_value)
                        for ComfMod_value in ComfMod_List:
                            assert SetInputData[0].Program_Line_3 == 'set ComfMod = ' + repr(ComfMod_value)
                            for ASTtol_value in numpy.arange(ASTtol_value_from, ASTtol_value_to,
                                                             ASTtol_value_steps):
                                assert SetInputData[0].Program_Line_4 == 'set ACSTtol = ' + repr(-ASTtol_value)
                                assert SetInputData[0].Program_Line_5 == 'set AHSTtol = ' + repr(ASTtol_value)
                                outputname = (
                                        filename
                                        + '[AS_ASHRAE55'
                                        + '[CA_' + repr(CAT_value)
                                        + '[CM_' + repr(ComfMod_value)
                                        + '[AT_' + repr(ASTtol_value)
                                        + suffix
                                        + '.idf'
                                )
                                assert outputname == filename
                                # idf1.savecopy(outputname)
