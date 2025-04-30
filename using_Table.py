#!/usr/bin/env python
# coding: utf-8

# # Using the class ``Table()`` for data analysis

# Say we have previously renamed the EPW files with rename_epw_files(), and the EPWs we currently have are:
# 
# - United-Kingdom_Aberdeen_Present
# 
# - United-Kingdom_London_Present
# 
# We also have transformed the IDF file TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220.idf, and the IDFs we currently have are:
# 
# - TestModel[CS_INT EN16798[CA_1[CM_0[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_X.idf
# 
# - TestModel[CS_INT EN16798[CA_1[CM_3[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_X.idf
# 
# - TestModel[CS_INT EN16798[CA_2[CM_0[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_X.idf
# 
# - TestModel[CS_INT EN16798[CA_2[CM_3[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_X.idf
# 
# - TestModel[CS_INT EN16798[CA_3[CM_0[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_X.idf
# 
# - TestModel[CS_INT EN16798[CA_3[CM_3[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_X.idf
# 
# Next, we simulate these files with runEp(), so the CSVs we get are:

# In[1]:


import os
print(*[i for i in os.listdir() if i.endswith('.csv') and 'TestModel' in i], sep='\n')

previous_files = [i for i in os.listdir()]

# So now, let's use the class Table() to analyse the data.

# ## 1. Getting the full dataset of simulation results

# In[3]:


from accim.data.postprocessing.main import Table
dataset_hourly = Table(
    #datasets=list #Since we are not specifying any list, it will use all available CSVs in the folder
    source_frequency='hourly', # This lets accim know which is the frequency of the input CSVs. Input CSVs with multiple frequencies are also allowed. It can be 'hourly', 'daily', 'monthly' and 'runperiod'. It can also be 'timestep' but might generate errors.
    frequency='hourly', # If 'daily', accim will aggregate the rows in days. It can be 'hourly', 'daily', 'monthly' and 'runperiod'. It can also be 'timestep' but might generate errors.
    frequency_agg_func='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True, 
    level=['building'], # A list containing the strings 'block' and/or 'building'. For instance, if ['block', 'building'], accim will generate new columns to sum up or average in blocks and building level.
    level_agg_func=['sum', 'mean'], # A list containing the strings 'sum' and/or 'mean'. For instance, if ['sum', 'mean'], accim will generate the new columns explained in the level argument by summing and averaging.
    level_excluded_zones=[],
    split_epw_names=True, #to split EPW names based on the pattern Country_City_RCPscenario-Year
    idf_path='TestModel.idf',
)


# A Table object has been created, which includes a number of accessible variables. The most important is the Pandas Dataframe created from the CSVs, which can be accessed with .df (in this case, dataset_hourly.df)

# In[4]:


dataset_hourly.df


# In[5]:


dataset_hourly.df.shape


# Also, you can see the block list that has been extracted from the zones in the CSV columns, as well as the zones with heating or cooling energy consumption, and the occupied zones:

# In[6]:


dataset_hourly.block_list


# In[7]:


dataset_hourly.hvac_zone_list


# In[8]:


dataset_hourly.occupied_zone_list


# In case of lots of CSVs, using the Table class would mean gathering the CSVs to make the Dataframe each time, and it might be very time-consuming. Therefore, the CSVs can be concatenated into a single CSV and store in the same folder with the argument concatenated_csv_name. Afterwards, that concatenated CSV can be read using the argument source_concatenated_csv_filepath each time a Table class object is created.

# In[9]:


concatenated_csvname = 'notebook_example'
dataset_hourly_indirect = Table(
    #datasets=list #Since we are not specifying any list, it will use all available CSVs in the folder
    source_frequency='hourly', # This lets accim know which is the frequency of the input CSVs. Input CSVs with multiple frequencies are also allowed. It can be 'hourly', 'daily', 'monthly' and 'runperiod'. It can also be 'timestep' but might generate errors.
    frequency='hourly', # If 'daily', accim will aggregate the rows in days. It can be 'hourly', 'daily', 'monthly' and 'runperiod'. It can also be 'timestep' but might generate errors.
    frequency_agg_func='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True, 
    concatenated_csv_name=concatenated_csvname #Useful when working with large datasets. It saves the output dataset to a CSV file, so you don't need to re-do some work. Afterwards, it can be imported with source_concatenated_csv_filepath argument.
    # All other arguments won't have any effect on the output. This is only to store the csv at early stage. Datawrangling will be performed later.
    
)


# We just generated a CSV, whose name begins with 'notebook example', specifies the input data and ends with 'CSVconcatenated'. If there is some row with NaN, it will be generated another CSV reporting this, but ending with 'Rows_with_NaNs'. We should be able to see it below:

# In[10]:


import os
os.listdir()


# Now, let's continue working with the CSVconcatenated we have generated:

# In[12]:


dataset_hourly_indirect = Table(
    source_concatenated_csv_filepath='notebook_example[srcfreq-hourly[freq-hourly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    # source_frequency='hourly', # The new source frequency is the previous already computed frequency, since we have already aggregated rows based on the previous frequency. Therefore, there is no need to specify this argument.
    # 3 arguments below have been previously specified, and in fact, are stored at the concatenated CSV filename. So you don't need to specify these again.
    # frequency='hourly',
    # frequency_agg_func='sum',
    # standard_outputs=True,
    level=['building'],
    level_agg_func=['sum', 'mean'],
    level_excluded_zones=[],
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
    idf_path='TestModel.idf',
    
)


# In[13]:


dataset_hourly_indirect.df.shape


# You can see we have obtained the same full dataset. Now, let's delete the concatenated CSV file to save some space.

# In[14]:

new_files = [i for i in os.listdir() if i not in previous_files]
for i in new_files:
    os.remove(i)


# for i in os.listdir():
#     if concatenated_csvname in i:
#         os.remove(i)


# ## 2. Filtering results

# We have used any of the 2 methods to obtain the full dataset of simulation results.

# At this point, we should have decided what table or graph we intend to make, and therefore we should know what data we are going to show in it. In this case, we want to make a figure to plot the indoor operative temperature and adaptive heating and cooling setpoints on the y main axis (left spine), and on the secondary y axis, 2 different spines, one of them to show the heating and cooling energy demand, and the other one the air changes, therefore, we will need to filter these columns. Let's take a look first at the full dataframe:

# In[15]:


print(*dataset_hourly.df.columns, sep='\n')


# Now, let's extract the data we are really interested in. For this, we can use the method called ``format_table()``:

# In[16]:


dataset_hourly.format_table(
    type_of_table='custom', # Used to choose some predefined tables. It can be 'energy demand', 'comfort hours', 'temperature', 'all' or 'custom'
    custom_cols=[ #if type_of_table is 'custom', custom_cols is used to filter the desired columns to keep
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'Building_Total_Zone Operative Temperature (°C) (mean)',
        'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
        'Building_Total_AFN Zone Infiltration Air Change Rate (ach) (summed)'
    ]
)


# So, we have already filtered the columns we wanted. Let's look at the result:

# In[17]:


dataset_hourly.df


# As you can see, the number of columns have been reduced to 29, which are 22 columns for the index and categorical data, and the 7 columns we filtered.

# ## 3. Making graphs

# At this point, you might be confused about what can you analyse and plot. The way to identify the IDFs individually is combining or gathering the categorical variables that make them different. In this case, for the IDFs, these are ComfMod and HVACmode (as we requested in the addAccis instance). In case of the EPW files, the columns related to these are:

# In[18]:


[i for i in dataset_hourly.df if 'EPW' in i]


# Therefore, ``EPW_City_or_subcountry`` should be enough to identify them, since it's the only categorical variables with multiple values (i.e. ``Country`` is always "United-Kingdom", and ``EPW_Scenario-Year``, ``EPW_Scenario`` and ``EPW_Year`` are "Present" in all cases).
# 
# To get a clearer view, you can use the method ``gather_vars_query``, which will provide a list of the categorical variables extracted from the csv filename that change, and therefore, can be used in the analysis, and the values these contain. Let's try it:

# In[19]:


dataset_hourly.gather_vars_query()


# ### 3.1 Scatter plot:

# Therefore, based on the output of ``gather_vars_query()``, some possible interesing graph would be a ``seaborn.FacetGrid`` -alike plot (or graph with subplots), which would have the combination of arguments ``CAT`` and ``ComfMod`` in the columns, and the values for the cities in the rows. Let's plot it:

# In[20]:


dataset_hourly.scatter_plot(
    vars_to_gather_rows=['ComfMod', 'CAT'], # variables to gather in rows of subplots
    vars_to_gather_cols=['EPW_City_or_subcountry'],# variables to gather in columns of subplots
    detailed_rows=['CM_0[CA_3', 'CM_3[CA_3'], #we only want to see those combinations
    data_on_x_axis='BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)', #column name (string) for the data on x axis

    data_on_y_main_axis=[ # similarly to above, a list including the name of the secondary y-axis and the column names you want to plot in it
        [
            'Energy (kWh/m2)',
            [
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
            ]
        ],
    ],
    data_on_y_sec_axis=[ #list which includes the name of the axis on the first place, and then in the second place, a list which includes the column names you want to plot
        [
            'Air renovation (ach)',
            [
                'Building_Total_AFN Zone Infiltration Air Change Rate (ach) (summed)'
            ]
        ],
        [
            'Operative Temperature (°C)',
            [
                'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
                'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
                'Building_Total_Zone Operative Temperature (°C) (mean)',
            ]
        ],
    ],

    colorlist_y_main_axis=[
        [
            'Energy (kWh/m2)',
            [
                'cyan',
                'orange',
            ]
        ],

    ],
    colorlist_y_sec_axis=[
        [
            'Air renovation (ach)',
            [
                'yellow'
            ]
        ],
        [
            'Operative Temperature (°C)',
            [
                'b',
                'r',
                'g',
            ]
        ],
    ],
    
    supxlabel='Running Mean Outdoor Temperature (°C)', # data label on x axis
    figname=f'WIP_scatterplot_RMOT',
    figsize=6,
    ratio_height_to_width=0.33,
    confirm_graph=True
)


# ### 3.2 Adaptive vs Static data scatter plot:

# A very specific type of scatter plot can be done to show the relationship between data related to adaptive and static setpoint temperatures. In this case, you would need to use the ``scatter_plot_with_baseline()`` function.

# In[ ]:


dataset_hourly.scatter_plot_with_baseline(
    vars_to_gather_rows=['EPW_City_or_subcountry'], #you can enter multiple variables, for example: ['EPW_City_or_subcountry', 'EPW_Scenario-Year']
    vars_to_gather_cols=['ComfMod', 'CAT'], #you can enter multiple variables
    data_on_y_axis_baseline_plot=[ # in this case, you only need to specify a list which includes the data columns you want to plot
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ],
    baseline='CM_0[CA_1', # the baseline needs to be in vars_to_gather_cols, and it's going to be shown on x axis. Given the variables we have simulated, you can choose between 'CM_0[CA_1', 'CM_0[CA_2', 'CM_0[CA_3', 'CM_3[CA_1', 'CM_3[CA_2' and 'CM_3[CA_3'
    colorlist_baseline_plot_data=[
        'b',
        'r',
    ],
    
    supxlabel='Static Energy Demand (kWh/m2)',
    supylabel='Adaptive Energy Demand (kWh/m2)',
    figname='WIP_scatterplot_adap_vs_stat',
    figsize=3,
    confirm_graph=True
)


# Now, let's delete all the images we have created to save some space:

# In[ ]:
new_files = [i for i in os.listdir() if i not in previous_files]
for i in new_files:
    os.remove(i)


# for i in os.listdir():
#     if i.endswith('.png'):
#         os.remove(i)


# ## 4. Making tables

# Now, let's make some tables comparing results. For example, let's make a table to show monthly values of heating and cooling energy demand. First, let's generate the dataset with monthly frequency and let's filter the columns to keep heating and cooling demand at building level.

# In[ ]:


from accim.data.postprocessing.main import Table
dataset_monthly = Table(
    #datasets=list Since we are not specifying any list, it will use all available CSVs in the folder
    source_frequency='hourly',
    frequency='monthly',
    frequency_agg_func='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    level_excluded_zones=[],
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
)

dataset_monthly.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ]
)


# Now, let's make the table we are looking for. You can choose 'multiindex', 'unstack' or 'pivot' as a reshaping method (remember that we are actually working with Pandas Dataframes). Let's go with unstack, and we are going to compare the baseline shown below with all gathered variables

# In[ ]:


dataset_monthly.wrangled_table(
    reshaping='unstack', #can be 'unstack' or 'pivot'
    vars_to_gather=['ComfMod', 'CAT'],
    vars_to_keep=['EPW_City_or_subcountry', 'Month'],
    baseline='CM_0[CA_1',
    comparison_mode=['baseline compared to others'], #can be 'baseline compared to others' or 'others compared to baseline'
    comparison_cols=['relative', 'absolute'] #'relative' to show the difference as a percentage, 'absolute' to show the difference by subtracting
)


# In[ ]:


dataset_monthly.wrangled_df_unstacked


# Let's make a different dataset to work with runperiod frequency.

# In[ ]:


from accim.data.postprocessing.main import Table
dataset_runperiod = Table(
    #datasets=list Since we are not specifying any list, it will use all available CSVs in the folder
    source_frequency='hourly',
    frequency='runperiod',
    frequency_agg_func='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    level_excluded_zones=[],
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
)

dataset_runperiod.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ]
)


# In this case, we are going to use the 'pivot' reshaping option:

# In[ ]:


dataset_runperiod.wrangled_table(
    reshaping='pivot',
    vars_to_gather=['ComfMod', 'CAT'],
    baseline='CM_0[CA_1',
    comparison_mode=['baseline compared to others'],
    comparison_cols=['relative', 'absolute']
)


# In[ ]:


dataset_runperiod.wrangled_df_pivoted


# Again, please remember we are working with Pandas Dataframe objects. That means we can modify the df we have generated. For instance, we can simplify it by removing all rows except those with 'CA_3' in the Category column, as shown below.

# In[ ]:


dataset_runperiod.df = dataset_runperiod.df[
    dataset_runperiod.df['CAT'].isin(['CA_3'])
]


# In[ ]:


dataset_runperiod.df


# And now we could make a similar pivoted table as above, but simplified to show only CA_3:

# In[ ]:


dataset_runperiod.wrangled_table(
    reshaping='pivot',
    vars_to_gather=['ComfMod'],
    baseline='CM_0',
    comparison_mode=['baseline compared to others'],
    comparison_cols=['relative', 'absolute']
)


# In[ ]:


dataset_runperiod.wrangled_df_pivoted


# Another method to achieve this is generating a different Table object, only reading the CSV files with CA_3 in it name:

# In[ ]:


import os
from accim.data.postprocessing.main import Table

dataset = [i for i in os.listdir() if i.endswith('.csv') and 'CA_3' in i]

dataset_runperiod_simplified_1 = Table(
    datasets=dataset,
    source_frequency='hourly',
    frequency='runperiod',
    frequency_agg_func='sum',
    # this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    level_excluded_zones=[],
    split_epw_names=True,  # to split EPW names based on the format Country_City_RCPscenario-YEar
)

dataset_runperiod_simplified_1.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ]
)

dataset_runperiod_simplified_1.wrangled_table(
    reshaping='pivot',
    vars_to_gather=['ComfMod'],
    baseline='CM_0',
    comparison_mode=['baseline compared to others'],
    comparison_cols=['relative', 'absolute']
)




# You can see below the resulting table is exactly the same:

# In[ ]:


dataset_runperiod_simplified_1.wrangled_df_pivoted


# You can finally export the table as xlsx format:

# In[ ]:


dataset_runperiod_simplified_1.wrangled_df_pivoted.to_excel('building_energy_demand.xlsx')


# Let's delete it now:

# In[ ]:
new_files = [i for i in os.listdir() if i not in previous_files]
for i in new_files:
    os.remove(i)


# for i in os.listdir():
#     if i.endswith('.xlsx'):
#         os.remove(i)

