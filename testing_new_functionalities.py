"""
Testing new functionalities – Sensitivity Analysis (Morris) + MCDM
===================================================================
This script demonstrates two new analytical capabilities added to
the OptimParamSimulation class in branch feature/analysis_methods:

  10. Sensitivity Analysis (Morris method, per EPW)
      Identifies which parameters most influence Heating and Cooling
      electricity demand. Uses Morris sampling: N*(k+1) EnergyPlus
      simulations, with N=5 trajectories and k=5 parameters → 30 runs/EPW.
      Outputs:
        · results_sa_morris_<EPW>.csv  – mu, mu*, sigma per parameter
        · plot_sa_morris_<EPW>.png     – bar chart mu* vs sigma

  11. MCDM – Best compromise solution (per EPW)
      Selects the best single design from the full set of simulations
      using two multi-criteria decision-making methods:
        · Knee Point: minimises normalised Euclidean distance to Utopia point
        · TOPSIS (equal weights): standard TOPSIS with equal weighting
        · TOPSIS (weighted 70/30): prioritises heating over cooling
      Outputs:
        · results_mcdm_best_solutions.csv
        · plot_mcdm_best_solutions.png  – all solutions + best highlighted

Note: For publication quality, increase num_samples in sampling_morris
to at least 50 (300 runs/EPW).
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['figure.dpi'] = 150
import matplotlib.pyplot as plt

import accim
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
# 5. Define the besos problem (needed for SA and MCDM)
# ---------------------------------------------------------------------------
parametric.set_problem(minimize_outputs=[True, True])

param_cols = ['CustAST_m', 'CustAST_n', 'CustAST_ASToffset', 'CustAST_ASTall', 'CustAST_ASTaul']
generated_files = []



# ---------------------------------------------------------------------------
# 10. Sensitivity Analysis (Morris) – separate results per EPW
# ---------------------------------------------------------------------------
# Morris method: N*(k+1) total runs, with k=5 parameters and N=5 trajectories
# → 5*(5+1) = 30 EnergyPlus runs per EPW (60 total for 2 EPWs).
# For publication quality, increase N to at least 50 (300 runs/EPW).

print("\n--- [10] Sensitivity Analysis (Morris) ---")

parametric.sampling_morris(num_samples=5, num_levels=4)  # 5*(5+1)=30 sims/EPW
parametric.run_parametric_simulation(
    epws=['Seville.epw', 'Sydney.epw'],
    out_dir='testing_new_functionalities',
    df=parametric.parameters_values_df,
    processes=6,
    keep_dirs=False,   # don't keep sim files for SA runs
)

epw_labels = parametric.outputs_param_simulation['epw'].unique()
sa_results_by_epw = {}

for epw_label in epw_labels:
    epw_tag = epw_label.replace(' ', '_')
    # Temporarily restrict outputs_param_simulation to this EPW so that
    # run_sensitivity_analysis picks up only the correct Y vector.
    original_df = parametric.outputs_param_simulation
    parametric.outputs_param_simulation = original_df[original_df['epw'] == epw_label].copy()

    sa_results = parametric.run_sensitivity_analysis(method='morris')
    sa_results_by_epw[epw_label] = sa_results
    parametric.outputs_param_simulation = original_df  # restore

    # Build a tidy summary DataFrame and save to CSV.
    # Morris outputs: mu (mean), mu_star (abs mean), sigma (std dev).
    rows = []
    for output_name, res in sa_results.items():
        for param, mu, mu_star, sigma in zip(
            res['names'], res['mu'], res['mu_star'], res['sigma']
        ):
            rows.append({
                'epw': epw_tag, 'output': output_name, 'parameter': param,
                'mu': round(float(mu), 4),
                'mu_star': round(float(mu_star), 4),
                'sigma': round(float(sigma), 4),
            })
    sa_df = pd.DataFrame(rows)
    fname_sa_csv = f'results_sa_morris_{epw_tag}.csv'
    sa_df.to_csv(fname_sa_csv, index=False)
    print(f"  SA results saved: {fname_sa_csv}")

    # --- Bar chart: mu_star (importance) and sigma (interactions) per output ---
    output_names_sa = list(sa_results.keys())
    n_outputs = len(output_names_sa)
    fig, axes = plt.subplots(1, n_outputs, figsize=(6 * n_outputs, 5), squeeze=False)
    for ax_idx, output_name in enumerate(output_names_sa):
        res = sa_results[output_name]
        ax_sa = axes[0][ax_idx]
        x = np.arange(len(res['names']))
        width = 0.35
        ax_sa.bar(x - width / 2, np.abs(res['mu_star']), width,
                  label='mu* (importance)', color='#457b9d', alpha=0.85)
        ax_sa.bar(x + width / 2, np.abs(res['sigma']), width,
                  label='sigma (interactions)', color='#e63946', alpha=0.85)
        ax_sa.set_xticks(x)
        ax_sa.set_xticklabels(res['names'], rotation=30, ha='right', fontsize=9)
        ax_sa.set_ylabel('Morris Index', fontsize=10)
        ax_sa.set_title(f'Morris Sensitivity — {output_name}\n[{epw_tag}]', fontsize=10)
        ax_sa.legend(fontsize=8)
        ax_sa.axhline(0, color='k', lw=0.5)
    plt.tight_layout()
    fname_sa_plot = f'plot_sa_morris_{epw_tag}.png'
    plt.savefig(fname_sa_plot, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  SA plot saved: {fname_sa_plot}")
    generated_files.append(fname_sa_plot)

# ---------------------------------------------------------------------------
# 11. MCDM – Best compromise solution, per EPW
# ---------------------------------------------------------------------------
# For this test, MCDM is applied to the parametric simulation results
# (treating all rows as Pareto-optimal, since no real optimisation was run).
# In a real workflow, load outputs_optimisation from run_optimisation().
print("\n--- [11] MCDM – Best Compromise Solution ---")

# Build a minimal outputs_optimisation from the parametric SA results.
# We mark all rows as 'pareto-optimal' for demonstration purposes.
param_sim_df = parametric.outputs_param_simulation.copy()
param_sim_df['pareto-optimal'] = True
parametric.outputs_optimisation = param_sim_df

# Detect heating/cooling column names from results.
available_energy_cols = [c for c in param_sim_df.columns if ':Electricity' in c]
heating_col = next((c for c in available_energy_cols if 'Heating:Electricity' in c), None)
cooling_col = next((c for c in available_energy_cols if 'Cooling:Electricity' in c), None)
if heating_col is None or cooling_col is None:
    raise KeyError(
        f'Heating/Cooling electricity columns not found. Available: {list(param_sim_df.columns)}'
    )

epw_labels = param_sim_df['epw'].unique()
all_mcdm_rows = []

for epw_label in epw_labels:
    epw_tag = epw_label.replace(' ', '_')

    # Restrict outputs_optimisation to this EPW for per-EPW MCDM.
    original_optim = parametric.outputs_optimisation
    parametric.outputs_optimisation = original_optim[original_optim['epw'] == epw_label].copy()

    # --- Knee Point (equal weighting implicit, minimise distance to Utopia) ---
    best_knee = parametric.get_best_compromise_solution(method='knee_point')
    best_knee['mcdm_method'] = 'knee_point'
    best_knee['epw'] = epw_tag

    # --- TOPSIS with equal weights ---
    best_topsis_eq = parametric.get_best_compromise_solution(method='topsis')
    best_topsis_eq['mcdm_method'] = 'topsis_equal'
    best_topsis_eq['epw'] = epw_tag

    # --- TOPSIS with custom weights: 70% heating, 30% cooling ---
    best_topsis_w = parametric.get_best_compromise_solution(
        method='topsis', weights=[0.7, 0.3]
    )
    best_topsis_w['mcdm_method'] = 'topsis_w70_30'
    best_topsis_w['epw'] = epw_tag

    parametric.outputs_optimisation = original_optim  # restore

    all_mcdm_rows.extend([best_knee, best_topsis_eq, best_topsis_w])

    # Print summary to console
    print(f"\n  [{epw_tag}] Best compromise solutions:")
    for row_df in [best_knee, best_topsis_eq, best_topsis_w]:
        method_label = row_df['mcdm_method'].iloc[0]
        h_col = next(c for c in row_df.columns if 'Heating:Electricity' in c)
        c_col = next(c for c in row_df.columns if 'Cooling:Electricity' in c)
        h_kwh = row_df[h_col].iloc[0] / 3.6e6
        c_kwh = row_df[c_col].iloc[0] / 3.6e6
        print(f"    {method_label:20s} | Heating={h_kwh:.1f} kWh | Cooling={c_kwh:.1f} kWh "
              f"| m={row_df['CustAST_m'].iloc[0]:.3f} "
              f"| n={row_df['CustAST_n'].iloc[0]:.2f} "
              f"| offset={row_df['CustAST_ASToffset'].iloc[0]:.2f}")

# Save combined MCDM table
mcdm_df = pd.concat(all_mcdm_rows, ignore_index=True)
mcdm_df.to_csv('results_mcdm_best_solutions.csv', index=False)
print("\n  MCDM summary saved: results_mcdm_best_solutions.csv")

# --- Figure: best solution highlighted on each EPW Pareto scatter ---
fig, axes = plt.subplots(1, len(epw_labels), figsize=(8 * len(epw_labels), 6), squeeze=False)
for ax_idx, epw_label in enumerate(epw_labels):
    epw_tag = epw_label.replace(' ', '_')
    ax_m = axes[0][ax_idx]
    df_epw = parametric.outputs_optimisation[parametric.outputs_optimisation['epw'] == epw_label].copy()
    df_epw['Heating [kWh]'] = df_epw[heating_col] / 3.6e6
    df_epw['Cooling [kWh]'] = df_epw[cooling_col] / 3.6e6

    # Plot dominated / Pareto background
    dom = df_epw[~df_epw['pareto-optimal']]
    par = df_epw[df_epw['pareto-optimal']]
    ax_m.scatter(dom['Heating [kWh]'], dom['Cooling [kWh]'], c='#cccccc', alpha=0.3, s=15, zorder=1)
    ax_m.scatter(par['Heating [kWh]'], par['Cooling [kWh]'], c='#457b9d', alpha=0.6, s=40,
                 edgecolors='k', linewidths=0.4, zorder=2, label='Pareto-optimal')

    # Overlay MCDM solutions
    mcdm_markers = {
        'knee_point':    ('*', '#e63946', 220, 'Knee Point'),
        'topsis_equal':  ('D', '#f4a261', 120, 'TOPSIS (equal)'),
        'topsis_w70_30': ('s', '#2a9d8f', 120, 'TOPSIS (70/30)'),
    }
    for mcdm_method, (marker, colour, size, label) in mcdm_markers.items():
        row = mcdm_df[(mcdm_df['epw'] == epw_tag) & (mcdm_df['mcdm_method'] == mcdm_method)]
        if row.empty:
            continue
        h = row[heating_col].iloc[0] / 3.6e6
        c = row[cooling_col].iloc[0] / 3.6e6
        ax_m.scatter(h, c, marker=marker, c=colour, s=size, zorder=5,
                     edgecolors='k', linewidths=0.6, label=label)

    ax_m.set_xlabel('Heating Electricity (kWh)', fontsize=11)
    ax_m.set_ylabel('Cooling Electricity (kWh)', fontsize=11)
    ax_m.set_title(f'Pareto Front + MCDM best solutions\n[{epw_tag}]', fontsize=11)
    ax_m.legend(fontsize=9)

plt.tight_layout()
fname_mcdm_plot = 'plot_mcdm_best_solutions.png'
plt.savefig(fname_mcdm_plot, dpi=300, bbox_inches='tight')
plt.close()
print(f"  MCDM plot saved: {fname_mcdm_plot}")
generated_files.append(fname_mcdm_plot)

# if __name__ == '__main__':
#     from multiprocessing import freeze_support
#     freeze_support()
#     main()
