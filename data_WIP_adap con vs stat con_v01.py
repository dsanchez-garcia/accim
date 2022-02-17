##

from accim.data.datawrangling import Table
import matplotlib.pyplot as plt
import time
start = time.time()

# making df
z = Table(frequency='hourly',
          sum_or_mean='sum',
          standard_outputs=True,
          level=['building'],
          level_sum_or_mean=['sum'],
          match_cities=False,
          normalised_energy_units=True,
          rename_cols=True,
          energy_units_in_kwh=True,
          )

# print(f'The number of columns and the list of these is going to be:')
# print(f'No. of columns = {len(list(set(z.df.Source)))}')
# print(f'List of columns:')
# print(*list(set(z.df.Source)), sep='\n')
#
# print(f'The number of rows and the list of these is going to be:')
# print(f'No. of rows = {len(list(set(z.df.Source)))}')

print(*z.df.columns, sep='\n')

# z.hvac_zone_list
# z.occupied_zone_list
# z.block_list

temp_list = []
# for col in z.df.columns:
#     for zone in z.occupied_zone_list:
#         if zone in col and 'Zone Thermostat Operative Temperature' in col:
#             temp_list.append(col)

additional_list = [
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]

custom_cols_list = temp_list + additional_list

z.format_table(type_of_table='custom',
               custom_cols=custom_cols_list,
               manage_epw_names=False
               )
##

self.df_for_graph = z.df.copy()

self.df_for_graph['col_to_gather_in_cols'] = self.df_for_graph[['Adaptive Standard', 'Category']].agg('['.join, axis=1)
self.df_for_graph['col_to_gather_in_rows'] = self.df_for_graph['EPW']

all_cols = list(set(self.df_for_graph['col_to_gather_in_cols']))
rows = list(set(self.df_for_graph['col_to_gather_in_rows']))

all_cols.sort()
rows.sort()

# todo argument
baseline = 'AS_CTE[CA_X'

cols = [x for x in all_cols if x not in set([baseline])]


self.df_for_graph['col_to_unstack'] = self.df_for_graph[['col_to_gather_in_cols', 'col_to_gather_in_rows']].agg('['.join, axis=1)

self.df_for_graph = self.df_for_graph.drop(
    columns=[
    'Model',
    'Adaptive Standard',
    'Category',
    'Comfort mode',
    'HVAC mode',
    'Ventilation control',
    'VSToffset',
    'MinOToffset',
    'MaxWindSpeed',
    'ASTtol',
    'Source',
    'EPW',
    'col_to_gather_in_cols',
    'col_to_gather_in_rows']
)

# todo daily and monthly cloud as well; extend based on frequency
multi_index = [
    'Month',
    'Day',
    'Hour',
    'col_to_unstack'
]


self.df_for_graph.set_index(multi_index, inplace=True)

self.df_for_graph = self.df_for_graph.unstack('col_to_unstack')

self.df_for_graph.columns = self.df_for_graph.columns.map('['.join)

# todo argument
datasets = [
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]

# making lists for figure
x_list = []
for i in range(len(rows)):
    temp_row = []
    for j in range(len(cols)):
        temp = [
            [i, j],
            f'{rows[i]}_{cols[j]}',
            [
                self.df_for_graph[[x for x in self.df_for_graph.columns if rows[i] in x and baseline in x and dataset in x]]
                for dataset in datasets
            ]
        ]
        temp_row.append(temp)
    x_list.append(temp_row)



y_list = []
for i in range(len(rows)):
    temp_row = []
    for j in range(len(cols)):
        temp = [
            [i, j],
            f'{rows[i]}_{cols[j]}',
            [
                self.df_for_graph[[x for x in self.df_for_graph.columns if rows[i] in x and cols[j] in x and dataset in x]]
                for dataset in datasets
            ],
            [dataset for dataset in datasets]
        ]
        temp_row.append(temp)
    y_list.append(temp_row)

#todo argument
s=4

fig, ax = plt.subplots(nrows=len(rows),
                       ncols=len(cols),
                       sharex=True,
                       sharey=True,
                       constrained_layout=True,
                       figsize=(s*len(cols), s*len(rows)))



# y_list_main_scatter
for i in range(len(rows)):
    for j in range(len(cols)):
        # ax[i, j].set_title(f'{rows[i]} / {cols[j]}')
        ax[i, j].grid(True, linestyle='-.')
        ax[i, j].tick_params(axis='both',
                             grid_color='black',
                             grid_alpha=0.5)
        ax[i, j].set_facecolor((0, 0, 0, 0.10))
        for k in range(len(x_list[i][j][2])):
            if i == 0 and j == 0:
                ax[i, j].scatter(
                    x_list[i][j][2][k],
                    y_list[i][j][2][k],
                    # todo include colors from list in argument
                    # c=data_dict[x][y],
                    s=1,
                    marker='o',
                    alpha=0.5,
                    label=y_list[i][j][3][k]
                )
            else:
                ax[i, j].scatter(
                    x_list[i][j][2][k],
                    y_list[i][j][2][k],
                    # c=data_dict[x][y],
                    s=1,
                    marker='o',
                    alpha=0.5,
                )

for i in range(len(rows)):
    ax[i, 0].set_ylabel(rows[i], rotation=90, size='large')

for j in range(len(cols)):
    ax[0, j].set_title(cols[j])

supx = fig.supxlabel('Static energy demand')
supy = fig.supylabel('Adaptive energy demand')

leg = fig.legend(
    bbox_to_anchor=(0.5, 0),
    loc='upper center',
    fontsize='large'
    # borderaxespad=0.1,
)

for i in range(len(leg.legendHandles)):
    leg.legendHandles[i]._sizes = [30]

# plt.subplots_adjust(
#     # bottom=0.2,
#     left=0.05
# )



# plt.tight_layout()


plt.savefig('temp_fig_adap vs stat en dem_3.png',
            dpi=1200,
            format='png',
            bbox_extra_artists=(leg, supx, supy),
            bbox_inches='tight'
            )


##

end = time.time()
print(end-start)