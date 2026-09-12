"""Experiment 4.2 - ParametricSimulation with 'accim custom model' (Table 5). v3

Requires accim >= 0.8.0 with the addAccis passthrough in the constructor and
the self-sufficient prefer='rdd_mdd' discovery (no ESO parsing).

Designed for interactive execution (IPython / Spyder / Jupyter): run top to
bottom, inspect any variable before the final call. Memory-safe pattern:
simplified outputs, per-batch checkpoints, hourly data kept on disk (.csv)
instead of in RAM.

NOTE (Windows multiprocessing): run_parametric_simulation() parallelises
EnergyPlus runs with ProcessPoolExecutor. On Windows (start method 'spawn')
every worker process re-imports this file as a fresh module, so all top-level
code must live inside `if __name__ == '__main__':` when running this file as
a plain script (python exp_4_2...). Not an issue when run interactively cell
by cell (IPython / Spyder / Jupyter), only when launched with `python file.py`.
See https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
"""

import multiprocessing

import matplotlib
matplotlib.use('Agg')  # non-interactive backend: avoids Tk image-buffer/
                       # memory errors when generating many/large figures
                       # unattended (no display needed to save PNGs to disk).

import pandas as pd
from besos import eppy_funcs as ef
from accim.parametric_and_optimisation.main import ParametricSimulation
from accim.utils import remove_accents_in_idf


def main():
    IDF = 'ALJARAFE CENTER_onlyGeometry.idf'
    EPWS = ['Seville_Present.epw', 'Seville_ssp245_2050.epw', 'Seville_ssp585_2080.epw']

    remove_accents_in_idf(IDF)
    building = ef.get_building(IDF)

    sim = ParametricSimulation(
        buildings=[building],
        epws=EPWS,
        parameters_type='accim custom model',
        ScriptType='vrf_mm',        # fully air-conditioned VRF, as in the real building
        output_type='simplified',   # keep accim's own outputs minimal (memory)
        output_freqs=['hourly'],
        eer=4.42,                   # validated VRF efficiency (ASHRAE Guideline 14 model)
        cop=4.95,
    )

    # Scenario labels, used later by analysis and figures
    sim.set_category_mapping(epw_mapping_rules={'scenario': {
        'present': 'Present',
        'ssp245-2050': 'ssp245_2050',
        'ssp585-2080': 'ssp585_2080',
    }})

    # Outputs. The HVAC electricity meter (objective E) goes into the results
    # table; the hourly variables below stay in the on-disk CSVs (policy 'keep',
    # ['.csv']) and are post-processed after the run, not held in memory:
    # - Zone Operative Temperature -> discomfort metric D (vs EN 16798-1 Cat II)
    # - Adaptive Cooling/Heating Setpoint Temperature (accim EMS output variables)
    #   plus PMOT/RMOT -> scatterplots with the linear regressions of each
    #   sampled adaptive model. NOTE: the custom model EMS equation is
    #   ComfTemp = PMOT*m + n, so PMOT (ASHRAE 55 running average) is the x-axis
    #   for the regressions; RMOT (CEN 15251) is included for completeness.
    meters = pd.DataFrame([{'key_name': 'Electricity:HVAC', 'frequency': 'Hourly'}])
    variables = pd.DataFrame([
        {'key_value': '*', 'variable_name': 'Zone Operative Temperature', 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Adaptive Cooling Setpoint Temperature_No Tolerance', 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Adaptive Heating Setpoint Temperature_No Tolerance', 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature', 'frequency': 'Hourly'},   # PMOT
        {'key_value': '*', 'variable_name': 'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature', 'frequency': 'Hourly'},   # RMOT
    ])

    # ESO-free availability discovery: generates/reads RDD-MDD and fills the
    # cache consumed by validate=True below (no ESO parsing involved).
    # refresh=True: force a fresh RDD/MDD discovery for THIS model. Without it,
    # discover_available_outputs() silently reuses any pre-existing
    # 'available_outputs/eplusout.rdd' left on disk by a DIFFERENT script/model
    # (all exp_4_* scripts share this repo as their working directory), which
    # can make custom EMS output variables look "not available" even though
    # they exist in this model (see exp_4_4's article_objectives EMS output).
    sim.discover_available_outputs(prefer='rdd_mdd', keep_available_outputs=True, refresh=True)

    sim.set_output_variables_to_idf(df_output_variable=variables, idf_scope='all', validate=True, mode='replace')
    sim.set_output_meters_to_idf(df_output_meter=meters, idf_scope='all', validate=True, mode='replace')
    sim.set_output_readers(df_output_meter=meters)

    # Design space (Table 5, experiment 4.2) and LHS plan
    sim.set_parameters(accis_params_dict={
        'CustAST_m': (0, 0.7),
        'CustAST_n': (5, 22.5),
        'CustAST_ASToffset': (1, 5),
        'CustAST_ASTaul': (22, 40),
    })
    sim.set_problem()
    sim.sampling_lhs(num_samples=100)

    sim.parameters_values_df  # inspect the sampled plan before launching

    preflight = sim.preflight_report_parametric(
        df=sim.parameters_values_df, epws=EPWS, verbose=True,
    )

    sim.run_parametric_simulation(
        epws=EPWS,
        out_dir='results_exp_4_2_parametric_custom',
        df=sim.parameters_values_df,
        processes=2,
        batch_size=int(preflight['recommendation']['batch_size']),
        checkpoint_every_batch=True,     # frees memory batch by batch
        resume_from_checkpoint=True,     # safe restart after interruption
        keep_dirs=True,
        keep_input=True,
        sim_files_extensions=['.csv'],   # policy 'keep': hourly data on disk, not in RAM
    )

    # =========================================================================
    # POST-PROCESSING: tables and figures
    # Run after the simulation finishes. In a fresh session, re-run the setup
    # lines above and call run_parametric_simulation again with
    # resume_from_checkpoint=True: completed runs are skipped and the merged
    # results table is returned without re-simulating.
    #
    # NOTE: when this whole file is executed top-to-bottom in a single
    # process (as with `python exp_4_2...`), `sim` above already holds the
    # merged results in memory - no need to recreate it or load any pickle
    # by a hardcoded path/date. (If you DO want to resume post-processing in
    # a brand-new session/process, call
    # sim.load_outputs_parametric(pickle_path=...) with the path printed by
    # the previous run instead.)
    # =========================================================================


    PLOTS_DIR = 'results_exp_4_2_parametric_custom/plots'

    # --- Tables --------------------------------------------------------------
    sim.set_building_floor_area(mode='all')   # floor area for kWh/m2; for the
                                              # paper, switch to the conditioned-
                                              # area mode (312 m2, Section 3.1)
    sim.normalize_outputs(df_types=['parametric'])

    results = sim.outputs_param_simulation
    results.head()                            # inspect columns interactively

    results.to_csv('results_exp_4_2_parametric_custom/table_runs.csv', index=False)
    # normalize_outputs() + set_building_floor_area() rename the raw meter
    # column to '<meter>_kWh/m2' (see exp_4_1 for the same fix/explanation).
    energy_col = 'Electricity:HVAC_kWh/m2' if 'Electricity:HVAC_kWh/m2' in results.columns else 'Electricity:HVAC'
    results.groupby('epw')[energy_col].describe().to_csv(
        'results_exp_4_2_parametric_custom/table_energy_by_epw.csv')

    # --- Run-period figures (parameter -> energy) ----------------------------
    # ASToffset first: the dominant parameter in the Energy 2025 study
    # normalize_per_m2=False: results are already normalized above.
    sim.plot_parametric_scatter(
        x='CustAST_ASToffset', y=energy_col, df_source='parametric',
        hue='epw', add_trend='linear', normalize_per_m2=False, out_dir=PLOTS_DIR)

    sim.plot_parametric_scatter(
        x='CustAST_m', y=energy_col, df_source='parametric',
        hue='epw', add_trend='linear', normalize_per_m2=False, out_dir=PLOTS_DIR)

    sim.plot_parametric_ecdf(
        x=energy_col, df_source='parametric',
        hue='epw', normalize_per_m2=False, out_dir=PLOTS_DIR)

    sim.plot_parametric_distributions(
        x='epw', y_vars=[energy_col], kind='violin', df_source='parametric',
        normalize_per_m2=False, show_points=True, out_dir=PLOTS_DIR)

    # --- Hourly figure: the adaptive-model regressions -----------------------
    # Attaches ONLY the listed columns from the on-disk CSVs (memory-conscious:
    # the setpoints and PMOT are single-key EMS/comfort series, so the hourly
    # table stays at ~300 runs x 8760 h x few columns).
    sim.get_hourly_df_parametric(
        output_columns=[
            'Adaptive Cooling Setpoint Temperature_No Tolerance',
            'Adaptive Heating Setpoint Temperature_No Tolerance',
            'Zone Operative Temperature',
            'ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature',  # PMOT: x-axis (ComfTemp = PMOT*m + n)
        ],
        file_source='csv',
        skip_confirmation=True,
        start_date='2024-01-01 01',
        normalize_per_m2=False,
    )
    sim.outputs_param_simulation_hourly.shape   # inspect before plotting

    # Setpoints (and operative temperature) vs the running-mean outdoor
    # temperature: one linear band per sampled adaptive model.
    sim.plot_hourly_scatter(
        df_source='parametric_hourly',
        epw_filter='Present',
        value_tokens=[
            'Adaptive Cooling Setpoint Temperature_No Tolerance',
            'Adaptive Heating Setpoint Temperature_No Tolerance',
            'Zone Operative Temperature',
        ],
        y_label='Temperature (C)',
        filename='plot_hourly_scatter_setpoints_vs_pmot_present.png',
        out_dir=PLOTS_DIR,
    )

    return sim


if __name__ == '__main__':
    multiprocessing.freeze_support()
    sim = main()
