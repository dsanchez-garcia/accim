"""Experiment 4.4 - OptimisationSimulation with 'accim custom model' (Table 5).

Requires accim >= 0.8.0 and the companion module article_objectives.py in the
working directory. Interactive execution.

Objectives (both minimised):
- E: HVAC electricity ('Electricity:HVAC' meter, hourly values summed).
- D: EN 16798-1 Cat II discomfort degree-hours, computed INSIDE EnergyPlus by
  an injected EMS program (zone-averaged operative temperature vs the Cat II
  adaptive limits with clamped running mean). The reference is FIXED and
  independent of the optimised parameters, avoiding the degenerate optimum
  discussed in paper Section 2.3 (an ACCIS-based discomfort count would be
  measured against the very setpoints being optimised).

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
from accim.parametric_and_optimisation.main import OptimisationSimulation
from accim.utils import remove_accents_in_idf
from article_objectives import add_en16798_discomfort_ems, EN16798_DH_OUTPUT


def main():
    IDF = 'ALJARAFE CENTER_onlyGeometry.idf'
    EPWS = ['Seville_Present.epw', 'Seville_ssp585_2080.epw']   # present + worst case

    remove_accents_in_idf(IDF)
    building = ef.get_building(IDF)

    opt = OptimisationSimulation(
        buildings=[building],
        epws=EPWS,
        parameters_type='accim custom model',
        ScriptType='vrf_ac',
        output_type='simplified',
        output_freqs=['hourly'],
        eer=4.42,
        cop=4.95,
    )

    # EMS-computed comfort objective (uses the RMOT sensor injected by ACCIS)
    add_en16798_discomfort_ems(building, category=2)

    opt.set_category_mapping(epw_mapping_rules={'scenario': {
        'present': 'Present',
        'ssp585-2080': 'ssp585_2080',
    }})

    meters = pd.DataFrame([
        {'key_name': 'Electricity:HVAC', 'frequency': 'Hourly', 'name': 'HVAC electricity (J)'},
    ])
    objective_variables = pd.DataFrame([
        # sum of hourly exceedance (C) -> annual degree-hours; sum is the default reducer
        {'key_value': 'EMS', 'variable_name': EN16798_DH_OUTPUT, 'frequency': 'Hourly',
         'name': 'EN16798 CatII discomfort (Ch)'},
    ])
    requested_variables = pd.DataFrame([
        {'key_value': '*', 'variable_name': EN16798_DH_OUTPUT, 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Zone Operative Temperature', 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Adaptive Cooling Setpoint Temperature_No Tolerance', 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Adaptive Heating Setpoint Temperature_No Tolerance', 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature', 'frequency': 'Hourly'},
    ])

    # refresh=True: force a fresh RDD/MDD discovery for THIS model. Without it,
    # discover_available_outputs() silently reuses any pre-existing
    # 'available_outputs/eplusout.rdd' left on disk by a DIFFERENT script/model
    # (all exp_4_* scripts share this repo as their working directory), which
    # can make custom EMS output variables (like article_objectives'
    # EN16798_DH_OUTPUT) look "not available" and get silently dropped by
    # set_output_variables_to_idf(validate=True) even though they DO exist in
    # this model.
    opt.discover_available_outputs(prefer='rdd_mdd', keep_available_outputs=True, refresh=True)
    opt.set_output_variables_to_idf(df_output_variable=requested_variables, idf_scope='all', validate=True, mode='replace')
    opt.set_output_meters_to_idf(df_output_meter=meters, idf_scope='all', validate=True, mode='replace')
    opt.set_outputs_for_simulation(df_output_meter=meters, df_output_variable=objective_variables)

    # Design space (Table 5, experiment 4.4): same domains as 4.2, as ranges
    opt.set_parameters(accis_params_dict={
        'CustAST_m': (0, 0.7),
        'CustAST_n': (5, 22.5),
        'CustAST_ASToffset': (1, 5),
        'CustAST_ASTaul': (22, 40),
    })
    opt.set_problem(minimize_outputs=[True, True])   # min [E, D]

    opt.estimate_optimisation_sims(evaluations=200, population_size=20, epws=EPWS)  # 200/EPW -> 400

    opt.run_optimisation(
        algorithm='NSGAII',
        epws=EPWS,
        out_dir='results_exp_4_4_optim_custom',
        evaluations=200,
        population_size=20,
        processes=2,
        keep_sim_files='non-dominated',   # prune dominated run folders in batches
        sim_files_extensions=['.csv'],    # policy 'keep': hourly data on disk only
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

    PLOTS_DIR = 'results_exp_4_4_optim_custom/plots'

    # --- Tables --------------------------------------------------------------
    opt.set_building_floor_area(mode='all')   # for the paper, switch to the
                                              # conditioned-area mode (312 m2)
    opt.normalize_outputs(df_types=['optimisation'])

    results_opt = opt.outputs_optimisation
    results_opt.head()                        # inspect columns (objectives,
                                              # parameters, Pareto annotation)

    results_opt.to_csv('results_exp_4_4_optim_custom/table_evaluations.csv', index=False)

    # Best-compromise solutions on the front (Section 2.5: decision support)
    opt.get_best_compromise_solution(method='topsis').to_csv(
        'results_exp_4_4_optim_custom/table_best_compromise_topsis.csv', index=False)
    opt.get_best_compromise_solution(method='knee_point').to_csv(
        'results_exp_4_4_optim_custom/table_best_compromise_knee.csv', index=False)

    # --- Figures --------------------------------------------------------------
    # Pareto front (objectives taken from the problem; fronts per EPW as set by
    # pareto_separate_by_epw=True). Coloured by the dominant parameter of the
    # Energy 2025 study.
    opt.plot_pareto_front(
        color_by='CustAST_ASToffset',
        normalize_per_m2=True, out_dir=PLOTS_DIR)

    # Parameters + objectives of the non-dominated set
    opt.plot_parallel_coordinates(out_dir=PLOTS_DIR)

    # Knee/TOPSIS solutions highlighted on the front
    opt.plot_best_compromise_solutions(
        separate_by_epw=True, normalize_per_m2=True, out_dir=PLOTS_DIR)

    return opt


if __name__ == '__main__':
    multiprocessing.freeze_support()
    opt = main()

