from accim.data.datawrangling import Table
dataset_hourly = Table(

    # source_frequency='hourly',
    # frequency='hourly',
    # frequency_agg_func='sum',
    # standard_outputs=True,
    # concatenated_csv_name='testing_accim_hourly_dataset',
    # drop_nan=True,

    source_concatenated_csv_filepath='testing_accim_hourly_dataset[srcfreq-hourly[freq-hourly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['mean', 'sum'],
    level_excluded_zones=[],
    split_epw_names=True,
)


# dataset_runperiod.df.to_excel('using_Table_00.xlsx')
# dataset_runperiod.df.shape
# dataset_runperiod.df.columns
# print(*dataset_hourly.df_backup.columns, sep='\n')

dataset_hourly.format_table(
    type_of_table='temperature',
    # custom_cols=[
    #     'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
    #     'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    #     'Site Outdoor Air Drybulb Temperature (°C)'
    # ]
)
# dataset_hourly.gather_vars_query(
#     vars_to_gather=[
#         'ComfStand',
#         'ComfMod',
#         'HVACmode'
#     ]
# )
#
# dataset_hourly.gather_vars_query(
#     vars_to_gather=[
#         'EPW_City_or_subcountry',
#         'EPW_Scenario-Year',
#     ]
# )



dataset_hourly.df.columns
## scatter_plot


dataset_hourly.time_plot(
    vars_to_gather_cols=['ComfStand', 'ComfMod', 'HVACmode'],
    vars_to_gather_rows=['EPW_City_or_subcountry', 'EPW_Scenario-Year'],
    # data_on_x_axis='BLOCK1:ZONE2_ASHRAE 55 Running mean outdoor temperature (°C)',
    data_on_y_main_axis=[
        [
            'Temperature (°C)',
            [
                'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
                'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
                'Building_Total_Zone Operative Temperature (°C) (mean)'
            ]
        ],
    ],
    # data_on_y_sec_axis=[
    #     [
    #         'Energy Demand (kWh/m2)',
    #         [
    #             'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
    #             'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    #         ]
    #     ],
    # ],

    colorlist_y_main_axis=[
        [
            'Temperature (°C)',
            [
                'b',
                'r',
                'g'
            ]
        ],
    ],
    # colorlist_y_sec_axis=[
    #     [
    #         'Energy Demand (kWh/m2)',
    #         [
    #             'c',
    #             'orange',
    #         ]
    #     ],
    # ],
    # rows_renaming_dict={
    #     'Ahmedabad[Present': 'Ahmedabad Present',
    #     'Ahmedabad[RCP85-2100': 'Ahmedabad RCP85-2100',
    #     'Shimla[Present': 'Shimla Present',
    #     'Shimla[RCP85-2100': 'Shimla RCP85-2100'
    #
    # },
    # cols_renaming_dict={
    #     'CM_0': 'static',
    #     'CM_3': 'adaptive'
    # },

    supxlabel='Running mean outdoor temperature (°C)',
    figname='testing_time_case_study_00',
    figsize=4,
    ratio_height_to_width=0.3
)

dataset_hourly.df_for_graph.columns

## time_plot



# todo check using csvs from other energyplus versions
# todo check if it works with csvs with different zones

# dataset_hourly.time_plot(
#     vars_to_gather_cols=['ComfMod'],
#     vars_to_gather_rows=['EPW_City_or_subcountry'],
#     data_on_y_main_axis=[
#         [
#             'Cooling Energy Demand (kWh/m2)',
#             [
#                 'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
#                 # 'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
#             ]
#         ],
#     ],
#     data_on_y_sec_axis=[
#         [
#             'Heating Energy Demand (kWh/m2)',
#             [
#                 'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
#                 # 'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
#             ]
#         ],
#     ],
#     colorlist_y_main_axis=[
#         [
#             'Cooling Energy Demand (kWh/m2)',
#             [
#                 'b',
#             ]
#         ],
#     ],
#     colorlist_y_sec_axis=[
#         [
#             'Heating Energy Demand (kWh/m2)',
#             [
#                 'r',
#             ]
#         ]
#     ],
#     rows_renaming_dict={
#         'Aberdeen': 'a',
#         'London': 'l'
#     },
#     cols_renaming_dict={
#         'CM_0': 'static',
#         'CM_3': 'adaptive'
#     },
#
#     figname='testing_timeplot',
#     figsize=8,
#     ratio_height_to_width=0.3,
#     confirm_graph=True
# )

##
# adaptive vs stat

# dataset_hourly.scatter_plot_adap_vs_stat(
#     vars_to_gather_cols=['ComfMod'],
#     vars_to_gather_rows=['EPW_City_or_subcountry'],
#     adap_vs_stat_data_y_main=[
#                 'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
#                 'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
#     ],
#
#     colorlist_adap_vs_stat_data=[
#                 'b',
#                 'r'
#     ],
#     baseline='CM_0',
#
#     rows_renaming_dict={
#         'Aberdeen': 'a',
#         'London': 'l'
#     },
#     cols_renaming_dict={
#         # 'CM_0': 'static',
#         'CM_3': 'adaptive'
#     },
#
#     supxlabel='Outdoor temperature',
#     figname='testing_scatter',
#     figsize=3,
#
# )
