from accim.data.datawrangling import Table
# import os
# os.listdir()

dataset_hourly = Table(
    frequency='hourly',
    frequency_sum_or_mean='sum',
    standard_outputs=True,
    level=['building'],
    level_sum_or_mean=['mean'],
    split_epw_names=True,
    # normalised_energy_units=False
)

dataset_hourly.df