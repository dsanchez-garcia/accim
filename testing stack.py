from accim.data.data_postprocessing import Table
dataset_hourly = Table(
    source_frequency='hourly',
    frequency='hourly',
    frequency_agg_func='sum',
    standard_outputs=True,
    level=['building'],
    level_agg_func=['mean', 'sum'],
    level_excluded_zones=['ATTIC:ATTIC'],
    split_epw_names=True,
)

dataset_hourly.format_table(
    type_of_table='custom',
    custom_cols=[
        # 'BLOCK1:PERIMETERXZNX4_ASHRAE 55 Running mean outdoor temperature (°C)',
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
        # 'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        # 'Building_Total_Zone Operative Temperature (°C) (mean)'
    ]
)

dataset_hourly.wrangled_table(
    reshaping='multiindex'
)

dataset_hourly.wrangled_df_multiindex

##

dataset_hourly.wrangled_df_multiindex.to_excel('testing multiindex.xlsx')

##
dataset_hourly.wrangled_df_stacked.to_excel('testing stack 3.xlsx')

