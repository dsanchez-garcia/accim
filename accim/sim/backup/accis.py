"""
Run the function below to add the ACCIS.

This function transform fixed setpoint temperature
building energy models into adaptive setpoint temperature energy models
by adding the Adaptive Comfort Control Implementation Script (ACCIS)
"""

def addAccis(
        ScriptType: str = None,
        Outputs: str = None,
        EnergyPlus_version: str = None,
        AdapStand: any = None,
        CAT: any = None,
        ComfMod: any = None,
        HVACmode: any = None,
        VentCtrl: any = None,
        VSToffset: any = [0],
        MinOToffset: any = [50],
        MaxWindSpeed: any = [50],
        ASTtol_start: float = 0.1,
        ASTtol_end_input: float = 0.1,
        ASTtol_steps: float = 0.1,
        NameSuffix: str = '',
        verboseMode: bool = True,
        confirmGen: bool = None):
    """
    Parameters
    :param ScriptType: The default is None.'vrf' for VRFsystem, 'ex_ac' for ExistingHVAC only with full air-conditioning mode, and 'ex_mm' for ExistingHVAC with mixed-mode..
    :param Outputs: The default is None. Can be 'standard', 'simplified' or 'timestep'.
    :param EnergyPlus_version: The default is None. Can be 'ep91', 'ep92', 'ep93', 'ep94', 'ep95' or 'ep96'.
    :param AdapStand: The default is None.
    (0 = CTE; 1 = EN16798-1; 2 = ASHRAE 55; 3 = JPN)
    :param CAT: The default is None.
    (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 90 = 90% ACCEPT)
    :param ComfMod: The default is None.
    (0 = Static; 1 = OUT-CTE; 2 = OUT-SEN16798/SASHRAE55; 3 = OUT-AEN16798/AASHRAE55)
    :param HVACmode: The default is None.
    (0 = Fully Air-conditioned; 1 = Naturally ventilated; 2 = Mixed Mode)
    :param VentCtrl: The default is None.
    (0 = Ventilates above neutral temperature; 1 = Ventilates above upper comfort limit)
    :param VSToffset: The default is 0. Please refer to documentation.
    :param MinOToffset: The default is 50. Please refer to documentation.
    :param MaxWindSpeed: The default is 50. Please refer to documentation.
    :param ASTtol_start: The default is 0.1. Please refer to documentation.
    :param ASTtol_end_input: The default is 0.1. Please refer to documentation.
    :param ASTtol_steps: The default is 0.1. Please refer to documentation.
    :param NameSuffix: The default is '' (an empty string). Please refer to documentation.
    :param verboseMode: True to print the process on screen. Default is True.
    :param confirmGen: True to skip confirmation of output IDF generation. Default is None.

    Exceptions
            DESCRIPTION. EnergyPlus version not supported.
        Only works for versions between EnergyPlus 9.1 (enter ep91) and
        EnergyPlus 9.6 (enter ep96).

    :return:
    Returns nothing. Output IDFs are generated in the source folder, where input IDFs were located.
    """
    import accim.sim.accim_Main as accim_Main
    from os import listdir, remove

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not '[' in file])

    filelist = ([file.split('.idf')[0] for file in filelist])

    objArgsDef = (
        ScriptType is not None,
        Outputs is not None,
        EnergyPlus_version is not None
    )

    fullScriptTypeList = ['vrf',
                          'ex_mm',
                          'ex_ac',
                          ]

    fullOutputsList = [
        'Standard',
        'standard',
        'Simplified',
        'simplified',
        'Timestep',
        'timestep'
    ]

    fullEPversionsList = [
        'Ep91',
        'ep91',
        'Ep92',
        'ep92',
        'Ep93',
        'ep93',
        'Ep94',
        'ep94',
        'Ep95',
        'ep95',
        'Ep96',
        'ep96'
    ]

    if all(objArgsDef):
        pass
    else:
        ScriptType = input("Enter the ScriptType (for VRFsystem: vrf; for ExistingHVAC with mixed mode: ex_mm; or for ExistingHVAC only with full air-conditioning mode: ex_ac): ")
        while ScriptType not in fullScriptTypeList:
            ScriptType = input("ScriptType was not correct. "
                               "Please, enter the ScriptType "
                               "(for VRFsystem: vrf; for ExistingHVAC with mixed mode: ex_mm; or for ExistingHVAC only with full air-conditioning mode: ex_ac): ")
        Outputs = input("Enter the Output (standard, simplified or timestep): ")
        while Outputs not in fullOutputsList:
            Outputs = input("Output was not correct. "
                            "Please, enter the Output (standard, simplified or timestep): ")
        EnergyPlus_version = input("Enter the EnergyPlus version (ep91 to ep96): ")
        while EnergyPlus_version not in fullEPversionsList:
            EnergyPlus_version = input("EnergyPlus version was not correct. "
                                       "Please, enter the EnergyPlus version (ep91 to ep96): ")
    if verboseMode:
        print('ScriptType is: '+ScriptType)
    if ScriptType not in fullScriptTypeList:
        print('Valid ScriptTypes: ')
        print(fullScriptTypeList)
        raise ValueError(ScriptType + " is not a valid ScriptType. "
                                      "You must choose a ScriptType from the list above.")
    if verboseMode:
        print('Outputs are: '+Outputs)
    if Outputs not in fullOutputsList:
        print('Valid Outputs: ')
        print(fullOutputsList)
        raise ValueError(Outputs + " is not a valid Output. "
                                   "You must choose a Output from the list above.")
    if verboseMode:
        print('EnergyPlus version is: '+EnergyPlus_version)
    if EnergyPlus_version not in fullEPversionsList:
        print('Valid EnergyPlus_version: ')
        print(fullEPversionsList)
        raise ValueError(EnergyPlus_version + " is not a valid EnergyPlus_version. "
                                              "You must choose a EnergyPlus_version"
                                              "from the list above.")
    notWorkingIDFs = []

    for file in filelist:
        if verboseMode:
            print('''\n=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================\n''')
            print('Starting with file:')
            print(file)
        z = accim_Main.accimJob(
            filename_temp=file,
            ScriptType=ScriptType,
            EnergyPlus_version=EnergyPlus_version,
            verboseMode=verboseMode
        )

        if z.accimNotWorking is True:
            # raise KeyError(f'accim is not going to work with {file}')
            notWorkingIDFs.append(file)
            continue

        z.setComfFieldsPeople(EnergyPlus_version=EnergyPlus_version, verboseMode=verboseMode)

        if ScriptType.lower() == 'vrf':
            z.addOpTempTherm(verboseMode=verboseMode)
            z.addBaseSchedules(verboseMode=verboseMode)
            z.setAvailSchOn(verboseMode=verboseMode)
            z.addVRFsystemSch(verboseMode=verboseMode)
            z.addCurveObj(verboseMode=verboseMode)
            z.addDetHVACobj(EnergyPlus_version=EnergyPlus_version, verboseMode=verboseMode)
            z.checkVentIsOn(verboseMode=verboseMode)
            z.addForscriptSchVRFsystem(verboseMode=verboseMode)
        elif 'ex' in ScriptType.lower():
            z.addForscriptSchExistHVAC(verboseMode=verboseMode)

        z.addEMSProgramsBase(ScriptType=ScriptType, verboseMode=verboseMode)
        z.addEMSOutputVariableBase(ScriptType=ScriptType, verboseMode=verboseMode)
        z.addGlobVarList(ScriptType=ScriptType, verboseMode=verboseMode)
        z.addIntVarList(verboseMode=verboseMode)
        z.addEMSSensorsBase(ScriptType=ScriptType, verboseMode=verboseMode)
        z.addEMSActuatorsBase(ScriptType=ScriptType, verboseMode=verboseMode)

        if ScriptType.lower() == 'vrf':
            z.addEMSSensorsVRFsystem(verboseMode=verboseMode)
        elif ScriptType.lower() == 'ex_mm':
            z.addEMSSensorsExisHVAC(verboseMode=verboseMode)

        z.addEMSPCMBase(verboseMode=verboseMode)

        if Outputs.lower() == 'simplified':
            z.addSimplifiedOutputVariables(verboseMode=verboseMode)
        elif Outputs.lower() == 'standard':
            z.addOutputVariablesBase(ScriptType=ScriptType, verboseMode=verboseMode)

        if Outputs.lower() == 'timestep':
            z.addOutputVariablesTimestep(verboseMode=verboseMode)

        z.saveaccim(verboseMode=verboseMode)
        if verboseMode:
            print('Ending with file:')
            print(file)
            print('''\n=======================END OF GENERIC IDF FILE GENERATION PROCESS=======================\n''')

    if verboseMode:
        print('The following IDFs will not work, and therefore these will be deleted:')
    if len(notWorkingIDFs) > 0:
        if verboseMode:
            print(*notWorkingIDFs, sep="\n")
        filelist_pymod = ([file for file in listdir() if file.endswith('.idf')
                     and '_pymod' in file])

        for file in notWorkingIDFs:
            for i in filelist_pymod:
                if file in i:
                    remove(i)
    else:
        if verboseMode:
            print('None')

    if verboseMode:
        print('''\n=======================START OF OUTPUT IDF FILES GENERATION PROCESS=======================\n''')

    args_needed_mm = (
        AdapStand is not None,
        CAT is not None,
        ComfMod is not None,
        HVACmode is not None,
        VentCtrl is not None,
    )

    args_needed_ac = (
        AdapStand is not None,
        CAT is not None,
        ComfMod is not None,
    )
    if ScriptType.lower() == 'vrf' or ScriptType.lower() == 'ex_mm':
        if all(args_needed_mm):
            z.genIDF(
                ScriptType=ScriptType,
                AdapStand=AdapStand,
                CAT=CAT,
                ComfMod=ComfMod,
                HVACmode=HVACmode,
                VentCtrl=VentCtrl,
                VSToffset=VSToffset,
                MinOToffset=MinOToffset,
                MaxWindSpeed=MaxWindSpeed,
                ASTtol_start=ASTtol_start,
                ASTtol_end_input=ASTtol_end_input,
                ASTtol_steps=ASTtol_steps,
                NameSuffix=NameSuffix,
                verboseMode=verboseMode,
                confirmGen=confirmGen
                )
        else:
            z.inputData(ScriptType=ScriptType)
            z.genIDF(ScriptType=ScriptType)
    elif ScriptType.lower() == 'ex_ac':
        if all(args_needed_ac):
            z.genIDF(
                ScriptType=ScriptType,
                AdapStand=AdapStand,
                CAT=CAT,
                ComfMod=ComfMod,
                HVACmode=[0],
                VentCtrl=[0],
                VSToffset=[0],
                MinOToffset=[0],
                MaxWindSpeed=[0],
                ASTtol_start=ASTtol_start,
                ASTtol_end_input=ASTtol_end_input,
                ASTtol_steps=ASTtol_steps,
                NameSuffix=NameSuffix,
                verboseMode=verboseMode,
                confirmGen=confirmGen
                )
        else:
            z.inputData(ScriptType=ScriptType)
            z.genIDF(ScriptType=ScriptType)

    if verboseMode:
        print('''\n=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================\n''')