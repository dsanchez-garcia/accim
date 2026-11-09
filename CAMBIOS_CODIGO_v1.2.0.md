# Cómo ha cambiado el código de accim en la versión 1.2.0

Guía de los cambios del código de la rama `v1.2.0` respecto a accim 1.1.0, para quien mantiene accim; no es
documentación de uso. Recoge las propuestas del bloque A de `notes/PROPUESTAS_MEJORAS_post_1.1.0_v01.md` y `_v02.md`
(índices de confort derivados del PMV; archivos del autor, en git desde el commit `e238dad`) que el autor pidió para
esta versión: las P1, A2, A1 y A5, en este orden; y después D2 (sección 7), que el autor incluyó en la 1.2.0 el
2026-11-09 con E2 y E1, y las demás propuestas de la v03 (`notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`), en el orden
del autor (`notes/COPILOT_BRIEF_v1.2.0_v01.md`): E1 (sección 8), E2 (sección 9), A3 (sección 10), B1 (sección 11)...

Lo que ya está en otros documentos no se repite aquí:

- `CHANGELOG.md` (sección Unreleased): los cambios que ve el usuario.
- `docs/source/4_detailed use.md`, secciones 4.3.1, 4.6.1, 4.7.3, 4.8 y 4.8.1: el uso.
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
- **E1.** `accim.sim.preview` calcula las consignas del ACCIS sin EnergyPlus: ejecuta con el intérprete de Erl de
  accim los programas EMS de las consignas (`accim.utils.get_setpoint_ems_programs`) en cada paso de tiempo de un EPW,
  con las medias móviles exteriores que calcula EnergyPlus, que reproduce exactamente (`energyplus_running_means`); y
  da las temperaturas exteriores de referencia de las normas (`outdoor_metrics`). Coincide con EnergyPlus 25.1 a la
  precisión de la máquina (sección 8).
- **E2.** `verify_accim_simulation` comprueba lo que calcula el EMS: el índice de cada zona de las consignas basadas
  en el PMV y la corrección del metabolismo del ePMV, con el PMV del paso anterior (salidas por paso de tiempo), y, con
  `epw`, las consignas de cada zona de los IDF de `AddAccis` frente a `compute_setpoints` (sección 9).
- **A3.** El aPMV admite los coeficientes adaptativos de un catálogo (`accim.constants.APMV_ADAPTIVE_COEFFICIENTS`:
  Yao 2009, GB/T 50785-2012 y los λN de Zhang 2024, estos con aviso) y elegirlos por el signo del PMV
  (`adaptive_coefficient_by='pmv_sign'`), además de por la estación (sección 10).
- **B1.** El modelo personalizado elige su temperatura exterior de referencia (`custom_outdoor_metric`): las medias de
  EnergyPlus o las de EN 16798-1 (B.1, B.2), ASHRAE 55 (n días), la media diaria, la mensual del EPW y la Te,ref de la
  ATG, calculadas en Erl sin `TrendVariable`, solo en los IDF que las usan (sección 11).
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

## 8. Las consignas del ACCIS sin EnergyPlus (E1)

La propuesta E1 pide `accim/sim/preview.py` con `outdoor_metrics(epw, alpha=0.8, days=30)`,
`compute_setpoints(epw, comfort_standard, category=None, comfort_mode=None, **custom_arguments)` y `plot_setpoints(df)`,
con las convenciones de EnergyPlus (Engineering Reference 25.2, §19.1), y pruebas frente al CSV de una simulación del
IDF de ejemplo para los ComfStand 1, 2 y 99, con la tolerancia del redondeo `SetpointAcc`. El brief del autor añade que
dé también las series exteriores con las que B1 iniciará las medias móviles en Erl (decisión D3), y la decisión D9, que
reproduzca las medias de EnergyPlus y ejecute el Erl de `get_setpoint_ems_code` con `accim.sim.ems.erl`.

**Antes.** `get_setpoint_ems_code` daba el Erl de cada combinación como texto, con los subprogramas recortados a las
líneas del modo de confort: no se puede ejecutar tal cual, porque `SetAST_Master` llama a los subprogramas enteros.
`accim.sim.ems.erl` (`ErlProgramSet`) ya interpretaba el Erl en Python para el backend de la API. No había forma de ver
las consignas de un clima sin simular.

**Ahora.**

- `accim.utils.get_setpoint_ems_programs` (en `ems_code.py`) da los programas de `get_setpoint_ems_code` por nombre y
  en el mismo orden (`SetInputData_<zone>`, `SetAppLimits`, `ApplyCAT`, `SetComfTemp`, `SetAST`, `SetAST_Master`, los
  subprogramas enteros y `SetASTnoTol`), con los mismos argumentos y valores por defecto; exige la categoría y el modo
  de confort cuando el estándar los tiene. Las comprobaciones de los argumentos están en `_checked_arguments`, que
  comparten las dos funciones; la salida de `get_setpoint_ems_code` no cambia.
- `accim.sim.preview` (módulo nuevo):
  - `read_epw_dry_bulb`: la temperatura seca de cada hora del EPW (las 8 líneas de cabecera, y días enteros de las
    horas 1 a 24).
  - `outdoor_metrics`: las temperaturas exteriores de referencia como las definen las normas (v03 §11.4), por hora o
    por día (`frequency`): media, máxima y mínima diarias; `RMOT`, la media móvil de EN 16798-1 (B.1) con cualquier α,
    calculada para un año que se repite (la suma infinita es la de los días del año dividida por 1 − α^n); `RMOT_7day`
    (B.2); `PMOT_n`, la media de los `days` días anteriores (ASHRAE 55-2020, 5.4.2.1); `Te_ref_nl` (van der Linden et
    al., 2006, con la media de la máxima y la mínima de cada día); y la media mensual. Los primeros días toman los
    últimos del archivo. Es la serie diaria con la que B1 iniciará las medias en Erl (D3).
  - `energyplus_running_means`: las medias que el EMS lee de EnergyPlus (`RMOT`, CEN 15251; `PMOT`, ASHRAE 55), tal
    como las calcula EnergyPlus 25.1, comprobado con simulaciones y con su código (`ThermalComfort.cc`):
    - `PMOT`: la media simple de las medias de los 30 días anteriores (ec. 19.70). Los días anteriores al periodo de
      simulación son los del EPW (media de sus 24 valores; para los primeros días del año, los últimos del archivo).
    - `RMOT`: el primer día del periodo, la suma ponderada de los 7 días anteriores de la ec. 19.82, que EnergyPlus no
      divide por 1 − α⁷ (con α = 0,8), así que sale baja los primeros días (en Sevilla, 5,92 °C el 1 de enero frente a
      8,34 °C de la B.1; 0,5 °C menos una semana después); el primer día no se actualiza; después, la ec. 19.83 con la
      media del día anterior.
    - La media de un día simulado es la de la temperatura exterior del primer paso de cada hora, que EnergyPlus
      interpola entre el valor horario anterior y el actual: media del EPW + ((N − 1)/N)·(T(d − 1, 24 h) − T(d, 24 h))/24,
      con N pasos por hora. El primer día del periodo, la hora anterior a la primera es la última del mismo día (el
      calentamiento repite el día), así que su media es la del EPW.
    - Con un `.stat` junto al EPW, EnergyPlus toma `PMOT` de sus medias mensuales; no se reproduce (documentado y en
      `TODO.md`). Hace falta un EPW de 365 días.
  - `compute_setpoints`: ejecuta con `ErlProgramSet` los programas, en el orden de `RunACCIS_<zone>`
    (`SetInputData_Z`, `SetAppLimits`, `ApplyCAT`, `SetComfTemp`, `SetAST`, que llama a `SetAST_Master` y a los
    subprogramas, `SetASTnoTol`, y `CountHours_Z` con `Z_OpT = 0`, para la aplicabilidad), en cada paso de tiempo, desde
    `start_date` hasta el final del año. El estado inicial es el de `InitASTvariables` (`ACST`, `AHST` y `ComfTemp`
    nulos, `CoolingSeason = 0`) y `ZoneTimeStep = 1/N`. Los sensores del EMS se leen en
    `BeginTimestepBeforePredictor`: en el primer paso de cada día leen la media del día anterior (y 0 en el primer paso
    del periodo), y `CurrentTime` es el final del paso (comprobado con el ComfStand 0: el paso que acaba a las 8:00 ya
    tiene las consignas del día). Los programas solo se ejecutan cuando cambian sus entradas (`RMOT`, `PMOT`, el día y,
    si lo usan, `CurrentTime`): con las mismas entradas dan lo mismo. Los valores horarios son la media de los pasos,
    como las salidas EMS de EnergyPlus (`Averaged`); `applicable` y `cooling_season`, los del último paso de la hora.
    Un valor nulo (la temperatura de confort de las consignas fijas) sale NaN; EnergyPlus lo informa como 0.
    `Tout_metric` es la media móvil que usan las líneas de las consignas del modo de confort (o `SetComfTemp`).
    Un año con 6 pasos por hora tarda menos de un segundo.
  - `plot_setpoints`: las consignas, la temperatura de confort y la media móvil del estándar.
- Pruebas: `tests/core/test_preview.py`, 30 pruebas: las fórmulas con EPW inventados; las medias de EnergyPlus
  (arranque, días simulados, inicio del año); los programas frente al texto de `get_setpoint_ems_code`; los argumentos;
  y dos simulaciones del modelo de ejemplo con EnergyPlus 25.1 (EN 16798-1 en una zona y ASHRAE 55 en la otra, 36 días
  de enero y febrero, horario; el modelo CUSTOM y ESP CTE, 4 días de julio, por paso de tiempo), con tolerancia
  0,0001 °C en las consignas y 1e-9 en las medias. Antes, cinco experimentos fuera del repositorio (ComfStand 1 un año
  horario; 2 del 10/03 al 20/04 horario; 1, 0 y 99 unos días por paso) coincidieron a la precisión de la máquina
  (~1e-14).
- Desviación de la v03: dice que, al calcularse del EPW, "no hay transitorio de arranque". EnergyPlus sí lo tiene en la
  media de CEN 15251 (la ec. 19.82 sin normalizar); se reproduce EnergyPlus, como pide D9.
- No cambian los IDF de salida ni la GUI (E1 no añade argumentos a `AddAccis`). Al comprobarlo con EnergyPlus salieron
  dos posibles errores de los ComfStand 9 y 10 (las medias de 7DRM y 30DRM parecen cambiadas, y la consigna de
  calefacción del modo 1 del 9 fuera de los límites lleva el signo de la de refrigeración): están en `TODO.md`,
  pendientes del autor, sin tocar.

## 9. La verificación de lo que calcula el EMS (E2)

La propuesta E2 pide a `verify_accim_simulation` (`accim/utils/verification.py`) que compruebe `ePMV = e·PMV`,
`aPMV = PMV/(1 + λ·PMV)`, `Activity_corrected = met·(1 − 0.067·PMV_prev)` con `PMV_prev > 0`, `Tout_metric` frente a
`outdoor_metrics()` (B1), `AHST ≥ AHSTfloor` y `ACST ≤ ACSTceil` (B5) y, para B3, que las consignas de los modelos
registrados coinciden con `compute_setpoints`. El brief añade: `ePMV = e·PMV` solo con PMV > 0 (así está hecho) y la
corrección del metabolismo «con la tolerancia del 5,5–6,1 %».

**Antes.** `verify_accim_simulation` tenía dos comprobaciones de los IDF de `AddAccis`: la temperatura operativa
dentro de las consignas mientras se climatiza (1) y las condiciones de las ventanas en modo mixto (2). En un IDF con
consignas basadas en el PMV no encontraba zonas (busca los sensores `<zona>_OpT` del ACCIS) y daba todo por bueno.

**Lo que hace el EMS** (comprobado el 2026-11-09 con tres simulaciones de EnergyPlus 25.1 con salidas por paso de
tiempo, del 28/04 al 03/05: aPMV y PMV en el modelo de ejemplo, ePMV con la corrección en el residencial, cuyo
`People` es de dos plantas): en `BeginTimestepBeforePredictor`, el sensor del PMV de cada `People` lee el del paso
anterior y el de sus ocupantes, el del paso actual (`Occupied hours_<zona>` y la schedule de 100 siguen a los
ocupantes del paso, no a los del anterior). Con eso, las salidas cumplen las fórmulas con diferencias de 1e-16, salvo
el primer paso de cada entorno (los días de diseño y el periodo de simulación), cuyo PMV anterior es el del
calentamiento.

**Ahora.**

- Comprobación 3 (`_pmv_index_mismatches`), en los modelos con programas `apply_<índice>_<zona>` de
  `accim.sim.pmv_index`, con las salidas por paso de tiempo (con las horarias no se hace y avisa: la media horaria no
  cumple las fórmulas, por el paso de retraso y porque la media de una función no es la función de la media):
  - El PMV de la zona que lee el EMS: el del `People` de la zona en el paso anterior; con varios `People`
    (`PMV_<zona>_<n>`), su media ponderada por sus ocupantes del paso (la media simple si no hay), como
    `average_PMV_<zona>`. Los sensores dicen de qué salidas se leen.
  - `Check3_aPMV`: aPMV = PMV/(1 + λ·PMV), con λ de la salida `Adaptive Coefficient_<zona>`.
  - `Check3_ePMV`: ePMV = e·PMV si PMV > 0 y PMV si no, con e de `Expectancy Factor_<zona>`; si el programa
    `monitor_ePMV_<zona>` no tiene `if` (`apply_to_heating=True`), e·PMV siempre.
  - `Check3_PMV`: el PMV de las consignas del PMV es el del paso anterior.
  - `Check3_MetabolicFactor`: el factor de cada `People` es 1 − 0,067·PMV (entre 0 y 3) en la estación de
    refrigeración y 1 en la de calefacción; la estación sale de los programas `set_cooling_season_input_data` y
    `set_cooling_season` del modelo, ejecutados con el intérprete de Erl de accim para cada día. Con un `People` de
    varias zonas, la media de sus PMV ponderada por los ocupantes (`resolve_targets` da las zonas de cada `People`).
  - `Check3_CorrectedActivity`: la actividad corregida es la actividad sin corregir por ese factor; solo si las
    salidas tienen la actividad sin corregir (`Schedule Value` de la schedule del sensor `Activity_base_<people>`).
  - La tolerancia del 5,5–6,1 % del brief: es la reducción de la actividad para un PMV de 1 *antes* de la corrección,
    cuando la corrección converge, y las salidas no tienen ese PMV. Se comprueba la relación exacta del EMS (con el PMV
    del paso anterior); queda en `notes/questions.md`, decidido provisionalmente.
- Comprobación 4 (`_setpoint_mismatches`), solo con el argumento nuevo `epw`, en los IDF de `AddAccis`: las salidas
  de cada zona (`Comfort Temperature_<zona>`, `Adaptive Cooling Setpoint Temperature_<zona>`... con y sin tolerancia)
  frente a `compute_setpoints` con los argumentos de su programa `SetInputData_<zona>`
  (`_compute_setpoints_arguments`, por `INPUT_VARIABLES`; la tolerancia es `AHSTtol`, y `ACSTtol` debe ser su
  opuesta), el EPW, el primer día del `RunPeriod` y los pasos por hora del objeto `Timestep` (6, el valor por defecto
  de su campo en el IDD, si está vacío; si no hay objeto, los de las salidas por paso); y las medias móviles de
  EnergyPlus frente a `energyplus_running_means`. Usa las salidas por paso de tiempo o, si no, las horarias, del
  último entorno (el periodo de simulación); si este no empieza el primer día del `RunPeriod`, no compara. Cubre todos
  los ComfStand, así que los de B3 pasarán por ella. `accim.sim.preview.SETPOINT_EMS_VARIABLES` da la variable EMS de
  cada columna de `compute_setpoints`.
- La hora de cada fila sale de `Date/Time` (`_dates_and_times`: el final del paso, con 24:00:00 como medianoche del
  día siguiente, y la fecha de la fila, también a las 24:00:00), en el año de `compute_setpoints` (2007, o 2008 con un
  29 de febrero); `_environment_starts` marca la primera fila de cada entorno (la que no sigue a la anterior por un
  paso). `_Outputs` busca las salidas por clave y variable, sin distinguir mayúsculas.
- El argumento `calculation_tolerance` (0,001) es la diferencia admitida en las comprobaciones 3 y 4. Las
  comprobaciones 1 y 2 no cambian. Las descripciones que se imprimen son ASCII (la consola de Windows, cp1252, no
  imprime λ).
- Pruebas: `tests/core/test_verification.py`, 12: las fechas y los entornos; la media ponderada; los argumentos de
  `compute_setpoints`; la comprobación 3 con salidas inventadas (aPMV, ePMV con y sin `apply_to_heating`, PMV; un
  valor erróneo; el aPMV del mismo paso; la corrección de un `People` de dos zonas, que con los ocupantes del paso
  anterior falla; sin salidas por paso, aviso); la comprobación 4 con salidas de `compute_setpoints` tras un día de
  diseño (otro EPW y otro `RunPeriod`); y dos simulaciones de EnergyPlus 25.1 (ePMV con la corrección, sin errores con
  tolerancia 1e-6; el modelo CUSTOM y ESP CTE frente a `compute_setpoints`, sin errores con su EPW y con errores en
  las medias y en el CUSTOM, no en ESP CTE, con otro).
- Encontrado de paso (en `TODO.md`, sin tocar): la comprobación 1 no encuentra las salidas de las zonas cuyo nombre
  tiene `:` (como `Block1:Zone1`), porque parte el nombre de la columna por el primer `:`; las comprobaciones nuevas
  buscan por clave y variable. Quedan para B1 y B5 sus comprobaciones (`Tout_metric`, suelo y techo).

## 10. El catálogo de coeficientes adaptativos del aPMV y su elección por el signo del PMV (A3)

La propuesta A3 pide `APMV_ADAPTIVE_COEFFICIENTS` en `accim/constants.py` (Yao 2009; GB/T 50785-2012 por zona
climática y tipo de edificio; los λN de la Tabla 6 de Zhang, Yao y Li 2024 por zona Köppen, de grado 'literature'),
claves del catálogo en `adaptive_coefficient_cooling/heating` resueltas en `generate_df_from_args`, un aviso con las
entradas 'literature', `get_adaptive_coefficients(key)` y la opción `adaptive_coefficient_by='season'|'pmv_sign'`. La
decisión D4 del brief mantiene `'season'` por defecto y admite las entradas 'literature' con aviso.

**Antes.** `apply_apmv_setpoints` tomaba λ como números (o diccionarios de números por zona), y el programa
`apply_aPMV_<zona>` elegía el de la estación (`adap_coeff_<zona>`), con el que `monitor_aPMV_<zona>` calculaba el aPMV
y con el que se convertían las dos consignas en las consignas PMV de los termostatos.

**Ahora.**

- `accim/constants.py`: `APMV_ADAPTIVE_COEFFICIENTS`, con los valores de la v03 (§11.2 y A3): `cooling` es el λ de las
  sensaciones cálidas (PMV ≥ 0) y `heating` el de las frías (PMV < 0), que `apply_apmv_setpoints` toma como
  `adaptive_coefficient_cooling` y `_heating`; `grade` ('standard' para Yao 2009 y GB/T 50785; 'literature' para los
  14 de Zhang 2024), `source` y `notes`. Aw no tiene λ de sensaciones frías (`None`). La Tabla 6 de Zhang da cada fila
  como «PMV<0 / PMV>0»: en el catálogo, `heating` y `cooling`.
- `accim/sim/pmv_index.py`:
  - `get_adaptive_coefficients(key)` (una copia de la entrada; `ValueError` con las claves válidas) y
    `resolve_adaptive_coefficients(values)`, que sustituye las claves de los cuatro argumentos de λ (también como
    valores de los diccionarios por zona) por el coeficiente de su lado y avisa una vez por clave 'literature' (muchos
    λN saturan en ±0,66 y algunos signos contradicen el mecanismo adaptativo: λ < 0 con PMV > 0 en Cfb, Csc, Dfb y Dwa;
    λ > 0 con PMV < 0 en Af y Cfa). Una clave sin coeficiente para su lado (Aw en calefacción) da `ValueError`.
  - `PmvIndex` tiene dos ganchos nuevos: `resolve` (los valores de los parámetros que se usan, a partir de los dados;
    `_index_values` lo llama antes de `validate`), y `seasonal_coefficient(options)` (si `apply_<índice>_<zona>` elige el
    coeficiente de la estación; si no, lo elige el monitor).
  - El índice 'apmv' tiene la opción `adaptive_coefficient_by` ('season' por defecto, o 'pmv_sign';
    `ADAPTIVE_COEFFICIENT_BY`; `_apmv_validate`). Con 'pmv_sign': `apply_aPMV_<zona>` solo elige las tolerancias por
    estación; `monitor_aPMV_<zona>` elige `adap_coeff_<zona>` por el signo de `PMV_<zona>` (el del paso anterior; el
    monitor va detrás de `average_PMV_<zona>`, así que también en las zonas con varios `People`) antes de calcular el
    aPMV; y la consigna de calefacción se convierte en la consigna PMV del termostato con λ de calefacción, y la de
    refrigeración con λ de refrigeración (`_apmv_inverse`), sea cual sea la estación. Esto último no lo dice la v03: es
    la inversa del aPMV con λ por el signo (una consigna negativa está en el lado frío); con el λ del signo del PMV de
    cada momento, las consignas del termostato cambiarían cada vez que el PMV cambia de signo. Queda en
    `notes/questions.md`, decidido provisionalmente.
  - Con 'season', las líneas no cambian (golden master idéntico).
- `accim/sim/apmv.py`: `apply_apmv_setpoints` acepta claves (los tipos de los argumentos lo dicen) y el argumento nuevo
  `adaptive_coefficient_by` (al final de la firma); `generate_df_from_args` resuelve las claves; `get_adaptive_coefficients`
  se exporta desde aquí, como pide la propuesta. Cada argumento toma el coeficiente de su lado: para usar los dos de una
  entrada hay que dar la clave a los dos (la v03 sugiere que una clave rellene los dos; queda en `notes/questions.md`,
  decidido provisionalmente, porque los valores por defecto son números y no se distingue un valor explícito igual al
  defecto).
- GUI (`accim/gui/forms.py`, `app.py`): en la pestaña *2. PMV-based setpoints*, *λ of the literature* (las claves del
  catálogo) rellena los dos campos de λ (el de calefacción no, si la entrada no tiene) y muestra las notas, la fuente
  y el grado (con 'literature', que hay que comprobarlos), y *Adaptive coefficient by* da `adaptive_coefficient_by`;
  ambos solo con el aPMV. Los campos siguen siendo números. `forms.APMV_OPTIONS` y `forms.ADAPTIVE_COEFFICIENT_BY`
  coinciden con los de `accim.sim.pmv_index` (probado); los rótulos de λ dicen «cooling season or PMV >= 0» y «heating
  season or PMV < 0» (sin «≥», que cp1252 no tiene: `tests/core/test_printed_messages.py`).
- Pruebas: `tests/core/test_apmv_coefficients.py` (6: el catálogo frente a los valores de la v03, incluidos los signos
  anómalos; `get_adaptive_coefficients`; la resolución y el aviso; el IDF con claves igual al de números;
  `generate_df_from_args`; el Erl de 'pmv_sign' con el intérprete en las dos estaciones y con PMV positivo, negativo y
  cero; y una simulación de EnergyPlus 25.1 con los dos backends, CSV iguales, los dos λ usados y la comprobación 3 de
  `verify_accim_simulation` sin errores), y en `tests/core/test_gui.py`, los formularios y la pestaña.
- Comparación de backends (`run_ep(backend='ems')` frente a `run_ep(backend='api')`, el modelo de ejemplo con
  'pmv_sign' y los λ de `gbt50785_cold_general`, del 24/04 al 07/05, salidas por paso y horarias): 2016 filas × 81
  columnas idénticas (diferencia máxima 0,0); 5,0 s frente a 7,4 s.

## 11. La métrica exterior del modelo personalizado (B1)

La propuesta B1 pide el argumento `custom_outdoor_metric` del modelo personalizado (ComfStand 99), `'pmot'` por
defecto (el comportamiento de antes), con `'rmot'`, `'rmot_alpha'` (y `custom_alpha`), `'rmot_7day'`, `'daily_mean'`,
`'ndrm'` (y `custom_days`), `'monthly_mean'` y `'te_ref_nl'`, calculadas en Erl sin
`EnergyManagementSystem:TrendVariable` (el backend de la API no lo admite), con `Tout_metric` como variable global y
salida EMS, y que `SetComfTemp`, `SetAppLimits` y `COUNT_HOURS` la usen con ComfStand 99. Las decisiones D3 (arranque
con los valores del EPW dado a AddAccis, o con PMOT y aviso; `'monthly_mean'` exige el EPW) y D7 (α fuera de 0,6–0,9 y
días fuera de 7–30 avisan) del brief la completan. Las ecuaciones son las de la v03 §11.4: EN 16798-1:2019, anexo B,
fórmulas (B.1) y (B.2); ASHRAE 55-2020, 5.4.2.1; van der Linden et al. (2006).

**Antes.** El modelo personalizado calculaba su temperatura de confort (`PMOT*m+n`), sus consignas
(`SetAST_CS99_0`), las horas (`CountHours_<zona>`) y, en modo mixto, la consigna de ventilación (`SetVST`) con `PMOT`,
la media de ASHRAE 55 de EnergyPlus.

**Ahora.**

- `accim/sim/ems/outdoor_metric.py` (nuevo):
  - `OUTDOOR_METRICS` (nombre → código, el valor de `CustAST_metric`: pmot 0 ... te_ref_nl 7), `metric_code`,
    `metric_name`, `check_outdoor_metric_arguments` (errores y los avisos de D7), `ring_days` (los días que se guardan:
    30, o más si una zona tiene más `custom_days`).
  - Tres programas: `SetOutdoorMetric` (del edificio, en BeginTimestepBeforePredictor antes de los de las zonas: suma
    los valores del final de cada hora, `Minute > 59.5`, que son los del EPW, y en el primer paso de cada día,
    `(Hour == 0) && (TimeStepNum == 1)`, desplaza las medias diarias `Tday_1...Tday_n` y las medias de máxima y mínima
    `Tmid_1...Tmid_3`; no suma los días de calentamiento, `WarmupFlag`); `SetOutdoorMetric_<zona>` (lo ejecuta
    `RunACCIS_<zona>` tras sus entradas: la media recursiva `RMOTa_<zona>` con su α y `Tout_metric` según
    `CustAST_metric`; `'monthly_mean'` sin EPW sería `@FatalHaltEp 6`, pero antes se da `ValueError`); e
    `InitOutdoorMetric` (BeginNewEnvironment: todo a 0, el valor de PMOT antes de que EnergyPlus lo calcule).
  - Arranque (D3): con el EPW, constantes del primer día del primer RunPeriod del IDF (`initial_values`, la serie de
    `outdoor_metrics`, con caché), usadas si el entorno empieza ese día; si no, o sin EPW (con aviso), PMOT en cuanto no
    es 0. Los 12 valores mensuales del EPW van en el programa: el IDF queda ligado a ese EPW.
  - `set_outdoor_metric_code(idf, enabled, epw, rewrite)` añade o quita las entradas, los programas, la línea de
    `RunACCIS_<zona>`, los programas de llamada, las variables globales (un objeto cuya primera variable es
    `Tout_metric`), las salidas `Tout_metric` y `Tout_metric_<zona>` (con `Output:Variable` en las frecuencias de las de
    la temperatura de confort) y cambia `PMOT` por `Tout_metric` en los programas del modelo personalizado
    (`_set_custom_model_lines`: la línea de `SetComfTemp`, `SetAST_CS99_<n>`, la rama propia en `CountHours_<zona>` y en
    `SetVST`). Sin EPW y sin `rewrite`, conserva los programas que ya tenga el modelo (y sus constantes del EPW) si
    guardan días suficientes. `uses_outdoor_metric`, `has_outdoor_metric_code`, `begins_with_weather_file`.
- `accim/sim/ems/program_lines.py`: `SET_COMF_TEMP`, `COUNT_HOURS` y `SET_VST` no cambian (comprobado frente a HEAD);
  nuevas `OUTDOOR_METRIC_VARIABLE`, `SET_COMF_TEMP_OUTDOOR_METRIC`, `COUNT_HOURS_OUTDOOR_METRIC` (la rama de 99 con
  `Tout_metric`), `SET_VST_OUTDOOR_METRIC` y `chain_comfort_standards` (las normas que nombra una cadena); el análisis
  de las ramas pasa a `_branches`, sin cambiar `for_comfort_standards`.
- `accim/sim/ems/setast.py`: `get_setpoint_lines` y `subprograms` admiten `outdoor_metric=True` (las líneas de 99 con
  `Tout_metric`); `CUSTOM_COMFORT_STANDARD`.
- `accim/sim/ems/programs.py`: `set_comfort_standard_code(idf, normas, epw=None)` escribe los programas de las normas
  como antes y llama al final a `set_outdoor_metric_code` (activado si el modelo tiene el código de 99 y alguna zona una
  métrica distinta de `'pmot'`); `code_comfort_standards(idf)` (None si el modelo tiene el código de todas las normas,
  como `add_accis_to_idf`).
- `accim/sim/ems/inputs.py`: tres entradas nuevas tras `CustAST_AHSTall` (`CustAST_metric`, `CustAST_alpha`,
  `CustAST_days`, con `outdoor_metric_only`), que `input_lines(..., outdoor_metric=True)` escribe y `input_values`
  convierte (el nombre de la métrica en su código). `ZONE_ARGUMENTS` las incluye.
- `accim/sim/generation.py`: `GenerationArguments` tiene `custom_outdoor_metric`, `custom_alpha` y `custom_days` (al
  final); `set_combination` escribe siempre las entradas de la métrica, y `set_comfort_standard_code` las quita si
  ninguna zona las necesita.
- `accim/sim/accis.py`: `AddAccis` tiene `custom_outdoor_metric`, `custom_alpha`, `custom_days` y `epw` al final de la
  firma (`_check_outdoor_metric`: errores, avisos de D7 también por zona, `ValueError` de `'monthly_mean'` sin EPW; los
  prompts no las preguntan, y se conservan si se usan); `_write_output_idfs` pasa `epw`. `modify_accis` tiene los
  cuatro al final, con `None` por defecto (conservan los valores de las zonas; `notes/questions.md`): si se da alguno,
  añade las líneas que falten y escribe de nuevo los programas (`rewrite=True`); los modelos de versiones anteriores
  solo admiten `'pmot'`.
- `accim/utils/ems_code.py`: `get_setpoint_ems_code` y `get_setpoint_ems_programs` toman las tres y `epw` y
  `start_date`; con 99 y una métrica distinta de `'pmot'` dan los programas de la métrica (con `<zone>`), sus entradas y
  las líneas con `Tout_metric`.
- `accim/sim/preview.py`: `compute_setpoints` ejecuta los programas de la métrica en cada paso (con `Hour`,
  `TimeStepNum`, `Minute`, `Month`, `WarmupFlag` = 0 y la temperatura exterior interpolada, exacta al final de cada
  hora), y su `Tout_metric` es la de esos programas; argumento nuevo `outdoor_metric_start` ('epw' o 'pmot').
- `accim/utils/verification.py`: `Check4_Tout_metric` (la métrica de cada zona frente a `compute_setpoints`, que
  arranca como el modelo: `begins_with_weather_file`). La v03 decía «frente a `outdoor_metrics()`»: `compute_setpoints`
  ejecuta los mismos programas, y en las pruebas se compara con `outdoor_metrics` y con pandas.
- `accim/data/postprocessing/main.py`: `Table` promedia en el tiempo `EMS:Tout_metric` (antes las habría sumado).
- GUI: en el marco del modelo personalizado, la métrica (lista con su descripción, `forms.CUSTOM_OUTDOOR_METRICS`),
  `custom_alpha`, `custom_days` y el EPW (`epw`, con *Browse...*); `custom_outdoor_metric_arguments`; los pares de la
  tabla de zonas admiten `custom_outdoor_metric=<nombre>`; el código EMS de la GUI incluye la métrica.
- Desviaciones de la v03: el código de la métrica solo está en los IDF cuyas zonas lo necesitan (con `'pmot'` los IDF
  son los de 1.1.0, golden master idéntico); además de `SetComfTemp` y `COUNT_HOURS`, usan `Tout_metric` las consignas
  de 99 y `SetVST` (`SetAppLimits` no compara la métrica en accim); el final de la hora es `Minute > 59.5` porque
  `TimeStepsPerHour`, que la guía del EMS lista, vale 0 en ese punto de llamada con EnergyPlus 25.1 (comprobado con una
  salida EMS de una copia); la prueba de `rmot_alpha(0.8)` frente al RMOT nativo es tras 21 días, no 14 (EnergyPlus
  arranca con la ecuación 19.82 sin dividir por 1 − α⁷: 0,10 K el día 15 en Sevilla desde el 1 de enero, menos de
  0,045 K desde el día 22).
- Pruebas: `tests/core/test_outdoor_metric.py` (34: códigos, avisos y errores de D7; las variantes de los programas;
  el código EMS; con el intérprete y un EPW inventado, frente a pandas: (B.1) recursiva con α 0,8 y 0,7, (B.2) y
  `rolling(n).mean()` desplazado para 7, 30 y 45 días, media diaria y mensual, Te,ref al final del día y de cada hora,
  el RMOT nativo y el arranque con PMOT; AddAccis: los IDF de las demás normas idénticos a los de un AddAccis sin la
  métrica y los objetos del de 99; `modify_accis` añade la métrica y, al volver a `'pmot'`, el modelo es idéntico al
  de referencia; los modelos de 0.x; EnergyPlus 25.1: `rmot_alpha` y `te_ref_nl` del 1/01 al 28/02 por paso, sin
  discrepancias en la comprobación 4 y a menos de 0,05 K del RMOT nativo desde el día 22; y los dos backends
  idénticos con `ndrm` y `daily_mean` arrancando con PMOT).
- Comparaciones con EnergyPlus 25.1 (fuera del repositorio, por paso de tiempo): `rmot_alpha` + `te_ref_nl` (1/01 a
  28/02), `ndrm(7)` + `rmot_7day` (10/06 a 20/07), `monthly_mean` + `daily_mean` (20/03 a 10/05), `rmot_alpha(0,7)` +
  `rmot` sin EPW (1/01 a 28/02) y `rmot_alpha` + `pmot` en modo mixto (1/07 a 10/08): 0 discrepancias en la
  comprobación 4, también en `Check4_Tout_metric`. Backends (`run_ep(backend='ems')` frente a `'api'`, tres de esos
  modelos): todas las columnas idénticas (diferencia máxima 0,0; 8496, 8496 y 5904 filas), 13,5 s frente a 16,2 s,
  12,8 frente a 16,2 y 9,5 frente a 13,1.
