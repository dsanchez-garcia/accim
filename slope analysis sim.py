import numpy as np

import accim
import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf
from accim.parametric_and_optimisation.objectives import return_time_series
from accim.parametric_and_optimisation.utils import make_all_combinations
from besos import eppy_funcs as ef
import matplotlib.pyplot as plt
import seaborn as sns
from accim.utils import print_available_outputs_mod, get_accim_args
from accim.parametric_and_optimisation.main import OptimParamSimulation, get_rdd_file_as_df, get_mdd_file_as_df, parse_mtd_file
from os import listdir

building = ef.get_building('SmallOffice.idf')
accim.utils.set_occupancy_to_always(idf_object=building)

parametric = OptimParamSimulation(
    building=building,
    parameters_type='accim custom model',
    make_averages=True,
    #output_type='standard', #
    #output_keep_existing=False, #
    #output_freqs=['hourly'], #
    #ScriptType='vrf_mm', #
    #SupplyAirTempInputMethod='temperature difference', #
    #debugging=True, #
    #verbosemode=False #
)

df_output_variables_idf = parametric.get_output_var_df_from_idf()
df_output_variables_idf

df_output_meters_idf = parametric.get_output_meter_df_from_idf()
df_output_meters_idf.head()



df_output_variables_idf = df_output_variables_idf[
    (
        df_output_variables_idf['variable_name'].str.contains('Setpoint Temperature_No Tolerance')
        |
        df_output_variables_idf['variable_name'].str.contains('Zone Operative Temperature_Building_Average')
        |
        df_output_variables_idf['variable_name'].str.contains('Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature')
    )
]
df_output_variables_idf




parametric.set_output_var_df_to_idf(outputs_df=df_output_variables_idf)

output_meters = [
    'Heating:Electricity',
    'Cooling:Electricity',
    'Electricity:HVAC',
]

parametric.set_output_met_objects_to_idf(output_meters=output_meters)

df_output_meters_idf = parametric.get_output_meter_df_from_idf()
df_output_meters_idf.head()




df_output_meters_testsim, df_output_variables_testsim = parametric.get_outputs_df_from_testsim()
df_output_meters_testsim
df_output_variables_testsim



df_output_variables_testsim = df_output_variables_testsim[
    ~(
        df_output_variables_testsim.key_value.str.contains('PERIMETER')
        &
        df_output_variables_testsim.variable_name.str.contains('ASHRAE 55')
    )
]

df_output_variables_testsim['func'] = return_time_series
df_output_variables_testsim['name'] = df_output_variables_testsim['variable_name'] + '_time series'



parametric.set_outputs_for_simulation(
    df_output_meter=df_output_meters_testsim,
    df_output_variable=df_output_variables_testsim,
)

##
import numpy as np
# m_values = [round(float(i), 2) for i in np.arange(start=0.1, stop=0.85, step=0.05)]
m_values = [i for i in np.arange(start=0.1, stop=0.85, step=0.05)]

m_values.append(0.33)

accis_parameters = {
    'CustAST_m': m_values,
}
parametric.set_parameters(accis_params_dict=accis_parameters)

args = get_accim_args(building)
args['CustAST']

parametric.parameters_list

##

parametric.set_problem()

all_combinations = make_all_combinations(accis_parameters)
all_combinations

##

parametric.run_parametric_simulation(
    epws=['Seville.epw'],
    out_dir='notebook_temp_dir',
    df=parametric.parameters_values_df,
    processes=4, # The number of CPUs to be used. Default is 2.
    #keep_input=True, # To keep the input values of parameters, as entered in df argument. Default is True.
    #keep_dirs=True # To keep the simulation outputs. Default is True.
)