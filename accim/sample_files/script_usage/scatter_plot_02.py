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
    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    'BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
    'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]

custom_cols_list = additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               split_epw_names=False
               )
print(*z.df.columns, sep='\n')

print(list(set(z.df['Adaptive Standard'])))
print(list(set(z.df['Category'])))

z.scatter_plot(type_of_graph='op temp vs rmot',
               vars_to_gather_rows=['EPW'],
               vars_to_gather_cols=['Adaptive Standard', 'Category'],
               # detailed_rows=['London_RCP85_2100', 'London_Present'],
               # detailed_cols=['AS_CTE[CA_X', 'AS_EN16798[CA_1'],
               data_on_x_axis='BLOCK1:ZONE2_EN16798-1 Running mean outdoor temperature (°C)',
               data_on_y_main_axis=[
                   'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
                   'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
                   'Building_Total_Zone Thermostat Operative Temperature (°C) [mean]',
               ],
               # colorlist=[
               #     'b',
               #     'r'
               # ],
               # supxlabel='Outdoor temperature',
               # supylabel='Energy demand',
               figname='test_figure_rmot vs op temp_4',
               figsize=4,
               confirm_graph=True
               )
end = time.time()
print(end-start)

