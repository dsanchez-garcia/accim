##

from accim.data.datawrangling import Table
import matplotlib.pyplot as plt
import time
start = time.time()

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

# print(f'The number of columns and the list of these is going to be:')
# print(f'No. of columns = {len(list(set(z.df.Source)))}')
# print(f'List of columns:')
# print(*list(set(z.df.Source)), sep='\n')
#
# print(f'The number of rows and the list of these is going to be:')
# print(f'No. of rows = {len(list(set(z.df.Source)))}')

print(*z.df.columns, sep='\n')

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
    'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]

custom_cols_list = temp_list + additional_list

z.format_table(type_of_graph='custom',
               custom_cols=custom_cols_list,
               manage_epw_names=False
               )

# print(*z.df.columns, sep='\n')

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

# making lists for figure
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
                ]['BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)']
            ]
        temp_row.append(temp)
    x_list.append(temp_row)


y_data_main_scatter = [
    'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)'
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

data_dict = {
    'op temp vs rmot': {
        'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]': 'g',
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)': 'b',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)': 'r',
        'Building_Total_Cooling Energy Demand (kWh/m2) [summed]': 'c',
        'Building_Total_Heating Energy Demand (kWh/m2) [summed]': 'm',
    },
    'outdoor temp vs energy demand': {
        'Building_Total_Cooling Energy Demand (kWh/m2) [summed]': 'b',
        'Building_Total_Heating Energy Demand (kWh/m2) [summed]': 'r',
    },
}


##
s=4
type_of_graph = 'op temp vs rmot'

fig, ax = plt.subplots(nrows=len(rows),
                       ncols=len(cols),
                       sharex=True,
                       sharey=True,
                       constrained_layout=True,
                       figsize=(s*len(cols), s*len(rows)))

# y_list_main_scatter
for i in range(len(rows)):
    for j in range(len(cols)):
        ax[i, j].set_title(f'{rows[i]} / {cols[j]}')
        ax[i, j].grid(True, linestyle='-.')
        ax[i, j].tick_params(axis='both',
                             grid_color='black',
                             grid_alpha=0.5)
        ax[i, j].set_facecolor((0, 0, 0, 0.10))
        for k in range(len(y_list_main_scatter[i][j][3])):
            for x in data_dict:
                if x in type_of_graph:
                    for y in data_dict[x]:
                        if y in y_list_main_scatter[i][j][2][k]:
                            if i == 0 and j == 0:
                                ax[i, j].scatter(
                                    x_list[i][j][2],
                                    y_list_main_scatter[i][j][3][k],
                                    c=data_dict[x][y],
                                    s=1,
                                    marker='o',
                                    alpha=0.5,
                                    label=y_list_main_scatter[i][j][2][k]
                                )
                            else:
                                ax[i, j].scatter(
                                    x_list[i][j][2],
                                    y_list_main_scatter[i][j][3][k],
                                    c=data_dict[x][y],
                                    s=1,
                                    marker='o',
                                    alpha=0.5,
                                )
        for k in range(len(y_list_sec[i][j][3])):
            for x in data_dict:
                if x in type_of_graph:
                    for y in data_dict[x]:
                        if y in y_list_sec[i][j][2][k]:
                            if i == 0 and j == 0:
                                ax[i, j].twinx().scatter(
                                    x_list[i][j][2],
                                    y_list_sec[i][j][3][k],
                                    c=data_dict[x][y],
                                    s=1,
                                    marker='o',
                                    alpha=0.5,
                                    label=y_list_sec[i][j][2][k]
                                )
                            else:
                                ax[i, j].twinx().scatter(
                                    x_list[i][j][2],
                                    y_list_sec[i][j][3][k],
                                    c=data_dict[x][y],
                                    s=1,
                                    marker='o',
                                    alpha=0.5,
                                )

# for k in range(len(y_list_main_scatter[0][0][3])):
#     ax[0, 0].scatter(label=y_list_main_scatter[0][0][2][k])
# for k in range(len(y_list_sec[0][0][3])):
#     ax[0, 0].twinx().scatter(label=y_list_sec[0][0][2][k])

# for k in range(len(y_list_main_plot[0][0][3])):
#     ax[0, 0].scatter(label=y_list_main_plot[0][0][2][k])


for i in range(len(rows)):
    ax[i, 0].set_ylabel(rows[i], rotation=90, size='large')

for j in range(len(cols)):
    ax[0, j].set_title(cols[j])

fig.supxlabel('Running mean outdoor temperature (°C)')
fig.supylabel('Operative temperature (°C)')

# fig_legend = ax[0,0].legend(loc='center right')
leg = fig.legend(
    bbox_to_anchor=(0.5, 0),
    loc='upper center',
    fontsize='large'
    # borderaxespad=0.1,
)

for i in range(len(leg.legendHandles)):
    leg.legendHandles[i]._sizes = [30]

# plt.subplots_adjust(bottom=0.2)
# plt.tight_layout()

plt.savefig('temp_fig_10.jpg',
            dpi=300,
            format='jpg',
            bbox_extra_artists=(leg,),
            bbox_inches='tight')


# legend1 = ax[0,0].legend(*scatter.legend_elements(),
#                     loc="lower left", title="Classes")
# fig.add_artist(legend1)

# y_list_main_plot
# for i in range(len(rows)):
#     for j in range(len(cols)):
#         ax[i, j].set_title(f'{rows[i]}_{cols[j]}')
#         for k in range(len(y_list_main_plot[i][j][3])):
#             if 'Cooling' in y_list_main_plot[i][j][2][k]:
#                 ax[i, j].plot(
#                     x_list[i][j][2],
#                     y_list_main_plot[i][j][3][k],
#                     c='b',
#                     ms=1,
#                     marker='o'
#                 )
#             if 'Heating' in y_list_main_plot[i][j][2][k]:
#                 ax[i, j].plot(
#                     x_list[i][j][2],
#                     y_list_main_plot[i][j][3][k],
#                     c='r',
#                     ms=1,
#                     marker='o'
#                 )

plt.show()

##
# todo testing
# y_list_main_plot[0][1][3][0]
# temp_df = z.df[
#     (z.df['col_to_gather_in_cols'] == 'AS_EN16798[CA_1') &
#     (z.df['col_to_gather_in_rows'] == 'London_Present')
#     ]
# temp_df.to_excel('temp_testing.xlsx')


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







# seaborn

# df2 = z.df.drop([
#     'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
#     'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
#     'col_to_gather_in_cols', 'col_to_gather_in_rows'
# ],
#     axis=1)
# df2.set_index([
# 'Model', 'Adaptive Standard', 'Category', 'Comfort mode', 'HVAC mode',
#        'Ventilation control', 'VSToffset', 'MinOToffset', 'MaxWindSpeed',
#        'ASTtol', 'EPW', 'Source', 'Hour',
#        # 'col_to_gather_in_cols', 'col_to_gather_in_rows'
# ], inplace=True)
#
# df2 = df2.stack()
#
# df2['col_to_gather_in_rows'] = z.df['col_to_gather_in_rows']
# df2['col_to_gather_in_cols'] = z.df['col_to_gather_in_cols']
#
# import seaborn as sns
# g = sns.FacetGrid(z.df2, row='col_to_gather_in_rows', col='col_to_gather_in_cols')
# g.map(sns.scatterplot, 'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)', 'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]')
#
#
#

end = time.time()
print(end-start)