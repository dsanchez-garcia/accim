from accim.data.datawrangling import Table

z = Table(frequency='runperiod',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['block', 'building'],
          level_sum_or_mean=['sum'],
          match_cities=False
          )
# todo list of possible var_to_gather and baseline
z.energy_demand_table(var_to_gather='Adaptive Standard',
                      baseline='ASHRAE55')

z.enDemDf.to_excel('export_test_enerdem.xlsx')

# print(*z.returndf().columns, sep='\n')

# z.df['EPW']
# print(z.df)

# z.df.to_excel('export_test.xlsx')