"""Experiment 4.3 - ParametricSimulation with 'apmv setpoints' (Table 5).

Requires accim >= 0.8.0. Interactive execution; memory-safe pattern as in 4.2.

Design notes:
- The onlyGeometry IDF has no HVAC: add_vrf_system() injects the VRF with the
  validated efficiency and the Fanger comfort configuration (TempCtrl='pmv')
  that the aPMV framework requires. The constructor then runs
  apply_apmv_setpoints on instantiation (parameters_type='apmv setpoints').
- Parameters: 'Adaptive cooling coefficient' is swept (heating-season lambda
  stays at the apply_apmv_setpoints default, -0.293), because the global
  'Adaptive coefficient' would force the same sign on both seasons.
  The 0.3 value keeps the 0.1-0.5 series and approximates the reference
  lambda = 0.293 of the original aPMV study (JOBE 2026).
- Output variables: apply_apmv_setpoints already injects the aPMV/PMV-related
  outputs, so variables are NOT replaced here (only the meter is managed).

NOTE (Windows multiprocessing): run_parametric_simulation() parallelises
EnergyPlus runs with ProcessPoolExecutor. On Windows (start method 'spawn')
every worker process re-imports this file as a fresh module, so all top-level
code must live inside `if __name__ == '__main__':` - otherwise each worker
tries to re-run the whole script (including spawning more workers) before
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
from accim.parametric_and_optimisation.main import ParametricSimulation
from accim.utils import remove_accents_in_idf


def main():
    IDF = 'ALJARAFE CENTER_onlyGeometry.idf'
    EPWS = ['Seville_Present.epw', 'Seville_ssp245_2050.epw', 'Seville_ssp585_2080.epw']

    remove_accents_in_idf(IDF)
    building = ef.get_building(IDF)
    add_vrf_system(building, eer=4.42, cop=4.95)   # validated VRF + Fanger comfort fields

    sim = ParametricSimulation(
        buildings=[building],
        epws=EPWS,
        parameters_type='apmv setpoints',   # runs apply_apmv_setpoints on init
        output_freqs=['hourly'],
    )

    sim.set_category_mapping(epw_mapping_rules={'scenario': {
        'present': 'Present',
        'ssp245-2050': 'ssp245_2050',
        'ssp585-2080': 'ssp585_2080',
    }})

    meters = pd.DataFrame([{'key_name': 'Electricity:HVAC', 'frequency': 'Hourly'}])

    # refresh=True: force a fresh RDD/MDD discovery for THIS model. Without it,
    # discover_available_outputs() silently reuses any pre-existing
    # 'available_outputs/eplusout.rdd' left on disk by a DIFFERENT script/model
    # (all exp_4_* scripts share this repo as their working directory), which
    # can make custom EMS output variables look "not available" even though
    # they exist in this model (see exp_4_4's article_objectives EMS output).
    sim.discover_available_outputs(prefer='rdd_mdd', keep_available_outputs=True, refresh=True)
    sim.set_output_meters_to_idf(df_output_meter=meters, idf_scope='all', validate=True, mode='append')
    sim.set_output_readers(df_output_meter=meters)

    # Design space (Table 5, experiment 4.3): 4 x 3 = 12 combinations
    sim.set_parameters(accis_params_dict={
        'Adaptive cooling coefficient': [0, 0.1, 0.3, 0.5],   # 0.3 ~ reference 0.293 of the aPMV study (JOBE 2026)
        'PMV setpoint': [0.2, 0.5, 0.7],   # ~ ISO 7730 Cat A/B/C; applied as +/-value
    })
    sim.set_problem()
    sim.sampling_full_set()

    sim.parameters_values_df  # inspect: 12 combinations x 3 EPWs = 36 runs

    preflight = sim.preflight_report_parametric(
        df=sim.parameters_values_df, epws=EPWS, verbose=True,
    )

    sim.run_parametric_simulation(
        epws=EPWS,
        out_dir='results_exp_4_3_parametric_apmv',
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

    PLOTS_DIR = 'results_exp_4_3_parametric_apmv/plots'

    # --- Tables --------------------------------------------------------------
    sim.set_building_floor_area(mode='all')   # for the paper, switch to the
                                              # conditioned-area mode (312 m2)
    sim.normalize_outputs(df_types=['parametric'])

    results = sim.outputs_param_simulation
    results.head()                            # inspect columns interactively

    results.to_csv('results_exp_4_3_parametric_apmv/table_runs.csv', index=False)
    # normalize_outputs() + set_building_floor_area() rename the raw meter
    # column to '<meter>_kWh/m2' (see exp_4_1 for the same fix/explanation).
    energy_col = 'Electricity:HVAC_kWh/m2' if 'Electricity:HVAC_kWh/m2' in results.columns else 'Electricity:HVAC'
    results.groupby('epw')[energy_col].describe().to_csv(
        'results_exp_4_3_parametric_apmv/table_energy_by_epw.csv')

    # --- Grid figures (4 lambdas x 3 PMV setpoints) --------------------------
    # Energy vs adaptive coefficient, one line per PMV setpoint, per scenario
    # normalize_per_m2=False: results are already normalized above.
    sim.plot_parametric_lines(
        x='Adaptive cooling coefficient', y_vars=[energy_col],
        df_source='parametric', hue='PMV setpoint', col='epw',
        normalize_per_m2=False, out_dir=PLOTS_DIR)

    # Full grid as annotated heatmap (categorical grid -> heatmap works here)
    sim.plot_parametric_heatmap(
        x='Adaptive cooling coefficient', y='PMV setpoint', z=energy_col,
        df_source='parametric', col='epw', annot=True, fmt='.1f',
        normalize_per_m2=False, out_dir=PLOTS_DIR)

    # --- Hourly figure: aPMV dynamics vs its setpoints -----------------------
    # aPMV and the aPMV setpoint bands are EMS outputs injected by
    # apply_apmv_setpoints (per-zone suffixed names; token matching finds them).
    sim.get_hourly_df_parametric(
        output_columns=['aPMV', 'aPMV Cooling Setpoint', 'aPMV Heating Setpoint'],
        file_source='csv',
        skip_confirmation=True,
        start_date='2024-01-01 01',
        normalize_per_m2=False,
    )
    sim.outputs_param_simulation_hourly.shape   # inspect before plotting

    sim.plot_hourly_lines(
        df_source='parametric_hourly',
        epw_filter='Present',
        value_tokens=['aPMV', 'aPMV Cooling Setpoint', 'aPMV Heating Setpoint'],
        y_label='aPMV (-)',
        filename='plot_hourly_lines_apmv_present.png',
        out_dir=PLOTS_DIR,
    )

    return sim


if __name__ == '__main__':
    multiprocessing.freeze_support()
    sim = main()

