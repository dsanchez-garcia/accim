# Informe de revisión de código — accim

- **Fecha:** 19/07/2026
- **Rama revisada:** `refactor/sim-v1`
- **Alcance:** todo el paquete `accim` **excepto** `accim/parametric_and_optimisation` (obsoleto, pendiente de actualización desde otra rama). Se han revisado: `accim/__init__.py`, `accim/utils.py`, `accim/lists.py`, `accim/sim/**` (engine, batch, single, apmv, prompts, idf_generation, dicts, utils, ems/*, hvac/*), `accim/data/**` (preprocessing, postprocessing, morphing), `accim/run/`, `accim/misc/`, empaquetado (`setup.py`, `MANIFEST.in`), tests y documentación.
- **Volumen:** ~23.400 líneas de Python en el núcleo (sin `parametric_and_optimisation` ni `sample_files`).

---

## 1. Resumen ejecutivo

El estado general es **bueno y en clara mejora**: la refactorización 1.0 (separación en `sim/engine|batch|single`, aislamiento de prompts interactivos, resolver HVAC multi-estrategia, módulo aPMV moderno, suite de tests golden con `xfail` documentados) es un salto de calidad enorme respecto a la 0.7.x. Los módulos nuevos (`apmv.py`, `hvac/resolver.py`, `prompts.py`) están bien documentados y estructurados.

Sin embargo, la revisión ha encontrado:

- **1 bug crítico de regresión** que rompe el flujo por lotes con versión explícita de EnergyPlus **y también el modo `auto` con más de un IDF** (§2.1).
- **~8 bugs confirmados** adicionales de gravedad media/alta (funciones que no hacen lo que dicen, ramas con variables sin definir, borrados de ficheros por coincidencia de subcadena, pérdida potencial de datos en el renombrado de EPWs).
- **Deuda técnica concentrada** en 3 ficheros gigantes (`idf_generation.py`, `data/postprocessing/main.py`, `preprocessing.py`) con duplicación masiva.
- **Riesgos de empaquetado**: `sample_files` pesa 137 MB y el `MANIFEST.in` lo incluye entero; el próximo build puede superar el límite de 100 MB por fichero de PyPI.
- Dependencia dura de `besos` (y sus monkey-patches) en el núcleo, aunque solo el módulo obsoleto la necesita realmente.

---

## 2. Bugs confirmados (ordenados por gravedad)

### 2.1. CRÍTICO — `TypeError` por nombre de argumento en `get_idd_path_from_ep_version`

- **Dónde:** `accim/sim/engine.py:119` llama `get_idd_path_from_ep_version(energyplus_version=...)`, pero la firma real es `def get_idd_path_from_ep_version(EnergyPlus_version: str)` (`accim/utils.py:560`). `accim/run/run.py:91` usa el nombre antiguo `EnergyPlus_version=` y por eso funciona.
- **Efecto:** `AddAccis(..., energyplus_version='9.6')` (cualquier versión explícita) revienta con `TypeError: unexpected keyword argument`.
- **Efecto adicional (grave):** con `energyplus_version='auto'` y **varios IDFs**, `batch.py:435-436` reasigna `energyplus_version` a la versión concreta del primer IDF, de modo que el **segundo IDF** entra por la rama explícita y también crashea.
- **Por qué no lo cazan los tests:** los tests de caracterización usan `energyplus_version="auto"` y un solo IDF.
- **Arreglo:** renombrar el parámetro en `utils.py` a `energyplus_version` (estilo 1.0) y actualizar `run.py`; añadir un test con versión explícita y otro batch con 2 IDFs.

### 2.2. ALTO — `remove_duplicated_output_variables` no elimina duplicados y, si lo hiciera, borraría objetos equivocados

- **Dónde:** `accim/sim/ems/programs.py:1357-1378`.
- **Problema 1:** `unique_list.append(i)` guarda **objetos**, pero la condición compara `i.Variable_Name not in unique_list` (una *string* contra una lista de objetos) → siempre `True` → nunca se detecta ningún duplicado. La función es un no-op.
- **Problema 2:** si detectara duplicados, el bucle de borrado elimina `idfobjects['Output:Variable'][-1]` (los **últimos N** objetos, sean cuales sean), no los duplicados detectados.
- **Problema 3:** ignora `Key_Value`: dos outputs con el mismo nombre de variable pero distinta key **sí** son legítimos.
- **Arreglo:** deduplicar por tupla `(Key_Value, Variable_Name, Reporting_Frequency)` y llamar `removeidfobject(obj_duplicado)` directamente (como ya hace correctamente `apmv._add_apmv_outputs`).

### 2.3. ALTO — Rama `ThermostatSetpoint:SingleCooling` sin bucle en `add_forscript_schedule_existing_hvac`

- **Dónde:** `accim/sim/hvac/existing.py:82-98`.
- **Problema:** las ramas DualSetpoint y SingleHeating iteran `for j in range(...)`, pero la rama SingleCooling **usa `j` sin bucle** (copy-paste). Resultado: `NameError` si ninguna rama anterior se ejecutó, o se crea el schedule de **una única zona arbitraria** (la del último `j` residual) en lugar de todas.
- **Nota adicional:** en `existing.py:102-109` las comparaciones están invertidas (`self.HVACzonelist[j][0] in 'ThermostatSetpoint:SingleHeating'`), y `h.Name in self.HVACzonelist[j][3][k]` compara por subcadena; funcionan solo por igualdad exacta y darán falsos positivos con nombres que sean subcadena de otros.

### 2.4. ALTO — Camino PMV del generador de IDFs roto (`ComfStand_value`/`ComfMod_value` sin definir)

- **Dónde:** `accim/sim/idf_generation.py:812-838` (rama `temp_control == 'pmv'`) y también `:522` (rama `ComfStand == 0`, usa `ComfMod_value` antes de asignarse).
- **Estado:** ya está documentado como `xfail` en `tests/sim/test_known_bugs.py` (variante PMV). La variante `ComfStand == 0` (`get_SetAST_lines(ComfStand_value, ComfMod_value)` en la línea 522 con `ComfMod_value` residual de otra iteración, o `NameError` si `ComfStand_List=[0]` va primero) **no** está cubierta por el xfail.
- **Arreglo de fondo:** ver propuesta §5.2 (generar combinaciones con un iterador único).

### 2.5. ALTO — Borrado de EPWs originales excluidos del renombrado (`rename_epw_files`)

- **Dónde:** `accim/data/preprocessing.py:600-637`.
- **Problema:** `exclusion_list` excluye ficheros del renombrado, pero esos ficheros **siguen en `epw_files_to_rename`**, de modo que si el usuario confirma el borrado de originales, se eliminan EPWs **que nunca fueron copiados/renombrados** → pérdida de datos.
- **Arreglo:** retirar de la lista de borrado los IDs excluidos del renombrado.

### 2.6. ALTO — Detección de escenario/año rota por comparación con la cadena `'nan'`

- **Dónde:** `accim/data/preprocessing.py:251` y `:285` (`if epw_df.loc[i, 'EPW_scenario'] == 'nan'`).
- **Problema:** cuando no hay match, la celda contiene `NaN` (float) o directamente la columna no existe; nunca es la *string* `'nan'`. Consecuencias: los ficheros sin escenario no reciben `'Present'` y la línea 281 (`EPW_scenario + '-' + EPW_year`) puede lanzar `TypeError`, o `KeyError` si ningún fichero tuvo match. El código antiguo (comentado justo debajo) manejaba esto con `type(...) is float` — parece una regresión.
- **Arreglo:** `pd.isna(...)` o inicializar las columnas antes del bucle.

### 2.7. MEDIO — Borrado de `_pymod.idf` por coincidencia de subcadena en batch

- **Dónde:** `accim/sim/batch.py:493-496` (`if file in i: remove(i)`).
- **Problema:** si `vivienda.idf` no funciona y existe `vivienda2.idf` (válido), `'vivienda' in 'vivienda2_pymod.idf'` es `True` → **se borra el `_pymod` del modelo válido**.
- **Relacionado:** `accim/sim/idf_generation.py:844-846` borra **todos** los `*_pymod.idf` del directorio al terminar, incluso los de otras ejecuciones y aunque `confirm_generation=False`.
- **Arreglo:** comparar contra el nombre exacto `f'{file}_pymod.idf'`.

### 2.8. MEDIO — `apply_specified_outputs` con argumento no interactivo lanza `NameError`

- **Dónde:** `accim/sim/ems/programs.py:1399-1448`.
- **Problema:** si se pasa `remove_or_keep` (no None), `outputs_to_delete` nunca se asigna y la línea 1448 lanza `NameError`. El parámetro documentado solo funciona en el camino interactivo.

### 2.9. MEDIO — `AddAccis.output_idfs` mapea todos los nombres al **mismo** objeto IDF

- **Dónde:** `accim/sim/idf_generation.py` (todas las llamadas `self.output_idf_dict.update({outputname: idf1})`).
- **Problema:** `idf1` es un único objeto que se muta en cada iteración; el diccionario acaba con N claves apuntando al **estado final** del mismo objeto. Cualquier usuario que inspeccione `output_idfs['X.idf']` verá los parámetros de la última combinación generada, no los de `X.idf`.
- **Arreglo:** o cargar cada `savecopy` de vuelta (caro), o documentar la limitación y guardar solo rutas, o guardar un snapshot ligero de los parámetros por fichero.

### 2.10. MEDIO — `pd.concat([])` si todos los IDFs fallan con `output_gen_dataframe=True`

- **Dónde:** `accim/sim/batch.py:482-483`.
- **Problema:** si todos los modelos acaban en `notWorkingIDFs` (se hace `continue` antes de generar dataframes), `df_outputs_to_concat` queda vacío y `pd.concat([])` lanza `ValueError`.

### 2.11. MEDIO — aPMV crea `ProgramCallingManager` para **todos** los programas EMS del modelo

- **Dónde:** `accim/sim/apmv.py:916-933` (`_add_apmv_program_calling_managers`).
- **Problema:** itera `programlist` = **todos** los `EnergyManagementSystem:Program` del IDF (incluidos programas previos del usuario o del propio ACCIS si se combinan flujos) y les crea un PCM en `BeginTimestepBeforePredictor`. Un programa ya gestionado por otro PCM pasaría a ejecutarse dos veces, o en un punto de llamada incorrecto.
- **Arreglo:** limitar a la lista de programas creados por el propio módulo aPMV.
- **Menor, mismo fichero:** en `_add_apmv_outputs` el bloque de `Output:Meter` (líneas 1023-1053) está anidado dentro del bucle `for freq in outputs_freq:` y vuelve a iterar `for freq in outputs_freq:` (variable sombreada) → trabajo repetido O(n²) e ilegibilidad, aunque la deduplicación evita duplicados reales.

### 2.12. MEDIO — `set_comfort_fields_people` lanza `NameError` con modelos sin objetos `People`

- **Dónde:** `accim/sim/hvac/base.py:181` (`del ppl, firstpeopleobject`): si el IDF no tiene `PEOPLE`, `firstpeopleobject` nunca se asigna.

### 2.13. MENORES (lista rápida)

| # | Dónde | Problema |
|---|-------|----------|
| a | `sim/single.py:429` | `pass` inalcanzable tras `return`. |
| b | `sim/single.py:712-743` | `modify_param` es WIP (valida y no hace nada) pero está **exportada** en `accim.sim.__all__`. Retirarla del API o completarla. |
| c | `sim/single.py:606-607` | `while setpoint_accuracy < 0: raise ...` — debería ser `if`. La validación de `cooling_season_*` no rechaza valores inválidos (ramas `pass` vacías). |
| d | `sim/single.py:160-175` | Lista local `fullEPversionsList` incluye `'25.2'`, pero `accim/lists.py` y `utils.get_idd_path_from_ep_version` solo llegan a `'25.1'`. Tres fuentes de verdad distintas para lo mismo (`lists.py`, `prompts.py`, `single.py`). |
| e | `sim/idf_generation.py:180-206` | `self.vof_max_temp_diff = vof_max_temp_diff,` — comas finales crean **tuplas** por accidente, con un parche posterior (`if type(...) is tuple`) para deshacerlo. Eliminar las comas y el parche. |
| f | `sim/idf_generation.py` | Inconsistencia al inyectar líneas dinámicas de SetAST: unas ramas hacen `obj.append(dline)` tras `pop()` hasta 18 elementos y otras `setattr(Program_Line_{idx})` desde 17 — revisar el posible off-by-one entre ramas. |
| g | `sim/engine.py:471-475` | Emparejamiento ventana-zona por subcadena (`tz.lower() in wname.lower()`): `ZONE1` casa con `ZONE10_Win` → sensores duplicados/incorrectos. |
| h | `sim/engine.py:32-33` | `from os import listdir` e `import numpy` en el **cuerpo de la clase** → quedan como atributos `AccimJob.listdir`, `AccimJob.numpy`. |
| i | `run/run.py:36` | `epw.split('.')[0]` trunca nombres de EPW con puntos (p. ej. `City.RCP4.5.epw`). Usar `os.path.splitext`. |
| j | `run/run.py:145-157` | `removefiles()` borra **todo** lo que no sea py/idf/epw/csv/eso del directorio de trabajo, sin confirmación. Muy peligroso como API pública. |
| k | `utils.py:497-501` | `eval(value)` sobre contenido del IDF en `get_accim_args` — ejecuta código arbitrario si el IDF no es de confianza. Usar `ast.literal_eval` + fallback. |
| l | `utils.py:316-338` | `amend_idf_version_from_dsb` reescribe el IDF **original** en disco en cada `AccimJob` (borrar + mover), aunque no haya nada que sustituir. Leer primero y reescribir solo si hay match. |
| m | `data/morphing.py:87-96` | `subprocess.run(cadena)` sin `check=True` ni control de retorno; como cadena solo funciona bien en Windows. Usar lista de argumentos + `check=True`. |
| n | `data/preprocessing.py:141` | `requests.get(url)` sin `timeout` en `give_address` → puede colgarse indefinidamente. |
| o | `sim/hvac/resolver.py` | El docstring de `resolve_hvac_zone_map` dice que los objetos no resueltos "no se incluyen en el dict", pero la estrategia D siempre devuelve algo; y documenta `verboseMode` cuando el parámetro es `verbose`. |
| p | `sim/batch.py:377` | Mensaje de error `'...'+output_freqs` concatena `str + list` → `TypeError` en lugar del `ValueError` intencionado. |
| q | `sim/engine.py` (`__init__`) | Si `script_type=None` (su valor por defecto), `script_type.lower()` lanza `AttributeError` en vez de un error claro. Validar antes. |

---

## 3. Arquitectura y deuda técnica

### 3.1. `accim/__init__.py` hace trabajo del módulo obsoleto

El `__init__` raíz contiene tres monkey-patches (dask/EvaluatorEP, platypus/besos optimizer, `_freeze`) y el shim del módulo `imp`, todos **exclusivos del flujo de optimización** (`parametric_and_optimisation`). Esto significa que `import accim` intenta importar `besos`, `dask` y `platypus` aunque el usuario solo quiera `Table` o `addAccis`. Además, el shim `sys.modules["imp"] = types.ModuleType("imp")` crea un módulo vacío: cualquier código que haga `imp.load_source(...)` fallará con un `AttributeError` confuso en vez de un `ImportError` claro.

**Propuesta:** mover los tres parches a `accim/parametric_and_optimisation/__init__.py` cuando actualices ese módulo desde la otra rama, y dejar el `__init__` raíz solo con `__version__`.

### 3.2. Dependencia dura de `besos` en el núcleo

`engine.py`, `single.py`, `apmv.py`, `utils.py`, `idf_generation.py` y `data/postprocessing/main.py` importan `besos` (básicamente por `get_building` y `IDF_class`). `besos` está semiabandonado y arrastra `dask`, `platypus`, etc. Todo lo que el núcleo usa de besos se puede replicar con **eppy puro** (~30 líneas: detectar la versión del IDF y fijar el IDD).

**Propuesta:** crear `accim/compat.py` con `get_building()` propio basado en eppy, y dejar `besos` como dependencia *extra* (`pip install accim[optimisation]`).

### 3.3. Los tres ficheros gigantes

| Fichero | Líneas | Problema |
|---------|--------|----------|
| `data/postprocessing/main.py` | 4.028 | `Table.__init__` ocupa **~1.330 líneas** y hace todo el pipeline (lectura, limpieza, agregación, renombrado). Imposible de testear por partes; los 30+ `todo` internos lo confirman. |
| `sim/idf_generation.py` | 848 | La estructura de bucles anidados de 6 niveles está **duplicada dos veces** (una para la vista previa de nombres, otra para la generación). Cada corrección hay que hacerla en 6 sitios. |
| `sim/ems/programs.py` + `ems/setast_models.py` | 4.593 | Aceptable por ser plantillas Erl (dominio), pero `add_output_variables_standard` (285 líneas) y compañía mezclan lógica y datos. |

**Propuesta concreta para `idf_generation.py`:** extraer un generador único de combinaciones:

```python
def iter_combinations(comfort_standards, categories, comfort_modes, hvac_modes, ...):
    """Yield ParamCombo(...) aplicando las reglas de compatibilidad CS/CAT/CM una sola vez."""
```

y consumirlo dos veces (para nombres y para generación). Eliminaría ~500 líneas duplicadas y de paso los bugs 2.4 y 2.13-f, porque `ComfMod_value` pasaría a ser un campo del combo, siempre definido.

**Propuesta para `Table`:** trocear `__init__` en métodos privados (`_load_csvs`, `_clean_columns`, `_aggregate`, `_split_names`...) sin cambiar el API. Los tests golden existentes ya protegen ese refactor — es el momento ideal.

### 3.4. Duplicación de vocabularios de validación

`fullScriptTypeList`, `fullOutputsTypeList`, `fullOutputsFreqList`, `fullTempCtrllist`, `fullEPversionsList` existen por triplicado (`lists.py`, `sim/prompts.py`, `sim/single.py`) y ya han divergido (el `'25.2'` de `single.py`). Única fuente: `accim/lists.py` (o mejor, `enum`s), e importar desde ahí. Las comparaciones dobles `'Standard', 'standard'` se resuelven normalizando con `.lower()` en un solo punto.

### 3.5. `accim/misc/` se distribuye dentro del paquete

Contiene scripts legacy (`parametric_v04.py`, `parametric_v05.py`, `amend_idfs*.py`, `wrangling dfs for sns.py` — con espacios en el nombre, ni siquiera importable). Nada lo importa. **Propuesta:** moverlo fuera del paquete (`tools/` o borrarlo; git conserva la historia).

### 3.6. Interactividad mezclada con lógica

La refactorización de `prompts.py` fue un acierto; queda pendiente aplicar el mismo patrón a:
- `rename_epw_files` (`preprocessing.py`): 8 `input()` entrelazados con la lógica de renombrado → inutilizable en pipelines/notebooks sin TTY.
- `apply_specified_outputs` (`programs.py:1428-1430`): prompt dentro de bucle por frecuencia.

---

## 4. Empaquetado, repositorio y CI

1. **Tamaño del paquete (urgente si publicas 1.0):** `accim/sample_files` = **137 MB** (107 MB solo notebooks con outputs, 17 MB CSVs) y `MANIFEST.in` hace `recursive-include accim/sample_files *`. El wheel 0.7.8.1 ya pesa 37 MB; con el contenido actual el 1.0 puede acercarse o superar el **límite de 100 MB de PyPI**. Propuestas:
   - Limpiar outputs de los notebooks (`nbstripout`) y hacer `prune` de `.ipynb_checkpoints`, `backup/`, `__pycache__`.
   - Mover los datasets pesados a *GitHub Releases* o a un repo aparte y descargarlos bajo demanda (p. ej. `accim.sample_files.download()` con `pooch`).
2. **Migrar a `pyproject.toml`** (PEP 621): `setup.py` con `import accim` en tiempo de build es frágil; además quedan ~90 líneas de código muerto comentado (el PostInstallCommand).
3. **Dependencias:** `install_requires` incluye `besos`, `SALib`, `datapackage`, `scikit-learn`, `seaborn`. `datapackage` está deprecado (sustituido por `frictionless`); `SALib`/`besos` son del módulo obsoleto; `scikit-learn` habría que confirmar si el núcleo lo usa. Propuesta de extras: `accim[optimisation]`, `accim[geo]` (geopy/pycountry/unidecode), `accim[plots]`.
4. **`.gitignore`:** faltan `__pycache__/` y `*.pyc` — de ahí el ruido actual de `git status` (decenas de directorios pycache sin trackear). También hay un IDF suelto en la raíz del repo (`OSM_TestResidentialUnit_...idf`) y carpetas `ondrive_backup`, `test_evaluator`, `jupyter notebooks` que convendría mover o ignorar.
5. **Sin CI:** no hay `.github/workflows`. Con la suite de 23 ficheros de test ya existente, un workflow de GitHub Actions (lint + tests puros que no requieren EnergyPlus, en matrix 3.9-3.13) es barato y de alto valor. Los tests golden que necesitan E+ pueden marcarse con un marker (`@pytest.mark.needs_energyplus`) y ejecutarse solo en un job opcional con E+ instalado (existen bundles/containers oficiales).
6. **Rutas de IDD hardcodeadas a Windows** (`utils.py:560-590`, `C:/EnergyPlusVX-Y-0/...`): en Linux/macOS es `/usr/local/EnergyPlus-X-Y-0/`. Propuesta: buscar en las rutas por SO + respetar una variable de entorno (`ENERGYPLUS_DIR` o el `IDD_PATH` que ya usan otras herramientas), y devolver `None`/lanzar excepción tipada en vez de la cadena mágica `'not-supported'`.

---

## 5. Propuestas de mejora priorizadas

### P0 — Correcciones antes de publicar 1.0 (1-2 días)

1. Bug 2.1 (keyword `EnergyPlus_version` → `energyplus_version`) + test con versión explícita y test batch multi-IDF.
2. Bug 2.3 (rama SingleCooling) y bug 2.12 (modelos sin People).
3. Bug 2.2 (`remove_duplicated_output_variables`) — o corregirlo o convertirlo temporalmente en no-op explícito documentado.
4. Bugs 2.5 y 2.6 (pérdida de datos y regresión `'nan'` en `rename_epw_files`).
5. Bug 2.7 (borrado por subcadena en batch).
6. Quitar `'25.2'` huérfano / unificar listas de versiones (2.13-d).
7. Añadir `__pycache__/` a `.gitignore`.

### P1 — Robustez y empaquetado (1-2 semanas)

1. Adelgazar `sample_files` y ajustar `MANIFEST.in` (§4.1) — bloqueante para publicar en PyPI con seguridad.
2. `pyproject.toml` + extras de dependencias (§4.2-4.3).
3. CI mínima en GitHub Actions (§4.5).
4. Rutas IDD multiplataforma + variable de entorno (§4.6).
5. Sustituir `eval` por `ast.literal_eval` (2.13-k) y añadir `timeout` a las requests de geocodificación (2.13-n).
6. Bugs 2.8-2.11 (NameError en `apply_specified_outputs`, `output_idfs` compartido, `pd.concat([])`, PCMs de aPMV).

### P2 — Refactor dirigido (el gran retorno de inversión)

1. **`idf_generation.py`:** iterador único de combinaciones (§3.3) — elimina la duplicación de 600 líneas y los bugs de variables residuales de una vez. Los goldens existentes protegen el cambio.
2. **`Table.__init__`:** trocear en métodos privados testables (§3.3).
3. **`rename_epw_files`:** separar en (a) función pura que propone nombres, (b) capa interactiva opcional, (c) función que aplica el plan — mismo patrón que ya usaste con `prompts.py`. De paso: unificar las 3 clases `give_address*` en una sola función con reintentos, respetar la política de Nominatim (User-Agent identificable + 1 req/s) y cachear resultados.
4. **`set_comfort_fields_people`:** las 4 ramas casi idénticas de 35 líneas se reducen a una copia genérica de campos compartidos + diffs por versión.
5. **Quitar besos del núcleo** (§3.2) cuando toques `parametric_and_optimisation`, moviendo también los monkey-patches del `__init__` raíz (§3.1).

### P3 — Calidad continua (progresivo)

1. **Logging:** sustituir los cientos de `print(...)` condicionados por `verbose` por `logging.getLogger('accim')`; `verbose` pasaría a configurar el nivel. Beneficio inmediato en notebooks y pipelines.
2. **Linter/formateador:** `ruff` (reglas F, E, B, UP) cazaría automáticamente varios de los bugs de este informe (variables sin definir, comparaciones sospechosas, `except:` desnudos, tuplas accidentales). Añadirlo a CI con una baseline.
3. **Excepciones propias** (`AccimError`, `UnsupportedEnergyPlusVersion`, `ZoneResolutionError`) en lugar de `ValueError`/cadenas mágicas.
4. **Type hints coherentes:** hoy conviven `any` (builtin, incorrecto como anotación) con `typing`. Un pase de `mypy --ignore-missing-imports` en los módulos nuevos es asumible.
5. **Nombres PEP 8 pendientes:** clases `rename_epw_files`, `give_address*`, `print_available_outputs_mod` (snake_case). Si haces otro clean-break es el momento; si no, alias con `DeprecationWarning`.
6. Completar o retirar `modify_param` (2.13-b) y el `todo` de validación AHST>ACST (`batch.py:300`).

---

## 6. Lo que está bien (y conviene conservar)

- **Suite de caracterización golden** con `--update-golden` y bugs conocidos como `xfail` estrictos: es exactamente la red de seguridad correcta para este tipo de refactor. El comentario de `test_known_bugs.py` documentando el bug PMV es ejemplar.
- **`hvac/resolver.py`:** diseño en cascada A→B→C1→C2→D limpio, bien comentado, con warnings accionables que indican al usuario exactamente qué `hvac_zone_map` pasar.
- **`apmv.py`:** resolución de jerarquía Space/ZoneList/Zone bien pensada, sanitización EMS centralizada, deduplicación de outputs por clave normalizada.
- **`prompts.py`:** el aislamiento de I/O interactivo es el patrón a extender al resto.
- **`MIGRATION.md` + CHANGELOG** en formato Keep-a-Changelog: la gestión del clean-break 1.0 está bien comunicada.
- Convergencia de los caminos single/batch en `_scan_and_setup_zones` y `apply_accis` (única fuente de verdad para la secuencia de inyección).

---

*Informe generado el 19/07/2026 mediante revisión estática del código en la rama `refactor/sim-v1`. Las referencias `fichero:línea` corresponden al estado actual de esa rama.*
