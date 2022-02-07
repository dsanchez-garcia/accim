from accim.data.datawrangling import Table

z = Table(frequency='runperiod',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['block', 'building'],
          level_sum_or_mean=['sum'],
          match_cities=False,
          normalised_energy_units=False,
          rename_cols=True,
          energy_units_in_kWh=True
          )
# print(*z.df.columns, sep='\n')

z.wrangled_table(
    vars_to_gather=[
        'Adaptive Standard',
        'Category'
        ],
    baseline='AS_CTE[CA_X',
    type_of_table='energy demand',
    custom_cols=[
        # 'Heating Energy Demand',
        # 'Cooling Energy Demand',
        # 'Total Energy Demand',
        'discomfortable'
        ],
    comparison_cols=['absolute', 'relative']
)

z.wrangled_df.to_excel('export_test_wrangled.xlsx')
# z.wrangled_df
# print(*z.returndf().columns, sep='\n')

# z.df['EPW']
# print(z.df)

# z.df.to_excel('export_test.xlsx')