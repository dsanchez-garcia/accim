

from accim.data.datawrangling import Table
dataset_runperiod = Table(
    source_frequency='hourly',
    frequency='runperiod',
    frequency_agg_func='sum',
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    level_excluded_zones=[],
    split_epw_names=True,
)


# dataset_runperiod.df.to_excel('using_Table_00.xlsx')
dataset_runperiod.df.shape
dataset_runperiod.df.columns

dataset_runperiod.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
        'Building_Total_Total Energy Demand (kWh/m2) (summed)'
    ]
)
print(*dataset_runperiod.df.columns, sep='\n')


# dataset_runperiod.df.to_excel('using_Table_01.xlsx')
# print(*dataset_runperiod.df.columns, sep='\n')
# In this case, we are going to use the 'pivot' reshaping option:

# In[ ]:


for i in ['pivot', 'stack', 'unstack', 'multiindex']:
    dataset_runperiod.wrangled_table(
        reshaping=i,
        vars_to_gather=['ComfMod'],
        # check_index_and_cols=True,
        baseline='CM_3',
        vars_to_keep=['EPW_City_or_subcountry'],
        comparison_mode=[
            'others compared to baseline',
            'baseline compared to others'
        ],
        comparison_cols=['relative', 'absolute'],
        rename_dict={
            'CM_0': 'Static',
            'CM_3': 'Adaptive'
        },
        excel_filename='testing_accim'
    )

# dataset_runperiod.wrangled_table(
#     reshaping='pivot',
#     # vars_to_gather=['EPW_City_or_subcountry', 'ComfMod'],
#     vars_to_gather=['ComfMod'],
#     check_index_and_cols=True,
#     baseline='CM_3',
#     comparison_mode=['others compared to baseline', 'baseline compared to others'],
#     comparison_cols=['relative', 'absolute'],
#     rename_dict={'CM_0': 'Static', 'CM_3': 'Adaptive'},
#     # excel_filename='whatever'
# )

# dataset_runperiod.wrangled_table(
#     reshaping='unstack',
#     vars_to_gather=['ComfMod'],
#     # check_index_and_cols=True,
#     # baseline='CM_0[CA_1',
#     comparison_mode='baseline compared to others',
#     comparison_cols=['relative', 'absolute'],
#     rename_dict={'CM_0': 'Static', 'CM_3': 'Adaptive', 'London': 'whatever'}
# )

dataset_runperiod.wrangled_df_unstacked.to_excel('temp3.xlsx')