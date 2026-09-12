"""
Test 02 — AccimPredefModelsParamSim + bypass_addAccis + parameters_type=None
=============================================================================
Clases:
  - AccimPredefModelsParamSim: wrapper de conveniencia
  - ParametricSimulation(bypass_addAccis=True): reutilizar IDF ya modificado
  - ParametricSimulation(parameters_type=None): simulación sin addAccis
Métodos cubiertos:
  AccimPredefModelsParamSim.__init__, set_parameters (opciones predefinidas),
  sampling_full_set, set_problem,
  sampling_custom(dict), sampling_custom(DataFrame), sampling_custom(list_of_dicts),
  set_building_floor_area(mode='custom'), set_building_floor_area(mode='list'),
  run_parametric_simulation, get_hourly_df, get_monthly_df,
  plot_categorical_boxplots(sharey=False, show_points=False),
  ParametricSimulation(bypass_addAccis=True) — flujo completo
IDFs: SF_Detached_B_min_North.idf (principal) + SF_Detached_D_min_North.idf (bypass)
EPWs: seville_2024, madrid_2024 (sólo 2 para rapidez)
"""

import os
import accim
import accim.utils
import pandas as pd
from besos import eppy_funcs as ef
from accim.parametric_and_optimisation.main import (
    ParametricSimulation,
    AccimPredefModelsParamSim,
)
import accim.sim.accis_single_idf_funcs as accis_funcs

OUT_DIR_WRAPPER  = 'test_02_wrapper_results'
OUT_DIR_BYPASS   = 'test_02_bypass_results'
OUT_DIR_NONE     = 'test_02_none_results'

IDF_B = 'SF_Detached_B_min_North.idf'
IDF_D = 'SF_Detached_D_min_North.idf'
IDF_OSM = 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf'
EPW_SEV = 'seville_2024.epw'
EPW_MAD = 'madrid_2024.epw'

# ---------------------------------------------------------------------------
# PARTE A — AccimPredefModelsParamSim (wrapper de conveniencia)
# ---------------------------------------------------------------------------
print("\n=== PARTE A: AccimPredefModelsParamSim ===")

building_b = ef.get_building(IDF_B)
accim.utils.reduce_runtime(
    idf_object=building_b,
    runperiod_begin_month=6,
    runperiod_begin_day_of_month=1,
    runperiod_end_month=7,
    runperiod_end_day_of_month=31,
)

# Agregar período de sizing para VRF autosizing (requerido por EnergyPlus)
building_b.newidfobject(
    'SIZINGPERIOD:WEATHERFILEDAYS',
    Name='SummerSizing',
    Begin_Month=6,
    Begin_Day_of_Month=1,
    End_Month=7,
    End_Day_of_Month=31,
    Day_of_Week_for_Start_Day='Sunday',
    Use_Weather_File_Daylight_Saving_Period='Yes',
    Use_Weather_File_Rain_and_Snow_Indicators='Yes'
)

wrapper_sim = AccimPredefModelsParamSim(
    buildings=[building_b],
    epws=[EPW_SEV, EPW_MAD],
    output_type='simplified',
    output_freqs=['hourly'],
    ScriptType='vrf_mm',
)

# Meters disponibles desde el IDF (el wrapper ya aplicó addAccis)
wrapper_sim.set_output_meters_to_idf(output_meters=['Heating:Electricity', 'Cooling:Electricity'])
outputs_from_testsim = wrapper_sim.discover_available_outputs(reduce_sim_time=True)
df_meters_ts = outputs_from_testsim['meters']
df_meters_problem = df_meters_ts[
    df_meters_ts['key_name'].isin(['Heating:Electricity', 'Cooling:Electricity'])
].drop_duplicates(subset=['key_name'])
wrapper_sim.set_output_readers(df_output_meter=df_meters_problem)

# Parámetros
wrapper_sim.set_parameters(accis_params_dict={'ComfStand': [0, 2]})   # CTE + ASHRAE55
wrapper_sim.sampling_full_set()
wrapper_sim.set_problem()

# set_building_floor_area mode='custom'
area_custom = wrapper_sim.set_building_floor_area(mode='custom', custom_area=120.0)
print(f"  Área custom: {area_custom} m²")
assert area_custom == 120.0

# set_category_mapping básico
wrapper_sim.set_category_mapping(
    epw_mapping_rules={'city': {'seville': ['seville'], 'madrid': ['madrid']}},
)
wrapper_sim.preview_category_mapping()

results_wrapper = wrapper_sim.run_parametric_simulation(
    out_dir=OUT_DIR_WRAPPER,
    processes=1,
    keep_dirs=True,
    keep_input=True,
)
print(f"  Filas wrapper: {len(results_wrapper)}")
assert not results_wrapper.empty
assert 'city' in results_wrapper.columns

# Hourly + Monthly
wrapper_sim.get_hourly_df(start_date='2024-06-01 01')
wrapper_sim.get_monthly_df(start_date='2024-06-01 01')
print(f"  Monthly shape: {wrapper_sim.outputs_param_simulation_monthly.shape}")

# plot_categorical_boxplots — sharey=False, show_points=False
wrapper_sim.plot_categorical_boxplots(
    df_source='parametric',
    col='city',
    out_dir=OUT_DIR_WRAPPER,
    sharey=False,
    show_points=False,
)

# ---------------------------------------------------------------------------
# PARTE B — ParametricSimulation(bypass_addAccis=True)
# ---------------------------------------------------------------------------
print("\n=== PARTE B: bypass_addAccis=True ===")

# Aplicar addAccis manualmente al IDF_OSM antes de pasar a ParametricSimulation
building_osm = ef.get_building(IDF_OSM)
building_osm.newidfobject(
    'SIZINGPERIOD:WEATHERFILEDAYS',
    Name='SummerSizing',
    Begin_Month=6,
    Begin_Day_of_Month=1,
    End_Month=7,
    End_Day_of_Month=31,
    Day_of_Week_for_Start_Day='Sunday',
    Use_Weather_File_Daylight_Saving_Period='Yes',
    Use_Weather_File_Rain_and_Snow_Indicators='Yes'
)

accim.utils.reduce_runtime(
    idf_object=building_osm,
    runperiod_begin_month=6,
    runperiod_begin_day_of_month=1,
    runperiod_end_month=7,
    runperiod_end_day_of_month=31,
)
accis_funcs.addAccis(
    idf=building_osm,
    ScriptType='vrf_mm',
    Output_type='simplified',
    Output_freqs=['hourly'],
    TempCtrl='temperature',
    SupplyAirTempInputMethod='temperature difference',
    verboseMode=False,
)

bypass_sim = ParametricSimulation(
    buildings=[building_osm],
    epws=[EPW_SEV, EPW_MAD],
    parameters_type='accim predefined model',
    output_type='simplified',
    output_freqs=['hourly'],
    bypass_addAccis=True,   # <-- NO re-aplica addAccis
)

bypass_sim.set_output_meters_to_idf(output_meters=['Heating:Electricity', 'Cooling:Electricity'])
outputs_from_testsim = bypass_sim.discover_available_outputs(reduce_sim_time=True)
df_meters_bp = outputs_from_testsim['meters']
df_meters_bp = df_meters_bp[
    df_meters_bp['key_name'].isin(['Heating:Electricity', 'Cooling:Electricity'])
].drop_duplicates(subset=['key_name'])
bypass_sim.set_output_readers(df_output_meter=df_meters_bp)

bypass_sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
bypass_sim.sampling_full_set()
bypass_sim.set_problem()

# set_building_floor_area mode='list' — usar primer zone del IDF
zones = [z.Name for z in building_osm.idfobjects['ZONE']]
area_list = bypass_sim.set_building_floor_area(mode='list', zones_list=zones[:1])
print(f"  Área (mode='list', zones={zones[:1]}): {area_list}")

results_bypass = bypass_sim.run_parametric_simulation(
    out_dir=OUT_DIR_BYPASS,
    processes=1,
    keep_dirs=True,
    keep_input=True,
)
print(f"  Filas bypass: {len(results_bypass)}")
assert not results_bypass.empty

bypass_sim.get_hourly_df(start_date='2024-06-01 01')
bypass_sim.get_monthly_df(start_date='2024-06-01 01')
bypass_sim.plot_categorical_boxplots(
    df_source='parametric',
    out_dir=OUT_DIR_BYPASS,
    sharey=True,
    show_points=True,
)

# ---------------------------------------------------------------------------
# PARTE C — ParametricSimulation(parameters_type=None)
# ---------------------------------------------------------------------------
print("\n=== PARTE C: parameters_type=None ===")

building_none = ef.get_building(IDF_B)
accim.utils.reduce_runtime(
    idf_object=building_none,
    runperiod_begin_month=6,
    runperiod_begin_day_of_month=1,
    runperiod_end_month=7,
    runperiod_end_day_of_month=31,
)

# Agregar período de sizing para cualquier equipo que requiera autosizing
building_none.newidfobject(
    'SIZINGPERIOD:WEATHERFILEDAYS',
    Name='SummerSizing',
    Begin_Month=6,
    Begin_Day_of_Month=1,
    End_Month=7,
    End_Day_of_Month=31,
    Day_of_Week_for_Start_Day='Sunday',
    Use_Weather_File_Daylight_Saving_Period='Yes',
    Use_Weather_File_Rain_and_Snow_Indicators='Yes'
)

none_sim = ParametricSimulation(
    buildings=[building_none],
    epws=[EPW_SEV, EPW_MAD],
    parameters_type=None,   # sin addAccis
    output_freqs=['hourly'],
)

# Añadir meters estándar directamente
none_sim.set_output_meters_to_idf(output_meters=['Heating:Electricity', 'Cooling:Electricity'])
outputs_from_testsim = none_sim.discover_available_outputs(reduce_sim_time=True)
df_meters_none = outputs_from_testsim['meters']
df_meters_none = df_meters_none[
    df_meters_none['key_name'].isin(['Heating:Electricity', 'Cooling:Electricity'])
].drop_duplicates(subset=['key_name'])
none_sim.set_output_readers(df_output_meter=df_meters_none)

# Sin parámetros accim → set_parameters vacío
none_sim.set_parameters()
none_sim.set_problem()

# sampling_custom — variante dict: {idf_name: [epws]}
none_sim.sampling_custom(
    custom_plan={'SF_Detached_B_min_North': [EPW_SEV, EPW_MAD]}
)
print(f"  parameters_values_df (dict):\n{none_sim.parameters_values_df}")

# sampling_custom — variante list of dicts
none_sim.sampling_custom(
    custom_plan=[
        {'idf': 'SF_Detached_B_min_North', 'epw': EPW_SEV},
        {'idf': 'SF_Detached_B_min_North', 'epw': EPW_MAD},
    ]
)
print(f"  parameters_values_df (list):\n{none_sim.parameters_values_df}")

# sampling_custom — variante DataFrame
df_plan = pd.DataFrame({
    'idf': ['SF_Detached_B_min_North', 'SF_Detached_B_min_North'],
    'epw': [EPW_SEV, EPW_MAD],
})
none_sim.sampling_custom(custom_plan=df_plan)
print(f"  parameters_values_df (DataFrame):\n{none_sim.parameters_values_df}")

none_sim.set_category_mapping(
    epw_mapping_rules={'city': {'seville': ['seville'], 'madrid': ['madrid']}},
)

results_none = none_sim.run_parametric_simulation(
    out_dir=OUT_DIR_NONE,
    processes=1,
    keep_dirs=True,
    keep_input=True,
)
print(f"  Filas (parameters_type=None): {len(results_none)}")
assert not results_none.empty

none_sim.get_hourly_df(start_date='2024-06-01 01')
none_sim.get_monthly_df(start_date='2024-06-01 01')
none_sim.plot_categorical_boxplots(
    df_source='parametric',
    col='city',
    out_dir=OUT_DIR_NONE,
)

print(f"\n=== SCRIPT 2 COMPLETADO — outputs en '{OUT_DIR_WRAPPER}/', '{OUT_DIR_BYPASS}/', '{OUT_DIR_NONE}/' ===")
