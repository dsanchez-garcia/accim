# %% [markdown]
# # Optimisation using apmv setpoints
# %%
#todo import qgrid to manually change output dfs
# %%
import accim
import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf
from accim.parametric_and_optimisation.objectives import average_results
from accim.parametric_and_optimisation.utils import make_all_combinations
from besos import eppy_funcs as ef
import matplotlib.pyplot as plt
import seaborn as sns
from accim.utils import print_available_outputs_mod, get_accim_args
from accim.parametric_and_optimisation.main import OptimParamSimulation, get_rdd_file_as_df, get_mdd_file_as_df, parse_mtd_file
from os import listdir
from accim.sim import apmv_setpoints

# %% [markdown]
# Let's have a look at the files we currently have in the path:
# %%
original_files = [i for i in listdir()]
original_files
# %% [markdown]
# Firstly, the IDF must be read using besos's `get_building` function.
# %%
building = ef.get_building('ALJARAFE CENTER_onlyGeometry.idf')
apmv_setpoints.add_vrf_system(building=building)

# %% [markdown]
# For this analysis, we want to use the HVAC system in all hours of the year, so that temperature is always comfortable. Therefore, we are going to set the occupancy to always on by means of the function `accim.utils.set_occupancy_to_always`, in which we input the IDF class instance we read in the previous cell.
# %%
accim.utils.set_occupancy_to_always(idf_object=building)
# %% [markdown]
# Now, let's start with the settings for the parametric analysis. First, let's instantiate the class `OptimParamSimulation`, and let's pass the IDF instance in the argument `building`. Argument `parameters_type` can take 3 different strings:
# - "accim predefined model", in which models are those previously defined in accim (ComfStand=0 to ComfStand=22);
# - "accim custom model", in which key parameters of the adaptive comfort model are defined in the relevant arguments;
# - "apmv setpoints", in which setpoints are based on the aPMV (Adaptive Predicted Mean Vote) instead of the PMV index;
# 
# In this case, we're going to use the 'apmv setpoints' type, in which we can define the adaptive comfort model.
# %%
parametric = OptimParamSimulation(
    building=building,
    parameters_type='apmv setpoints',
    #output_type='standard', #
    #output_keep_existing=False, #
    #output_freqs=['hourly'], #
    #ScriptType='vrf_mm', #
    #SupplyAirTempInputMethod='temperature difference', #
    #debugging=True, #
    #verbosemode=False #
)
# %% [markdown]
# An initial and generic version of the Adaptive-Comfort-Control-Implementation Script (ACCIS) has been added to the idf instance `building`. For instance, you can take a look at the parameter values accis currently has:
# %%
[i for i in building.idfobjects['energymanagementsystem:program'] if 'set_zone_input_data' in i.Name.lower()]
# %% [markdown]
# ## Setting the outputs
# %% [markdown]
# **If you have already read any of the other parametric simulation examples, you can skip this entire outputs section, since it is exactly the same.**
# %% [markdown]
# ### Outputs for the idf (i.e. the outputs for each simulation run)
# %% [markdown]
# First of all, we are going to set the outputs of the simulations that are going to be performed. This is an important step, especially if you are going to run hundreds or thousands of simulations.
# %% [markdown]
# Let's take a look at the Output:Variable objects we currently have in the idf. The method `get_output_var_df_from_idf()` returns a pandas DataFrame which contains the information of the existing Output:Variable objects in the idf:
# %%
df_output_variables_idf = parametric.get_output_var_df_from_idf()
df_output_variables_idf
# %% [markdown]
# now, let's see the Output:Meter objects:
# %%
df_output_meters_idf = parametric.get_output_meter_df_from_idf()
df_output_meters_idf.head()
# %% [markdown]
# In this case, we can see there is no Output:Meter. However, there is a large number of Output:Variable objects which might result in heavy simulation outputs. So, let's get rid of some of them. We can drop the rows we want, and then input the modified DataFrame in the method `set_output_var_df_to_idf(outputs_df)`.
# %%
df_output_variables_idf = df_output_variables_idf[
        df_output_variables_idf['variable_name'].str.contains('aPMV')
]
df_output_variables_idf
# %% [markdown]
# Let's keep only the Output:Variable objects we have filtered using the `set_output_var_df_to_idf(outputs_df)`:
# %%
parametric.set_output_var_df_to_idf(outputs_df=df_output_variables_idf)
# %% [markdown]
# We have removed all rows except the adaptive heating and cooling setpoints, the operative temperature and the running mean outdoor temperature. Next optional step is adding Output:Meter objects. We can do that using the method `set_output_met_objects_to_idf(output_meters)`, where `output_meters` is a list of Output:Meter key names.
# %%
output_meters = [
    'Heating:Electricity',
    'Cooling:Electricity',
    #'Electricity:HVAC',
]
parametric.set_output_met_objects_to_idf(output_meters=output_meters)
# %% [markdown]
# Let's see Output:Meter objects we currently have after adding these:
# %%
df_output_meters_idf = parametric.get_output_meter_df_from_idf()
df_output_meters_idf.head()
# %% [markdown]
# ### Outputs to be read and shown in the parametric simulation or optimisation
# %% [markdown]
# To successfully run the parametric simulation or optimisation, it is advisable running a test simulation to know the outputs that each simulation will have. We can do that with the method `get_outputs_df_from_testsim()`, which returns a tuple containing 2 DataFrames containing respectively the Output:Meter and Output:Variable objects from the simulation. In this case, you won't find wildcards such as "*".
# %%
df_output_meters_testsim, df_output_variables_testsim = parametric.get_outputs_df_from_testsim()
# %%
df_output_meters_testsim
# %%
df_output_variables_testsim
# %% [markdown]
# We can get DataFrames from the .rdd and .mdd files generated from the test simulation using the functions `get_rdd_file_as_df()` and `get_mdd_file_as_df()`. 
# %%
df_rdd = get_rdd_file_as_df()
df_rdd
# %%
df_mdd = get_mdd_file_as_df()
df_mdd
# %% [markdown]
# Also, we can parse the .mtd files as a list using the function `parse_mtd_file()`.
# %%
mtd_list = parse_mtd_file()
mtd_list[0:2]
# %% [markdown]
# Therefore, we have 2 DataFrames, one for the Output:Meter and another for the Output:Variable objects. Next step is setting the outputs for the parametric simulation. To do so, we'll need to pass the DataFrames into the method `set_outputs_for_simulation(df_output_meter, df_output_variable)`. If you have some knowledge about the python package besos, you might think of these dataframes as if each row was a `MeterReader` or `VariableReader` instances respectively for the Output:Meter and Output:Variable dataframes, and the arguments in these were the specified in the columns. The `MeterReader` class takes the arguments `key_name`, `frequency`, `name` and `func`, while `VariableReader` class takes the arguments  `key_value`, `variable_name`, `frequency`, `name` and `func`.
# %%
[i for i in df_output_meters_testsim.columns]
# %%
[i for i in df_output_variables_testsim.columns]
# %% [markdown]
# If you take a look at the columns of the dataframes above, you can see the names are the arguments in the `MeterReader` and `VariableReader` classes, and only `name` and `func` are missing. That means, you can add these columns to input the `name` and `func` arguments as desired. **The only limitation is that you cannot return time series in optimisation**. In case of the Output:Meter dataframe, we won't add the `name` and `func` columns, which means the name will be the `key_name` and hourly results will be aggregated using the pd.Series.sum() function. However, in case of the Output:Variable dataframe, we will specify these: we want the average rather than the sum, therefore we will pass the name bound to the function `average_results`, and we will add '_average' as a suffix to the `variable_name` column. We will also remove the outputs for BLOCK1:ZONE2, which are the rows 2 and 4.
# %%
df_output_variables_testsim['func'] = average_results
df_output_variables_testsim['name'] = df_output_variables_testsim['variable_name'] + '_average'
df_output_variables_testsim = df_output_variables_testsim[~df_output_variables_testsim['variable_name'].str.contains('BLOCK1:ZONE2')]
df_output_variables_testsim
# %% [markdown]
# Finally, let's set the outputs for parametric simulation and optimisation:
# %%
df_output_meters_testsim = df_output_meters_testsim[
    df_output_meters_testsim['key_name'].str.contains('Heating:Electricity|Cooling:Electricity')
]
parametric.set_outputs_for_simulation(
    df_output_meter=df_output_meters_testsim,
    #df_output_variable=df_output_variables_testsim,
)
# %% [markdown]
# If you want to inspect the `VariableReader` and `MeterReader` objects, you can see the internal variable `sim_outputs`:
# %%
parametric.sim_outputs
# %% [markdown]
# ## Setting the parameters
# %% [markdown]
# At the top of the script, when you instantiated the class `OptimParamSimulation`, you already specified which type of parameters you were going to use. Now, the parameters we're about to set, must match the `parameters_type` argument. At this point, you may not know which parameters you can use, so you can call the method `get_available_parameters()`, which will return a list of available parameters:
# %%
available_parameters = parametric.get_available_parameters()
available_parameters
# %% [markdown]
# If you don't know what are these, please refer to the [documentation](https://accim.readthedocs.io/en/master/4_detailed%20use.html).
# %% [markdown]
# Using the 'apmv setpoints' type, the values can be either a list of options or a range of values. Now, let's set the parameters using the method `set_parameters(accis_params_dict, additional_params)`. In this method, we set the parameters related to accim using the argument `accis_params_dict`, which takes a dictionary following the pattern {'parameter name': [1, 2, 3, etc]} in case of list of options, or {'parameter name': (min_value, max_value)} in case of the range of values. We can also add some other parameters not related to accim in the argument `additional_params`, which takes a list of parameters as if these were input straight to the besos EPProblem class.
# %% [markdown]
# An example using ranges, could be:
# %%
accis_parameters = {
    'Adaptive coefficient': (0.01, 0.99),
    'PMV setpoint': (0.2, 0.7),
}
parametric.set_parameters(accis_params_dict=accis_parameters)
# %% [markdown]
# Let's take a look at the values that the arguments currently have:
# %%
args = get_accim_args(building)
args
# %% [markdown]
# If you want to inspect the `Parameter` objects, you can see the internal variable `parameters_list`:
# %%
parametric.parameters_list
# %% [markdown]
# ## Running the optimisation
# %% [markdown]
# ### Setting the problem
# %% [markdown]
# First, let's set the problem. To do so, use the `set_problem()` method. In case of the parametric simulation you don't need to input any argument. However, in case of the optimisation, you must input the arguments `minimize_outputs`, `constraints` and `constraint_bounds`, similarly as you would do in the besos `EPProblem` class.
# %%
parametric.set_problem(
    minimize_outputs=[True, True] # Means minimise Heating:Electricity and Cooling:Electricity
)
# %% [markdown]
# Again, you can inspect the `EPProblem` class instance in the internal variable `problem`:
# %%
parametric.problem
# %% [markdown]
# ### Running the simulations
# %% [markdown]
# Now, we're ready to run the simulations, by means of the `run_optimisation(algorithm, epw, out_dir, evaluations, population_size)` method. After calling the method, the outputs (a DataFrame) is saved in the internal variable `outputs_optimisation`. We want to run the parametric simulations with both Sydney and Seville climate files, therefore the filenames are input in a list in the `epws` argument. The simulation outputs will be saved in a directory named 'notebook_temp_dir'.
# %%
parametric.run_optimisation(
    algorithm='NSGAII',
    epws=['Seville.epw', 'Sydney.epw'],
    out_dir='notebook_temp_dir',
    evaluations=5,
    population_size=10,
    #keep_input=True, # To keep the input values of parameters, as entered in df argument. Default is True.
)
# %% [markdown]
# Let's take a look at the simulation results
# %%
parametric.outputs_optimisation
# %% [markdown]
# We can see the columns are the following:
# %% [markdown]
# - the parameters, which are:
# %%
[i.value_descriptors[0].name for i in parametric.parameters_list]
# %% [markdown]
# - the outputs, which are:
# %%
[i.name for i in parametric.sim_outputs]
# %% [markdown]
# - the violation column, for those simulations in which constraints have been exceeded
# - the pareto-optimal column, which shows True for the optimal values
# - the epw for each simulation, in the column 'epw'
# %% [markdown]
# ### Visualising the results
# %% [markdown]
# At this point, if you have some knowledge of pandas and some package to plot the data (e.g. matplotlib or seaborn), you can carry out your own analysis and visualization. We're going to do some example below.
# %%
g = sns.FacetGrid(
    data=parametric.outputs_optimisation,
    col='epw'
)

g.map_dataframe(
    sns.scatterplot,
    x='Heating:Electricity',
    y='Cooling:Electricity',
    hue='pareto-optimal',
)
g.add_legend(title='Pareto')
# %% [markdown]
# We're done with the example, so let's remove all new files, so that we can re-run it again.
# %%
current_files = [i for i in listdir()]
new_files = set(current_files) - set(original_files)
new_files
# %%
import os
import os
import shutil
print("The following NEW files/directories have been identified to be removed:")
for item in new_files:
    print(f"- {item}")
user_decision = input("Do you want to proceed and delete these files? [y/n]: ")
if user_decision.lower() == 'y':
    for item in new_files:
        item_path = os.path.join(os.getcwd(), item)
        if os.path.isfile(item_path):
            os.remove(item_path)
            print(f"Deleted file: {item}")
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
            print(f"Deleted directory: {item}")
else:
    print("Deletion cancelled by the user.")