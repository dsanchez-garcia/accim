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

df_backup = z.df.copy()
##
z.custom_order(
    ordered_list=['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha'],
    column_to_order='EPW_City_or_subcountry'
)
z.df = z.df.sort_values(['EPW_City_or_subcountry'])

##
z.df = z.df.copy()

z.df = z.df[
    (z.df['EPW_Scenario-Year'].isin(['Present']))
    &
    (z.df['HVAC mode'].isin(['HM_0']))
    &
    (z.df['Category'].isin(['CA_80']))
    &
    (z.df['AdapStand'].isin(['AS_JPN'])
    &
        (
            (z.df['Comfort mode'].isin(['CM_0']))
            |
            (z.df['Comfort mode'].isin(['CM_3']))
        )
    )
]


z.df = z.df.set_index([pd.RangeIndex(len(z.df))])

##
vars_to_gather = ['Comfort mode']
z.wrangled_table(
    reshaping='unstack',
    vars_to_gather=vars_to_gather,
    baseline='CM_0',
    comparison_cols=['relative', 'absolute']
)

temp_df = z.wrangled_df_unstacked.copy()

# temp_df.set_axis(
#     labels=[i.replace('Building_Total_', '') for i in temp_df.columns],
#     axis=1,
#     inplace=True
# )
#
# temp_df.set_axis(
#     labels=[i.replace('(summed)', '') for i in temp_df.columns],
#     axis=1,
#     inplace=True
# )

# temp_df.to_excel('table_energy_demand_v02_to_be_deleted_2.xlsx')
#
# temp_df.columns = pd.MultiIndex.from_arrays(
#     [
#         [x[i] for x in temp_df.columns.get_level_values(0).str.split('[')] for i in range(len(vars_to_gather)+1)
#     ]
# )

# todo reorder column before multiindexing columns
temp_df.columns
ordered_columns = []
for i in z.val_cols:
    for j in temp_df.columns:
        if i in j:
            ordered_columns.append(j)

temp_df = temp_df.reindex(columns=ordered_columns)

##
temp_df.columns = pd.MultiIndex.from_arrays(
    [
        [x[0] for x in temp_df.columns.get_level_values(0).str.split('[')],
        [x[1] for x in temp_df.columns.get_level_values(0).str.split('[')]
    ]
)


temp_df.to_excel('table_energy_demand_v02_to_be_deleted_4.xlsx')

# z.wrangled_df_unstacked.to_excel('table_energy_demand_v00.xlsx')

##
# df_graph = z.wrangled_df_unstacked.copy()
# df_graph = df_graph.stack()
#
# df_graph.index = pd.MultiIndex.from_arrays(
#     [
#         list(df_graph.index.get_level_values(0)),
#         [x[0] for x in df_graph.index.get_level_values(1).str.split('[')],
#         [x[1] for x in df_graph.index.get_level_values(1).str.split('[')]
#     ]
# )
#
# df_graph.to_excel('to_be_removed.xlsx')
#
# df_graph = df_graph.to_frame()
#
# df_graph.columns = ['Energy Demand (kWh/m2·year)']
# df_graph.index.names = ['Zone', 'Operation mode', 'Comfort mode']
#
# df_graph = df_graph.reset_index()
#
# for i in range(len(df_graph)):
#     if 'Total_Heating' in df_graph.loc[i, 'Operation mode']:
#         df_graph.loc[i, 'Operation mode'] = 'Heating'
#     elif 'Total_Cooling' in df_graph.loc[i, 'Operation mode']:
#         df_graph.loc[i, 'Operation mode'] = 'Cooling'
#     elif 'Total_Total' in df_graph.loc[i, 'Operation mode']:
#         df_graph.loc[i, 'Operation mode'] = 'Total'
#
#
# ##
# import seaborn as sns
#
# # sns.barplot(x='Zone', hue='Comfort mode', y='values', data=df_graph)
# sns.set_context(
#     context='paper',
#     font_scale=1.25
# )
# sns.set_style('whitegrid')
#
# g = sns.FacetGrid(
#     df_graph,
#     col='Operation mode',
#     legend_out=True,
#     # height=5,
#     # width=5
# )
# g.map_dataframe(
#     sns.barplot,
#     x='Zone',
#     hue='Comfort mode',
#     y='Energy Demand (kWh/m2·year)',
#     palette='hot'
# )
# g.set_xticklabels(
#     rotation=90
# )
# g.set_titles(col_template="{col_name}", row_template="{row_name}")
#
# g.add_legend()
#
#
# # g.tight_layout()
# g.savefig('barplot_v00.png')