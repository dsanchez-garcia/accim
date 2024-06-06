from besos import eppy_funcs as ef
from accim.utils import set_occupancy_to_always
from accim.parametric_and_optimisation.main import OptimParamSimulation, get_mdd_file_as_df, get_rdd_file_as_df, parse_mtd_file
import accim.parametric_and_optimisation.objectives as obj

# 1. check output data
# 2. check input dataframe
# 3. run parametric_and_optimisation simulation




#Arguments
idf_path = 'ALJARAFE CENTER_mod.idf'

building = ef.get_building(idf_path)

set_occupancy_to_always(idf_object=building)

test_class_instance = OptimParamSimulation(
    building=building,
    parameters_type='apmv setpoints'
    # output_keep_existing=False,
    # debugging=True

)



# Setting the Output:Variable and Output:Meter objects in the idf
#todo do not print on screen the process of accis, only the first time
df_output_variables_idf = test_class_instance.get_output_var_df_from_idf()

df_output_variables_idf_mod = df_output_variables_idf.copy()


df_output_variables_idf_mod = df_output_variables_idf_mod[
    (
        df_output_variables_idf_mod['variable_name'].str.contains('aPMV')
        |
        df_output_variables_idf_mod['variable_name'].str.contains('Zone Operative Temperature')
        |
        df_output_variables_idf_mod['variable_name'].str.contains('Comfortable Hours')
    )
]


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

# def average_results(result):
#     return result.data["Value"].mean()
# def sum_results(result):
#     return result.data["Value"].sum()
#
# def return_time_series(result):
#     return result.data["Value"].to_list()

# df_outputmeters_3 = df_outputmeters_2.copy()
df_outputvariables_3 = df_outputvariables_2.copy()

df_outputvariables_3['func'] = obj.return_time_series
# df_outputvariables_3 = df_outputvariables_3.drop(index=[2, 4])
df_outputvariables_3['name'] = df_outputvariables_3['variable_name'] + '_time series'

test_class_instance.set_outputs_for_simulation(
    df_output_meter=df_outputmeters_2,
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




available_params = test_class_instance.get_available_parameters()

apmv_parameters = {
    'Adaptive coefficient': (0.2, 0.6),
    'PMV setpoint': (0.2, 0.7),
}


# from besos.parameters import wwr, RangeParameter
# other_parameters = [wwr(RangeParameter(0.1, 0.9))]

test_class_instance.set_parameters(
    accis_params_dict=apmv_parameters,
    # additional_params=other_parameters
)

# Let's set the problem
test_class_instance.set_problem()

# Let's generate a sampling dataframe
test_class_instance.sampling_full_factorial(level=5)
temp_full_fac = test_class_instance.parameters_values_df

test_class_instance.sampling_lhs(num_samples=3)
temp_lhs = test_class_instance.parameters_values_df

# test_class_instance.sampling_full_set()
# temp_full_set = test_class_instance.parameters_values_df

#todo try to return series of pmot, acst, ahst and optemp and plot them in facetgrid
outputs = test_class_instance.run_parametric_simulation(
    epws=[
        'Sydney.epw',
        'Seville.epw'
    ],
    out_dir='WIP_testing predefined models',
    df=temp_lhs,
    processes=6,
)

outputs = outputs.reset_index()

outputs.to_excel('WIP_outputs_param_apmv.xlsx')

##

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import seaborn as sns
import ast

[i for i in outputs.columns]
apmv = 'aPMV_PlantaX08_Office_time series'
# values = outputs[apmv]

length = len(ast.literal_eval(outputs.loc[0, apmv]))

start_datetime = datetime(2023, 1, 1, 1, 0)
dates = [start_datetime + timedelta(hours=i) for i in range(length)]

# plt.figure(figsize=(10, 5))
# plt.plot(df['DateTime'], df['Value'], marker='o')
# plt.plot(dates, values)
# plt.xlabel('DateTime')
# plt.ylabel('Value')
# plt.title('Time Series Plot')
# plt.grid(True)
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.show()

fig, axs = plt.subplots(
    nrows=len(outputs),
    figsize=(10, 5)
)
for i in outputs.index:
    for c in [apmv]:
        x = dates
        y = ast.literal_eval(outputs.loc[i, c])

        sns.lineplot(
            x=x,
            y=y,
            ax=axs[i]
        )


##





##

##



##
# remove_accents_in_idf(idf_path=idf_path)

# gv = [i for i in building.idfobjects['EnergyManagementSystem:GlobalVariable']]
# [i.Variable_Name for i in building.idfobjects['output:variable'] if 'Occupied Discomfortable' in i.Variable_Name]











# Objectives






# obj_avg = [MeterReader(key_name='TOTAL OCCUPIED DISCOMFORTABLE HOURS', func=avg, name='AVERAGE OCCUPIED DISCOMFORTABLE HOURS')]





