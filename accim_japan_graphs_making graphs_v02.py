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
# df_fullAC = df_runperiod_backup.copy()
# # print(*df_fullAC, sep='\n')
# 
# df_fullAC = df_fullAC[
#     # (
#     #     (df_fullAC['AdapStand'].isin(['AS_PMV']))
#     #     &
#     #     (df_fullAC['EPW_Scenario-Year'].isin(['Present']))
#     # )
#     # |
#     (
#             (df_fullAC['HVACmode'].isin(['HM_0']))
#             &
#             (df_fullAC['Category'].isin(['CA_80']))
#             &
#             (df_fullAC['EPW_Scenario-Year'].isin(['Present']))
#     )
#     ]
# 
# df_fullAC = df_fullAC[
#     (
#             (df_fullAC['AdapStand'].isin(['AS_ASHRAE55']))
#             &
#             (df_fullAC['ComfMod'].isin(['CM_3']))
#     )
#     |
#     (
#             (df_fullAC['AdapStand'].isin(['AS_JPN']))
#             &
#             (df_fullAC['ComfMod'].isin(['CM_3']))
#     )
#     |
#     (
#             (df_fullAC['AdapStand'].isin(['AS_JPN']))
#             &
#             (df_fullAC['ComfMod'].isin(['CM_0']))
#     )
#     # |
#     # (
#     #         (df_fullAC['AdapStand'].isin(['AS_PMV']))
#     # )
#     ]
# 
# df_fullAC = df_fullAC.set_index([pd.RangeIndex(len(df_fullAC))])
# 
# z.df = df_fullAC
# z.wrangled_table(
#     reshaping='unstack',
#     vars_to_gather=['AdapStand', 'ComfMod'],
#     baseline='AS_JPN[CM_3',
#     comparison_mode='baseline compared to others',
#     comparison_cols=['relative', 'absolute']
# )
# 
# z.wrangled_df_unstacked.to_excel('section1_unstacked_test_9.xlsx')

## Section 2
# df_MM = df_runperiod_backup.copy()
# # print(*df_MM, sep='\n')
# 
# df_MM = df_MM[
#     (
#         (df_MM['Category'].isin(['CA_80']))
#         &
#         (df_MM['EPW_Scenario-Year'].isin(['Present']))
#     )
#     &
#     (
#         (
#                 (df_MM['AdapStand'].isin(['AS_ASHRAE55']))
#                 &
#                 (df_MM['ComfMod'].isin(['CM_3']))
#                 &
#                 (df_MM['HVACmode'].isin(['HM_0']))
#         )
#         |
#         (
#                 (df_MM['AdapStand'].isin(['AS_JPN']))
#                 &
#                 (df_MM['ComfMod'].isin(['CM_0']))
#                 &
#                 (df_MM['HVACmode'].isin(['HM_0']))
#         )
#         |
#         (
#                 (df_MM['AdapStand'].isin(['AS_JPN']))
#                 &
#                 (df_MM['ComfMod'].isin(['CM_3']))
#                 &
#                 (df_MM['HVACmode'].isin(['HM_2']))
#         )
# 
#     )
#     ]
# 
# df_MM = df_MM.set_index([pd.RangeIndex(len(df_MM))])
# 
# # dict_tree = {}
# # for i in z.indexcols:
# #     for j in range(len(df_MM)):
# # df_MM = df_MM.set_index(z.indexcols)
# # print(*df_MM.index, sep='\n')
# 
# z.df = df_MM
# z.wrangled_table(
#     reshaping='unstack',
#     vars_to_gather=['AdapStand', 'ComfMod', 'HVACmode'],
#     baseline='AS_JPN[CM_3[HM_2',
#     comparison_mode='baseline compared to others',
#     comparison_cols=['relative', 'absolute'],
#     # check_index_and_cols=True,
#     vars_to_keep=[
#         'EPW_City_or_subcountry'
#     ]
# )
# 
# z.wrangled_df_unstacked.to_excel('section2_unstacked_test_00.xlsx')

## Section 3

df_CC = df_backup.copy()
# print(*df_CC, sep='\n')

df_CC = df_CC[
    (df_CC['Category'].isin(['CA_80']))
    &
    (
        (
                (df_CC['AdapStand'].isin(['AS_ASHRAE55']))
                &
                (df_CC['ComfMod'].isin(['CM_3']))
                &
                (df_CC['HVACmode'].isin(['HM_0']))
        )
        |
        (
                (df_CC['AdapStand'].isin(['AS_JPN']))
                &
                (df_CC['ComfMod'].isin(['CM_0']))
                &
                (df_CC['HVACmode'].isin(['HM_0']))
        )
        |
        (
                (df_CC['AdapStand'].isin(['AS_JPN']))
                &
                (df_CC['ComfMod'].isin(['CM_3']))
                &
                (df_CC['HVACmode'].isin(['HM_2']))
        )

    )
    ]

df_CC = df_CC.set_index([pd.RangeIndex(len(df_CC))])
df_CC_backup = df_CC.copy()
##
df_CC = df_CC_backup
df_CC['city_scenario-year'] = df_CC[['EPW_City_or_subcountry', 'EPW_Scenario-Year']].agg(' '.join, axis=1)
df_CC['adapstand-comfmod-hvacmode'] = df_CC[['AdapStand', 'ComfMod', 'HVACmode']].agg('-'.join, axis=1)
df_CC = df_CC.drop(columns=list(set(df_CC.columns.to_list()) - set(z.val_cols) - set(['city_scenario-year', 'adapstand-comfmod-hvacmode'])))
df_CC_temp = df_CC.melt(id_vars=['city_scenario-year', 'adapstand-comfmod-hvacmode'])



import seaborn as sns
g = sns.FacetGrid(
    data=df_CC_temp,
    col='variable',
    hue='adapstand-comfmod-hvacmode'
)
g.map_dataframe(
    sns.barplot,
    y='city_scenario-year',
    x='value'
)

##
df_CC = df_CC_backup
df_CC['city_scenario-year'] = df_CC[['EPW_City_or_subcountry', 'EPW_Scenario-Year']].agg(' '.join, axis=1)
df_CC['adapstand-comfmod-hvacmode'] = df_CC[['AdapStand', 'ComfMod', 'HVACmode']].agg('-'.join, axis=1)
df_CC = df_CC.drop(columns=list(set(df_CC.columns.to_list()) - set(z.val_cols) - set(['city_scenario-year', 'adapstand-comfmod-hvacmode'])))
df_CC_temp = df_CC.melt(id_vars=['city_scenario-year', 'adapstand-comfmod-hvacmode'])



import seaborn as sns
g = sns.catplot(
    y='city_scenario-year',
    x='value',
    hue='adapstand-comfmod-hvacmode',
    col='variable',
    data=df_CC_temp,
    kind='bar',

)
##
df_CC = df_CC_backup
# df_CC['city_scenario-year'] = df_CC[['EPW_City_or_subcountry', 'EPW_Scenario-Year']].agg(' '.join, axis=1)
df_CC['AdapStand[ComfMod[HVACmode'] = df_CC[['AdapStand', 'ComfMod', 'HVACmode']].agg('['.join, axis=1)
df_CC = df_CC.drop(columns=list(set(df_CC.columns.to_list()) - set(z.val_cols) - set(['EPW_City_or_subcountry', 'EPW_Scenario-Year', 'AdapStand[ComfMod[HVACmode'])))
df_CC.columns = [i
                     .replace('Building_Total_Cooling Energy Demand (kWh/m2) (summed)','Cooling')
                     .replace('Building_Total_Heating Energy Demand (kWh/m2) (summed)','Heating')
                     .replace('Building_Total_Total Energy Demand (kWh/m2) (summed)', 'Total')
                 for i in df_CC.columns]
df_CC_temp = df_CC.melt(id_vars=['EPW_City_or_subcountry', 'EPW_Scenario-Year', 'AdapStand[ComfMod[HVACmode'])


##
import seaborn as sns
import matplotlib.pyplot as plt
# sns.set_theme(context='paper')
sns.set_style("darkgrid", {"grid.color": "0.6"})
g = sns.catplot(
    y='EPW_Scenario-Year',
    x='value',
    hue='AdapStand[ComfMod[HVACmode',
    col='variable',
    row='EPW_City_or_subcountry',
    row_order=z.ordered_list,
    data=df_CC_temp,
    kind='point',
    orient='h',
    height=1.5,
    aspect=1.5,
    margin_titles=True,
    sharex=True,
    legend_out=True

)
g.set_titles(col_template="{col_name}", row_template="{row_name}")
g.set_axis_labels('Energy demand (kWh/m2)', 'Scenario')
# g.tight_layout()
g.figure.subplots_adjust(wspace=0, hspace=0)
plt.xticks([250, 500, 750, 1000])
# plt.legend(
#     title='Adaptive Standard - Comfort mode - HVAC mode',
#     loc='bottom center'
# )
# g._legend.set_title('AdapStand-ComfMod-HVACmode')
g.savefig('temp_section3_v00.png')

##
df_CC = df_CC_backup
df_CC['city_scenario-year'] = df_CC[['EPW_City_or_subcountry', 'EPW_Scenario-Year']].agg(' '.join, axis=1)
df_CC['adapstand-comfmod-hvacmode'] = df_CC[['AdapStand', 'ComfMod', 'HVACmode']].agg('-'.join, axis=1)
df_CC = df_CC.drop(columns=list(set(df_CC.columns.to_list()) - set(z.val_cols) - set(['city_scenario-year', 'adapstand-comfmod-hvacmode'])))
df_CC_temp = df_CC.melt(id_vars=['city_scenario-year', 'adapstand-comfmod-hvacmode'])


df_CC_temp = df_CC_temp[df_CC_temp['adapstand-comfmod-hvacmode'].isin(['AS_ASHRAE55-CM_3-HM_0'])]

from matplotlib import pyplot, transforms
from matplotlib.transforms import Affine2D
from matplotlib.collections import PathCollection
import pandas as pd
import seaborn as sns


def lineplot_plusplus(orientation="horizontal", **kwargs):
    line = sns.lineplot(**kwargs)

    r = Affine2D().scale(sx=1, sy=-1).rotate_deg(90)
    for x in line.images + line.lines + line.collections:
        trans = x.get_transform()
        x.set_transform(r + trans)
        if isinstance(x, PathCollection):
            transoff = x.get_offset_transform()
            x._transOffset = r + transoff

    old = line.axis()
    line.axis(old[2:4] + old[0:2])
    xlabel = line.get_xlabel()
    line.set_xlabel(line.get_ylabel())
    line.set_ylabel(xlabel)

    return line


df = pd.DataFrame([[0, 1], [0, 2], [0, 1.5], [1, 1], [1, 5]], columns=['group', 'val'])
lineplot_plusplus(x='city_scenario-year', y='value', data=df_CC_temp, orientation="vertical")


##
df_CC = df_CC_backup
# df_CC['city_scenario-year'] = df_CC[['EPW_City_or_subcountry', 'EPW_Scenario-Year']].agg(' '.join, axis=1)
df_CC['adapstand-comfmod-hvacmode'] = df_CC[['AdapStand', 'ComfMod', 'HVACmode']].agg('-'.join, axis=1)
df_CC = df_CC.drop(columns=list(set(df_CC.columns.to_list()) - set(z.val_cols) - set(['EPW_City_or_subcountry', 'EPW_Scenario-Year', 'adapstand-comfmod-hvacmode'])))
df_CC_temp = df_CC.melt(id_vars=['EPW_City_or_subcountry', 'EPW_Scenario-Year', 'adapstand-comfmod-hvacmode'])



import seaborn as sns
g = sns.FacetGrid(
    data=df_CC_temp,
    col='variable',
    row='EPW_City_or_subcountry',
    hue='adapstand-comfmod-hvacmode'
)
g.map_dataframe(
    sns.lineplot,
    y='EPW_Scenario-Year',
    x='value'
)


## trying to plot different settings
# dict_tree = {}
# for i in z.indexcols:
#     for j in range(len(df_CC)):
# df_CC = df_CC.set_index(z.indexcols)
# print(*df_CC.index, sep='\n')

## Section3 tables
# # V00
# z.df = df_CC
# z.wrangled_table(
#     reshaping='unstack',
#     vars_to_gather=['AdapStand', 'ComfMod', 'HVACmode'],
#     baseline='AS_JPN[CM_3[HM_2',
#     comparison_mode='baseline compared to others',
#     comparison_cols=['relative', 'absolute'],
#     # check_index_and_cols=True,
#     vars_to_keep=[
#         'EPW_City_or_subcountry',
#         'EPW_Scenario',
#         'EPW_Year'
#     ]
# )
#
# z.wrangled_df_unstacked.to_excel('section3_unstacked_v00_01.xlsx')
#
#
# # V01
# z.df = df_CC
# z.wrangled_table(
#     reshaping='unstack',
#     vars_to_gather=[
#         'EPW_Scenario',
#         'EPW_Year'
#     ],
#     baseline='Present[Present',
#     comparison_mode='baseline compared to others',
#     comparison_cols=['relative', 'absolute'],
#     # check_index_and_cols=True,
#     vars_to_keep=[
#         'EPW_City_or_subcountry',
#         'AdapStand',
#         'ComfMod',
#         'HVACmode'
#     ]
# )
#
# z.wrangled_df_unstacked.to_excel('section3_unstacked_v01_01.xlsx')


