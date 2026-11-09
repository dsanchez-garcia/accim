# Cómo ha cambiado el código de accim en la versión 1.2.0

Guía de los cambios del código de la rama `v1.2.0` respecto a accim 1.1.0, para quien mantiene accim; no es
documentación de uso. Recoge las propuestas del bloque A de `notes/PROPUESTAS_MEJORAS_post_1.1.0_v01.md` y `_v02.md`
(índices de confort derivados del PMV; archivos del autor, fuera de git) que el autor pidió para esta versión: las P1,
A2 y A1, en este orden; A5 queda pendiente.

Lo que ya está en otros documentos no se repite aquí:

- `CHANGELOG.md` (sección Unreleased): los cambios que ve el usuario.
- `docs/source/4_detailed use.md`, secciones 4.8 y 4.8.1: el uso.
- `DEVLOG.md`: el registro del trabajo, con cómo se comprobó.
- `notes/decisions.md`: las decisiones y sus motivos.

## 1. En resumen

- **A2.** Las consignas basadas en el PMV comparten un motor, `accim.sim.pmv_index`: `apply_apmv_setpoints` llama a
  `apply_pmv_index_setpoints(index='apmv')`, y la nueva `apply_pmv_setpoints`, a `apply_pmv_index_setpoints(index='pmv')`.
  Los IDF del aPMV no cambian (sección 2).
- **A1.** El ePMV de Fanger y Toftum (2002) es el tercer índice del motor (`'epmv'`), con `apply_epmv_setpoints`, su
  corrección del metabolismo opcional, el tipo de parámetros `'epmv setpoints'` del paramétrico y la pestaña de la GUI
  para los tres índices (sección 3). El cuaderno How-to está escrito, pero sin ejecutar (`TODO.md`).
- **A5** (vestimenta dinámica) queda pendiente, a petición del autor (`TODO.md`).

## 2. El motor común de los índices derivados del PMV (A2)

**Antes.** `accim/sim/apmv.py` tenía `apply_apmv_setpoints` y sus funciones auxiliares (`_ensure_infrastructure`,
`_add_apmv_sensors`, `_add_apmv_programs`, `_add_apmv_outputs`...), con el aPMV en las líneas Erl de
`_add_apmv_programs` y en los nombres de las variables, los programas y las salidas.

**Ahora.** Esas funciones están en `accim/sim/pmv_index.py`, con el mismo código salvo los nombres (`_add_sensors`,
`_add_programs`...) y el argumento `pmv_index` de las que escriben lo que depende del índice. Cada índice es un
`PmvIndex` del registro `PMV_INDICES`:

| Campo de `PmvIndex` | aPMV | PMV |
|---|---|---|
| `name` (en los nombres EMS) | `aPMV` | `PMV` |
| `parameters` (líneas de `set_zone_input_data_<zona>`) | `adaptive_coefficient_cooling` y `_heating` (variables `adap_coeff_cooling`, `adap_coeff_heating`) | ninguno |
| `coefficient` (el coeficiente de la estación) | `adap_coeff` | ninguno |
| `inverse` (la consigna PMV del termostato) | `sp/(1-adap_coeff*sp)` | `sp` |
| `monitor` (el índice de la zona) | `aPMV = PMV/(1+adap_coeff*PMV)` | ninguno: el índice es el sensor `PMV_<zona>` |

El esqueleto de los programas es el mismo para todos los índices: `set_zone_input_data_<zona>`, `apply_<name>_<zona>`,
`average_PMV_<zona>` (zonas con varias instancias de ocupantes), `monitor_<name>_<zona>` y
`count_<name>_comfort_hours_<zona>`. El Erl de un índice nuevo se reduce al coeficiente de cada estación, la inversa y
el monitor.

- `apply_apmv_setpoints` conserva la firma, los valores por defecto, los nombres de 0.x (`_accepts_legacy_arguments`)
  y la salida: los IDF de `s07` y `s08` del golden master son idénticos.
- `generate_df_from_args` llama a `arguments_table`, la versión genérica, con las mismas columnas y avisos.
- `_resolve_targets` está en `pmv_index`; `apmv` lo importa, y `apmv_setpoints` (el módulo de 0.x) lo sigue
  exportando.
- `_check_other_indices` impide aplicar dos índices a un modelo, porque actuarían sobre las mismas schedules
  (`PMV_H_SP_<zona>` y `PMV_C_SP_<zona>`). Aplicar el mismo índice dos veces sigue dando avisos y no cambia nada, como
  antes.
- Los modificadores del paramétrico (`funcs_for_besos/param_apmv.py`) buscan las líneas de
  `set_zone_input_data_<zona>` por el nombre de su variable (`_set_input_line`), porque su posición depende del índice:
  antes escribían las líneas 1 a 4, que en un modelo con consignas PMV son otras. `_get_apmv_program_targets` ya no se
  usaba y se ha quitado. `change_adaptive_coeff` (de `apmv`) sigue escribiendo las líneas 1 y 2: solo vale para el
  aPMV, como su nombre dice.

**Lo que se vio al probarlo.**

- El índice de cada zona y las horas dentro de las consignas se calculan en `BeginTimestepBeforePredictor`, con el PMV
  del paso de tiempo anterior: el sensor todavía no tiene el del paso en curso. Ya era así en 1.1.0; ahora lo dice la
  sección 4.8 y lo comprueba `test_pmv_index.py`.
- Con los termostatos de confort térmico (Fanger), los dos backends dan las mismas consignas y variables EMS, pero los
  resultados de EnergyPlus difieren por redondeo: 2.9e-10 °C en la temperatura de las zonas y 7e-4 J en la energía en
  tres días. Ya pasaba en 1.1.0 con el aPMV (comprobado con un worktree de `master`: la misma diferencia máxima que en
  la rama); con los modelos de `AddAccis`, los CSV son idénticos. No se ha buscado la causa dentro de EnergyPlus. La
  sección 4.9 lo dice.

## 3. El ePMV (A1)

**El índice.** `PMV_INDICES['epmv']` en `pmv_index.py`, con el mismo esqueleto que los otros índices:

| Campo de `PmvIndex` | ePMV |
|---|---|
| `name` | `ePMV` |
| `parameters` | `expectancy_factor` (variable `expectancy_factor_<zona>`; 0.8 por defecto, también para las zonas que faltan) |
| `coefficient` | `e`: `expectancy_factor_<zona>` en la estación de refrigeración y 1 en la de calefacción |
| `inverse` | `sp/e` para la consigna de refrigeración; la de calefacción, sin cambios salvo con `apply_to_heating` |
| `monitor` | `ePMV = e*PMV` si `PMV > 0`, y `PMV` si no; con `apply_to_heating`, siempre `e*PMV` |
| `options` | `apply_to_heating` y `metabolic_correction` (`False`) |
| `validate` | `0.5 <= e <= 1` en cada valor y en `default_expectancy_factor`; las opciones, booleanas; aviso con `apply_to_heating` |
| `add_objects` | la corrección del metabolismo (abajo) |

El monitor y la inversa son coherentes: el índice que se mide es el que controla el termostato. Si el monitor
multiplicara también los PMV negativos sin que `e` dividiera la consigna de calefacción, el contador de horas tomaría
como confortable un PMV de -0.71 con `e = 0.7` mientras el termostato mantiene -0.5. Así lo decidió el autor (la e solo
en la estación de refrigeración y en la consigna de refrigeración, como Fanger y Toftum, Tabla 3: "solo se ve afectado
el límite superior").

**`add_objects`, el campo nuevo de `PmvIndex`.** Una función que añade los objetos EMS propios del índice y devuelve
sus programas; el motor la llama después de `_add_programs`, de modo que sus programas van al final (tras los de todas
las zonas, con el PMV de cada una ya calculado, también el medio de las zonas con varias instancias) y reciben gestor de
llamadas, y antes de `_add_outputs`, que añade las `Output:Variable` de todas las salidas EMS.

**La corrección del metabolismo** (`_add_metabolic_correction`), por objeto `People` (o `People:Instance`):

- La schedule de actividad del `People` pasa a ser una copia de la suya (`ePMV_Activity_<people>`, del mismo tipo:
  `Schedule:Compact`, `:Constant`, `:Year` o `:File`), que actúa el EMS; un sensor (`Activity_base_<people>`, `Schedule
  Value`) lee la original, que queda como actividad sin corregir. Hace falta una schedule propia por `People` porque la
  original puede ser compartida, y una copia porque EnergyPlus calcula las ganancias del primer paso de cada entorno
  antes de que actúe el EMS: con la copia, ese paso tiene la actividad sin corregir, no un valor arbitrario.
- El programa `correct_activity_<people>`: en la estación de refrigeración, el PMV de su zona (o, si el `People` es de
  varias zonas, el PMV medio de sus ocupantes, ponderado por su número; la media simple si no hay ocupantes), acotado
  entre 0 y 3; en la de calefacción, 0. `metabolic_factor = 1-0.067*PMV`, y la actividad es la base por el factor.
- Salidas `Metabolic Correction Factor_<people>` y `Corrected Activity Level_<people>`; esta informa del actuador, lo que
  EnergyPlus admite y el backend de la API ya resolvía (declara una variable global para los actuadores que se
  informan).
- `set_pmv_input_parameters(activity_level=...)` para un `People` con la corrección lanza `ValueError` antes de cambiar
  nada: la schedule nueva quitaría la corrección. Se comprueba solo para los `People` que recibirían un valor.

**Lo que se vio al probarlo** (EnergyPlus 25.1, tres días de julio y el año del modelo residencial):

- Los sensores leen al principio de cada paso el PMV del paso anterior y los ocupantes del paso actual (EnergyPlus
  actualiza el número de ocupantes con las ganancias internas, antes de `BeginTimestepBeforePredictor`).
- Las ganancias de los ocupantes (`People Total Heating Rate`) son exactamente ocupantes × actividad corregida del paso
  anterior: EnergyPlus calcula las ganancias internas antes de ese punto de llamada. El termostato (en el predictor) y el
  PMV del final del paso sí usan la actividad del paso. Se consideró hacerlo en
  `BeginZoneTimestepBeforeInitHeatBalance` (antes de las ganancias), sin probarlo: la estación y el PMV medio de las
  zonas con varias instancias llegarían con un paso de retraso; se dejó en el mismo punto que el resto, documentado.
- Las acciones sobre `Schedule:Year` funcionan (modelo residencial) y los dos backends dan lo mismo: idéntico en el
  modelo residencial; en el de dos zonas con VRF, las variables EMS y las schedules idénticas y el resto con diferencias
  de redondeo, como con el aPMV (sección 2).
- La aproximación respecto a Fanger y Toftum, con el PMV de ISO 7730 (script aparte, no en el repositorio): con 1,2 met
  y 0,5 clo, para un PMV de 1 sin corregir, ellos reducen la actividad un 6,7 % y la corrección converge a un 6,1 %
  (PMV 0,914 frente a 0,906); con 1 met, 5,5 % (PMV 0,824 frente a 0,783).

**El paramétrico.** `params_dicts.epmv_setpoints_params` (`expectancy_factor` y los tres de las consignas) y el tipo de
parámetros `'epmv setpoints'` en `SimulationBase`, que aplica `apply_epmv_setpoints` como `'apmv setpoints'` aplica
`apply_apmv_setpoints`; `get_available_parameters` usa `getattr(self, 'is_epmv_setpoints', False)` para los objetos
guardados con versiones anteriores. `change_expectancy_factor_all_zones` comprueba el rango (0,5 a 1).

**La GUI.** La pestaña 2 se llama *PMV-based setpoints*: un desplegable con el índice (`forms.PMV_INDEX_FUNCTIONS`), y
`update_state` desactiva los campos de los otros índices (`forms.PMV_INDEX_PARAMETERS`), también en la tabla de zonas
(`_ZoneTable.set_state(disabled=...)`, que ya existía para el modo mixto). `forms.apmv_arguments` devuelve `index` y
solo los argumentos del índice (`index_setpoint_fields`); una fila de zona con un parámetro de otro índice es un
`FormError`. Las sesiones de 1.1.0 no tienen `index`: se toma `'apmv'`. La tarea pone las entradas del PMV antes que las
consignas. Un test comprueba que los diccionarios de `forms` coinciden con `PMV_INDICES` y las firmas de las funciones.

**El cuaderno.** `accim/sample_files/jupyter_notebooks/example_epmv_setpoints/using_epmv_setpoints.ipynb`, con copias
del modelo y el EPW del cuaderno del aPMV (1,7 MB más en `accim-samples`), registrado en
`docs/prepare_howto_notebooks.py`. Sigue el estilo del del aPMV (besos para leer y simular) y no se ha ejecutado, a
petición del autor; su página y sus enlaces quedan en `TODO.md`. `export` sin una copia ejecutada solo informa ("no
executed copy").

## 4. Pruebas

- `tests/core/test_pmv_index.py` (A2): el registro y los parámetros de los índices; `apply_apmv_setpoints` escribe el
  mismo modelo que el motor; los objetos EMS de las consignas PMV; las consignas PMV son las del aPMV con coeficientes 0
  (los programas ejecutados con el intérprete Erl de accim, en las dos estaciones, con y sin ocupantes); dos índices en
  un modelo; los modificadores del paramétrico; y tres días de julio con los dos backends de EnergyPlus 25.1.
- `tests/core/test_epmv.py` (A1, 17 pruebas): la comprobación de los argumentos y el aviso de `apply_to_heating`; los
  objetos EMS; las consignas, el ePMV y las horas con el intérprete Erl (las dos estaciones, `apply_to_heating`, sin
  ocupantes); con `e = 1`, las consignas del PMV; la corrección del metabolismo (los objetos, los valores con el
  intérprete, aplicarla dos veces) y la de un `People` de dos zonas (el modelo residencial, `Schedule:Year`);
  `set_pmv_input_parameters` antes y después; el modificador del paramétrico del factor de expectativa; y tres días de
  julio con los dos backends: ePMV = 0,7 × PMV del paso anterior, el factor, la consigna de 0,4/0,7 y las ganancias con
  la actividad del paso anterior.
- `tests/parametric_and_optimisation/test_epmv_parameters.py`: el tipo de parámetros `'epmv setpoints'`;
  `test_legacy_names.py` deja fuera los parámetros posteriores a 1.0.0, que no tienen nombre de 0.x.
- `tests/core/test_gui.py`: los argumentos del ePMV y del PMV, los errores, la coherencia con `PMV_INDICES`, la tarea
  (también con el modelo de ejemplo y la corrección) y los campos que la pestaña activa con cada índice.
- El golden master (`s07` y `s08`) comprueba que los IDF del aPMV no cambian.
