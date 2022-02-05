from accim.data.datawrangling import Table

z = Table(frequency='runperiod',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['block', 'building'],
          level_sum_or_mean=['sum'],
          match_cities=False
          )

z.wrangled_table(
    vars_to_gather=[
        'Adaptive Standard',
        'Category'
        ],
    type_of_table='energy demand',
    comparison_cols=['absolute', 'relative'])

z.wrangled_df.to_excel('export_test_wrangled.xlsx')
# z.wrangled_df
# print(*z.returndf().columns, sep='\n')

# z.df['EPW']
# print(z.df)

# z.df.to_excel('export_test.xlsx')