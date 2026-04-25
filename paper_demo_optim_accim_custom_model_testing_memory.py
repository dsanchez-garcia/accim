"""
Paper demo – Workflow 2: Multi-objective optimisation using accim custom model
==============================================================================
Parameters varied (5-dimensional search space for NSGA-II):
  · CustAST_m         – slope of the adaptive setpoint line (0.01–0.99)
  · CustAST_n         – intercept of the adaptive line (5–23 °C)
  · CustAST_ASToffset – symmetric comfort bandwidth (±offset) (1.5–5 °C)
  · CustAST_ASTall    – applicability lower limit temperature (8–16 °C)
  · CustAST_ASTaul    – applicability upper limit temperature (28–38 °C)

Objectives minimised simultaneously with NSGA-II:
  · Annual Heating:Electricity  [J]
  · Annual Cooling:Electricity  [J]

Analyses generated:
  1. Pareto front scatter, colour = ASToffset, size = slope m.
  2. Parallel coordinates plot for ALL evaluation points, coloured by
     Pareto status → reveals which parameter sub-regions concentrate
     optimal solutions.
  3. Pairwise scatter matrix (seaborn PairGrid) of parameters for
     Pareto-optimal solutions only, coloured by total energy.
  4. Summary table saved to CSV.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['figure.dpi'] = 150
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import seaborn as sns
from pandas.plotting import parallel_coordinates

import accim
from accim.parametric_and_optimisation.objectives import average_results
from accim.parametric_and_optimisation.main import OptimParamSimulation
from besos import eppy_funcs as ef


# def main():
# ---------------------------------------------------------------------------
# 1. Build the EnergyPlus model
# ---------------------------------------------------------------------------
building = ef.get_building('OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
accim.utils.set_occupancy_to_always(idf_object=building)
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

# ---------------------------------------------------------------------------
# 2. Instantiate OptimParamSimulation
# ---------------------------------------------------------------------------
parametric = OptimParamSimulation(
    building=building,
    parameters_type='accim custom model',
)

# ---------------------------------------------------------------------------
# 3. Select IDF outputs
# ---------------------------------------------------------------------------
df_vars = parametric.get_output_var_df_from_idf()
df_vars = df_vars[
    (df_vars['variable_name'].str.contains('Setpoint Temperature_No Tolerance')) |
    (df_vars['variable_name'].str.contains('Zone Operative Temperature')) |
    (df_vars['variable_name'].str.contains('Running Average Outdoor Air Temperature'))
]
parametric.set_output_var_df_to_idf(outputs_df=df_vars)
parametric.set_output_met_objects_to_idf(
    output_meters=['Heating:Electricity', 'Cooling:Electricity']
)

df_meters_ts, _ = parametric.get_outputs_df_from_testsim()
parametric.set_outputs_for_simulation(df_output_meter=df_meters_ts)

# ---------------------------------------------------------------------------
# 4. Define optimisation parameters (5-D search space)
# ---------------------------------------------------------------------------
accis_parameters = {
    'CustAST_m': (0.01, 0.99),
    'CustAST_n': (5, 23),
    'CustAST_ASToffset': (1.5, 5),
    'CustAST_ASTall': (8, 16),
    'CustAST_ASTaul': (28, 38),
}
parametric.set_parameters(accis_params_dict=accis_parameters)

# ---------------------------------------------------------------------------
# 5. Run NSGA-II optimisation
# ---------------------------------------------------------------------------
parametric.set_problem(minimize_outputs=[True, True])
parametric.run_optimisation(
    algorithm='NSGAII',
    epws=['Seville.epw'],
    out_dir='paper_optim_custom_temp_testing_6',
    evaluations=30,
    population_size=10,
    processes=6,
    keep_dirs=True
)

# ---------------------------------------------------------------------------
## 6. Post-process
# ---------------------------------------------------------------------------
df = parametric.outputs_optimisation.copy()

param_cols = ['CustAST_m', 'CustAST_n', 'CustAST_ASToffset', 'CustAST_ASTall', 'CustAST_ASTaul']
available_energy_cols = [c for c in df.columns if ':Electricity' in c]
heating_col = next((c for c in available_energy_cols if 'Heating:Electricity' in c), None)
cooling_col = next((c for c in available_energy_cols if 'Cooling:Electricity' in c), None)
if heating_col is None or cooling_col is None:
    raise KeyError(
        f'Heating/Cooling electricity columns not found. Available columns: {list(df.columns)}'
    )
energy_cols = [heating_col, cooling_col]

df['Total [J]'] = df[energy_cols].sum(axis=1)
df['Heating [kWh]'] = df[heating_col] / 3.6e6
df['Cooling [kWh]'] = df[cooling_col] / 3.6e6
df['Total [kWh]'] = df['Heating [kWh]'] + df['Cooling [kWh]']
df['pareto_str'] = df['pareto-optimal'].map({True: 'Pareto-optimal', False: 'Dominated'})
df.to_csv('results_optim_custom_recomputed.csv', index=False)

pareto = df[df['pareto-optimal']].copy()
dominated = df[~df['pareto-optimal']].copy()

# Save the paths to each simulation CSV grouped by Pareto status.
pd.DataFrame(
    {'simulation_output_csv_path': parametric.optimisation_csv_paths_non_dominated}
).to_csv('results_optim_custom_non_dominated_paths_recomputed.csv', index=False)
pd.DataFrame(
    {'simulation_output_csv_path': parametric.optimisation_csv_paths_dominated}
).to_csv('results_optim_custom_dominated_paths_recomputed.csv', index=False)
pd.DataFrame(parametric.optimisation_csv_paths_non_dominated_by_epw).to_csv(
    'results_optim_custom_non_dominated_paths_by_epw_recomputed.csv',
    index=False
)
pd.DataFrame(parametric.optimisation_csv_paths_dominated_by_epw).to_csv(
    'results_optim_custom_dominated_paths_by_epw_recomputed.csv',
    index=False
)

# New hourly functionality: expand only a subset and include outputs from file.
seville_subset = df[df['epw'] == 'Seville'].head(3).copy()
parametric.get_hourly_df_optimisation(
    df=seville_subset,
    include_file_outputs=True,
    file_source='csv',
    file_output_columns=None,
)
parametric.outputs_optimisation_hourly.to_csv('results_optim_custom_hourly_subset_recomputed.csv', index=False)

parametric.get_hourly_df_optimisation(
    include_file_outputs=True
)
parametric.outputs_optimisation_hourly.to_csv('results_optim_custom_hourly_full_recomputed.csv', index=False)

# ---------------------------------------------------------------------------
# 7. Figure 1 – Pareto front scatter
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(
    dominated['Heating [kWh]'], dominated['Cooling [kWh]'],
    c='#cccccc', alpha=0.3, s=15, label='Dominated', zorder=1
)
norm_off = Normalize(df['CustAST_ASToffset'].min(), df['CustAST_ASToffset'].max())
sc = ax.scatter(
    pareto['Heating [kWh]'], pareto['Cooling [kWh]'],
    c=pareto['CustAST_ASToffset'], cmap='RdYlGn',
    norm=norm_off,
    s=pareto['CustAST_m'] * 300, alpha=0.85,
    edgecolors='k', linewidths=0.4, zorder=3, label='Pareto-optimal'
)
fig.colorbar(sc, ax=ax, label='ASToffset (±°C comfort band)')
pf = pareto.sort_values('Heating [kWh]')
ax.plot(pf['Heating [kWh]'], pf['Cooling [kWh]'], '--', color='grey', lw=0.8, zorder=2)
ax.set_xlabel('Annual Heating Electricity (kWh)', fontsize=12)
ax.set_ylabel('Annual Cooling Electricity (kWh)', fontsize=12)
ax.set_title('NSGA-II Pareto Front – Custom Adaptive Comfort Model\n'
             'Dot size ∝ slope m  |  Colour = Comfort bandwidth (ASToffset)', fontsize=10)
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig('plot_optim_custom_pareto_recomputed.png', dpi=300, bbox_inches='tight')
plt.close()

# ---------------------------------------------------------------------------
# 8. Figure 2 – Parallel coordinates plot (all evaluations)
# ---------------------------------------------------------------------------
cols_pc = param_cols + ['pareto_str']
df_pc = df[cols_pc].copy()
df_pc_norm = df_pc.copy()
for c in param_cols:
    lo, hi = df_pc_norm[c].min(), df_pc_norm[c].max()
    df_pc_norm[c] = (df_pc_norm[c] - lo) / (hi - lo + 1e-12)

fig, ax = plt.subplots(figsize=(12, 5))
colour_map = {'Pareto-optimal': '#e63946', 'Dominated': '#adb5bd'}
for _, row in df_pc_norm.iterrows():
    colour = colour_map[row['pareto_str']]
    alpha = 0.7 if row['pareto_str'] == 'Pareto-optimal' else 0.12
    lw = 1.2 if row['pareto_str'] == 'Pareto-optimal' else 0.5
    ax.plot(range(len(param_cols)), row[param_cols].values, color=colour, alpha=alpha, lw=lw)

ax.set_xticks(range(len(param_cols)))
ax.set_xticklabels(
    ['Slope m', 'Intercept n', 'Comfort\nbandwidth\n(ASToffset)',
     'Lower appl.\nlimit (ASTall)', 'Upper appl.\nlimit (ASTaul)'],
    fontsize=9
)
ax.set_ylabel('Normalised parameter value  [0 = min, 1 = max]', fontsize=10)
ax.set_title('Parallel Coordinates – 5-D Custom Model Parameter Space\n'
             '(Red = Pareto-optimal  |  Grey = Dominated)', fontsize=11)
legend_elements = [
    Line2D([0], [0], color='#e63946', lw=1.5, label='Pareto-optimal'),
    Line2D([0], [0], color='#adb5bd', lw=1.0, label='Dominated'),
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
plt.tight_layout()
plt.savefig('plot_optim_custom_parallel_recomputed.png', dpi=300, bbox_inches='tight')
plt.close()

# ---------------------------------------------------------------------------
# 9. Figure 3 – PairGrid of Pareto-optimal solutions
# ---------------------------------------------------------------------------
norm_e = Normalize(pareto['Total [kWh]'].min(), pareto['Total [kWh]'].max())
cmap_e = cm.get_cmap('coolwarm')

def _pairplot_scatter(x, y, **kwargs):
    ax = plt.gca()
    colours = cmap_e(norm_e(pareto.loc[x.index, 'Total [kWh]'].values))
    ax.scatter(x.values, y.values, c=colours, s=30, alpha=0.8, edgecolors='k', linewidths=0.2)

def _pairplot_hist(x, **kwargs):
    plt.gca().hist(x, bins=10, color='#457b9d', alpha=0.7, edgecolor='white')

g = sns.PairGrid(pareto[param_cols + ['Total [kWh]']], vars=param_cols)
g.map_diag(_pairplot_hist)
g.map_offdiag(_pairplot_scatter)
sm = cm.ScalarMappable(cmap='coolwarm', norm=norm_e)
sm.set_array([])
cbar = g.figure.colorbar(sm, ax=g.axes, shrink=0.6, pad=0.02)
cbar.set_label('Total HVAC Energy (kWh)', fontsize=9)
g.figure.suptitle('Pairwise Parameter Space – Pareto-Optimal Solutions\n'
                  '(Colour = Total Annual HVAC Energy)', y=1.01, fontsize=11)
g.figure.savefig('plot_optim_custom_pairplot_recomputed.png', dpi=300, bbox_inches='tight')
plt.close('all')

print("Done. Outputs saved:")
print("  results_optim_custom_recomputed.csv")
print("  results_optim_custom_non_dominated_paths_recomputed.csv")
print("  results_optim_custom_dominated_paths_recomputed.csv")
print("  results_optim_custom_non_dominated_paths_by_epw_recomputed.csv")
print("  results_optim_custom_dominated_paths_by_epw_recomputed.csv")
print("  results_optim_custom_hourly_subset_recomputed.csv")
print("  results_optim_custom_hourly_full_recomputed.csv")
print("  plot_optim_custom_pareto_recomputed.png")
print("  plot_optim_custom_parallel_recomputed.png")
print("  plot_optim_custom_pairplot_recomputed.png")
print("  Full results file:", parametric.outputs_optimisation_filepath)


# if __name__ == '__main__':
#     from multiprocessing import freeze_support
#     freeze_support()
#     main()


##

sns.scatterplot(
    data=parametric.outputs_optimisation,
    x='Heating:Electricity', y='Cooling:Electricity',
    hue='pareto-optimal', palette='Set1',
    s=100, alpha=0.8, edgecolors='k', linewidths=0.2,
    legend=True,
)
plt.show()