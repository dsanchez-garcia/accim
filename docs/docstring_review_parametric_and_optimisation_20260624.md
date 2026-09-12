# Revision de docstrings - parametric_and_optimisation

- Fecha: 2026-06-24
- Alcance: todos los modulos, clases, funciones y metodos en `accim/parametric_and_optimisation`.
- Criterios evaluados por elemento:
  - `args`: si todos los argumentos estan explicados en la docstring (por nombre).
  - `finalidad`: si se explica funcionamiento/finalidad.
  - `uso`: si se explica como/cuando usarlo.
  - `ejemplos`: si incluye ejemplos de uso.

## Resumen global

- Elementos analizados: **390**
- Con docstring: **390**
- Sin docstring: **0**
- `args` OK (incluye N/A): **390/390**
- `finalidad` OK: **390/390**
- `uso` OK: **390/390**
- `ejemplos` OK: **390/390**

## Hallazgos criticos prioritarios

- No se detectaron hallazgos criticos (sin docstrings ni docstrings malformadas).

## Revision uno a uno

### `accim/parametric_and_optimisation/__init__.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module __init__` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/analysis.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module analysis` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `class AnalysisMixin` | 29 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._normalise_floor_area_idf_name` | 48 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._get_floor_area_idf_name` | 83 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._idf_objects` | 115 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._idf_object_items` | 154 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._first_existing_attr` | 188 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._iter_list_object_values` | 219 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._get_zone_lookup` | 260 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._get_space_to_zone_lookup` | 288 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._get_zonelist_lookup` | 318 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._get_spacelist_lookup` | 347 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._resolve_zone_like_names` | 383 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._resolve_occupied_zone_names` | 428 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._is_air_conditioning_object_class` | 463 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._is_conditioned_zone_field` | 495 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._iter_conditioned_zone_targets` | 534 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._resolve_air_conditioned_zone_names` | 578 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._sum_floor_area` | 608 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._resolve_floor_area_config` | 649 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._coerce_custom_floor_area` | 702 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._coerce_zones_list` | 728 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._load_floor_area_buildings_from_backup_paths` | 769 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._get_floor_area_buildings` | 838 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._set_and_return_building_floor_area` | 954 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._calculate_floor_area_for_idf` | 986 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._normalise_representative_mode` | 1048 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._normalise_representative_category_value` | 1073 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._representative_sort_key` | 1103 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._format_representative_values` | 1130 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._available_idf_mapping_categories` | 1154 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._get_floor_area_idf_category_groups` | 1179 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._normalise_representative_map` | 1246 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._resolve_floor_area_representative_plan` | 1287 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin.set_building_floor_area` | 1404 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin.normalize_outputs` | 1547 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin.run_sensitivity_analysis` | 1652 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._canonical_output_name` | 1748 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin._resolve_output_columns` | 1777 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin.get_best_compromise_solution` | 1876 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin.run_sensitivity_analysis_by_epw` | 1954 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin.run_clustering` | 2136 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method AnalysisMixin.run_robustness_analysis` | 2209 | Yes | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/file_cleanup.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module file_cleanup` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function _normalise_extension_token` | 23 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _normalise_extensions_list` | 66 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _normalise_policy` | 124 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function normalize_sim_file_cleanup_options` | 155 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function sim_file_policy_will_remove_extension` | 195 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function prune_simulation_output_files` | 238 | Yes | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/funcs_for_besos/__init__.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module __init__` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module param_accis` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function get_valid_param_combinations` | 53 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function drop_invalid_param_combinations` | 142 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_ComfStand` | 264 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_ACSTaul` | 285 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_ACSTall` | 306 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_AHSTaul` | 327 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_AHSTall` | 348 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_ASTall` | 369 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_ASTaul` | 391 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_m` | 413 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_n` | 435 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_ACSToffset` | 456 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_AHSToffset` | 478 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CustAST_ASToffset` | 499 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CAT` | 522 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CATcoolOffset` | 543 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CATheatOffset` | 564 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_ComfMod` | 585 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_HVACmode` | 606 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_VentCtrl` | 626 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_VSToffset` | 646 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_MinOToffset` | 666 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_MaxWindSpeed` | 686 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_ASTtol` | 706 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CoolSeasonStart` | 727 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_CoolSeasonEnd` | 752 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_SetpointAcc` | 777 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_MaxTempDiffVOF` | 797 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_MinTempDiffVOF` | 817 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function modify_MultiplierVOF` | 837 | Yes | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/funcs_for_besos/param_apmv.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module param_apmv` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function _get_apmv_program_targets` | 37 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _get_apmv_input_programs_by_target` | 67 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function change_adaptive_coeff_all_zones` | 97 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function change_adaptive_coeff_cooling_all_zones` | 139 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function change_adaptive_coeff_heating_all_zones` | 179 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function change_pmv_setpoint_all_zones` | 219 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function change_pmv_cooling_setpoint_all_zones` | 260 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function change_pmv_heating_setpoint_all_zones` | 300 | Yes | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/main.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module main` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function get_rdd_file_as_df` | 53 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function parse_mtd_file` | 74 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function get_mdd_file_as_df` | 113 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _serialize_output_func` | 134 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _resolve_output_func` | 164 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _run_single_evaluation_worker` | 199 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function compare_simulation_instances` | 399 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _collect_pickle_files` | 1393 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _order_pickle_files` | 1488 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _resolve_reference_pickle` | 1527 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function compare_latest_pickles_in_folders` | 1586 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function compare_multiple_pickles_with_reference` | 1686 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function preflight_report` | 1824 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class SimulationComparisonSession` | 1887 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession.__init__` | 1902 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession._effective_kwargs` | 1990 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession._capture` | 2030 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession.compare` | 2092 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession.compare_latest_in_folders` | 2135 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession.compare_latest_sources_in_folders` | 2182 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession._load_source_dataframe` | 2277 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession._resolve_case_insensitive_column` | 2388 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession._resolve_sources_for_output_analysis` | 2430 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession.compare_selected_outputs` | 2487 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession.compare_multiple_with_reference` | 2733 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession.save_last_report_json` | 2798 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationComparisonSession.get_last_summary` | 2827 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `class SimulationBase` | 2865 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.__init__` | 2883 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._normalize_results_root_path` | 3015 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._resolve_results_out_dir` | 3042 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._warn_if_sim_file_cleanup_can_remove_csv` | 3084 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._cleanup_simulation_output_directories` | 3128 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._save_idf_backup` | 3200 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_output_var_df_from_idf` | 3242 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_idf_identifier` | 3281 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._resolve_idf_scope` | 3310 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._idf_scope_label` | 3392 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._idfobjects_get_case` | 3419 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._norm_output_token` | 3450 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._variable_key_from_obj` | 3478 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._meter_key_from_obj` | 3506 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.scan_output_objects` | 3532 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.autocorrect_output_duplicates` | 3586 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_buildings_by_idf` | 3647 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_problem_input_names` | 3679 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_external_input_names` | 3706 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_all_input_names` | 3729 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._prepare_dataframe_for_buildings` | 3752 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_output_meter_df_from_idf` | 3835 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_output_variables_df_from_idf` | 3868 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_output_meters_df_from_idf` | 3886 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.set_output_variables_to_idf` | 3904 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.set_output_var_df_to_idf` | 4031 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.keep_only_outputs_in_idfs` | 4069 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.set_output_meters_to_idf` | 4260 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.set_output_met_objects_to_idf` | 4475 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_outputs_df_from_testsim` | 4533 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.discover_available_outputs` | 4779 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.select_outputs` | 4879 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.clear_outputs` | 5111 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.apply_outputs_preflight` | 5174 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.set_outputs_for_simulation` | 5338 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_available_parameters` | 5394 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.set_parameters` | 5417 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.set_problem` | 5599 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.sampling_full_set` | 5638 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.sampling_custom` | 5676 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._expand_samples_with_buildings_and_epws` | 5702 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.sampling_full_factorial` | 5738 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.sampling_lhs` | 5759 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_salib_problem` | 5780 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.sampling_sobol` | 5802 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.sampling_morris` | 5830 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.set_category_mapping` | 5862 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._resolve_category_for_value` | 5934 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.apply_category_mapping` | 5964 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.add_epw_suffix_category` | 6091 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.preview_category_mapping` | 6211 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._simulation_df_source_map` | 6294 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._resolve_simulation_df_source` | 6323 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._normalise_summary_count_key` | 6345 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._detect_energy_columns_from_numeric` | 6369 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_rule_based_category_candidates` | 6392 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._infer_category_columns` | 6427 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.build_simulation_summary` | 6498 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.print_simulation_summary` | 6603 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_default_simulation_summary_json_path` | 6673 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.export_simulation_summary_json` | 6705 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._refresh_simulation_summary_after_results_change` | 6764 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.set_evaluator` | 6811 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._run_evaluator_df_apply` | 6831 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._serialize_problem_outputs` | 6892 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._serialize_problem_add_outputs` | 6908 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_problem_add_output_names` | 6933 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._serialize_output_readers` | 6963 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._normalize_signature_value` | 7029 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._build_parametric_task_signature` | 7064 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._default_parametric_checkpoint_path` | 7104 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._default_parametric_batches_dir` | 7130 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._save_parametric_batch_chunk` | 7156 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._load_parametric_checkpoint_state` | 7210 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._merge_parametric_batch_pickles` | 7290 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._save_parametric_checkpoint` | 7338 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._default_optimisation_checkpoint_path` | 7425 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._save_optimisation_checkpoint` | 7451 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._load_optimisation_checkpoint` | 7513 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._iter_parametric_task_blueprints` | 7551 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._get_system_resource_snapshot` | 7657 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.preflight_report_parametric` | 7708 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.preflight_report_optimisation` | 7965 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.run_parametric_simulation` | 8135 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.load_outputs_parametric` | 8622 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.estimate_optimisation_sims` | 8722 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.run_optimisation` | 8761 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._build_full_optimisation_outputs_df` | 9216 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._make_match_key` | 9296 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._annotate_pareto_status` | 9326 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._set_optimisation_outputs` | 9406 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._save_outputs_optimisation_full` | 9469 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.load_outputs_optimisation` | 9513 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.compare_with` | 9614 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.merge` | 9693 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._merge_one` | 9763 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.merge_all` | 9856 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_hourly_df_parametric` | 9907 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_hourly_df` | 10087 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_monthly_df` | 10113 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._resolve_simulation_file_path` | 10183 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._flatten_eso_column_name` | 10235 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._extract_hourly_outputs_from_file` | 10259 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase._attach_hourly_outputs_from_simulation_files` | 10350 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_hourly_df_optimisation` | 10396 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_monthly_df_optimisation` | 10541 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method SimulationBase.get_hourly_df_columns` | 10646 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `class ParametricSimulation` | 10697 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method ParametricSimulation.__init__` | 10726 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method ParametricSimulation.outputs_param_sim` | 10793 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method ParametricSimulation.outputs_param_sim` | 10807 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class OptimisationSimulation` | 10831 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method OptimisationSimulation.__init__` | 10866 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class AccimPredefModelsParamSim` | 10943 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method AccimPredefModelsParamSim.__init__` | 10959 | Yes | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/objectives.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module objectives` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function average_results` | 34 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function sum_results` | 60 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function return_time_series` | 84 | Yes | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/parameters.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module parameters` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function accis_parameter` | 42 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function get_available_params_accim_predef_models` | 154 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function get_available_params_accim_custom_models` | 177 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function get_available_params_apmv_setpoints` | 199 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `class Parameter` | 221 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method Parameter.__init__` | 237 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method Parameter.modify` | 294 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class ComfStand` | 357 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method ComfStand.__init__` | 370 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method ComfStand.modify` | 384 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_ACSTaul` | 409 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ACSTaul.__init__` | 422 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ACSTaul.modify` | 436 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_ACSTall` | 461 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ACSTall.__init__` | 474 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ACSTall.modify` | 488 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_AHSTaul` | 513 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_AHSTaul.__init__` | 526 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_AHSTaul.modify` | 540 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_AHSTall` | 565 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_AHSTall.__init__` | 578 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_AHSTall.modify` | 592 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_ASTaul` | 617 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ASTaul.__init__` | 630 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ASTaul.modify` | 644 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_ASTall` | 669 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ASTall.__init__` | 682 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ASTall.modify` | 696 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_m` | 721 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_m.__init__` | 734 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_m.modify` | 748 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_n` | 773 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_n.__init__` | 786 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_n.modify` | 800 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_ACSToffset` | 825 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ACSToffset.__init__` | 838 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ACSToffset.modify` | 852 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_AHSToffset` | 877 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_AHSToffset.__init__` | 890 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_AHSToffset.modify` | 904 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CustAST_ASToffset` | 929 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ASToffset.__init__` | 942 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CustAST_ASToffset.modify` | 956 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CAT` | 981 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CAT.__init__` | 994 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CAT.modify` | 1008 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CATcoolOffset` | 1033 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CATcoolOffset.__init__` | 1046 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CATcoolOffset.modify` | 1060 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CATheatOffset` | 1085 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CATheatOffset.__init__` | 1098 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CATheatOffset.modify` | 1112 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class ComfMod` | 1137 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method ComfMod.__init__` | 1150 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method ComfMod.modify` | 1164 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class HVACmode` | 1189 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method HVACmode.__init__` | 1202 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method HVACmode.modify` | 1216 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class VentCtrl` | 1241 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method VentCtrl.__init__` | 1254 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method VentCtrl.modify` | 1268 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class VSToffset` | 1293 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method VSToffset.__init__` | 1306 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method VSToffset.modify` | 1320 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class MinOToffset` | 1345 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MinOToffset.__init__` | 1358 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MinOToffset.modify` | 1372 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class MaxWindSpeed` | 1397 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MaxWindSpeed.__init__` | 1410 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MaxWindSpeed.modify` | 1424 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class ASTtol` | 1449 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method ASTtol.__init__` | 1462 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method ASTtol.modify` | 1476 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CoolSeasonStart` | 1501 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CoolSeasonStart.__init__` | 1514 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CoolSeasonStart.modify` | 1528 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class CoolSeasonEnd` | 1553 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CoolSeasonEnd.__init__` | 1566 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method CoolSeasonEnd.modify` | 1580 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class SetpointAcc` | 1605 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SetpointAcc.__init__` | 1618 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method SetpointAcc.modify` | 1632 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class MaxTempDiffVOF` | 1657 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MaxTempDiffVOF.__init__` | 1670 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MaxTempDiffVOF.modify` | 1684 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class MinTempDiffVOF` | 1709 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MinTempDiffVOF.__init__` | 1722 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MinTempDiffVOF.modify` | 1736 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `class MultiplierVOF` | 1761 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MultiplierVOF.__init__` | 1774 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method MultiplierVOF.modify` | 1788 | Yes | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/params_dicts.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module params_dicts` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/patches.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module patches` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `class GlobalAllCapsDict` | 23 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method GlobalAllCapsDict.__getitem__` | 37 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _ensure_run_energyplus_copies_in_idf` | 62 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function _patched_eval_func` | 140 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _patched_to_platypus` | 340 | Yes | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/plotting.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module plotting` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `class PlottingMixin` | 28 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._safe_plot_token` | 44 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._summarise_placeholder_values` | 69 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._get_mapping_placeholder_columns` | 102 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._build_filename_template_context` | 163 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._resolve_output_filename` | 203 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._ensure_unique_output_path` | 266 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._is_energy_like_column` | 300 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._get_plot_source_df` | 325 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._apply_plot_data_filter` | 361 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.get_filtered_results_table` | 408 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._normalise_plot_columns` | 463 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._filter_epw_rows` | 535 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._find_first_column_contains` | 570 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._collect_subplot_dimension_values` | 602 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin._resolve_subplot_dimension_orders` | 635 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.prepare_hourly_long_df` | 681 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_hourly_scatter` | 835 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_hourly_lines` | 1077 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_best_compromise_solutions` | 1318 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_pareto_front` | 1598 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_parallel_coordinates` | 1799 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_pairwise_scatter_matrix` | 1912 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_categorical_boxplots` | 2085 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_parametric_scatter` | 2420 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_parametric_lines` | 2629 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_parametric_heatmap` | 2834 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_parametric_contour` | 3042 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_parametric_distributions` | 3242 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_parametric_ecdf` | 3457 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_parametric_density_2d` | 3619 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `method PlottingMixin.plot_parametric_radar` | 3860 | Yes | Yes | Yes | Yes | OK en criterios evaluados |

### `accim/parametric_and_optimisation/utils.py`

| Elemento | Linea | args | finalidad | uso | ejemplos | Observaciones |
|---|---:|:---:|:---:|:---:|:---:|---|
| `module utils` | 1 | N/A | Yes | Yes | Yes | OK en criterios evaluados |
| `function descriptor_has_options` | 38 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function expand_to_hourly_dataframe` | 80 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function identify_hourly_columns` | 162 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function make_all_combinations` | 200 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _subplot_sort_key` | 225 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _subplot_custom_match_key` | 252 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _can_sort_subplot_values_numerically` | 280 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _is_data_filter_sequence` | 313 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _casefold_if_needed` | 339 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _normalise_series_for_text` | 367 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _match_scalar_condition` | 394 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _match_sequence_condition` | 426 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _numeric_compare_series` | 458 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function _build_filter_mask` | 499 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function apply_data_filter` | 583 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function resolve_subplot_order` | 685 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
| `function resolve_subplot_orders` | 760 | Yes | Yes | Yes | Yes | OK en criterios evaluados |
