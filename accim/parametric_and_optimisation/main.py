import os
import re
from typing import Literal, List, Union
import warnings

import accim

import pandas as pd
import besos
from besos import sampling
from besos.evaluator import EvaluatorEP
import besos.optimizer as optimizer
from besos.parameters import RangeParameter, CategoryParameter
from besos.problem import EPProblem
from besos.objectives import VariableReader, MeterReader
from besos import IDF_class

from accim.utils import print_available_outputs_mod, modify_timesteps, set_occupancy_to_always, remove_accents_in_idf
from accim.parametric_and_optimisation.utils import expand_to_hourly_dataframe, identify_hourly_columns

import accim.sim.accis_single_idf_funcs as accis
import accim.sim.apmv_setpoints as apmv

import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf_accim
import accim.parametric_and_optimisation.funcs_for_besos.param_apmv as bf_apmv
import accim.parametric_and_optimisation.parameters as params
import accim.parametric_and_optimisation.params_dicts as params_dicts


allowed_output_freqs = Literal['timestep', 'hourly', 'daily', 'monthly', 'runperiod']


def get_rdd_file_as_df():
    """
    Returns the .rdd file from the test simulation as a pandas DataFrame

    :return: a pandas DataFrame containing the .rdd file from the test simulation
    """
    rdd_df = pd.read_csv(
        filepath_or_buffer='available_outputs/eplusout.rdd',
        sep=',|;',
        skiprows=2,
        names=['object', 'key_value', 'variable_name', 'frequency', 'units'],
        engine='python'
    )
    return rdd_df


def parse_mtd_file() -> list[Union[dict[str, Union[str, None, list[str]]], dict[str, Union[str, None, list[str]]]]]:
    """
    Returns a list of the objects in the .mtd file from the test simulation.

    :return: a list of the objects in the .mtd file from the test simulation
    """
    meter_list = []
    with open('available_outputs/eplusout.mtd', 'r') as file:
        lines = file.readlines()

    meter_id, description = None, None
    on_meters = []

    for line in lines:
        line = line.strip()
        if line.startswith('Meters for'):
            if meter_id is not None:
                meter_list.append({
                    'meter_id': meter_id,
                    'description': description,
                    'on_meters': on_meters
                })
            match = re.match(r'Meters for (\d+),(.+)', line)
            if match:
                meter_id = match.group(1)
                description = match.group(2)
                on_meters = []
        elif line.startswith('OnMeter'):
            on_meters.append(line.split('=')[1].strip())

    # Add the last meter
    if meter_id is not None:
        meter_list.append({
            'meter_id': meter_id,
            'description': description,
            'on_meters': on_meters
        })

    return meter_list


def get_mdd_file_as_df():
    """
    Returns the .mdd file from the test simulation as a pandas DataFrame

    :return: a pandas DataFrame containing the .mdd file from the test simulation
    """
    mdd_df = pd.read_csv(
        filepath_or_buffer='available_outputs/eplusout.mdd',
        sep=',|;',
        skiprows=2,
        names=['object', 'meter_name', 'frequency', 'units'],
        engine='python'
    )
    return mdd_df


class OptimParamSimulation:
    def __init__(
            self,
            building: IDF_class,
            parameters_type: Literal['accim custom model', 'accim predefined model', 'apmv setpoints'],
            output_type: Literal['standard', 'custom', 'detailed', 'simplified'] = 'standard',
            output_keep_existing: bool = False,
            output_freqs: List[allowed_output_freqs] = ['hourly'],
            ScriptType: Literal['vrf_mm', 'vrf_ac', 'ex_ac'] = 'vrf_mm',
            SupplyAirTempInputMethod: Literal['temperature difference', 'supply air temperature'] = 'temperature difference',
            debugging: bool = False,
            verbosemode: bool = True,
    ):
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
        :param debugging: True to generate the .EDD file
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
        else:
            raise KeyError(f'String {parameters_type} entered in argument parametric_simulation_type '
                           f'is not supported. Valid strings are: '
                           f'"accim custom model", "accim predefined model" or "apmv setpoints".')

        #todo not working
        # if not all(freq in allowed_output_freqs for freq in output_freqs):
        #     raise ValueError(f"Invalid output frequencies: {output_freqs}. Allowed values are: {allowed_output_freqs}")
        
        allowed_ScriptType = ['vrf_mm', 'vrf_ac', 'ex_ac']
        if ScriptType not in allowed_ScriptType:
            raise ValueError(f"Invalid ScriptType: {ScriptType}. Allowed values are: {allowed_ScriptType}")

        allowed_SupplyAirTempInputMethod = ['temperature difference', 'supply air temperature']
        if SupplyAirTempInputMethod not in allowed_SupplyAirTempInputMethod:
            raise ValueError(f"Invalid ScriptType: {SupplyAirTempInputMethod}. Allowed values are: {allowed_SupplyAirTempInputMethod}")
        
        allowed_output_type = ['standard', 'custom', 'detailed', 'simplified']
        if output_type not in allowed_output_type:
            raise ValueError(f"Invalid output_type: {output_type}. Allowed values are: {allowed_output_type}")

        if is_accim_custom_model or is_accim_predef_model:
            self.ScriptType = ScriptType
            self.temp_ctrl = temp_ctrl
            self.SupplyAirTempInputMethod = SupplyAirTempInputMethod
            self.output_keep_existing = output_keep_existing
            self.output_type = output_type

            accis.addAccis(
                idf=building,
                ScriptType=ScriptType,
                SupplyAirTempInputMethod=SupplyAirTempInputMethod,
                Output_keep_existing=output_keep_existing,
                Output_type=output_type,
                # Output_take_dataframe=set_outputs_df,
                Output_freqs=output_freqs,
    
                # EnergyPlus_version='9.4',
                TempCtrl=temp_ctrl,
                # Output_gen_dataframe=True,
                # make_averages=True,
                debugging=debugging,
                verboseMode=verbosemode
            )
        elif is_apmv_setpoints:
            # apmv.add_vrf_system(building=building)
            apmv.apply_apmv_setpoints(building=building, outputs_freq=output_freqs)
            print('Arguments output_type, output_keep_existing, ScriptType, and SupplyAirTempInputMethod '
                  'are only used in accim predefined and custom models, '
                  'therefore these will not have any effect in this case.')

        self.building = building
        self.output_freqs = output_freqs
        self.parameters_type = parameters_type

        self.is_accim_custom_model = is_accim_custom_model
        self.is_accim_predef_model = is_accim_predef_model
        self.is_apmv_setpoints = is_apmv_setpoints

    def get_output_var_df_from_idf(self) -> pd.DataFrame:
        """
        Gets a pandas DataFrame which contains the Output:Variable objects from the idf.
        Therefore, it may contain wildcards such as '*', which means the variable is requested
        for all zones.

        :return: a pandas DataFrame which contains the Output:Variable objects from the idf
        """
        if self.is_accim_custom_model or self.is_accim_predef_model:
            output_variable_df = accis.gen_outputs_df(
                idf=self.building,
                ScriptType=self.ScriptType,
                Output_keep_existing=self.output_keep_existing,
                Output_type=self.output_type,
                Output_freqs=self.output_freqs,
                TempCtrl=self.temp_ctrl,
                verboseMode=False,
            )
        else:
            output_var_dict = {
                'key_value': [i.Key_Value for i in self.building.idfobjects['Output:Variable']],
                'variable_name': [i.Variable_Name for i in self.building.idfobjects['Output:Variable']],
                'frequency': [i.Reporting_Frequency for i in self.building.idfobjects['Output:Variable']],
                'schedule_name': [i.Schedule_Name for i in self.building.idfobjects['Output:Variable']],
            }
            output_variable_df = pd.DataFrame.from_dict(output_var_dict)

        return output_variable_df

    def get_output_meter_df_from_idf(self) -> pd.DataFrame:
        """
        Gets a pandas DataFrame which contains the Output:Meter objects from the idf.

        :return: a pandas DataFrame which contains the Output:Meter objects from the idf
        """
        output_meter_dict = {
            'key_name': [i.Key_Name for i in self.building.idfobjects['Output:Meter']],
            'frequency': [i.Reporting_Frequency for i in self.building.idfobjects['Output:Meter']],
        }
        output_meter_df = pd.DataFrame.from_dict(output_meter_dict)

        return output_meter_df

    def set_output_var_df_to_idf(self, outputs_df: pd.DataFrame = None):
        """
        Keeps the Output:Variable objects contained in the input pandas DataFrame and removes
        all others. This is important to save space if thousands of simulations with heavy outputs
        are run.

        :type outputs_df: pd.DataFrame
        :param outputs_df: the DataFrame containing Output:Variable objects to be kept
        :return:
        """
        if self.is_accim_custom_model or self.is_accim_predef_model:
            accis.addAccis(
                idf=self.building,
                ScriptType=self.ScriptType,
                SupplyAirTempInputMethod=self.SupplyAirTempInputMethod,
                Output_keep_existing=self.output_keep_existing,
                Output_type=self.output_type,
                Output_take_dataframe=outputs_df,
                Output_freqs=self.output_freqs,

                # EnergyPlus_version='9.4',
                TempCtrl=self.temp_ctrl,
                # Output_gen_dataframe=True,
                # make_averages=True,
                # debugging=True,
                verboseMode=False,
            )
        else:
            alloutputs = [output for output in self.building.idfobjects['Output:Variable']]
            for i in alloutputs:
                self.building.removeidfobject(i)

            for i in outputs_df.index:
                self.building.newidfobject(
                    'Output:Variable',
                    Key_Value=outputs_df.loc[i, 'key_value'],
                    Variable_Name=outputs_df.loc[i, 'variable_name'],
                    Reporting_Frequency=outputs_df.loc[i, 'frequency'].capitalize(),
                    Schedule_Name=outputs_df.loc[i, 'schedule_name']
                )

            # raise KeyError('get_output_var_df_from_idf method is only available for "accim custom model" or '
            #                '"accim predefined model" types.')


    def set_output_met_objects_to_idf(self, output_meters: list):
        """
        Adds the Output:Meter objects from the output_meters argument.

        :type output_meters: list
        :param output_meters: a list containing Output:Meter objects to be added
        :return:
        """
        for meter in output_meters:
            for freq in self.output_freqs:
                self.building.newidfobject(
                    key='OUTPUT:METER',
                    Key_Name=meter,
                    Reporting_Frequency=freq
                )

    def get_outputs_df_from_testsim(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Gets two pandas DataFrames which contain the Output:Variable and Output:Meter objects from a test simulation.
        Therefore, it won't contain wildcards such as '*'.

        :return: a tuple containing the DataFrames containing Output:Variable and Output:Meter
        """
        available_outputs = print_available_outputs_mod(self.building)
        df_outputmeters = pd.DataFrame(
            available_outputs.meterreaderlist,
            columns=['key_name', 'frequency']
        )
        df_outputvariables = pd.DataFrame(
            available_outputs.variablereaderlist,
            columns=['key_value', 'variable_name', 'frequency']
        )

        return df_outputmeters, df_outputvariables

    def set_outputs_for_simulation(
            self,
            df_output_variable: pd.DataFrame = None,
            df_output_meter: pd.DataFrame = None,
    ):
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
                    objs_meters.append(
                            MeterReader(
                                key_name=df_output_meter.loc[i, 'key_name'],
                                frequency=df_output_meter.loc[i, 'frequency'],
                                name=df_output_meter.loc[i, 'output_name'],
                                func=df_output_meter.loc[i, 'func'],
                            )
                        )
                else:
                    objs_meters.append(
                        MeterReader(
                            key_name=df_output_meter.loc[i, 'key_name'],
                            frequency=df_output_meter.loc[i, 'frequency'],
                            name=df_output_meter.loc[i, 'output_name'],
                        )
                    )

        objs_variables = []
        if df_output_variable is not None:
            for i in df_output_variable.index:
                if 'func' in [c for c in df_output_variable.columns]:
                    objs_variables.append(
                            VariableReader(
                                key_value=df_output_variable.loc[i, 'key_value'],
                                variable_name=df_output_variable.loc[i, 'variable_name'],
                                frequency=df_output_variable.loc[i, 'frequency'],
                                name=df_output_variable.loc[i, 'output_name'],
                                func=df_output_variable.loc[i, 'func'],
                            )
                        )
                else:
                    objs_variables.append(
                            VariableReader(
                                key_value=df_output_variable.loc[i, 'key_value'],
                                variable_name=df_output_variable.loc[i, 'variable_name'],
                                frequency=df_output_variable.loc[i, 'frequency'],
                                name=df_output_variable.loc[i, 'output_name'],
                            )
                        )

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

    def set_parameters(
            self,
            accis_params_dict: dict,
            additional_params: list = None,
            use_dflt_values: bool = False,
            # HVACmode: Literal[0, 1, 2] = 2,
            # VentCtrl: Literal[0, 1, 2, 3] = 0,
    ):
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
            raise ValueError(f'The following parameters are not allowed in '
                             f'parameters_type {self.parameters_type}: {not_allowed_parameters}')

        if self.is_accim_custom_model:
            # accis.modifyAccis(
            #     idf=self.building,
            #     ComfStand=99,
            #     ComfMod=3,
            #     CAT=80,
            #     # HVACmode=HVACmode,
            #     # VentCtrl=VentCtrl,
            # )
            bf_accim.modify_ComfStand(self.building, 99)
            bf_accim.modify_ComfMod(self.building, 3)
            bf_accim.modify_CAT(self.building, 80)

            # Checking parameters are defined:
            bf_accim.modify_CustAST_m(self.building, 0)
            bf_accim.modify_CustAST_n(self.building, 0)
            bf_accim.modify_CustAST_ASToffset(self.building, 0)
            bf_accim.modify_CustAST_ASTaul(self.building, 0)
            bf_accim.modify_CustAST_ASTall(self.building, 0)

            args = accim.utils.get_accim_args(self.building)
            parameters_to_check = [k for k, v in args['CustAST'].items() if 'CustAST_' + k not in parameters and v == 0]
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
                print(f'The following parameters are not included in the parameters to be set, '
                                 f'and have not been defined yet (i.e. the value is 0): '
                                 f'{parameters_to_be_defined}')
                dflt_values = {
                    'm': 0.31,
                    'n': 17.8,
                    'ACSToffset': 3.5,
                    'AHSToffset': -3.5,
                    'ACSTaul': 33.5,
                    'ACSTall': 10,
                    'AHSTaul': 33.5,
                    'AHSTall': 10
                }
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


        parameters_list = [params.accis_parameter(k, v) for k, v in accis_params_dict.items()]
        if additional_params is not None:
            parameters_list.extend(additional_params)

        self.parameters_list = parameters_list
        self.descriptors_has_options = descriptors_has_options
        self.descriptors_has_range = descriptors_has_range

    def set_problem(
            self,
            minimize_outputs: list = None,
            constraints: list = None,
            constraint_bounds: list = None,
            **kwargs
    ):
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
        # if type == 'parametric_and_optimisation simulation':
        #     problem = EPProblem(
        #         inputs=self.parameters_list,
        #         outputs=self.sim_outputs
        #     )
        # elif type == 'optimisation':
        problem = EPProblem(
            inputs=self.parameters_list,
            outputs=self.sim_outputs,
            minimize_outputs=minimize_outputs,
            constraints=constraints,
            constraint_bounds=constraint_bounds,
            **kwargs
        )
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
            # from itertools import product
            # combinations = list(product(*parameters_values.values()))
            # parameters_values_df = pd.DataFrame(combinations, columns=parameters_values.keys())
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
            parameters_values_df = sampling.dist_sampler(
                sampling.full_factorial,
                self.problem,
                num_samples=2,
                level=level
            )
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
            parameters_values_df = sampling.dist_sampler(
                sampling.lhs,
                self.problem,
                num_samples=num_samples
            )
        else:
            raise KeyError('sampling_lhs method can only be used with range descriptors.')

        self.parameters_values_df = parameters_values_df

    def set_evaluator(
            self,
            epw: str,
            out_dir: str,
    ) -> besos.evaluator.EvaluatorEP:
        """
        Used internally for setting the evaluator in run_parametric_simulation and run_optimisation methods.

        :param epw: The epw file name
        :param out_dir: The name of the output directory to save the results.
        :return: the besos.evaluator.EvaluatorEP class instance
        """
        evaluator = EvaluatorEP(
            problem=self.problem,
            building=self.building,
            epw=epw,
            out_dir=out_dir
        )
        return evaluator


    def run_parametric_simulation(
            self,
            epws: list,
            out_dir: str,
            df: pd.DataFrame,
            processes: int = 2,
            keep_input: bool = True,
            keep_dirs: bool = True,
    ) -> pd.DataFrame:
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
            # evaluator = EvaluatorEP(
            #     problem=self.problem,
            #     building=self.building,
            #     epw=epw,
            #     out_dir=out_dir
            # )
            evaluator = self.set_evaluator(
                epw=epw,
                out_dir=out_dir,
            )
            outputs = evaluator.df_apply(
                df=df,
                keep_input=keep_input,
                keep_dirs=keep_dirs,
                processes=processes
            )
            outputs['epw'] = epwname
            outputs_dict.update({epwname: outputs})
            evaluators.update({epwname: evaluator})

        outputs_param_simulation = pd.concat([df for df in outputs_dict.values()])
        if len(epws) > 1:
            outputs_param_simulation = outputs_param_simulation.reset_index()

        self.outputs_param_simulation = outputs_param_simulation
        self.evaluators = evaluators
        # return outputs_param_simulation

    def run_optimisation(
            self,
            epws: list,
            out_dir: str,
            evaluations: int,
            population_size: int,
            algorithm: str = 'NSGAII',
            **kwargs
    ) -> pd.DataFrame:
        """
        Runs the optimisation using

        :param epws: The epw filename
        :param out_dir: the directory name to save the outputs
        :param evaluations: The algorithm will be stopped once it uses more than this many evaluations.
            For more information, refer to besos.optimizer.platypus_alg
        :param population_size: The number of simulations to run
        
        :return: a pandas DataFrame
        """
        available_algorithms = [
            'GeneticAlgorithm',
            'EvolutionaryStrategy',
            'NSGAII',
            'EpsMOEA',
            'GDE3',
            'SPEA2',
            'MOEAD',
            'NSGAIII',
            'ParticleSwarm',
            'OMOPSO',
            'SMPSO',
            'CMAES',
            'IBEA',
            'PAES',
            'PESA2',
            'EpsNSGAII',
        ]
        outputs_dict = {}
        evaluators = {}

        for epw in epws:
            evaluator = self.set_evaluator(
                epw=epw,
                out_dir=out_dir
            )
            # outputs_optimisation = NSGAII(evaluator, evaluations=evaluations, population_size=population_size)
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

            epwname = epw.split('.epw')[0]
            outputs_optimisation['epw'] = epwname
            outputs_dict.update({epwname: outputs_optimisation})
            evaluators.update({epwname: evaluator})

        outputs_optimisation = pd.concat([df for df in outputs_dict.values()])
        if len(epws) > 1:
            outputs_optimisation = outputs_optimisation.reset_index()

        self.outputs_optimisation = outputs_optimisation
        self.evaluators = evaluators

        # return outputs_optimisation

    def get_hourly_df(self, start_date: str = '2024-01-01 01'):
        """
        Transforms the hourly values of outputs_param_simulation to a new pandas DataFrame, saved in the
         internal variable named outputs_param_simulation_hourly.

        :param start_date: the start date for the simulation results, in format 'YYY-MM-DD HH'
        """
        parameter_columns = [i.name for i in self.parameters_list]
        parameter_columns.append('epw')
        self.outputs_param_simulation_hourly = expand_to_hourly_dataframe(
            df=self.outputs_param_simulation,
            parameter_columns=parameter_columns,
            start_date=start_date
        )

    def get_hourly_df_columns(self):
        """
        Identifies the columns which contain hourly values, and save the names in a list, saved in the
        internal variable named outputs_hourly_columns
        """
        self.outputs_hourly_columns = identify_hourly_columns(self.outputs_param_simulation)

class AccimPredefModelsParamSim(OptimParamSimulation):
    def __init__(
            self,
            building: besos.IDF_class,
            output_type: str = 'standard',
            output_keep_existing: bool = False,
            output_freqs: list = ['hourly'],
            ScriptType: str = 'vrf_mm',
            SupplyAirTempInputMethod: str = 'temperature difference',
            debugging: bool = False,
    ):
        super().__init__(
            self,
            building,
            output_type,
            output_keep_existing,
            output_freqs,
            ScriptType,
            SupplyAirTempInputMethod,
            debugging
        )

        accis.modifyAccis(
            idf=building,
            ComfStand=99,
            ComfMod=3,
            CAT=80,
            HVACmode=2,
            VentCtrl=0,
        )

