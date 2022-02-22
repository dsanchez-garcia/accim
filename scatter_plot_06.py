from accim.data.datawrangling import Table
import time
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import pandas as pd
import collections

z = Table(frequency='hourly',
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
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
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
        # 'London_RCP85_2100',
        'London_Present'
    ],
    detailed_cols=[
        # 'AS_CTE[CA_X',
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
    ],
    colorlist=[
        'b',
        'r',
        'g'
    ],
    confirm_graph=True
)
z.df_for_graph['Date/Time'] = z.df_for_graph.index
start_date = datetime.datetime.strptime(z.df_for_graph['Date/Time'][0], "%d/%m %H:%M")
end_date = datetime.datetime.strptime(z.df_for_graph['Date/Time'][len(z.df_for_graph)-1], "%d/%m %H:%M")
(end_date-start_date).days

freq_dict = {
    'timestep': 'X',
    'hourly': 'H',
    'daily': 'D',
    'monthly': 'M?',
    'runperiod': '?'
}
frequency = 'hourly'

z.df_for_graph['temp_date'] =pd.date_range(
    start=start_date,
    periods=len(z.df_for_graph),
    # '2017-31-12 23:00',
    freq = freq_dict[frequency]
)

z.df_for_graph.set_index(z.df_for_graph['temp_date'], inplace=True)

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
    # self.x_list[i][j][2],
    # x_values,
    # 'Date/Time',
    # z.df_for_graph.index,
    z.df_for_graph.index,

    # y
    # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100',
    z.df_for_graph['Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100'],
    # temp_df.test


    # data=z.df_for_graph,
    # linewidth=1
    # c=self.y_list[i][j][4][k],
    # ms=markersize,
    # marker='o',
    # alpha=0.5,
    # label=self.y_list[i][j][3][k]
)
current_axis = plt.gca()

current_axis.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
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
    # self.x_list[i][j][2],
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
    # c=self.y_list[i][j][4][k],
    # ms=markersize,
    # marker='o',
    # alpha=0.5,
    # label=self.y_list[i][j][3][k]
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
    # self.x_list[i][j][2],
    # x_values,
    # 'Date/Time',
    # z.df_for_graph.index,

    # y
    # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100',
    # z.df_for_graph['Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_RCP85_2100'],
    z.df_for_graph.test


    # data=z.df_for_graph,
    # linewidth=1
    # c=self.y_list[i][j][4][k],
    # ms=markersize,
    # marker='o',
    # alpha=0.5,
    # label=self.y_list[i][j][3][k]
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


