from accim.data.datawrangling import Table
import time
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import pandas as pd
import collections
start = time.time()
frequency = 'hourly'

import glob

allfiles = glob.glob('*.csv', recursive=True)
files_desired = [
    'London_Present',
    'London_RCP85_2100',
    'AS_EN16798[CA_3',
]
files = [f for f in allfiles if all(d in f for d in files_desired)]

# files = [f for f in allfiles if
#          'London_Present' in f and 'AS_EN16798[CA_3' in f or
#          'London_RCP85_2100' in f and 'AS_EN16798[CA_3' in f or
#          'London_Present' in f and 'AS_CTE[CA_X' in f or
#          'London_RCP85_2100' in f and 'AS_CTE[CA_X' in f
#          ]

files = [f for f in allfiles if
         'Japan_Nagasaki_Present' in f and 'AS_JPN[CA_3[CM_3' in f or
         'Japan_Nagasaki_RCP85-2100' in f and 'AS_JPN[CA_3[CM_3' in f
         ]


z = Table(
    datasets=files,
    frequency=frequency,
    sum_or_mean='sum',
    standard_outputs=True,
    level=['building'],
    level_sum_or_mean=['sum', 'mean'],
    match_cities=False,
    manage_epw_names=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    )

# print(*z.df.columns, sep='\n')

# z.df.to_excel('temp_runperiod.xlsx')

additional_list = [
    'Site Outdoor Air Drybulb Temperature (°C)',
    'Site Outdoor Air Relative Humidity (%)'
    # 'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    # 'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    # 'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    # 'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    # 'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    # 'Building_Total_AFN Zone Infiltration Volume (m3) [summed]',
    # 'Building_Total_Comfortable Hours_No Applicability (h) [mean]'
]


custom_cols_list = additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               split_epw_names=True
               )

# DONEtodo add function to amend epw names before simulation; then amend datawrangling to automatically manage epw names if required

# todo function for average of high and low temps: groupby source and day, then agg max, then groupby month and agg mean
vars_to_analyse = [
    'Site Outdoor Air Drybulb Temperature (°C)',
    'Site Outdoor Air Relative Humidity (%)'
]
site_dict = {}
for i in vars_to_analyse:
    temp = {i: ['mean', 'max', 'min']}
    site_dict.update(temp)

# z.df = z.df.groupby(['Source', 'Month', 'Day']).agg({
#     'Site Outdoor Air Drybulb Temperature (°C)': [
#         'mean',
#         'max',
#         'min'
#     ]})

df_for_graph_monthly_site = z.df.copy()
# z.df = z.df.groupby(['Source', 'Month', 'Day']).agg(site_dict)
df_for_graph_monthly_site = df_for_graph_monthly_site.groupby(['Source', 'Month', 'Day']).agg(site_dict).groupby(['Source', 'Month']).agg('mean')

df_for_graph_monthly_site.columns = df_for_graph_monthly_site.columns.map('['.join)
##

df_for_graph_monthly_site['new'] = ['_'.join(map(str, i)) for i in df_for_graph_monthly_site.index.tolist()]
df_for_graph_monthly_site['data'] = 'temp'

df_for_graph_monthly_site = df_for_graph_monthly_site.set_index([pd.RangeIndex(len(df_for_graph_monthly_site))])

for i in range(len(df_for_graph_monthly_site)):
    df_for_graph_monthly_site.loc[i, 'data'] = str(df_for_graph_monthly_site.loc[i, 'new']).split('[')[-1]

df_for_graph_monthly_site[[
    'EPW_Country_name',
    'EPW_City_or_subcountry',
    'EPW_Scenario-Year',
    'Month'
    ]] = df_for_graph_monthly_site['data'].str.split('_', expand=True)



##
