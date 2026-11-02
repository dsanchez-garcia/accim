---
title: Open questions
type: log
tags: [vault, questions]
created: 2026-09-13
---

# Open questions

Pending questions or blockers that need a human decision. Newest first.
Move a question to [[decisions.md]] once it is resolved (and delete or mark
it here as answered).

## How to use this file

```md
## YYYY-MM-DD — Short question
- Context:
- Why it matters:
- Options considered:
- Owner:
- Status: open | answered (see [[decisions.md]])
```

## Open

## 2026-11-01 — Is the scope and the technology of the first GUI right?

- Context: The author asked on 2026-11-01 for a graphical user interface in English, and the item of [[../TODO.md]] said that he would choose its scope (which steps) and technology; he could not answer, so the first version was made with the options below (see [[decisions.md#2026-11-01 — The first GUI uses tkinter and covers AddAccis, run_ep and the hours within the setpoints|the decision]]): tkinter, and three tabs (`AddAccis`, `run_ep` and the hours within the setpoints).
- Why it matters: other steps (`Table` and its figures, `rename_epw_files`, the arguments of each zone, the aPMV setpoints, the parametric module) or another technology (a web interface with Streamlit or similar, which would add a dependency) change how much the GUI covers and what users must install.
- Options considered: keep tkinter and add tabs for more steps; a web interface as an optional extra (`pip install "accim[gui]"`); leave the rest in Python.
- Owner: the author.
- Status: open.

## 2026-11-01 — Which names should the arguments of accim 1.0.0 have? (review asked by the author)

- Context: The author asked on 2026-11-01 for a review of the names of the arguments, with a suggestion for each one ("`ComfMod` no me gusta; debería ser `ComfMode`, o similar"). The names of 1.0.0 are a mechanical translation of those of 0.x to snake case (decision of 2026-10-30), so they keep the abbreviations of 0.x (`comf_mod`, `cat`, `vst_offset`...). 1.0.0 is not released, so renaming them now costs users nothing: the aliases of 0.x (`LEGACY_ARGUMENT_NAMES`) would point to the new names.
- Suggestions (current name → suggestion; "=" keeps it):

  | Group | Current (0.x) | Suggestion | Why |
  | --- | --- | --- | --- |
  | Model | `script_type` (`ScriptType`) | = | Established in the papers; its values (`vrf_ac`...) say the HVAC system and the operation |
  | Model | `supply_air_temp_input_method` | = | The field of EnergyPlus |
  | Model | `output_type`, `energyplus_version`, `hvac_zone_map`, `name_suffix`, `idfs`, `zone_arguments` | = | Clear |
  | Model | `output_freqs` (`Output_freqs`) | `output_frequencies` | No abbreviation; `apply_apmv_setpoints` says `outputs_freq` |
  | Model | `output_keep_existing` | `keep_existing_outputs` | A boolean reads as an action |
  | Model | `output_gen_dataframe` | `make_outputs_dataframe` | Like `make_averages` |
  | Model | `output_take_dataframe` | `outputs_dataframe` | It is the DataFrame of the outputs to keep |
  | Model | `temp_ctrl` (`TempCtrl`) | `setpoint_type` ('temperature' or 'pmv') | 'pmv' is not a temperature control |
  | Model | `vrf_schedule` (`VRFschedule`) | `vrf_availability_schedule` | It is the availability schedule |
  | Model | `eer`, `cop` | `vrf_eer`, `vrf_cop` | Only for the VRF systems |
  | Model | `make_averages` | `add_building_averages` | What it adds |
  | Model | `debugging` | `debug_ems` | It writes the EDD file of the EMS |
  | Model | `verbose_mode` (`verboseMode`) | `verbose` | Convention of Python |
  | Model | `confirm_gen` (`confirmGen`) | `confirm` | Shorter, without abbreviation |
  | Comfort | `comf_stand` (`ComfStand`) | `comfort_standard` | |
  | Comfort | `cat` (`CAT`) | `category` | |
  | Comfort | `comf_mod` (`ComfMod`) | `comfort_mode` | Asked by the author |
  | Comfort | `cat_cool_offset`, `cat_heat_offset` | `category_cooling_offset`, `category_heating_offset` | |
  | Comfort | `setpoint_acc` (`SetpointAcc`) | `setpoint_accuracy` | |
  | Comfort | `cool_season_start`, `cool_season_end` | `cooling_season_start`, `cooling_season_end` | The names of `apply_apmv_setpoints` |
  | Comfort | `ast_tol_start`, `ast_tol_end_input`, `ast_tol_steps` | `setpoint_tolerance_start`, `setpoint_tolerance_end`, `setpoint_tolerance_step` | "end_input" and "steps" are odd |
  | Comfort | `ast_tol` (`modify_accis`, `zone_arguments`) | `setpoint_tolerance` | |
  | Custom model | `cust_ast_m`, `cust_ast_n` | `custom_slope`, `custom_intercept` | |
  | Custom model | `cust_ast_acst_offset`, `cust_ast_ahst_offset` | `custom_cooling_offset`, `custom_heating_offset` | |
  | Custom model | `cust_ast_acst_aul`, `cust_ast_acst_all` | `custom_cooling_upper_limit`, `custom_cooling_lower_limit` | Applicability limits (running mean outdoor temperature) |
  | Custom model | `cust_ast_ahst_aul`, `cust_ast_ahst_all` | `custom_heating_upper_limit`, `custom_heating_lower_limit` | |
  | Ventilation | `hvac_mode` (`HVACmode`), `max_wind_speed` | = | Clear |
  | Ventilation | `vent_ctrl` (`VentCtrl`) | `ventilation_control` | |
  | Ventilation | `vst_offset` (`VSToffset`) | `ventilation_setpoint_offset` | |
  | Ventilation | `min_ot_offset` (`MinOToffset`) | `min_outdoor_temp_offset` | |
  | Ventilation | `max_temp_diff_vof`, `min_temp_diff_vof` | `opening_factor_max_temp_diff`, `opening_factor_min_temp_diff` | "VOF" is the venting opening factor |
  | Ventilation | `multiplier_vof` (`MultiplierVOF`) | `min_opening_factor` | It is the opening factor above the maximum temperature difference |

- Related names, to decide in the same review: `apply_apmv_setpoints` (`outputs_freq` → `output_frequencies`, `adap_coeff_cooling` → `adaptive_coefficient_cooling`, `pmv_cooling_sp` → `pmv_cooling_setpoint`, `tolerance_cooling_sp_cooling_season` → `cooling_setpoint_tolerance_cooling_season`, `dflt_for_*` → `default_*`); `run_ep` (`run_only_accim` → `only_accim_idfs`, `confirm_run` → `confirm`, `num_cpus` → `processes`, as the parametric module); the arguments and parameters of `accim.parametric_and_optimisation` (`ScriptType`, `VRFschedule`..., and `'ComfStand'`, `'ComfMod'`, `'CustAST_m'`...), which kept the names of 0.x by the decision of 2026-10-30; the columns of `Table` (`ComfStand`, `CAT`, `ComfMod`...); and the EMS variables (`ComfStand`, `ComfMod`, `CAT`, `HVACmode`, `VentCtrl`, `CustAST_*`...), which could become `ComfortStandard`, `ComfortMode`, `Category`... now that 1.0.0 changes the EMS programs anyway. The tags of the names of the output IDFs (`[CS_`, `[CA_`, `[CM_`...) should stay: `Table` reads them and the results of earlier versions have them (`CM` already reads "comfort mode").
- Why it matters: the names of 1.0.0 will be public once it is released; renaming them later needs another round of deprecated aliases.
- Options considered: (a) the suggestions above for the arguments of `AddAccis`, `add_accis_to_idf` and `modify_accis` (recommended), with the related names in the same step or later; (b) only the most confusing ones (`comf_mod`, `temp_ctrl`, `ast_tol_end_input`, `ast_tol_steps`, `cool_season_*`); (c) keep the names of 1.0.0.
- Owner: author.
- Status: open.

