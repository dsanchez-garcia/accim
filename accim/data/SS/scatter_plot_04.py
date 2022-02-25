from accim.data.datawrangling import Table
import time
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import pandas as pd
import collections

start1 = time.time()

# making df
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
missing_row = z.df[z.df['Date/Time']=='07/06 12:00']
missing_row_2 = z.df[z.df['Date/Time']=='None/ None:00']

z.df[47579]

datelist = list(z.df['Date/Time'])

occurrences = collections.Counter(datelist)
for i in occurrences:
    if occurrences[i] != 12:
        print(i)
        print(occurrences[i])

# z.df['Hour_mod'] = (pd.to_numeric(z.df['Hour'])-1).astype(str).str.pad(width=2, side='left', fillchar='0')
# for i in range(len(z.df)):
#     if '.' in z.df.loc[i, 'Hour_mod']:
#         print(i)
#         print(z.df.loc[i, 'Hour_mod'])
#
# dates = z.df['Date/Time']
#
# # for i in dates:
# #     if len(i) > 11:
# #         print(i)
#
# z.df['Hour'] = z.df['Hour'].str.replace('.0','').str.pad(width=2, side='left', fillchar='0')
#
#
# for i in range(len(z.df)):
#     if len(z.df.loc[i, 'Date/Time']) > 11:
#         # print(z.df.loc[i, 'Hour'])
#         print(i)
#         print(z.df.loc[i, 'Date/Time'])


# print(z.df['Date/Time_orig'])
# z.df['Date/Time_orig'] = z.df['Date/Time'].copy()

# listx = ['0'+str(i) if i<10 else str(i) for i in range(1,25)]
#
# z.df['Hour']
#
# any(z.df.loc[0, 'Hour'] in x for x in listx)
#
# for i in range(len(z.df)):
#     if not(any(z.df.loc[i, 'Hour'] in x for x in listx)):
#         # print(z.df.loc[i, 'Hour'])
#         print(i)
#
# z.df.loc[len(z.df['Hour']) > 2, 'Source']


# print(*z.df.columns, sep='\n')

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
# print(*z.df.columns, sep='\n')

# z.df.to_excel('temp.xlsx')

z.generate_fig_data(
    vars_to_gather_rows=['EPW'],
    vars_to_gather_cols=['Adaptive Standard', 'Category'],
    detailed_rows=[
        'London_RCP85_2100',
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

# len(z.df_for_graph)
# len(z.df)



## Version 01
# start2 = time.time()
#
# # fig = plt.figure()
# plt.plot(z.df_for_graph['Adaptive Heating Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_Present'])
# plt.plot(z.df_for_graph['Adaptive Cooling Setpoint Temperature_No Tolerance (°C)[AS_EN16798[CA_3[London_Present'])
# plt.plot(z.df_for_graph['Building_Total_Zone Thermostat Operative Temperature (°C) [mean][AS_EN16798[CA_3[London_Present'])
#
# plt.savefig('temp_time_plot.png')
#
# end2 = time.time()
# print(end2-start2)

## Version 02
# start3 = time.time()
# figsize = 15
# fig, ax = plt.subplots(nrows=len(z.rows),
#                        ncols=len(z.cols),
#                        sharex=True,
#                        sharey=True,
#                        constrained_layout=True,
#                        figsize=(figsize * len(z.cols), figsize * len(z.rows)/3))
#
# len(z.df_for_graph)
# dates = z.df['Date/Time']
#
# # for i in dates:
# #     if len(i) > 11:
# #         print(i)
#
# # for i in range(len(z.df)):
# #     if len(z.df.loc[i, 'Date/Time']) > 11:
# #         # print(z.df.loc[i, 'Hour'])
# #         print(i)
# #
# # z.df.loc[52558]['Source']
#
# # dates_copy = dates.copy()
# # dates_copy[23] = '01/01 00:'
# # temp = datetime.datetime.strptime(dates_copy[23], "%d/%m %H:%M").date()
#
# # z.df['Date/Time'][0]
# x_values = [datetime.datetime.strptime(d, "%d/%m %H:%M").date() for d in dates]
# current_axis = plt.gca()
# formatter = mdates.DateFormatter("%d/%m %H:%M")
#
# ax.xaxis.set_major_formatter(formatter)
# locator = mdates.MonthLocator()
# ax.xaxis.set_major_locator(locator)
#
#
# for i in range(len(z.rows)):
#     for j in range(len(z.cols)):
#         for k in range(len(z.y_list_main[i][j][2])):
#             if len(z.rows) == 1 and len(z.cols) == 1:
#                 ax.plot(
#                     # self.x_list[i][j][2],
#                     z.y_list_main[i][j][2][k],
#                     linewidth=1
#                     # c=self.y_list_main[i][j][4][k],
#                     # ms=markersize,
#                     # marker='o',
#                     # alpha=0.5,
#                     # label=self.y_list_main[i][j][3][k]
#                 )
#             # if len(z.rows) == 1 and len(z.cols) > 1:
#             #     ax[i, j].plot(
#             #         # self.x_list[i][j][2],
#             #         z.y_list_main[i][j][2][k],
#             #         linewidth=1
#             #         # c=self.y_list_main[i][j][4][k],
#             #         # ms=markersize,
#             #         # marker='o',
#             #         # alpha=0.5,
#             #         # label=self.y_list_main[i][j][3][k]
#             #     )
#             if len(z.cols) == 1 and len(z.rows) > 1:
#                 ax[i].plot(
#                     # self.x_list[i][j][2],
#                     z.y_list_main[i][j][2][k],
#                     linewidth=1
#                     # c=self.y_list_main[i][j][4][k],
#                     # ms=markersize,
#                     # marker='o',
#                     # alpha=0.5,
#                     # label=self.y_list_main[i][j][3][k]
#                 )
#             else:
#                 ax[i, j].plot(
#                     # self.x_list[i][j][2],
#                     z.y_list_main[i][j][2][k],
#                     linewidth=1
#                     # c=self.y_list_main[i][j][4][k],
#                     # ms=markersize,
#                     # marker='o',
#                     # alpha=0.5,
#                     # label=self.y_list_main[i][j][3][k]
#                 )
# plt.savefig('temp_time_plot_3.png',
#             dpi=900)
#
# end3 = time.time()
# print(end3-start3)

## Version 03
# start4 = time.time()
#
# z.WIP_timeline_plot(
#     supxlabel='Time',
#     supylabel='Tempreature',
#     figname='temp_time_plot_4_test',
#     figsize=18
# )
# end4 = time.time()
# print(end4-start4)

## Version 04
# start5 = time.time()
#
# z.WIP_timeline_plot_2(figname='temp_time_plot_5',
#                   figsize=15)
# end5 = time.time()
# print(end5-start5)



##
end1 = time.time()
print(end1-start1)

