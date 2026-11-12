# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Verification of the simulations of the models of accim: checks of the outputs against the arguments of
the ACCIS, and of the values that the EMS calculates (the indices derived from the PMV, the metabolic correction of
the ePMV and the setpoints of :func:`accim.sim.preview.compute_setpoints`)."""

import os
import re
import warnings
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from accim.utils.accim_args import get_accim_args_flattened
from accim.utils.outputs import read_eso_using_readvarseso

__all__ = [
    'AccimSimulationVerifier',
    'verify_accim_simulation',
]


def verify_accim_simulation(
        eso_file_path: str,
        idf_path: str,
        eplus_install_dir: Optional[str] = None,
        tolerance: float = 0.1,
        epw: Optional[str] = None,
        calculation_tolerance: float = 1e-3,
) -> pd.DataFrame:
    """
    Reads EnergyPlus simulation output and verifies that the ACCIS EMS scripts
    added by AddAccis are working correctly.

    The function performs six categories of checks:

    **Check 1 – HVAC Setpoint Adherence (per zone):**
    - If cooling is active (CoolCoil > 0): Zone Operative Temperature <= ACST_Sch + tolerance
    - If heating is active (HeatCoil > 0): Zone Operative Temperature >= AHST_Sch - tolerance

    **Check 2 – Window Operation Logic (per window in mixed-mode models):**
    Replicates the explicit conditions of the EMS program ``SetWindowOperation_<windowname>``:

    *HVACmode = 0 (HVAC only):*
      Window must be closed (VentOpenFact == 0).

    *HVACmode = 1 (Natural Ventilation priority — HVAC as backup):*
      Window may open only when ALL of the following:
      - HVAC coils are inactive (NoH_NoC_reqs == 1)
      - OpT < ACST (cooling need)
      - WindSpeed <= MaxWindSpeed
      - OutT > MinOutTemp
      - OutT < OpT
      - Occupancy > 0

      And the VentCtrl sub-condition (for Ventilates_HVACmode1):

      - VentCtrl = 0: OutT < OpT, OutT > MinOutTemp, OpT > VST, WindSpeed <= MaxWindSpeed
      - VentCtrl = 1: OutT < OpT, OutT > MinOutTemp, OpT > ACSTnoTol, WindSpeed <= MaxWindSpeed

    *HVACmode = 2 (Changeover / Free-running):*
      Window may open when:
      NoH_NoC_reqs == 1 AND meets_base_reqs == 1 AND OpT > VST

    **Check 3 – Setpoints based on the PMV (per zone, models of** :func:`accim.sim.pmv_index.apply_pmv_index_setpoints`,
    **such as those of** :func:`accim.sim.apmv.apply_apmv_setpoints` **and** :func:`accim.sim.apmv.apply_epmv_setpoints`
    **):**
    The EMS calculates the index of each zone at the beginning of each timestep from the PMV of its occupants of the
    previous timestep (*Zone Thermal Comfort Fanger Model PMV* of each People object; in a zone with several, their
    mean weighted by their *People Occupant Count* of the timestep), so these checks need the outputs at timestep
    frequency; the first timestep of each environment (sizing period or run period) is not checked:

    - ``Check3_aPMV``: aPMV = PMV/(1 + λ·PMV) (Yao et al., 2009), with the adaptive coefficient λ of the output
      ``Adaptive Coefficient_<zone>``.
    - ``Check3_ePMV``: ePMV = e·PMV if PMV > 0, and PMV otherwise (Fanger and Toftum, 2002, as accim applies it: on
      the warm side of the scale; on both sides with ``apply_to_heating``), with the expectancy factor e of the output
      ``Expectancy Factor_<zone>`` (1 in the heating season).
    - ``Check3_PMV``: the PMV of the zone of the PMV setpoints is that of the previous timestep.
    - ``Check3_MetabolicFactor`` (ePMV setpoints with ``metabolic_correction=True``, each People object):
      Metabolic Correction Factor = 1 − 0.067·PMV in the cooling season (Fanger and Toftum, 2002), with the PMV of the
      previous timestep between 0 and 3 (the mean of the zones of the People object, weighted by their occupants), and
      1 in the heating season.
    - ``Check3_CorrectedActivity``: Corrected Activity Level = the activity level without the correction (the output
      *Schedule Value* of its schedule, which must be added to the model to check it) times that factor.
    - ``Check3_PpdWeightedHours`` (``report_ppd_weighted_hours=True``, each zone): the PPD-weighted hours of Method C
      of CEN/TR 16798-2:2019, Annex D, ``PPD Weighted Hours_<zone>``: in each occupied timestep (the output
      ``Occupied hours_<zone>``, its length), PPD(PMV)/PPD(PMVlimit) (ISO 7730:2025, formula (5)) if the PMV of the
      previous timestep is at or above the upper limit, or below the lower limit, and 0 otherwise; the limits are the
      setpoints of the index without the tolerances (``<index> Heating Setpoint No Tolerance_<zone>``...) on the scale
      of the PMV: those of the PMV, aPMV/(1 − λ·aPMV) with the λ of the output ``Adaptive Coefficient_<zone>`` (or,
      with ``adaptive_coefficient_by='pmv_sign'``, read from the monitor of the zone, the λ of each side of the scale
      of the program ``set_zone_input_data_<zone>``), and ePMV/e on the side of the scale where the monitor of the
      zone applies the expectancy factor e of the output ``Expectancy Factor_<zone>``.

    **Check 4 – Setpoints against** :func:`accim.sim.preview.compute_setpoints` **(per zone, output IDFs of AddAccis,
    only with** ``epw`` **):**
    The comfort temperature and the setpoints that the EMS of each zone reports (``Comfort Temperature_<zone>``,
    ``Adaptive Cooling Setpoint Temperature_<zone>``... with and without the tolerance) are those that
    ``compute_setpoints`` calculates with the arguments of the zone (its program ``SetInputData_<zone>``), the weather
    file ``epw``, the first day of the RunPeriod and the timesteps per hour of the model; and the running mean outdoor
    temperatures of EnergyPlus (*Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air
    Temperature* and *... ASHRAE 55 ...*) are those of :func:`accim.sim.preview.energyplus_running_means`
    (``Check4_RMOT``, ``Check4_PMOT``, ``Check4_ComfTemp``, ``Check4_ACST``, ``Check4_AHST``, ``Check4_ACSTnoTol``
    and ``Check4_AHSTnoTol``). With the custom model and an outdoor metric other than 'pmot'
    (:mod:`accim.sim.ems.outdoor_metric`), and with JPN Aqilah 2025 in a model whose programs of the outdoor metric
    begin with the values of a weather file (its running mean of EN 16798-1 with α = 0.8,
    :data:`accim.sim.ems.standard_lines.WEATHER_FILE_METRICS`), the outdoor metric that the EMS of each zone calculates
    (``Tout_metric_<zone>``) is that of ``compute_setpoints`` too (``Check4_Tout_metric``), which begins as the programs
    of the model do (with the values of the weather file given to AddAccis, or with PMOT; with them, T0 of
    'te_ref_nl' is that of the Schedule:File object of that weather file). The static setpoints of JPN
    Aqilah 2025 are those of the inputs StaticAHST and StaticACST of each zone. With the regimes of the
    custom model (:mod:`accim.sim.ems.custom_regimes`), ``compute_setpoints`` gets those of the program
    ``SelectCustomRegime_<zone>`` of each zone, and the number of the regime that the EMS reports
    (``CustomRegime_<zone>``) is that of ``compute_setpoints`` (``Check4_custom_regime``); the zones whose regimes have
    the conditions 'hvac_off' or 'hvac_on', which depend on the HVAC system, are not checked. They are checked with the
    outputs at timestep frequency, or else hourly, of the last environment of the outputs (the run period). The zones
    whose setpoints a hook of the API backend sets (the setpoints of the ATHB and of the SET of
    :mod:`accim.sim.comfort_hooks`, with the program ``ApplyHookSetpoints_<zone>``) are not checked. In the zones with
    the limiter of the drift of the setpoints (:mod:`accim.sim.ems.drift_limiter`), the setpoints applied depend on the
    indoor temperatures of the simulation, so its targets (``DriftTargetAHST_<zone>`` and ``DriftTargetACST_<zone>``,
    the setpoints of the comfort standard without the tolerance, before the minimum and maximum of the setpoints) are
    those of ``compute_setpoints`` without the minimum and maximum (``Check4_DriftTargetAHST`` and
    ``Check4_DriftTargetACST``), and the setpoints applied are not checked. The running mean
    of ASHRAE 55 of a run period that begins between the 2nd and the 30th of January is that of EnergyPlus 25.1 (with
    the mean of 31 December in place of that of the day before the run period, see
    :func:`accim.sim.preview.energyplus_running_means`); with a .stat file next to the weather file, EnergyPlus takes it
    from the monthly means of the .stat file, which check 4 does not reproduce (its summary says so).

    **Check 5 – The minimum and maximum of the setpoints (per zone, output IDFs of AddAccis):**
    The heating setpoint of the thermostat of each zone with a minimum (``heating_setpoint_minimum``, the input
    ``AHSTmin`` of its program ``SetInputData_<zone>``, see :mod:`accim.sim.ems.setpoint_limits`) is not below the
    minimum plus the tolerance of the setpoints of the zone (``Check5_AHSTmin``), and the cooling setpoint of each zone
    with a maximum (``cooling_setpoint_maximum``, ``ACSTmax``) is not above the maximum minus that tolerance
    (``Check5_ACSTmax``), in the outputs at timestep frequency, or else hourly: the thermostats get the minimum and
    the maximum with the tolerance (finding A19 of the self-audit of 2026-11-11, decided on 2026-11-12). The setpoints
    without the tolerance (the outputs ``..._No Tolerance``, the limits of the comfort band of the hour counters) are
    checked against the minimum and the maximum themselves (``Check5_AHSTmin_noTol`` and ``Check5_ACSTmax_noTol``):
    since finding B5-1 of the review of accim 1.2.0, the minimum and the maximum bound them as well.

    **Check 6 – The long-term discomfort (per zone and building, output IDFs of AddAccis with**
    ``report_long_term_discomfort=True`` **, see** :mod:`accim.sim.ems.long_term_discomfort` **):**
    In each timestep with occupants (the output ``Occupied Hours_<zone>``, the length of the timestep), the outputs
    ``Hours Above Upper Limit_<zone>`` and ``Hours Below Lower Limit_<zone>`` are the length of the timestep if the
    operative temperature of the zone of the previous timestep (that which the EMS reads) is above the cooling setpoint
    without the tolerance (``Adaptive Cooling Setpoint Temperature_No Tolerance_<zone>``), or below the heating
    setpoint without the tolerance (or above and below the limits of ``long_term_range`` that the program of the zone
    has: the constant ones of EN 16798-1, Table B.2, or those of the season of its Table B.5, by the running mean
    outdoor temperature of CEN 15251 of the previous timestep, which needs its output), and ``Degree Hours Above Upper
    Limit_<zone>`` and
    ``Degree Hours Below Lower Limit_<zone>`` are the difference times that length (Methods A and B of CEN/TR
    16798-2:2019, Annex D); in the timesteps without occupants, they are 0 (``Check6_<output>``). The outputs of the
    building (``..._Building``) are the sums of those of the zones. They are checked with the outputs at timestep
    frequency; the first timestep of each environment is not checked.

    :param eso_file_path: Path to the eplusout.eso file.
    :type eso_file_path: str
    :param idf_path: Path to the IDF file used for simulation (to read accim args and window names).
    :type idf_path: str
    :param eplus_install_dir: Path to EnergyPlus installation directory (for ReadVarsESO).
    :type eplus_install_dir: str, optional
    :param tolerance: Temperature tolerance in °C for setpoint checks. Default is 0.1 °C.
    :type tolerance: float
    :param epw: The weather file of the simulation, for check 4 (not done without it).
    :type epw: str, optional
    :param calculation_tolerance: The largest difference between the values that the EMS calculates and those of
        checks 3, 4 and 5 (in °C for the temperatures). Default is 0.001.
    :type calculation_tolerance: float
    :return: DataFrame with all detected mismatch timesteps, with columns
        ['timestep', 'zone_or_window', 'check', 'description', 'value_found', 'value_expected'].
        Empty DataFrame means all checks passed.
    :rtype: pd.DataFrame
    """

    # ─────────────────────────────────────────────
    # 1. READ SIMULATION OUTPUTS
    # ─────────────────────────────────────────────
    print(f"Reading ESO file: {eso_file_path}")
    eso = read_eso_using_readvarseso(
        eso_file_path=eso_file_path,
        eplus_install_dir=eplus_install_dir,
        only_run_period=True,
        cleanup=False,
    )

    # Gather all data into one flat df to make column lookup easier
    all_dfs = []
    for freq, df in eso['data'].items():
        if df.empty:
            continue
        df_flat = df.copy()
        # Flatten MultiIndex columns to "Area:Variable" strings
        df_flat.columns = [
            f"{a}:{v}" if a != 'Environment' else f"Environment:{v}"
            for (a, v, u) in df_flat.columns
        ]
        df_flat['_freq'] = freq
        all_dfs.append(df_flat)

    if not all_dfs:
        warnings.warn("No simulation output data found in the ESO file.")
        return pd.DataFrame()

    # Use hourly if present, else first available frequency
    freq_order = ['Hourly', 'Timestep', 'Daily', 'Monthly']
    chosen_df = None
    chosen_freq = None
    for fq in freq_order:
        for df_temp in all_dfs:
            if df_temp['_freq'].iloc[0] == fq:
                chosen_df = df_temp.drop(columns=['_freq'])
                chosen_freq = fq
                break
        if chosen_df is not None:
            break

    if chosen_df is None:
        chosen_df = all_dfs[0].drop(columns=['_freq'])
        chosen_freq = all_dfs[0]['_freq'].iloc[0]

    print(f"Using output frequency: {chosen_freq} ({len(chosen_df)} time steps)")

    # ─────────────────────────────────────────────
    # 2. READ ACCIM ARGS FROM IDF
    # ─────────────────────────────────────────────
    print(f"Reading IDF: {idf_path}")
    from accim.sim.accis import load_idf
    building = load_idf(idf_path)

    try:
        accim_args = get_accim_args_flattened(building)
    except Exception as e:
        warnings.warn(f"Could not read accim args from IDF: {e}. Skipping window checks.")
        accim_args = {}

    # Global EMS scalar parameters (set once per simulation, not per timestep)
    MaxWindSpeed = float(accim_args.get('MaxWindSpeed', 5.0))
    MinOutTemp   = float(accim_args.get('MinOutTemp', 6.0))
    VentCtrl     = int(float(accim_args.get('VentCtrl', 0)))
    HVACmode     = int(float(accim_args.get('HVACmode', 1)))
    VST          = float(accim_args.get('VST', 20.0))

    # ─────────────────────────────────────────────
    # HELPER: case-insensitive column searcher
    # ─────────────────────────────────────────────
    def find_col(df, area_fragment: str, variable_fragment: str) -> Optional[str]:
        """Return the first column whose 'area:variable' pattern (case-insensitive)
        contains both fragments."""
        area_frag_up = area_fragment.upper()
        var_frag_up  = variable_fragment.upper()
        for col in df.columns:
            col_up = col.upper()
            parts = col_up.split(':', 1)
            if len(parts) == 2:
                if area_frag_up in parts[0] and var_frag_up in parts[1]:
                    return col
            else:
                if var_frag_up in col_up:
                    return col
        return None

    def find_cols_by_variable(df, variable_fragment: str) -> List[str]:
        """Return all columns whose variable part contains the fragment (case-insensitive)."""
        var_frag_up = variable_fragment.upper()
        matches = []
        for col in df.columns:
            col_up = col.upper()
            parts = col_up.split(':', 1)
            var_part = parts[1] if len(parts) == 2 else col_up
            if var_frag_up in var_part:
                matches.append(col)
        return matches

    def find_cols_by_area(df, area_fragment: str) -> List[str]:
        """Return all columns whose area part contains the fragment (case-insensitive)."""
        area_frag_up = area_fragment.upper()
        matches = []
        for col in df.columns:
            col_up = col.upper()
            parts = col_up.split(':', 1)
            if len(parts) == 2 and area_frag_up in parts[0]:
                matches.append(col)
        return matches

    # ─────────────────────────────────────────────
    # 3. DETECT ZONES AND WINDOWS FROM EMS OBJECTS
    # ─────────────────────────────────────────────
    # Build a map {ems_name: actual_ep_key} from _OpT sensors.
    # 'ems_name'     = sensor Name without '_OpT'  (e.g. 'Floor_1_Residential_Living_Occupants')
    #                  matches schedule keys ACST_Sch_{ems_name}, AHST_Sch_{ems_name}
    # 'actual_ep_key'= OutputVariable_or_OutputMeter_Index_Key_Name  (e.g. 'Floor_1_Zone')
    #                  matches EnergyPlus output column areas (Zone Operative Temperature, coils …)
    ems_zone_map: Dict[str, str] = {}  # {ems_name: actual_ep_key}
    for sc in building.idfobjects['EnergyManagementSystem:Sensor']:
        if sc.Name.endswith('_OpT'):
            ems_name   = sc.Name[:-4]  # strip '_OpT'
            actual_key = str(sc.OutputVariable_or_OutputMeter_Index_Key_Name)
            ems_zone_map[ems_name] = actual_key

    ems_zone_names: List[str] = list(ems_zone_map.keys())

    # Window names (from SetWindowOperation programs)
    window_names: List[str] = []
    for prog in building.idfobjects['EnergyManagementSystem:Program']:
        if prog.Name.upper().startswith('SETWINDOWOPERATION_'):
            w = prog.Name[len('SetWindowOperation_'):]
            window_names.append(w)

    # Comfort zones = all EMS zones that are NOT window zones
    # (window zones have no ACST/AHST schedules)
    comfort_zone_names: List[str] = [z for z in ems_zone_names if z not in window_names]

    # Build map {window_ems_name: ventilation_schedule_name} for non-AFN models
    # by scanning EMS actuators whose name contains the window name
    window_vent_sch_map: Dict[str, str] = {}
    for act in building.idfobjects['EnergyManagementSystem:Actuator']:
        act_name_up = act.Name.upper()
        for wname in window_names:
            if wname.upper() in act_name_up:
                comp_id = str(act.Actuated_Component_Unique_Name)
                if comp_id and comp_id not in ('', 'None'):
                    window_vent_sch_map[wname] = comp_id
                break

    is_mixed_mode = len(window_names) > 0
    print(f"Detected {len(ems_zone_names)} EMS zone(s): {ems_zone_names}")
    print(f"  EMS->EP key map: { {k: v for k, v in ems_zone_map.items()} }")
    print(f"Mixed-mode model: {is_mixed_mode}  |  Windows detected: {window_names}")
    if window_vent_sch_map:
        print(f"  Window->VentSchedule map: {window_vent_sch_map}")
    print(f"EMS params — HVACmode={HVACmode}, VentCtrl={VentCtrl}, "
          f"MaxWindSpeed={MaxWindSpeed}, MinOutTemp={MinOutTemp}, VST={VST}")

    # ─────────────────────────────────────────────
    # 4. BUILD RESULTS ACCUMULATOR
    # ─────────────────────────────────────────────
    mismatch_rows: List[dict] = []

    def add_mismatch(timestep, zone_or_window: str, check: str,
                     description: str, value_found, value_expected):
        mismatch_rows.append({
            'timestep':       timestep,
            'zone_or_window': zone_or_window,
            'check':          check,
            'description':    description,
            'value_found':    round(float(value_found), 4) if isinstance(value_found, (int, float)) else value_found,
            'value_expected': value_expected,
        })

    # ─────────────────────────────────────────────
    # 5.A CHECK 1 – HVAC SETPOINT ADHERENCE
    # ─────────────────────────────────────────────
    print("\n--- Check 1: HVAC Setpoint Adherence ---")

    # Only run setpoint checks for comfort zones (not raw window zones)
    for zone in comfort_zone_names:
        actual_ep_key = ems_zone_map.get(zone, zone)

        # ── Operative temperature: use the actual EnergyPlus zone key in the column area
        opt_col = find_col(chosen_df, actual_ep_key, 'Operative Temperature')
        if opt_col is None:
            opt_col = find_col(chosen_df, actual_ep_key, 'Zone Operative Temperature')
        if opt_col is None:
            warnings.warn(
                f"Zone '{zone}' (EP key '{actual_ep_key}'): "
                f"No 'Operative Temperature' column found. Skipping setpoint check."
            )
            continue

        # ── ACST / AHST schedules: key uses the EMS name (not the actual zone key)
        acst_col = find_col(chosen_df, f'ACST_Sch_{zone}', 'Schedule Value')
        ahst_col = find_col(chosen_df, f'AHST_Sch_{zone}', 'Schedule Value')

        if acst_col is None or ahst_col is None:
            warnings.warn(
                f"Zone '{zone}': ACST_Sch or AHST_Sch column not found "
                f"(acst_col={acst_col}, ahst_col={ahst_col}). Skipping setpoint check."
            )
            continue

        # ── Cooling / heating rate: use actual_ep_key (the area in the output)
        cool_col = (
            find_col(chosen_df, actual_ep_key, 'Cooling Coil Total Cooling Rate')
            or find_col(chosen_df, actual_ep_key, 'VRF Heat Pump Cooling Electricity')
            or find_col(chosen_df, actual_ep_key, 'Cooling Rate')
        )
        heat_col = (
            find_col(chosen_df, actual_ep_key, 'Heating Coil Heating Rate')
            or find_col(chosen_df, actual_ep_key, 'VRF Heat Pump Heating Electricity')
            or find_col(chosen_df, actual_ep_key, 'Heating Rate')
        )

        if cool_col is None and heat_col is None:
            warnings.warn(
                f"Zone '{zone}' (EP key '{actual_ep_key}'): No cooling or heating rate column found. "
                "Setpoint check will be skipped for this zone."
            )
            continue

        print(f"  Zone '{zone}': OpT col='{opt_col}', ACST col='{acst_col}', "
              f"cool col='{cool_col}', heat col='{heat_col}'")

        opt    = chosen_df[opt_col].astype(float)
        acst   = chosen_df[acst_col].astype(float)
        ahst   = chosen_df[ahst_col].astype(float)

        for pos, idx in enumerate(chosen_df.index):
            opt_val  = float(opt.iat[pos])
            acst_val = float(acst.iat[pos])
            ahst_val = float(ahst.iat[pos])

            # Cooling check
            if cool_col is not None:
                cool_rate = float(chosen_df[cool_col].iat[pos])
                if cool_rate > 0 and opt_val > acst_val + tolerance:
                    add_mismatch(
                        timestep       = idx,
                        zone_or_window = zone,
                        check          = 'Check1_Cooling',
                        description    = (
                            f"Cooling active (rate={cool_rate:.2f} W) but OpT ({opt_val:.2f} °C) "
                            f"> ACST ({acst_val:.2f} °C) + tolerance ({tolerance} °C)"
                        ),
                        value_found    = opt_val,
                        value_expected = f"<= {acst_val + tolerance:.2f} °C",
                    )

            # Heating check
            if heat_col is not None:
                heat_rate = float(chosen_df[heat_col].iat[pos])
                if heat_rate > 0 and opt_val < ahst_val - tolerance:
                    add_mismatch(
                        timestep       = idx,
                        zone_or_window = zone,
                        check          = 'Check1_Heating',
                        description    = (
                            f"Heating active (rate={heat_rate:.2f} W) but OpT ({opt_val:.2f} °C) "
                            f"< AHST ({ahst_val:.2f} °C) - tolerance ({tolerance} °C)"
                        ),
                        value_found    = opt_val,
                        value_expected = f">= {ahst_val - tolerance:.2f} °C",
                    )

        # Summary per zone
        cool_fails = sum(1 for r in mismatch_rows
                         if r['zone_or_window'] == zone and r['check'] == 'Check1_Cooling')
        heat_fails = sum(1 for r in mismatch_rows
                         if r['zone_or_window'] == zone and r['check'] == 'Check1_Heating')
        total_ts = len(chosen_df)
        print(f"  Zone '{zone}': Cooling mismatches: {cool_fails}/{total_ts} | "
              f"Heating mismatches: {heat_fails}/{total_ts}")

    # ─────────────────────────────────────────────
    # 5.B CHECK 2 – WINDOW OPERATION LOGIC
    # ─────────────────────────────────────────────
    if is_mixed_mode:
        print("\n--- Check 2: Window Operation Logic (SetWindowOperation) ---")

        # Outdoor temperature and wind speed (Environment-level sensors)
        out_t_col  = (find_col(chosen_df, 'Environment', 'Site Outdoor Air Drybulb Temperature')
                      or find_col(chosen_df, 'ENVIRONMENT', 'Drybulb'))
        wind_col   = (find_col(chosen_df, 'Environment', 'Site Wind Speed')
                      or find_col(chosen_df, 'ENVIRONMENT', 'Wind Speed'))

        if out_t_col is None:
            warnings.warn("'Site Outdoor Air Drybulb Temperature' column not found. "
                          "Window checks requiring OutT will be skipped.")
        if wind_col is None:
            warnings.warn("'Site Wind Speed' column not found. "
                          "Window checks requiring WindSpeed will be skipped.")

        for wname in window_names:
            # Actual EnergyPlus key for the window zone (e.g. 'Floor_1_Zone')
            actual_win_key = ems_zone_map.get(wname, wname)

            # ── Opening factor
            # 1. Try AFN surface opening factor
            vof_col = (
                find_col(chosen_df, wname, 'AFN Surface Venting Window or Door Opening Factor')
                or find_col(chosen_df, actual_win_key, 'AFN Surface Venting Window or Door Opening Factor')
                or find_col(chosen_df, wname, 'Opening Factor')
            )
            if vof_col is None:
                # 2. Scheduled ventilation: look up schedule from the actuator map built earlier
                vent_sch_name = window_vent_sch_map.get(wname)
                if vent_sch_name:
                    vof_col = find_col(chosen_df, vent_sch_name, 'Schedule Value')
            if vof_col is None:
                # 3. Derive schedule name from actual EnergyPlus zone key: Vent_Sch_{actual_win_key}
                vof_col = find_col(chosen_df, f'Vent_Sch_{actual_win_key}', 'Schedule Value')
            if vof_col is None:
                warnings.warn(
                    f"Window '{wname}' (EP key '{actual_win_key}'): "
                    f"No opening factor / ventilation schedule column found. Skipping window check."
                )
                continue

            print(f"  Window '{wname}': opening-factor col='{vof_col}'")

            # ── Per-window operative temperature: use actual EP key
            opt_w_col = (
                find_col(chosen_df, actual_win_key, 'Operative Temperature')
                or find_col(chosen_df, actual_win_key, 'Zone Operative Temperature')
                or find_col(chosen_df, wname, 'Operative Temperature')
            )

            # ── Cooling / heating coils: use actual EP key
            cool_w_col = (
                find_col(chosen_df, actual_win_key, 'Cooling Coil Total Cooling Rate')
                or find_col(chosen_df, actual_win_key, 'Cooling Rate')
                or find_col(chosen_df, wname, 'Cooling Coil Total Cooling Rate')
            )
            heat_w_col = (
                find_col(chosen_df, actual_win_key, 'Heating Coil Heating Rate')
                or find_col(chosen_df, actual_win_key, 'Heating Rate')
                or find_col(chosen_df, wname, 'Heating Coil Heating Rate')
            )

            # ── Occupancy: try window zone first, then fall back to any EMS occ column
            occ_col = (
                find_col(chosen_df, actual_win_key, 'People Occupant Count')
                or find_col(chosen_df, wname, 'People Occupant Count')
            )
            # Last resort: use any EMS occupancy output (first comfort zone)
            if occ_col is None:
                for cz in comfort_zone_names:
                    occ_col = find_col(chosen_df, 'EMS', f'People Occupant Count_{cz}')
                    if occ_col:
                        break

            # ── ACST reference for window zone: take from first comfort zone
            # (ACSTnoTol is a global EMS variable, approximated here by the schedule value)
            acst_no_tol_col = None
            for cz in comfort_zone_names:
                cand = find_col(chosen_df, f'ACST_Sch_{cz}', 'Schedule Value')
                if cand:
                    acst_no_tol_col = cand
                    break
            acst_w_col = acst_no_tol_col

            vof    = chosen_df[vof_col].astype(float)
            out_t  = chosen_df[out_t_col].astype(float) if out_t_col else None
            wind   = chosen_df[wind_col].astype(float)  if wind_col  else None

            prev_checks = len(mismatch_rows)

            for pos, idx in enumerate(chosen_df.index):
                vof_val = float(vof.iat[pos])
                window_open = vof_val > 0.0

                # Retrieve optional per-timestep variables safely
                opt_val   = float(chosen_df[opt_w_col].iat[pos])   if opt_w_col   else None
                cool_val  = float(chosen_df[cool_w_col].iat[pos])  if cool_w_col  else 0.0
                heat_val  = float(chosen_df[heat_w_col].iat[pos])  if heat_w_col  else 0.0
                occ_val   = float(chosen_df[occ_col].iat[pos])     if occ_col     else 1.0
                out_t_val = float(out_t.iat[pos])                  if out_t  is not None else None
                wind_val  = float(wind.iat[pos])                   if wind   is not None else 0.0
                acst_val  = float(chosen_df[acst_w_col].iat[pos])  if acst_w_col  else None

                # ── Derive NoH_NoC_reqs
                no_h_no_c = (cool_val == 0.0) and (heat_val == 0.0)

                # ───────────────────────────────────────────────────
                # HVACmode = 0: window must NEVER open
                # ───────────────────────────────────────────────────
                if HVACmode == 0:
                    if window_open:
                        add_mismatch(
                            timestep       = idx,
                            zone_or_window = wname,
                            check          = 'Check2_HVACmode0',
                            description    = (
                                f"HVACmode=0 (HVAC-only) but window is open "
                                f"(VentOpenFact={vof_val:.3f})"
                            ),
                            value_found    = vof_val,
                            value_expected = 0.0,
                        )

                # ───────────────────────────────────────────────────
                # HVACmode = 1: window opens only when all conditions met
                # ───────────────────────────────────────────────────
                elif HVACmode == 1:
                    if window_open:
                        # Condition: noH_noC_reqs must be True
                        if not no_h_no_c:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode1_NoHNoC',
                                description    = (
                                    f"HVACmode=1: Window open but HVAC is active "
                                    f"(CoolCoil={cool_val:.2f}, HeatCoil={heat_val:.2f})"
                                ),
                                value_found    = f"cool={cool_val:.2f}, heat={heat_val:.2f}",
                                value_expected = "CoolCoil=0 AND HeatCoil=0",
                            )

                        # Condition: OpT < roundedACST (cooling need)
                        if opt_val is not None and acst_val is not None:
                            if opt_val >= acst_val:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode1_OpT_lt_ACST',
                                    description    = (
                                        f"HVACmode=1: Window open but OpT ({opt_val:.2f} °C) "
                                        f">= ACST ({acst_val:.2f} °C) — no cooling need"
                                    ),
                                    value_found    = opt_val,
                                    value_expected = f"< {acst_val:.2f} °C",
                                )

                        # Condition: WindSpeed <= MaxWindSpeed
                        if wind_val > MaxWindSpeed:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode1_WindSpeed',
                                description    = (
                                    f"HVACmode=1: Window open but WindSpeed ({wind_val:.2f} m/s) "
                                    f"> MaxWindSpeed ({MaxWindSpeed} m/s)"
                                ),
                                value_found    = wind_val,
                                value_expected = f"<= {MaxWindSpeed} m/s",
                            )

                        # Condition: OutT > MinOutTemp
                        if out_t_val is not None and out_t_val <= MinOutTemp:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode1_MinOutTemp',
                                description    = (
                                    f"HVACmode=1: Window open but OutT ({out_t_val:.2f} °C) "
                                    f"<= MinOutTemp ({MinOutTemp} °C)"
                                ),
                                value_found    = out_t_val,
                                value_expected = f"> {MinOutTemp} °C",
                            )

                        # Condition: OutT < OpT (outdoor cooler than indoor)
                        if out_t_val is not None and opt_val is not None:
                            if out_t_val >= opt_val:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode1_OutT_lt_OpT',
                                    description    = (
                                        f"HVACmode=1: Window open but OutT ({out_t_val:.2f} °C) "
                                        f">= OpT ({opt_val:.2f} °C)"
                                    ),
                                    value_found    = out_t_val,
                                    value_expected = f"< OpT ({opt_val:.2f} °C)",
                                )

                        # Condition: Occupancy > 0
                        if occ_val <= 0:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode1_Occupancy',
                                description    = (
                                    f"HVACmode=1: Window open but zone is unoccupied "
                                    f"(Occ_count={occ_val})"
                                ),
                                value_found    = occ_val,
                                value_expected = "> 0",
                            )

                        # VentCtrl sub-condition for Ventilates_HVACmode1
                        if VentCtrl == 0:
                            # OpT > VST
                            if opt_val is not None and opt_val <= VST:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode1_VentCtrl0_OpT_gt_VST',
                                    description    = (
                                        f"VentCtrl=0: Window open but OpT ({opt_val:.2f} °C) "
                                        f"<= VST ({VST} °C)"
                                    ),
                                    value_found    = opt_val,
                                    value_expected = f"> {VST} °C",
                                )

                        elif VentCtrl == 1:
                            # OpT > ACSTnoTol (≈ ACST without offset)
                            if opt_val is not None and acst_val is not None:
                                if opt_val <= acst_val:
                                    add_mismatch(
                                        timestep       = idx,
                                        zone_or_window = wname,
                                        check          = 'Check2_HVACmode1_VentCtrl1_OpT_gt_ACSTnoTol',
                                        description    = (
                                            f"VentCtrl=1: Window open but OpT ({opt_val:.2f} °C) "
                                            f"<= ACSTnoTol ({acst_val:.2f} °C)"
                                        ),
                                        value_found    = opt_val,
                                        value_expected = f"> {acst_val:.2f} °C",
                                    )

                # ───────────────────────────────────────────────────
                # HVACmode = 2: changeover / free-running
                # Window can open when: NoH_NoC_reqs AND meets_base_reqs AND OpT > VST
                # meets_base_reqs: OpT < ACST, WindSpeed <= MaxWind, OutT > MinOutTemp,
                #                  OutT < OpT, Occ > 0
                # ───────────────────────────────────────────────────
                elif HVACmode == 2:
                    if window_open:
                        # NoH_NoC_reqs: HVAC must be off
                        if not no_h_no_c:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_NoHNoC',
                                description    = (
                                    f"HVACmode=2: Window open but HVAC is active "
                                    f"(CoolCoil={cool_val:.2f}, HeatCoil={heat_val:.2f})"
                                ),
                                value_found    = f"cool={cool_val:.2f}, heat={heat_val:.2f}",
                                value_expected = "CoolCoil=0 AND HeatCoil=0",
                            )

                        # meets_base_reqs: OpT < ACST
                        if opt_val is not None and acst_val is not None:
                            if opt_val >= acst_val:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode2_OpT_lt_ACST',
                                    description    = (
                                        f"HVACmode=2: Window open but OpT ({opt_val:.2f} °C) "
                                        f">= ACST ({acst_val:.2f} °C)"
                                    ),
                                    value_found    = opt_val,
                                    value_expected = f"< {acst_val:.2f} °C",
                                )

                        # meets_base_reqs: WindSpeed <= MaxWindSpeed
                        if wind_val > MaxWindSpeed:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_WindSpeed',
                                description    = (
                                    f"HVACmode=2: Window open but WindSpeed ({wind_val:.2f} m/s) "
                                    f"> MaxWindSpeed ({MaxWindSpeed} m/s)"
                                ),
                                value_found    = wind_val,
                                value_expected = f"<= {MaxWindSpeed} m/s",
                            )

                        # meets_base_reqs: OutT > MinOutTemp
                        if out_t_val is not None and out_t_val <= MinOutTemp:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_MinOutTemp',
                                description    = (
                                    f"HVACmode=2: Window open but OutT ({out_t_val:.2f} °C) "
                                    f"<= MinOutTemp ({MinOutTemp} °C)"
                                ),
                                value_found    = out_t_val,
                                value_expected = f"> {MinOutTemp} °C",
                            )

                        # meets_base_reqs: OutT < OpT
                        if out_t_val is not None and opt_val is not None:
                            if out_t_val >= opt_val:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode2_OutT_lt_OpT',
                                    description    = (
                                        f"HVACmode=2: Window open but OutT ({out_t_val:.2f} °C) "
                                        f">= OpT ({opt_val:.2f} °C)"
                                    ),
                                    value_found    = out_t_val,
                                    value_expected = f"< OpT ({opt_val:.2f} °C)",
                                )

                        # meets_base_reqs: Occupancy > 0
                        if occ_val <= 0:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_Occupancy',
                                description    = (
                                    f"HVACmode=2: Window open but zone is unoccupied "
                                    f"(Occ_count={occ_val})"
                                ),
                                value_found    = occ_val,
                                value_expected = "> 0",
                            )

                        # Ventilates_HVACmode2: OpT > VST
                        if opt_val is not None and opt_val <= VST:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_OpT_gt_VST',
                                description    = (
                                    f"HVACmode=2: Window open but OpT ({opt_val:.2f} °C) "
                                    f"<= VST ({VST} °C)"
                                ),
                                value_found    = opt_val,
                                value_expected = f"> {VST} °C",
                            )

            new_fails = len(mismatch_rows) - prev_checks
            open_ts   = int((vof > 0.0).sum())
            print(f"  Window '{wname}': {open_ts}/{len(chosen_df)} timesteps open | "
                  f"Condition violations: {new_fails}")

    # ─────────────────────────────────────────────
    # 5.C CHECK 3 – SETPOINTS BASED ON THE PMV
    # ─────────────────────────────────────────────
    timestep_data = eso['data'].get('Timestep')
    rows, messages = _pmv_index_mismatches(building, timestep_data, calculation_tolerance)
    if messages:
        print("\n--- Check 3: Setpoints based on the PMV (the index of the PMV of the previous timestep) ---")
        print('\n'.join(messages))
    mismatch_rows.extend(rows)

    # ─────────────────────────────────────────────
    # 5.D CHECK 4 – SETPOINTS AGAINST compute_setpoints
    # ─────────────────────────────────────────────
    if epw is not None:
        print("\n--- Check 4: Setpoints and running means against accim.sim.preview.compute_setpoints ---")
        rows, messages = _setpoint_mismatches(building, eso['data'], epw, calculation_tolerance)
        print('\n'.join(messages))
        mismatch_rows.extend(rows)

    # ─────────────────────────────────────────────
    # 5.E CHECK 5 – THE MINIMUM AND MAXIMUM OF THE SETPOINTS
    # ─────────────────────────────────────────────
    rows, messages = _setpoint_limit_mismatches(building, eso['data'], calculation_tolerance)
    if messages:
        print("\n--- Check 5: The minimum heating setpoint and the maximum cooling setpoint ---")
        print('\n'.join(messages))
    mismatch_rows.extend(rows)

    # ─────────────────────────────────────────────
    # 5.F CHECK 6 – THE LONG-TERM DISCOMFORT
    # ─────────────────────────────────────────────
    rows, messages = _long_term_mismatches(building, eso['data'], calculation_tolerance)
    if messages:
        print("\n--- Check 6: The long-term discomfort of the occupied hours ---")
        print('\n'.join(messages))
    mismatch_rows.extend(rows)

    # ─────────────────────────────────────────────
    # 6. RETURN RESULTS
    # ─────────────────────────────────────────────
    result_df = pd.DataFrame(mismatch_rows)

    if result_df.empty:
        print("\nAll checks passed. No mismatches detected.")
    else:
        print(f"\n{len(result_df)} mismatch(es) detected across "
              f"{result_df['check'].nunique()} check type(s).")
        print(result_df.groupby(['zone_or_window', 'check']).size()
              .rename('count').reset_index().to_string(index=False))

    return result_df


# ─────────────────────────────────────────────────────────────────────────────
# CHECKS 3 AND 4: THE VALUES THAT THE EMS CALCULATES
# ─────────────────────────────────────────────────────────────────────────────

#: The date and time of a row of the outputs of EnergyPlus: 'MM/DD  HH:MM:SS'
_DATE_TIME = re.compile(r'(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})')
#: The program that applies the setpoints of an index of accim.sim.pmv_index to a zone: apply_<index>_<zone>
_PMV_INDEX_PROGRAM = re.compile(r'apply_(aPMV|ePMV|PMV)_(.+)$', re.IGNORECASE)
#: The running mean outdoor temperatures of EnergyPlus, by their columns in accim.sim.preview
_RUNNING_MEANS = {
    'RMOT': 'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature',
    'PMOT': 'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature',
}


def _dates_and_times(timestamps: Sequence[str]) -> Tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """The date and time of the end of each row of the outputs of EnergyPlus (``'MM/DD  HH:MM:SS'``; ``24:00:00`` is
    the end of the day, the midnight of the next day), and the date of each row (that of the timestamp, also at
    24:00:00), in the year of :func:`accim.sim.preview.compute_setpoints` (2007, or 2008 if there is a 29 February).

    :raises ValueError: If a timestamp has another format.
    """
    parts = []
    for timestamp in timestamps:
        match = _DATE_TIME.search(str(timestamp))
        if match is None:
            raise ValueError(f'{timestamp!r} is not a date and time of the outputs of EnergyPlus (MM/DD  HH:MM:SS).')
        parts.append([int(value) for value in match.groups()])
    parts = np.array(parts, dtype=np.int64).reshape(-1, 5)
    year = 2008 if ((parts[:, 0] == 2) & (parts[:, 1] == 29)).any() else 2007
    dates = pd.DatetimeIndex(pd.to_datetime(pd.DataFrame({'year': np.full(len(parts), year), 'month': parts[:, 0],
                                                          'day': parts[:, 1]})))
    seconds = parts[:, 2] * 3600 + parts[:, 3] * 60 + parts[:, 4]
    return dates + pd.to_timedelta(seconds, unit='s'), dates


def _environment_starts(datetimes: pd.DatetimeIndex) -> np.ndarray:
    """Whether each row of the outputs is the first one of an environment (a sizing period or a run period): its time
    is not that of the previous row plus one step (the most frequent difference between rows)."""
    starts = np.ones(len(datetimes), dtype=bool)
    if len(datetimes) > 1:
        differences = np.diff(datetimes.asi8)
        starts[1:] = differences != pd.Series(differences).mode().iloc[0]
    return starts


class _Outputs:
    """The outputs of one frequency of :func:`accim.utils.outputs.read_eso_using_readvarseso` (a DataFrame with the
    columns (key, variable, units) and the date and time of each row as its index): their values by key and variable
    (in any case), the date and time of the end of each row, its date, and the first rows of the environments."""

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame
        self.timestamps = [str(timestamp).strip() for timestamp in frame.index]
        self.datetimes, self.dates = _dates_and_times(self.timestamps)
        self.starts = _environment_starts(self.datetimes)
        self._columns = {(str(column[0]).strip().upper(), str(column[1]).strip().upper()): column
                         for column in frame.columns}

    def get(self, key: str, variable: str) -> Optional[np.ndarray]:
        """The values of an output (None if it is not in the outputs)."""
        column = self._columns.get((str(key).strip().upper(), str(variable).strip().upper()))
        return None if column is None else self.frame[column].to_numpy(dtype=float)

    def keys(self, variable: str) -> List[str]:
        """The keys of an output variable."""
        return [str(column[0]) for (_, name), column in self._columns.items() if name == variable.strip().upper()]

    def previous(self, values: np.ndarray) -> np.ndarray:
        """The values of the previous row (NaN in the first row of each environment)."""
        result = np.r_[np.nan, values[:-1]]
        result[self.starts] = np.nan
        return result


def _program_lines(program) -> List[str]:
    return [str(line).strip() for line in program.fieldvalues[2:] if str(line).strip()]


def _weighted_mean(values: Sequence[np.ndarray], weights: Sequence[np.ndarray]) -> np.ndarray:
    """The mean of some values weighted by the occupants, or their simple mean where there are none, as the EMS
    programs of accim.sim.pmv_index calculate the PMV of a zone with several People objects."""
    total = sum(weights)
    weighted = sum(value * weight for value, weight in zip(values, weights))
    return np.where(total > 0, weighted / np.where(total > 0, total, 1), sum(values) / len(values))


def _mismatch_rows(timestamps: Sequence[str], found: np.ndarray, expected: np.ndarray, zone: str, check: str,
                   description: str, tolerance: float) -> Tuple[List[dict], str]:
    """The mismatches (the rows whose value differs from the expected one by more than the tolerance; the rows without
    an expected value are not checked), and a line of the summary."""
    difference = np.abs(found - expected)
    checked = np.isfinite(difference)
    bad = np.flatnonzero(checked & (np.where(checked, difference, 0) > tolerance))
    rows = [{
        'timestep': timestamps[position],
        'zone_or_window': zone,
        'check': check,
        'description': f'{description}: {found[position]:.6f} instead of {expected[position]:.6f}',
        'value_found': round(float(found[position]), 6),
        'value_expected': round(float(expected[position]), 6),
    } for position in bad]
    return rows, f"  '{zone}' {check} ({description}): {len(bad)} mismatch(es) in {int(checked.sum())} timesteps"


def _pmv_index_mismatches(building, frame: Optional[pd.DataFrame], tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 3 of :func:`verify_accim_simulation`: the indices derived from the PMV of the setpoints of
    :mod:`accim.sim.pmv_index`, and the metabolic correction of the ePMV, from the PMV of the previous timestep.

    :param building: The model (eppy).
    :param frame: The outputs at timestep frequency of :func:`accim.utils.outputs.read_eso_using_readvarseso` (None
        if there are none).
    :param tolerance: The largest difference allowed.
    :return: The mismatches, and the lines of the summary (none if the model has no setpoints based on the PMV).
    """
    from accim.constants import EPMV_MET_REDUCTION_PER_PMV
    from accim.data.postprocessing.long_term_discomfort import ppd_from_pmv
    from accim.sim.ems.erl import ErlProgramSet
    from accim.sim.pmv_index import (_MAX_METABOLIC_PMV, PMV_INDICES, PPD_WEIGHTED_HOURS_PROGRAM,
                                     metabolic_correction_names)
    from accim.sim.targets import resolve_targets, sanitize_ems_name
    from accim.utils.people import get_people_objects

    indices = {pmv_index.name.upper(): pmv_index for pmv_index in PMV_INDICES.values()}
    programs = {str(program.Name).upper(): program for program in building.idfobjects['EnergyManagementSystem:Program']}
    zones = []
    for program in building.idfobjects['EnergyManagementSystem:Program']:
        match = _PMV_INDEX_PROGRAM.match(str(program.Name))
        if match is not None and match.group(1).upper() in indices:
            zones.append((indices[match.group(1).upper()], match.group(2)))
    if not zones:
        return [], []
    if frame is None or frame.empty:
        message = ("The setpoints based on the PMV are checked with the outputs at timestep frequency, since the EMS "
                   "calculates the index of each timestep from the PMV of the previous one: add 'timestep' to the "
                   "output_frequencies of the setpoints to check them.")
        warnings.warn(message)
        return [], [f'  Not checked. {message}']
    outputs = _Outputs(frame)
    sensors = {str(sensor.Name).upper(): (str(sensor.OutputVariable_or_OutputMeter_Index_Key_Name),
                                          str(sensor.OutputVariable_or_OutputMeter_Name))
               for sensor in building.idfobjects['EnergyManagementSystem:Sensor']}

    def sensor_values(name: str) -> Tuple[Optional[np.ndarray], str]:
        """The values of the output that an EMS sensor reads, and what is missing if they are not in the outputs."""
        if name.upper() not in sensors:
            return None, f'the EMS sensor {name}'
        key, variable = sensors[name.upper()]
        values = outputs.get(key, variable)
        return values, ('' if values is not None else f"the output '{variable}' of '{key}' at timestep frequency")

    def zone_pmv(suffix: str) -> Tuple[Optional[np.ndarray], str]:
        """The PMV of a zone that the EMS reads at each timestep: that of its People object of the previous timestep
        (with several People objects, their mean weighted by their occupants of the timestep)."""
        if f'PMV_{suffix}'.upper() in sensors:
            pmv, missing = sensor_values(f'PMV_{suffix}')
            return (None, missing) if pmv is None else (outputs.previous(pmv), '')
        values, weights = [], []
        number = 1
        while f'PMV_{suffix}_{number}'.upper() in sensors:
            pmv, missing = sensor_values(f'PMV_{suffix}_{number}')
            occupants, missing_occupants = sensor_values(f'People_Occupant_Count_{suffix}_{number}')
            if pmv is None or occupants is None:
                return None, missing or missing_occupants
            values.append(outputs.previous(pmv))
            weights.append(occupants)
            number += 1
        if not values:
            return None, f'the EMS sensor PMV_{suffix}'
        return _weighted_mean(values, weights), ''

    rows: List[dict] = []
    lines: List[str] = []

    def check(found, expected, zone, name, description):
        new_rows, line = _mismatch_rows(outputs.timestamps, found, expected, zone, name, description, tolerance)
        rows.extend(new_rows)
        lines.append(line)

    with np.errstate(invalid='ignore'):
        pmv_of_zones: Dict[str, np.ndarray] = {}
        for pmv_index, suffix in zones:
            name = pmv_index.name
            pmv, missing = zone_pmv(suffix)
            found = outputs.get('EMS', f'{name}_{suffix}')
            coefficient = (outputs.get('EMS', f'{pmv_index.coefficient_output}_{suffix}')
                           if pmv_index.coefficient_output else None)
            if found is None:
                missing = f"the output '{name}_{suffix}' at timestep frequency"
            elif pmv_index.coefficient_output and coefficient is None:
                missing = f"the output '{pmv_index.coefficient_output}_{suffix}' at timestep frequency"
            if pmv is not None:
                pmv_of_zones[suffix] = pmv
            if pmv is None or missing:
                lines.append(f"  '{suffix}' Check3_{name}: not checked, without {missing}.")
                continue
            if pmv_index.key == 'apmv':
                # Yao et al. (2009)
                check(found, pmv / (1 + coefficient * pmv), suffix, 'Check3_aPMV', 'aPMV = PMV/(1 + lambda*PMV)')
            elif pmv_index.key == 'epmv':
                # Fanger and Toftum (2002): on the warm side of the scale, unless the monitor of the zone applies the
                # expectancy factor to every PMV (apply_to_heating). The argument is not stored in the model: it is
                # read from the lines of the program monitor_ePMV_<zone> of accim.sim.pmv_index, which has an 'if'
                # (e*PMV if PMV > 0) without apply_to_heating and none with it, so this check depends on those lines
                # (finding E2 of section 3.5 of the review of accim 1.2.0)
                monitor = programs.get(f'MONITOR_{name}_{suffix}'.upper())
                both_sides = monitor is not None and not any(
                    line.lower().startswith('if') for line in _program_lines(monitor))
                check(found, np.where((pmv > 0) | both_sides, coefficient * pmv, pmv), suffix, 'Check3_ePMV',
                      'ePMV = e*PMV' if both_sides else 'ePMV = e*PMV if PMV > 0')
            elif pmv_index.key == 'pmv':
                check(found, pmv, suffix, 'Check3_PMV', 'PMV of the previous timestep')
            else:
                lines.append(f"  '{suffix}': no check for the index {name}.")

        # The PPD-weighted hours of Method C of CEN/TR 16798-2 (report_ppd_weighted_hours), of each zone with them
        for pmv_index, suffix in zones:
            if f'{PPD_WEIGHTED_HOURS_PROGRAM}{suffix}'.upper() not in programs:
                continue
            name = pmv_index.name
            found = outputs.get('EMS', f'PPD Weighted Hours_{suffix}')
            hours = outputs.get('EMS', f'Occupied hours_{suffix}')
            lower, upper = (outputs.get('EMS', f'{name} {side} Setpoint No Tolerance_{suffix}')
                            for side in ('Heating', 'Cooling'))
            pmv = pmv_of_zones.get(suffix)
            monitor = programs.get(f'MONITOR_{name}_{suffix}'.upper())
            # The monitor of the aPMV has an 'if' with adaptive_coefficient_by='pmv_sign' (that of the ePMV, without
            # apply_to_heating), as in the checks of the indices above
            monitor_if = monitor is not None and any(line.lower().startswith('if') for line in _program_lines(monitor))
            missing = ''
            if found is None:
                missing = f"the output 'PPD Weighted Hours_{suffix}' at timestep frequency"
            elif hours is None or lower is None or upper is None:
                missing = (f"the outputs 'Occupied hours_{suffix}' and '{name} Heating (and Cooling) Setpoint No "
                           f"Tolerance_{suffix}' at timestep frequency")
            elif pmv is None:
                missing = 'the PMV of the zone'
            elif pmv_index.key == 'apmv' and monitor_if:
                inputs = programs.get(f'SET_ZONE_INPUT_DATA_{suffix}'.upper())
                values = {}
                for line in (_program_lines(inputs) if inputs is not None else []):
                    target, _, value = line[len('set '):].partition('=')
                    values[target.strip().upper()] = value.strip()
                try:
                    coefficients = [float(values[f'ADAP_COEFF_{side}_{suffix}'.upper()])
                                    for side in ('HEATING', 'COOLING')]
                except (KeyError, ValueError):
                    missing = f'the adaptive coefficients of the program set_zone_input_data_{suffix}'
            elif pmv_index.coefficient_output and outputs.get(
                    'EMS', f'{pmv_index.coefficient_output}_{suffix}') is None:
                missing = f"the output '{pmv_index.coefficient_output}_{suffix}' at timestep frequency"
            if missing:
                lines.append(f"  '{suffix}' Check3_PpdWeightedHours: not checked, without {missing}.")
                continue
            if pmv_index.key == 'apmv':
                # The PMV whose aPMV = PMV/(1 + lambda*PMV) is the setpoint (Yao et al., 2009)
                if monitor_if:
                    heating, cooling = coefficients
                else:
                    heating = cooling = outputs.get('EMS', f'{pmv_index.coefficient_output}_{suffix}')
                lower, upper = lower / (1 - heating * lower), upper / (1 - cooling * upper)
            elif pmv_index.key == 'epmv':
                # ePMV = e*PMV on the warm side (on both sides with apply_to_heating, whose monitor has no 'if')
                factor = outputs.get('EMS', f'{pmv_index.coefficient_output}_{suffix}')
                lower, upper = (lower if monitor_if else lower / factor), upper / factor
            ppd = ppd_from_pmv(pmv)
            weight = (np.where(pmv >= upper, ppd / ppd_from_pmv(upper), 0.0)
                      + np.where(pmv < lower, ppd / ppd_from_pmv(lower), 0.0))
            check(found, np.where(np.isnan(pmv), np.nan, weight * hours), suffix, 'Check3_PpdWeightedHours',
                  'PPD(PMV)/PPD(PMV limit) times the occupied hours, Method C of CEN/TR 16798-2')

        # The metabolic correction of the ePMV, of each People object
        corrected_people = []
        for people in get_people_objects(building):
            names = metabolic_correction_names(str(people.Name))
            if names['program'].upper() in programs:
                corrected_people.append((people, names))
        if corrected_people:
            season = None
            inputs_program = programs.get('SET_COOLING_SEASON_INPUT_DATA')
            season_program = programs.get('SET_COOLING_SEASON')
            if inputs_program is not None and season_program is not None:
                # CoolingSeason of each day, with the programs of the model
                erl = ErlProgramSet({'inputs': _program_lines(inputs_program),
                                     'season': _program_lines(season_program)},
                                    global_variables=['CoolingSeason', 'CoolSeasonStart', 'CoolSeasonEnd'])
                erl.run('inputs')
                seasons = {}
                for day in np.unique(outputs.dates.dayofyear):
                    erl.set('DayOfYear', float(day))
                    erl.run('season')
                    seasons[day] = erl.get('CoolingSeason')
                season = np.array([seasons[day] for day in outputs.dates.dayofyear], dtype=float)
            suffixes_of_people: Dict[str, List[str]] = {}
            for target in resolve_targets(building):
                for people_name in target.people_names:
                    suffixes_of_people.setdefault(str(people_name).upper(), []).append(target.ems_suffix)
            for people, names in corrected_people:
                suffix = sanitize_ems_name(str(people.Name))
                factor = outputs.get('EMS', f'Metabolic Correction Factor_{suffix}')
                zone_suffixes = suffixes_of_people.get(str(people.Name).upper(), [])
                pmvs, missing = [], ''
                for zone_suffix in zone_suffixes:
                    pmv = pmv_of_zones.get(zone_suffix)
                    if pmv is None:
                        pmv, missing = zone_pmv(zone_suffix)
                    pmvs.append(pmv)
                weights = []
                if len(zone_suffixes) > 1:
                    for zone_suffix in zone_suffixes:
                        occupants, missing_occupants = sensor_values(f'People_Occupant_Count_{zone_suffix}')
                        weights.append(occupants)
                        missing = missing or missing_occupants
                if factor is None:
                    missing = f"the output 'Metabolic Correction Factor_{suffix}' at timestep frequency"
                elif season is None:
                    missing = 'the EMS programs set_cooling_season_input_data and set_cooling_season'
                elif not zone_suffixes:
                    missing = 'the zones of the People object'
                if missing or any(pmv is None for pmv in pmvs) or any(weight is None for weight in weights):
                    lines.append(f"  '{suffix}' Check3_MetabolicFactor: not checked, without "
                                 f"{missing or 'the PMV of its zones'}.")
                    continue
                mean = pmvs[0] if len(pmvs) == 1 else _weighted_mean(pmvs, weights)
                # Fanger and Toftum (2002): 6.7 % less for each unit of PMV, in the cooling season, between 0 and 3
                expected = 1 - EPMV_MET_REDUCTION_PER_PMV * np.clip(np.where(season == 1, mean, 0), 0,
                                                                    _MAX_METABOLIC_PMV)
                check(factor, expected, suffix, 'Check3_MetabolicFactor',
                      f'1 - {EPMV_MET_REDUCTION_PER_PMV}*PMV in the cooling season')
                base, missing = sensor_values(names['base'])
                corrected = outputs.get('EMS', f'Corrected Activity Level_{suffix}')
                if base is None or corrected is None:
                    missing = missing or f"the output 'Corrected Activity Level_{suffix}' at timestep frequency"
                    lines.append(f"  '{suffix}' Check3_CorrectedActivity: not checked, without {missing}.")
                    continue
                check(corrected, base * expected, suffix, 'Check3_CorrectedActivity',
                      f'activity level*(1 - {EPMV_MET_REDUCTION_PER_PMV}*PMV)')
    return rows, lines


def _timesteps_per_hour(building, outputs: Optional[_Outputs]) -> Optional[int]:
    """The timesteps per hour of a model: those of its Timestep object (6, the default of its field in the IDD, if it
    is empty), or else those of its outputs at timestep frequency (None if it has neither)."""
    timesteps = building.idfobjects['Timestep']
    if timesteps:
        value = str(timesteps[0].Number_of_Timesteps_per_Hour).strip()
        return int(float(value)) if value else 6
    if outputs is not None and len(outputs.datetimes) > 1:
        minutes = pd.Series(np.diff(outputs.datetimes.asi8)).mode().iloc[0] / 6e10
        if minutes > 0 and 60 % minutes == 0:
            return int(60 // minutes)
    return None


def _compute_setpoints_arguments(values: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :func:`accim.sim.preview.compute_setpoints` of a zone, from the values of the variables of its
    program SetInputData_<zone> (``accim.sim.ems.inputs.INPUT_VARIABLES``).

    :raises ValueError: If the tolerances of the cooling and heating setpoints are not opposite, as
        ``setpoint_tolerance`` sets them.
    """
    import inspect
    import math

    from accim.sim.ems.drift_limiter import INPUTS as DRIFT_INPUTS
    from accim.sim.ems.inputs import INPUT_VARIABLES
    from accim.utils.ems_code import get_setpoint_ems_code

    accepted = set(inspect.signature(get_setpoint_ems_code).parameters)
    arguments = {}
    for item in INPUT_VARIABLES:
        # setpoint_tolerance is AHSTtol, and ACSTtol its opposite; compute_setpoints cannot calculate the limiter of the
        # drift of the setpoints, whose targets are its setpoints
        if (item.argument in accepted and item.variable in values and item.variable != 'ACSTtol'
                and item.variable not in DRIFT_INPUTS):
            arguments[item.argument] = values[item.variable]
    if 'ACSTtol' in values and 'AHSTtol' in values and not math.isclose(values['ACSTtol'], -values['AHSTtol']):
        raise ValueError(f"ACSTtol ({values['ACSTtol']}) is not the opposite of AHSTtol ({values['AHSTtol']})")
    return arguments


def _setpoint_mismatches(building, data: Mapping[str, pd.DataFrame], epw: str,
                         tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 4 of :func:`verify_accim_simulation`: the setpoints of each zone of an output IDF of AddAccis against
    :func:`accim.sim.preview.compute_setpoints`, and the running mean outdoor temperatures of EnergyPlus against
    :func:`accim.sim.preview.energyplus_running_means`, in the last environment of the outputs (the run period).

    :param building: The model (eppy).
    :param data: The outputs of :func:`accim.utils.outputs.read_eso_using_readvarseso`, by frequency.
    :param epw: The weather file of the simulation.
    :param tolerance: The largest difference allowed.
    :return: The mismatches, and the lines of the summary.
    """
    from accim.sim.ems.custom_regimes import OUTPUT_PREFIX as REGIME_OUTPUT_PREFIX, PROGRAM_PREFIX, parse_regime_program
    from accim.sim.ems.hook_setpoints import PROGRAM_PREFIX as HOOK_PROGRAM_PREFIX, hook_zones
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.objects import ZONE_SETPOINT_OUTPUT_VARIABLES
    from accim.sim.ems.outdoor_metric import (OUTPUT_PREFIX, begins_with_weather_file, metric_code,
                                              metric_comfort_standards)
    from accim.sim.ems.standard_lines import WEATHER_FILE_METRICS
    from accim.sim.preview import SETPOINT_EMS_VARIABLES, compute_setpoints, energyplus_running_means

    zone_programs = input_programs(building)
    if not zone_programs:
        return [], ['  Not checked: the model has no programs SetInputData_<zone> (output IDFs of AddAccis).']
    columns_of_variables = {variable: column for column, variable in SETPOINT_EMS_VARIABLES.items()}
    outputs_of_columns = {columns_of_variables[variable]: output
                          for output, (variable, _) in ZONE_SETPOINT_OUTPUT_VARIABLES.items()
                          if variable in columns_of_variables}
    chosen = None
    for frequency in ('Timestep', 'Hourly'):
        frame = data.get(frequency)
        if frame is None or frame.empty:
            continue
        outputs = _Outputs(frame)
        if any(outputs.get('EMS', f'{output}_{zone}') is not None
               for zone in zone_programs for output in outputs_of_columns.values()):
            chosen = frequency, outputs
            break
    if chosen is None:
        return [], ['  Not checked: no setpoints of the zones (Comfort Temperature_<zone>...) at timestep or hourly '
                    'frequency.']
    frequency, outputs = chosen
    run_periods = building.idfobjects['RunPeriod']
    timesteps_per_hour = _timesteps_per_hour(building, outputs if frequency == 'Timestep' else None)
    if not run_periods or timesteps_per_hour is None:
        return [], ['  Not checked: the model has no RunPeriod, or no Timestep object.']
    month, day = int(run_periods[0].Begin_Month), int(run_periods[0].Begin_Day_of_Month)
    start_date = f'{day:02d}/{month:02d}'
    environment = np.cumsum(outputs.starts)
    rows = np.flatnonzero(environment == environment[-1])
    first = outputs.dates[rows[0]]
    if (first.month, first.day) != (month, day):
        return [], [f'  Not checked: the last environment of the outputs begins on {first.day:02d}/{first.month:02d}, '
                    f'not on the first day of the RunPeriod ({start_date}).']
    timestamps = [outputs.timestamps[row] for row in rows]
    datetimes = outputs.datetimes[rows]
    mismatches: List[dict] = []
    lines = [f'  {frequency} outputs from {start_date}, {timesteps_per_hour} timesteps per hour, weather file {epw}']
    stat_file = os.path.splitext(str(epw))[0] + '.stat'
    if os.path.isfile(stat_file):
        lines.append(f'  Note: {os.path.basename(stat_file)} is next to the weather file: if it was next to the weather '
                     f'file of the simulation, EnergyPlus took the running mean of ASHRAE 55 (PMOT) from its monthly '
                     f'means, which energyplus_running_means does not reproduce (Check4_PMOT, and the setpoints with '
                     f'PMOT).')
    # The running means, those of the first People object (all have the same)
    try:
        running_means = energyplus_running_means(epw, timesteps_per_hour, start_date).set_index('date')
    except ValueError as error:
        return [], lines + [f'  Not checked: {error}']
    for column, variable in _RUNNING_MEANS.items():
        keys = outputs.keys(variable)
        if not keys:
            continue
        expected = running_means[column].reindex(outputs.dates[rows]).to_numpy(dtype=float)
        new_rows, line = _mismatch_rows(timestamps, outputs.get(keys[0], variable)[rows], expected, keys[0],
                                        f'Check4_{column}', f'{column} of energyplus_running_means', tolerance)
        mismatches.extend(new_rows)
        lines.append(line)
    previews: Dict[Tuple, pd.DataFrame] = {}
    # The outdoor metric of the custom model begins with the values of the weather file of AddAccis, or with PMOT
    metric_start = 'epw' if begins_with_weather_file(building) else 'pmot'
    # The setpoints of the zones whose setpoints a hook of the API backend sets (accim.sim.ems.hook_setpoints) are not
    # those of compute_setpoints
    hooked = {zone.upper() for zone in hook_zones(building)}
    for zone, program in zone_programs.items():
        if zone.upper() in hooked:
            lines.append(f"  '{zone}': not checked (its setpoints are those of a hook of the API backend, "
                         f"{HOOK_PROGRAM_PREFIX}{zone}).")
            continue
        try:
            inputs = read_inputs(program)
            arguments = _compute_setpoints_arguments(inputs)
            # The limiter of the drift (accim.sim.ems.drift_limiter): its targets are the setpoints of the comfort
            # standard before the minimum and maximum of the setpoints
            drift = 'DriftMode' in inputs
            if drift:
                arguments.pop('heating_setpoint_minimum', None)
                arguments.pop('cooling_setpoint_maximum', None)
            # The regimes of the custom model of the zone (accim.sim.ems.custom_regimes); those of a comfort standard
            # with regimes are those of its definition, and the other comfort standards do not use them
            regime_program = building.getobject('EnergyManagementSystem:Program', f'{PROGRAM_PREFIX}{zone}')
            if regime_program is not None and arguments.get('comfort_standard') == 99:
                arguments['custom_regimes'] = parse_regime_program(regime_program.fieldvalues[2:], zone)
            key = tuple(sorted(arguments.items()))
            if key not in previews:
                previews[key] = compute_setpoints(epw, timesteps_per_hour=timesteps_per_hour, start_date=start_date,
                                                  frequency='timestep' if frequency == 'Timestep' else 'hourly',
                                                  outdoor_metric_start=metric_start, **arguments).set_index('datetime')
        except (ValueError, TypeError) as error:
            lines.append(f"  '{zone}': not checked ({error}).")
            continue
        preview = previews[key].reindex(datetimes)
        inside = preview['Tout'].notna().to_numpy()
        if drift:
            lines.append(f"  '{zone}': the limiter of the drift of the setpoints: its targets are checked, not the "
                         f"setpoints applied.")
            for column, target in (('AHSTnoTol', 'DriftTargetAHST'), ('ACSTnoTol', 'DriftTargetACST')):
                found = outputs.get('EMS', f'{target}_{zone}')
                if found is None:
                    continue
                expected = np.where(inside, preview[column].to_numpy(dtype=float), np.nan)
                new_rows, line = _mismatch_rows(timestamps, found[rows], expected, zone, f'Check4_{target}',
                                                f'{column} of compute_setpoints', tolerance)
                mismatches.extend(new_rows)
                lines.append(line)
        for column, output in outputs_of_columns.items():
            if drift and column in ('ACST', 'AHST', 'ACSTnoTol', 'AHSTnoTol'):
                continue
            found = outputs.get('EMS', f'{output}_{zone}')
            if found is None:
                continue
            # A null value (the comfort temperature of static setpoints) is reported as 0
            expected = np.where(inside, np.nan_to_num(preview[column].to_numpy(dtype=float)), np.nan)
            new_rows, line = _mismatch_rows(timestamps, found[rows], expected, zone, f'Check4_{column}',
                                            f'{output} of compute_setpoints', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
        # The outdoor metric that the EMS programs calculate (not with 'pmot', which is PMOT): that of the custom
        # model, that of a comfort standard defined by its data (accim.sim.standards), or that of JPN Aqilah 2025 with
        # the values of a weather file (accim.sim.ems.standard_lines.WEATHER_FILE_METRICS)
        found = outputs.get('EMS', f'{OUTPUT_PREFIX}{zone}')
        standard = arguments.get('comfort_standard')
        if found is not None and ((standard in metric_comfort_standards()
                                   and metric_code(arguments.get('custom_outdoor_metric', 0)) != 0)
                                  or (standard in WEATHER_FILE_METRICS and metric_start == 'epw')):
            expected = np.where(inside, preview['Tout_metric'].to_numpy(dtype=float), np.nan)
            new_rows, line = _mismatch_rows(timestamps, found[rows], expected, zone, 'Check4_Tout_metric',
                                            f'{OUTPUT_PREFIX}{zone} of compute_setpoints', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
        # The regime of the custom model of each timestep
        found = outputs.get('EMS', f'{REGIME_OUTPUT_PREFIX}{zone}')
        if found is not None and 'custom_regime' in preview:
            expected = np.where(inside, preview['custom_regime'].to_numpy(dtype=float), np.nan)
            new_rows, line = _mismatch_rows(timestamps, found[rows], expected, zone, 'Check4_custom_regime',
                                            f'{REGIME_OUTPUT_PREFIX}{zone} of compute_setpoints', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
    return mismatches, lines


def _setpoint_limit_mismatches(building, data: Mapping[str, pd.DataFrame],
                               tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 5 of :func:`verify_accim_simulation`: the heating setpoint without the tolerance of each zone with a
    minimum (``AHSTmin`` in its program SetInputData_<zone>, :mod:`accim.sim.ems.setpoint_limits`) is not below it, and
    the cooling setpoint without the tolerance of each zone with a maximum (``ACSTmax``) is not above it; and the
    setpoints of its thermostats (with the tolerance) are not below the minimum plus the tolerance of the setpoints of
    the zone, nor above the maximum minus it (:func:`accim.sim.ems.setpoint_limits.thermostat_limits`: finding A19 of
    the self-audit of 2026-11-11, decided on 2026-11-12), in the outputs of the setpoints of the zone at timestep
    frequency, or else hourly (whose means keep the limits too).

    :return: The mismatches, and the lines of the summary (none if no zone has a minimum or a maximum).
    """
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.setpoint_limits import thermostat_limits, zone_limits

    limits = {zone: values for zone, values in zone_limits(building).items()
              if any(value is not None for value in values.values())}
    if not limits:
        return [], []
    # The limits of the thermostats: with the tolerance of the setpoints of each zone
    for zone, program in input_programs(building).items():
        if zone in limits:
            inputs = read_inputs(program)
            heating, cooling = thermostat_limits(limits[zone]['AHSTmin'], limits[zone]['ACSTmax'],
                                                 inputs.get('AHSTtol', 0), inputs.get('ACSTtol', 0))
            limits[zone] = dict(limits[zone], AHSTmin_thermostat=heating, ACSTmax_thermostat=cooling)
    outputs_of_limits = {
        'AHSTmin': ('AHSTmin_thermostat', 'Adaptive Heating Setpoint Temperature', np.maximum,
                    'minimum plus the tolerance'),
        'AHSTmin_noTol': ('AHSTmin', 'Adaptive Heating Setpoint Temperature_No Tolerance', np.maximum, 'minimum'),
        'ACSTmax': ('ACSTmax_thermostat', 'Adaptive Cooling Setpoint Temperature', np.minimum,
                    'maximum minus the tolerance'),
        'ACSTmax_noTol': ('ACSTmax', 'Adaptive Cooling Setpoint Temperature_No Tolerance', np.minimum, 'maximum'),
    }
    chosen = None
    for frequency in ('Timestep', 'Hourly'):
        frame = data.get(frequency)
        if frame is not None and not frame.empty:
            outputs = _Outputs(frame)
            if any(outputs.get('EMS', f'{output}_{zone}') is not None
                   for zone in limits for _, output, _, _ in outputs_of_limits.values()):
                chosen = frequency, outputs
                break
    if chosen is None:
        return [], ['  Not checked: no setpoints of the zones (Adaptive Heating Setpoint Temperature_<zone>...) at '
                    'timestep or hourly frequency.']
    frequency, outputs = chosen
    mismatches: List[dict] = []
    lines = [f'  {frequency} outputs']
    for zone, values in limits.items():
        for check, (variable, output, bound, side) in outputs_of_limits.items():
            limit = values.get(variable)
            found = outputs.get('EMS', f'{output}_{zone}')
            if limit is None or found is None:
                continue
            new_rows, line = _mismatch_rows(outputs.timestamps, found, bound(found, float(limit)), zone,
                                            f'Check5_{check}', f'{output}_{zone} within the {side} '
                                            f'{round(float(limit), 10):g}', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
    return mismatches, lines


def _long_term_mismatches(building, data: Mapping[str, pd.DataFrame],
                          tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 6 of :func:`verify_accim_simulation`: the long-term discomfort of each zone with the program
    CountLongTermDiscomfort_<zone> (:mod:`accim.sim.ems.long_term_discomfort`), from its occupied hours, its operative
    temperature of the previous timestep and its setpoints without the tolerance (or the constant limits of its
    program, ``long_term_range``), and that of the building, the sums of the zones, in the outputs at timestep
    frequency.

    :return: The mismatches, and the lines of the summary (none if the model has no long-term discomfort).
    """
    from accim.sim.ems.long_term_discomfort import (BUILDING, BUILDING_PROGRAM, OUTPUTS, PROGRAM_PREFIX, RUNNING_MEAN,
                                                    SeasonalRange, model_long_term_limits)

    zones = [str(p.Name)[len(PROGRAM_PREFIX):] for p in building.idfobjects['EnergyManagementSystem:Program']
             if str(p.Name).upper().startswith(PROGRAM_PREFIX.upper())
             and str(p.Name).upper() != BUILDING_PROGRAM.upper()]
    if not zones:
        return [], []
    frame = data.get('Timestep')
    if frame is None or frame.empty:
        return [], ['  Not checked: it needs the outputs at timestep frequency.']
    outputs = _Outputs(frame)
    sensors = {str(sensor.Name).upper(): (str(sensor.OutputVariable_or_OutputMeter_Index_Key_Name),
                                          str(sensor.OutputVariable_or_OutputMeter_Name))
               for sensor in building.idfobjects['EnergyManagementSystem:Sensor']}
    mismatches: List[dict] = []
    lines = ['  Timestep outputs']
    totals: Dict[str, List[np.ndarray]] = {output: [] for output in OUTPUTS}
    constant_limits = model_long_term_limits(building)
    for zone in zones:
        hours = outputs.get('EMS', f'Occupied Hours_{zone}')
        limits = constant_limits.get(zone)
        if limits is None:
            upper = outputs.get('EMS', f'Adaptive Cooling Setpoint Temperature_No Tolerance_{zone}')
            lower = outputs.get('EMS', f'Adaptive Heating Setpoint Temperature_No Tolerance_{zone}')
        elif isinstance(limits, SeasonalRange):
            # The seasonal range (finding A15 of the self-audit of 2026-11-11): the limits of each timestep are those
            # of the running mean outdoor temperature that the EMS reads at its beginning, that of the previous one
            lines.append(f"  '{zone}': the seasonal range of long_term_range, {limits.heating[0]} to "
                         f"{limits.heating[1]} °C with a running mean outdoor temperature below "
                         f"{limits.heating_below} °C, {limits.cooling[0]} to {limits.cooling[1]} °C above "
                         f"{limits.cooling_above} °C, and {limits.heating[0]} to {limits.cooling[1]} °C between them.")
            sensor = sensors.get(RUNNING_MEAN.upper())
            running_mean = None if sensor is None else outputs.get(*sensor)
            if running_mean is None:
                lower = upper = None
            else:
                season = outputs.previous(running_mean)
                lower = np.where(season < limits.heating_below, limits.heating[0],
                                 np.where(season > limits.cooling_above, limits.cooling[0], limits.heating[0]))
                upper = np.where(season < limits.heating_below, limits.heating[1],
                                 np.where(season > limits.cooling_above, limits.cooling[1], limits.cooling[1]))
                # No limits in the first timestep of each environment, whose running mean is that of the warm-up days
                lower, upper = (np.where(np.isnan(season), np.nan, values) for values in (lower, upper))
        else:
            lower, upper = limits
            lines.append(f"  '{zone}': the constant range of long_term_range, {lower} to {upper} °C.")
        sensor = sensors.get(f'{zone}_OpT'.upper())
        temperature = None if sensor is None else outputs.get(*sensor)
        found = {output: outputs.get('EMS', f'{output}_{zone}') for output in OUTPUTS}
        for output, values in found.items():
            totals[output].append(values)
        if any(values is None for values in (hours, upper, lower, temperature)):
            lines.append(f"  '{zone}': not checked, without its occupied hours, setpoints without the tolerance (or "
                         f"the running mean outdoor temperature of its seasonal range) or operative temperature at "
                         f"timestep frequency.")
            continue
        previous = outputs.previous(temperature)
        occupied = hours > 0
        above = occupied & (previous > upper)
        below = occupied & (previous < lower)
        expected = {
            'Hours Above Upper Limit': np.where(above, hours, 0.0),
            'Hours Below Lower Limit': np.where(below, hours, 0.0),
            'Degree Hours Above Upper Limit': np.where(above, (previous - upper) * hours, 0.0),
            'Degree Hours Below Lower Limit': np.where(below, (lower - previous) * hours, 0.0),
        }
        for output, values in found.items():
            if values is None:
                lines.append(f"  '{zone}' Check6_{output}: not checked, without the output {output}_{zone}.")
                continue
            # The first timestep of each environment, whose previous temperature is that of the warm-up days
            reference = np.where(np.isnan(previous), np.nan, expected[output])
            new_rows, line = _mismatch_rows(outputs.timestamps, values, reference, zone, f'Check6_{output}',
                                            f'{output}_{zone} from the operative temperature of the previous '
                                            f'timestep', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
    for output, values in totals.items():
        found = outputs.get('EMS', f'{output}_{BUILDING}')
        if found is None or any(value is None for value in values):
            lines.append(f"  '{BUILDING}' Check6_{output}: not checked, without the outputs of the building and of "
                         f"all the zones.")
            continue
        new_rows, line = _mismatch_rows(outputs.timestamps, found, sum(values), BUILDING, f'Check6_{output}',
                                        f'{output}_{BUILDING}, the sum of the zones', tolerance)
        mismatches.extend(new_rows)
        lines.append(line)
    return mismatches, lines


class AccimSimulationVerifier:
    """
    Object-oriented utility to verify ACCIM EMS simulation results.

    This class reads an EnergyPlus simulation output (either ``.csv`` or ``.eso``) and
    evaluates two primary checks to ensure adaptive comfort setups function correctly:

    - **Check 1**: Operative Temperature adherence within adjusted setpoint bounds (all timesteps).
    - **Check 2**: Window operation conditional logic for Mixed-Mode models (HVACmode = 2).

    Parameters
    ----------
    eso_file_path : str
        Absolute or relative path to the EnergyPlus output data. If an ``eplusout.csv``
        file exists alongside the ``.eso``, it is read directly to avoid the overhead of
        running ``ReadVarsESO``. Otherwise the ESO is parsed via besos.
    idf_path : str
        Path to the corresponding IDF model. Used to auto-discover EMS sensor names,
        window names, zone names, and control parameters (HVACmode, MaxWindSpeed,
        ACSTtol, AHSTtol) from the ``SetInputData_<zone>`` EMS programs (``SetInputData`` in the
        models of earlier versions of accim; with several zones, the values of the last one).
    eplus_install_dir : Optional[str], default None
        EnergyPlus installation directory, required by ``ReadVarsESO`` when falling back
        to ``.eso`` parsing.

    Attributes
    ----------
    summary : str
        Human-readable string summarising violation counts for Check 1 and Check 2.
    violations : Dict[str, pd.DataFrame]
        Raw violation rows, one per flagged timestep. Keys are ``'setpoint'`` and
        ``'window'``. Each DataFrame has columns:
        ``['timestep', 'zone_or_window', 'check', 'description', 'value_found',
        'value_expected']``.
    summary_table_setpoint : pd.DataFrame
        Aggregated count table for Check 1 violations, grouped by zone and check type.
        Columns: ``['zone_or_window', 'check', 'count']``. Empty if no violations.
    summary_table_window : pd.DataFrame
        Aggregated count table for Check 2 violations, grouped by window and condition.
        Columns: ``['zone_or_window', 'check', 'count']``. Empty if no violations.

    Check Identifiers
    -----------------
    The ``check`` column in the violation DataFrames uses the following identifiers:

    **Check 1 -- Setpoint Adherence**

    ``Check1_TooHot``
        The zone Operative Temperature (OpT) exceeds the **adjusted cooling setpoint**,
        defined as ``ACST_Sch - ACSTtol``. ``ACST_Sch`` is the per-timestep adaptive
        cooling setpoint schedule computed by the EMS; ``ACSTtol`` is the tolerance
        margin subtracted to give the effective upper comfort band limit.
        EnergyPlus columns: ``Zone Operative Temperature``,
        ``Schedule Value`` for ``ACST_Sch_<zone>``.
        A single isolated spike (one timestep violated with no violation immediately
        before or after) is **pardoned** to absorb transient thermal shocks (e.g. a brief
        window opening that lets in cold/hot air).

    ``Check1_TooCold``
        The zone Operative Temperature (OpT) falls below the **adjusted heating setpoint**,
        defined as ``AHST_Sch - AHSTtol``. ``AHST_Sch`` is the per-timestep adaptive
        heating setpoint schedule; ``AHSTtol`` is the tolerance margin subtracted to give
        the effective lower comfort band limit.
        EnergyPlus columns: ``Zone Operative Temperature``,
        ``Schedule Value`` for ``AHST_Sch_<zone>``.
        Same single-spike pardon applies as for ``Check1_TooHot``.

    **Check 2 -- Window Operation Logic (Mixed-Mode, HVACmode = 2)**

    In Mixed-Mode the EMS program ``SetWindowOperation_<window>`` controls the ventilation
    opening fraction every timestep. All seven conditions below must hold simultaneously
    for the window to be legitimately open. A violation is flagged whenever the window is
    open but any condition is not satisfied.

    Automatic pardons are applied to account for the inherent one-timestep EMS actuation lag:

    - ``close_transit``: the **last open timestep** before a window closing event is pardoned,
      because the EMS detects the condition violation at timestep t but the close command only
      takes effect at timestep t+1.
    - ``just_turned_on``: the **first timestep of HVAC activation** is pardoned for the same
      reason: the window was still open when the HVAC came on, and the EMS closes it at t+1.
    - ``open_transit`` *(Hourly frequency only)*: the **first hour of a window opening block**
      is also pardoned, because hourly averaging of mixed on/off states within the hour produces
      artificial condition overlaps that do not represent true violations.

    ``Check2_Cond1_HVACidle``
        The mechanical system must not be active while the window is open. Mixed-Mode logic
        prohibits simultaneous HVAC and natural ventilation to prevent energy waste (e.g.
        conditioned air escaping through open windows).
        EnergyPlus columns: ``Cooling Coil Total Cooling Rate``, ``Heating Coil Heating Rate``.
        Condition: CoolingRate == 0 AND HeatingRate == 0.

    ``Check2_Cond2_Occupied``
        The zone must be occupied for natural ventilation to activate. The EMS suppresses window
        opening when the zone is unoccupied to avoid unnecessary air infiltration.
        EnergyPlus column: ``People Occupant Count``.
        Condition: OccupantCount > 0.

    ``Check2_Cond3_OpT_lt_ACST``
        The zone Operative Temperature must be **below** the adaptive cooling setpoint. This
        ensures natural ventilation is only triggered when there is a genuine cooling need,
        i.e. indoor temperature has not yet reached the comfort upper limit.
        EnergyPlus columns: ``Zone Operative Temperature``,
        ``Schedule Value`` for ``ACST_Sch_<zone>`` (minus ACSTtol).
        Condition: OpT < ACST_Sch - ACSTtol.

    ``Check2_Cond4_OpT_gt_VST``
        The zone Operative Temperature must be **above** the Ventilation Setpoint Temperature
        (VST). VST is the lower thermal comfort bound: below it, natural ventilation would cause
        overcooling discomfort, so the window must stay closed.
        EnergyPlus column: EMS output ``Ventilation Setpoint Temperature`` -- a **per-timestep
        series** computed dynamically by the EMS, not a static value.
        Condition: OpT > VST.

    ``Check2_Cond5_OutT_lt_OpT``
        The outdoor air temperature must be **lower** than the indoor Operative Temperature for
        natural ventilation to be thermally effective. If outdoor air is warmer than indoors,
        opening windows would heat the space rather than cool it.
        EnergyPlus columns: ``Site Outdoor Air Drybulb Temperature``, ``Zone Operative Temperature``.
        Condition: OutdoorT < OpT.

    ``Check2_Cond6_MinOutTemp``
        The outdoor air temperature must **exceed** the Minimum Outdoor Temperature threshold.
        This prevents natural ventilation when outdoor conditions are too cold, which could cause
        thermal discomfort or damage HVAC equipment.
        EnergyPlus column: EMS output ``Minimum Outdoor Temperature for ventilation`` -- a
        **per-timestep series** computed dynamically by the EMS, not a static value.
        Condition: OutdoorT > MinOutTemp.

    ``Check2_Cond7_MaxWindSpeed``
        The outdoor wind speed must not exceed the maximum allowed threshold. High wind speeds
        can cause excessive infiltration rates, draughts, or structural concerns.
        EnergyPlus column: ``Site Wind Speed``.
        Condition: WindSpeed <= MaxWindSpeed, where MaxWindSpeed is a static scalar extracted
        from the ``SetInputData_<zone>`` EMS programs in the IDF (``SetInputData`` in earlier versions).

    Notes
    -----
    **Hourly frequency warning**: Hourly outputs are averaged over the full hour, so a window
    that opens for only 10 minutes shows a fractional opening factor. Conditions that were
    mutually exclusive within the hour (e.g. HVAC active for 10 min, window open for 50 min)
    can appear to overlap in the hourly average, causing false positives. Sub-hourly (Timestep)
    output frequency is strongly recommended for accurate verification.

    **Required EnergyPlus outputs**: All relevant ``Output:Variable`` objects must be present in
    the IDF. If any required column is missing from the CSV/ESO, a ``ValueError`` is raised
    identifying exactly which output is absent.
    """
    def __init__(
            self,
            eso_file_path: str,
            idf_path: str,
            eplus_install_dir: Optional[str] = None,
    ):
        self.eso_file_path = eso_file_path
        self.idf_path = idf_path
        self.eplus_install_dir = eplus_install_dir

        self.summary: str = ""
        self.violations: Dict[str, pd.DataFrame] = {
            "setpoint": pd.DataFrame(),
            "window": pd.DataFrame()
        }
        self.summary_table_setpoint: Optional[pd.DataFrame] = None
        self.summary_table_window: Optional[pd.DataFrame] = None

        self._evaluate()

    def _evaluate(self):
        # ─────────────────────────────────────────────────────────────────────────
        # 1. READ CSV/ESO → FLAT DATAFRAME
        # ─────────────────────────────────────────────────────────────────────────
        csv_path = self.eso_file_path.replace('.eso', '.csv')
        if os.path.exists(csv_path):
            print(f"Reading CSV file directly: {csv_path}")
            chosen_df = pd.read_csv(csv_path)
            
            if 'Date/Time' in chosen_df.columns:
                _timestamps = chosen_df['Date/Time'].astype(str)
            else:
                _timestamps = pd.Series(chosen_df.index, dtype=str)
                
            # Deduce frequency dynamically to correctly initialize chosen_freq
            chosen_freq = 'Unknown'
            dt_str = _timestamps.str.strip().str.slice(0, 5)
            if len(dt_str) > 0 and "/" in dt_str.iloc[0]:
                ts_per_day = dt_str.value_counts().mode().iloc[0]
                if ts_per_day == 24:
                    chosen_freq = 'Hourly'
                elif ts_per_day > 24:
                    chosen_freq = 'Timestep'
                elif ts_per_day == 1:
                    chosen_freq = 'Daily'
        else:
            print(f"Reading ESO file: {self.eso_file_path}")
            eso = read_eso_using_readvarseso(
                eso_file_path=self.eso_file_path,
                eplus_install_dir=self.eplus_install_dir,
                only_run_period=True,  # Note: 8832 hours often means EnergyPlus included 3 Design Days in the ESO
                cleanup=False,
            )

            all_dfs = []
            for freq, df in eso['data'].items():
                if df.empty:
                    continue
                df_flat = df.copy()
                df_flat.columns = [f"{a}:{v}" for (a, v, u) in df_flat.columns]
                df_flat['_freq'] = freq
                all_dfs.append(df_flat)

            if not all_dfs:
                warnings.warn("No simulation output data found in the ESO file.")
                self.summary = "Verification failed: No simulation output data found."
                return

            # Prefer the finest available frequency so window checks are accurate
            for fq in ('Timestep', 'Hourly', 'Daily', 'Monthly'):
                match = next((d for d in all_dfs if d['_freq'].iloc[0] == fq), None)
                if match is not None:
                    chosen_df = match.drop(columns=['_freq'])
                    chosen_freq = fq
                    break
            else:
                chosen_df = all_dfs[0].drop(columns=['_freq'])
                chosen_freq = all_dfs[0]['_freq'].iloc[0]

            _timestamps = pd.Series(chosen_df.index, dtype=object)

        print(f"Using output frequency: {chosen_freq} ({len(chosen_df)} timesteps total)")
        
        # Print warning if Hourly is selected because averaging behavior
        # can mask instantaneous states and produce artificial logic conflicts.
        if chosen_freq == 'Hourly':
            warn_msg = (
                "Warning: Hourly frequency selected. Results may be mathematically "
                "inconsistent because hourly outputs average the window openings "
                "and HVAC active states. Mid-hour transitions generally trigger "
                "false-positive overlaps. Timestep frequency is highly recommended."
            )
            print(f"[{chosen_freq}] {warn_msg}")
            warnings.warn(warn_msg)

        # ─── Remove Design Days (Sizing Period) ──────────────────────────────────
        dt_str = _timestamps.str.strip().str.slice(0, 5)
        if len(dt_str) > 0 and "/" in dt_str.iloc[0]:
            ts_per_day = dt_str.value_counts().mode().iloc[0]
            expected_annual = ts_per_day * (366 if "02/29" in dt_str.values else 365)
            
            if len(chosen_df) > expected_annual:
                drop_count = len(chosen_df) - expected_annual
                chosen_df = chosen_df.iloc[drop_count:].copy()
                _timestamps = _timestamps.iloc[drop_count:].copy()
                print(f"Dropped {drop_count} design/warm-up timesteps. Kept {len(chosen_df)} run-period timesteps.")

        chosen_df = chosen_df.reset_index(drop=True)
        _timestamps = _timestamps.reset_index(drop=True)

        def _find(area_frag: str, var_frag: str) -> Optional[str]:
            au, vu = area_frag.upper(), var_frag.upper()
            for col in chosen_df.columns:
                parts = col.upper().split(':', 1)
                if len(parts) == 2 and au in parts[0] and vu in parts[1]:
                    return col
            return None

        # ─────────────────────────────────────────────────────────────────────────
        # 2. READ IDF — zone names, window names, EMS params
        # ─────────────────────────────────────────────────────────────────────────
        print(f"Reading IDF: {self.idf_path}")
        from accim.sim.accis import load_idf
        building = load_idf(self.idf_path)

        ems_zone_map: Dict[str, str] = {}
        for sc in building.idfobjects['EnergyManagementSystem:Sensor']:
            if sc.Name.endswith('_OpT'):
                ems_zone_map[sc.Name[:-4]] = str(sc.OutputVariable_or_OutputMeter_Index_Key_Name)

        window_names: List[str] = [
            prog.Name[len('SetWindowOperation_'):]
            for prog in building.idfobjects['EnergyManagementSystem:Program']
            if prog.Name.upper().startswith('SETWINDOWOPERATION_')
        ]
        comfort_zones = [z for z in ems_zone_map if z not in window_names]

        try:
            accim_args = get_accim_args_flattened(building)
        except Exception:
            accim_args = {}

        if 'HVACmode' not in accim_args:
            raise ValueError("Required 'HVACmode' parameter not found in IDF.")
        if 'MaxWindSpeed' not in accim_args:
            raise ValueError("Required 'MaxWindSpeed' parameter not found in IDF.")

        HVACmode    = int(float(accim_args['HVACmode']))
        MaxWindSpeed= float(accim_args['MaxWindSpeed'])

        window_vent_sch_map: Dict[str, str] = {}
        for act in building.idfobjects['EnergyManagementSystem:Actuator']:
            act_name_up = act.Name.upper()
            for wname in window_names:
                if wname.upper() in act_name_up:
                    comp_id = str(act.Actuated_Component_Unique_Name)
                    if comp_id and comp_id not in ('', 'None'):
                        window_vent_sch_map[wname] = comp_id
                    break

        _acst_tol_col = _find('EMS', 'z_test_ACSTtol')
        _ahst_tol_col = _find('EMS', 'z_test_AHSTtol')
        
        acst_tol_val = float(chosen_df[_acst_tol_col].iat[0]) if _acst_tol_col else None
        ahst_tol_val = float(chosen_df[_ahst_tol_col].iat[0]) if _ahst_tol_col else None

        if acst_tol_val is None or ahst_tol_val is None:
            # Fallback securely to the SetInputData Program embedded in the IDF model (that of the first zone,
            # SetInputData_<zone>, since accim 1.0.0)
            for prog in building.idfobjects['EnergyManagementSystem:Program']:
                if prog.Name.upper() == 'SETINPUTDATA' or prog.Name.upper().startswith('SETINPUTDATA_'):
                    for i in range(1, 40):
                        field = f"Program_Line_{i}"
                        if hasattr(prog, field):
                            val = getattr(prog, field)
                            if not val: continue
                            val_str = str(val).upper().replace(' ', '')
                            if val_str.startswith('SETACSTTOL='):
                                acst_tol_val = float(val_str.split('=')[1])
                            elif val_str.startswith('SETAHSTTOL='):
                                ahst_tol_val = float(val_str.split('=')[1])
                    break

        if acst_tol_val is None or ahst_tol_val is None:
            raise ValueError("Required ACSTtol or AHSTtol variable not found in EMS output columns or SetInputData program.")
            
        acst_tol = float(acst_tol_val)
        ahst_tol = float(ahst_tol_val)

        print(f"ACSTtol={acst_tol} °C  |  AHSTtol={ahst_tol} °C")
        print(f"HVACmode={HVACmode}  |  MaxWindSpeed={MaxWindSpeed} m/s")

        # ─────────────────────────────────────────────────────────────────────────
        # 3. ACCUMULATE VIOLATIONS
        # ─────────────────────────────────────────────────────────────────────────
        violations_setpoint: List[dict] = []
        violations_window: List[dict] = []
        summary_lines = [f"Checked {len(chosen_df)} timesteps."]

        def _add(pos_array, target_list: List[dict], zone_or_window: str, check: str,
                 desc_fn, found_fn, expected_fn):
            for p in pos_array:
                target_list.append({
                    'timestep':       _timestamps.iat[p],
                    'zone_or_window': zone_or_window,
                    'check':          check,
                    'description':    desc_fn(p),
                    'value_found':    found_fn(p),
                    'value_expected': expected_fn(p),
                })

        # ─── CHECK 1: SETPOINTS ──────────────────────────────────────────────────
        print("\n--- Check 1: Temperature within adjusted setpoint bounds ---")
        summary_lines.append("\n[Check 1: Setpoints]")

        for zone in comfort_zones:
            actual_key = ems_zone_map.get(zone, zone)

            opt_col  = _find(actual_key, 'Operative Temperature') or _find(actual_key, 'Zone Operative Temperature')
            acst_col = _find(f'ACST_Sch_{zone}', 'Schedule Value')
            ahst_col = _find(f'AHST_Sch_{zone}', 'Schedule Value')

            if not opt_col: raise ValueError(f"Required 'Operative Temperature' output not found for zone '{zone}'.")
            if not acst_col: raise ValueError(f"Required 'ACST_Sch_{zone}' output not found.")
            if not ahst_col: raise ValueError(f"Required 'AHST_Sch_{zone}' output not found.")

            opt          = chosen_df[opt_col].astype(float)
            acst_limit   = chosen_df[acst_col].astype(float) - acst_tol   # ACST_SCH − ACSTtol
            ahst_limit   = chosen_df[ahst_col].astype(float) - ahst_tol   # AHST_SCH − AHSTtol

            # Too hot (pardon isolated 1-timestep spikes)
            hot_mask = (opt > acst_limit).values
            hot_prev = pd.Series(hot_mask).shift(1, fill_value=False).values
            hot_next = pd.Series(hot_mask).shift(-1, fill_value=False).values
            valid_hot = hot_mask & ~(hot_mask & ~hot_prev & ~hot_next)
            hot_pos = valid_hot.nonzero()[0]
            
            _add(hot_pos, violations_setpoint, zone, 'Check1_TooHot',
                 lambda p: f"OpT ({opt.iat[p]:.2f}°C) > ACST_SCH-ACSTtol ({acst_limit.iat[p]:.2f}°C)",
                 lambda p: round(float(opt.iat[p]), 4),
                 lambda p: f"<= {acst_limit.iat[p]:.2f}°C")

            # Too cold (pardon isolated 1-timestep spikes)
            cold_mask = (opt < ahst_limit).values
            cold_prev = pd.Series(cold_mask).shift(1, fill_value=False).values
            cold_next = pd.Series(cold_mask).shift(-1, fill_value=False).values
            valid_cold = cold_mask & ~(cold_mask & ~cold_prev & ~cold_next)
            cold_pos = valid_cold.nonzero()[0]
            
            _add(cold_pos, violations_setpoint, zone, 'Check1_TooCold',
                 lambda p: f"OpT ({opt.iat[p]:.2f}°C) < AHST_SCH-AHSTtol ({ahst_limit.iat[p]:.2f}°C)",
                 lambda p: round(float(opt.iat[p]), 4),
                 lambda p: f">= {ahst_limit.iat[p]:.2f}°C")

            n_hot, n_cold, total = len(hot_pos), len(cold_pos), len(chosen_df)
            msg = f"  Zone '{zone}': too-hot={n_hot}/{total}  |  too-cold={n_cold}/{total}"
            print(msg)
            summary_lines.append(msg)

        # ─── CHECK 2: WINDOW OPERATION ───────────────────────────────────────────
        if HVACmode == 2 and window_names:
            print("\n--- Check 2: Window operation conditions (HVACmode=2) ---")
            summary_lines.append("\n[Check 2: Windows]")

            out_t_col = _find('Environment', 'Site Outdoor Air Drybulb Temperature')
            if not out_t_col: raise ValueError("Required 'Site Outdoor Air Drybulb Temperature' column not found in output.")
            wind_col  = _find('Environment', 'Site Wind Speed')
            if not wind_col: raise ValueError("Required 'Site Wind Speed' column not found in output.")

            out_t = chosen_df[out_t_col].astype(float)
            wind  = chosen_df[wind_col].astype(float)
            
            min_out_t_col = _find('EMS', 'Minimum Outdoor Temperature for ventilation')
            if not min_out_t_col: raise ValueError("Required 'Minimum Outdoor Temperature for ventilation' EMS output not found.")
            vst_col       = _find('EMS', 'Ventilation Setpoint Temperature')
            if not vst_col: raise ValueError("Required 'Ventilation Setpoint Temperature' EMS output not found.")
            
            min_out_t_series = chosen_df[min_out_t_col].astype(float)
            vst_series = chosen_df[vst_col].astype(float)

            for wname in window_names:
                actual_win_key = ems_zone_map.get(wname, wname)

                vof_col = (
                    _find(wname, 'AFN Surface Venting Window or Door Opening Factor')
                    or _find(actual_win_key, 'AFN Surface Venting Window or Door Opening Factor')
                )
                if not vof_col:
                    sch_name = window_vent_sch_map.get(wname)
                    if sch_name: vof_col = _find(sch_name, 'Schedule Value')
                if not vof_col:
                    vof_col = _find(f'Vent_Sch_{actual_win_key}', 'Schedule Value')
                if not vof_col:
                    raise ValueError(f"Required 'Opening Factor' or 'Schedule Value' output not found for window '{wname}'.")

                opt_w_col  = _find(actual_win_key, 'Operative Temperature') or _find(actual_win_key, 'Zone Operative Temperature')
                if not opt_w_col: raise ValueError(f"Required 'Operative Temperature' output not found for zone '{actual_win_key}'.")
                
                cool_w_col = _find(actual_win_key, 'Cooling Coil Total Cooling Rate') or _find(actual_win_key, 'Cooling Rate')
                if not cool_w_col: raise ValueError(f"Required 'Cooling Rate' output not found for zone '{actual_win_key}'.")
                
                heat_w_col = _find(actual_win_key, 'Heating Coil Heating Rate') or _find(actual_win_key, 'Heating Rate')
                if not heat_w_col: raise ValueError(f"Required 'Heating Rate' output not found for zone '{actual_win_key}'.")
                
                occ_col    = _find(actual_win_key, 'People Occupant Count') or _find(wname, 'People Occupant Count')
                if not occ_col:
                    for cz in comfort_zones:
                        occ_col = _find('EMS', f'People Occupant Count_{cz}')
                        if occ_col: break
                if not occ_col: raise ValueError(f"Required 'People Occupant Count' output not found for zone '{actual_win_key}'.")

                acst_ref = None
                for cz in comfort_zones:
                    cz_col = _find(f'ACST_Sch_{cz}', 'Schedule Value')
                    if cz_col:
                        acst_ref = chosen_df[cz_col].astype(float) - acst_tol
                        break
                if acst_ref is None: raise ValueError("Required 'ACST_Sch' column not found for computing window checks.")

                vof   = chosen_df[vof_col].astype(float)
                opt_w = chosen_df[opt_w_col].astype(float)
                cool  = chosen_df[cool_w_col].astype(float)
                heat  = chosen_df[heat_w_col].astype(float)
                occ   = chosen_df[occ_col].astype(float)

                # Identify 1-timestep delay where HVAC just turned on
                hvac_now = (cool.values > 0) | (heat.values > 0)
                hvac_prev = pd.Series(hvac_now).shift(1, fill_value=False).values
                just_turned_on = hvac_now & ~hvac_prev
                
                # Identify 1-timestep delay where Window closes in the NEXT timestep.
                # This pardons transient limits (e.g. OpT falling below VST, Wind crossing MaxWindSpeed)
                # because the EMS takes 1 timestep to fully actuate the window closure.
                open_mask = (vof > 0.0).values
                open_next = pd.Series(open_mask).shift(-1, fill_value=False).values
                close_transit = open_mask & ~open_next

                # Examine timesteps where window is open AND we are not in the transit delays
                valid_open_mask = open_mask & ~just_turned_on & ~close_transit
                
                # For Hourly frequencies, averaging causes false positives when the 
                # state toggles mid-hour (e.g. window opened or HVAC activated for just 10 mins).
                # We extend the pardon to include the opening transit hour too.
                if chosen_freq == 'Hourly':
                    open_prev = pd.Series(open_mask).shift(1, fill_value=False).values
                    open_transit = open_mask & ~open_prev
                    valid_open_mask = valid_open_mask & ~open_transit

                open_pos  = valid_open_mask.nonzero()[0]
                n_open    = len(open_pos)

                if n_open == 0:
                    msg = f"  Window '{wname}': never open."
                    print(msg); summary_lines.append(msg)
                    continue

                prev = len(violations_window)

                bad = open_pos[(cool.iloc[open_pos].values > 0) | (heat.iloc[open_pos].values > 0)]
                _add(bad, violations_window, wname, 'Check2_Cond1_HVACidle',
                     lambda p: f"Window open but HVAC already active (cool={cool.iat[p]:.1f} W, heat={heat.iat[p]:.1f} W)",
                     lambda p: f"cool={cool.iat[p]:.1f}, heat={heat.iat[p]:.1f}",
                     lambda p: "Cool==0 AND Heat==0")

                bad = open_pos[occ.iloc[open_pos].values <= 0]
                _add(bad, violations_window, wname, 'Check2_Cond2_Occupied',
                     lambda p: f"Window open but zone unoccupied (Occ={occ.iat[p]:.0f})",
                     lambda p: round(float(occ.iat[p]), 4),
                     lambda p: "> 0")

                bad = open_pos[opt_w.iloc[open_pos].values >= acst_ref.iloc[open_pos].values]
                _add(bad, violations_window, wname, 'Check2_Cond3_OpT_lt_ACST',
                     lambda p: f"Window open but OpT ({opt_w.iat[p]:.2f}°C) >= roundedACST ({acst_ref.iat[p]:.2f}°C)",
                     lambda p: round(float(opt_w.iat[p]), 4),
                     lambda p: f"< {acst_ref.iat[p]:.2f}°C")

                bad = open_pos[opt_w.iloc[open_pos].values <= vst_series.iloc[open_pos].values]
                _add(bad, violations_window, wname, 'Check2_Cond4_OpT_gt_VST',
                     lambda p: f"Window open but OpT ({opt_w.iat[p]:.2f}°C) <= VST ({vst_series.iat[p]:.2f}°C)",
                     lambda p: round(float(opt_w.iat[p]), 4),
                     lambda p: f"> {vst_series.iat[p]:.2f}°C")

                bad = open_pos[out_t.iloc[open_pos].values >= opt_w.iloc[open_pos].values]
                _add(bad, violations_window, wname, 'Check2_Cond5_OutT_lt_OpT',
                     lambda p: f"Window open but OutT ({out_t.iat[p]:.2f}°C) >= OpT ({opt_w.iat[p]:.2f}°C)",
                     lambda p: round(float(out_t.iat[p]), 4),
                     lambda p: f"< OpT ({opt_w.iat[p]:.2f}°C)")

                bad = open_pos[out_t.iloc[open_pos].values <= min_out_t_series.iloc[open_pos].values]
                _add(bad, violations_window, wname, 'Check2_Cond6_MinOutTemp',
                     lambda p: f"Window open but OutT ({out_t.iat[p]:.2f}°C) <= MinOutTemp ({min_out_t_series.iat[p]:.2f}°C)",
                     lambda p: round(float(out_t.iat[p]), 4),
                     lambda p: f"> {min_out_t_series.iat[p]:.2f}°C")

                bad = open_pos[wind.iloc[open_pos].values > MaxWindSpeed]
                _add(bad, violations_window, wname, 'Check2_Cond7_MaxWindSpeed',
                     lambda p: f"Window open but WindSpeed ({wind.iat[p]:.2f} m/s) > MaxWindSpeed ({MaxWindSpeed} m/s)",
                     lambda p: round(float(wind.iat[p]), 4),
                     lambda p: f"<= {MaxWindSpeed} m/s")

                n_new = len(violations_window) - prev
                msg = f"  Window '{wname}': 7-condition violations = {n_new} (out of {n_open} open steps)."
                print(msg); summary_lines.append(msg)

        # ─────────────────────────────────────────────────────────────────────────
        # 4. STORE RESULTS
        # ─────────────────────────────────────────────────────────────────────────
        df_setpoint = pd.DataFrame(violations_setpoint)
        df_window = pd.DataFrame(violations_window)
        
        self.violations["setpoint"] = df_setpoint
        self.violations["window"] = df_window
        self.summary = "\n".join(summary_lines)

        n_s = len(df_setpoint)
        n_w = len(df_window)
        
        if n_s > 0:
            self.summary_table_setpoint = df_setpoint.groupby(['zone_or_window', 'check']).size().rename('count').reset_index()
        else:
            self.summary_table_setpoint = pd.DataFrame(columns=['zone_or_window', 'check', 'count'])
            
        if n_w > 0:
            self.summary_table_window = df_window.groupby(['zone_or_window', 'check']).size().rename('count').reset_index()
        else:
            self.summary_table_window = pd.DataFrame(columns=['zone_or_window', 'check', 'count'])

        n_s = len(self.violations['setpoint'])
        n_w = len(self.violations['window'])
        if n_s == 0 and n_w == 0:
            msg = "\n[PASS] All checks passed — no violations detected."
            print(msg); self.summary += msg
        else:
            msg = f"\n[FAIL] {n_s} setpoint violation(s), {n_w} window violation(s)."
            print(msg); self.summary += msg
