"""Experiment 4.5 - OptimisationSimulation with 'apmv setpoints' (Table 5). v2

Requires accim >= 0.8.0. Interactive execution.

Objectives (both minimised):
- E: HVAC electricity ('Electricity:HVAC' meter, hourly values summed).
- D: 'Discomfortable Total Hours' - the aPMV framework's own EMS hour counter
  (per-timestep increments, 'Summed' type), so the default sum reducer yields
  annual discomfort hours. The model has a SINGLE zone (PLANTAX08:OFFICE), so
  one per-zone counter covers the whole building; with more than one zone the
  per-zone counters would have to be summed into a single value to minimise.

CAVEAT (see paper Section 2.3): this counter compares aPMV against the
aPMV_C/H_SP_noTol setpoints, which move with the optimised 'PMV setpoint'
variable - i.e. the comfort reference is not fully independent of the decision
space. If the resulting front collapses towards the widest PMV setpoint,
consider fixing 'PMV setpoint' (optimising only the lambdas) or reverting to
an external metric (article_objectives.add_mean_abs_pmv_ems).

NOTE (Windows multiprocessing): run_optimisation() parallelises EnergyPlus
runs with ProcessPoolExecutor. On Windows (start method 'spawn') every
worker process re-imports this file as a fresh module, so all top-level code
must live inside `if __name__ == '__main__':` - otherwise each worker tries
to re-run the whole script (including spawning more workers) before
finishing its own bootstrap, raising a RuntimeError about starting a new
process before the current process has finished its bootstrapping phase.
See https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
"""

import multiprocessing

import matplotlib
matplotlib.use('Agg')  # non-interactive backend: avoids Tk image-buffer/
                       # memory errors when generating many/large figures
                       # unattended (no display needed to save PNGs to disk).

import pandas as pd
from besos import eppy_funcs as ef
from accim.sim.apmv_setpoints import add_vrf_system
from accim.parametric_and_optimisation.main import OptimisationSimulation
from accim.utils import remove_accents_in_idf


def main():
    IDF = 'ALJARAFE CENTER_onlyGeometry.idf'
    EPWS = ['Seville_Present.epw', 'Seville_ssp585_2080.epw']   # present + worst case

    remove_accents_in_idf(IDF)
    building = ef.get_building(IDF)
    add_vrf_system(building, eer=4.42, cop=4.95)   # validated VRF + Fanger comfort fields

    opt = OptimisationSimulation(
        buildings=[building],
        epws=EPWS,
        parameters_type='apmv setpoints',   # runs apply_apmv_setpoints on init
        output_freqs=['hourly'],
    )

    # Exact per-zone EMS counter name (suffix = sanitized zone+People names),
    # derived from the transformed model so it also works with other IDFs.
    DISCOMF_VAR = [v.Name for v in building.idfobjects['EnergyManagementSystem:OutputVariable']
                   if v.Name.startswith('Discomfortable Total Hours')][0]
    DISCOMF_VAR   # inspect

    opt.set_category_mapping(epw_mapping_rules={'scenario': {
        'present': 'Present',
        'ssp585-2080': 'ssp585_2080',
    }})

    meters = pd.DataFrame([
        {'key_name': 'Electricity:HVAC', 'frequency': 'Hourly', 'name': 'HVAC electricity (J)'},
    ])
    # apply_apmv_setpoints already injects the Output:Variable requests for its
    # EMS counters, so only the meter needs to be added to the IDF.
    objective_variables = pd.DataFrame([
        {'key_value': 'EMS', 'variable_name': DISCOMF_VAR, 'frequency': 'Hourly',
         'name': 'Discomfort hours (h)'},   # default reducer: sum -> annual hours
    ])

    # refresh=True: force a fresh RDD/MDD discovery for THIS model. Without it,
    # discover_available_outputs() silently reuses any pre-existing
    # 'available_outputs/eplusout.rdd' left on disk by a DIFFERENT script/model
    # (all exp_4_* scripts share this repo as their working directory), which
    # can make model-specific EMS output variables (like the per-zone
    # 'Discomfortable Total Hours_<suffix>') look "not available" even though
    # they exist in this model.
    opt.discover_available_outputs(prefer='rdd_mdd', keep_available_outputs=True, refresh=True)
    opt.set_output_meters_to_idf(df_output_meter=meters, idf_scope='all', validate=True, mode='append')
    opt.set_outputs_for_simulation(df_output_meter=meters, df_output_variable=objective_variables)

    # Design space (Table 5, experiment 4.5)
    opt.set_parameters(accis_params_dict={
        'Adaptive cooling coefficient': (0, 1),
        'Adaptive heating coefficient': (-1, 0),
        'PMV setpoint': (0.2, 0.9),
    })
    opt.set_problem(minimize_outputs=[True, True])   # min [E, D]

    opt.estimate_optimisation_sims(evaluations=200, population_size=20, epws=EPWS)  # 200/EPW -> 400

    opt.run_optimisation(
        algorithm='NSGAII',
        epws=EPWS,
        out_dir='results_exp_4_5_optim_apmv',
        evaluations=200,
        population_size=20,
        processes=2,
        keep_sim_files='non-dominated',
        sim_files_extensions=['.csv'],
        pareto_separate_by_epw=True,
        checkpoint_every_case=True,
        resume_from_checkpoint=True,
        export_summary_json=True,
    )

    # =========================================================================
    # POST-PROCESSING: tables and figures
    # Run after the optimisation finishes. In a fresh session, re-run the setup
    # lines above and call run_optimisation again with
    # resume_from_checkpoint=True: completed IDF x EPW cases are reused.
    # =========================================================================

    PLOTS_DIR = 'results_exp_4_5_optim_apmv/plots'

    # --- Tables --------------------------------------------------------------
    opt.set_building_floor_area(mode='all')   # for the paper, switch to the
                                              # conditioned-area mode (312 m2)
    opt.normalize_outputs(df_types=['optimisation'])

    results_opt = opt.outputs_optimisation
    results_opt.head()                        # inspect columns (objectives,
                                              # parameters, Pareto annotation)

    results_opt.to_csv('results_exp_4_5_optim_apmv/table_evaluations.csv', index=False)

    opt.get_best_compromise_solution(method='topsis').to_csv(
        'results_exp_4_5_optim_apmv/table_best_compromise_topsis.csv', index=False)
    opt.get_best_compromise_solution(method='knee_point').to_csv(
        'results_exp_4_5_optim_apmv/table_best_compromise_knee.csv', index=False)

    # --- Figures --------------------------------------------------------------
    # Pareto front coloured by the PMV setpoint: this doubles as the degeneracy
    # diagnostic of the docstring caveat - if the colour gradient aligns with the
    # front (widest setpoint dominating both objectives), the comfort reference
    # is being gamed and 'PMV setpoint' should be fixed out of the design space.
    opt.plot_pareto_front(
        color_by='PMV setpoint',
        normalize_per_m2=True, out_dir=PLOTS_DIR)

    opt.plot_parallel_coordinates(out_dir=PLOTS_DIR)

    opt.plot_best_compromise_solutions(
        separate_by_epw=True, normalize_per_m2=True, out_dir=PLOTS_DIR)

    return opt


if __name__ == '__main__':
    multiprocessing.freeze_support()
    opt = main()

