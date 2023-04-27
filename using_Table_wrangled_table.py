

from accim.data.datawrangling import Table
dataset_runperiod = Table(
    #datasets=list Since we are not specifying any list, it will use all available CSVs in the folder
    source_frequency='hourly',
    frequency='runperiod',
    frequency_agg_func='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    level_excluded_zones=[],
    #match_cities=bool Only used when EPW file has NOT been previously renamed
    #manage_epw_names=bool Only used when EPW file has NOT been previously renamed
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
)

# dataset_runperiod.df.to_excel('using_Table_00.xlsx')
# dataset_runperiod.df.shape

dataset_runperiod.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ]
)


# In this case, we are going to use the 'pivot' reshaping option:

# In[ ]:


# for i in ['pivot', 'stack', 'unstack', 'multiindex']:
#     dataset_runperiod.wrangled_table(
#         reshaping=i,
#         vars_to_gather=['ComfMod'],
#         check_index_and_cols=True,
#         # baseline='CM_0[CA_1',
#         comparison_mode='baseline compared to others',
#         comparison_cols=['relative', 'absolute']
#     )

dataset_runperiod.wrangled_table(
    reshaping='pivot',
    # vars_to_gather=['EPW_City_or_subcountry', 'ComfMod'],
    vars_to_gather=['ComfMod'],
    check_index_and_cols=True,
    # baseline='CM_0[CA_1',
    comparison_mode='baseline compared to others',
    comparison_cols=['relative', 'absolute']
)

# dataset_runperiod.wrangled_table(
#     reshaping='unstack',
#     vars_to_gather=['ComfMod'],
#     check_index_and_cols=True,
#     # baseline='CM_0[CA_1',
#     comparison_mode='baseline compared to others',
#     comparison_cols=['relative', 'absolute']
# )
