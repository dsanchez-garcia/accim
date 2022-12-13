"""
Run the function below to add the ACCIS.

This function transform fixed setpoint temperature
building energy models into adaptive setpoint temperature energy models
by adding the Adaptive Comfort Control Implementation Script (ACCIS)
"""

def addAccis(
        ScriptType: str = None,
        Output_type: str = None,
        # todo
        Output_freqs: any = None,
        Outputs_keep_existing: bool = None,
        EnergyPlus_version: str = None,
        TempCtrl: str = None,
        ComfStand: any = None,
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
    :param ScriptType: The default is None.
    'vrf_ac' for VRFsystem with full air-conditionin mode, 
    'vrf_mm' for VRFsystem with mixed-mode, 
    'ex_ac' for ExistingHVAC only with full air-conditioning mode, 
    'ex_mm' for ExistingHVAC with mixed-mode.
    :param Output_type: The default is None. Can be 'standard', 'simplified' or 'timestep'.
    :param EnergyPlus_version: The default is None. Can be '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1' or '22.2'.
    :param TempCtrl: The default is None. Can be 'temp' or 'pmv'.
    :param ComfStand: The default is None.
        '0 = ESP CTE;
        '1 = INT EN16798;
        '2 = INT ASHRAE55;
        '3 = JPN Rijal;
        '4 = CHN GBT50785 Cold;
        '5 = CHN GBT50785 HotMild;
        '6 = CHN Yang;
        '7 = IND IMAC C NV;
        '8 = IND IMAC C MM;
        '9 = IND IMAC R 7DRM;
        '10 = IND IMAC R 30DRM;
        '11 = IND Dhaka;
        '12 = ROM Udrea;
        '13 = AUS Williamson;
        '14 = AUS DeDear;
        '15 = BRA Rupp NV;
        '16 = BRA Rupp AC;
        '17 = MEX Oropeza Arid;
        '18 = MEX Oropeza DryTropic;
        '19 = MEX Oropeza Temperate;
        '20 = MEX Oropeza HumTropic;
    :param CAT: The default is None.
    (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 85 = 85% ACCEPT; 90 = 90% ACCEPT)
    :param ComfMod: The default is None.
    (0 = Static;
    1 = Adaptive when applicable, otherwise relevant local static model;
    2 = Adaptive when applicable, otherwise relevant international static model
    3 = Adaptive when applicable, otherwise horizontal extention of adaptive setpoints)
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
        Only works for versions between EnergyPlus 9.1 (enter 9.1) and
        EnergyPlus 22.2 (enter 22.2).

    :return:
    Returns nothing. Output IDFs are generated in the source folder, where input IDFs were located.
    """
    import accim.sim.accim_Main as accim_Main
    from os import listdir, remove
    import accim

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not '[' in file])

    filelist = ([file.split('.idf')[0] for file in filelist])

    objArgsDef = (
        ScriptType is not None,
        Output_type is not None,
        Output_freqs is not None,
        Outputs_keep_existing is not None,
        EnergyPlus_version is not None,
        TempCtrl is not None,
    )

    fullScriptTypeList = ['vrf_ac',
                          'vrf_mm',
                          'ex_mm',
                          'ex_ac',
                          ]

    fullOutputsTypeList = [
        'Standard',
        'standard',
        'Simplified',
        'simplified',
        'Existing',
        'existing',

        'Timestep',
        'timestep',
        'Runperiod',
        'runperiod'
    ]

    fullOutputsFreqList = [
        'Timestep',
        'timestep',
        'Hourly',
        'hourly',
        'Daily',
        'daily',
        'Monthly',
        'monthly',
        'Runperiod',
        'runperiod'
    ]

    fullEPversionsList = [
        '9.1',
        '9.2',
        '9.3',
        '9.4',
        '9.5',
        '9.6',
        '22.1',
        '22.2'
    ]

    fullTempCtrllist = [
        'temperature',
        'temp',
        'pmv'
    ]

    if all(objArgsDef):
        pass
    else:
        ScriptType = input("Enter the ScriptType (\n"
                           "for VRFsystem with full air-conditioning mode: vrf_ac;\n"
                           "for VRFsystem with mixed-mode: vrf_mm;\n"
                           "for ExistingHVAC with mixed mode: ex_mm;\n"
                           "for ExistingHVAC with full air-conditioning mode: ex_ac\n"
                           "): ")
        while ScriptType not in fullScriptTypeList:
            ScriptType = input("    ScriptType was not correct. "
                               "    Enter the ScriptType (\n"
                               "    for VRFsystem with full air-conditioning mode: vrf_ac;\n"
                               "    for VRFsystem with mixed-mode: vrf_mm;\n"
                               "    for ExistingHVAC with mixed mode: ex_mm;\n"
                               "    for ExistingHVAC with full air-conditioning mode: ex_ac\n"
                               "    ): ")
        Outputs_keep_existing = input('Do you want to keep the existing outputs (true or false)?: ')
        while Outputs_keep_existing.lower() not in ['true', 'false']:
            Outputs_keep_existing = input('The answer you entered is not valid. '
                                          'Do you want to keep the existing outputs (true or false)?: ')
        Output_type = input("Enter the Output type (standard, simplified or existing): ")
        while Output_type not in fullOutputsTypeList:
            Output_type = input("   Output type was not correct. "
                            "Please, enter the Output type (standard, simplified or existing): ")
        Output_freqs = list(freq for freq in input(
            "Enter the Output frequencies separated by space (timestep, hourly, daily, monthly, runperiod): ").split())
        while (not(all(elem in fullOutputsFreqList for elem in Output_freqs))):
            Output_freqs = list(freq for freq in input(
                "Some of the Output frequencies are not correct. "
                "Please, enter the Output frequencies again separated by space "
                "(timestep, hourly, daily, monthly, runperiod): ").split())
        EnergyPlus_version = input("Enter the EnergyPlus version (9.1 to 22.2): ")
        while EnergyPlus_version not in fullEPversionsList:
            EnergyPlus_version = input("    EnergyPlus version was not correct. "
                                       "Please, enter the EnergyPlus version (9.1 to 22.2): ")
        TempCtrl = input('Enter the Temperature Control method (temperature or pmv): ')
        while TempCtrl not in fullTempCtrllist:
            TempCtrl = input("  Temperature Control method was not correct. "
                             "Please, enter the Temperature Control method (temperature or pmv): ")


    if verboseMode:
        print('Basic input data:')
        # print(f'accim version: {accim.__version__}')
        print('ScriptType is: '+ScriptType)
    if ScriptType not in fullScriptTypeList:
        print('Valid ScriptTypes: ')
        print(fullScriptTypeList)
        raise ValueError(ScriptType + " is not a valid ScriptType. "
                                      "You must choose a ScriptType from the list above.")
    if verboseMode:
        print('Output type is: ' + Output_type)
    if Output_type not in fullOutputsTypeList:
        print('Valid Output type: ')
        print(fullOutputsTypeList)
        raise ValueError(Output_type + " is not a valid Output. "
                                   "You must choose a Output from the list above.")
    if verboseMode:
        print('Output frequencies are: ')
        print(Output_freqs)
    if not (all(elem in fullOutputsFreqList for elem in Output_freqs)):
        print('Valid Output freqs: ')
        print(fullOutputsFreqList)
        raise ValueError('Some of the Output frequencies in '+Output_freqs + " is not a valid Output. "
                                   "All Output frequencies must be included in the list above.")
    if verboseMode:
        print('EnergyPlus version is: '+EnergyPlus_version)
    if EnergyPlus_version not in fullEPversionsList:
        print('Valid EnergyPlus_version: ')
        print(fullEPversionsList)
        raise ValueError(EnergyPlus_version + " is not a valid EnergyPlus_version. "
                                              "You must choose a EnergyPlus_version"
                                              "from the list above.")
    if verboseMode:
        print('Temperature Control method is: '+TempCtrl)
    if TempCtrl not in fullTempCtrllist:
        print('Valid Temperature Control methods: ')
        print(fullTempCtrllist)
        raise ValueError(TempCtrl + " is not a valid Temperature Control method. "
                                              "You must choose a Temperature Control method"
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
            TempCtrl=TempCtrl,
            verboseMode=verboseMode
        )

        if z.accimNotWorking is True:
            # raise KeyError(f'accim is not going to work with {file}')
            notWorkingIDFs.append(file)
            continue

        z.setComfFieldsPeople(EnergyPlus_version=EnergyPlus_version, TempCtrl=TempCtrl, verboseMode=verboseMode)

        if 'vrf' in ScriptType.lower():
            if TempCtrl.lower() == 'temperature' or TempCtrl.lower() == 'temp':
                z.addOpTempTherm(verboseMode=verboseMode)
            elif TempCtrl.lower() == 'pmv':
                z.setPMVsetpoint(verboseMode=verboseMode)
            z.addBaseSchedules(verboseMode=verboseMode)
            z.setAvailSchOn(verboseMode=verboseMode)
            z.addVRFsystemSch(verboseMode=verboseMode)
            z.addCurveObj(verboseMode=verboseMode)
            z.addDetHVACobj(EnergyPlus_version=EnergyPlus_version, verboseMode=verboseMode, TempCtrl=TempCtrl)
            if ScriptType.lower() == 'vrf_mm':
                z.checkVentIsOn(verboseMode=verboseMode)
            z.addForscriptSchVRFsystem(verboseMode=verboseMode)
        elif 'ex' in ScriptType.lower():
            # todo check if PMV can work with ex_ac
            z.addForscriptSchExistHVAC(verboseMode=verboseMode)

        z.addEMSProgramsBase(ScriptType=ScriptType, verboseMode=verboseMode)
        z.addEMSOutputVariableBase(ScriptType=ScriptType, verboseMode=verboseMode)
        z.addGlobVarList(ScriptType=ScriptType, verboseMode=verboseMode)
        z.addIntVarList(verboseMode=verboseMode)
        z.addEMSSensorsBase(ScriptType=ScriptType, verboseMode=verboseMode)
        z.addEMSActuatorsBase(ScriptType=ScriptType, verboseMode=verboseMode)

        if 'vrf' in ScriptType.lower():
            z.addEMSSensorsVRFsystem(ScriptType=ScriptType, verboseMode=verboseMode)
        elif ScriptType.lower() == 'ex_mm':
            z.addEMSSensorsExisHVAC(verboseMode=verboseMode)

        z.addEMSPCMBase(verboseMode=verboseMode)
        #todo continue here
        if Outputs_keep_existing == 'true':
            Outputs_keep_existing = True
        elif Outputs_keep_existing == 'false':
            Outputs_keep_existing = False
        if Outputs_keep_existing is True:
            pass
        else:
            z.removeExistingOutputVariables()

        if Output_type.lower() == 'simplified':
            z.addOutputVariablesSimplified(
                Output_freqs=Output_freqs,
                TempCtrl=TempCtrl,
                verboseMode=verboseMode
            )
        elif Output_type.lower() == 'standard':
            z.addOutputVariablesStandard(
                Outputs_freq=Output_freqs,
                ScriptType=ScriptType,
                TempCtrl=TempCtrl,
                verboseMode=verboseMode
            )

        # if Output_type.lower() == 'simplified':
        #     z.addSimplifiedOutputVariables(
        #         TempCtrl=TempCtrl,
        #         verboseMode=verboseMode
        #     )
        # elif Output_type.lower() == 'standard':
        #     z.addOutputVariablesBase(
        #         ScriptType=ScriptType,
        #         TempCtrl=TempCtrl,
        #         verboseMode=verboseMode
        #     )
        #
        # if Output_type.lower() == 'timestep':
        #     z.addOutputVariablesTimestep(verboseMode=verboseMode)
        #
        # if Output_type.lower() == 'runperiod':
        #     z.addOutputVariablesRunperiod(
        #         ScriptType=ScriptType,
        #         verboseMode=verboseMode
        #     )

        z.removeDuplicatedOutputVariables()

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
        ComfStand is not None,
        CAT is not None,
        ComfMod is not None,
        HVACmode is not None,
        VentCtrl is not None,
    )

    args_needed_ac = (
        ComfStand is not None,
        CAT is not None,
        ComfMod is not None,
    )
    if ScriptType.lower() == 'vrf_mm' or ScriptType.lower() == 'ex_mm':
        if all(args_needed_mm):
            z.genIDF(
                ScriptType=ScriptType,
                TempCtrl=TempCtrl,
                ComfStand=ComfStand,
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
            z.inputData(
                ScriptType=ScriptType,
            )
            z.genIDF(
                ScriptType=ScriptType,
                TempCtrl=TempCtrl,
            )
    elif ScriptType.lower() == 'ex_ac' or ScriptType.lower() == 'vrf_ac':
        if all(args_needed_ac):
            z.genIDF(
                ScriptType=ScriptType,
                TempCtrl=TempCtrl,
                ComfStand=ComfStand,
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
            z.inputData(
                ScriptType=ScriptType,
            )
            z.genIDF(
                ScriptType=ScriptType,
                TempCtrl=TempCtrl,
            )

    if verboseMode:
        print('''\n=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================\n''')
