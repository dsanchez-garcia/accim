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

# cities_order = CategoricalDtype(
#     ['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha'],
#     ordered=True
# )
#
# z.df['EPW_City_or_subcountry'] = z.df['EPW_City_or_subcountry'].astype(cities_order)
# z.df['EPW_City_or_subcountry']
# z.df = z.df.sort_values(['EPW_City_or_subcountry', 'Adaptive Standard', 'Category', 'Comfort mode'])


df_backup = z.df.copy()

# cities_order = ['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha']

##
z.custom_order(
    ordered_list=['Asahikawa', 'Sapporo', 'Morioka', 'Niigata', 'Maebashi', 'Tokyo', 'Kagoshima', 'Naha'],
    column_to_order='EPW_City_or_subcountry',

)
z.df = z.df.sort_values(['EPW_City_or_subcountry', 'Adaptive Standard', 'Category', 'Comfort mode'])

##

# Testing reshaping

# z.df = z.df[
#     ~z.df['Adaptive Standard'].isin(['AS_PMV'])
# ]

z.df = z.df[
    (z.df['EPW_Scenario-Year'].isin(['Present']))
    &
    (z.df['HVAC mode'].isin(['HM_0']))
    &
    (z.df['Category'].isin(['CA_80']))
    &
    (z.df['Adaptive Standard'].isin(['AS_JPN'])
    &
        (
            (z.df['Comfort mode'].isin(['CM_0']))
            |
            (z.df['Comfort mode'].isin(['CM_3']))
        )
    )
]
##

z.generate_fig_data(
    vars_to_gather_cols=['Confort mode'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    data_on_x_axis='BLOCK1:ZONE1_ASHRAE 55 Running mean outdoor temperature (°C)',
    data_on_y_main_axis=[
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'BLOCK1:ZONE1_ASHRAE 55 Running mean outdoor temperature (°C)',
    ],
    colorlist_y_main_axis=[
        'b',
        'r',
        'g',
    ]
)

z.scatter_plot(
    supxlabel='Comfort mode',
    figname='WIP_scatterplot_PMOT_v00.png',
    figsize=3,
    ratio_height_to_width=0.5,
)



##

z.wrangled_table(reshaping='stack',
                 # vars_to_gather=[
                 #     # 'Adaptive Standard',
                 #     'Comfort mode'
                 #    ],
                 # baseline='CM_0',
                 # comparison_cols=['relative', 'absolute']
                 )

# z.wrangled_df_unstacked.to_excel('temp_stacked.xlsx')

# z.wrangled_df_stacked.columns = ['values']
# z.wrangled_df_stacked.index = z.wrangled_df_stacked.index.set_names(['ComfMod', 'City', 'Variable'])
z.wrangled_df_stacked.index