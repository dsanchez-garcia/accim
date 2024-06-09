#!/usr/bin/env python
# coding: utf-8

# # Parametric simulation using accim custom models

# In[15]:


#todo import qgrid to manually change output dfs


# In[16]:


import accim
from accim.parametric_and_optimisation.objectives import return_time_series
from accim.parametric_and_optimisation.utils import make_all_combinations
from besos import eppy_funcs as ef
import matplotlib.pyplot as plt
#import matplotlib
#matplotlib.use('gtk3cairo')
import seaborn as sns
from accim.utils import print_available_outputs_mod, get_accim_args
from accim.parametric_and_optimisation.main import OptimParamSimulation, get_rdd_file_as_df, get_mdd_file_as_df, parse_mtd_file
from os import listdir


# Let's have a look at the files we currently have in the path:

# In[17]:


original_files = [i for i in listdir()]
original_files


# Firstly, the IDF must be read using besos's `get_building` function.

# In[18]:


building = ef.get_building('TestModel.idf')


# For this analysis, we want to use the HVAC system in all hours of the year, so that temperature is always comfortable. Therefore, we are going to set the occupancy to always on by means of the function `accim.utils.set_occupancy_to_always`, in which we input the IDF class instance we read in the previous cell.

# In[19]:


accim.utils.set_occupancy_to_always(idf_object=building)


# Now, let's start with the settings for the parametric analysis. First, let's instantiate the class `OptimParamSimulation`, and let's pass the IDF instance in the argument `building`. Argument `parameters_type` can take 3 different strings:
# - "accim predefined model", in which models are those previously defined in accim (ComfStand=0 to ComfStand=22);
# - "accim custom model", in which key parameters of the adaptive comfort model are defined in the relevant arguments;
# - "apmv setpoints", in which setpoints are based on the aPMV (Adaptive Predicted Mean Vote) instead of the PMV index;
# 
# In this case, we're going to use the 'accim custom model' type, in which we can define the adaptive comfort model.

# In[20]:


parametric = OptimParamSimulation(
    building=building,
    parameters_type='accim custom model',
    #output_type='standard', #
    #output_keep_existing=False, #
    #output_freqs=['hourly'], #
    #ScriptType='vrf_mm', #
    #SupplyAirTempInputMethod='temperature difference', #
    #debugging=True, #
    #verbosemode=False #
)


# An initial and generic version of the Adaptive-Comfort-Control-Implementation Script (ACCIS) has been added to the idf instance `building`. For instance, you can take a look at the parameter values accis currently has:

# In[21]:


[i for i in building.idfobjects['energymanagementsystem:program'] if i.Name.lower() == 'setinputdata']


# ## Setting the outputs

# **If you have already read any of the other parametric simulation examples, you can skip this entire outputs section, since it is exactly the same.**

# ### Outputs for the idf (i.e. the outputs for each simulation run)

# First of all, we are going to set the outputs of the simulations that are going to be performed. This is an important step, especially if you are going to run hundreds or thousands of simulations.

# Let's take a look at the Output:Variable objects we currently have in the idf. The method `get_output_var_df_from_idf()` returns a pandas DataFrame which contains the information of the existing Output:Variable objects in the idf:

# In[22]:


df_output_variables_idf = parametric.get_output_var_df_from_idf()
df_output_variables_idf


# now, let's see the Output:Meter objects:

# In[23]:


df_output_meters_idf = parametric.get_output_meter_df_from_idf()
df_output_meters_idf.head()


# In this case, we can see there is no Output:Meter. However, there is a large number of Output:Variable objects which might result in heavy simulation outputs. So, let's get rid of some of them. We can drop the rows we want, and then input the modified DataFrame in the method `set_output_var_df_to_idf(outputs_df)`.

# In[24]:


df_output_variables_idf = df_output_variables_idf[
    (
        df_output_variables_idf['variable_name'].str.contains('Setpoint Temperature_No Tolerance')
        |
        df_output_variables_idf['variable_name'].str.contains('Zone Operative Temperature')
        |
        df_output_variables_idf['variable_name'].str.contains('Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature')
        # |
        # df_output_variables_idf['variable_name'].str.contains('People Occupant')
        # |
        # df_output_variables_idf['key_value'].str.contains('Sch_BLOCK')
        # |
        # df_output_variables_idf['variable_name'].str.contains('Site Outdoor Drybulb')
        # |
        # df_output_variables_idf['variable_name'].str.contains('z_test')

    )
]
df_output_variables_idf


# Let's keep only the Output:Variable objects we have filtered using the `set_output_var_df_to_idf(outputs_df)`:

# In[25]:


parametric.set_output_var_df_to_idf(outputs_df=df_output_variables_idf)


# We have removed all rows except the adaptive heating and cooling setpoints, the operative temperature and the running mean outdoor temperature. Next optional step is adding Output:Meter objects. We can do that using the method `set_output_met_objects_to_idf(output_meters)`, where `output_meters` is a list of Output:Meter key names.

# In[26]:


output_meters = [
    'Heating:Electricity',
    'Cooling:Electricity',
    'Electricity:HVAC',
]
parametric.set_output_met_objects_to_idf(output_meters=output_meters)


# Let's see Output:Meter objects we currently have after adding these:

# In[27]:


df_output_meters_idf = parametric.get_output_meter_df_from_idf()
df_output_meters_idf.head()


# ### Outputs to be read and shown in the parametric simulation or optimisation

# To successfully run the parametric simulation or optimisation, it is advisable running a test simulation to know the outputs that each simulation will have. We can do that with the method `get_outputs_df_from_testsim()`, which returns a tuple containing 2 DataFrames containing respectively the Output:Meter and Output:Variable objects from the simulation. In this case, you won't find wildcards such as "*".

# In[28]:


df_output_meters_testsim, df_output_variables_testsim = parametric.get_outputs_df_from_testsim()


# In[29]:


df_output_meters_testsim


# In[30]:


df_output_variables_testsim


# We can get DataFrames from the .rdd and .mdd files generated from the test simulation using the functions `get_rdd_file_as_df()` and `get_mdd_file_as_df()`. 

# In[31]:


df_rdd = get_rdd_file_as_df()
df_rdd


# In[32]:


df_mdd = get_mdd_file_as_df()
df_mdd


# Also, we can parse the .mtd files as a list using the function `parse_mtd_file()`.

# In[33]:


mtd_list = parse_mtd_file()
mtd_list[0:2]


# Therefore, we have 2 DataFrames, one for the Output:Meter and another for the Output:Variable objects. Next step is setting the outputs for the parametric simulation. To do so, we'll need to pass the DataFrames into the method `set_outputs_for_simulation(df_output_meter, df_output_variable)`. If you have some knowledge about the python package besos, you might think of these dataframes as if each row was a `MeterReader` or `VariableReader` instances respectively for the Output:Meter and Output:Variable dataframes, and the arguments in these were the specified in the columns. The `MeterReader` class takes the arguments `key_name`, `frequency`, `name` and `func`, while `VariableReader` class takes the arguments  `key_value`, `variable_name`, `frequency`, `name` and `func`.

# In[34]:


[i for i in df_output_meters_testsim.columns]


# In[35]:


[i for i in df_output_variables_testsim.columns]


# If you take a look at the columns of the dataframes above, you can see the names are the arguments in the `MeterReader` and `VariableReader` classes, and only `name` and `func` are missing. That means, you can add these columns to input the `name` and `func` arguments as desired. In case of the Output:Meter dataframe, we won't add the `name` and `func` columns, which means the name will be the `key_name` and hourly results will be aggregated using the pd.Series.sum() function. However, in case of the Output:Variable dataframe, we will specify these: we want the hourly values rather than the aggregation, therefore we will pass the name bound to the function `return_time_series`, and we will add '_time series' as a suffix to the `variable_name` column. We will also remove the outputs for BLOCK1:ZONE2, which are the rows 2 and 4.

# In[36]:

##
df_output_variables_testsim['func'] = return_time_series
df_output_variables_testsim['name'] = df_output_variables_testsim['variable_name'] + '_time series'
df_output_variables_testsim = df_output_variables_testsim.drop(index=[2, 4])
df_output_variables_testsim


# Finally, let's set the outputs for parametric simulation and optimisation:

# In[37]:


parametric.set_outputs_for_simulation(
    df_output_meter=df_output_meters_testsim,
    df_output_variable=df_output_variables_testsim,
)


# If you want to inspect the `VariableReader` and `MeterReader` objects, you can see the internal variable `sim_outputs`:

# In[38]:


parametric.sim_outputs


# ## Setting the parameters

# At the top of the script, when you instantiated the class `OptimParamSimulation`, you already specified which type of parameters you were going to use. Now, the parameters we're about to set, must match the `parameters_type` argument. At this point, you may not know which parameters you can use, so you can call the method `get_available_parameters()`, which will return a list of available parameters:

# In[39]:


available_parameters = parametric.get_available_parameters()
available_parameters


# If you don't know what are these, please refer to the [documentation](https://accim.readthedocs.io/en/master/4_detailed%20use.html).

# Tu use the custom model, the following parameters must be defined, either by including them in the parameters to vary, or manually defined:

# In[40]:


[i for i in available_parameters if '_AST' not in i]


# The remaining parameters, which are:

# In[41]:


[i for i in available_parameters if '_AST' in i]


# are used to set symmetrical comfort thresholds in case of 'CustAST_ASToffset' (i.e. a value of 3 means +3 is used as ACSToffset and -3 as AHSToffset), or in case of 'CustAST_ASTaul' and 'CustAST_ASTall', to set the same value to the applicability upper or lower limit for heating and cooling purposes (i.e. a value of 15 for CustAST_ASTall means 15 is used for CustAST_ACSTaul and CustAST_AHSTaul)

# Using the 'accim custom model' type, the values can be either a list of options or a range of values. Now, let's set the parameters using the method `set_parameters(accis_params_dict, additional_params)`. In this method, we set the parameters related to accim using the argument `accis_params_dict`, which takes a dictionary following the pattern {'parameter name': [1, 2, 3, etc]} in case of list of options, or {'parameter name': (min_value, max_value)} in case of the range of values. We can also add some other parameters not related to accim in the argument `additional_params`, which takes a list of parameters as if these were input straight to the besos EPProblem class.

# ### Example 1

# An example using ranges, could be:

# In[42]:




# In[43]:


# accis_parameters = {
#     'CustAST_m': (0.01, 0.99),
#     'CustAST_n': (5, 23),
#     'CustAST_ASToffset': (2, 4),
#     'CustAST_ASTall': (10, 15),
#     'CustAST_ASTaul': (30, 35),
# }
# parametric.set_parameters(accis_params_dict=accis_parameters)


# In this case, all parameters have been defined. Otherwise, we would be requested to continue with default values or to input them. Let's see Example 2.

# ### Example 3

# A different option might be using m, n and ASToffset as parameters, and setting ASTall and ASTaul to some specific value so that these don't vary.

# In[44]:


# accis_parameters = {
#     'CustAST_m': (0.01, 0.99),
#     'CustAST_n': (5, 23),
#     'CustAST_ASToffset': (2, 4),
# }
# parametric.set_parameters(accis_params_dict=accis_parameters)


# In[ ]:





# Let's take a look at the values that the arguments currently have:

# In[45]:


# args = get_accim_args(building)
# args['CustAST']


# As you can see, 'm', 'n', 'ACSToffset' and 'AHSToffset' have the value 0, because these are the arguments included in the parameters, and their values will vary depending on the sample we specify later, and the values for the applicabiliy upper and lower limits have the values we just input.

# ### Example 3

# Now, let's use a list of options instead of range of values.

# In[46]:


# accis_parameters = {
#     'CustAST_m': [0, 0.3, 0.6],
#     'CustAST_n': [10, 23],
# }
# parametric.set_parameters(accis_params_dict=accis_parameters)


# Again, let's take a look at the arguments:

# In[47]:


# args = get_accim_args(building)
# args['CustAST']


# So, let's continue with Example 2, dropping CustAST_ASToffset and using default values for the non-defined arguments:

# In[48]:


accis_parameters = {
    'CustAST_m': (0.01, 0.99),
    'CustAST_n': (5, 23),
}
parametric.set_parameters(accis_params_dict=accis_parameters, use_dflt_values=True)

args = accim.utils.get_accim_args(building)
args

import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf
bf.modify_VentCtrl(building, 2)
bf.modify_MaxTempDiffVOF(building, 6)
bf.modify_MinTempDiffVOF(building, 1)
args_new = accim.utils.get_accim_args(building)
args_new

##

# If you want to inspect the `Parameter` objects, you can see the internal variable `parameters_list`:

# In[49]:


parametric.parameters_list


# ## Running the parametric simulation

# ### Setting the problem

# First, let's set the problem. To do so, use the `set_problem()` method. In case of the parametric simulation you don't need to input any argument. However, in case of the optimisation, you must input the arguments `minimize_outputs`, `constraints` and `constraint_bounds`, similarly as you would do in the besos `EPProblem` class.

# In[50]:


parametric.set_problem()


# Again, you can inspect the `EPProblem` class instance in the internal variable `problem`:

# In[51]:


parametric.problem


# ### Sampling the simulation runs

# The way to inform besos of the variations and permutations it must carry out in the parametric analysis is by means of a DataFrame, which must contain a column per `Parameter`, in which values are specified. There are multiple ways to do this DataFrame. For instance, we could make a dataframe from scratch:

# In[52]:


# import pandas as pd
# param_dict = {
#     'CustAST_m': [0.1, 0.6],
#     'CustAST_n': [22, 8],
#     'CustAST_ASToffset': [2.5, 4],
#     'CustAST_ASTall': [10, 10],
#     'CustAST_ASTaul': [35, 35],
# }
# input_param_df = pd.DataFrame(data=param_dict)
# input_param_df


# We could input that df, which would result in 2 simulations. But now, imagine we want to make all possible combinations from the values we just did from scratch. We could use the function `make_all_combinations(parameters_values_dict)`. The argument `parameters_values_dict` must be a dictionary in the format {'parameter name': list_of_values}, such as the previouly defined param_dict, so let's input it. Let's see the possibilities:

# In[53]:


# all_combinations = make_all_combinations(param_dict)
# all_combinations


# Also, we can use the sampling functions from besos (`full_factorial` and `lhs`), which have been wrapped in the methods `sampling_full_factorial(level)` and `sampling_lhs(num_samples)`. After calling these, the samples are saved in the internal variable `parameters_values_df`. Let's see some examples:

# In[54]:


# parametric.sampling_lhs(num_samples=3)
# parametric.parameters_values_df


# In[55]:


parametric.sampling_full_factorial(level=3)
parametric.parameters_values_df


# ### Running the simulations

# Now, we're ready to run the simulations, by means of the `run_parametric_simulation(epws, out_dir, df, processes)` method. After calling the method, the outputs (a DataFrame) is saved in the internal variable `outputs_param_simulation`. It is based on the use of the `EvaluatorEP` class, `df_apply` method. We want to run the parametric simulations with both Sydney and Seville climate files, therefore the filenames are input in a list in the `epws` argument. The simulation outputs will be saved in a directory named 'notebook_temp_dir'. The values for the parameters will be driven by the internal variable `parameters_values_df`, as input in the `df` argument.

# In[56]:


parametric.run_parametric_simulation(
    epws=['Sydney.epw', 'Seville.epw'],
    out_dir='WIP_notebook_temp_dir_2',
    df=parametric.parameters_values_df,
    processes=6, # The number of CPUs to be used. Default is 2.
    #keep_input=True, # To keep the input values of parameters, as entered in df argument. Default is True.
    #keep_dirs=True # To keep the simulation outputs. Default is True.
)


# Let's take a look at the simulation results

# In[57]:


parametric.outputs_param_simulation


# We can see the columns are the following:

# - the parameters, which are:

# In[58]:


[i.value_descriptors[0].name for i in parametric.parameters_list]


# - the outputs, which are:

# In[59]:


[i.name for i in parametric.sim_outputs]


# - the path to the output files for each simulation, in the column 'out_dir'
# - the epw for each simulation, in the column 'epw'

# ### Visualising the results

# #### Aggregated columns

# At this point, if you have some knowledge of pandas and some package to plot the data (e.g. matplotlib or seaborn), you can carry out your own analysis and visualization. We're going to do some example below.

# In[60]:


#import sys
#!{sys.executable} -m pip install matplotlib==3.7.0


# In[61]:


sns.scatterplot(
    data=parametric.outputs_param_simulation,
    x='Heating:Electricity',
    y='Cooling:Electricity',
    hue='CustAST_m',
    style='CustAST_n'
)


# #### Time series columns

# If you requested some output to be reported in time series, you can get a dataframe containing the hourly values using the method `get_hourly_df()`. This dataframe is saved in the internal variable `outputs_param_simulation_hourly`:

# In[62]:


parametric.get_hourly_df()
parametric.outputs_param_simulation_hourly


# Let's prepare the `outputs_param_simulation_hourly` df for plotting:

# In[63]:


#Let's make a copy of the dataframe to not to modify the original one
df = parametric.outputs_param_simulation_hourly.copy()

# The name of the column for the Running mean outdoor temperature is very long, so let's save it in the variable rmot:
rmot = [i for i in df.columns if 'Running Average' in i][0]

#Let's remove the columns where value is the same for all rows
for c in df.columns:
    if len(set(df[c])) == 1:
        df = df.drop(columns=[c])
#Now let's remove the hour and datetime columns, since will
df = df.drop(columns=['hour'])

# Now let's reshape the df for plotting purposes
df = df.melt(id_vars=['datetime', 'CustAST_m', 'CustAST_n','epw', rmot])


# Firstly, we're going to plot the hourly temperatures to see the slope of the comfort model, and check all hours are within thermal comfort limits (since we applied adaptive setpoints)

# In[64]:


g1 = sns.FacetGrid(
    data=df[df['epw'].str.contains('Seville')],
    row='CustAST_m',
    col='CustAST_n'
)
g1.map_dataframe(
    sns.scatterplot,
    x=rmot,
    y='value',
    hue='variable',
    s=1,
    #alpha=0.5
)
g1.set_axis_labels('RMOT (°C)', 'Indoor Operative Temperature (°C)')
g1.add_legend(loc='upper center', bbox_to_anchor=(0.5, 0))

for lh in g1._legend.legend_handles:
    lh.set_markersize(5)
plt.tight_layout()


# Now, we're going to plot time on x-axis and change the plot type to lineplot, to see the variarion of the indoor operative temperature throughout the year:

# In[65]:


g2 = sns.FacetGrid(
    data=df[df['epw'].str.contains('Seville')],
    row='CustAST_m',
    col='CustAST_n'
)
g2.map_dataframe(
    sns.lineplot,
    x='datetime',
    y='value',
    hue='variable',
)
g2.set_axis_labels('Time', 'Indoor Operative Temperature (°C)')
g2.add_legend(loc='upper center', bbox_to_anchor=(0.5, 0))
plt.tight_layout()


# In[66]:




# We're done with the example, so let's remove all new files, so that we can re-run it again.

# In[48]:

arguments = accim.utils.get_accim_args(building)

parametric.parameters_values_df
parametric.evaluators['Seville'].generate_building(df=parametric.parameters_values_df, index=8, file_name='num_8')







# current_files = [i for i in listdir()]
# new_files = set(current_files) - set(original_files)
# new_files


# In[51]:


# import os
# import shutil
# for item in new_files:
#     item_path = os.path.join(os.getcwd(), item)
#     if os.path.isfile(item_path):
#         os.remove(item_path)
#     elif os.path.isdir(item_path):
#         shutil.rmtree(item_path)

