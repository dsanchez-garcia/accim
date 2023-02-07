from accim.data.datawrangling import Table
import pandas as pd

# z = Table(
#     source_frequency='hourly',
#     frequency='monthly',
#     frequency_sum_or_mean='sum',
#     concatenated_csv_name='testing_data_gathering'
# )

##
block_zone_dict = {
    'Block1': ['ATTIC_ZN'],
    'Block2': ['CORE_ZN_ZN', 'PERIMETER_ZN_1_ZN', 'PERIMETER_ZN_2_ZN', 'PERIMETER_ZN_3_ZN', 'PERIMETER_ZN_4_ZN']
}

z = Table(
    source_concatenated_csv_filepath='testing_data_gathering[freq-monthly[frequency_sum_or_mean-sum[standard_outputs-None[CSVconcatenated.csv',
    # source_frequency='hourly',
    # frequency='monthly',
    # frequency_sum_or_mean='sum',
    level=['building'],
    level_sum_or_mean=['mean'],
    block_zone_hierarchy=block_zone_dict,
    level_excluded_zones=[],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)

print(*z.df.columns, sep='\n')

z.df.to_excel('test.xlsx')