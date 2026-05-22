# %% [markdown]
# Smoke check del workflow de outputs (estilo notebook)
#
# Objetivos:
# 1) Verificar que al instanciar no se pierden outputs añadidos por usuario.
# 2) Verificar autocorrección de duplicados en init (Output:Variable y Output:Meter).
# 3) Verificar set_output_variables_to_idf con mode='append' y mode='replace'.
# 4) Verificar que set_output_meters_to_idf evita duplicados.
# 5) Verificar que apply_outputs_preflight por defecto usa clean_mode='none'.
# 6) Verificar protección anti-duplicado en aPMV al reaplicar salidas.

# %%
from pathlib import Path
import inspect
import warnings
import pandas as pd
from besos import eppy_funcs as ef

from accim.parametric_and_optimisation.main import ParametricSimulation
import accim.sim.apmv_setpoints as apmv

print("Python imports OK")

# %%
repo_root = Path(__file__).resolve().parents[1]
test_data_dir = repo_root / "tests" / "test_data"
idf_path = test_data_dir / "SF_Detached_B_min_North.idf"
epw_path = test_data_dir / "seville_2024.epw"

assert idf_path.exists(), f"No existe IDF de test: {idf_path}"
assert epw_path.exists(), f"No existe EPW de test: {epw_path}"

print(f"IDF: {idf_path}")
print(f"EPW: {epw_path}")

# %%
# Preparar un building con outputs de usuario + duplicados intencionales
building = ef.get_building(str(idf_path))

user_var = {
    "Key_Value": "USER_OBJECT",
    "Variable_Name": "USER CUSTOM VARIABLE",
    "Reporting_Frequency": "Hourly",
    "Schedule_Name": "",
}
user_meter = {
    "Key_Name": "USER:CUSTOM:METER",
    "Reporting_Frequency": "Hourly",
}

# Output:Variable usuario
building.newidfobject(
    "OUTPUT:VARIABLE",
    Key_Value=user_var["Key_Value"],
    Variable_Name=user_var["Variable_Name"],
    Reporting_Frequency=user_var["Reporting_Frequency"],
    Schedule_Name=user_var["Schedule_Name"],
)
# Duplicado intencional de Output:Variable
building.newidfobject(
    "OUTPUT:VARIABLE",
    Key_Value=user_var["Key_Value"],
    Variable_Name=user_var["Variable_Name"],
    Reporting_Frequency=user_var["Reporting_Frequency"],
    Schedule_Name=user_var["Schedule_Name"],
)

# Output:Meter usuario
building.newidfobject(
    "OUTPUT:METER",
    Key_Name=user_meter["Key_Name"],
    Reporting_Frequency=user_meter["Reporting_Frequency"],
)
# Duplicado intencional de Output:Meter
building.newidfobject(
    "OUTPUT:METER",
    Key_Name=user_meter["Key_Name"],
    Reporting_Frequency=user_meter["Reporting_Frequency"],
)

output_vars_before = list(building.idfobjects.get("Output:Variable", []))
if len(output_vars_before) == 0:
    output_vars_before = list(building.idfobjects.get("OUTPUT:VARIABLE", []))

output_meters_before = list(building.idfobjects.get("Output:Meter", []))
if len(output_meters_before) == 0:
    output_meters_before = list(building.idfobjects.get("OUTPUT:METER", []))

var_count_before = len(output_vars_before)
meter_count_before = len(output_meters_before)

var_dup_before = sum(
    1
    for o in output_vars_before
    if str(getattr(o, "Key_Value", "")).strip().upper() == user_var["Key_Value"]
    and str(getattr(o, "Variable_Name", "")).strip().upper() == user_var["Variable_Name"]
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == user_var["Reporting_Frequency"].upper()
)

meter_dup_before = sum(
    1
    for o in output_meters_before
    if str(getattr(o, "Key_Name", "")).strip().upper() == user_meter["Key_Name"]
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == user_meter["Reporting_Frequency"].upper()
)

print(f"Antes de init -> Output:Variable total={var_count_before}, duplicados target={var_dup_before}")
print(f"Antes de init -> Output:Meter total={meter_count_before}, duplicados target={meter_dup_before}")
assert var_dup_before >= 2
assert meter_dup_before >= 2

# %%
# Instanciar y verificar:
# - autocorrección de duplicados con warning
# - preservación de outputs usuario
with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter("always")
    sim = ParametricSimulation(
        buildings=[building],
        epws=[str(epw_path)],
        parameters_type="accim predefined model",
        output_type="standard",
        output_freqs=["hourly"],
        verbosemode=False,
    )

messages = [str(w.message) for w in captured]
dedup_warnings = [m for m in messages if "duplicated output objects" in m.lower()]
print(f"Warnings de autocorrección detectados: {len(dedup_warnings)}")
if len(dedup_warnings) == 0:
    print("No se capturó warning de duplicados. Mensajes capturados:")
    for m in messages:
        print(" -", m)

removed_vars_init = int(sim.outputs_duplicates_initial_.get("removed_variables", 0))
removed_meters_init = int(sim.outputs_duplicates_initial_.get("removed_meters", 0))
print(f"Reporte init duplicados -> vars removidas={removed_vars_init}, meters removidos={removed_meters_init}")
assert (removed_vars_init + removed_meters_init) >= 1

building_after = sim.buildings[0]

var_dup_after = sum(
    1
    for o in (
        list(building_after.idfobjects.get("Output:Variable", []))
        if len(list(building_after.idfobjects.get("Output:Variable", []))) > 0
        else list(building_after.idfobjects.get("OUTPUT:VARIABLE", []))
    )
    if str(getattr(o, "Key_Value", "")).strip().upper() == user_var["Key_Value"]
    and str(getattr(o, "Variable_Name", "")).strip().upper() == user_var["Variable_Name"]
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == user_var["Reporting_Frequency"].upper()
)

meter_dup_after = sum(
    1
    for o in (
        list(building_after.idfobjects.get("Output:Meter", []))
        if len(list(building_after.idfobjects.get("Output:Meter", []))) > 0
        else list(building_after.idfobjects.get("OUTPUT:METER", []))
    )
    if str(getattr(o, "Key_Name", "")).strip().upper() == user_meter["Key_Name"]
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == user_meter["Reporting_Frequency"].upper()
)

print(f"Después de init -> duplicados target Output:Variable={var_dup_after}, Output:Meter={meter_dup_after}")
assert var_dup_after == 1
assert meter_dup_after == 1

# %%
# Verificar mode='append' en set_output_variables_to_idf: no duplica existentes y añade faltantes
append_df = pd.DataFrame(
    [
        {
            "key_value": user_var["Key_Value"],
            "variable_name": user_var["Variable_Name"],
            "frequency": "hourly",
            "schedule_name": "",
        },
        {
            "key_value": "APPEND_ONLY",
            "variable_name": "APPEND TEST VARIABLE",
            "frequency": "hourly",
            "schedule_name": "",
        },
        {
            "key_value": "APPEND_ONLY",
            "variable_name": "APPEND TEST VARIABLE",
            "frequency": "hourly",
            "schedule_name": "",
        },
    ]
)

sim.set_output_variables_to_idf(df_output_variable=append_df, mode="append")

user_var_count_post_append = sum(
    1
    for o in (
        list(sim.buildings[0].idfobjects.get("Output:Variable", []))
        if len(list(sim.buildings[0].idfobjects.get("Output:Variable", []))) > 0
        else list(sim.buildings[0].idfobjects.get("OUTPUT:VARIABLE", []))
    )
    if str(getattr(o, "Key_Value", "")).strip().upper() == user_var["Key_Value"]
    and str(getattr(o, "Variable_Name", "")).strip().upper() == user_var["Variable_Name"]
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == "HOURLY"
)

append_only_count = sum(
    1
    for o in (
        list(sim.buildings[0].idfobjects.get("Output:Variable", []))
        if len(list(sim.buildings[0].idfobjects.get("Output:Variable", []))) > 0
        else list(sim.buildings[0].idfobjects.get("OUTPUT:VARIABLE", []))
    )
    if str(getattr(o, "Key_Value", "")).strip().upper() == "APPEND_ONLY"
    and str(getattr(o, "Variable_Name", "")).strip().upper() == "APPEND TEST VARIABLE"
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == "HOURLY"
)

print(f"Post append -> USER CUSTOM VARIABLE={user_var_count_post_append}, APPEND TEST VARIABLE={append_only_count}")
assert user_var_count_post_append == 1
assert append_only_count == 1

# %%
# Verificar mode='replace': reemplaza todos los Output:Variable por los de entrada
replace_df = pd.DataFrame(
    [
        {
            "key_value": "REPLACE_ONLY",
            "variable_name": "REPLACE TEST VARIABLE",
            "frequency": "hourly",
            "schedule_name": "",
        }
    ]
)

sim.set_output_variables_to_idf(df_output_variable=replace_df, mode="replace")

replace_count = sum(
    1
    for o in (
        list(sim.buildings[0].idfobjects.get("Output:Variable", []))
        if len(list(sim.buildings[0].idfobjects.get("Output:Variable", []))) > 0
        else list(sim.buildings[0].idfobjects.get("OUTPUT:VARIABLE", []))
    )
    if str(getattr(o, "Key_Value", "")).strip().upper() == "REPLACE_ONLY"
    and str(getattr(o, "Variable_Name", "")).strip().upper() == "REPLACE TEST VARIABLE"
)

old_user_count_after_replace = sum(
    1
    for o in (
        list(sim.buildings[0].idfobjects.get("Output:Variable", []))
        if len(list(sim.buildings[0].idfobjects.get("Output:Variable", []))) > 0
        else list(sim.buildings[0].idfobjects.get("OUTPUT:VARIABLE", []))
    )
    if str(getattr(o, "Key_Value", "")).strip().upper() == user_var["Key_Value"]
    and str(getattr(o, "Variable_Name", "")).strip().upper() == user_var["Variable_Name"]
)

print(f"Post replace -> REPLACE TEST VARIABLE={replace_count}, USER CUSTOM VARIABLE={old_user_count_after_replace}")
assert replace_count == 1
assert old_user_count_after_replace == 0

# %%
# Verificar set_output_meters_to_idf: no duplica al reinsertar
sim.output_freqs = ["hourly"]
sim.set_output_meters_to_idf(output_meters=[user_meter["Key_Name"]], validate=False)
sim.set_output_meters_to_idf(output_meters=[user_meter["Key_Name"]], validate=False)

meter_df_advanced = pd.DataFrame(
    [
        {"key_name": "DF_ONLY:METER", "frequency": "daily"},
        {"key_name": "DF_ONLY:METER", "frequency": "daily"},
    ]
)
sim.set_output_meters_to_idf(df_output_meter=meter_df_advanced, validate=False)

meter_count_final = sum(
    1
    for o in (
        list(sim.buildings[0].idfobjects.get("Output:Meter", []))
        if len(list(sim.buildings[0].idfobjects.get("Output:Meter", []))) > 0
        else list(sim.buildings[0].idfobjects.get("OUTPUT:METER", []))
    )
    if str(getattr(o, "Key_Name", "")).strip().upper() == user_meter["Key_Name"]
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == "HOURLY"
)

print(f"Output:Meter USER:CUSTOM:METER (hourly) -> {meter_count_final}")
assert meter_count_final == 1

df_meter_daily_count = sum(
    1
    for o in (
        list(sim.buildings[0].idfobjects.get("Output:Meter", []))
        if len(list(sim.buildings[0].idfobjects.get("Output:Meter", []))) > 0
        else list(sim.buildings[0].idfobjects.get("OUTPUT:METER", []))
    )
    if str(getattr(o, "Key_Name", "")).strip().upper() == "DF_ONLY:METER"
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == "DAILY"
)

df_meter_hourly_count = sum(
    1
    for o in (
        list(sim.buildings[0].idfobjects.get("Output:Meter", []))
        if len(list(sim.buildings[0].idfobjects.get("Output:Meter", []))) > 0
        else list(sim.buildings[0].idfobjects.get("OUTPUT:METER", []))
    )
    if str(getattr(o, "Key_Name", "")).strip().upper() == "DF_ONLY:METER"
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == "HOURLY"
)

print(f"Output:Meter DF_ONLY:METER -> daily={df_meter_daily_count}, hourly={df_meter_hourly_count}")
assert df_meter_daily_count == 1
assert df_meter_hourly_count == 0

# %%
# Verificar default de apply_outputs_preflight(clean_mode='none')
clean_mode_default = inspect.signature(sim.apply_outputs_preflight).parameters["clean_mode"].default
print(f"Default clean_mode en apply_outputs_preflight: {clean_mode_default}")
assert clean_mode_default == "none"

# %%
# Verificar protección anti-duplicado en aPMV al reaplicar outputs
building_apmv = ef.get_building(str(idf_path))

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    apmv.apply_apmv_setpoints(building=building_apmv, outputs_freq=["hourly"], verbose_mode=False)
count_schedule_first = sum(
    1
    for o in (
        list(building_apmv.idfobjects.get("Output:Variable", []))
        if len(list(building_apmv.idfobjects.get("Output:Variable", []))) > 0
        else list(building_apmv.idfobjects.get("OUTPUT:VARIABLE", []))
    )
    if str(getattr(o, "Variable_Name", "")).strip().upper() == "SCHEDULE VALUE"
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == "HOURLY"
)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    apmv.apply_apmv_setpoints(building=building_apmv, outputs_freq=["hourly"], verbose_mode=False)
count_schedule_second = sum(
    1
    for o in (
        list(building_apmv.idfobjects.get("Output:Variable", []))
        if len(list(building_apmv.idfobjects.get("Output:Variable", []))) > 0
        else list(building_apmv.idfobjects.get("OUTPUT:VARIABLE", []))
    )
    if str(getattr(o, "Variable_Name", "")).strip().upper() == "SCHEDULE VALUE"
    and str(getattr(o, "Reporting_Frequency", "")).strip().upper() == "HOURLY"
)

print(f"aPMV Schedule Value hourly -> primera={count_schedule_first}, segunda={count_schedule_second}")
assert count_schedule_second == count_schedule_first

# %%
print("\nOK: smoke script de workflow de outputs completado.")



