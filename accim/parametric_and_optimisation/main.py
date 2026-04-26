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

from accim.utils import print_available_outputs_mod, modify_timesteps, set_occupancy_to_always, remove_accents_in_idf, \
    reduce_runtime, read_eso_using_readvarseso
from accim.parametric_and_optimisation.utils import expand_to_hourly_dataframe, identify_hourly_columns

import accim.sim.accis_single_idf_funcs as accis
import accim.sim.apmv_setpoints as apmv

# To avoid multiprocessing pickling issues with local classes on Windows
class GlobalAllCapsDict(dict):
    def __getitem__(self, key):
        return super().__getitem__(key.upper())

def _patched_eval_func(evaluator, all_outputs):
    if getattr(evaluator, 'out_dir', None) is not None:
        if not hasattr(evaluator, '_out_dir_patched'):
            evaluator.out_dir = f"{evaluator.out_dir}_{os.getpid()}"
            evaluator._out_dir_patched = True
    keep_dirs = getattr(evaluator, '_keep_dirs', False)
    results = evaluator(all_outputs, keep_dirs=keep_dirs)
    if not hasattr(evaluator, '_optimisation_eval_records'):
        evaluator._optimisation_eval_records = []
    eval_record = {'inputs': tuple(all_outputs)}
    if keep_dirs:
        eval_record['results'] = tuple(results[:-1])
        eval_record['sim_dir'] = results[-1]
    else:
        eval_record['results'] = tuple(results)
        eval_record['sim_dir'] = None
    evaluator._optimisation_eval_records.append(eval_record)
    log_base = getattr(evaluator, '_optimisation_log_base', None)
    if log_base is not None:
        def _json_safe(value):
            if isinstance(value, dict):
                return {k: _json_safe(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [_json_safe(v) for v in value]
            if isinstance(value, os.PathLike):
                return os.fspath(value)
            if hasattr(value, 'item'):
                try:
                    return value.item()
                except (ValueError, TypeError):
                    pass
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            return str(value)

        log_payload = {
            'inputs': _json_safe(list(eval_record['inputs'])),
            'results': _json_safe(list(eval_record['results'])),
            'sim_dir': _json_safe(eval_record['sim_dir']),
        }
        log_path = f"{log_base}_{os.getpid()}.jsonl"
        with open(log_path, 'a', encoding='utf-8') as logfile:
            logfile.write(json.dumps(log_payload) + '\n')
    if keep_dirs:
        results = results[:-1]

    keep_sim_files = getattr(evaluator, '_keep_sim_files', 'all')
    if keep_dirs and keep_sim_files == 'non-dominated':
        records = evaluator._optimisation_eval_records
        if len(records) > 0 and len(records) % getattr(evaluator, '_keep_sim_files_batch_size', 50) == 0:
            import shutil
            import numpy as np
            minimize_flags = getattr(evaluator.problem, 'minimize_outputs', None)
            output_names = evaluator.problem.names("outputs")
            n_outputs = len(output_names)
            if minimize_flags is None:
                minimize_flags = [True] * n_outputs
            else:
                minimize_flags = [(m if m is not None else True) for m in minimize_flags]
            
            costs = np.zeros((len(records), n_outputs))
            for i, rec in enumerate(records):
                costs[i, :] = rec['results'][:n_outputs]
                
            for j, minimize in enumerate(minimize_flags):
                if not minimize:
                    costs[:, j] = -costs[:, j]
                    
            n = costs.shape[0]
            is_pareto = np.ones(n, dtype=bool)
            for i in range(n):
                if not is_pareto[i]:
                    continue
                others_mask = np.arange(n) != i
                dominated_i = (
                    np.all(costs[others_mask] <= costs[i], axis=1)
                    & np.any(costs[others_mask] < costs[i], axis=1)
                )
                if np.any(dominated_i):
                    is_pareto[i] = False
                    
            for i in range(n):
                if not is_pareto[i]:
                    sim_dir = records[i].get('sim_dir')
                    if sim_dir is not None and os.path.exists(sim_dir):
                        try:
                            shutil.rmtree(sim_dir)
                        except Exception:
                            pass
                        records[i]['sim_dir'] = None

    return evaluator.package_for_platypus(results)

def _patched_to_platypus(self):
    problem = self.problem.to_platypus()
    problem.function = functools.partial(_patched_eval_func, self)
    return problem

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
            make_averages: bool = False,
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
        :param make_averages: to make average outputs of hour-counting and operative temperature related outputs
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
            self.make_averages = make_averages

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
                make_averages=make_averages,
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
        self.outputs_optimisation = None
        self.outputs_optimisation_filepath = None
        self.optimisation_csv_paths_non_dominated = []
        self.optimisation_csv_paths_dominated = []
        self.optimisation_csv_paths_non_dominated_by_epw = {}
        self.optimisation_csv_paths_dominated_by_epw = {}

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
                make_averages=self.make_averages,
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

    def get_outputs_df_from_testsim(self, reduce_sim_time: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
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
            use_dflt_values: bool = True,
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

        if descriptors_has_options is True:
            for k, v in accis_params_dict.items():
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
                raise ValueError(f"Parameter {inp.name} must be a RangeParameter for Sensitivity Analysis.")
            bounds.append([desc.min, desc.max])

        problem = {
            'num_vars': len(names),
            'names': names,
            'bounds': bounds
        }
        return problem

    def sampling_sobol(self, num_samples: int = 128):
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
            raise ImportError("SALib is required for Sensitivity Analysis. Install it with: pip install SALib")

        problem = self._get_salib_problem()
        
        # Generate samples using SALib
        samples = saltelli.sample(problem, num_samples)
        
        # Convert to pandas DataFrame with column names matching the parameters
        self.parameters_values_df = pd.DataFrame(samples, columns=problem['names'])

    def sampling_morris(self, num_samples: int = 100, num_levels: int = 4):
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
            raise ImportError("SALib is required for Sensitivity Analysis. Install it with: pip install SALib")

        problem = self._get_salib_problem()
        
        # Generate samples using SALib
        samples = morris_sampler.sample(problem, N=num_samples, num_levels=num_levels)
        
        # Convert to pandas DataFrame with column names matching the parameters
        self.parameters_values_df = pd.DataFrame(samples, columns=problem['names'])

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

    def estimate_optimisation_sims(
            self,
            evaluations: int,
            population_size: int,
            epws: list,
    ) -> int:
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
        print(
            f"Estimated simulations\n"
            f"  evaluations    : {evaluations}\n"
            f"  population_size: {population_size}\n"
            f"  EPWs           : {len(epws)} ({', '.join(epws)})\n"
            f"  sims per EPW   : {sims_per_epw}  "
            f"({math.ceil(evaluations / population_size)} generation(s) × {population_size})\n"
            f"  TOTAL          : {total}"
        )
        return total

    def run_optimisation(
            self,
            epws: list,
            out_dir: str,
            evaluations: int,
            population_size: int,
            algorithm: str = 'NSGAII',
            processes: int = 1,
            keep_sim_files: Literal['all', 'non-dominated', 'none'] = 'all',
            keep_sim_files_batch_size: int = 50,
            keep_df: Literal['all', 'non-dominated'] = 'all',
            **kwargs
    ) -> pd.DataFrame:
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
        full_outputs_dict = {}
        evaluators = {}
        os.makedirs(out_dir, exist_ok=True)

        from besos.evaluator import AbstractEvaluator
        # Monkey-patch besos' AbstractEvaluator.to_platypus to support keep_dirs seamlessly
        # and avoid unpicklable lambda functions when using multiprocessing.
        if not hasattr(AbstractEvaluator, '_original_to_platypus'):
            AbstractEvaluator._original_to_platypus = AbstractEvaluator.to_platypus
        AbstractEvaluator.to_platypus = _patched_to_platypus

        # Build the platypus parallel evaluator when processes > 1.
        # We cannot pass `evaluator` via kwargs because besos.optimizer wrappers
        # consume it positionally. Instead, we temporarily override the global
        # PlatypusConfig.default_evaluator.
        if processes > 1:
            import platypus
            from platypus.config import PlatypusConfig

            original_evaluator = PlatypusConfig.default_evaluator
            platypus_evaluator = platypus.ProcessPoolEvaluator(processes)
            PlatypusConfig.default_evaluator = platypus_evaluator

        try:
            for epw in epws:
                evaluator = self.set_evaluator(
                    epw=epw,
                    out_dir=out_dir
                )
                evaluator._keep_sim_files = keep_sim_files
                evaluator._keep_sim_files_batch_size = keep_sim_files_batch_size
                evaluator._keep_dirs = False if keep_sim_files == 'none' else True
                evaluator._optimisation_eval_records = []
                epwname = epw.split('.epw')[0]
                evaluator._optimisation_log_base = os.path.join(
                    out_dir,
                    f'optim_eval_log_{epwname}_{os.getpid()}'
                )
                for log_file in pyglob.glob(f"{evaluator._optimisation_log_base}_*.jsonl"):
                    try:
                        os.remove(log_file)
                    except OSError:
                        pass
                
                # We need to temporarily decouple the building evaluator internal dictionaries
                # because besos wraps `idfobjects` inside a local class `AllCapsDict` on `read()`,
                # which natively conflicts with Windows Python ProcessPool Evaluators pickling process
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
                full_outputs_optimisation = self._build_full_optimisation_outputs_df(
                    evaluator=evaluator,
                    epwname=epwname
                )
                full_outputs_dict.update({epwname: full_outputs_optimisation})
                evaluators.update({epwname: evaluator})
        finally:
            # Always close the process pool and restore the original evaluator
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

        outputs_optimisation = self._annotate_pareto_status(
            outputs_optimisation_full=outputs_optimisation,
            outputs_optimisation=outputs_optimisation_non_dominated
        )

        if keep_sim_files == 'non-dominated':
            import shutil
            for idx, row in outputs_optimisation[~outputs_optimisation['pareto-optimal']].iterrows():
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
            # Forcefully clean up any worker BESOS_Output folders created during this run.
            # When keep_sim_files='none', besos does not generate unique subdirectories
            # per evaluation, so the raw files overwrite each other directly in the 
            # out_dir/BESOS_Output_{pid} working directory, which is left behind.
            worker_dirs = glob.glob(os.path.join(out_dir, "BESOS_Output*"))
            for w_dir in worker_dirs:
                if os.path.isdir(w_dir):
                    try:
                        shutil.rmtree(w_dir)
                    except Exception:
                        pass
            
            # Clean up the JSONL evaluation logs that are no longer needed
            log_files = glob.glob(os.path.join(out_dir, "optim_eval_log_*.jsonl"))
            for log_file in log_files:
                try:
                    os.remove(log_file)
                except OSError:
                    pass
            
            # Since simulation files are deleted, clean the dataframe paths
            outputs_optimisation['simulation_directory'] = pd.NA
            outputs_optimisation['simulation_output_csv_path'] = pd.NA

        if keep_df == 'non-dominated':
            outputs_optimisation = outputs_optimisation[outputs_optimisation['pareto-optimal']].copy()
            if len(epws) > 1:
                outputs_optimisation = outputs_optimisation.reset_index(drop=True)

        self._set_optimisation_outputs(
            outputs_optimisation_full=outputs_optimisation,
            outputs_optimisation_non_dominated=outputs_optimisation_non_dominated
        )
        self._save_outputs_optimisation_full(out_dir=out_dir)
        self.evaluators = evaluators

        # return outputs_optimisation

    def _build_full_optimisation_outputs_df(
            self,
            evaluator: EvaluatorEP,
            epwname: str,
    ) -> pd.DataFrame:
        records = getattr(evaluator, '_optimisation_eval_records', [])
        if len(records) == 0:
            log_base = getattr(evaluator, '_optimisation_log_base', None)
            if log_base is not None:
                log_files = pyglob.glob(f"{log_base}_*.jsonl")
                for log_file in log_files:
                    with open(log_file, 'r', encoding='utf-8') as logfile:
                        for line in logfile:
                            payload = json.loads(line)
                            records.append(
                                {
                                    'inputs': tuple(payload['inputs']),
                                    'results': tuple(payload['results']),
                                    'sim_dir': payload['sim_dir'],
                                }
                            )
        input_names = evaluator.problem.names("inputs")
        output_names = evaluator.problem.names("outputs")
        constraint_names = evaluator.problem.names("constraints")

        rows = []
        for record in records:
            row = {}
            for idx, input_name in enumerate(input_names):
                row[input_name] = record['inputs'][idx]
            for idx, output_name in enumerate(output_names):
                row[output_name] = record['results'][idx]
            for idx, constraint_name in enumerate(constraint_names):
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

    def _annotate_pareto_status(
            self,
            outputs_optimisation_full: pd.DataFrame,
            outputs_optimisation: pd.DataFrame
    ) -> pd.DataFrame:
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

        output_names = self.problem.names("outputs")
        minimize_outputs = getattr(self.problem, 'minimize_outputs', None)

        # Determine minimisation direction per objective.
        # minimize_outputs is a list of booleans (True = minimise, False = maximise, None = show only).
        # For Pareto dominance we always work in a "lower is better" space,
        # so we flip maximised objectives before the dominance check.
        if minimize_outputs is None:
            minimize_flags = [True] * len(output_names)
        else:
            minimize_flags = [
                (m if m is not None else True) for m in minimize_outputs
            ]

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
                # Check whether i is dominated by any other row currently
                # considered non-dominated.
                others_mask = np.arange(n) != i
                dominated_i = (
                    np.all(costs[others_mask] <= costs[i], axis=1)
                    & np.any(costs[others_mask] < costs[i], axis=1)
                )
                if np.any(dominated_i):
                    is_pareto[i] = False
            return is_pareto

        def _pareto_mask_for_group(group: pd.DataFrame) -> pd.Series:
            """Compute Pareto mask for a single EPW group."""
            objective_data = group[output_names].values.astype(float)
            # Convert to minimisation space
            for j, minimise in enumerate(minimize_flags):
                if not minimise:
                    objective_data[:, j] = -objective_data[:, j]
            mask = _is_pareto_optimal(objective_data)
            return pd.Series(mask, index=group.index)

        pareto_mask = pd.Series(False, index=outputs_optimisation_full.index)
        if 'epw' in outputs_optimisation_full.columns and outputs_optimisation_full['epw'].notna().any():
            for epw, group in outputs_optimisation_full.groupby('epw'):
                pareto_mask.loc[group.index] = _pareto_mask_for_group(group)
        else:
            pareto_mask = _pareto_mask_for_group(outputs_optimisation_full)

        outputs_optimisation_full['pareto-optimal'] = pareto_mask
        return outputs_optimisation_full
    def _set_optimisation_outputs(
            self,
            outputs_optimisation_full: pd.DataFrame,
            outputs_optimisation_non_dominated: pd.DataFrame = None
    ):
        if 'pareto-optimal' not in outputs_optimisation_full.columns:
            raise KeyError("Column 'pareto-optimal' is required in outputs_optimisation_full.")
        if 'simulation_output_csv_path' not in outputs_optimisation_full.columns:
            outputs_optimisation_full['simulation_output_csv_path'] = pd.NA
        if 'epw' not in outputs_optimisation_full.columns:
            outputs_optimisation_full['epw'] = pd.NA
        if (
            outputs_optimisation_non_dominated is not None
            and 'epw' in outputs_optimisation_non_dominated.columns
            and outputs_optimisation_full['epw'].isna().all()
            and len(outputs_optimisation_non_dominated['epw'].dropna().unique()) == 1
        ):
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

        self.outputs_optimisation = outputs_optimisation_full
        if 'epw' not in self.outputs_optimisation.columns:
            self.outputs_optimisation['epw'] = pd.NA
        self.optimisation_csv_paths_non_dominated = (
            self.outputs_optimisation[self.outputs_optimisation['pareto-optimal']]['simulation_output_csv_path']
            .dropna()
            .drop_duplicates()
            .tolist()
        )
        self.optimisation_csv_paths_non_dominated_by_epw = {}
        self.optimisation_csv_paths_dominated_by_epw = {}
        if 'epw' in outputs_optimisation_full.columns:
            non_dominated_df = outputs_optimisation_full[outputs_optimisation_full['pareto-optimal']].copy()
            dominated_df = outputs_optimisation_full[~outputs_optimisation_full['pareto-optimal']].copy()
            epws = sorted({str(epw) for epw in outputs_optimisation_full['epw'].dropna().unique().tolist()})
            for epw in epws:
                self.optimisation_csv_paths_non_dominated_by_epw[epw] = (
                    non_dominated_df.loc[non_dominated_df['epw'].astype(str) == epw, 'simulation_output_csv_path']
                    .dropna()
                    .drop_duplicates()
                    .tolist()
                )
                self.optimisation_csv_paths_dominated_by_epw[epw] = (
                    dominated_df.loc[dominated_df['epw'].astype(str) == epw, 'simulation_output_csv_path']
                    .dropna()
                    .drop_duplicates()
                    .tolist()
                )
        self.optimisation_csv_paths_dominated = (
            outputs_optimisation_full[~outputs_optimisation_full['pareto-optimal']]['simulation_output_csv_path']
            .dropna()
            .drop_duplicates()
            .tolist()
        )

    def _save_outputs_optimisation_full(self, out_dir: str):
        os.makedirs(out_dir, exist_ok=True)
        full_results_filename = f'outputs_optimisation_{os.getpid()}.csv'
        full_results_path = os.path.join(out_dir, full_results_filename)
        self.outputs_optimisation.to_csv(full_results_path, index=False)
        self.outputs_optimisation_filepath = full_results_path

    def load_outputs_optimisation(
            self,
            csv_path: str = None
    ) -> pd.DataFrame:
        """
        Loads full optimisation outputs (dominated + non-dominated) from a CSV file
        previously generated by :meth:`run_optimisation`, and rebuilds the related
        internal attributes without rerunning simulations.

        :param csv_path: path to a CSV file with full optimisation outputs.
            If None, uses ``self.outputs_optimisation_filepath``.
        :return: pandas DataFrame containing full optimisation outputs (dominated + non-dominated)
        """
        target_csv_path = csv_path or self.outputs_optimisation_filepath
        if target_csv_path is None:
            raise ValueError(
                'No csv_path was provided and no previous outputs_optimisation file is available. '
                'Run run_optimisation first or provide a valid csv_path.'
            )

        outputs_optimisation = pd.read_csv(target_csv_path)
        if 'pareto-optimal' not in outputs_optimisation.columns:
            raise KeyError(
                "Column 'pareto-optimal' not found in the provided CSV. "
                "Please load a file generated from outputs_optimisation."
            )
        self.outputs_optimisation_filepath = target_csv_path
        self._set_optimisation_outputs(outputs_optimisation_full=outputs_optimisation)
        return self.outputs_optimisation

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

    @staticmethod
    def _resolve_simulation_file_path(row: pd.Series, file_source: Literal['csv', 'eso']) -> str:
        error_msg = (
            f"{file_source.upper()} path cannot be resolved for this simulation. "
            f"If you used keep_sim_files='non-dominated' and this is a dominated simulation, "
            f"the files were deleted to save space. To analyze this simulation, re-run keeping its files."
        )
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
        area, variable, units = col
        return f'{variable} [{units}] | {area}'

    def _extract_hourly_outputs_from_file(
            self,
            row: pd.Series,
            file_source: Literal['csv', 'eso'],
            file_output_columns: Optional[List[str]] = None,
            eplus_install_dir: Optional[str] = None,
            only_run_period: bool = True
    ) -> dict:
        path = self._resolve_simulation_file_path(row=row, file_source=file_source)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Simulation output file not found: {path}")

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
                    raise KeyError(
                        f"Requested CSV columns not found in '{path}': {missing}. "
                        f"Example available columns: {sample_cols[:8]}"
                    )
            return {c: df_file[c].tolist() for c in selected_cols}

        eso_results = read_eso_using_readvarseso(
            eso_file_path=path,
            eplus_install_dir=eplus_install_dir,
            only_run_period=only_run_period,
            cleanup=True
        )
        data_by_freq = eso_results.get('data', {})
        hourly_df = data_by_freq.get('Hourly')
        if hourly_df is None or hourly_df.empty:
            non_empty = [df for df in data_by_freq.values() if isinstance(df, pd.DataFrame) and not df.empty]
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

    def _attach_hourly_outputs_from_simulation_files(
            self,
            df: pd.DataFrame,
            file_source: Literal['csv', 'eso'],
            file_output_columns: Optional[List[str]] = None,
            eplus_install_dir: Optional[str] = None,
            only_run_period: bool = True
    ) -> pd.DataFrame:
        df_augmented = df.copy()
        per_row_outputs = []
        all_output_cols = set()
        for _, row in df_augmented.iterrows():
            try:
                row_outputs = self._extract_hourly_outputs_from_file(
                    row=row,
                    file_source=file_source,
                    file_output_columns=file_output_columns,
                    eplus_install_dir=eplus_install_dir,
                    only_run_period=only_run_period
                )
            except (ValueError, FileNotFoundError) as e:
                # If files were deleted by keep_sim_files='non-dominated' (or missing for any reason),
                # we skip this row. The resulting hourly df will only contain data for valid rows.
                row_outputs = {}
            per_row_outputs.append(row_outputs)
            all_output_cols.update(row_outputs.keys())

        for col in all_output_cols:
            target_col = col
            if target_col in df_augmented.columns:
                target_col = f'{target_col}__from_{file_source}'
            df_augmented[target_col] = [row_outputs[col] if col in row_outputs else [] for row_outputs in per_row_outputs]

        return df_augmented

    def get_hourly_df_optimisation(
            self,
            start_date: str = '2024-01-01 01',
            df: Optional[pd.DataFrame] = None,
            include_file_outputs: bool = False,
            file_source: Literal['csv', 'eso'] = 'csv',
            file_output_columns: Optional[List[str]] = None,
            eplus_install_dir: Optional[str] = None,
            only_run_period: bool = True,
    ):
        """
        Expands optimisation results (dominated + non-dominated) to hourly frequency,
        and saves the result in ``outputs_optimisation_hourly``.
        The ``pareto-optimal`` column is preserved so dominated and non-dominated rows
        can be filtered afterwards.

        :param start_date: start date for the expanded hourly time index ('YYYY-MM-DD HH')
        :param df: optional dataframe of simulations to expand; if None, uses ``outputs_optimisation``
            (which contains all simulations, dominated and non-dominated).
        :param include_file_outputs: if True, reads additional hourly outputs from simulation files
            (.csv or .eso) and appends them before expanding.
        :param file_source: source file type for additional outputs ('csv' or 'eso').
        :param file_output_columns: optional list of output columns to extract from file source.
            If None, all numeric CSV columns or all parsed ESO hourly columns are used.
        :param eplus_install_dir: optional EnergyPlus directory used by ESO parsing.
        :param only_run_period: when ``file_source='eso'``, keeps run period only if True.
        """
        if df is None:
            source_df = self.outputs_optimisation.copy()
        else:
            source_df = df.copy()

        if source_df is None or source_df.empty:
            raise ValueError('No optimisation data available to expand hourly.')

        if include_file_outputs:
            source_df = self._attach_hourly_outputs_from_simulation_files(
                df=source_df,
                file_source=file_source,
                file_output_columns=file_output_columns,
                eplus_install_dir=eplus_install_dir,
                only_run_period=only_run_period
            )

        parameter_columns = [i.name for i in self.parameters_list if i.name in source_df.columns]
        for extra_col in ['epw', 'pareto-optimal']:
            if extra_col in source_df.columns:
                parameter_columns.append(extra_col)

        self.outputs_optimisation_hourly = expand_to_hourly_dataframe(
            df=source_df,
            parameter_columns=parameter_columns,
            start_date=start_date
        )

    def get_hourly_df_columns(self):
        """
        Identifies the columns which contain hourly values, and save the names in a list, saved in the
        internal variable named outputs_hourly_columns
        """
        self.outputs_hourly_columns = identify_hourly_columns(self.outputs_param_simulation)

    def run_sensitivity_analysis(self, method: Literal['sobol', 'morris'] = 'sobol', **kwargs) -> dict:
        """
        Runs Sensitivity Analysis on the results of a parametric simulation using SALib.
        
        :param method: 'sobol' or 'morris'. Must match the sampling method used.
        :param kwargs: additional arguments to pass to SALib.analyze.sobol or SALib.analyze.morris.
        :return: a dictionary mapping each output name to its SALib analysis results.
        """
        if getattr(self, 'outputs_param_simulation', None) is None or self.outputs_param_simulation.empty:
            raise ValueError("You must run run_parametric_simulation before running sensitivity analysis.")

        try:
            from SALib.analyze import sobol, morris
        except ImportError:
            raise ImportError("SALib is required for Sensitivity Analysis. Install it with: pip install SALib")

        problem = self._get_salib_problem()
        df = self.outputs_param_simulation
        output_names = self.problem.names("outputs")
        
        results = {}
        for output_name in output_names:
            if output_name not in df.columns:
                print(f"Warning: Output {output_name} not found in results DataFrame. Skipping.")
                continue
                
            Y = df[output_name].values.astype(float)
            
            if method == 'sobol':
                try:
                    res = sobol.analyze(problem, Y, **kwargs)
                except ValueError as e:
                    raise ValueError(f"Error analyzing with Sobol. Make sure you generated samples with sampling_sobol(). Details: {e}")
            elif method == 'morris':
                try:
                    res = morris.analyze(problem, df[problem['names']].values.astype(float), Y, **kwargs)
                except ValueError as e:
                    raise ValueError(f"Error analyzing with Morris. Make sure you generated samples with sampling_morris(). Details: {e}")
            else:
                raise ValueError(f"Unknown sensitivity analysis method: {method}")
                
            results[output_name] = res
            
        self.sensitivity_results = results
        return results

    def get_best_compromise_solution(self, method: Literal['knee_point', 'topsis'] = 'topsis', weights: list = None) -> pd.DataFrame:
        """
        Identifies the best compromise solution from the Pareto front.

        :param method: The MCDM method to use. 'knee_point' (closest distance to Utopia point) or 'topsis'.
        :param weights: A list of weights for each objective, used only in 'topsis'. 
            If None, equal weights are applied. Must match the number of objectives.
        :return: A pandas DataFrame containing the best compromise solution(s).
        """
        if getattr(self, 'outputs_optimisation', None) is None or self.outputs_optimisation.empty:
            raise ValueError("No optimization results found. Run optimization first.")

        # Filter for Pareto optimal solutions
        pareto_df = self.outputs_optimisation[self.outputs_optimisation['pareto-optimal'] == True].copy()
        if pareto_df.empty:
            raise ValueError("No Pareto optimal solutions found in outputs_optimisation.")

        output_names = self.problem.names("outputs")
        minimize_outputs = getattr(self.problem, 'minimize_outputs', None)
        
        if minimize_outputs is None:
            minimize_flags = [True] * len(output_names)
        else:
            minimize_flags = [(m if m is not None else True) for m in minimize_outputs]

        # Extract objectives array
        obj_values = pareto_df[output_names].values.astype(float)
        
        # Step 1: Normalize (Min-Max normalization to [0, 1])
        mins = obj_values.min(axis=0)
        maxs = obj_values.max(axis=0)
        
        # Avoid division by zero if all values in an objective are the same
        ranges = maxs - mins
        ranges[ranges == 0] = 1.0
        
        norm_values = (obj_values - mins) / ranges
        
        if method == 'knee_point':
            # Step 2: Define Utopia point in normalized space
            # For minimized objectives, ideal is 0. For maximized, ideal is 1.
            utopia = np.zeros(len(output_names))
            for i, minimize in enumerate(minimize_flags):
                if not minimize:
                    utopia[i] = 1.0
                    
            # Step 3: Calculate Euclidean distance to Utopia point
            distances = np.sqrt(np.sum((norm_values - utopia)**2, axis=1))
            pareto_df['distance_to_utopia'] = distances
            
            # Step 4: Find minimum distance
            best_idx = np.argmin(distances)
            return pareto_df.iloc[[best_idx]].copy()
            
        elif method == 'topsis':
            if weights is None:
                weights = np.ones(len(output_names)) / len(output_names)
            else:
                if len(weights) != len(output_names):
                    raise ValueError(f"Length of weights ({len(weights)}) must match number of outputs ({len(output_names)}).")
                weights = np.array(weights) / np.sum(weights)

            sq_sum = np.sqrt(np.sum(obj_values**2, axis=0))
            sq_sum[sq_sum == 0] = 1.0
            topsis_norm = obj_values / sq_sum
            
            weighted_norm = topsis_norm * weights
            
            # Determine ideal best and ideal worst
            ideal_best = np.zeros(len(output_names))
            ideal_worst = np.zeros(len(output_names))
            
            for i, minimize in enumerate(minimize_flags):
                if minimize:
                    ideal_best[i] = np.min(weighted_norm[:, i])
                    ideal_worst[i] = np.max(weighted_norm[:, i])
                else:
                    ideal_best[i] = np.max(weighted_norm[:, i])
                    ideal_worst[i] = np.min(weighted_norm[:, i])
                    
            # Distance to ideal best and worst
            d_best = np.sqrt(np.sum((weighted_norm - ideal_best)**2, axis=1))
            d_worst = np.sqrt(np.sum((weighted_norm - ideal_worst)**2, axis=1))
            
            # Closeness coefficient (C)
            # Avoid division by zero
            denom = d_best + d_worst
            denom[denom == 0] = 1.0
            closeness = d_worst / denom
            
            pareto_df['topsis_score'] = closeness
            
            # Best is maximum closeness
            best_idx = np.argmax(closeness)
            return pareto_df.iloc[[best_idx]].copy()
            
        else:
            raise ValueError(f"Unknown MCDM method: {method}")

    def run_sensitivity_analysis_by_epw(
            self,
            method: Literal['sobol', 'morris'] = 'morris',
            out_dir: str = '.',
            **kwargs
    ) -> dict:
        """
        Runs Sensitivity Analysis separately for each EPW found in
        ``outputs_param_simulation``, saves a CSV and a bar-chart PNG per EPW,
        and returns a nested dict ``{epw_label: SALib_results_dict}``.

        The results are also stored in ``self.sensitivity_results_by_epw``.

        Typical workflow::

            sim.sampling_morris(num_samples=50)
            sim.run_parametric_simulation(epws=['Seville.epw', 'Sydney.epw'], ...)
            sa = sim.run_sensitivity_analysis_by_epw(method='morris', out_dir='results')

        :param method: ``'sobol'`` or ``'morris'``. Must match the sampling
            method used before calling ``run_parametric_simulation``.
        :param out_dir: directory where CSV and PNG files will be saved.
        :param kwargs: additional keyword arguments forwarded to
            ``run_sensitivity_analysis``.
        :return: nested dict ``{epw_label: {output_name: SALib_result}}``.
        """
        import matplotlib
        import matplotlib.pyplot as plt

        if getattr(self, 'outputs_param_simulation', None) is None or self.outputs_param_simulation.empty:
            raise ValueError(
                'No parametric simulation results found. '
                'Run run_parametric_simulation before calling this method.'
            )

        os.makedirs(out_dir, exist_ok=True)
        epw_labels = self.outputs_param_simulation['epw'].unique()
        results_by_epw = {}
        original_df = self.outputs_param_simulation

        for epw_label in epw_labels:
            epw_tag = str(epw_label).replace(' ', '_')

            # Restrict to this EPW for SA
            self.outputs_param_simulation = original_df[
                original_df['epw'] == epw_label
            ].copy()

            sa_results = self.run_sensitivity_analysis(method=method, **kwargs)
            results_by_epw[epw_label] = sa_results
            self.outputs_param_simulation = original_df  # restore

            # --- Build and save tidy CSV ---
            rows = []
            if method == 'sobol':
                for output_name, res in sa_results.items():
                    for param, s1, st in zip(res['names'], res['S1'], res['ST']):
                        rows.append({
                            'epw': epw_tag, 'output': output_name,
                            'parameter': param,
                            'S1': round(float(s1), 4),
                            'ST': round(float(st), 4),
                        })
                x_labels = ('S1 (first-order)', 'ST (total-order)')
                bar_keys = ('S1', 'ST')
                y_label = 'Sobol Index'
                title_prefix = 'Sobol Sensitivity'
                bar_colours = ('#457b9d', '#e63946')
                ylim = (0, 1)
            else:  # morris
                for output_name, res in sa_results.items():
                    for param, mu, mu_star, sigma in zip(
                        res['names'], res['mu'], res['mu_star'], res['sigma']
                    ):
                        rows.append({
                            'epw': epw_tag, 'output': output_name,
                            'parameter': param,
                            'mu': round(float(mu), 4),
                            'mu_star': round(float(mu_star), 4),
                            'sigma': round(float(sigma), 4),
                        })
                x_labels = ('mu* (importance)', 'sigma (interactions)')
                bar_keys = ('mu_star', 'sigma')
                y_label = 'Morris Index'
                title_prefix = 'Morris Sensitivity'
                bar_colours = ('#457b9d', '#e63946')
                ylim = None

            sa_df = pd.DataFrame(rows)
            fname_csv = os.path.join(out_dir, f'results_sa_{method}_{epw_tag}.csv')
            sa_df.to_csv(fname_csv, index=False)
            print(f'  SA ({method}) results saved: {fname_csv}')

            # --- Bar chart per output ---
            output_names_sa = list(sa_results.keys())
            n_outputs = len(output_names_sa)
            fig, axes = plt.subplots(1, n_outputs, figsize=(6 * n_outputs, 5), squeeze=False)
            width = 0.35
            for ax_idx, output_name in enumerate(output_names_sa):
                res = sa_results[output_name]
                ax_sa = axes[0][ax_idx]
                x = np.arange(len(res['names']))
                vals_a = np.abs(res[bar_keys[0]])
                vals_b = np.abs(res[bar_keys[1]])
                ax_sa.bar(x - width / 2, vals_a, width,
                          label=x_labels[0], color=bar_colours[0], alpha=0.85)
                ax_sa.bar(x + width / 2, vals_b, width,
                          label=x_labels[1], color=bar_colours[1], alpha=0.85)
                ax_sa.set_xticks(x)
                ax_sa.set_xticklabels(res['names'], rotation=30, ha='right', fontsize=9)
                ax_sa.set_ylabel(y_label, fontsize=10)
                ax_sa.set_title(f'{title_prefix} — {output_name}\n[{epw_tag}]', fontsize=10)
                ax_sa.legend(fontsize=8)
                if ylim:
                    ax_sa.set_ylim(*ylim)
                ax_sa.axhline(0, color='k', lw=0.5)
            plt.tight_layout()
            fname_plot = os.path.join(out_dir, f'plot_sa_{method}_{epw_tag}.png')
            plt.savefig(fname_plot, dpi=300, bbox_inches='tight')
            plt.close()
            print(f'  SA ({method}) plot saved: {fname_plot}')

        self.sensitivity_results_by_epw = results_by_epw
        return results_by_epw

    def plot_best_compromise_solutions(
            self,
            out_dir: str = '.',
            mcdm_configs: list = None,
    ) -> pd.DataFrame:
        """
        Identifies the best compromise solution(s) from the Pareto front for
        each EPW found in ``outputs_optimisation``, saves the results to a
        CSV and a scatter-plot PNG, and returns the combined DataFrame.

        :param out_dir: directory where output files will be saved.
        :param mcdm_configs: list of dicts, each specifying one MCDM run.
            Each dict must have a ``'method'`` key (``'knee_point'`` or
            ``'topsis'``) and may optionally have:

            - ``'weights'``: list of per-objective weights (TOPSIS only).
            - ``'label'``: string label used in the legend and CSV column
              (auto-generated if omitted).

            Default (when ``None``)::

                [
                    {'method': 'knee_point'},
                    {'method': 'topsis'},
                    {'method': 'topsis', 'weights': [0.7, 0.3], 'label': 'topsis_w70_30'},
                ]

        :return: pandas DataFrame with all best solutions (one row per
            EPW × MCDM method), also saved to CSV.
        """
        import matplotlib.pyplot as plt

        if getattr(self, 'outputs_optimisation', None) is None or self.outputs_optimisation.empty:
            raise ValueError(
                'No optimisation results found. '
                'Run run_optimisation (or load via load_outputs_optimisation) first.'
            )

        os.makedirs(out_dir, exist_ok=True)

        if mcdm_configs is None:
            output_names = self.problem.names('outputs')
            n_obj = len(output_names)
            mcdm_configs = [
                {'method': 'knee_point'},
                {'method': 'topsis'},
                {'method': 'topsis',
                 'weights': [0.7] + [0.3 / max(n_obj - 1, 1)] * (n_obj - 1),
                 'label': 'topsis_w70_30'},
            ]

        # Auto-generate labels if missing
        label_counts: dict = {}
        for cfg in mcdm_configs:
            if 'label' not in cfg:
                base = cfg['method']
                label_counts[base] = label_counts.get(base, 0) + 1
                suffix = '' if label_counts[base] == 1 else f'_{label_counts[base]}'
                cfg['label'] = f"{base}{suffix}"

        # Colour / marker scheme for up to 8 configs
        _marker_cycle = ['*', 'D', 's', '^', 'P', 'X', 'v', 'o']
        _colour_cycle = ['#e63946', '#f4a261', '#2a9d8f', '#e9c46a',
                         '#264653', '#a8dadc', '#457b9d', '#6d6875']
        _size_cycle   = [220, 120, 120, 120, 120, 120, 120, 120]

        epw_labels = self.outputs_optimisation['epw'].unique()
        output_names = self.problem.names('outputs')
        heating_col = next((c for c in output_names if 'Heating' in c), output_names[0])
        _fallback_cool = output_names[-1] if len(output_names) > 1 else output_names[0]
        cooling_col = next((c for c in output_names if 'Cooling' in c), _fallback_cool)

        all_mcdm_rows = []
        original_optim = self.outputs_optimisation

        for epw_label in epw_labels:
            epw_tag = str(epw_label).replace(' ', '_')
            self.outputs_optimisation = original_optim[
                original_optim['epw'] == epw_label
            ].copy()

            print(f'\n  [{epw_tag}] Best compromise solutions:')
            for cfg in mcdm_configs:
                method = cfg['method']
                weights = cfg.get('weights', None)
                label = cfg['label']
                row_df = self.get_best_compromise_solution(method=method, weights=weights)
                row_df = row_df.copy()
                row_df['mcdm_method'] = label
                row_df['epw'] = epw_tag
                all_mcdm_rows.append(row_df)

                h_kwh = row_df[heating_col].iloc[0] / 3.6e6
                c_kwh = row_df[cooling_col].iloc[0] / 3.6e6
                print(f'    {label:25s} | {heating_col}={h_kwh:.1f} kWh'
                      f' | {cooling_col}={c_kwh:.1f} kWh')

            self.outputs_optimisation = original_optim  # restore

        mcdm_df = pd.concat(all_mcdm_rows, ignore_index=True)
        fname_csv = os.path.join(out_dir, 'results_mcdm_best_solutions.csv')
        mcdm_df.to_csv(fname_csv, index=False)
        print(f'\n  MCDM summary saved: {fname_csv}')

        # --- Figure: one subplot per EPW ---
        fig, axes = plt.subplots(
            1, len(epw_labels),
            figsize=(8 * len(epw_labels), 6),
            squeeze=False
        )
        for ax_idx, epw_label in enumerate(epw_labels):
            epw_tag = str(epw_label).replace(' ', '_')
            ax_m = axes[0][ax_idx]
            df_epw = original_optim[original_optim['epw'] == epw_label].copy()
            df_epw['_h'] = df_epw[heating_col] / 3.6e6
            df_epw['_c'] = df_epw[cooling_col] / 3.6e6

            dom = df_epw[~df_epw['pareto-optimal']]
            par = df_epw[df_epw['pareto-optimal']]
            ax_m.scatter(dom['_h'], dom['_c'], c='#cccccc', alpha=0.3, s=15, zorder=1)
            ax_m.scatter(par['_h'], par['_c'], c='#457b9d', alpha=0.6, s=40,
                         edgecolors='k', linewidths=0.4, zorder=2, label='Pareto-optimal')

            for i, cfg in enumerate(mcdm_configs):
                label = cfg['label']
                row = mcdm_df[
                    (mcdm_df['epw'] == epw_tag) &
                    (mcdm_df['mcdm_method'] == label)
                ]
                if row.empty:
                    continue
                h = row[heating_col].iloc[0] / 3.6e6
                c = row[cooling_col].iloc[0] / 3.6e6
                ax_m.scatter(
                    h, c,
                    marker=_marker_cycle[i % len(_marker_cycle)],
                    c=_colour_cycle[i % len(_colour_cycle)],
                    s=_size_cycle[i % len(_size_cycle)],
                    zorder=5, edgecolors='k', linewidths=0.6, label=label
                )

            ax_m.set_xlabel(f'{heating_col} (kWh)', fontsize=11)
            ax_m.set_ylabel(f'{cooling_col} (kWh)', fontsize=11)
            ax_m.set_title(f'Pareto Front + MCDM best solutions\n[{epw_tag}]', fontsize=11)
            ax_m.legend(fontsize=9)

        plt.tight_layout()
        fname_plot = os.path.join(out_dir, 'plot_mcdm_best_solutions.png')
        plt.savefig(fname_plot, dpi=300, bbox_inches='tight')
        plt.close()
        print(f'  MCDM plot saved: {fname_plot}')

        return mcdm_df

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

