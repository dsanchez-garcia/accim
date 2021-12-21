import pytest
from accim.sim import accim_Main

def test_genIDFMultipleZone():
    pass
    from eppy.modeleditor import IDF
    from os import listdir
    import numpy

    iddfile = 'C:/EnergyPlusV9-5-0/Energy+.idd'
    IDF.setiddname(iddfile)

    z = accim_Main.accimJob(
        filename_temp='TestModel_MultipleZone',
        ScriptType='mz',
        EnergyPlus_version='ep95',
        verboseMode=False)

    z.addEMSProgramsMultipleZone(verboseMode=False)
    z.saveaccim(verboseMode=False)

    idf1 = IDF('TestModel_MultipleZone_pymod.idf')
    SetInputData = (
        [program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetInputData'])

    z.genIDFMultipleZone(
        AdapStand=[1, 2],
        CAT=[1, 80],
        ComfMod=[1, 2],
        HVACmode=[0, 2],
        VentCtrl=[0, 1],
        VSToffset=[0, 1],
        MinOToffset=[5, 10],
        MaxWindSpeed=[5, 10],
        ASTtol_start=0.1,
        ASTtol_end_input=0.2,
        ASTtol_steps=0.1,
        NameSuffix='whatever',
        verboseMode=False,
        confirmGen=True)

    filelist_pymod = ([file for file in listdir() if file.endswith('_pymod.idf')])
    filelist_pymod = ([file.split('.idf')[0] for file in filelist_pymod])
    print(filelist_pymod)

    AdapStand_List = [1, 2]
    CAT_List = [1, 80]
    ComfMod_List = [1, 80]
    HVACmode_List = [0, 2]
    VentCtrl_List = [0, 1]
    VSToffset_List = [0, 1]
    MinOToffset_List = [5, 10]
    MaxWindSpeed_List = [5, 10]
    ASTtol_value_from = 0.1
    ASTtol_value_to = 0.2
    ASTtol_value_steps = 0.1
    suffix = 'whatever'

    for file in filelist_pymod:
        filename = file

        fname1 = filename + '.idf'
        idf1 = IDF(fname1)

        # print(filename)

        SetInputData = (
        [program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetInputData'])

        for AdapStand_value in AdapStand_List:
            assert SetInputData[0].Program_Line_1 == 'set AdapStand = ' + repr(AdapStand_value)
            if AdapStand_value == 0:
                assert SetInputData[0].Program_Line_2 == 'set CAT = 1'
                assert SetInputData[0].Program_Line_3 == 'set ComfMod = 0'
                for HVACmode_value in HVACmode_List:
                    assert SetInputData[0].Program_Line_4 == 'set HVACmode = ' + repr(HVACmode_value)
                    if HVACmode_value == 0:
                        for ASTtol_value in numpy.arange(ASTtol_value_from, ASTtol_value_to,
                                                         ASTtol_value_steps):
                            assert SetInputData[0].Program_Line_5 == 'set ACSTtol = ' + repr(-ASTtol_value)
                            assert SetInputData[0].Program_Line_6 == 'set AHSTtol = ' + repr(ASTtol_value)
                            outputname = (
                                    filename
                                    + '[AS_CTE'
                                    + '[CA_X'
                                    + '[CM_X'
                                    + '[HM_' + repr(HVACmode_value)
                                    + '[VC_X'
                                    + '[VO_X'
                                    + '[MT_X'
                                    + '[MW_X'
                                    + '[AT_' + repr(ASTtol_value)
                                    + suffix
                                    + '.idf'
                            )
                            assert outputname == filename
                    else:
                        for VentCtrl_value in VentCtrl_List:
                            assert SetInputData[0].Program_Line_5 == 'set VentCtrl = ' + repr(VentCtrl_value)
                            for VSToffset_value in VSToffset_List:
                                assert SetInputData[0].Program_Line_6 == 'set VSToffset = ' + repr(VSToffset_value)
                                for MinOToffset_value in MinOToffset_List:
                                    assert SetInputData[0].Program_Line_7 == 'set MinOToffset = ' + repr(MinOToffset_value)
                                    for MaxWindSpeed_value in MaxWindSpeed_List:
                                        assert SetInputData[0].Program_Line_8 == 'set MaxWindSpeed = ' + repr(
                                            MaxWindSpeed_value)
                                        for ASTtol_value in numpy.arange(ASTtol_value_from, ASTtol_value_to,
                                                                         ASTtol_value_steps):
                                            assert SetInputData[0].Program_Line_9 == 'set ACSTtol = ' + repr(-ASTtol_value)
                                            assert SetInputData[0].Program_Line_10 == 'set AHSTtol = ' + repr(ASTtol_value)
                                            outputname = (
                                                    filename
                                                    + '[AS_CTE'
                                                    + '[CA_X'
                                                    + '[CM_X'
                                                    + '[HM_' + repr(HVACmode_value)
                                                    + '[VC_' + repr(VentCtrl_value)
                                                    + '[VO_' + repr(VSToffset_value)
                                                    + '[MT_' + repr(MinOToffset_value)
                                                    + '[MW_' + repr(MaxWindSpeed_value)
                                                    + '[AT_' + repr(ASTtol_value)
                                                    + suffix
                                                    + '.idf'
                                            )
                                            assert outputname == filename
            elif AdapStand_value == 1:
                for CAT_value in CAT_List:
                    if CAT_value not in range(0, 4):
                        continue
                    else:
                        assert SetInputData[0].Program_Line_2 == 'set CAT = ' + repr(CAT_value)
                        for ComfMod_value in ComfMod_List:
                            assert SetInputData[0].Program_Line_3 == 'set ComfMod = ' + repr(ComfMod_value)
                            for HVACmode_value in HVACmode_List:
                                assert SetInputData[0].Program_Line_4 == 'set HVACmode = ' + repr(HVACmode_value)
                                if HVACmode_value == 0:
                                    for ASTtol_value in numpy.arange(ASTtol_value_from, ASTtol_value_to,
                                                                     ASTtol_value_steps):
                                        assert SetInputData[0].Program_Line_9 == 'set ACSTtol = ' + repr(-ASTtol_value)
                                        assert SetInputData[0].Program_Line_10 == 'set AHSTtol = ' + repr(ASTtol_value)
                                        outputname = (
                                                filename
                                                + '[AS_EN16798'
                                                + '[CA_' + repr(CAT_value)
                                                + '[CM_' + repr(ComfMod_value)
                                                + '[HM_' + repr(HVACmode_value)
                                                + '[VC_X'
                                                + '[VO_X'
                                                + '[MT_X'
                                                + '[MW_X'
                                                + '[AT_' + repr(ASTtol_value)
                                                + suffix
                                                + '.idf'
                                        )
                                        assert outputname == filename
                                else:
                                    for VentCtrl_value in VentCtrl_List:
                                        assert SetInputData[0].Program_Line_5 == 'set VentCtrl = ' + repr(VentCtrl_value)
                                        for VSToffset_value in VSToffset_List:
                                            assert SetInputData[0].Program_Line_6 == 'set VSToffset = ' + repr(VSToffset_value)
                                            for MinOToffset_value in MinOToffset_List:
                                                assert SetInputData[0].Program_Line_7 == 'set MinOToffset = ' + repr(
                                                    MinOToffset_value)
                                                for MaxWindSpeed_value in MaxWindSpeed_List:
                                                    assert SetInputData[0].Program_Line_8 == 'set MaxWindSpeed = ' + repr(
                                                        MaxWindSpeed_value)
                                                    for ASTtol_value in numpy.arange(ASTtol_value_from,
                                                                                     ASTtol_value_to,
                                                                                     ASTtol_value_steps):
                                                        assert SetInputData[0].Program_Line_9 == 'set ACSTtol = ' + repr(
                                                            -ASTtol_value)
                                                        assert SetInputData[0].Program_Line_10 == 'set AHSTtol = ' + repr(
                                                            ASTtol_value)
                                                        outputname = (
                                                                filename
                                                                + '[AS_EN16798'
                                                                + '[CA_' + repr(CAT_value)
                                                                + '[CM_' + repr(ComfMod_value)
                                                                + '[HM_' + repr(HVACmode_value)
                                                                + '[VC_' + repr(VentCtrl_value)
                                                                + '[VO_' + repr(VSToffset_value)
                                                                + '[MT_' + repr(MinOToffset_value)
                                                                + '[MW_' + repr(MaxWindSpeed_value)
                                                                + '[AT_' + repr(ASTtol_value)
                                                                + suffix
                                                                + '.idf'
                                                        )
                                                        assert outputname == filename
            elif AdapStand_value == 2:
                for CAT_value in CAT_List:
                    if CAT_value not in range(80, 91, 10):
                        continue
                    else:
                        assert SetInputData[0].Program_Line_2 == 'set CAT = ' + repr(CAT_value)
                        for ComfMod_value in ComfMod_List:
                            assert SetInputData[0].Program_Line_3 == 'set ComfMod = ' + repr(ComfMod_value)
                            for HVACmode_value in HVACmode_List:
                                assert SetInputData[0].Program_Line_4 == 'set HVACmode = ' + repr(HVACmode_value)
                                if HVACmode_value == 0:
                                    for ASTtol_value in numpy.arange(ASTtol_value_from, ASTtol_value_to,
                                                                     ASTtol_value_steps):
                                        assert SetInputData[0].Program_Line_9 == 'set ACSTtol = ' + repr(-ASTtol_value)
                                        assert SetInputData[0].Program_Line_10 == 'set AHSTtol = ' + repr(ASTtol_value)
                                        outputname = (
                                                filename
                                                + '[AS_EN16798'
                                                + '[CA_' + repr(CAT_value)
                                                + '[CM_' + repr(ComfMod_value)
                                                + '[HM_' + repr(HVACmode_value)
                                                + '[VC_X'
                                                + '[VO_X'
                                                + '[MT_X'
                                                + '[MW_X'
                                                + '[AT_' + repr(ASTtol_value)
                                                + suffix
                                                + '.idf'
                                        )
                                        assert outputname == filename
                                else:
                                    for VentCtrl_value in VentCtrl_List:
                                        assert SetInputData[0].Program_Line_5 == 'set VentCtrl = ' + repr(VentCtrl_value)
                                        for VSToffset_value in VSToffset_List:
                                            assert SetInputData[0].Program_Line_6 == 'set VSToffset = ' + repr(VSToffset_value)
                                            for MinOToffset_value in MinOToffset_List:
                                                assert SetInputData[0].Program_Line_7 == 'set MinOToffset = ' + repr(
                                                    MinOToffset_value)
                                                for MaxWindSpeed_value in MaxWindSpeed_List:
                                                    assert SetInputData[0].Program_Line_8 == 'set MaxWindSpeed = ' + repr(
                                                        MaxWindSpeed_value)
                                                    for ASTtol_value in numpy.arange(ASTtol_value_from,
                                                                                     ASTtol_value_to,
                                                                                     ASTtol_value_steps):
                                                        assert SetInputData[0].Program_Line_9 == 'set ACSTtol = ' + repr(
                                                            -ASTtol_value)
                                                        assert SetInputData[0].Program_Line_10 == 'set AHSTtol = ' + repr(
                                                            ASTtol_value)
                                                        outputname = (
                                                                filename
                                                                + '[AS_ASHRAE55'
                                                                + '[CA_' + repr(CAT_value)
                                                                + '[CM_' + repr(ComfMod_value)
                                                                + '[HM_' + repr(HVACmode_value)
                                                                + '[VC_' + repr(VentCtrl_value)
                                                                + '[VO_' + repr(VSToffset_value)
                                                                + '[MT_' + repr(MinOToffset_value)
                                                                + '[MW_' + repr(MaxWindSpeed_value)
                                                                + '[AT_' + repr(ASTtol_value)
                                                                + suffix
                                                                + '.idf'
                                                        )
                                                        assert outputname == filename