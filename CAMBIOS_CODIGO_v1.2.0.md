# Cómo ha cambiado el código de accim en la versión 1.2.0

Guía de los cambios del código de la rama `v1.2.0` respecto a accim 1.1.0, para quien mantiene accim; no es
documentación de uso. Recoge las propuestas del bloque A de `notes/PROPUESTAS_MEJORAS_post_1.1.0_v01.md` y `_v02.md`
(índices de confort derivados del PMV; archivos del autor, en git desde el commit `e238dad`) que el autor pidió para
esta versión: las P1, A2, A1 y A5, en este orden; y después D2 (sección 7), que el autor incluyó en la 1.2.0 el
2026-11-09 con E2 y E1, y las demás propuestas de la v03 (`notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`), en el orden
del autor (`notes/COPILOT_BRIEF_v1.2.0_v01.md`): E1 (sección 8), E2 (sección 9), A3 (sección 10), B1 (sección 11),
B5 (sección 12), C1 (sección 13), D1 (sección 14), B2 (sección 15), B3 (sección 16), B4 (sección 17), C2 (sección
18), E4 (sección 19), A4 (sección 20) y A6 (sección 21); y, al final, lo que faltaba de D2: las salidas opcionales
del ACCIS y del ATHB en `Table` (sección 22). Después, las tareas de la revisión independiente de la 1.2.0
(`notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md`, §7), en el orden del autor: G1 (sección 23) y las siguientes; y, en
la tercera sesión, las tareas S1 a S5 de `notes/COPILOT_SIGUIENTE_SESION.md` y las correcciones de su auditoría de la
segunda sesión (sección 38 y las siguientes).

Lo que ya está en otros documentos no se repite aquí:

- `CHANGELOG.md` (sección Unreleased): los cambios que ve el usuario.
- `docs/source/4_detailed use.md`, secciones 4.2.2, 4.2.3, 4.2.4, 4.2.5, 4.2.6, 4.3.1, 4.5.1, 4.6.1, 4.7.3, 4.7.4,
  4.7.5, 4.8, 4.8.1, 4.9, 4.9.1 y 4.9.2: el uso.
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
- **B5.** Suelo de la consigna de calefacción y techo de la de refrigeración (`heating_setpoint_floor`,
  `cooling_setpoint_ceiling`; los valores de la tabla B.2 de EN 16798-1 en `accim.constants.EN16798_TABLE_B2`), para
  todas las normas y modos de confort, salvo las consignas basadas en el PMV (D5); y las horas ocupadas por debajo de
  unas temperaturas (`report_hours_below`, salidas `HoursBelow_<T>_<zona>`). Solo los IDF que los usan cambian
  (sección 12).
- **C1.** El paramétrico varía la vestimenta, la actividad y la velocidad del aire (con las consignas basadas en el
  PMV, avisando fuera de los rangos de ISO 7730:2025 §4), la métrica exterior del modelo personalizado y el suelo y el
  techo de las consignas, con una clase para cada parámetro (sección 13).
- **D1.** Los indicadores de disconfort de largo plazo de CEN/TR 16798-2 (anexo D, métodos A, B y C; anexo E,
  tabla E.1) en `accim.data.postprocessing.long_term_discomfort`, y los de los métodos A y B de cada simulación, zona
  y edificio con `Table(long_term_indicators=True)` (sección 14).
- **B2.** El modelo personalizado admite varios regímenes (`custom_regimes`, una lista de `CustomRegime`), cada uno
  con sus coeficientes y la condición en que se aplica (siempre, estación, HVAC apagado o encendido en modo mixto, o la
  métrica exterior por debajo, por encima o entre dos valores); el programa `SelectCustomRegime_<zona>` pone las
  entradas del modelo del primero que se cumple, y la salida `CustomRegime_<zona>` dice cuál (sección 15).
- **B3.** Normas de confort definidas por sus datos (`ComfortStandardDefinition`, en YAML con
  `load_comfort_standards`), con números ≥ 100: accim añade sus ramas al final de las cadenas de las normas integradas,
  que no cambian, y sus subprogramas, y `AddAccis`, `modify_accis`, el código EMS (con su evidencia),
  `compute_setpoints`, la verificación, el paramétrico y la GUI las toman como las integradas; ejemplos de JPN Aqilah
  2025 y de Qatar (este, incompleto) y un cuaderno How-to (sección 16).
- **B4.** JPN Aqilah 2025 es la norma integrada 23 (`0,38·RMOT + 16,9`, de 5 a 30 °C, ±2,0 K (80) y ±1,5 K (90),
  estáticas de 20/28 °C, elección del usuario por D2), con su código al final de las cadenas, de modo que los IDF de
  las demás normas no cambian; los modelos con el código de todas las normas lo incluyen (sección 17).
- **C2.** Con `report_long_term_discomfort=True`, el EMS cuenta en cada paso de tiempo los indicadores de largo plazo
  de los métodos A y B de CEN/TR 16798-2 (horas ocupadas y grados-hora por encima de la consigna de refrigeración y por
  debajo de la de calefacción sin la tolerancia) de cada zona y del edificio, y el paramétrico los lee con los
  reductores `hours_outside_range` y `degree_hours`; `deviation_constraint_bound` da la cota de una restricción con la
  tabla E.1; el método C queda pendiente del autor (sección 18).
- **E4.** `morph_epws(engine='pyfwg')` ejecuta el Future Weather Generator global a través de pyfwg
  (`pyfwg.morph_epw_global`, versiones 3, 4 y 5 de la herramienta), con los mismos nombres de los EPW futuros que
  con Java (el motor por defecto, que no cambia); el extra `accim[weather]` instala pyfwg y pyweatherfiles; el
  cuaderno espera al jar de la herramienta (sección 19).
- **A4.** Las consignas del balance térmico adaptativo (ATHB): `apply_athb_setpoints` prepara un modelo con el
  ACCIS y devuelve un gancho del backend de la API de Python que, en cada paso, busca por bisección las temperaturas
  operativas cuyo ATHB_PMV (pythermalcomfort) es cada consigna y las da a los programas de consignas del ACCIS;
  `run_ep(..., hooks=[...])` solo con `backend='api'`; el extra `accim[comfort]` (sección 20).
- **A6.** Las consignas de la temperatura efectiva estándar (SET), con un gancho como el del ATHB que
  interpola una tabla de las consignas por humedad relativa (el SET de pythermalcomfort detiene EnergyPlus si se
  calcula en sus callbacks); las del PPD son las del PMV de `apply_pmv_setpoints` (sección 21).
- **D2, completada.** `Table` toma también las salidas opcionales del ACCIS y del ATHB (`Tout_metric`,
  `CustomRegime_<zona>`, `HoursBelow_<T>_<zona>`, las horas y grados-hora de largo plazo de las zonas y del edificio y
  `ATHB_PMV/clo/met_<zona>`): las promedia o les aplica `frequency_agg_func`, las conserva con
  `standard_outputs=True`, les da nombres de `Table` y valores de bloque y de edificio (sección 22).
- **G1 (revisión v04).** Los ganchos del ATHB y de la SET se ejecutan antes de los programas del EMS y dan sus
  consignas al ACCIS con el programa `ApplyHookSetpoints_<zona>`, justo después de SetAST: la tolerancia, el redondeo,
  el suelo y el techo, los contadores de horas (también los de largo plazo) y las salidas de las consignas de cada zona
  son ya los del gancho (sección 23).
- **G2 (revisión v04).** `energyplus_running_means` y `compute_setpoints` reproducen la PMOT de EnergyPlus con un
  periodo que empieza del 2 al 30 de enero (la media del 31 de diciembre en lugar de la del día anterior durante 30
  días), y la verificación avisa de un .stat junto al EPW (sección 24).
- **G3 (revisión v04).** El gancho de la SET calcula por bisección en los callbacks si se pide (`method='bisection'`),
  con la salida `SET_<zona>`, tras llamar a pythermalcomfort antes de cargar la API de EnergyPlus; pide las salidas de
  temperaturas y humedad de las zonas (`set_of_results`) y se sienta por defecto con 1,2 met o menos (sección 25).
- **G4 (revisión v04).** Con el archivo climático de la simulación, JPN Aqilah 2025 (23) usa la media móvil de
  EN 16798-1 con α 0,8 que calcula el EMS desde el archivo (sus consignas son las de su gemelo YAML 101 desde el
  primer día), y sin él lee el RMOT de EnergyPlus con un aviso; sus consignas estáticas son los argumentos
  `static_heating_setpoint` y `static_cooling_setpoint` (20 y 28 °C), entradas `StaticAHST` y `StaticACST` de sus zonas
  (sección 26).
- **G5 (revisión v04).** Saneamiento: `adaptive_coefficients=<clave>` da los dos λ de una entrada del catálogo y una
  clave con el número por defecto en el otro lado avisa; con `'pmv_sign'` se comprueban los signos de las consignas;
  el suelo y el techo acotan también las consignas sin tolerancia y son exactos tras el redondeo, con aviso si cruzan
  los límites de aplicabilidad (aviso sustituido en S1, sección 38); un formateador único de los números de los
  programas; el YAML de Qatar completo (102)
  carga; las categorías en orden numérico y aviso por los signos de los offsets; `fwg_add_uhi=False` con pyfwg, aviso
  con `fwg_options_ensemble=0` y limpieza tras un `ValueError`; `run_ep(processes=0)` en el proceso actual; pruebas
  que se saltan sin besos (sección 27).
- **H1 (revisión v04).** El suelo y el techo de las consignas se llaman ahora `heating_setpoint_minimum` y
  `cooling_setpoint_maximum` (entradas EMS `AHSTmin` y `ACSTmax`, parámetros `HeatingSetpointMinimum` y
  `CoolingSetpointMaximum`); los nombres anteriores funcionan como alias obsoletos (sección 28).
- **E-F1 (bloque F).** `add_thermal_comfort_model` añade el modelo Pierce a los objetos People; en un año del modelo de
  ejemplo, el SET de pythermalcomfort queda 0,045 K por debajo del de EnergyPlus de media (máximo 0,20 K) de pie y
  0,116 K (máximo 0,34 K) sentado (sección 29).
- **F1 (bloque F).** El estándar de confort 24, INT Sun2026 SET (el modelo causal de Sun, Brager y Schiavon, 2026:
  TSV = 0,11·SET − 2,6), es un gancho del SET por bisección con las entradas de los objetos People y la temperatura
  radiante media de la zona (`apply_sun2026_setpoints`); no tiene código EMS (sección 30).
- **F2 (bloque F).** El limitador de la deriva de las consignas por la historia térmica interior (`drift_mode`
  'rate' o 'window', con `max_drift_rate`, `alpha_indoor`, `delta_cool`, `delta_heat` e `initial_T_rm_in`), en Erl y
  solo en las zonas que lo piden (sección 31).
- **F3 (bloque F).** Los indicadores de la adaptación al clima interior (`Table(indoor_adaptation_indicators=True)`:
  horas en la banda causal del SET, sobreenfriamiento, T_rm_in y Tn_exp, efecto de enfriamiento) y las salidas de los
  modelos de confort de EnergyPlus (`add_thermal_comfort_outputs`), con su nombre en `Table` (sección 32).
- **H2.** T0 de `te_ref_nl` es la media de la máxima y la mínima del día completo: con el EPW, un `Schedule:File`
  (`accim.sim.schedule_files`) leído por un sensor; sin él, la del día anterior, con aviso (sección 33).
- **H3.** El disconfort de largo plazo admite un rango constante (`long_term_range=('en16798', categoría[, tipo de
  edificio])`, los límites de la tabla B.2 de EN 16798-1); las consignas basadas en el PMV cuentan el método C, las
  horas ponderadas por el PPD (`report_ppd_weighted_hours`, salida `PPD Weighted Hours_<zona>`), y el reductor
  `ppd_weighted_hours` las lee; el método C de D1 sigue el texto literal (veredicto #20); `Table` con
  `source_frequency='timestep'` conserva las salidas y agrupa los pasos en su hora (sección 34).
- **H4.** El gancho del ATHB informa de las consignas en los límites de `temperature_range` (salida
  `ATHB_saturated_<zona>` y aviso al final de la simulación), sus salidas tienen por defecto las frecuencias del modelo,
  `met` debe ser mayor que 0 y avisa fuera de 0,8–4 met y por encima de 1 m/s (sección 35).
- **H5.** Cada régimen del modelo personalizado puede tener su propia métrica exterior (`outdoor_metric`, `alpha` y
  `days` de `CustomRegime`), y una norma de confort definida por sus datos puede tener varios regímenes (clave
  `regimes` de los YAML), con el programa de los regímenes del modelo personalizado; la documentación explica el
  `CustomRegime_<zona>` promediado y la alternancia con `'hvac_off'`/`'hvac_on'` (sección 36).
- **H6.** La vestimenta puede ser una función de una temperatura exterior del EPW
  (`set_pmv_input_parameters(clothing_insulation=función, epw=..., clothing_outdoor_metric='RMOT')`), escrita como un
  `Schedule:File`; `read_epw_dry_bulb` lee los EPW como Latin-1 (sección 37).
- **S1 (tercera sesión, decisión 19).** El aviso del mínimo y el máximo de las consignas ya no los compara con
  `ACSTaul`/`AHSTall` (límites de aplicabilidad de la métrica exterior, no consignas): con el EPW, compara cada zona
  con las consignas de su modelo de confort de `compute_setpoints`, paso a paso en el periodo de simulación, y da un
  aviso por zona con el límite, la consigna extrema, el número de días y el primero (sección 38).
- **S2 (tercera sesión, decisión 20).** Las consignas estáticas del YAML de Qatar (102) son 20 y 26 °C, las de las
  oficinas de la categoría II de la tabla B.2 de EN 16798-1 (25,5 °C era la de refrigeración de la categoría I)
  (sección 39).
- **S3 (tercera sesión, decisión 13).** El estado del modo `'rate'` del limitador de la deriva es la media de las
  consignas aplicadas en los pasos ocupados del último día con ocupantes, no la consigna del último paso del día
  anterior (sección 40).
- **S4 (tercera sesión, decisión 9, provisional).** `table_indicators` del módulo de los indicadores de la adaptación
  interior da también, con `pythermalcomfort_set` (desactivado por defecto), los indicadores de la banda causal con el
  SET de pythermalcomfort, en columnas con el sufijo `_pythermalcomfort` (sección 41).
- **S5 (tercera sesión, decisiones 1, 7, 16 y 22).** Documentación y pruebas de las notas de cuatro decisiones
  aceptadas: un ejemplo de vestimenta con la temperatura de las 6:00, la ruta absoluta de los CSV de los
  `Schedule:File`, los modos 0 y 3 del estándar 24 y el retraso de un día de las medias móviles de EnergyPlus en el
  primer paso de cada día (sección 42).
- **Correcciones de la autoauditoría de la sesión 2 (tercera sesión).** Los hallazgos A1–A26 de
  `notes/attachments/autoauditoria_sesion2_v1.2.0.json` corregidos sin decisión del autor, uno por commit (sección 43).
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
que accim no tenía entonces (hechas al final, sección 22).

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

## 12. El suelo y el techo de las consignas, y las horas por debajo de unas temperaturas (B5)

La propuesta B5 pide los argumentos `heating_setpoint_floor` (clave `AHSTfloor`) y `cooling_setpoint_ceiling`
(`ACSTceil`) de `AddAccis`, `None` por defecto, aplicados en todas las normas y modos de confort como las últimas
líneas de `SetAST` antes de `ROUNDING` (`if AHST < AHSTfloor; set AHST = AHSTfloor` y `if ACST > ACSTceil; set ACST =
ACSTceil`); la constante `EN16798_TABLE_B2` con el mínimo de calefacción y el máximo de refrigeración por tipo de
edificio y categoría (residencial I–IV: 21,0/25,5, 20,0/26,0, 18,0/27,0, 16,0/28,0; oficina I–IV: 21,0/25,5,
20,0/26,0, 19,0/27,0, 18,0/28,0); la lista opcional `report_hours_below` con los contadores `HoursBelow_<T>_<zona>`;
las clases `HeatingSetpointFloor` y `CoolingSetpointCeiling` del paramétrico; y pruebas en una semana de invierno y
otra de verano. La decisión D5 del brief: no se aplican a las consignas basadas en el PMV (se documenta). Los valores
de la tabla B.2 se han comprobado en UNE-EN 16798-1:2020 (página 49): la tabla está en B.2.1 (edificios con
refrigeración mecánica) y B.2.2 (edificios sin ella, el modelo adaptativo) dice que «durante la estación de invierno,
deben aplicarse los mismos límites de temperatura que los mostrados en la tabla B.2» (página 51); la tabla supone
~1,0 clo en invierno, ~0,5 clo en verano y ~1,2 met.

**Antes.** Los límites de aplicabilidad de cada norma cambian la ecuación de las consignas (modos 1, 2 y 3), pero
nada las acotaba: con el modo 3 de INT EN16798, categoría II, la consigna de calefacción de Sevilla en enero es de unos
18 °C, por debajo de los 20 °C de la tabla B.2.

**Ahora.**

- `accim/sim/ems/setpoint_limits.py` (nuevo):
  - `INPUTS = ('AHSTfloor', 'ACSTceil')`, `PROGRAM_PREFIX = 'ApplySetpointLimits_'`, `HOURS_BELOW_PROGRAM_PREFIX =
    'CountHoursBelow_'`, `HOURS_BELOW_PREFIX = 'HoursBelow_'`.
  - `check_setpoint_limits(suelo, techo, where)` (números o `None`, y suelo < techo), `check_hours_below` (lista de
    números distintos; `None` o `[]`, ninguna), `hours_below_variable(T, zona)` (`HoursBelow_17p5_<zona>` para 17,5, y
    `m` por el signo menos: los nombres del EMS no admiten puntos).
  - `limit_program_lines(suelo, techo)`: las líneas de `ApplySetpointLimits_<zona>`, que acotan `AHST` y `ACST` y
    repiten `ROUNDING`.
  - `set_setpoint_limits_code(idf)`: escribe, actualiza o quita `ApplySetpointLimits_<zona>` según las entradas de cada
    `SetInputData_<zona>`, con la línea `run ApplySetpointLimits_<zona>` justo después de `run SetAST` en
    `RunACCIS_<zona>`, y declara `AHSTfloor` y `ACSTceil` (un objeto `EnergyManagementSystem:GlobalVariable`) si alguna
    zona los tiene. `has_setpoint_limits`, `zone_limits`.
  - `hours_below_lines(zona, T)` y `set_hours_below_code(idf, T, frecuencias)`: el programa `CountHoursBelow_<zona>`
    (`if Occ_count_<zona> > 0` y `if <zona>_OpT < T` → `1*ZoneTimeStep`, como `COUNT_HOURS_NO_APP`), que
    `RunACCIS_<zona>` ejecuta tras `CountHoursNoApp_<zona>`, las variables globales y las salidas EMS `Summed` en
    horas.
- `accim/constants.py`: `EN16798_TABLE_B2`, con los valores de la v03, comprobados en la norma.
- `accim/sim/ems/inputs.py`: `InputVariable.optional`; las entradas opcionales `AHSTfloor` y `ACSTceil` (tras
  `CustAST_days`), que `input_lines` solo escribe si tienen valor, así que los IDF sin ellas no cambian.
  `ZONE_ARGUMENTS` las incluye.
- `accim/sim/generation.py`: `GenerationArguments` tiene `heating_setpoint_floor` y `cooling_setpoint_ceiling`.
- `accim/sim/accis.py`: `AddAccis` tiene los tres argumentos al final de la firma (`_check_setpoint_limits`, también
  por zona; `ValueError` con `setpoint_type='pmv'`, D5; los prompts no los preguntan, `_NOT_ASKED_ARGUMENTS`);
  `set_hours_below_code` antes de las salidas (las salidas estándar y detalladas toman todas las salidas EMS; con
  `'simplified'`, `_add_hours_below_outputs` añade las suyas); `_write_output_idfs` llama a
  `set_setpoint_limits_code` tras `set_combination`. `modify_accis` tiene el suelo y el techo al final, `None` por
  defecto (conservan los de cada zona), y añade las líneas que falten; los modelos de versiones anteriores no los
  admiten.
- `accim/sim/ems/programs.py`: `set_comfort_standard_code` añade primero el código de la métrica exterior de B1 y
  después escribe los programas de las normas, para que los subprogramas `SetAST_CS<n>_<k>` sean siempre los últimos
  programas del modelo y el orden de los programas sea el mismo en todos los IDF de salida (antes, la métrica iba al
  final; solo afecta a los IDF de 99 con una métrica distinta de `'pmot'`, que son nuevos en 1.2.0).
- `accim/utils/ems_code.py`: `get_setpoint_ems_code` y `get_setpoint_ems_programs` toman el suelo y el techo y dan las
  entradas y el programa `ApplySetpointLimits_<zone>` antes de `SetASTnoTol`, con una leyenda. `accim/sim/preview.py`:
  `compute_setpoints` ejecuta ese programa justo después de `SetAST`. `accim/utils/verification.py`: la comprobación 5
  (`Check5_AHSTfloor`, `Check5_ACSTceil`); la 4 ya compara las consignas acotadas, porque toma las entradas de cada
  zona.
- Paramétrico: `param_accis.modify_AHSTfloor` y `modify_ACSTceil` (todas las zonas, con la comprobación del suelo
  frente al techo de cada zona), las clases `HeatingSetpointFloor` y `CoolingSetpointCeiling` de `parameters.py`, y
  los parámetros `heating_setpoint_floor` y `cooling_setpoint_ceiling` de los modelos predefinidos y personalizados
  (`params_dicts`, y las tuplas de la GUI, que deben coincidir).
- GUI: un marco nuevo en *Add the ACCIS* con una lista de los valores de la tabla B.2, que rellena el suelo y el techo
  (vacíos: ninguno; desactivados con las consignas del PMV) y las temperaturas de `report_hours_below`;
  `forms.setpoint_limit_arguments`, `SETPOINT_LIMIT_FIELDS`, `EN16798_TABLE_B2_CHOICES`; el código EMS de la GUI
  incluye el suelo y el techo, también los de cada zona.
- Desviaciones de la v03: las líneas no están al final de los subprogramas de `SetAST`, sino en un programa de cada
  zona que se ejecuta justo después de `SetAST`, acota `AHST` y `ACST` y repite `ROUNDING`: como `ROUNDING` lee `ACST`
  y `AHST` sin redondear y escribe `roundedACST` y `roundedAHST`, el resultado es exactamente el de acotar antes del
  redondeo (comprobado con el intérprete en un año: las consignas son las de acotar y redondear con las fórmulas de
  `ROUNDING`), los subprogramas compartidos no cambian y no hace falta un valor centinela para las zonas sin suelo ni
  techo (una variable nula detiene EnergyPlus); las clases del paramétrico llevan los nombres de la v03, no el nombre
  de la variable EMS como las demás (`ASTtol`...); y los parámetros se registran ya en el paramétrico (C1 añadirá los
  demás).
- Pruebas: `tests/core/test_setpoint_limits.py` (20: la tabla B.2; las comprobaciones y los nombres; las líneas; los
  contadores con el intérprete; con `compute_setpoints`, un semestre con suelo y techo (INT EN16798), solo suelo (INT
  ASHRAE55) y solo techo (ESP CTE, consignas estáticas): las consignas son las de acotar antes de redondear, y las demás
  columnas no cambian; el código EMS; AddAccis: con `None` los IDF son idénticos a los de antes, y con suelo y techo
  solo cambian las entradas, las líneas de `RunACCIS_<zona>`, los programas nuevos y las variables globales; suelo de
  una zona; los errores; las horas por debajo con salidas estándar y simplificadas, y con `'pmv'`; `modify_accis` y el
  paramétrico; los modelos de 0.x; EnergyPlus 25.1: una semana de invierno (1–7/01) y otra de verano (15–21/07) por
  paso de tiempo con suelo 20, techo 26 y horas por debajo de 26, 25 y 24,5 °C: comprobaciones 4 y 5 sin
  discrepancias, el suelo actúa en todos los pasos de invierno y el techo (25,9999 °C) en más del 90 % de los de verano,
  y los contadores son exactamente la duración del paso cuando la zona tiene ocupantes y su temperatura operativa del
  paso anterior está por debajo, decrecientes con T; y los dos backends idénticos) y
  `tests/parametric_and_optimisation/test_setpoint_limit_parameters.py` (2).
- Comparaciones con EnergyPlus 25.1 (fuera del repositorio): con la temperatura operativa del paso actual en lugar de
  la del anterior, los contadores difieren en 5 a 8 pasos por semana, así que el EMS lee la del paso anterior. Backends
  (`run_ep(backend='ems')` frente a `'api'`, las dos semanas por paso de tiempo): 1008 filas y 108 columnas idénticas
  (diferencia máxima 0,0, también en las 18 columnas de las consignas y los contadores), 5,7 s frente a 7,0 s y 4,1 s
  frente a 6,5 s.
- Hallazgo: con un periodo que empieza el 8 de enero, el PMOT de `energyplus_running_means` (E1) es 0,142361 °C mayor
  que el de EnergyPlus todos los días de la semana (`TODO.md`); con el 1 de enero y el 15 de julio, coinciden.

## 13. Los parámetros de los ocupantes, de los índices nuevos y del modelo personalizado en el paramétrico (C1)

La propuesta C1 pide las clases `Clo`, `Met`, `AirVelocity` (con `set_pmv_input_parameters`), `ExpectancyFactor`,
`HeatingSetpointFloor`, `CoolingSetpointCeiling`, `CustAST_metric`, `CustAST_alpha` y `CustAST_days`, con avisos
fuera de los rangos de ISO 7730:2025 §4 (0,8–4 met, 0–2 clo, 0–1 m/s) y de ASHRAE 55 (≤ 1,5 clo), registradas en
`params_dicts.py` y en `get_available_params_apmv_setpoints()`/`get_available_params_accim_custom_models()`, y una
prueba con un diseño de dos puntos de `Clo` que compruebe la schedule de vestimenta de los IDF generados. El brief
cambia `clo`/`met` por `clothing_insulation`/`activity_level` y señala `get_available_params_epmv_setpoints()` como
patrón. Los rangos se han comprobado en ISO 7730:2025 (§4, página 3 de la norma: «M 46 W/m² a 232 W/m² (0,8 met a
4 met); Icl 0 a 0,310 m²·K/W (0 clo a 2 clo)... var 0 m/s a 1 m/s», y el área corporal media A_Du = 1,8 m²) y en la
Engineering Reference 25.2 de EnergyPlus (§19.1: «this average person area of 1.8 m² is used for the body surface
area [in] all thermal comfort models»; 1 met = 58,2 W/m²).

**Antes.** El paramétrico tenía las consignas del aPMV y del ePMV, pero no las entradas del PMV de los ocupantes;
B1 y B5 no tenían parámetros (los de B5 se registraron con B5).

**Ahora.**

- `accim/constants.py`: `PMV_BODY_SURFACE_AREA` (1,8 m²), `PMV_INPUT_RANGES` (la actividad en W/persona, 46–232 W/m²
  por 1,8 m² = 82,8–417,6 W/persona, como el *Activity Level* de las People de EnergyPlus; 0–2 clo; 0–1 m/s) y
  `ASHRAE55_MAX_CLOTHING_INSULATION` (1,5 clo, v03 §11.3).
- `funcs_for_besos/param_apmv.py`: `change_clothing_insulation_all_zones`, `change_activity_level_all_zones` y
  `change_air_velocity_all_zones` (llaman a `set_pmv_input_parameters` con `verbose=False`; `_check_pmv_input` avisa
  fuera de los rangos y da `ValueError` con un valor negativo o que no es un número).
- `funcs_for_besos/param_accis.py`: `modify_CustAST_metric` (el nombre o el código de la métrica; las opciones del
  paramétrico son números), `modify_CustAST_alpha` y `modify_CustAST_days` (redondeado al día entero), con
  `_set_outdoor_metric_input`: comprueba los valores de cada zona (los avisos de D7), escribe la entrada (añadiendo la
  línea que falte) y llama a `set_outdoor_metric_code` si el modelo necesita el código de la métrica o lo tiene. Los
  programas del modelo se conservan si pueden (con los valores del EPW, si `modify_accis` recibió `epw` antes del
  estudio); si no, empiezan con PMOT (aviso) y `'monthly_mean'` da `ValueError`. Con `'pmot'` y sin código, las
  entradas se quedan en `SetInputData_<zona>` como variables locales de Erl (la guía del EMS: las variables no
  declaradas son locales), para que `custom_alpha` o `custom_days` aplicados antes que `custom_outdoor_metric` en una
  muestra se conserven: sin esto, el α de la muestra se perdía al quitar las entradas.
  `drop_invalid_param_combinations` quita las filas con suelo ≥ techo.
- `params_dicts.py`: `clothing_insulation`, `activity_level` y `air_velocity` en `apmv_setpoints_params` y
  `epmv_setpoints_params`; `custom_outdoor_metric`, `custom_alpha` y `custom_days` en `accim_custom_model_params` (y en
  la tupla de la GUI). `main.py`: `sampling_full_set()` aplica `drop_invalid_param_combinations` también a los modelos
  personalizados.
- `parameters.py`: las clases `Clo`, `Met`, `AirVelocity`, `ExpectancyFactor`, `AdaptiveCoefficientCooling`,
  `AdaptiveCoefficientHeating`, `CustAST_metric`, `CustAST_alpha` y `CustAST_days` (las de B5 ya estaban).
- Desviaciones de la v03: los nombres de los parámetros son los de los argumentos de accim (`clothing_insulation`,
  `activity_level` en W/persona, `air_velocity`, `custom_outdoor_metric`...), como pide el brief; el rango de la
  actividad se da en W/persona; las entradas del PMV no son parámetros de los modelos de accim (consignas de
  temperatura); se añaden `AdaptiveCoefficientCooling` y `AdaptiveCoefficientHeating`, que la tabla de la v03 pide si
  no existían; la fábrica `custom_regime_parameters(n)` espera a B2 (`TODO.md`).
- Pruebas: `tests/parametric_and_optimisation/test_pmv_and_metric_parameters.py` (8: el registro y las clases; los
  rangos y sus avisos; los planes sin suelo ≥ techo, también de los modelos personalizados; los modificadores de las
  entradas del PMV en el modelo de ejemplo con el aPMV; el diseño de dos puntos de `clothing_insulation` con
  `sampling_full_set()` y `EvaluatorEP.generate_building` de besos, sin simular: cada IDF tiene sus `Sch_Clo_<people>`
  con su valor; los modificadores de la métrica, en el orden de una muestra, con el redondeo de los días, el anillo de
  45 días, los avisos y los errores; la métrica conserva el EPW de `modify_accis`; los modelos de 0.x), y las listas
  de `test_epmv_parameters.py` y `test_legacy_names.py`.

## 14. Los indicadores de disconfort de largo plazo (D1)

La propuesta D1 pide un módulo de funciones puras de pandas con los métodos del anexo D de CEN/TR 16798-2:2019
(A: horas y % de horas ocupadas fuera del rango; B: grados-hora; C: ponderado por el PPD), `ppd_from_pmv` (ISO 7730),
`deviation_check` (anexo E, tabla E.1) y `hours_below`, y la opción `long_term_indicators=True` de `Table` por zona y
edificio "para los periodos cálido y frío", con `ACSTnoTol`/`AHSTnoTol` como límites por defecto. La decisión D8 del
brief cambia las pruebas: no reproducir la tabla D.1 (necesita calcular el PMV), comprobar los pesos del método B
analíticamente, el método C con el PPD de la fórmula, y `ppd_from_pmv` en 0, ±0,5 y ±1 con la fórmula. Comprobado en
UNE-CEN/TR 16798-2:2019 (páginas 68 a 71: los métodos A, B y C con sus desigualdades, la tabla D.1 y la tabla E.1 con
el ejemplo de 126 h al año, 20 h a la semana y 44 h al mes al 6 %) y en ISO 7730:2025 (cláusula 5, fórmula (5)).

**Antes.** `Table` daba las horas de confort de las consignas de accim (los contadores del EMS), pero no los
indicadores de largo plazo de la norma.

**Ahora.**

- `accim/data/postprocessing/long_term_discomfort.py` (nuevo): `ppd_from_pmv`; `hours_outside_range` (método A:
  `hot_h`, `cold_h`, `hot_pct`, `cold_pct`, `occupied_h`; fuera del rango es por encima del superior o por debajo del
  inferior, con los límites dentro, como en el método B); `degree_hours` (método B: `hot_Kh`, `cold_Kh`);
  `ppd_weighted_hours` (método C: `hot_h`, `cold_h`; un PMV igual al límite superior, que el anexo D no pone en ningún
  caso, se toma como dentro); `deviation_check` y `DEVIATION_LIMITS` (los porcentajes de la tabla E.1, con niveles
  '3%' y '6%' por su porcentaje anual: 25 % de 175 h son 43,75 h, que la tabla redondea a 44 h); `hours_below`; y
  `table_indicators`, los de los métodos A y B de una tabla de `Table`. Las funciones toman Series (o arrays) de cada
  fila, la ocupación (`occupied`: None, booleanos o números como los ocupantes) y las horas de cada fila
  (`timestep_h`: un número o una Series), y dejan fuera las filas con valores ausentes.
- `accim/data/postprocessing/main.py`: `Table(..., long_term_indicators=False)` (al final de la firma; con `True`,
  `ValueError` si `frequency` no es 'timestep' u 'hourly'); al final del constructor, el atributo
  `long_term_indicators`, solo en las tablas que lo piden (así el JSON de las demás no cambia), con una fila por
  simulación (`Source` y las columnas que la describen) y `<zona>_Occupied Hours (h)`, `_Hours Above Upper Limit (h)`,
  `_Hours Below Lower Limit (h)`, sus porcentajes, `_Degree Hours Above Upper Limit (Kh)` y `_Degree Hours Below Lower
  Limit (Kh)` de cada zona y del edificio (`Building_`, la suma de las zonas). Los límites son las salidas EMS de las
  consignas sin tolerancia de cada zona, la temperatura es su temperatura operativa y el tiempo, sus horas ocupadas de
  cada fila (`Occupied Hours_<zona>`); `_JSON_ATTRIBUTES` la incluye.
- GUI: la casilla *Long-term discomfort indicators* de la pestaña *Table and figures* (`forms.TABLE_DEFAULTS`,
  `table_arguments`, que la exige con tablas horarias o por paso), y el registro muestra los indicadores.
- Desviaciones de la v03: las pruebas siguen D8, no la tabla D.1; `Table` da los métodos A y B (no el C, que necesita
  el PMV y sus límites, ni las desviaciones de la tabla E.1, que dependen del periodo) en un atributo con una fila por
  simulación, no como columnas de `Table.df` (cuyas filas son las horas); los periodos cálido y frío son los de la
  norma (por encima y por debajo del rango), no las estaciones (`notes/questions.md`).
- Pruebas: `tests/core/test_long_term_discomfort.py` (9: el PPD de la fórmula, calculado en la prueba; los pesos del
  método B de la tabla D.1 (3, 2, 1 y 1, 2, 3 K) con la ocupación, las horas de cada fila y límites de cada fila; el
  método A con ocupantes, valores ausentes y sin horas ocupadas; los pesos PPD del método C; las desviaciones de la
  tabla E.1 en las horas de trabajo; las horas por debajo; `Table` con un CSV inventado de dos zonas, con y sin
  `rename_cols`, frente al cálculo de cada zona y del edificio; sus errores, y que las demás tablas no tienen el
  atributo), y 2 de la GUI. Con el CSV por paso de tiempo de una simulación de B5, la tabla por paso coincide con el
  cálculo directo desde el CSV (zona 1: 60 h ocupadas, 25,1667 h por encima y 16,7978 K·h).
- Hallazgo: `Table` con `source_frequency='timestep'` y `standard_outputs=True` deja fuera todas las salidas
  (EnergyPlus escribe `(TimeStep)` y el filtro busca `Timestep`); en `TODO.md`.

## 15. Varios regímenes del modelo personalizado (B2)

La propuesta B2 pide la dataclass congelada `CustomRegime` en `accim/sim/arguments.py` (pendiente, ordenada en el
origen, compensaciones de refrigeración y calefacción, los cuatro límites de aplicabilidad, la condición y una
`outdoor_metric` opcional), el argumento `custom_regimes` de `AddAccis`, un programa Erl `SelectCustomRegime` con una
cadena `if/elseif` (el último régimen, 'always') que asigne los coeficientes del primer régimen cuya condición se
cumple sin cambiar `SetComfTemp`, `SetAppLimits`, `ApplyCAT` ni las líneas de las consignas de la norma 99, los
argumentos escalares `CustAST_*` como un régimen 'always' (prueba de regresión: el mismo IDF de salida), `ValueError`
para 'hvac_on'/'hvac_off' sin modo mixto, la fábrica `custom_regime_parameters(n)` del paramétrico y pruebas con dos
regímenes (`metric_below 10` y 'always') del texto Erl y de una semana simulada. La decisión D6 del brief fija la
prioridad: el orden de la lista; el primero que se cumple gana; el último es 'always' o accim añade uno con los
argumentos escalares.

**Antes.** El modelo personalizado tenía un solo juego de coeficientes: las entradas `m`, `n`, `CustAST_ACSToffset`,
`CustAST_AHSToffset`, `CustAST_ACSTall`, `CustAST_ACSTaul`, `CustAST_AHSTall` y `CustAST_AHSTaul` de
`SetInputData_<zona>`, que `SetAppLimits` y `ApplyCAT` copian en `ACSTall`... y `ACSToffset`... (con la compensación
de la categoría) y que `SetComfTemp` y `SetAST_CS99_*` usan.

**Ahora.**

- `accim/sim/arguments.py`: `CustomRegime` (congelada; `__post_init__` comprueba los ocho números, normaliza la
  condición a minúsculas y tuplas, para poder compararlas y usarlas como claves, y exige `outdoor_metric=None`),
  `REGIME_CONDITIONS`, `METRIC_CONDITIONS` y `check_custom_regimes` (lista de `CustomRegime`, o None; un régimen
  'always' que no es el último da `ValueError`, porque los siguientes no se aplicarían nunca). `accim.sim.CustomRegime`
  la importa sin cargar el resto.
- `accim/sim/ems/custom_regimes.py` (nuevo): `regime_program_lines` escribe el programa `SelectCustomRegime_<zona>`:
  `set CustomRegime_<zona> = 0` si el último no es 'always'; las líneas de la estación de refrigeración de
  `SetAST_Master` (`COOLING_SEASON_LINES`, que ponen `CoolingSeason` con el mismo valor que `SetAST_Master` le dará
  después) si alguna condición es de estación; las líneas con que `ApplyAST_<zona>` del modo mixto pone
  `NoH_NoC_reqs` (`program_lines.HVAC_OFF_FROM_COILS`, de las baterías del VRF de accim, o `HVAC_OFF_FROM_LOAD`, de la
  carga a las consignas del termostato con los sistemas existentes, públicas ahora) si alguna es del HVAC; y la cadena
  `if/elseif/else/endif`, que pone las ocho entradas del régimen y `CustomRegime_<zona>` (su número). Las condiciones:
  `CoolingSeason == 1` y `== 0`; `NoH_NoC_reqs == 1` y `== 0`; `PMOT < x`, `PMOT > x` y
  `(PMOT >= x1) && (PMOT <= x2)` (o `Tout_metric` con el código de B1). Los números se escriben sin exponente
  (`numpy.format_float_positional`). `set_custom_regimes` lo escribe en las zonas cuya norma es 99 y lo quita de las
  demás (con la línea `run SelectCustomRegime_<zona>` de `RunACCIS_<zona>`, justo antes de `run SetAppLimits`, la
  variable global y la salida EMS `CustomRegime_<zona>`, promediada y sin unidades, y sus `Output:Variable` a las
  frecuencias de las de la temperatura de confort de la zona); sin regímenes, el IDF queda como sin ellos.
  `custom_regimes_of` y `parse_regime_program` leen los regímenes de las líneas Erl, porque eppy pierde los
  comentarios de los programas al leer un IDF (comprobado). `hvac_off_lines` toma las líneas de `ApplyAST_<zona>`
  (None si no es modo mixto).
- `accim/sim/ems/outdoor_metric.py`: `_set_custom_model_lines` cambia también `PMOT` por `Tout_metric` (y al revés) en
  los programas `SelectCustomRegime_<zona>`, como en los demás del modelo personalizado.
- `accim/sim/accis.py`: `AddAccis(..., custom_regimes=None)` (al final): `ValueError` con `setpoint_type='pmv'`, con
  'hvac_off'/'hvac_on' sin `vrf_mm` ni `ex_mm`, y sin la norma 99 en los IDF de salida ni en `zone_arguments`;
  `_write_output_idfs` llama a `set_custom_regimes` en cada combinación, después de `set_setpoint_limits_code` y antes
  de `set_comfort_standard_code`. `modify_accis(..., custom_regimes=None)`: None conserva los regímenes, una lista los
  pone en las zonas con la norma 99 (también la de la misma llamada; si no hay ninguna, `ValueError` antes de cambiar
  nada) y una lista vacía los quita; los modelos de versiones anteriores solo tienen un régimen.
- `accim/utils/ems_code.py`: `get_setpoint_ems_code` y `get_setpoint_ems_programs` toman `custom_regimes` y
  `script_type` ('vrf_mm' o 'ex_mm', para las condiciones del HVAC); la sección `SelectCustomRegime_<zone>` va antes de
  `SetAppLimits`, con la lista de las condiciones en su título y una leyenda.
- `accim/sim/preview.py`: `compute_setpoints` ejecuta el programa de los regímenes antes de `SetAppLimits` y da la
  columna `custom_regime` (la media de la hora, como la salida); con 'hvac_off'/'hvac_on', `ValueError` (dependen del
  HVAC de la simulación).
- `accim/utils/verification.py`: la comprobación 4 pasa a `compute_setpoints` los regímenes de cada zona y compara
  `CustomRegime_<zona>` (`Check4_custom_regime`); las zonas con condiciones del HVAC quedan sin comprobar (en
  `TODO.md`).
- `accim/data/postprocessing/main.py`: `Table` promedia en el tiempo `EMS:CustomRegime` (`_AVERAGED_OUTPUTS`).
- Paramétrico: `param_accis.modify_custom_regime(idf, value, regime, field)` cambia un coeficiente de un régimen en
  todas las zonas que los tienen (conserva la condición); `params_dicts.custom_regime_parameter` y
  `custom_regime_modifier` (un `functools.partial`, que se puede enviar a otros procesos) para los parámetros
  `custom_regime_<régimen>_<campo>`, que `accis_parameter` construye y `set_parameters` acepta con los modelos
  personalizados; `parameters.CustomRegimeParameter` y `custom_regime_parameters(n)`, que devuelve las clases
  `CustAST_m_1`, `CustAST_n_1`, `CustAST_ACSToffset_1`, `CustAST_AHSToffset_1`, `CustAST_ACSTall_1`,
  `CustAST_ACSTaul_1`, `CustAST_AHSTall_1`, `CustAST_AHSTaul_1`, `CustAST_m_2`... Cierra la tarea de C1.
- GUI: el campo *Regimes (custom_regimes)* en el marco del modelo personalizado (`forms.parse_custom_regimes`,
  `custom_regime_arguments`, `CUSTOM_REGIMES_HINT`): un régimen por línea o separados por punto y coma,
  `condición: pendiente ordenada ...`; el código EMS de la ventana los incluye, con el tipo de script del formulario.
- Desviaciones de la v03 (en `notes/questions.md`, decididas provisionalmente): un programa por zona
  (`SelectCustomRegime_<zona>`, porque las condiciones del HVAC leen los sensores de la zona) en vez de uno solo; el
  programa escribe las entradas `m`, `n`, `CustAST_*` y no `ACSToffset`, `ACSTall`... (que `ApplyCAT` y `SetAppLimits`
  sobrescribirían); el régimen añadido de D6 son las entradas escalares de `SetInputData_<zona>` (sin `else`), no una
  copia congelada; la salida `CustomRegime_<zona>`, que la v03 no pide; `outdoor_metric` de cada régimen sin
  implementar (`ValueError` si no es None, tarea bloqueada en `TODO.md`); los mismos regímenes en todas las zonas del
  modelo personalizado; y la fábrica, con los ocho coeficientes de cada régimen, no los valores de las condiciones.
- Pruebas: `tests/core/test_custom_regimes.py` (20: la comprobación de los regímenes y de la lista; el texto Erl de
  dos regímenes (`metric_below 10` y 'always') y de las demás condiciones, y su lectura; el intérprete de Erl con los
  límites de las condiciones; `compute_setpoints` con dos regímenes, con las estaciones y sin 'always', con la métrica
  de B1 y con un solo régimen igual a los argumentos escalares (el mismo resultado); el código EMS; `AddAccis` (los IDF
  sin regímenes, y los de la otra norma, idénticos byte a byte), `zone_arguments`, la métrica de B1, los errores,
  `modify_accis` y `Table`; y tres con EnergyPlus 25.1), `tests/parametric_and_optimisation/test_custom_regime_parameters.py` (4,
  con un diseño de dos puntos de `custom_regime_1_slope` generado con `EvaluatorEP.generate_building`) y 2 de la GUI.
- EnergyPlus 25.1 (Sevilla): del 1 al 7 de abril, tres regímenes (`metric_below 16`, 'cooling_season' desde el 5 de
  abril y 'always'), por paso de tiempo: `verify_accim_simulation` sin discrepancias en la comprobación 4
  (`Check4_custom_regime`, `Check4_ACST`, `Check4_AHST`, `Check4_ComfTemp` de cada zona, 1008 pasos) y los tres
  regímenes en la semana; del 1 al 7 de junio en modo mixto (`vrf_mm`), 'hvac_off' y 'always': el régimen de cada paso
  es el 1 exactamente cuando las baterías de la zona estuvieron paradas el paso anterior, y las consignas son las de
  `compute_setpoints` del régimen de cada paso; y los backends `ems` y `api` (del 1 al 10 de abril, `vrf_mm`, horario,
  `metric_below 16`, 'hvac_off' y 'cooling_season') dan CSV idénticos (`check_exact=True`). Con `run_ep`
  (`backend='ems'` y `'api'`, por paso de tiempo), los modelos de abril (`vrf_ac`, 1008 filas × 102 columnas) y de junio
  (`vrf_mm`, 1008 × 113) tienen una diferencia máxima de 0,0 (ems 4,7 y 4,3 s; api 6,3 y 6,9 s). Suite completa: 1644
  pasan, 1 omitida; el golden master no cambia.

## 16. Las normas de confort definidas por sus datos (B3)

La propuesta B3 pide un registro de normas de confort en `accim/sim/standards.py`: `ComfortStandardDefinition`
(`standard`, `outdoor_metric`, `regimes`, `category_offsets` con compensaciones asimétricas, `static_setpoints`,
`evidence` y `citation`), `register_comfort_standard()` y `load_comfort_standards(yaml_path)` con el esquema YAML de
la propuesta (con mensajes de error claros); que `program_lines.py` (`SET_COMF_TEMP`, `SET_APP_LIMITS`, `APPLY_CAT`,
`COUNT_HOURS`) y `setpoint_lines.py` construyan su Erl desde el registro para los números ≥ 100, mientras las normas
0–22 y 99 conservan sus líneas literales (prueba de regresión: los IDF de salida de los modelos de ejemplo, idénticos
byte a byte); los archivos `accim/sample_files/comfort_standards/jpn_aqilah2025_fr.yaml` y
`qat_indraganti2018_hvac.yaml` con los datos de la propuesta; un cuaderno How-to; las listas de la GUI desde el
registro; `print_setpoint_ems_code` con el bloque `evidence`; la documentación, `CHANGELOG.md` y `DEVLOG.md`. Las
decisiones D1 (el 23 es para JPN Aqilah 2025 integrada, B4; los números ≥ 100, para las normas de YAML) y D11 (los dos
ejemplos de la v03; el bloque `evidence`, obligatorio) del brief la completan.

**Antes.** Una norma nueva exigía tocar `standards.py` (`COMFORT_STANDARDS`), las cadenas `if ComfStand == ...` de
`program_lines.py` (`SET_COMF_TEMP`, `SET_APP_LIMITS`, `APPLY_CAT`, `COUNT_HOURS`, `SET_VST`), las líneas de sus
modos de confort en `setpoint_lines.py` (`SETPOINT_LINES`) y `MODULAR_COMFORT_MODES` de `setast.py`, y publicar una
versión.

**Ahora.**

- `accim/sim/standards.py`: `FIRST_REGISTRY_NUMBER = 100`, `DEFINITION_COMFORT_MODES = (0, 1, 2, 3)`;
  `ComfortStandardDefinition` (congelada; `__post_init__` comprueba el número, la etiqueta, que da nombre a los IDF de
  salida y no puede llevar `[]\/:*?"<>|`, la métrica (con `alpha` y `days`, campos añadidos), un solo régimen
  `'always'`, las compensaciones de cada categoría, las consignas estáticas que piden los modos 0 y 1 (calefacción
  menor que refrigeración), el modo 2 solo con las categorías 80 y 90, la evidencia no vacía y la cita);
  `definition_from_mapping` (las claves de los YAML: `number`, `label`, `title`, `citation`, `outdoor_metric`,
  `comfort_temperature`, `applicability`, `categories`, `comfort_modes`, `evidence`; opcionales `alpha`, `days`,
  `static_setpoints`; los mensajes nombran el archivo y la clave); `register_comfort_standard(definition,
  replace=False)` (`ValueError` con un número < 100, uno ya registrado sin `replace` o la etiqueta de otra norma),
  `unregister_comfort_standard`, `registered_comfort_standards`, `comfort_standard_definition`; y
  `load_comfort_standards(path, register=True, replace=False)` (un archivo o una carpeta; importa `yaml` solo al usarse,
  con un `ImportError` que dice cómo instalarlo; nada de un archivo o carpeta que no es válido se registra). También
  `accim.sim.load_comfort_standards`, `register_comfort_standard` y `ComfortStandardDefinition`. `setup.py` pide
  `pyyaml` (besos ya lo instalaba).
- `accim/sim/ems/standard_lines.py` (nuevo): `standard_branches` escribe las ramas `elseif ComfStand == <n>` de
  `SetComfTemp` (`<métrica>*<pendiente>+<ordenada>`; con pendiente negativa, `<ordenada>-<métrica>*<-pendiente>`,
  porque Erl no admite un signo menos tras un signo de multiplicar, ni entre paréntesis: lo comprobó el intérprete de
  Erl de accim, que reproduce el error de EnergyPlus), `SetAppLimits`, `ApplyCAT` (las compensaciones de las
  categorías más las del régimen, y `CATcoolOffset`/`CATheatOffset`) y, si la métrica no es PMOT, `CountHours` y
  `SetVST`; `setpoint_lines`, las de sus modos de confort, como las de las normas integradas (el modo 2, con las
  consignas estáticas de ISO 7730 del código, `ISO7730_STATIC_SETPOINTS`: con la métrica PMOT y los coeficientes de
  ASHRAE 55 dan exactamente `SETPOINT_LINES[(2, 2)]`, y el modo 3 con los de JPN Rijal, `SETPOINT_LINES[(3, 3)]`);
  `add_standard_lines` y `remove_standard_lines` las ponen y quitan de `REGISTERED_BRANCHES`, `SETPOINT_LINES` y
  `MODULAR_COMFORT_MODES`; `metric_variable` (PMOT, RMOT o `Tout_metric`), `needs_outdoor_metric_code`,
  `outdoor_metric_standards` y `standard_inputs` (las entradas `CustAST_metric`, `CustAST_alpha` y `CustAST_days` de las
  zonas de la norma: las de su métrica si la calcula el EMS, y 'pmot' si no).
- `accim/sim/ems/program_lines.py`: `REGISTERED_BRANCHES` y las funciones `set_comf_temp_lines`,
  `set_app_limits_lines`, `apply_cat_lines`, `count_hours_lines` y `set_vst_lines` (las cadenas literales con las ramas
  del registro al final: antes del último `endif` o del `else`; en `SetVST`, antes de la rama genérica de PMOT), y
  `registered_standards_in`. Sin normas registradas devuelven las constantes de siempre.
- `accim/sim/ems/programs.py`: `set_comfort_standard_code`, `code_comfort_standards` y `accis_programs` usan esas
  funciones; `_set_vst_registered_branches` deja en `SetVST` las ramas de las normas del IDF; `add_comfort_standard_code`
  toma `epw` (así `modify_accis` con `epw` ya no avisa de que la métrica empieza con PMOT antes de escribirla con el
  EPW).
- `accim/sim/ems/outdoor_metric.py`: `metric_comfort_standards()` (99 y las registradas cuya métrica calcula el EMS),
  y `_set_custom_model_lines` respeta las ramas del registro en `CountHours` y `SetVST`.
- `accim/sim/ems/inputs.py`: `input_values` da a las zonas de una norma registrada las entradas de su métrica.
  `accim/sim/accis.py`: `modify_accis` se las da también a las zonas que la conservan, y escribe el código EMS de la
  métrica cuando alguna zona lo necesita. `accim/sim/generation.py`: las categorías y modos de las registradas.
- `accim/utils/ems_code.py`: la cabecera del código EMS da la cita, la métrica, las consignas estáticas y la
  evidencia (`_definition_lines`), y el código, los programas de la métrica (con `epw`, empezando con el EPW).
  `accim/sim/preview.py` (`compute_setpoints`) y `accim/utils/verification.py` (comprobación 4, también
  `Check4_Tout_metric`) funcionan con ellas.
- Paramétrico: `param_accis.modify_ComfStand` da a las zonas la métrica de la norma registrada (`_set_outdoor_metric_inputs`);
  `get_valid_param_combinations` y `drop_invalid_param_combinations` incluyen sus categorías y modos; y los procesos de
  las simulaciones en paralelo, que no tienen el registro del proceso principal, lo reciben: `run_parametric_simulation`
  pasa las definiciones a `_run_single_evaluation_worker` (`comfort_standards`) y `run_optimisation` las deja en el
  evaluador (`_accim_comfort_standards`), que `_patched_eval_func` registra (`patches._register_comfort_standards`).
- GUI: el botón *Load comfort standards (YAML)...* de la pestaña *1. Add the ACCIS* (`tasks.load_comfort_standards`,
  con `replace=True`; los errores, en un diálogo) y `refresh_standards`, que rehace la lista (conservando la selección)
  y las opciones de la tabla de zonas; el EPW se habilita con las normas registradas cuya métrica calcula el EMS
  (`forms.registered_metric_standards`, `weather_file_arguments`), también para el código EMS de la ventana; la
  sesión guarda los YAML cargados (`comfort_standard_files`) y, al abrirla, los carga de nuevo y lista los que no
  encuentra y las normas que siguen sin registrar.
- Ejemplos: `accim/sample_files/comfort_standards/jpn_aqilah2025_fr.yaml` (101, con los datos de la v03: métrica
  `rmot_alpha` con α 0,8, `Tc = 0,38·Trm + 16,9`, aplicabilidad de 5 a 30 °C, ±1,5 K (90 %) y ±2,0 K (80 %), modos 0 a
  3, consignas estáticas 20/28 °C de D2 y la evidencia) y `qat_indraganti2018_hvac.yaml` (102, con la ecuación, la
  cita y la evidencia de la v03, y vacías la métrica, la aplicabilidad, las categorías y los modos, que la v03 no da:
  `load_comfort_standards` lo rechaza; tarea bloqueada en `TODO.md`). El cuaderno How-to
  `jupyter_notebooks/comfort_standards_registry/using_comfort_standard_registry.ipynb` (con copias del modelo, el EPW
  y los dos YAML) registra JPN Aqilah 2025, muestra el rechazo de Qatar y el código EMS con la evidencia, compara sus
  consignas con las de JPN Rijal (3) sin EnergyPlus, simula un año con las dos (EnergyPlus 25.1, `vrf_mm`) y lo
  verifica (comprobación 4 sin discrepancias en 8760 horas, también `Tout_metric`); su página está en las How-to
  Guides.
- Desviaciones de la v03 (en `notes/questions.md`, decididas provisionalmente): un solo régimen `'always'` por norma;
  el modo 2 solo con las categorías 80 y 90, con las consignas de ISO 7730 del código; las métricas que calcula el EMS,
  a través de las entradas de la zona del modelo personalizado (una zona las conserva si `modify_accis` le da otra
  norma); `load_comfort_standards` registra por defecto; el YAML de Qatar, incompleto; y, además de lo que pide el
  prompt, las ramas de `SetVST`, los campos `alpha` y `days`, el paramétrico y sus procesos en paralelo.
- Pruebas: `tests/core/test_comfort_standard_registry.py` (los dos YAML; el esquema, con 22 errores; las definiciones;
  la carga de archivos y carpetas; el registro; las líneas Erl, también con pendiente negativa en el intérprete; que
  las cadenas de las normas integradas no cambian y su código EMS tampoco; la evidencia; `compute_setpoints` frente a
  la fórmula y en los cuatro modos fuera de los límites; `AddAccis`, cuyos IDF de la norma 1 son idénticos byte a byte
  con y sin el registro; `modify_accis`; dos con EnergyPlus 25.1: la comprobación 4 y los dos backends),
  `tests/parametric_and_optimisation/test_registered_comfort_standards.py` (combinaciones válidas, los procesos de las
  simulaciones en paralelo y de la optimización, `modify_ComfStand` y un plan generado con `EvaluatorEP`) y 2 de la
  GUI.
- Backends con `run_ep` (`ems` y `api`, por paso de tiempo, 1008 filas, sin cargar el registro): JPN Aqilah 2025 en
  abril (`vrf_ac`, categoría 80, modo 1; 103 columnas), en junio (`vrf_mm`, 90, modo 3; 114) y una norma 102 con RMOT
  y límites 15–25 °C en enero (`vrf_ac`, 90, modo 2: las estáticas de ISO 7730, 24/20 °C; 100): diferencia máxima 0,0
  en todas las columnas. Suite completa: 1695 pasan, 1 omitida (y después, con la sesión de la GUI, las 130 pruebas de
  la GUI); el golden master no cambia.

## 17. JPN Aqilah 2025, la norma de confort 23 (B4)

La v03 da la base de la propuesta B4 (Aqilah, Rijal, Yoshida y Nicol, 2025: `Tc = 0,38·Trm + 16,9`, ecuación 8, con
`Trm` la media móvil de α = 0,8 de McCartney y Nicol, ecuación 7; aplicable de 5 a 30 °C; bandas de ±1,5 K (90 %) y
±2,0 K (80 %), conclusiones 5 y 6) y su decisión de diseño (la norma 3 no cambia; una norma 23 `JPN Aqilah2025`, o el
YAML de B3; las diferencias con la 3 en la documentación; consignas estáticas de 20/28 °C como valores del usuario,
configurables), sin prompt. Las decisiones D1 (la 23 es JPN Aqilah 2025) y D2 (20,0/28,0 °C por defecto,
configurables, documentadas como elección del usuario) del brief la completan.

**Antes.** Las normas integradas eran la 0 a la 22 y la 99, con su código EMS literal; JPN Aqilah 2025 solo existía
como norma definida por sus datos (el YAML 101 de B3).

**Ahora.**

- `accim/sim/standards.py`: la norma 23 (`JPN Aqilah2025`, `23 = JPN Aqilah2025`, categorías 80 y 90, modos 0 a 3)
  entre la 22 y la 99; `built_in_definitions()` con su `ComfortStandardDefinition` (métrica 'rmot', régimen
  0,38/16,9 con límites 5–30, compensaciones ±2,0 (80) y ±1,5 (90), estáticas (20,0, 28,0), la evidencia y la cita
  de la v03) y `definition_of(número)` (la integrada o la del registro; `comfort_standard_definition` sigue siendo solo
  la del registro).
- `accim/sim/ems/program_lines.py`: `BUILT_IN_BRANCHES[23]` (`SetComfTemp` con `RMOT*0.38+16.9`, `SetAppLimits`,
  `ApplyCAT`, `CountHours` y `SetVST` con RMOT), que las funciones de B3 añaden al final de las cadenas antes que las
  del registro (`_all_branches`; `registered_standards_in` también las reconoce); `setpoint_lines.py`:
  `SETPOINT_LINES[(23, 0..3)]`; `setast.py`: `MODULAR_COMFORT_MODES[23]`. Las cadenas literales de la 1.1.0 no
  cambian, así que tampoco las cadenas filtradas de los IDF de `AddAccis` de las demás normas (y B1 y B3 siguen
  reconociendo los modelos de la 1.1.0). Una prueba comprueba que estas líneas literales son las que escribe
  `accim.sim.ems.standard_lines` desde la definición, y que los modos 2 y 3 son los de JPN Rijal con RMOT y los
  coeficientes de la ecuación 8.
- `accim/sim/generation.py` (`_generates` con `definition_of`); `accim/utils/ems_code.py` (la cabecera de la norma
  integrada definida por sus datos, con su métrica, estáticas y evidencia); `accim/sim/accis.py` y
  `param_accis.modify_ComfStand` (`ValueError` con los modelos de versiones anteriores, que no tienen el código de la
  23 ni el del registro); `param_accis.get_valid_param_combinations` y `drop_invalid_param_combinations` (23: [[80, 90],
  [0, 1, 2, 3]]); las listas de normas de los docstrings y de `README.md`.
- Golden master: las 22 configuraciones de `AddAccis` no cambian; las de las funciones en memoria (`s01`–`s06` y
  `s09`), cuyos modelos tienen el código de todas las normas, solo ganan el de la 23 (sin líneas quitadas, comprobado
  con `difflib`) y se han escrito de nuevo con `--update-golden`; `tests/core/golden_master/README.md` lo explica.
- Pruebas actualizadas porque cambia el conjunto de normas integradas: `test_comfort_standard_code.py` y
  `test_outdoor_metric.py` (las cadenas completas son las de las funciones), `test_ems_code.py`, `test_prompts.py` y
  `test_zone_arguments.py` (24, no 23, como norma que no existe) y `test_comfort_standard_registry.py`.
- Documentación: la sección 4.2 del uso detallado (tabla de argumentos, lista y tabla de normas, un párrafo y una tabla
  de las diferencias con JPN Rijal, la transcripción de las preguntas), 4.2.5 y 4.3 (la tabla completa de consignas no
  tiene la 23: tarea en `TODO.md`).
- Decisiones provisionales (en `notes/questions.md`): la media móvil es la RMOT de EnergyPlus (CEN 15251, α = 0,8),
  como en INT EN16798, no la `rmot_alpha` de B1 del YAML; las estáticas se configuran con una norma definida por sus
  datos con los mismos datos, sin argumentos nuevos (tarea bloqueada en `TODO.md`); sin cuaderno How-to (la v03 no lo
  pide; el de B3 compara el mismo modelo con JPN Rijal).
- Pruebas: `tests/core/test_jpn_aqilah2025.py` (13: el catálogo y la definición, igual a la del YAML salvo la
  métrica; el código EMS literal frente al generador de B3 y frente a JPN Rijal; el código EMS con la evidencia;
  `compute_setpoints` frente a la fórmula en los modos 0 a 3, con las estáticas en el primer paso; las combinaciones
  del paramétrico; `AddAccis`, con los IDF de la norma 1 idénticos byte a byte; `modify_accis`; los modelos de
  versiones anteriores; y dos con EnergyPlus 25.1: del 1 al 7 de enero, la comprobación 4 sin discrepancias en 1008
  pasos y los 28 °C estáticos en el primer paso; y los dos backends).
- Backends con `run_ep` (`ems` y `api`, por paso de tiempo, 1008 filas): enero (`vrf_ac`, categoría 90, modo 1; 100
  columnas), abril (`vrf_mm`, 90, modo 2; 111) y junio (`vrf_mm`, 80, modo 3; 111): diferencia máxima 0,0 en todas las
  columnas. Suite completa: 1707 pasan, 1 omitida y 2 fallan, dos pruebas más que tomaban la 23 como norma inexistente
  (`test_zone_arguments.py`, ahora la 24) y las cadenas de un modelo de `add_accis_to_idf` como las literales
  (`test_outdoor_metric.py`); corregidas, sus dos archivos pasan (65).

## 18. Los objetivos de confort de largo plazo (C2)

La v03 pide en `objectives.py`, reutilizando D1, `hours_outside_range` (método A), `degree_hours` (método B) y
`ppd_weighted_hours` (método C) de CEN/TR 16798-2:2019 (anexo D), por zona y edificio y por periodo cálido y frío, con
las categorías de EN 16798-1 como rangos, y los criterios de desviación admisible de la tabla E.1 (3 %/6 % anual,
12 %/25 % mensual, 20 %/50 % semanal) como restricciones de la optimización; sin prompt, y el brief no la ajusta.

**Antes.** Los indicadores de largo plazo solo se calculaban después de las simulaciones (D1:
`accim.data.postprocessing.long_term_discomfort` y `Table(long_term_indicators=True)`), y los reductores de
`objectives.py` (sumas, medias y el estado de confort de EnergyPlus) no los daban.

**Ahora.**

- El problema: los reductores de besos reciben una sola salida (`EPResults`) cada uno, y los indicadores necesitan a la
  vez la temperatura operativa, los límites y los ocupantes. Así que los cuenta el EMS.
- `accim/sim/ems/long_term_discomfort.py` (nuevo): con `report_long_term_discomfort=True`, cada zona tiene el programa
  `CountLongTermDiscomfort_<zona>`, que `RunACCIS_<zona>` ejecuta justo después de `CountHoursNoApp_<zona>`, y que en
  cada paso ocupado pone `Hours Above Upper Limit_<zona>` y `Hours Below Lower Limit_<zona>` (método A: la duración del
  paso si la temperatura operativa supera la consigna de refrigeración sin la tolerancia, `ACSTnoTol`, o queda por
  debajo de la de calefacción, `AHSTnoTol`) y `Degree Hours Above Upper Limit_<zona>` y `Degree Hours Below Lower
  Limit_<zona>` (método B: la diferencia por esa duración, en Kh), y 0 sin ocupantes; son salidas sumadas. El edificio
  tiene las sumas de sus zonas (`..._Building`), que suma el programa `CountLongTermDiscomfort_Building` (una zona por
  línea), cuyo gestor de llamadas va después de los de las zonas (los gestores del mismo punto de llamada se ejecutan
  en el orden del IDF, como ya supone `programs.py`). Los límites son los de los contadores de horas del ACCIS y de
  `Table(long_term_indicators=True)` de D1; con INT EN16798 (1), los de las categorías de EN 16798-1 dentro de su
  aplicabilidad. `set_long_term_discomfort_code(idf, frequencies)` los añade a un modelo de `add_accis_to_idf`.
- `accim/sim/accis.py`: el argumento `report_long_term_discomfort` (False por defecto) de `AddAccis` y
  `add_accis_to_idf` (`ValueError` si no es booleano o con `setpoint_type='pmv'`, cuyas zonas no siguen las consignas
  del ACCIS); con `output_type` 'simplified' se añaden sus `Output:Variable` (`_request_outputs`, que ahora usa también
  `_add_hours_below_outputs`); 'standard' y 'detailed' ya piden todas las salidas del EMS, y 'custom' conserva las
  elegidas.
- `accim/parametric_and_optimisation/objectives.py`: los reductores `hours_outside_range` (método A) y `degree_hours`
  (método B) suman esas salidas: comprueban que la salida es una de ellas (por el nombre `EMS,<salida>_<zona>` de besos)
  y sus valores como `checked_sum_results`; `deviation_constraint_bound(horas ocupadas, periodo, nivel)` da la cota de
  una restricción en el formato de besos y platypus (`'<=126.0'` con 2100 h, `'yearly'` y `'6%'`), con la nueva
  `deviation_limit` de D1, que ahora usa `deviation_check` (mismo resultado). `accim/parametric_and_optimisation/main.py`:
  las cuatro clases del paramétrico pasan `report_long_term_discomfort` a `add_accis_to_idf`.
- `accim/utils/verification.py`: la comprobación 6 de `verify_accim_simulation` (cada zona, desde sus horas ocupadas,
  su temperatura operativa del paso anterior y sus consignas sin la tolerancia; el edificio, como la suma de sus zonas;
  por paso de tiempo, sin el primer paso de cada entorno).
- GUI: una casilla en el marco del suelo y el techo de las consignas de la pestaña de `AddAccis`, desactivada (y
  omitida) con las consignas basadas en el PMV.
- EnergyPlus escribe en mayúsculas las unidades de las variables de salida del EMS (el campo no tiene `\retaincase`):
  los grados-hora salen como `[KH]`.
- Documentación: la sección 4.2.6 del uso detallado (nueva) y las 4.2 (tabla de argumentos), 4.6.1 (comprobación 6),
  4.7.4 y 4.10; la página del paramétrico (los objetivos y la restricción con la tabla E.1).
- Decisiones provisionales (en `notes/questions.md`): el EMS cuenta los indicadores, a petición, con el rango de las
  consignas sin la tolerancia del ACCIS y las sumas de las zonas para el edificio; la cota de la restricción es la del
  periodo simulado (el criterio anual), y los criterios semanal y mensual se comprueban después de las simulaciones
  (tarea en `TODO.md`); el método C no se cuenta, porque necesita un PMV y unos límites que debe elegir el autor
  (tarea bloqueada en `TODO.md`); TM52 y TM59, fuera de alcance (D12, tarea en `TODO.md`).
- Pruebas: `tests/core/test_long_term_discomfort_counters.py` (22: las líneas Erl frente a las funciones de D1 en el
  intérprete de accim, también con la consigna de calefacción por encima de la de refrigeración; el edificio como suma;
  los objetos de `add_accis_to_idf` y de `AddAccis` con 'standard' y 'simplified'; los errores; los modelos de
  versiones anteriores; y con EnergyPlus 25.1: una semana de invierno y otra de verano por paso de tiempo, con la
  comprobación 6 sin discrepancias y los totales de las funciones de D1; las demás salidas no cambian; y los dos
  backends); `tests/parametric_and_optimisation/test_objectives.py` (6: los reductores, sus errores, las cotas de la
  tabla E.1 también con platypus, los reductores con los resultados de besos de una semana simulada y las clases del
  paramétrico); `tests/core/test_long_term_discomfort.py` (`deviation_limit`); y la GUI. El golden master no cambia.
- Backends con `run_ep` (`ems` y `api`, por paso de tiempo, 1008 filas): enero (`vrf_ac`, INT EN16798, categoría 2,
  modo 3; 112 columnas), abril (`vrf_mm`, categoría 1, modo 2, HVACmode 1; 123) y julio (`vrf_mm`, INT ASHRAE55,
  categoría 80, modo 3, HVACmode 2; 123): diferencia máxima 0,0 en todas las columnas. Un estudio paramétrico de dos
  simulaciones (categorías I y III, del 1 al 7 de julio) con los reductores nuevos da los totales de los CSV de cada
  simulación (10,17 h y 2,31 Kh por encima con la categoría I; 0 con la III). Suite completa: 1738 pasan y 1 omitida;
  la documentación, con los mismos avisos que antes (59).

## 19. Los archivos climáticos futuros con pyfwg (E4)

La v03 pide que `accim.data.morphing.morph_epws()` delegue opcionalmente en pyfwg (Future Weather Generator) y acepte
los TMY de pyweatherfiles, solo si están instalados (`accim[weather]`), y un cuaderno: EPW presente → EPW futuros →
`run_ep` → `Table` con los indicadores de D1; sin prompt, y el brief no la ajusta.

**Antes.** `morph_epws` ejecutaba el Future Weather Generator con Java desde la línea de órdenes, con 8 argumentos
posicionales (los de una versión anterior de la herramienta), movía cada EPW a una carpeta con su nombre, renombraba
los EPW de cada escenario (`<EPW>_<escenario>.epw`) y los devolvía a la carpeta de trabajo.

**Ahora.**

- `accim/data/morphing.py`: el argumento `engine` (`'java'` por defecto, como antes; `'pyfwg'`) y `pyfwg_arguments`.
  Con `'pyfwg'`, `_morph_with_pyfwg` importa pyfwg (con un `ImportError` que dice cómo instalarlo), comprueba con
  `pyfwg.detect_fwg_tool` que la herramienta es la global (`ValueError` con la de Europa o las CORDEX; si pyfwg no la
  identifica, la deja a pyfwg) y llama a `pyfwg.morph_epw_global` para cada EPW, que se queda donde está: la herramienta
  escribe en una carpeta con su nombre junto a él, y los EPW futuros se renombran y se mueven junto al original con
  `_move_scenario_epws`, la misma función que usa ahora el motor de Java (sin cambiar lo que hace). Las opciones
  `fwg_options_*` pasan a pyfwg como `fwg_gcms` (lista), `fwg_create_ensemble`, `fwg_month_transition_hours`,
  `fwg_use_multithreading`, `fwg_interpolation_method_id` y `fwg_limit_variables`, y se muestra la salida de la
  herramienta, como con Java; `pyfwg_arguments` da los demás argumentos de `morph_epw_global` (`fwg_version`,
  `fwg_add_uhi`...), comprobados con su firma, y no los de los archivos, que fija `morph_epws`. Si la herramienta no
  escribe ningún EPW futuro de un EPW (pyfwg registra el error y sigue), `RuntimeError` al final, después de los demás.
  Las constantes `SCENARIOS` (los de pyfwg: `GLOBAL_SCENARIOS` × `ALL_POSSIBLE_YEARS`), `DEFAULT_GCMS` (los modelos de
  antes, todos en `pyfwg.DEFAULT_GLOBAL_GCMS`) y `ENGINES`; una docstring del módulo.
- `setup.py`: el extra `weather` (`pyfwg>=0.4.0`, `pyweatherfiles`), el de la v03 (E3). accim no importa
  pyweatherfiles: sus EPW (`HourlyEPWConverter`) se transforman por su ruta con `engine='pyfwg'`.
- La API de pyfwg se ha leído en su código instalado (0.4.0, de PyPI). Su orden para la versión 3 de la herramienta
  tiene 12 argumentos (`_build_command_v3`: también el desplazamiento de la desviación típica, el ajuste de la hora
  solar, el modelo de irradiación difusa y la isla de calor), y las versiones 4 y 5 usan clave y valor: la orden del
  motor de Java de accim puede no ser la de las versiones actuales (tarea en `TODO.md`, para comprobar con el jar).
- Documentación: la sección 4.5.1 del uso detallado (nueva) y la sección 2 (el extra); `tests/README.md`.
- Decisiones provisionales (en `notes/questions.md`): pyfwg a petición (`engine`), no siempre que esté instalado; solo
  la herramienta global; los TMY de pyweatherfiles, como EPW por su ruta. El cuaderno y la prueba con la herramienta
  esperan al jar, que no está en este equipo (tarea bloqueada en `TODO.md`).
- Pruebas: `tests/core/test_morphing.py` (10 nuevas: pyfwg simulado, con EPW de la carpeta de trabajo y de otra
  carpeta, sus opciones y `pyfwg_arguments`, los errores, la herramienta global, los fallos, sin pyfwg; los argumentos y
  las constantes frente a pyfwg 0.4.0 instalado; y una con la herramienta, omitida sin `ACCIM_FWG_JAR`). Las 9 de antes
  pasan sin cambios. `tests/core`: 1240 pasan y 2 omitidas; la documentación, con los mismos avisos que antes (59).

## 20. Las consignas del balance térmico adaptativo, ATHB (A4)

La v03 pide (con su prompt, el ajuste del brief y D10) `accim/sim/comfort_hooks.py` con `AthbSetpointHook`, un gancho
`after_programs` del backend de la API de Python que calcula el ATHB-PMV de cada zona con
`pythermalcomfort.models.pmv_athb` (importación perezosa; extra `accim[comfort]`) y busca por bisección (0,1 K) las
temperaturas operativas cuyo ATHB_PMV es la consigna de calefacción y la de refrigeración, escribiéndolas en los
actuadores de las consignas del ACCIS; `apply_athb_setpoints(building, ...)`, que prepara el IDF y devuelve el gancho;
y el argumento `hooks` de `run_ep`, solo con `backend='api'` (`NotImplementedError` en otro caso). Antes de escribirlo
se ha leído `help(ErlController)`: `get(nombre, programa)`, `set(nombre, valor)` y los ganchos
`hook(controller, calling_point)`.

**Antes.** Las consignas basadas en el PMV eran las de `accim.sim.pmv_index` (aPMV, ePMV y PMV, con termostatos de
Fanger y el EMS); el EMS no puede calcular el ATHB, que necesita el PMV completo con el clo y el met adaptados en cada
paso.

**Ahora.**

- `accim/sim/comfort_hooks.py` (nuevo): las ecuaciones del ATHB de pythermalcomfort 4.8.1 (comprobadas en su código
  instalado; son las de la v03): `athb_met` (met − 0,234·trm/58,2), `athb_clo` (10^(−0,17168 − 0,000485·trm +
  0,08176·met_adaptado − 0,00527·trm·met_adaptado)) y `athb_pmv` (el `pmv_athb` del paquete, con un `ImportError`
  que dice cómo instalarlo). `AthbSetpointHook(zonas, athb_cooling_setpoint=0.5, athb_heating_setpoint=-0.5, met=1.1,
  air_speed=0.1, clo='adaptive', tolerance_k=0.1, max_iterations=20, temperature_range=(10, 30))`: en
  `BEGINTIMESTEPBEFOREPREDICTOR`, tras los programas del ACCIS, lee `RMOT` y los sensores de cada zona, busca por
  bisección (las dos consignas a la vez, con arrays de numpy) las temperaturas operativas cuyo ATHB_PMV (con la
  temperatura del aire y la radiante iguales a ella y la humedad de la zona) es cada consigna, dentro del rango (sus
  límites fuera de él; el de ISO 7730:2025 para el PMV), y las da a `AHST_Act_<zona>` y `ACST_Act_<zona>`; pone
  `ATHB_PMV_<zona>` (de la temperatura del aire y la radiante de la zona), `ATHB_clo_<zona>` y `ATHB_met_<zona>`. Se
  puede enviar a los procesos de las simulaciones (pickle). `apply_athb_setpoints`: con el ACCIS de accim 1.0.0 o
  posterior y climatización completa (`ValueError` en modo mixto, cuyas ventanas siguen las consignas del ACCIS, sin el
  ACCIS o dos veces), añade los sensores `ATHB_MAT_<zona>`, `ATHB_MRT_<zona>` y `ATHB_RH_<zona>` (con la clave del
  sensor `<zona>_OpT`), las variables globales y las salidas del EMS (promediadas) y sus `Output:Variable`.
- `accim/run/run.py`: `run_ep(..., hooks=None)`; con `backend='api'`, los pasa como `after_programs` a
  `run_simulations`; con `'ems'`, `NotImplementedError`.
- `setup.py`: el extra `comfort` (`pythermalcomfort>=4.8; python_version >= "3.11"`): pythermalcomfort 4.8.1 exige
  Python 3.11 o posterior, y accim admite 3.9.
- Documentación: la sección 4.9.1 del uso detallado (nueva) y la 4.9 (`hooks`), la sección 2 (el extra) y la API.
- Decisiones provisionales (en `notes/questions.md`): solo climatización completa; las consignas en todos los pasos
  (como el ACCIS); el rango de 10 a 30 °C; el ATHB_PMV de cada zona con su temperatura del aire y radiante; en el
  primer paso de cada entorno la media móvil es 0, como para el ACCIS; sin la caché de la v03 (rendimiento: ~1 ms por
  zona y paso). Desviación de la prueba (3) de la v03 (ATHB_PMV dentro de las consignas en las horas con climatización):
  en el modelo de ejemplo el VRF supera la consigna de refrigeración hasta 1 K mientras refrigera (como con las
  consignas del ACCIS), y el ATHB_PMV de la zona usa su temperatura del aire y radiante, así que no se cumple de forma
  estricta; las pruebas comprueban en su lugar que las consignas de las schedules son las de la bisección con los
  sensores de la zona, y el clo y el met los de la media móvil. Los argumentos del gancho no se guardan en el modelo:
  `verify_accim_simulation` no comprueba estas consignas (tarea en `TODO.md`).
- Pruebas: `tests/core/test_comfort_hooks.py` (12: las ecuaciones, también frente a pythermalcomfort; la bisección y
  sus límites; el gancho con un controlador falso; sus argumentos; pickle; sin pythermalcomfort; `apply_athb_setpoints`
  y sus errores; `run_ep` con `hooks` y el EMS; y con EnergyPlus 25.1: una semana con `run_ep(backend='api',
  hooks=[gancho])`, cuyas consignas son las de la bisección con la humedad y la media móvil del paso anterior, y el
  mismo modelo sin el gancho con los dos backends, idénticos). Suite completa: 1759 pasan y 2 omitidas; la
  documentación, con los mismos avisos que antes (59).

## 21. Las consignas de la temperatura efectiva estándar (SET) y del PPD (A6)

La v03 (A6, sin prompt) da dos vías para las consignas de la SET: (a) un control proporcional en Erl de la consigna a
partir de la SET del paso anterior (k ≈ 0,8, con saturación; con retardo y posible oscilación) y (b) un gancho del
backend de la API con `pythermalcomfort.models.set_tmp` y bisección (exacto); las del PPD, con A2 (las consignas del
PMV de las categorías de ISO 7730:2025, tabla A.1: PPD < 6, 10, 15 y 25 % ↔ PMV ±0,2, 0,5, 0,7 y 1,0); y nombra el
cooling effect, sin diseño. Prioridad baja hasta tener A4.

**Antes.** No había consignas de la SET; las del PMV (`apply_pmv_setpoints`, A2) ya daban las del PPD de las
categorías, sin decirlo la documentación (ni la categoría IV).

**Ahora.**

- `accim/sim/comfort_hooks.py`: `standard_effective_temperature` (el `set_tmp` de pythermalcomfort, sin sus límites de
  entradas ni redondeo); `SET_TEMPERATURE_RANGE` (10–40 °C, los límites de pythermalcomfort); `SetSetpointHook(zonas,
  set_cooling_setpoint, set_heating_setpoint, met, clo, air_speed, position='standing', ...)` (sin valores por defecto
  para las consignas, el met, el clo ni la velocidad del aire, que la v03 no da; avisa fuera de los límites de
  pythermalcomfort); `apply_set_setpoints` (solo el sensor `SET_RH_<zona>`, sin variables globales ni salidas, así que
  no tiene `output_frequencies`; excluye el ATHB, que fija los mismos termostatos). La bisección y la preparación del
  modelo se comparten con el ATHB (`_bisect`, `_model_zones`, `_add_hook_objects`).
- El SET de pythermalcomfort detiene EnergyPlus con una violación de acceso (código -1073741819) en su primera llamada
  desde un callback de la API (un gancho que solo lo llama), también con un calentamiento previo y en un hilo con una
  pila de 64 MB; `pmv_athb` sí funciona. (Corregido por G3, sección 25: el fallo es propio de este entorno, Python
  3.14.3 con numba 0.68.1, y se da en la primera llamada de `set_tmp` en un proceso que ya ha cargado la biblioteca
  de la API de EnergyPlus, dentro de un callback o no; una llamada antes de cargarla lo evita, y la revisión de la
  1.2.0 lo ejecutó en los callbacks con Python 3.12 y numba 0.68.1.) Como, con las demás entradas fijas, las consignas solo dependen de la humedad
  relativa, el gancho las calcula por bisección para cada humedad de 0 a 100 % (cada 1 %) al crearse, en el proceso
  principal, y en los callbacks las interpola con la humedad de cada zona (`setpoints_of_humidity`). No hay salida de
  la SET de las zonas (tarea en `TODO.md`).
- Documentación: la sección 4.9.2 del uso detallado (nueva) y la 4.8 (las categorías del PPD, con la IV); en
  `accim/run/run.py`, la de `hooks` de `run_ep` (el gancho de la SET; los mismos ganchos en todas las simulaciones de
  la carpeta).
- Decisiones provisionales (en `notes/questions.md`): solo la vía (b), con la tabla; la vía (a) y el cooling effect
  esperan al autor (tarea bloqueada en `TODO.md`). Los argumentos del gancho no se guardan en el modelo (como en A4):
  ni `verify_accim_simulation` ni la GUI tratan estas consignas (la tarea de A4 y A6 en `TODO.md`).
- Pruebas: `tests/core/test_comfort_hooks.py` (6 nuevas: la SET frente a pythermalcomfort, también sentado; la
  bisección y sus límites; la tabla, su interpolación y el gancho con un controlador falso, y pickle; sus argumentos y
  avisos; `apply_set_setpoints` y la exclusión con el ATHB; y una semana con EnergyPlus 25.1 y
  `run_ep(backend='api', hooks=[gancho])`, cuyas consignas son las de la tabla con la humedad del paso anterior y,
  dentro de la tolerancia, las de la bisección exacta). Suite completa: 1765 pasan y 2 omitidas; la documentación, con
  los mismos avisos que antes (59). El código del EMS no cambia (solo se añaden sensores al aplicar las consignas), así
  que no hay comparación nueva de backends: la de A4 (el modelo sin gancho, idéntico con los dos) sigue pasando.

## 22. Las salidas opcionales del ACCIS y del ATHB en `Table` (D2, completada)

La v03 pide en D2 que `Table` reconozca también `ATHB_PMV_<zone>`, `Tout_metric` y `HoursBelow_*_<zone>` en el
renombrado y en las figuras y `wrangled_table` (unidades: adimensional, °C, h). Eran salidas de A4, B1 y B5, que no
existían cuando se hizo D2 (sección 7), así que quedó una tarea en `TODO.md`, con `CustomRegime_<zona>` de B2. Con
todas hechas, se ha completado, y con las salidas de C2, que son del mismo tipo.

**Antes** (comprobado el 2026-11-10 con tres días de abril del modelo de ejemplo con el modelo personalizado, su
métrica exterior, dos regímenes, las horas por debajo de 18 y 17,5 °C, el disconfort de largo plazo y las consignas
del ATHB, EnergyPlus 25.1 y el backend de la API, con un script fuera del repositorio):

- con `standard_outputs=True`, `Table` quitaba todas estas salidas;
- sin él, quedaban con su nombre EMS en mayúsculas (`EMS:ATHB_PMV_BLOCK1:ZONE1 [](HOURLY)`), sin valores de bloque
  ni de edificio;
- con valores diarios y `frequency_agg_func='sum'`, sumaba el ATHB_PMV (6,36 en vez de 0,265), el clo y el met; la
  métrica exterior y el régimen ya se promediaban (B1 y B2 los habían añadido a `_AVERAGED_OUTPUTS`).

**Ahora.**

- El módulo nuevo `accim/data/postprocessing/optional_output_columns.py`, como `pmv_index_columns` (sección 7), dice
  qué hace `Table` con ellas: `averaged_outputs()` (la métrica exterior, el régimen y las del ATHB; `Tout_metric` y
  `CustomRegime` pasan aquí desde `_AVERAGED_OUTPUTS`, sin cambiar lo que se promedia), `standard_outputs()`,
  `zone_columns()` (las de las zonas, con la salida exacta, como `pmv_index_columns.zone_columns`; las de
  `HoursBelow_<T>_<zona>` con la temperatura, que no tiene `_`, en minúsculas: `HoursBelow_17p5 (h)`),
  `other_columns()` (`Tout_metric` y las del edificio de C2) y `comfort_hours()`. Los nombres y unidades se comprueban
  frente a los módulos de `accim.sim` que crean las salidas (una prueba).
- Los nombres en `Table`: `Block1:Zone1_CustomRegime`, `Block1:Zone1_HoursBelow_18 (h)`,
  `Block1:Zone1_Hours Above Upper Limit (h)`, `Block1:Zone1_Degree Hours Above Upper Limit (Kh)` (los de los
  indicadores de `Table(long_term_indicators=True)`, D1), `Building_Hours Above Upper Limit (h)` (las sumas del EMS),
  `Block1:Zone1_ATHB_PMV`, `Block1:Zone1_ATHB_clo (clo)`, `Block1:Zone1_ATHB_met (met)` y `Tout_metric (°C)`.
- La métrica exterior de cada zona (`Tout_metric_<zona>`) conserva su nombre EMS, como la temperatura de confort y
  las consignas de cada zona del ACCIS: con `<zona>_Tout_metric (°C)`, el nombre `Tout_metric (°C)` estaría dentro de
  los de las zonas y las figuras lo tomarían con ellos (decisión provisional en `notes/questions.md`).
- Valores de bloque y de edificio (`_add_pmv_index_levels` pasa a llamarse `_add_zone_output_levels` y recibe las
  columnas de los dos módulos): las horas, los grados-hora y las del ATHB; el régimen y la métrica de las zonas, no.
  Las salidas del edificio de C2 son las sumas del EMS de todas las zonas, también de las excluidas.
- `format_table(type_of_table='comfort hours')` toma también las horas por debajo de las temperaturas y por encima y
  por debajo de los límites (no los grados-hora).
- Documentación: la sección 4.7.5 del uso detallado (nueva), y una frase en las secciones de cada salida (4.2.2,
  4.2.3, 4.2.4, 4.2.6 y 4.9.1); la API del módulo.
- Pruebas: `tests/core/test_table_optional_outputs.py` (18: los nombres frente a `accim.sim`; con tres modelos, los
  nombres, que ningún nombre contiene otro, la media o la suma en el tiempo y los valores de bloque y de edificio,
  también con zonas excluidas; `rename_cols=False`; `standard_outputs=True`; la tabla `'comfort hours'`; `time_plot` y
  `wrangled_table`; y una simulación de dos días de enero con EnergyPlus 25.1 y todas las salidas, cuyos valores
  diarios son las medias o sumas del CSV). No cambia ningún IDF ni el código del EMS. Suite completa: 1783 pasan y 2
  omitidas (la prueba con el jar del Future Weather Generator y la de EnergyPlus 26.1, que no están en esta máquina);
  la documentación, con los mismos 59 avisos.

## 23. Los ganchos del ATHB y de la SET y los contadores y salidas del ACCIS (G1, revisión v04)

La revisión v04 (§3.1, hallazgo A4/A6-1) encontró que los ganchos de A4 y A6 solo escribían los actuadores de las
consignas (`AHST_Act_<zona>`, `ACST_Act_<zona>`) después de los programas del ACCIS, de modo que los contadores de
horas (`CountHours_<zona>`, `CountHoursNoApp_<zona>`), los de largo plazo de C2 y las salidas `Adaptive ... Setpoint
Temperature_<zona>` seguían siendo los de las consignas adaptativas que los termostatos ya no seguían. La tarea G1 pide
la opción (a): que el gancho actualice `ACST`, `AHST`, `ACSTnoTol`, `AHSTnoTol` y las redondeadas, y que los
contadores se ejecuten después.

**Antes.** El controlador de la API ejecuta los ganchos `after_programs` después de todos los programas del punto de
llamada; los contadores se ejecutan dentro de `RunACCIS_<zona>`, con las variables de cada zona, justo después de
SetAST y SetASTnoTol; así que, cuando el gancho escribía, las horas ya estaban contadas.

**Ahora.**

- `accim/sim/ems/hook_setpoints.py` (nuevo): el programa `ApplyHookSetpoints_<zona>`, que `RunACCIS_<zona>` ejecuta
  justo después de `run SetAST`: si `HookSetpoints_<zona>` es 1, pone `AHST = HookAHST_<zona>+AHSTtol` y
  `ACST = HookACST_<zona>+ACSTtol` y las redondea (las líneas de ROUNDING), y vuelve a poner la marca a 0;
  `InitHookSetpoints` (con su gestor de llamadas en BeginNewEnvironment) pone las variables a 0 al empezar cada
  entorno; `set_hook_setpoints_code()` añade todo (es idempotente: los ganchos del ATHB y de la SET comparten los
  objetos).
- `accim/sim/comfort_hooks.py`: los dos ganchos tienen `runs_before_programs = True`, se ejecutan antes de los
  programas (con los sensores ya leídos) y dan sus consignas con esas variables, no con los actuadores; si se ejecutan
  después de los programas, paran la simulación con un `RuntimeError`, porque los programas del paso no las tomarían.
- `accim/run/run.py`: `run_ep(hooks=...)` pasa los ganchos con `runs_before_programs` como `before_programs`, y los
  demás como `after_programs`.
- `accim/sim/ems/setpoint_limits.py`: `ApplySetpointLimits_<zona>` se ejecuta después de `ApplyHookSetpoints_<zona>`
  si la zona lo tiene, de modo que el suelo y el techo de B5 acotan también las consignas del gancho (D5), se añadan
  antes o después.
- `accim/utils/verification.py`: la comprobación 4 no comprueba las zonas cuyas consignas pone un gancho.
- Así, todo lo que el ACCIS hace después de SetAST sigue al gancho: la tolerancia, el redondeo, el suelo y el techo,
  las consignas sin tolerancia (las del gancho), los contadores de horas y de largo plazo, los termostatos y las
  salidas de las consignas de cada zona. La temperatura de confort y los límites de aplicabilidad con los que
  `CountHours_<zona>` reparte sus horas siguen siendo los de la norma de confort de la zona.
- Decisión provisional (en `notes/questions.md`): las consignas del gancho son los límites de la banda de confort (las
  consignas sin tolerancia), y los termostatos las reciben con la tolerancia de las consignas de la zona, como las
  adaptativas; por tanto, las consignas de los termostatos de A4 y A6 (aún no publicadas) cambian en la tolerancia
  (0,1 K por defecto); con `setpoint_tolerance=0`, los termostatos reciben las del gancho tal cual.
- Documentación: las secciones 4.9, 4.9.1, 4.9.2 y 4.6.1 del uso detallado y la API del módulo nuevo.
- Pruebas: `tests/core/test_comfort_hooks.py` (23: 5 nuevas y 6 cambiadas): el controlador falso; el reparto de los
  ganchos de `run_ep`; el modelo (los programas y su orden después de SetAST y antes del suelo y el techo, añadidos
  antes o después del gancho); el intérprete de Erl con los programas de una zona (sin gancho, las adaptativas; con
  22/26 °C, los termostatos a 22,1/25,9 °C, las sin tolerancia a 22/26 °C, las redondeadas a 22,1/25,8999 °C y las
  horas contadas con ellas; la marca se usa una vez; el suelo y el techo las acotan); y con EnergyPlus 25.1: las
  consignas sin tolerancia son las de la bisección del ATHB (y las de la tabla de la SET), las de los termostatos las
  de con tolerancia, y las horas ocupadas confortables las de la temperatura operativa dentro de ellas; los dos
  backends dan resultados idénticos sin gancho y con unas consignas constantes dadas por un gancho (API) y por las
  mismas líneas en los programas (EMS), `check_exact=True`. Los archivos de pruebas afectados (límites, verificación,
  golden master, API, largo plazo): 119 pasan; el golden master no cambia.

## 24. La media móvil de ASHRAE 55 de EnergyPlus con un periodo de simulación del 2 al 30 de enero (G2, revisión v04)

La revisión v04 (§3.1, hallazgo E1-1) explicó los 0,14 °C de la tarea P1 encontrada con B5: con un periodo de
simulación que empieza el día D de enero (2 ≤ D ≤ 30), `CalcThermalComfortAdaptiveASH55` de `ThermalComfort.cc`
(EnergyPlus 25.1) lee los días 1 a D − 1 de enero y luego los últimos días de diciembre, de modo que la variable
`avgDryBulbASH` se queda con la media del 31 de diciembre, y el primer `BeginDayFlag` la escribe sobre la media del
día D − 1, donde se queda 30 días. El 1 de enero y a partir del día 31 no pasa nada, y la RMOT no se ve afectada.

**Antes.** `energyplus_running_means` y `compute_setpoints` daban la media de los 30 días anteriores: con
`Seville_Present.epw` desde el 8 de enero, una PMOT 0,142361 °C por encima de la de EnergyPlus todos los días de la
semana, y la comprobación 4 de `verify_accim_simulation` lo daba por discrepancia.

**Ahora.**

- `accim/sim/preview.py` (`_energyplus_daily`): con un comienzo del 2 al 30 de enero, la media del día anterior al
  periodo es la del 31 de diciembre en las ventanas de la PMOT; los docstrings de `energyplus_running_means` y
  `compute_setpoints` lo explican.
- `accim/utils/verification.py`: el docstring dice seis categorías de comprobaciones (no cuatro), y la comprobación 4
  avisa en su resumen si hay un archivo .stat junto al EPW (EnergyPlus toma entonces la PMOT de sus medias mensuales,
  que no se reproducen).
- Documentación: las secciones 4.3.1 y 4.6.1 del uso detallado; las entradas de E1 (también "unos segundos" en vez de
  "un segundo") y E2 del CHANGELOG.
- Pruebas: `tests/core/test_preview.py` (2 nuevas: con un EPW cuyas medias diarias son el número del día, desde el 8
  de enero, la PMOT lleva el 31 de diciembre en lugar del 7 de enero durante sus 30 ventanas, la RMOT no cambia y los
  comienzos del 1 y 31 de enero y del 1 de marzo tampoco; y con EnergyPlus 25.1, del 8 de enero al 20 de febrero, las
  consignas de INT EN16798 y de INT ASHRAE 55 son las de `compute_setpoints` y la RMOT y la PMOT las de
  `energyplus_running_means`, 10,574306 °C el 8 de enero, la cifra de EnergyPlus); `tests/core/test_verification.py`
  (el aviso del .stat y las zonas con ganchos). 44 pasan. No cambia ningún IDF ni el código del EMS.

## 25. La SET en los callbacks de EnergyPlus (método 'bisection'), sus salidas y la documentación de A6 (G3, revisión v04)

La revisión v04 (§3.1 y §3.3, hallazgos A6-1 a A6-4) encontró que la tabla de A6 se apoyaba en que `set_tmp` no puede
calcularse en los callbacks, cuando la revisión lo ejecutó allí con Python 3.12 y numba 0.68.1; que el modelo no pedía
las temperaturas de aire y radiante; que la postura por defecto era de pie; y que faltaba documentar el coste del JIT y
la insensibilidad del SET de ASHRAE 55 a velocidades del aire bajas. El bloque F necesita la SET en los callbacks.

**Lo comprobado.** Con Python 3.14.3, numba 0.68.1, pythermalcomfort 4.8.1 y EnergyPlus 25.1: sin una llamada previa,
la primera llamada de `set_tmp` en un callback detiene el proceso (violación de acceso, -1073741819); con una llamada
antes de `run_simulation` (con números, o con números y un array), funciona; con `NUMBA_DISABLE_JIT=1`,
pythermalcomfort falla (`'function' object has no attribute 'py_func'`); y con la biblioteca de la API de EnergyPlus
ya cargada, la primera llamada detiene el proceso aunque no esté en un callback. El fallo es, pues, la primera llamada
de numba en un proceso que ya ha cargado la biblioteca de la API: por eso el calentamiento de A6 no servía.

**Ahora.**

- `SetSetpointHook(..., position=None, method='table')`: con `method='bisection'`, las consignas se calculan en cada
  paso y la SET de cada zona es la salida `SET_<zona>` (de los sensores `SET_MAT_<zona>`, `SET_MRT_<zona>` y
  `SET_RH_<zona>`); `prepare()` calcula una SET con números y otra con un array de dos valores; `position=None` es
  sentado con 1,2 met o menos y de pie por encima.
- `run_simulation` llama a `prepare()` de los ganchos (`prepare_hooks`) antes de cargar la biblioteca de la API, en el
  proceso de cada simulación.
- `apply_set_setpoints(..., method='table', output_frequencies=None)`: los tres sensores y las salidas de EnergyPlus de
  la temperatura media del aire, la radiante media y la humedad relativa de las zonas (a las frecuencias de las salidas
  del EMS del modelo), y `SET_<zona>` con la bisección; `set_of_results(results, hook)` calcula la SET de cada zona en
  cada fila de los resultados; `Table` la llama `<zona>_SET (°C)`.
- Documentación (docstrings y sección 4.9.2): el fallo de `set_tmp` en este entorno; el coste del JIT (16 s con la
  caché de numba vacía: 13,6 s de importar pythermalcomfort y 2,3 s de la primera SET); que el SET del código de ASHRAE
  55 no cambia con velocidades por debajo de 0,1 m/s, ni de unos 0,16 m/s a 1,1 met y 0,21 m/s a 1,2 met (comprobado en
  `two_nodes_gagge.py`); el efecto de la postura (hasta 0,008 K en calefacción y 0,05 K en refrigeración) y el de la
  ponderación del aire y la radiante (con tr − ta = ±3 K, hasta 0,10 y 0,07 K). Las afirmaciones anteriores (sección 21,
  DEVLOG y decisiones) llevan la corrección.
- Pruebas: `tests/core/test_comfort_hooks.py` (28: 5 nuevas y 3 cambiadas; con EnergyPlus 25.1, dos días por bisección
  con `run_ep` en un proceso nuevo, sin violación de acceso, con las consignas y la SET de los valores que leen los
  sensores, a 1e-6) y `tests/core/test_table_optional_outputs.py`. No cambia el código EMS del ACCIS.

## 26. JPN Aqilah 2025 con el archivo climático y sus consignas estáticas como argumentos (G4, revisión v04)

La revisión v04 (§3.1, §3.3 y §6.2, hallazgos B4-1 y B4-2, veredictos 29 y 30) encontró que la norma 23 lee el RMOT de
EnergyPlus, cuyo primer valor en un periodo de simulación es la suma de la ecuación 19.82 de la Engineering Reference
sin dividir por 1 − α⁷ (un 21 % más baja), de modo que su temperatura de confort queda baja unas tres semanas frente a
su gemelo YAML 101 (`rmot_alpha` iniciado con el archivo climático); y que sus consignas estáticas 20/28 °C eran
literales. El autor decidió: `rmot_alpha` desde el EPW cuando `AddAccis` lo recibe, el RMOT si no (con aviso), y los
argumentos `static_heating_setpoint`/`static_cooling_setpoint` (20,0/28,0, claves EMS `StaticAHST`/`StaticACST`).

**Lo medido** (`compute_setpoints`, Sevilla, categoría 90, modo 3; 23 con RMOT frente a 101): el primer día, de la hora 2
a la 24, 23 queda 0,92 K (1 de enero), 1,47 K (1 de abril) y 1,93 K (1 de julio) por debajo; desde el día 21, como mucho
0,024, 0,024 y 0,028 K. En la primera hora de cada día difieren durante un paso (23 aún lee el RMOT del día anterior y
101 ya ha actualizado su media), hasta 0,10 K en la media horaria (0,1013 K el 2 de mayo desde el 1 de enero). El
criterio de la tarea (< 0,1 K desde el día 21 y > 1 K el día 1) se cumple para el transitorio con los arranques del 1 de
abril y del 1 de julio y las horas 2 a 24 (y todas las horas de los días 21 a 30); así lo comprueba la prueba.

**Ahora.**

- Con el archivo climático de la simulación (`epw` de `AddAccis` o `modify_accis`), las zonas de la norma 23 tienen las
  entradas de `rmot_alpha` (código 2, α 0,8, 30 días) y su código (sus ramas de `SetComfTemp`, `CountHours_<zona>` y
  `SetVST`, y sus subprogramas) lee `Tout_metric` en lugar de RMOT, con los programas de la métrica exterior del modelo
  personalizado, que empiezan con los valores del archivo: sus consignas son las de 101 desde el primer día. Sin él, lee
  RMOT como antes, y `AddAccis` y `modify_accis` avisan. Un modelo cuyos programas ya empiezan con los valores de un
  archivo los conserva para la norma 23 (`modify_accis` sin `epw`, el paramétrico). Funciones nuevas:
  `standard_lines.WEATHER_FILE_METRICS`, `weather_file_definition`, `weather_file_lines`;
  `outdoor_metric.outdoor_metric_needed`, `weather_file_zones`, `set_weather_file_lines`.
- `compute_setpoints(..., outdoor_metric_start='epw')`, por defecto, da las consignas con el archivo, y `'pmot'` las de
  RMOT; `print_setpoint_ems_code(..., epw=...)` imprime el código con el archivo; la comprobación 4 de
  `verify_accim_simulation` compara también `Tout_metric_<zona>` de la norma 23 con el archivo.
- Las consignas estáticas de la norma 23 (modo 0, y fuera de los límites en el modo 1) son las entradas `StaticAHST` y
  `StaticACST` de sus zonas (módulo nuevo `accim.sim.ems.static_setpoints`), con los argumentos `static_heating_setpoint`
  y `static_cooling_setpoint` de `AddAccis` (20,0 y 28,0), `modify_accis` (`None` las conserva), `zone_arguments`,
  `print_setpoint_ems_code` y `compute_setpoints` (`ValueError` si la de calefacción no es menor); los modelos con su
  código las declaran como variables globales del EMS. Las demás normas las ignoran y sus IDF no cambian; los modelos
  con el código de todas las normas (`add_accis_to_idf`: archivos `s01` a `s06` y `s09` del golden master, escritos de
  nuevo) tienen las líneas de la 23 con las entradas y su declaración.
- Paramétrico: los parámetros `static_heating_setpoint` y `static_cooling_setpoint` (`modify_StaticAHST`,
  `modify_StaticACST`, las clases `StaticHeatingSetpoint` y `StaticCoolingSetpoint`); `modify_ComfStand(idf, 23)` da a
  las zonas las consignas que un parámetro no les dio y la media del archivo si el modelo la tiene;
  `drop_invalid_param_combinations` quita las filas con la de calefacción no menor. Interfaz gráfica: los campos de las
  consignas estáticas y el archivo climático con la norma 23.
- Pruebas: `tests/core/test_jpn_aqilah2025.py` (28: con el archivo, la 23 es la 101 en cada paso; el transitorio sin
  él; las consignas estáticas; `AddAccis`, `modify_accis`, `add_accis_to_idf` y el paramétrico; con EnergyPlus 25.1,
  desde el 8 de enero con el archivo, la comprobación 4 sin discrepancias, y los dos backends con resultados idénticos),
  `tests/core/test_comfort_standard_code.py` y `tests/core/test_gui.py`.

## 27. Saneamiento de la revisión v04 (G5)

La tarea G5 de la revisión v04 (§3.2 a §3.5 y §7) reúne los hallazgos menores y las decisiones provisionales que el
autor cambió (veredictos 3, 13, 26 y 28).

**Coeficientes del aPMV (A3-1, A3-2, veredicto 3).** `apply_apmv_setpoints(adaptive_coefficients=<clave>)` da los dos
coeficientes de una entrada del catálogo (`pmv_index.both_adaptive_coefficients`), con `ValueError` si los argumentos
de cada lado no tienen sus valores por defecto, la clave no existe o a la entrada le falta un lado. Una clave en un lado
con el número por defecto en el otro (0,293 o −0,293, sin fuente; `APMV_DEFAULT_COEFFICIENTS`) avisa. Con
`adaptive_coefficient_by='pmv_sign'`, las consignas de refrigeración deben ser ≥ 0 y las de calefacción ≤ 0, también las
de los diccionarios por zona y las de por defecto (`check_pmv_sign_setpoints`, antes de tocar el modelo).

**Suelo y techo (B5-1, B5-2, B5-3, veredicto 13).** `ApplySetpointLimits_<zona>` corre ahora justo después de
`SetASTnoTol`: acota `AHST` y `ACST` (las consignas con tolerancia de los termostatos), redondea de nuevo, fija las
consignas redondeadas al suelo o al techo cuando los alcanzan (el redondeo estricto daba 25,9999 °C con un techo de 26 °C
y 19,11 °C con un suelo de 19,1 °C y precisión 100) y acota también `AHSTnoTol` y `ACSTnoTol`, los límites de la banda
de confort de los contadores (antes la de calefacción quedaba en el suelo menos la tolerancia). Un modelo con el programa
tras `SetAST` (versiones previas de la 1.2.0) lo mueve al reescribir los límites. `AddAccis` y `modify_accis` avisan si
el suelo supera `ACSTaul` o el techo baja de `AHSTall` de la norma de la zona (`warn_crossed_setpoint_limits`, con el
intérprete de Erl sobre `SetInputData_<zona>` y `SetAppLimits`; la lectura literal del veredicto queda en
`notes/questions.md`). La comprobación 5 de `verify_accim_simulation` mira también las consignas sin tolerancia
(`Check5_AHSTfloor_noTol`, `Check5_ACSTceil_noTol`); `compute_setpoints`, `print_setpoint_ems_code` y
`get_setpoint_ems_programs` siguen el nuevo orden. El docstring y la sección 4.2.3 dicen que la consigna de ventilación
sólo sigue al suelo y al techo donde sale de las consignas redondeadas (dentro de los límites suele ser la temperatura
de confort más el offset).

**Métrica exterior (B1-2 y §3.4).** Un EPW sin algún mes da `ValueError` (sus medias mensuales serían `nan`, que Erl
tomaría por una variable). Un único formateador de los números de los programas, `accim.sim.ems.erl.format_number`
(posicional, sin exponente), en `custom_regimes`, `standard_lines`, `outdoor_metric` (con `.0`, como `repr`),
`setpoint_limits` y `ems_code`; los IDF no cambian (golden master). La prueba con EnergyPlus compara además
`rmot_alpha`, `te_ref_nl`, `rmot_7day` y `ndrm` con sus ecuaciones calculadas con pandas desde el EPW (1e-9 °C).

**Normas definidas por sus datos (B3-1 a B3-3, veredictos 26 y 28).** `qat_indraganti2018_hvac.yaml` (102) tiene los
datos de v04 §6.3 (elecciones del autor anotadas en su evidencia) y carga, como la carpeta de ejemplos; el cuaderno
How-to lo lee (ejecutado y exportado de nuevo). El código EMS lista las categorías en orden numérico (las de 101 quedan
como las de la 23). Un offset de refrigeración < 0 o de calefacción > 0 avisa. La documentación dice que el modo 2 no
está definido para categorías distintas de 80 y 90. La discrepancia entre 25,5 °C y la Tabla B.2 (26 °C en la categoría
II de oficinas) queda en `notes/questions.md`.

**Archivos climáticos futuros (E4-1 a E4-3).** Con pyfwg, `morph_epws` da `fwg_add_uhi=False` salvo que
`pyfwg_arguments` lo dé (pyfwg añade la isla de calor por defecto con las versiones 3 y 4 de la herramienta, y Java no);
`fwg_options_ensemble=0` avisa con los dos motores (todos los EPW de los modelos se renombran igual); un `ValueError` de
pyfwg borra las carpetas del proceso como los demás errores.

**Infraestructura y documentación (§3.4, §3.5).** `run_simulations(processes=0)` y `run_ep(processes=0)` ejecutan en el
proceso actual (con el backend EMS, `_run_idfs_in_this_process` con `prepare_run` de eppy; antes 0 eran todos los
procesadores); un número negativo es `ValueError` en `run_simulations`. Las cuatro pruebas de `tests/core` que importan
besos lo piden con `pytest.importorskip` (las demás, en `TODO.md`). Documentación: `activity_level` no es parámetro con
la corrección metabólica del ePMV, las sumas de bloque y de edificio de `Table` de magnitudes no aditivas no tienen
sentido físico, el `BANNER` toma la versión de `__version__` (lista de la publicación) y el comentario de
`_pmv_index_mismatches` sobre la dependencia del texto de `monitor_ePMV_<zona>`.

- Pruebas: `test_setpoint_limits.py` (líneas, redondeo exacto en Erl, consignas sin tolerancia con
  `compute_setpoints`, el movimiento de la línea, los avisos, EnergyPlus 25.1 y los dos backends), `test_comfort_hooks.py`,
  `test_apmv_coefficients.py`, `test_energyplus_api.py`, `test_outdoor_metric.py`, `test_comfort_standard_registry.py`,
  `test_morphing.py`, `test_gui.py`, `test_jpn_aqilah2025.py`.

## 28. El renombrado del suelo y del techo de las consignas (H1, revisión v04)

El autor pidió (decisión 8 del bloque F, v04 §4.5) cambiar `heating_setpoint_floor` y `cooling_setpoint_ceiling`, que
pueden leerse como un suelo físico (suelo radiante), antes de publicar la 1.2.0, porque son API pública.

**Ahora.**

- Argumentos `heating_setpoint_minimum` y `cooling_setpoint_maximum` en `AddAccis`, `modify_accis`, `zone_arguments`,
  `print_setpoint_ems_code`, `get_setpoint_ems_code`, `get_setpoint_ems_programs` y `compute_setpoints`; entradas EMS
  `AHSTmin` y `ACSTmax` (el programa sigue siendo `ApplySetpointLimits_<zona>`); comprobaciones `Check5_AHSTmin`,
  `Check5_ACSTmax` y sus `_noTol` en `verify_accim_simulation`; parámetros `heating_setpoint_minimum` y
  `cooling_setpoint_maximum` del paramétrico, con las clases `HeatingSetpointMinimum` y `CoolingSetpointMaximum` y los
  modificadores `param_accis.modify_AHSTmin` y `modify_ACSTmax`; campos de la interfaz gráfica. Los textos dicen «la
  consigna mínima de calefacción» y «la consigna máxima de refrigeración».
- Alias obsoletos con `DeprecationWarning` («deprecated since accim 1.2.0»): los argumentos antiguos
  (`accim.sim.arguments.DEPRECATED_ARGUMENT_NAMES`, con el decorador `accepts_legacy_kwargs`, al que
  `accim._deprecation` añade el argumento `version`, como a `warn_deprecated`, `rename_legacy_kwargs` y
  `deprecated_alias`), también como claves de `zone_arguments` (`check_zone_arguments`; `ValueError` si una zona da los
  dos nombres); los parámetros (`LEGACY_PARAMETER_NAMES` de `params_dicts`, con la versión en el aviso), las clases
  `HeatingSetpointFloor` y `CoolingSetpointCeiling` y los modificadores `modify_AHSTfloor` y `modify_ACSTceil`. La
  interfaz gráfica lee las sesiones guardadas con los nombres antiguos (`forms.current_names`, y las filas del
  paramétrico). Los modelos hechos con las entradas EMS antiguas (`AHSTfloor`, `ACSTceil`), sólo de versiones de
  desarrollo, deben generarse de nuevo.
- El mensaje de los argumentos antiguos de un `__init__` nombra la clase (`AddAccis()`), no `__init__()`.
- Pruebas: `test_setpoint_limits.py` (los nombres nuevos y los antiguos con sus avisos: código EMS, `compute_setpoints`,
  `AddAccis` con IDF idénticos, `modify_accis`, `zone_arguments`), `test_gui.py` (sesiones antiguas),
  `test_legacy_names.py` y `test_setpoint_limit_parameters.py` (paramétrico). El golden master no cambia (ninguna
  configuración tiene suelo ni techo).

## 29. El SET de EnergyPlus (Pierce) frente al de pythermalcomfort (E-F1, bloque F)

El bloque F (`notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §3 y §5) pide, antes de usar F1 en un artículo, comparar
hora a hora el SET del modelo de dos nodos de Pierce de EnergyPlus con el de `pythermalcomfort.models.set_tmp` (el que
invierte el gancho de la SET) a partir de las mismas salidas, y anotar la diferencia media y la máxima.

**Ahora.**

- `accim.sim.people.add_thermal_comfort_model(building, comfort_model)` añade `'Fanger'`, `'Pierce'` o `'KSU'`
  (`THERMAL_COMFORT_MODELS`) en el primer campo *Thermal Comfort Model n Type* vacío de los objetos People (y de los
  People:Definition de EnergyPlus 26.2), sin tocar los del ACCIS; `PIERCE_SET_OUTPUT` es el nombre de la salida del SET
  de Pierce (comprobado en el `.rdd` de EnergyPlus 25.1 y en la Engineering Reference 25.2, 19.1.4).
- Medido (modelo de ejemplo con el ACCIS, INT EN16798 categoría II modo 3, `vrf_ac`, un año en Sevilla, EnergyPlus 25.1,
  6 pasos por hora; `set_tmp` con la temperatura media del aire, la radiante media y la humedad relativa de la zona, y
  los horarios de actividad, vestimenta y velocidad del aire del People): diferencia (pythermalcomfort − EnergyPlus) de
  las medias horarias de −0,045 K de media, 0,056 K en valor absoluto y 0,180/0,196 K como máximo (zonas 1/2), de pie
  (la postura de EnergyPlus, área radiante 0,72); sentado (la del gancho con 1,2 met o menos), −0,116 K, 0,118/0,117 K
  y 0,324/0,344 K. El área corporal y la presión no cambian el resultado; la diferencia crece con el SET (de −0,01 K
  por debajo de 26 °C a −0,14 K por encima de 30 °C). La tabla está en `notes/decisions.md` y en la sección 4.9.2.
- Pruebas: `tests/core/test_pierce_set.py` (el ayudante; la simulación anual reproduce la tabla con 0,001 K).

## 30. El estándar de confort 24, INT Sun2026 SET (F1, bloque F)

El bloque F (`notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §4 y §6, `notes/PROMPTS_COPILOT_bloque_F_v02.md`) pide el
modelo SET causal de Sun, Brager y Schiavon (2026), Energy and Buildings 370, 118097 (TSV = 0,11·SET − 2,6; banda de
19,1 a 28,2 °C de SET para TSV ±0,5; SET neutro 23,6 °C), como estándar de confort 24, sobre el gancho del SET por
bisección de G3 (v04 §4.6: el gancho generalizado y el estándar 24 como capa fina).

**Antes.** El gancho del SET (A6, G3) tenía metabolismo, vestimenta y velocidad del aire constantes, y resolvía la
temperatura operativa con la radiante media igual a la del aire.

**Ahora.**

- `SetSetpointHook` y `apply_set_setpoints` aceptan `met`, `clo` y `air_speed` None (con `method='bisection'`): el
  gancho los lee en cada paso de los horarios del objeto People de cada zona (sensores `SET_Act_<zone>`, el nivel de
  actividad entre 104,76 W/met = 58,2 W/m² × 1,8 m²; `SET_Clo_<zone>` o, con el modelo dinámico de vestimenta,
  `SET_CloValue_<zone>`, la salida *Zone Thermal Comfort Clothing Value*; `SET_CloMethod_<zone>` con
  CalculationMethodSchedule; `SET_Vel_<zone>`), y `tr_mode`: 'equal_air' (por defecto, como A6) o 'zone' (la
  temperatura del aire con la radiante media de la zona, que se escribe en los termostatos del ACCIS como operativa,
  (aire + radiante)/2, decisión del autor del 10/11/2026).
- `apply_sun2026_setpoints(building, comfort_mode=1, category=80, tsv_limit=None, set_offset=None, tr_mode='zone',
  ...)` devuelve un `Sun2026SetpointHook`: modo 1 'SET band' (el SET de la banda de TSV ±tsv_limit; 0,5 por defecto y
  con las categorías 80 y 90; 0,7 y 1,0 con aviso de extrapolación) o modo 2 'SET neutral +/- offset' (23,6 °C ±
  `set_offset`); bisección entre 10 y 40 °C con tolerancia de 0,05 K; salidas `TSV_causal_<zone>` y
  `HoursInCausalBand_<zone>` además de `SET_<zone>`; el mínimo y el máximo de B5 acotan sus consignas después, y sin
  mínimo avisa una vez por zona si la consigna de calefacción baja de 18 °C; añade el modelo Pierce y su salida.
- El estándar 24 está en el catálogo (`accim.sim.standards`, `HOOK_COMFORT_STANDARDS`) sin código EMS: `AddAccis`,
  `modify_accis`, `print_setpoint_ems_code` y `compute_setpoints` dan un `ValueError` con él, y la interfaz gráfica y
  las preguntas de `AddAccis` no lo ofrecen. El respaldo del backend EMS (bucle Erl de v03 A6a) queda en `TODO.md`
  (P2).
- `Table` nombra las salidas nuevas (`<zone>_TSV_causal`, `<zone>_HoursInCausalBand (h)`).
- Medido (dos semanas del modelo de ejemplo en Sevilla, EnergyPlus 25.1): el SET horario del gancho queda por debajo
  del SET Pierce de EnergyPlus 0,08 K de media en invierno (máximo 0,20 K) y 0,155 K en verano (máximo 0,29 K); de
  pie y alineado con el paso que leen los sensores, 0,01 y 0,08 K (`notes/decisions.md`).
- Decisiones provisionales en `notes/questions.md`: los modos son 1 y 2; los "límites CustAST_ACSTaul/all y
  AHSTaul/all" del encargo son límites de aplicabilidad de la métrica exterior y no se aplican a las consignas; la
  vestimenta del modelo dinámico se lee de su salida.
- Pruebas: `tests/core/test_sun2026_set.py` (18).

## 31. El limitador de la deriva de las consignas (F2, bloque F)

Parkinson, de Dear y Brager (2020), Energy and Buildings 206, 109559: los ocupantes se adaptan a la temperatura
interior media a la que están expuestos (Fig. 6), y los cambios de consigna deben repartirse en días o semanas (§4.3.2).
El bloque F (`notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §4 y §6) pide un limitador opcional.

**Antes.** Las consignas de cada día eran las del estándar de confort, sin límite de su variación.

**Ahora.**

- Argumentos `drift_mode` (None por defecto: sin limitador y sin cambios en los IDF), `max_drift_rate` (0,5 K/día),
  `alpha_indoor` (0,8), `delta_cool` y `delta_heat` (1,0 K) e `initial_T_rm_in` (None) en `AddAccis`, `modify_accis`
  (None los conserva) y `zone_arguments` (`accim.sim.ems.drift_limiter`).
- 'rate': las consignas de cada día quedan a `max_drift_rate` como mucho de las aplicadas al final del día anterior (el
  primer día ocupado sin límite). 'window': las consignas quedan en [T_rm_in − `delta_heat`, T_rm_in + `delta_cool`],
  con T_rm_in(d) = (1 − α)·T_occ_media(d − 1) + α·T_rm_in(d − 1) de la temperatura operativa de las horas ocupadas,
  inactivo hasta un día ocupado completo salvo con `initial_T_rm_in`.
- Las zonas con limitador reciben las entradas `DriftMode`, `MaxDriftRate`, `AlphaIndoor`, `DeltaCool`, `DeltaHeat` (e
  `InitTrmIn`), el programa `ApplyDriftLimiter_<zone>` (tras `SetAST` y el gancho, antes de `SetASTnoTol` y del mínimo y
  máximo de B5; acumuladores Erl `sum_T_occ_<zone>` y `n_occ_<zone>` volcados al cambiar `DayOfYear`, fuera del
  calentamiento, sin `TrendVariable`), `InitDriftLimiter` y las salidas `T_rm_in_<zone>`, `DriftTarget*_<zone>`,
  `DriftApplied*_<zone>` y `DriftLimitedHours_<zone>`.
- `print_setpoint_ems_code` muestra sus programas; `compute_setpoints` da un `ValueError`; `verify_accim_simulation`
  comprueba los objetivos del limitador. Parámetros del paramétrico (`drift_mode` con los códigos 0, 1 y 2...), campos
  de la interfaz gráfica y nombres en `Table`.
- Con EnergyPlus 25.1, los dos backends dan resultados idénticos y T_rm_in coincide con su cálculo en pandas.
- Decisiones provisionales en `notes/questions.md`: la consigna aplicada del día anterior es la de su último paso; los
  días sin horas ocupadas no cambian T_rm_in; el código 0 del parámetro `drift_mode` lo desactiva.
- Pruebas: `tests/core/test_drift_limiter.py` (11) y `tests/parametric_and_optimisation/test_drift_parameters.py` (2).

## 32. Los indicadores de la adaptación al clima interior (F3, bloque F)

La propuesta del bloque F (`notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §4 F3) pide medir las consignas de todos los
modelos en los mismos términos: horas dentro de la banda causal del SET, sobreenfriamiento, neutralidad por exposición
(Parkinson, de Dear y Brager, 2020, Fig. 6) y, por la decisión sobre A6 (v04 §6.8), el efecto de enfriamiento de la
velocidad del aire como indicador.

**Antes.** `Table` descartaba con `standard_outputs=True` las salidas del modelo Pierce y del efecto de enfriamiento, y
sin ello las sumaba en el tiempo; no había indicadores de la banda causal, del sobreenfriamiento ni de Tn_exp.

**Ahora.**

- Módulo nuevo `accim.data.postprocessing.indoor_adaptation`: `causal_band_hours` (horas ocupadas con el SET dentro de
  la banda de TSV ±0,5 de Sun, Brager y Schiavon, 2026, por encima y por debajo), `overcooling_hours` (horas ocupadas
  de la temporada de refrigeración por debajo de 22 °C o de una consigna de calefacción de referencia),
  `indoor_running_mean` (T_rm_in con la definición y el arranque del limitador de F2), `exposure_neutral_temperature`
  (Tn_exp = 1,06 + 0,951·T_rm_in, y los coeficientes MM y NV) y `exposure_hours` (horas con abs(To − Tn_exp) > 2,5 K,
  umbral inferido por la propuesta), y `table_indicators`.
- `Table(indoor_adaptation_indicators=True)`: atributo `indoor_adaptation_indicators` con una fila por simulación y los
  indicadores de cada zona y del edificio; casilla en la interfaz gráfica.
- `accim.sim.people.add_thermal_comfort_outputs`: añade los modelos Fanger, Pierce y CoolingEffectASH55 a los objetos
  People y pide sus salidas por instancia de ocupantes; `add_thermal_comfort_model` acepta CoolingEffectASH55 si el IDD
  del modelo lo tiene (el de EnergyPlus 9.4 no).
- `Table` promedia esas salidas, las conserva con `standard_outputs=True`, les da valores de bloque y edificio y las
  llama `<zone>_SET_Pierce (°C)`, `<zone>_SET_Pierce_PMV`, `<zone>_CoolingEffect (°C)`, `<zone>_CoolingEffect_PMV` y
  `<zone>_CoolingEffect_PPD` (ningún nombre contiene otro); la tabla 'comfort hours' incluye `HoursInCausalBand (h)`.
- Documentación: sección 4.7.6 (también el diseño del estudio de validación, con las funciones de accim de cada caso).
- Decisiones provisionales en `notes/questions.md`: el SET de los indicadores es el de EnergyPlus; el sobreenfriamiento
  se cuenta en la temporada de refrigeración del ACCIS con un único umbral; T_rm_in se calcula de las filas de la tabla
  y la banda de Tn_exp es de 2,5 K por defecto; el caso (i) del estudio.
- Pruebas: `tests/core/test_indoor_adaptation.py` (20, también con EnergyPlus 25.1).

## 33. T0 de te_ref_nl, del día completo (H2)

Van der Linden et al. (2006) definen Ti con la máxima y la mínima del día completo; el EMS tomaba para T0 las de las
horas del día transcurridas, y Te,ref derivaba dentro del día (hallazgo B1-1, veredicto #8).

**Antes.** `set OutdoorMidRange = (OutdoorMax+OutdoorMin)/2` de las horas cerradas del día (o la temperatura exterior
del paso antes de cerrar la primera hora).

**Ahora.**

- Con el EPW (`epw` de `AddAccis` o `modify_accis`) y alguna zona con `te_ref_nl`: el `Schedule:File`
  `ACCIS Outdoor Mid Range`, con un CSV `<epw>_outdoor_mid_range.csv` en la carpeta del modelo (ruta absoluta en el
  objeto) con la media de la máxima y la mínima del día de cada hora del EPW, y el sensor `OutdoorMidRangeToday` de su
  *Schedule Value*: `set OutdoorMidRange = OutdoorMidRangeToday`. EnergyPlus 25.1 da el valor del día desde su primer
  paso, así que Te,ref es constante en cada día.
- Sin el EPW: `set OutdoorMidRange = Tmid_1` (la del día anterior), con aviso. Los programas que empiezan con los
  valores de un EPW y no leen el sensor se escriben de nuevo (empezando con PMOT) si una zona pasa a `te_ref_nl` sin él.
- Módulo nuevo `accim.sim.schedule_files` (también para H6). `compute_setpoints`, `print_setpoint_ems_code` y
  `verify_accim_simulation` siguen la definición nueva; los dos backends dan los mismos resultados.
- Los IDF con el código de la métrica exterior cambian en la rama de `te_ref_nl` (sus resultados con otras métricas no);
  el golden master no tiene ninguno.
- Pruebas: `tests/core/test_outdoor_metric.py` (la prueba de la ATG con la definición nueva, el código EMS, AddAccis,
  modify_accis, EnergyPlus con los dos backends) y `tests/core/test_schedule_files.py`.

## 34. El rango constante del disconfort de largo plazo, el método C y `Table` por pasos de tiempo (H3)

Tarea H3 de la revisión v04 (hallazgos C2-1 y D1-1; decisión 5 de su §6 y veredicto #20).

**Antes.** Los contadores de largo plazo del ACCIS (C2) comparaban la temperatura operativa con las consignas sin la
tolerancia (`AHSTnoTol` y `ACSTnoTol`): miden cuánto falla el control en mantener su banda, que con el modo de confort
3, las consignas estáticas, el modelo personalizado o el mínimo y el máximo no es la de una norma, y dos modelos con
normas distintas no se comparan con ellas. El método C (horas ponderadas por el PPD) no se contaba. En D1,
`ppd_weighted_hours` dejaba dentro del rango un PMV igual al límite superior. `Table` con
`source_frequency='timestep'` y `standard_outputs=True` descartaba todas las salidas (buscaba `Timestep` en los
nombres de las columnas, que EnergyPlus escribe `(TimeStep)`), y al agrupar por horas tomaba los pasos de 00:10 a 00:50
por la hora anterior.

**Ahora.**

- `long_term_range` (en `AddAccis`, `add_accis_to_idf`, `set_long_term_discomfort_code` y las clases del
  paramétrico), con `report_long_term_discomfort=True`: `None` (por defecto, como antes) o `('en16798', categoría)` /
  `('en16798', categoría, tipo de edificio)`, el mínimo de calefacción y el máximo de refrigeración de la tabla B.2 de
  EN 16798-1:2019 (`accim.constants.EN16798_TABLE_B2`); en las categorías III y IV el tipo de edificio es obligatorio
  (sus mínimos difieren; provisional en `notes/questions.md`). Los programas `CountLongTermDiscomfort_<zona>` comparan
  con esos números (`long_term_limits`, `zone_lines(zona, límites)`); `model_long_term_limits` los lee de los
  programas y la comprobación 6 de `verify_accim_simulation` los usa. La GUI tiene la lista de los rangos de la tabla
  B.2 bajo la casilla del disconfort de largo plazo.
- El método C en las consignas basadas en el PMV (`report_ppd_weighted_hours=True` en `apply_apmv_setpoints`,
  `apply_epmv_setpoints`, `apply_pmv_setpoints` y `apply_pmv_index_setpoints`): el programa
  `count_ppd_weighted_hours_<zona>`, tras los contadores de horas de la zona, y la salida sumada
  `PPD Weighted Hours_<zona>`: en cada paso ocupado, PPD(PMV)/PPD(PMVlímite) (fórmula (5) de ISO 7730:2025, en Erl
  con `@Exp` y variables locales, sin un menos tras `*`) si el PMV del paso anterior está en el límite superior o por
  encima, o por debajo del inferior, por la duración del paso. Los límites son las consignas del índice sin
  tolerancias en la escala del PMV, con la inversa del índice con la que los termostatos reciben las suyas
  (`ppd_weighted_hours_lines`, `PPD_WEIGHTED_HOURS_OUTPUTS`, `zone_outputs(..., ppd_weighted_hours=True)`;
  provisional en `notes/questions.md`). Sin el argumento, los IDF no cambian. El reductor `ppd_weighted_hours` del
  paramétrico la lee; en el paramétrico, `report_long_term_discomfort=True` con `'apmv setpoints'` y
  `'epmv setpoints'` la añade (antes no hacía nada con ellos) y `long_term_range` da un `ValueError`. `Table` la llama
  `<zona>_PPD Weighted Hours (h)`; la comprobación 3 de `verify_accim_simulation`, `Check3_PpdWeightedHours`; la GUI
  tiene su casilla en la pestaña de las consignas basadas en el PMV.
- `ppd_weighted_hours` de D1: rango semiabierto, PMVlímite,inferior ≤ PMV < PMVlímite,superior (veredicto #20).
- `Table` compara la frecuencia de las columnas sin mayúsculas, da a cada hora los pasos que terminan en ella (los de
  00:10 a 01:00 son la hora 00:00–01:00), comprueba la agregación con los pasos de cada hora y, con
  `frequency='timestep'`, solo resta una hora a los pasos que terminan una hora. La sección 4.7.4 explica por qué sus
  indicadores no son los contadores del EMS (la temperatura del paso anterior, por paso).
- Páginas de la API de `accim.sim.ems.long_term_discomfort` y `accim.sim.schedule_files`, que faltaban.
- Pruebas: `tests/core/test_long_term_discomfort_counters.py` (los límites, el Erl frente a D1, los modelos, AddAccis y
  EnergyPlus con los dos backends y la comprobación 6), `tests/core/test_ppd_weighted_hours.py` (nueva: el Erl frente a
  D1 con los tres índices y sus opciones, los modelos, EnergyPlus con los dos backends y la comprobación 3),
  `tests/core/test_long_term_discomfort.py` (el método C semiabierto y `Table` por pasos),
  `tests/core/test_table_pmv_index.py`, `tests/core/test_gui.py` y
  `tests/parametric_and_optimisation/test_objectives.py`.

## 35. La saturación, las frecuencias y los rangos del gancho del ATHB (H4)

Tarea H4 de la revisión v04 (hallazgos A4-1 a A4-3 y el de las pruebas de §3.4).

**Antes.** Las consignas del ATHB fuera de `temperature_range` (10–30 °C) eran sus límites sin que nada lo dijera;
`apply_athb_setpoints(output_frequencies=('hourly',))` no seguía las frecuencias del modelo; `met = 0` se aceptaba; la
relación entre el nivel de actividad de los People (W/persona) y `met`, y que `air_speed` es la velocidad relativa, no
estaban documentadas; la prueba con EnergyPlus solo comprobaba −3 ≤ ATHB_PMV ≤ 3.

**Ahora.**

- `AthbSetpointHook`: la salida sumada `ATHB_saturated_<zona>` (la duración del paso si una consigna está en un límite
  del rango; el método `saturated`), las horas fuera de los días de calentamiento (`saturated_hours`) y los métodos
  `prepare()` (las pone a cero) y `finish()` (avisa de ellas), que `run_simulation` llama antes y después de cada
  simulación (`accim.sim.energyplus_api.finish_hooks`, nueva). En los procesos de `run_ep`, el aviso va a su consola y
  las salidas guardan las horas.
- `apply_athb_setpoints(output_frequencies=None)`: por defecto, las frecuencias de las salidas EMS del modelo, como los
  ganchos de la SET (cambia los IDF que se preparaban con el valor por defecto anterior, `('hourly',)`, si el modelo
  tiene otras).
- `met` > 0 (`ValueError`); avisos fuera de 0,8–4 met (`accim.constants.PMV_MET_RANGE`, nueva) y por encima de 1 m/s
  (ISO 7730:2025, §4).
- `Table`: `<zona>_ATHB_saturated (h)`, sumada, con valores de bloque y de edificio, fuera de la tabla de horas de
  confort.
- Documentación (4.9.1, 4.7.5 y docstrings): 1 met = 58,2 W/m² × 1,8 m² ≈ 104,8 W/persona (la superficie corporal de
  EnergyPlus, Input Output Reference, campo *Activity Level Schedule Name* de `People`) y la velocidad relativa,
  v + 0,3·(met − 1) por encima de 1 met (`pythermalcomfort.utilities.v_relative`).
- Pruebas: `tests/core/test_comfort_hooks.py` (la saturación con un controlador falso, el aviso, `prepare`, los avisos
  de met y velocidad, las frecuencias por defecto; con EnergyPlus 25.1, la afirmación acotada: el ATHB_PMV a 0,25 o
  menos de la consigna de refrigeración en al menos el 95 % de los pasos ocupados con la batería de frío encendida, el
  ATHB_PMV frente al de las salidas del paso anterior, y las horas saturadas con un rango hasta 27,5 °C) y
  `tests/core/test_table_optional_outputs.py`.

## 36. La métrica exterior de cada régimen y los regímenes de las normas de confort definidas por sus datos (H5)

Tarea H5 de la revisión v04 (decisiones 1 y 4 de su §6; hallazgos B2-1 y B2-2).

**Antes.** `CustomRegime(outdoor_metric=...)` daba un `ValueError` salvo con `None`: todos los regímenes usaban la
métrica exterior de la zona. Una norma de confort definida por sus datos tenía un solo régimen `'always'` (un
`ValueError` con varios). La documentación no decía que `CustomRegime_<zona>` horario es un promedio ni que las
condiciones `'hvac_off'`/`'hvac_on'` pueden alternar de un paso al siguiente.

**Ahora (métrica de cada régimen, B2).**

- `CustomRegime` tiene `outdoor_metric`, `alpha` y `days` (`None`: los de la zona; `alpha` y `days` necesitan
  `outdoor_metric`) y la propiedad `metric_spec`. Las condiciones comparan la métrica de la zona; la temperatura de
  confort, las consignas, la aplicabilidad y los contadores del régimen usan la suya.
- `SetOutdoorMetric_<zona>` calcula en cada paso la métrica de cada régimen con una propia,
  `ToutRegime_<régimen>_<zona>` (con su media móvil de EN 16798-1, `RMOTr_<régimen>_<zona>`, si tiene su propio alfa,
  que empieza con el EPW como la de la zona). La rama del régimen en `SelectCustomRegime_<zona>` fija las entradas de
  su métrica (`CustAST_metric`, y `CustAST_alpha`/`CustAST_days` si se dan) y `Tout_metric`; tras la cadena,
  `Tout_metric_<zona>` es la métrica del régimen del paso. `parse_regime_program` lee estas líneas con validación
  estricta.
- Los modelos con estos regímenes tienen el código EMS de la métrica exterior aunque las zonas tengan `'pmot'`; sus
  programas se conservan mientras calculan las métricas de los regímenes de cada zona y se reescriben si cambian (sin
  `epw`, empezando con PMOT y con aviso si empezaban con un EPW). `'monthly_mean'` necesita `epw` (`ValueError`
  temprano en `AddAccis`). Una zona que `modify_accis` pasa a otra norma pierde sus regímenes si alguno tiene métrica
  propia (cambiaría el `Tout_metric` que leen otras normas); si no, los conserva, como antes.
- `print_setpoint_ems_code`, `get_setpoint_ems_programs`, `compute_setpoints`, `verify_accim_simulation` (comprobación
  4), el paramétrico (los regímenes conservan su métrica) y la GUI (`outdoor_metric=rmot_alpha alpha=0.7` tras los
  coeficientes de un régimen) los admiten. Los IDF sin estos regímenes no cambian (golden master).
- Documentación (4.2.4 y el módulo `accim.sim.ems.custom_regimes`): B2-2, `CustomRegime_<zona>` promediado en una hora
  no es entero cuando el régimen cambia dentro de ella (solo la frecuencia de paso da el régimen de cada paso); B2-1,
  `'hvac_off'`/`'hvac_on'` leen el HVAC del paso anterior y el régimen que eligen cambia las consignas que deciden si
  el HVAC funciona, así que los regímenes pueden alternar (no hay tiempo mínimo en un régimen).

**Ahora (varios regímenes de una norma de confort, B3).**

- Clave `regimes` de los YAML, en lugar de `comfort_temperature` y `applicability` (`ValueError` con ambas): una lista
  de regímenes con los campos de `CustomRegime` (los ocho coeficientes, obligatorios; `condition`, `outdoor_metric`,
  `alpha` y `days`, opcionales; las condiciones con valor son listas, `[metric_below, 10]`), en su orden de prioridad.
  El último debe ser `'always'` (la norma no tiene otros coeficientes cuando ninguna condición se cumple) y
  `'hvac_off'`/`'hvac_on'` son solo del modelo personalizado (`ValueError`). Una temperatura de confort y una
  aplicabilidad son un único régimen `'always'`, cuyo código EMS no cambia.
- Con varios regímenes, o un régimen con métrica propia (`accim.sim.ems.standard_lines.uses_regimes`), el código EMS
  de la norma es el del modelo personalizado: sus ramas leen las entradas de este (`Tout_metric*m+n`,
  `CustAST_ACSTaul`..., y los desplazamientos de cada categoría más `CustAST_ACSToffset`/`CustAST_AHSToffset`), sus
  zonas reciben `SelectCustomRegime_<zona>` con sus regímenes y la salida `CustomRegime_<zona>`, y su métrica es
  `Tout_metric` (el modelo tiene el código EMS de la métrica también con `'pmot'` y `'rmot'`).
- Sus zonas reciben sus regímenes sea cual sea `custom_regimes` (`custom_regimes.standard_regimes`;
  `set_custom_regimes` los escribe) y los pierden cuando `modify_accis` o `param_accis.modify_ComfStand` les da otra
  norma (`set_standard_regimes`, nueva); `param_accis.modify_custom_regime` solo cambia los del modelo personalizado.
- `print_setpoint_ems_code` imprime los regímenes y su programa; `compute_setpoints` lo ejecuta (las consignas son las
  del modelo personalizado con los mismos regímenes); la comprobación 4 de `verify_accim_simulation` pasa
  `custom_regimes` solo en las zonas del modelo personalizado.
- Documentación: 4.2.5 (la clave `regimes`, con un ejemplo) y 4.2.4.

**Pruebas.** `tests/core/test_regime_metrics.py` (nuevo: las líneas y su lectura, las métricas de los regímenes, un
régimen `'always'` con métrica propia igual a la zona con esa métrica para las 7 métricas, las condiciones con la
métrica de la zona, `AddAccis`/`modify_accis`, los programas conservados con el EPW, y con EnergyPlus 25.1 la
comprobación 4 sin discrepancias y ambos backends idénticos); `tests/core/test_standard_regimes.py` (nuevo: el YAML con
regímenes y sus errores, las líneas EMS, `compute_setpoints` igual al del modelo personalizado con los mismos
regímenes, `AddAccis`/`modify_accis`, y con EnergyPlus 25.1 la comprobación 4 sin discrepancias y ambos backends
idénticos); `tests/core/test_custom_regimes.py`, `tests/core/test_comfort_standard_registry.py`,
`tests/core/test_gui.py` y `tests/parametric_and_optimisation/test_registered_comfort_standards.py`.

## 37. La vestimenta en función de la temperatura exterior (H6)

Tarea H6 de la revisión v04 (A5, decisión de su §6).

**Antes.** `set_pmv_input_parameters` aceptaba para `clothing_insulation` un número, un diccionario por estación o
`'dynamic_ashrae55'`; la vestimenta en función de la temperatura exterior (`callable(rmot) -> clo`) estaba bloqueada.
`read_epw_dry_bulb` (E1) leía los EPW como UTF-8, y el `Seville.epw` de los archivos de ejemplo, cuya cabecera tiene
caracteres en otra codificación, paraba `outdoor_metrics` y `compute_setpoints` con un `UnicodeDecodeError`.

**Ahora.**

- `clothing_insulation` puede ser una función: recibe una `pandas.Series` con los valores horarios de una columna de
  `accim.sim.preview.outdoor_metrics(epw)` (`clothing_outdoor_metric`, `'RMOT'` por defecto, la media móvil de
  EN 16798-1 con α = 0,8; las demás en `CLOTHING_OUTDOOR_METRICS`) y devuelve la vestimenta de cada hora. accim la
  escribe en un CSV en la carpeta del modelo (con el nombre de la schedule, del EPW y 8 caracteres del SHA-1 de los
  valores) que lee un `Schedule:File` `Sch_Clo_<people>` (`accim.sim.schedule_files`), en lugar del
  `Schedule:Compact`; un número o un diccionario vuelven a escribir el `Schedule:Compact` y quitan el `Schedule:File`.
- `clothing_insulation_values(función, epw, outdoor_metric)` da los valores sin modelo; `ValueError` (antes de cambiar
  el modelo) sin `epw`, con una función para otro parámetro, con valores negativos o no numéricos o sin un valor por
  hora; avisos fuera de 0–2 clo (ISO 7730:2025) y por encima de 1,5 clo (ASHRAE 55-2020).
- `read_epw_dry_bulb` lee los EPW como Latin-1 (cuyos bytes son todos caracteres; los registros son ASCII).
- Documentación (4.8): la función, su temperatura exterior y su archivo, y que EnergyPlus 25.1 informa de *Zone Thermal
  Comfort Clothing Value* solo con los métodos `DynamicClothingModelASHRAE55` y `CalculationMethodSchedule` (0 con
  `ClothingInsulationSchedule`, cuyo PMV usa la schedule igualmente: la salida *Schedule Value* de `Sch_Clo_<people>`
  da la vestimenta).
- Pruebas: `tests/core/test_pmv_input_parameters.py` (la función de RMOT y de `Tout`, el archivo y sus campos, la
  sustitución entre función, número y diccionario, los valores por zona, los errores sin cambiar el modelo, los avisos;
  con EnergyPlus 25.1, la *Schedule Value* y la vestimenta del método `CalculationMethodSchedule` iguales a la función
  hora a hora en una semana de enero y otra de julio, con el horario de verano del modelo) y
  `tests/core/test_preview.py` (un EPW con la cabecera en Latin-1).

## 38. El aviso del mínimo y el máximo de las consignas, con las consignas del modelo de confort (S1, decisión 19)

La revisión de Claude Science del 11/11/2026 (`notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §2.2) encontró que el
veredicto 13 de la v04, que G5 aplicó al pie de la letra, comparaba el mínimo de calefacción y el máximo de refrigeración
con `ACSTaul` y `AHSTall`, que son límites de aplicabilidad de la métrica exterior (10 y 30 °C en INT EN16798), no
consignas: el aviso solo saltaba con valores extremos, mientras que las consignas pueden cruzarse con valores corrientes
(un mínimo de 24 °C por encima de una consigna de refrigeración de 23,5 °C en invierno). La decisión 19 elige la opción
(ii) de la pregunta: comparar con las consignas del modelo de confort de cada zona con el archivo climático.

**Antes.** `warn_crossed_setpoint_limits(idf)` ejecutaba `SetInputData_<zona>` y `SetAppLimits` con el intérprete de
Erl y avisaba si el mínimo superaba `ACSTaul` o el máximo bajaba de `AHSTall`.

**Ahora.**

- `accim.sim.ems.setpoint_limits.warn_crossed_setpoint_limits(idf, epw=None)`: sin `epw`, no avisa (las consignas de la
  mayoría de los modelos de confort dependen de la temperatura exterior). Con él, calcula para cada zona con mínimo o
  máximo las consignas de su modelo de confort con `accim.sim.preview.compute_setpoints` y los argumentos de la zona
  (los de su `SetInputData_<zona>` sin el mínimo ni el máximo, con la función de la comprobación 4 de
  `verify_accim_simulation`, y los regímenes de su `SelectCustomRegime_<zona>` en el modelo personalizado), por pasos de
  tiempo, con los pasos por hora del modelo, desde el primer día de su primer `RunPeriod` hasta el último (o hasta el
  final del año si el periodo sigue en el siguiente), y con la métrica exterior del modelo personalizado empezando como
  empiezan sus programas. Compara las consignas de los termostatos (`ACST`/`AHST`, con tolerancia y redondeadas): un
  aviso por zona si el mínimo es mayor o igual que la consigna de refrigeración en algún paso, o el máximo menor o igual
  que la de calefacción, con el límite, la consigna extrema, el número de días con cruce y el primero. El primer paso del
  periodo lee medias móviles 0, como en EnergyPlus, así que cuenta (en el modo 3 de INT EN16798, la consigna de
  refrigeración de una media por debajo de los límites).
- Se dejan fuera, con un mensaje de depuración del logger del módulo (el primer uso de `logging` en accim), las zonas
  cuyas consignas da un gancho de la API, las que tienen el limitador de la deriva, las que `compute_setpoints` rechaza
  (las condiciones `'hvac_off'`/`'hvac_on'`, un EPW que no es de 365 días...) y los modelos sin `RunPeriod` o sin
  `Timestep`.
- `AddAccis` (cada IDF de salida) y `modify_accis` le pasan su `epw`; el `ValueError` de un mínimo no menor que el máximo
  se mantiene. Los IDF no cambian.
- Documentación: docstrings del módulo, de `AddAccis` y de `modify_accis`, y la sección 4.2.3 del uso detallado. Las
  elecciones de detalle (qué consignas, qué días, cuándo compara `modify_accis`) están en `notes/questions.md`.
- Pruebas (`tests/core/test_setpoint_limits.py`, 4 nuevas en lugar de la del aviso literal): sin cruce y sin EPW, sin
  aviso (y el modelo no cambia); con un mínimo de 24,5 °C y un máximo de 25,5 °C en Sevilla (INT EN16798, categoría I,
  modo 3), un aviso por zona con los números que da un cálculo por días con pandas; solo el mínimo de una zona; el
  periodo de junio a agosto del modelo (el mínimo de 24 °C solo cruza en su primer paso); las zonas con gancho y con
  limitador, y el modelo sin `RunPeriod`, con sus mensajes de depuración; y `AddAccis` con y sin EPW, con los mismos IDF
  de salida.

## 39. Las consignas estáticas del YAML de Qatar (S2, decisión 20)

La revisión de Claude Science del 11/11/2026 (`notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §2.2) encontró que la v04
(§6.3) daba al YAML de Qatar las consignas estáticas 20 y 25,5 °C citando la tabla B.2 de EN 16798-1 (oficinas,
categoría II), cuyos valores son 20 y 26 °C (`accim.constants.EN16798_TABLE_B2`); 25,5 °C es la consigna de
refrigeración de la categoría I. G5 aplicó los números de la v04 y dejó la discrepancia en `notes/questions.md`.

**Ahora.**

- `qat_indraganti2018_hvac.yaml` (las dos copias: la de `comfort_standards` y la del cuaderno How-to del registro):
  `static_setpoints: {heating: 20.0, cooling: 26.0}`, con el comentario y la evidencia corregidos. Afecta a los modos de
  confort 0 y 1 de la norma 102 (los que usan las consignas estáticas).
- `tests/core/test_comfort_standard_registry.py`: las consignas estáticas son (20,0, 26,0) y las de la tabla B.2 de las
  oficinas de la categoría II.
- Documentación: la sección 4.2.5 del uso detallado y la entrada del CHANGELOG del registro; el cuaderno How-to
  `using_comfort_standard_registry` (su texto, y ejecutado y exportado de nuevo, con la evidencia de Qatar actualizada).

## 40. La referencia del modo 'rate' del limitador de la deriva (S3, decisión 13)

La decisión 6 del autor (bloque F) dice que, en el modo `'rate'`, «el estado es la consigna aplicada del día anterior».
F2 tomó la del último paso del día anterior (decisión provisional). La decisión 13 la cambia por la media de las
consignas aplicadas en los pasos ocupados del día anterior: es la misma con consignas constantes en el día (las del
ACCIS) y representa mejor las de un gancho, que cambian dentro del día (el SET del estándar 24 con la humedad y la
temperatura radiante de la zona). Los días sin pasos ocupados conservan la referencia del último día ocupado, como
T_rm_in (decisión 14).

**Antes.** `ApplyDriftLimiter_<zona>` guardaba en cada paso la consigna aplicada (`DriftLastAHST_<zona>`,
`DriftLastACST_<zona>`) y, al cambiar `DayOfYear`, la copiaba en la referencia (`DriftRefAHST_<zona>`,
`DriftRefACST_<zona>`), también tras los días sin ocupantes.

**Ahora.**

- `accim.sim.ems.drift_limiter.program_lines`: en los pasos ocupados (`Occ_count_<zona>` > 0, fuera del calentamiento),
  tras los límites, suma las consignas aplicadas en `DriftSumAHST_<zona>` y `DriftSumACST_<zona>` (con el mismo
  contador `n_occ_<zona>` que la temperatura operativa); al cambiar `DayOfYear`, si el día tuvo pasos ocupados, la
  referencia es su media (si no, se conserva) y los acumuladores vuelven a 0. Las variables `DriftLast*` desaparecen
  (`_STATE`, y por tanto `InitDriftLimiter`). Los modelos de versiones de desarrollo con el programa anterior lo
  reciben nuevo cuando se escribe de nuevo el código del limitador (`set_drift_limiter_code`).
- Comprobado: con consignas constantes en los pasos ocupados de cada día, la media es la consigna del final del día,
  así que los resultados no cambian (el test del escalón de 5 K en 10 días sigue igual; en EnergyPlus, la consigna del
  ACCIS es constante en los pasos ocupados de cada día de la oficina de ejemplo y su media es la del último paso).
  Cambian tras los días sin ocupantes: la referencia es la del último día ocupado (el test del día sin ocupantes se ha
  ajustado a la decisión 14).
- Documentación: el docstring del módulo y de `AddAccis`, la sección 4.2.7 del uso detallado y el CHANGELOG.
- Pruebas (`tests/core/test_drift_limiter.py`): con el intérprete de Erl, un gancho cuyas consignas suben 0,25 K por
  hora (la referencia es la media de las horas ocupadas, 23,125 °C, no la del último paso, 25,75 °C); con EnergyPlus
  25.1, del lunes 1 al martes 9 de abril, las mismas consignas dadas por un gancho de Python (backend de la API) y por
  las líneas equivalentes al principio de `RunACCIS_<zona>` (backend EMS): resultados idénticos (`check_exact`), la
  regla de la media comprobada día a día con pandas (también el fin de semana sin ocupantes) y el límite activo; y la
  prueba de los dos backends del limitador comprueba la nueva referencia.

## 41. Los indicadores de la banda causal con el SET de pythermalcomfort (S4, decisión 9, provisional)

El texto de Sun, Brager y Schiavon (2026) no dice qué implementación del SET usaron (pregunta para Ruiji Sun). La
decisión 9, provisional, mantiene el SET del modelo Pierce de EnergyPlus en los indicadores de F3 y pide añadir,
detrás de un argumento desactivado por defecto, los mismos indicadores con el SET de pythermalcomfort (`set_tmp`, con
`set_of_results` de G3 y las entradas que comparó E-F1), porque E-F1 midió diferencias del orden de lo que mueve las
horas cerca de los bordes de la banda de 19,1 a 28,2 °C.

**Antes.** `table_indicators` daba los indicadores de la banda causal solo con el SET del modelo Pierce.

**Ahora.**

- `accim.data.postprocessing.indoor_adaptation.table_indicators(..., pythermalcomfort_set=None)`: con un diccionario
  de las entradas de los ocupantes (`met`, `clo`, `air_speed` y, opcional, `position`, por defecto la postura de los
  ganchos: sentado con 1,2 met o menos) o un gancho del SET con ellas, añade `<zona>_Mean SET_pythermalcomfort (°C)`,
  `<zona>_Mean TSV_causal_pythermalcomfort`, `<zona>_Hours In Causal Band_pythermalcomfort (h)`, `... Above ...`,
  `... Below ...` y `(%)` tras los indicadores de cada zona, y los del edificio tras los suyos
  (`PYTHERMALCOMFORT_SET_INDICATORS`). Las demás columnas no cambian; sin el argumento, la salida es la misma.
- El SET es el de `set_of_results` de las salidas *Zone Mean Air Temperature*, *Zone Mean Radiant Temperature* y *Zone
  Air Relative Humidity* de cada zona (con su nombre en la tabla como clave) en cada fila del CSV de cada simulación
  (la columna `Source` con `.csv`, en la carpeta actual), promediado en las filas del CSV de cada fila de la tabla (los
  pasos de cada hora, como `Table` promedia el SET de Pierce; la hora de cada fila como la da `Table`: la de la
  etiqueta de EnergyPlus, menos 1 en las que acaban una hora). Las zonas sin esas salidas dan NaN, con un aviso; un
  CSV que no está, un `ValueError`.
- Las entradas de los ocupantes son constantes (como en `set_of_results`); E-F1 usó las de los horarios de los objetos
  People en cada paso, así que con una vestimenta estacional o dinámica los dos SET no tienen las mismas entradas
  (documentado; la opción de leerlas de los horarios queda en `notes/questions.md`, con el resto de las elecciones de
  diseño).
- Documentación: el docstring del módulo y de `table_indicators`, la sección 4.7.6 del uso detallado y el CHANGELOG.
- Pruebas (`tests/core/test_indoor_adaptation.py`, con un SET de prueba que depende de todas sus entradas, porque numba
  no carga en el servidor): las columnas nuevas y su orden, las demás iguales, los valores de cada zona y del edificio
  desde las fórmulas, el gancho como entrada, la postura y `tsv_limit`; una tabla horaria y otra de pasos de un CSV de
  dos pasos por hora; los errores y el aviso; con la simulación de EnergyPlus 25.1 del test de los indicadores, los
  valores de cada hora del CSV real; y una prueba con pythermalcomfort, que se salta sin él.

## 42. Las notas de las decisiones aceptadas 1, 7, 16 y 22 (S5)

Los veredictos del 11 de noviembre aceptaron estas decisiones con una instrucción; ninguna cambia el código de accim.

- **Decisión 1 (H6).** La sección 4.8 del uso detallado tiene un ejemplo de función de la vestimenta con la columna
  `'Tout'` (`clothing_outdoor_metric='Tout'`) para los modelos de la temperatura exterior de las 6:00: el de ASHRAE
  55-2020, figura 5-1 (1,00 clo por debajo de −5 °C; 0,818 − 0,0364·ta6 de −5 a 5 °C;
  10^(−0,1635 − 0,0066·ta6), la ecuación 4 de Schiavon y Lee, 2013, de 5 a 26 °C; 0,46 clo desde 26 °C). La serie
  tiene las 24 horas de cada día en orden y la sexta acaba a las 6:00, así que la función da a cada día la vestimenta
  de su temperatura de las 6:00 (de 0,47 a 0,89 clo con `Seville_Present.epw`). Prueba nueva en
  `tests/core/test_pmv_input_parameters.py`: los valores de la propuesta A5 en −10, 0, 10, 20 y 30 °C, la hora de las
  6:00 por su fecha y el rango de la documentación.
- **Decisión 7 (H2).** Los objetos `Schedule:File` de accim (T0 de `'te_ref_nl'`, `ACCIS Outdoor Mid Range`; y la
  vestimenta de una función, `Sch_Clo_<people>`, H6) tienen la ruta absoluta de su CSV: un IDF simulado en otro
  ordenador, o tras mover su carpeta, no lo encuentra, y EnergyPlus 25.1 se detiene antes de simular con el error
  grave `Schedule:File="...", File Name: "..." not found` (comprobado el 11 de noviembre). Documentado en las
  secciones 4.2.2 y 4.8 y en el CHANGELOG; el modo relativo es una entrada P2 de `TODO.md`.
- **Decisión 16 (F1).** Los modos 0 y 3 del estándar 24 ya daban un `ValueError` claro, que nombra los modos 1 y 2:
  prueba nueva en `tests/core/test_sun2026_set.py` con `sun2026_set_setpoints`, `Sun2026SetpointHook` y
  `apply_sun2026_setpoints` (0, 3, '0' y 0.0; el modelo no cambia).
- **Decisión 22 (G4).** En el primer paso de cada día, el EMS lee las medias móviles de EnergyPlus del día anterior,
  así que las consignas de ese paso llevan un día de retraso; afecta al estándar 23 sin el EPW y también al 1 (RMOT)
  y, menos, a los de PMOT. Medido con `compute_setpoints` y `Seville_Present.epw` desde el 1 de enero: la temperatura
  de confort del primer paso de cada día es exactamente la del día anterior, hasta 0,44 K (1) y 0,51 K (23) distinta de
  la del resto del día (el 2 de mayo; 0,12 y 0,13 K de media desde el día 9) y hasta 0,13 K con PMOT (2). Documentado en
  la sección del estándar 23 (donde se describe la prueba de 23 frente a 101), en la de `compute_setpoints` y en el
  CHANGELOG.

## 43. Correcciones de la autoauditoría de la sesión 2

La autoauditoría de la sesión 2 (`notes/attachments/autoauditoria_sesion2_v1.2.0.json`, hallazgos A1–A26) se corrige
según el §7 de `notes/COPILOT_SIGUIENTE_SESION.md`: cada hallazgo de tipo bug o científico con un arreglo sin decisión
del autor, en su commit, con una prueba que falla antes y pasa después; los de diseño, prueba, documentación o menores,
en grupos si el arreglo es pequeño; el resto, en `notes/questions.md` o `TODO.md`.

### A7. Las horas saturadas del gancho del ATHB, solo las del periodo de simulación

**Antes.** `AthbSetpointHook` sumaba las horas con una consigna en un límite de `temperature_range`
(`saturated_hours`, y el aviso de `finish()`) «fuera de los días de calentamiento» con `controller.get('WarmupFlag')`;
pero el controlador del backend de la API solo actualiza las variables integradas que leen los programas EMS del
modelo, y ningún programa de un modelo del ACCIS sin la métrica exterior del modelo personalizado ni el limitador de
la deriva lee `WarmupFlag`: la variable era `None` y se sumaban también los días de calentamiento y los periodos de
dimensionado (los días de diseño).

**Ahora.** `accim.sim.comfort_hooks._in_run_period(controller)` lo pregunta a la API de EnergyPlus (`kind_of_sim`,
3 en los periodos de simulación del archivo climático, y `warmup_flag`); con un controlador sin la API (las pruebas),
`WarmupFlag`. Las salidas `ATHB_saturated_<zona>` no cambian (son de cada paso).

- Pruebas (`tests/core/test_comfort_hooks.py`): una unitaria con un controlador cuya API dice el tipo de simulación y
  el calentamiento, sin la variable `WarmupFlag` (como el controlador real), que falla sin el arreglo (contaba el
  calentamiento) y pasa con él; y otra con EnergyPlus 25.1 y el controlador real (dos días de julio del modelo de
  ejemplo): cuentan exactamente los 288 pasos del periodo de simulación, y quedan fuera los días de diseño y los de
  calentamiento.
- Documentación: el docstring de la clase, la sección 4.9.1 y la entrada del ATHB del CHANGELOG.

### A3. El gancho del SET con la vestimenta dinámica añade el modelo Pierce

**Antes.** `apply_set_setpoints(..., clo=None, method='bisection')` en un modelo cuyos objetos People usan la
vestimenta dinámica (`DynamicClothingModelASHRAE55`, o `CalculationMethodSchedule`) añadía los sensores
`SET_CloValue_<zona>` de la salida *Zone Thermal Comfort Clothing Value*, que EnergyPlus solo da para los objetos
People con el modelo Fanger, Pierce o KSU; los modelos del ACCIS con consignas de temperatura solo tienen
AdaptiveASH55 y AdaptiveCEN15251, así que EnergyPlus se detenía antes de simular (en los dos backends).
`apply_sun2026_setpoints` ya añadía el modelo Pierce.

**Ahora.** Con `clo=None` y la vestimenta dinámica en alguna zona, `apply_set_setpoints` añade el modelo Pierce a los
objetos People (`add_thermal_comfort_model`, que comprueba antes de cambiar nada) salvo si todos tienen ya Fanger,
Pierce o KSU (`_needs_comfort_model`, con los objetos People:Definition de EnergyPlus 26.2); comprueba antes los
horarios que el modelo Pierce necesita (`_people_inputs(..., pierce=True)`: eficiencia y velocidad del aire). Los
modelos que ya funcionaban no cambian.

- Pruebas (`tests/core/test_sun2026_set.py`): los objetos People reciben Pierce con la vestimenta dinámica, no si ya
  tienen Fanger ni con la vestimenta dada, y el error sin el horario de eficiencia (sin cambiar el modelo); y el modelo
  preparado corre en EnergyPlus 25.1 sin el gancho (backend EMS, un día de julio). Las dos fallan sin el arreglo
  (EnergyPlus terminaba con un error fatal) y pasan con él.
- Documentación: el docstring de `apply_set_setpoints`, la sección 4.9.2 y la entrada del SET del CHANGELOG.

### A12. La temporada de refrigeración de los indicadores de la adaptación interior que cruza el fin de año

**Antes.** `table_indicators` tomaba la temporada de refrigeración como `(día >= inicio) & (día < fin)`, así que una
temporada que sigue en el año siguiente (inicio después del fin, como el ACCIS admite para el hemisferio sur) no tenía
ningún día, y las horas de sobreenfriamiento eran 0 (y su porcentaje NaN). Además, `Table` usa siempre 1 de mayo a 30
de septiembre, sin que la documentación lo dijera.

**Ahora.** `_cooling_season` sigue las líneas del ACCIS (`COOLING_SEASON_LINES`): la unión si el inicio es posterior
al fin, ningún día si son iguales. La sección 4.7.6 y el docstring dicen que `Table` usa los valores por defecto y que
`table_indicators` toma los de las simulaciones. Prueba en `test_the_arguments_of_the_indicators` (del 27 de octubre al
1 de mayo, o al 30 de abril, y una temporada vacía), que falla sin el arreglo (0 h) y pasa con él.

### A13. La fuente de los 22 °C del sobreenfriamiento

**Antes.** El docstring del módulo de los indicadores de la adaptación interior, `OVERCOOLING_TEMPERATURE`,
`overcooling_hours` y la sección 4.7.6 atribuían el umbral de 22 °C a Parkinson, Schiavon, de Dear y Brager (2021),
*Overcooling of offices...*, Scientific Reports 11, como la propuesta del bloque F; ese artículo estudia el
sobreenfriamiento pero no da ningún umbral de temperatura.

**Ahora.** Citan Parkinson, de Dear y Brager (2020), Energy and Buildings 206, 109559, sección 4.3.2: la consigna
habitual de verano de las oficinas climatizadas, «current summertime practices (~22 °C)» (comprobado en el texto de
ambos artículos de la biblioteca). El valor sigue siendo una decisión de diseño de la propuesta; nota en la decisión
de F3 de `notes/decisions.md`. Solo cambia la documentación (sin prueba: es una cita).

### A9. La ventana del limitador de la deriva, no más estrecha que el doble de la tolerancia

**Antes.** Con `drift_mode='window'`, donde las dos consignas llegan a los límites de la ventana (T_rm_in − `delta_heat`
y T_rm_in + `delta_cool`), los termostatos las reciben con la tolerancia (la de calefacción subida y la de
refrigeración bajada), así que con `delta_heat + delta_cool` menor que el doble de la tolerancia se cruzaban (la de
calefacción por encima de la de refrigeración); se aceptaba sin error ni aviso (también en la GUI y en el módulo
paramétrico).

**Ahora.** `accim.sim.ems.drift_limiter.check_window_width` da un `ValueError` en ese caso: `AddAccis` lo comprueba con
la mayor tolerancia de los IDF de salida (y la de cada zona de `zone_arguments`), y `modify_accis` con la tolerancia
que tendrá cada zona y sus deltas (los dados o los que tiene), antes de cambiar nada; los planes del módulo paramétrico
(`drop_invalid_param_combinations`) quitan esas filas. El cruce cuando toda la banda queda fuera de la ventana es
el hallazgo A8 (diseño, en `notes/questions.md`).

- Pruebas: `test_the_window_cannot_be_narrower_than_twice_the_tolerance` (`tests/core/test_drift_limiter.py`: la
  función, `modify_accis` con su tolerancia, con la de una zona y con una tolerancia mayor después, sin cambiar el
  modelo, y `AddAccis` con la mayor tolerancia de la serie y con una zona) y
  `test_the_plans_drop_the_windows_narrower_than_twice_the_tolerance` (el plan paramétrico, también con `ASTtol`); fallan
  sin el arreglo y pasan con él.
- Documentación: la sección 4.2.7, la entrada del limitador del CHANGELOG y el docstring de
  `drop_invalid_param_combinations`.

### Grupo de documentación: A14, A16, A17, A18, A20, A22, A24 y A26

Correcciones pequeñas de la documentación, sin cambios del código (un commit):

- **A14.** El docstring de `indoor_running_mean` decía que, por pasos, T_occ_mean es la media del EMS del limitador; es
  la del EMS salvo un paso (el EMS lee la temperatura operativa del paso anterior): con la temperatura desplazada una
  fila, la función da la T_rm_in del EMS (la auditoría lo midió: diferencia ≤ 1,1e-14 K).
- **A16.** El CHANGELOG y la sección 4.9.1 decían que el ATHB_PMV estaba «dentro de 0,25» de la consigna de
  refrigeración; la prueba comprueba una cota superior (como mucho 0,25 por encima, en el 95 % de los pasos ocupados con
  la batería de frío encendida): ahora lo dicen así.
- **A17.** La firma de `apply_athb_setpoints` del CHANGELOG decía `output_frequencies=('hourly',)`; es `None` desde H4.
- **A18.** El YAML de Qatar (las dos copias) decía que el artículo no da la α de su media móvil y tomaba 0,8 de
  EN 16798-1 como elección; el artículo la da (ecuación 4: «we used the value of 0.8 in this analysis», comprobado en
  su texto): el comentario, la evidencia (`alpha: "0.8, that of the article (its equation 4)"`), la cita completa
  (Energy and Buildings 159, 201-212, doi:10.1016/j.enbuild.2017.10.087), la sección 4.2.5, el texto del cuaderno
  How-to del registro (ejecutado y exportado de nuevo con `docs/prepare_howto_notebooks.py`, 63 s, 0 problemas) y el
  CHANGELOG. El valor no cambia.
- **A20.** El docstring de `format_number` decía que todos los módulos lo usan; las entradas de `SetInputData_<zona>` se
  escriben con `str(valor)` (con exponente en algunos números, `5e-05`), que EnergyPlus lee igual: comprobado con
  EnergyPlus 25.1 (un programa con `set TestExpA = 5e-05*100000` dio 5 y `-1E-05*100000+2.5e+1`, 24).
- **A22 y A26.** Con los IDD de EnergyPlus 9.4 y 9.6, los `Schedule:File` no tienen el campo *Adjust Schedule for
  Daylight Savings*, y EnergyPlus los desplaza una hora durante el horario de verano: el T0 de `'te_ref_nl'` de la
  última hora de cada día es el del día siguiente, y la vestimenta de una función, la de la hora siguiente. Documentado
  en el docstring de `accim.sim.schedule_files`, las secciones 4.2.2 y 4.8 y el CHANGELOG (las opciones de un aviso o de
  desplazar el CSV quedan en `TODO.md`).
- **A24.** La sección 4.2.1 decía que los modelos de `add_accis_to_idf` tienen el código de todos los estándares (para
  editar el estándar de una zona); una zona que pasa al 23 editando su programa necesita también `StaticAHST` y
  `StaticACST` (si no, EnergyPlus se detiene): documentado; el arreglo del código choca con la decisión de G4 (solo las
  zonas del 23 tienen esas entradas, y las salidas de las demás no cambian) y queda en `notes/questions.md`.

### Grupo de argumentos: A11 y A23

- **A11.** `AddAccis` ignoraba en silencio `max_drift_rate`, `alpha_indoor`, `delta_cool`, `delta_heat` e
  `initial_T_rm_in` (distintos de sus valores por defecto, o en `zone_arguments`) cuando ninguna zona tiene
  `drift_mode`, mientras `modify_accis` da un `ValueError`. Ahora avisa (`_warn_unused_drift_arguments`; un aviso y no
  un error, para que los IDF de salida no cambien). Prueba: el aviso con un argumento general y otro de una zona, el IDF
  sin limitador, y ningún aviso con `drift_mode` ni con los valores por defecto.
- **A23.** `drop_invalid_param_combinations` no traducía los nombres del desarrollo de 1.2.0
  (`heating_setpoint_floor`, `cooling_setpoint_ceiling`), así que con ellos se saltaba la regla del mínimo y el máximo
  (H1 dice que los nombres antiguos siguen funcionando). Ahora los toma, y las columnas del plan no cambian. Prueba en
  `tests/parametric_and_optimisation/test_setpoint_limit_parameters.py`.
- Las dos pruebas fallan sin los arreglos y pasan con ellos.

### Grupo de los ganchos: A5 y A6

- **A5.** Cuando el gancho del SET no calcula el SET de una zona en un paso (sin el valor de un sensor, con una
  actividad o una vestimenta dinámica de 0, o sin la temperatura del aire), no actualizaba `HoursInCausalBand_<zona>`,
  una salida sumada, que repetía así las horas del último paso con SET aunque la zona estuviera desocupada. Ahora
  `SetSetpointHook` llama a `_skipped` en esos casos, y `Sun2026SetpointHook` pone esa salida a 0; `SET_<zona>` y
  `TSV_causal_<zona>` (promediadas) conservan su último valor (documentado en 4.9.3). Prueba con un controlador
  simulado y un SET de prueba (numba no carga en el servidor), que falla sin el arreglo.
- **A6.** No había prueba de que `run_simulation` llame a `prepare()` de los ganchos antes de cargar la biblioteca de
  la API de EnergyPlus (el orden que necesita el gancho del SET por bisección): prueba nueva que sustituye
  `load_energyplus_api` y comprueba el orden (`prepare` de los ganchos de antes y de después de los programas, y luego
  la carga). El código ya lo hacía.

### A21. El nombre del CSV de T0 de `'te_ref_nl'`, con un hash de sus valores

**Antes.** El CSV del `Schedule:File` de T0 se llamaba `<nombre del EPW>_outdoor_mid_range.csv`, en la carpeta del
modelo, y `write_schedule_file` lo reescribe si su contenido cambia: dos archivos climáticos con el mismo nombre en
carpetas distintas (el presente y 2050, por ejemplo) usados por modelos de la misma carpeta se sobrescribían, y los
modelos escritos antes leían sin aviso el T0 del otro archivo.

**Ahora.** `accim.sim.ems.outdoor_metric.mid_range_file_name(epw, values=None)`:
`<nombre del EPW>_outdoor_mid_range_<hash>.csv`, con 8 caracteres del SHA-1 de los valores, como los CSV de la
vestimenta de una función (H6, decisión 1). `MID_RANGE_FILE_SUFFIX` es ahora `'_outdoor_mid_range'`. Prueba nueva:
dos EPW llamados `Seville.epw` en dos carpetas dan dos nombres, y dos modelos de la misma carpeta leen cada uno los
valores de su archivo; las pruebas de H2 usan el nombre nuevo. Documentado en la sección 4.2.2 y el CHANGELOG.

## 44. Los estándares de confort 9 y 10 leen las medias de sus modelos (decisión del 12/11/2026)

Los estándares 9 y 10, IND IMAC R 7DRM y 30DRM, son los modelos A y B de Rawal et al. (2022), Building and Environment
219, 109187 (§4.4 y fig. 15): Tneut = 0,39·Tout-7DRM + 18,42 y Tneut = 0,42·Tout-30DRM + 17,60, con las medias simples
de la temperatura exterior de los 7 y de los 30 días anteriores (el artículo las distingue de sus versiones
ponderadas), aplicables de 5,5 a 33 °C, con bandas de ±2,15 K (90 %) y ±3,6 K (80 %). La revisión de Claude Science del
11/11/2026 encontró sus medias cambiadas, y las decisiones del 12/11/2026 (`notes/decisions.md`) las corrigen en la
1.2.0.

**Antes.**

- El 9 (7DRM) leía `PMOT`, la media simple de 30 días de EnergyPlus.
- Las consignas, los contadores de horas y la consigna de ventilación del 10 (30DRM) leían `RMOT`, la media exponencial
  de CEN 15251 de EnergyPlus (α = 0,8), mientras su temperatura de confort leía `PMOT`.
- En el modo de confort 1 del 9, fuera de los límites de aplicabilidad, la consigna de calefacción era la recta del
  código indio más 2,72 o 1,5 K (los valores de la de refrigeración), así que las dos consignas coincidían salvo por
  las tolerancias.

**Ahora.**

- El 10 lee `PMOT` en todo: `SETPOINT_LINES[(10, 1..3)]`, `COUNT_HOURS` (su condición es `if ComfStand == 1`) y
  `SET_VST` (`elseif ComfStand == 1`).
- El 9 lee la media aritmética de las medias diarias de los 7 días anteriores. EnergyPlus no la calcula, así que la
  calcula el EMS con el código de la métrica exterior del modelo personalizado (B1): `'ndrm'` con 7 días, en
  `Tout_metric`. `accim.sim.ems.standard_lines` tiene `BUILT_IN_METRICS = {9: ('ndrm', 0.8, 7)}`, `built_in_metric()`,
  `own_metric_inputs()` (las entradas `CustAST_metric = 5`, `CustAST_alpha = 0.8` y `CustAST_days = 7` de las zonas del
  9, o las de un estándar del registro) y `left_metric_inputs()`; `outdoor_metric_standards()` incluye el 9. Sus líneas
  (`SET_COMF_TEMP`, `SETPOINT_LINES[(9, 1..3)]` y sus ramas de `CountHours` y `SetVST` en `BUILT_IN_BRANCHES[9]`) leen
  `Tout_metric`; las consignas estáticas (la recta 0,078·T + 23,25 de los modos 0 y 1) siguen con `PMOT`, como en el 7,
  el 8 y el 10.
- Las zonas del 9 tienen siempre el código de la métrica exterior: lo ponen `AddAccis`, `modify_accis`
  (`input_values`, `uses_outdoor_metric`, `_set_built_in_metric_inputs` en `set_outdoor_metric_code`) y el parámetro
  `comfort_standard` del módulo paramétrico (`modify_ComfStand`). Con el archivo climático (`epw`), la media empieza el
  primer día del periodo con los 7 días anteriores del archivo; sin él, con `PMOT`, con el aviso de las métricas que
  calcula el EMS (que ahora nombra el 9). Los argumentos `custom_outdoor_metric`, `custom_alpha` y `custom_days` no la
  cambian.
- Una zona que deja el 9 por un estándar sin métrica propia vuelve a `'pmot'` (salvo que la llamada le dé otra
  métrica), para que el modelo personalizado no herede la media de 7 días, y el modelo pierde el código de la métrica
  exterior si ninguna zona lo necesita.
- El signo de la consigna de calefacción del modo 1 del 9 fuera de los límites: menos 2,72 o 1,5 K.
- `compute_setpoints` (la columna `Tout_metric` y `attrs['metric'] == 'ndrm'` para el 9), `print_setpoint_ems_code`
  (los programas de la métrica exterior del 9 y un comentario con su métrica), `verify_accim_simulation` (la
  comprobación 4, con `Check4_Tout_metric` en el 9) y la tabla de temperaturas de `Table` (la columna
  `Tout_metric (°C)` para el 9 en los modos 1 a 3, y la media de ASHRAE 55 para el 10).
- Los modelos de versiones anteriores de accim (un programa `SetInputData`) conservan su código del 9 y del 10; los
  anteriores a la 0.8, que reciben los subprogramas de esta versión, los reciben con `PMOT` en lugar de `Tout_metric`.

**Limitación documentada.** En un modelo sin el código de la métrica exterior (los de `add_accis_to_idf`, que tienen
el código de todos los estándares, o los IDF de salida de otros estándares), una zona cuyo estándar se cambia al 9
editando su programa `SetInputData_<zona>` detiene EnergyPlus («Variable = 'TOUT_METRIC' used in expression has not been
initialized») en lugar de leer otra media; `modify_accis` añade ese código.

**Migración.** Los resultados del 9 y del 10 cambian: con `Seville_Present.epw` y un año, la media de 7 días se aparta
de `PMOT` hasta 5,2 K (1,6 K de media), y `PMOT` de `RMOT` hasta 4,1 K desde el día 22 (1,5 K de media en el año), así
que sus temperaturas de confort cambian hasta 2,0 K y 1,7 K (0,6 K de media en los dos). Los resultados publicados con
accim 1.1.0 o anteriores se reproducen con esas versiones.

**IDF de salida y golden master.** Cambian a propósito: los IDF del 9 (el código de la métrica exterior y
`Tout_metric`) y del 10 (`PMOT`), en `b01` (16 de 200 archivos) y `b03`; una línea del programa `SetVST` de todos los
modelos en modo mixto (`elseif ComfStand == 1 || ComfStand == 10` pasa a `elseif ComfStand == 1`; `b02`, `b03`, `b05`,
`b07` a `b10`, `b12`, `b13`, `b15` a `b17` y `b22`); y los modelos con el código de todos los estándares (`s01` a `s06`
y `s09`). Comprobado línea a línea antes de reescribir los archivos: no cambia ninguna otra línea.

**Pruebas.** `tests/core/test_imac_r.py` (las líneas, `compute_setpoints` frente a la media de 7 días del archivo
climático desde tres fechas de inicio, el inicio con `PMOT`, el signo, `AddAccis` y `modify_accis`, y EnergyPlus 25.1:
la comprobación 4 sin discrepancias con y sin el archivo climático, y los dos backends con resultados idénticos);
`tests/core/test_comfort_standard_code.py` da `Tout_metric` a sus programas, y `tests/core/test_table_columns.py` y
`tests/core/test_comfort_standard_registry.py` siguen las cadenas nuevas.

## 45. El mínimo y el máximo de las consignas llegan al termostato con la tolerancia (A19, con S1)

El hallazgo A19 de la autoauditoría del 11/11/2026: donde el mínimo de calefacción o el máximo de refrigeración
limitan, el termostato recibía el propio límite (AHST = AHSTnoTol = AHSTmin), de modo que la tolerancia desaparecía
justo ahí, al contrario que en el resto de consignas del ACCIS y en las de los ganchos. Con el termostato en el límite
de la banda de confort, la temperatura operativa se asienta sobre él, y los contadores de horas, el disconfort de largo
plazo y `report_hours_below` cuentan como disconfort los decimales del control. Decidido el 12/11/2026
(`notes/decisions.md`): opción (ii).

**Ahora.**

- `limit_program_lines` (`accim.sim.ems.setpoint_limits`): `ApplySetpointLimits_<zona>` acota `AHST` con
  `AHSTmin+AHSTtol` y `ACST` con `ACSTmax+ACSTtol` (`ACSTtol` es la tolerancia con signo menos), redondea, deja esos
  valores exactos donde limitan, y acota `AHSTnoTol` y `ACSTnoTol` con los límites, como antes. Con 20 y 26 °C y la
  tolerancia por defecto (0,1 K), el termostato calienta a 20,1 °C y enfría a 25,9 °C donde los límites acotan, y la
  banda de confort es de 20 a 26 °C. Con `setpoint_tolerance=0` nada cambia, ni en los IDF sin límites.
- `check_setpoint_limits(minimum, maximum, where='', setpoint_tolerance=None)`: con la tolerancia, el máximo tiene que
  estar al menos dos tolerancias por encima del mínimo (si no, las consignas de los termostatos sobre los dos límites
  se cruzan): `ValueError`. Lo comprueban `AddAccis` (con la mayor tolerancia de sus IDF de salida, o la de la zona en
  `zone_arguments`), `modify_accis` (en cada llamada, también con los límites que las zonas conservan),
  `print_setpoint_ems_code` y los parámetros del módulo paramétrico (con la tolerancia de cada zona).
- `thermostat_limits(minimum, maximum, heating_tolerance, cooling_tolerance)`: las consignas del termostato sobre los
  límites. El aviso de S1 (`warn_crossed_setpoint_limits`) compara esas consignas con las del modelo de confort, y su
  mensaje las nombra («24,5 °C, 24,6 °C in its thermostat with the tolerance»); sin tolerancia, el mensaje es el de
  antes.
- `verify_accim_simulation`, comprobación 5: las consignas de los termostatos frente al mínimo más la tolerancia y el
  máximo menos ella (`Check5_AHSTmin`, `Check5_ACSTmax`), y las de sin tolerancia frente a los límites
  (`Check5_AHSTmin_noTol`, `Check5_ACSTmax_noTol`).
- `compute_setpoints` y `print_setpoint_ems_code` siguen el programa (la leyenda del código lo explica).

**Pruebas.** `tests/core/test_setpoint_limits.py`: las líneas del programa; el intérprete de Erl con tolerancias de 0,
0,1 y 0,25 K (también una consigna entre el límite y el límite más la tolerancia); `compute_setpoints` con y sin
tolerancia; el `ValueError` de las dos tolerancias en `check_setpoint_limits`, `AddAccis`, `modify_accis`, el código
EMS y el módulo paramétrico; el aviso con un mínimo que solo cruza por la tolerancia (23,95 °C frente a 23,9999 °C); y
EnergyPlus 25.1: en una semana de invierno y otra de verano, los termostatos están exactamente en 20,1 y 25,9 °C donde
los límites acotan, las comprobaciones 4 y 5 no dan discrepancias y los dos backends dan resultados idénticos.
`tests/core/test_comfort_hooks.py` y `tests/core/test_sun2026_set.py`: las consignas de un gancho acotadas por el
mínimo llegan al termostato con la tolerancia.

**Medición de F1 repetida.** La semana de invierno de la prueba del estándar 24 (8–14 de enero, con un mínimo de
18 °C en una zona) cambia porque ese termostato calienta ahora a 18,1 °C: la mayor diferencia horaria entre el SET del
gancho y el de EnergyPlus en esa zona pasa de 0,191 a 0,187 K, y la otra zona está dentro de la banda causal 58,2 de
sus 60 horas ocupadas (antes, 56,3). Comprobado con el commit anterior en un árbol de trabajo temporal; la semana de
verano no cambia. Actualizados `MEASURED` de `tests/core/test_sun2026_set.py` y la sección 4.9.3.

## 46. Las consignas estáticas del estándar 23 en todas las zonas de los modelos con su código (A24)

El hallazgo A24 de la autoauditoría del 11/11/2026: en los modelos con el código EMS de todos los estándares de
confort (`add_accis_to_idf`), una zona cuyo estándar se cambiaba al 23 (JPN Aqilah 2025) editando
`set ComfStand = 23` en su programa `SetInputData_<zona>` detenía EnergyPlus en el calentamiento («Variable =
'STATICACST' used in expression has not been initialized»), porque solo las zonas del 23 tenían las entradas
`StaticAHST` y `StaticACST` (decisión de G4). Decidido el 12/11/2026 (`notes/decisions.md`): opción (ii).

**Ahora.**

- `accim.sim.ems.static_setpoints.set_static_setpoint_inputs(idf, enabled=True)`: da a todas las zonas del modelo las
  dos entradas que les falten, con sus valores por defecto (20,0 y 28,0 °C), en el sitio que les corresponde en el
  orden de `INPUT_VARIABLES` (antes de las del mínimo y el máximo, del limitador de la deriva y del factor de
  apertura); sin `enabled`, las quita de las zonas cuyo estándar no las usa.
- `set_static_setpoint_variables(idf)` (que ya llamaban `add_accis_to_idf`, al añadir las variables globales, y
  `set_comfort_standard_code`, y por tanto `AddAccis`, `modify_accis` y el módulo paramétrico) la llama: con el código
  del 23 (sus subprogramas `SetAST_CS23_<trozo>`), todas las zonas tienen las entradas; sin él, ni variables globales
  ni entradas.
- Las zonas de otros estándares las ignoran. Los IDF de salida de `AddAccis` sin el código del 23 no cambian; en los
  que tienen una zona del 23 (con `zone_arguments`), las demás zonas reciben los valores por defecto.

**Golden master.** Cambian solo `s01` a `s06` y `s09` (los modelos de las funciones en memoria, con el código de todos
los estándares): dos líneas más en cada `SetInputData_<zona>`, comprobado línea a línea antes de reescribirlos.

**Pruebas.** `tests/core/test_jpn_aqilah2025.py`: un modelo de `add_accis_to_idf` con una zona cambiada a mano al 23
(solo `ComfStand`, `CAT` y `ComfMod`) se simula con EnergyPlus 25.1 y sus consignas son 20 y 28 °C (falla con el
código anterior, comprobado en un árbol de trabajo temporal del commit previo); todas las zonas de un IDF de `AddAccis`
con una zona del 23 tienen las entradas, y los IDF sin su código, ninguna; un modelo que pierde el código del 23 las
pierde. `tests/core/test_zone_arguments.py` y `tests/core/test_modifyaccis_setast.py` esperan las dos líneas nuevas.
Documentación: la sección 4.2.1 ya no avisa de este fallo.

## 47. E-F1 medida otra vez: el SET de EnergyPlus (Pierce) y el de pythermalcomfort según el nivel de actividad (A1 y A2)

Los hallazgos A1 y A2 de la autoauditoría del 11/11/2026: el modelo de Pierce de EnergyPlus convierte el nivel de
actividad con 1,8258 m² (accim, con 1,8 m²), y su código no tiene el término de la actividad en el coeficiente
convectivo del ambiente real, que sí tienen su Engineering Reference y pythermalcomfort; así que la medición de E-F1,
hecha con los 110,7 W/persona del modelo de ejemplo, mezclaba una diferencia de entradas con la del modelo y solo valía
cerca de 1 met. Decidido el 12/11/2026 (`notes/decisions.md`): medirla otra vez con las dos conversiones y a 1,1 y
1,2 met; los ganchos conservan los 1,8 m².

**El código de accim no cambia** (solo comentarios y docstrings: `accim.constants.PMV_BODY_SURFACE_AREA`,
`accim.sim.comfort_hooks.MET_ACTIVITY_LEVEL` y `accim.data.postprocessing.indoor_adaptation`, que decían que EnergyPlus
usa 1,8 m² en todos sus modelos de confort, o daban las diferencias de E-F1 sin el nivel de actividad).

**La medición** (modelo de ejemplo con el ACCIS, un año en Sevilla, EnergyPlus 25.1, 6 pasos por hora, 0,137 m/s, 1,0
clo en invierno y 0,5 clo en verano; medias horarias del SET de pythermalcomfort 4.8.1 menos el de EnergyPlus; media
del año y, entre paréntesis, máximo en valor absoluto de las dos zonas). Columnas: (a) conversión de accim (1,8 m²),
de pie; (b) la misma, sentado; (c) conversión del modelo de Pierce (1,8258 m²), de pie; (d) como (c), sin el término de
la actividad en el coeficiente convectivo del ambiente real de pythermalcomfort:

| Nivel de actividad | (a) | (b) | (c) | (d) |
|---|---|---|---|---|
| 110,7 W/persona | −0,045 K (0,20) | −0,116 K (0,34) | −0,058 K (0,14) | −0,058 K (0,14) |
| 115 W/persona | −0,325 K (0,60) | −0,398 K (0,75) | −0,331 K (0,53) | −0,056 K (0,14) |
| 126 W/persona | −0,943 K (1,44) | −1,021 K (1,58) | −0,966 K (1,41) | −0,051 K (0,13) |

Conclusiones (`notes/decisions.md`, «E-F1 measured again»): los dos SET coinciden (0,05–0,2 K) solo hasta unos
1,05 met; por encima, el de EnergyPlus es más alto (0,3 K a 1,1 met y 1 K a 1,2 met), y toda esa dependencia del nivel
de actividad es el término 5,66·(met − 0,85)^0,39 del coeficiente convectivo del ambiente real, que el código de
EnergyPlus solo tiene en el ambiente estándar; la superficie corporal de la conversión cambia el SET 0,01–0,02 K de
media.

**Pruebas.** `tests/core/test_pierce_set.py`, reescrito: el nivel de actividad es su parámetro (110,7, 115 y 126
W/persona; las tres simulaciones de un año corren a la vez, cada una en su carpeta), con las dos conversiones y las dos
posturas (24 casos medidos, dentro de 0,001 K); comprueba que la diferencia crece con el nivel de actividad, y que sin
el término de la actividad en el ambiente real de pythermalcomfort (una copia de su fuente 4.8.1 con esa condición
anulada; se omite con otra versión) queda en 0,05–0,06 K en los tres niveles. `_accis_model` ya no recibe
`monkeypatch` (lo usa una fixture de módulo), y `tests/core/test_indoor_adaptation.py`, que lo importa, lo llama así.

**Documentación.** Sección 4.9.2 (qué hace el código de EnergyPlus y qué dice su Engineering Reference, la tabla por
nivel de actividad, y corregida la frase que atribuía los 1,8 m² a EnergyPlus sin más), 4.9.3 y 4.7.6; `CHANGELOG.md`;
y `notes/BORRADOR_issue_EnergyPlus_SET_Pierce_2026-11-12.md`, el borrador del issue para el repositorio de EnergyPlus
sobre la diferencia entre su código y su Engineering Reference, que publica el autor si lo ve oportuno (el listado del
programa del SET de ASHRAE 55 que cita el código no está en la biblioteca: no comprobado).

## 48. Un modelo preparado para un gancho no se simula sin él en silencio (A4)

El hallazgo A4 de la autoauditoría del 11/11/2026: un modelo preparado por `apply_athb_setpoints`,
`apply_set_setpoints` o `apply_sun2026_setpoints` (con los programas `ApplyHookSetpoints_<zona>`) que se simulaba sin
el gancho —con el backend EMS de `run_ep`, su valor por defecto, o con el de la API sin pasárselo— corría con las
consignas del estándar de confort de sus zonas y las salidas del gancho a 0, sin error ni aviso. Decidido el
12/11/2026 (`notes/decisions.md`): opción (ii).

**Ahora.**

- `accim.sim.ems.hook_setpoints`: `hook_zones_of_file(path)` (las zonas con ese programa, leídas del texto del IDF,
  sin eppy, sea cual sea su versión de EnergyPlus), `missing_hook_message(models, backend)` y la clase
  `MissingHookWarning` (un `UserWarning`).
- `accim.run.run_ep`: con el backend EMS, un `ValueError` que nombra los modelos de la carpeta preparados para un
  gancho, antes de simular nada (`_check_setpoint_hooks`); dice con qué correrían y cómo simularlos
  (`run_ep(backend='api', hooks=[hook])`).
- `accim.sim.energyplus_api.runner`: `warn_without_setpoint_hook(idfs, before_programs)`; `run_simulation` avisa
  (`MissingHookWarning`) si el modelo está preparado para un gancho y no recibe ninguno en `before_programs`;
  `run_simulations` avisa una sola vez por todos sus modelos (cada simulación ya no repite el aviso), también a través
  de `run_ep(backend='api')` sin `hooks` con `runs_before_programs`.
- Los modelos simulados fuera de accim (EP-Launch, la línea de órdenes de EnergyPlus) siguen corriendo sin el gancho y
  sin aviso: queda documentado (secciones 4.9.1 y 4.9.3). La salida EMS opcional que proponía el hallazgo (los pasos
  ocupados sin consignas del gancho) no se añade.

**Pruebas.** `tests/core/test_missing_hook.py` (nuevo: el mensaje, las zonas de un fichero, el `ValueError` de `run_ep`
antes de simular nada, y el aviso de `run_simulation`, `run_simulations` y `run_ep(backend='api')`, uno solo por
llamada). En `tests/core/test_sun2026_set.py`, la prueba de los dos backends sin el gancho con el estándar 24
(`test_without_the_hook_both_backends_give_the_same_results_with_comfort_standard_24`) ahora comprueba con EnergyPlus
25.1 el error del backend EMS y el aviso del de la API, además de que sin el gancho los dos dan los mismos resultados.
`tests/core/test_table_optional_outputs.py` simulaba con el backend EMS un modelo con los objetos del ATHB (y
comprobaba que sus salidas eran 0): ahora lo simula con el backend de la API y el gancho, y comprueba el error del EMS.

## 49. `modify_accis` avisa cuando las zonas del estándar 23 pierden el inicio con el fichero climático (A25)

El hallazgo A25 de la autoauditoría del 11/11/2026: una llamada a `modify_accis` sin `epw` que reescribe los programas
de la métrica exterior (por ejemplo, la que solo cambia la métrica exterior del modelo personalizado de otra zona) los
deja empezando con PMOT, y las zonas de JPN Aqilah 2025 (23) pasan de la media móvil del fichero climático
(`Tout_metric`, `rmot_alpha`) al RMOT nativo de EnergyPlus, cuyo primer valor es un 21 % bajo (B4-1). Lo hacía sin el
aviso de RMOT (la llamada no da el estándar 23) y con un aviso que decía que su `rmot_alpha` empieza con PMOT, lo que
no es cierto para esas zonas (su código ya no lo lee). Decidido el 12/11/2026 (`notes/decisions.md`): opción (i).

**Ahora.**

- `accim.sim.accis.modify_accis`: guarda si los programas de la métrica exterior empezaban con los valores de un
  fichero climático antes de los cambios (`begins_with_weather_file`), y da el aviso de RMOT (`_warn_rmot_start`, con
  el texto `_RMOT_START_LOST`: «whose programs of the outdoor metric this call has written again without the weather
  file of the simulation») siempre que el modelo tiene zonas del 23 y deja de empezar con ellos en la llamada; si no
  empezaba con ellos, avisa como antes, solo cuando la llamada da el estándar 23.
- `accim.sim.ems.outdoor_metric.set_outdoor_metric_code`: el aviso de las métricas que empiezan con PMOT ya no
  incluye la de las zonas del 23 cuando los programas se escriben sin fichero climático (su código lee RMOT y su
  métrica no se usa); si ninguna otra métrica empieza con PMOT, no se da.
- La entrada `CustAST_metric = 2` de esas zonas se queda (sin usar), como antes, y vuelve a usarse si una llamada
  posterior da `epw`.

**Pruebas.** `tests/core/test_jpn_aqilah2025.py::test_modify_accis_warns_when_its_zones_lose_the_weather_file`: el caso
del hallazgo (un aviso de RMOT con el motivo, y el de PMOT solo con `rmot_7day`), una llamada que no toca la métrica
(conserva el inicio, sin avisos), otra posterior sin `epw` (no repite el aviso), la vuelta con `epw`, y un modelo con
todas las zonas del 23 (solo el aviso de RMOT). Documentación: la sección 4.2 (JPN Aqilah 2025) y la docstring de
`modify_accis`.

## 50. `drift_mode='window'` es un modo experimental, con un aviso; `'rate'` es el recomendado (A8)

El hallazgo A8 de la autoauditoría del 11/11/2026: con `drift_mode='window'` las dos consignas se recortan a
T_rm_in ± delta, y T_rm_in es la media móvil de la temperatura operativa de la propia zona, así que la consigna que el
estándar de confort deja lejos de la zona se va a su temperatura: la banda entre consignas queda en `delta_heat` +
`delta_cool` como mucho (2 K), y la calefacción o la refrigeración funcionan para mantener la zona a 1 K de su media
reciente. Es la decisión 6 del autor implementada tal cual, no un error. Decidido el 12/11/2026
(`notes/decisions.md`): opciones (i) y (iii); `'window'` no se redefine en la 1.2.0.

**Ahora.**

- `accim.sim.ems.drift_limiter.WINDOW_WARNING`: el texto del aviso (qué hace el modo, su banda, su coste y que `'rate'`
  es el modo recomendado); la docstring del módulo lo explica, con la medición de abril.
- `accim.sim.accis._warn_window_drift_mode`: `AddAccis` y `modify_accis` dan ese aviso (`UserWarning`) una vez por
  llamada cuando una zona recibe `drift_mode='window'` (en los argumentos o en `zone_arguments`), después de comprobar
  los argumentos; no cuando las zonas lo conservan en una llamada que no lo da, ni con `'rate'`.
- El módulo paramétrico (parámetro `drift_mode`, código 2) no avisa: daría un aviso por simulación; su documentación
  dice que es un modo experimental.

**La medición, repetida el 12/11/2026** (modelo de ejemplo, Sevilla, INT EN16798 categoría II, modo de confort 3,
`vrf_ac`, EnergyPlus 25.1; sin limitador → con `'window'` y sus valores por defecto en todas las zonas):

| Mes | Baterías de calefacción (kWh) | Baterías de refrigeración (kWh) | Electricidad del VRF (kWh) | Banda media (K) |
|---|---|---|---|---|
| Enero | 19,7 → 42 814 | 12 878 → 7552 | 9918 → 32 654 | 7,00 → 1,26 |
| Abril | 125,9 → 32 488 | 9520 → 4678 | 7817 → 21 715 | 7,00 → 1,97 |
| Julio | 10,4 → 4464 | 8209 → 9464 | 8249 → 11 709 | 7,00 → 2,22 |

(la banda media entre consignas en las horas ocupadas de Block1:Zone1, con el primer día ocupado, sin limitador).
Coincide con la del hallazgo salvo en `'rate'`: con 0,5 K/día ya no da exactamente lo mismo que no tener limitador,
como decía la autoauditoría, sino que limitó las consignas unos 0,2 K dos lunes de abril y uno de julio (12 h ocupadas
cada uno; ninguno de enero), con 27 kWh más en las baterías de calefacción de abril. La causa probable es la tarea S3,
posterior a la autoauditoría, que cambió el estado de la tasa a la media de las consignas aplicadas en las horas
ocupadas del último día ocupado (no se ha comprobado con el código anterior).

**Pruebas.** `tests/core/test_drift_limiter.py`: el aviso (una vez por llamada en `modify_accis` y en `AddAccis`,
también con `zone_arguments`; no con `'rate'`, ni cuando las zonas lo conservan, ni cuando los argumentos no son
válidos) y la medición de abril con EnergyPlus 25.1 (sin limitador, con `'window'` y con `'rate'`: energía de las
baterías, banda media, consigna media de calefacción y horas limitadas). Documentación: sección 4.2.7 del uso
detallado y la tabla de parámetros del módulo paramétrico.

## 51. El SET de referencia de la banda causal es el de pythermalcomfort: la documentación (decisión 9)

La documentación y las docstrings decían que los indicadores de la banda causal con el SET de pythermalcomfort eran
provisionales, hasta que los autores del modelo causal dijeran qué SET habían usado, y remitían a una pregunta de
`notes/questions.md` que ya está respondida. Decidido el 12/11/2026 (`notes/decisions.md`): el modelo de Sun, Brager y
Schiavon (2026) toma el SET de la ASHRAE Global Thermal Comfort Database II, versión 2.1, y el script que genera esa
versión de la base de datos lo calcula con `set_tmp` de pythermalcomfort (con sus valores por defecto: de pie); así que
ese es el SET de referencia, y el SET de Pierce de EnergyPlus queda como el indicador que cualquier modelo tiene sin
pythermalcomfort (lo aproxima solo hasta unos 1,05 met: sección 47).

**El código no cambia** (ninguna salida ni columna cambia de nombre; `Table(indoor_adaptation_indicators=True)` sigue
igual). Cambian los textos:

- Sección 4.7.6 del uso detallado: el párrafo «The indicators with the SET of pythermalcomfort (provisional)» pasa a
  ser «The reference SET of the causal band: that of pythermalcomfort», con el porqué, qué indicadores son los de
  referencia (las salidas del gancho del estándar 24 y los de `table_indicators(..., pythermalcomfort_set=...)`), qué
  queda con el SET de Pierce, y la nota de la postura: la base de datos calculó su SET de pie y los ganchos de accim
  sientan a los ocupantes con 1,2 met o menos (0,03–0,07 K menos); `'position': 'standing'` da el de la base de datos.
- Secciones 4.9.2 (la conclusión de E-F1) y 4.9.3 (un punto nuevo en las decisiones del estándar 24).
- Docstrings de `accim.data.postprocessing.indoor_adaptation` (el módulo, `PYTHERMALCOMFORT_SET_INDICATORS` y
  `table_indicators`) y de `accim.sim.comfort_hooks.apply_sun2026_setpoints` (`position`), y `CHANGELOG.md`.

Queda para el autor preguntar a Ruiji Sun si el SET del artículo es la columna `set` de la base de datos (inferido de
su script y del artículo anterior de los mismos autores); nada espera a esa respuesta.

## 52. `pythermalcomfort_set` con las entradas de los ocupantes de los objetos People (S4, opción (ii))

Decidido el 12/11/2026 (`notes/decisions.md`, decisión 9): los indicadores de la banda causal con el SET de
pythermalcomfort son los de referencia, así que deben poder tomar las entradas de los ocupantes que toma el gancho del
estándar 24 (las de los objetos People de cada zona en cada paso de tiempo), no solo valores constantes; lo necesitan
los casos (iii) y (iv) del estudio de validación (ropa por estación, modelo dinámico de ropa, velocidades del aire).

**Ahora.**

- `accim.sim.comfort_hooks.people_inputs(building, zones=None)`: los horarios de los objetos People de cada zona
  ocupada (actividad, ropa, método de cálculo de la ropa y velocidad del aire), la clave de sus salidas y la de las de
  sus ocupantes; `add_people_input_outputs(building, output_frequencies=None)`: pide las salidas con las que se calcula
  el SET después de la simulación (las condiciones de la zona, el *Schedule Value* de esos horarios y, con el modelo
  dinámico de ropa, *Zone Thermal Comfort Clothing Value*).
- `accim.sim.people.add_thermal_comfort_outputs(..., occupant_inputs=False)`: con `True`, las pide también (comprueba
  antes de cambiar nada que, con el modelo dinámico de ropa, haya un modelo Fanger o Pierce que la reporte).
- `set_of_results(results, hook, keys=None, frequency=None, people=None)`: con un gancho que lee entradas de los People
  (`met`, `clo` o `air_speed` None), las toma de esas salidas en cada fila (antes daba un `ValueError`), con la postura
  del metabolismo de cada fila; `people` son los horarios (`people_inputs`), o `hook.people`, que ahora ponen
  `apply_set_setpoints` y `apply_sun2026_setpoints`. Las filas en las que el gancho no calcularía el SET (actividad 0,
  ropa del modelo dinámico 0) son NaN. Si faltan las salidas: `MissingOccupantInputs` (un `ValueError`), que dice cómo
  pedirlas.
- `accim.data.postprocessing.indoor_adaptation.table_indicators(..., pythermalcomfort_set=...)`: además de números,
  `'people'` (para las tres entradas, o para cada una en el diccionario: `{'met': 'people', 'clo': 0.5, 'air_speed':
  'people'}`); los horarios se leen del modelo de cada simulación (el IDF de la carpeta actual cuyo nombre es el de su
  CSV hasta el fichero climático, o el de la clave `'idf'`), una vez por modelo; un gancho que lee entradas de los
  People da los de su modelo. Errores claros: falta el modelo, una zona de la tabla sin People, o faltan las salidas.

**Medición** (semana del 15 al 21 de julio del modelo de ejemplo con el estándar 24, Sevilla, EnergyPlus 25.1, 6 pasos
por hora): con los valores que leen los sensores del gancho, el SET de `set_of_results` es el del gancho (a 0,001 K);
con los de cada fila, difiere 0,012–0,013 K de media (0,14 K como máximo). Con filas de paso de tiempo, las horas dentro
de la banda causal con `'people'` son las mismas que las del gancho (27,8 y 34,3 de las 60 horas ocupadas de cada zona;
28 y 35 con filas horarias), frente a 24,7 y 31,2 con el SET de Pierce, 0,2 K más alto.

**De paso.** Esa medición mostró que el sensor de la temperatura radiante media de los ganchos (`SET_MRT_<zona>`) lee
la que EnergyPlus ha calculado para el propio paso de tiempo (igual a la salida de la misma fila), no la del paso
anterior, como decían la documentación y las docstrings; los de la temperatura del aire y la humedad sí leen las del
paso anterior. Corregido el texto (secciones 4.9.1 y 4.9.2, y las docstrings de `accim.sim.comfort_hooks`); el código
no cambia.

**Pruebas.** `tests/core/test_people_set_inputs.py` (nuevo): los horarios de un modelo, las salidas pedidas (también
con el modelo dinámico de ropa, y sin cambiar nada cuando falta un modelo que la reporte), `set_of_results` con cada
fuente de la ropa, la postura y entradas mezcladas, `table_indicators` con `'people'`, con la clave `'idf'` y con un
gancho, sus errores, y la simulación con EnergyPlus 25.1 contra las salidas del gancho del estándar 24.

## 53. El rango estacional de EN 16798-1 para la incomodidad a largo plazo, y la limitación del constante (A15)

El hallazgo A15 de la autoauditoría del 11/11/2026: `long_term_range=('en16798', categoría)` toma el mínimo de la
estación de calefacción (pensado para 1,0 clo) y el máximo de la de refrigeración (0,5 clo) de la tabla B.2 como un
rango constante de todos los pasos de tiempo, así que da por confortables las horas de verano demasiado frías y las de
invierno demasiado cálidas (21 °C en julio o 25,5 °C en enero, en una oficina de categoría II). Decidido el 12/11/2026
(`notes/decisions.md`): opciones (i), documentarlo, y (ii), un rango estacional con los límites de la propia norma.

**Ahora.**

- `accim.constants`: `EN16798_TABLE_B5` (los rangos de las estaciones de calefacción y de refrigeración de la tabla
  B.5 de EN 16798-1:2019, por tipo de edificio y categoría, leídos el 12/11/2026 en UNE-EN 16798-1:2020, p. 54) y
  `EN16798_SEASON_RUNNING_MEANS` (10 y 15 °C: los umbrales de θrm de la nota de la tabla).
- `accim.sim.ems.long_term_discomfort`: `LONG_TERM_RANGES` gana `'en16798_seasonal'`; `long_term_limits` devuelve
  para él un `SeasonalRange` (rangos de calefacción y refrigeración y sus umbrales; su método `limits(θrm)` da los
  límites); `seasonal_lines` escribe las líneas que fijan los límites del paso de tiempo en las variables locales
  `LongTermLower` y `LongTermUpper` del programa `CountLongTermDiscomfort_<zona>` a partir del sensor `RMOT`;
  `zone_lines` las pone delante y compara con ellas; `model_long_term_limits` las reconoce. El modelo declara y
  reporta lo mismo que con el rango constante. Hace falta el tipo de edificio en las categorías I a III.
- `accim.utils.verification` (comprobación 6): con el rango estacional, los límites de cada paso son los de la
  estación de la media móvil del paso anterior (la que lee el EMS), que necesita su salida.
- `accim.data.postprocessing.long_term_discomfort`: `range_limits(long_term_range, running_mean=None)` (los límites de
  un rango para `hours_outside_range` y `degree_hours`: dos números, o los de cada fila) y
  `table_indicators(df, zones, long_term_range=None, running_mean=None)` (los indicadores de una tabla con un rango de
  EN 16798-1, en lugar de las consignas de cada simulación; `Table(long_term_indicators=True)` no cambia).
- Docstrings de `AddAccis`, `add_accis_to_idf` y las clases del módulo paramétrico. La lista de la interfaz gráfica
  sigue teniendo solo los rangos de la tabla B.2.

Sin `long_term_range`, o con `'en16798'`, los IDF de salida no cambian (golden master idéntico).

**Medición** (modelo de ejemplo, Sevilla, INT EN16798 categoría II, modo de confort 3, EnergyPlus 25.1; rangos de las
oficinas de categoría II; dos semanas, 120 horas ocupadas por zona): del 15 al 28 de enero (θrm de 6,7 a 11,3 °C:
estación de calefacción diez de los días), 69,7 y 70,3 horas por encima del límite superior del rango estacional
(24 °C en la estación de calefacción), frente a 4,8 y 19,3 por encima de los 26 °C del constante; del 12 al 25 de marzo
(θrm de 11,0 a 18,3 °C), las mismas horas con ambos (58,2 y 55,7 por encima de 26 °C, ninguna por debajo).

**Pruebas.** `tests/core/test_long_term_discomfort_counters.py`: la tabla B.5 (los ocho rangos, tecleados de la norma)
y sus errores; el programa con el intérprete de Erl frente a las funciones de D1 con diez pares de media móvil y
temperatura; `range_limits` (las horas que el rango constante deja fuera, las filas sin media móvil y sus errores); el
modelo de `add_accis_to_idf`; y, con EnergyPlus 25.1 y los dos backends, las dos quincenas de la medición (resultados
idénticos, comprobación 6 sin discrepancias, y los totales iguales a los de las funciones de D1 con la media móvil del
paso anterior). `tests/core/test_long_term_discomfort.py`: `table_indicators` con los rangos constante y estacional.

## 54. El script del estudio de validación de F3 (`tools/indoor_adaptation_study.py`)

No es código del paquete: es una herramienta de desarrollo (`tools/`), como `compare_backends.py`. Con las elecciones
decididas el 12/11/2026 (`notes/decisions.md`, decisión 13), construye a partir de un modelo con el ACCIS los modelos
de los casos del estudio de validación del bloque F y los simula con el backend de la API de Python:

- `i_fixed`: consignas fijas de 20 y 26 °C (un estándar de confort definido por sus datos, en modo de confort 0);
- `ii_en16798` y `ii_ashrae55`: las consignas adaptativas de EN 16798-1 (categoría II) y ASHRAE 55 (80 %);
- `iii_seasonal` y `iii_dynamic`: el modelo causal del SET (estándar 24) con la ropa por estación (1,0 y 0,5 clo) y con
  el modelo dinámico de ropa de ASHRAE 55;
- `iv_v06`, `iv_v09` y `iv_v12`: el modelo causal con velocidades del aire de 0,6, 0,9 y 1,2 m/s en las horas de los
  ventiladores de la estación de refrigeración;
- `v_<caso>_r025`, `_r05` y `_r10`: los casos (ii) y (iv) (también `iii_dynamic`, que es el caso (iv) a 0,1 m/s) con
  el limitador de la deriva (`'rate'`) a 0,25, 0,5 y 1,0 K/día. En total, 26 casos.

Escribe `indicators.csv`, una fila por simulación: la energía de las baterías y la electricidad del VRF, la incomodidad
a largo plazo con el rango estacional de EN 16798-1 (sección 53), y los indicadores de la adaptación al clima interior,
los de la banda causal con el SET de referencia y las entradas de los People (`pythermalcomfort_set='people'`, sección
52) y con el SET de Pierce.

**Lo que no hace.** La referencia estática (a) del estudio, las consignas de PMV de `apply_pmv_setpoints`: sus modelos
no tienen las salidas del ACCIS que necesitan los indicadores de `Table`. Y las simulaciones del estudio en sí (un año
de cada caso en cada clima: un año de un caso del modelo causal tarda horas) no se han hecho: esperan al acuerdo del
autor con Ruiji Sun, al fichero climático del clima cálido y húmedo y, para 2050 y 2080, al jar del Future Weather
Generator. La entrada de `TODO.md` sigue abierta con lo que falta.

**Lo que han enseñado las pruebas** (una semana de enero y otra de julio del modelo de ejemplo en Sevilla, que es un
modelo de pruebas y no el del estudio). Dos cuestiones del diseño de los casos (iv) y (v) quedan abiertas en
`notes/questions.md` (12/11/2026), con sus números y sus opciones; el script mantiene los casos como se decidieron:

1. La velocidad del aire de los ventiladores está en las dos consignas. El hook del modelo causal convierte los dos
   límites de la banda del SET con la velocidad del aire del objeto People, así que los ventiladores suben también la
   consigna de calefacción (con 1,2 m/s, de unos 19 °C a 25–26,7 °C en sus horas) y las baterías de calefacción
   trabajan en julio en las primeras horas de los ventiladores (10,6 kWh en la semana con 1,2 m/s). La propuesta del
   bloque F tenía un `air_speed_cooling`, solo para la consigna de refrigeración.
2. El limitador (`'rate'`) limita todos los pasos de tiempo, también los no ocupados, a la media de las consignas de
   los pasos ocupados del día anterior ± la tasa. Con las consignas de un hook, que cambian dentro del día (y mucho
   más con los ventiladores), mantiene de noche las consignas de las horas ocupadas: con 1,2 m/s y 0,25 K/día, 344 kWh
   de calefacción en la semana de julio en vez de 10,6, y 1550 kWh de refrigeración en vez de 2044, la mayor parte de
   la diferencia en las horas no ocupadas. Así, el caso (v) del modelo causal mediría sobre todo eso, y no la deriva
   entre días. La sección 4.2.7 del uso detallado lo explica ahora.

## 55. Los dos backends con los modelos de `add_accis_to_idf`: el test de A24 y un hallazgo

Al repasar la definición de terminado de A24 (sección 46: ambos backends cuando cambia el código del EMS), su test con
EnergyPlus solo simulaba con el backend del EMS. Ahora simula también con el de la API de Python y compara.

**El hallazgo.** Con ese modelo los dos backends no dan ficheros idénticos: las salidas del EMS y las consignas de los
termostatos (los valores de sus schedules, que son lo único que accim le pasa a EnergyPlus) son idénticas en todos los
pasos de tiempo, pero el resto de las salidas difiere en las últimas cifras (hasta 5·10⁻¹⁰ K en las temperaturas de las
zonas y 5·10⁻³ J en las energías horarias, en dos días de julio del modelo de ejemplo). No lo causa A24 ni ninguna
tarea de esta sesión: ocurre igual, con los mismos números, con el código de `f3f9eb5`, y ocurre con cualquier modelo
de `add_accis_to_idf` (los que llevan el código de todos los estándares de confort), también sin editar. Con los IDF de
salida de `AddAccis`, que son los que comparan los tests de ambos backends, los ficheros son idénticos. La diferencia
nace antes del primer paso de tiempo que se reporta (ya está en el primer día de diseño), probablemente en las primeras
ejecuciones de los programas que EnergyPlus hace sin callbacks mientras dimensiona; la causa no está encontrada.

**Lo que cambia.** `tests/core/test_jpn_aqilah2025.py`: el test de la zona cambiada a mano compara de forma exacta las
salidas del EMS y los valores de los schedules, y el resto con una tolerancia relativa de 10⁻⁶. La sección 4.9 del uso
detallado lo dice, junto al caso ya conocido de los termostatos del PMV. `TODO.md` tiene una entrada P2 para encontrar
la causa. No cambia código del paquete.

## 56. Los checks 1 y 2 de `verify_accim_simulation` encuentran las zonas y las ventanas con «:» en el nombre

Era la única entrada P1 que quedaba en `TODO.md` (del 9/11/2026), hecha el 13/11/2026 a petición del autor.

**El fallo.** Los checks 1 y 2 partían el nombre de cada salida, `<clave>:<variable>`, por el primer «:». Con los
nombres de DesignBuilder (`Block1:Zone1`, como los del modelo de ejemplo) la clave quedaba en `BLOCK1` y no
encontraban ninguna salida: `verify_accim_simulation` se saltaba las zonas y las ventanas con un aviso, y
`AccimSimulationVerifier` lanzaba un `ValueError`. Es decir, con los modelos de la mayoría de los usuarios estos dos
checks no comprobaban nada.

**La corrección** (`accim/utils/verification.py`; la lógica de los checks no cambia):

- `_key_and_variable()`: la clave de una salida es el texto anterior a su último «:», como la lee
  `read_eso_using_readvarseso` (los nombres de las variables de EnergyPlus no llevan «:»). Sirve también para las
  columnas de los CSV, con sus unidades y su frecuencia.
- `_find_column()`: entre las columnas que contienen los dos fragmentos, se queda con la de clave más cercana (la
  clave exacta; luego la que contiene el fragmento como palabras completas; luego dentro de un nombre más largo), y lo
  mismo con la variable. Así las salidas de `Block1:Zone1` no se toman de `Block1:Zone10`.
- Cada ventana se comprueba con el factor de apertura de su propia superficie (la que mueve su actuador
  `<ventana>_VentOpenFact`) y con la consigna de refrigeración y la ocupación de su propia zona; antes, con los de la
  primera ventana de la zona y los de la primera zona.

**Lo que informan ahora** (antes se lo saltaban), medido con el modelo de ejemplo en Sevilla:

- *Check 1*: los pasos de tiempo en que el sistema de una zona está encendido y la zona, fuera de su consigna. En la
  semana de julio de las pruebas de F3, 77 y 71 horas (de las 168 de cada zona) con las consignas fijas de 20 y 26 °C,
  6 y 17 con EN 16798-1 y 15 y 26 con ASHRAE 55; en la de enero, 18 y 21, 43 y 43, y 55 y 50. En esas horas las
  baterías dan del 86 al 99 % de su máximo de la semana: el sistema está al límite. No es un error del EMS, sino del
  sistema del modelo de ejemplo, que no mantiene la consigna.
- *Check 2 de la función*: en una semana de abril en modo mixto, 213 desajustes que no son errores del EMS. Compara las
  condiciones con las salidas del mismo paso de tiempo (el EMS abre y cierra con la temperatura operativa del paso
  anterior) y con constantes de 20 y 6 °C para la consigna de ventilación y la temperatura exterior mínima, que en los
  modelos de accim se calculan en cada paso. La clase `AccimSimulationVerifier`, que las lee de las salidas del EMS y
  descarta los pasos del retardo, no da ninguno en la misma simulación.

**Los tests.** Seis tests nuevos en `tests/core/test_verification.py`: la clave y la variable de una columna; la
columna más cercana; el check 1 y el check 2 con salidas inventadas del modelo de ejemplo (con el código anterior se
saltaban las 2 zonas y las 6 ventanas); y dos con EnergyPlus (el check 1 de dos días de julio, igual que el cálculo
directo con el CSV, y los dos checks y la clase con tres días en modo mixto). Cuatro tests antiguos (seis casos: el del
limitador de la deriva y los de la incomodidad a largo plazo) exigían que `verify_accim_simulation` no diera ningún
desajuste en simulaciones del modelo de ejemplo, cuando el check 1 se saltaba sus zonas; ahora exigen que no lo dé
ningún otro check. No son más laxos en lo que comprobaban: los checks 3 a 6.

**Lo que queda por decidir** (`notes/questions.md`, 13/11/2026): qué deben informar los checks 1 y 2. Para el check 1:
dejarlo así, informarlo aparte de los desajustes (para que un resultado vacío signifique que el EMS funciona) o poder
saltárselo. Para el check 2: dejarlo así, darle a la función el de la clase, o escribirlo como los checks 3 a 6 (la
apertura de cada ventana contra las condiciones de su programa con los valores que lee el EMS, exacto). Mientras
tanto queda como estaba, con la documentación (sección 4.6.1) diciendo qué informa cada uno.

## 57. Los checks 1 y 2 de la verificación: el check 1 aparte, un check 2 exacto y una sola implementación

Decidido por el autor el 13/11/2026 («Haz los checks 1 y 2») sobre la pregunta que dejó abierta la sección 56: la
recomendación de Claude Code, es decir, informar el check 1 aparte de los desajustes, escribir el check 2 como los
checks 3 a 6 y tener una sola implementación para la función y la clase.

**Check 1: aparte de los desajustes.** Sus filas (`Check1_Cooling` y `Check1_Heating`: el sistema de una zona
encendido y la zona fuera de su consigna en más de `tolerance`) hablan del sistema de climatización, no del EMS. Ya no
están en la tabla que devuelve `verify_accim_simulation`, de modo que un resultado vacío significa que el EMS hace lo
que dicen sus programas. Se cuentan en el resumen, están en `resultado.attrs['setpoints_not_met']` (una tabla con las
mismas columnas) y el argumento nuevo `setpoints_not_met=True` las añade al resultado, como antes.

**Check 2: exacto.** Compara el factor de apertura de cada ventana con el de sus programas del EMS
(`SetMyVOF_<ventana>` y `SetWindowOperation_<ventana>`), con los valores que estos leen al principio de cada paso de
tiempo. Qué leen se midió con EnergyPlus 25.1, no se supuso:

- del paso anterior: la temperatura operativa de la zona y si el sistema enfrió o calentó (con los sistemas
  existentes, la carga hasta las consignas del termostato);
- del propio paso: la temperatura exterior y la velocidad del viento de la zona, los ocupantes, y la consigna de
  refrigeración, la consigna de ventilación y la temperatura exterior mínima que calcula el EMS.

Con esos valores la réplica es exacta (diferencia máxima del orden de 1e-15) en siete simulaciones: modo 2 con control
de ventilación 0 y 2, modo 1 con 0 y 1, dos de ellas también con una velocidad máxima del viento que se alcanza, y un
modelo con radiadores (`ex_mm`). Además coincide con los propios programas, ejecutados con el intérprete de Erl, en 14
combinaciones. Es un solo identificador, `Check2_OpeningFactor`, con `calculation_tolerance`, para los tres modos; la
descripción de cada desajuste lleva los valores leídos. En la semana de abril en modo mixto en la que el check
anterior daba 213 desajustes falsos, ahora no da ninguno.

Dos condiciones:

- Necesita las salidas con frecuencia de paso de tiempo. Con las horarias no se hace, y el resumen lo dice.
- Los programas leen la temperatura exterior y el viento *de la zona* (a la altura de su centroide), que las salidas
  estándar no tienen. `output_type='detailed'` las añade ahora en modo mixto (y, con `ex_mm`, la carga hasta las
  consignas). Sin ellas se usan las del sitio y el resumen lo avisa: en el modelo de ejemplo el viento de las zonas es
  el 49 % del del sitio, lo que no da ningún desajuste falso con la velocidad máxima por defecto (50 m/s) y da 75 y 480
  (de 6042 valores) con 1 m/s. Las salidas estándar no cambian; si deben llevarlas queda como entrada nueva de
  `TODO.md`. Las salidas detalladas en modo mixto sí cambian, a propósito: las tres configuraciones del golden master
  que las usan (`b02_vrf_mm_grid`, `b13_vrf_mm_scheduled_vent` y `s02_add_modify`) se han vuelto a escribir, y solo
  difieren de las anteriores en esos objetos `Output:Variable` (comprobado: sin ellos, el texto es idéntico).

**Una sola implementación.** `AccimSimulationVerifier` ejecuta el mismo código (`_setpoints_not_met()` y
`_window_mismatches()`): `violations['setpoint']` son las filas del check 1 y `violations['window']`, los desajustes
del check 2. Tiene los argumentos nuevos `tolerance` y `calculation_tolerance`, sigue leyendo el CSV que haya junto al
ESO y ya no lanza `ValueError` si falta una salida: el resumen dice qué no se comprueba y por qué. Desaparecen sus
identificadores (`Check1_TooHot`, `Check1_TooCold`, `Check2_Cond…`) y los de la función (`Check2_HVACmode…`). El
módulo pasa de 1990 a 1397 líneas.

**Otros cambios.** `accim.utils.read_csv_outputs()` (nueva, pública) lee el CSV de `ReadVarsESO` igual que
`read_eso_using_readvarseso()` devuelve las salidas; es la parte de esta que leía el CSV. Los dos archivos de tests que
esa mañana pasaron a exigir «ningún desajuste salvo los del check 1» vuelven a exigir un resultado vacío.

**Los tests** (`tests/core/test_verification.py`, 38): el check 1 con salidas inventadas (las filas aparte, con
`setpoints_not_met=True`, con otra tolerancia, y las baterías encontradas por los sensores del EMS o por su nombre);
el factor de apertura que espera el check 2 contra los programas ejecutados con el intérprete de Erl (`vrf_mm` y
`ex_mm`, siete casos de modo y control de ventilación, 1500 pasos aleatorios cada uno); el check 2 con salidas
inventadas (cada condición que cierra la ventana, una ventana mal abierta y otra mal cerrada, las salidas del sitio con
su aviso, las horarias sin comprobar); las salidas detalladas de modo mixto; y, con EnergyPlus 25.1, el check 1 de dos
días de julio, el check 2 de tres días de abril y mayo en cuatro configuraciones (salidas detalladas y estándar, modos
2 y 1, control 0 y 2), con la clase y con una ventana abierta a propósito, y el check 2 de una semana del modelo con
radiadores.

## 58. El estudio de validación de F3: ventiladores que controlan los ocupantes (`air_speed_heating`)

Resuelve la pregunta que quedó abierta el 12/11/2026 (sección 54), a petición del autor el 13/11/2026. Las decisiones
las tomó Claude Code por delegación y son **provisionales**: son elecciones del diseño del estudio, para acordar con
los autores de los modelos (entrada del mensaje a Ruiji Sun en `TODO.md`). Los valores por defecto de accim no cambian.

**El problema 1: los ventiladores subían también la consigna de calefacción.** El gancho del estándar 24 convierte los
dos límites de la banda causal del SET con una sola velocidad del aire, la del objeto People (decisión 5 del autor del
10/11). Con 1,1 met, 0,5 clo y 50 % de humedad, las consignas de 19,09 y 28,18 °C de SET son 20,1 y 28,9 °C a 0,1 m/s,
y 23,9 y 32,5 °C a 1,2 m/s: los ventiladores subían casi 4 K la consigna de calefacción, y las baterías de calor
funcionaban en sus horas. Además, el SET de una zona a 22 °C con 1,2 m/s es 16,7 °C (por debajo de la banda), cuando
sus ocupantes tendrían el ventilador apagado (21,1 °C).

**La solución: `air_speed_heating`.** Argumento nuevo de `SetSetpointHook`, `Sun2026SetpointHook`,
`apply_set_setpoints()` y `apply_sun2026_setpoints()` (`None` por defecto: sin él no cambia nada). Con él, la velocidad
del aire del gancho (o del objeto People) es la de unos ventiladores que controlan los ocupantes, que solo los usan
cuando los necesitan:

- la consigna de refrigeración se invierte con la velocidad de los ventiladores, y la de calefacción con
  `air_speed_heating` (0,1 m/s, aire en calma);
- el SET de cada zona (salidas `SET_<zona>`, `TSV_causal_<zona>` y `HoursInCausalBand_<zona>`, y `set_of_results()`)
  es el de aire en calma mientras no supere la consigna de refrigeración del SET, y el de los ventiladores cuando la
  supera;
- `table_indicators(pythermalcomfort_set={..., 'air_speed_heating': 0.1})` aplica la misma regla al SET de referencia
  de los indicadores, con el límite superior de la banda causal como umbral.

Es una corrección del lado cálido, como la de EN 16798-1 para los ventiladores (B.2.3 y tabla B.4: solo en verano, por
encima de 25 °C y con control personal; comprobado en la norma). El SET del modelo Pierce de EnergyPlus no puede seguir
esta regla (usa la velocidad del schedule en todas las horas); el SET de referencia es el de pythermalcomfort.

**El problema 2: el limitador de la deriva con consignas que cambian dentro del día.** `drift_mode='rate'` limita cada
paso de tiempo, también los no ocupados, a ± la tasa alrededor de la media de las consignas aplicadas en las horas
ocupadas del día anterior. Con ventiladores solo en las horas ocupadas, mantenía todo el día las consignas de esas
horas: con 1,2 m/s y 0,25 K/día, 343,6 kWh de calefacción en vez de 10,6 y 1549,6 kWh de refrigeración en vez de
2043,7 en la semana de julio. Eso no es una deriva entre días.

**Lo decidido para el problema 2.** El limitador se queda como está (cambiarlo es rediseñar F2, y la alternativa
correcta necesita memoria de las consignas de cada hora del día anterior). Se quita la causa en el estudio: la velocidad
de los ventiladores es la de todas las horas de la temporada de refrigeración (antes, la de las horas ocupadas). El
schedule dice la velocidad que los ocupantes *pueden* tener; las consignas de las horas no ocupadas son las que el
sistema mantendría para ellos, como en los demás casos, que tampoco tienen consigna reducida.

**El script** (`tools/indoor_adaptation_study.py`): los casos con ventiladores usan `air_speed_heating=0.1`
(`--air-speed-heating`; −1 para el comportamiento anterior) y el schedule de todas las horas (`--fan-hours 7 19` para
las horas ocupadas, como antes).

**Medido con los dos cambios** (semana del 15 al 21 de julio, modelo de ejemplo, Sevilla; entre paréntesis, antes):

| | 0,6 m/s | 0,9 m/s | 1,2 m/s |
| :--- | :--- | :--- | :--- |
| Baterías de calor, sin limitador (kWh) | 0 (0) | 0 (1,4) | 0 (10,6) |
| Baterías de calor, con limitador a 0,25 K/día (kWh) | 0 (27,8) | 0 (193,3) | 0 (343,6) |
| Baterías de frío, sin limitador (kWh) | 1546 (2082) | 1414 (2059) | 1341 (2044) |
| Limitador a 0,25 / 0,5 / 1,0 K/día: frío | +2,4 / +0,2 / −1,1 % | +5,1 / +1,9 / −0,8 % | +6,7 / +3,1 / −0,5 % |

Antes, el limitador cambiaba el frío de 1,2 m/s un −24 %. Los casos sin ventiladores y la semana de enero dan lo mismo
que el 12/11.

**Lo que queda, sin decidir.** El limitador sigue actuando sobre todo *dentro* del día con las consignas del gancho,
que siguen la temperatura radiante, la humedad y la ropa. En esa semana, la consigna de refrigeración cambia de 0,2 a
0,9 K dentro de las horas ocupadas de cada día sin ventiladores y de 2,0 a 3,5 K con 1,2 m/s, mientras que su media
diaria cambia de 0,16 a 0,25 K y de 0,02 a 1,35 K entre días; el limitador toca alguna consigna en 81, 70 y 25 de las
120 horas ocupadas sin ventiladores, y en 86, 75 y 56 con ellos. Por eso la sensibilidad del ahorro a la tasa de deriva
es limpia en las consignas adaptativas del caso (ii), constantes dentro del día, y la del modelo SET causal mezcla la
deriva entre días con el perfil de cada día. `TODO.md` tiene una entrada nueva con la alternativa (limitar la consigna
de cada hora respecto a la de la misma hora del último día ocupado), para que el autor decida con los autores de los
modelos si los casos del SET causal siguen en el caso (v).

**Los tests** (cinco nuevos, en `tests/core/test_sun2026_set.py` y `tests/core/test_people_set_inputs.py`): las
consignas con `air_speed_heating` son exactamente la de calefacción del aire en calma y la de refrigeración de los
ventiladores (bisección, con las dos temperaturas radiantes, y tabla); el SET de la regla; el gancho del estándar 24
con un controlador simulado; `set_of_results()` y `table_indicators()` con las entradas de los objetos People; y, con
EnergyPlus, tres días de julio del modelo de ejemplo con ventiladores de 1,2 m/s (consignas, SET de cada paso y
baterías de calor apagadas).
