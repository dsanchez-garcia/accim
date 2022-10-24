

from accim.data.datawrangling import Table
dataset_hourly = Table(
    #datasets=list Since we are not specifying any list, it will use all available CSVs in the folder
    frequency='hourly',
    frequency_sum_or_mean='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    # level=['building'],

    #match_cities=bool Only used when EPW file has NOT been previously renamed
    #manage_epw_names=bool Only used when EPW file has NOT been previously renamed
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
    concatenated_csv_name='notebook_example' #Useful when working with large datasets. It saves the output dataset to a CSV file, so you don't need to re-do some work. Afterwards, it can be imported with source_concatenated_csv_filepath argument.
)

dataset_hourly = Table(
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
    # frequency='hourly',
    # frequency_sum_or_mean='sum',
    level=['building'],
    level_sum_or_mean=['sum', 'mean'],
    source_concatenated_csv_filepath='notebook_example[freq-hourly[frequency_sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv'
)

print(*dataset_hourly.df.columns, sep='\n')

dataset_hourly.format_table(
    type_of_table='custom',
    custom_cols=[
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'Building_Total_Zone Operative Temperature (°C) (mean)',
        'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
        'Building_Total_AFN Zone Infiltration Air Change Rate (ach) (summed)'
    ]
)

## Wrangled table
from accim.data.datawrangling import Table
dataset_monthly = Table(
    #datasets=list Since we are not specifying any list, it will use all available CSVs in the folder
    frequency='monthly',
    frequency_sum_or_mean='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_sum_or_mean=['sum'],
    #match_cities=bool Only used when EPW file has NOT been previously renamed
    #manage_epw_names=bool Only used when EPW file has NOT been previously renamed
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
)

dataset_monthly.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ]
)

dataset_monthly.wrangled_table(
    reshaping='unstack',
    vars_to_gather=['ComfMod', 'Category'],
    baseline='CM_0[CA_1',
    comparison_mode='baseline compared to others',
    comparison_cols=['relative', 'absolute']
)

# dataset_hourly.wrangled_table(
#     reshaping='unstack',
#     vars_to_gather=[
#         'EPW_Scenario',
#         'EPW_Year'
#     ],
#     baseline='Present[Present',
#     comparison_mode='baseline compared to others',
#     comparison_cols=[
#         'relative',
#         'absolute'
#     ],
#     # check_index_and_cols=True,
#     vars_to_keep=[
#         'EPW_City_or_subcountry',
#         'AdapStand',
#         'ComfMod',
#         'HVACmode'
#     ]
# )
##

dataset_runperiod = Table(
    #datasets=list Since we are not specifying any list, it will use all available CSVs in the folder
    frequency='runperiod',
    frequency_sum_or_mean='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_sum_or_mean=['sum'],
    #match_cities=bool Only used when EPW file has NOT been previously renamed
    #manage_epw_names=bool Only used when EPW file has NOT been previously renamed
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
)

dataset_runperiod.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ]
)

dataset_runperiod.wrangled_table(
    reshaping='pivot',
    vars_to_gather=['ComfMod', 'Category'],
    baseline='CM_0[CA_1',
    comparison_mode='baseline compared to others',
    comparison_cols=['relative', 'absolute']
)

dataset_runperiod.wrangled_df_pivoted

##
import os
from accim.data.datawrangling import Table

dataset = [i for i in os.listdir() if i.endswith('.csv') and 'CA_3' in i]
dataset_runperiod_simplified_1 = Table(
    datasets=dataset,
    frequency='runperiod',
    frequency_sum_or_mean='sum',
    # this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_sum_or_mean=['sum'],
    # match_cities=bool Only used when EPW file has NOT been previously renamed
    # manage_epw_names=bool Only used when EPW file has NOT been previously renamed
    split_epw_names=True,  # to split EPW names based on the format Country_City_RCPscenario-YEar
)

dataset_runperiod_simplified_1.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ]
)

dataset_runperiod_simplified_1.wrangled_table(
    reshaping='pivot',
    vars_to_gather=['ComfMod'],
    baseline='CM_0',
    comparison_mode='baseline compared to others',
    comparison_cols=['relative', 'absolute']
)



## Figures

dataset_hourly.generate_fig_data(
    vars_to_gather_rows=['ComfMod', 'Category'],
    vars_to_gather_cols=['EPW_City_or_subcountry'],

    detailed_rows=['CM_0[CA_3', 'CM_3[CA_3'],

    data_on_x_axis='BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    data_on_y_main_axis=[
        [
            'Indoor Operative Temperature (°C)',
            [
                'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
                'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
                'Building_Total_Zone Operative Temperature (°C) (mean)',
            ]
        ],
    ],
    data_on_y_sec_axis=[
        [
            'Energy (kWh/m2)',
            [
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
            ]
        ],
        [
            'Air renovation (ach)',
            [
                'Building_Total_AFN Zone Infiltration Air Change Rate (ach) (summed)'
            ]
        ]
    ],
    colorlist_y_main_axis=[
        [
            'Indoor Operative Temperature (°C)',
            [
                'b',
                'r',
                'g',
            ]
        ],
    ],
    colorlist_y_sec_axis=[
        [
            'Energy (kWh/m2)',
            [
                'cyan',
                'orange',
            ]
        ],
        [
            'Air renovation (ach)',
            [
                'yellow'
            ]
        ]
    ]
)

dataset_hourly.scatter_plot(
    supxlabel='Running Mean Outdoor Temperature (°C)',
    figname=f'WIP_scatterplot_PMOT_3',
    figsize=6,
    ratio_height_to_width=0.33,
    confirm_graph=True
)

##

dataset_hourly.generate_fig_data(
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    vars_to_gather_cols=['ComfMod', 'Category'],
    adap_vs_stat_data_y_main=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ],
    baseline='CM_0[CA_1',
    colorlist_adap_vs_stat_data=[
        'b',
        'r',
    ]
)

dataset_hourly.scatter_plot_adap_vs_stat(
    supxlabel='Static (CM_0) Energy Demand (kWh/m2)',
    supylabel='Adaptive (CM_3) Energy Demand (kWh/m2)',
    figname='WIP_scatterplot_adap_vs_stat',
    figsize=3,
    confirm_graph=True
)