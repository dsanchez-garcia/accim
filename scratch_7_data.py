from accim.data.datawrangling import Table
import matplotlib.pyplot as plt
import time
start = time.time()

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

# print(f'The number of columns and the list of these is going to be:')
# print(f'No. of columns = {len(list(set(z.df.Source)))}')
# print(f'List of columns:')
# print(*list(set(z.df.Source)), sep='\n')
#
# print(f'The number of rows and the list of these is going to be:')
# print(f'No. of rows = {len(list(set(z.df.Source)))}')

# print(*z.df.columns, sep='\n')

# z.hvac_zone_list
# z.occupied_zone_list
# z.block_list

temp_list = []
# for col in z.df.columns:
#     for zone in z.occupied_zone_list:
#         if zone in col and 'Zone Thermostat Operative Temperature' in col:
#             temp_list.append(col)

additional_list = [
    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    'BLOCK1:ZONE2_ASHRAE 55 Running mean outdoor temperature (°C)',
    'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]

custom_cols_list = temp_list + additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               manage_epw_names=False
               )

print(*z.df.columns, sep='\n')

# fig, ax = plt.subplots(3)
# for i in range(3):
#     ax[i].scatter(
#         z.df['BLOCK1:ZONE2_ASHRAE 55 Running mean outdoor temperature (°C)'],
#         z.df['Adaptive Cooling Setpoint Temperature_No Tolerance (°C)'],
#         c='r',
#         s=1,
#         marker='o',
#     )
#     plt.show()

# multiple plots
z.df['col_to_gather_in_cols'] = z.df[['Adaptive Standard', 'Category']].agg('['.join, axis=1)
z.df['col_to_gather_in_rows'] = z.df['EPW']
# print(list(set(z.df['col_to_gather_in_cols'])))

cols = list(set(z.df['col_to_gather_in_cols']))
rows = list(set(z.df['col_to_gather_in_rows']))

cols.sort()
rows.sort()

# for col in cols:
#     for row in rows:
#         x_{col}_{row} =
#
# fig, ax = plt.subplots(3, 4)
#
# for i in range(len(cols)*len(rows)):
#     ax[i].scatter(
#         z.df[
#             (z.df['col_to_gather_in_cols'] == 'AS_EN16798[CA_3') &
#             (z.df['col_to_gather_in_rows'] == 'London_Present')
#             ]['BLOCK1:ZONE2_ASHRAE 55 Running mean outdoor temperature (°C)']
#     )

# x_list = []
# for i in range(len(rows)):
#     for j in range(len(cols)):
#         temp = [
#             [i, j],
#             f'{rows[i]}_{cols[j]}',
#             z.df[
#                 (z.df['col_to_gather_in_rows'] == rows[i]) &
#                 (z.df['col_to_gather_in_cols'] == cols[j])
#                 ]['BLOCK1:ZONE2_ASHRAE 55 Running mean outdoor temperature (°C)']
#             ]
#         x_list.append(temp)

x_list = []
for i in range(len(rows)):
    temp_row = []
    for j in range(len(cols)):
        temp = [
            [i, j],
            f'{rows[i]}_{cols[j]}',
            z.df[
                (z.df['col_to_gather_in_rows'] == rows[i]) &
                (z.df['col_to_gather_in_cols'] == cols[j])
                ]['BLOCK1:ZONE2_ASHRAE 55 Running mean outdoor temperature (°C)']
            ]
        temp_row.append(temp)
    x_list.append(temp_row)


y_data_main_scatter = [
    'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]'
]
y_list_main_scatter = []
for i in range(len(rows)):
    temp_row = []
    for j in range(len(cols)):
        temp = [
            [i, j],
            f'{rows[i]}_{cols[j]}',
            [i for i in y_data_main_scatter],
            [z.df[
                (z.df['col_to_gather_in_rows'] == rows[i]) &
                (z.df['col_to_gather_in_cols'] == cols[j])
                ][k]
             for k in y_data_main_scatter
             ]]
        temp_row.append(temp)
    y_list_main_scatter.append(temp_row)

y_data_main_plot = [
    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)'
]
y_list_main_plot = []
for i in range(len(rows)):
    temp_row = []
    for j in range(len(cols)):
        temp = [
            [i, j],
            f'{rows[i]}_{cols[j]}',
            [i for i in y_data_main_plot],
            [z.df[
                (z.df['col_to_gather_in_rows'] == rows[i]) &
                (z.df['col_to_gather_in_cols'] == cols[j])
                ][k]
             for k in y_data_main_plot
             ]]
        temp_row.append(temp)
    y_list_main_plot.append(temp_row)



y_data_sec = [
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]'
]
y_list_sec = []
for i in range(len(rows)):
    temp_row = []
    for j in range(len(cols)):
        temp = [
            [i, j],
            f'{rows[i]}_{cols[j]}',
            [i for i in y_data_sec],
            [z.df[
                (z.df['col_to_gather_in_rows'] == rows[i]) &
                (z.df['col_to_gather_in_cols'] == cols[j])
                ][k]
             for k in y_data_sec
        ]]
        temp_row.append(temp)
    y_list_sec.append(temp_row)


# print(cols)
# print(rows)
# print(x_list)
# print(y_list_main_scatter)
# print(y_list_main_plot)
# print(y_list_sec)

fig, ax = plt.subplots(len(rows), len(cols))
# ax[0].scatter()
# for i in range(12):
#     ax[i].scatter()
#
# ax[0].scatter(
#     z.df['BLOCK1:ZONE2_ASHRAE 55 Running mean outdoor temperature (°C)'],
#     z.df['Building_Total_Zone Thermostat Operative Temperature (°C) [mean]'],
#     c='g',
#     s=1,
#     marker='o'
# )


# y_list_main_scatter
for i in range(len(rows)):
    for j in range(len(cols)):
        for k in range(len(y_list_main_scatter[i][j][3])):
            # if i in x_list[i][0]:
            if 'Zone Thermostat Operative Temperature' in y_list_main_scatter[i][j][2][k]:
                ax[i, j].scatter(
                    x_list[i][j][2],
                    y_list_main_scatter[i][j][3][k],
                    c='g',
                    marker='o'
                )

# y_list_main_plot
for i in range(len(rows)):
    for j in range(len(cols)):
        for k in range(len(y_list_main_plot[i][j][3])):
            if 'Cooling' in y_list_main_plot[i][j][2][k]:
                ax[i, j].plot(
                    x_list[i][j][2],
                    y_list_main_plot[i][j][3][k],
                    c='b',
                    marker='o'
                )
            if 'Heating' in y_list_main_plot[i][j][2][k]:
                ax[i, j].plot(
                    x_list[i][j][2],
                    y_list_main_plot[i][j][3][k],
                    c='r',
                    marker='o'
                )






# def format_col_name(col: str):
#     col = (col
#            .replace(' ', '_')
#            .replace(':', '_')
#            .replace('_(kWh/m2)', '')
#            .replace('_(Wh/m2)', '')
#            .replace('_(kWh)', '')
#            .replace('_(Wh)', '')
#            .replace('_(°C)', '')
#            .replace('_(h)', '')
#            .replace('_(m/s)', '')
#            .replace('[summed]', 'summed')
#            .replace('[mean]', 'mean')
#            )
#     return col
#
# cols_to_plot = [
#     'Adaptive Standard',
#     'Category'
# ]
#
# cols_to_plot = [format_col_name(i) for i in cols_to_plot]
#
# rename_dict = {}
# for col in z.df.columns:
#     temp = {col: format_col_name(col)}
#     rename_dict.update(temp)
#
# z.df = z.df.rename(columns=rename_dict)





# single plot
# sources = list(set(z.df['Source']))
# df_temp = z.df[z.df.Source =='TestModel_onlyGeometryForVRFsystem_V960_pymod[AS_ASHRAE55[CA_90[CM_3[HM_2[VC_1[VO_0[MT_0[MW_0[AT_0.1[Seville_Present']
# # print(*df_temp.columns, sep='\n')
#
#
# fig, ax = plt.subplots()
# ax.plot(
#     df_temp.BLOCK1_ZONE2_ASHRAE_55_Running_mean_outdoor_temperature,
#     df_temp.Adaptive_Cooling_Setpoint_Temperature_No_Tolerance,
#     c='r',
#     ms=1,
#     marker='o',
#     # linewidth=1
# )
# ax.plot(
#     df_temp.BLOCK1_ZONE2_ASHRAE_55_Running_mean_outdoor_temperature,
#     df_temp.Adaptive_Heating_Setpoint_Temperature_No_Tolerance,
#     c='b',
#     ms=1,
#     marker='o',
#     # linewidth=1
# )
# ax.scatter(
#     df_temp.BLOCK1_ZONE2_ASHRAE_55_Running_mean_outdoor_temperature,
#     df_temp.Building_Total_Zone_Thermostat_Operative_Temperature_mean,
#     c='g',
#     s=1,
#     marker='o'
# )
#
# ax2 = ax.twinx()
# ax2.scatter(
#     df_temp.BLOCK1_ZONE2_ASHRAE_55_Running_mean_outdoor_temperature,
#     df_temp.Building_Total_Cooling_Energy_Demand_summed,
#     s=1,
#     marker='o'
# )
# ax2.scatter(
#     df_temp.BLOCK1_ZONE2_ASHRAE_55_Running_mean_outdoor_temperature,
#     df_temp.Building_Total_Heating_Energy_Demand_summed,
#     s=1,
#     marker='o'
# )
# plt.show()

end = time.time()
print(end-start)