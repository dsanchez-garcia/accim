"""
Run the function below to add the ACCIS.

This function transform fixed setpoint temperature
building energy models into adaptive setpoint temperature energy models
by adding the Adaptive Comfort Control Implementation Script (ACCIS)
"""


class addAccis:
    """
    Adds the Adaptive-Comfort-Control Implementation Script, which is an EnergyManagementSystem
    script that applies adaptive setpoint temperatures to EnergyPlus building energy models.

    :param ScriptType: The default is None.
        'vrf_ac' for VRF system with full air-conditioning mode,
        'vrf_mm' for VRF system with mixed-mode,
        'ex_ac' for existing HVAC only with full air-conditioning mode,
        'ex_mm' for existing HVAC with mixed-mode.
    :type ScriptType: str
    :param SupplyAirTempInputMethod: The default is None.
        'supply air temperature' or 'temperature difference' to use such
        supply air temperature input method in the VRF system.
        Only used if vrf_ac or vrf_mm are used.
    :type SupplyAirTempInputMethod: str
    :param Output_type: The default is None.
        Can be 'standard', 'simplified', 'detailed' or 'custom'.
    :type Output_type: str
    :param Output_freqs: The default is None.
         A list containing the following strings:
         ['timestep', 'hourly', 'daily', 'monthly', 'runperiod']
    :type Output_freqs: list
    :param Output_keep_existing: The default is None.
        It is a boolean (True or False) to keep the existing Output:Variable objects or not.
    :type Output_keep_existing: bool
    :param Output_gen_dataframe: The default is None.
        It is a boolean (True or False) to generate a pandas DataFrame instance
        containing all Output:Variable objects.
    :type Output_gen_dataframe: bool
    :param Output_take_dataframe: It takes the pandas DataFrame previously generated
        with Output_gen_dataframe, which the user has filtered to keep only the rows
        related to the Output:Variable objects that need to be kept in the model.
    :type Output_take_dataframe: bool
    :param EnergyPlus_version: The default is None.
        Can be '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1', '22.2' or '23.1'.
    :type EnergyPlus_version: str
    :param TempCtrl: The default is None. Can be 'temp' or 'pmv'.
    :type TempCtrl: str
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
        '21 = CHL Perez-Fargallo;
        '22 = INT ISO7730
    :type ComfStand: list
    :param CAT: The default is None.
        (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 85 = 85% ACCEPT; 90 = 90% ACCEPT)
    :type CAT: list
    :param ComfMod: The default is None.
        (0/0.X = Static;
        1/1.X = Adaptive when applicable, otherwise relevant local static model;
        2 = Adaptive when applicable, otherwise relevant international static model
        3 = Adaptive when applicable, otherwise horizontal extention of adaptive setpoints)
    :type ComfMod: list
    :param SetpointAcc: A float. It is the number for the accuracy of the setpoint temperatures.
        For instance, if 2 was used, setpoints would be rounded to every half Celsius degree;
        if 10 was used, the setpoints would be rounded to the first decimal.
    :type SetpointAcc: float
    :param CoolSeasonStart: A date in format dd/mm, or the number of the day in the year.
        Defines when start the cooling season, only used in some static setpoint temperatures.
    :type CoolSeasonStart: any
    :param CoolSeasonEnd: A date in format dd/mm, or the number of the day in the year.
        Defines when ends the cooling season, only used in some static setpoint temperatures.
    :type CoolSeasonEnd: any
    :param HVACmode: The default is None.
        (0 = Fully Air-conditioned; 1 = Naturally ventilated; 2 = Mixed Mode)
    :type HVACmode: list
    :param VentCtrl: The default is None.
        (if HVACmode = 1:
        0 = Ventilates above neutral temperature;
        1 = Ventilates above upper comfort limit;
        if HVACmode = 2:
        0 = Ventilates above neutral temperature and fully opens doors and windows;
        1 = Ventilates above lower comfort limit and fully opens doors and windows;
        2 = Ventilates above neutral temperature and opens doors and windows based on the customised venting opening factor;
        3 = Ventilates above lower comfort limit and opens doors and windows based on the customised venting opening factor;
        )
    :type VentCtrl: list
    :param MaxTempDiffVOF: The maximum temperature difference for the Venting Opening Factor.
        Must be a number greater than 0.
    :type MaxTempDiffVOF: float
    :param MinTempDiffVOF: The minimum temperature difference for the Venting Opening Factor.
        Must be a number greater than 0 and smaller than the maximum temperature difference.
    :type MinTempDiffVOF: float
    :param MultiplierVOF: The multiplier for the modulation of the Venting Opening Factor.
        Must be a number between 0 and 1.
    :type MultiplierVOF: float
    :param VSToffset: The default is 0. Please refer to documentation.
    :type VSToffset: list
    :param MinOToffset: The default is 50. Please refer to documentation.
    :type MinOToffset: list
    :param MaxWindSpeed: The default is 50. Please refer to documentation.
    :type MaxWindSpeed: list
    :param ASTtol_start: The default is 0.1. Please refer to documentation.
    :type ASTtol_start: float
    :param ASTtol_end_input: The default is 0.1. Please refer to documentation.
    :type ASTtol_end_input: float
    :param ASTtol_steps: The default is 0.1. Please refer to documentation.
    :type ASTtol_steps: float
    :param NameSuffix: The default is '' (an empty string). Please refer to documentation.
    :type NameSuffix: str
    :param verboseMode: True to print the process on screen. Default is True.
    :type verboseMode: bool
    :param confirmGen: True to skip confirmation of output IDF generation. Default is None.
    :type confirmGen: bool
    :ivar arguments: A dictionary containing all arguments
    :ivar df_outputs: the pandas DataFrame instance created with argument ``Output_gen_dataframe``
    :ivar input_idfs: A dictionary containing all input IDFs following the format {'input idf filename': class ``eppy.modeleditor.IDF object``}
    :ivar occupied_zones: A dictionary containing all input idfs and
        occupied zone names following the format {'idf filename': [list of zone names]}
    :ivar occupied_zones_original_name: A dictionary containing all input idfs and
        occupied zone original names following the format {'idf filename': [list of zone original names]}
    :ivar output_idfs: A dictionary containing all output IDFs following the format {'output idf filename': class ``eppy.modeleditor.IDF object``}
    :ivar windows_and_doors: A dictionary containing all input idfs and
        window and door names following the format
        {'idf filename': [list of window and door names]}
    :ivar windows_and_doors_original_name: A dictionary containing all input idfs and
        window and door original names following the format
        {'idf filename': [list of window and door original names]}
    """
    def __init__(
        self,
        file: str = None,
        ScriptType: str = None,
        SupplyAirTempInputMethod: str = None,
        Output_type: str = None,
        Output_freqs: any = None,
        Output_keep_existing: bool = None,
        # Output_gen_dataframe: bool = None,
        # Output_take_dataframe: pd.DataFrame = None,
        EnergyPlus_version: str = None,
        TempCtrl: str = None,


        # ASTtol_start: float = 0.1,
        # ASTtol_end_input: float = 0.1,
        # ASTtol_steps: float = 0.1,
        # NameSuffix: str = '',
        verboseMode: bool = True,
        # confirmGen: bool = None
    ):
        """
        Constructor method.
        """

        import accim.sim.accim_Main_single_idf as accim_Main
        import besos
        from besos.errors import InstallationError

        # IDF.setiddname(api_environment.EnergyPlusInputIddPath)
        # file = IDF(api_environment.EnergyPlusInputIdfPath)


        if verboseMode:
            print('''\n=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================\n''')
            print('Starting with file:')
            # print(file)

        if EnergyPlus_version is None:
            try:
                EnergyPlus_version = f'{file.idd_version[0]}.{file.idd_version[1]}'
            except besos.errors.InstallationError:
                pass

        z = accim_Main.accimJob(
            idf_class_instance=file,
            ScriptType=ScriptType,
            EnergyPlus_version=EnergyPlus_version,
            TempCtrl=TempCtrl,
            verboseMode=verboseMode
        )
        # self.occupied_zones.update({file: z.occupiedZones})
        # self.occupied_zones_original_name.update({file: z.occupiedZones_orig})
        # self.windows_and_doors.update({file: z.windownamelist})
        # self.windows_and_doors_original_name.update({file: z.windownamelist_orig})

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
            z.addDetHVACobj(EnergyPlus_version=EnergyPlus_version, verboseMode=verboseMode, SupplyAirTempInputMethod=SupplyAirTempInputMethod)
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

        if Output_keep_existing == 'true':
            Output_keep_existing = True
        elif Output_keep_existing == 'false':
            Output_keep_existing = False
        if Output_keep_existing is True:
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
        elif Output_type.lower() == 'detailed' or Output_type.lower() == 'custom':
            z.addOutputVariablesStandard(
                Outputs_freq=Output_freqs,
                ScriptType=ScriptType,
                TempCtrl=TempCtrl,
                verboseMode=verboseMode
            )
            z.addOutputVariablesDetailed(
                Outputs_freq=Output_freqs,
                verboseMode=verboseMode
            )
            if Output_type.lower() == 'custom':
                z.outputsSpecified()

        self.SetInputData = ([program for program in file.idfobjects['EnergyManagementSystem:Program'] if
                         program.Name == 'SetInputData'][0])
        self.SetVOFinputData = ([program for program in file.idfobjects['EnergyManagementSystem:Program'] if
                            program.Name == 'SetVOFinputData'][0])
        self.SetAST = ([program for program in file.idfobjects['EnergyManagementSystem:Program'] if
                   program.Name == 'SetAST'][0])

        self.file = file

    def modifyAccis(
            self,
            ComfStand: int = None,
            CAT: int = None,
            ComfMod: float = None,
            SetpointAcc: float = 10000,
            CoolSeasonStart: any = 121,
            CoolSeasonEnd: any = 274,
            HVACmode: int = None,
            VentCtrl: int = None,
            MaxTempDiffVOF: float = 20,
            MinTempDiffVOF: float = 0.5,
            MultiplierVOF: float = 0.25,
            VSToffset: int = 0,
            MinOToffset: int = 50,
            MaxWindSpeed: int = 50,
            ASTtol: int = 0.1,

    ):

        while SetpointAcc < 0:
            raise ValueError('The value for SetpointAcc cannot be less than 0.')


        self.SetInputData.Program_Line_1 = 'set ComfStand = ' + repr(ComfStand)
        self.SetInputData.Program_Line_2 = 'set CAT = ' + repr(CAT)
        self.SetInputData.Program_Line_3 = 'set ComfMod = ' + repr(ComfMod)
        self.SetInputData.Program_Line_4 = 'set HVACmode = ' + repr(HVACmode)
        self.SetInputData.Program_Line_5 = 'set VentCtrl = ' + repr(VentCtrl)
        self.SetInputData.Program_Line_6 = 'set VSToffset = ' + repr(VSToffset)
        self.SetInputData.Program_Line_7 = 'set MinOToffset = ' + repr(MinOToffset)
        self.SetInputData.Program_Line_8 = 'set MaxWindSpeed = ' + repr(MaxWindSpeed)
        self.SetInputData.Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol)
        self.SetInputData.Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol)
        self.SetInputData.Program_Line_11 = 'set CoolSeasonStart = ' + repr(CoolSeasonStart)
        self.SetInputData.Program_Line_12 = 'set CoolSeasonEnd = ' + repr(CoolSeasonEnd)
        self.SetAST.Program_Line_1 = 'set SetpointAcc = ' + repr(SetpointAcc)

        self.SetVOFinputData.Program_Line_1 = 'set MaxTempDiffVOF = ' + repr(MaxTempDiffVOF)
        self.SetVOFinputData.Program_Line_2 = 'set MinTempDiffVOF = ' + repr(MinTempDiffVOF)
        self.SetVOFinputData.Program_Line_3 = 'set MultiplierVOF = ' + repr(MultiplierVOF)
