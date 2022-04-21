from accim.data.datawrangling import Table
csvfiles = [
    r'TestModel_onlyGeometryForVRFsystem_V960[AS_JPN[CA_90[CM_3[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_temp[Japan_Asahikawa_RCP85-2100.csv',
    r'TestModel_onlyGeometryForVRFsystem_V960[AS_JPN[CA_90[CM_3[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_temp[Japan_Asahikawa_Present.csv',
]
csvfiles_2 = [
    r'TestModel_onlyGeometryForVRFsystem_V960[AS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_pmv[Japan_Asahikawa_RCP85-2100.csv',
    r'TestModel_onlyGeometryForVRFsystem_V960[AS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_pmv[Japan_Asahikawa_Present.csv',
]

totalcsv = csvfiles + csvfiles_2

z = Table(
    # todo con csvfiles_2, es decir, pmv, hay que reemplazar : por _; averiguar por qué
    datasets=csvfiles_2,
    frequency='runperiod',
    sum_or_mean='sum',
    standard_outputs=True,
    level=['block', 'building'],
    level_sum_or_mean=['sum', 'mean'],
    split_epw_names=True,
    normalised_energy_units=True,
)

# z.df.to_excel('to_be_deleted.xlsx')

# list_orig = ['block1:zone1', 'block1:zone2']
# list_under = ['block1_zone1', 'block1_zone2']
#
# for i in list_orig:
#     for j in list_under:
#         if i.replace(':', '_') in j:
#             print(f'{i} in {j}')