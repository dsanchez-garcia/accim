from accim.data.datawrangling import Table
import time
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import pandas as pd
import collections
start = time.time()
frequency = 'hourly'
z = Table(frequency=frequency,
          sum_or_mean='sum',
          standard_outputs=True,
          level=['building'],
          level_sum_or_mean=['sum', 'mean'],
          match_cities=False,
          normalised_energy_units=True,
          rename_cols=True,
          energy_units_in_kwh=True,
          )

# print(*z.df.columns, sep='\n')

additional_list = [
    # 'Site Outdoor Air Drybulb Temperature (°C)',
    # 'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    # 'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]

custom_cols_list = additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               manage_epw_names=False
               )



z.generate_fig_data(
    vars_to_gather_rows=['EPW'],
    vars_to_gather_cols=['Adaptive Standard', 'Category'],
    detailed_rows=[
        'London_Present',
        # 'London_RCP85_2050',
        'London_RCP85_2100',
    ],
    detailed_cols=[
        # 'AS_CTE[CA_X',
        'AS_EN16798[CA_1'
    ],
    adap_vs_stat_data_y_main=[
            'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
            'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    ],
    adap_vs_stat_data_y_sec=[
            'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    ],

    # data_on_x_axis=(
    #     # 'Date/Time'
    #     'Site Outdoor Air Drybulb Temperature (°C)'
    #     # 'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)'
    # ),
    # data_on_y_main_axis=[
    #     # 'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    #     # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    #     # 'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    #     'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    #     'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    # ],
    # data_on_y_sec_axis=[
    #     # 'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    #     # 'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    # ],
    colorlist_y_main_axis=[
        'b',
        'r',
        # 'g'
    ],
    colorlist_y_sec_axis=[
        'c',
        # 'm'
    ]
)

# print(*z.x_list, sep='\n')
z.rows

##
z.WIP_scatter_plot_adap_vs_stat(
    supxlabel='Static Energy Demand',
    supylabel='Adaptive Energy Demand',
    figname='test_scatter_plot_adap_vs_stat_01',
    figsize=5,
    confirm_graph=False
)






##
z.WIP_scatter_plot(
    supxlabel='Outdoor temperature',
    supylabel='Operative temmperature',
    # y_sec_label='Energy demand',
    figname='test_scatter_plot_07_02',
    figsize=8,
    ratio_height_to_width=1,
    confirm_graph=True
)

end = time.time()
print(end-start)