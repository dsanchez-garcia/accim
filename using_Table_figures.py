from accim.data.data_postprocessing import Table
dataset_hourly = Table(
    #datasets=list Since we are not specifying any list, it will use all available CSVs in the folder
    source_frequency='hourly',
    frequency='hourly',
    frequency_agg_func='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    level_excluded_zones=[],
    #match_cities=bool Only used when EPW file has NOT been previously renamed
    #manage_epw_names=bool Only used when EPW file has NOT been previously renamed
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
)


# dataset_runperiod.df.to_excel('using_Table_00.xlsx')
# dataset_runperiod.df.shape
# dataset_runperiod.df.columns
# print(*dataset_hourly.df_backup.columns, sep='\n')

dataset_hourly.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
        'Site Outdoor Air Drybulb Temperature (°C)'
    ]
)
dataset_hourly.cols_for_multiindex
dataset_hourly.gather_vars_query(['ComfMod'])
## scatter_plot

dataset_hourly.generate_fig_data(
    vars_to_gather_cols=['ComfMod'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    data_on_y_main_axis=[
        [
            'Energy Demand (kWh/m2)',
            [
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
            ]
        ],
    ],
    # data_on_y_sec_axis=[
    #         'Temperature',
    #         [
    #             'Site Outdoor Air Drybulb Temperature (°C)'
    #         ]
    #     ],
    data_on_x_axis='Site Outdoor Air Drybulb Temperature (°C)',

    colorlist_y_main_axis=[
        [
            'Energy Demand (kWh/m2)',
            [
                'b',
                'r'
            ]
        ],
    ],
    # colorlist_y_sec_axis=[
    #     'Heating Energy Demand (kWh/m2)',
    #     [
    #         'r',
    #     ]
    # ],

)

##

dataset_hourly.scatter_plot(
    vars_to_gather_cols=['ComfMod'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    data_on_y_main_axis=[
        [
            'Energy Demand (kWh/m2)',
            [
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
            ]
        ],
    ],
    # data_on_y_sec_axis=[
    #         'Temperature',
    #         [
    #             'Site Outdoor Air Drybulb Temperature (°C)'
    #         ]
    #     ],
    data_on_x_axis='Site Outdoor Air Drybulb Temperature (°C)',

    colorlist_y_main_axis=[
        [
            'Energy Demand (kWh/m2)',
            [
                'b',
                'r'
            ]
        ],
    ],
    # colorlist_y_sec_axis=[
    #     'Heating Energy Demand (kWh/m2)',
    #     [
    #         'r',
    #     ]
    # ],
    rows_renaming_dict={
        'Aberdeen': 'a',
        'London': 'l'
    },
    cols_renaming_dict={
        'CM_0': 'static',
        'CM_3': 'adaptive'
    },

    supxlabel='Outdoor temperature',
    figname='testing_scatter',
    figsize=3,

)

## time_plot



# todo check using csvs from other energyplus versions
# todo check if it works with csvs with different zones

dataset_hourly.time_plot(
    vars_to_gather_cols=['ComfMod'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    data_on_y_main_axis=[
        [
            'Cooling Energy Demand (kWh/m2)',
            [
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                # 'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
            ]
        ],
    ],
    data_on_y_sec_axis=[
        [
            'Heating Energy Demand (kWh/m2)',
            [
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
                # 'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
            ]
        ],
    ],
    colorlist_y_main_axis=[
        [
            'Cooling Energy Demand (kWh/m2)',
            [
                'b',
            ]
        ],
    ],
    colorlist_y_sec_axis=[
        [
            'Heating Energy Demand (kWh/m2)',
            [
                'r',
            ]
        ]
    ],
    rows_renaming_dict={
        'Aberdeen': 'a',
        'London': 'l'
    },
    cols_renaming_dict={
        'CM_0': 'static',
        'CM_3': 'adaptive'
    },

    figname='testing_timeplot',
    figsize=8,
    ratio_height_to_width=0.3,
    confirm_graph=True
)

##
# adaptive vs stat

dataset_hourly.scatter_plot_adap_vs_stat(
    vars_to_gather_cols=['ComfMod'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    adap_vs_stat_data_y_main=[
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ],

    colorlist_adap_vs_stat_data=[
                'b',
                'r'
    ],
    baseline='CM_0',

    rows_renaming_dict={
        'Aberdeen': 'a',
        'London': 'l'
    },
    cols_renaming_dict={
        # 'CM_0': 'static',
        'CM_3': 'adaptive'
    },

    supxlabel='Outdoor temperature',
    figname='testing_scatter',
    figsize=3,

)
