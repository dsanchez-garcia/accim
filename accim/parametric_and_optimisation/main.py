import os
import re
import json
import glob as pyglob
from typing import Literal, List, Union, Optional
import warnings
import functools
import accim
import numpy as np
import pandas as pd
import besos
from besos import sampling
from besos.evaluator import EvaluatorEP
import besos.optimizer as optimizer
from besos.parameters import RangeParameter, CategoryParameter
from besos.problem import EPProblem
from besos.objectives import VariableReader, MeterReader
from besos import IDF_class
from accim.utils import print_available_outputs_mod, modify_timesteps, set_occupancy_to_always, remove_accents_in_idf, reduce_runtime, read_eso_using_readvarseso
from accim.parametric_and_optimisation.utils import expand_to_hourly_dataframe, identify_hourly_columns
import accim.sim.accis_single_idf_funcs as accis
import accim.sim.apmv_setpoints as apmv
import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf_accim
import accim.parametric_and_optimisation.funcs_for_besos.param_apmv as bf_apmv
import accim.parametric_and_optimisation.parameters as params
from accim.parametric_and_optimisation.analysis import AnalysisMixin
from accim.parametric_and_optimisation.plotting import PlottingMixin
from accim.parametric_and_optimisation.patches import GlobalAllCapsDict, _patched_eval_func, _patched_to_platypus
import accim.parametric_and_optimisation.params_dicts as params_dicts
allowed_output_freqs = Literal['timestep', 'hourly', 'daily', 'monthly', 'runperiod']

def get_rdd_file_as_df():
    """
    Returns the .rdd file from the test simulation as a pandas DataFrame

    :return: a pandas DataFrame containing the .rdd file from the test simulation
    """
    rdd_df = pd.read_csv(filepath_or_buffer='available_outputs/eplusout.rdd', sep=',|;', skiprows=2, names=['object', 'key_value', 'variable_name', 'frequency', 'units'], engine='python')
    return rdd_df

def parse_mtd_file() -> list[Union[dict[str, Union[str, None, list[str]]], dict[str, Union[str, None, list[str]]]]]:
    """
    Returns a list of the objects in the .mtd file from the test simulation.

    :return: a list of the objects in the .mtd file from the test simulation
    """
    meter_list = []
    with open('available_outputs/eplusout.mtd', 'r') as file:
        lines = file.readlines()
    (meter_id, description) = (None, None)
    on_meters = []
    for line in lines:
        line = line.strip()
        if line.startswith('Meters for'):
            if meter_id is not None:
                meter_list.append({'meter_id': meter_id, 'description': description, 'on_meters': on_meters})
            match = re.match('Meters for (\\d+),(.+)', line)
            if match:
                meter_id = match.group(1)
                description = match.group(2)
                on_meters = []
        elif line.startswith('OnMeter'):
            on_meters.append(line.split('=')[1].strip())
    if meter_id is not None:
        meter_list.append({'meter_id': meter_id, 'description': description, 'on_meters': on_meters})
    return meter_list

def get_mdd_file_as_df():
    """
    Returns the .mdd file from the test simulation as a pandas DataFrame

    :return: a pandas DataFrame containing the .mdd file from the test simulation
    """
    mdd_df = pd.read_csv(filepath_or_buffer='available_outputs/eplusout.mdd', sep=',|;', skiprows=2, names=['object', 'meter_name', 'frequency', 'units'], engine='python')
    return mdd_df

class OptimParamSimulation(AnalysisMixin, PlottingMixin):

    def __init__(self, building: IDF_class=None, parameters_type: Literal['accim custom model', 'accim predefined model', 'apmv setpoints', None]=None, output_type: Literal['standard', 'custom', 'detailed', 'simplified']='standard', output_keep_existing: bool=False, output_freqs: List[allowed_output_freqs]=['hourly'], ScriptType: Literal['vrf_mm', 'vrf_ac', 'ex_ac']='vrf_mm', SupplyAirTempInputMethod: Literal['temperature difference', 'supply air temperature']='temperature difference', make_averages: bool=False, debugging: bool=False, verbosemode: bool=True, bypass_addAccis: bool=False):
        """
        Creates a class instance to run parametric simulations and optimisation.

        :param building: the besos.IDF_class returned from method get_building(idfpath)
        :param parameters_type: to specify the type of parameters that should be used:
            can be 'accim custom model', 'accim predefined model', or 'apmv setpoints'
        :param output_type: to specify the outputs that are going to be requested;
            only used in accim predefined and custom models
        :param output_keep_existing: to keep or remove existing outputs;
            only used in accim predefined and custom models
        :param output_freqs: to specify the frequency or frequencies for the outputs; must be a list containing any of
            the following strings: 'timestep', 'hourly', 'daily', 'monthly', 'runperiod'
        :param ScriptType: to specify the ScriptType; must one of the following strings: 'vrf_mm', 'vrf_ac', 'ex_ac';
            for more information, please refer to addAccis()
        :param SupplyAirTempInputMethod: in case 'vrf_mm' or 'vrf_ac' ScriptTypes are used, specifies the supply air
            temperature input method for the VRF systems
        :param make_averages: to make average outputs of hour-counting and operative temperature related outputs
        :param debugging: True to generate the .EDD file
        :param bypass_addAccis: True to skip the internal addAccis execution (useful when loading previous sessions)
        """
        is_accim_predef_model = False
        is_accim_custom_model = False
        is_apmv_setpoints = False
        if parameters_type == 'accim custom model':
            temp_ctrl = 'temperature'
            is_accim_custom_model = True
        elif parameters_type == 'accim predefined model':
            temp_ctrl = 'temperature'
            is_accim_predef_model = True
        elif parameters_type == 'apmv setpoints':
            temp_ctrl = 'PMV'
            is_apmv_setpoints = True
        elif parameters_type is None:
            temp_ctrl = None
        else:
            raise KeyError(f'String {parameters_type} entered in argument parametric_simulation_type is not supported. Valid strings are: "accim custom model", "accim predefined model" or "apmv setpoints".')
        allowed_ScriptType = ['vrf_mm', 'vrf_ac', 'ex_ac']
        if ScriptType not in allowed_ScriptType:
            raise ValueError(f'Invalid ScriptType: {ScriptType}. Allowed values are: {allowed_ScriptType}')
        allowed_SupplyAirTempInputMethod = ['temperature difference', 'supply air temperature']
        if SupplyAirTempInputMethod not in allowed_SupplyAirTempInputMethod:
            raise ValueError(f'Invalid ScriptType: {SupplyAirTempInputMethod}. Allowed values are: {allowed_SupplyAirTempInputMethod}')
        allowed_output_type = ['standard', 'custom', 'detailed', 'simplified']
        if output_type not in allowed_output_type:
            raise ValueError(f'Invalid output_type: {output_type}. Allowed values are: {allowed_output_type}')
        if is_accim_custom_model or is_accim_predef_model:
            self.ScriptType = ScriptType
            self.temp_ctrl = temp_ctrl
            self.SupplyAirTempInputMethod = SupplyAirTempInputMethod
            self.output_keep_existing = output_keep_existing
            self.output_type = output_type
            self.make_averages = make_averages
            if not bypass_addAccis:
                accis.addAccis(idf=building, ScriptType=ScriptType, SupplyAirTempInputMethod=SupplyAirTempInputMethod, Output_keep_existing=output_keep_existing, Output_type=output_type, Output_freqs=output_freqs, TempCtrl=temp_ctrl, make_averages=make_averages, debugging=debugging, verboseMode=verbosemode)
        elif is_apmv_setpoints:
            apmv.apply_apmv_setpoints(building=building, outputs_freq=output_freqs)
            print('Arguments output_type, output_keep_existing, ScriptType, and SupplyAirTempInputMethod are only used in accim predefined and custom models, therefore these will not have any effect in this case.')
        elif parameters_type is None:
            self.ScriptType = None
            self.temp_ctrl = None
            self.SupplyAirTempInputMethod = None
            self.output_keep_existing = None
            self.output_type = None
            self.make_averages = None
        self.building = building
        self.output_freqs = output_freqs
        self.parameters_type = parameters_type
        self.is_accim_custom_model = is_accim_custom_model
        self.is_accim_predef_model = is_accim_predef_model
        self.is_apmv_setpoints = is_apmv_setpoints
        self.last_run_type = None
        self.outputs_optimisation = None
        self.outputs_optimisation_filepath = None
        self.optimisation_csv_paths_non_dominated = []
        self.optimisation_csv_paths_dominated = []
        self.optimisation_csv_paths_non_dominated_by_epw = {}
        self.optimisation_csv_paths_dominated_by_epw = {}
        # Save an initial IDF backup right after addAccis/apply_apmv_setpoints so the
        # modified IDF (with EMS scripts and outputs already injected) is always
        # recoverable, even if run_parametric_simulation / run_optimisation are not called yet.
        self.idf_backup_path: str = None
        if parameters_type is not None and not bypass_addAccis:
            self._save_idf_backup(label='post_setup')

    # ------------------------------------------------------------------
    # IDF backup helpers
    # ------------------------------------------------------------------

    def _save_idf_backup(self, label: str = '', out_dir: str = None) -> str:
        """
        Saves a copy of ``self.building`` to disk as an IDF file and stores
        the path in ``self.idf_backup_path``.

        :param label: optional suffix to embed in the filename.
        :param out_dir: optional directory where the backup should be saved.
        :return: absolute path to the saved IDF.
        """
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if out_dir is None:
            backup_dir = os.path.join(os.getcwd(), 'accim_idf_backups')
        else:
            backup_dir = out_dir
        os.makedirs(backup_dir, exist_ok=True)
        suffix = f'_{label}' if label else ''
        filename = f'accim_idf_backup{suffix}_{timestamp}.idf'
        backup_path = os.path.join(backup_dir, filename)
        self.building.savecopy(backup_path)
        self.idf_backup_path = os.path.abspath(backup_path)
        return self.idf_backup_path

    def get_output_var_df_from_idf(self) -> pd.DataFrame:
        """
        Gets a pandas DataFrame which contains the Output:Variable objects from the idf.
        Therefore, it may contain wildcards such as '*', which means the variable is requested
        for all zones.

        :return: a pandas DataFrame which contains the Output:Variable objects from the idf
        """
        if self.is_accim_custom_model or self.is_accim_predef_model:
            output_variable_df = accis.gen_outputs_df(idf=self.building, ScriptType=self.ScriptType, Output_keep_existing=self.output_keep_existing, Output_type=self.output_type, Output_freqs=self.output_freqs, TempCtrl=self.temp_ctrl, verboseMode=False)
        else:
            output_var_dict = {'key_value': [i.Key_Value for i in self.building.idfobjects['Output:Variable']], 'variable_name': [i.Variable_Name for i in self.building.idfobjects['Output:Variable']], 'frequency': [i.Reporting_Frequency for i in self.building.idfobjects['Output:Variable']], 'schedule_name': [i.Schedule_Name for i in self.building.idfobjects['Output:Variable']]}
            output_variable_df = pd.DataFrame.from_dict(output_var_dict)
        return output_variable_df

    def get_output_meter_df_from_idf(self) -> pd.DataFrame:
        """
        Gets a pandas DataFrame which contains the Output:Meter objects from the idf.

        :return: a pandas DataFrame which contains the Output:Meter objects from the idf
        """
        output_meter_dict = {'key_name': [i.Key_Name for i in self.building.idfobjects['Output:Meter']], 'frequency': [i.Reporting_Frequency for i in self.building.idfobjects['Output:Meter']]}
        output_meter_df = pd.DataFrame.from_dict(output_meter_dict)
        return output_meter_df

    def set_output_var_df_to_idf(self, outputs_df: pd.DataFrame=None):
        """
        Keeps the Output:Variable objects contained in the input pandas DataFrame and removes
        all others. This is important to save space if thousands of simulations with heavy outputs
        are run.

        :type outputs_df: pd.DataFrame
        :param outputs_df: the DataFrame containing Output:Variable objects to be kept
        :return:
        """
        if self.is_accim_custom_model or self.is_accim_predef_model:
            accis.addAccis(idf=self.building, ScriptType=self.ScriptType, SupplyAirTempInputMethod=self.SupplyAirTempInputMethod, Output_keep_existing=self.output_keep_existing, Output_type=self.output_type, Output_take_dataframe=outputs_df, Output_freqs=self.output_freqs, TempCtrl=self.temp_ctrl, make_averages=self.make_averages, verboseMode=False)
        else:
            alloutputs = [output for output in self.building.idfobjects['Output:Variable']]
            for i in alloutputs:
                self.building.removeidfobject(i)
            for i in outputs_df.index:
                self.building.newidfobject('Output:Variable', Key_Value=outputs_df.loc[i, 'key_value'], Variable_Name=outputs_df.loc[i, 'variable_name'], Reporting_Frequency=outputs_df.loc[i, 'frequency'].capitalize(), Schedule_Name=outputs_df.loc[i, 'schedule_name'])

    def set_output_met_objects_to_idf(self, output_meters: list):
        """
        Adds the Output:Meter objects from the output_meters argument.

        :type output_meters: list
        :param output_meters: a list containing Output:Meter objects to be added
        :return:
        """
        for meter in output_meters:
            for freq in self.output_freqs:
                self.building.newidfobject(key='OUTPUT:METER', Key_Name=meter, Reporting_Frequency=freq)

    def get_outputs_df_from_testsim(self, reduce_sim_time: bool=True) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Gets two pandas DataFrames which contain the Output:Variable and Output:Meter objects from a test simulation.
        Therefore, it won't contain wildcards such as '*'.

        :param reduce_sim_time: True to reduce the simulation runtime

        :return: a tuple containing the DataFrames containing Output:Variable and Output:Meter
        """
        building_for_testsim = self.building
        if reduce_sim_time:
            from besos.eppy_funcs import get_building
            self.building.savecopy('temp_reduced_runtime.idf')
            building_for_testsim = get_building('temp_reduced_runtime.idf')
            reduce_runtime(idf_object=building_for_testsim, maximum_figures_in_shadow_overlap_calculations=200, timesteps=2)
        available_outputs = print_available_outputs_mod(building_for_testsim)
        if reduce_sim_time:
            from os import remove
            remove('temp_reduced_runtime.idf')
        df_outputmeters = pd.DataFrame(available_outputs.meterreaderlist, columns=['key_name', 'frequency'])
        df_outputvariables = pd.DataFrame(available_outputs.variablereaderlist, columns=['key_value', 'variable_name', 'frequency'])
        return (df_outputmeters, df_outputvariables)

    def set_outputs_for_simulation(self, df_output_variable: pd.DataFrame=None, df_output_meter: pd.DataFrame=None):
        """
        Sets the outputs for the parametric analysis or optimisation based on the input pandas DataFrames
        for Output:Variable and/or Output:Meter objects. These DataFrames can include columns for the output name
        and the aggregation function (see the 'func' argument of MeterReader and VariableReader classes in besos),
        respectively named 'name' and 'func'. If no 'name' and/or 'func' columns are provided,
        the names will be the variable and meter names, and the hourly values will be summed.

        :param df_output_variable: a pandas DataFrame containing the Output:Variable objects, similar to that one
            returned from method get_outputs_df_from_testsim()
        :param df_output_meter: a pandas DataFrame containing the Output:Meter objects, similar to that one
            returned from method get_outputs_df_from_testsim()
        """
        if df_output_variable is not None:
            df_output_variable['output_name'] = 'temp'
            if 'name' in df_output_variable.columns:
                df_output_variable['output_name'] = df_output_variable['name']
            else:
                df_output_variable['output_name'] = df_output_variable['variable_name']
        if df_output_meter is not None:
            df_output_meter['output_name'] = 'temp'
            if 'name' in df_output_meter.columns:
                df_output_meter['output_name'] = df_output_meter['name']
            else:
                df_output_meter['output_name'] = df_output_meter['key_name']
        objs_meters = []
        if df_output_meter is not None:
            for i in df_output_meter.index:
                if 'func' in [c for c in df_output_meter.columns]:
                    objs_meters.append(MeterReader(key_name=df_output_meter.loc[i, 'key_name'], frequency=df_output_meter.loc[i, 'frequency'], name=df_output_meter.loc[i, 'output_name'], func=df_output_meter.loc[i, 'func']))
                else:
                    objs_meters.append(MeterReader(key_name=df_output_meter.loc[i, 'key_name'], frequency=df_output_meter.loc[i, 'frequency'], name=df_output_meter.loc[i, 'output_name']))
        objs_variables = []
        if df_output_variable is not None:
            for i in df_output_variable.index:
                if 'func' in [c for c in df_output_variable.columns]:
                    objs_variables.append(VariableReader(key_value=df_output_variable.loc[i, 'key_value'], variable_name=df_output_variable.loc[i, 'variable_name'], frequency=df_output_variable.loc[i, 'frequency'], name=df_output_variable.loc[i, 'output_name'], func=df_output_variable.loc[i, 'func']))
                else:
                    objs_variables.append(VariableReader(key_value=df_output_variable.loc[i, 'key_value'], variable_name=df_output_variable.loc[i, 'variable_name'], frequency=df_output_variable.loc[i, 'frequency'], name=df_output_variable.loc[i, 'output_name']))
        self.sim_outputs = objs_meters + objs_variables

    def get_available_parameters(self) -> list:
        """
        Returns a list containing the available parameters depending on the parameters_type argument previously input.

        :return: a list containing the available parameters depending on the parameters_type argument previously input
        """
        if self.is_accim_predef_model:
            available_params = [i for i in params_dicts.accim_predef_model_params.keys()]
        elif self.is_accim_custom_model:
            available_params = [i for i in params_dicts.accim_custom_model_params.keys()]
        elif self.is_apmv_setpoints:
            available_params = [i for i in params_dicts.apmv_setpoints_params.keys()]
        return available_params

    def set_parameters(self, accis_params_dict: dict, additional_params: list=None, use_dflt_values: bool=True):
        """
        Sets the parameters for the parametric analysis or optimisation.

        :param accis_params_dict: a dictionary containing the parameters names in the keys,
            and in the values, the options or range of values using respectively
            a list or tuple with min and max values.
        :param additional_params: any other additional parameter, as it would be added in besos
        :param HVACmode: only used in accim predefined and custom models; sets the HVACmode argument;
            for more information, refer to addAccis
        :param VentCtrl: only used in accim predefined and custom models; sets the VentCtrl argument;
            for more information, refer to addAccis
        """
        accis_descriptors_has_options = False
        add_descriptors_has_options = False
        descriptors_has_options = False
        if all([type(v) == list for v in accis_params_dict.values()]):
            accis_descriptors_has_options = True
        if additional_params is not None:
            if all([type(additional_params[i].value_descriptor) == CategoryParameter for i in range(len(additional_params))]):
                add_descriptors_has_options = True
        if accis_descriptors_has_options:
            if additional_params is not None:
                if add_descriptors_has_options:
                    descriptors_has_options = True
            else:
                descriptors_has_options = True
        if descriptors_has_options is True:
            for (k, v) in accis_params_dict.items():
                accis_params_dict[k] = [round(float(i), 2) for i in v]
        accis_descriptors_has_range = False
        add_descriptors_has_range = False
        descriptors_has_range = False
        if all([type(v) == tuple for v in accis_params_dict.values()]):
            accis_descriptors_has_range = True
        if additional_params is not None:
            if all([type(additional_params[i].value_descriptor) == RangeParameter for i in range(len(additional_params))]):
                add_descriptors_has_range = True
        if accis_descriptors_has_range:
            if additional_params is not None:
                if add_descriptors_has_range:
                    descriptors_has_range = True
            else:
                descriptors_has_range = True
        if descriptors_has_options is False and descriptors_has_range is False:
            raise TypeError('All Descriptors are not CategoryParameters or RangeParameters.')
        parameters = [k for k in accis_params_dict.keys()]
        available_parameters = self.get_available_parameters()
        not_allowed_parameters = []
        for p in parameters:
            if p not in available_parameters:
                not_allowed_parameters.append(p)
        if len(not_allowed_parameters) > 0:
            raise ValueError(f'The following parameters are not allowed in parameters_type {self.parameters_type}: {not_allowed_parameters}')
        if self.is_accim_custom_model:
            bf_accim.modify_ComfStand(self.building, 99)
            bf_accim.modify_ComfMod(self.building, 3)
            bf_accim.modify_CAT(self.building, 80)
            bf_accim.modify_CustAST_m(self.building, 0)
            bf_accim.modify_CustAST_n(self.building, 0)
            bf_accim.modify_CustAST_ASToffset(self.building, 0)
            bf_accim.modify_CustAST_ASTaul(self.building, 0)
            bf_accim.modify_CustAST_ASTall(self.building, 0)
            args = accim.utils.get_accim_args(self.building)
            parameters_to_check = [k for (k, v) in args['CustAST'].items() if 'CustAST_' + k not in parameters and v == 0]
            if 'CustAST_ASToffset' in parameters:
                try:
                    parameters_to_check.remove('AHSToffset')
                    parameters_to_check.remove('ACSToffset')
                except ValueError:
                    pass
            if 'CustAST_ASTall' in parameters:
                try:
                    parameters_to_check.remove('AHSTall')
                    parameters_to_check.remove('ACSTall')
                except ValueError:
                    pass
            if 'CustAST_ASTaul' in parameters:
                try:
                    parameters_to_check.remove('AHSTaul')
                    parameters_to_check.remove('ACSTaul')
                except ValueError:
                    pass
            parameters_to_be_defined = []
            for p in parameters_to_check:
                if args['CustAST'][p] == 0:
                    parameters_to_be_defined.append(p)
            if len(parameters_to_be_defined) > 0:
                print(f'The following parameters are not included in the parameters to be set, and have not been defined yet (i.e. the value is 0): {parameters_to_be_defined}')
                dflt_values = {'m': 0.31, 'n': 17.8, 'ACSToffset': 3.5, 'AHSToffset': -3.5, 'ACSTaul': 33.5, 'ACSTall': 10, 'AHSTaul': 33.5, 'AHSTall': 10}
                if use_dflt_values:
                    print('Default values will be set for these parameters. The default values are:')
                    for p in parameters_to_be_defined:
                        print(f'{p}: {dflt_values[p]}')
                else:
                    print('If you want, default values can be set for these parameters. The default values are:')
                    for p in parameters_to_be_defined:
                        print(f'{p}: {dflt_values[p]}')
                    user_decision = input('Do you want to continue with default values? [y/n]: ')
                    if user_decision.lower() == 'y' or user_decision == '':
                        if 'm' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_m(self.building, dflt_values['m'])
                        if 'n' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_n(self.building, dflt_values['n'])
                        if 'ACSToffset' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSToffset(self.building, dflt_values['ACSToffset'])
                        if 'AHSToffset' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSToffset(self.building, dflt_values['AHSToffset'])
                        if 'ACSTaul' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSTaul(self.building, dflt_values['ACSTaul'])
                        if 'ACSTall' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSTall(self.building, dflt_values['ACSTall'])
                        if 'AHSTaul' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSTaul(self.building, dflt_values['AHSTaul'])
                        if 'AHSTall' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSTall(self.building, dflt_values['AHSTall'])
                    else:
                        user_values = {}
                        for p in parameters_to_be_defined:
                            value = float(input(f'Enter the value for argument {p}: '))
                            user_values.update({p: value})
                        if 'm' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_m(self.building, user_values['m'])
                        if 'n' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_n(self.building, user_values['n'])
                        if 'ACSToffset' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSToffset(self.building, user_values['ACSToffset'])
                        if 'AHSToffset' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSToffset(self.building, user_values['AHSToffset'])
                        if 'ACSTaul' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSTaul(self.building, user_values['ACSTaul'])
                        if 'ACSTall' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSTall(self.building, user_values['ACSTall'])
                        if 'AHSTaul' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSTaul(self.building, user_values['AHSTaul'])
                        if 'AHSTall' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSTall(self.building, user_values['AHSTall'])
        elif self.is_accim_predef_model:
            if descriptors_has_range:
                raise KeyError('Accim predefined models approach is only valid with options descriptors.')
        parameters_list = [params.accis_parameter(k, v) for (k, v) in accis_params_dict.items()]
        if additional_params is not None:
            parameters_list.extend(additional_params)
        self.parameters_list = parameters_list
        self.descriptors_has_options = descriptors_has_options
        self.descriptors_has_range = descriptors_has_range

    def set_problem(self, minimize_outputs: list=None, constraints: list=None, constraint_bounds: list=None, **kwargs):
        """
        Sets the besos EPProblem class instance, using for inputs the parameters previously set in the set_parameters
        method, and for outputs, those set using the set_outputs_for_simulation method.

        :param minimize_outputs: only used in optimisation; a list containing booleans to specify if the outputs must
            be minimized (True), maximized (False), or just show the output (None).
        :param constraints: only used in optimisation;
            a list containing the Output:Meter key names to be considered as constraints
        :param constraint_bounds: only used in optimisation;
            a list containing the logical expressions for the constraints
        """
        problem = EPProblem(inputs=self.parameters_list, outputs=self.sim_outputs, minimize_outputs=minimize_outputs, constraints=constraints, constraint_bounds=constraint_bounds, **kwargs)
        self.problem = problem

    def sampling_full_set(self):
        """
        Combines all values from all parameters and saves it into a pandas DataFrame, stored in an internal variable
        named parameters_values_df.
        """
        from accim.parametric_and_optimisation.utils import make_all_combinations
        if self.descriptors_has_options:
            num_samples = 1
            parameters_values = {}
            for p in self.parameters_list:
                num_samples = num_samples * len(p.value_descriptors[0].options)
                parameters_values.update({p.value_descriptors[0].name: p.value_descriptors[0].options})
            parameters_values_df = make_all_combinations(parameters_values)
        else:
            raise KeyError('sampling_full_set method can only be used with option (i.e. category) descriptors.')
        if self.is_accim_predef_model:
            parameters_values_df = bf_accim.drop_invalid_param_combinations(parameters_values_df)
        self.parameters_values_df = parameters_values_df

    def sampling_full_factorial(self, level: int):
        """
        Split the range of every parameter in the number of parts specified in argument level,
        and saves it into a pandas DataFrame, stored in an internal variable named parameters_values_df.
        For more information, see besos.sampling.dist_sampler and besos.sampling.full_factorial

        :param level: an integer; represents the number of parts to split each parameter's range
        """
        if self.descriptors_has_range:
            parameters_values_df = sampling.dist_sampler(sampling.full_factorial, self.problem, num_samples=2, level=level)
        else:
            raise KeyError('sampling_full_factorial method can only be used with range descriptors.')
        self.parameters_values_df = parameters_values_df

    def sampling_lhs(self, num_samples: int):
        """
        Uses Latin Hypercube Sampling to make samples, where the total number is specified in the num_samples argument,
        and saves it into a pandas DataFrame, stored in an internal variable named parameters_values_df.
        For more information, see besos.sampling.dist_sampler and besos.sampling.lhs

        :param num_samples: an integer; represents the total number of samples
        """
        if self.descriptors_has_range:
            parameters_values_df = sampling.dist_sampler(sampling.lhs, self.problem, num_samples=num_samples)
        else:
            raise KeyError('sampling_lhs method can only be used with range descriptors.')
        self.parameters_values_df = parameters_values_df

    def _get_salib_problem(self) -> dict:
        """
        Internal method to build the SALib problem dictionary based on besos parameters.
        """
        names = self.problem.names('inputs')
        bounds = []
        from besos.parameters import RangeParameter
        for inp in self.problem.inputs:
            desc = inp.value_descriptors[0]
            if not isinstance(desc, RangeParameter):
                raise ValueError(f'Parameter {inp.name} must be a RangeParameter for Sensitivity Analysis.')
            bounds.append([desc.min, desc.max])
        problem = {'num_vars': len(names), 'names': names, 'bounds': bounds}
        return problem

    def sampling_sobol(self, num_samples: int=128):
        """
        Uses Saltelli's extension of the Sobol sequence to generate samples for Sensitivity Analysis.
        The samples are saved into a pandas DataFrame, stored in an internal variable named parameters_values_df.
        Requires SALib to be installed.

        :param num_samples: an integer; represents the number of samples to generate.
            The total number of samples generated will be num_samples * (2 * num_vars + 2).
            For Sobol, num_samples should preferably be a power of 2 (e.g. 64, 128, 256, 512, 1024).
        """
        if not self.descriptors_has_range:
            raise KeyError('sampling_sobol method can only be used with range descriptors.')
        try:
            from SALib.sample import saltelli
        except ImportError:
            raise ImportError('SALib is required for Sensitivity Analysis. Install it with: pip install SALib')
        problem = self._get_salib_problem()
        samples = saltelli.sample(problem, num_samples)
        self.parameters_values_df = pd.DataFrame(samples, columns=problem['names'])

    def sampling_morris(self, num_samples: int=100, num_levels: int=4):
        """
        Uses Morris' method to generate samples for Sensitivity Analysis.
        The samples are saved into a pandas DataFrame, stored in an internal variable named parameters_values_df.
        Requires SALib to be installed.

        :param num_samples: an integer; represents the number of trajectories (N).
            The total number of samples generated will be num_samples * (num_vars + 1).
        :param num_levels: number of grid levels.
        """
        if not self.descriptors_has_range:
            raise KeyError('sampling_morris method can only be used with range descriptors.')
        try:
            from SALib.sample import morris as morris_sampler
        except ImportError:
            raise ImportError('SALib is required for Sensitivity Analysis. Install it with: pip install SALib')
        problem = self._get_salib_problem()
        samples = morris_sampler.sample(problem, N=num_samples, num_levels=num_levels)
        self.parameters_values_df = pd.DataFrame(samples, columns=problem['names'])

    def set_evaluator(self, epw: str, out_dir: str) -> besos.evaluator.EvaluatorEP:
        """
        Used internally for setting the evaluator in run_parametric_simulation and run_optimisation methods.

        :param epw: The epw file name
        :param out_dir: The name of the output directory to save the results.
        :return: the besos.evaluator.EvaluatorEP class instance
        """
        evaluator = EvaluatorEP(problem=self.problem, building=self.building, epw=epw, out_dir=out_dir)
        return evaluator

    def run_parametric_simulation(self, epws: list, out_dir: str, df: pd.DataFrame, processes: int=2, keep_input: bool=True, keep_dirs: bool=True) -> pd.DataFrame:
        """
        Runs the parametric simulation.

        :param epws: a list of .epw filenames
        :param out_dir: the name of the directory to store the outputs
        :param df: a pandas DataFrame which contains the values of the parameters to simulate
        :param processes: the number of CPUs to be used in simulation
        :param keep_input: True to keep the input DataFrame in the results
        :param keep_dirs: True to keep the simulation results
        :return: a pandas DataFrame
        """
        outputs_dict = {}
        evaluators = {}
        for epw in epws:
            epwname = epw.split('.epw')[0]
            evaluator = self.set_evaluator(epw=epw, out_dir=out_dir)
            outputs = evaluator.df_apply(df=df, keep_input=keep_input, keep_dirs=keep_dirs, processes=processes)
            outputs['epw'] = epwname
            outputs_dict.update({epwname: outputs})
            evaluators.update({epwname: evaluator})
        outputs_param_simulation = pd.concat([df for df in outputs_dict.values()])
        if len(epws) > 1:
            outputs_param_simulation = outputs_param_simulation.reset_index()
        if hasattr(self, 'problem') and hasattr(self.problem, 'names'):
            outputs_param_simulation.attrs['parameters_names'] = self.problem.names('inputs')
            outputs_param_simulation.attrs['outputs_names'] = self.problem.names('outputs')
        elif hasattr(self, 'parameters_names') and hasattr(self, 'outputs_names'):
            outputs_param_simulation.attrs['parameters_names'] = self.parameters_names
            outputs_param_simulation.attrs['outputs_names'] = self.outputs_names
        self.outputs_param_simulation = outputs_param_simulation
        self.evaluators = evaluators
        os.makedirs(out_dir, exist_ok=True)
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        # Update the IDF backup with the exact building state used for this run
        self._save_idf_backup(label='pre_parametric', out_dir=out_dir)
        # Embed the backup path and epws in attrs so they survive pickle serialisation
        self.outputs_param_simulation.attrs['idf_backup_path'] = self.idf_backup_path
        self.outputs_param_simulation.attrs['epws'] = epws
        _base = os.path.join(out_dir, f'outputs_param_simulation_{timestamp}')
        self.outputs_param_simulation.to_csv(f'{_base}.csv', index=False)
        self.outputs_param_simulation.to_pickle(f'{_base}.pkl')
        import json as _json
        _json_payload = {
            'attrs': self.outputs_param_simulation.attrs,
            'data': self.outputs_param_simulation.to_dict(orient='list'),
            'idf_backup_path': self.idf_backup_path,
        }
        with open(f'{_base}.json', 'w', encoding='utf-8') as _f:
            _json.dump(_json_payload, _f, indent=2, default=str)
        self.outputs_param_simulation_filepath = f'{_base}.csv'
        self.epws = self.outputs_param_simulation.attrs.get('epws', [])
        self.last_run_type = 'parametric'

    def load_outputs_parametric(self, csv_path: str=None, pickle_path: str=None, json_path: str=None, hourly_csv_path: str=None, hourly_pickle_path: str=None, parameters_names: list=None, outputs_names: list=None) -> pd.DataFrame:
        """
        Loads outputs of a previous parametric simulation from a CSV, Pickle, or JSON file.
        This allows you to resume a parametric session without rerunning the simulations.
        
        :param csv_path: path to the CSV file containing parametric simulation results.
        :param pickle_path: path to the Pickle file containing parametric simulation results (recommended).
        :param json_path: path to the JSON file containing parametric simulation results (human-readable).
        :param hourly_csv_path: path to the CSV file containing hourly parametric simulation results.
        :param hourly_pickle_path: path to the Pickle file containing hourly parametric simulation results.
        :param parameters_names: optional list of parameter names to reconstruct the internal problem object.
        :param outputs_names: optional list of output names to reconstruct the internal problem object.
        :return: pandas DataFrame containing the loaded parametric simulation outputs.
        """
        import pandas as pd
        if not csv_path and (not pickle_path) and (not json_path):
            raise ValueError('A valid csv_path, pickle_path, or json_path must be provided.')
        if pickle_path:
            self.outputs_param_simulation = pd.read_pickle(pickle_path)
            # Restore idf_backup_path from attrs if it was embedded at save time
            _ibp = self.outputs_param_simulation.attrs.get('idf_backup_path')
            if _ibp:
                self.idf_backup_path = _ibp
                print(f'  [info] idf_backup_path restored: {self.idf_backup_path}')
        elif json_path:
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            self.outputs_param_simulation = pd.DataFrame(payload['data'])
            for (k, v) in payload.get('attrs', {}).items():
                self.outputs_param_simulation.attrs[k] = v
            # Restore the IDF backup path stored at save time
            if payload.get('idf_backup_path'):
                self.idf_backup_path = payload['idf_backup_path']
                print(f'  [info] idf_backup_path restored: {self.idf_backup_path}')
        else:
            self.outputs_param_simulation = pd.read_csv(csv_path)
        if hourly_pickle_path:
            self.outputs_param_simulation_hourly = pd.read_pickle(hourly_pickle_path)
        elif hourly_csv_path:
            self.outputs_param_simulation_hourly = pd.read_csv(hourly_csv_path)
        parameters_names = parameters_names or self.outputs_param_simulation.attrs.get('parameters_names')
        outputs_names = outputs_names or self.outputs_param_simulation.attrs.get('outputs_names')
        if parameters_names and outputs_names and not (hasattr(self, 'problem') and type(self.problem).__name__ != 'MockProblem'):

            class MockProblem:

                def __init__(self, inputs, outputs):
                    self._inputs = inputs
                    self._outputs = outputs

                def names(self, typ):
                    if typ == 'inputs':
                        return self._inputs
                    elif typ == 'outputs':
                        return self._outputs
            self.problem = MockProblem(parameters_names, outputs_names)
            self.parameters_names = parameters_names
            self.outputs_names = outputs_names
        self.epws = self.outputs_param_simulation.attrs.get('epws', [])
        self.last_run_type = 'parametric'
        return self.outputs_param_simulation

    def estimate_optimisation_sims(self, evaluations: int, population_size: int, epws: list) -> int:
        """
        Estimates the maximum number of EnergyPlus simulations that will be run by
        :meth:`run_optimisation` **before** launching it.

        NSGA-II (and most platypus algorithms) work in discrete generations, each of which
        evaluates exactly ``population_size`` individuals.  The stopping criterion
        ``evaluations`` is checked **between** generations, so the algorithm always
        completes the current generation before stopping.  Therefore:

        .. code-block:: text

            sims_per_epw = population_size × ⌈evaluations / population_size⌉
            total_sims   = sims_per_epw × len(epws)

        Special case: if ``evaluations < population_size`` the initial generation
        already exceeds the budget, but it is always completed in full, so
        ``sims_per_epw`` equals ``population_size``.

        :param evaluations: same value you will pass to :meth:`run_optimisation`
        :param population_size: same value you will pass to :meth:`run_optimisation`
        :param epws: same list you will pass to :meth:`run_optimisation`
        :return: estimated total number of EnergyPlus simulations
        """
        import math
        sims_per_epw = population_size * math.ceil(evaluations / population_size)
        total = sims_per_epw * len(epws)
        print(f"Estimated simulations\n  evaluations    : {evaluations}\n  population_size: {population_size}\n  EPWs           : {len(epws)} ({', '.join(epws)})\n  sims per EPW   : {sims_per_epw}  ({math.ceil(evaluations / population_size)} generation(s) × {population_size})\n  TOTAL          : {total}")
        self.epws = self.outputs_param_simulation.attrs.get('epws', [])
        self.last_run_type = 'parametric'
        return total

    def run_optimisation(self, epws: list, out_dir: str, evaluations: int, population_size: int, algorithm: str='NSGAII', processes: int=1, keep_sim_files: Literal['all', 'non-dominated', 'none']='all', keep_sim_files_batch_size: int=50, keep_df: Literal['all', 'non-dominated']='all', **kwargs) -> pd.DataFrame:
        """
        Runs the optimisation.

        :param epws: a list of .epw filenames
        :param out_dir: the directory name to save the outputs
        :param evaluations: the algorithm will be stopped once it uses more than this many
            evaluations (i.e. EnergyPlus simulations).  Because the algorithm always completes
            the current generation before stopping, the actual number of simulations per EPW
            is ``population_size × ⌈evaluations / population_size⌉``.
            Use :meth:`estimate_optimisation_sims` to preview the count before running.
        :param population_size: number of individuals in each generation; each individual
            corresponds to one EnergyPlus simulation
        :param algorithm: the optimisation algorithm to use; default is 'NSGAII'
        :param processes: number of CPU cores to use for parallel evaluation of individuals
            within each generation.  Uses ``platypus.ProcessPoolEvaluator`` internally.
            Default is 1 (sequential).  Values > 1 are useful when ``population_size`` is
            large and each simulation is independent.
        :param keep_sim_files: specifies which simulation results directories to keep:
            'all' (keeps everything), 'non-dominated' (deletes directories of dominated solutions to save space),
            or 'none' (keeps no simulation files).
        :param keep_sim_files_batch_size: number of evaluations per worker to wait before running the local pareto batch cleanup.
        :param keep_df: specifies which evaluations to keep in the outputs_optimisation DataFrame:
            'all' (keeps dominated and non-dominated) or 'non-dominated'.
        :return: a pandas DataFrame
        """
        self.epws = epws
        available_algorithms = ['GeneticAlgorithm', 'EvolutionaryStrategy', 'NSGAII', 'EpsMOEA', 'GDE3', 'SPEA2', 'MOEAD', 'NSGAIII', 'ParticleSwarm', 'OMOPSO', 'SMPSO', 'CMAES', 'IBEA', 'PAES', 'PESA2', 'EpsNSGAII']
        outputs_dict = {}
        full_outputs_dict = {}
        evaluators = {}
        os.makedirs(out_dir, exist_ok=True)
        from besos.evaluator import AbstractEvaluator
        if not hasattr(AbstractEvaluator, '_original_to_platypus'):
            AbstractEvaluator._original_to_platypus = AbstractEvaluator.to_platypus
        AbstractEvaluator.to_platypus = _patched_to_platypus
        if processes > 1:
            import platypus
            from platypus.config import PlatypusConfig
            original_evaluator = PlatypusConfig.default_evaluator
            platypus_evaluator = platypus.ProcessPoolEvaluator(processes)
            PlatypusConfig.default_evaluator = platypus_evaluator
        try:
            for epw in epws:
                evaluator = self.set_evaluator(epw=epw, out_dir=out_dir)
                evaluator._keep_sim_files = keep_sim_files
                evaluator._keep_sim_files_batch_size = keep_sim_files_batch_size
                evaluator._keep_dirs = False if keep_sim_files == 'none' else True
                evaluator._optimisation_eval_records = []
                epwname = epw.split('.epw')[0]
                evaluator._optimisation_log_base = os.path.join(out_dir, f'optim_eval_log_{epwname}_{os.getpid()}')
                for log_file in pyglob.glob(f'{evaluator._optimisation_log_base}_*.jsonl'):
                    try:
                        os.remove(log_file)
                    except OSError:
                        pass
                if processes > 1 and hasattr(evaluator, '_building') and hasattr(evaluator._building, 'idfobjects'):
                    evaluator._building.idfobjects = GlobalAllCapsDict(evaluator._building.idfobjects)
                if algorithm == 'GeneticAlgorithm':
                    outputs_optimisation = optimizer.GeneticAlgorithm(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'EvolutionaryStrategy':
                    outputs_optimisation = optimizer.EvolutionaryStrategy(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'NSGAII':
                    outputs_optimisation = optimizer.NSGAII(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'EpsMOEA':
                    outputs_optimisation = optimizer.EpsMOEA(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'GDE3':
                    outputs_optimisation = optimizer.GDE3(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'SPEA2':
                    outputs_optimisation = optimizer.SPEA2(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'MOEAD':
                    outputs_optimisation = optimizer.MOEAD(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'NSGAIII':
                    outputs_optimisation = optimizer.NSGAIII(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'ParticleSwarm':
                    outputs_optimisation = optimizer.ParticleSwarm(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'OMOPSO':
                    outputs_optimisation = optimizer.OMOPSO(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'SMPSO':
                    outputs_optimisation = optimizer.SMPSO(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'CMAES':
                    outputs_optimisation = optimizer.CMAES(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'IBEA':
                    outputs_optimisation = optimizer.IBEA(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'PAES':
                    outputs_optimisation = optimizer.PAES(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'PESA2':
                    outputs_optimisation = optimizer.PESA2(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'EpsNSGAII':
                    outputs_optimisation = optimizer.EpsNSGAII(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                else:
                    raise KeyError(f'Input algorithm {algorithm} not found. Available algorithms are: {available_algorithms}')
                outputs_optimisation['epw'] = epwname
                outputs_dict.update({epwname: outputs_optimisation})
                full_outputs_optimisation = self._build_full_optimisation_outputs_df(evaluator=evaluator, epwname=epwname)
                full_outputs_dict.update({epwname: full_outputs_optimisation})
                evaluators.update({epwname: evaluator})
        finally:
            if processes > 1:
                platypus_evaluator.close()
                PlatypusConfig.default_evaluator = original_evaluator
                if hasattr(AbstractEvaluator, '_original_to_platypus'):
                    AbstractEvaluator.to_platypus = AbstractEvaluator._original_to_platypus
        outputs_optimisation_non_dominated = pd.concat([df for df in outputs_dict.values()])
        if len(epws) > 1:
            outputs_optimisation_non_dominated = outputs_optimisation_non_dominated.reset_index()
        outputs_optimisation = pd.concat([df for df in full_outputs_dict.values()])
        if len(epws) > 1:
            outputs_optimisation = outputs_optimisation.reset_index(drop=True)
        outputs_optimisation = self._annotate_pareto_status(outputs_optimisation_full=outputs_optimisation, outputs_optimisation=outputs_optimisation_non_dominated)
        if keep_sim_files == 'non-dominated':
            import shutil
            for (idx, row) in outputs_optimisation[~outputs_optimisation['pareto-optimal']].iterrows():
                sim_dir = row.get('simulation_directory')
                if pd.notna(sim_dir) and isinstance(sim_dir, str) and os.path.exists(sim_dir):
                    try:
                        shutil.rmtree(sim_dir)
                    except Exception:
                        pass
                outputs_optimisation.at[idx, 'simulation_directory'] = pd.NA
                outputs_optimisation.at[idx, 'simulation_output_csv_path'] = pd.NA
        elif keep_sim_files == 'none':
            import shutil
            import glob
            worker_dirs = glob.glob(os.path.join(out_dir, 'BESOS_Output*'))
            for w_dir in worker_dirs:
                if os.path.isdir(w_dir):
                    try:
                        shutil.rmtree(w_dir)
                    except Exception:
                        pass
            log_files = glob.glob(os.path.join(out_dir, 'optim_eval_log_*.jsonl'))
            for log_file in log_files:
                try:
                    os.remove(log_file)
                except OSError:
                    pass
            outputs_optimisation['simulation_directory'] = pd.NA
            outputs_optimisation['simulation_output_csv_path'] = pd.NA
        if keep_df == 'non-dominated':
            outputs_optimisation = outputs_optimisation[outputs_optimisation['pareto-optimal']].copy()
            if len(epws) > 1:
                outputs_optimisation = outputs_optimisation.reset_index(drop=True)
        self._set_optimisation_outputs(outputs_optimisation_full=outputs_optimisation, outputs_optimisation_non_dominated=outputs_optimisation_non_dominated)
        self._save_outputs_optimisation_full(out_dir=out_dir)
        self.epws = self.outputs_optimisation.attrs.get('epws', [])
        self.last_run_type = 'optimisation'
        self.evaluators = evaluators

    def _build_full_optimisation_outputs_df(self, evaluator: EvaluatorEP, epwname: str) -> pd.DataFrame:
        records = getattr(evaluator, '_optimisation_eval_records', [])
        if len(records) == 0:
            log_base = getattr(evaluator, '_optimisation_log_base', None)
            if log_base is not None:
                log_files = pyglob.glob(f'{log_base}_*.jsonl')
                for log_file in log_files:
                    with open(log_file, 'r', encoding='utf-8') as logfile:
                        for line in logfile:
                            payload = json.loads(line)
                            records.append({'inputs': tuple(payload['inputs']), 'results': tuple(payload['results']), 'sim_dir': payload['sim_dir']})
        input_names = evaluator.problem.names('inputs')
        output_names = evaluator.problem.names('outputs')
        constraint_names = evaluator.problem.names('constraints')
        rows = []
        for record in records:
            row = {}
            for (idx, input_name) in enumerate(input_names):
                row[input_name] = record['inputs'][idx]
            for (idx, output_name) in enumerate(output_names):
                row[output_name] = record['results'][idx]
            for (idx, constraint_name) in enumerate(constraint_names):
                row[constraint_name] = record['results'][len(output_names) + idx]
            if record['sim_dir'] is not None:
                row['simulation_directory'] = record['sim_dir']
                row['simulation_output_csv_path'] = os.path.join(record['sim_dir'], 'eplusout.csv')
            else:
                row['simulation_directory'] = None
                row['simulation_output_csv_path'] = None
            row['epw'] = epwname
            rows.append(row)
        full_df = pd.DataFrame(rows)
        required_columns = ['simulation_directory', 'simulation_output_csv_path', 'epw']
        for col in required_columns:
            if col not in full_df.columns:
                full_df[col] = pd.Series(dtype=object)
        return full_df

    @staticmethod
    def _make_match_key(df: pd.DataFrame, match_columns: list) -> pd.Series:
        key_df = df[match_columns].copy()
        for column in match_columns:
            if pd.api.types.is_numeric_dtype(key_df[column]):
                key_df[column] = key_df[column].astype(float).round(12)
            key_df[column] = key_df[column].astype(str)
        return key_df.apply(lambda row: '|'.join(row.values.tolist()), axis=1)

    def _annotate_pareto_status(self, outputs_optimisation_full: pd.DataFrame, outputs_optimisation: pd.DataFrame) -> pd.DataFrame:
        """
        Recomputes the Pareto front from scratch using the objective values
        directly on the full evaluation history, grouped per EPW.

        This approach is more reliable than matching against the final NSGA-II
        population (which only contains the last generation), avoiding both
        false negatives caused by points evaluated in earlier generations that
        are genuinely non-dominated, and floating-point matching issues.
        """
        if outputs_optimisation_full.empty:
            outputs_optimisation_full['pareto-optimal'] = pd.Series(dtype=bool)
            return outputs_optimisation_full
        output_names = self.problem.names('outputs')
        minimize_outputs = getattr(self.problem, 'minimize_outputs', None)
        if minimize_outputs is None:
            minimize_flags = [True] * len(output_names)
        else:
            minimize_flags = [m if m is not None else True for m in minimize_outputs]

        def _is_pareto_optimal(costs: np.ndarray) -> np.ndarray:
            """
            Return a boolean mask of length n where True means the row is
            Pareto-non-dominated (all objectives already in minimisation space).

            Solution i is dominated iff there exists j such that:
              j <= i on ALL objectives  AND  j < i on AT LEAST ONE objective.
            """
            n = costs.shape[0]
            is_pareto = np.ones(n, dtype=bool)
            for i in range(n):
                if not is_pareto[i]:
                    continue
                others_mask = np.arange(n) != i
                dominated_i = np.all(costs[others_mask] <= costs[i], axis=1) & np.any(costs[others_mask] < costs[i], axis=1)
                if np.any(dominated_i):
                    is_pareto[i] = False
            return is_pareto

        def _pareto_mask_for_group(group: pd.DataFrame) -> pd.Series:
            """Compute Pareto mask for a single EPW group."""
            objective_data = group[output_names].values.astype(float)
            for (j, minimise) in enumerate(minimize_flags):
                if not minimise:
                    objective_data[:, j] = -objective_data[:, j]
            mask = _is_pareto_optimal(objective_data)
            return pd.Series(mask, index=group.index)
        pareto_mask = pd.Series(False, index=outputs_optimisation_full.index)
        if 'epw' in outputs_optimisation_full.columns and outputs_optimisation_full['epw'].notna().any():
            for (epw, group) in outputs_optimisation_full.groupby('epw'):
                pareto_mask.loc[group.index] = _pareto_mask_for_group(group)
        else:
            pareto_mask = _pareto_mask_for_group(outputs_optimisation_full)
        outputs_optimisation_full['pareto-optimal'] = pareto_mask
        return outputs_optimisation_full

    def _set_optimisation_outputs(self, outputs_optimisation_full: pd.DataFrame, outputs_optimisation_non_dominated: pd.DataFrame=None):
        if 'pareto-optimal' not in outputs_optimisation_full.columns:
            raise KeyError("Column 'pareto-optimal' is required in outputs_optimisation_full.")
        if 'simulation_output_csv_path' not in outputs_optimisation_full.columns:
            outputs_optimisation_full['simulation_output_csv_path'] = pd.NA
        if 'epw' not in outputs_optimisation_full.columns:
            outputs_optimisation_full['epw'] = pd.NA
        if outputs_optimisation_non_dominated is not None and 'epw' in outputs_optimisation_non_dominated.columns and outputs_optimisation_full['epw'].isna().all() and (len(outputs_optimisation_non_dominated['epw'].dropna().unique()) == 1):
            outputs_optimisation_full['epw'] = outputs_optimisation_non_dominated['epw'].dropna().iloc[0]
        if outputs_optimisation_full.empty and outputs_optimisation_non_dominated is not None:
            fallback_full = outputs_optimisation_non_dominated.copy()
            if 'pareto-optimal' not in fallback_full.columns:
                fallback_full['pareto-optimal'] = True
            if 'simulation_output_csv_path' not in fallback_full.columns:
                fallback_full['simulation_output_csv_path'] = pd.NA
            if 'simulation_directory' not in fallback_full.columns:
                fallback_full['simulation_directory'] = pd.NA
            outputs_optimisation_full = fallback_full
        if hasattr(self, 'problem') and hasattr(self.problem, 'names'):
            outputs_optimisation_full.attrs['parameters_names'] = self.problem.names('inputs')
            outputs_optimisation_full.attrs['outputs_names'] = self.problem.names('outputs')
            outputs_optimisation_full.attrs['minimize_outputs'] = getattr(self.problem, 'minimize_outputs', [])
        elif hasattr(self, 'parameters_names') and hasattr(self, 'outputs_names'):
            outputs_optimisation_full.attrs['parameters_names'] = self.parameters_names
            outputs_optimisation_full.attrs['outputs_names'] = self.outputs_names
            outputs_optimisation_full.attrs['minimize_outputs'] = getattr(self.problem, 'minimize_outputs', []) if hasattr(self, 'problem') else []
        self.outputs_optimisation = outputs_optimisation_full
        if 'epw' not in self.outputs_optimisation.columns:
            self.outputs_optimisation['epw'] = pd.NA
        self.optimisation_csv_paths_non_dominated = self.outputs_optimisation[self.outputs_optimisation['pareto-optimal']]['simulation_output_csv_path'].dropna().drop_duplicates().tolist()
        self.optimisation_csv_paths_non_dominated_by_epw = {}
        self.optimisation_csv_paths_dominated_by_epw = {}
        if 'epw' in outputs_optimisation_full.columns:
            non_dominated_df = outputs_optimisation_full[outputs_optimisation_full['pareto-optimal']].copy()
            dominated_df = outputs_optimisation_full[~outputs_optimisation_full['pareto-optimal']].copy()
            epws = sorted({str(epw) for epw in outputs_optimisation_full['epw'].dropna().unique().tolist()})
            for epw in epws:
                self.optimisation_csv_paths_non_dominated_by_epw[epw] = non_dominated_df.loc[non_dominated_df['epw'].astype(str) == epw, 'simulation_output_csv_path'].dropna().drop_duplicates().tolist()
                self.optimisation_csv_paths_dominated_by_epw[epw] = dominated_df.loc[dominated_df['epw'].astype(str) == epw, 'simulation_output_csv_path'].dropna().drop_duplicates().tolist()
        self.optimisation_csv_paths_dominated = outputs_optimisation_full[~outputs_optimisation_full['pareto-optimal']]['simulation_output_csv_path'].dropna().drop_duplicates().tolist()

    def _save_outputs_optimisation_full(self, out_dir: str):
        import json
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs(out_dir, exist_ok=True)
        # Update the IDF backup with the exact building state used for this optimisation run
        self._save_idf_backup(label='pre_optimisation', out_dir=out_dir)
        # Embed the backup path and epws in attrs so they survive pickle serialisation
        self.outputs_optimisation.attrs['idf_backup_path'] = self.idf_backup_path
        self.outputs_optimisation.attrs['epws'] = getattr(self, 'epws', [])
        full_results_filename = f'outputs_optimisation_{timestamp}'
        full_results_path = os.path.join(out_dir, f'{full_results_filename}.csv')
        self.outputs_optimisation.to_csv(full_results_path, index=False)
        self.outputs_optimisation.to_pickle(os.path.join(out_dir, f'{full_results_filename}.pkl'))
        json_payload = {
            'attrs': self.outputs_optimisation.attrs,
            'data': self.outputs_optimisation.to_dict(orient='list'),
            'idf_backup_path': self.idf_backup_path,
        }
        with open(os.path.join(out_dir, f'{full_results_filename}.json'), 'w', encoding='utf-8') as f:
            json.dump(json_payload, f, indent=2, default=str)
        self.outputs_optimisation_filepath = full_results_path

    def load_outputs_optimisation(self, csv_path: str=None, pickle_path: str=None, json_path: str=None, hourly_csv_path: str=None, hourly_pickle_path: str=None, parameters_names: list=None, outputs_names: list=None, minimize_outputs: list=None) -> pd.DataFrame:
        """
        Loads full optimisation outputs (dominated + non-dominated) from a CSV, Pickle, or JSON file
        previously generated by :meth:`run_optimisation`, and rebuilds the related
        internal attributes without rerunning simulations.

        :param csv_path: path to a CSV file with full optimisation outputs.
        :param pickle_path: path to a Pickle file with full optimisation outputs (recommended).
        :param json_path: path to a JSON file with full optimisation outputs (human-readable).
        :param hourly_csv_path: path to a CSV file with hourly optimisation outputs.
        :param hourly_pickle_path: path to a Pickle file with hourly optimisation outputs.
        :param parameters_names: optional list of parameter names to reconstruct the internal problem object.
        :param outputs_names: optional list of output names to reconstruct the internal problem object.
        :param minimize_outputs: optional list of booleans indicating if outputs should be minimized.
        :return: pandas DataFrame containing full optimisation outputs (dominated + non-dominated)
        """
        target_path = pickle_path or json_path or csv_path or self.outputs_optimisation_filepath
        if target_path is None:
            raise ValueError('No path was provided and no previous outputs_optimisation file is available. Run run_optimisation first or provide a valid csv_path/pickle_path/json_path.')
        if pickle_path or str(target_path).endswith('.pkl') or str(target_path).endswith('.pickle'):
            outputs_optimisation = pd.read_pickle(target_path)
            # Restore idf_backup_path from attrs if it was embedded at save time
            _ibp = outputs_optimisation.attrs.get('idf_backup_path')
            if _ibp:
                self.idf_backup_path = _ibp
                print(f'  [info] idf_backup_path restored: {self.idf_backup_path}')
        elif json_path or str(target_path).endswith('.json'):
            import json
            with open(target_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            outputs_optimisation = pd.DataFrame(payload['data'])
            for (k, v) in payload.get('attrs', {}).items():
                outputs_optimisation.attrs[k] = v
            # Restore the IDF backup path stored at save time
            if payload.get('idf_backup_path'):
                self.idf_backup_path = payload['idf_backup_path']
                print(f'  [info] idf_backup_path restored: {self.idf_backup_path}')
        else:
            outputs_optimisation = pd.read_csv(target_path)
        if 'pareto-optimal' not in outputs_optimisation.columns:
            raise KeyError("Column 'pareto-optimal' not found in the provided file. Please load a file generated from outputs_optimisation.")
        self.outputs_optimisation_filepath = target_path
        self._set_optimisation_outputs(outputs_optimisation_full=outputs_optimisation)
        if hourly_pickle_path:
            self.outputs_optimisation_hourly = pd.read_pickle(hourly_pickle_path)
        elif hourly_csv_path:
            self.outputs_optimisation_hourly = pd.read_csv(hourly_csv_path)
        parameters_names = parameters_names or outputs_optimisation.attrs.get('parameters_names')
        outputs_names = outputs_names or outputs_optimisation.attrs.get('outputs_names')
        minimize_outputs = minimize_outputs or outputs_optimisation.attrs.get('minimize_outputs')
        if parameters_names and outputs_names and not (hasattr(self, 'problem') and type(self.problem).__name__ != 'MockProblem'):

            class MockProblem:

                def __init__(self, inputs, outputs, minimize_flags):
                    self._inputs = inputs
                    self._outputs = outputs
                    self.minimize_outputs = minimize_flags

                def names(self, typ):
                    if typ == 'inputs':
                        return self._inputs
                    elif typ == 'outputs':
                        return self._outputs
            self.problem = MockProblem(parameters_names, outputs_names, minimize_outputs)
            self.parameters_names = parameters_names
            self.outputs_names = outputs_names
        self.epws = self.outputs_optimisation.attrs.get('epws', [])
        self.last_run_type = 'optimisation'
        return self.outputs_optimisation

    def get_hourly_df(self, start_date: str='2024-01-01 01'):
        """
        Transforms the hourly values of outputs_param_simulation to a new pandas DataFrame, saved in the
         internal variable named outputs_param_simulation_hourly.

        :param start_date: the start date for the simulation results, in format 'YYY-MM-DD HH'
        """
        if hasattr(self, 'parameters_list'):
            parameter_columns = [i.name for i in self.parameters_list]
        elif hasattr(self, 'problem') and hasattr(self.problem, 'names'):
            parameter_columns = self.problem.names('inputs')
        elif hasattr(self, 'outputs_param_simulation') and self.outputs_param_simulation.attrs.get('parameters_names'):
            parameter_columns = list(self.outputs_param_simulation.attrs['parameters_names'])
        else:
            parameter_columns = []
        if 'epw' not in parameter_columns:
            parameter_columns.append('epw')
        parameter_columns = [c for c in parameter_columns if c in self.outputs_param_simulation.columns]
        self.outputs_param_simulation_hourly = expand_to_hourly_dataframe(df=self.outputs_param_simulation, parameter_columns=parameter_columns, start_date=start_date)

    @staticmethod
    def _resolve_simulation_file_path(row: pd.Series, file_source: Literal['csv', 'eso']) -> str:
        error_msg = f"{file_source.upper()} path cannot be resolved for this simulation. If you used keep_sim_files='non-dominated' and this is a dominated simulation, the files were deleted to save space. To analyze this simulation, re-run keeping its files."
        if file_source == 'csv':
            if pd.notna(row.get('simulation_output_csv_path', pd.NA)):
                return str(row['simulation_output_csv_path'])
            if pd.notna(row.get('simulation_directory', pd.NA)):
                return os.path.join(str(row['simulation_directory']), 'eplusout.csv')
            raise ValueError(error_msg)
        if file_source == 'eso':
            if pd.notna(row.get('simulation_directory', pd.NA)):
                return os.path.join(str(row['simulation_directory']), 'eplusout.eso')
            if pd.notna(row.get('simulation_output_csv_path', pd.NA)):
                csv_path = str(row['simulation_output_csv_path'])
                return os.path.join(os.path.dirname(csv_path), 'eplusout.eso')
            raise ValueError(error_msg)
        raise ValueError(f"Unsupported file_source '{file_source}'. Use 'csv' or 'eso'.")

    @staticmethod
    def _flatten_eso_column_name(col: tuple) -> str:
        (area, variable, units) = col
        return f'{variable} [{units}] | {area}'

    def _extract_hourly_outputs_from_file(self, row: pd.Series, file_source: Literal['csv', 'eso'], file_output_columns: Optional[List[str]]=None, eplus_install_dir: Optional[str]=None, only_run_period: bool=True) -> dict:
        path = self._resolve_simulation_file_path(row=row, file_source=file_source)
        if not os.path.exists(path):
            raise FileNotFoundError(f'Simulation output file not found: {path}')
        if file_source == 'csv':
            df_file = pd.read_csv(path)
            excluded_columns = {'Date/Time', 'date/time'}
            numeric_cols = [c for c in df_file.columns if c not in excluded_columns and pd.api.types.is_numeric_dtype(df_file[c])]
            if file_output_columns is None:
                selected_cols = numeric_cols
            else:
                selected_cols = []
                missing = []
                lower_exact_map = {c.lower(): c for c in df_file.columns}
                for requested in file_output_columns:
                    if requested in df_file.columns:
                        selected_cols.append(requested)
                        continue
                    requested_lower = requested.lower()
                    if requested_lower in lower_exact_map:
                        selected_cols.append(lower_exact_map[requested_lower])
                        continue
                    contains_matches = [c for c in df_file.columns if requested_lower in c.lower()]
                    if len(contains_matches) == 1:
                        selected_cols.append(contains_matches[0])
                    else:
                        missing.append(requested)
                if missing:
                    sample_cols = [c for c in df_file.columns if ':Zone Operative Temperature' in c or 'VRF Heat Pump Cooling Electricity Energy' in c]
                    raise KeyError(f"Requested CSV columns not found in '{path}': {missing}. Example available columns: {sample_cols[:8]}")
            return {c: df_file[c].tolist() for c in selected_cols}
        eso_results = read_eso_using_readvarseso(eso_file_path=path, eplus_install_dir=eplus_install_dir, only_run_period=only_run_period, cleanup=True)
        data_by_freq = eso_results.get('data', {})
        hourly_df = data_by_freq.get('Hourly')
        if hourly_df is None or hourly_df.empty:
            non_empty = [df for df in data_by_freq.values() if isinstance(df, pd.DataFrame) and (not df.empty)]
            if len(non_empty) == 0:
                raise ValueError(f'No readable data found in ESO file: {path}')
            hourly_df = non_empty[0]
        flattened_map = {}
        for col in hourly_df.columns:
            flattened_name = self._flatten_eso_column_name(col)
            flattened_map[flattened_name] = hourly_df[col].tolist()
        if file_output_columns is None:
            return flattened_map
        missing = [c for c in file_output_columns if c not in flattened_map]
        if missing:
            raise KeyError(f"Requested ESO columns not found in '{path}': {missing}")
        return {c: flattened_map[c] for c in file_output_columns}

    def _attach_hourly_outputs_from_simulation_files(self, df: pd.DataFrame, file_source: Literal['csv', 'eso'], file_output_columns: Optional[List[str]]=None, eplus_install_dir: Optional[str]=None, only_run_period: bool=True) -> pd.DataFrame:
        df_augmented = df.copy()
        per_row_outputs = []
        all_output_cols = set()
        for (_, row) in df_augmented.iterrows():
            try:
                row_outputs = self._extract_hourly_outputs_from_file(row=row, file_source=file_source, file_output_columns=file_output_columns, eplus_install_dir=eplus_install_dir, only_run_period=only_run_period)
            except (ValueError, FileNotFoundError) as e:
                row_outputs = {}
            per_row_outputs.append(row_outputs)
            all_output_cols.update(row_outputs.keys())
        for col in all_output_cols:
            target_col = col
            if target_col in df_augmented.columns:
                target_col = f'{target_col}__from_{file_source}'
            df_augmented[target_col] = [row_outputs[col] if col in row_outputs else [] for row_outputs in per_row_outputs]
        return df_augmented

    def get_hourly_df_optimisation(self, only_pareto_optimal: bool=True, epw_filter: Union[str, List[str]]=None, simulation_indices: Optional[List[int]]=None, output_columns: Optional[List[str]]=None, include_summary_columns: bool=True, file_source: Literal['csv', 'eso']='csv', eplus_install_dir: Optional[str]=None, only_run_period: bool=True, start_date: Optional[str]=None, skip_confirmation: bool=False):
        """
        Expands optimisation results to hourly frequency and saves the result
        in ``outputs_optimisation_hourly``.

        The method reads hourly values directly from the simulation output files
        (CSV or ESO), giving you full control over which simulations and which
        outputs are expanded to avoid memory saturation with large batches.

        When ``epw_filter`` and ``output_columns`` are both left as None (defaults),
        an automatic size estimate is printed and you will be asked to confirm before
        the expansion proceeds. Use ``skip_confirmation=True`` to bypass this prompt.

        :param only_pareto_optimal: if True (default), only Pareto-optimal (non-dominated)
            solutions are expanded. Set to False to include dominated solutions too.
        :param epw_filter: EPW name or list of EPW names to limit the expansion to
            specific climates. Partial strings are accepted (substring match).
            If None (default), all available EPWs are included.
            Example: ``'Seville'`` or ``['Seville', 'Sydney']``.
        :param simulation_indices: optional list of integer row indices (0-based, from
            ``outputs_optimisation``) to select exactly which simulations to expand.
            This is the most direct way to expand specific runs.
            Overrides ``only_pareto_optimal`` and ``epw_filter`` when provided.

            Example – expand only the 3rd and 7th rows::

                parametric.get_hourly_df_optimisation(simulation_indices=[2, 6])

            Example – expand only the Pareto-optimal rows with index < 10::

                pareto_idx = parametric.outputs_optimisation[
                    parametric.outputs_optimisation['pareto-optimal']
                ].index[:10].tolist()
                parametric.get_hourly_df_optimisation(simulation_indices=pareto_idx)

        :param output_columns: list of column names (or partial names) to extract from
            the simulation output file. If None (default), all numeric hourly columns
            are used. Use ``get_hourly_df_columns()`` first to discover available names.
            Example: ``['Zone Operative Temperature', 'VRF Heat Pump Cooling']``.
        :param include_summary_columns: if True (default), the parameter columns
            (e.g. ``CustAST_m``, ``CustAST_n`` …), ``epw`` and ``pareto-optimal`` are
            preserved as identifier columns in the expanded DataFrame.
        :param file_source: source file to read hourly values from: ``'csv'`` (default)
            or ``'eso'``.
        :param eplus_install_dir: EnergyPlus installation directory, only required
            when ``file_source='eso'``.
        :param only_run_period: when ``file_source='eso'``, keep only the run-period
            data (True by default).
        :param start_date: start date and time for the hourly index in
            ``'YYYY-MM-DD HH'`` format. When None (default), the date is inferred
            automatically from the first simulation CSV file.
        :param skip_confirmation: if True, skips the interactive size-confirmation
            prompt that is shown when ``epw_filter`` and ``output_columns`` are both
            left at their defaults. Useful for running in non-interactive environments
            (scripts, notebooks, CI pipelines).
        """
        if getattr(self, 'last_run_type', None) != 'optimisation':
            raise ValueError('This method requires optimisation outputs. Please run run_optimisation() or load_outputs_optimisation() first.')
        if getattr(self, 'outputs_optimisation', None) is None or self.outputs_optimisation.empty:
            raise ValueError('No optimisation data available to expand hourly.')
        _using_defaults = epw_filter is None and output_columns is None and (simulation_indices is None)
        source_df = self.outputs_optimisation.copy()
        if simulation_indices is not None:
            source_df = source_df.loc[simulation_indices]
        else:
            if only_pareto_optimal and 'pareto-optimal' in source_df.columns:
                source_df = source_df[source_df['pareto-optimal']]
            if epw_filter is not None:
                if isinstance(epw_filter, str):
                    epw_filter = [epw_filter]
                epw_mask = source_df['epw'].astype(str).apply(lambda x: any((f.lower() in x.lower() for f in epw_filter)))
                source_df = source_df[epw_mask]
        if source_df.empty:
            raise ValueError('The applied filters resulted in an empty selection. Relax only_pareto_optimal, epw_filter, or simulation_indices.')
        source_df = self._attach_hourly_outputs_from_simulation_files(df=source_df, file_source=file_source, file_output_columns=output_columns, eplus_install_dir=eplus_install_dir, only_run_period=only_run_period)
        if start_date is None:
            try:
                first_row = self.outputs_optimisation.iloc[0]
                csv_path = self._resolve_simulation_file_path(row=first_row, file_source='csv')
                if os.path.exists(csv_path):
                    _dt_raw = pd.read_csv(csv_path, usecols=['Date/Time'], nrows=1)['Date/Time'].iloc[0]
                    _dt_clean = _dt_raw.strip()
                    (_month_day, _time) = _dt_clean.split()
                    (_month, _day) = _month_day.split('/')
                    _hour = int(_time.split(':')[0])
                    start_date = f'2024-{int(_month):02d}-{int(_day):02d} {_hour:02d}'
            except Exception:
                pass
            if start_date is None:
                start_date = '2024-01-01 01'
        if include_summary_columns:
            if hasattr(self, 'parameters_list'):
                param_cols = [i.name for i in self.parameters_list if i.name in source_df.columns]
            elif hasattr(self, 'problem') and hasattr(self.problem, 'names'):
                param_cols = [c for c in self.problem.names('inputs') if c in source_df.columns]
            elif self.outputs_optimisation.attrs.get('parameters_names'):
                param_cols = [c for c in self.outputs_optimisation.attrs['parameters_names'] if c in source_df.columns]
            else:
                _known_non_param = {'epw', 'pareto-optimal', 'simulation_output_csv_path', 'simulation_directory'}
                if hasattr(self, 'problem') and hasattr(self.problem, 'names'):
                    _known_non_param.update(self.problem.names('outputs') or [])
                param_cols = [c for c in source_df.columns if c not in _known_non_param and (not source_df[c].apply(lambda x: isinstance(x, (list, tuple))).any())]
            for extra_col in ['epw', 'pareto-optimal']:
                if extra_col in source_df.columns and extra_col not in param_cols:
                    param_cols.append(extra_col)
        else:
            param_cols = []
        from accim.parametric_and_optimisation.utils import identify_hourly_columns
        hourly_cols = identify_hourly_columns(source_df)
        n_rows = len(source_df)
        n_hourly = len(hourly_cols)
        if n_hourly > 0:
            sample = source_df[hourly_cols[0]].iloc[0]
            n_steps = len(sample) if isinstance(sample, (list, tuple)) else 8760
        else:
            n_steps = 8760
        total_rows = n_rows * n_steps
        total_cols = len(param_cols) + n_hourly + 2
        approx_mb = total_rows * total_cols * 8 / 1000000.0
        size_msg = f"\n  Simulations selected : {n_rows}\n  Hourly steps per sim : {n_steps}\n  Hourly output columns: {n_hourly}  → {hourly_cols[:5]}{('...' if n_hourly > 5 else '')}\n  Expanded shape       : ~{total_rows:,} rows × {total_cols} cols\n  Approx. memory       : ~{approx_mb:.1f} MB"
        if _using_defaults and (not skip_confirmation):
            print(f'[get_hourly_df_optimisation] Estimated output size:{size_msg}')
            answer = input('\nProceed with expansion? [y/N]: ').strip().lower()
            if answer != 'y':
                print('Expansion cancelled. Use epw_filter, output_columns or simulation_indices to reduce the size.')
                return None
        else:
            print(f'[get_hourly_df_optimisation] Expanding…{size_msg}')
        self.outputs_optimisation_hourly = expand_to_hourly_dataframe(df=source_df, parameter_columns=param_cols, start_date=start_date)

    def get_hourly_df_columns(self):
        """
        Identifies the columns which contain hourly values, and save the names in a list, saved in the
        internal variable named outputs_hourly_columns. Supports both parametric and optimisation runs.
        """
        import os
        import pandas as pd
        if getattr(self, 'last_run_type', None) == 'optimisation':
            if getattr(self, 'outputs_optimisation', None) is None or self.outputs_optimisation.empty:
                raise ValueError('Optimisation outputs not found. Run or load optimisation first.')
            for (_, row) in self.outputs_optimisation.iterrows():
                try:
                    path = self._resolve_simulation_file_path(row=row, file_source='csv')
                    if os.path.exists(path):
                        df_file = pd.read_csv(path, nrows=5)
                        excluded_columns = {'Date/Time', 'date/time'}
                        numeric_cols = [c for c in df_file.columns if c not in excluded_columns and pd.api.types.is_numeric_dtype(df_file[c])]
                        self.outputs_hourly_columns = numeric_cols
                        return self.outputs_hourly_columns
                except Exception:
                    continue
            raise FileNotFoundError('Could not find any valid simulation output CSV files to infer hourly columns.')
        elif getattr(self, 'last_run_type', None) == 'parametric':
            if getattr(self, 'outputs_param_simulation', None) is None or self.outputs_param_simulation.empty:
                raise ValueError('Parametric outputs not found. Run or load parametric simulation first.')
            self.outputs_hourly_columns = identify_hourly_columns(self.outputs_param_simulation)
            return self.outputs_hourly_columns
        else:
            raise ValueError('No previous simulation run type detected. Please run parametric or optimisation first.')

class AccimPredefModelsParamSim(OptimParamSimulation):

    def __init__(self, building: besos.IDF_class, output_type: str='standard', output_keep_existing: bool=False, output_freqs: list=['hourly'], ScriptType: str='vrf_mm', SupplyAirTempInputMethod: str='temperature difference', debugging: bool=False):
        super().__init__(building=building, output_type=output_type, output_keep_existing=output_keep_existing, output_freqs=output_freqs, ScriptType=ScriptType, SupplyAirTempInputMethod=SupplyAirTempInputMethod, debugging=debugging)
        accis.modifyAccis(idf=building, ComfStand=99, ComfMod=3, CAT=80, HVACmode=2, VentCtrl=0)