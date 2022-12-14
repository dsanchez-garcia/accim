# from accim.data.datawrangling import genCSVconcatenated, Table
# import os
# x = genCSVconcatenated(
#     frequency='runperiod',
#     datasets_per_chunk=2,
#     concatenated_csv_name='testing'
# )
#
# x = Table(
#     source_concatenated_csv_filepath='testing[freq-runperiod[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
#     level=['building'],
#     level_sum_or_mean=['sum'],
#     match_cities=False,
#     manage_epw_names=True,
#     split_epw_names=True,
#     normalised_energy_units=True,
#     rename_cols=True,
#     energy_units_in_kwh=True,
#     drop_nan=True
# )

##
from accim.data.datawrangling import Table

# todo continue testing

x = Table(
    # path=r'/tests_data_run_sim/testing_CSVs',
    source_frequency='runperiod',
    frequency='runperiod',
    frequency_sum_or_mean='sum',
    standard_outputs=True,
    level=['block', 'building'],
    level_sum_or_mean=['sum'],
    match_cities=False,
    manage_epw_names=False,
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
    drop_nan=True
)

# x.df.to_excel('freqs_fin_source_runperiod_agg_runperiod.xlsx')
# print(*x.df.columns, sep='\n')

##

# cols = x.df.columns
# num_cols = x.df._get_numeric_data().columns.to_list()
# num_cols.remove('count')
# cat_cols = list(set(cols) - set(num_cols))
#
# num_cols = sorted(num_cols)
#
#
#
# df = x.df.copy()
# df_rearranged = df.copy()
# # df_rearranged = df_rearranged[cat_cols] + df_rearranged[num_cols]
#
# # df_rearranged = df_rearranged.reindex(columns=cat_cols+num_cols)
#
# df_rearranged = df_rearranged[cat_cols+num_cols]
#
# cols_model =[
#     'Source',
#     'Model',
#     'ComfStand',
#     'Category',
#     'ComfMod',
#     'HVACmode',
#     'VentCtrl',
#     'VSToffset',
#     'MinOToffset',
#     'MaxWindSpeed',
#     'ASTtol',
#     'NameSuffix',
#     'count',
#     'EPW',
# ]
#
# cols_epw = [
#     'EPW_Country_name',
#     'EPW_City_or_subcountry',
#     'EPW_Scenario',
#     'EPW_Year',
#     'EPW_Scenario-Year',
# ]
#
# cols_date = [
#     'Month',
#     'Month/Day',
#     'Day',
#     'Date/Time',
# ]
#
# # x.df.to_excel('temp.xlsx')
# # import os
# # os.listdir('tests_data_run_sim/testing_CSVs')
# # os.listdir()
#
# #
# # import glob
# # glob.glob('tests_data_run_sim/testing_CSVs')
#
#
# fixed_columns = [
#     'Model',
#     'ComfStand',
#     'Category',
#     'ComfMod',
#     'HVACmode',
#     'VentCtrl',
#     'VSToffset',
#     'MinOToffset',
#     'MaxWindSpeed',
#     'ASTtol',
#     'NameSuffix',
#     'EPW'
# ]
#
# cols_model = ['Source'] + fixed_columns
#
