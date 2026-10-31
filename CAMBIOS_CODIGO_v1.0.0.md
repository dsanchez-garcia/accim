# Cómo ha cambiado el código de accim en la versión 1.0.0

Guía para entender la reorganización del código de la rama `v1.0.0` respecto a accim 0.8.2 (rama
`master`): qué hay en cada módulo, cómo encajan las piezas y dónde buscar lo que antes estaba en otro
sitio. Está pensada para quien mantiene accim; no es documentación de uso.

Lo que ya está en otros documentos no se repite aquí:

- `CHANGELOG.md` (sección Unreleased): los cambios que ve el usuario, con las correcciones.
- `docs/source/9_migration_guide.md`: la tabla de nombres antiguos y nuevos, y los cambios de
  comportamiento.
- `DEVLOG.md`: el registro del trabajo, con cómo se comprobó cada cambio.
- `notes/decisions.md`: las decisiones de diseño y sus motivos.

## Índice

1. [En resumen](#1-en-resumen)
2. [Mapa de módulos](#2-mapa-de-módulos)
3. [De los métodos de 0.8.2 a las funciones de 1.0.0](#3-de-los-métodos-de-082-a-las-funciones-de-100)
4. [Cómo funciona `AddAccis`](#4-cómo-funciona-addaccis)
5. [`add_accis_to_idf` y `modify_accis`](#5-add_accis_to_idf-y-modify_accis)
6. [Los programas EMS](#6-los-programas-ems)
7. [Nombres antiguos y compatibilidad](#7-nombres-antiguos-y-compatibilidad)
8. [El backend de la API de Python](#8-el-backend-de-la-api-de-python)
9. [El resto del paquete](#9-el-resto-del-paquete)
10. [Cambios de comportamiento](#10-cambios-de-comportamiento)
11. [Pruebas](#11-pruebas)
12. [Dónde tocar para...](#12-dónde-tocar-para)

## 1. En resumen

**Lo que no cambia**

- El uso. `AddAccis`, `add_accis_to_idf`, `modify_accis` y `run_ep` hacen lo mismo que `addAccis`, el
  `addAccis` de `accis_single_idf_funcs`, `modifyAccis` y `runEp`; cambian los nombres, que siguen PEP 8
  (`script_type` en vez de `ScriptType`...). Los nombres de 0.x siguen funcionando, con un
  `DeprecationWarning` que da el nuevo.
- Las preguntas de `AddAccis()` (siguen mostrando `ScriptType`, `ComfStand`...) y el uso de
  `accim.parametric_and_optimisation`, cuyos parámetros conservan los nombres de 0.x.
- Las líneas Erl de los programas EMS.
- Los IDF de salida: se generaron con 0.8.2 y con 1.0.0 en 29 configuraciones (todos los tipos de
  script, todas las normas de confort, control por PMV, consignas aPMV, modelos de OpenStudio y
  DesignBuilder, EnergyPlus 25.1 a 26.2...) y son idénticos, salvo las correcciones de la sección 10.

**Lo que cambia**

- `accim.sim` ya no es un conjunto de módulos grandes cuyos métodos heredaba una clase (`accimJob`),
  sino módulos pequeños, cada uno con una responsabilidad, con funciones que reciben el modelo
  (`AccimModel`).
- El mismo código construye el modelo para archivos (`AddAccis`) y para objetos IDF en memoria
  (`add_accis_to_idf`, que usa el módulo paramétrico). En 0.8.2 eran dos caminos (`accim_Main` y
  `accim_Main_single_idf`) que se habían separado: la ventilación natural con objetos `ZoneVentilation`
  y el dimensionado solo estaban en el primero.
- Es más rápido: con el `TestModel` de ejemplo y 140 IDF de salida, `AddAccis` tarda unos 6 s en vez
  de 20, y `from accim.sim import accis`, 1,5 s en vez de 16 a 24.
- `import accim` no importa nada más ni modifica otras librerías; antes importaba besos, dask y
  platypus y les aplicaba parches.
- Hay un backend nuevo que ejecuta los programas EMS en Python, a través de la API de Python de
  EnergyPlus, con los mismos resultados que el EMS.

**Tamaño** (líneas de Python, sin los archivos de ejemplo):

| Parte | 0.8.2 | 1.0.0 |
| --- | ---: | ---: |
| `accim/sim` | 14 353 | 12 285, de ellas 1 947 del backend de la API (`ems/erl.py` y `energyplus_api/`) |
| `accim/utils.py` → `accim/utils/` | 3 350 | 3 536 |
| `accim/run` | 253 | 227 |

## 2. Mapa de módulos

### `accim.sim`

| 0.8.2 | Qué hacía | 1.0.0 |
| --- | --- | --- |
| `accis.py` (clase `addAccis`) | La clase pública: preguntas, comprobaciones, bucle de los IDF y generación de los IDF de salida | `accis.py`: `AddAccis` (archivos); `add_accis_to_idf`, `modify_accis` y `gen_outputs_df` (objetos IDF); `load_idf`. Las comprobaciones están en `arguments.py` y las preguntas en `prompts.py` |
| `accim_Main.py` (clase `accimJob`) | Leía el modelo (zonas ocupadas, ventanas, termostatos) y heredaba los métodos de los demás módulos | `model.py` (`AccimModel`), `targets.py` (zonas ocupadas y sus ocupantes) y `build.py` (la secuencia de pasos) |
| `accim_Main_single_idf.py` | La copia de `accim_Main` para objetos IDF | Desaparece: `add_accis_to_idf` usa `AccimModel` y `build.py` |
| `accim_Base.py` | Modelos de confort de los People, consignas PMV, objetos de control de salida, dimensionado, guardar el IDF | `people.py`, `hvac/vrf.py` y `outputs.py` |
| `accim_Base_EMS.py` | Programas, gestores de llamada, variables, sensores, actuadores y variables de salida del EMS, y las Output:Variable | `ems/programs.py`, `ems/objects.py`, `ems/program_lines.py` (las líneas Erl) y `outputs.py` |
| `setAST_models.py` | Las líneas de las consignas de cada norma de confort y los subprogramas de `SetAST` | `ems/setpoint_lines.py` (una tabla `(ComfStand, ComfMod)` → líneas) y `ems/setast.py` (`SetAST_Master` y los subprogramas) |
| `accim_VRFsystem.py`, `accim_VRFsystem_EMS.py` | Los objetos del sistema VRF y sus sensores | `hvac/vrf.py` (la lógica) y `hvac/vrf_data.py` (los valores de los objetos, los de 0.x) |
| `accim_ExistingHVAC.py`, `accim_ExistingHVAC_EMS.py`, `accim_ExistingHVAC_resolver.py` | Los sistemas existentes (`ex_ac`, `ex_mm`) | `hvac/existing.py` y `hvac/resolver.py` |
| `accim_IDFgeneration.py` (`genIDF`) | Escribía cada IDF de salida a partir de los `*_pymod.idf` | `generation.py`: `combinations`, `output_name`, `IdfWriter` y `OutputIdfs` |
| `dicts.py`, `lists.py`, `utils.py` | Datos de las normas y `scan_zones` | `standards.py` (catálogo de normas de confort), `arguments.py` (valores válidos), `targets.py` y `model.py` |
| `accis_single_idf.py`, `accis_single_idf_funcs.py` | La versión en memoria (614 y 779 líneas) | Módulos obsoletos (145 y 51 líneas) que llaman a `add_accis_to_idf` y `modify_accis` con los nombres antiguos |
| `apmv_setpoints.py` | Consignas aPMV | `apmv.py`; `apmv_setpoints.py` es un módulo obsoleto que lo reexporta |
| — | | Nuevos: `idf_tools.py` (utilidades para los objetos de eppy), `ems/erl.py` (el intérprete de Erl) y `energyplus_api/` (el backend de la API) |

### El resto

| 0.8.2 | 1.0.0 |
| --- | --- |
| `accim/__init__.py`: importaba besos, dask y platypus y les aplicaba parches | Sin efectos: `__version__`, y los subpaquetes se importan al usarlos (`import accim` y luego `accim.utils...`). Los parches están en `accim/_besos_compat.py`, que aplica `accim.parametric_and_optimisation` |
| `accim/utils.py` (3 350 líneas, importaba besos) | Paquete `accim/utils/`: `people`, `editing`, `accim_args`, `versions`, `outputs`, `verification` y `workspace`. Cada función se importa al usarla (`__getattr__` de PEP 562), así que `from accim.utils import reduce_runtime` sigue funcionando |
| — | `accim/energyplus.py`: las instalaciones de EnergyPlus (`find_energyplus`, `idd_path`, `read_idf_version` y la variable de entorno `ACCIM_ENERGYPLUS_DIR`) |
| Constantes repartidas | `accim/constants.py` (`SUPPORTED_ENERGYPLUS_VERSIONS`...); `accim/lists.py` se mantiene por compatibilidad |
| — | `accim/_deprecation.py`: el mecanismo de los nombres antiguos (sección 7) |
| `run/run.py` (`runEp`) | `run/run.py`: `run_ep`, con `backend='ems'` o `'api'`, y `simulation_name` |
| `accim.data` | Igual, con `gen_csv_concatenated`, `preview_table_cols` y `name_export_rows_with_nan` (los nombres antiguos funcionan) |
| `accim.parametric_and_optimisation` | Igual; cambian sus llamadas internas a `accim.sim` (y algunas correcciones, sección 10). Nuevo `_pareto.py` (la dominancia con restricciones) y, en `objectives.py`, `checked_sum_results`, `hours_outside_comfort` y `fraction_outside_comfort` |

## 3. De los métodos de 0.8.2 a las funciones de 1.0.0

Para buscar dónde está ahora algo concreto. En 0.8.2, `accimJob` heredaba todos estos métodos y los
llamaba en orden; en 1.0.0 son funciones que reciben el `AccimModel`.

| 0.8.2 | 1.0.0 |
| --- | --- |
| `accimJob.__init__`, `utils.scan_zones` | `AccimModel.__init__` (`model.py`) y `targets.resolve_targets` |
| `setComfFieldsPeople` | `people.set_comfort_models` |
| `setPMVsetpoint` | `hvac.vrf.set_pmv_setpoints` |
| `addOpTempTherm`, `addBaseSchedules`, `setAvailSchOn`, `addVRFsystemSch`, `addCurveObj`, `addDetHVACobj` | `hvac.vrf.add_operative_temperature_thermostats`, `add_base_schedules`, `add_vrf_schedules`, `add_curves` y `add_vrf_objects`, que llama `hvac.vrf.add_vrf_system`. `setAvailSchOn` (la disponibilidad de los `ZoneHVAC:IdealLoadsAirSystem`) ya no existe: `add_vrf_objects` elimina esos objetos, que el VRF dejaba sin conectar |
| `addForscriptSchVRFsystem`, `checkVentIsOn`, `addEMSSensorsVRFsystem` | `hvac.vrf.add_setpoint_schedules`, `check_ventilation` y `add_coil_sensors` |
| `addForscriptSchExistHVAC`, `addEMSSensorsExisHVAC`, `addEMSInitExisHVAC` | `hvac.existing.add_setpoint_schedules`, `add_coil_sensors` y `add_coil_initialisation` |
| `resolve_hvac_zone_map` (`accim_ExistingHVAC_resolver`) | `hvac.resolver` (las mismas estrategias) |
| `addEMSProgramsBase`, `addEMSPCMBase` | `ems.programs.add_programs` y `add_program_calling_managers` |
| `addEMSOutputVariableBase`, `addGlobVarList`, `addIntVarList`, `addEMSSensorsBase`, `addEMSActuatorsBase`, `makeAverages` | `ems.objects.add_output_variables`, `add_global_variables`, `add_internal_variables`, `add_sensors`, `add_actuators` y `add_building_averages` |
| `addOutputVariablesSimplified`, `addOutputVariablesStandard`, `addOutputVariablesDetailed`, `outputsSpecified`, `removeExistingOutputVariables`, `removeDuplicatedOutputVariables`, `genOutputDataframe`, `takeOutputDataFrame` | `outputs.add_simplified_outputs`, `add_standard_outputs`, `add_detailed_outputs`, `select_custom_outputs`, `remove_existing_outputs`, `remove_duplicated_outputs`, `output_variables_dataframe` y `take_output_dataframe` |
| `addControlFilesObjects`, `addOutputVariableDictionaryObject`, `addOutputEnergyManagementSystem`, `setSimulationControlSizing` | `outputs.add_output_control_files`, `add_variable_dictionary`, `add_ems_debug_output` y `enable_sizing_calculations` |
| `get_SetAST_lines`, `get_SetAST_Master_program`, `get_SetAST_subprogram_chunk`, `get_valid_combinations` (`setAST_models`) | `ems.setast.get_setpoint_lines`, `master_program_lines`, `subprograms` y `MODULAR_COMFORT_MODES` |
| `genIDF`, `inputData`, `replace_SetAST_dynamic_lines` (`accim_IDFgeneration`) | `generation.combinations`, `output_name` e `IdfWriter`, y `AddAccis._write_output_idfs` |
| `saveaccim` (escribía `*_pymod.idf`) | No hay archivos intermedios: `AddAccis` guarda el texto del modelo (`idf_tools.idf_text`) |
| `addAccis`, `modifyAccis`, `gen_outputs_df`, `modify_param` (`accis_single_idf_funcs`) | `accis.add_accis_to_idf`, `modify_accis` y `gen_outputs_df` (`modify_param` sigue en el módulo obsoleto) |

## 4. Cómo funciona `AddAccis`

`AddAccis(...)` (en `sim/accis.py`) hace, en orden:

1. Lista los IDF de entrada (`_input_files`: los de la carpeta, salvo los que tienen `[` o `_pymod` en
   el nombre, o los de `idfs`) e imprime la cabecera (`BANNER`).
2. **Primera etapa de argumentos** (tipo de script, salidas, versión de EnergyPlus, control por
   temperatura o PMV). Si falta alguno, `prompts.ask_model_arguments()` los pregunta todos, como en
   0.x. `_check_model_arguments` los comprueba (con `arguments.py`) antes de leer ningún IDF.
3. **Para cada IDF de entrada:**
   - `load_idf` lo lee con besos (versión `'auto'`) o con eppy y el IDD de la versión indicada
     (`accim.energyplus.idd_path`); se trabaja sobre una copia (`idf_tools.copy_idf`).
   - `AccimModel(idf, script_type, temp_ctrl)` lo analiza: las zonas ocupadas y los ocupantes de cada
     una (`targets.resolve_targets`, que tiene en cuenta los `Space`, `SpaceList`, `ZoneList` y los
     `People:Instance` de EnergyPlus 26.2), las ventanas (aberturas de AirflowNetwork o, sin
     AirflowNetwork, los objetos `ZoneVentilation`, cada uno con un horario `Vent_Sch_<zona>`), y los
     termostatos y sistemas existentes (con `ex_*`). Las zonas quedan en el orden del IDF, siempre el
     mismo.
   - `build.add_accis_objects(model, ...)` añade los objetos: los modelos de confort de los People, el
     sistema VRF o los horarios de los sistemas existentes, los programas EMS, sus variables, sensores
     y actuadores, los gestores de llamada y los objetos de control de salida.
   - `build.add_outputs(model, ...)` añade las Output:Variable del tipo de salida, o las de
     `output_take_dataframe`.
   - `outputs.enable_sizing_calculations(model)` activa el dimensionado, y avisa si el modelo no tiene
     periodos de dimensionado.
   - Guarda el texto del modelo (no el objeto, que ocupa mucha más memoria).
4. **Segunda etapa de argumentos** (normas de confort, categorías, modos, ventilación, tolerancias...):
   `_generation_arguments` los pregunta si faltan (`prompts.ask_generation_arguments`) y los guarda en
   un `GenerationArguments` (`generation.py`).
5. **Generación de los IDF de salida** (`_write_output_idfs`): `generation.combinations` da las
   combinaciones válidas (salta, con un aviso, las que no tienen consignas, y los controles de
   ventilación 2 y 3 con ventilación natural sola); `output_name` da el nombre de cada archivo
   (`modelo[CS_...[CA_...[...].idf`); y, tras la confirmación, un `IdfWriter` por modelo escribe todos
   sus IDF de salida.
6. `output_idfs` (un `OutputIdfs`) da la ruta de cada IDF de salida, y lee el objeto IDF solo cuando se
   pide.

**Por qué es más rápido.** En 0.8.2, `genIDF` abría con eppy el `*_pymod.idf` para cada IDF de salida,
cambiaba unos programas y lo guardaba con eppy, que es lento. Todos los IDF de salida de un modelo
comparten todos los objetos salvo cinco programas EMS (`SetInputData`, `SetAST`, `ApplyCAT`,
`SetAppLimits` y `SetVOFinputData`), así que `IdfWriter` escribe una vez el texto de los demás objetos
y, para cada combinación, solo esos programas, con el formato de eppy: los archivos son idénticos byte a
byte a los que guardaría eppy (lo comprueba `tests/core/test_generation.py`). Además, `accim.sim` no
importa besos al cargarse.

## 5. `add_accis_to_idf` y `modify_accis`

`add_accis_to_idf(idf, ...)` hace los pasos 2 y 3 sobre un objeto IDF en memoria (sin copiarlo ni
escribir archivos), con los argumentos por defecto de `SetInputData` (ComfStand 1, CAT 1, ComfMod 2,
HVACmode 2, VentCtrl 0). Con los sistemas VRF también activa el dimensionado, como `AddAccis`; con los
sistemas existentes no lo toca. Devuelve el `AccimModel`.

`modify_accis(idf, ...)` cambia los argumentos de un modelo que ya tiene el ACCIS: reescribe
`SetInputData`, `SetAST` (deja sus 4 primeras líneas, que ejecutan `SetAST_Master`), `ApplyCAT`,
`SetAppLimits` y `SetVOFinputData`. Los argumentos que son `None` conservan su valor. A los modelos de
versiones anteriores les añade `SetAST_Master` y sus subprogramas (antes de 0.8) o les pone los
subprogramas actuales de ESP CTE e INT ISO7730 (antes de 1.0).

El módulo paramétrico usa `add_accis_to_idf` al crear la simulación, `modify_accis` para el modelo base
de `AccimPredefModelsParamSim` (el modelo custom con los coeficientes por defecto de 'accim custom
model', los de ASHRAE 55 con un 80 % de aceptabilidad), y las funciones de
`parametric_and_optimisation/funcs_for_besos/param_accis.py`, que cambian líneas concretas de esos
programas en cada simulación.

## 6. Los programas EMS

- `ems/program_lines.py`: las líneas Erl de los programas del ACCIS (`SetComfTemp`, `SetAST`,
  `CountHours_<zona>`, `SetWindowOperation_<ventana>`...), las de 0.8.2. `ems/programs.py` los añade al
  modelo (`add_programs`) y crea sus gestores de llamada (`add_program_calling_managers`), sin añadir
  gestores a los programas que el modelo ya tenía.
- `ems/setpoint_lines.py`: una tabla con las líneas que calculan `ACST` y `AHST` para cada norma de
  confort (`ComfStand`) y modo (`ComfMod`), y las del redondeo (`ROUNDING`).
- `ems/setast.py`: `SetAST` ejecuta `SetAST_Master`, que calcula la temporada de refrigeración y ejecuta
  los subprogramas de la norma de `SetInputData` (`SetAST_CS<n>_<trozo>`). Cada subprograma tiene las
  líneas de hasta 3 modos de confort, para no pasar del límite de líneas de un programa de EnergyPlus; los
  de ESP CTE y INT ISO7730 (0 y 22), cuyas consignas no dependen del modo, las fijan sea cual sea `ComfMod`
  (`depends_on_comfort_mode`). `MODULAR_COMFORT_MODES` dice qué modos tiene cada norma; debe coincidir con
  las combinaciones válidas del módulo paramétrico (`param_accis.drop_invalid_param_combinations`).
- `ems/objects.py`: las variables globales, variables internas, sensores, actuadores y variables de
  salida del EMS, y las medias del edificio (`make_averages`).
- `ems/erl.py`: el intérprete de Erl (sección 8). También lo usan los tests para comprobar los
  programas que escribe accim.

## 7. Nombres antiguos y compatibilidad

Todo pasa por `accim/_deprecation.py`:

- `warn_deprecated(old, new)`: el aviso (`DeprecationWarning`) con el nombre nuevo.
- `rename_legacy_kwargs(kwargs, mapping, function_name)`: cambia los nombres antiguos de los argumentos
  por los nuevos, con un aviso; si un argumento llega con los dos nombres, da `TypeError`.
- `deprecated_alias(...)` y `accepts_legacy_kwargs(...)`: crean los alias de funciones (`runEp`,
  `removefiles`, `genCSVconcatenated`...) y las funciones que aceptan los argumentos antiguos.

La correspondencia de los argumentos de `AddAccis` está en `arguments.LEGACY_ARGUMENT_NAMES`
(`ScriptType` → `script_type`, `ComfStand` → `comf_stand`...). `addAccis` es una subclase de `AddAccis`
que renombra los argumentos, y `AddAccis.arguments` (un `_Arguments`) responde también a las claves
antiguas. Los módulos obsoletos (`accis_single_idf`, `accis_single_idf_funcs`, `apmv_setpoints`)
llaman a las funciones nuevas; `accis_single_idf.addAccis` conserva incluso los argumentos posicionales
y los atributos de 0.x. `tests/core/test_deprecation.py` comprueba que los scripts de 0.x siguen
funcionando.

Para retirar los nombres antiguos en una versión futura (`ROADMAP.md`, R-03) basta con borrar los
módulos obsoletos, los alias y `LEGACY_ARGUMENT_NAMES`.

## 8. El backend de la API de Python

Ejecuta los IDF de salida de accim sin el EMS de EnergyPlus: los programas EMS se ejecutan en Python,
en las llamadas (*callbacks*) de la API de Python de EnergyPlus (`pyenergyplus`, EnergyPlus 24.2 o
posterior), con las reglas del EMS, así que los resultados son los mismos. Sirve para leer y cambiar
las variables de los programas durante la simulación con código Python (sección 4.9 de la
documentación, *Detailed use*).

| Módulo (en `accim/sim/`) | Qué hace |
| --- | --- |
| `energyplus_api/idf.py` | Lee el IDF como texto (`parse_idf`, `render_idf`), extrae sus objetos EMS (`read_ems` → `EmsDefinition`) y da el IDF que ejecuta la API (`objects_for_api`): el mismo modelo sin programas, gestores de llamada ni actuadores, con variables globales para las variables de salida del EMS que informan de variables de programas o de actuadores. Los sensores y las variables internas se quedan, para que EnergyPlus los actualice como siempre |
| `ems/erl.py` | Compila cada programa Erl a una función de Python (`ErlProgramSet`). Cada sentencia se ejecuta primero como código Python con números; si falla (un Null, una variable sin inicializar, una división por cero...), se evalúa otra vez con las reglas exactas de `RuntimeLanguageProcessor.cc`. Así, lo habitual es rápido y lo raro, exacto |
| `energyplus_api/controller.py` | `ErlController`: en cada punto de llamada hace lo que `EMSManager.cc`: reinicia las variables al empezar cada entorno, actualiza las variables integradas, los sensores y las variables internas, ejecuta los programas de sus gestores en el orden del IDF, aplica los actuadores (Null los libera; los enteros se redondean hacia abajo y los lógicos solo son verdaderos con 1) y escribe las variables de salida. Los mensajes de `@WarnEP`, `@SevereWarnEP` y `@FatalHaltEP` van al archivo de errores |
| `energyplus_api/runner.py` | `run_simulation` (una simulación) y `run_simulations` (varias, cada una en su propio proceso: un proceso solo puede cargar la API de una versión de EnergyPlus) |
| `energyplus_api/runtime.py` | Carga `pyenergyplus` de la instalación de la versión del IDF |

`accim.run.run_ep(backend='api')` usa `run_simulations` con los IDF y EPW de la carpeta, y nombra los
archivos de salida igual que con el EMS (`simulation_name`).

Las reglas se comprobaron en el código fuente de EnergyPlus (24.2, 25.1, 26.1 y 26.2): el orden de los
operadores, el signo menos, los valores Null y sin inicializar, `^` como `pow` de C, los errores
durante el dimensionado y después, el reinicio de las variables, el ámbito de las variables de
salida... Con los tipos de modelo de accim y con los ejemplos de EMS de EnergyPlus que admite, los CSV
de los dos backends son idénticos (`DEVLOG.md` da el detalle, y `tests/core/test_energyplus_api.py`
lo comprueba con un modelo de accim y con un ejemplo de EnergyPlus). No admite
`EnergyManagementSystem:TrendVariable`, `CurveOrTableIndexVariable` ni `ConstructionIndexVariable`, la
interfaz externa, los plugins de Python, el punto de llamada `UserDefinedComponentModel` ni las
funciones psicrométricas y de curvas del EMS: con ellos da un error claro, y hay que usar el backend del
EMS.

## 9. El resto del paquete

- `accim.utils`: las mismas funciones, repartidas en submódulos, que se importan al usarlas. Las
  funciones de besos que 0.x importaba en `accim.utils` (`get_building`...) siguen disponibles.
- `accim.energyplus`: busca las instalaciones de EnergyPlus (en su carpeta por defecto o en
  `ACCIM_ENERGYPLUS_DIR`), sus IDD y la versión de un IDF. Lo usan `load_idf`, `run_ep` y el backend de
  la API.
- `accim.run`: `run_ep` con los dos backends, y `remove_files` (antes `removefiles`).
- `accim.data`: la misma estructura, con nombres nuevos y alias.
- `accim.parametric_and_optimisation`: su uso no cambia. Llama a `accis.add_accis_to_idf`,
  `accis.modify_accis` y `accim.sim.apmv` en vez de a los módulos de 0.x, y aplica los parches de besos
  (`_besos_compat`) al importarse.

## 10. Cambios de comportamiento

Están en la sección 9.3 de la guía de migración y en `CHANGELOG.md`. En resumen:

- Correcciones que cambian los IDF de salida: `ThermostatSetpoint:SingleCooling` en todas las zonas, los
  gestores de llamada de más, `make_averages`, las tolerancias, las combinaciones sin consignas...
- `add_accis_to_idf`, y por tanto el módulo paramétrico, controla la ventilación natural de los objetos
  `ZoneVentilation` y activa el dimensionado de los sistemas VRF, como `AddAccis`.
- Con los sistemas VRF, `add_vrf_objects` elimina los `ZoneHVAC:IdealLoadsAirSystem` del modelo, que quedaban
  sin conectar y daban un error grave en cada simulación (los resultados no cambian).
- Los IDF de salida son deterministas: las zonas, y los objetos de cada zona, siempre en el mismo orden.
- `run_ep` nombra las simulaciones con el nombre completo del EPW.
- Correcciones del módulo paramétrico encontradas al poner en marcha sus tests (el registro de las
  evaluaciones de las optimizaciones con EPW dados como rutas, y el análisis de Sobol por EPW).
- Correcciones del módulo paramétrico del 31/10/2026, sin cambiar su uso: los subprogramas de ESP CTE e
  INT ISO7730 fijan sus consignas con cualquier `ComfMod`; el filtro de los planes comprueba cada regla;
  el modelo base de `AccimPredefModelsParamSim` tiene los coeficientes por defecto del modelo custom;
  `run_optimisation` comprueba antes de empezar lo que necesita cada algoritmo y usa `population_size`
  como tamaño de cada generación (`_check_optimisation_algorithm` y `_GENERATION_SIZE_OPTIONS` en
  `main.py`); y el post-proceso (`analysis.py`, `utils.py`, `plotting.py`) divide cada fila por el área de
  su IDF o se detiene con un error claro (`_floor_areas_of_rows`), solo convierte las columnas en J,
  sigue el calendario de EnergyPlus (`_interval_reference_times`, `_AutoYearStartDate`) y explica qué
  archivos de simulación faltan.
- Del bloque de integridad de `review/refactor-sim-v1-20261024`, dos partes, también sin cambiar el uso: el
  estado de Pareto y la limpieza de `keep_sim_files='non-dominated'` tienen en cuenta las restricciones, como
  platypus (`_pareto.py`: una evaluación que las cumple domina a cualquiera que no); y la firma de cada
  simulación de los checkpoints paramétricos incluye el contenido del IDF (sus objetos) y del EPW y los
  nombres de las salidas (`_content_digest`), así que al reanudar se repiten las que cambiaron.
- Objetivos de confort independientes del control (`objectives.hours_outside_comfort` y
  `fraction_outside_comfort`): leen el estado de confort adaptativo que EnergyPlus calcula para cada objeto
  `People` (ASHRAE 55 y CEN 15251, que accim activa en todos sus modelos), en lugar de las métricas EMS de la
  etiqueta `archive/feat-comfort-metrics-experiment-api`.

## 11. Pruebas

| Carpeta | Qué prueba | Cómo se ejecuta |
| --- | --- | --- |
| `tests/core` | `accim.sim`, el intérprete de Erl (`test_erl.py`), el backend de la API (`test_energyplus_api.py`, con simulaciones con los dos backends), la generación (`test_generation.py`), el *golden master* de los IDF de salida (`test_golden_master.py`), los nombres antiguos (`test_deprecation.py`), `accim.utils` (`test_utils_package.py`), el dimensionado (`test_sizing.py`)... | `python -m pytest tests/core tests/parametric_and_optimisation -q -p no:cacheprovider`. Cada test que necesita una versión de EnergyPlus se salta si no está instalada; `--update-golden` vuelve a escribir los archivos golden tras un cambio buscado |
| `tests/parametric_and_optimisation` (`test_*.py`) | El módulo paramétrico, sin EnergyPlus o con simulaciones cortas | Con la orden anterior |
| `tests/parametric_and_optimisation` (`NN_test_*.py`) | Simulaciones reales con EnergyPlus 9.6 (87 tests) | Dándolos explícitamente, desde una carpeta de trabajo (ver su `README.md`) |
| `tests/parametric_and_optimisation_full_workflow` | Flujos completos (5 scripts) | `python -m pytest <script> -s` desde su carpeta; si el script llega al final, pytest dice «no tests ran» |

Durante la refactorización se usaron dos herramientas que ahora están en el repositorio:

- El *golden master* (`tests/core/golden_master`, con su `README.md`): genera los IDF de 29
  configuraciones y los compara objeto a objeto, en su orden, con los de 1.0.0 guardados en
  `golden/` (0,4 MB, comprimidos con xz). Se ejecuta con los tests de `tests/core`, cada configuración
  en su propio proceso (eppy solo usa un IDD por proceso). Su `runner.py` también ejecuta las
  configuraciones con otra versión de accim (con `--legacy`, la API de 0.x) y compara dos resultados:
  así se repite la comparación con 0.8.2.
- La comparación de los dos backends (`tools/compare_backends.py`): simula un modelo con el EMS y con
  la API y compara los CSV.

## 12. Dónde tocar para...

| Para... | Toca... |
| --- | --- |
| Añadir una norma de confort | `standards.py` (número, nombre, categorías y modos), `ems/setpoint_lines.py` (las líneas de cada modo), `ems/setast.py` (`MODULAR_COMFORT_MODES`) y `param_accis.drop_invalid_param_combinations` (combinaciones válidas del módulo paramétrico); si hace falta, `ems/program_lines.py` (`SetAppLimits`, `ApplyCAT`...). Las preguntas toman la lista de `standards.py` |
| Cambiar un programa EMS | `ems/program_lines.py` (o `ems/setpoint_lines.py`). Si es uno de los cinco programas que cambian en cada IDF de salida, también `generation.IdfWriter` y `modify_accis` |
| Cambiar o añadir salidas | `outputs.py` |
| Cambiar el sistema VRF | `hvac/vrf.py` y `hvac/vrf_data.py` |
| Admitir una versión de EnergyPlus | `constants.SUPPORTED_ENERGYPLUS_VERSIONS` (y `ENERGYPLUS_VERSIONS_WITH_SPACES`); revisar `energyplus.py` y `tests/core/test_energyplus_versions.py` |
| Renombrar un argumento | El argumento en las funciones, y el nombre antiguo en `arguments.LEGACY_ARGUMENT_NAMES` |
| Añadir una función de Erl al backend de la API | `ems/erl.py`: `_FUNCTIONS`, la versión rápida en `_FAST_NAMESPACE` y la exacta en `_ExactEvaluator.function`, con un test en `tests/core/test_erl.py` |
| Cambiar lo que pregunta `AddAccis` | `prompts.py`, y las transcripciones de `docs/source/4_detailed use.md` (ver `docs/README.md`, §5) |
| Cambiar a propósito los IDF de salida | Después del cambio, `python tests/core/golden_master/runner.py write CARPETA` y `compare CARPETA` para ver qué cambia, y `python -m pytest tests/core/test_golden_master.py --update-golden` para guardar los nuevos golden (ver `tests/core/golden_master/README.md`) |
