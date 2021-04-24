"""Class for accim SingleZone and MultipleZone."""

class accimJob():
    """accim object."""
    # todo clean imports
    from os import listdir
    import numpy

    import accim.sim.accim_IDFgeneration as IDFgen
    import accim.sim.accim_Base as base
    import accim.sim.accim_Base_EMS as base_EMS
    import accim.sim.accim_SingleZone as sz
    import accim.sim.accim_SingleZone_EMS as sz_EMS
    import accim.sim.accim_MultipleZone as mz
    import accim.sim.accim_MultipleZone_EMS as mz_EMS

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

        Exceptions
                DESCRIPTION. EnergyPlus version not supported.
            Only works for EnergyPlus 9.1 (enter Ep91) and
            EnergyPlus 9.4 (enter Ep94) versions.

        :return:
        """
        import accim.sim.accim_Main as main
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
                ScriptType = input("ScriptType was not correct. Please, enter the ScriptType (MultipleZone or mz, or SingleZone or sz): ")
            Outputs = input("Enter the Output (Standard, Simplified or Timestep): ")
            while Outputs not in fullOutputsList:
                Outputs = input("Output was not correct. Please, enter the Output (Standard, Simplified or Timestep): ")
            EnergyPlus_version = input("Enter the EnergyPlus version (Ep91 or Ep94): ")
            while EnergyPlus_version not in fullEPversionsList:
                EnergyPlus_version = input("EnergyPlus version was not correct. Please, enter the EnergyPlus version (Ep91 or Ep94): ")
        if verboseMode:
            print('ScriptType is: ' + ScriptType)
        if ScriptType not in fullScriptTypeList:
            print('Valid ScriptTypes: ')
            print(fullScriptTypeList)
            raise ValueError(ScriptType + " is not a valid ScriptType. You must choose a ScriptType from the list above.")
        if verboseMode:
            print('Outputs are: ' + Outputs)
        if Outputs not in fullOutputsList:
            print('Valid Outputs: ')
            print(fullOutputsList)
            raise ValueError(Outputs + " is not a valid Output. You must choose a Output from the list above.")
        if verboseMode:
            print('EnergyPlus version is: ' + EnergyPlus_version)
        if EnergyPlus_version not in fullEPversionsList:
            print('Valid EnergyPlus_version: ')
            print(fullEPversionsList)
            raise ValueError(EnergyPlus_version + " is not a valid EnergyPlus_version. You must choose a EnergyPlus_version from the list above.")

        for file in filelist:
            if verboseMode:
                print('''\n=======================START OF PROCESS=======================\n''')
                print('Starting with file:')
                print(file)
            z = main.accimJob(filename_temp=file, ScriptType=ScriptType, EnergyPlus_version=EnergyPlus_version, verboseMode=verboseMode)

            z.base.setComfFieldsPeople(verboseMode=verboseMode)
            z.base.addOpTempTherm(verboseMode=verboseMode)
            z.base.addBaseSchedules(verboseMode=verboseMode)
            z.base.setAvailSchOn(verboseMode=verboseMode)

            if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
                z.mz.addMultipleZoneSch(verboseMode=verboseMode)
                z.mz.addCurveObj(verboseMode=verboseMode)
                if EnergyPlus_version.lower() == 'ep94':
                    z.mz.addDetHVACobjEp94(verboseMode=verboseMode)
                elif EnergyPlus_version.lower() == 'ep91':
                    z.mz.addDetHVACobjEp91(verboseMode=verboseMode)
                z.mz.checkVentIsOn(verboseMode=verboseMode)
                z.mz.addForscriptSchMultipleZone(verboseMode=verboseMode)
            elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
                z.sz.addForscriptSchSingleZone(verboseMode=verboseMode)

            z.base_EMS.addEMSProgramsBase(verboseMode=verboseMode)
            z.base_EMS.addEMSOutputVariableBase(verboseMode=verboseMode)

            if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
                z.mz_EMS.addGlobVarListMultipleZone(verboseMode=verboseMode)
                z.mz_EMS.addEMSSensorsMultipleZone(verboseMode=verboseMode)
                z.mz_EMS.addEMSActuatorsMultipleZone(verboseMode=verboseMode)
                z.mz_EMS.addEMSProgramsMultipleZone(verboseMode=verboseMode)
            elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
                z.sz_EMS.addGlobVarListSingleZone(verboseMode=verboseMode)
                z.sz_EMS.addEMSSensorsSingleZone(verboseMode=verboseMode)
                z.sz_EMS.addEMSActuatorsSingleZone(verboseMode=verboseMode)
                z.sz_EMS.addEMSProgramsSingleZone(verboseMode=verboseMode)

            z.base_EMS.addEMSPCMBase(verboseMode=verboseMode)

            if ScriptType.lower() == 'MultipleZones'.lower() or ScriptType.lower() == 'mz':
                z.mz_EMS.addEMSOutputVariableMultipleZone(verboseMode=verboseMode)
                if Outputs.lower() == 'Simplified'.lower():
                    z.base_EMS.addSimplifiedOutputVariables(verboseMode=verboseMode)
                elif Outputs.lower() == 'Standard'.lower():
                    z.mz_EMS.addOutputVariablesMultipleZone(verboseMode=verboseMode)
            elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
                if Outputs.lower() == 'Simplified'.lower():
                    z.base_EMS.addSimplifiedOutputVariables(verboseMode=verboseMode)
                elif Outputs.lower() == 'Standard'.lower():
                    z.sz_EMS.addOutputVariablesSingleZone(verboseMode=verboseMode)
            if Outputs.lower() == 'Timestep'.lower():
                z.base_EMS.addOutputVariablesTimestep(verboseMode=verboseMode)

            z.base.saveaccim(verboseMode=verboseMode)
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
                z.IDFgen.genIDFMultipleZone(
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
                z.IDFgen.inputdataMultipleZone()
                z.IDFgen.genIDFMultipleZone()
        elif ScriptType.lower() == 'SingleZone'.lower() or ScriptType.lower() == 'sz':
            if all(args_needed_sz):
                z.IDFgen.genIDFSingleZone(
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
                z.IDFgen.inputdataSingleZone()
                z.IDFgen.genIDFSingleZone()
