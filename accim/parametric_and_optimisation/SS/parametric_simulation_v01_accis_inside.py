import os
import re

import pandas as pd
import warnings
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

import accim.parametric_and_optimisation.parameters as params

# 1. check output data
# 2. check input dataframe
# 3. run parametric_and_optimisation simulation




#Arguments
idf_path = 'TestModel.idf'

building = ef.get_building(idf_path)




# # Outputs
# output_type = 'standard'
# output_variables = []
# output_meters = [
#     'HeatingCoils:EnergyTransfer',
#     'CoolingCoils:EnergyTransfer',
#     'Heating:Electricity',
#     'Cooling:Electricity',
#     'Electricity:HVAC',
# ]
# df = pd.DataFrame()
#
# #Parameters
# accis_parameters = {
#     'CustAST_m': [0.3, 0.4, 0.5],
#     'CustAST_n': [15, 20]
# }
# other_parameters = []






# accis.modifyAccis(
#     idf=building,
#
# )
#
class ParametricSimulation:
    def __init__(
            self,
            building,
            output_type: str = 'standard',
            # set_outputs_df: pd.DataFrame = None,
            output_keep_existing: bool = False,
            output_freqs: list = ['hourly'],
            ScriptType: str = 'vrf_mm',
            SupplyAirTempInputMethod: str = 'temperature difference',

    ):
        self.ScriptType = ScriptType
        self.SupplyAirTempInputMethod = SupplyAirTempInputMethod
        self.output_keep_existing = output_keep_existing
        self.output_type = output_type
        # self.output_take_dataframe = set_outputs_df
        self.output_freqs = output_freqs

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
            # debugging=True
        )

        pass
    def get_output_var_df_from_idf(self):
        """
        Gets a pandas DataFrame which contains the Output:Variable objects from the idf.
        Therefore, it may contain wildcards such as '*', which means the variable is requested
        for all zones.

        :return:
        """
        output_variable_df = accis.gen_outputs_df(
            idf=building,
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
            idf=building,
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
                building.newidfobject(
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
        available_outputs = print_available_outputs_mod(building)
        df_outputmeters = pd.DataFrame(
            available_outputs.meterreaderlist,
            columns=['output:meter', 'frequency']
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

    def set_outputs_for_parametric_simulation(self, df_output_variable, output_meters):
        objs_meters = [MeterReader(key_name=i, name=i) for i in output_meters]
        objs_variables = []
        for i in df_output_variable.index:
            objs_variables.append(
                    VariableReader(
                        key_value=df_output_variable.loc[i, 'key_value'],
                        variable_name=df_output_variable.loc[i, 'variable_name'],
                        frequency=df_output_variable.loc[i, 'frequency'],
                        name=df_output_variable.loc[i, 'variable_name'],
                        # func=mean
                    )
                )
        self.param_sim_outputs = objs_meters + objs_variables


test_class_instance = ParametricSimulation(building=building)

# Setting the Output:Variable objects in the idf
#todo do not print on screen the process of accis, only the first time
df_output_variables_idf = test_class_instance.get_output_var_df_from_idf()

df_output_variables_idf_mod = df_output_variables_idf.copy()
df_output_variables_idf_mod = df_output_variables_idf_mod[
    (
        df_output_variables_idf_mod['variable_name'].str.contains('Setpoint Temperature_No Tolerance')
        |
        df_output_variables_idf_mod['variable_name'].str.contains('AFN Zone Ventilation Air Change Rate')
    )
]

test_class_instance.set_output_var_df_to_idf(outputs_df=df_output_variables_idf_mod)

output_meters = [
    'HeatingCoils:EnergyTransfer',
    'CoolingCoils:EnergyTransfer',
    'Heating:Electricity',
    'Cooling:Electricity',
    'Electricity:HVAC',
]
test_class_instance.set_output_met_objects_to_idf(output_meters=output_meters)

# Checking the Output:Meter and Output:Variable objects in the simulation
df_outputmeters_2, df_outputvariables_2 = test_class_instance.get_outputs_df_from_testsim()

#Other variables could be reported. These can be read in the rdd, mdd and mtd files
df_rdd = test_class_instance.get_rdd_file_as_df()
df_mdd = test_class_instance.get_mdd_file_as_df()
meter_list = test_class_instance.parse_mtd_file()

# To end with outputs, let's set the objective outputs (outputs for the Problem object), which are those displayed by BESOS in case of parametric_and_optimisation analysis, or used in case of optimisation

test_class_instance.set_outputs_for_parametric_simulation(
    output_meters=output_meters,
    df_output_variable=df_outputvariables_2
)


# At this point, the outputs of each energyplus simulation has been set. So, next step is setting parameters


##





##
# remove_accents_in_idf(idf_path=idf_path)

# gv = [i for i in building.idfobjects['EnergyManagementSystem:GlobalVariable']]
# [i.Variable_Name for i in building.idfobjects['output:variable'] if 'Occupied Discomfortable' in i.Variable_Name]



[i.Variable_Name for i in building.idfobjects['output:variable']]
[i for i in building.idfobjects['output:variable']]
[i for i in building.idfobjects['output:meter']]



[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setinputdata']
bf.modify_ComfStand(building, 99)
bf.modify_CAT(building, 80)
bf.modify_ComfMod(building, 3)
bf.modify_MinOToffset(building, 50)
bf.modify_MaxWindSpeed(building, 50)
bf.modify_VentCtrl(building, 2)
bf.modify_ASTtol(building, 0.1)

[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setvofinputdata']
bf.modify_MultiplierVOF(building, 0.1)
bf.modify_MaxTempDiffVOF(building, 6)


[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'applycat']



parameters_list = [params.accis_parameter(k, v) for k, v in accis_parameters.items()]
parameters_list.extend(other_parameters)






def avg(result):
    return result.data["Value"].sum()/2

def mean(result):
    return result.data["Value"].mean()

# Objectives






# obj_avg = [MeterReader(key_name='TOTAL OCCUPIED DISCOMFORTABLE HOURS', func=avg, name='AVERAGE OCCUPIED DISCOMFORTABLE HOURS')]


problem = EPProblem(
    inputs=parameters_list,
    # outputs=objectives+objs_variables
    outputs=objs_meters+objs_variables
)





num_samples = 1
parameters_values = {}
# for p in accis_parameters:
#     num_samples = num_samples*len(p.value_descriptor.options)
for p in parameters_list:
    num_samples = num_samples*len(p.value_descriptors[0].options)
    parameters_values.update({p.value_descriptors[0].name: p.value_descriptors[0].options})

time_hours_considering_6_cpus = num_samples*75/3600/6
time_days_considering_6_cpus = time_hours_considering_6_cpus/24

from itertools import product
combinations = list(product(*parameters_values.values()))
parameters_values_df = pd.DataFrame(combinations, columns=parameters_values.keys())

# parameters_values_df_part = parameters_values_df.copy()
# CustAST_ASTaul_value = 20
# parameters_values_df_part = parameters_values_df_part[
#     parameters_values_df_part['CustAST_ASTaul'] == CustAST_ASTaul_value
# ]

# parameters_values_df_part_test = parameters_values_df_part[0:5]

# inputs_fullfactorial = sampling.dist_sampler(sampling.full_factorial, problem, num_samples=num_samples, level=20)
# inputs_fullfactorial = inputs_fullfactorial.drop_duplicates()
# inputs_fullfactorial = inputs_fullfactorial.reset_index().drop(columns=['index'])
# inputs_lhs


# inputs_full_factorial = sampling.dist_sampler(sampling.full_factorial, problem)

##


evaluator = EvaluatorEP(
    problem=problem,
    building=building,
    epw='Sydney.epw',
    out_dir=f'testing param sim'
)

outputs = evaluator.df_apply(
    parameters_values_df,
    keep_input=True,
    keep_dirs=True,
    # out_dir='outdir',
    processes=6
)

# outputs.to_excel('outputs_for_ASTaul_value_20.xlsx')
# outputs_mod = outputs
# outputs_mod['energy ratio'] = outputs_mod['HVAC Electricity Usage'] / outputs_mod['Total Electricity Usage']

# generated_buildings = [evaluator.generate_building(df=samples_short, index=i, file_name=f'short_sample_row_{i}') for i in range(5)]
# evaluator.generate_building(df=inputs_lhs, index=0, file_name='num_0')
# evaluator.generate_building(df=inputs_lhs, index=1, file_name='num_1')
# evaluator.generate_building(df=inputs_lhs, index=2, file_name='num_2')
# evaluator.generate_building(df=inputs_lhs, index=3, file_name='num_3')
# evaluator.generate_building(df=inputs_lhs, index=4, file_name='num_4')

##
