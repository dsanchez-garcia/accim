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
    :param ScriptType: The default is 'MultipleZones'. Can be 'MultipleZones'or
        'mz', or 'SingleZone' or 'sz'.
    :param Outputs: The default is 'Standard'. Can be 'Standard',
        'Simplified' or 'Timestep'.
    :param EnergyPlus_version: The default is 'Ep94'. Can be 'Ep91' or 'Ep94'.
    :param AdapStand: The default is None.(0 = CTE; 1 = EN16798-1; 2 = ASHRAE 55)
    :param CAT: The default is None.(1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 90 = 90% ACCEPT)
    :param ComfMod: The default is None.(0 = Static; 1 = OUT-CTE; 2 = OUT-SEN16798/SASHRAE55; 3 = OUT-AEN16798/AASHRAE55)
    :param HVACmode: The default is None.(0 = Fully Air-conditioned; 1 = Naturally ventilated; 2 = Mixed Mode)
    :param VentCtrl: (0 = Ventilates above neutral temperature; 1 = Ventilates above upper comfort limit)
    :param VSToffset: Please refer to documentation.
    :param MinOToffset: Please refer to documentation.
    :param MaxWindSpeed: Please refer to documentation.
    :param ASTtol_start: Please refer to documentation.
    :param ASTtol_end_input: Please refer to documentation.
    :param ASTtol_steps: Please refer to documentation.
    :param NameSuffix: Please refer to documentation.
    :param verboseMode: True to print the process on screen. Default is True.
    :param confirmGen: True to skip confirmation of output IDF generation. Default is None.

    Exceptions
            DESCRIPTION. EnergyPlus version not supported.
        Only works for EnergyPlus 9.1 (enter Ep91) and
        EnergyPlus 9.4 (enter Ep94) versions.

    :return:
    """
    import accim.sim.accim_Main as accim_Main
    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not '_pymod' in file])

    filelist = ([file.split('.idf')[0] for file in filelist])

    objArgsDef = (
        ScriptType is not None,
        Outputs is not None,
        EnergyPlus_version is not None
    )

    fullScriptTypeList = ['MultipleZone',
                          'multiplezone',
                          'mz',
                          'SingleZone',
                          'singlezone',
                          'sz'
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
        'Ep94',
        'ep94'
    ]

    if all(objArgsDef):
        pass
    else:
        ScriptType = input("Enter the ScriptType (MultipleZone or mz, or SingleZone or sz): ")
        while ScriptType not in fullScriptTypeList:
            ScriptType = input("ScriptType was not correct. "
                               "Please, enter the ScriptType "
                               "(MultipleZone or mz, or SingleZone or sz): ")
        Outputs = input("Enter the Output (Standard, Simplified or Timestep): ")
        while Outputs not in fullOutputsList:
            Outputs = input("Output was not correct. "
                            "Please, enter the Output (Standard, Simplified or Timestep): ")
        EnergyPlus_version = input("Enter the EnergyPlus version (Ep91 or Ep94): ")
        while EnergyPlus_version not in fullEPversionsList:
            EnergyPlus_version = input("EnergyPlus version was not correct. "
                                       "Please, enter the EnergyPlus version (Ep91 or Ep94): ")
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

    for file in filelist:
        if verboseMode:
            print('''\n=======================START OF PROCESS=======================\n''')
            print('Starting with file:')
            print(file)
        z = accim_Main.accimJob(filename_temp=file, ScriptType=ScriptType, EnergyPlus_version=EnergyPlus_version, verboseMode=verboseMode)

        z.setComfFieldsPeople(verboseMode=verboseMode)
        z.addOpTempTherm(verboseMode=verboseMode)
        z.addBaseSchedules(verboseMode=verboseMode)
        z.setAvailSchOn(verboseMode=verboseMode)

        if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
            z.addMultipleZoneSch(verboseMode=verboseMode)
            z.addCurveObj(verboseMode=verboseMode)
            if EnergyPlus_version.lower() == 'ep94':
                z.addDetHVACobjEp94(verboseMode=verboseMode)
            elif EnergyPlus_version.lower() == 'ep91':
                z.addDetHVACobjEp91(verboseMode=verboseMode)
            z.checkVentIsOn(verboseMode=verboseMode)
            z.addForscriptSchMultipleZone(verboseMode=verboseMode)
        elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
            z.addForscriptSchSingleZone(verboseMode=verboseMode)

        z.addEMSProgramsBase(verboseMode=verboseMode)
        z.addEMSOutputVariableBase(verboseMode=verboseMode)

        if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
            z.addGlobVarListMultipleZone(verboseMode=verboseMode)
            z.addEMSSensorsMultipleZone(verboseMode=verboseMode)
            z.addEMSActuatorsMultipleZone(verboseMode=verboseMode)
            z.addEMSProgramsMultipleZone(verboseMode=verboseMode)
        elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
            z.addGlobVarListSingleZone(verboseMode=verboseMode)
            z.addEMSSensorsSingleZone(verboseMode=verboseMode)
            z.addEMSActuatorsSingleZone(verboseMode=verboseMode)
            z.addEMSProgramsSingleZone(verboseMode=verboseMode)

        z.addEMSPCMBase(verboseMode=verboseMode)

        if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
            z.addEMSOutputVariableMultipleZone(verboseMode=verboseMode)
            if Outputs.lower() == 'Simplified'.lower():
                z.addSimplifiedOutputVariables(verboseMode=verboseMode)
            elif Outputs.lower() == 'Standard'.lower():
                z.addOutputVariablesMultipleZone(verboseMode=verboseMode)
        elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
            if Outputs.lower() == 'Simplified'.lower():
                z.addSimplifiedOutputVariables(verboseMode=verboseMode)
            elif Outputs.lower() == 'Standard'.lower():
                z.addOutputVariablesSingleZone(verboseMode=verboseMode)
        if Outputs.lower() == 'Timestep'.lower():
            z.addOutputVariablesTimestep(verboseMode=verboseMode)

        z.saveaccim(verboseMode=verboseMode)
        if verboseMode:
            print('Ending with file:')
            print(file)
            print('''\n=======================END OF PROCESS=======================\n''')

    # arguments = (
    #     AdapStand is None,
    #     CAT is None,
    #     ComfMod is None,
    #     HVACmode is None,
    #     VentCtrl is None,
    #     VSToffset == [0],
    #     MinOToffset == [50],
    #     MaxWindSpeed == [50],
    #     ASTtol_start == 0.1,
    #     ASTtol_end_input == 0.1,
    #     ASTtol_steps == 0.1
    #     )

    args_needed_mz = (
        AdapStand is not None,
        CAT is not None,
        ComfMod is not None,
        HVACmode is not None,
        VentCtrl is not None,
    )

    args_needed_sz = (
        AdapStand is not None,
        CAT is not None,
        ComfMod is not None,
    )

    if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
        if all(args_needed_mz):
            z.genIDFMultipleZone(
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
            z.inputdataMultipleZone()
            z.genIDFMultipleZone()
    elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
        if all(args_needed_sz):
            z.genIDFSingleZone(
                AdapStand=AdapStand,
                CAT=CAT,
                ComfMod=ComfMod,
                ASTtol_start=ASTtol_start,
                ASTtol_end_input=ASTtol_end_input,
                ASTtol_steps=ASTtol_steps,
                NameSuffix=NameSuffix,
                verboseMode=verboseMode,
                confirmGen=confirmGen
                )
        else:
            z.inputdataSingleZone()
            z.genIDFSingleZone()
