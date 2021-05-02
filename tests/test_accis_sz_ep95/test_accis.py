from accim.sim import accis

def test_addAccis():
    from accim.sim import accis
    from os import listdir
    scriptTypeList = ['sz']
    outputsList = ['simplified', 'standard', 'timestep']
    EPlist = ['ep95']

    for i in scriptTypeList:
        for j in outputsList:
            for k in EPlist:
                accis.addAccis(
                    ScriptType=i,
                    Outputs=j,
                    EnergyPlus_version=k,
                    AdapStand=[1],
                    CAT=[1],
                    ComfMod=[1],
                    ASTtol_start=0.1,
                    ASTtol_end_input=0.1,
                    ASTtol_steps=0.1,
                    NameSuffix=j,
                    verboseMode=False,
                    confirmGen=True
                )
    expectedNames = [
        'TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_1[AT_0.1[simplified.idf',
        'TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_1[AT_0.1[standard.idf',
        'TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_1[AT_0.1[timestep.idf'
        ]

    actualNames = [i for i in listdir() if i.endswith('.idf') and '_pymod' in i]

    for i in range(len(actualNames)):
        assert actualNames[i] == expectedNames[i]
