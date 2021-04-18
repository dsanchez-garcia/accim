"""Class for accim SingleZone and MultipleZone."""

class accimInstance():
    """accim object."""

    from os import listdir
    import numpy

    from accim.sim.accim_IDFgeneration import inputdataSingleZone
    from accim.sim.accim_IDFgeneration import inputdataMultipleZone
    from accim.sim.accim_IDFgeneration import genIDFSingleZone
    from accim.sim.accim_IDFgeneration import genIDFMultipleZone

    from accim.sim.accim_Base import setComfFieldsPeople
    from accim.sim.accim_Base import addOpTempTherm
    from accim.sim.accim_Base import addBaseSchedules
    from accim.sim.accim_Base import setAvailSchOn
    from accim.sim.accim_Base import saveaccim

    from accim.sim.accim_Base_EMS import addEMSProgramsBase
    from accim.sim.accim_Base_EMS import addEMSPCMBase
    from accim.sim.accim_Base_EMS import addEMSOutputVariableBase
    from accim.sim.accim_Base_EMS import addOutputVariablesTimestep
    from accim.sim.accim_Base_EMS import addSimplifiedOutputVariables


    from accim.sim.accim_SingleZone import addForscriptSchSingleZone

    from accim.sim.accim_SingleZone_EMS import addGlobVarListSingleZone
    from accim.sim.accim_SingleZone_EMS import addEMSSensorsSingleZone
    from accim.sim.accim_SingleZone_EMS import addEMSActuatorsSingleZone
    from accim.sim.accim_SingleZone_EMS import addEMSProgramsSingleZone
    from accim.sim.accim_SingleZone_EMS import addOutputVariablesSingleZone


    from accim.sim.accim_MultipleZone import addMultipleZoneSch
    from accim.sim.accim_MultipleZone import addCurveObj
    from accim.sim.accim_MultipleZone import addDetHVACobjEp91
    from accim.sim.accim_MultipleZone import addDetHVACobjEp94
    from accim.sim.accim_MultipleZone import addForscriptSchMultipleZone
    from accim.sim.accim_MultipleZone import checkVentIsOn

    from accim.sim.accim_MultipleZone_EMS import addGlobVarListMultipleZone
    from accim.sim.accim_MultipleZone_EMS import addEMSSensorsMultipleZone
    from accim.sim.accim_MultipleZone_EMS import addEMSActuatorsMultipleZone
    from accim.sim.accim_MultipleZone_EMS import addEMSProgramsMultipleZone
    from accim.sim.accim_MultipleZone_EMS import addEMSOutputVariableMultipleZone
    from accim.sim.accim_MultipleZone_EMS import addOutputVariablesMultipleZone


    def __init__(self, filename_temp, ScriptType: str = None, EnergyPlus_version: str = None, verboseMode: bool = True):
        from eppy import modeleditor
        from eppy.modeleditor import IDF
        if EnergyPlus_version.lower() == 'ep94':
            iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
        elif EnergyPlus_version.lower() == 'ep91':
            iddfile = 'C:/EnergyPlusV9-1-0/Energy+.idd'
        else:
            raise ValueError("""EnergyPlus version not supported.\n
                                     Only works for EnergyPlus 9.1 (enter Ep91) and
                                     EnergyPlus 9.4 (enter Ep94) versions.""")
        IDF.setiddname(iddfile)

        fname1 = filename_temp+'.idf'
        self.idf0 = IDF(fname1)
        self.idf0.savecopy(filename_temp+'_pymod.idf')

        self.filename = filename_temp+'_pymod'
        fname1 = self.filename+'.idf'
        self.idf1 = IDF(fname1)
        self.filename = filename_temp+'_pymod'

        # print(self.filename)

        self.zonenames_orig = ([zone.Name for zone in self.idf1.idfobjects['ZONE']])
        # print(self.zonenames_orig)

        self.zonenames = ([sub.replace(':', '_') for sub in ([zone.Name for zone in self.idf1.idfobjects['ZONE']])])
        # print(self.zonenames)
        if verboseMode:
            print(f'The zones in the model {filename_temp} are:')
            print(*self.zonenames, sep="\n")

        if ScriptType.lower() == 'mz' or ScriptType.lower() == 'multiplezone':
            self.windownamelist_orig = ([window.Name for window in self.idf1.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening'] if window.Name.endswith('_Win')])
            # print(self.windownamelist_orig)
            self.windownamelist_orig_split = ([i.split('_') for i in self.windownamelist_orig])
            # print(self.windownamelist_orig_split)

            self.windownamelist = ([sub.replace(':', '_') for sub in ([window.Name for window in self.idf1.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening'] if window.Name.endswith('_Win')])])
            # print(self.windownamelist)
            if verboseMode:
                print(f'The windows in the model {filename_temp} are:')
                print(*self.windownamelist, sep="\n")
