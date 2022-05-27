from accim.data.datawrangling import Table
import pandas as pd
## Runperiod dataframe
data_runperiod = Table(
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
# print(*data_runperiod.df.columns, sep='\n')
data_runperiod.format_table(
    type_of_table='custom',
    custom_cols=[i for i in data_runperiod.df.columns if
                 'Building_Total' in i
                 and '(summed)' in i
                 and 'Energy Demand' in i
                 ],
    split_epw_names=True
)

data_runperiod.custom_order(
    ordered_list=['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha'],
    column_to_order='EPW_City_or_subcountry'
)
df_runperiod_backup = data_runperiod.df.copy()

## Daily dataframe
data_daily = Table(
    source_concatenated_csv_filepath='Japan_graphs[freq-daily[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_sum_or_mean=['sum', 'mean'],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)

# print(*data_daily.df.columns, sep='\n')
data_daily.format_table(
    type_of_table='custom',
    custom_cols=[i for i in data_daily.df.columns if
                 'Building_Total' in i
                 and '(summed)' in i
                 and 'Energy Demand' in i
                 and 'Building_Total_Total Energy Demand (kWh/m2) (summed)' not in i
                 ],
    split_epw_names=True
)

data_daily.df.columns = [i
                        .replace('Building_Total_', '')
                        .replace(' (summed)', '')
                         for i in data_daily.df.columns]
data_daily.val_cols = [i
                        .replace('Building_Total_', '')
                        .replace(' (summed)', '')
                       for i in data_daily.val_cols]

data_daily.custom_order(
    ordered_list=['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha'],
    column_to_order='EPW_City_or_subcountry'
)
df_daily_backup = data_daily.df.copy()

## Hourly dataframe

data_hourly = Table(
    source_concatenated_csv_filepath='Japan_graphs_MM[freq-hourly[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_sum_or_mean=['sum', 'mean'],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)

print(*data_hourly.df.columns, sep='\n')
data_hourly.format_table(
    type_of_table='custom',
    custom_cols=[i for i in data_hourly.df.columns if
                 'Building_Total' in i
                 and '(summed)' in i
                 and 'Energy Demand' in i
                 and 'Building_Total_Total Energy Demand (kWh/m2) (summed)' not in i
                 ],
    split_epw_names=True
)

data_hourly.df.columns = [i
                        .replace('Building_Total_', '')
                        .replace(' (summed)', '')
                         for i in data_hourly.df.columns]
data_hourly.val_cols = [i
                        .replace('Building_Total_', '')
                        .replace(' (summed)', '')
                       for i in data_hourly.val_cols]

data_hourly.custom_order(
    ordered_list=['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha'],
    column_to_order='EPW_City_or_subcountry'
)
df_hourly_backup = data_hourly.df.copy()




## Section 1
# df_fullAC = df_runperiod_backup.copy()
df_fullAC = df_daily_backup.copy()
# print(*df_fullAC, sep='\n')

df_fullAC = df_fullAC[
    # (
    #     (df_fullAC['AdapStand'].isin(['AS_PMV']))
    #     &
    #     (df_fullAC['EPW_Scenario-Year'].isin(['Present']))
    # )
    # |
    (
            (df_fullAC['HVACmode'].isin(['HM_0']))
            &
            (df_fullAC['Category'].isin(['CA_80']))
            &
            (df_fullAC['EPW_Scenario-Year'].isin(['Present']))
    )
    ]

df_fullAC = df_fullAC[
    (
            (df_fullAC['AdapStand'].isin(['AS_ASHRAE55']))
            &
            (df_fullAC['ComfMod'].isin(['CM_3']))
    )
    |
    (
            (df_fullAC['AdapStand'].isin(['AS_JPN']))
            &
            (df_fullAC['ComfMod'].isin(['CM_3']))
    )
    |
    (
            (df_fullAC['AdapStand'].isin(['AS_JPN']))
            &
            (df_fullAC['ComfMod'].isin(['CM_0']))
    )
    # |
    # (
    #         (df_fullAC['AdapStand'].isin(['AS_PMV']))
    # )
    ]

df_fullAC = df_fullAC.set_index([pd.RangeIndex(len(df_fullAC))])

## Section 1 Figure 1
data_daily.df = df_fullAC
data_daily.generate_fig_data(
    vars_to_gather_cols=['AdapStand', 'ComfMod', 'HVACmode'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    detailed_rows=['Asahikawa', 'Maebashi', 'Naha'],
    custom_rows_order=data_daily.ordered_list,
    adap_vs_stat_data_y_main=data_daily.val_cols,
    baseline='AS_JPN[CM_3[HM_0',
    colorlist_adap_vs_stat_data=['b', 'r'],

)

data_daily.scatter_plot_adap_vs_stat(
    supxlabel='AS_JPN[CM_3[HM_0 Energy Demand (kWh/m2)',
    supylabel='Reference Energy Demand (kWh/m2)',
    figname='temp_section1_fig1_v00',
    figsize=3,
    confirm_graph=True

)

## Section 1 Table 1
# data_runperiod.df = df_fullAC
# data_runperiod.wrangled_table(
#     reshaping='unstack',
#     vars_to_gather=['AdapStand', 'ComfMod'],
#     baseline='AS_JPN[CM_3',
#     comparison_mode='baseline compared to others',
#     comparison_cols=['relative', 'absolute']
# )
#
# data_runperiod.wrangled_df_unstacked.to_excel('section1_unstacked_test_9.xlsx')

## Section 2
df_MM = df_runperiod_backup.copy()
# df_MM = df_daily_backup.copy()
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
                (df_MM['AdapStand'].isin(['AS_ASHRAE55']))
                &
                (df_MM['ComfMod'].isin(['CM_3']))
                &
                (df_MM['HVACmode'].isin(['HM_0']))
        )
        |
        (
                (df_MM['AdapStand'].isin(['AS_JPN']))
                &
                (df_MM['ComfMod'].isin(['CM_0']))
                &
                (df_MM['HVACmode'].isin(['HM_0']))
        )
        |
        (
                (df_MM['AdapStand'].isin(['AS_JPN']))
                &
                (df_MM['ComfMod'].isin(['CM_3']))
                &
                (df_MM['HVACmode'].isin(['HM_0']))
        )
        |
        (
                (df_MM['AdapStand'].isin(['AS_JPN']))
                &
                (df_MM['ComfMod'].isin(['CM_3']))
                &
                (df_MM['HVACmode'].isin(['HM_2']))
        )

    )
    ]

df_MM = df_MM.set_index([pd.RangeIndex(len(df_MM))])
## Section 2 Figure 1
data_daily.df = df_MM
data_daily.generate_fig_data(
    vars_to_gather_cols=['AdapStand', 'ComfMod', 'HVACmode'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    detailed_rows=['Asahikawa', 'Maebashi', 'Naha'],
    custom_rows_order=data_daily.ordered_list,
    adap_vs_stat_data_y_main=data_daily.val_cols,
    baseline='AS_JPN[CM_3[HM_2',
    colorlist_adap_vs_stat_data=['b', 'r'],

)

data_daily.scatter_plot_adap_vs_stat(
    supxlabel='AS_JPN[CM_3[HM_2 Energy Demand (kWh/m2)',
    supylabel='Reference Energy Demand (kWh/m2)',
    figname='temp_section2_fig1_v00',
    figsize=3,
    confirm_graph=True

)
## Section 2 Figure 2: promedio de ach en cada hora; en columnas, o los meses de verano, o presente y los RCP; en filas, las zonas climáticas


## Section 2 Table
data_runperiod.df = df_MM
data_runperiod.wrangled_table(
    reshaping='unstack',
    vars_to_gather=['AdapStand', 'ComfMod', 'HVACmode'],
    baseline='AS_JPN[CM_3[HM_2',
    comparison_mode='baseline compared to others',
    comparison_cols=['relative', 'absolute'],
    # check_index_and_cols=True,
    vars_to_keep=[
        'EPW_City_or_subcountry'
    ]
)

data_runperiod.wrangled_df_unstacked.to_excel('section2_unstacked_test_00.xlsx')

## Section 3
# df_CC = df_runperiod_backup.copy()
# # print(*df_CC, sep='\n')
#
# df_CC = df_CC[
#     (df_CC['Category'].isin(['CA_80']))
#     &
#     (
#         (
#                 (df_CC['AdapStand'].isin(['AS_ASHRAE55']))
#                 &
#                 (df_CC['ComfMod'].isin(['CM_3']))
#                 &
#                 (df_CC['HVACmode'].isin(['HM_0']))
#         )
#         |
#         (
#                 (df_CC['AdapStand'].isin(['AS_JPN']))
#                 &
#                 (df_CC['ComfMod'].isin(['CM_0']))
#                 &
#                 (df_CC['HVACmode'].isin(['HM_0']))
#         )
#         |
#         (
#                 (df_CC['AdapStand'].isin(['AS_JPN']))
#                 &
#                 (df_CC['ComfMod'].isin(['CM_3']))
#                 &
#                 (df_CC['HVACmode'].isin(['HM_2']))
#         )
#
#     )
#     ]
#
# df_CC = df_CC.set_index([pd.RangeIndex(len(df_CC))])
# df_CC_backup = df_CC.copy()
# ##
# df_CC = df_CC_backup
# # df_CC['city_scenario-year'] = df_CC[['EPW_City_or_subcountry', 'EPW_Scenario-Year']].agg(' '.join, axis=1)
# df_CC['AdapStand[ComfMod[HVACmode'] = df_CC[['AdapStand', 'ComfMod', 'HVACmode']].agg('['.join, axis=1)
# df_CC = df_CC.drop(columns=list(set(df_CC.columns.to_list()) - set(data_runperiod.val_cols) - set(['EPW_City_or_subcountry', 'EPW_Scenario-Year', 'AdapStand[ComfMod[HVACmode'])))
# df_CC.columns = [i
#                      .replace('Building_Total_Cooling Energy Demand (kWh/m2) (summed)','Cooling')
#                      .replace('Building_Total_Heating Energy Demand (kWh/m2) (summed)','Heating')
#                      .replace('Building_Total_Total Energy Demand (kWh/m2) (summed)', 'Total')
#                  for i in df_CC.columns]
# df_CC_temp = df_CC.melt(id_vars=['EPW_City_or_subcountry', 'EPW_Scenario-Year', 'AdapStand[ComfMod[HVACmode'])

## Graph 01
# import seaborn as sns
# import matplotlib.pyplot as plt
# sns.set_theme(context='paper')
# sns.set_style("whitegrid", {"grid.color": "0.6"})
#
# g = sns.catplot(
#     y='EPW_Scenario-Year',
#     x='value',
#     hue='AdapStand[ComfMod[HVACmode',
#     col='variable',
#     row='EPW_City_or_subcountry',
#     row_order=data_runperiod.ordered_list,
#     data=df_CC_temp,
#     kind='point',
#     orient='h',
#     height=1.5,
#     aspect=1.5,
#     margin_titles=True,
#     sharex=True,
#     legend_out=True
#
# )
# g.set_titles(col_template="{col_name}", row_template="{row_name}")
# g.set_axis_labels('Energy demand (kWh/m2)', 'Scenario')
# # g.tight_layout()
# g.figure.subplots_adjust(wspace=0, hspace=0)
# plt.xticks([0, 250, 500, 750, 1000])
# # plt.legend(
# #     title='Adaptive Standard - Comfort mode - HVAC mode',
# #     loc='bottom center'
# # )
# # g._legend.set_title('AdapStand-ComfMod-HVACmode')
# g.savefig('temp_section3_v00.png')

## Section3 tables
# # V00
# data_runperiod.df = df_CC
# data_runperiod.wrangled_table(
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
# data_runperiod.wrangled_df_unstacked.to_excel('section3_unstacked_v00_01.xlsx')
#
#
# # V01
# data_runperiod.df = df_CC
# data_runperiod.wrangled_table(
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
# data_runperiod.wrangled_df_unstacked.to_excel('section3_unstacked_v01_01.xlsx')


