import os
import re

import accim

import pandas as pd
import warnings
import besos
from besos import eppy_funcs as ef, sampling
from besos.evaluator import EvaluatorEP
from besos.optimizer import NSGAII, df_solution_to_solutions
from besos.parameters import RangeParameter, expand_plist, wwr, FieldSelector, Parameter, GenericSelector, \
    CategoryParameter
from besos.problem import EPProblem
from besos.eplus_funcs import get_idf_version, run_building
from matplotlib import pyplot as plt
from platypus import Archive, Hypervolume, Solution
from besos.eplus_funcs import print_available_outputs
from besos.objectives import VariableReader, MeterReader

from accim.utils import print_available_outputs_mod, modify_timesteps, set_occupancy_to_always, remove_accents_in_idf
import numpy as np

import accim.sim.accis_single_idf_funcs as accis
import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf

import accim.parametric_and_optimisation.parameters_accis as params

# 1. check output data
# 2. check input dataframe
# 3. run parametric_and_optimisation simulation




class ParametricSimulation:
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
        self.ScriptType = ScriptType
        self.SupplyAirTempInputMethod = SupplyAirTempInputMethod
        self.output_keep_existing = output_keep_existing
        self.output_type = output_type
        # self.output_take_dataframe = set_outputs_df
        self.output_freqs = output_freqs
        self.building = building

        accis.addAccis(
            idf=building,
            ScriptType=ScriptType,
            SupplyAirTempInputMethod=SupplyAirTempInputMethod,
            Output_keep_existing=output_keep_existing,
            Output_type=output_type,
            # Output_take_dataframe=set_outputs_df,
            Output_freqs=output_freqs,

            # EnergyPlus_version='9.4',
            TempCtrl='temperature',
            # Output_gen_dataframe=True,
            # make_averages=True,
            debugging=debugging
        )
    def get_output_var_df_from_idf(self):
        """
        Gets a pandas DataFrame which contains the Output:Variable objects from the idf.
        Therefore, it may contain wildcards such as '*', which means the variable is requested
        for all zones.

        :return:
        """
        output_variable_df = accis.gen_outputs_df(
            idf=self.building,
            ScriptType=self.ScriptType,
            Output_keep_existing=self.output_keep_existing,
            Output_type=self.output_type,
            Output_freqs=self.output_freqs,
            TempCtrl='temperature',
        )

        return output_variable_df

    def set_output_var_df_to_idf(self, outputs_df: pd.DataFrame = None):
        """
        Keeps the Output:Variable objects contained in the input pandas DataFrame and removes
        all others. This is important to save space if thousands of simulations with heavy outputs
        are run.

        :type outputs_df: pd.DataFrame
        :param outputs_df: the DataFrame containing Output:Variable objects to be kept
        :return:
        """
        accis.addAccis(
            idf=self.building,
            ScriptType=self.ScriptType,
            SupplyAirTempInputMethod=self.SupplyAirTempInputMethod,
            Output_keep_existing=self.output_keep_existing,
            Output_type=self.output_type,
            Output_take_dataframe=outputs_df,
            Output_freqs=self.output_freqs,

            # EnergyPlus_version='9.4',
            TempCtrl='temperature',
            # Output_gen_dataframe=True,
            # make_averages=True,
            # debugging=True
        )
    def set_output_met_objects_to_idf(self, output_meters):
        for meter in output_meters:
            for freq in self.output_freqs:
                self.building.newidfobject(
                    key='OUTPUT:METER',
                    Key_Name=meter,
                    Reporting_Frequency=freq
                )

    def get_outputs_df_from_testsim(self):
        """
        Gets a pandas DataFrame which contains the Output:Variable objects from a test simulation.
        Therefore, it won't contain wildcards such as '*'.

        :return:
        """
        available_outputs = print_available_outputs_mod(self.building)
        df_outputmeters = pd.DataFrame(
            available_outputs.meterreaderlist,
            columns=['meter_name', 'frequency']
        )
        df_outputvariables = pd.DataFrame(
            available_outputs.variablereaderlist,
            columns=['key_value', 'variable_name', 'frequency']
        )

        return df_outputmeters, df_outputvariables

    def get_rdd_file_as_df(self):
        rdd_df = pd.read_csv(
            filepath_or_buffer='available_outputs/eplusout.rdd',
            sep=',|;',
            skiprows=2,
            names=['object', 'key_value', 'variable_name', 'frequency', 'units']
        )
        return rdd_df

    def get_mdd_file_as_df(self):
        mdd_df = pd.read_csv(
            filepath_or_buffer='available_outputs/eplusout.mdd',
            sep=',|;',
            skiprows=2,
            names=['object', 'meter_name', 'frequency', 'units']
        )
        return mdd_df

    def parse_mtd_file(self):
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


    def set_outputs_for_parametric_simulation(
            self,
            df_output_variable: pd.DataFrame = None,
            df_output_meter: pd.DataFrame = None,
    ):
        # objs_meters = [MeterReader(key_name=i, name=i) for i in output_meters]
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
                df_output_meter['output_name'] = df_output_meter['meter_name']

        objs_meters = []
        if df_output_meter is not None:
            for i in df_output_meter.index:
                if 'func' in [c for c in df_output_meter.columns]:
                    objs_meters.append(
                            MeterReader(
                                key_name=df_output_meter.loc[i, 'meter_name'],
                                frequency=df_output_meter.loc[i, 'frequency'],
                                name=df_output_meter.loc[i, 'output_name'],
                                func=df_output_meter.loc[i, 'func'],
                            )
                        )
                else:
                    objs_meters.append(
                        MeterReader(
                            key_name=df_output_meter.loc[i, 'meter_name'],
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

        self.param_sim_outputs = objs_meters + objs_variables

    def set_parameters(self, accis_params_dict, additional_params: list = None):
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

        parameters_list = [params.accis_parameter(k, v) for k, v in accis_params_dict.items()]
        if additional_params is not None:
            parameters_list.extend(additional_params)

        self.parameters_list = parameters_list
        self.descriptors_has_options = descriptors_has_options

    def set_problem(self):
        problem = EPProblem(
            inputs=self.parameters_list,
            outputs=self.param_sim_outputs
        )
        self.problem = problem

    def sampling_full_set(self):
        if self.descriptors_has_options:
            num_samples = 1
            parameters_values = {}
            for p in self.parameters_list:
                num_samples = num_samples * len(p.value_descriptors[0].options)
                parameters_values.update({p.value_descriptors[0].name: p.value_descriptors[0].options})
            from itertools import product
            combinations = list(product(*parameters_values.values()))
            parameters_values_df = pd.DataFrame(combinations, columns=parameters_values.keys())

        self.parameters_values_df = parameters_values_df

    def sampling_full_factorial(self, level: int):
        parameters_values_df = sampling.dist_sampler(
            sampling.full_factorial,
            self.problem,
            num_samples=2,
            level=level
        )
        self.parameters_values_df = parameters_values_df


    def sampling_lhs(self, num_samples: int):
        parameters_values_df = sampling.dist_sampler(
            sampling.lhs,
            self.problem,
            num_samples=num_samples
        )
        self.parameters_values_df = parameters_values_df

    def set_evaluator(
            self,
            epw: str,
            out_dir: str,
    ):
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
    ):
        outputs_dict = {}
        for epw in epws:
            epwname = epw.split('.epw')[0]
            evaluator = EvaluatorEP(
                problem=self.problem,
                building=self.building,
                epw=epw,
                out_dir=out_dir
            )

            outputs = evaluator.df_apply(
                df=df,
                keep_input=keep_input,
                keep_dirs=keep_dirs,
                processes=processes
            )
            outputs['epw'] = epwname
            outputs_dict.update({epwname: outputs})
        all_outputs = pd.concat([df for df in outputs_dict.values()])
        return all_outputs

class AccimPredefModelsParamSim(ParametricSimulation):
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

