import matplotlib.pyplot as plt

from accim.data.data_postprocessing import Table
dataset_hourly = Table(
    source_frequency='hourly',
    frequency='hourly',
    frequency_agg_func='sum',
    standard_outputs=True,
    level=['building'],
    level_agg_func=['mean', 'sum'],
    level_excluded_zones=['ATTIC:ATTIC'],
    split_epw_names=True,
)

dataset_hourly.format_table(
    type_of_table='custom',
    custom_cols=[
        # 'BLOCK1:PERIMETERXZNX4_ASHRAE 55 Running mean outdoor temperature (°C)',
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
        'Site Outdoor Air Drybulb Temperature (°C)'
        # 'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        # 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        # 'Building_Total_Zone Operative Temperature (°C) (mean)'
    ]
)

df = dataset_hourly.df

x = 'Site Outdoor Air Drybulb Temperature (°C)'
y = [i for i in dataset_hourly.val_cols if 'Site Outdoor Air Drybulb Temperature (°C)' not in i]

df = df.melt(
    id_vars=[i for i in df.columns if i not in y],
    value_vars=y,
    var_name='variable',
    value_name='Temperature (°C)'
    )


import seaborn as sns

sns.scatterplot(
    data=df,
    x=x,
    y='Temperature (°C)',
    hue='EPW',
    style='variable'

)
##
import matplotlib.pyplot as plt

df = dataset_hourly.df
df = df[
    df['EPW_City_or_subcountry'].str.contains('Shimla')
]

x = 'Site Outdoor Air Drybulb Temperature (°C)'
y = 'Building_Total_Cooling Energy Demand (kWh/m2) (summed)'
y_twin = 'Building_Total_Heating Energy Demand (kWh/m2) (summed)'


sns.scatterplot(
    data=df,
    x=x,
    y=y,
    hue='EPW',

)

ax2 = plt.twinx()

sns.scatterplot(
    data=df,
    x=x,
    y=y_twin,
    hue='EPW',
    ax=ax2
)