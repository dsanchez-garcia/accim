from accim.sim import accis

def test_addAccis():
    from accim.sim import accis
    from os import listdir
    scriptTypeList = ['ex_mm', 'ex_ac']
    outputsList = ['simplified', 'standard', 'timestep']
    EPlist = ['ep95']

    for i in scriptTypeList:
        for j in outputsList:
            for k in EPlist:
                accis.addAccis(
                    ScriptType=i,
                    Output_type=j,
                    EnergyPlus_version=k,
                    ComfStand=[1],
                    CAT=[1],
                    ComfMod=[1],
                    HVACmode=[2],
                    VentCtrl=[0],
                    VSToffset=[0],
                    MinOToffset=[50],
                    MaxWindSpeed=[50],
                    ASTtol_start=0.1,
                    ASTtol_end_input=0.1,
                    ASTtol_steps=0.1,
                    NameSuffix=i+'_'+j,
                    verboseMode=False,
                    confirmGen=True
                )
    expectedNames = [
        'TestModel_ExistingHVAC_PTAC_pymod[AS_EN16798[CA_1[CM_1[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[ex_ac_simplified.idf',
        'TestModel_ExistingHVAC_PTAC_pymod[AS_EN16798[CA_1[CM_1[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[ex_ac_standard.idf',
        'TestModel_ExistingHVAC_PTAC_pymod[AS_EN16798[CA_1[CM_1[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[ex_ac_timestep.idf',
        'TestModel_ExistingHVAC_PTAC_pymod[AS_EN16798[CA_1[CM_1[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[ex_mm_simplified.idf',
        'TestModel_ExistingHVAC_PTAC_pymod[AS_EN16798[CA_1[CM_1[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[ex_mm_standard.idf',
        'TestModel_ExistingHVAC_PTAC_pymod[AS_EN16798[CA_1[CM_1[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[ex_mm_timestep.idf',
    ]

    actualNames = [i for i in listdir() if i.endswith('.idf') and '_pymod' in i]

    for i in range(len(actualNames)):
        assert actualNames[i] == expectedNames[i]
