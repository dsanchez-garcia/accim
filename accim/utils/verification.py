# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Verification of the simulations of the models of accim: checks of the outputs against the arguments of
the ACCIS."""

import os
import warnings
from typing import Dict, List, Optional

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
) -> pd.DataFrame:
    """
    Reads EnergyPlus simulation output and verifies that the ACCIS EMS scripts
    added by AddAccis are working correctly.

    The function performs two categories of checks:

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

    :param eso_file_path: Path to the eplusout.eso file.
    :type eso_file_path: str
    :param idf_path: Path to the IDF file used for simulation (to read accim args and window names).
    :type idf_path: str
    :param eplus_install_dir: Path to EnergyPlus installation directory (for ReadVarsESO).
    :type eplus_install_dir: str, optional
    :param tolerance: Temperature tolerance in °C for setpoint checks. Default is 0.1 °C.
    :type tolerance: float
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
    from besos.eppy_funcs import get_building
    building = get_building(idf_path)

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
    print(f"  EMS→EP key map: { {k: v for k, v in ems_zone_map.items()} }")
    print(f"Mixed-mode model: {is_mixed_mode}  |  Windows detected: {window_names}")
    if window_vent_sch_map:
        print(f"  Window→VentSchedule map: {window_vent_sch_map}")
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
    # 6. RETURN RESULTS
    # ─────────────────────────────────────────────
    result_df = pd.DataFrame(mismatch_rows)

    if result_df.empty:
        print("\n✓ All checks passed. No mismatches detected.")
    else:
        print(f"\n✗ {len(result_df)} mismatch(es) detected across "
              f"{result_df['check'].nunique()} check type(s).")
        print(result_df.groupby(['zone_or_window', 'check']).size()
              .rename('count').reset_index().to_string(index=False))

    return result_df


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
        ACSTtol, AHSTtol) from the ``SetInputData`` EMS program.
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
        from the ``SetInputData`` EMS program in the IDF.

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
        from besos.eppy_funcs import get_building
        building = get_building(self.idf_path)

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
            # Fallback securely to the SetInputData Program embedded in the IDF model
            for prog in building.idfobjects['EnergyManagementSystem:Program']:
                if prog.Name.upper() == 'SETINPUTDATA':
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
                 lambda p: f"OpT ({opt.iat[p]:.2f}°C) > ACST_SCH−ACSTtol ({acst_limit.iat[p]:.2f}°C)",
                 lambda p: round(float(opt.iat[p]), 4),
                 lambda p: f"<= {acst_limit.iat[p]:.2f}°C")

            # Too cold (pardon isolated 1-timestep spikes)
            cold_mask = (opt < ahst_limit).values
            cold_prev = pd.Series(cold_mask).shift(1, fill_value=False).values
            cold_next = pd.Series(cold_mask).shift(-1, fill_value=False).values
            valid_cold = cold_mask & ~(cold_mask & ~cold_prev & ~cold_next)
            cold_pos = valid_cold.nonzero()[0]
            
            _add(cold_pos, violations_setpoint, zone, 'Check1_TooCold',
                 lambda p: f"OpT ({opt.iat[p]:.2f}°C) < AHST_SCH−AHSTtol ({ahst_limit.iat[p]:.2f}°C)",
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
