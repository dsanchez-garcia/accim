from accim.data.datawrangling import Table

z = Table(frequency='runperiod',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['whatever'],
          level_sum_or_mean=['sum']
          )

# print(*z.returndf().columns, sep='\n')

# z.df['EPW']
# print(z.df)

z.df.to_excel('export_test.xlsx')