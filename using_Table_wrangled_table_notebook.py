from accim.data.data_postprocessing import Table
dataset_monthly = Table(
    #datasets=list Since we are not specifying any list, it will use all available CSVs in the folder
    source_frequency='hourly',
    frequency='runperiod',
    frequency_agg_func='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    level_excluded_zones=[],
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
)

dataset_monthly.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ]
)

dataset_monthly.gather_vars_query(
    vars_to_gather=[
        'ComfMod',
        'CAT'
    ]
)

dataset_monthly.wrangled_table(
    reshaping='unstack', #can be 'unstack' or 'pivot'
    vars_to_gather=['ComfMod', 'CAT'],
    vars_to_keep=['EPW_City_or_subcountry'],
    baseline='CM_0[CA_1',
    comparison_mode=['baseline compared to others'], #can be 'baseline compared to others' or 'others compared to baseline'
    comparison_cols=['relative', 'absolute'] #'relative' to show the difference as a percentage, 'absolute' to show the difference by subtracting
)
