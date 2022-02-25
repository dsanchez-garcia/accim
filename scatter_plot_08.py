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

print(*z.df.columns, sep='\n')

additional_list = [
    # 'Site Outdoor Air Drybulb Temperature (°C)',
    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    # 'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    'Building_Total_AFN Zone Infiltration Volume (m3) [summed]'
]

custom_cols_list = additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               manage_epw_names=False
               )




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
    # baseline='London_Present',


    # todo temporarily unavailable
    # adap_vs_stat_data_y_sec=[
    #         'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    # ],

    data_on_x_axis=(
        'Date/Time'
        # 'Site Outdoor Air Drybulb Temperature (°C)'
        # 'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)'
    ),
    data_on_y_main_axis=[
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
        # 'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
        # 'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    ],
    data_on_y_sec_axis=[
        'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
        'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
        'Building_Total_AFN Zone Infiltration Volume (m3) [summed]'
    ],
    colorlist_y_main_axis=[
        'b',
        'r',
        'g'
    ],
    colorlist_y_sec_axis=[
        'c',
        'm'
    ]
)

# print(*z.x_list, sep='\n')
# z.rows
# z.df_for_graph.columns
# z.df_for_graph.index

##
freq_graph_dict = {
    'timestep': ['X?', "%d/%m %H:%M"],
    'hourly': ['H', "%d/%m %H:%M"],
    'daily': ['D', "%d/%m"],
    'monthly': ['M?', "%m"],
    'runperiod': ['?', "?"]
}

figsize = 7
ratio_height_to_width = 1/3

fig, ax = plt.subplots(nrows=len(z.rows),
                       ncols=len(z.cols),
                       sharex=True,
                       sharey=True,
                       constrained_layout=True,
                       figsize=(figsize * len(z.cols), ratio_height_to_width * figsize * len(z.rows)))
main_y_axis = []
sec_y_axis = []

for i in range(len(z.rows)):
    main_y_axis_temp_rows = []
    sec_y_axis_temp_rows = []
    for j in range(len(z.cols)):

        current_axis = plt.gca()
        current_axis.xaxis.set_major_formatter(mdates.DateFormatter(freq_graph_dict[z.frequency][1]))
        current_axis.xaxis.set_major_locator(mdates.MonthLocator())

        main_y_axis_temp_cols = []
        sec_y_axis_temp_cols = []

        if len(z.rows) == 1 and len(z.cols) == 1:
            for k in range(len(z.y_main_units)):
                main_y_axis_temp_cols.append(ax)
            main_y_axis_temp_rows.append(main_y_axis_temp_cols)
            if len(z.data_on_y_sec_axis) > 0:
                for k in range(len(z.y_sec_units)):
                    sec_y_axis_temp_cols.append(ax.twinx())
                sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
        elif len(z.cols) == 1 and len(z.rows) > 1:
            for k in range(len(z.y_main_units)):
                main_y_axis_temp_cols.append(ax[i])
            main_y_axis_temp_rows.append(main_y_axis_temp_cols)
            if len(z.data_on_y_sec_axis) > 0:
                for k in range(len(z.y_sec_units)):
                    sec_y_axis_temp_cols.append(ax[i].twinx())
                sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)

        else:
            for k in range(len(z.y_main_units)):
                main_y_axis_temp_cols.append(ax[i, j])
            main_y_axis_temp_rows.append(main_y_axis_temp_cols)
            if len(z.data_on_y_sec_axis) > 0:
                for k in range(len(z.y_sec_units)):
                    sec_y_axis_temp_cols.append(ax[i, j].twinx())
                sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
    main_y_axis.append(main_y_axis_temp_rows)
    sec_y_axis.append(sec_y_axis_temp_rows)

for i in range(len(z.rows)):
    for j in range(len(z.cols)):

        # main_y_axis[i][j].xaxis.set_major_formatter(mdates.DateFormatter(freq_graph_dict[z.frequency][1]))
        # main_y_axis[i][j].xaxis.set_major_locator(mdates.MonthLocator())

        for k in range(len(z.y_list_main[i][j])):
            main_y_axis[i][j][k].grid(True, linestyle='-.')
            main_y_axis[i][j][k].tick_params(axis='both',
                                             grid_color='black',
                                             grid_alpha=0.5)
            main_y_axis[i][j][k].set_facecolor((0, 0, 0, 0.10))

            for x in range(len(z.y_list_main[i][j][k]['dataframe'])):
                if i == 0 and j == 0:
                    main_y_axis[i][j][k].plot(
                        z.df_for_graph['Date/Time'],
                        z.y_list_main[i][j][k]['dataframe'][x],
                        linewidth=1,
                        c=z.y_list_main[i][j][k]['color'][x],
                        # ms=markersize,
                        # marker='o',
                        # alpha=0.5,
                        label=z.y_list_main[i][j][k]['label'][x],
                    )
                else:
                    main_y_axis[i][j][k].plot(
                        z.df_for_graph['Date/Time'],
                        z.y_list_main[i][j][k]['dataframe'][x],
                        linewidth=1,
                        c=z.y_list_main[i][j][k]['color'][x],
                        # ms=markersize,
                        # marker='o',
                        # alpha=0.5,
                    )

for i in range(len(z.rows)):
    for j in range(len(z.cols)):
        for k in range(len(z.y_list_sec[i][j])):
            if k > 0:
                # sec_y_axis[i][j][k].set_ylabel('whatever')
                sec_y_axis[i][j][k].spines["right"].set_position(("axes", 1+k*0.1))
                sec_y_axis[i][j][k].spines["right"].set_visible(True)
            for x in range(len(z.y_list_sec[i][j][k]['dataframe'])):
                if i == 0 and j == 0:
                    sec_y_axis[i][j][k].plot(
                        z.df_for_graph['Date/Time'],
                        z.y_list_sec[i][j][k]['dataframe'][x],
                        linewidth=1,
                        c=z.y_list_sec[i][j][k]['color'][x],
                        # ms=markersize,
                        # marker='o',
                        # alpha=0.5,
                        label=z.y_list_sec[i][j][k]['label'][x],
                    )
                else:
                    sec_y_axis[i][j][k].plot(
                        z.df_for_graph['Date/Time'],
                        z.y_list_sec[i][j][k]['dataframe'][x],
                        linewidth=1,
                        c=z.y_list_sec[i][j][k]['color'][x],
                        # ms=markersize,
                        # marker='o',
                        # alpha=0.5,
                    )
