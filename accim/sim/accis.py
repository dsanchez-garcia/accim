"""
Run the function below to add the ACCIS.

This function transform fixed setpoint temperature
building energy models into adaptive setpoint temperature energy models
by adding the Adaptive Comfort Control Implementation Script (ACCIS)
"""
import pandas as pd
from accim import __version__


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
    :param EnergyPlus_version: The default is 'auto'.
        Can be '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1', '22.2', '23.1', '23.2' or 'auto'.
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
        '22 = INT ISO7730;
        '99 = CUSTOM;
    :type ComfStand: list
    :param CustAST_m: The m coefficient (slope) of custom model linear regression (mx+n)
    :type CustAST_m: float
    :param CustAST_n: The n coefficient of custom model linear regression (mx+n)
    :type CustAST_n: float
    :param CustAST_AHSToffset: The offset for heating setpoint from neutral temperature
        for the custom model linear regression. This value will be summed, therefore, it must be negative.
    :type CustAST_AHSToffset: float
    :param CustAST_ACSToffset: The offset for cooling setpoint from neutral temperature
        for the custom model linear regression. This value will be summed, therefore, it must be positive.
    :type CustAST_ACSToffset: float
    :param CustAST_ACSTaul: The value for the cooling setpoint applicability upper limit (ACSTaul).
    :type CustAST_ACSTaul: float
    :param CustAST_ACSTall: The value for the cooling setpoint applicability lower limit (ACSTall).
    :type CustAST_ACSTall: float
    :param CustAST_AHSTaul: The value for the heating setpoint applicability upper limit (AHSTaul).
    :type CustAST_AHSTaul: float
    :param CustAST_AHSTall: The value for the heating setpoint applicability lower limit (AHSTall).
    :type CustAST_AHSTall: float
    :param CAT: The default is None.
        (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 85 = 85% ACCEPT; 90 = 90% ACCEPT)
    :type CAT: list
    :param CATcoolOffset: An offset to modify comfort models.
        This value is summed to the predefined cooling setpoint offset for the CAT value.
    :type CATcoolOffset: float
    :param CATheatOffset: An offset to modify comfort models.
        This value is summed to the predefined heating setpoint offset for the CAT value.
    :type CATheatOffset: float
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
    :param eer: The energy efficiency ratio of the VRF system for each zone,
    added when using ScriptType vrf_mm or vrf_ac
    :type: eer: int
    :param cop: The coefficient of performance of the VRF system for each zone,
    added when using ScriptType vrf_mm or vrf_ac
    :type: cop: int
    :param make_averages: Used to make averages of hour-counting variables.
    :type make_averages: bool
    :param debugging: If True, an Output:EnergyManagementSystem object is used
        to generate the EDD file.
    :type debugging: bool
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
        ScriptType: str = None,
        SupplyAirTempInputMethod: str = None,
        Output_type: str = None,
        Output_freqs: any = None,
        Output_keep_existing: bool = None,
        Output_gen_dataframe: bool = None,
        Output_take_dataframe: pd.DataFrame = None,
        EnergyPlus_version: str = 'auto',
        TempCtrl: str = None,
        VRFschedule: str = 'On 24/7',
        ComfStand: any = None,
        CAT: any = None,
        CATcoolOffset: float = 0,
        CATheatOffset: float = 0,
        ComfMod: any = None,
        SetpointAcc: float = 10000,
        CustAST_ACSTaul: float = 0,
        CustAST_ACSTall: float = 0,
        CustAST_AHSTaul: float = 0,
        CustAST_AHSTall: float = 0,
        CustAST_m: float = 0,
        CustAST_n: float = 0,
        CustAST_ACSToffset: float = 0,
        CustAST_AHSToffset: float = 0,
        CoolSeasonStart: any = 121,
        CoolSeasonEnd: any = 274,
        HVACmode: any = None,
        VentCtrl: any = None,
        MaxTempDiffVOF: float = 20,
        MinTempDiffVOF: float = 0.5,
        MultiplierVOF: float = 0.25,
        VSToffset: any = [0],
        MinOToffset: any = [50],
        MaxWindSpeed: any = [50],
        ASTtol_start: float = 0.1,
        ASTtol_end_input: float = 0.1,
        ASTtol_steps: float = 0.1,
        NameSuffix: str = '',
        verboseMode: bool = True,
        confirmGen: bool = None,
        eer: float = 2,
        cop: float = 2.1,
        make_averages: bool = False,
        debugging: bool = False,
    ):
        """
        Constructor method.
        """

        # import accim.sim.accim_Main as accim_Main
        import accim.sim.accim_Main as accim_Main

        from os import listdir, remove
        import accim
        import pandas as pd

        filelist = ([file for file in listdir() if file.endswith('.idf')
                     and not '[' in file
                     and not '_pymod' in file])
        if len(filelist) == 0:
            raise FileNotFoundError('No idf files were found. There must be at least 1 idf file located at the path where this script is being run.')

        filelist = ([file.split('.idf')[0] for file in filelist])

        # todo avoid AHST higher than ACST when CAT offsets are used

        objArgsDef = (
            ScriptType is not None,
            SupplyAirTempInputMethod is not None,
            Output_type is not None,
            Output_freqs is not None,
            Output_keep_existing is not None,
            # EnergyPlus_version is not None,
            TempCtrl is not None,
        )

        fullScriptTypeList = [
            'vrf_ac',
            'vrf_mm',
            'ex_mm',
            'ex_ac',
        ]

        SupplyAirTempInputMethodList = [
            'supply air temperature',
            'temperature difference'
        ]

        fullOutputsTypeList = [
            'Standard',
            'standard',
            'Simplified',
            'simplified',
            'Detailed',
            'detailed',
            'Custom',
            'custom',
            # 'Show outputs',
            # 'show outputs'
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
            '22.2',
            '23.1',
            '23.2',
            'auto',
        ]

        fullTempCtrllist = [
            'temperature',
            'temp',
            'pmv'
        ]

        print(
            '\n--------------------------------------------------------'
            f'\nAdaptive-Comfort-Control-Implemented Model (ACCIM) v{__version__}'
            '\n--------------------------------------------------------'
            '\n\nThis tool allows to apply adaptive setpoint temperatures. '
            '\nFor further information, please read the documentation: '
            '\nhttps://accim.readthedocs.io/en/master/'
            '\nFor a visual understanding of the tool, please visit the following jupyter notebooks:'
            '\n-    Using addAccis() to apply adaptive setpoint temperatures'
            '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/addAccis/using_addAccis.html'
            '\n-    Using rename_epw_files() to rename the EPWs for proper data analysis after simulation'
            '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/rename_epw_files/using_rename_epw_files.html'
            '\n-    Using runEp() to directly run simulations with EnergyPlus'
            '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/runEp/using_runEp.html'
            '\n-    Using the class Table() for data analysis'
            '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/Table/using_Table.html'
            '\n-    Full example'
            '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/full_example/full_example.html'
            '\n'
            '\nStarting with the process.'
        )
        self.arguments = {}
        if all(objArgsDef):
            pass
        else:
            print(
                '\nNow, you are going to be asked to enter some information for different arguments '
                'to generate the output IDFs with adaptive setpoint temperatures. '
                '\nIf you are not sure about how to use these parameters, please take a look at the documentation in the following link: '
                #todo change url in all places
                '\nhttps://accim.readthedocs.io/en/master/4_detailed%20use.html'
                '\n\nPlease, enter the following information:'
            )
            ScriptType = input("\nEnter the ScriptType (\n"
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
            if 'vrf' in ScriptType.lower():
                SupplyAirTempInputMethod = input("\nEnter the SupplyAirTempInputMethod (\n"
                                   "for Supply Air Temperature: supply air temperature;\n"
                                   "for Temperature Difference: temperature difference;\n"
                                   "): ")
                while SupplyAirTempInputMethod not in SupplyAirTempInputMethodList:
                    SupplyAirTempInputMethod = input(
                        "    SupplyAirTempInputMethod was not correct. "
                        "    Enter the SupplyAirTempInputMethod (\n"
                                   "for Supply Air Temperature: supply air temperature;\n"
                                   "for Temperature Difference: temperature difference;\n"
                                   "): ")
            Output_keep_existing = input('\nDo you want to keep the existing outputs (true or false)?: ')
            while Output_keep_existing.lower() not in ['true', 'false']:
                Output_keep_existing = input('The answer you entered is not valid. '
                                              'Do you want to keep the existing outputs (true or false)?: ')
            Output_type = input("\nEnter the Output type (standard, simplified, detailed or custom): ")
            while Output_type not in fullOutputsTypeList:
                Output_type = input("   Output type was not correct. "
                                "Please, enter the Output type (standard, simplified, detailed or custom): ")
            Output_freqs = list(freq for freq in input(
                "\nEnter the Output frequencies separated by space (timestep, hourly, daily, monthly, runperiod): ").split())
            while (not(all(elem in fullOutputsFreqList for elem in Output_freqs))):
                Output_freqs = list(freq for freq in input(
                    "Some of the Output frequencies are not correct. "
                    "Please, enter the Output frequencies again separated by space "
                    "(timestep, hourly, daily, monthly, runperiod): ").split())
            Output_gen_dataframe = input('\nDo you want to generate a dataframe to see all outputs? (true or false): ')
            while Output_gen_dataframe.lower() not in ['true', 'false']:
                Output_gen_dataframe = input('The answer you entered is not valid. '
                                              'Do you want to generate a dataframe to see all outputs? (true or false):')
            if Output_gen_dataframe.lower() == 'true':
                Output_gen_dataframe = True
            elif Output_gen_dataframe.lower() == 'false':
                Output_gen_dataframe = False
            EnergyPlus_version = input("\nEnter the EnergyPlus version (9.1 to 23.2, or auto): ")
            while EnergyPlus_version not in fullEPversionsList:
                EnergyPlus_version = input("    EnergyPlus version was not correct. "
                                           "Please, enter the EnergyPlus version (9.1 to 23.2, or auto): ")
            TempCtrl = input('\nEnter the Temperature Control method (temperature or pmv): ')
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
        if 'vrf' in ScriptType.lower():
            if verboseMode:
                print('Supply Air Temperature Input Method is: '+SupplyAirTempInputMethod)
            if SupplyAirTempInputMethod not in SupplyAirTempInputMethodList:
                print('Valid Supply Air Temperature Input Methods: ')
                print(SupplyAirTempInputMethod)
                raise ValueError(SupplyAirTempInputMethod + " is not a valid Supply Air Temperature Input Method. "
                                              "You must choose a Supply Air Temperature Input Method from the list above.")
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
        if EnergyPlus_version.lower() != 'auto':
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
        self.arguments.update(
            {
                'ScriptType': ScriptType,
                'SupplyAirTempInputMethod': SupplyAirTempInputMethod,
                'Output_type': Output_type,
                'Output_freqs': Output_freqs,
                'Output_keep_existing': Output_keep_existing,
                'Output_gen_dataframe': Output_gen_dataframe,
                'Output_take_dataframe': Output_take_dataframe,
                'EnergyPlus_version': EnergyPlus_version,
                'TempCtrl': TempCtrl,
            }
        )

        notWorkingIDFs = []

        if Output_gen_dataframe:
            df_outputs_to_concat = []
        self.input_idfs = {}
        self.occupied_zones = {}
        self.occupied_zones_original_name = {}
        self.windows_and_doors = {}
        self.windows_and_doors_original_name = {}

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

            if EnergyPlus_version.lower() == 'auto':
                EnergyPlus_version = '.'.join([str(i) for i in z.idf1.idd_version[:2]])

            self.input_idfs.update({file: z.idf0})
            self.occupied_zones.update({file: z.occupiedZones})
            self.occupied_zones_original_name.update({file: z.occupiedZones_orig})
            if z.ismixedmode:
                self.windows_and_doors.update({file: z.windownamelist})
                self.windows_and_doors_original_name.update({file: z.windownamelist_orig})

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
                z.addDetHVACobj(
                    EnergyPlus_version=EnergyPlus_version,
                    verboseMode=verboseMode,
                    SupplyAirTempInputMethod=SupplyAirTempInputMethod,
                    eer=eer,
                    cop=cop,
                    VRFschedule=VRFschedule
                )
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

            if make_averages:
                z.makeAverages(verboseMode=verboseMode)

            z.addControlFilesObjects(verboseMode=verboseMode)

            z.addOutputVariableDictionaryObject(verboseMode=verboseMode)

            if debugging:
                z.addOutputEnergyManagementSystem(verboseMode=verboseMode)

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
                    Outputs_freq=Output_freqs,
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
                    Output_gen_dataframe = False
                    z.outputsSpecified()

            if Output_take_dataframe is not None:
                z.takeOutputDataFrame(
                    idf_filename=file,
                    df_outputs_in=Output_take_dataframe,
                    verboseMode=verboseMode
                )

            z.removeDuplicatedOutputVariables()

            if Output_gen_dataframe:
                z.genOutputDataframe(idf_filename=file)
                df_outputs_to_concat.append(z.df_outputs_temp)

            z.saveaccim(verboseMode=verboseMode)
            if verboseMode:
                print('Ending with file:')
                print(file)
                print('''\n=======================END OF GENERIC IDF FILE GENERATION PROCESS=======================\n''')

        if Output_gen_dataframe:
            self.df_outputs = pd.concat(df_outputs_to_concat)

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
                    CATcoolOffset=CATcoolOffset,
                    CATheatOffset=CATheatOffset,
                    ComfMod=ComfMod,
                    SetpointAcc=SetpointAcc,
                    CustAST_ACSTaul=CustAST_ACSTaul,
                    CustAST_ACSTall=CustAST_ACSTall,
                    CustAST_AHSTaul=CustAST_AHSTaul,
                    CustAST_AHSTall=CustAST_AHSTall,
                    CustAST_m=CustAST_m,
                    CustAST_n=CustAST_n,
                    CustAST_ACSToffset=CustAST_ACSToffset,
                    CustAST_AHSToffset=CustAST_AHSToffset,
                    CoolSeasonStart=CoolSeasonStart,
                    CoolSeasonEnd=CoolSeasonEnd,
                    HVACmode=HVACmode,
                    VentCtrl=VentCtrl,
                    MaxTempDiffVOF=MaxTempDiffVOF,
                    MinTempDiffVOF=MinTempDiffVOF,
                    MultiplierVOF=MultiplierVOF,
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
                self.arguments.update(
                    {
                        'ScriptType': ScriptType,
                        'TempCtrl': TempCtrl,
                        'ComfStand': ComfStand,
                        'CAT': CAT,
                        'CATcoolOffset': CATcoolOffset,
                        'CATheatOffset': CATheatOffset,
                        'ComfMod': ComfMod,
                        'SetpointAcc': SetpointAcc,
                        'CustAST_ACSTaul': CustAST_ACSTaul,
                        'CustAST_ACSTall': CustAST_ACSTall,
                        'CustAST_AHSTaul': CustAST_AHSTaul,
                        'CustAST_AHSTall': CustAST_AHSTall,
                        'CustAST_m': CustAST_m,
                        'CustAST_n': CustAST_n,
                        'CustAST_ACSToffset': CustAST_ACSToffset,
                        'CustAST_AHSToffset': CustAST_AHSToffset,
                        'CoolSeasonStart': CoolSeasonStart,
                        'CoolSeasonEnd': CoolSeasonEnd,
                        'HVACmode': HVACmode,
                        'VentCtrl': VentCtrl,
                        'MaxTempDiffVOF': MaxTempDiffVOF,
                        'MinTempDiffVOF': MinTempDiffVOF,
                        'MultiplierVOF': MultiplierVOF,
                        'VSToffset': VSToffset,
                        'MinOToffset': MinOToffset,
                        'MaxWindSpeed': MaxWindSpeed,
                        'ASTtol_start': ASTtol_start,
                        'ASTtol_end_input': ASTtol_end_input,
                        'ASTtol_steps': ASTtol_steps,
                        'NameSuffix': NameSuffix,
                        'verboseMode': verboseMode,
                        'confirmGen': confirmGen,
                    }
                )
            else:
                z.inputData(
                    ScriptType=ScriptType,
                )
                self.arguments.update(z.user_input_arguments)
                self.arguments.update(
                    {
                        'NameSuffix': NameSuffix,
                        'verboseMode': verboseMode,
                        'confirmGen': confirmGen,
                    }
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
                    CATcoolOffset=CATcoolOffset,
                    CATheatOffset=CATheatOffset,
                    ComfMod=ComfMod,
                    SetpointAcc=SetpointAcc,
                    CustAST_ACSTaul=CustAST_ACSTaul,
                    CustAST_ACSTall=CustAST_ACSTall,
                    CustAST_AHSTaul=CustAST_AHSTaul,
                    CustAST_AHSTall=CustAST_AHSTall,
                    CustAST_m=CustAST_m,
                    CustAST_n=CustAST_n,
                    CustAST_ACSToffset=CustAST_ACSToffset,
                    CustAST_AHSToffset=CustAST_AHSToffset,
                    CoolSeasonStart=CoolSeasonStart,
                    CoolSeasonEnd=CoolSeasonEnd,
                    HVACmode=[0],
                    VentCtrl=[0],
                    VSToffset=[0],
                    MaxTempDiffVOF=1,
                    MinTempDiffVOF=0,
                    MultiplierVOF=0,
                    MinOToffset=[0],
                    MaxWindSpeed=[0],
                    ASTtol_start=ASTtol_start,
                    ASTtol_end_input=ASTtol_end_input,
                    ASTtol_steps=ASTtol_steps,
                    NameSuffix=NameSuffix,
                    verboseMode=verboseMode,
                    confirmGen=confirmGen
                    )
                self.arguments.update(
                    {
                        'ScriptType': ScriptType,
                        'TempCtrl': TempCtrl,
                        'ComfStand': ComfStand,
                        'CAT': CAT,
                        'CATcoolOffset': CATcoolOffset,
                        'CATheatOffset': CATheatOffset,
                        'ComfMod': ComfMod,
                        'SetpointAcc': SetpointAcc,
                        'CustAST_ACSTaul': CustAST_ACSTaul,
                        'CustAST_ACSTall': CustAST_ACSTall,
                        'CustAST_AHSTaul': CustAST_AHSTaul,
                        'CustAST_AHSTall': CustAST_AHSTall,
                        'CustAST_m': CustAST_m,
                        'CustAST_n': CustAST_n,
                        'CustAST_ACSToffset': CustAST_ACSToffset,
                        'CustAST_AHSToffset': CustAST_AHSToffset,
                        'CoolSeasonStart': CoolSeasonStart,
                        'CoolSeasonEnd': CoolSeasonEnd,
                        'HVACmode': [0],
                        'VentCtrl': [0],
                        'MaxTempDiffVOF': 1,
                        'MinTempDiffVOF': 0,
                        'MultiplierVOF': 0,
                        'VSToffset': [0],
                        'MinOToffset': [0],
                        'MaxWindSpeed': [0],
                        'ASTtol_start': ASTtol_start,
                        'ASTtol_end_input': ASTtol_end_input,
                        'ASTtol_steps': ASTtol_steps,
                        'NameSuffix': NameSuffix,
                        'verboseMode': verboseMode,
                        'confirmGen': confirmGen,
                    }
                )
            else:
                z.inputData(
                    ScriptType=ScriptType,
                )
                self.arguments.update(z.user_input_arguments)
                self.arguments.update(
                    {
                        'NameSuffix': NameSuffix,
                        'verboseMode': verboseMode,
                        'confirmGen': confirmGen,
                    }
                )
                z.genIDF(
                    ScriptType=ScriptType,
                    TempCtrl=TempCtrl,
                )
        self.output_idfs = z.output_idf_dict
        if verboseMode:
            print('''\n=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================\n''')

        #todo pop up when process ends; by defalt True
