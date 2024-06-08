import os
import re

import accim

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
from accim.parametric_and_optimisation.main import OptimParamSimulation, get_mdd_file_as_df, get_rdd_file_as_df, parse_mtd_file

# 1. check output data
# 2. check input dataframe
# 3. run parametric_and_optimisation simulation




#Arguments
idf_path = 'TestModel.idf'

building = ef.get_building(idf_path)

accim.utils.set_occupancy_to_always(idf_object=building)

parametric = OptimParamSimulation(
    building=building,
    parameters_type='accim custom model'
    # output_keep_existing=False,
    # debugging=True

)

# Setting the Output:Variable and Output:Meter objects in the idf
#todo do not print on screen the process of accis, only the first time
df_output_variables_idf = parametric.get_output_var_df_from_idf()

df_output_variables_idf_mod = df_output_variables_idf.copy()

[i for i in df_output_variables_idf['variable_name'] if 'Running Average Outdoor' in i]

df_output_variables_idf_mod = df_output_variables_idf_mod[
    (
        df_output_variables_idf_mod['variable_name'].str.contains('Setpoint Temperature_No Tolerance')
        |
        df_output_variables_idf_mod['variable_name'].str.contains('Zone Operative Temperature')
        |
        df_output_variables_idf_mod['variable_name'].str.contains('Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature')
    )
]

[i for i in building.idfobjects['energymanagementsystem:program'] if i.Name.lower() == 'setinputdata']

parametric.set_output_var_df_to_idf(outputs_df=df_output_variables_idf_mod)

output_meters = [
    # 'HeatingCoils:EnergyTransfer',
    # 'CoolingCoils:EnergyTransfer',
    'Heating:Electricity',
    'Cooling:Electricity',
    'Electricity:HVAC',
]
parametric.set_output_met_objects_to_idf(output_meters=output_meters)

# Checking the Output:Meter and Output:Variable objects in the simulation
# df_outputmeters_2, df_outputvariables_2 = parametric.get_outputs_df_from_testsim()

#Other variables could be reported. These can be read in the rdd, mdd and mtd files
# df_rdd = get_rdd_file_as_df()
# df_mdd = get_mdd_file_as_df()
# meter_list = parse_mtd_file()


# To end with outputs, let's set the objective outputs (outputs for the Problem object), which are those displayed by BESOS in case of parametric_and_optimisation analysis, or used in case of optimisation

# def average_results(result):
#     return result.data["Value"].mean()
# def sum_results(result):
#     return result.data["Value"].sum()
#
# def return_time_series(result):
#     return result.data["Value"].to_list()
#
# df_outputmeters_3 = df_outputmeters_2.copy()
# df_outputvariables_3 = df_outputvariables_2.copy()
#
# df_outputvariables_3['func'] = return_time_series
# df_outputvariables_3 = df_outputvariables_3.drop(index=[2, 4])
# df_outputvariables_3['name'] = df_outputvariables_3['variable_name'] + '_time series'
#
# parametric.set_outputs_for_simulation(
#     df_output_meter=df_outputmeters_3,
#     # df_output_variable=df_outputvariables_3,
#     df_output_variable=df_outputvariables_3,
#     # func=average_results
# )

# At this point, the outputs of each energyplus simulation has been set. So, next step is setting parameters




accis_parameters = {
    'CustAST_m': (0.01, 0.99),
    'CustAST_n': (5, 23),
    'CustAST_ASToffset': (2, 4),
    # 'CustAST_ASTall': (10, 15),
    # 'CustAST_ASTaul': (30, 35),
}


# accis_parameters = {
#     'ComfStand': [1, 2, 3],
#     'CAT': [1, 2, 3],
#     'ComfMod': [3],
# }

# bf.modify_CustAST_ASTaul(building, 35)
# bf.modify_CustAST_ASTall(building, 10)

# from besos.parameters import wwr, RangeParameter
# other_parameters = [wwr(RangeParameter(0.1, 0.9))]

parametric.set_parameters(
    accis_params_dict=accis_parameters,
    # additional_params=other_parameters
)

#todo if custom models, check if any of the arguments is not defined: those defined in the parameters can be 0, but the remaining cannot

args = accim.utils.get_accim_args(building)
args['CustAST']
# parameters_defined = [i.value_descriptors[0].name for i in parametric.parameters_list]
# parameters_to_check = [k for k, v in args['CustAST'].items() if 'CustAST_'+k not in parameters_defined and v==0]
# if 'CustAST_ASToffset' in parameters_defined:
#     try:
#         parameters_to_check.remove('AHSToffset')
#         parameters_to_check.remove('ACSToffset')
#     except ValueError:
#         pass
# if 'CustAST_ASTall' in parameters_defined:
#     try:
#         parameters_to_check.remove('AHSTall')
#         parameters_to_check.remove('ACSTall')
#     except ValueError:
#         pass
# if 'CustAST_ASTaul' in parameters_defined:
#     try:
#         parameters_to_check.remove('AHSTaul')
#         parameters_to_check.remove('ACSTaul')
#     except ValueError:
#         pass
#
# parameters_to_be_defined = []
# for p in parameters_to_check:
#     if args['CustAST'][p] == 0:
#         parameters_to_be_defined.append(p)
# if len(parameters_to_be_defined) > 0:
#     raise ValueError(f'The following parameters are not included in the parameters to be set, '
#                      f'and have not been defined yet (i.e. the value is 0): '
#                      f'{parameters_to_be_defined}')

##
param_dict = {
    'CustAST_m': [0.1, 0.6],
    'CustAST_n': [22, 8],
    'CustAST_ASToffset': [2.5, 4],
    'CustAST_ASTall': [10, 10],
    'CustAST_ASTaul': [35, 35],
}
from accim.parametric_and_optimisation.utils import make_all_combinations
all_combinations = make_all_combinations(param_dict)

##

[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setinputdata']
[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setvofinputdata']
[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'applycat']

##
from accim.utils import get_accim_args

args = get_accim_args(building)
args['SetInputData'].obj

# building.savecopy('TestModel_mod.idf')
##



##
# Let's set the problem
parametric.set_problem()

# Let's generate a sampling dataframe
parametric.sampling_full_factorial(level=5)
temp_full_fac = parametric.parameters_values_df

parametric.sampling_lhs(num_samples=3)
temp_lhs = parametric.parameters_values_df

# parametric.sampling_full_set()
# temp_full_set = parametric.parameters_values_df

#todo try to return series of pmot, acst, ahst and optemp and plot them in facetgrid
outputs = parametric.run_parametric_simulation(
    epws=[
        'Sydney.epw',
        'Seville.epw'
    ],
    out_dir='WIP_testing accim custom models',
    df=temp_lhs,
    processes=6,
)

outputs = outputs.reset_index()

outputs.to_excel('WIP_outputs_custom.xlsx')

##


import seaborn as sns
import ast
rmot = [i for i in outputs.columns if 'Running' in i][0]
optemp = [i for i in outputs.columns if 'Operative' in i][0]
ahst = [i for i in outputs.columns if 'Adaptive Heating' in i][0]
acst = [i for i in outputs.columns if 'Adaptive Cooling' in i][0]

# sns.scatterplot(
#     x=[float(i) for i in outputs.loc[1][rmot]],
#     y=[float(i) for i in outputs.loc[1][optemp]]
# )

fig, axs = plt.subplots(
    nrows=len(outputs),
    figsize=(10, 5)
)
for i in outputs.index:
    for c in [optemp, acst, ahst]:
        x = ast.literal_eval(outputs.loc[i, rmot])
        y = ast.literal_eval(outputs.loc[i, c])

        sns.scatterplot(
            x=x,
            y=y,
            ax=axs[i]
        )


##

##



##
# remove_accents_in_idf(idf_path=idf_path)

# gv = [i for i in building.idfobjects['EnergyManagementSystem:GlobalVariable']]
# [i.Variable_Name for i in building.idfobjects['output:variable'] if 'Occupied Discomfortable' in i.Variable_Name]











# Objectives






# obj_avg = [MeterReader(key_name='TOTAL OCCUPIED DISCOMFORTABLE HOURS', func=avg, name='AVERAGE OCCUPIED DISCOMFORTABLE HOURS')]





