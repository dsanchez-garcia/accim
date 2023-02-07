from accim.data.datawrangling import Table
import pandas as pd

z = Table(
    # source_concatenated_csv_filepath='TestModel_section1_test[freq-hourly[frequency_sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    source_frequency='hourly',
    frequency='monthly',
    frequency_sum_or_mean='sum',
    level=['block', 'building'],
    level_sum_or_mean=['mean'],
    level_excluded_zones=[],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)

print(*z.df.columns, sep='\n')

z.df.to_excel('test_DSB_2.xlsx')