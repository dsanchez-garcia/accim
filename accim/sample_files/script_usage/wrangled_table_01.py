from accim.data.datawrangling import Table

z = Table(frequency='runperiod',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['building'],
          level_sum_or_mean=['sum', 'mean'],
          match_cities=False,
          normalised_energy_units=True,
          rename_cols=True,
          energy_units_in_kwh=True,
          )
# z.df.to_excel('export_test_full_df.xlsx')
# print(*z.df.columns, sep='\n')
# print(*z.wrangled_df.columns, sep='\n')

z.format_table(type_of_table='energy demand',
               # custom_cols=custom_cols_list,
               manage_epw_names=False
               )


z.wrangled_table(
    vars_to_gather=[
        'Adaptive Standard',
        'Category'
        ],
    baseline='AS_CTE[CA_X',
    comparison_cols=['absolute', 'relative']
)

z.wrangled_df.to_excel('export_test_wrangled_temp_3.xlsx')
