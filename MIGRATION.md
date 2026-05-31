# Migrating to accim 1.0

accim 1.0 is a **clean-break** release. The `accim.sim` subpackage was
reorganised and every public name was changed to follow Python's PEP 8 naming
conventions (snake_case for functions/arguments, CapWords for classes). There
are **no backward-compatible aliases**: code written for 0.7.x must be updated.

The behaviour of the generated EnergyPlus models is **unchanged** — only the
Python API (module paths, class/function names and argument names) changed.

---

## 1. Quick before/after

### Transforming IDFs in a folder (batch)

```python
# 0.7.x
from accim.sim import accis
accis.addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='supply air temperature',
    Output_type='standard',
    Output_freqs=['hourly'],
    Output_keep_existing=False,
    EnergyPlus_version='auto',
    TempCtrl='temperature',
    ComfStand=[2], CAT=[80], ComfMod=[3], HVACmode=[2], VentCtrl=[0],
    verboseMode=True, confirmGen=False,
)

# 1.0
from accim.sim import AddAccis
AddAccis(
    script_type='vrf_mm',
    supply_air_temp_method='supply air temperature',
    output_type='standard',
    output_freqs=['hourly'],
    output_keep_existing=False,
    energyplus_version='auto',
    temp_control='temperature',
    comfort_standard=[2], category=[80], comfort_mode=[3],
    hvac_mode=[2], vent_control=[0],
    verbose=True, confirm_generation=False,
)
```

### Applying the ACCIS to a single in-memory IDF

```python
# 0.7.x
import accim.sim.accis_single_idf_funcs as accis
accis.addAccis(idf=building, ScriptType='vrf_mm', ...)
accis.modifyAccis(idf=building, ComfStand=2, CAT=80, ComfMod=3, HVACmode=2, VentCtrl=0)

# 1.0
from accim.sim import AddAccisToIdf, modify_accis      # or: add_accis (function form)
AddAccisToIdf(idf=building, script_type='vrf_mm', ...)
modify_accis(idf=building, comfort_standard=2, category=80, comfort_mode=3,
             hvac_mode=2, vent_control=0)
```

### aPMV setpoints (unchanged name, new module path)

```python
# 0.7.x
from accim.sim import apmv_setpoints
apmv_setpoints.apply_apmv_setpoints(building=building, outputs_freq=['hourly'])

# 1.0
from accim.sim import apply_apmv_setpoints
apply_apmv_setpoints(building=building, outputs_freq=['hourly'])
```

---

## 2. Public entry points

| 0.7.x | 1.0 |
|---|---|
| `accim.sim.accis.addAccis` (class) | `accim.sim.AddAccis` (class) |
| `accim.sim.accis_single_idf_funcs.addAccis` (function) | `accim.sim.AddAccisToIdf` (class) or `accim.sim.add_accis` (function) |
| `accim.sim.accis_single_idf_funcs.modifyAccis` | `accim.sim.modify_accis` |
| `accim.sim.accis_single_idf_funcs.gen_outputs_df` | `accim.sim.gen_outputs_df` |
| `accim.sim.apmv_setpoints.apply_apmv_setpoints` | `accim.sim.apply_apmv_setpoints` |
| `accim.sim.accis_single_idf` (class module) | removed (use `AddAccisToIdf`) |

All public entry points are now importable directly from `accim.sim`.

## 3. Argument renames

| 0.7.x | 1.0 | | 0.7.x | 1.0 |
|---|---|---|---|---|
| `ScriptType` | `script_type` | | `HVACmode` | `hvac_mode` |
| `SupplyAirTempInputMethod` | `supply_air_temp_method` | | `VentCtrl` | `vent_control` |
| `Output_type` | `output_type` | | `MaxTempDiffVOF` | `vof_max_temp_diff` |
| `Output_freqs` | `output_freqs` | | `MinTempDiffVOF` | `vof_min_temp_diff` |
| `Output_keep_existing` | `output_keep_existing` | | `MultiplierVOF` | `vof_multiplier` |
| `Output_gen_dataframe` | `output_gen_dataframe` | | `VSToffset` | `vent_setpoint_offset` |
| `Output_take_dataframe` | `output_take_dataframe` | | `MinOToffset` | `min_outdoor_temp_offset` |
| `EnergyPlus_version` | `energyplus_version` | | `MaxWindSpeed` | `max_wind_speed` |
| `TempCtrl` | `temp_control` | | `ASTtol_start` | `ast_tol_start` |
| `VRFschedule` | `vrf_schedule` | | `ASTtol_end_input` | `ast_tol_end` |
| `ComfStand` | `comfort_standard` | | `ASTtol_steps` | `ast_tol_steps` |
| `CAT` | `category` | | `ASTtol` | `ast_tol` |
| `CATcoolOffset` | `category_cool_offset` | | `NameSuffix` | `name_suffix` |
| `CATheatOffset` | `category_heat_offset` | | `verboseMode` | `verbose` |
| `ComfMod` | `comfort_mode` | | `confirmGen` | `confirm_generation` |
| `SetpointAcc` | `setpoint_accuracy` | | `debugging` | `debug` |
| `CoolSeasonStart` | `cooling_season_start` | | `CustAST_m` | `custom_ast_m` |
| `CoolSeasonEnd` | `cooling_season_end` | | `CustAST_n` | `custom_ast_n` |
| `CustAST_ACSToffset` | `custom_ast_acst_offset` | | `CustAST_AHSToffset` | `custom_ast_ahst_offset` |
| `CustAST_ACSTaul` | `custom_ast_acst_aul` | | `CustAST_ACSTall` | `custom_ast_acst_all` |
| `CustAST_AHSTaul` | `custom_ast_ahst_aul` | | `CustAST_AHSTall` | `custom_ast_ahst_all` |

Unchanged argument names: `idf`, `idfs`, `eer`, `cop`, `make_averages`,
`hvac_zone_map`.

Domain abbreviations kept as-is: `ast` (Adaptive Setpoint Temperature),
ACST/AHST (Adaptive Cooling/Heating Setpoint Temperature), `aul`/`all`
(applicability upper/lower limit), `vof` (Venting Opening Factor).

## 4. Internal module reorganisation (`accim.sim`)

If you imported internal modules directly:

| 0.7.x module | 1.0 module |
|---|---|
| `accim.sim.accis` | `accim.sim.batch` |
| `accim.sim.accis_single_idf_funcs` | `accim.sim.single` |
| `accim.sim.accim_Main` | `accim.sim.engine` |
| `accim.sim.accim_Main_single_idf` | `accim.sim.engine` (`AccimJobInMemory`) |
| `accim.sim.accim_IDFgeneration` | `accim.sim.idf_generation` |
| `accim.sim.apmv_setpoints` | `accim.sim.apmv` |
| `accim.sim.accim_Base` | `accim.sim.hvac.base` |
| `accim.sim.accim_VRFsystem` (+`_EMS`) | `accim.sim.hvac.vrf` (+`vrf_ems`) |
| `accim.sim.accim_ExistingHVAC` (+`_EMS`, `_resolver`) | `accim.sim.hvac.existing` (+`existing_ems`, `resolver`) |
| `accim.sim.accim_Base_EMS` | `accim.sim.ems.programs` |
| `accim.sim.setAST_models` | `accim.sim.ems.setast_models` |

The engine class `accimJob` is now `AccimJob` (file/disk based) with
`AccimJobInMemory` for already-loaded IDF objects.

## 5. `accim.run` (run_ep)

```python
# 0.7.x
from accim.run import run
run.runEp(runOnlyAccim=True, confirmRun=True, num_CPUs=2, EnergyPlus_version='24.2')

# 1.0
from accim.run import run
run.run_ep(run_only_accim=True, confirm_run=True, num_cpus=2, energyplus_version='24.2')
```

| 0.7.x | 1.0 |
|---|---|
| `run.runEp` | `run.run_ep` |
| `runOnlyAccim` | `run_only_accim` |
| `confirmRun` | `confirm_run` |
| `num_CPUs` | `num_cpus` |
| `EnergyPlus_version` | `energyplus_version` |

## 6. `accim.data` (postprocessing.Table)

The public API of `Table` is unchanged, but note:

- `Table(..., idf_path=...)` is now **required** to resolve the building zones.
  Passing `idf_path=None` previously raised a cryptic
  `AttributeError: 'dict' object has no attribute 'idfobjects'`; it now raises a
  clear `ValueError`.
- A bug in `wrangled_table(reshaping='pivot')` (which passed `index=None` to
  `pivot_table`) was fixed. The `unstack` reshaping is the recommended path.
