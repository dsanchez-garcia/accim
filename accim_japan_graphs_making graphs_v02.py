from accim.data.datawrangling import Table
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

z.custom_order(
    ordered_list=['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha'],
    column_to_order='EPW_City_or_subcountry'
)
df_backup = z.df.copy()

## Section 1
#
# df_fullAC = df_backup.copy()
# # print(*df_fullAC, sep='\n')
#
# df_fullAC = df_fullAC[
#     # (
#     #     (df_fullAC['Adaptive Standard'].isin(['AS_PMV']))
#     #     &
#     #     (df_fullAC['EPW_Scenario-Year'].isin(['Present']))
#     # )
#     # |
#     (
#             (df_fullAC['HVAC mode'].isin(['HM_0']))
#             &
#             (df_fullAC['Category'].isin(['CA_80']))
#             &
#             (df_fullAC['EPW_Scenario-Year'].isin(['Present']))
#     )
#     ]
#
# df_fullAC = df_fullAC[
#     (
#             (df_fullAC['Adaptive Standard'].isin(['AS_ASHRAE55']))
#             &
#             (df_fullAC['Comfort mode'].isin(['CM_3']))
#     )
#     |
#     (
#             (df_fullAC['Adaptive Standard'].isin(['AS_JPN']))
#             &
#             (df_fullAC['Comfort mode'].isin(['CM_3']))
#     )
#     |
#     (
#             (df_fullAC['Adaptive Standard'].isin(['AS_JPN']))
#             &
#             (df_fullAC['Comfort mode'].isin(['CM_0']))
#     )
#     # |
#     # (
#     #         (df_fullAC['Adaptive Standard'].isin(['AS_PMV']))
#     # )
#     ]
#
# df_fullAC = df_fullAC.set_index([pd.RangeIndex(len(df_fullAC))])
#
# z.df = df_fullAC
# z.wrangled_table(
#     reshaping='unstack',
#     vars_to_gather=['Adaptive Standard', 'Comfort mode'],
#     baseline='AS_JPN[CM_3',
#     comparison_mode='baseline compared to others',
#     comparison_cols=['relative', 'absolute']
# )
#
# z.wrangled_df_unstacked.to_excel('section1_unstacked_test_6.xlsx')

## Section 2

df_MM = df_backup.copy()
# print(*df_MM, sep='\n')

df_MM = df_MM[
    (
        (df_MM['Category'].isin(['CA_80']))
        &
        (df_MM['EPW_Scenario-Year'].isin(['Present']))
    )
    &
    (
        (
                (df_MM['Adaptive Standard'].isin(['AS_ASHRAE55']))
                &
                (df_MM['Comfort mode'].isin(['CM_3']))
                &
                (df_MM['HVAC mode'].isin(['HM_0']))
        )
        |
        (
                (df_MM['Adaptive Standard'].isin(['AS_JPN']))
                &
                (df_MM['Comfort mode'].isin(['CM_0']))
                &
                (df_MM['HVAC mode'].isin(['HM_0']))
        )
        |
        (
                (df_MM['Adaptive Standard'].isin(['AS_JPN']))
                &
                (df_MM['Comfort mode'].isin(['CM_3']))
                &
                (df_MM['HVAC mode'].isin(['HM_2']))
        )

    )
    ]

df_MM = df_MM.set_index([pd.RangeIndex(len(df_MM))])

# dict_tree = {}
# for i in z.indexcols:
#     for j in range(len(df_MM)):
df_MM = df_MM.set_index(z.indexcols)
print(*df_MM.index, sep='\n')

z.df = df_MM
z.wrangled_table(
    reshaping='unstack',
    vars_to_gather=['Adaptive Standard', 'Comfort mode', 'HVAC mode'],
    baseline='AS_JPN[CM_3[HM_2',
    comparison_mode='baseline compared to others',
    comparison_cols=['relative', 'absolute'],
    # check_index_and_cols=True,
    vars_to_keep=[
        'EPW_City_or_subcountry'
    ]
)

z.wrangled_df_unstacked.to_excel('section1_unstacked_test_8.xlsx')
