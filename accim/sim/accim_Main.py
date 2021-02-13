"""Classes for accim SingleZone and MultipleZone."""


class accimobj:
    """accim Object."""

    from os import listdir
    import numpy

    from sim.accim_IDFgeneration import inputdataSingleZone
    from sim.accim_IDFgeneration import inputdataMultipleZone
    from sim.accim_IDFgeneration import genIDFSingleZone
    from sim.accim_IDFgeneration import genIDFMultipleZone

    from sim.accim_Base import setComfFieldsPeople
    from sim.accim_Base import addOpTempTherm
    from sim.accim_Base import addBaseSchedules
    from sim.accim_Base import setAvailSchOn
    from sim.accim_Base import saveaccim

    from sim.accim_Base_EMS import addEMSProgramsBase
    from sim.accim_Base_EMS import addEMSPCMBase
    from sim.accim_Base_EMS import addEMSOutputVariableBase
    from sim.accim_Base_EMS import addOutputVariablesTimestep
    from sim.accim_Base_EMS import addSimplifiedOutputVariables

    pass


class accimobj_SingleZone_Ep91(accimobj):
    """SingleZone accim object."""

    from sim.accim_SingleZone import addForscriptSchSingleZone

    from sim.accim_SingleZone_EMS import addGlobVarListSingleZone
    from sim.accim_SingleZone_EMS import addEMSSensorsSingleZone
    from sim.accim_SingleZone_EMS import addEMSActuatorsSingleZone
    from sim.accim_SingleZone_EMS import addEMSProgramsSingleZone
    from sim.accim_SingleZone_EMS import addOutputVariablesSingleZone

    def __init__(self, filename_temp):
        from eppy import modeleditor
        from eppy.modeleditor import IDF

        iddfile = "C:/EnergyPlusV9-1-0/Energy+.idd"
        IDF.setiddname(iddfile)

        fname1 = filename_temp + ".idf"
        self.idf0 = IDF(fname1)
        self.idf0.savecopy(filename_temp + "_pymod.idf")

        self.filename = filename_temp + "_pymod"
        fname1 = self.filename + ".idf"
        self.idf1 = IDF(fname1)
        self.filename = filename_temp + "_pymod"

        print(self.filename)

        self.zonenames_orig = [zone.Name for zone in self.idf1.idfobjects["ZONE"]]
        # print(self.zonenames_orig)

        self.zonenames = [
            sub.replace(":", "_")
            for sub in ([zone.Name for zone in self.idf1.idfobjects["ZONE"]])
        ]
        # print(self.zonenames)


class accimobj_MultipleZone_Ep91(accimobj):
    """MultipleZone accim object."""

    from sim.accim_MultipleZone import addMultipleZoneSch
    from sim.accim_MultipleZone import addCurveObj
    from sim.accim_MultipleZone import addDetHVACobjEp91
    from sim.accim_MultipleZone import addForscriptSchMultipleZone
    from sim.accim_MultipleZone import checkVentIsOn

    from sim.accim_MultipleZone_EMS import addGlobVarListMultipleZone
    from sim.accim_MultipleZone_EMS import addEMSSensorsMultipleZone
    from sim.accim_MultipleZone_EMS import addEMSActuatorsMultipleZone
    from sim.accim_MultipleZone_EMS import addEMSProgramsMultipleZone
    from sim.accim_MultipleZone_EMS import addEMSOutputVariableMultipleZone
    from sim.accim_MultipleZone_EMS import addOutputVariablesMultipleZone

    def __init__(self, filename_temp):
        from eppy import modeleditor
        from eppy.modeleditor import IDF

        iddfile = "C:/EnergyPlusV9-1-0/Energy+.idd"
        IDF.setiddname(iddfile)

        fname1 = filename_temp + ".idf"
        self.idf0 = IDF(fname1)
        self.idf0.savecopy(filename_temp + "_pymod.idf")

        self.filename = filename_temp + "_pymod"
        fname1 = self.filename + ".idf"
        self.idf1 = IDF(fname1)
        self.filename = filename_temp + "_pymod"

        print(self.filename)

        self.zonenames_orig = [zone.Name for zone in self.idf1.idfobjects["ZONE"]]
        # print(self.zonenames_orig)

        self.zonenames = [
            sub.replace(":", "_")
            for sub in ([zone.Name for zone in self.idf1.idfobjects["ZONE"]])
        ]
        # print(self.zonenames)

        self.windownamelist_orig = [
            window.Name
            for window in self.idf1.idfobjects[
                "AirflowNetwork:MultiZone:Component:DetailedOpening"
            ]
            if window.Name.endswith("_Win")
        ]
        print(self.windownamelist_orig)
        self.windownamelist_orig_split = [
            i.split("_") for i in self.windownamelist_orig
        ]
        # print(self.windownamelist_orig_split)

        self.windownamelist = [
            sub.replace(":", "_")
            for sub in (
                [
                    window.Name
                    for window in self.idf1.idfobjects[
                        "AirflowNetwork:MultiZone:Component:DetailedOpening"
                    ]
                    if window.Name.endswith("_Win")
                ]
            )
        ]
        # print(self.windownamelist)


class accimobj_SingleZone_Ep94(accimobj):
    """SingleZone accim object."""

    from sim.accim_SingleZone import addForscriptSchSingleZone

    from sim.accim_SingleZone_EMS import addGlobVarListSingleZone
    from sim.accim_SingleZone_EMS import addEMSSensorsSingleZone
    from sim.accim_SingleZone_EMS import addEMSActuatorsSingleZone
    from sim.accim_SingleZone_EMS import addEMSProgramsSingleZone
    from sim.accim_SingleZone_EMS import addOutputVariablesSingleZone

    def __init__(self, filename_temp):
        from eppy import modeleditor
        from eppy.modeleditor import IDF

        iddfile = "C:/EnergyPlusV9-4-0/Energy+.idd"
        IDF.setiddname(iddfile)

        fname1 = filename_temp + ".idf"
        self.idf0 = IDF(fname1)
        self.idf0.savecopy(filename_temp + "_pymod.idf")

        self.filename = filename_temp + "_pymod"
        fname1 = self.filename + ".idf"
        self.idf1 = IDF(fname1)
        self.filename = filename_temp + "_pymod"

        print(self.filename)

        self.zonenames_orig = [zone.Name for zone in self.idf1.idfobjects["ZONE"]]
        # print(self.zonenames_orig)

        self.zonenames = [
            sub.replace(":", "_")
            for sub in ([zone.Name for zone in self.idf1.idfobjects["ZONE"]])
        ]
        # print(self.zonenames)


class accimobj_MultipleZone_Ep94(accimobj):
    """MultipleZone accim object."""

    from sim.accim_MultipleZone import addMultipleZoneSch
    from sim.accim_MultipleZone import addCurveObj
    from sim.accim_MultipleZone import addDetHVACobjEp94
    from sim.accim_MultipleZone import addForscriptSchMultipleZone
    from sim.accim_MultipleZone import checkVentIsOn

    from sim.accim_MultipleZone_EMS import addGlobVarListMultipleZone
    from sim.accim_MultipleZone_EMS import addEMSSensorsMultipleZone
    from sim.accim_MultipleZone_EMS import addEMSActuatorsMultipleZone
    from sim.accim_MultipleZone_EMS import addEMSProgramsMultipleZone
    from sim.accim_MultipleZone_EMS import addEMSOutputVariableMultipleZone
    from sim.accim_MultipleZone_EMS import addOutputVariablesMultipleZone

    def __init__(self, filename_temp):
        from eppy import modeleditor
        from eppy.modeleditor import IDF

        iddfile = "C:/EnergyPlusV9-4-0/Energy+.idd"
        IDF.setiddname(iddfile)

        fname1 = filename_temp + ".idf"
        self.idf0 = IDF(fname1)
        self.idf0.savecopy(filename_temp + "_pymod.idf")

        self.filename = filename_temp + "_pymod"
        fname1 = self.filename + ".idf"
        self.idf1 = IDF(fname1)
        self.filename = filename_temp + "_pymod"

        print(self.filename)

        self.zonenames_orig = [zone.Name for zone in self.idf1.idfobjects["ZONE"]]
        # print(self.zonenames_orig)

        self.zonenames = [
            sub.replace(":", "_")
            for sub in ([zone.Name for zone in self.idf1.idfobjects["ZONE"]])
        ]
        # print(self.zonenames)

        self.windownamelist_orig = [
            window.Name
            for window in self.idf1.idfobjects[
                "AirflowNetwork:MultiZone:Component:DetailedOpening"
            ]
            if window.Name.endswith("_Win")
        ]
        print(self.windownamelist_orig)
        self.windownamelist_orig_split = [
            i.split("_") for i in self.windownamelist_orig
        ]
        # print(self.windownamelist_orig_split)

        self.windownamelist = [
            sub.replace(":", "_")
            for sub in (
                [
                    window.Name
                    for window in self.idf1.idfobjects[
                        "AirflowNetwork:MultiZone:Component:DetailedOpening"
                    ]
                    if window.Name.endswith("_Win")
                ]
            )
        ]
        # print(self.windownamelist)
