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
from accim.parametric_and_optimisation.main import OptimParamSimulation

# 1. check output data
# 2. check input dataframe
# 3. run parametric_and_optimisation simulation




#Arguments
idf_path = 'TestModel.idf'

building = ef.get_building(idf_path)

accim.utils.set_occupancy_to_always(idf_object=building)

new_test = OptimParamSimulation()

test_class_instance = OptimParamSimulation(
    building=building,
    parameters_type='accim predefined model'
    # output_keep_existing=False,
    # debugging=True

)

# Setting the Output:Variable and Output:Meter objects in the idf
#todo do not print on screen the process of accis, only the first time
df_output_variables_idf = test_class_instance.get_output_var_df_from_idf()

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

test_class_instance.set_output_var_df_to_idf(outputs_df=df_output_variables_idf_mod)

output_meters = [
    # 'HeatingCoils:EnergyTransfer',
    # 'CoolingCoils:EnergyTransfer',
    'Heating:Electricity',
    'Cooling:Electricity',
    'Electricity:HVAC',
]
test_class_instance.set_output_met_objects_to_idf(output_meters=output_meters)

# Checking the Output:Meter and Output:Variable objects in the simulation
df_outputmeters_2, df_outputvariables_2 = test_class_instance.get_outputs_df_from_testsim()

#Other variables could be reported. These can be read in the rdd, mdd and mtd files
df_rdd = get_rdd_file_as_df()
df_mdd = get_mdd_file_as_df()
meter_list = parse_mtd_file()


# To end with outputs, let's set the objective outputs (outputs for the Problem object), which are those displayed by BESOS in case of parametric_and_optimisation analysis, or used in case of optimisation

def average_results(result):
    return result.data["Value"].mean()
def sum_results(result):
    return result.data["Value"].sum()

def return_time_series(result):
    return result.data["Value"].to_list()

df_outputmeters_3 = df_outputmeters_2.copy()
df_outputvariables_3 = df_outputvariables_2.copy()

df_outputvariables_3['func'] = return_time_series
df_outputvariables_3 = df_outputvariables_3.drop(index=[2, 4])
df_outputvariables_3['name'] = df_outputvariables_3['variable_name'] + '_time series'

test_class_instance.set_outputs_for_simulation(
    df_output_meter=df_outputmeters_3,
    # df_output_variable=df_outputvariables_3,
    df_output_variable=df_outputvariables_3,
    # func=average_results
)

# At this point, the outputs of each energyplus simulation has been set. So, next step is setting parameters

#todo make 3 different types: predefined_accis, custom_accis and apmv_setpoints

# accis.modifyAccis(
#     idf=building,
#     ComfStand=99,
#     ComfMod=3,
#     CAT=80,
#     HVACmode=2,
#     VentCtrl=0,
# )


# accis_parameters = {
#     'CustAST_m': (0.01, 0.99),
#     'CustAST_n': (5, 23),
#     'CustAST_ASToffset': (2, 4),
#     'CustAST_ASTall': (10, 15),
#     'CustAST_ASTaul': (30, 35),
# }


accis_parameters = {
    'ComfStand': [1, 2],
    'CAT': [80, 90],
    'ComfMod': [3],
}


# from besos.parameters import wwr, RangeParameter
# other_parameters = [wwr(RangeParameter(0.1, 0.9))]

test_class_instance.set_parameters(
    accis_params_dict=accis_parameters,
    # additional_params=other_parameters
)

# Let's set the problem
test_class_instance.set_problem()

# Let's generate a sampling dataframe
# test_class_instance.sampling_full_factorial(level=5)
# temp_full_fac = test_class_instance.parameters_values_df

# test_class_instance.sampling_lhs(num_samples=3)
# temp_lhs = test_class_instance.parameters_values_df

test_class_instance.sampling_full_set()
temp_full_set = test_class_instance.parameters_values_df

#todo try to return series of pmot, acst, ahst and optemp and plot them in facetgrid
outputs = test_class_instance.run_parametric_simulation(
    epws=[
        'Sydney.epw',
        'Seville.epw'
    ],
    out_dir='WIP_testing predefined models',
    df=temp_full_set,
    processes=6,
)

outputs = outputs.reset_index()

outputs.to_excel('WIP_outputs.xlsx')

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




##

