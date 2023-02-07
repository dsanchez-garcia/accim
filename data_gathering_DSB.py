from accim.data.datawrangling import Table
import pandas as pd

# z = Table(
#     source_frequency='hourly',
#     frequency='monthly',
#     frequency_sum_or_mean='sum',
#     concatenated_csv_name='testing_data_gathering_DSB'
# )

##

z = Table(
    source_concatenated_csv_filepath='testing_data_gathering_DSB[freq-monthly[frequency_sum_or_mean-sum[standard_outputs-None[CSVconcatenated.csv',
    # source_frequency='hourly',
    # frequency='monthly',
    # frequency_sum_or_mean='sum',
    level=['block', 'building'],
    level_sum_or_mean=['mean'],
    # block_zone_hierarchy=block_zone_dict,
    level_excluded_zones=[],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)

print(*z.df.columns, sep='\n')

z.df.to_excel('test_DSB.xlsx')