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
# Testing

df_testing = df_backup.copy()

vars_to_gather = [
    'Adaptive Standard',
    'Comfort mode',
]



# df_testing['col_to_pivot'] = 'temp'
# z.indexcols.append('col_to_pivot')

# z.enter_vars_to_gather(vars_to_gather)

# z.wrangled_df = df_testing.copy()

# if 'Month' in df_testing.columns:
#     df_testing['col_to_pivot'] = (df_testing[vars_to_gather].agg('['.join, axis=1) + '_' +
#                                         df_testing['Month'].astype(str) +
#                                         '[Month')
# else:
#     df_testing['col_to_pivot'] = df_testing[vars_to_gather].agg('['.join, axis=1)

# df_testing['col_to_pivot'] = df_testing['col_to_pivot']





df_testing = df_testing.set_index([pd.RangeIndex(len(df_testing))])

df_testing = df_testing[
    # (df_testing['EPW_Scenario-Year'].isin(['Present']))
    # &
    (df_testing['HVAC mode'].isin(['HM_0']))
    &
    (df_testing['Category'].isin(['CA_80']))
    &
    (
        (
            (df_testing['Adaptive Standard'].isin(['AS_ASHRAE55']))
            &
            (df_testing['Comfort mode'].isin(['CM_0']))
        )
        |
        (
            (df_testing['Adaptive Standard'].isin(['AS_JPN']))
            &
            (
                (df_testing['Comfort mode'].isin(['CM_0']))
                |
                (df_testing['Comfort mode'].isin(['CM_3']))
            )
        )
    )

    # (
    #     (df_testing['Adaptive Standard'].isin(['AS_ASHRAE55']))
    #     |
    #     (df_testing['Adaptive Standard'].isin(['AS_JPN']))
    # )
    # &
    # (
    #     (df_testing['Comfort mode'].isin(['CM_0']))
    #     |
    #     (df_testing['Comfort mode'].isin(['CM_3']))
    # )

        # (df_testing['Adaptive Standard'].isin(['AS_JPN']))
    # &
    # (
    #     (df_testing['Comfort mode'].isin(['CM_0']))
    #     |
    #     (df_testing['Comfort mode'].isin(['CM_3']))
    # )


    # (
    #     (df_testing['Adaptive Standard'].isin(['AS_JPN'])) &
    #     (df_testing['Comfort mode'].isin(['CM_3']))
    # )
    # |
    # (
    #     (df_testing['Adaptive Standard'].isin(['AS_JPN'])) &
    #     (df_testing['Comfort mode'].isin(['CM_0']))
    # )
    ]


df_testing = df_testing.set_index([pd.RangeIndex(len(df_testing))])

try:
    z.indexcols.remove('EPW')
    z.indexcols.remove('Source')
except ValueError:
    pass

df_testing = df_testing.drop(['EPW', 'Source'], axis=1)

df_testing = df_testing.drop(['EPW_Scenario-Year'], axis=1)
try:
    z.indexcols.remove('EPW_Scenario-Year')
except ValueError:
    pass

cols_to_clean = []
cols_for_multiindex = []
for i in z.indexcols:
    if (df_testing[i][0] == df_testing[i]).all():
        cols_to_clean.append(i)
    else:
        cols_for_multiindex.append(i)

df_testing = df_testing.drop(cols_to_clean, axis=1)

cols_for_values = list(set(df_testing.columns) - set(cols_for_multiindex))

df_testing = df_testing.set_index(cols_for_multiindex)

vars_to_gather = [
    'Adaptive Standard',
    'Comfort mode',
]

df_testing_unstacked = df_testing.unstack(
    vars_to_gather
    # not working
    # 'col_to_pivot'
)
# df_testing.index

df_testing_unstacked.to_excel('temp_unstacked_levels.xlsx')

df_testing_unstacked.columns

baseline = 'AS_ASHRAE55[CM_0'
# baseline = baseline.split('[')


# df_testing_unstacked[('Building_Total_Cooling Energy Demand (kWh/m2) (summed)', 'AS_ASHRAE55', 'CM_0')]

comparison_cols = ['relative']

# df_testing_unstacked_temp = df_testing_unstacked.copy()

df_testing_unstacked.columns = ['['.join(col).strip('[') for col in df_testing_unstacked.columns.values]

other_than_baseline = [i.split('[', maxsplit=1)[1] for i in df_testing_unstacked.columns if baseline not in i]
other_than_baseline = list(dict.fromkeys(other_than_baseline))

baseline_col = [col for col in df_testing_unstacked.columns if baseline in col][0]

# cols_to_transfer = []
# in this case the months are located in rows, so no need to add months to columns
for i in cols_for_values:
    for j in other_than_baseline:
        for x in [col for col in df_testing_unstacked.columns if i in col and j in col]:
            if any('relative' in k for k in comparison_cols):
                df_testing_unstacked[f'{i}[1-({j}/{baseline})'] = (
                        1 -
                        (df_testing_unstacked[x] / df_testing_unstacked[baseline_col])
                )
                # cols_to_transfer.append(f'{i}[1-({j}/{baseline})')
            if any('absolute' in k for k in comparison_cols):
                df_testing_unstacked[f'{i}[{baseline} - {j}'] = (
                        df_testing_unstacked[baseline_col] - df_testing_unstacked[x]
                )
                # cols_to_transfer.append(f'{i}[{baseline} - {j}')

# for i in cols_for_values:
#     for j in cols_to_transfer:
#         if i in j:
#             df_testing_unstacked[(i, 'AS_JPN', 'CM_0')] = df_testing_unstacked_temp[j]
#             df_testing_unstacked[(i, j.split('[', maxsplit=1)[1]), 'x'] = df_testing_unstacked_temp[j]

# levels_list
#
# for i in cols_for_values:
#     for
#
# df_testing_unstacked_temp.to_excel('temp_unstacked_no levels_computed.xlsx')



##
# 3.1.	Full air-conditioning energy performance
z.df = df_backup.copy()
z.df = z.df[
    (z.df['EPW_Scenario-Year'].isin(['Present']))
    & (z.df['HVAC mode'].isin(['HM_0']))
    & (z.df['Category'].isin(['CA_80']))
    # & (
    #     (z.df['Adaptive Standard'].isin(['AS_JPN'])) &
    #     (z.df['Comfort mode'].isin(['CM_3']))
    # ) | (
    #     (z.df['Adaptive Standard'].isin(['AS_JPN'])) &
    #     (z.df['Comfort mode'].isin(['CM_0']))
    # )
    ]


z.df = z.df[
    (z.df['Adaptive Standard'].isin(['AS_JPN'])) &
    (z.df['Comfort mode'].isin(['CM_0'])) |
    (z.df['Adaptive Standard'].isin(['AS_JPN'])) &
    (z.df['Comfort mode'].isin(['CM_3']))
    ]


z.df = z.df.set_index([pd.RangeIndex(len(z.df))])

cols_to_clean = []
cols_for_multiindex = []
for i in z.indexcols:
    if (z.df[i][0] == z.df[i]).all():
        cols_to_clean.append(i)
    else:
        cols_for_multiindex.append(i)

z.df = z.df.drop(cols_to_clean, axis=1)
z.df = z.df.drop(['EPW', 'Source'], axis=1)
cols_for_multiindex.remove('EPW')
cols_for_multiindex.remove('Source')

z.df = z.df.set_index(cols_for_multiindex)

# todo next unstack CM

##
df_wrangled_table = df_backup.copy()
df_wrangled_table = df_wrangled_table[
    (df_wrangled_table['EPW_Scenario-Year'].isin(['Present']))
    & (df_wrangled_table['HVAC mode'].isin(['HM_0']))
    & (df_wrangled_table['Category'].isin(['CA_80']))
    # & (
    #     (df_wrangled_table['Adaptive Standard'].isin(['AS_JPN'])) &
    #     (df_wrangled_table['Comfort mode'].isin(['CM_3']))
    # ) | (
    #     (df_wrangled_table['Adaptive Standard'].isin(['AS_JPN'])) &
    #     (df_wrangled_table['Comfort mode'].isin(['CM_0']))
    # )
    ]


df_wrangled_table = df_wrangled_table[
    (df_wrangled_table['Adaptive Standard'].isin(['AS_JPN'])) &
    (df_wrangled_table['Comfort mode'].isin(['CM_0'])) |
    (df_wrangled_table['Adaptive Standard'].isin(['AS_JPN'])) &
    (df_wrangled_table['Comfort mode'].isin(['CM_3']))
    ]

df_wrangled_table = df_wrangled_table.drop(list(set(z.indexcols) - set(['Adaptive Standard', 'Comfort mode', 'EPW_City_or_subcountry'])), axis=1)

# todo wrangled_table works with z.df, not with df_wrangled_table
z.wrangled_table(
    vars_to_gather=['Comfort mode'],
    baseline='CM_0',
    comparison_cols=['absolute', 'relative']
)


# todo consider to make a method to unstack, to compare variables






##
df_temp = z.df[
    (z.df['HVAC mode'].isin(['HM_0'])) &
    (z.df['Category'].isin(['CA_80'])) &
    (
        (z.df['Adaptive Standard'].isin(['AS_JPN'])) &
        (z.df['Comfort mode'].isin(['CM_3']))
    ) | (
        (z.df['Adaptive Standard'].isin(['AS_JPN'])) &
        (z.df['Comfort mode'].isin(['CM_0']))
    )
    ]


##

dftemp = z.df.copy()
multiindex = list(set(z.indexcols) - set(['EPW', 'Source', 'EPW_Scenario-Year']))
dftemp = dftemp.set_index(multiindex)
dftemp.to_excel('0_1_temp_multiindex.xlsx')

# set(z.indexcols) - set(z.available_vars_to_gather)