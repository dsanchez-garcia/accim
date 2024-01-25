"""
Run the function below to add the ACCIS.

This function transform fixed setpoint temperature
building energy models into adaptive setpoint temperature energy models
by adding the Adaptive Comfort Control Implementation Script (ACCIS)
"""

import pandas as pd
import besos.IDF_class
from accim import __version__

def addAccis(
    idf: besos.IDF_class = None,
    ScriptType: str = None,
    SupplyAirTempInputMethod: str = None,
    Output_type: str = None,
    Output_freqs: any = None,
    Output_keep_existing: bool = None,
    Output_gen_dataframe: bool = None,
    Output_take_dataframe: pd.DataFrame = None,
    EnergyPlus_version: str = None,
    TempCtrl: str = None,
    verboseMode: bool = True,
):

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
    :param verboseMode: True to print the process on screen. Default is True.
    :type verboseMode: bool
    :ivar arguments: A dictionary containing all arguments
    :ivar df_outputs: the pandas DataFrame instance created with argument ``Output_gen_dataframe``
    :ivar occupied_zones: A list containing all occupied zone names within the input idf.
    :ivar occupied_zones_original_name: A list containing all occupied zone original names within the input idf.
    :ivar windows_and_doors: A list containing all window and door names within the input idf.
    :ivar windows_and_doors_original_name:  A list containing all window and door original names within the input idf.
    """


    import accim.sim.accim_Main_single_idf as accim_Main
    import besos
    from besos.errors import InstallationError

    # IDF.setiddname(api_environment.EnergyPlusInputIddPath)
    # idf = IDF(api_environment.EnergyPlusInputIdfPath)

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
    if EnergyPlus_version is None:
        EnergyPlus_version = f'{idf.idd_version[0]}.{idf.idd_version[1]}'
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
    arguments = {
        'ScriptType': ScriptType,
        'SupplyAirTempInputMethod': SupplyAirTempInputMethod,
        'Output_type': Output_type,
        'Output_freqs': Output_freqs,
        'Output_keep_existing': Output_keep_existing,
        'Output_gen_dataframe': Output_gen_dataframe,
        'Output_take_dataframe': Output_take_dataframe,
        'EnergyPlus_version': EnergyPlus_version,
        'TempCtrl': TempCtrl,
        'verboseMode': verboseMode
    }


    if verboseMode:
        print('''\n=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================\n''')
        print('Starting with file:')
        # print(idf)


    z = accim_Main.accimJob(
        idf_class_instance=idf,
        ScriptType=ScriptType,
        EnergyPlus_version=EnergyPlus_version,
        TempCtrl=TempCtrl,
        verboseMode=verboseMode
    )

    # self.occupied_zones = z.occupiedZones
    # self.occupied_zones_original_name = z.occupiedZones_orig
    # self.windows_and_doors = z.windownamelist
    # self.windows_and_doors_original_name = z.windownamelist_orig

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
            Output_gen_dataframe = False
            z.outputsSpecified()

    if Output_take_dataframe is not None:
        z.takeOutputDataFrame(
            idf_filename=idf.idfname.split('.idf')[0],
            df_outputs_in=Output_take_dataframe,
            verboseMode=verboseMode
        )

    z.removeDuplicatedOutputVariables()

    # if Output_gen_dataframe:
    #     z.genOutputDataframe(idf_filename=idf.idfname.split('.idf')[0])
    #     self.df_outputs = z.df_outputs_temp

    if verboseMode:
        print('''\n=======================END OF OUTPUT IDF FILE GENERATION PROCESS=======================\n''')


    # self.idf = idf

def modifyAccis(
        idf,
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
    """
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
    :type ComfStand: int
    :param CAT: The default is None.
        (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 85 = 85% ACCEPT; 90 = 90% ACCEPT)
    :type CAT: int
    :param ComfMod: The default is None.
        (0/0.X = Static;
        1/1.X = Adaptive when applicable, otherwise relevant local static model;
        2 = Adaptive when applicable, otherwise relevant international static model
        3 = Adaptive when applicable, otherwise horizontal extention of adaptive setpoints)
    :type ComfMod: float
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
    :type HVACmode: int
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
    :type VentCtrl: int
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
    :type VSToffset: float
    :param MinOToffset: The default is 50. Please refer to documentation.
    :type MinOToffset: float
    :param MaxWindSpeed: The default is 50. Please refer to documentation.
    :type MaxWindSpeed: float
    :param ASTtol: The default is 0.1. Please refer to documentation.
    :type ASTtol: float
    """

    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetVOFinputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                        program.Name == 'SetVOFinputData'][0])
    SetAST = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
               program.Name == 'SetAST'][0])

    arguments_accis = {
        'ComfStand': ComfStand,
        'CAT': CAT,
        'ComfMod': ComfMod,
        'SetpointAcc': SetpointAcc,
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
        'ASTtol': ASTtol
    }

    while SetpointAcc < 0:
        raise ValueError('The value for SetpointAcc cannot be less than 0.')

    if type(CoolSeasonStart) is int:
        if CoolSeasonStart <= 365 and CoolSeasonStart > 0:
            pass
    elif type(CoolSeasonStart) is str:
        if len(CoolSeasonStart.split('/')) == 2:
            day = int(CoolSeasonStart.split('/')[0])
            month = int(CoolSeasonStart.split('/')[1])
            from datetime import date
            day_of_year = date(year=2007, month=month, day=day).timetuple().tm_yday
            CoolSeasonStart = day_of_year

    if type(CoolSeasonEnd) is int:
        if CoolSeasonEnd <= 365 and CoolSeasonEnd > 0:
            pass
    elif type(CoolSeasonEnd) is str:
        if len(CoolSeasonEnd.split('/')) == 2:
            day = int(CoolSeasonEnd.split('/')[0])
            month = int(CoolSeasonEnd.split('/')[1])
            from datetime import date
            day_of_year = date(year=2007, month=month, day=day).timetuple().tm_yday
            CoolSeasonEnd = day_of_year



    SetInputData.Program_Line_1 = 'set ComfStand = ' + repr(ComfStand)
    SetInputData.Program_Line_2 = 'set CAT = ' + repr(CAT)
    SetInputData.Program_Line_3 = 'set ComfMod = ' + repr(ComfMod)
    SetInputData.Program_Line_4 = 'set HVACmode = ' + repr(HVACmode)
    SetInputData.Program_Line_5 = 'set VentCtrl = ' + repr(VentCtrl)
    SetInputData.Program_Line_6 = 'set VSToffset = ' + repr(VSToffset)
    SetInputData.Program_Line_7 = 'set MinOToffset = ' + repr(MinOToffset)
    SetInputData.Program_Line_8 = 'set MaxWindSpeed = ' + repr(MaxWindSpeed)
    SetInputData.Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol)
    SetInputData.Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol)
    SetInputData.Program_Line_11 = 'set CoolSeasonStart = ' + repr(CoolSeasonStart)
    SetInputData.Program_Line_12 = 'set CoolSeasonEnd = ' + repr(CoolSeasonEnd)

    SetAST.Program_Line_1 = 'set SetpointAcc = ' + repr(SetpointAcc)

    SetVOFinputData.Program_Line_1 = 'set MaxTempDiffVOF = ' + repr(MaxTempDiffVOF)
    SetVOFinputData.Program_Line_2 = 'set MinTempDiffVOF = ' + repr(MinTempDiffVOF)
    SetVOFinputData.Program_Line_3 = 'set MultiplierVOF = ' + repr(MultiplierVOF)
