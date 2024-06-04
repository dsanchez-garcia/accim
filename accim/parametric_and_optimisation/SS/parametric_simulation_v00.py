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

import accim.parametric_and_optimisation.parameters_accis as params

# 1. check output data
# 2. check input dataframe
# 3. run parametric_and_optimisation simulation

#Arguments
idf_path = 'TestModel.idf'

# Outputs
output_type = 'standard'
output_variables = []
output_meters = [
    'HeatingCoils:EnergyTransfer',
    'CoolingCoils:EnergyTransfer',
    'Heating:Electricity',
    'Cooling:Electricity',
    'Electricity:HVAC',
]
df = pd.DataFrame()

#Parameters
accis_parameters = {
    'CustAST_m': [0.3, 0.4, 0.5],
    'CustAST_n': [15, 20]
}
other_parameters = []



# remove_accents_in_idf(idf_path=idf_path)

building = ef.get_building(idf_path)

# params.Parameter('ComfStand').name
# params.Parameter('ComfStand').modify(building, 15)
#
# params.Parameter('ComfStand').


accis.addAccis(
    idf=building,
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type=output_type,
    # Output_take_dataframe=df,
    Output_freqs=['hourly'],

    # EnergyPlus_version='9.4',
    TempCtrl='temperature',
    # Output_gen_dataframe=True,
    # make_averages=True,
    # debugging=True
)




# gv = [i for i in building.idfobjects['EnergyManagementSystem:GlobalVariable']]
# [i.Variable_Name for i in building.idfobjects['output:variable'] if 'Occupied Discomfortable' in i.Variable_Name]


for meter in output_meters:
    building.newidfobject(
        key='OUTPUT:METER',
        Key_Name=meter,
        Reporting_Frequency='hourly'
    )

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


available_outputs = print_available_outputs_mod(building)

df_meters = pd.DataFrame(available_outputs.meterreaderlist, columns=['output:meter', 'frequency'])
df_variables = pd.DataFrame(available_outputs.variablereaderlist, columns=['area','output:variable', 'frequency'])

parameters_list = [params.accis_parameter(k, v) for k, v in accis_parameters.items()]
parameters_list.extend(other_parameters)






def avg(result):
    return result.data["Value"].sum()/2

def mean(result):
    return result.data["Value"].mean()

# Objectives

objs_variables = []
for i in range(len(available_outputs.variablereaderlist)):
    if (
            'Adaptive Cooling Setpoint Temperature_No Tolerance' == available_outputs.variablereaderlist[i][1] or
            'Adaptive Heating Setpoint Temperature_No Tolerance' == available_outputs.variablereaderlist[i][1] or
            'Zone Operative Temperature' == available_outputs.variablereaderlist[i][1] or
            'AFN Zone Infiltration Air Change Rate' == available_outputs.variablereaderlist[i][1] or
            'AFN Zone Ventilation Air Change Rate' == available_outputs.variablereaderlist[i][1]

    ):
        objs_variables.append(
            VariableReader(
                key_value=available_outputs.variablereaderlist[i][0],
                variable_name=available_outputs.variablereaderlist[i][1],
                frequency=available_outputs.variablereaderlist[i][2],
                name=available_outputs.variablereaderlist[i][1],
                func=mean
            )
        )



objs_meters = [MeterReader(key_name=i, name=i) for i in output_meters]

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
