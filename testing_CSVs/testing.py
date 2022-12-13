from accim.data.datawrangling import genCSVconcatenated, Table
import os
x = genCSVconcatenated(
    frequency='runperiod',
    datasets_per_chunk=2,
    concatenated_csv_name='testing'
)

x = Table(
    source_concatenated_csv_filepath='testing[freq-runperiod[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_sum_or_mean=['sum'],
    match_cities=False,
    manage_epw_names=True,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    drop_nan=True
)

##
from accim.data.datawrangling import genCSVconcatenated, Table
x = Table(
    frequency='runperiod',
    frequency_sum_or_mean='sum',
    level=['building'],
    level_sum_or_mean=['sum'],
    match_cities=False,
    manage_epw_names=True,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    drop_nan=True
)

os.listdir('testing_CSVs')