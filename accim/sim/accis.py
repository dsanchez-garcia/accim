"""
Run any of the functions below to add the accis.

These functions transform fixed setpoint temperature
building energy models into adaptive setpoint temperature energy models
by addingthe Adaptive Comfort Control Implementation Script (ACCIS)
"""


def addAccisSingleZoneEp91():
    """Add SingleZone accis."""
    import sim.accim_Main as accim_Main
    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
    import sim.accim_Main as accim_Main

    from os import listdir

    filelist = [
        file
        for file in listdir()
        if file.endswith(".idf") and not file.endswith("_pymod.idf")
    ]

    filelist = [file.split(".idf")[0] for file in filelist]

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
