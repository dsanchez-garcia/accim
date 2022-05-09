from accim.data.datawrangling import Table
import pandas as pd

z = Table(
    frequency='hourly',
    sum_or_mean='sum',
    standard_outputs=True,
    # source_concatenated_csv_filepath='Japan_graphs[freq-hourly[sum_or_mean-sum[standard_outputs-True[CSVconcatenated_Asahikawa_Sapporo.csv',
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
##



##

custom_columns = [
    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    'BLOCK1:ZONE1_ASHRAE 55 Running mean outdoor temperature (°C)',
    'Building_Total_Zone Operative Temperature (°C) (mean)'
]
z.format_table(
    type_of_table='custom',
    custom_cols=custom_columns,
    split_epw_names=True
)

# z.custom_order(
#     ordered_list=['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha'],
#     column_to_order='EPW_City_or_subcountry'
# )
#
# z.df = z.df.sort_values(['EPW_City_or_subcountry', 'Adaptive Standard', 'Category', 'Comfort mode'])


df_backup = z.df.copy()
##

z.wrangled_table(reshaping='stack')
df_testing = z.wrangled_df_stacked.unstack()
df_testing = df_testing.droplevel(0, axis=1)
df_testing = df_testing.melt(
    'BLOCK1:ZONE1_ASHRAE 55 Running mean outdoor temperature (°C)',
    var_name='temp',
    value_name='values'
)



##


import seaborn as sns

temp_plot = sns.FacetGrid(
    df_testing,
    row='EPW_City_or_subcountry',
    col='Comfort mode',
    margin_titles=True,
    legend_out=True
              )

temp_plot.map_dataframe(
    sns.scatterplot,
    x='BLOCK1:ZONE1_ASHRAE 55 Running mean outdoor temperature (°C)',
    y='values',
    # c='Building_Total_Total Energy Demand (kWh/m2) [summed]',
    # s='Site Wind Speed (m/s)',
    alpha=0.5,
    cmap='rainbow',
    hue='temp',
    legend='full',
)
temp_plot.add_legend()
# temp_plot.savefig('temp_x_2.png')

##
z.generate_fig_data(
    vars_to_gather_cols=['Comfort mode'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    data_on_x_axis='BLOCK1:ZONE1_ASHRAE 55 Running mean outdoor temperature (°C)',
    data_on_y_main_axis=[
        ['Temperature',[
            'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
            'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
            'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
        ]
         ],
    ],
    colorlist_y_main_axis=[
        ['Temperature',[
            'b',
            'r',
            'g',
            ]
         ],
    ],
)

z.scatter_plot(
    supxlabel='Comfort mode',
    figname='WIP_scatterplot_PMOT_v00.png',
    figsize=3,
    ratio_height_to_width=0.5,
)


##
z.wrangled_table(
    reshaping='unstack',
)


##
