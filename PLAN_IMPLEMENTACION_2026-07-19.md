# Plan de implementación — Correcciones y mejoras de accim

- **Fecha del plan:** 19/07/2026
- **Basado en:** [`INFORME_REVISION_2026-07-19.md`](INFORME_REVISION_2026-07-19.md) (revisión de la rama `refactor/sim-v1`)
- **Alcance:** todo el paquete excepto `accim/parametric_and_optimisation` (se actualizará desde otra rama; ver T51 para el único punto de contacto).
- **Objetivo del documento:** que cualquier sesión futura (tuya o de un agente) pueda ejecutar cada tarea **sin releer el informe ni re-explorar el código**. Cada tarea incluye: archivos y líneas, cambio exacto (antes/después), tests de verificación, riesgos y criterio de aceptación.

> ⚠️ **Las referencias `fichero:línea` corresponden al estado de la rama `refactor/sim-v1` a 19/07/2026.** Si se ejecutan tareas fuera de orden, las líneas pueden desplazarse: buscar siempre por el fragmento de código citado, no solo por el número de línea.

---

## 0. Protocolo de trabajo (leer antes de cada sesión)

### 0.1. Preparación de cada sesión

```bash
cd D:/Python/accim
git status                  # confirmar árbol limpio
git checkout refactor/sim-v1
git pull                    # si hay remoto
python -m pytest tests/ -x -q --ignore=tests/parametric_and_optimisation --ignore=tests/parametric_and_optimisation_full_workflow
```

Usar el **entorno virtual donde están instaladas las dependencias de accim** (besos, eppy, pandas...). Los tests que requieren EnergyPlus se auto-saltan si no encuentran el IDD (`pytest.skip` interno), así que la suite siempre es ejecutable.

### 0.2. Convenciones de ramas y commits

- Una rama por fase: `fix/p0-bugs`, `chore/p1-packaging`, `refactor/p2-idf-generation`, etc.
- Un commit por tarea (ID de tarea en el mensaje): `fix(utils): T01 unify get_idd_path_from_ep_version keyword (energyplus_version)`.
- **Nunca** mezclar en el mismo commit una corrección de código y una regeneración de goldens (ver 0.3).

### 0.3. Protocolo de goldens (crítico)

Los tests de caracterización (`tests/sim`, `tests/data`) congelan el IDF generado. Varias correcciones de este plan **cambian legítimamente el output** (p. ej. T03 elimina duplicados que antes no se eliminaban). Protocolo:

1. Aplicar la corrección → `python -m pytest tests/sim tests/data -q`.
2. Si fallan goldens: inspeccionar el diff del test y **verificar que el único cambio es el esperado** por la tarea (cada tarea indica el "cambio de golden esperado").
3. Regenerar deliberadamente: `python -m pytest tests/sim tests/data --update-golden`.
4. Commit separado: `test: regenerate goldens after T03 (duplicated Output:Variable now actually removed)`.
5. Si el diff contiene cambios NO esperados → **parar, no regenerar**, investigar.

### 0.4. Tests xfail

`tests/sim/test_known_bugs.py` tiene `xfail(strict=True)`. Si una tarea corrige el bug correspondiente, el test pasará a **XPASS y la suite fallará**: es intencionado. La tarea correspondiente (T31) indica cómo promocionarlo a golden.

### 0.5. Reparto sugerido en sesiones (por cuota)

| Sesión | Contenido | Esfuerzo estimado |
|--------|-----------|-------------------|
| S1 | Fase 0 (baseline) + T01–T06 | 2–3 h |
| S2 | T07–T15 (resto P0) + regeneración de goldens | 2–3 h |
| S3 | T16–T20 (empaquetado) | 2–3 h |
| S4 | T21–T27 (robustez P1) | 2–3 h |
| S5 | T30–T31 (refactor idf_generation, la tarea más grande) | 4–6 h |
| S6 | T32–T35 (Table, rename_epw_files, base.py) | 4–6 h |
| S7 | T40–T45 (besos/compat, monkey-patches) | 3–4 h |
| S8 | T50–T57 (calidad continua: logging, ruff, excepciones) | progresivo |

Dependencias duras: T31 depende de T30. T20 (CI) rinde más tras T40 (besos opcional), pero puede hacerse antes con nota. Todo lo demás es independiente y puede reordenarse.

---

## FASE 0 — Preparación (hacer una sola vez, antes de T01)

### T00 — Baseline y limpieza del repo

**Objetivo:** partir de un estado reproducible.

1. **`.gitignore`** — añadir al final:
   ```gitignore
   __pycache__/
   *.py[cod]
   *.egg-info/
   .coverage
   htmlcov/
   ```
   (La entrada `*.egg-info/` ya existe; no duplicar.)
2. Confirmar que los `__pycache__` que aparecen en `git status` desaparecen de "untracked". **No** hay ninguno trackeado (verificado en la revisión), así que no hace falta `git rm`.
3. Ejecutar la suite completa y **guardar el resultado como baseline** en un archivo de notas de la sesión:
   ```bash
   python -m pytest tests/ -q --ignore=tests/parametric_and_optimisation --ignore=tests/parametric_and_optimisation_full_workflow | tail -20
   ```
   Anotar: nº passed / skipped / xfailed. El estado esperado del baseline es: todo verde con 1 xfail (`test_batch_pmv_currently_broken`) y skips si no está EnergyPlus.
4. Decidir qué hacer con los ficheros sueltos de la raíz (no bloqueante): `OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf`, `testing_new_functionalities_optimisation.py`, `test_evaluator/`, `jupyter notebooks/`, `ondrive_backup/` → moverlos fuera del repo o añadirlos a `.gitignore`.

**Criterio de aceptación:** `git status` limpio de pycache; baseline de tests anotado.

---

## FASE 1 — P0: Correcciones de bugs (T01–T15)

### T01 — CRÍTICO: unificar el keyword de `get_idd_path_from_ep_version`

**Bug:** `accim/sim/engine.py:119` llama con `energyplus_version=`, la firma real es `EnergyPlus_version` (`accim/utils.py:560`) → `TypeError` con versión explícita.

**Cambios:**

1. `accim/utils.py:560` — renombrar el parámetro (el estilo 1.0 es snake_case):
   ```python
   # ANTES
   def get_idd_path_from_ep_version(EnergyPlus_version: str):
       if EnergyPlus_version.lower() == '9.1':
   # DESPUÉS
   def get_idd_path_from_ep_version(energyplus_version: str):
       if energyplus_version.lower() == '9.1':
   ```
   Sustituir **todas** las ocurrencias de `EnergyPlus_version` dentro del cuerpo (líneas 560–590, unas 15 ocurrencias).
2. `accim/run/run.py:91` y `:97` — actualizar las dos llamadas:
   ```python
   iddfile = get_idd_path_from_ep_version(energyplus_version=energyplus_version)
   ```
3. Los tests existentes llaman **posicionalmente** (`get_idd_path_from_ep_version("9.6")`) — no requieren cambio.

**Test nuevo** — añadir a `tests/utils/test_utils_pure.py`:
```python
def test_get_idd_path_accepts_snake_case_keyword():
    # Regresión T01: engine.py llama con este keyword exacto.
    from accim.utils import get_idd_path_from_ep_version
    assert get_idd_path_from_ep_version(energyplus_version="9.6").endswith("Energy+.idd")
    assert get_idd_path_from_ep_version(energyplus_version="0.0") == "not-supported"
```

**Verificación:** `python -m pytest tests/utils -q` + `grep -rn "EnergyPlus_version" accim tests --include="*.py"` debe devolver **cero** resultados (fuera de `parametric_and_optimisation`).

---

### T02 — CRÍTICO: no contaminar `energyplus_version` entre IDFs del batch

**Bug:** `accim/sim/batch.py:435-436` reasigna la variable del bucle:
```python
if energyplus_version.lower() == 'auto':
    energyplus_version = '.'.join([str(i) for i in z.idf1.idd_version[:2]])
```
Con `auto` y varios IDFs, el 2º IDF ya no entra por la rama `auto` (y además, sin T01, crasheaba). Con IDFs de versiones mixtas, se les impone la versión del primero.

**Cambio** en `accim/sim/batch.py` (dentro de `for file in filelist:`):
```python
# ANTES
if energyplus_version.lower() == 'auto':
    energyplus_version = '.'.join([str(i) for i in z.idf1.idd_version[:2]])
...
output_gen_dataframe = z.apply_accis(
    ...
    energyplus_version=energyplus_version,

# DESPUÉS
if energyplus_version.lower() == 'auto':
    ep_version_resolved = '.'.join([str(i) for i in z.idf1.idd_version[:2]])
else:
    ep_version_resolved = energyplus_version
...
output_gen_dataframe = z.apply_accis(
    ...
    energyplus_version=ep_version_resolved,
```
`energyplus_version` (el argumento del usuario) no debe reasignarse **nunca** dentro del bucle. Revisar que ninguna otra línea del `__init__` posterior al bucle use `energyplus_version` esperando el valor resuelto (verificado: no lo hay; `self.arguments` guarda el valor original del usuario, lo cual es correcto).

**Test nuevo** — `tests/sim/test_batch_multi_idf.py`:
```python
"""Regresión T01+T02: batch con >1 IDF y modo auto / versión explícita."""
import os, shutil
from pathlib import Path
import pytest
import accim.utils

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE = REPO_ROOT / "accim" / "sample_files" / "sample IDFs" / "input_IDFs" / \
    "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V960.idf"

def _needs_ep96():
    idd = accim.utils.get_idd_path_from_ep_version("9.6")
    if idd == "not-supported" or not os.path.exists(idd):
        pytest.skip("EnergyPlus 9.6 no instalado")

@pytest.mark.parametrize("ep_version", ["auto", "9.6"])
def test_batch_two_idfs(tmp_path, ep_version):
    _needs_ep96()
    if not SAMPLE.exists():
        pytest.skip("IDF de muestra ausente")
    shutil.copy(str(SAMPLE), str(tmp_path / "model_a.idf"))
    shutil.copy(str(SAMPLE), str(tmp_path / "model_b.idf"))
    prev = os.getcwd(); os.chdir(str(tmp_path))
    try:
        from accim.sim import batch
        batch.AddAccis(
            script_type="vrf_mm", supply_air_temp_method="supply air temperature",
            temp_control="temperature", output_keep_existing=False,
            output_gen_dataframe=False, output_type="standard",
            output_freqs=["hourly"], energyplus_version=ep_version,
            comfort_standard=[1], category=[2], comfort_mode=[3],
            hvac_mode=[0], vent_control=[0],
            confirm_generation=True, verbose=False,
        )
        generated = [f for f in os.listdir() if "[CS_" in f]
        assert any(f.startswith("model_a") for f in generated)
        assert any(f.startswith("model_b") for f in generated)
    finally:
        os.chdir(prev)
```

**Riesgo de golden:** ninguno (los goldens actuales usan 1 IDF).

---

### T03 — ALTO: reescribir `remove_duplicated_output_variables`

**Bug:** `accim/sim/ems/programs.py:1357-1378` — compara `Variable_Name` (str) contra una lista de **objetos** (nunca detecta nada) y, además, el borrado usa `idfobjects['Output:Variable'][-1]` (borraría los últimos N, no los duplicados).

**Cambio** — sustituir el cuerpo completo de la función (mantener la firma y el docstring, eliminar el bloque comentado "Alternative method" de las líneas 1380-1397):
```python
def remove_duplicated_output_variables(self):
    """Remove duplicated Output:Variable objects for accim.

    Two outputs are duplicates when Key_Value, Variable_Name,
    Reporting_Frequency and Schedule_Name all match (case-insensitive).
    """
    seen = set()
    duplicates = []
    for output in self.idf1.idfobjects['Output:Variable']:
        key = (
            str(output.Key_Value or '').strip().upper(),
            str(output.Variable_Name or '').strip().upper(),
            str(output.Reporting_Frequency or '').strip().upper(),
            str(output.Schedule_Name or '').strip().upper(),
        )
        if key in seen:
            duplicates.append(output)
        else:
            seen.add(key)
    for output in duplicates:
        self.idf1.removeidfobject(output)
```
Nota: incluir `Key_Value` en la clave es la corrección del "Problema 3" del informe — dos outputs con igual variable pero distinta key son legítimos y deben conservarse.

**Test nuevo** — `tests/sim/test_output_variables.py` (unitario, sin EnergyPlus: construir un IDF mínimo en memoria con eppy usando el IDD 9.6 si está, o skip):
```python
def test_remove_duplicated_output_variables(idf_960_blank):  # fixture: IDF con solo Version
    from accim.sim.ems.programs import remove_duplicated_output_variables
    class Holder: pass
    h = Holder(); h.idf1 = idf_960_blank
    for _ in range(2):
        h.idf1.newidfobject('Output:Variable', Key_Value='*',
                            Variable_Name='Zone Mean Air Temperature',
                            Reporting_Frequency='Hourly')
    h.idf1.newidfobject('Output:Variable', Key_Value='ZONE1',
                        Variable_Name='Zone Mean Air Temperature',
                        Reporting_Frequency='Hourly')
    remove_duplicated_output_variables(h)
    outs = h.idf1.idfobjects['Output:Variable']
    assert len(outs) == 2                      # se elimina 1 duplicado exacto
    assert {o.Key_Value for o in outs} == {'*', 'ZONE1'}  # la key distinta sobrevive
```

**Cambio de golden esperado:** los IDFs golden pueden perder objetos `Output:Variable` que estaban repetidos. Verificar en el diff que **solo desaparecen duplicados exactos** y regenerar (protocolo 0.3).

---

### T04 — ALTO: rama `SingleCooling` sin bucle en `add_forscript_schedule_existing_hvac`

**Bug:** `accim/sim/hvac/existing.py:82-98` usa `j` sin definir su bucle.

**Cambio 1** — añadir el bucle (misma estructura que la rama SingleHeating de las líneas 64-81):
```python
# ANTES (líneas 82-98)
elif 'ThermostatSetpoint:SingleCooling' in self.HVACzonelist[i][0]:
    if "ACST_Sch_" + self.HVACzonelist[i][2][j] in [sch.Name ...
# DESPUÉS
elif 'ThermostatSetpoint:SingleCooling' in self.HVACzonelist[i][0]:
    for j in range(len(self.HVACzonelist[i][2])):
        if "ACST_Sch_" + self.HVACzonelist[i][2][j] in [sch.Name
                                                         for sch
                                                         in self.idf1.idfobjects['Schedule:Compact']]:
            ...
```
(Indentar todo el bloque interior un nivel; el contenido no cambia.)

**Cambio 2** — corregir las comparaciones invertidas de las líneas 100-111:
```python
# ANTES
if self.HVACzonelist[j][0] in 'ThermostatSetpoint:SingleHeating':
    for SP in [h for h in ... if h.Name in self.HVACzonelist[j][3][k]]:
# DESPUÉS
if self.HVACzonelist[j][0] == 'ThermostatSetpoint:SingleHeating':
    for SP in [h for h in ... if h.Name == self.HVACzonelist[j][3][k]]:
```
Aplicar `in` → `==` en las 3 ramas (SingleHeating, SingleCooling, DualSetpoint) y en los 4 filtros `h.Name`.

**Test nuevo:** requiere un IDF con termostato SingleCooling. Si no hay muestra disponible, crear el test unitario con un `Holder` como en T03: construir `HVACzonelist = [['ThermostatSetpoint:SingleCooling', ['ZONE1','ZONE2'], ['ZONE1','ZONE2'], ['SP1','SP2']]]` sobre un IDF en blanco con dos `ThermostatSetpoint:SingleCooling` y verificar que se crean `ACST_Sch_ZONE1` **y** `ACST_Sch_ZONE2` y que cada SP apunta a su schedule.

**Cambio de golden esperado:** ninguno para los goldens actuales (usan DualSetpoint), pero verificar.

---

### T05 — ALTO: pérdida de datos en `rename_epw_files` (exclusión + borrado)

**Bug:** `accim/data/preprocessing.py:600-637` — los EPWs excluidos del renombrado siguen en `epw_files_to_rename` y se borran si `confirm_deletion`.

**Cambio** — tras construir `exclusion_list` (línea 600-606) y **antes** del bloque `if confirm_deletion ...` (línea 627), filtrar la lista de borrado:
```python
# Nunca borrar originales que fueron excluidos del renombrado ni que
# no llegaron a copiarse (SameFileError ya los retira de la lista).
files_safe_to_delete = [
    epw_df.loc[i, 'EPW_file_names']
    for i in range(len(epw_df))
    if i not in exclusion_list
    and epw_df.loc[i, 'EPW_file_names'] in epw_files_to_rename
]
```
y en el bloque de borrado (líneas 634-637) iterar `files_safe_to_delete` en lugar de `epw_files_to_rename`. Además, si `confirm_renaming` es False, el borrado debe saltarse por completo (no hay copias):
```python
if confirm_deletion and confirm_renaming:
    for i in files_safe_to_delete:
        os.remove(i)
        print(f'The file {i} has been deleted.')
elif confirm_deletion and not confirm_renaming:
    print('Deletion skipped: files were not renamed, so originals are the only copies.')
```

**Test** — ampliar `tests/data/test_preprocessing.py`: caso con 2 EPWs, `exclusion_list` simulada... la exclusión se lee por `input()`; este test necesita monkeypatch de `builtins.input`. Secuencia de inputs a parchear (en orden): amendments (`''`), exclusión (`'1'`), renombrado (`'y'`), borrado (`'y'`). Asserts: el EPW con ID 1 sigue existiendo con su nombre original; el ID 0 tiene copia renombrada y original borrado. (Los tests existentes de preprocessing ya hacen monkeypatch de red/geocoding — reutilizar esas fixtures.)

---

### T06 — ALTO: comparación con la cadena `'nan'` en `rename_epw_files`

**Bug:** `accim/data/preprocessing.py:251` y `:285` — `== 'nan'` nunca es cierto con `NaN` real; además `KeyError` posible si ningún fichero tuvo match (columna inexistente).

**Cambio 1** — inicializar las columnas antes de los bucles de detección (insertar tras crear `epw_df`, junto a la línea 220):
```python
epw_df['EPW_scenario'] = np.nan
epw_df['EPW_year'] = np.nan
```
**Cambio 2** — sustituir las dos comparaciones:
```python
# línea 251  ANTES: if epw_df.loc[i, 'EPW_scenario'] == 'nan':
if pd.isna(epw_df.loc[i, 'EPW_scenario']):
# línea 285  ANTES: if epw_df.loc[i, 'EPW_year'] == 'nan':
if pd.isna(epw_df.loc[i, 'EPW_year']):
```
**Cambio 3** — el bloque de la línea 277-281 (`EPW_scenario_year`) usa `EPW_year` que puede ser aún NaN en ese punto: mover el bloque de asignación de `EPW_scenario_year` (líneas 277-281) **después** del bloque de fallback de `EPW_year` (líneas 283-298). Revisar el orden final: detección escenario → fallback escenario → detección año → fallback año → composición `EPW_scenario_year`.

**Test** — en `tests/data/test_preprocessing.py`: EPW llamado `Weather_NoScenario.epw` (sin RCP/SSP ni año) → tras el proceso, `EPW_scenario == 'Present'` y el nombre propuesto termina en `_Present`. Y un `City_RCP45.epw` sin año → no debe lanzar `TypeError`.

---

### T07 — MEDIO: borrado de `_pymod` por subcadena en batch

**Bug:** `accim/sim/batch.py:490-496` — `if file in i: remove(i)` borra `vivienda2_pymod.idf` cuando falla `vivienda`.

**Cambio:**
```python
# ANTES
filelist_pymod = ([file for file in listdir() if file.endswith('.idf') and '_pymod' in file])
for file in notWorkingIDFs:
    for i in filelist_pymod:
        if file in i:
            remove(i)
# DESPUÉS
for file in notWorkingIDFs:
    pymod_name = file + '_pymod.idf'
    if os.path.exists(pymod_name):
        remove(pymod_name)
```
(Añadir `import os` si no está ya importado en ese scope; el `__init__` ya importa `from os import listdir, remove` — usar `from os.path import exists` o `import os.path`.)

**Test:** unitario con `tmp_path`: crear `a_pymod.idf` y `ab_pymod.idf`, simular `notWorkingIDFs=['a']` → solo se borra `a_pymod.idf`. (Puede testearse extrayendo el bucle a una función módulo-nivel `._remove_pymod_files(notWorkingIDFs)` — preferible para testabilidad.)

---

### T08 — MEDIO: `idf_generation` borra TODOS los `*_pymod.idf` del cwd

**Bug:** `accim/sim/idf_generation.py:844-846` borra todos los `_pymod.idf` del directorio, incluso de otras ejecuciones, e incluso con `confirm_generation=False`.

**Cambio:**
```python
# ANTES
filelist_pymod = ([file for file in listdir() if file.endswith('_pymod.idf')])
for file in filelist_pymod:
    os.remove(file)
# DESPUÉS  (filelist_pymod aquí es la lista ya normalizada sin '.idf' del principio de la función)
for file in filelist_pymod:
    pymod_path = file + '.idf'
    if os.path.exists(pymod_path):
        os.remove(pymod_path)
```
Nota: en este punto de la función, la variable `filelist_pymod` contiene los nombres **sin** extensión (se les quitó `.idf` en las líneas 217-221). El bloque actual la **resombrea** con un nuevo listdir — eliminar ese resombreado.

**Decisión de diseño:** mantener el borrado también cuando `confirm_generation=False` sería discutible; propuesta: borrar solo los `_pymod` propios de esta ejecución en ambos casos (comportamiento actual documentado, menos sorpresa). Si prefieres conservarlos con `False`, envolver en `if confirm_generation:`.

---

### T09 — MEDIO: `NameError` en `set_comfort_fields_people` sin objetos People

**Bug:** `accim/sim/hvac/base.py:181` — `del ppl, firstpeopleobject` cuando el modelo no tiene `PEOPLE`.

**Cambio:** eliminar la línea `del ppl, firstpeopleobject` (es inútil al final de una función) y añadir un aviso temprano:
```python
ppl = ([people for people in self.idf1.idfobjects['PEOPLE']])
if len(ppl) == 0:
    if verbose:
        print('WARNING: No PEOPLE objects found in the model; '
              'adaptive comfort fields cannot be applied.')
    return
```

**Test:** unitario con IDF en blanco (solo `Version`) → la llamada no lanza y no crea objetos.

---

### T10 — MEDIO: guard de `pd.concat([])` en batch

**Bug:** `accim/sim/batch.py:482-483` — `ValueError` si todos los IDFs fallaron y `output_gen_dataframe=True`.

**Cambio:**
```python
# ANTES
if output_gen_dataframe:
    self.df_outputs = pd.concat(df_outputs_to_concat)
# DESPUÉS
if output_gen_dataframe:
    if df_outputs_to_concat:
        self.df_outputs = pd.concat(df_outputs_to_concat)
    else:
        self.df_outputs = pd.DataFrame(
            columns=['key_value', 'variable_name', 'reporting_frequency', 'schedule_name'])
```
(Las columnas deben coincidir con las que crea `gen_output_dataframe` en `programs.py:1470` — verificar el nombre exacto de columnas allí antes de commitear.)

---

### T11 — MEDIO: `apply_specified_outputs` no interactivo lanza `NameError`

**Bug:** `accim/sim/ems/programs.py:1399-1448` — si `remove_or_keep` ≠ None, `outputs_to_delete` no se asigna.

**Cambio** — añadir parámetro `custom_outputs` y unificar los dos caminos:
```python
def apply_specified_outputs(self, remove_or_keep: str = None, custom_outputs: list = None):
    """Filter Output:Variable objects, either interactively or programmatically.

    :param remove_or_keep: 'remove' to delete the outputs listed in custom_outputs,
        'keep' to delete every output NOT listed. None → interactive prompt per frequency.
    :param custom_outputs: list of Variable_Name strings. Required if remove_or_keep is given.
    """
    if remove_or_keep is not None and custom_outputs is None:
        raise ValueError("custom_outputs must be provided when remove_or_keep is set.")
    if remove_or_keep is not None and remove_or_keep.lower() not in ('remove', 'keep'):
        raise ValueError("remove_or_keep must be 'remove' or 'keep'.")

    all_outputs_to_delete = []
    for freq in ['Timestep', 'Hourly', 'Daily', 'Monthly', 'Runperiod']:
        alloutputs = [o for o in self.idf1.idfobjects['Output:Variable']
                      if freq == o.Reporting_Frequency]
        if not alloutputs:
            continue
        if remove_or_keep is None:
            alloutputsnames = list(dict.fromkeys(o.Variable_Name for o in alloutputs))
            print(f'\nThe current existing outputs for {freq} Frequency are:')
            print(*alloutputsnames, sep='\n')
            from accim.sim.prompts import prompt_custom_outputs
            action, selection = prompt_custom_outputs()
        else:
            action, selection = remove_or_keep, custom_outputs
        if action.lower() == 'remove':
            outputs_to_delete = [o for o in alloutputs if o.Variable_Name in selection]
        else:  # keep
            outputs_to_delete = [o for o in alloutputs if o.Variable_Name not in selection]
        all_outputs_to_delete.extend(outputs_to_delete)

    for obj in all_outputs_to_delete:
        self.idf1.removeidfobject(obj)
```
Eliminar los tres bloques de código comentado de la versión actual (líneas 1438-1460). El único llamador es `engine.apply_accis` (`self.apply_specified_outputs()` sin argumentos) — sin cambios allí.

**Test:** unitario tipo T03: 3 outputs, `remove_or_keep='keep', custom_outputs=['Zone Mean Air Temperature']` → solo sobrevive esa.

---

### T12 — MEDIO: PCMs de aPMV limitados a los programas propios

**Bug:** `accim/sim/apmv.py:916-933` — crea un `ProgramCallingManager` para **cada** programa EMS del modelo.

**Cambio 1** — hacer que los generadores devuelvan los nombres creados. En `_add_apmv_programs` (línea 765), acumular y devolver:
```python
def _add_apmv_programs(...) -> List[str]:
    created = []
    ...
    # tras cada newidfobject de programa (o si ya existía y es nuestro):
    created.append(prog_name)
    ...
    return created
```
Incluir en `created` los nombres aunque ya existieran (son programas aPMV de una pasada anterior que también necesitan PCM). Los nombres propios son: `set_cooling_season_input_data`, `set_cooling_season`, `set_zone_input_data_{suffix}`, `apply_aPMV_{suffix}`, `monitor_aPMV_{suffix}`, `count_aPMV_comfort_hours_{suffix}`.

**Cambio 2** — `_add_apmv_program_calling_managers(building, program_names, verbose_mode)`:
```python
def _add_apmv_program_calling_managers(building: IDF, program_names: List[str], verbose_mode: bool):
    pcmlist = [pcm.Name for pcm in building.idfobjects['EnergyManagementSystem:ProgramCallingManager']]
    for prog in program_names:
        if prog not in pcmlist:
            building.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=prog,
                                  EnergyPlus_Model_Calling_Point="BeginTimestepBeforePredictor",
                                  Program_Name_1=prog)
            if verbose_mode: print(f"Added ProgramCallingManager for: {prog}")
```
**Cambio 3** — en `apply_apmv_setpoints` (línea 445-448):
```python
apmv_programs = _add_apmv_programs(building, ems_target_suffixes, df_arguments,
                                   cooling_season_start, cooling_season_end, verbose_mode)
_add_apmv_program_calling_managers(building, apmv_programs, verbose_mode)
```

**Test:** IDF con un programa EMS preexistente `UserProgram` → tras `apply_apmv_setpoints`, no existe ningún PCM llamado `UserProgram`.

**Cambio de golden esperado:** si algún golden de aPMV existe y el modelo de muestra tenía programas ACCIS previos, pueden desaparecer PCMs → verificar diff (solo eliminaciones de PCM ajenos).

---

### T13 — MEDIO: bloque `Output:Meter` anidado y variable `freq` sombreada en aPMV

**Bug:** `accim/sim/apmv.py:1023-1053` — el bloque de meters está dentro del `for freq in outputs_freq:` exterior y vuelve a iterar `for freq in outputs_freq:`.

**Cambio:** desindentar el bloque completo `# 3. Add Output:Meter objects` (desde `meter_objects = [` hasta el final del doble bucle) **un nivel**, para que quede fuera del bucle exterior, al mismo nivel que `# 4. Ensure OutputControl:Files`. El bucle interior `for freq in outputs_freq:` ya existente pasa a ser el único.

**Verificación:** sin cambio funcional en el IDF (la deduplicación ya evitaba duplicados) → los goldens no deben cambiar. Test rápido: llamar `apply_apmv_setpoints` con `outputs_freq=['hourly','daily']` y contar que cada meter aparece exactamente 2 veces (una por frecuencia).

---

### T14 — Lote de fixes menores (una pasada, commits pequeños)

| ID | Archivo | Cambio exacto |
|----|---------|---------------|
| T14a | `accim/sim/single.py:429` | Eliminar el `pass` tras `return df_outputs_temp`. |
| T14b | `accim/sim/single.py:116-117` | Eliminar `import besos` y `from besos.errors import InstallationError` (no usados). |
| T14c | `accim/sim/single.py:606-607` | `while setpoint_accuracy < 0: raise ...` → `if setpoint_accuracy < 0: raise ValueError(...)`. |
| T14d | `accim/sim/single.py:122-181` | Borrar las 5 listas locales y `from accim.sim.prompts import fullScriptTypeList, SupplyAirTempInputMethodList, fullOutputsTypeList, fullOutputsFreqList, fullTempCtrllist` + `from accim.lists import fullEPversionsList`. ⚠️ La lista local incluía `'25.2'` y no `'auto'`: ver T15 antes de decidir. La validación de la línea 244 debe seguir aceptando la versión detectada del IDF. |
| T14e | `accim/sim/idf_generation.py:180-182, 193-195` | Quitar las **comas finales** (`self.vof_max_temp_diff = vof_max_temp_diff,` → sin coma) en los 6 puntos, y **eliminar** el parche de las líneas 200-206 (`if type(...) is tuple: ...`). |
| T14f | `accim/sim/batch.py:377` | `'Some of the Output frequencies in '+output_freqs+...` → `f'Some of the Output frequencies in {output_freqs} are not valid. ...'`. |
| T14g | `accim/sim/engine.py:88-95` | Validar al principio del `__init__`: `if script_type is None or script_type.lower() not in ('vrf_ac','vrf_mm','ex_ac','ex_mm', 'vrfsystem_mm', 'existinghvac_mm'): raise ValueError(f'Invalid script_type: {script_type!r}')` (comprobar antes la lista real admitida: `_scan_and_setup_zones` acepta también los alias largos `vrfsystem_mm`/`existinghvac_mm`, líneas 177-181). |
| T14h | `accim/sim/engine.py:32-33` | Eliminar `from os import listdir` e `import numpy` del cuerpo de la clase (comprobar con grep que ningún método usa `self.listdir`/`self.numpy` — los métodos importan lo suyo localmente). |
| T14i | `accim/run/run.py:36` | `epw = epw.split('.')[0]` → `epw = os.path.splitext(epw)[0]`. |
| T14j | `accim/utils.py:497-501` | `value = eval(value)` → `import ast` (a nivel de módulo) y `value = ast.literal_eval(value)` dentro del mismo `try/except (ValueError, SyntaxError): pass`. |
| T14k | `accim/data/preprocessing.py:141` | `requests.get(url)` → `requests.get(url, headers={'User-Agent': f'accim/{__version__}'}, timeout=10)` (importar `from accim import __version__`). |
| T14l | `accim/utils.py:316-338` | Reescribir `amend_idf_version_from_dsb`: leer el fichero completo; si `'Version, 9.4.0.002'` no está, **return sin tocar el fichero**; si está, escribir el reemplazo (escritura atómica: tempfile + `os.replace`). |
| T14m | `accim/data/morphing.py:87-96` | `subprocess.run(f'java -cp "{fwg_path}" ...')` → lista de argumentos + control de errores: `result = subprocess.run(['java', '-cp', fwg_path, 'futureweathergenerator.Morph', epw_path, fwg_options_gcms, str(fwg_options_ensemble), str(fwg_options_month_transition_hours), folder_path + '/', str(fwg_options_do_multithread_computation).lower(), str(fwg_options_interpolation_method_id), str(fwg_options_do_limit_variables).lower()], capture_output=not verbose)` seguido de `if result.returncode != 0: raise RuntimeError(f'FutureWeatherGenerator failed for {epw_path} (exit {result.returncode})')`. ⚠️ Antes de fusionar, probar manualmente con FWG que acepta `true/false` en minúscula (Java `Boolean.parseBoolean` es case-insensitive, pero verificar). |
| T14n | `accim/sim/hvac/resolver.py` docstring | Corregir: los objetos siempre acaban en el dict (la estrategia D es fallback universal); renombrar `verboseMode` → `verbose` en la sección Parameters. |
| T14o | `accim/sim/hvac/base.py:301` | Corregir el mensaje copy-paste: `'Not added - Output:VariableDictionary object - it already existed'`. |
| T14p | `accim/sim/single.py:712-743` (`modify_param`) | Decisión requerida (ver §Decisiones). Opción recomendada: retirarla de `accim/sim/__init__.py` (`__all__` y el import) y añadirle `raise NotImplementedError('modify_param is not implemented yet; use modify_accis instead.')` al final, hasta implementarla. |

**Verificación del lote:** `python -m pytest tests/ -q` + grep de regresión:
```bash
grep -rn "eval(" accim --include="*.py" | grep -v literal_eval | grep -v parametric
grep -rn "= .*,$" accim/sim/idf_generation.py | grep "vof_"   # debe devolver 0
```

---

### T15 — Unificar los vocabularios de validación (una sola fuente)

**Problema:** `fullScriptTypeList`, `fullOutputsTypeList`, `fullOutputsFreqList`, `fullTempCtrllist`, `fullEPversionsList` triplicados (`accim/lists.py`, `accim/sim/prompts.py`, `accim/sim/single.py`) y divergentes (`'25.2'`).

**Diseño:**
1. `accim/lists.py` pasa a ser la **única fuente**:
   ```python
   """Lists to be used in the whole project."""

   # Versiones de EnergyPlus con soporte de IDD en accim.utils.get_idd_path_from_ep_version
   SUPPORTED_EP_VERSIONS = ['9.1', '9.2', '9.3', '9.4', '9.5', '9.6',
                            '22.1', '22.2', '23.1', '23.2', '24.1', '24.2',
                            '25.1', '25.2']
   fullEPversionsList = SUPPORTED_EP_VERSIONS + ['auto']   # compat
   epvers_space_objs = ['9.6', '22.1', '22.2', '23.1', '23.2', '24.1', '24.2', '25.1', '25.2']

   fullScriptTypeList = ['vrf_ac', 'vrf_mm', 'ex_mm', 'ex_ac']
   SupplyAirTempInputMethodList = ['supply air temperature', 'temperature difference']
   fullOutputsTypeList = ['standard', 'simplified', 'detailed', 'custom']
   fullOutputsFreqList = ['timestep', 'hourly', 'daily', 'monthly', 'runperiod']
   fullTempCtrllist = ['temperature', 'temp', 'pmv']
   ```
2. **Decisión sobre `'25.2'`:** incluirla exige añadir en `get_idd_path_from_ep_version` la entrada `'25.2' → 'C:/EnergyPlusV25-2-0/Energy+.idd'` (T22 la convierte en tabla; hacerlo allí). Añadir `'25.2'` a `epvers_space_objs` también. Si prefieres no soportarla aún, eliminarla de todas partes — pero dejar constancia en el CHANGELOG.
3. `accim/sim/prompts.py`: borrar las listas locales (líneas 15-46) y reexportarlas para compatibilidad:
   ```python
   from accim.lists import (fullScriptTypeList, SupplyAirTempInputMethodList,
                            fullOutputsTypeList, fullOutputsFreqList, fullTempCtrllist)
   ```
4. Normalización a minúsculas: las listas nuevas de outputs/freqs son solo minúsculas → los puntos de validación deben comparar con `.lower()`:
   - `batch.py:366` → `if output_type.lower() not in fullOutputsTypeList:`
   - `batch.py:374` → `all(elem.lower() in fullOutputsFreqList for elem in output_freqs)`
   - `single.py` (mismas dos comprobaciones tras T14d)
   - `prompts.py:97` y `:102` (los `while` de los inputs) → comparar con `.lower()`
5. `single.py` (T14d) importa de `accim.lists` / `accim.sim.prompts`.

**Test nuevo** — `tests/utils/test_vocabularies.py`:
```python
def test_single_and_prompts_share_lists():
    from accim import lists
    from accim.sim import prompts
    assert prompts.fullScriptTypeList is lists.fullScriptTypeList

def test_every_supported_version_has_idd_path():
    from accim import lists
    from accim.utils import get_idd_path_from_ep_version
    for v in lists.SUPPORTED_EP_VERSIONS:
        assert get_idd_path_from_ep_version(v) != 'not-supported'
```

**Riesgo:** cambiar la validación a case-insensitive es una relajación segura (acepta lo que antes aceptaba y más). No toca goldens.

---

## FASE 2 — P1: Empaquetado, plataforma y robustez (T16–T27)

### T16 — Adelgazar `sample_files` y `MANIFEST.in` (bloqueante para publicar)

**Contexto:** `accim/sample_files` = 137 MB (jupyter_notebooks 107 MB, sample_CSVs 17 MB). Wheel 0.7.8.1 = 37 MB. Límite PyPI: 100 MB/fichero.

**Pasos:**
1. Limpiar outputs de todos los notebooks del paquete:
   ```bash
   pip install nbstripout
   find accim/sample_files -name "*.ipynb" -not -path "*checkpoint*" -exec nbstripout {} \;
   ```
   ⚠️ **Antes de esto**: confirmar que la documentación (Sphinx/nbsphinx) no renderiza esos notebooks CON outputs desde el paquete. Comprobar `docs/source/jupyter_notebooks/` — si los docs usan copias propias, no hay conflicto; si referencian los del paquete, decidir: mantener outputs solo en los que la doc renderiza (lista blanca) o ejecutar notebooks en el build de docs.
2. Borrar del repo: todos los `.ipynb_checkpoints/`, `backup/`, `__pycache__` bajo `sample_files` (`git rm -r --cached` + borrado físico).
3. `MANIFEST.in` — versión endurecida:
   ```
   include README.md
   include LICENSE
   recursive-include accim/sample_files *
   prune accim/sample_files/jupyter_notebooks/*/.ipynb_checkpoints
   recursive-exclude accim __pycache__ *
   recursive-exclude accim *.py[cod]
   global-exclude .ipynb_checkpoints
   prune accim/sample_files/jupyter_notebooks/full_example/backup
   prune accim/sample_files/jupyter_notebooks/full_example_IBPSA/backup
   prune accim/sample_files/jupyter_notebooks/research_paper_case_study_v0-7-3/backup
   ```
4. Evaluar mover `sample_CSVs` (17 MB) fuera del wheel: opción A (rápida) dejarlos; opción B (mejor) publicarlos como asset en un GitHub Release y añadir `accim.sample_files.download_csvs()` con `pooch`. **Decisión pospuesta** — si el wheel tras los pasos 1-3 queda < 30 MB, opción A es aceptable.
5. Medir:
   ```bash
   python -m build
   ls -lh dist/
   python -m zipfile -l dist/accim-1.0.0-py3-none-any.whl | sort -k1 -rn | head -20
   ```

**Criterio de aceptación:** wheel < 50 MB (objetivo < 30), sin `.ipynb_checkpoints` ni `__pycache__` dentro.

### T17 — Migrar a `pyproject.toml`

**Pasos:**
1. Crear `pyproject.toml` en la raíz:
   ```toml
   [build-system]
   requires = ["setuptools>=68"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "accim"
   version = "1.0.0"          # ver nota de versión única abajo
   description = "Transforms PMV-based into adaptive setpoint temperature EnergyPlus building energy models"
   readme = "README.md"
   requires-python = ">=3.9"
   license = { text = "GPL-3.0-or-later" }
   authors = [{ name = "Daniel Sánchez-García", email = "daniel.sanchezgarcia@uca.es" }]
   keywords = ["adaptive thermal comfort", "building energy model",
               "building performance simulation", "energy efficiency"]
   classifiers = [
       "Programming Language :: Python :: 3",
       "Intended Audience :: Science/Research",
       "Operating System :: Microsoft :: Windows",
       "Topic :: Scientific/Engineering",
   ]
   dependencies = [
       "eppy>=0.5.63",
       "pandas",
       "numpy",
       "matplotlib",
       "seaborn",
       "besos",            # ← pasa a extra en T40; mientras tanto se queda
   ]

   [project.optional-dependencies]
   geo = ["geopy", "pycountry", "unidecode", "requests", "certifi"]
   optimisation = ["besos", "SALib", "platypus-opt", "dask"]
   dev = ["pytest>=8.0", "ruff", "build", "nbstripout"]

   [project.urls]
   Homepage = "https://github.com/dsanchez-garcia/accim"
   Documentation = "https://accim.readthedocs.io"

   [tool.setuptools.packages.find]
   include = ["accim*"]

   [tool.setuptools]
   include-package-data = true
   ```
2. **Auditar dependencias antes de fijar la lista** (el `setup.py` actual lista `scikit-learn`, `datapackage`, `SALib`, `besos`...):
   ```bash
   grep -rn "^import \|^from " accim --include="*.py" | grep -v parametric | grep -v sample_files \
     | grep -oE "(import|from) [a-z_0-9]+" | sort | uniq -c | sort -rn
   ```
   Confirmaciones esperadas: `datapackage` se importa en `preprocessing.py` y `postprocessing/main.py` (¿se usa de verdad o es import muerto? — si es muerto, eliminarlo y quitar la dependencia; está deprecado); `scikit-learn` probablemente solo en `parametric_and_optimisation` → quitar del núcleo; `unidecode`, `pycountry`, `geopy`, `requests`, `certifi` → extra `geo` con import perezoso y mensaje claro (`raise ImportError("pip install accim[geo]")`).
3. Vaciar `setup.py` a un shim (o eliminarlo si los .bat de build no lo llaman):
   ```python
   from setuptools import setup
   setup()
   ```
4. **Versión única:** dejar `accim/__init__.py::__version__` como fuente y en `pyproject.toml` usar
   `dynamic = ["version"]` + `[tool.setuptools.dynamic] version = {attr = "accim.__version__"}` — funciona porque el `__init__` protege todos sus imports pesados con try/except (verificado). Alternativa más robusta (recomendada tras T41): mover la versión a `accim/_version.py` sin imports.
5. Actualizar los `.bat` de build (`dist_build_package.bat`) para usar `python -m build`.

**Verificación:** `python -m build && pip install dist/*.whl --force-reinstall --no-deps && python -c "import accim; print(accim.__version__)"`.

### T18 — Rutas de IDD multiplataforma + variable de entorno

**Contexto:** `accim/utils.py:560-590` hardcodea `C:/EnergyPlusVX-Y-0/Energy+.idd`.

**Cambio** — sustituir la escalera if/elif por:
```python
import os
import platform

def _ep_install_dirs(version: str):
    """Candidate EnergyPlus install dirs for a given 'X.Y' version, per platform."""
    vtag = version.replace('.', '-') + '-0'          # '9.6' -> '9-6-0'
    env = os.environ.get('ACCIM_ENERGYPLUS_DIR') or os.environ.get('ENERGYPLUS_DIR')
    if env:
        yield env
    system = platform.system()
    if system == 'Windows':
        yield rf'C:\EnergyPlusV{vtag}'
    elif system == 'Darwin':
        yield f'/Applications/EnergyPlus-{vtag}'
    else:
        yield f'/usr/local/EnergyPlus-{vtag}'

def get_idd_path_from_ep_version(energyplus_version: str) -> str:
    """Return the Energy+.idd path for the given EnergyPlus version.

    Honours ACCIM_ENERGYPLUS_DIR / ENERGYPLUS_DIR. Returns 'not-supported'
    if the version is not in accim.lists.SUPPORTED_EP_VERSIONS (kept as a
    sentinel for backwards compatibility).
    """
    from accim.lists import SUPPORTED_EP_VERSIONS
    v = energyplus_version.lower()
    if v not in SUPPORTED_EP_VERSIONS:
        return 'not-supported'
    for base in _ep_install_dirs(v):
        candidate = os.path.join(base, 'Energy+.idd')
        if os.path.isfile(candidate):
            return candidate
    # Fallback: previous behaviour (first candidate path, even if not present),
    # so existing callers that only compare against 'not-supported' keep working.
    return os.path.join(next(_ep_install_dirs(v)), 'Energy+.idd')
```
⚠️ **Compatibilidad con tests:** `tests/utils/test_utils_pure.py` parametriza rutas exactas (`C:/EnergyPlusV9-6-0/Energy+.idd`). El separador cambia a `\` con `os.path.join` en Windows → actualizar el test para comparar con `os.path.normpath`, y añadir casos: (a) env var definida y existente gana; (b) versión no soportada → `'not-supported'`.

**Mantener el sentinel `'not-supported'`** en esta fase (lo consumen `engine.py:120` y `run.py:93`). La migración a excepción tipada es T54.

### T19 — Documentar `ACCIM_ENERGYPLUS_DIR` y actualizar docs de instalación

En `docs/source/2_installation.md`: sección "EnergyPlus location" explicando el orden de resolución (env var → ruta por defecto del SO) y el soporte 25.2 si se adoptó en T15.

### T20 — CI mínima (GitHub Actions)

Crear `.github/workflows/ci.yml`:
```yaml
name: CI
on:
  push: { branches: [main, master, "refactor/**", "fix/**"] }
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install ruff
      - run: ruff check accim tests --exclude accim/parametric_and_optimisation --exclude accim/sample_files --exclude accim/misc

  tests:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.9", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python-version }}" }
      - run: pip install -e .[dev]
      - run: python -m pytest tests/ -q
             --ignore=tests/parametric_and_optimisation
             --ignore=tests/parametric_and_optimisation_full_workflow
```
**Notas / riesgos:**
- Los tests que necesitan EnergyPlus ya se auto-saltan (patrón `pytest.skip` si el IDD no existe) → la suite corre sin E+.
- ⚠️ **`pip install besos` puede fallar en CI** (paquete semiabandonado, pins antiguos). Si falla: (a) fijar `besos==<versión que uses localmente>` y `pip install --no-deps besos` + deps manuales, o (b) adelantar T40 (quitar besos del núcleo) antes de activar CI. Dejar el workflow en la rama aunque falle, con el job de besos marcado `continue-on-error: true`, para no bloquear.
- Job opcional futuro: instalar EnergyPlus en ubuntu (los releases publican `.sh` instalable silencioso) y correr los goldens completos; dejarlo como TODO comentado en el YAML.

### T21 — Política de Nominatim (rate-limit y User-Agent)

`accim/data/preprocessing.py`:
1. Sustituir `Nominatim(user_agent="abcd")` (línea 334) por:
   ```python
   from accim import __version__
   geolocator = Nominatim(user_agent=f"accim/{__version__} (https://github.com/dsanchez-garcia/accim)")
   ```
2. Envolver el reverse con rate-limit:
   ```python
   from geopy.extra.rate_limiter import RateLimiter
   reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1.1)
   location = reverse(f"{lat},{lon}")
   ```
3. Quitar el header falso `'User-Agent': 'Mozilla/5.0'` de `give_address_ssl`/`give_address_openssl`/`give_address` y usar el mismo UA identificable.
4. (Se fusiona con T33 cuando se unifiquen las tres clases `give_address*`.)

### T22 — Tabla de versiones-IDD y soporte 25.2

Si en T15 se decidió soportar `'25.2'`: ya queda cubierto por T18 (la ruta se deriva de la versión, no hay tabla que ampliar). Añadir test paramétrico en `tests/utils/test_utils_pure.py` para `'25.2'`. Si se decidió NO soportarla, verificar que no queda en ninguna lista.

### T23 — `run.removefiles()` seguro

`accim/run/run.py:145-157`:
```python
def removefiles(confirm: bool = False, dry_run: bool = False):
    """Delete simulation by-products in the CWD.

    Keeps .py/.idf/.epw/.csv/.eso, and additionally deletes Table.csv,
    Meter.csv and Zsz.csv. Refuses to act unless confirm=True.
    """
    extensions = ('.py', '.idf', '.epw', '.csv', '.eso')
    csvextensions = ('Table.csv', 'Meter.csv', 'Zsz.csv')
    deletelist = [f for f in os.listdir() if not f.endswith(extensions)]
    deletelist += [f for f in os.listdir() if f.endswith(csvextensions)]
    deletelist = [f for f in deletelist if os.path.isfile(f)]
    print(f"{'Would delete' if dry_run else 'Deleting'} {len(deletelist)} files:")
    print(*deletelist, sep='\n')
    if dry_run:
        return deletelist
    if not confirm:
        raise ValueError("removefiles() is destructive. Call with confirm=True "
                         "(or dry_run=True to preview).")
    for f in deletelist:
        os.remove(f)
    return deletelist
```
**Breaking change** deliberado (antes borraba sin preguntar): anotar en CHANGELOG y MIGRATION.

### T24 — `output_idfs` con estado engañoso (bug 2.9)

**Decisión requerida** (ver §Decisiones). Opción recomendada (B):
- `accim/sim/idf_generation.py`: sustituir `self.output_idf_dict.update({outputname: idf1})` por `self.output_idf_dict[outputname] = None` **y** mantener un nuevo dict `self.output_idf_params[outputname] = {'ComfStand': ComfStand_value, 'CAT': CAT_value, 'ComfMod': ComfMod_value, 'HVACmode': HVACmode_value, 'VentCtrl': ..., 'ASTtol': round(ASTtol_value, 2)}` (usar los valores en scope de cada rama; en la rama PMV, los que apliquen).
- `batch.py:697`: `self.output_idfs = z.output_idf_dict` → exponer también `self.output_idf_params`.
- Documentar en el docstring de `AddAccis` que `output_idfs` contiene rutas (claves) y que para inspeccionar un IDF hay que cargarlo del disco.
- Alternativa (A, si algún flujo tuyo depende de los objetos): recargar cada `savecopy` con eppy — coste alto en memoria/tiempo; descartada por defecto.
- **Simplificación**: esta tarea es mucho más fácil DESPUÉS de T30 (el dict se rellena en un solo sitio). Si se hace T30 primero, T24 se reduce a 5 líneas.

### T25 — Emparejamiento ventana-zona exacto en engine

**Bug 2.13-g:** `accim/sim/engine.py:471-475` usa subcadena (`tz.lower() in wname.lower()` → `ZONE1` casa con `ZONE10_Win`).

**Cambio:**
1. En `_scan_and_setup_zones`, al construir `windownamelist_orig` (ramas AFN y Scheduled, líneas 198-257), construir además:
   ```python
   self.zone_to_windows = {}    # zone name (lower, underscore form) -> [window names]
   ```
   - Rama AFN: cuando `i.split('_')[0].lower() == k.lower()` (línea 207), hacer `self.zone_to_windows.setdefault(k.lower().replace(':','_').replace(' ','_'), []).append(i.replace(':','_'))`.
   - Rama Scheduled: al crear `virtual_window_name`, registrar igual.
2. En el bloque ExisHVAC (líneas 470-475), sustituir:
   ```python
   # ANTES
   temp_win = []
   for tz in temp_zone:
       for wname in self.windownamelist:
           if tz.lower() in wname.lower():
               temp_win.append(wname)
   # DESPUÉS
   temp_win = []
   for tz in temp_zone:
       temp_win.extend(self.zone_to_windows.get(tz.lower(), []))
   ```
**Cambio de golden esperado:** solo si algún modelo de muestra tiene zonas cuyo nombre es prefijo de otra (improbable). Verificar diff igualmente.

### T26 — `remove_existing_output_variables` — nombre vs. comportamiento

`accim/sim/ems/programs.py:1335-1355` borra también `Output:Meter` y `Output:EnvironmentalImpactFactors`. Es probablemente intencional (limpieza previa) pero el nombre engaña. Acción mínima: documentarlo en el docstring ("also removes Output:Meter and Output:EnvironmentalImpactFactors"). Eliminar el `del` final con el backslash colgante (líneas 1354-1355). No cambiar comportamiento (goldens intactos).

### T27 — `modify_accis` y `ApplyCAT` según el estándar (bug 2.14 del informe, "a verificar")

**Verificación previa (30 min):** comparar qué escribe `generate_idfs` en `ApplyCAT.Program_Line_4/5` para `ComfStand in [1,4,5,22]` (NO las toca → conservan lo que pone `add_ems_programs`) frente a `modify_accis` (`single.py:706-709`, las sobrescribe SIEMPRE con `custom + cat offset`).
1. Leer el contenido por defecto de `ApplyCAT` en `accim/sim/ems/programs.py` (buscar `Name='ApplyCAT'`).
2. Si el default de las líneas 4/5 depende del CAT (lógica EMS), la sobrescritura incondicional de `modify_accis` **rompe** los estándares 1/4/5/22 → condicionar:
   ```python
   if comfort_standard == 99:
       ApplyCAT.Program_Line_4 = ...
       ApplyCAT.Program_Line_5 = ...
   ```
3. Si el default resulta equivalente, documentar y cerrar sin cambio.
**Añadir test golden de `modify_accis`** con `comfort_standard=1` y con `99` (comparar los programas EMS resultantes).

---

## FASE 3 — P2: Refactors dirigidos (T30–T35)

### T30 — Refactor de `idf_generation.py`: iterador único de combinaciones ⭐ (la tarea de mayor retorno)

**Problema:** la estructura de bucles de 6 niveles está duplicada (preview líneas 253-443, generación 459-838); las reglas de compatibilidad CS/CAT/CM están repetidas 6 veces; los bugs 2.4 (variables residuales), 2.13-f (inyección SetAST inconsistente) y parte de 2.9 viven ahí.

**Diseño objetivo** — nuevo módulo `accim/sim/combinations.py`:

```python
"""Parameter-combination generator for ACCIS output IDFs.

Single source of truth for (a) which combinations are valid and
(b) how each combination is named. Consumed twice by idf_generation:
once for the preview list, once for the actual generation.
"""
from dataclasses import dataclass
from typing import Iterator, List, Optional
import numpy

COMFORT_STANDARD_TAGS = {
    0: 'ESP CTE', 1: 'INT EN16798', 2: 'INT ASHRAE55', 3: 'JPN Rijal',
    4: 'CHN GBT50785 Cold', 5: 'CHN GBT50785 HotMild', 6: 'CHN Yang',
    7: 'IND IMAC C NV', 8: 'IND IMAC C MM', 9: 'IND IMAC R 7DRM',
    10: 'IND IMAC R 30DRM', 11: 'IND Dhaka', 12: 'ROU Udrea',
    13: 'AUS Williamson', 14: 'AUS DeDear', 15: 'BRA Rupp NV',
    16: 'BRA Rupp AC', 17: 'MEX Oropeza Arid', 18: 'MEX Oropeza DryTropic',
    19: 'MEX Oropeza Temperate', 20: 'MEX Oropeza HumTropic',
    21: 'CHL Perez-Fargallo', 22: 'INT ISO7730', 99: 'CUSTOM',
}

# Reglas de compatibilidad extraídas de la implementación actual
# (idf_generation.py líneas 305-379 — conservar EXACTAMENTE la semántica):
CAT_RULES = {
    'range_0_3': [1, 22],          # CAT in range(0, 4)
    'cat_1_2':   [4, 5],           # CAT in [1, 2]
    'range_80_90_10': [2, 3, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
    'range_80_90_5':  [7, 8],      # CAT in range(80, 91, 5)
}
FRACTIONAL_COMFMODS = [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5]

@dataclass(frozen=True)
class ParamCombo:
    comfort_standard: int
    category: Optional[float]      # None → '[CA_X'
    comfort_mode: Optional[float]  # None → '[CM_X'
    hvac_mode: int
    vent_control: Optional[int]
    vst_offset: Optional[float]
    min_ot_offset: Optional[float]
    max_wind_speed: Optional[float]
    ast_tol: Optional[float]
    is_pmv: bool = False

    def output_name(self, base_filename: str, suffix: str) -> str:
        def tag(prefix, value):
            return f'[{prefix}_' + ('X' if value is None else str(value))
        if self.is_pmv:
            return (base_filename + '[CS_PMV' + '[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X'
                    + suffix + '.idf')
        return (base_filename
                + '[CS_' + COMFORT_STANDARD_TAGS[self.comfort_standard]
                + tag('CA', self.category) + tag('CM', self.comfort_mode)
                + f'[HM_{self.hvac_mode}' + tag('VC', self.vent_control)
                + tag('VO', self.vst_offset) + tag('MT', self.min_ot_offset)
                + tag('MW', self.max_wind_speed)
                + '[AT_' + ('X' if self.ast_tol is None else str(round(self.ast_tol, 2)))
                + suffix + '.idf')

def _category_is_valid(cs: int, cat) -> bool: ...
def _comfmod_is_valid(cs: int, cm) -> bool: ...

def iter_combinations(*, temp_control, comfort_standards, categories, comfort_modes,
                      hvac_modes, vent_controls, vst_offsets, min_ot_offsets,
                      max_wind_speeds, ast_from, ast_to, ast_steps) -> Iterator[ParamCombo]:
    if temp_control.lower() == 'pmv':
        yield ParamCombo(comfort_standard=-1, category=None, comfort_mode=None,
                         hvac_mode=0, vent_control=None, vst_offset=None,
                         min_ot_offset=None, max_wind_speed=None, ast_tol=None, is_pmv=True)
        return
    for cs in comfort_standards:
        if cs == 0:
            # CS 0 no itera CAT/CM (usa CAT=1, CM=0 internamente pero se nombra con X)
            for combo in _iter_hvac_levels(cs, None, None, hvac_modes, vent_controls,
                                           vst_offsets, min_ot_offsets, max_wind_speeds,
                                           ast_from, ast_to, ast_steps):
                yield combo
            continue
        for cat in categories:
            if not _category_is_valid(cs, cat):
                continue
            for cm in comfort_modes:
                if not _comfmod_is_valid(cs, cm):
                    continue
                yield from _iter_hvac_levels(cs, cat, cm, hvac_modes, vent_controls,
                                             vst_offsets, min_ot_offsets, max_wind_speeds,
                                             ast_from, ast_to, ast_steps)

def _iter_hvac_levels(cs, cat, cm, hvac_modes, vent_controls, vst_offsets,
                      min_ot_offsets, max_wind_speeds, ast_from, ast_to, ast_steps):
    for hm in hvac_modes:
        if hm == 0:
            for at in numpy.arange(ast_from, ast_to, ast_steps):
                yield ParamCombo(cs, cat, cm, hm, None, None, None, None, float(at))
        else:
            for vc in vent_controls:
                if hm == 1 and vc in (2, 3):
                    continue
                for vo in vst_offsets:
                    for mt in min_ot_offsets:
                        for mw in max_wind_speeds:
                            for at in numpy.arange(ast_from, ast_to, ast_steps):
                                yield ParamCombo(cs, cat, cm, hm, vc, vo, mt, mw, float(at))
```

**Reglas a trasladar con exactitud** (verificar contra el original línea a línea al implementarlas):
- `_category_is_valid`: CS∈{1,22}→CAT∈range(0,4); CS∈{4,5}→CAT∈{1,2}; CS∈{2,3,6,9..21}→CAT∈{80,90}; CS∈{7,8}→CAT∈{80,85,90}. *(Ojo: `range(80,91,10)` = {80,90} — el 85 solo vale para IMAC.)*
- `_comfmod_is_valid`: CS∈{13,14}→CM∉{0,1} **y además** los fraccionales solo valen para {13,14} (`idf_generation.py:313` y `:376`); CS==22→CM==0; CS==21→CM∈{2,3}.

**Pasos de la migración:**
1. Escribir `combinations.py` + tests unitarios exhaustivos **antes de tocar** `idf_generation.py`:
   - `tests/sim/test_combinations.py`: para una matriz de entradas representativa, comparar `[c.output_name(f, s) for c in iter_combinations(...)]` contra la lista que genera el **código actual** (fase preview). Técnica: ejecutar temporalmente la preview actual capturando `outputlist` (extraerla a una función pura o copiarla al test como oráculo) → así el refactor queda demostrado como equivalente. Casos mínimos: CS=[1], CS=[0], CS=[2], CS=[7], CS=[13], CS=[21], CS=[22], CS=[99], mezclas, HM=[0,1,2], VC=[0,1,2,3], y PMV.
2. Reescribir `generate_idfs` para consumir el iterador dos veces:
   ```python
   combos = list(iter_combinations(...))
   outputlist = [c.output_name(file.replace('_pymod',''), suffix) for c in combos
                 for file in filelist_pymod]        # preview
   ...
   for file in filelist_pymod:
       idf1 = get_building(file + '.idf')
       programs = _find_accis_programs(idf1)        # helper: dict con SetInputData, ApplyCAT...
       for combo in combos:
           _apply_combo_to_programs(programs, combo, self)   # escribe las Program_Line_N
           _inject_setast_lines(programs['SetAST'], combo)   # UN único método de inyección
           outputname = combo.output_name(file.replace('_pymod',''), suffix)
           idf1.savecopy(outputname)
           self.output_idf_dict[outputname] = None
           self.output_idf_params[outputname] = combo        # T24 gratis
   ```
3. `_apply_combo_to_programs`: una única función con TODO lo que hoy está repetido en 6 ramas (SetInputData líneas 1-12, ApplyCAT 1-2 (+4-5 según T27), SetAppLimits 2-5, SetAST 1-3, SetVOFinputData cuando `hm==2 and vc in (2,3)`). Para la rama CS==0: `set CAT = 1`, `set ComfMod = 0` (como hoy, líneas 488-489). Para PMV: `set HVACmode = 0` y **sin** líneas dinámicas SetAST (esto CORRIGE el bug 2.4; ver T31).
4. `_inject_setast_lines(setast_program, combo)`: decidir **una** convención (recomendada: `while len(obj) > 18: pop()` seguido de `obj.append(...)`, que es la de la mayoría de ramas actuales) y usarla siempre. ⚠️ Antes de fijarla, comparar con un golden real qué produce cada una de las dos variantes actuales (`obj.append` vs `setattr Program_Line_17+`) — si producen IDFs distintos, la convención elegida debe ser la que coincida con los goldens de las ramas más usadas, y el cambio en las demás ramas se acepta como corrección (documentar en CHANGELOG).
5. Borrar el código muerto: bucles de preview antiguos, ramas duplicadas, comentarios `# time.sleep` / `# pbar`.
6. Correr goldens → diff → esperar: idénticos para configuraciones "temp" estándar; cambios solo en (a) PMV (antes crasheaba), (b) ramas cuya inyección SetAST difería.

**Criterio de aceptación:** `test_combinations.py` verde (equivalencia con el oráculo); goldens de batch/single idénticos salvo los cambios documentados; `idf_generation.py` < 300 líneas.

### T31 — Promocionar el xfail de PMV a golden

Depende de T30 (que corrige el `UnboundLocalError`).
1. `tests/sim/test_known_bugs.py::test_batch_pmv_currently_broken` pasará a XPASS (strict) → **fallará la suite**: es la señal.
2. Quitar el decorador `@pytest.mark.xfail` y mover el cuerpo a `tests/sim/test_characterization_batch.py` como nueva config `batch_vrf_mm_pmv_v960` siguiendo el patrón de las configs existentes (mirar `_golden.py` para el registro).
3. `pytest tests/sim --update-golden` para crear el golden inicial del PMV; revisar manualmente el IDF generado (el `[CS_PMV...idf`): debe contener `set HVACmode = 0` y NO líneas dinámicas SetAST heredadas de otra iteración.
4. Actualizar el comentario final de `test_known_bugs.py` (o borrar el fichero si queda vacío).

### T32 — Trocear `Table.__init__` (postprocessing)

**Contexto:** `accim/data/postprocessing/main.py:108-1440` (~1.330 líneas). Los comentarios `# Step:` existentes marcan las costuras naturales.

**Estrategia (refactor mecánico sin cambio de comportamiento):**
1. Identificar los bloques por los comentarios `# Step:` / `flowchart_state_in_paper = 'A.x'` (el propio código está anotado con los estados del flowchart del paper — usarlos como mapa).
2. Extraer en este orden (cada uno un commit, goldens tras cada paso):
   - `_validate_frequencies(source_frequency, frequency)` (líneas ~167-194)
   - `_parse_concatenated_filename(path)` (líneas ~198-213) → devuelve (source_frequency, frequency, frequency_agg_func, standard_outputs)
   - `_discover_source_files(datasets)` (líneas ~254-282; unificar con la copia de `utils.py::preview_Table_cols` — extraer AMBAS a una función módulo-nivel `_filter_simulation_csvs(files)`)
   - `_load_and_concat(source_files, ...)` 
   - `_clean_columns(df, ...)` (la lista `cleaned_columns` pasa a constante de módulo `_STANDARD_EMS_COLUMNS`)
   - `_aggregate(df, level, level_agg_func, ...)`
   - `_split_epw_names(df)` 
   - `_normalise_energy_units(df, ...)`
   - `_rename_columns(df, ...)`
3. `__init__` queda como orquestador de ~50 líneas que llama a los métodos en orden y asigna `self.df`.
4. Regla estricta: **ningún cambio de lógica** en esta tarea; cada extracción se valida con `pytest tests/data -q` (los tests de caracterización de Table congelan el df resultante).
5. Los ~15 `todo` del cuerpo se copian como issues/lista en `TODO.md` o issues de GitHub, y se borran del código solo si se transcriben.

**Criterio de aceptación:** goldens de `tests/data` idénticos sin regenerar; ningún método > 150 líneas.

### T33 — Refactor de `rename_epw_files` (plan / interactivo / aplicar)

**Contexto:** `accim/data/preprocessing.py:150-639`. Objetivo: mismo patrón que `prompts.py`.

**Diseño:**
```python
# accim/data/preprocessing.py  (nuevo esqueleto)

@dataclass
class EpwRenamePlan:
    old_name: str; abs_path: str
    country: str; city: str; scenario_year: str
    @property
    def new_name(self): return f"{self.country}_{self.city}_{self.scenario_year}"

def build_rename_plan(filelist=None, rename_city_dict=None, country_to_city_dict=None,
                      geocoder=None) -> list[EpwRenamePlan]:
    """Pura (sin input()). geocoder inyectable para tests (por defecto _NominatimGeocoder)."""

def apply_rename_plan(plans, delete_originals=False, exclude=()) -> None:
    """Copia/renombra según el plan; borra originales solo de los renombrados (T05)."""

class rename_epw_files:          # wrapper de compatibilidad, interactivo
    def __init__(self, filelist=None, rename_city_dict=None, country_to_city_dict=None,
                 confirm_renaming=None, confirm_deletion=None):
        plans = build_rename_plan(...)
        plans = _interactive_amendments(plans)      # todos los input() viven aquí
        apply_rename_plan(plans, ...)
```
Piezas:
1. `_NominatimGeocoder` — clase única que absorbe `give_address`, `give_address_ssl`, `give_address_openssl`: un método `reverse(lat, lon) -> dict` con la cadena de fallbacks SSL dentro (los 4 bloques duplicados de 40 líneas se convierten en un bucle sobre estrategias), rate-limit de T21, y caché en memoria `functools.lru_cache` por (lat, lon) redondeados.
2. Detección de escenario/año: extraer a funciones puras `detect_scenario(name) -> str|None`, `detect_year(name) -> str|None` con las tablas actuales — y tests unitarios directos (`RCP4.5`, `ssp585`, `Presente`, sin match).
3. Deprecar las tres clases `give_address*` con `DeprecationWarning` reexportando la nueva (`give_address = _NominatimGeocoder` con shim), o eliminarlas si aceptas breaking (anotar en MIGRATION).
4. Los tests existentes de `tests/data/test_preprocessing.py` deben seguir pasando; añadir tests puros para `build_rename_plan` con geocoder falso (sin red).

### T34 — Deduplicar `set_comfort_fields_people`

**Contexto:** `accim/sim/hvac/base.py:20-181`, 4 ramas de ~35 líneas casi idénticas.

**Cambio:**
```python
_PEOPLE_COMMON_FIELDS = [
    'Name', 'Number_of_People_Schedule_Name', 'Number_of_People_Calculation_Method',
    'Number_of_People', 'Fraction_Radiant', 'Sensible_Heat_Fraction',
    'Activity_Level_Schedule_Name', 'Carbon_Dioxide_Generation_Rate',
    'Enable_ASHRAE_55_Comfort_Warnings', 'Mean_Radiant_Temperature_Calculation_Type',
    'Surface_NameAngle_Factor_List_Name', 'Work_Efficiency_Schedule_Name',
    'Clothing_Insulation_Calculation_Method',
    'Clothing_Insulation_Calculation_Method_Schedule_Name',
    'Clothing_Insulation_Schedule_Name', 'Air_Velocity_Schedule_Name',
]

def set_comfort_fields_people(self, energyplus_version=None, temp_control=None, verbose=True):
    ppl = list(self.idf1.idfobjects['PEOPLE'])
    if not ppl:
        if verbose: print('WARNING: No PEOPLE objects found...')
        return
    for old in ppl:
        modern = 'Zone_or_ZoneList_or_Space_or_SpaceList_Name' in old.fieldnames
        fields = {f: old[f] for f in _PEOPLE_COMMON_FIELDS}
        if modern:
            fields['Zone_or_ZoneList_or_Space_or_SpaceList_Name'] = old.Zone_or_ZoneList_or_Space_or_SpaceList_Name
            fields['People_per_Floor_Area'] = old.People_per_Floor_Area
            fields['Floor_Area_per_Person'] = old.Floor_Area_per_Person
        else:
            fields['Zone_or_ZoneList_Name'] = old.Zone_or_ZoneList_Name
            fields['People_per_Zone_Floor_Area'] = old.People_per_Zone_Floor_Area
            fields['Zone_Floor_Area_per_Person'] = old.Zone_Floor_Area_per_Person
        fields['Thermal_Comfort_Model_1_Type'] = 'AdaptiveASH55'
        fields['Thermal_Comfort_Model_2_Type'] = 'AdaptiveCEN15251'
        fields['Thermal_Comfort_Model_3_Type'] = 'Fanger' if temp_control == 'pmv' else ''
        fields['Thermal_Comfort_Model_4_Type'] = ''
        fields['Thermal_Comfort_Model_5_Type'] = ''
        self.idf1.newidfobject('PEOPLE', **fields)
        self.idf1.removeidfobject(self.idf1.idfobjects['PEOPLE'][0])
    if verbose:
        print('The people objects in the model have been amended.')
```
Nota: `old[f]` con eppy usa `__getitem__` por nombre de campo — verificado que funciona con EpBunch. Goldens: idénticos (mismos campos, mismo orden de rotación).

### T35 — `gen_outputs_df` sin efectos secundarios documentados

`accim/sim/single.py:364-429` ejecuta `add_accis` completo (muta el IDF) solo para listar outputs. Mínimo: documentar la mutación en el docstring con un WARNING claro. Ideal: operar sobre una copia (`copy.deepcopy(idf)` es caro pero seguro; alternativamente `idf.savecopy(tmp)` + recarga). Decisión según uso real que le des.

---

## FASE 4 — P2b: Desacoplar besos (T40–T42)

### T40 — `accim/compat.py`: sustituir `get_building`/`IDF_class` de besos

**Contexto:** el núcleo usa de besos: `get_building` (engine, idf_generation, postprocessing/main, utils), `IDF_class` (anotaciones de tipo en apmv, single, utils), `read_eso`/`objectives` (solo el monkey-patch de apmv), `eplus_funcs.get_idf_version/run_building` (utils: `print_available_outputs_mod`).

**Pasos:**
1. Crear `accim/compat.py`:
   ```python
   """Thin compatibility layer so the accim core does not require besos."""
   from eppy.modeleditor import IDF

   def get_building(idf_path: str) -> IDF:
       """Load an IDF resolving the IDD from the file's own Version object.

       Mirrors besos.eppy_funcs.get_building for the accim use case.
       """
       import io, re, os
       from accim.utils import get_idd_path_from_ep_version
       with open(idf_path, encoding='utf-8', errors='ignore') as f:
           content = f.read()
       m = re.search(r'^\s*Version\s*,\s*([0-9]+\.[0-9]+)', content,
                     re.IGNORECASE | re.MULTILINE)
       if not m:
           raise ValueError(f'Could not detect EnergyPlus version in {idf_path}')
       version = m.group(1)
       idd = get_idd_path_from_ep_version(version)
       if idd == 'not-supported' or not os.path.isfile(idd):
           raise FileNotFoundError(f'No IDD found for EnergyPlus {version}')
       try:
           IDF.setiddname(idd)
       except Exception:   # IDDAlreadySetError si ya hay uno fijado
           pass
       return IDF(idf_path)
   ```
   ⚠️ Diferencia de comportamiento con besos: `IDF.setiddname` es global en eppy — si ya se fijó un IDD de otra versión, eppy lanza/ignora. besos gestiona esto con `modeleditor.IDF` fresco. Revisar el patrón real de besos (`besos/eppy_funcs.py::get_building`) al implementarlo y replicar la solución (usa `eppy_funcs.get_idf_version_pth` + `config`). Si el multi-IDD en un proceso resulta complejo, documentar la limitación (un proceso = una versión E+), que ya era de facto la situación.
2. Buscar y reemplazar (fuera de `parametric_and_optimisation`):
   ```bash
   grep -rln "from besos.eppy_funcs import get_building" accim --include="*.py"
   # engine.py, idf_generation.py, data/postprocessing/main.py, utils.py →
   # from accim.compat import get_building
   ```
3. Anotaciones `besos.IDF_class` → `eppy.modeleditor.IDF` (apmv.py:19,30; single.py:26,30,325,365; utils.py:24-25 y firmas).
4. `utils.py`: `print_available_outputs_mod` usa `run_building` de besos → moverla a un import perezoso dentro del método con mensaje `ImportError("This helper requires besos: pip install accim[optimisation]")`, o reimplementar con `eppy.runner`. Decisión: import perezoso (es una utilidad menor).
5. El monkey-patch `read_eso` de `apmv.py:42-72` ya está en try/except ImportError → se queda, pero solo se activa si besos está instalado. OK sin cambios.
6. `pyproject.toml`: mover `besos` de `dependencies` a `optional-dependencies.optimisation`.

**Verificación:** en un venv limpio SIN besos: `pip install -e .` + `python -c "from accim.sim import AddAccis, add_accis, apply_apmv_setpoints"` + `pytest tests/utils tests/sim -q` (los goldens con E+ presente deben pasar igual).

### T41 — Mover los monkey-patches del `__init__` raíz

**Contexto:** `accim/__init__.py:3-73` (shim `imp`, patch dask/EvaluatorEP, patch platypus/get_operator, patch `_freeze`).

**Pasos (coordinar con la actualización del módulo parametric desde la otra rama):**
1. Cortar TODO el bloque desde `import sys` (línea 3) hasta el final y pegarlo al principio de `accim/parametric_and_optimisation/__init__.py` (o mejor, en `accim/parametric_and_optimisation/_besos_patches.py` importado desde su `__init__`).
2. `accim/__init__.py` queda en 1 línea: `__version__ = "1.0.0"`.
3. El shim de `imp` (líneas 4-7): mantenerlo junto a los patches (lo necesita besos en py≥3.12), con un comentario de por qué; considerar `sys.modules.setdefault("imp", ...)`.
4. **Riesgo:** si algún flujo tuyo importa `accim` y LUEGO usa besos directamente contando con los patches — tras el cambio, los patches solo se aplican al importar `accim.parametric_and_optimisation`. Documentar en MIGRATION.
5. ⚠️ Ejecutar DESPUÉS o EN COORDINACIÓN con el merge de la rama del módulo parametric para evitar conflictos.

### T42 — Import perezoso del stack geo

`preprocessing.py` importa `geopy` a nivel de módulo (línea 20-21) → mover dentro de las funciones que lo usan, con mensaje de error accionable si falta (`pip install accim[geo]`). Igual con `datapackage` si sobrevivió a la auditoría de T17.2 (si es import muerto, eliminar).

---

## FASE 5 — P3: Calidad continua (T50–T57)

### T50 — Logging en lugar de print

**Estrategia incremental (no big-bang):**
1. Crear `accim/_logging.py`:
   ```python
   import logging
   logger = logging.getLogger('accim')

   def set_verbose(verbose: bool):
       """Map the historical verbose flag onto logging levels."""
       handler_exists = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
       if not handler_exists:
           h = logging.StreamHandler()
           h.setFormatter(logging.Formatter('%(message)s'))
           logger.addHandler(h)
       logger.setLevel(logging.INFO if verbose else logging.WARNING)
   ```
2. Migrar módulo a módulo (orden: engine → programs → vrf → base → batch/single → data), patrón mecánico:
   - `if verbose: print(x)` → `logger.info(x)`
   - `print(x)` incondicional informativo → `logger.info(x)`
   - avisos → `logger.warning(x)` (los `warnings.warn` de apmv/resolver se quedan como están: son API).
   - Los `print` de `prompts.py` NO se migran (son UI interactiva).
3. Los entry points (`AddAccis.__init__`, `add_accis`, `apply_apmv_setpoints`) llaman `set_verbose(verbose)` al principio.
4. Goldens: no comparan stdout → sin riesgo. Los tests que capturan output (si alguno usa `capsys`) → revisar y adaptar con `caplog`.

### T51 — ruff + formateo

1. Añadir a `pyproject.toml`:
   ```toml
   [tool.ruff]
   line-length = 120
   exclude = ["accim/parametric_and_optimisation", "accim/sample_files", "accim/misc",
              "docs", "ondrive_backup", "jupyter notebooks"]

   [tool.ruff.lint]
   select = ["E4", "E7", "E9", "F", "B", "UP", "C4"]
   ignore = ["E741"]
   ```
2. `ruff check accim tests` → arreglar primero F821 (nombres sin definir), F841 (variables muertas), B006 (mutable defaults: quedan `idf_generation.py:45-47` — cambiarlos a `None` + normalización interna como ya hace batch), E711/E712 (`== True` → `is True` o directo).
3. NO activar el formateador (`ruff format`) hasta después de T30/T32 para no ensuciar diffs de refactor.
4. Añadir el job lint al CI (ya previsto en T20).

### T52 — Excepciones propias

1. Crear `accim/exceptions.py`:
   ```python
   class AccimError(Exception): ...
   class UnsupportedEnergyPlusVersionError(AccimError, ValueError): ...
   class ZoneResolutionError(AccimError): ...
   class InvalidArgumentError(AccimError, ValueError): ...
   ```
2. Sustituir gradualmente (compatible: heredan de ValueError donde antes se lanzaba ValueError): validaciones de batch/single/engine (`InvalidArgumentError`), `'not-supported'` → `UnsupportedEnergyPlusVersionError` en los llamadores nuevos (T54), `accimNotWorking` → considerar lanzar `ZoneResolutionError` con la lista de objetos no resueltos en vez del flag booleano (breaking → solo con deprecación).

### T53 — Type hints y `any` builtin

- Barrido de `: any` (builtin, anotación incorrecta) → `typing.Any` o el tipo real: `batch.py` (8 usos), `single.py`, `idf_generation.py`, `morphing.py:19`.
- `mypy accim/sim/hvac/resolver.py accim/sim/apmv.py accim/compat.py --ignore-missing-imports` como objetivo inicial acotado; ampliar módulo a módulo.

### T54 — Retirar el sentinel `'not-supported'`

Tras T18/T52: `get_idd_path_from_ep_version` lanza `UnsupportedEnergyPlusVersionError`; adaptar `engine.py:120-122` (el raise actual se simplifica) y `run.py:93-97` (el bucle `while` captura la excepción). Mantener durante una versión un wrapper deprecado si hay usuarios externos del helper.

### T55 — Renombres PEP 8 pendientes con deprecación

- `rename_epw_files` → `RenameEpwFiles` (o función `rename_epw_files()` de verdad tras T33), `print_available_outputs_mod` → `PrintAvailableOutputs`, `give_address*` → absorbidas por T33.
- Patrón de alias:
  ```python
  class RenameEpwFiles: ...
  def __getattr__(name):        # module-level __getattr__ (PEP 562)
      if name == 'rename_epw_files':
          warnings.warn('rename_epw_files is deprecated, use RenameEpwFiles',
                        DeprecationWarning, stacklevel=2)
          return RenameEpwFiles
      raise AttributeError(name)
  ```
- Actualizar MIGRATION.md.

### T56 — `modify_param`: implementar o eliminar (cierre de T14p)

Si se decide implementar:
```python
_PARAM_TO_PROGRAM_LINE = {
    'comfstand':   ('SetInputData', 'Program_Line_1', 'set ComfStand = {v}'),
    'cat':         ('SetInputData', 'Program_Line_2', 'set CAT = {v}'),
    'comfmod':     ('SetInputData', 'Program_Line_3', 'set ComfMod = {v}'),
    'hvacmode':    ('SetInputData', 'Program_Line_4', 'set HVACmode = {v}'),
    'ventctrl':    ('SetInputData', 'Program_Line_5', 'set VentCtrl = {v}'),
    'vstoffset':   ('SetInputData', 'Program_Line_6', 'set VSToffset = {v}'),
    'minotoffset': ('SetInputData', 'Program_Line_7', 'set MinOToffset = {v}'),
    'maxwindspeed':('SetInputData', 'Program_Line_8', 'set MaxWindSpeed = {v}'),
    'coolseasonstart': ('SetInputData', 'Program_Line_11', 'set CoolSeasonStart = {v}'),
    'coolseasonend':   ('SetInputData', 'Program_Line_12', 'set CoolSeasonEnd = {v}'),
    'setpointacc': ('SetAST', 'Program_Line_1', 'set SetpointAcc = {v}'),
    'maxtempdiffvof': ('SetVOFinputData', 'Program_Line_1', 'set MaxTempDiffVOF = {v}'),
    'mintempdiffvof': ('SetVOFinputData', 'Program_Line_2', 'set MinTempDiffVOF = {v}'),
    'multipliervof':  ('SetVOFinputData', 'Program_Line_3', 'set MultiplierVOF = {v}'),
    # 'asttol' es especial: escribe DOS líneas (9 con -v, 10 con +v)
}
```
Caso especial `asttol`: setear `Program_Line_9 = f'set ACSTtol = {-value}'` y `Program_Line_10 = f'set AHSTtol = {value}'`. Test unitario por parámetro + roundtrip con `get_accim_args`.

### T57 — Backlog de TODOs del código

Transcribir a issues (o a un `TODO.md`) y borrar del código los ya cubiertos por este plan:
- `batch.py:300` — validar AHST < ACST cuando se usan offsets de CAT (añadir la validación en `__init__` de AddAccis: `if category_heat_offset > category_cool_offset: warn`... definir la regla exacta contigo).
- `engine.py:321` — zonas single/dual mezcladas en `zonenames_orig`.
- `engine.py:338` — sensores duplicados si conviven dos tipos de coil del mismo grupo (relacionado con T25).
- `programs.py:775/923` — falta sensor COOLCOIL si no hay cooling coil.
- `programs.py:1952` — key de People con SpaceList (verificar si el flujo apmv ya lo cubre y el de accis no).
- Los ~20 `todo` de `data/postprocessing/main.py` (tras T32 será más fácil atacarlos).

---

## Decisiones que debes tomar tú (marcar antes de ejecutar)

| # | Tarea | Decisión | Opciones (recomendada en negrita) |
|---|-------|----------|-----------------------------------|
| D1 | T15/T22 | ¿Soportar EnergyPlus 25.2? | **Sí** (trivial tras T18) / No (borrar '25.2' de single.py) |
| D2 | T8 | ¿Borrar `_pymod` también con `confirm_generation=False`? | **Sí (comportamiento actual)** / No |
| D3 | T14p/T56 | `modify_param` | **Implementar (T56)** / Retirar del API |
| D4 | T16.4 | `sample_CSVs` (17 MB) dentro del wheel | **Mantener si wheel < 30 MB** / Mover a Release + descarga |
| D5 | T24 | `output_idfs` | **Claves + params (opción B)** / Recargar IDFs (opción A) |
| D6 | T27 | ApplyCAT en `modify_accis` para CS 1/4/5/22 | Pendiente de la verificación previa descrita |
| D7 | T33/T55 | ¿Aceptas breaking en `give_address*`? | **Deprecar 1 versión** / Eliminar directo |
| D8 | T35 | `gen_outputs_df` ¿copia o documentar mutación? | **Documentar** (barato) / Copiar |
| D9 | T41 | Momento de mover los monkey-patches | **Junto al merge de la rama parametric** |

---

## Checklist final pre-release 1.0 (tras completar P0+P1)

- [ ] `grep -rn "EnergyPlus_version" accim tests --include="*.py"` → 0 resultados (fuera de parametric).
- [ ] Suite completa verde: 0 xfail inesperados, goldens regenerados solo con diffs documentados.
- [ ] `python -m build` → wheel < 50 MB, sin checkpoints/pycache dentro.
- [ ] Instalación limpia en venv nuevo: `pip install dist/*.whl` + smoke test `from accim.sim import AddAccis`.
- [ ] CHANGELOG actualizado: sección con TODOS los bugs corregidos (T01-T15) y los breaking changes (T23 removefiles, T41 patches).
- [ ] MIGRATION.md actualizado si hubo renombres/deprecaciones.
- [ ] CI verde en GitHub (lint + tests en ubuntu/windows).
- [ ] Tag + release + `twine upload` (o el .bat actualizado).

---

*Plan generado el 19/07/2026 a partir del informe de revisión de la misma fecha. Ante cualquier discrepancia entre este plan y el código real (líneas desplazadas, código ya cambiado), prevalece el código: localizar los fragmentos citados por contenido y adaptar.*
