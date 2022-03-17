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
    # datasets=files,
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

# z.df.to_excel('temp_runperiod.xlsx')


##

temp_df = z.df[z.df.Source == 'TestModel_onlyGeometryForVRFsystem_V960_pymod[AS_CTE[CA_X[CM_X[HM_2[VC_1[VO_0[MT_0[MW_0[AT_0.1[London_RCP85_2100']

print(*temp_df.columns, sep='\n')

plt.scatter(x='Site Outdoor Air Drybulb Temperature (°C)',
            y='Building_Total_AFN Zone Infiltration Volume (m3) [summed]',
            c='Building_Total_Total Energy Demand (kWh/m2) [summed]',
            # c='Month',
            s='Site Wind Speed (m/s)',
            alpha=0.5,
            cmap='rainbow',
            data=temp_df)
plt.colorbar(label='wha')

##
import seaborn as sns
temp_df = z.df[z.df.Source == 'TestModel_onlyGeometryForVRFsystem_V960_pymod[AS_CTE[CA_X[CM_X[HM_2[VC_1[VO_0[MT_0[MW_0[AT_0.1[London_RCP85_2100']

temp_plot1 = sns.scatterplot(
    x='Site Outdoor Air Drybulb Temperature (°C)',
    y='Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    # c='Building_Total_Total Energy Demand (kWh/m2) [summed]',
    # s='Site Wind Speed (m/s)',
    alpha=0.5,
    cmap='rainbow',
    hue='Category',
    legend='full',
    data=temp_df
)

ax2 = plt.twinx()

temp_plot2 = sns.scatterplot(
    x='Site Outdoor Air Drybulb Temperature (°C)',
    y='Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    # c='Building_Total_Total Energy Demand (kWh/m2) [summed]',
    # s='Site Wind Speed (m/s)',
    alpha=0.5,
    cmap='rainbow',
    hue='Category',
    legend='full',
    data=temp_df,
    ax=ax2
)

# temp_plot1.add_legend()
# temp_plot1.savefig('temp_x_2.png')

##

import seaborn as sns

temp_plot = sns.FacetGrid(
    z.df,
    row='EPW',
    col='Category',
    margin_titles=True,
    legend_out=True
              )

temp_plot.map_dataframe(
    sns.scatterplot,
    x='Site Outdoor Air Drybulb Temperature (°C)',
    y='Building_Total_AFN Zone Infiltration Volume (m3) [summed]',
    # c='Building_Total_Total Energy Demand (kWh/m2) [summed]',
    # s='Site Wind Speed (m/s)',
    alpha=0.5,
    cmap='rainbow',
    hue='Month',
    legend='full',
)
temp_plot.add_legend()
temp_plot.savefig('temp_x_2.png')




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
               split_epw_names=False
               )

# print(*z.df.columns, sep='\n')


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

        'AS_CTE[CA_X',
        # 'AS_EN16798[CA_3'
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

##
z.time_plot(supxlabel='temp',
            figname='temp_x',
            figsize=6,
            ratio_height_to_width=1/4,
            confirm_graph=True
            )