"""
Run any of the functions below to add the accis.

These functions transform fixed setpoint temperature
building energy models into adaptive setpoint temperature energy models
by addingthe Adaptive Comfort Control Implementation Script (ACCIS)
"""


def addAccisSingleZoneEp91():
    """Add SingleZone accis."""
    import accim.sim.accim_Main as accim_Main
    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_SingleZone_Ep91(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addForscriptSchSingleZone()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListSingleZone()
        z.addEMSSensorsSingleZone()
        z.addEMSActuatorsSingleZone()
        z.addEMSProgramsSingleZone()
        z.addEMSPCMBase()
        z.addOutputVariablesSingleZone()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataSingleZone()
    z.genIDFSingleZone()


def addAccisSingleZoneEp94():
    """Add SingleZone accis."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_SingleZone_Ep94(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addForscriptSchSingleZone()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListSingleZone()
        z.addEMSSensorsSingleZone()
        z.addEMSActuatorsSingleZone()
        z.addEMSProgramsSingleZone()
        z.addEMSPCMBase()
        z.addOutputVariablesSingleZone()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataSingleZone()
    z.genIDFSingleZone()


def addAccisSingleZoneTimestepEp91():
    """Add SingleZone accis with timestep output data frecuency."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_SingleZone_Ep91(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addForscriptSchSingleZone()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListSingleZone()
        z.addEMSSensorsSingleZone()
        z.addEMSActuatorsSingleZone()
        z.addEMSProgramsSingleZone()
        z.addEMSPCMBase()
        z.addOutputVariablesSingleZone()
        z.addOutputVariablesTimestep()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataSingleZone()
    z.genIDFSingleZone()


def addAccisSingleZoneTimestepEp94():
    """Add SingleZone accis with timestep output data frecuency."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_SingleZone_Ep94(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addForscriptSchSingleZone()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListSingleZone()
        z.addEMSSensorsSingleZone()
        z.addEMSActuatorsSingleZone()
        z.addEMSProgramsSingleZone()
        z.addEMSPCMBase()
        z.addOutputVariablesSingleZone()
        z.addOutputVariablesTimestep()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataSingleZone()
    z.genIDFSingleZone()


def addAccisSingleZoneSimplifiedEp91():
    """Add SingleZone accis with simplified outputs."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_SingleZone_Ep91(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addForscriptSchSingleZone()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListSingleZone()
        z.addEMSSensorsSingleZone()
        z.addEMSActuatorsSingleZone()
        z.addEMSProgramsSingleZone()
        z.addEMSPCMBase()
        z.addSimplifiedOutputVariables()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataSingleZone()
    z.genIDFSingleZone()


def addAccisSingleZoneSimplifiedEp94():
    """Add SingleZone accis with simplified outputs."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_SingleZone_Ep94(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addForscriptSchSingleZone()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListSingleZone()
        z.addEMSSensorsSingleZone()
        z.addEMSActuatorsSingleZone()
        z.addEMSProgramsSingleZone()
        z.addEMSPCMBase()
        z.addSimplifiedOutputVariables()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataSingleZone()
    z.genIDFSingleZone()


def addAccisMultipleZoneEp91():
    """Add MultipleZone accis."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_MultipleZone_Ep91(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addMultipleZoneSch()
        z.addCurveObj()
        z.addDetHVACobjEp91()
        z.addForscriptSchMultipleZone()
        z.checkVentIsOn()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListMultipleZone()
        z.addEMSSensorsMultipleZone()
        z.addEMSActuatorsMultipleZone()
        z.addEMSProgramsMultipleZone()
        z.addEMSPCMBase()
        z.addEMSOutputVariableMultipleZone()
        z.addOutputVariablesMultipleZone()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataMultipleZone()
    z.genIDFMultipleZone()


def addAccisMultipleZoneEp94():
    """Add MultipleZone accis."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_MultipleZone_Ep94(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addMultipleZoneSch()
        z.addCurveObj()
        z.addDetHVACobjEp94()
        z.addForscriptSchMultipleZone()
        z.checkVentIsOn()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListMultipleZone()
        z.addEMSSensorsMultipleZone()
        z.addEMSActuatorsMultipleZone()
        z.addEMSProgramsMultipleZone()
        z.addEMSPCMBase()
        z.addEMSOutputVariableMultipleZone()
        z.addOutputVariablesMultipleZone()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataMultipleZone()
    z.genIDFMultipleZone()


def addAccisMultipleZoneTimestepEp91():
    """Add MultipleZone accis with timestep output data frecuency."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_MultipleZone_Ep91(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addMultipleZoneSch()
        z.addCurveObj()
        z.addDetHVACobjEp91()
        z.addForscriptSchMultipleZone()
        z.checkVentIsOn()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListMultipleZone()
        z.addEMSSensorsMultipleZone()
        z.addEMSActuatorsMultipleZone()
        z.addEMSProgramsMultipleZone()
        z.addEMSPCMBase()
        z.addEMSOutputVariableMultipleZone()
        z.addOutputVariablesMultipleZone()
        z.addOutputVariablesTimestep()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataMultipleZone()
    z.genIDFMultipleZone()


def addAccisMultipleZoneTimestepEp94():
    """Add MultipleZone accis with timestep output data frecuency."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_MultipleZone_Ep94(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addMultipleZoneSch()
        z.addCurveObj()
        z.addDetHVACobjEp94()
        z.addForscriptSchMultipleZone()
        z.checkVentIsOn()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListMultipleZone()
        z.addEMSSensorsMultipleZone()
        z.addEMSActuatorsMultipleZone()
        z.addEMSProgramsMultipleZone()
        z.addEMSPCMBase()
        z.addEMSOutputVariableMultipleZone()
        z.addOutputVariablesMultipleZone()
        z.addOutputVariablesTimestep()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataMultipleZone()
    z.genIDFMultipleZone()


def addAccisMultipleZoneSimplifiedEp91():
    """Add MultipleZone accis with simplified output."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_MultipleZone_Ep91(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addMultipleZoneSch()
        z.addCurveObj()
        z.addDetHVACobjEp91()
        z.addForscriptSchMultipleZone()
        z.checkVentIsOn()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListMultipleZone()
        z.addEMSSensorsMultipleZone()
        z.addEMSActuatorsMultipleZone()
        z.addEMSProgramsMultipleZone()
        z.addEMSPCMBase()
        z.addEMSOutputVariableMultipleZone()
        z.addSimplifiedOutputVariables()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataMultipleZone()
    z.genIDFMultipleZone()


def addAccisMultipleZoneSimplifiedEp94():
    """Add MultipleZone accis with simplified output."""
    import accim.sim.accim_Main as accim_Main

    from os import listdir

    filelist = ([file for file in listdir() if file.endswith('.idf')
                 and not file.endswith('_pymod.idf')])

    filelist = ([file.split('.idf')[0] for file in filelist])

    for file in filelist:
        z = accim_Main.accimobj_MultipleZone_Ep94(file)

        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        z.addMultipleZoneSch()
        z.addCurveObj()
        z.addDetHVACobjEp94()
        z.addForscriptSchMultipleZone()
        z.checkVentIsOn()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        z.addGlobVarListMultipleZone()
        z.addEMSSensorsMultipleZone()
        z.addEMSActuatorsMultipleZone()
        z.addEMSProgramsMultipleZone()
        z.addEMSPCMBase()
        z.addEMSOutputVariableMultipleZone()
        z.addSimplifiedOutputVariables()

        z.saveaccim()

    z = accim_Main.accimobj()
    z.inputdataMultipleZone()
    z.genIDFMultipleZone()


def addAccis(
        ScriptType: str = 'MultipleZones',
        Outputs: str = 'Standard',
        EnergyPlus_version: str ='Ep94',
        AdapStand: any = None,
        CAT: any = None,
        ComfMod: any = None,
        HVACmode: any = None,
        VentCtrl: any = None,
        VSToffset: any = 0,
        MinOToffset: any = 50,
        MaxWindSpeed: any = 50,
        ASTtol_start: float = 0.1,
        ASTtol_end_input: float = 0.1,
        ASTtol_steps: float = 0.1,
        NameSuffix: str = ''
        ):
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

    for file in filelist:
        z = accim_Main.accimInstance(filename_temp=file, ScriptType=ScriptType, EnergyPlus_version=EnergyPlus_version)

        # if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
        #     if EnergyPlus_version.lower() == 'ep94':
        #         z = accim_Main.accimobj_MultipleZone_Ep94(file)
        #     elif EnergyPlus_version.lower() == 'ep91':
        #         z = accim_Main.accimobj_MultipleZone_Ep91(file)
        #     else:
        #         raise ValueError("""EnergyPlus version not supported.\n
        #                          Only works for EnergyPlus 9.1 (enter Ep91) and
        #                          EnergyPlus 9.4 (enter Ep94) versions.""")
        # elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
        #     if EnergyPlus_version.lower() == 'ep94':
        #         z = accim_Main.accimobj_SingleZone_Ep94(file)
        #     elif EnergyPlus_version.lower() == 'ep91':
        #         z = accim_Main.accimobj_SingleZone_Ep91(file)
        #     else:
        #         raise ValueError("""EnergyPlus version not supported.\n
        #                          Only works for EnergyPlus 9.1 (enter Ep91) and
        #                          EnergyPlus 9.4 (enter Ep94) versions.""")


        z.setComfFieldsPeople()
        z.addOpTempTherm()
        z.addBaseSchedules()
        z.setAvailSchOn()

        if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
            z.addMultipleZoneSch()
            z.addCurveObj()
            if EnergyPlus_version.lower() == 'ep94':
                z.addDetHVACobjEp94()
            elif EnergyPlus_version.lower() == 'ep91':
                z.addDetHVACobjEp91()
            z.checkVentIsOn()
            z.addForscriptSchMultipleZone()
        elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
            z.addForscriptSchSingleZone()

        z.addEMSProgramsBase()
        z.addEMSOutputVariableBase()

        if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
            z.addGlobVarListMultipleZone()
            z.addEMSSensorsMultipleZone()
            z.addEMSActuatorsMultipleZone()
            z.addEMSProgramsMultipleZone()
        elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
            z.addGlobVarListSingleZone()
            z.addEMSSensorsSingleZone()
            z.addEMSActuatorsSingleZone()
            z.addEMSProgramsSingleZone()

        z.addEMSPCMBase()

        if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
            z.addEMSOutputVariableMultipleZone()
            if Outputs.lower() == 'Simplified'.lower():
                z.addSimplifiedOutputVariables()
            elif Outputs.lower() == 'Standard'.lower():
                z.addOutputVariablesMultipleZone()
        elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
            if Outputs.lower() == 'Simplified'.lower():
                z.addSimplifiedOutputVariables()
            elif Outputs.lower() == 'Standard'.lower():
                z.addOutputVariablesSingleZone()
        if Outputs.lower() == 'Timestep'.lower():
            z.addOutputVariablesTimestep()

        z.saveaccim()

    z = accim_Main.accimobj()

    arguments = (
        AdapStand is None,
        CAT is None,
        ComfMod is None,
        HVACmode is None,
        VentCtrl is None,
        VSToffset == 0,
        MinOToffset == 50,
        MaxWindSpeed == 50,
        ASTtol_start == 0.1,
        ASTtol_end_input == 0.1,
        ASTtol_steps == 0.1
        )

    if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
        if all(arguments):
            z.inputdataMultipleZone()
            z.genIDFMultipleZone()
        else:
            z.genIDFMultipleZone(
                AdapStand,
                CAT,
                ComfMod,
                HVACmode,
                VentCtrl,
                VSToffset,
                MinOToffset,
                MaxWindSpeed,
                ASTtol_start,
                ASTtol_end_input,
                ASTtol_steps,
                NameSuffix
                )
    elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
        if all(arguments):
            z.inputdataSingleZone()
            z.genIDFSingleZone()
        else:
            z.genIDFSingleZone(
                AdapStand,
                CAT,
                ComfMod,
                ASTtol_start,
                ASTtol_end_input,
                ASTtol_steps,
                NameSuffix
                )
