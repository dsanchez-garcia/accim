# accim — Propuestas de mejora y nuevas funciones (tras la 1.1.0) — v04: revisión de la implementación de la 1.2.0 y pendientes

- Fecha: 2026-11-10. Rama `v1.2.0` en `d6dbae16` (18 commits de la sesión autónoma de Copilot del 9–10/11/2026, informe en `notes/INFORME_SESION_v1.2.0_2026-11-10.md`), actualizada hoy en `D:\Python\accim` por *fast-forward*; los 8 archivos sin seguimiento de `notes/` (bloque F y adjuntos) no se han tocado.
- Objeto de esta versión: (1) resultado de la revisión independiente de las 15 propuestas implementadas (A3, A4, A6, B1–B5, C1, C2, D1, D2, E1, E2, E4; A1, A2 y A5 venían de antes), hecha leyendo el código y ejecutando sus tests con EnergyPlus 25.1; (2) respuesta a las 36 decisiones provisionales de `notes/questions.md` y a las 8 tareas bloqueadas de `TODO.md`; (3) revisión del A6 (SET) a la luz del bloque F (`notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md`, paper con Ruiji Sun) y plan de convergencia A6 → F1/F2; (4) lista de tareas para la siguiente sesión de Copilot, con sus prompts.
- Etiquetas: **[verificado]** leído en código/fuente o comprobado ejecutando; **[hallazgo]** problema encontrado en la revisión; **[recomendación para el autor]** respuesta propuesta a una pregunta de `questions.md` o a una tarea bloqueada, que el autor confirma o edita antes de la siguiente sesión; **[pendiente]** sigue abierto.
- Versiones anteriores: v03 (base científica, §11 fórmulas, §12 EnergyPlus; sigue vigente), v02, v01.

---

## 0. Resumen ejecutivo

**Veredicto global.** Las 15 propuestas están implementadas y son, en lo esencial, correctas: las ecuaciones, coeficientes y límites coinciden con la hoja de fórmulas de la v03 (§11) en todos los casos comprobados (catálogo λ completo, ATHB, SET, EN 16798-1 B.1/B.2, Te,ref, Aqilah 2025, métodos A/B/C del CEN/TR 16798-2, PPD), los programas Erl no usan `TrendVariable`, los IDF de salida de la 1.1.0 no cambian (según el *golden master* del implementador; no se ha vuelto a ejecutar aquí) y el implementador documentó con honestidad todo lo que decidió o dejó bloqueado. Los revisores no encontraron **ningún error que dé resultados equivocados en el uso previsto**, pero sí **cuatro hallazgos de primer orden** que hay que corregir antes de publicar la 1.2.0:

1. **A4/A6 — los ganchos de la API sólo sobrescriben las consignas actuadas.** Los contadores de horas de confort del ACCIS, los indicadores de largo plazo de C2, la aplicabilidad de `HoursBelow` y las salidas `Adaptive Cooling/Heating Setpoint Temperature_<zone>` siguen calculándose con las consignas **adaptativas** que el termostato ya no sigue. En un modelo con ATHB o SET, las horas de confort y las columnas de consigna de `Table` son las de otro modelo. **[hallazgo, diseño; corregir]**
2. **E1 — `compute_setpoints` no reproduce el PMOT de EnergyPlus cuando el RunPeriod empieza entre el 2 y el 30 de enero**: en `ThermalComfort.cc` (25.1) la rama de "wrap" deja la media diaria del día anterior al inicio sustituida por la del 31 de diciembre; explica exactamente los 0.14 °C del `TODO.md` del implementador. **[hallazgo, científico; corregir y testear]**
3. **A6 — la justificación de la tabla por HR es errónea en general**: `set_tmp` de pythermalcomfort **sí** funciona dentro de los *callbacks* de EnergyPlus 25.1 con Python 3.12 / numba 0.68.1 (tres simulaciones, 5196 llamadas cada una, incluida la compilación JIT en el *callback*); el *access violation* es propio del entorno Python 3.14 del implementador. La primera llamada a `set_tmp` cuesta 7.0 s (JIT) y las siguientes 0.8 ms. La tabla es un buen diseño de rendimiento y debe quedarse por defecto, pero hay que reescribir la documentación y añadir el método por bisección en el *callback*, que es el que necesita F1 (entradas variables). **[hallazgo; corregir documentación y añadir opción]**
4. **B4 — el ComfStand 23 (Aqilah 2025) lee el RMOT de EnergyPlus, que en los primeros días de un RunPeriod está un 21 % (0.8⁷) por debajo de la media móvil verdadera** (la ec. 19.82 no divide por 1 − α⁷); con periodos de prueba de 1–2 semanas la temperatura de confort del 23 queda sesgada a la baja (−2.4/−3.9/−5.1 K el día 1 en tres arranques comprobados frente al gemelo YAML 101, que se inicializa desde el EPW). Para simulaciones anuales es irrelevante; para los tests y los estudios cortos, no. **[hallazgo, científico; decidir y documentar]**

Además: 2 decisiones provisionales que deben cambiarse (A3: una clave del catálogo sólo rellena un lado y empareja un λ con fuente con el −0.293 sin fuente; B3: el YAML de Qatar incompleto hace fallar la carga de la carpeta de ejemplos), 4 tests de `tests/core` que importan besos y fallan en vez de saltarse, y el renombrado de B5 pedido por el autor en el bloque F que no está en `TODO.md`. El detalle está en §3; las acciones para la siguiente sesión de Copilot, con sus prompts, en §7.

**Lo que no se pudo comprobar aquí** (§8): la igualdad de los dos backends a través de `run_ep` (el *sandbox* deniega las tuberías de `multiprocessing`; los tests equivalentes se repitieron en proceso y pasaron), el *golden master* completo, la suite entera, la GUI y la compilación de la documentación, y el fallo de `set_tmp` en Python 3.14.

---

## 1. Método de la revisión

- Cuatro revisores independientes (sub-agentes de Claude Science, 10/11/2026, 63–83 min cada uno), de sólo lectura sobre `D:\Python\accim` en `d6dbae16`, con la v03 §11/§12 como patrón y el informe del implementador como mapa: **Preview-Verify** (E1, E2, D2, D1, C2), **Custom-model** (B1, B5, B2, A3), **Registry** (B3, B4, C1, E4) y **API-hooks** (A4, A6).
- Tests ejecutados con `C:\Users\sanga\.claude-science\conda\envs\pecs-eplus\python.exe` (Python 3.12.15, eppy, pandas, pytest, pythermalcomfort 4.8.1, numba 0.68.1; **sin besos**), `PYTHONPATH=D:\Python\accim`, EnergyPlus 25.1: 13 archivos de test, **≈ 310 tests pasados**; los fallos (≈ 16) son todos del entorno: tuberías de `multiprocessing` denegadas (tests EMS-vs-API y `run_ep`), `ReadVarsESO.exe` de 25.1 no lanzable (WinError 623) y 4 tests de `tests/core` que importan besos. Los tres tests con EnergyPlus de A4/A6 se repitieron en proceso con `run_simulation` y sus aserciones pasaron.
- Comprobaciones propias de los revisores: lectura de `ThermalComfort.cc` de EnergyPlus 25.1 (E1, B4); simulación propia con umbrales negativos de B2; comparación `compute_setpoints` 23 vs 101 (B4); `inspect.getsource` de `pmv_athb`, `pmv_e`, `pmv_a`, `set_tmp` (A4, A6); medición de tiempos de `set_tmp` (7.04 s la primera llamada, 0.8 ms después); tres simulaciones con `set_tmp` dentro de los *callbacks* (A6); verificación de los 19 valores del catálogo λ (A3); lectura del *wheel* de pyfwg 0.4.0 (E4).
- Resultados completos de los revisores: archivo adjunto `notes/attachments/revision_v1.2.0_hallazgos.json` (estructurado: veredictos, hallazgos, decisiones revisadas, tests ejecutados, no evaluado).

---

## 2. Veredicto por propuesta

| Propuesta | Commit | Veredicto | Resumen |
|---|---|---|---|
| E1 `accim.sim.preview` | `dcb5ddff` | correcta con incidencias | Métricas exteriores exactas (B.1, B.2, n días, Te,ref, mensual); reproduce `ThermalComfort.cc` salvo el arranque entre el 2 y el 30 de enero (hallazgo E1-1). |
| D2 `Table` (dos commits) | `aff9cfc2`, `eec5f8e7` | correcta | Clasificación de columnas correcta (índices promediados, horas sumadas); valores "(summed)" de bloque/edificio para magnitudes intensivas (convención previa de `Table`). |
| E2 `verify_accim_simulation` | `622bc7d4` | correcta con incidencias | Comprobaciones 3–6 fieles al Erl; docstring dice "cuatro" categorías y son seis; comprobación 4 heredará el hallazgo E1-1. |
| A3 catálogo λ, `pmv_sign` | `9cfac72f` | correcta con incidencias | 19 valores verificados uno a uno; clave que sólo rellena un lado (cambiar); sin validación de signos de las consignas con `pmv_sign`. |
| B1 métrica exterior | `aedfa3a6` | correcta con incidencias | Erl correcto (fin de hora `Minute > 59.5`, fin de día, *warm-up* excluido, inicialización desde el EPW); `T0` de Te,ref intradiario; `nan` y notación exponencial posibles en constantes Erl; PMOT = 0 en el primer paso. |
| B5 suelo/techo, `HoursBelow` | `c2e0f446` | correcta con incidencias | Acota la consigna **con** tolerancia (las `noTol` quedan a `floor − tol`); techo redondeado a 25.9999; docstring de SetVST inexacto. |
| C1 parámetros | `25152d45` | correcta con incidencias (sólo lectura) | Clases y rangos correctos; `activity_level` no aplicable con corrección metabólica (documentar). |
| D1 indicadores | `2f139de3` | correcta | Métodos A/B/C, PPD y Tabla E.1 exactos; diferencia horario/paso de tiempo frente a los contadores EMS de C2 sin documentar; TODO P1 de `Table` con `timestep`. |
| B2 regímenes | `ab767df8` | correcta con incidencias | Prioridad, condiciones y umbrales negativos verificados en EnergyPlus; realimentación posible con `hvac_on/off`; `CustomRegime` promediado. |
| B3 registro YAML | `975f7969` | correcta con incidencias | Esquema, validación y Erl ≥ 100 correctos; Qatar incompleto rompe la carga por carpeta; orden de categorías y signos de los offsets sin comprobar. |
| B4 ComfStand 23 | `2be69e27` | correcta con incidencias | Ecuación, bandas, aplicabilidad y estáticas correctas; transitorio del RMOT (hallazgo B4-1); sin test 23 vs 101; estáticas no configurables (D2). |
| C2 objetivos largo plazo | `9f26f39a` | correcta con incidencias | Contadores Erl fieles a A/B; rango = consignas del ACCIS sin tolerancia (no categorías EN); método C bloqueado. |
| E4 pyfwg | `c6ee7df4` | correcta con incidencias | Firma de `morph_epw_global` correcta para pyfwg 0.4.0; diferencia de isla de calor urbana por defecto entre motores; sobrescritura con `ensemble=0`. |
| A4 ATHB | `689362d8` | correcta con incidencias | Ecuaciones y unidades exactas (llama a `pmv_athb`); bisección monótona; hallazgo de los contadores (0-1); saturación silenciosa en 10/30 °C; test científico débil. |
| A6 SET | `c8e127c9` | correcta con incidencias | Tabla por HR exacta por construcción (error de interpolación ≤ 0.03 K); justificación del fallo errónea; sin salida SET; postura `standing` por defecto; insensible a v < 0.1 m/s. |
| C3 (R-06), D2 completado | `9e7d54f1`, `eec5f8e7` | correctas | — |

A1, A2 y A5 (sesión anterior) no se han vuelto a revisar.

---

## 3. Hallazgos **[hallazgo]** (fuente: los cuatro revisores; severidad: *científico*, *diseño*, *test*, *doc*, *menor*)

### 3.1 De primer orden (corregir antes de la 1.2.0)

**A4/A6-1 (diseño).** `AthbSetpointHook.__call__` y `SetSetpointHook.__call__` escriben sólo `AHST_Act_<zone>`/`ACST_Act_<zone>` después de los programas del ACCIS; `CountHours_<zone>`, `CountHoursNoApp`, los contadores de C2 y B5 y las salidas `Adaptive … Setpoint Temperature_<zone>` usan `ACSTnoTol`/`AHSTnoTol` adaptativos. Corrección: (a) que el gancho escriba también las variables globales `ACST`, `AHST`, `ACSTnoTol`, `AHSTnoTol` (y las redondeadas) antes de que corran los contadores — como los contadores van en el mismo *calling point* y ya han corrido, hace falta mover los programas de recuento a un *calling point* posterior (`AfterPredictorAfterHVACManagers`) o ejecutarlos desde el gancho (`controller.run_calling_point`), o (b) que el gancho cuente sus propias horas en Python desde `<zone>_OpT` y `Occ_count_<zone>` y publique variables `ATHB_ComfHours_<zone>`/`SET_ComfHours_<zone>`, y que `Table` y la documentación digan que las horas y consignas "Adaptive" son las del ACCIS. Mínimo imprescindible: la documentación (4.9.1/4.9.2, CHANGELOG).

**E1-1 (científico).** `accim/sim/preview.py::_energyplus_daily` y `energyplus_running_means`: para RunPeriods que empiezan el día D con 2 ≤ D ≤ 30 de enero, `CalcThermalComfortAdaptiveASH55` (25.1) lee los días 1…D−1 en las posiciones 31−D…30 y los últimos 30−(D−1) días de diciembre en 1…30−(D−1), pero el escalar `avgDryBulbASH` se queda con el **último día leído (31 de diciembre)** y en el primer `BeginDayFlag` hace `DailyAveOutTemp(30) = avgDryBulbASH`, pisando la media del día D−1 con la del 31 de diciembre (coincide con los 0.1424 °C observados). Corrección: en `_energyplus_daily`, con 1 ≤ D−1 ≤ 29, la media diaria del día D−1 de las ventanas PMOT debe ser la del 31 de diciembre (RMOT no se ve afectado); test con EnergyPlus con arranque entre el 2 y el 30 de enero (el implementador ya tiene la simulación del 8 de enero de B5); nota en los docstrings y en la comprobación 4 de E2.

**A6-1 (doc + diseño).** Reescribir en `comfort_hooks.py`, CHANGELOG, DEVLOG, CAMBIOS §21 y docs 4.9.2: "`set_tmp` detuvo EnergyPlus 25.1 con un *access violation* en el entorno de desarrollo (Python 3.14, pythermalcomfort 4.8.1); funciona en Python 3.12 con numba 0.68.1" en vez de "no puede calcularse en los *callbacks*". Añadir `SetSetpointHook(method='table' | 'bisection')` con `'table'` por defecto y `'bisection'` que llame a `set_tmp` en el *callback* (con calentamiento del JIT antes de `run_simulation`: una llamada escalar y una vectorial), que es la base de F1 (§4). Documentar el coste único del JIT (≈ 7 s) y que numba lo cachea.

**B4-1 (científico).** Decidir entre: (a) mantener el RMOT de EnergyPlus (fiel a Aqilah 2025 en régimen y coherente con el ComfStand 1) documentando el transitorio y recomendando ≥ 3 semanas de simulación, o (b) usar `rmot_alpha` inicializado desde el EPW (como el YAML 101) cuando se dé EPW a `AddAccis`. Recomendación: **(b) cuando hay EPW, (a) si no**, con aviso. En cualquier caso añadir el test 23 vs 101: `|ComfTemp_23 − ComfTemp_101| < 0.1 K` desde el día 21 y `> 1 K` el día 1 (documenta el transitorio).

### 3.2 Decisiones provisionales que deben cambiarse (véase también §5)

- **A3-1 (diseño).** Una clave del catálogo en un solo argumento deja el otro lado en el valor por defecto −0.293/0.293 (sin fuente; el lado frío de Yao es −0.125). Corrección: argumento nuevo `adaptive_coefficients=<clave>` que fija los dos lados (error si se combina con números explícitos), manteniendo las claves por lado; como mínimo, aviso cuando un lado es clave y el otro queda en el numérico por defecto.
- **B3-1 (diseño).** `qat_indraganti2018_hvac.yaml` incompleto en la carpeta de ejemplos → `load_comfort_standards(carpeta)` falla entera (verificado). Corrección: completar el YAML con los datos de §6.3 (recomendación) o moverlo a `incomplete/` hasta entonces; opción `strict=False` en el cargador.

### 3.3 Científicos y de diseño de segundo orden

- **B5-1 (diseño).** `ApplySetpointLimits_<zone>` acota `ACST`/`AHST`, que ya incluyen `ACSTtol`/`AHSTtol`; por tanto `AHSTnoTol = floor − AHSTtol` y los contadores de confort, D1 y C2 usan un límite inferior 0.1 K por debajo del suelo. Decidir: documentarlo, o acotar también `AHSTnoTol`/`ACSTnoTol` tras `SetASTnoTol` (recomendado: acotar también; el suelo es un límite de la consigna "sin tolerancia" por definición).
- **B5-2 (menor).** El techo redondeado hacia abajo da `ceiling − 1/SetpointAcc` (25.9999 con 26 °C); el suelo es exacto. Recomendación: fijar `roundedACST = ACSTceil` en la rama del techo.
- **B5-3 (doc).** El docstring de `setpoint_limits.py` dice que SetVST usa las consignas acotadas; en la rama aplicable `VST = ComfTemp + VSToffset` no está acotado; sólo `roundedACST/AHST` lo están. Corregir docstring y docs 4.2.3.
- **B1-1 (diseño).** `T0` de `te_ref_nl` es la media (máx+mín)/2 **parcial** del día en curso: Te,ref deriva dentro del día (a la 01:00 `T0` es la temperatura nocturna). Van der Linden define `Ti` como la media de la máxima y la mínima del día completo. Recomendación: cuando hay EPW, escribir el (máx+mín)/2 del día como `Schedule:File` diario leído por un sensor `Schedule Value`; sin EPW, la opción (b) de `questions.md` (día anterior) y aviso; documentar la deriva si se mantiene el valor corriente.
- **B1-2 (menor).** Con `monthly_mean`, un EPW sin algún mes escribe `set OutdoorMonthlyMean = nan`; `_number()` (= `repr(float)`) puede emitir notación exponencial, que Erl no lee (`custom_regimes._number` ya usa `numpy.format_float_positional`). Corrección: `ValueError` si falta un mes; un único formateador de constantes Erl compartido.
- **B1-3 (menor).** En el primer paso del RunPeriod los sensores PMOT/RMOT leen 0 (comportamiento de la 1.1.0); con B2 una condición `('metric_below', x)` se cumple espuriamente en ese paso. Documentar; opcionalmente proteger las condiciones con `if PMOT <> 0` (cambiaría IDF de `pmot`: decisión del autor).
- **B2-1 (diseño).** `hvac_on`/`hvac_off` usan el estado del HVAC del paso anterior y el régimen cambia las consignas que deciden el HVAC de este paso: posible alternancia paso a paso. Documentar el riesgo; opción futura de permanencia mínima (N pasos).
- **B2-2 / D2-2 (menor).** `CustomRegime_<zone>` promediado por hora da valores no enteros (2.8333 observado) cuando el régimen cambia dentro de la hora. Documentar que sólo la frecuencia `timestep` da el régimen de cada paso.
- **A4-1 (diseño).** Saturación silenciosa en los límites de `temperature_range` (10/30 °C; 10/40 °C en SET): con RMOT ≥ 33 °C la consigna de refrigeración del ATHB roza 30 °C. Registrar la saturación (contador por zona o variable `ATHB_saturated_<zone>`) y avisar al final.
- **A4-2 (diseño).** `met` y `air_speed` del gancho son independientes del *Activity Level* (W/persona) y de la velocidad del `People` que EnergyPlus usa para las ganancias internas y sus propias salidas de confort; `air_speed` es la velocidad **relativa** de pythermalcomfort (el usuario debe sumar 0.3·(met − 1) para met > 1). Documentar la relación 1 met = 58.2 W/m² × 1.8 m² ≈ 104.8 W/persona; opción futura `met='people'`.
- **A4-3 (menor).** `apply_athb_setpoints(output_frequencies=('hourly',))` ignora las frecuencias del modelo (mezcla en `Table`); `met = 0` aceptado. Por defecto las frecuencias de las salidas existentes del ACCIS; aviso fuera de 0.8–4 met y v > 1 m/s.
- **A6-2 (científico, menor).** La consigna es la `Top` tal que `SET(Top, Top, …) = objetivo`; el SET de la zona pondera `ta`/`tr` con `h_r = 4.7` y `h_cc ≈ 3.0` (0.61/0.39 a 0.1 m/s y 1.1 met), no 0.5/0.5. Pequeño, sin documentar; con `method='bisection'` puede resolverse con el desfase `tr − ta` del paso anterior (y es lo que pide F1 con `tr_mode='zone'`).
- **A6-3 (diseño).** Sin salida SET de las zonas; el modelo preparado no tiene `Zone Mean Air/Radiant Temperature` ni HR en sus salidas, así que el postproceso que describe la documentación **no es posible** con su CSV. Corrección: añadir esos sensores/salidas como hace `apply_athb_setpoints`, un auxiliar `set_of_results(df, hook)` y, con `'bisection'`, la variable `SET_<zone>`; opcionalmente `Pierce` en el `People` para el SET de EnergyPlus (tarea E-F1 del bloque F).
- **A6-4 (diseño).** `position='standing'` por defecto para ocupantes sedentarios (factor radiativo 0.73 frente a 0.70 sentado); en el código SET de ASHRAE 55 la velocidad se acota a `max(v, 0.1)` y `h_cc = max(h_cc, 5.66·(met − 0.85)^0.39)`, de modo que a 1.2 met la velocidad no influye hasta ≈ 0.2 m/s. Decidir la postura (recomendado `'sitting'` si met ≤ 1.2) y documentar la insensibilidad para que no se tome por un error.
- **C2-1 (diseño).** El rango de los contadores es la consigna del ACCIS sin tolerancia, no la categoría EN 16798-1 pedida en v03: con ComfMod 3, consignas estáticas, CUSTOM o suelo/techo mide "cuánto falla el control en mantener su propia banda", no el disconfort frente a una norma, y dos configuraciones con modelos distintos no son comparables. Mantener el defecto; añadir `long_term_range=('en16798', categoría)` opcional con límites constantes.
- **D1-1 (doc).** La documentación dice que `long_term_indicators` funciona con `timestep` u `hourly`, pero el TODO P1 del propio implementador dice que `Table` con `source_frequency='timestep'` y `standard_outputs=True` descarta todas las salidas; además los indicadores de `Table` sobre medias horarias no coinciden con los contadores EMS por paso (con la `OpT` del paso anterior). Arreglar el P1 y añadir la frase de diferencia.
- **E4-1 (diseño).** `morph_epws(engine='pyfwg')` no fija `fwg_add_uhi`: con jars v4/v5 pyfwg envía `-add_uhi=true:14:1` (isla de calor LCZ 14→1) y con v3 `0:14:1`; el motor Java de accim nunca la pasa → los dos motores no dan los mismos EPW futuros. Recomendación: `fwg_add_uhi=False` explícito salvo que `pyfwg_arguments` lo dé; documentar.
- **E4-2 (menor).** Con `fwg_options_ensemble=0` hay un EPW por GCM y todos se renombran al mismo `<EPW>_<escenario>.epw`: sobrevive el último sin aviso (preexistente en Java). Avisar o incluir el GCM en el nombre.
- **E4-3 (menor).** `ValueError` de `morph_epw_global` no limpia las carpetas temporales (los `OSError`/`RuntimeError` sí).
- **B3-2 (menor).** Las líneas `ApplyCAT`/ComfMod 2 siguen el orden del YAML (90 antes de 80) y el 23 integrado lista 80, 90: Erl semánticamente igual pero no byte a byte. Iterar `sorted(category_offsets)`.
- **B3-3 (diseño).** Sin comprobación de signo de los offsets de categoría (un YAML con `heating_offset: 1.5` pone la consigna de calefacción por encima de la de confort). Aviso cuando `cooling_offset < 0` o `heating_offset > 0`; convención de signos en la documentación.
- **A3-2 (menor).** Con `pmv_sign`, la inversa usa λ por nombre de lado, no por signo del valor; validar `pmv_cooling_setpoint ≥ 0` y `pmv_heating_setpoint ≤ 0` (también en diccionarios).
- **B4-2 (diseño).** Consignas estáticas 20/28 literales (D2 decía "configurables"): véase §6.2.

### 3.4 Tests

- **4 tests de `tests/core` importan besos y fallan en vez de saltarse** (`test_setpoint_limits.py::test_modify_accis_adds_and_keeps_the_floor_and_ceiling`, `::test_the_models_of_earlier_versions…`, `test_jpn_aqilah2025.py::test_the_valid_combinations_of_the_parametric_module`, `::test_the_models_of_earlier_versions_do_not_have_it`): `pytest.importorskip('besos')` o mover las aserciones paramétricas a `tests/parametric_and_optimisation`.
- **A4:** el test con EnergyPlus comprueba `schedule == bisección(sensores)` y sólo `−3 ≤ ATHB_PMV ≤ 3`; falta una aserción acotada de la afirmación científica (p. ej. `ATHB_PMV ≤ sp_cool + 0.25` en ≥ 95 % de los pasos ocupados con refrigeración activa, o una variante IdealLoads del modelo de ejemplo) y que `ATHB_PMV_<zone> == athb_pmv(MAT, MRT, RH)` del paso anterior.
- **B4:** falta el test 23 vs 101 (§3.1). **E1:** falta el test con arranque 2–30 de enero (§3.1). **B1:** EnergyPlus nunca se compara directamente con pandas para `rmot_7day`/`ndrm`/`te_ref_nl` (sólo vía `compute_setpoints`); añadir la aserción directa en `test_the_outdoor_metrics_in_energyplus`.
- **E4:** el único test contra la API real de pyfwg se salta sin pyfwg instalado (CI: instalar `accim[weather]`).
- **Infraestructura:** ofrecer `run_simulations(processes=0)` / `run_ep(processes=0)` para ejecutar en el proceso actual (los tests EMS-vs-API serían ejecutables en entornos sin tuberías de `multiprocessing`, como este *sandbox*).

### 3.5 Documentación

- E2: "four categories of checks" → seis; nota sobre el `.stat` (EnergyPlus usa medias mensuales para el PMOT si hay `.stat` junto al EPW; la comprobación 4 no lo reproduce).
- E1: "calculates a year in about a second" → "a few seconds" (3.3 s medidos).
- C1: `activity_level` no es parámetro de modelos con `metabolic_correction=True` (`set_pmv_input_parameters` lanza `ValueError`); decirlo en `parametric_and_optimisation.rst`.
- A4/A6: coste único del JIT; "(summed)" de bloque/edificio de magnitudes intensivas en `Table` (convención previa, pero las columnas nuevas lo multiplican); `BANNER` de `AddAccis` aún dice `v1.1.0` (lista de la release).
- E2: `_pmv_index_mismatches` infiere `apply_to_heating` por la ausencia de `if` en el programa monitor: acoplado al texto del Erl; leerlo de los argumentos guardados en el IDF o comentar la dependencia.

## 4. Revisión del A6 (SET) frente al bloque F (paper con Ruiji Sun)

### 4.1 Lo que hay (A6, commit `c8e127c9`) **[verificado en `accim/sim/comfort_hooks.py`]**
- `apply_set_setpoints(building, ...)` + `SetSetpointHook(zones, set_cooling_setpoint, set_heating_setpoint, met, clo, air_speed, position='standing', tolerance_k=0.1, max_iterations=20, temperature_range=SET_TEMPERATURE_RANGE)`. Sin valores por defecto para las consignas SET ni para met/clo/velocidad (v03 no los daba).
- La consigna es la **temperatura operativa** `Top` tal que `SET(tdb = tr = Top, v, RH, met, clo) = SET_sp`, resuelta por bisección; como met, clo y v son constantes del hook, la consigna sólo depende de la HR, y el hook **tabula** las consignas para HR = 0…100 % (paso 1 %) al construirse e interpola en cada paso con el sensor `SET_RH_<zone>`. Motivo: `pythermalcomfort.models.set_tmp` provoca un *access violation* en EnergyPlus 25.1 al llamarse dentro de los *callbacks* de la API (el `pmv_athb` de A4 no).
- Sin salida del SET de la zona (ni el Pierce de EnergyPlus ni el de pythermalcomfort); las consignas PPD se remiten a `apply_pmv_setpoints` (categorías I–IV); vía Erl (a) y *cooling effect*: bloqueados.

### 4.2 Lo que necesita F1 (Sun, Brager & Schiavon 2026; decisiones del autor del 10/11/2026 en `PROPUESTA_ADAPTACION_INTERIOR_v03.md` §6) **[verificado en ese documento]**
| Requisito F1 | Estado en A6 | Qué falta |
|---|---|---|
| Banda SET causal: `TSV = 0.11·SET − 2.6`; `SET_heat = (−tsv_limit + 2.6)/0.11`, `SET_cool = (tsv_limit + 2.6)/0.11` (19.1 / 28.2 °C con 0.5; neutro 23.6 °C); `tsv_limit` 0.5 por defecto, 0.7/1.0 con aviso de extrapolación; CAT 80 y 90 → 0.5 | A6 recibe dos SET numéricos cualesquiera | Un `ComfStand 24 INT Sun2026 SET` que fije las consignas SET desde `tsv_limit` y dos *comfort modes* (`SET band`, `SET neutral ± offset`) |
| Incógnita de la inversión: **temperatura de aire** con la Tr real de la zona (`tr_mode='zone'`, por defecto) o `tr = ta` (`'equal_air'`) | A6 resuelve `Top` con `tr = ta = Top` (equivale a `'equal_air'`) y actúa el termostato de temperatura operativa | `tr_mode`; con `'zone'`, leer `Zone Mean Radiant Temperature` y resolver `ta`; decidir qué termostato recibe el valor (ver 4.4) |
| clo, met y velocidad **variables en el tiempo** desde los schedules del `People` (clo por estación o `DynamicClothingModelASHRAE55` de A5; ventiladores vía schedule de velocidad) | Constantes del hook → la tabla por HR es válida | Leer los schedules cada paso (sensores EMS `Schedule Value`); la tabla por HR deja de bastar: hace falta `set_tmp` en el *callback* o una tabla multidimensional (HR × clo × v × met × tr−ta) |
| Suelo sanitario común de B5 tras la inversión (D5) y aviso si la consigna invertida de calefacción baja de 18 °C | A6 recorta con `temperature_range` (10–30 °C) y no usa B5 | Aplicar `heating_setpoint_floor` (o su nuevo nombre, §4.5) después de la bisección; aviso en el log |
| Salidas: SET de EnergyPlus (`Pierce` en el `People`, `Zone Thermal Comfort Pierce Model Standard Effective Temperature`), SET recalculado por accim, TSV causal, horas dentro de la banda | Ninguna salida de SET | Añadir `Pierce` a *Thermal Comfort Model Type* como `_update_fanger_object` hace con Fanger; variables EMS `SET_<zone>`, `TSV_causal_<zone>`, contador de horas |
| Tarea E-F1: comparar hora a hora el SET Pierce de EnergyPlus con el de pythermalcomfort y anotar la diferencia media y máxima en `notes/decisions.md` | No hecha | Simulación corta con el IDF de ejemplo; es la condición para usar F1 en el artículo |

### 4.3 El bloqueo técnico: `set_tmp` dentro de los *callbacks*
Hipótesis más probable **[inferido; el revisor API-hooks mide los tiempos, véase §3]**: `set_tmp` de pythermalcomfort 4.8.1 compila con **numba** en la primera llamada (segundos) y la compilación en el hilo del *callback* de EnergyPlus (con su propio *stack* y *signal handlers*) produce el *access violation*; `pmv_athb` no usa numba y funciona. Soluciones, por orden de preferencia:
1. **Calentar el JIT antes de `run_simulation`**: llamar una vez a `set_tmp` (escalares y arrays) en el proceso padre antes de arrancar EnergyPlus; si el fallo persiste, fijar `NUMBA_DISABLE_JIT=1` sólo para ese proceso (`set_tmp` en modo Python puro: ~ms por llamada, suficiente para una bisección de 20 pasos por zona).
2. **Interpolación multidimensional** precalculada: tabla `Top*(RH, clo, v)` con los valores discretos que toman los schedules (clo por estación: 2 valores; v: los del schedule; met: 1–2), construida al preparar el hook; exacta cuando los schedules son escalonados, aproximada con el clo dinámico de A5 (que es continuo en `ta6`).
3. **Reimplementar el SET de Gagge (dos nodos) en Python puro dentro de accim** (`accim.sim.set_model`), que además permite reproducir exactamente el Pierce de EnergyPlus (coeficientes del Engineering Reference §19.1.4: `hc = 8.6·v^0.53` con v ≥ 0.137 m/s, `hc = 5.66·(met − 0.85)^0.39` si met > 0.9) y elimina la dependencia de pythermalcomfort en el bucle. Más trabajo, pero es la única vía que garantiza SET_accim == SET_EnergyPlus.

### 4.4 Decisión que el A6 deja implícita y F1 hace explícita **[pendiente del autor]**
A6 controla la temperatura operativa (termostato dual de Top del ACCIS) con `tr = ta`. F1 (decisión 4 del autor) pide resolver `ta` con la Tr real de la zona. Son compatibles sólo si el termostato que recibe la consigna controla la temperatura de **aire**: con `tr_mode='zone'`, la consigna debe ir al termostato de aire (o convertirse en Top = (ta + tr)/2 antes de actuar el de Top). Propuesta: en `'zone'`, actuar la consigna de aire; en `'equal_air'`, la de Top (comportamiento actual de A6). Hay que decidirlo antes de implementar F1.

### 4.5 Renombrado de B5 pedido por el autor (decisión 8 del bloque F) **[pendiente, P1 antes de la 1.2.0]**
`heating_setpoint_floor` / `cooling_setpoint_ceiling` → `heating_setpoint_minimum` / `cooling_setpoint_maximum` (claves EMS `AHSTmin` / `ACSTmax`; parámetros `HeatingSetpointMinimum` / `CoolingSetpointMaximum`), con alias deprecados vía `accim._deprecation`. No está en `TODO.md` (comprobado hoy): añadirlo.

### 4.6 Plan de convergencia A6 → F1 (orden recomendado)
1. Resolver 4.3 (prueba del calentamiento JIT; si falla, opción 2) y 4.5 (renombrado). 2. Tarea E-F1 (SET Pierce vs pythermalcomfort). 3. Generalizar `SetSetpointHook`: entradas dinámicas desde los schedules, `tr_mode`, suelo B5, salidas SET/TSV/horas. 4. `ComfStand 24` como capa fina sobre el hook (consignas SET desde `tsv_limit`). 5. F2 (limitador de deriva) como módulo independiente aplicable a cualquier ComfStand (su prompt ya está en `notes/PROMPTS_COPILOT_bloque_F_v02.md`). 6. F3 indicadores.

## 5. Las 36 decisiones provisionales de `notes/questions.md` **[recomendación para el autor: confirmar o editar antes de la sesión]**

Criterio general: se aceptan las decisiones conservadoras que no cambian los IDF de salida de la 1.1.0; se cambian las que contradicen la base científica de la v03 o las decisiones del autor del bloque F. "Aceptar" significa: Copilot mueve la entrada a `notes/decisions.md` tal cual. "Cambiar" lleva la instrucción concreta.

| # | Propuesta | Decisión provisional del implementador | Veredicto | Instrucción |
|---|---|---|---|---|
| 1 | E1 | Medias móviles de los primeros días con el año repetido (los primeros días toman los últimos del archivo, como EnergyPlus para ASHRAE 55) | Aceptar | Coherente con el Engineering Reference §19.1 (medias "calculated directly from the weather file"). Documentar que para CEN 15251 EnergyPlus 25.1 arranca sin dividir por 1 − α⁷ (hallazgo de E1) y que `compute_setpoints` lo reproduce. |
| 2 | E2 | Corrección metabólica comprobada con la relación exacta del EMS (factor = 1 − 0.067·PMV del paso anterior), con `calculation_tolerance` | Aceptar | Es lo correcto: la banda 5.5–6.1 % es el resultado, no la regla. |
| 3 | A3 | Una clave del catálogo sólo rellena el coeficiente al que se pasa | **Cambiar** | Una clave debe rellenar los dos lados cuando el otro argumento no se da explícitamente (el catálogo es por pares `cooling/heating`; pasar `gbt50785_cold_general` sólo en refrigeración y dejar −0.293 en calefacción mezcla fuentes). Si se da número en el otro, el número manda. |
| 4 | A3 | Con `'pmv_sign'`, cada consigna se invierte con el λ de su lado | Aceptar | Correcto: la consigna de refrigeración es un aPMV > 0 (λ_warm) y la de calefacción un aPMV < 0 (λ_cool). |
| 5 | B1 | El código EMS de la métrica sólo en los IDF cuyas zonas usan una métrica distinta de `'pmot'` | Aceptar | Mantiene los IDF de la 1.1.0. |
| 6 | B1 | `Tout_metric` en todos los programas donde el CUSTOM usa la temperatura exterior (SetComfTemp, SetAST_CS99_0, CountHours, SetVST) | Aceptar | Es más completo que la v03 (que olvidaba SetVST). |
| 7 | B1 | Los programas empiezan con los valores del EPW el primer día del primer RunPeriod (PMOT de EnergyPlus si no hay EPW) | Aceptar | Conforme a D3. |
| 8 | B1 | `T0` de `te_ref_nl` antes de que acabe la primera hora del día: la temperatura exterior del paso | **Cambiar** (H2) | Van der Linden define `Ti` como la media de la máxima y la mínima del día completo; el valor parcial hace derivar `Te,ref` dentro del día. Con EPW: `T0` diario desde el EPW (`Schedule:File` leído por un sensor `Schedule Value`); sin EPW: el (máx+mín)/2 del día anterior y aviso. Hasta H2, documentar la deriva. |
| 9 | B1 | Argumentos de la métrica en `modify_accis`: `None` por defecto, conservando los de cada zona | Aceptar | — |
| 10 | B5 | Suelo y techo en un programa por zona tras SetAST, que redondea de nuevo | Aceptar | Mejor que las líneas en los subprogramas compartidos. |
| 11 | B5 | Suelo/techo en `modify_accis`: `None` por defecto | Aceptar | — |
| 12 | B5 | Salidas de `report_hours_below` con todos los `output_type` salvo `'custom'`, también con consignas PMV, `p`/`m` en los nombres | Aceptar | — |
| 13 | B5 | Suelo por encima de la consigna de refrigeración (o techo bajo la de calefacción): se aplica tal cual, documentado | **Cambiar** | Emitir `ValueError` al construir el modelo si `floor >= ceiling`, y un aviso en el log si el suelo supera `ACSTaul` o el techo baja de `AHSTall` (consignas cruzadas en EnergyPlus producen avisos y resultados sin sentido). |
| 14 | C1 | Tipos de parámetros de las entradas del PMV: sólo `'apmv setpoints'` y `'epmv setpoints'` | Aceptar | Los modelos del ACCIS controlan temperatura; clo/met no son parámetros suyos. |
| 15 | C1 | `activity_level` en W/persona con aviso fuera de 82.8–417.6 | Aceptar | 1.0–4 met × 58.2 W/m² × 1.8 m² (ISO 7730:2025 §4: 0.8–4 met → el límite inferior estricto sería 83.8 W/persona con 0.8 met; aceptar 82.8 como aproximación documentada o corregir a 0.8·58.2·1.8 = 83.8). |
| 16 | C1 | Métrica exterior del CUSTOM como parámetro: códigos de las métricas, días redondeados, EPW de `modify_accis` conservado | Aceptar | — |
| 17 | C1 | Planes con suelo ≥ techo excluidos | Aceptar | Coherente con el nº 13. |
| 18 | D1 | Periodos cálido y frío de los indicadores: por encima y por debajo del rango, no por estación | Aceptar | Es la definición literal del Anexo D (Σ para Θo > upper y Σ para Θo < lower). |
| 19 | D1 | `Table(long_term_indicators=True)` da los métodos A y B en un atributo nuevo, una fila por simulación | Aceptar | — |
| 20 | D1 | Un PMV igual al límite superior está dentro del rango; `deviation_check` usa los porcentajes de la Tabla E.1 | Aceptar | El TR escribe `PMV_limit,lower ≤ PMV < PMV_limit,upper` para `wf = 0` (límite superior excluido) — **cambiar** a `<` en el límite superior para seguir el texto literal; porcentajes: correcto (las horas de la Tabla E.1 no cuadran, como detectó el implementador). |
| 21 | B2 | Métrica exterior por régimen: no disponible (`ValueError` salvo `None`) | Aceptar por ahora | Véase la tarea bloqueada B2 en §6. |
| 22 | B2 | Un programa por zona que escribe las entradas del CUSTOM antes de SetAppLimits, sin `else` | Aceptar | — |
| 23 | B2 | Significado de las condiciones: estación de SetAST_Master, HVAC de ApplyAST (modo mixto), métricas como los límites de aplicabilidad (`<`, `>`, `<=` dentro) | Aceptar | — |
| 24 | B2 | Los mismos regímenes en todas las zonas del ComfStand 99; los ocho coeficientes como parámetros | Aceptar | Regímenes por zona: tarea P2 futura si hace falta. |
| 25 | B3 | `load_comfort_standards` registra por defecto | Aceptar | — |
| 26 | B3 | ComfMod 2 sólo con las categorías 80 y 90; la métrica a través de las entradas de la zona | Aceptar con nota | Documentar que ComfMod 2 (ISO 7730 fuera de aplicabilidad) con categorías I–IV de un YAML no está definido. |
| 27 | B3 | Un régimen `'always'` por definición | Aceptar por ahora | Véase la tarea bloqueada B3 en §6. |
| 28 | B3 | YAML de Qatar con las claves que faltan vacías, rechazado al cargar | **Cambiar** | Completar el YAML con los datos de §6 (tarea B3-Qatar) y que cargue. |
| 29 | B4 | Consignas estáticas de JPN Aqilah 2025 literales (20/28), configurables sólo vía YAML | **Cambiar** | Añadir los argumentos `static_heating_setpoint` / `static_cooling_setpoint` (véase §6, B4). |
| 30 | B4 | Media móvil de JPN Aqilah 2025 = RMOT de EnergyPlus (como INT EN16798) | Aceptar | Aqilah usa α = 0.8 iniciada una semana antes (ec. 7); el RMOT de EnergyPlus es α = 0.8 truncado a 7 días (Eng. Ref. 19.82): misma definición a efectos prácticos. Documentarlo en el docstring del ComfStand 23. |
| 31 | C2 | Método C no contado | Aceptar por ahora | Véase §6, C2. |
| 32 | C2 | Contadores EMS bajo petición (`False` por defecto), límites de D1, restricción acotada al periodo simulado | Aceptar | — |
| 33 | E4 | `morph_epws(engine='java'|'pyfwg')`, Java por defecto; sólo la herramienta global; TMY como rutas EPW | Aceptar | — |
| 34 | A4 | Sólo aire acondicionado total, consignas en todos los pasos, rango 10–30 °C | Aceptar con nota | El rango 10–30 °C coincide con el de validez del PMV (ISO 7730:2025 §4: ta 10–30 °C); en modo mixto queda como tarea P2. |
| 35 | A6 | Vía (b) con tabla por HR; (a) y *cooling effect* esperan al autor | **Cambiar** | Sustituir por el plan de convergencia A6 → F1 de §4.6; la vía (a) en Erl se descarta (el autor eligió la API en el bloque F); el *cooling effect* se pospone a F3. |
| 36 | D2 (completado) | Nombres en `Table` de las salidas opcionales; sin valores de bloque/edificio para régimen y métrica | Aceptar | — |

## 6. Las 8 tareas bloqueadas de `TODO.md` y cómo desbloquearlas **[recomendación para el autor]**

1. **B2 — métrica exterior por régimen.** Decisión: las **condiciones** de todos los regímenes se evalúan con la métrica de la zona (`CustAST_metric` de la zona), y el régimen seleccionado puede fijar **su propia métrica** para calcular `ComfTemp` (`outdoor_metric`, `alpha`, `days` propios; si son `None`, los de la zona). Implementación: `SetOutdoorMetric` calcula todas las métricas distintas que aparecen en los regímenes de la zona (una variable `Tout_metric_<k>` por métrica) y `SelectCustomRegime_<zone>` copia la del régimen elegido en `Tout_metric`. Prioridad P2.
2. **B4 — argumentos para las consignas estáticas de JPN Aqilah 2025.** Decisión: sí, argumentos nuevos `static_heating_setpoint` y `static_cooling_setpoint` (por defecto 20.0 y 28.0, claves EMS `StaticAHST`/`StaticACST`), en `AddAccis`, `modify_accis` y `zone_arguments`, válidos para **todos** los ComfStand con *comfort mode* 1 cuya norma no fije consignas estáticas propias (ahora mismo sólo el 23; documentar que los demás los ignoran). Parámetros `StaticHeatingSetpoint`/`StaticCoolingSetpoint` en el paramétrico. P2.
3. **B3 — datos del modelo de Qatar.** Decisión (datos de Indraganti & Boussaa 2018 ya verificados en v03 y elecciones del autor donde el artículo calla): `outdoor_metric: rmot_alpha`, `alpha: 0.8` (el artículo usa una media móvil exterior sin dar α; se adopta la de EN 16798-1 y se anota en `evidence`); `comfort_temperature: {slope: 0.049, intercept: 22.5}`; `applicability: {metric_min: 10.0, metric_max: 40.0}` (rango de Tr del estudio: media 30.7 °C, SD 6.4 → ±1.5 SD ≈ 21–40 °C; se abre a 10 °C por abajo para cubrir el invierno de oficinas con HVAC, anotado como elección); `categories: {90: ±2.5, 80: ±3.5}` (bandas de ASHRAE 55, como hace el propio artículo al comparar; anotado como "no propias"); `comfort_modes: [0, 1, 2, 3]`; `static_setpoints: {heating: 20.0, cooling: 25.5}` (EN 16798-1 Tabla B.2 oficinas cat. II); `evidence: {N: 3742, R2: 0.015, SE: 0.007, p: '<0.001', Tr_mean: 30.7, Tr_sd: 6.4, mode: HVAC, bands: 'ASHRAE 55, not own'}`. El YAML debe cargar y servir de segundo ejemplo. P2.
4. **B3 — varios regímenes en un YAML.** Decisión: clave `regimes:` (lista) con el mismo esquema que `CustomRegime` de B2 (`slope`, `intercept`, offsets, límites, `condition`, `outdoor_metric` opcional); `comfort_temperature` escalar equivale a un único régimen `'always'`. Depende de la tarea 1. P2.
5. **C2 — Método C como objetivo.** Decisión: sólo para modelos con consignas basadas en el PMV (`pmv_index`), con los límites `pmv_heating_setpoint`/`pmv_cooling_setpoint` sin tolerancia y el PMV de la zona que ya mide el EMS; `wf = PPD(PMV)/PPD(PMV_limit)` con la fórmula (5) de ISO 7730:2025 en Erl (`@Exp`); contador `PpdWeightedHours_<zone>`. Para los modelos de temperatura del ACCIS, Método C no aplica (no hay PMV): `ValueError` documentado. P2.
6. **C2 y D1 — CIBSE TM52/TM59.** Siguen sin texto: permanece bloqueado. **[pendiente]**
7. **E4 — cuaderno y test con el jar del Future Weather Generator.** Pendiente de que el autor coloque el jar y fije `ACCIM_FWG_JAR` (y la versión de Java que exige). Además, resolver la discrepancia de la línea de comandos (8 argumentos del motor Java de accim frente a 12 de pyfwg para la versión 3): adoptar la de pyfwg como referencia. **[pendiente del autor]**
8. **A6 — *cooling effect* y vía Erl.** Decisión: vía Erl descartada; *cooling effect* pospuesto a F3 (indicador, no consigna). Lo que sustituye a esta tarea es el plan §4.6.

Fuera de esa lista pero bloqueada "pendiente del autor": **A5 — clo en función de la temperatura exterior** (`callable(rmot) -> clo`). Decisión: implementar como `Schedule:File` generado desde el EPW con `accim.sim.preview.outdoor_metrics` (E1 ya existe), función `clothing_insulation=callable`; la versión Erl por tramos no se hace. P2.

## 7. Tareas para la siguiente sesión de Copilot (orden recomendado) y prompt único

Convención: las tareas G1–G5 son correcciones de la revisión (prioridad P1, antes de la 1.2.0); H1–H6, mejoras y decisiones ya tomadas en §5–§6 (P2); F1–F3, el bloque F (sus prompts están en `notes/PROMPTS_COPILOT_bloque_F_v02.md` y no se repiten aquí). Cada tarea: un commit, push, CHANGELOG/DEVLOG/TODO/CAMBIOS, tests, ambos backends si cambia el EMS.

| Id | Tarea | Hallazgos que cierra | Prioridad |
|---|---|---|---|
| G1 | Ganchos ATHB/SET coherentes con los contadores y salidas del ACCIS (opción (a) de A4/A6-1: el gancho actualiza `ACST`, `AHST`, `ACSTnoTol`, `AHSTnoTol` y redondeadas, y los programas de recuento se ejecutan después; si no es viable, opción (b) con contadores propios) + documentación | A4/A6-1 | P1 |
| G2 | `compute_setpoints`/`energyplus_running_means`: reproducir la rama de enero de EnergyPlus; test con arranque 8 de enero; docstrings; nota en la comprobación 4 de E2 | E1-1, E2 doc | P1 |
| G3 | A6: reescritura de la justificación; `method='table'|'bisection'` con calentamiento del JIT; sensores/salidas MAT, MRT, HR; `SET_<zone>` con bisección; auxiliar `set_of_results`; `position` por defecto `'sitting'` si met ≤ 1.2 (o sin defecto); documentación de la insensibilidad a v < 0.1 m/s y del coste JIT | A6-1…A6-4 | P1 |
| G4 | B4: `rmot_alpha` desde el EPW cuando `AddAccis` recibe EPW, RMOT si no (aviso); test 23 vs 101; argumentos `static_heating_setpoint`/`static_cooling_setpoint` (§6.2) | B4-1, B4-2 | P1 |
| G5 | Saneamiento: 4 tests con `importorskip('besos')`; `run_ep(processes=0)`; A3 `adaptive_coefficients=<clave>` + aviso; validación de signos con `pmv_sign`; B5 acotar también `noTol` y techo exacto; docstring SetVST; B1 `ValueError` sin mes y formateador Erl común; B3 Qatar completo (§6.3), orden de categorías, aviso de signos; E4 `fwg_add_uhi=False`, aviso `ensemble=0`, limpieza en `ValueError`; docs de §3.5 | A3-1, A3-2, B5-1…3, B1-2, B3-1…3, E4-1…3, 3.4, 3.5 | P1 |
| H1 | Renombrado B5: `heating_setpoint_minimum`/`cooling_setpoint_maximum` (claves `AHSTmin`/`ACSTmax`, parámetros `HeatingSetpointMinimum`/`CoolingSetpointMaximum`) con alias deprecados | §4.5 | P1 |
| H2 | B1 `te_ref_nl`: `T0` diario desde el EPW (`Schedule:File`) y documentación de la alternativa | B1-1 | P2 |
| H3 | C2: `long_term_range=('en16798', categoría)` opcional; método C para modelos `pmv_index` (§6.5); documentar diferencia `Table` horario vs contadores EMS y arreglar el TODO P1 de `Table` con `timestep` | C2-1, D1-1 | P2 |
| H4 | A4: registro de saturación y aviso; `output_frequencies=None` → las del modelo; avisos de rango de met/v; documentación W/persona ↔ met y velocidad relativa; test científico acotado | A4-1…A4-3, 3.4 | P2 |
| H5 | B2: métrica por régimen (§6.1); documentar la alternancia con `hvac_on/off` y `CustomRegime` promediado; B3 varios regímenes en YAML (§6.4) | B2-1, B2-2, §6.1, §6.4 | P2 |
| H6 | A5: `clothing_insulation=callable` → `Schedule:File` desde `outdoor_metrics` | §6 (A5) | P2 |
| F1–F3 | Bloque F (SET causal de Sun 2026 como ComfStand 24 sobre `SetSetpointHook(method='bisection')`, limitador de deriva, indicadores) — tras G3 y H1; tarea E-F1 primero | §4 | P1 (paper) |

### 7.1 Prompt único para la sesión (pegar tal cual; las decisiones de §5–§6 son vinculantes)

```
You are working autonomously on accim, branch v1.2.0 (D:\Python\accim), after `git pull` (HEAD d6dbae16 or later). Read first: notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md (this review: section 3 findings, section 5 decisions on the 36 provisional questions, section 6 decisions on the blocked tasks, section 7 task list), then notes/COPILOT_BRIEF_v1.2.0_v01.md (rules D1-D12), notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md sections 11-12 (formulas and EnergyPlus names), notes/INFORME_SESION_v1.2.0_2026-11-10.md, notes/questions.md, TODO.md, and for the block F tasks notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md and notes/PROMPTS_COPILOT_bloque_F_v02.md. The structured review results are in notes/attachments/revision_v1.2.0_hallazgos.json.

Step 0: move the 36 entries of notes/questions.md to notes/decisions.md with the author's verdicts of v04 section 5 (accept as is, or with the stated change), and update TODO.md with the decisions of v04 section 6 (unblock the tasks that now have a decision, keep CIBSE TM52/TM59 and the pyfwg jar blocked). Commit and push.

Then implement, in this order, one commit and push each: G1, G2, G3, G4, G5, H1, then E-F1 (the SET comparison task of the block F proposal, section 3), F1, F2, F3, then H2, H3, H4, H5, H6. Each task is defined in v04 section 7 with the findings it closes (section 3) and the decisions it applies (sections 5-6); the block F tasks use the prompts of notes/PROMPTS_COPILOT_bloque_F_v02.md with the names that exist in the code after H1 (heating_setpoint_minimum / cooling_setpoint_maximum).

Definition of done for every task, as in the previous session: PEP 8, English reST docstrings with citations; eppy, never besos; Erl through accim.sim.ems, never TrendVariable; pytest green for the affected test files (skip, never fail, when besos or an EnergyPlus version is missing); golden master byte-identical unless the task changes outputs on purpose (say so); when EMS code or a hook changes, a sample IDF simulated with both backends (identical setpoints and EMS variables; for the hooks compare the applied setpoints and the new counters); CHANGELOG.md [Unreleased], DEVLOG.md (Context / Changes / Files / Verification), TODO.md, CAMBIOS_CODIGO_v1.2.0.md, docs and GUI when arguments or outputs change; commit message style fix(sim): ... (G1) / feat(sim): ... (F1); push after each commit; partial work committed as wip(...) with a TODO entry.

Rules: never invent a formula, coefficient, EnergyPlus name, Erl function or API method not found in v03 sections 11-12, the code, Energy+.idd or the EnergyPlus documentation in C:\EnergyPlusV25-2-0; a decision that v04 sections 5-6, the brief D1-D12 or the block F section 6 do not cover goes to notes/questions.md with the most conservative option chosen provisionally, and you continue; three failures of a step -> TODO.md entry with the error, move on; never loosen a test, never force-push. When set_tmp or any pythermalcomfort call crashes inside an EnergyPlus callback in your Python version, warm up the function once before run_simulation and retry, then try NUMBA_DISABLE_JIT=1 for the worker process, and record the Python/numba versions and the outcome in DEVLOG.md before falling back to the table method.

At the end write notes/INFORME_SESION_v1.2.0_<date>_2.md with the same sections as the previous report (commits, deviations, TODO entries, provisional decisions, tests and backend comparisons, blocked items with the exact missing information), commit and push it, and stop.
```

---

## 8. Lo que esta revisión no ha podido comprobar **[pendiente]**

- Igualdad EMS vs API a través de `run_ep`/`run_simulations` (tuberías de `multiprocessing` denegadas en el *sandbox*); los tests equivalentes de A4/A6/C2 se repitieron en proceso y pasaron; para B1/B5/B2/A3/B3 se confía en el informe del implementador.
- El *golden master* de las 22 configuraciones de `AddAccis`, la suite completa (1783 tests), la compilación de Sphinx, la GUI y la compilación con Python 3.9.
- El *access violation* de `set_tmp` en Python 3.14 (no disponible aquí); en Python 3.12 / numba 0.68.1 no se reproduce.
- Las afirmaciones de rendimiento (15 s por semana con ATHB; 1 ms por zona y paso; 1.5 s la tabla SET): no medibles con simulaciones concurrentes.
- Los tests y el código del paramétrico (`tests/parametric_and_optimisation`, C1, B2/B3 paramétricos): sólo lectura, sin besos.
- EnergyPlus 25.2 y 26.x con los ganchos (los tests fijan 25.1).
- CIBSE TM52/TM59 y el texto de GB/T 50785-2012: documentos no disponibles.

---

## 9. Archivos de esta versión

- `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (este documento).
- `notes/attachments/revision_v1.2.0_hallazgos.json`: resultados estructurados de los cuatro revisores (veredictos, hallazgos con ubicación/evidencia/corrección, decisiones revisadas, tests ejecutados, no evaluado).
- Inalterados: v03 (base científica), `COPILOT_BRIEF_v1.2.0_v01.md`, `INFORME_SESION_v1.2.0_2026-11-10.md`, bloque F (`PROPUESTA_ADAPTACION_INTERIOR_v03.md`, `PROMPTS_COPILOT_bloque_F_v02.md`, adjuntos `set_band_*`).
