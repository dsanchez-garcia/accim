from accim.data.datawrangling import Table
import time
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import pandas as pd
import collections
start = time.time()
frequency = 'hourly'

import glob

allfiles = glob.glob('*.csv', recursive=True)
# files_desired = [
#     'London_Present',
#     'London_RCP85_2100',
#     'AS_EN16798[CA_3',
# ]
# files = [f for f in allfiles if all(d in f for d in files_desired)]

# files = [f for f in allfiles if
#          'London_Present' in f and 'AS_EN16798[CA_3' in f or
#          'London_RCP85_2100' in f and 'AS_EN16798[CA_3' in f or
#          'London_Present' in f and 'AS_CTE[CA_X' in f or
#          'London_RCP85_2100' in f and 'AS_CTE[CA_X' in f
#          ]

files = [f for f in allfiles if 'Asahikawa' in f]



z = Table(
    datasets=allfiles,
    frequency=frequency,
    sum_or_mean='sum',
    standard_outputs=True,
    level=[],
    level_agg_func=[],
    match_cities=False,
    manage_epw_names=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    )

# print(*z.df.columns, sep='\n')

# z.df.to_excel('temp_runperiod.xlsx')

additional_list = [
    'Site Outdoor Air Drybulb Temperature (°C)',
    'Site Outdoor Air Relative Humidity (%)'
    # 'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    # 'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    # 'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    # 'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    # 'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
    # 'Building_Total_AFN Zone Infiltration Volume (m3) [summed]',
    # 'Building_Total_Comfortable Hours_No Applicability (h) [mean]'
]


custom_cols_list = additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               split_epw_names=True
               )

# DONEtodo add function to amend epw names before simulation; then amend datawrangling to automatically manage epw names if required

# todo function for average of high and low temps: groupby source and day, then agg max, then groupby month and agg mean
vars_to_analyse = [
    'Site Outdoor Air Drybulb Temperature (°C)',
    'Site Outdoor Air Relative Humidity (%)'
]
site_dict = {}
for i in vars_to_analyse:
    temp = {i: ['mean', 'max', 'min']}
    site_dict.update(temp)

# z.df = z.df.groupby(['Source', 'Month', 'Day']).agg({
#     'Site Outdoor Air Drybulb Temperature (°C)': [
#         'mean',
#         'max',
#         'min'
#     ]})

df_for_graph_monthly_site = z.df.copy()
# z.df = z.df.groupby(['Source', 'Month', 'Day']).agg(site_dict)
df_for_graph_monthly_site = df_for_graph_monthly_site.groupby(['Source', 'Month', 'Day']).agg(site_dict).groupby(['Source', 'Month']).agg('mean')

# df_for_graph_monthly_site.columns = df_for_graph_monthly_site.columns.map('['.join)



df_for_graph_monthly_site = df_for_graph_monthly_site.stack()



df_for_graph_monthly_site['new'] = ['_'.join(map(str, i)) for i in df_for_graph_monthly_site.index.tolist()]
df_for_graph_monthly_site['data'] = 'temp'

df_for_graph_monthly_site = df_for_graph_monthly_site.set_index([pd.RangeIndex(len(df_for_graph_monthly_site))])

for i in range(len(df_for_graph_monthly_site)):
    df_for_graph_monthly_site.loc[i, 'data'] = str(df_for_graph_monthly_site.loc[i, 'new']).split('[')[-1]

df_for_graph_monthly_site[[
    'EPW_Country_name',
    'EPW_City_or_subcountry',
    'EPW_Scenario-Year',
    'Month',
    'mean_max_or_min'
    ]] = df_for_graph_monthly_site['data'].str.split('_', expand=True)

df_for_graph_monthly_site = df_for_graph_monthly_site.drop('new', axis=1)
df_for_graph_monthly_site = df_for_graph_monthly_site.drop('data', axis=1)
df_for_graph_monthly_site.columns

df_for_graph_monthly_site['EPW_Country_City_Scenario-Year'] = df_for_graph_monthly_site[[
    'EPW_Country_name',
    'EPW_City_or_subcountry',
    'EPW_Scenario-Year',
    ]].agg('_'.join, axis=1)

df_for_graph_monthly_site[[
    'EPW_Scenario',
    'EPW_Year',
]] = df_for_graph_monthly_site['EPW_Scenario-Year'].str.split('-', expand=True)
df_for_graph_monthly_site.EPW_Year.fillna(value='Present', inplace=True)

##

import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(
    context='paper',
    # style='whitegrid',

)

sns.set_style("darkgrid", {"grid.color": ".6"})

height = 1.5
aspect = 1.5
temp_plot = sns.FacetGrid(
    df_for_graph_monthly_site,
    col='EPW_Scenario',
    row='EPW_City_or_subcountry',
    hue='EPW_Year',
    sharex=True,
    sharey='row',
    margin_titles=True,
    legend_out=True,
    height=height,
    aspect=aspect
              )

temp_plot.map_dataframe(
    sns.lineplot,
    data=df_for_graph_monthly_site,
    x='Month',
    y='Site Outdoor Air Drybulb Temperature (°C)',
    # c='Building_Total_Total Energy Demand (kWh/m2) [summed]',
    # s='Site Wind Speed (m/s)',
    alpha=0.5,
    # cmap='rainbow',
    # hue='mean_max_or_min',
    # style='EPW_Year',
    # style='mean_max_or_min',
    legend='full',
)

plt.subplots_adjust(hspace=0.00, wspace=0.00)

# temp_plot.set_ylabels('Temperature (°C)')
# temp_plot.set_ylabels('')
# temp_plot.set_xlabels('')

# temp_plot.fig.axis.xaxis.set_visible(False)
# temp_plot.fig.axes.yaxis.set_visible(False)
temp_plot.set(xlabel=None, ylabel=None)

temp_plot.set_titles(col_template='{col_name}', row_template='{row_name}')

temp_plot.fig.supxlabel('Month')
temp_plot.fig.supylabel('Temperature (°C)')


temp_plot.fig.tight_layout()

temp_plot.add_legend()

# temp_plot.supylabel('whatever')

temp_plot.savefig(
    fname=f'temp_x_height_{height}_aspect_{aspect}.png',
    dpi=900
)
# temp_plot.savefig(f'temp_x_height_default.png')
# temp_plot.savefig(f'temp_x_height_default_v00.png')





##


sns.lineplot(
    data=df_for_graph_monthly_site,
    x='Month',
    y='Site Outdoor Air Drybulb Temperature (°C)',
    hue='mean_max_or_min',
    style='EPW_Country_City_Scenario-Year'
)

ax2 = plt.twinx()

sns.lineplot(
    data=df_for_graph_monthly_site,
    x='Month',
    y='Site Outdoor Air Relative Humidity (%)',
    hue='mean_max_or_min',
    style='EPW_Country_City_Scenario-Year'
)



##

# not used

df_for_graph_monthly_site['new'] = ['_'.join(map(str, i)) for i in df_for_graph_monthly_site.index.tolist()]
df_for_graph_monthly_site['data'] = 'temp'

df_for_graph_monthly_site = df_for_graph_monthly_site.set_index([pd.RangeIndex(len(df_for_graph_monthly_site))])

for i in range(len(df_for_graph_monthly_site)):
    df_for_graph_monthly_site.loc[i, 'data'] = str(df_for_graph_monthly_site.loc[i, 'new']).split('[')[-1]

df_for_graph_monthly_site[[
    'EPW_Country_name',
    'EPW_City_or_subcountry',
    'EPW_Scenario-Year',
    'Month'
    ]] = df_for_graph_monthly_site['data'].str.split('_', expand=True)



##
