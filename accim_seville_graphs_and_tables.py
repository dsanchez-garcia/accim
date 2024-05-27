import pandas as pd
df = pd.read_csv('accim_seville_runperiod[srcfreq-hourly[freq-runperiod[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv')
dict_replace = {
    'Seville_Present': 'Spain_Seville_Present',
    'Seville_ssp126_2050': 'Spain_Seville_SSP126-2050',
    'Seville_ssp126_2080': 'Spain_Seville_SSP126-2080',
    'Seville_ssp245_2050': 'Spain_Seville_SSP245-2050',
    'Seville_ssp245_2080': 'Spain_Seville_SSP245-2080',
    'Seville_ssp370_2050': 'Spain_Seville_SSP370-2050',
    'Seville_ssp370_2080': 'Spain_Seville_SSP370-2080',
    'Seville_ssp585_2050': 'Spain_Seville_SSP585-2050',
    'Seville_ssp585_2080': 'Spain_Seville_SSP585-2080',
}
for k, v in dict_replace.items():
    df['Source'] = [i.replace(k, v) for i in df['Source']]

df = df.drop(columns=['Unnamed: 0.1'])

df.to_csv('accim_seville_amended_runperiod[srcfreq-hourly[freq-runperiod[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv')

## Section 1
## Energy demand table (Table R1)
from accim.data.postprocessing.main import Table
z = Table(
    source_concatenated_csv_filepath='accim_seville_amended_runperiod[srcfreq-hourly[freq-runperiod[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    # level_excluded_zones=['BLOCK1:BATHROOM'],
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    idf_path='ALJARAFE CENTER_onlyGeometry.idf'
)
# print(*z.df.columns, sep='\n')
z.format_table(
    type_of_table='custom',
    custom_cols=[i for i in z.df.columns if
                 'Building_Total' in i
                 and '(summed)' in i
                 and 'Energy Demand' in i
                 ],
    # split_epw_names=True
)

dict_replace = {
    'NS_rite': 'RITE',
    'NS_seville': 'Adap Sevilla',
    'NS_X': 'Adap ASHRAE55',
}
for k, v in dict_replace.items():
    z.df['NameSuffix'] = [i.replace(k, v) for i in z.df['NameSuffix']]


df_backup = z.df.copy()
df_present = z.df.copy()

df_present = df_present[
    # (~(df_present['HVACmode'].isin(['HM_2'])))
    # &
    (df_present['EPW_Scenario'].str.contains('Present'))]

z.df = df_present
z.wrangled_table(
    reshaping='pivot',
    vars_to_gather=['NameSuffix'],
    baseline='Adap Sevilla',
    comparison_mode=['baseline compared to others'],
    comparison_cols=['relative', 'absolute']
)

# z.wrangled_df_pivoted.to_excel('comparison_present_v00.xlsx')

df_present_wrangled = z.wrangled_df_pivoted.copy()
# old_names = [
#     'CS_BRA Rupp NV[CM_3',
#     'CS_BRA Rupp NV[CM_0',
#     'CS_INT ASHRAE55[CM_3'
# ]
# new_names = [
#     'BRA_Adap_AC',
#     'BRA_Stat_AC',
#     'ASH_Adap_AC',
# ]

# for i in range(len(old_names)):
#     # df_present_wrangled.columns = [j[1].replace(old_names[i], new_names[i]) for j in df_present_wrangled]
#     df_present_wrangled.rename(columns=lambda s: s.replace(old_names[i], new_names[i]), inplace=True)
df_present_wrangled.rename(index=lambda s: s.replace(' (summed)', ''), inplace=True)
df_present_wrangled.rename(index=lambda s: s.replace('Building_Total_', ''), inplace=True)

# df_present_wrangled.to_excel('section1_tableR1_present_v00.xlsx')

##


import matplotlib.pyplot as plt
import seaborn as sns
fig, ax = plt.subplots(
    nrows=1, ncols=3,
    figsize=(15, 7.5)
)
sns.heatmap(
    data=df_present_wrangled.iloc[:, 0:3],
    square=True,
    annot=True,
    cbar_kws={'label': f'Demanda energética (kWh/m²)'},
    fmt='g',
    ax=ax[0],
    xticklabels=[i for i in df_present_wrangled.iloc[:, 0:3].columns]
)
ax[0].set(xlabel='Scenario')
ax[0].set(ylabel='Adaptation profile')
ax[0].set_title('(a) Demanda energética', y=1.05, pad=1, fontdict={'fontsize': 11})

sns.heatmap(
    data=df_present_wrangled.loc[:, [i for i in df_present_wrangled.columns if '/' in i]],
    square=True,
    annot=True,
    cbar_kws={'label': f'Variación en la demanda energética (%)'},
    fmt='g',
    ax=ax[1],
    xticklabels=[i for i in df_present_wrangled.loc[:, [i for i in df_present_wrangled.columns if '/' in i]]]
)
ax[1].set(xlabel='Scenario')
ax[1].set(ylabel='Adaptation profile')
ax[1].set_title('(b) Variación en kWh/m²', y=1.05, pad=1, fontdict={'fontsize': 11})

sns.heatmap(
    data=df_present_wrangled.loc[:, [i for i in df_present_wrangled.columns if ' - ' in i]],
    square=True,
    annot=True,
    cbar_kws={'label': f'Variación en la demanda energética (%)'},
    fmt='g',
    ax=ax[2],
    xticklabels=[i for i in df_present_wrangled.loc[:, [i for i in df_present_wrangled.columns if ' - ' in i]]]
)
ax[2].set(xlabel='Scenario')
ax[2].set(ylabel='Adaptation profile')
ax[2].set_title('(b) Variación en %', y=1.05, pad=1, fontdict={'fontsize': 11})


plt.tight_layout()

plt.savefig(f'section1_tableR1_present_v00.png')


# z.df_backup.to_excel('to_be_deleted.xlsx')

##

from accim.data.postprocessing.main import Table
z_cc = Table(
    source_concatenated_csv_filepath='accim_seville_amended_runperiod[srcfreq-hourly[freq-runperiod[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    idf_path='ALJARAFE CENTER_onlyGeometry.idf'
)
dict_replace = {
    'NS_rite': 'RITE',
    'NS_seville': 'Adap Sevilla',
    'NS_X': 'Adap ASHRAE55',
}
for k, v in dict_replace.items():
    z_cc.df['NameSuffix'] = [i.replace(k, v) for i in z_cc.df['NameSuffix']]

# print(*z.df.columns, sep='\n')
z_cc.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Total Energy Demand (kWh/m2) (summed)'
    ],
    # split_epw_names=True

)

z_cc.wrangled_table(
    reshaping='unstack',
    vars_to_gather=[
        # 'ComfStand',
        # 'ComfMod',
        # 'HVACmode',

        'EPW_Scenario',
        'EPW_Year'
        # 'EPW_Scenario-Year'
    ],
    baseline='Present[Present',
    # baseline='Present',

    comparison_mode=['baseline compared to others'],
    comparison_cols=[
        'relative',
        'absolute'
    ],
    # check_index_and_cols=True,
    vars_to_keep=[
        'NameSuffix',

        # 'EPW_Scenario-Year'

        # 'ComfStand',
        # 'ComfMod',
        # 'HVACmode',
        # 'EPW_City_or_subcountry',
    ]
)

# z_cc.wrangled_df_unstacked.to_excel('section2_climate_change_increase_v01.xlsx')
df_cc = z_cc.wrangled_df_unstacked.copy()


df_cc.rename(columns=lambda s: s.replace(' (summed)', ''), inplace=True)
df_cc.rename(columns=lambda s: s.replace('Building_Total_', ''), inplace=True)
df_cc.rename(columns=lambda s: s.replace('Present[Present', 'Presente'), inplace=True)
df_cc.rename(columns=lambda s: s.replace('[', '_'), inplace=True)

df_cc.columns.names
df_cc = df_cc.droplevel(0, axis=1)
# df_cc = df_cc.round(0)
##
import matplotlib.pyplot as plt
import seaborn as sns
fig, ax = plt.subplots(
    nrows=1, ncols=3,
    figsize=(11.5, 5)
)
sns.heatmap(
    data=df_cc.iloc[:, 0:9].transpose().round(0),
    square=True,
    annot=True,
    cbar_kws={'label': f'Demanda energética (kWh/m²)'},
    fmt='g',
    ax=ax[0],
    # xticklabels=[i for i in df_cc.iloc[:, 0:9].columns]
)
ax[0].set(xlabel='Modelo de confort')
ax[0].set(ylabel='Escenario')
ax[0].set_title('(a) Demanda energética', y=1.05, pad=1, fontdict={'fontsize': 11})

sns.heatmap(
    data=df_cc.loc[:, [i for i in df_cc.columns if '/' in i]].transpose()*100,
    square=True,
    annot=True,
    cbar_kws={'label': f'Variación en la demanda energética (%)'},
    fmt='g',
    ax=ax[1],
    # xticklabels=[i for i in df_cc.loc[:, [i for i in df_cc.columns if '/' in i]]]
)
ax[1].set(xlabel='Modelo de confort')
ax[1].set(ylabel='Escenario')
ax[1].set_title('(b) Variación en %', y=1.05, pad=1, fontdict={'fontsize': 11})

sns.heatmap(
    data=df_cc.loc[:, [i for i in df_cc.columns if ' - ' in i]].transpose().round(0),
    square=True,
    annot=True,
    cbar_kws={'label': f'Variación en la demanda energética (kWh/m²)'},
    fmt='g',
    ax=ax[2],
    # xticklabels=[i for i in df_cc.loc[:, [i for i in df_cc.columns if ' - ' in i]]]
)
ax[2].set(xlabel='Modelo de confort')
ax[2].set(ylabel='Escenario')
ax[2].set_title('(c) Variación en kWh/m²', y=1.05, pad=1, fontdict={'fontsize': 11})


plt.tight_layout()

plt.savefig(f'section2_climate_change_increase_v00.png')






##


from accim.data.postprocessing.main import Table
z = Table(
    source_concatenated_csv_filepath='accim_seville_amended_hourly[srcfreq-hourly[freq-hourly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    # level_excluded_zones=['BLOCK1:BATHROOM'],
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    idf_path='ALJARAFE CENTER_onlyGeometry.idf'
)
# print(*z.df.columns, sep='\n')
pmot = 'PLANTAX08:OFFICE_ASHRAE 55 Running mean outdoor temperature (°C)'
z.format_table(
    type_of_table='custom',
    custom_cols=[  # if type_of_table is 'custom', custom_cols is used to filter the desired columns to keep
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'Building_Total_Zone Operative Temperature (°C) (mean)',
        pmot,
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',

        # 'Building_Total_AFN Zone Infiltration Air Change Rate (ach) (summed)'
    ]
)

print(*z.df_backup.columns, sep='\n')

# df_filtered = z.df.copy()
# df_filtered = df_filtered[
#     (df_filtered['Building_Total_Zone Operative Temperature (°C) (mean)'] < df_filtered['Adaptive Cooling Setpoint Temperature_No Tolerance (°C)'])
#     &
#     (df_filtered['Building_Total_Zone Operative Temperature (°C) (mean)'] > df_filtered['Adaptive Heating Setpoint Temperature_No Tolerance (°C)'])
#     ]
# z.df = df_filtered


z.df.columns = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.val_cols]
z.df.columns = [i
    .replace('_No Tolerance', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('_No Tolerance', '')
    for i in z.val_cols]



z.scatter_plot(
    vars_to_gather_cols=['NameSuffix'],
    vars_to_gather_rows=['EPW_Scenario-Year'],
    # detailed_rows=['GC01-Florianopolis', 'GC07-Chapeco', 'GC20-Palmas'],
    # detailed_cols=['CS_BRA Rupp NV[CM_0[HM_0', 'CS_INT ASHRAE55[CM_3[HM_0', 'CS_BRA Rupp NV[CM_3[HM_2'],
    # custom_rows_order=data_daily.ordered_list,
    # custom_cols_order=['CS_BRA Rupp NV[CM_0[HM_0', 'CS_INT ASHRAE55[CM_3[HM_0', 'CS_BRA Rupp NV[CM_3[HM_2'],
    data_on_x_axis=pmot,
    data_on_y_sec_axis=[ #list which includes the name of the axis on the first place, and then in the second place, a list which includes the column names you want to plot
        [
            'Indoor Operative Temperature (°C)',
            [
                'Adaptive Cooling Setpoint Temperature (°C)',
                'Adaptive Heating Setpoint Temperature (°C)',
                'Zone Operative Temperature (°C) (mean)',
            ]
        ],
    ],
    data_on_y_main_axis=[ # similarly to above, a list including the name of the secondary y-axis and the column names you want to plot in it
        [
            'Energy (kWh/m2)',
            [
                'Cooling Energy Demand (kWh/m2)',
                'Heating Energy Demand (kWh/m2)',
            ]
        ],
    ],
    colorlist_y_sec_axis=[
        [
            'Indoor Operative Temperature (°C)',
            [
                'b',
                'r',
                'g',
            ]
        ],
    ],
    colorlist_y_main_axis=[
        [
            'Energy (kWh/m2)',
            [
                'cyan',
                'orange',
            ]
        ]
    ],
    # best_fit_deg_y_main_axis=[1, 1],

    supxlabel='Prevailing Mean Outdoor Temperature (°C)', # data label on x axis
    figname=f'scatterplot_PMOT_v00_300dpi',
    figsize=4,
    ratio_height_to_width=0.5,
    # confirm_graph=True,
    dpi=300
)





##









































## Section 1. Graph 1

from accim.data.data_postprocessing import Table
z = Table(
    source_concatenated_csv_filepath='Brazil_ACCIM_Present_AC[srcfreq-hourly[freq-hourly[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)
z.format_table(
    type_of_table='custom',
    custom_cols=[i for i in z.df.columns if
                 'Building_Total' in i
                 and '(summed)' in i
                 and 'Energy Demand' in i
                 and 'Building_Total_Total Energy Demand (kWh/m2) (summed)' not in i
                 ],
)

print(*z.df.columns, sep='\n')

z.df.columns = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.val_cols]

df_h = z.df.copy()

df_h = df_h[
    (df_h['EPW_City_or_subcountry'].isin(['GC01-Florianopolis']))
    |
    (df_h['EPW_City_or_subcountry'].isin(['GC07-Chapeco']))
    |
    (df_h['EPW_City_or_subcountry'].isin(['GC20-Palmas']))
]
df_h = df_h.reset_index().drop('index', axis=1)



z.df = df_h
z.scatter_plot_with_baseline(
    vars_to_gather_cols=['ComfStand', 'ComfMod', 'HVACmode'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    # detailed_rows=['Asahikawa', 'Maebashi', 'Naha'],
    # custom_rows_order=data_daily.ordered_list,
    data_on_y_axis_baseline_plot=z.val_cols,
    baseline='CS_BRA Rupp NV[CM_3[HM_0',
    colorlist_baseline_plot_data=['b', 'r'],

    supxlabel='BRA_Adap_AC Hourly Energy Demand (kWh/m2)',
    supylabel='Reference Hourly Energy Demand (kWh/m2)',
    figname='temp_section1_fig1_v02_dpi300',
    figsize=3,
    confirm_graph=True,
    dpi=300,

)



## Section 2
## Energy demand table (Table R2)
from accim.data.data_postprocessing import Table
z = Table(
    source_concatenated_csv_filepath='Brazil_ACCIM[freq-runperiod[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
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
                 # and 'Energy Consumption' in i
                 ],
    # split_epw_names=True
)

df_backup = z.df.copy()
df_MM = z.df.copy()

df_MM = df_MM[
    (
        (~(df_MM['HVACmode'].isin(['HM_2'])))
        &
        (df_MM['EPW_Scenario'].isin(['Present']))
    )
    |
    (
        (df_MM['HVACmode'].isin(['HM_2']))
        &
        (df_MM['EPW_Scenario'].isin(['Present']))
        &
        (df_MM['ComfMod'].isin(['CM_3']))
    )
]

z.df = df_MM
z.wrangled_table(
    reshaping='unstack',
    vars_to_gather=['ComfStand', 'ComfMod', 'HVACmode'],
    baseline='CS_BRA Rupp NV[CM_3[HM_2',
    comparison_mode=['baseline compared to others'],
    comparison_cols=['relative', 'absolute'],
    check_index_and_cols=True
)

df_MM_wrangled = z.wrangled_df_unstacked.copy()
old_names = [
    'CS_BRA Rupp NV[CM_3[HM_0',
    'CS_BRA Rupp NV[CM_0[HM_0',
    'CS_INT ASHRAE55[CM_3[HM_0',
    'CS_BRA Rupp NV[CM_3[HM_2',
]
new_names = [
    'BRA_Adap_AC',
    'BRA_Stat_AC',
    'ASH_Adap_AC',
    'BRA_Adap_MM',

]

for i in range(len(old_names)):
    # df_MM_wrangled.columns = [j[1].replace(old_names[i], new_names[i]) for j in df_MM_wrangled]
    df_MM_wrangled.rename(columns=lambda s: s.replace(old_names[i], new_names[i]), inplace=True)
df_MM_wrangled.rename(columns=lambda s: s.replace(' (summed)', ''), inplace=True)
df_MM_wrangled.rename(columns=lambda s: s.replace('Building_Total_', ''), inplace=True)


# df_MM_wrangled = df_MM_wrangled.droplevel(0, axis=0)
# df_MM_wrangled = df_MM_wrangled.sort_index()
# df_MM_wrangled = df_MM_wrangled.transpose()
df_MM_wrangled.to_excel('section2_tableR1_unstacked_v00.xlsx')

# print(*df_MM_wrangled.columns, sep='\n')


## Section 2. Graph 1

from accim.data.data_postprocessing import Table
z = Table(
    source_concatenated_csv_filepath='Brazil_ACCIM_Present_MM[srcfreq-hourly[freq-hourly[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)
z.format_table(
    type_of_table='custom',
    custom_cols=[i for i in z.df.columns if
                 'Building_Total' in i
                 and '(summed)' in i
                 and 'Energy Demand' in i
                 and 'Building_Total_Total Energy Demand (kWh/m2) (summed)' not in i
                 ],
)

print(*z.df.columns, sep='\n')

z.df.columns = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.val_cols]

z.scatter_plot_with_baseline(
    vars_to_gather_cols=['ComfStand', 'ComfMod', 'HVACmode'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    # detailed_rows=['Asahikawa', 'Maebashi', 'Naha'],
    # custom_rows_order=data_daily.ordered_list,
    data_on_y_axis_baseline_plot=z.val_cols,
    baseline='CS_BRA Rupp NV[CM_3[HM_2',
    colorlist_baseline_plot_data=['b', 'r'],

    supxlabel='BRA_Adap_MM Hourly Energy Demand (kWh/m2)',
    supylabel='Reference Hourly Energy Demand (kWh/m2)',
    figname='Fig_07_section2_fig1_v03_300dpi',
    figsize=3,
    confirm_graph=True,
    dpi=300,
    best_fit_deg=[1, 1],
)

## Section 2 Graph 2

from accim.data.data_postprocessing import Table
z = Table(
    source_concatenated_csv_filepath='Brazil_ACCIM_Present_MM[srcfreq-hourly[freq-hourly[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    level_excluded_zones=['BLOCK1:BATHROOM'],
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)

z.format_table(
    type_of_table='custom',
    custom_cols=[  # if type_of_table is 'custom', custom_cols is used to filter the desired columns to keep
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'Building_Total_Zone Operative Temperature (°C) (mean)',
        'BLOCK1:LIVINGROOM_ASHRAE 55 Running mean outdoor temperature (°C)',
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',

        # 'Building_Total_AFN Zone Infiltration Air Change Rate (ach) (summed)'
    ]
)

print(*z.df_backup.columns, sep='\n')

# df_filtered = z.df.copy()
# df_filtered = df_filtered[
#     (df_filtered['Building_Total_Zone Operative Temperature (°C) (mean)'] < df_filtered['Adaptive Cooling Setpoint Temperature_No Tolerance (°C)'])
#     &
#     (df_filtered['Building_Total_Zone Operative Temperature (°C) (mean)'] > df_filtered['Adaptive Heating Setpoint Temperature_No Tolerance (°C)'])
#     ]
# z.df = df_filtered


z.df.columns = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.val_cols]
z.df.columns = [i
    .replace('_No Tolerance', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('_No Tolerance', '')
    for i in z.val_cols]



z.scatter_plot(
    vars_to_gather_cols=['ComfStand', 'ComfMod', 'HVACmode'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    detailed_rows=['GC01-Florianopolis', 'GC07-Chapeco', 'GC20-Palmas'],
    detailed_cols=['CS_BRA Rupp NV[CM_0[HM_0', 'CS_INT ASHRAE55[CM_3[HM_0', 'CS_BRA Rupp NV[CM_3[HM_2'],
    # custom_rows_order=data_daily.ordered_list,
    custom_cols_order=['CS_BRA Rupp NV[CM_0[HM_0', 'CS_INT ASHRAE55[CM_3[HM_0', 'CS_BRA Rupp NV[CM_3[HM_2'],
    data_on_x_axis='BLOCK1:LIVINGROOM_ASHRAE 55 Running mean outdoor temperature (°C)',
    data_on_y_sec_axis=[ #list which includes the name of the axis on the first place, and then in the second place, a list which includes the column names you want to plot
        [
            'Indoor Operative Temperature (°C)',
            [
                'Adaptive Cooling Setpoint Temperature (°C)',
                'Adaptive Heating Setpoint Temperature (°C)',
                'Zone Operative Temperature (°C) (mean)',
            ]
        ],
    ],
    data_on_y_main_axis=[ # similarly to above, a list including the name of the secondary y-axis and the column names you want to plot in it
        [
            'Energy (kWh/m2)',
            [
                'Cooling Energy Demand (kWh/m2)',
                'Heating Energy Demand (kWh/m2)',
            ]
        ],
    ],
    colorlist_y_sec_axis=[
        [
            'Indoor Operative Temperature (°C)',
            [
                'b',
                'r',
                'g',
            ]
        ],
    ],
    colorlist_y_main_axis=[
        [
            'Energy (kWh/m2)',
            [
                'cyan',
                'orange',
            ]
        ]
    ],
    best_fit_deg_y_main_axis=[1, 1],

    supxlabel='Prevailing Mean Outdoor Temperature (°C)', # data label on x axis
    figname=f'Fig_08_scatterplot_PMOT_v03_300dpi',
    figsize=4,
    ratio_height_to_width=0.5,
    confirm_graph=True,
    dpi=300
)

##

# """
# Traceback (most recent call last):
#   File "C:\Users\user\AppData\Local\Programs\Python\Python39\lib\site-packages\IPython\core\interactiveshell.py", line 3444, in run_code
#     exec(code_obj, self.user_global_ns, self.user_ns)
#   File "<ipython-input-2-71a5fffd7d9d>", line 86, in <module>
#     z.scatter_plot(
#   File "C:\Users\user\AppData\Local\Programs\Python\Python39\lib\site-packages\accim\data\datawrangling.py", line 2529, in scatter_plot
#     main_y_axis[i][j][k].scatter(
#   File "C:\Users\user\AppData\Local\Programs\Python\Python39\lib\site-packages\matplotlib\__init__.py", line 1412, in inner
#     return func(ax, *map(sanitize_sequence, args), **kwargs)
#   File "C:\Users\user\AppData\Local\Programs\Python\Python39\lib\site-packages\matplotlib\axes\_axes.py", line 4369, in scatter
#     raise ValueError("x and y must be the same size")
# ValueError: x and y must be the same size
# """

## Section 3

from accim.data.datawrangling import Table
z_cc = Table(
    source_concatenated_csv_filepath='Brazil_ACCIM[freq-runperiod[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum'],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)
# print(*z.df.columns, sep='\n')
z_cc.format_table(
    type_of_table='custom',
    custom_cols=[i for i in z_cc.df.columns if
                 'Building_Total' in i
                 and '(summed)' in i
                 and 'Energy Demand' in i
                 ],
    # split_epw_names=True
)

z_cc.wrangled_table(
    reshaping='unstack',
    vars_to_gather=[
        'EPW_Scenario',
        'EPW_Year'
    ],
    baseline='Present[Present',
    comparison_mode='baseline compared to others',
    comparison_cols=[
        'relative',
        'absolute'
    ],
    # check_index_and_cols=True,
    vars_to_keep=[
        'EPW_City_or_subcountry',
        'ComfStand',
        'ComfMod',
        'HVACmode'
    ]
)

z_cc.wrangled_df_unstacked.to_excel('section3_Table_unstacked_v01.xlsx')

## Section 3 Graph 1 Ventilation hours

from accim.data.data_postprocessing import Table
z = Table(
    source_concatenated_csv_filepath='Brazil_ACCIM_CC_MM[freq-hourly[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)
print(*z.df_backup.columns, sep='\n')

##
z.format_table(
    type_of_table='custom',
    custom_cols=[  # if type_of_table is 'custom', custom_cols is used to filter the desired columns to keep
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'Building_Total_Zone Operative Temperature (°C) (mean)',
        'BLOCK1:LIVINGROOM_ASHRAE 55 Running mean outdoor temperature (°C)',
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',

        'Building_Total_AFN Zone Ventilation Air Change Rate (ach) (summed)',
        'Building_Total_AFN Zone Ventilation Air Change Rate (ach) (mean)',
    ]
)

print(*z.df_backup.columns, sep='\n')


# df_filtered = z.df.copy()
# df_filtered = df_filtered[
#     (df_filtered['Building_Total_Zone Operative Temperature (°C) (mean)'] < df_filtered['Adaptive Cooling Setpoint Temperature_No Tolerance (°C)'])
#     &
#     (df_filtered['Building_Total_Zone Operative Temperature (°C) (mean)'] > df_filtered['Adaptive Heating Setpoint Temperature_No Tolerance (°C)'])
#     ]
# z.df = df_filtered

z.df.columns = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.val_cols]
z.df.columns = [i
    .replace('_No Tolerance', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('_No Tolerance', '')
    for i in z.val_cols]
##


z.time_plot(
    vars_to_gather_rows=['EPW_Scenario-Year'],
    vars_to_gather_cols=['EPW_City_or_subcountry'],
    # detailed_rows=['GC01-Florianopolis', 'GC07-Chapeco', 'GC20-Palmas'],
    # detailed_cols=['CS_BRA Rupp NV[CM_0[HM_0', 'CS_INT ASHRAE55[CM_3[HM_0', 'CS_BRA Rupp NV[CM_3[HM_2'],
    # custom_rows_order=data_daily.ordered_list,
    # custom_cols_order=['CS_BRA Rupp NV[CM_0[HM_0', 'CS_INT ASHRAE55[CM_3[HM_0', 'CS_BRA Rupp NV[CM_3[HM_2'],
    data_on_y_main_axis=[ #list which includes the name of the axis on the first place, and then in the second place, a list which includes the column names you want to plot
        [
            'Zone Ventilation Air Change Rate (ach)',
            [
                # 'Adaptive Cooling Setpoint Temperature (°C)',
                # 'Adaptive Heating Setpoint Temperature (°C)',
                # 'Zone Operative Temperature (°C) (mean)',
                'AFN Zone Ventilation Air Change Rate (ach) (mean)',

            ]
        ],
    ],
    data_on_y_sec_axis=[ # similarly to above, a list including the name of the secondary y-axis and the column names you want to plot in it
        [
            'Energy (kWh/m2)',
            [
                'Cooling Energy Demand (kWh/m2)',
                'Heating Energy Demand (kWh/m2)',
            ]
        ],
    ],
    colorlist_y_main_axis=[
        [
            'Zone Ventilation Air Change Rate (ach)',
            [
                'b',
                # 'r',
                # 'g',
            ]
        ],
    ],
    colorlist_y_sec_axis=[
        [
            'Energy (kWh/m2)',
            [
                'cyan',
                'orange',
            ]
        ]
    ],
    supxlabel='Time',
    figname='testing.png',
    figsize=4,
    ratio_height_to_width=0.33,
)


##
# z.scatter_plot(
#     supxlabel='Running Mean Outdoor Temperature (°C)', # data label on x axis
#     figname=f'WIP_scatterplot_RMOT_02',
#     figsize=4,
#     ratio_height_to_width=0.5,
#     confirm_graph=True
# )

##
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

df_MM_hourly = z.df.copy()
df_MM_hourly = df_MM_hourly[
    (df_MM_hourly.Month.isin(['12']))
    |
    (df_MM_hourly.Month.isin(['01']))
    |
    (df_MM_hourly.Month.isin(['02']))
    |
    (df_MM_hourly.Month.isin(['03']))
    ]

df_MM_hourly = df_MM_hourly.drop(columns=list(
    set(df_MM_hourly.columns.to_list()) - set(['Month', 'Hour', 'EPW_City_or_subcountry', 'EPW_Scenario-Year', 'EPW_Scenario', 'EPW_Year']) - set(z.val_cols)
))
df_MM_hourly = df_MM_hourly.set_index([pd.RangeIndex(len(df_MM_hourly))])

df_MM_hourly.Month = [int(float(i)) for i in df_MM_hourly.Month]
df_MM_hourly.Hour = [int(float(i)) for i in df_MM_hourly.Hour]


sns.set_theme(context='paper')
# sns.set_style('darkgrid', {"grid.color": "0.5", "grid.linestyle": ":"})
sns.set_style('whitegrid', {
    'axes.facecolor': '0.9',
    "grid.color": "0.5",
    "grid.linestyle": ":",
    'axes.spines.left': True,
    'axes.spines.bottom': True,
    'axes.spines.right': True,
    'axes.spines.top': True
    }
)
# sns.axes_style(
# {'axes.facecolor': 'grey'}
# )

g = sns.FacetGrid(
    data=df_MM_hourly,
    col='EPW_City_or_subcountry',
    row='Month',
    hue='EPW_Scenario-Year',
    # row_order=data_hourly.ordered_list,
    col_order=['GC01-Florianopolis', 'GC07-Chapeco', 'GC20-Palmas'],
    row_order=[12, 1, 2, 3],
    legend_out=True,
    sharex=True,
    # sharey=False,
    sharey=True,
    margin_titles=True,
    despine=False

)
g.map_dataframe(
    sns.lineplot,
    x='Hour',
    y='AFN Zone Ventilation Air Change Rate (ach) (mean)',
    estimator='mean',
    ci=None,

)
g.set_titles(col_template="{col_name}", row_template="Month {row_name}")
g.set_axis_labels(x_var='Hour', y_var='Air Change Rate (ach)')
plt.xticks(list(range(0, 24, 2)))
g.add_legend()
g.savefig('temp_v05.png')

## Vent hours table

from accim.data.datawrangling import Table
z = Table(
    source_concatenated_csv_filepath='Brazil_ACCIM[freq-runperiod[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['mean'],
    level_excluded_zones=['BLOCK1:BATHROOM'],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)

##
z.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Ventilation Hours (h) (mean)',
        # 'Building_Total_AFN Zone Ventilation Air Change Rate (ach) (summed)',
        'Building_Total_AFN Zone Ventilation Air Change Rate (ach) (mean)',
    ]
)

df_backup = z.df.copy()
df_MM = z.df.copy()

df_MM = df_MM[(df_MM['HVACmode'].isin(['HM_2']))]

z.df = df_MM

for i in ['relative', 'absolute']:
    z.wrangled_table(
        reshaping='unstack',
        vars_to_gather=['EPW_Scenario', 'EPW_Year'],
        baseline='Present[Present',
        comparison_cols=[i],
        vars_to_keep=['EPW_City_or_subcountry'],
        # check_index_and_cols=True
    )

    z.wrangled_df_unstacked.to_excel(f'section3_ach_mean_{i}.xlsx')

## Total energy demand graph CC  / cons: values are average between different comfmods
import seaborn as sns
from accim.data.datawrangling import Table
z_runperiod_CC = Table(
    source_concatenated_csv_filepath='Brazil_ACCIM[freq-runperiod[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)
z_runperiod_CC.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Total Energy Demand (kWh/m2) (summed)',
    ]
)
z_runperiod_CC.df['Mode'] = 'temp'
z_runperiod_CC.df['Mode'] = z_runperiod_CC.df['ComfStand'] +'['+ z_runperiod_CC.df['ComfMod'] +'['+ z_runperiod_CC.df['HVACmode']

old_names = [
    'CS_BRA Rupp NV[CM_3[HM_0',
    'CS_BRA Rupp NV[CM_3[HM_2',
    'CS_BRA Rupp NV[CM_0[HM_0',
    'CS_INT ASHRAE55[CM_3[HM_0',
]
new_names = [
    'BRA_Adap_AC',
    'BRA_Adap_MM',
    'BRA_Stat_AC',
    'ASH_Adap_AC',
]

z_runperiod_CC.df = z_runperiod_CC.df.replace(old_names, new_names)

z_runperiod_CC.df.rename(columns=lambda s: s.replace(' (summed)', ''), inplace=True)
z_runperiod_CC.df.rename(columns=lambda s: s.replace('(kWh/m2)', '(kWh/m2·year)'), inplace=True)
z_runperiod_CC.df.rename(columns=lambda s: s.replace('Building_Total_', ''), inplace=True)
##
sns.set_style("whitegrid",
              # {"grid.color": ".2",
              #  "grid.linestyle": ":"
              #  }
)
sns.set_context('paper')
# sns.color_palette('rocket')
# sns.set_palette('rocket')
grid = sns.FacetGrid(
    data=z_runperiod_CC.df,
    # col='fig_section',
    col='EPW_City_or_subcountry',
    col_wrap=4,
    # height=1
    aspect=1,
    size=3,
    sharey=False,
    # hue='EPW_Scenario-Year',
    legend_out=True,
    # palette='rocket'
)
grid.map(
    sns.barplot,
    x=z_runperiod_CC.df['Mode'],
    order=[
    'BRA_Stat_AC',
    'ASH_Adap_AC',
    'BRA_Adap_AC',
    'BRA_Adap_MM',
    ],
    hue=z_runperiod_CC.df['EPW_Scenario-Year'],
    y=z_runperiod_CC.df['Total Energy Demand (kWh/m2·year)'],
    ci=None,
)
grid.set_axis_labels("Scenario", "Total Energy Demand (kWh/m2·year)")
# grid.set(ylim=(0, 50))
grid.set_titles(
    col_template="{col_name}",
    # row_template="{row_name}"
)
for axes in grid.axes.flat:
    _ = axes.set_xticklabels(axes.get_xticklabels(), rotation=90)
grid.add_legend()
sns.move_legend(
    grid,
    loc='lower center',
    bbox_to_anchor=(0.5, -0.01),
    ncol=7,
    # frameon=False
)
grid.tight_layout()
grid.savefig(f'Fig_7_energy demand CC_v01.png', dpi=900)

## Not sure: maybe generate table to summarize building total energy demand

from accim.data.datawrangling import Table
z_cc = Table(
    source_concatenated_csv_filepath='Brazil_ACCIM[freq-runperiod[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    manage_epw_names=False,
    match_cities=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)
# print(*z.df.columns, sep='\n')
z_cc.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Total Energy Demand (kWh/m2) (summed)'
    ],
    # split_epw_names=True
)

z_cc.wrangled_table(
    reshaping='unstack',
    vars_to_gather=[
        # 'ComfStand',
        # 'ComfMod',
        # 'HVACmode',

        'EPW_Scenario',
        'EPW_Year'
    ],
    baseline='Present[Present',
    comparison_mode='baseline compared to others',
    comparison_cols=[
        'relative',
        'absolute'
    ],
    # check_index_and_cols=True,
    vars_to_keep=[
        'ComfStand',
        'ComfMod',
        'HVACmode',
        'EPW_City_or_subcountry',
    ]
)
##
temp_df = z_cc.wrangled_df_unstacked
# temp_df = temp_df.unstack(2)
# temp_df = temp_df.unstack(0)
# temp_df = temp_df.unstack(0)

z_cc.wrangled_df_unstacked.to_excel('section3_Table_summary_v01.xlsx')
##
# import seaborn as sns
# glue = sns.load_dataset("glue").pivot("Model", "Task", "Score")
#
# heatmap = sns.heatmap(z_cc.wrangled_df_unstacked, annot=True)
# heatmap.savefig('temp.png')
#
# figure = heatmap.get_figure()
# figure.savefig('svm_conf.png', dpi=400)