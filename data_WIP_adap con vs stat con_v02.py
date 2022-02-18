##

from accim.data.datawrangling import Table
import matplotlib.pyplot as plt
import time
start = time.time()

# making df
z = Table(frequency='daily',
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
# todo argument
datasets = [
    'Building_Total_Cooling Energy Demand (kWh/m2) [summed]',
    'Building_Total_Heating Energy Demand (kWh/m2) [summed]',
]
colorlist = [
    'b',
    'r'
]

df_for_graph = z.df.copy()

df_for_graph['col_to_gather_in_cols'] = df_for_graph[['Adaptive Standard', 'Category']].agg('['.join, axis=1)
df_for_graph['col_to_gather_in_rows'] = df_for_graph['EPW']

all_cols = list(set(df_for_graph['col_to_gather_in_cols']))
rows = list(set(df_for_graph['col_to_gather_in_rows']))

all_cols.sort()
rows.sort()

# todo argument
baseline = 'AS_CTE[CA_X'

cols = [x for x in all_cols if x not in set([baseline])]

df_for_graph['col_to_unstack'] = df_for_graph[['col_to_gather_in_cols', 'col_to_gather_in_rows']].agg('['.join, axis=1)

df_for_graph = df_for_graph.drop(
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
# todo argument
frequency = 'daily'

multi_index = [
    # 'Month',
    # 'Day',
    # 'Hour',
    'col_to_unstack'
]
if 'monthly' in frequency:
    multi_index.append('Month')
if 'daily' in frequency:
    multi_index.extend(['Month', 'Day'])
if 'hourly' in frequency:
    multi_index.extend(['Month', 'Day', 'Hour'])
if 'timestep' in frequency:
    multi_index.extend(['Month', 'Day', 'Hour', 'Minute'])

df_for_graph.set_index(multi_index, inplace=True)

max_value = max([df_for_graph[dataset].max() for dataset in datasets])

df_for_graph['Building_Total_Cooling Energy Demand (kWh/m2) [summed]'].max()

df_for_graph = df_for_graph.unstack('col_to_unstack')

df_for_graph.columns = df_for_graph.columns.map('['.join)


# making lists for figure
x_list = []
for i in range(len(rows)):
    temp_row = []
    for j in range(len(cols)):
        temp = [
            [i, j],
            f'{rows[i]}_{cols[j]}',
            [
                df_for_graph[[x for x in df_for_graph.columns if rows[i] in x and baseline in x and dataset in x]]
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
                df_for_graph[[x for x in df_for_graph.columns if rows[i] in x and cols[j] in x and dataset in x]]
                for dataset in datasets
            ],
            [dataset for dataset in datasets],
            [color for color in colorlist]
        ]
        temp_row.append(temp)
    y_list.append(temp_row)

#todo argument
s=2
import numpy as np
fig, ax = plt.subplots(nrows=len(rows),
                       ncols=len(cols),
                       sharex=True,
                       sharey=True,
                       constrained_layout=True,
                       figsize=(s*len(cols), s*len(rows)))
import matplotlib.lines as lines
# y_list_main_scatter
for i in range(len(rows)):
    for j in range(len(cols)):
        # ax[i, j].set_title(f'{rows[i]} / {cols[j]}')
        # ax[i, j].set_aspect('equal')
        # ax[i, j].axis('equal')
        ax[i, j].grid(True,
                      linestyle='-.',
                      which='both',
                      axis='both'
                      )
        # not working
        # ax[i, j].set_yticks(np.linspace(ax[i, j].get_yticks()[0], ax[i, j].get_yticks()[-1], len(ax[i, j].get_yticks())))
        ax[i, j].tick_params(axis='both',
                             grid_color='black',
                             grid_alpha=0.5)
        ax[i, j].set_facecolor((0, 0, 0, 0.10))
        # lines
        ax[i, j].add_artist((lines.Line2D(
            [0, max_value], [0, max_value],
            dashes=(2, 2, 2, 2),
            linewidth=1,
            color='gray'
            )))
        ax[i, j].add_artist((lines.Line2D(
            [0, max_value/2], [0, max_value],
            dashes=(2, 2, 2, 2),
            linewidth=1,
            color='gray'
            )))
        ax[i, j].add_artist((lines.Line2D(
            [0, max_value/4], [0, max_value],
            dashes=(2, 2, 2, 2),
            linewidth=1,
            color='gray'
            )))

        for k in range(len(x_list[i][j][2])):
            if i == 0 and j == 0:
                ax[i, j].scatter(
                    x_list[i][j][2][k],
                    y_list[i][j][2][k],
                    c=y_list[i][j][4][k],
                    s=1,
                    marker='o',
                    alpha=0.5,
                    label=y_list[i][j][3][k]
                )
            else:
                ax[i, j].scatter(
                    x_list[i][j][2][k],
                    y_list[i][j][2][k],
                    c=y_list[i][j][4][k],
                    s=1,
                    marker='o',
                    alpha=0.5,
                )
        # ax[i, j].set_box_aspect(1)
        # ax[i, j].set(adjustable='box', aspect='equal')
        # ax[i, j].set_aspect('equal', share=True)
        ax[i, j].set_ylim((0, max_value))
        ax[i, j].set_xlim((0, max_value))


ax[0, 0].set_aspect('equal',
                    # adjustable='box',
                    share=True)

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


plt.savefig('temp_fig_adap vs stat en dem_daily.png',
            dpi=1200,
            format='png',
            bbox_extra_artists=(leg, supx, supy),
            bbox_inches='tight'
            )


##

end = time.time()
print(end-start)