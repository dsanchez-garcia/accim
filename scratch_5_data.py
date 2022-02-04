from accim.data.datawrangling import Table

z = Table(frequency='runperiod',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['block', 'building'],
          level_sum_or_mean=['sum'],
          match_cities=False
          )
# todo list of possible var_to_gather_1 and baseline
z.energy_demand_table(stages_no=2,
                      var_to_gather_1='Adaptive Standard',
                      var_to_gather_2='Category',
                      baseline='CTE_X')

z.enDemDf.to_excel('export_test_enerdem.xlsx')
z.enDemDf
# print(*z.returndf().columns, sep='\n')

# z.df['EPW']
# print(z.df)

# z.df.to_excel('export_test.xlsx')