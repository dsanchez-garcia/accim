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

files = [f for f in allfiles if
         'London_Present' in f and 'AS_EN16798[CA_3' in f or
         'London_RCP85_2100' in f and 'AS_EN16798[CA_3' in f or
         'London_Present' in f and 'AS_CTE[CA_X' in f or
         'London_RCP85_2100' in f and 'AS_CTE[CA_X' in f
         ]


z = Table(
    datasets=files,
    frequency=frequency,
    sum_or_mean='sum',
    standard_outputs=True,
    level=['building'],
    level_sum_or_mean=['sum', 'mean'],
    match_cities=False,
    manage_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    )

# todo add function to amend epw names before simulation; then amend datawrangling to automatically manage epw names if required,
# todo function for average of high and low temps: groupby source and day, then agg max, then groupby month and agg mean
print(*z.df.columns, sep='\n')
##
# z.df.to_excel('temp_runperiod.xlsx')

additional_list = [
    'Site Outdoor Air Drybulb Temperature (°C)',
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
               manage_epw_names=True
               )

