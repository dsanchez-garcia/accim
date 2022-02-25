from accim.data.datawrangling import Table
import time
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import pandas as pd
import collections

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

additional_list = [
    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    # 'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    # 'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    # 'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]

custom_cols_list = additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               manage_epw_names=False
               )



##
z.generate_fig_data(
    vars_to_gather_rows=['EPW'],
    vars_to_gather_cols=['Adaptive Standard', 'Category'],
    detailed_rows=[
        'London_RCP85_2100',
        'London_RCP85_2050',
        'London_Present'
    ],
    detailed_cols=[
        'AS_CTE[CA_X',
        'AS_EN16798[CA_1'
    ],
    graph_mode='anything else',
    data_on_x_axis=[
        'Date/Time'
        # 'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    ],
    data_on_y_main_axis=[
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
        # 'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
        # 'Building_Total_Heating Energy Demand (kWh/m2) [summed]',

    ],
    colorlist=[
        'b',
        'r',
        'g'
    ],
    confirm_graph=True
)
z.df_for_graph['Date/Time'] = z.df_for_graph.index

freq_graph_dict = {
    'timestep': ['X?', "%d/%m %H:%M"],
    'hourly': ['H', "%d/%m %H:%M"],
    'daily': ['D', "%d/%m"],
    'monthly': ['M?', "%m"],
    'runperiod': ['?', "?"]
}

start_date = datetime.datetime.strptime(z.df_for_graph['Date/Time'][0], freq_graph_dict[frequency][1])
# end_date = datetime.datetime.strptime(z.df_for_graph['Date/Time'][len(z.df_for_graph)-1], "%d/%m %H:%M")
# (end_date-start_date).days


z.df_for_graph['Date/Time'] = pd.date_range(
    start=start_date,
    periods=len(z.df_for_graph),
    # '2017-31-12 23:00',
    freq = freq_graph_dict[frequency][0]
)

# todo consider not to set Date/time as index, since it needs to be specified anyway in timeplot
z.df_for_graph.set_index(z.df_for_graph['Date/Time'], inplace=True)
z.df_for_graph = z.df_for_graph.drop(z.df_for_graph['Date/Time'])

##
start3 = time.time()
figsize = 15
fig, ax = plt.subplots(nrows=len(z.rows),
                       ncols=len(z.cols),
                       sharex=True,
                       sharey=True,
                       constrained_layout=True,
                       figsize=(figsize * len(z.cols), figsize * len(z.rows)/3))

for i in range(len(z.rows)):
    for j in range(len(z.cols)):
        current_axis = plt.gca()
        current_axis.xaxis.set_major_formatter(mdates.DateFormatter(freq_graph_dict[frequency][1]))
        current_axis.xaxis.set_major_locator(mdates.MonthLocator())

        for k in range(len(z.y_list_main[i][j][2])):
            if len(z.rows) == 1 and len(z.cols) == 1:
                ax.plot(
                    z.df_for_graph.index,
                    z.y_list_main[i][j][2][k],
                    linewidth=1,
                    c=z.y_list_main[i][j][4][k],
                    label=z.y_list_main[i][j][3][k]
                )
            elif len(z.rows) == 1 and len(z.cols) > 1:
                ax[i, j].plot(
                    z.df_for_graph.index,
                    z.y_list_main[i][j][2][k],
                    linewidth=1,
                    c=z.y_list_main[i][j][4][k],
                    label=z.y_list_main[i][j][3][k]
                )
            elif len(z.cols) == 1 and len(z.rows) > 1:
                ax[i].plot(
                    z.df_for_graph.index,
                    z.y_list_main[i][j][2][k],
                    linewidth=1,
                    c=z.y_list_main[i][j][4][k],
                    label=z.y_list_main[i][j][3][k]
                )
            else:
                ax[i, j].plot(
                    z.df_for_graph.index,
                    z.y_list_main[i][j][2][k],
                    linewidth=1
                    # c=z.y_list_main[i][j][4][k],
                    # ms=markersize,
                    # marker='o',
                    # alpha=0.5,
                    # label=z.y_list_main[i][j][3][k]
                )

plt.show()
# plt.savefig('temp_time_plot_3.png',
#             dpi=900)

end3 = time.time()
print(end3-start3)




##
fig, ax = plt.subplots(nrows=1,
                       ncols=1,
                       sharex=True,
                       sharey=True,
                       constrained_layout=True,
                       figsize=(15, 5)
                       )
ax.plot(
    # x
    # z.x_list[i][j][2],
    # x_values,
    # 'Date/Time',
    # z.df_for_graph.index,
    z.df_for_graph.index,

    # y
    # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100',
    # z.df_for_graph['Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100'],
    z.df_for_graph['Building_Total_Cooling Energy Demand (kWh/m2) [summed][AS_EN16798[CA_3[London_RCP85_2100'],


    # temp_df.test


    # data=z.df_for_graph,
    # linewidth=1
    # c=z.y_list_main[i][j][4][k],
    # ms=markersize,
    # marker='o',
    # alpha=0.5,
    # label=z.y_list_main[i][j][3][k]
)
current_axis = plt.gca()

current_axis.xaxis.set_major_formatter(mdates.DateFormatter(freq_graph_dict[frequency][1]))
current_axis.xaxis.set_major_locator(mdates.MonthLocator())

plt.show()


# z.df_for_graph.to_csv('unstacked_csv_data.csv')

## Version 02
# for i in z.df_for_graph.index:
#     z.df_for_graph.loc[i, 'Date'] = datetime.datetime.strptime(
#         str(i),
#         # z.df_for_graph.loc[i, 'Date/Time_temp'],
#         "%d/%m %H:%M"
#     ).date()
#     z.df_for_graph.loc[i, 'Time'] = datetime.datetime.strptime(
#         str(i),
#         # z.df_for_graph.loc[i, 'Date/Time_temp'],
#         "%d/%m %H:%M"
#     ).time()
#     z.df_for_graph.loc[i, 'Date/Time'] = datetime.datetime.combine(
#         z.df_for_graph.loc[i, 'Date'],
#         z.df_for_graph.loc[i, 'Time']
#     )
#
# z.df_for_graph.set_index([z.df_for_graph['Date/Time']], inplace=True)
# z.df_for_graph['test'] = range(len(z.df_for_graph))

##

plt.plot_date(z.df_for_graph.index, z.df_for_graph.test)


##

first = list(z.df_for_graph.index)[0]


temp_df = z.df_for_graph.copy()

temp_df['temp_date'] =pd.date_range(
    start='2017-01-01 00:00',
    periods=8760,
    # '2017-31-12 23:00',
    freq = 'H'
)

temp_df.set_index(temp_df['temp_date'], inplace=True)


fig, ax = plt.subplots(nrows=1,
                       ncols=1,
                       sharex=True,
                       sharey=True,
                       constrained_layout=True,
                       figsize=(15, 5)
                       )
ax.plot(
    # x
    # z.x_list[i][j][2],
    # x_values,
    # 'Date/Time',
    # z.df_for_graph.index,
    temp_df.index,

    # y
    # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100',
    # z.df_for_graph['Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100'],
    temp_df.test


    # data=z.df_for_graph,
    # linewidth=1
    # c=z.y_list_main[i][j][4][k],
    # ms=markersize,
    # marker='o',
    # alpha=0.5,
    # label=z.y_list_main[i][j][3][k]
)

current_axis = plt.gca()

current_axis.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
current_axis.xaxis.set_major_locator(mdates.MonthLocator())

plt.show()




##
fig, ax = plt.subplots(nrows=1,
                       ncols=1,
                       sharex=True,
                       sharey=True,
                       constrained_layout=True,
                       figsize=(15, 5)
                       )
ax.plot(
    # x
    # z.x_list[i][j][2],
    # x_values,
    # 'Date/Time',
    # z.df_for_graph.index,

    # y
    # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100',
    # z.df_for_graph['Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100'],
    z.df_for_graph.test


    # data=z.df_for_graph,
    # linewidth=1
    # c=z.y_list_main[i][j][4][k],
    # ms=markersize,
    # marker='o',
    # alpha=0.5,
    # label=z.y_list_main[i][j][3][k]
)
plt.show()

##
current_axis = plt.gca()
formatter = mdates.DateFormatter("%d/%m %H:%M")

current_axis.xaxis.set_major_formatter(formatter)
locator = mdates.MonthLocator()
current_axis.xaxis.set_major_locator(locator)

plt.show()

plt.locator_params(axis='x', nbins=10)


plt.show()
# plt.savefig('temp_time_plot_3.png',
#             dpi=900)


