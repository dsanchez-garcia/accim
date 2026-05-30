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
import besos.IDF_class
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
    :param EnergyPlus_version: The default is None.
        Can be '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1', '22.2', '23.1', '23.2', '24.1', '24.2', '25.1' or 'auto'.
    :type EnergyPlus_version: str
    :param TempCtrl: The default is None. Can be 'temp' or 'pmv'.
    :type TempCtrl: str
    :param verboseMode: True to print the process on screen. Default is True.
    :type verboseMode: bool
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
    :param hvac_zone_map: Optional. Manual mapping of existing HVAC object names to
        zone names.  Used only when ScriptType is ``'ex_mm'`` or ``'ex_ac'``.
        Format: ``{'HVAC Object Name': 'Zone Name'}``.
    :type hvac_zone_map: dict or None
    :ivar arguments: A dictionary containing all arguments
    :ivar df_outputs: the pandas DataFrame instance created with argument ``Output_gen_dataframe``
    :ivar occupied_zones: A list containing all occupied zone names within the input idf.
    :ivar occupied_zones_original_name: A list containing all occupied zone original names within the input idf.
    :ivar windows_and_doors: A list containing all window and door names within the input idf.
    :ivar windows_and_doors_original_name:  A list containing all window and door original names within the input idf.
    """
    def __init__(
        self,
        idf: besos.IDF_class = None,
        script_type: str = None,
        supply_air_temp_method: str = None,
        output_type: str = None,
        output_freqs: any = None,
        output_keep_existing: bool = None,
        output_gen_dataframe: bool = None,
        output_take_dataframe: pd.DataFrame = None,
        energyplus_version: str = None,
        temp_control: str = None,
        vrf_schedule: str = 'On 24/7',
        verbose: bool = True,
        eer: float = 2,
        cop: float = 2.1,
        make_averages: bool = False,
        debug: bool = False,
        hvac_zone_map: dict = None,
    ):
        """
        Constructor method.
        """

        # import accim.sim.accim_Main_single_idf as accim_Main
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

        # fullEPversionsList = [
        #     '9.1',
        #     '9.2',
        #     '9.3',
        #     '9.4',
        #     '9.5',
        #     '9.6',
        #     '22.1',
        #     '22.2',
        #     '23.1',
        #     '23.2',
        #     '24.1',
        #     '24.2',
        #     '25.1'
        # ]

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
        if energyplus_version is None:
            energyplus_version = f'{idf.idd_version[0]}.{idf.idd_version[1]}'
        if verbose:
            print('EnergyPlus version is: '+energyplus_version)
        # if EnergyPlus_version not in fullEPversionsList:
        #     print('Valid EnergyPlus_version: ')
        #     print(fullEPversionsList)
        #     raise ValueError(EnergyPlus_version + " is not a valid EnergyPlus_version. "
        #                                           "You must choose a EnergyPlus_version"
        #                                           "from the list above.")
        if verbose:
            print('Temperature Control method is: '+temp_control)
        if temp_control not in fullTempCtrllist:
            print('Valid Temperature Control methods: ')
            print(fullTempCtrllist)
            raise ValueError(temp_control + " is not a valid Temperature Control method. "
                                                  "You must choose a Temperature Control method"
                                                  "from the list above.")
        self.arguments = {
            'ScriptType': script_type,
            'SupplyAirTempInputMethod': supply_air_temp_method,
            'Output_type': output_type,
            'Output_freqs': output_freqs,
            'Output_keep_existing': output_keep_existing,
            'Output_gen_dataframe': output_gen_dataframe,
            'Output_take_dataframe': output_take_dataframe,
            'EnergyPlus_version': energyplus_version,
            'TempCtrl': temp_control,
            'verboseMode': verbose
        }


        if verbose:
            print('''\n=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================\n''')
            print('Starting with file:')
            # print(idf)


        z = accim_Main.AccimJob(
            idf_class_instance=idf,
            script_type=script_type,
            energyplus_version=energyplus_version,
            temp_control=temp_control,
            verbose=verbose,
            hvac_zone_map=hvac_zone_map,
        )

        self.occupied_zones = z.occupiedZones
        self.occupied_zones_original_name = z.occupiedZones_orig
        if z.ismixedmode:
            self.windows_and_doors = z.windownamelist
            self.windows_and_doors_original_name = z.windownamelist_orig

        z.set_comfort_fields_people(energyplus_version=energyplus_version, temp_control=temp_control, verbose=verbose)

        if 'vrf' in script_type.lower():
            if temp_control.lower() == 'temperature' or temp_control.lower() == 'temp':
                z.add_operative_temp_thermostat(verbose=verbose)
            elif temp_control.lower() == 'pmv':
                z.set_pmv_setpoint(verbose=verbose)
            z.add_base_schedules(verbose=verbose)
            z.set_availability_schedule_on(verbose=verbose)
            z.add_vrf_system_schedule(verbose=verbose)
            z.add_curve_objects(verbose=verbose)
            z.add_detailed_hvac_objects(
                energyplus_version=energyplus_version,
                verbose=verbose,
                supply_air_temp_method=supply_air_temp_method,
                eer=eer,
                cop=cop,
                vrf_schedule=vrf_schedule
            )
            if script_type.lower() == 'vrf_mm':
                z.check_ventilation_is_on(verbose=verbose)
            z.add_forscript_schedule_vrf(verbose=verbose)
        elif 'ex' in script_type.lower():
            # todo check if PMV can work with ex_ac
            z.add_forscript_schedule_existing_hvac(verbose=verbose)

        z.add_ems_programs(script_type=script_type, verbose=verbose)
        z.add_ems_output_variables(script_type=script_type, verbose=verbose)
        z.add_global_variables(script_type=script_type, verbose=verbose)
        z.add_internal_variables(verbose=verbose)
        z.add_ems_sensors(script_type=script_type, verbose=verbose)
        z.add_ems_actuators(script_type=script_type, verbose=verbose)

        if 'vrf' in script_type.lower():
            z.add_ems_sensors_vrf(script_type=script_type, verbose=verbose)
        elif script_type.lower() == 'ex_mm':
            z.add_ems_sensors_existing_hvac(verbose=verbose)
            z.add_ems_init_existing_hvac(verbose=verbose)

        z.add_ems_pcm(verbose=verbose)

        if make_averages:
            z.make_averages(verbose=verbose)

        if output_keep_existing == 'true':
            output_keep_existing = True
        elif output_keep_existing == 'false':
            output_keep_existing = False
        if output_keep_existing is True:
            pass
        else:
            z.remove_existing_output_variables()

        if output_type.lower() == 'simplified':
            z.add_output_variables_simplified(
                output_freqs=output_freqs,
                temp_control=temp_control,
                verbose=verbose
            )
        elif output_type.lower() == 'standard':
            z.add_output_variables_standard(
                output_freqs=output_freqs,
                script_type=script_type,
                temp_control=temp_control,
                verbose=verbose
            )
        elif output_type.lower() == 'detailed' or output_type.lower() == 'custom':
            z.add_output_variables_standard(
                output_freqs=output_freqs,
                script_type=script_type,
                temp_control=temp_control,
                verbose=verbose
            )
            z.add_output_variables_detailed(
                output_freqs=output_freqs,
                verbose=verbose
            )
            if output_type.lower() == 'custom':
                output_gen_dataframe = False
                z.apply_specified_outputs()

        if output_take_dataframe is not None:
            z.take_output_dataframe(
                idf_filename=idf.idfname.split('.idf')[0],
                df_outputs_in=output_take_dataframe,
                verbose=verbose
            )

        z.remove_duplicated_output_variables()

        if output_gen_dataframe:
            z.gen_output_dataframe(idf_filename=idf.idfname.split('.idf')[0])
            self.df_outputs = z.df_outputs_temp

        z.add_control_files_objects(verbose=verbose)

        z.add_output_variable_dictionary(verbose=verbose)

        if debug:
            z.add_output_ems(verbose=verbose)

        if verbose:
            print('''\n=======================END OF OUTPUT IDF FILE GENERATION PROCESS=======================\n''')

        self.SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                         program.Name == 'SetInputData'][0])
        self.SetVOFinputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                            program.Name == 'SetVOFinputData'][0])
        self.SetAST = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                   program.Name == 'SetAST'][0])

        self.ApplyCAT = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'ApplyCAT'][0])

        self.SetComfTemp = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                        program.Name == 'SetComfTemp'][0])
        self.SetAppLimits = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                         program.Name == 'SetAppLimits'][0])

        # self.idf = idf

    def modifyAccis(
            self,
            comfort_standard: int = None,
            category: int = None,
            category_cool_offset: float = 0,
            category_heat_offset: float = 0,
            comfort_mode: float = None,
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
            hvac_mode: int = None,
            vent_control: int = None,
            vof_max_temp_diff: float = 6,
            vof_min_temp_diff: float = 1,
            vof_multiplier: float = 0.25,
            vent_setpoint_offset: int = 0,
            min_outdoor_temp_offset: int = 50,
            max_wind_speed: int = 50,
            ast_tol: int = 0.1,

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

        self.arguments_accis = {
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
            'ASTtol': ast_tol
        }

        while setpoint_accuracy < 0:
            raise ValueError('The value for SetpointAcc cannot be less than 0.')
        
        if type(cooling_season_start) is int:
            if cooling_season_start <= 365 and cooling_season_start > 0:
                pass
        elif type(cooling_season_start) is str:
            if len(cooling_season_start.split('/')) == 2:
                day = int(cooling_season_start.split('/')[0])
                month = int(cooling_season_start.split('/')[1])
                from datetime import date
                day_of_year = date(year=2007, month=month, day=day).timetuple().tm_yday
                cooling_season_start = day_of_year

        if type(cooling_season_end) is int:
            if cooling_season_end <= 365 and cooling_season_end > 0:
                pass
        elif type(cooling_season_end) is str:
            if len(cooling_season_end.split('/')) == 2:
                day = int(cooling_season_end.split('/')[0])
                month = int(cooling_season_end.split('/')[1])
                from datetime import date
                day_of_year = date(year=2007, month=month, day=day).timetuple().tm_yday
                cooling_season_end = day_of_year



        self.SetInputData.Program_Line_1 = 'set ComfStand = ' + str(comfort_standard)
        self.SetInputData.Program_Line_2 = 'set CAT = ' + str(category)
        self.SetInputData.Program_Line_3 = 'set ComfMod = ' + str(comfort_mode)
        self.SetInputData.Program_Line_4 = 'set HVACmode = ' + str(hvac_mode)
        self.SetInputData.Program_Line_5 = 'set VentCtrl = ' + str(vent_control)
        self.SetInputData.Program_Line_6 = 'set VSToffset = ' + str(vent_setpoint_offset)
        self.SetInputData.Program_Line_7 = 'set MinOToffset = ' + str(min_outdoor_temp_offset)
        self.SetInputData.Program_Line_8 = 'set MaxWindSpeed = ' + str(max_wind_speed)
        self.SetInputData.Program_Line_9 = 'set ACSTtol = ' + str(-ast_tol)
        self.SetInputData.Program_Line_10 = 'set AHSTtol = ' + str(ast_tol)
        self.SetInputData.Program_Line_11 = 'set CoolSeasonStart = ' + str(cooling_season_start)
        self.SetInputData.Program_Line_12 = 'set CoolSeasonEnd = ' + str(cooling_season_end)

        self.SetComfTemp.Program_Line_2 = f'set ComfTemp = PMOT*{str(custom_ast_m)}+{str(custom_ast_n)}'

        self.SetAppLimits.Program_Line_2 = f'set ACSTaul = {str(custom_ast_acst_aul)}'
        self.SetAppLimits.Program_Line_3 = f'set ACSTall = {str(custom_ast_acst_all)}'
        self.SetAppLimits.Program_Line_4 = f'set AHSTaul = {str(custom_ast_ahst_aul)}'
        self.SetAppLimits.Program_Line_5 = f'set AHSTall = {str(custom_ast_ahst_all)}'

        self.SetAST.Program_Line_1 = 'set SetpointAcc = ' + str(setpoint_accuracy)
        self.SetAST.Program_Line_2 = 'set m = ' + str(custom_ast_m)
        self.SetAST.Program_Line_3 = 'set n = ' + str(custom_ast_n)

        # Dynamic injection: trim to the 16 base lines then append model-specific lines
        while len(self.SetAST.obj) > 18:
            self.SetAST.obj.pop()
        from accim.sim.ems.setast_models import get_SetAST_lines
        dynamic_lines = get_SetAST_lines(comfort_standard, comfort_mode)
        for dline in dynamic_lines:
            self.SetAST.obj.append(dline)

        self.SetVOFinputData.Program_Line_1 = 'set MaxTempDiffVOF = ' + str(vof_max_temp_diff)
        self.SetVOFinputData.Program_Line_2 = 'set MinTempDiffVOF = ' + str(vof_min_temp_diff)
        self.SetVOFinputData.Program_Line_3 = 'set MultiplierVOF = ' + str(vof_multiplier)

        self.ApplyCAT.Program_Line_1 = 'set CATcoolOffset = ' + str(category_cool_offset)
        self.ApplyCAT.Program_Line_2 = 'set CATheatOffset = ' + str(category_heat_offset)
        self.ApplyCAT.Program_Line_4 = f'set ACSToffset = {str(custom_ast_acst_offset)} + {str(category_cool_offset)}'
        self.ApplyCAT.Program_Line_5 = f'set AHSToffset = {str(custom_ast_ahst_offset)} + {str(category_heat_offset)}'

