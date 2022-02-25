from accim.data.datawrangling import Table
import time
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import pandas as pd
import collections
start = time.time()
frequency = 'runperiod'

import glob

allfiles = glob.glob('*.csv', recursive=True)
files_desired = [
    'London_Present',
    'London_RCP85_2100',
    'AS_EN16798[CA_3',
]
files = [f for f in allfiles if all(d in f for d in files_desired)]

files = [f for f in allfiles if
         # 'London_Present' in f and 'AS_EN16798[CA_3' in f or
         # 'London_RCP85_2100' in f and 'AS_EN16798[CA_3' in f or
         # 'London_Present' in f and 'AS_CTE[CA_X' in f or
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
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    )

z.df.to_excel('temp_runperiod.xlsx')

##

additional_list = [
    'Site Outdoor Air Drybulb Temperature (°C)',
    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    'Building_Total_AFN Zone Infiltration Volume (m3) [summed]',
    'Building_Total_Comfortable Hours_No Applicability (h) [mean]'
]

custom_cols_list = additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               manage_epw_names=False
               )

print(*z.df.columns, sep='\n')


##

z.generate_fig_data(
    vars_to_gather_rows=[
        'EPW',
        # 'Adaptive Standard',
        # 'Category'
    ],
    vars_to_gather_cols=[
        # 'EPW',
        'Adaptive Standard',
        'Category'
    ],
    detailed_rows=[
        'London_Present',
        # 'London_RCP85_2050',
        'London_RCP85_2100',

        # 'AS_CTE[CA_X',
        # 'AS_EN16798[CA_3'
    ],
    detailed_cols=[
        # 'London_Present',
        # 'London_RCP85_2050',
        # 'London_RCP85_2100',

        # 'AS_CTE[CA_X',
        'AS_EN16798[CA_3'
    ],

    # adap_vs_stat_data_y_main=[
    #         'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    #         'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    # ],
    # baseline=(
    #     'AS_CTE[CA_X'
    #     # 'London_Present',
    # ),
    # colorlist_adap_vs_stat_data=[
    #     'b',
    #     'r'
    # ],

    # temporarily unavailable
    # adap_vs_stat_data_y_sec=[
    #         'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    # ],

    data_on_x_axis=(
        # 'Date/Time'
        # 'Site Outdoor Air Drybulb Temperature (°C)'
        'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)'
    ),
    data_on_y_main_axis=[
        ['Temperature',[
            'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
            'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
            'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
        ]
         ],
    ],

    data_on_y_sec_axis=[
        ['Energy demand',[
            'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
            'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
            ]
         ],
        ['Infiltration Volume',[
            'Building_Total_AFN Zone Infiltration Volume (m3) [summed]'
            ],
        ],
        ['Comfort hours', [
            'Building_Total_Comfortable Hours_No Applicability (h) [mean]'
        ],
         ],
    ],

    colorlist_y_main_axis=[
        ['Temperature',[
            'b',
            'r',
            'g',
            ]
         ],
    ],

    colorlist_y_sec_axis=[
        ['Energy demand', [
            'c',
            'm',
        ]
         ],
        ['Infiltration Volume', [
            'y'
        ],
         ],
        ['Comfort hours', [
            'orange'
        ],
         ],
    ]
)
