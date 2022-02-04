from accim.data.datawrangling import Table

z = Table(frequency='runperiod',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['block', 'building'],
          level_sum_or_mean=['sum'],
          match_cities=False
          )

z.energy_demand_table(vars_to_gather=['Model',
                                      'Adaptive Standard',
                                      'Comfort mode',
                                      'Category'])

z.enDemDf.to_excel('export_test_enerdem.xlsx')
# z.enDemDf
# print(*z.returndf().columns, sep='\n')

# z.df['EPW']
# print(z.df)

# z.df.to_excel('export_test.xlsx')