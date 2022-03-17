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
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    )

# print(*z.df.columns, sep='\n')

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



##

# figsize = 8
# ratio_height_to_width = 1/3
# fig, ax = plt.subplots(nrows=len(z.rows),
#                        ncols=len(z.cols),
#                        sharex=True,
#                        sharey=True,
#                        constrained_layout=False,
#                        # constrained_layout=True,
#                        figsize=(figsize * len(z.cols), ratio_height_to_width * figsize * len(z.rows)))
#
# main_y_axis = []
# sec_y_axis = []
#
# for i in range(len(z.rows)):
#     main_y_axis_temp_rows = []
#     sec_y_axis_temp_rows = []
#     for j in range(len(z.cols)):
#
#         main_y_axis_temp_cols = []
#         sec_y_axis_temp_cols = []
#
#         if len(z.rows) == 1 and len(z.cols) == 1:
#             for k in range(len(z.data_on_y_main_axis)):
#                 main_y_axis_temp_cols.append(ax)
#             main_y_axis_temp_rows.append(main_y_axis_temp_cols)
#             if len(z.data_on_y_sec_axis) > 0:
#                 for k in range(len(z.data_on_y_sec_axis)):
#                     sec_y_axis_temp_cols.append(ax.twinx())
#                 sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
#         elif len(z.cols) == 1 and len(z.rows) > 1:
#             for k in range(len(z.data_on_y_main_axis)):
#                 main_y_axis_temp_cols.append(ax[i])
#             main_y_axis_temp_rows.append(main_y_axis_temp_cols)
#             if len(z.data_on_y_sec_axis) > 0:
#                 for k in range(len(z.data_on_y_sec_axis)):
#                     sec_y_axis_temp_cols.append(ax[i].twinx())
#                 sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
#         else:
#             for k in range(len(z.data_on_y_main_axis)):
#                 main_y_axis_temp_cols.append(ax[i, j])
#             main_y_axis_temp_rows.append(main_y_axis_temp_cols)
#             if len(z.data_on_y_sec_axis) > 0:
#                 for k in range(len(z.data_on_y_sec_axis)):
#                     sec_y_axis_temp_cols.append(ax[i, j].twinx())
#                 sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
#     main_y_axis.append(main_y_axis_temp_rows)
#     sec_y_axis.append(sec_y_axis_temp_rows)
#
# # for i in range(len(z.rows)):
# #     for j in range(len(z.cols)):
# #         for k in range(len(z.y_list_sec[i][j])):
# #             # if i > 0 and j > 0:
# #             # if i > 0:
# #                 # sec_y_axis[0][0][k].sharey(sec_y_axis[i][j][k])
# #                 # sec_y_axis[0][0][k].sharex(sec_y_axis[i][j][k])
# #             sec_y_axis[0][0][k].get_shared_y_axes().join(sec_y_axis[0][0][k], sec_y_axis[i][j][k])
# #             # sec_y_axis[0][0][k].get_shared_x_axes().join(sec_y_axis[0][0][k], sec_y_axis[i][j][k])
#
# for i in range(len(z.rows)):
#     for j in range(len(z.cols)):
#         for k in range(len(z.y_list_main[i][j])):
#             main_y_axis[i][j][k].grid(True, linestyle='-.')
#             main_y_axis[i][j][k].tick_params(axis='both',
#                                              grid_color='black',
#                                              grid_alpha=0.5)
#             main_y_axis[i][j][k].set_facecolor((0, 0, 0, 0.10))
#
#             for x in range(len(z.y_list_main[i][j][k]['dataframe'])):
#                 if i == 0 and j == 0:
#                     main_y_axis[i][j][k].scatter(
#                         z.x_list[i][j][2],
#                         z.y_list_main[i][j][k]['dataframe'][x],
#                         c=z.y_list_main[i][j][k]['color'][x],
#                         s=1,
#                         marker='o',
#                         alpha=0.5,
#                         label=z.y_list_main[i][j][k]['label'][x],
#                     )
#                 else:
#                     main_y_axis[i][j][k].scatter(
#                         z.x_list[i][j][2],
#                         z.y_list_main[i][j][k]['dataframe'][x],
#                         c=z.y_list_main[i][j][k]['color'][x],
#                         s=1,
#                         marker='o',
#                         alpha=0.5,
#                     )
#
# for i in range(len(z.rows)):
#     for j in range(len(z.cols)):
#         for k in range(len(z.y_list_sec[i][j])):
#             # if i > 0 and j > 0:
#             sec_y_axis[0][0][k].get_shared_y_axes().join(sec_y_axis[0][0][k], sec_y_axis[i][j][k])
#                 # sec_y_axis[0][0][k].sharey(sec_y_axis[i][j][k])
#             if len(z.data_on_y_sec_axis) > 1:
#                 if len(z.y_list_sec[i][j]) >= 1:
#                     if j < (len(z.cols)-1):
#                         # sec_y_axis[i][j][k].set_yticklabels([])
#                         sec_y_axis[i][j][k].set_yticks([], [])
#                     if j == (len(z.cols)-1):
#                         sec_y_axis[i][j][k].set_ylabel(z.data_on_y_sec_axis[k][0])
#                         sec_y_axis[i][j][k].spines["right"].set_position(("axes", 1 + k * 0.1))
#                         sec_y_axis[i][j][k].spines["right"].set_visible(True)
#             for x in range(len(z.y_list_sec[i][j][k]['dataframe'])):
#                 if i == 0 and j == 0:
#                     sec_y_axis[i][j][k].scatter(
#                         z.x_list[i][j][2],
#                         z.y_list_sec[i][j][k]['dataframe'][x],
#                         c=z.y_list_sec[i][j][k]['color'][x],
#                         s=1,
#                         marker='o',
#                         alpha=0.5,
#                         label=z.y_list_sec[i][j][k]['label'][x],
#                     )
#                 else:
#                     sec_y_axis[i][j][k].scatter(
#                         z.x_list[i][j][2],
#                         z.y_list_sec[i][j][k]['dataframe'][x],
#                         c=z.y_list_sec[i][j][k]['color'][x],
#                         s=1,
#                         marker='o',
#                         alpha=0.5,
#                     )
#
# if len(z.rows) == 1:
#     if len(z.cols) == 1:
#         for i in range(len(z.rows)):
#             ax.set_ylabel(z.rows[i], rotation=90, size='large')
#         for j in range(len(z.cols)):
#             ax.set_title(z.cols[j])
#
# if len(z.rows) > 1:
#     if len(z.cols) == 1:
#         for i in range(len(z.rows)):
#             ax[i].set_ylabel(z.rows[i], rotation=90, size='large')
#         for j in range(len(z.cols)):
#             ax[0].set_title(z.cols[j])
#     else:
#         for i in range(len(z.rows)):
#             ax[i, 0].set_ylabel(z.rows[i], rotation=90, size='large')
#         for j in range(len(z.cols)):
#             ax[0, j].set_title(z.cols[j])
#
# supx = fig.supxlabel('whatever')
# supy = fig.supylabel(z.data_on_y_main_axis[0][0])
#
# leg = fig.legend(
#     bbox_to_anchor=(0.5, 0),
#     loc='upper center',
#     fontsize='large'
#     # borderaxespad=0.1,
# )
# if len(z.data_on_y_sec_axis) == 1:
#     rhstext = fig.text(1, 0.5, s=z.data_on_y_sec_axis[0][0], va='center', rotation='vertical', size='large')
#
# if len(z.data_on_y_sec_axis) == 1:
#     bbox_extra_artists_tuple = (rhstext, leg, supx, supy)
# else:
#     bbox_extra_artists_tuple = (leg, supx, supy)
#
# for i in range(len(leg.legendHandles)):
#     leg.legendHandles[i]._sizes = [30]
#
# # plt.subplots_adjust(bottom=0.2)
# plt.tight_layout()
#
#
# plt.savefig(
#     f'whatever_tight_{figsize}' + '.png',
#     # f'whatever_constrained_{figsize}' + '.png',
#     dpi=300,
#     format='png',
#     bbox_extra_artists=bbox_extra_artists_tuple,
#     bbox_inches='tight')
#
# plt.show()
#
#
# # for i in range(len(z.rows)):
# #     for j in range(len(z.cols)):
# #         for k in range(len(z.y_list_sec[i][j])):
# #             if i > 0 and j > 0:
# #                 # sec_y_axis[0][0][k].sharey(sec_y_axis[i][j][k])
# #                 # sec_y_axis[0][0][k].sharex(sec_y_axis[i][j][k])
# #                 sec_y_axis[0][0][k].get_shared_y_axes().join(sec_y_axis[0][0][k], sec_y_axis[i][j][k])
# #                 sec_y_axis[0][0][k].get_shared_x_axes().join(sec_y_axis[0][0][k], sec_y_axis[i][j][k])


# print(*z.x_list, sep='\n')
# z.rows
# z.df_for_graph.columns
# z.df_for_graph.index

##

z.scatter_plot_adap_vs_stat(
    supxlabel='Static Energy Demand',
    supylabel='Adaptive Energy Demand',
    figname='test_scatter_plot_adap_vs_stat_01_transposed',
    figsize=5,
    confirm_graph=True
)






##
z.scatter_plot(
    supxlabel='Outdoor temperature',
    figname='test_scatter_plot_07_09_shared',
    figsize=7,
    ratio_height_to_width=0.75,
    confirm_graph=True
)



##

z.time_plot(
    supxlabel='Year',
    figname='test_scatter_plot_07_timeplot_07_shared',
    figsize=14,
    ratio_height_to_width=1/3,
    confirm_graph=True
)
end = time.time()
print(end-start)
