"""Experiment 4.1 - ParametricSimulation with 'accim predefined model' (Table 5).

Requires accim >= 0.8.0. Interactive execution; memory-safe pattern as in 4.2.

Design notes:
- ScriptType='vrf_mm' (not 'vrf_ac'): the mixed-mode retrofit scenario
  (HVACmode=2) needs the ventilation EMS that only vrf_mm injects.
- The static baseline is obtained with ComfMod=0 (static setpoints within each
  standard) instead of ComfStand=0, because the 'n/a' CAT/ComfMod tokens of
  ComfStand=0 cannot be applied by the EMS mutators (they would write
  'set CAT = n/a').

NOTE (Windows multiprocessing): run_parametric_simulation() parallelises
EnergyPlus runs with ProcessPoolExecutor. On Windows (start method 'spawn')
every worker process re-imports this file as a fresh module, so all top-level
code must live inside `if __name__ == '__main__':` - otherwise each worker
tries to re-run the whole script (including spawning more workers) before
finishing its own bootstrap, raising:
RuntimeError: An attempt has been made to start a new process before the
current process has finished its bootstrapping phase.
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
        parameters_type='accim predefined model',
        ScriptType='vrf_mm',        # mixed-mode capable (HVACmode parameter below)
        output_type='simplified',
        output_freqs=['hourly'],
        eer=4.42,                   # validated VRF efficiency
        cop=4.95,
    )

    sim.set_category_mapping(epw_mapping_rules={'scenario': {
        'present': 'Present',
        'ssp245-2050': 'ssp245_2050',
        'ssp585-2080': 'ssp585_2080',
    }})

    meters = pd.DataFrame([{'key_name': 'Electricity:HVAC', 'frequency': 'Hourly'}])
    variables = pd.DataFrame([
        {'key_value': '*', 'variable_name': 'Zone Operative Temperature', 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Adaptive Cooling Setpoint Temperature_No Tolerance', 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Adaptive Heating Setpoint Temperature_No Tolerance', 'frequency': 'Hourly'},
        {'key_value': '*', 'variable_name': 'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature', 'frequency': 'Hourly'},   # PMOT
        {'key_value': '*', 'variable_name': 'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature', 'frequency': 'Hourly'},   # RMOT
    ])

    # refresh=True: force a fresh RDD/MDD discovery for THIS model. Without it,
    # discover_available_outputs() silently reuses any pre-existing
    # 'available_outputs/eplusout.rdd' left on disk by a DIFFERENT script/model
    # (all exp_4_* scripts share this repo as their working directory), which
    # can make custom EMS output variables look "not available" even though
    # they exist in this model (see exp_4_4's article_objectives EMS output).
    sim.discover_available_outputs(prefer='rdd_mdd', keep_available_outputs=True, refresh=True)
    sim.set_output_variables_to_idf(df_output_variable=variables, idf_scope='all', validate=True, mode='replace')
    sim.set_output_meters_to_idf(df_output_meter=meters, idf_scope='all', validate=True, mode='replace')
    sim.set_outputs_for_simulation(df_output_meter=meters)

    # Design space (Table 5, experiment 4.1): 5 standards x categories x
    # {static, adaptive} x {full AC, mixed-mode retrofit}. sampling_full_set
    # filters invalid (ComfStand, CAT, ComfMod) combinations automatically.
    sim.set_parameters(accis_params_dict={
        'ComfStand': [1, 2, 3, 14, 16],   # EN 16798-1, ASHRAE 55, JPN Rijal, AUS de Dear, BRA Rupp AC
        'CAT': [1, 2, 3, 80, 90],
        'ComfMod': [0, 3],                # 0 = static baseline, 3 = fully adaptive
        'HVACmode': [0, 2],               # 0 = full AC (real), 2 = mixed-mode (hypothetical retrofit)
    })
    sim.set_problem()
    sim.sampling_full_set()               # applies drop_invalid_param_combinations

    sim.parameters_values_df  # inspect: 44 valid combinations x 3 EPWs = 132 runs

    preflight = sim.preflight_report_parametric(
        df=sim.parameters_values_df, epws=EPWS, verbose=True,
    )

    sim.run_parametric_simulation(
        epws=EPWS,
        out_dir='results_exp_4_1_parametric_predefined',
        df=sim.parameters_values_df,
        processes=2,
        batch_size=int(preflight['recommendation']['batch_size']),
        checkpoint_every_batch=True,
        resume_from_checkpoint=True,
        keep_dirs=True,
        keep_input=True,
        sim_files_extensions=['.csv'],
    )

    # =========================================================================
    # POST-PROCESSING: tables and figures
    # Run after the simulation finishes. In a fresh session, re-run the setup
    # lines above and call run_parametric_simulation again with
    # resume_from_checkpoint=True: completed runs are skipped and the merged
    # results table is returned without re-simulating.
    # =========================================================================

    PLOTS_DIR = 'results_exp_4_1_parametric_predefined/plots'

    # --- Tables --------------------------------------------------------------
    sim.set_building_floor_area(mode='all')   # for the paper, switch to the
                                              # conditioned-area mode (312 m2)
    sim.normalize_outputs(df_types=['parametric'])

    results = sim.outputs_param_simulation
    results.head()                            # inspect columns interactively

    results.to_csv('results_exp_4_1_parametric_predefined/table_runs.csv', index=False)
    # normalize_outputs() + set_building_floor_area() rename the raw meter
    # column to '<meter>_kWh/m2' (confirmed in the generated table_runs.csv).
    energy_col = 'Electricity:HVAC_kWh/m2' if 'Electricity:HVAC_kWh/m2' in results.columns else 'Electricity:HVAC'
    results.groupby(['epw', 'ComfStand'])[energy_col].describe().to_csv(
        'results_exp_4_1_parametric_predefined/table_energy_by_epw_comfstand.csv')

    # --- Categorical figures (the core of Section 4.1) -----------------------
    # One boxplot panel per categorical parameter, split by scenario and
    # coloured by operating mode (full AC vs mixed-mode retrofit).
    # NOTE: normalize_outputs() above already renamed the raw meter column to
    # '<meter>_kWh/m2' and the data is already per-m2, so we pass that column
    # name here with normalize_per_m2=False (the original 'Electricity:HVAC'
    # column no longer exists - re-normalizing it would KeyError/double-divide).
    sim.plot_categorical_boxplots(
        df_source='parametric', y_vars=[energy_col],
        col='epw', hue='HVACmode',
        normalize_per_m2=False, show_points=True, out_dir=PLOTS_DIR)

    # Standard x category grid (categorical values -> heatmap works here,
    # unlike the LHS space of experiment 4.2)
    sim.plot_parametric_heatmap(
        x='ComfStand', y='CAT', z=energy_col, df_source='parametric',
        col='epw', annot=True, fmt='.1f',
        normalize_per_m2=False, out_dir=PLOTS_DIR)

    # --- Hourly figure: setpoints of each standard vs running mean -----------
    sim.get_hourly_df_parametric(
        output_columns=[
            'Adaptive Cooling Setpoint Temperature_No Tolerance',
            'Adaptive Heating Setpoint Temperature_No Tolerance',
            'Zone Operative Temperature',
            'ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature',  # PMOT (ASHRAE-type models)
            'CEN 15251 Adaptive Model Running Average Outdoor Air Temperature',  # RMOT (EN 16798-1)
        ],
        file_source='csv',
        skip_confirmation=True,
        start_date='2024-01-01 01',
        normalize_per_m2=False,
    )
    sim.outputs_param_simulation_hourly.shape   # inspect before plotting

    sim.plot_hourly_scatter(
        df_source='parametric_hourly',
        epw_filter='Present',
        value_tokens=[
            'Adaptive Cooling Setpoint Temperature_No Tolerance',
            'Adaptive Heating Setpoint Temperature_No Tolerance',
            'Zone Operative Temperature',
        ],
        y_label='Temperature (C)',
        filename='plot_hourly_scatter_setpoints_vs_rmot_present.png',
        out_dir=PLOTS_DIR,
    )

    return sim


if __name__ == '__main__':
    multiprocessing.freeze_support()
    sim = main()

