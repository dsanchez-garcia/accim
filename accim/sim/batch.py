# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Run the function below to add the ACCIS.

This function transform fixed setpoint temperature
building energy models into adaptive setpoint temperature energy models
by adding the Adaptive Comfort Control Implementation Script (ACCIS)
"""
import pandas as pd
from accim import __version__
from accim import lists


class AddAccis:
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
        Can be '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1', '22.2', '23.1', '23.2', '24.1', '24.2', '25.1' or 'auto'.
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
    :param hvac_zone_map: Optional. Manual mapping of existing HVAC object names to
        zone names.  Used only when ScriptType is ``'ex_mm'`` or ``'ex_ac'`` and
        the automatic resolver cannot determine the correct zone (e.g. shared or
        central HVAC equipment not following the ``[ZoneName ObjectName]`` naming
        convention).  Format: ``{'HVAC Object Name': 'Zone Name'}``.
        If the resolver emits a ``UserWarning`` for a given object, provide that
        object's name as a key in this dict with the correct zone name as the value.
    :type hvac_zone_map: dict or None
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
        idfs: list = None,
        script_type: str = None,
        supply_air_temp_method: str = None,
        output_type: str = None,
        output_freqs: any = None,
        output_keep_existing: bool = None,
        output_gen_dataframe: bool = None,
        output_take_dataframe: pd.DataFrame = None,
        energyplus_version: str = 'auto',
        temp_control: str = None,
        vrf_schedule: str = 'On 24/7',
        comfort_standard: any = None,
        category: any = None,
        category_cool_offset: float = 0,
        category_heat_offset: float = 0,
        comfort_mode: any = None,
        setpoint_accuracy: float = 10000,
        custom_ast_acst_aul: float = 0,
        custom_ast_acst_all: float = 0,
        custom_ast_ahst_aul: float = 0,
        custom_ast_ahst_all: float = 0,
        custom_ast_m: float = 0,
        custom_ast_n: float = 0,
        custom_ast_acst_offset: float = 0,
        custom_ast_ahst_offset: float = 0,
        cooling_season_start: any = 121,
        cooling_season_end: any = 274,
        hvac_mode: any = None,
        vent_control: any = None,
        vof_max_temp_diff: float = 6,
        vof_min_temp_diff: float = 1,
        vof_multiplier: float = 0.25,
        vent_setpoint_offset: any = None,
        min_outdoor_temp_offset: any = None,
        max_wind_speed: any = None,
        ast_tol_start: float = 0.1,
        ast_tol_end: float = 0.1,
        ast_tol_steps: float = 0.1,
        name_suffix: str = '',
        verbose: bool = True,
        confirm_generation: bool = None,
        eer: float = 2,
        cop: float = 2.1,
        make_averages: bool = False,
        debug: bool = False,
        hvac_zone_map: dict = None,
    ):
        """
        Constructor method.
        """
        # Avoid mutable default arguments (lists): normalise to the historical defaults.
        if vent_setpoint_offset is None:
            vent_setpoint_offset = [0]
        if min_outdoor_temp_offset is None:
            min_outdoor_temp_offset = [50]
        if max_wind_speed is None:
            max_wind_speed = [50]

        import accim.sim.engine as accim_Main

        from os import listdir, remove
        import accim
        import pandas as pd

        if idfs is None:
            filelist = ([file for file in listdir() if file.endswith('.idf')
                         and not '[' in file
                         and not '_pymod' in file])
        else:
            filelist = [file for file in idfs
                        if file.endswith('.idf')
                        and not '[' in file
                        and not '_pymod' in file]
        if len(filelist) == 0:
            raise FileNotFoundError('No idf files were found. There must be at least 1 idf file located at the path where this script is being run.')

        filelist = ([file.split('.idf')[0] for file in filelist])

        # todo avoid AHST higher than ACST when CAT offsets are used

        objArgsDef = (
            script_type is not None,
            supply_air_temp_method is not None,
            output_type is not None,
            output_freqs is not None,
            output_keep_existing is not None,
            # EnergyPlus_version is not None,
            temp_control is not None,
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
            script_type = input("\nEnter the ScriptType (\n"
                               "for VRFsystem with full air-conditioning mode: vrf_ac;\n"
                               "for VRFsystem with mixed-mode: vrf_mm;\n"
                               "for ExistingHVAC with mixed mode: ex_mm;\n"
                               "for ExistingHVAC with full air-conditioning mode: ex_ac\n"
                               "): ")
            while script_type not in fullScriptTypeList:
                script_type = input("    ScriptType was not correct. "
                                   "    Enter the ScriptType (\n"
                                   "    for VRFsystem with full air-conditioning mode: vrf_ac;\n"
                                   "    for VRFsystem with mixed-mode: vrf_mm;\n"
                                   "    for ExistingHVAC with mixed mode: ex_mm;\n"
                                   "    for ExistingHVAC with full air-conditioning mode: ex_ac\n"
                                   "    ): ")
            if 'vrf' in script_type.lower():
                supply_air_temp_method = input("\nEnter the SupplyAirTempInputMethod (\n"
                                   "for Supply Air Temperature: supply air temperature;\n"
                                   "for Temperature Difference: temperature difference;\n"
                                   "): ")
                while supply_air_temp_method not in SupplyAirTempInputMethodList:
                    supply_air_temp_method = input(
                        "    SupplyAirTempInputMethod was not correct. "
                        "    Enter the SupplyAirTempInputMethod (\n"
                                   "for Supply Air Temperature: supply air temperature;\n"
                                   "for Temperature Difference: temperature difference;\n"
                                   "): ")
            output_keep_existing = input('\nDo you want to keep the existing outputs (true or false)?: ')
            while output_keep_existing.lower() not in ['true', 'false']:
                output_keep_existing = input('The answer you entered is not valid. '
                                              'Do you want to keep the existing outputs (true or false)?: ')
            output_type = input("\nEnter the Output type (standard, simplified, detailed or custom): ")
            while output_type not in fullOutputsTypeList:
                output_type = input("   Output type was not correct. "
                                "Please, enter the Output type (standard, simplified, detailed or custom): ")
            output_freqs = list(freq for freq in input(
                "\nEnter the Output frequencies separated by space (timestep, hourly, daily, monthly, runperiod): ").split())
            while (not(all(elem in fullOutputsFreqList for elem in output_freqs))):
                output_freqs = list(freq for freq in input(
                    "Some of the Output frequencies are not correct. "
                    "Please, enter the Output frequencies again separated by space "
                    "(timestep, hourly, daily, monthly, runperiod): ").split())
            output_gen_dataframe = input('\nDo you want to generate a dataframe to see all outputs? (true or false): ')
            while output_gen_dataframe.lower() not in ['true', 'false']:
                output_gen_dataframe = input('The answer you entered is not valid. '
                                              'Do you want to generate a dataframe to see all outputs? (true or false):')
            if output_gen_dataframe.lower() == 'true':
                output_gen_dataframe = True
            elif output_gen_dataframe.lower() == 'false':
                output_gen_dataframe = False
            energyplus_version = input("\nEnter the EnergyPlus version (9.1 to 25.1, or auto): ")
            while energyplus_version not in lists.fullEPversionsList:
                energyplus_version = input("    EnergyPlus version was not correct. "
                                           "Please, enter the EnergyPlus version (9.1 to 25.1, or auto): ")
            temp_control = input('\nEnter the Temperature Control method (temperature or pmv): ')
            while temp_control not in fullTempCtrllist:
                temp_control = input("  Temperature Control method was not correct. "
                                 "Please, enter the Temperature Control method (temperature or pmv): ")

        if verbose:
            print('Basic input data:')
            # print(f'accim version: {accim.__version__}')
            print('ScriptType is: '+script_type)
        if script_type not in fullScriptTypeList:
            print('Valid ScriptTypes: ')
            print(fullScriptTypeList)
            raise ValueError(script_type + " is not a valid ScriptType. "
                                          "You must choose a ScriptType from the list above.")
        if 'vrf' in script_type.lower():
            if verbose:
                print('Supply Air Temperature Input Method is: '+supply_air_temp_method)
            if supply_air_temp_method not in SupplyAirTempInputMethodList:
                print('Valid Supply Air Temperature Input Methods: ')
                print(supply_air_temp_method)
                raise ValueError(supply_air_temp_method + " is not a valid Supply Air Temperature Input Method. "
                                              "You must choose a Supply Air Temperature Input Method from the list above.")
        if verbose:
            print('Output type is: ' + output_type)
        if output_type not in fullOutputsTypeList:
            print('Valid Output type: ')
            print(fullOutputsTypeList)
            raise ValueError(output_type + " is not a valid Output. "
                                       "You must choose a Output from the list above.")
        if verbose:
            print('Output frequencies are: ')
            print(output_freqs)
        if not (all(elem in fullOutputsFreqList for elem in output_freqs)):
            print('Valid Output freqs: ')
            print(fullOutputsFreqList)
            raise ValueError('Some of the Output frequencies in '+output_freqs + " is not a valid Output. "
                                       "All Output frequencies must be included in the list above.")
        if energyplus_version.lower() != 'auto':
            if verbose:
                print('EnergyPlus version is: '+energyplus_version)
            if energyplus_version not in lists.fullEPversionsList:
                print('Valid EnergyPlus_version: ')
                print(lists.fullEPversionsList)
                raise ValueError(energyplus_version + " is not a valid EnergyPlus_version. "
                                                      "You must choose a EnergyPlus_version"
                                                      "from the list above.")
        if verbose:
            print('Temperature Control method is: '+temp_control)
        if temp_control not in fullTempCtrllist:
            print('Valid Temperature Control methods: ')
            print(fullTempCtrllist)
            raise ValueError(temp_control + " is not a valid Temperature Control method. "
                                                  "You must choose a Temperature Control method"
                                                  "from the list above.")
        self.arguments.update(
            {
                'ScriptType': script_type,
                'SupplyAirTempInputMethod': supply_air_temp_method,
                'Output_type': output_type,
                'Output_freqs': output_freqs,
                'Output_keep_existing': output_keep_existing,
                'Output_gen_dataframe': output_gen_dataframe,
                'Output_take_dataframe': output_take_dataframe,
                'EnergyPlus_version': energyplus_version,
                'TempCtrl': temp_control,
            }
        )

        notWorkingIDFs = []

        if output_gen_dataframe:
            df_outputs_to_concat = []
        self.input_idfs = {}
        self.occupied_zones = {}
        self.occupied_zones_original_name = {}
        self.windows_and_doors = {}
        self.windows_and_doors_original_name = {}
        valid_pymod_files = []

        for file in filelist:
            if verbose:
                print('''\n=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================\n''')
                print('Starting with file:')
                print(file)
            z = accim_Main.AccimJob(
                filename_temp=file,
                script_type=script_type,
                energyplus_version=energyplus_version,
                temp_control=temp_control,
                verbose=verbose,
                hvac_zone_map=hvac_zone_map,
            )

            if energyplus_version.lower() == 'auto':
                energyplus_version = '.'.join([str(i) for i in z.idf1.idd_version[:2]])

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

            output_gen_dataframe = z.apply_accis(
                script_type=script_type,
                supply_air_temp_method=supply_air_temp_method,
                temp_control=temp_control,
                output_type=output_type,
                output_freqs=output_freqs,
                output_keep_existing=output_keep_existing,
                output_take_dataframe=output_take_dataframe,
                output_gen_dataframe=output_gen_dataframe,
                make_averages=make_averages,
                debug=debug,
                eer=eer,
                cop=cop,
                vrf_schedule=vrf_schedule,
                energyplus_version=energyplus_version,
                verbose=verbose,
                take_dataframe_filename=file,
                single_idf=False,
            )

            if output_gen_dataframe:
                z.gen_output_dataframe(idf_filename=file)
                df_outputs_to_concat.append(z.df_outputs_temp)

            z.set_simulation_control_sizing(verbose=verbose)
            z.save(verbose=verbose)
            if verbose:
                print('Ending with file:')
                print(file)
                print('''\n=======================END OF GENERIC IDF FILE GENERATION PROCESS=======================\n''')
            valid_pymod_files.append(file.split('.idf')[0] + '_pymod.idf')

        if output_gen_dataframe:
            self.df_outputs = pd.concat(df_outputs_to_concat)

        if verbose:
            print('The following IDFs will not work, and therefore these will be deleted:')
        if len(notWorkingIDFs) > 0:
            if verbose:
                print(*notWorkingIDFs, sep="\n")
            filelist_pymod = ([file for file in listdir() if file.endswith('.idf')
                         and '_pymod' in file])

            for file in notWorkingIDFs:
                for i in filelist_pymod:
                    if file in i:
                        remove(i)
        else:
            if verbose:
                print('None')

        if verbose:
            print('''\n=======================START OF OUTPUT IDF FILES GENERATION PROCESS=======================\n''')

        args_needed_mm = (
            comfort_standard is not None,
            category is not None,
            comfort_mode is not None,
            hvac_mode is not None,
            vent_control is not None,
        )

        args_needed_ac = (
            comfort_standard is not None,
            category is not None,
            comfort_mode is not None,
        )
        if script_type.lower() == 'vrf_mm' or script_type.lower() == 'ex_mm':
            if all(args_needed_mm):
                z.generate_idfs(
                    filelist_pymod=valid_pymod_files,
                    script_type=script_type,
                    temp_control=temp_control,
                    comfort_standard=comfort_standard,
                    category=category,
                    category_cool_offset=category_cool_offset,
                    category_heat_offset=category_heat_offset,
                    comfort_mode=comfort_mode,
                    setpoint_accuracy=setpoint_accuracy,
                    custom_ast_acst_aul=custom_ast_acst_aul,
                    custom_ast_acst_all=custom_ast_acst_all,
                    custom_ast_ahst_aul=custom_ast_ahst_aul,
                    custom_ast_ahst_all=custom_ast_ahst_all,
                    custom_ast_m=custom_ast_m,
                    custom_ast_n=custom_ast_n,
                    custom_ast_acst_offset=custom_ast_acst_offset,
                    custom_ast_ahst_offset=custom_ast_ahst_offset,
                    cooling_season_start=cooling_season_start,
                    cooling_season_end=cooling_season_end,
                    hvac_mode=hvac_mode,
                    vent_control=vent_control,
                    vof_max_temp_diff=vof_max_temp_diff,
                    vof_min_temp_diff=vof_min_temp_diff,
                    vof_multiplier=vof_multiplier,
                    vent_setpoint_offset=vent_setpoint_offset,
                    min_outdoor_temp_offset=min_outdoor_temp_offset,
                    max_wind_speed=max_wind_speed,
                    ast_tol_start=ast_tol_start,
                    ast_tol_end=ast_tol_end,
                    ast_tol_steps=ast_tol_steps,
                    name_suffix=name_suffix,
                    verbose=verbose,
                    confirm_generation=confirm_generation
                    )
                self.arguments.update(
                    {
                        'ScriptType': script_type,
                        'TempCtrl': temp_control,
                        'ComfStand': comfort_standard,
                        'CAT': category,
                        'CATcoolOffset': category_cool_offset,
                        'CATheatOffset': category_heat_offset,
                        'ComfMod': comfort_mode,
                        'SetpointAcc': setpoint_accuracy,
                        'CustAST_ACSTaul': custom_ast_acst_aul,
                        'CustAST_ACSTall': custom_ast_acst_all,
                        'CustAST_AHSTaul': custom_ast_ahst_aul,
                        'CustAST_AHSTall': custom_ast_ahst_all,
                        'CustAST_m': custom_ast_m,
                        'CustAST_n': custom_ast_n,
                        'CustAST_ACSToffset': custom_ast_acst_offset,
                        'CustAST_AHSToffset': custom_ast_ahst_offset,
                        'CoolSeasonStart': cooling_season_start,
                        'CoolSeasonEnd': cooling_season_end,
                        'HVACmode': hvac_mode,
                        'VentCtrl': vent_control,
                        'MaxTempDiffVOF': vof_max_temp_diff,
                        'MinTempDiffVOF': vof_min_temp_diff,
                        'MultiplierVOF': vof_multiplier,
                        'VSToffset': vent_setpoint_offset,
                        'MinOToffset': min_outdoor_temp_offset,
                        'MaxWindSpeed': max_wind_speed,
                        'ASTtol_start': ast_tol_start,
                        'ASTtol_end_input': ast_tol_end,
                        'ASTtol_steps': ast_tol_steps,
                        'NameSuffix': name_suffix,
                        'verboseMode': verbose,
                        'confirmGen': confirm_generation,
                    }
                )
            else:
                z.input_data(
                    script_type=script_type,
                )
                self.arguments.update(z.user_input_arguments)
                self.arguments.update(
                    {
                        'NameSuffix': name_suffix,
                        'verboseMode': verbose,
                        'confirmGen': confirm_generation,
                    }
                )
                z.generate_idfs(
                    filelist_pymod=valid_pymod_files,
                    script_type=script_type,
                    temp_control=temp_control,
                )
        elif script_type.lower() == 'ex_ac' or script_type.lower() == 'vrf_ac':
            if all(args_needed_ac):
                z.generate_idfs(
                    filelist_pymod=valid_pymod_files,
                    script_type=script_type,
                    temp_control=temp_control,
                    comfort_standard=comfort_standard,
                    category=category,
                    category_cool_offset=category_cool_offset,
                    category_heat_offset=category_heat_offset,
                    comfort_mode=comfort_mode,
                    setpoint_accuracy=setpoint_accuracy,
                    custom_ast_acst_aul=custom_ast_acst_aul,
                    custom_ast_acst_all=custom_ast_acst_all,
                    custom_ast_ahst_aul=custom_ast_ahst_aul,
                    custom_ast_ahst_all=custom_ast_ahst_all,
                    custom_ast_m=custom_ast_m,
                    custom_ast_n=custom_ast_n,
                    custom_ast_acst_offset=custom_ast_acst_offset,
                    custom_ast_ahst_offset=custom_ast_ahst_offset,
                    cooling_season_start=cooling_season_start,
                    cooling_season_end=cooling_season_end,
                    hvac_mode=[0],
                    vent_control=[0],
                    vent_setpoint_offset=[0],
                    vof_max_temp_diff=1,
                    vof_min_temp_diff=0,
                    vof_multiplier=0,
                    min_outdoor_temp_offset=[0],
                    max_wind_speed=[0],
                    ast_tol_start=ast_tol_start,
                    ast_tol_end=ast_tol_end,
                    ast_tol_steps=ast_tol_steps,
                    name_suffix=name_suffix,
                    verbose=verbose,
                    confirm_generation=confirm_generation
                    )
                self.arguments.update(
                    {
                        'ScriptType': script_type,
                        'TempCtrl': temp_control,
                        'ComfStand': comfort_standard,
                        'CAT': category,
                        'CATcoolOffset': category_cool_offset,
                        'CATheatOffset': category_heat_offset,
                        'ComfMod': comfort_mode,
                        'SetpointAcc': setpoint_accuracy,
                        'CustAST_ACSTaul': custom_ast_acst_aul,
                        'CustAST_ACSTall': custom_ast_acst_all,
                        'CustAST_AHSTaul': custom_ast_ahst_aul,
                        'CustAST_AHSTall': custom_ast_ahst_all,
                        'CustAST_m': custom_ast_m,
                        'CustAST_n': custom_ast_n,
                        'CustAST_ACSToffset': custom_ast_acst_offset,
                        'CustAST_AHSToffset': custom_ast_ahst_offset,
                        'CoolSeasonStart': cooling_season_start,
                        'CoolSeasonEnd': cooling_season_end,
                        'HVACmode': [0],
                        'VentCtrl': [0],
                        'MaxTempDiffVOF': 1,
                        'MinTempDiffVOF': 0,
                        'MultiplierVOF': 0,
                        'VSToffset': [0],
                        'MinOToffset': [0],
                        'MaxWindSpeed': [0],
                        'ASTtol_start': ast_tol_start,
                        'ASTtol_end_input': ast_tol_end,
                        'ASTtol_steps': ast_tol_steps,
                        'NameSuffix': name_suffix,
                        'verboseMode': verbose,
                        'confirmGen': confirm_generation,
                    }
                )
            else:
                z.input_data(
                    script_type=script_type,
                )
                self.arguments.update(z.user_input_arguments)
                self.arguments.update(
                    {
                        'NameSuffix': name_suffix,
                        'verboseMode': verbose,
                        'confirmGen': confirm_generation,
                    }
                )
                z.generate_idfs(
                    filelist_pymod=valid_pymod_files,
                    script_type=script_type,
                    temp_control=temp_control,
                )
        self.output_idfs = z.output_idf_dict
        if verbose:
            print('''\n=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================\n''')

        #todo pop up when process ends; by defalt True
