from accim.data.data_postprocessing import Table
dataset_hourly = Table(
    source_frequency='hourly',
    frequency='hourly',
    frequency_agg_func='sum',
    standard_outputs=True,
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



# dataset_hourly.df.columns
## scatter_plot


dataset_hourly.scatter_plot(
    vars_to_gather_rows=['ComfStand', 'ComfMod', 'HVACmode'],
    vars_to_gather_cols=['EPW_City_or_subcountry', 'EPW_Scenario-Year'],
    data_on_x_axis='BLOCK1:ZONE2_ASHRAE 55 Running mean outdoor temperature (°C)',
    data_on_y_main_axis=[
        [
            'Energy Demand (kWh/m2)',
            [
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
            ]
        ],
    ],
    data_on_y_sec_axis=[
        [
            'Temperature (°C)',
            [
                'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
                'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
                'Building_Total_Zone Operative Temperature (°C) (mean)'
            ]
        ],
    ],
    colorlist_y_main_axis=[
        [
            'Energy Demand (kWh/m2)',
            [
                'cyan',
                'orange',
            ]
        ],
    ],
    colorlist_y_sec_axis=[
        [
            'Temperature (°C)',
            [
                'blue',
                'red',
                'green'
            ]
        ],
    ],
    cols_renaming_dict={
        'Ahmedabad[Present': 'Ahmedabad Present',
        'Ahmedabad[RCP85-2100': 'Ahmedabad RCP85-2100',
        'Shimla[Present': 'Shimla Present',
        'Shimla[RCP85-2100': 'Shimla RCP85-2100'

    },
    rows_renaming_dict={
        'CS_IND IMAC C NV[CM_0[HM_0': 'IND_Stat_AC',
        'CS_IND IMAC C NV[CM_3[HM_0': 'IND_Adap_AC',
        'CS_IND IMAC C NV[CM_3[HM_1': 'IND_Adap_NV',
        'CS_IND IMAC C NV[CM_3[HM_2': 'IND_Adap_MM',
        'CS_INT ASHRAE55[CM_3[HM_0': 'ASH_Adap_AC'
    },

    sharex=False,
    sharey=False,
    supxlabel='Running mean outdoor temperature (°C)',
    figname='testing_scatterplot_case_study',
    figsize=4,
    ratio_height_to_width=0.5,
    dpi=300,
    confirm_graph=True
)



## time_plot



# todo check using csvs from other energyplus versions
# todo check if it works with csvs with different zones

dataset_hourly.time_plot(
    vars_to_gather_rows=['ComfStand', 'ComfMod', 'HVACmode'],
    vars_to_gather_cols=['EPW_City_or_subcountry', 'EPW_Scenario-Year'],
    data_on_y_main_axis=[
        [
            'Energy Demand (kWh/m2)',
            [
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
            ]
        ],
    ],
    data_on_y_sec_axis=[
        [
            'Temperature (°C)',
            [
                'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
                'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
                'Building_Total_Zone Operative Temperature (°C) (mean)'
            ]
        ],
    ],
    colorlist_y_main_axis=[
        [
            'Energy Demand (kWh/m2)',
            [
                'cyan',
                'orange',
            ]
        ],
    ],
    colorlist_y_sec_axis=[
        [
            'Temperature (°C)',
            [
                'blue',
                'red',
                'green'
            ]
        ],
    ],
    cols_renaming_dict={
        'Ahmedabad[Present': 'Ahmedabad Present',
        'Ahmedabad[RCP85-2100': 'Ahmedabad RCP85-2100',
        'Shimla[Present': 'Shimla Present',
        'Shimla[RCP85-2100': 'Shimla RCP85-2100'
    },
    rows_renaming_dict={
        'CS_IND IMAC C NV[CM_0[HM_0': 'IND_Stat_AC',
        'CS_IND IMAC C NV[CM_3[HM_0': 'IND_Adap_AC',
        'CS_IND IMAC C NV[CM_3[HM_1': 'IND_Adap_NV',
        'CS_IND IMAC C NV[CM_3[HM_2': 'IND_Adap_MM',
        'CS_INT ASHRAE55[CM_3[HM_0': 'ASH_Adap_AC'
    },
    # sharex=False,
    sharey=False,
    figname='testing_timeplot_case_study_2',
    figsize=4,
    ratio_height_to_width=0.5,
    dpi=300,
    confirm_graph=True
)

##
# adaptive vs stat

dataset_hourly.scatter_plot_with_baseline(
    vars_to_gather_rows=['EPW_City_or_subcountry', 'EPW_Scenario-Year'],
    vars_to_gather_cols=['ComfStand', 'ComfMod', 'HVACmode'],
    detailed_cols=[
        'CS_IND IMAC C NV[CM_0[HM_0',
        'CS_IND IMAC C NV[CM_3[HM_0',
        'CS_INT ASHRAE55[CM_3[HM_0'
    ],
    data_on_y_axis_baseline_plot=[
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ],
    colorlist_baseline_plot_data=[
                'blue',
                'red'
    ],
    baseline='CS_IND IMAC C NV[CM_3[HM_2',
    rows_renaming_dict={
        'Ahmedabad[Present': 'Ahmedabad Present',
        'Ahmedabad[RCP85-2100': 'Ahmedabad RCP85-2100',
        'Shimla[Present': 'Shimla Present',
        'Shimla[RCP85-2100': 'Shimla RCP85-2100'
    },
    cols_renaming_dict={
        'CS_IND IMAC C NV[CM_0[HM_0': 'IND_Stat_AC',
        'CS_IND IMAC C NV[CM_3[HM_0': 'IND_Adap_AC',
        'CS_INT ASHRAE55[CM_3[HM_0': 'ASH_Adap_AC'
    },
    supxlabel='IND_Adap_MM',
    figname='testing_scatter_case_study',
    figsize=3,
    dpi=300
)
