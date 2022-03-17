##

from accim.data.datawrangling import Table
import matplotlib.pyplot as plt
import time
start = time.time()

# making df
z = Table(frequency='daily',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['building'],
          level_sum_or_mean=['sum'],
          match_cities=False,
          normalised_energy_units=True,
          rename_cols=True,
          energy_units_in_kwh=True,
          )


# print(*z.df.columns, sep='\n')


temp_list = []
# for col in z.df.columns:
#     for zone in z.occupied_zone_list:
#         if zone in col and 'Zone Thermostat Operative Temperature' in col:
#             temp_list.append(col)

additional_list = [
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]

custom_cols_list = temp_list + additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               split_epw_names=False
               )

z.scatter_plot_adap_vs_stat(
    vars_to_gather_cols=['Adaptive Standard', 'Category'],
    vars_to_gather_rows=['EPW'],
    adap_vs_stat_data=additional_list,
    baseline='AS_CTE[CA_X',
    supxlabel='Static Energy Demand',
    supylabel='Adaptive Energy Demand',
    colorlist=[
        'b',
        'r'
    ],
    figname='temp_fig_adap vs stat en dem_daily_3',
    figsize=3,
    markersize=4,
    confirm_graph=True
)

end = time.time()
print(end-start)