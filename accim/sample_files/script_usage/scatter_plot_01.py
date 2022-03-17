from accim.data.datawrangling import Table
import time
start = time.time()

# making df
z = Table(frequency='hourly',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['building'],
          level_sum_or_mean=['sum', 'mean'],
          match_cities=False,
          normalised_energy_units=True,
          rename_cols=True,
          energy_units_in_kwh=True,
          )
print(*z.df.columns, sep='\n')

additional_list = [
    'Site Outdoor Air Drybulb Temperature (°C)',
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]

custom_cols_list = additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               split_epw_names=False
               )
print(*z.df.columns, sep='\n')


z.scatter_plot(type_of_graph='custom',
               vars_to_gather_rows=['EPW'],
               vars_to_gather_cols=['Adaptive Standard', 'Category'],
               data_on_x_axis='Site Outdoor Air Drybulb Temperature (°C)',
               data_on_y_main_axis=[
                   'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
                   'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
               ],
               colorlist=[
                   'b',
                   'r'
               ],
               supxlabel='Outdoor temperature',
               supylabel='Energy demand'
               )
end = time.time()
print(end-start)

