# Cómo ha cambiado el código de accim en la versión 1.2.0

Guía de los cambios del código de la rama `v1.2.0` respecto a accim 1.1.0, para quien mantiene accim; no es
documentación de uso. Recoge las propuestas del bloque A de `notes/PROPUESTAS_MEJORAS_post_1.1.0_v01.md` y `_v02.md`
(índices de confort derivados del PMV; archivos del autor, en git desde el commit `e238dad`) que el autor pidió para
esta versión: las P1, A2, A1 y A5, en este orden; y después D2 (sección 7), que el autor incluyó en la 1.2.0 el
2026-11-09 con E2 y E1.

Lo que ya está en otros documentos no se repite aquí:

- `CHANGELOG.md` (sección Unreleased): los cambios que ve el usuario.
- `docs/source/4_detailed use.md`, secciones 4.7.3, 4.8 y 4.8.1: el uso.
- `DEVLOG.md`: el registro del trabajo, con cómo se comprobó.
- `notes/decisions.md`: las decisiones y sus motivos.

## 1. En resumen

- **A2.** Las consignas basadas en el PMV comparten un motor, `accim.sim.pmv_index`: `apply_apmv_setpoints` llama a
  `apply_pmv_index_setpoints(index='apmv')`, y la nueva `apply_pmv_setpoints`, a `apply_pmv_index_setpoints(index='pmv')`.
  Los IDF del aPMV no cambian (sección 2).
- **A1.** El ePMV de Fanger y Toftum (2002) es el tercer índice del motor (`'epmv'`), con `apply_epmv_setpoints`, su
  corrección del metabolismo opcional, el tipo de parámetros `'epmv setpoints'` del paramétrico y la pestaña de la GUI
  para los tres índices (sección 3). El cuaderno How-to está ejecutado, y su página, en las How-to Guides.
- **A5.** `set_pmv_input_parameters` admite la actividad y la vestimenta por estación (una `Schedule:Compact` alineada
  con la estación de refrigeración de las consignas) y el modelo dinámico de vestimenta de ASHRAE 55
  (`'dynamic_ashrae55'`), y cada llamada escribe de nuevo sus schedules; `accim.sim.people.set_clothing_method` pone
  cualquiera de los tres métodos de la vestimenta de EnergyPlus (sección 4).
- **D2.** `Table` lee los CSV de los IDF con consignas basadas en el PMV (`<IDF>[<EPW>.csv`), promedia en el tiempo sus
  salidas (menos las horas), no toma la actividad corregida por una energía y da a las salidas de las zonas el nombre
  de su zona, con valores de bloque y de edificio, que las figuras distinguen (sección 7).
- Las categorías del PMV y la aproximación de la corrección del metabolismo se han comprobado en ISO 7730:2025 y
  EN 16798-1:2019, y el modelo dinámico de vestimenta de A5, en Schiavon y Lee (2013) y ASHRAE 55-2020 (sección 6).
- Lo que quedaba abierto se ha comprobado: el golden master y las pruebas de EnergyPlus 26.1 y 26.2, también la de A5
  con `People:Instance` (sección 5); la corrección del metabolismo en `BeginZoneTimestepBeforeInitHeatBalance`
  (sección 3); y dónde empiezan a diferir los dos backends con los termostatos de confort (sección 2).

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
  la rama); con los modelos de `AddAccis`, los CSV son idénticos. La sección 4.9 lo dice. Después (2026-11-09) se
  localizó dónde empieza, con las consignas PMV en el modelo de dos zonas y las salidas de los días de calentamiento
  (`Output:Diagnostics` con `ReportDuringWarmup`): el dimensionado es idéntico (el `.eio` solo difiere en la
  convergencia del calentamiento), y la primera diferencia aparece el primer día de calentamiento del periodo (1 de
  julio, de 7:20 a 7:30) en las temperaturas del aire de las dos zonas (en el decimocuarto decimal) y en la potencia de
  refrigeración de la zona 1 (en el undécimo), mientras que en ese paso son idénticas las consignas PMV y las variables
  EMS, las consignas de temperatura que calcula el termostato de confort, la temperatura radiante media, la humedad y
  el PMV. Nace, pues, en la simulación de la climatización o del balance del aire de las zonas, no en el EMS, el PMV ni
  el termostato; más dentro de EnergyPlus no se ha buscado.

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
  `BeginZoneTimestepBeforeInitHeatBalance`, antes de las ganancias, y se dejó en el mismo punto que el resto, porque la
  estación y el PMV medio de las zonas con varias instancias llegarían con un paso de retraso. Se probó después
  (2026-11-09), cambiando el punto de llamada de los programas `correct_activity_<people>` (fuera del repositorio): las
  ganancias son entonces exactamente ocupantes × actividad corregida del mismo paso, con el mismo PMV (el del paso
  anterior), y el backend de la API admite ese punto (con diferencias de redondeo como las de la sección 2); pero la
  estación llega con un paso de retraso: el primer paso del 1 de octubre aún tiene la corrección (factor 0,9586) con
  e = 1. Las zonas de varias instancias no se probaron. En un año del modelo residencial del cuaderno, la diferencia es
  despreciable: 9149,74 frente a 9149,70 kWh de climatización, el mismo PMV medio (0,539) y la misma temperatura
  operativa media (26,15 °C). Se mantiene `BeginTimestepBeforePredictor`.
- Las acciones sobre `Schedule:Year` funcionan (modelo residencial) y los dos backends dan lo mismo: idéntico en el
  modelo residencial; en el de dos zonas con VRF, las variables EMS y las schedules idénticas y el resto con diferencias
  de redondeo, como con el aPMV (sección 2).
- La aproximación respecto a Fanger y Toftum, con el PMV del programa normativo de ISO 7730:2025 (anexo D, escrito en
  Python fuera del repositorio; sección 6), la temperatura del aire igual a la radiante media, 0,1 m/s y 50 % de
  humedad relativa: con 1,2 met y 0,5 clo, para un PMV de 1 sin corregir, ellos reducen la actividad un 6,7 % (PMV
  0,905) y la corrección converge a un 6,1 % (PMV 0,914); con 1 met, 5,5 % (PMV 0,823 frente a 0,782). Entre 0,1 y
  0,3 m/s y entre 40 y 70 % de humedad, las reducciones son las mismas y los PMV cambian en ±0,01; los valores que se
  calcularon antes con otro script (0,914 frente a 0,906, y 0,824 frente a 0,783) están entre los de 40 y 50 %.

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
`docs/prepare_howto_notebooks.py`. Sigue el estilo del del aPMV (besos para leer y simular). Se escribió sin ejecutarlo,
a petición del autor; después se ejecutó (unos 45 s con EnergyPlus 25.1: tres simulaciones anuales) y se exportó: su
página está en el `toctree` de las How-to Guides, en la tabla de `2_installation.md` y en la de `docs/README.md`
§7.1, y la enlazan la sección 4.8.1 y el Quick tutorial. Sus resultados confirman la conclusión: con el ePMV, la
temperatura operativa media de la estación de refrigeración sube de 25,11 a 25,71 °C y la electricidad de la
climatización baja de 10212 a 9588 kWh; con la corrección del metabolismo (un 3,6 % menos de actividad de media), 26,15
°C y 9150 kWh, con el mismo PMV medio (0,54). Las temperaturas no salen en el cuaderno: se comprobaron repitiendo sus
simulaciones aparte.

## 4. La actividad y la vestimenta por estación, y el modelo dinámico de vestimenta de ASHRAE 55 (A5)

**Antes.** `set_pmv_input_parameters` escribía, para cada parámetro de cada `People`, una `Schedule:Compact` constante
(`Sch_Act_<people>`, `Sch_Clo_<people>`, `Sch_Vel_<people>` y `Sch_Eff_<people>`), con un valor para todo el modelo o
uno por zona. Si la schedule ya existía, la volvía a usar con su valor: una segunda llamada con otro valor no cambiaba
nada.

**Ahora.**

- `activity_level` y `clothing_insulation` admiten también un diccionario por estación,
  `{'heating_season': x, 'cooling_season': y}`, para todo el modelo o como valor de una zona en el diccionario por
  zonas. Un diccionario cuyas claves son de las dos estaciones es por estación (tiene que tener las dos, con números:
  si no, `ValueError`); cualquier otro es por zonas, como antes. `air_velocity` y `work_efficiency` no cambian.
- La schedule por estación (`_seasonal_schedule_fields`) tiene el valor de refrigeración desde `cooling_season_start`
  hasta el día anterior a `cooling_season_end`, como el programa `set_cooling_season` (`COOLING_SEASON_LINES`):
  `Through: 4/30`, `Through: 9/30` y `Through: 12/31` con los días por defecto (121 y 274); si la estación pasa de un
  año al siguiente (inicio mayor que fin), al revés. Los días se convierten en fechas con un año no bisiesto, como
  `transform_ddmm_to_int`. `cooling_season_start` y `cooling_season_end` son argumentos solo por nombre, después de
  `verbose`, para no cambiar el significado de las llamadas posicionales; `_day_of_year` los comprueba siempre (un día
  de 1 a 366 o 'dd/mm', y distintos).
- `clothing_insulation='dynamic_ashrae55'` (con mayúsculas o minúsculas) pone `DynamicClothingModelASHRAE55` en el
  campo `Clothing Insulation Calculation Method` del `People` (o del `People:Instance` de EnergyPlus 26.2, que tiene ese
  campo: comprobado en el IDD de la etiqueta `v26.2.0` de EnergyPlus; en las versiones anteriores, en los IDD de 9.4,
  9.6, 25.1 y 25.2) y no toca su schedule de vestimenta, que EnergyPlus no lee con ese método. Un número o un
  diccionario por estación vuelve a poner `ClothingInsulationSchedule` si el campo tenía otro método; con el campo
  vacío o con `ClothingInsulationSchedule`, no lo toca, así que los modelos de antes no cambian.
- Cada llamada escribe de nuevo las schedules de los parámetros que recibe (`_write_compact_schedule`: borra la del
  mismo nombre y crea la nueva, al final de los `Schedule:Compact`). Es la corrección del fallo de antes.
- La corrección del metabolismo copia la schedule de actividad tal como está, también la estacional.
- `accim.sim.people.set_clothing_method(building, method, schedule=None, calculation_method_schedule=None)`, de la
  propuesta, cuyo `schedule` no definía: el autor eligió (2026-11-09, la opción (b) de `notes/questions.md`) que
  `schedule` sea la schedule de vestimenta (la de `ClothingInsulationSchedule`, y la de los periodos del método 1 de
  `CalculationMethodSchedule`) y que `CalculationMethodSchedule` tenga otro argumento, que se llama como su campo del
  IDD, `calculation_method_schedule` (obligatorio con ese método y solo con él). Pone el método en todos los `People`
  (o `People:Instance`); antes de cambiar nada comprueba el método (`CLOTHING_METHODS`, con mayúsculas o
  minúsculas), que las schedules estén en el modelo y que la del método tenga los valores 1 y 2 (`schedule_values` de
  `accim.sim.hvac.schedules`, si puede leerla), y avisa de los `People` sin schedule de vestimenta con los métodos que
  la leen. Con `DynamicClothingModelASHRAE55`, `schedule` es un error, porque EnergyPlus no la lee.
- De la propuesta no se ha hecho `clothing_insulation` como función de la temperatura exterior (necesita E1, o un Erl
  por tramos): `TODO.md`.

**Lo que se vio al probarlo** (EnergyPlus 25.1, el modelo de ejemplo de dos zonas en Sevilla).

- EnergyPlus aplica la schedule por estación en hora local, con el horario de verano del modelo (del último domingo de
  marzo al último domingo de octubre): en la hora estándar de los resultados cambia a las 23:00 del día anterior,
  mientras que el programa EMS de la estación, con `DayOfYear`, cambia a las 0:00. Cambian el mismo día; la diferencia
  es esa hora.
- Con el EPW de Sevilla, sin años bisiestos, una simulación de 2004 no tiene el 29 de febrero: el EMS cambia de estación
  el 1 de mayo, como la schedule.
- El modelo dinámico: EnergyPlus calcula la vestimenta de cada día con la temperatura exterior del primer paso de
  tiempo después de las 6:00 (de 6:00 a 6:10, con seis pasos por hora) y las ecuaciones de ASHRAE 55 de la propuesta
  (Schiavon y Lee, 2013; comprobadas en el artículo y en la norma, sección 6), y la mantiene hasta ese paso del día siguiente; antes del primero de cada periodo de
  simulación, 0,75 clo. Comprobado en tres de los cuatro tramos (de −5 a 5 °C, de 5 a 26 °C y desde 26 °C; en los días
  simulados de Sevilla no hubo menos de −5 °C).
- La salida `Zone Thermal Comfort Clothing Value` solo da la vestimenta con el modelo dinámico: con la schedule, da 0.
  Con `CalculationMethodSchedule` sí da la de la schedule en los periodos del método 1 (1 clo en enero, en la prueba),
  y la del modelo dinámico en los del método 2 (julio).

## 5. Pruebas

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
- `tests/core/test_pmv_input_parameters.py` (A5, 33 pruebas): los campos de los `People` y los valores de las schedules
  los días 120, 121, 273, 274 y 275; la estación que pasa de un año a otro y la que empieza el 1 de enero o acaba el 31
  de diciembre; el modelo dinámico y la vuelta a la schedule; las llamadas repetidas; los valores por zona; los errores,
  sin cambiar el modelo; un `People` de dos zonas (el modelo residencial); la copia de la corrección del metabolismo;
  `set_clothing_method` (cada método, sus schedules, los errores sin cambiar el modelo y el aviso); y tres simulaciones
  con EnergyPlus 25.1: los valores de las schedules a mediodía de esos días, con el factor de expectativa del ePMV como
  estación de las consignas; la vestimenta del modelo dinámico frente a las ecuaciones de ASHRAE 55 en tres días de
  enero y tres de julio; y `CalculationMethodSchedule`, con la schedule de vestimenta en enero y el modelo dinámico en
  julio.
- `tests/core/test_people_instance.py`: los valores por estación, el modelo dinámico y `set_clothing_method` en los
  `People:Instance` de EnergyPlus 26.2 (con el IDF simulado del archivo, que ahora tiene los campos del método de la
  vestimenta).
- `tests/core/test_energyplus_versions.py`: una prueba nueva con EnergyPlus 26.2, el modelo de ejemplo con `People` y
  con `People:Definition` y `People:Instance`, con la vestimenta dinámica en una zona y la actividad y la vestimenta por
  estación: los `People:Instance` tienen los campos de A5, EnergyPlus simula los dos modelos igual, y la vestimenta
  dinámica es la misma en todas las horas que comprueba (de 8:00 a 24:00).
- El golden master (`s07` y `s08`) comprueba que los IDF del aPMV no cambian.
- `tests/core/test_table_pmv_index.py` (D2, 28 pruebas): CSV con los nombres de columna de EnergyPlus (los de la
  simulación de la sección 7) y valores inventados, con el modelo de DesignBuilder, el residencial de OpenStudio (zonas
  con el nombre de su espacio y un `People` de dos zonas) y uno con dos `People` en una zona: los nombres de las salidas
  de los tres índices y de la corrección del metabolismo; que ningún nombre de una zona, de un bloque o del edificio
  contenga otro; la media en el tiempo y la suma de las horas; la actividad corregida sin convertir; los valores de
  bloque y de edificio, también con una zona excluida; `rename_cols=False`; `standard_outputs`;
  `format_table('comfort hours')`; los nombres `<IDF>[<EPW>.csv`, junto a los de `AddAccis` en la misma tabla, y el
  error con otros; `time_plot` del ePMV y sus consignas (una columna por nombre); y `wrangled_table` de dos modelos en
  dos ciudades. Una prueba exige un nombre en `Table` para cada salida de `zone_outputs` (o que mantenga el suyo a
  propósito).
- El golden master y las pruebas de EnergyPlus 26.1 y 26.2 se ejecutaron (2026-11-09) en un ordenador sin esas
  versiones, con los zip de NREL extraídos fuera del repositorio y enlazados (uniones de directorio) temporalmente en
  `C:\EnergyPlusV26-1-0` y `C:\EnergyPlusV26-2-0`: 87 passed. Con `ACCIM_ENERGYPLUS_DIR` no basta: besos (la
  configuración `s09` del golden master) y cuatro pruebas de `test_energyplus_versions.py` buscan EnergyPlus en su
  carpeta por defecto.

## 6. Lo comprobado en las normas y los artículos

Comprobado en UNE-EN ISO 7730:2025, UNE-EN 16798-1:2020 (EN 16798-1:2019) y UNE-CEN/TR 16798-2:2019, que faltaban
cuando se escribieron las propuestas (§9.2 de la v02), y en los textos de A5:

- Las categorías del PMV que citan la sección 4.8 del uso detallado, el docstring de `apply_pmv_setpoints` y
  `PMV_INDICES['pmv']` (−0,2 y 0,2; −0,5 y 0,5; −0,7 y 0,7) son las categorías I, II y III de la tabla A.1 de ISO
  7730:2025 y de la tabla B.1 de EN 16798-1; las dos tienen además la IV (−1 y 1). ISO 7730:2025 llama I a III a las
  categorías A, B y C de la edición de 2005, así que el cuaderno del ePMV ya no dice «category B of ISO 7730», sino
  «category II of EN 16798-1 and ISO 7730»; se ejecutó y exportó de nuevo, con los mismos resultados.
- La vestimenta del ejemplo de A5 (1 clo en la estación de calefacción y 0,5 en la de refrigeración) es la que suponen
  EN 16798-1 (tabla B.2) e ISO 7730:2025 (A.4) para sus criterios de diseño; ISO 7730 pide estimar la vestimenta
  teniendo en cuenta la estación del año (4.1). El aislamiento «dinámico» de ISO 7730 (C.2, ISO 9920: lo que lo reducen
  el movimiento del cuerpo y el del aire) no es el modelo dinámico de vestimenta de ASHRAE 55 de A5.
- El programa del PMV del anexo D de ISO 7730:2025, escrito en Python fuera del repositorio, reproduce la tabla D.1 con
  diferencias de redondeo de 0,01 en tres de sus trece casos; con él se comprobó la aproximación de la sección 3.
- CEN/TR 16798-2 no interviene en la 1.2.0. Su evaluación del confort a largo plazo, para las propuestas C2 y D1, está
  en su apartado 8 y en su anexo D (informativo); la v02 de las propuestas la cita como anexo F.
- El modelo dinámico de vestimenta de A5, en el artículo original (Schiavon y Lee, 2013, *Building and Environment* 59,
  250-260, que también faltaba) y en ANSI/ASHRAE 55-2020: las ecuaciones de la propuesta, de la documentación y de las
  pruebas son la ecuación 10 del artículo (§3.6) y las de la figura 5-1 de la norma (5.2.2.2 g y su apéndice
  informativo, «Method 4»). La norma lo admite en edificios climatizados mecánicamente y avisa de que, al basarse en
  estudios de campo, puede no valer para todas las culturas y tipos de ocupación (lo dice la sección 4.8 del uso
  detallado); no se aplica a ocupantes con más de 1,5 clo (5.2.2.3). El artículo recuerda que las normas suponen 1 clo
  en invierno y 0,5 en verano, como el ejemplo de A5.

## 7. Las simulaciones de las consignas basadas en el PMV en `Table` (D2)

La propuesta D2 pide que `Table` reconozca `ePMV_<zone>`, `e_<zone>` y `aPMV_<zone>` en el renombrado (`rename_cols`) y
en las figuras de `time_plot`; también `Tout_metric` y `HoursBelow_*`, que son salidas de B1 y B5, que accim no tiene
(quedan en `TODO.md`). El factor de expectativa se llama `Expectancy Factor_<zone>`, no `e_<zone>`. La v03 de las
propuestas (del autor, en git desde `4d5fb90`, escrita sobre el código de la 1.1.0) añade `Activity_corrected_<zone>`
(aquí, `Corrected Activity Level_<people>`, de cada `People`), `ATHB_PMV_<zone>` (A4) y `HoursBelow_*_<zone>` (D1 o
B5), `wrangled_table` y las unidades (adimensional, W/persona, °C, h): todo hecho menos las salidas de A4, B1, B5 y D1,
que accim no tiene.

**Antes** (comprobado el 2026-11-09 con tres días de julio del modelo de ejemplo con las consignas del ePMV y la
corrección del metabolismo, EnergyPlus 25.1, con un script fuera del repositorio):

- `Table` partía el nombre de cada CSV por `[` en las doce columnas de los nombres de los IDF de `AddAccis` (`Model`,
  `ComfStand`... `EPW`). Los IDF de las consignas del PMV no son de `AddAccis` (la GUI los llama
  `<entrada>_<índice>.idf`), así que `run_ep` llama a sus CSV `<IDF>[<EPW>.csv`, con dos partes, y `Table` se paraba
  con `ValueError: Columns must be same length as key`; también desde la pestaña de la GUI, que pasa a `Table` todos
  los CSV con `[`.
- Con un nombre de doce partes, las salidas EMS de las zonas quedaban con su nombre EMS en mayúsculas
  (`EMS:EPMV_BLOCK1:ZONE1 [](HOURLY)`), sin valores de bloque ni de edificio, y `standard_outputs=True` las quitaba.
- Al agregar en el tiempo, `Table` solo promedia las salidas de `_AVERAGED_OUTPUTS`; a las demás les aplica
  `frequency_agg_func`. Con `'sum'` y valores diarios, sumaba el índice (15,33 en vez de 0,639), el factor de
  expectativa (16,8 en vez de 0,7), las consignas, las schedules de los termostatos y la temperatura del aire, que solo
  añaden estas consignas; el PMV de EnergyPlus sí se promediaba.
- `Corrected Activity Level` (W por persona) pasaba de `[W]` a `(Wh)` y luego a kWh/m2, como si fuera una energía.
- Con `normalised_energy_units=True` (por defecto), los totales de bloque y de edificio de la energía se dividen por
  la suma de las superficies de las zonas (las salidas EMS `Zone Floor Area` del ACCIS); estas simulaciones no las
  tienen, así que la suma era 0 y los totales, infinitos (en la simulación del modelo residencial, con su VRF, el total
  de refrigeración del edificio). Pasaba lo mismo con `output_type='simplified'`, que tampoco añade esas salidas.

**Ahora.**

- `_name_fields` (en `main.py`) da las doce columnas de cada nombre: las partes, si son doce; si son dos
  (`<IDF>[<EPW>.csv`), el IDF en `Model`, el EPW en `EPW` y `CS_X`, `CA_X`... `NS_X` en las demás, como los argumentos
  de `AddAccis` que no se aplican; con otro número de partes, un `ValueError` con el nombre del archivo y los dos
  patrones (antes, el error de pandas de arriba).
- Los nombres de las salidas salen del motor, para que no se separen: `accim.sim.pmv_index` tiene
  `zone_outputs(pmv_index)` (las salidas de cada zona que `_add_outputs` escribía en un diccionario dentro de la
  función; ahora las escribe de ahí, en el mismo orden: el golden master no cambia), `PMV_SETPOINT_SCHEDULES`
  (`PMV_H_SP`, `PMV_C_SP`) y `METABOLIC_CORRECTION_OUTPUTS`.
- El módulo nuevo `accim/data/postprocessing/pmv_index_columns.py` dice qué hace `Table` con ellas, sin engordar el
  constructor (lo que pide R-04): `averaged_outputs()` (todas menos los contadores de horas, que se suman), que
  `_averaged_outputs()` de `main.py` añade a `_AVERAGED_OUTPUTS` en la agregación en el tiempo y al juntar las
  instancias de una zona; `standard_outputs()`, que se añade a la lista de `standard_outputs=True`; `power_outputs()`,
  que no se convierten en energía (la actividad corregida); `comfort_hours()`, para
  `format_table(type_of_table='comfort hours')`; y `zone_columns()`, las columnas de las zonas con su zona y su nombre
  en `Table`.
- `zone_columns` reconoce `EMS:<salida>_<zona>...` con la salida exacta (sin la exactitud,
  `EMS:COMFORTABLE HOURS_NO APPLICABILITY_<zona>`, del ACCIS, sería `Comfortable Hours`): el resto del nombre tiene que
  empezar por la zona que `zone_of` encuentra en la columna. En las zonas que se llaman como su espacio, detrás de la
  zona va el nombre del `People` (`Floor_1_Residential_Living_Occupants`), como en las salidas del ACCIS. Las schedules
  de los termostatos, `PMV_H_SP_<zona>:SCHEDULE VALUE`, con la zona exacta.
- Los nombres en `Table` (sección 4.7.3 del uso detallado): el índice y su coeficiente, con su nombre
  (`Block1:Zone1_aPMV`, `Block1:Zone1_Expectancy Factor`); las consignas, con el índice entre paréntesis, como las
  unidades de las temperaturas de consigna (`Block1:Zone1_Heating Setpoint (aPMV)`,
  `Block1:Zone1_Cooling Setpoint_No Tolerance (aPMV)`); los contadores, con `(h)`; las schedules,
  `Thermostat Heating Setpoint (PMV)` y `Thermostat Cooling Setpoint (PMV)`; la temperatura del aire, como la operativa.
  Las figuras de `Table` toman las columnas cuyo nombre contiene el que se les da, así que ningún nombre puede contener
  otro: con `Block1:Zone1_aPMV Heating Setpoint`, pedir `Block1:Zone1_aPMV` daría también las consignas. Por eso las
  consignas llevan el índice detrás.
- Mantienen su nombre EMS: `PMV_<zona>` de las consignas del PMV (`Block1:Zone1_PMV` ya es el PMV de EnergyPlus; el
  del EMS es el del paso anterior, la media de los ocupantes ponderada por su número), `Occupied hours_<zona>` (es la
  misma columna que `Occupied Hours_<zona>` del ACCIS, que `Table` no renombra; cambiarla cambiaría las tablas del
  ACCIS) y las salidas de la corrección del metabolismo de los `People` de varias zonas.
- Las salidas de la corrección del metabolismo son de cada `People` (`EMS:<salida>_<People>`): `_occupied_zones` da a
  las de un `People` de una sola zona (target) el sufijo EMS de la zona (`metabolic_correction_suffixes`), así que se
  llaman como la zona (`Block1:Zone1_Corrected Activity Level (W/person)`) y, en una zona con varios `People`, se
  promedian, como las salidas de las instancias de una zona (`_rename_and_merge_columns`). No tienen valores de bloque
  ni de edificio.
- Los nombres nuevos no tienen `[`, que `wrangled_table` usa para separar el nombre de la columna del de la simulación,
  y ninguno contiene otro, así que `wrangled_table` toma una columna por nombre, como las figuras.
- `_add_pmv_index_levels` (en `main.py`) añade los valores de bloque y de edificio (suma y media, con `level`,
  `level_agg_func` y las zonas excluidas, como los demás) del índice, el coeficiente, las consignas y los contadores; la
  temperatura del aire, por `outputdict`. Las schedules de los termostatos no los tienen: valen −100 y 100 con la zona
  vacía.
- `_zorder` dibuja encima las series cuyo nombre tiene `Setpoint` (antes, `Setpoint Temperature`), en `time_plot` y en
  `scatter_plot`.
- `per_area` (en el paso de la normalización del constructor) divide los totales de bloque y de edificio por su
  superficie solo donde es positiva, y deja NaN en las demás filas, que lista con un mensaje, como ya listaba la
  energía de las zonas que no puede dividir. En una tabla mixta, la energía de las zonas ya era NaN en las filas sin
  superficie (división por NaN).
- `_add_pmv_index_levels` añade las columnas nuevas de una vez (`pd.concat`): una a una, pandas avisaba de que la tabla
  quedaba fragmentada (`PerformanceWarning`).
- No se ha cambiado: el `PMV` de EnergyPlus se sigue juntando con la media simple de las instancias de una zona,
  mientras que el `PMV_<zona>` del EMS pondera por el número de ocupantes; `ComfStand` deja de ser una variable de la
  tabla si sus valores son un estándar y `CS_X` (la regla de `Table` para los argumentos que no se aplican, `_X`), así
  que en una tabla con simulaciones de los dos tipos se distinguen por `Model`.
