from accim.data.datawrangling import Table
from pandas.api.types import CategoricalDtype
import pandas as pd

z = Table(
    source_concatenated_csv_filepath='Japan_graphs[freq-runperiod[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_sum_or_mean=['sum', 'mean'],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)

# print(*z.df.columns, sep='\n')

z.format_table(
    type_of_table='custom',
    custom_cols=[i for i in z.df.columns if
                 'Building_Total' in i
                 and '(summed)' in i
                 and 'Energy Demand' in i
                 ],
    split_epw_names=True
)

cities_order = CategoricalDtype(
    ['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha'],
    ordered=True
)

z.df['EPW_City_or_subcountry'] = z.df['EPW_City_or_subcountry'].astype(cities_order)
z.df['EPW_City_or_subcountry']
z.df = z.df.sort_values(['EPW_City_or_subcountry', 'Adaptive Standard', 'Category', 'Comfort mode'])


df_backup = z.df.copy()

# cities_order = ['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha']

##

# Testing reshaping

z.wrangled_table(reshaping='unstack',
                 vars_to_gather=[
                     'Adaptive Standard',
                     'Comfort mode'
                    ],
                 baseline='x',
                 comparison_cols=['relative', 'absolute']
                 )

##
