from accim.data.datawrangling import Table
csvfiles = [
    r'TestModel_onlyGeometryForVRFsystem_V960[AS_JPN[CA_90[CM_3[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_temp[Japan_Asahikawa_RCP85-2100.csv',
    r'TestModel_onlyGeometryForVRFsystem_V960[AS_JPN[CA_90[CM_3[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_temp[Japan_Asahikawa_Present.csv',
]
csvfiles_2 = [
    r'TestModel_onlyGeometryForVRFsystem_V960[AS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_pmv[Japan_Asahikawa_RCP85-2100.csv',
    r'TestModel_onlyGeometryForVRFsystem_V960[AS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_pmv[Japan_Asahikawa_Present.csv',
]

CSVfile = [
    r'JapaneseApartment_v04_Adiabatic_PMV_SCRIPT[AS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_X[Japan_Asahikawa_Present.csv'
    ]

totalcsv = csvfiles + csvfiles_2

z = Table(
    # todo con csvfiles_2, es decir, pmv, hay que reemplazar : por _; averiguar por qué
    # datasets=CSVfile,
    frequency='runperiod',
    sum_or_mean='sum',
    standard_outputs=True,
    level=['block', 'building'],
    level_sum_or_mean=['sum', 'mean'],
    split_epw_names=True,
    normalised_energy_units=True,
)
z.df.to_excel('to be deleted.xlsx')

# print(*z.df.columns, sep="\n")

# z.df.to_excel('to_be_deleted.xlsx')

# list_orig = ['block1:zone1', 'block1:zone2']
# list_under = ['block1_zone1', 'block1_zone2']
#
# for i in list_orig:
#     for j in list_under:
#         if i.replace(':', '_') in j:
#             print(f'{i} in {j}')

# import pandas as pd
# temp_df = pd.read_csv(r'C:\Python\accim\TestModel_onlyGeometryForVRFsystem_V960[AS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_pmv[Japan_Asahikawa_Present.csv')
# temp_op_temp = [i for i in temp_df.columns if 'Operative Temperature' in i]
#
# occupied_zone_list = [i.split(' ')[0][:-5]
#                       for i
#                       in [i
#                           for i
#                           in temp_df.columns
#                           if 'Zone Operative Temperature [C](Hourly)' in i
#                           ]
#                       ]



# import pandas as pd
# z.df.to_csv('temp.csv')
# df = pd.read_csv('temp.csv')
# optemp_df = df.filter(regex='Operative Temperature')
# optemp_to_drop = []
# optemp_to_drop.extend(optemp_df.columns[optemp_df.isna().any()].tolist())
#
# for i in optemp_df.columns:
#     if (optemp_df[i] == 0).all():
#         optemp_to_drop.append(i)
#
# df = df.drop(optemp_to_drop, axis=1)
