from accim.data.datawrangling import Table
z = Table(
    frequency='monthly',
    sum_or_mean='sum',
    standard_outputs=True,
    level='building',
    level_sum_or_mean='sum',
    split_epw_names=True,
    normalised_energy_units=True,
)
