from accim.data.datawrangling import Table
z = Table(
    frequency='monthly',
    sum_or_mean='sum',
    standard_outputs=True,
    level=['block', 'building'],
    level_sum_or_mean=['sum', 'mean'],
    split_epw_names=False,
    normalised_energy_units=True,
)

z.df.to_excel('to_be_deleted.xlsx')

# list_orig = ['block1:zone1', 'block1:zone2']
# list_under = ['block1_zone1', 'block1_zone2']
#
# for i in list_orig:
#     for j in list_under:
#         if i.replace(':', '_') in j:
#             print(f'{i} in {j}')