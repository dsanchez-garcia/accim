# Experimentos del paper: entrega preparada

**2026-09-30 — revisión estática, no validación por simulación.** No se han
ejecutado los scripts, muestreadores, discovery, preflight ni EnergyPlus durante
esta preparación. Los originales, resultados y checkpoints se conservan.

## 1. Qué copiar y requisitos

Copiar **esta carpeta completa**, con exactamente estos cinco scripts:

| Experimento | Archivo definitivo | Diseño conservado | Previsión de campaña |
|---|---|---|---:|
| 4.1 | [exp_4_1_parametric_predefined_model.py](exp_4_1_parametric_predefined_model.py) | Predefined, `vrf_mm`; ComfStand 1/2/3/14/16, CAT 1/2/3/80/90, ComfMod 0/3, HVACmode 0/2; full set filtrado, tres EPW | 132* |
| 4.2 | [exp_4_2_parametric_custom_model.py](exp_4_2_parametric_custom_model.py) | Custom, `vrf_ac`; m (0,0.7), n (5,22.5), offset (1,5), aul (22,40); LHS 100, tres EPW | 300 |
| 4.3 | [exp_4_3_parametric_apmv.py](exp_4_3_parametric_apmv.py) | aPMV; lambda cooling 0/0.1/0.3/0.5, PMV 0.2/0.5/0.7, lambda heating −0.293; full set, tres EPW | 36 |
| 4.4 | [exp_4_4_optimisation_custom_model.py](exp_4_4_optimisation_custom_model.py) | Custom, `vrf_ac`; rangos de 4.2; NSGA-II, población 20, presupuesto 200 por EPW; presente y SSP585 2080 | 400 |
| 4.5 | [exp_4_5_optimisation_apmv.py](exp_4_5_optimisation_apmv.py) | aPMV; cooling (0,1), heating (−1,0), PMV (0.2,0.9); mismo NSGA-II y dos EPW que 4.4 | 400 |

**Total previsto: 1.268 simulaciones de campaña, pendiente de comprobar.**
Discovery, warmup/sizing, reintentos y reinicios no forman parte de esa previsión.

**\* Discrepancia detectada:** el catálogo actual admite para esos cinco
estándares 12+8+8+4+8 = **40 combinaciones**, 120 casos con tres EPW: CS14 no admite
ComfMod=0. Es una intersección estática de listas, no un muestreo ejecutado.
Se mantiene 132 como previsión del encargo; el plan real debe revisarse y la
campaña exige `--count-note` si difiere. No se inventan combinaciones para alcanzar
132. Si se confirman 120, el total pasa a 1.256 y habrá que corregir el manuscrito.

**Los cinco scripts sólo contienen configuración y llamadas a accim.** No hay
funciones auxiliares, clases, EMS incrustado ni imports entre experimentos.
La rama `feat/comfort-metrics-experiment-api` incorpora estas APIs públicas:

- `SimulationBase.add_comfort_metrics(...)`, heredado por ambas clases de simulación.
- `accim.sim.add_comfort_metrics(...)`, constructor independiente de reporting EMS.
- `accim.parametric_and_optimisation.objectives.checked_sum_results(...)`, reductor importable por workers.
- `accim.parametric_and_optimisation.run_paper_experiment(...)`, gestión de los cinco flujos.

Ya no se necesita `article_objectives.py` ni que un experimento importe 4.4.
Las métricas nuevas se solicitan explícitamente después de preparar el control;
no cambian automáticamente las consignas ni objetivos de otras campañas.

Crear `inputs/` junto a los scripts y copiar allí, sin modificar los originales:

- `ALJARAFE CENTER_onlyGeometry.idf` (privado; no redistribuir con el paper).
- `Seville_Present.epw`, `Seville_ssp245_2050.epw`, `Seville_ssp585_2080.epw`.

Requisitos: Python ≥3.9 en un entorno compatible con BESOS; `accim` de la
**rama `feat/comfort-metrics-experiment-api`**, BESOS, eppy, Platypus (`platypus-opt`),
NumPy, pandas, SciPy, matplotlib, seaborn, unidecode y **openpyxl** para las
exportaciones Excel de accim (ahora declarado como dependencia). Instalar accim desde una copia de esa rama con
sus dependencias; no asumir que cualquier distribución «≥0.8.0» incorpora los
arreglos recientes. Registrar el entorno instalado antes de la campaña.

EnergyPlus y su IDD deben corresponder a la versión del IDF y estar configurados
para BESOS. La copia de referencia inspeccionada declara 9.4. Si se necesita
transición, hacerla sobre otra copia y usar otra campaña. La API real admite
`EnergyPlus_version=None` para detectar la versión; **no admite `'auto'`**.

## 2. Rutas y operaciones separadas

Editar la sección inicial de cada script o usar `--idf`, `--epw-dir`,
`--results-root`, `--campaign`, `--result`. **Las rutas relativas se interpretan
desde la carpeta de los scripts**, no desde el directorio de lanzamiento.
Los inputs se copian a un directorio de trabajo privado; quitar acentos y
transformar el IDF sólo afecta a esa copia. Los EPW se pasan a BESOS como nombres
simples desde ese directorio: evita rutas Windows dentro de IDs y nombres de logs.

| Acción | Efecto | ¿Puede simular? |
|---|---|---|
| Sin argumentos / `help` | Ayuda; ninguna campaña | No |
| `prepare` | Copias, transformación, auditoría y vista previa del plan | No |
| `discover --simulate` | Prueba reducida explícita, RDD/MDD y contrato CSV | **Sí, sólo en el otro PC** |
| `new --simulate` | Campaña nueva, carpeta que no exista | **Sí** |
| `resume --simulate` | Sólo campaña propia compatible e incompleta | **Sí** |
| `load --result ...` | Tablas/figuras desde un consolidado concreto | **Nunca** |

`load` no necesita cargar el IDF ni disponer de los EPW: utiliza una instancia
sin edificios y los métodos `load_outputs_parametric/optimisation`. Rechaza
checkpoints como si fueran resultados; jamás usa run/resume para postprocesar.
Sólo abrir pickles de procedencia confiable.

Ejemplos para **el PC de destino**, invocando la ruta al script si se está en otro
directorio (sustituir los nombres entre `<...>` por archivos elegidos):

```powershell
python .\exp_4_2_parametric_custom_model.py prepare
python .\exp_4_2_parametric_custom_model.py load --result 'archivo_consolidado.pkl'
python .\exp_4_2_parametric_custom_model.py load --result 'archivo_consolidado.pkl' --hourly --climate Present
```

Después de las verificaciones de la sección 6, y **no durante esta preparación**:

```powershell
python .\exp_4_4_optimisation_custom_model.py discover --simulate
python .\exp_4_4_optimisation_custom_model.py new --simulate --campaign paper-v1 --approval '<discovery_approval.json>' --area-note '<revision de superficie>' --schedule-note '<revision de horarios>' --ems-note '<validacion numerica realizada>'
```

Para reanudar, sustituir `new` por `resume`, conservando campaña y configuración.
4.1 exige además `--count-note '<recuento real y decision>'` si el plan no da 132.
Por defecto se usan dos workers y lotes de diez; ajustar `--workers` y
`--batch-size` después de probar Windows multiprocessing en un área de pruebas.
No hay un preflight que simule implícitamente.

En Spyder se puede editar `ARGUMENTS` con una lista explícita; en Jupyter importar
`EXPERIMENT` y `SETTINGS` del archivo y llamar a
`run_paper_experiment(EXPERIMENT, SETTINGS, argv=[...])` de accim.
No pegar todo en una celda ni heredar los argumentos
del kernel. Para campañas paralelas es preferible lanzar el archivo guardado
en un proceso Python independiente. Todos tienen main guard y `freeze_support()`;
el reductor se resuelve por ruta de módulo, sin lambdas/closures en los workers.

## 3. Resultados, planes y traslado entre PCs

Cada experimento separa `checks/`, `campaigns/<nombre>/` y `postprocess/` dentro
de `results/exp_4_N/`. Nunca apuntar una campaña nueva a un archivo histórico.
Se conservan los consolidados nativos y una copia `results_raw_<fecha>.pkl` con
metadatos y rutas relativas; la fecha se genera al escribir, no se fija al cargar.
Cada postproceso escribe en otra carpeta y no sobrescribe el consolidado elegido.

- **LHS:** una campaña nueva guarda `plan.pkl` y `plan.csv`. Resume no vuelve a
  muestrear: recarga el plan exacto, lo compara con `checkpoint.input_plan` y usa
  `resume_plan_source='auto'`, presente en esta fuente. La semilla no sustituye
  al plan. El `preview_plan` de prepare es sólo una vista previa.
- **Checkpoint paramétrico:** se comprueban todos los lotes y las firmas
  completadas. Un checkpoint que marca tareas completas pero ha perdido los
  lotes se rechaza, evitando saltarse simulaciones y perder sus resultados.
- **Optimización:** resume reutiliza casos IDF×EPW **terminados**, no la población,
  generación ni estado RNG interrumpidos. Un caso incompleto vuelve a empezar;
  no se garantiza la misma trayectoria aleatoria. Ampliar el presupuesto es
  otra configuración, no continuar la población antigua.
- Los hashes nativos no cubren todo el método científico. `campaign.json` añade
  hashes de inputs/fuentes, parámetros, objetivos, unidades y configuración.
  Cambiar modelo, outputs o fuente obliga a otra campaña. Los checkpoints
  históricos sin ese manifiesto son deliberadamente **load-only**.
- Para trasladar una campaña propia, copiar **todo su directorio**, incluidos
  `plan.pkl`, manifiesto, lotes, checkpoints, `active_checkpoint.txt`, `recovery/`
  y carpetas `accim*` (también las que llevan PID). Resume migra rutas en una
  copia del checkpoint/lotes, sin modificar el checkpoint de origen. Mantener
  los mismos nombres IDF/EPW; no se reescriben sus identidades a ciegas.
- Para horarios históricos con rutas absolutas, indicar juntos `--old-root`
  (prefijo antiguo exacto) y `--new-root` (ubicación trasladada). Se exige una
  correspondencia explícita y que los archivos existan; no se busca por el
  primer nombre coincidente. Los backups IDF de metadatos no se cargan para
  postprocesar: el denominador se especifica expresamente.
- Para rutas históricas **relativas al antiguo directorio de trabajo**, indicar
  `--legacy-path-base` antes del mapeo old/new. En 4.2 los valores pueden empezar
  por `results_exp_4_2_parametric_custom/BESOS_Output/...`: su base es la carpeta
  de trabajo anterior, no otra vez la carpeta del consolidado.
- La integración en accim cambia el manifiesto a `paper-prepared-v2` y los
  nombres de outputs EMS a `ACCIM_Paper ..._<sufijo>`, obtenidos de metadatos.
  No reanudar una campaña v1 como si fuera v2: conservarla para carga y crear
  otra campaña para la nueva implementación.

**4.2 archivado:** se revisó también
`ondrive_backup/Paper param optim/param - accim custom models/exp_4_2_parametric_custom_model_v3_w-figs.py`.
Su sidecar declara **300/300**, y existe el consolidado
`outputs_param_simulation_20260716_142703.pkl`. Seleccionarlo explícitamente con
`load`, sin resume. No se hereda de esa versión ni `vrf_mm` ni la recarga
incondicional del pickle fechado. No se ha deserializado el checkpoint aquí.
**La cabecera del CSV horario archivado inspeccionado sólo contiene temperatura
operativa y meters, no PMOT ni consignas.** Sus figuras energéticas pueden
prepararse con el consolidado; la regresión custom no puede obtenerse de ese CSV.
El script falla claramente si faltan series; no las inventa ni vuelve a simular.

## 4. Métricas y normalización

EER=4.42 y COP=4.95 se conservan en todos los VRF. Para aPMV se añade VRF/Fanger
una sola vez, se fijan signos iniciales cooling positivo/heating negativo y se
evita repetir la inyección en el constructor. Se exige una zona, un People y
un único target resuelto; una variante multizona requiere otro diseño.

**4.4, implementado en `accim.sim.comfort_metrics`:**
`D = sum(ocupado × max(To − superior, inferior − To, 0) × Δt_h)`.
`R = clamp(RMOT,10,30)`, neutral `0.33 R + 18.8`, superior `neutral+3`, inferior
`neutral−4` (Cat II según ACCIM). La extensión horizontal fuera de 10–30 °C es
una política explícita, no una afirmación de aplicabilidad ilimitada de EN.
No intervienen m, n, offset ni aul optimizados. Se instala después de ACCIS sobre
el **mismo IDF que evalúa el optimizador**. Sensores: To con clave de zona;
RMOT y `People Occupant Count` con clave People/Space resuelta, no zona inventada.
Calling point `EndOfZoneTimestepBeforeZoneReporting`; incremento reiniciado cada
timestep, `Summed`, `ZoneTimestep`, `C-hr`, reader clave `EMS`, suma de reportes
horarios sin multiplicar por Δt otra vez. También se reporta D en campañas nuevas
4.1/4.2. No es intercambiable con los helpers anteriores (±3, sin ocupación o
calling point distinto); cargar optimizaciones antiguas exige
`--legacy-metric-note` y no certifica equivalencia.

**Ocupación:** D se evalúa cuando el número instantáneo de ocupantes es >0, sin
ponderar por personas. La referencia IDF inspeccionada usa `On 24/7`; por tanto
esa puerta puede permanecer abierta todo el año. No se inventa el horario
9–19 laborables del manuscrito: revisar/corregir una copia del input, repetir
checks y documentar la decisión con `--schedule-note`. El VRF conserva también
su disponibilidad por defecto hasta esa revisión.

**4.5:** el contador nativo `Discomfortable Total Hours_<sufijo>` se selecciona
sólo si hay **exactamente uno**, `Summed/ZoneTimestep` con unidades h. Es la suma
de incrementos en horas, **no grado-horas ni necesariamente horas ocupadas**;
su programa actual se llama antes del predictor. Su referencia cambia con el
PMV setpoint optimizado. Se mantiene ese objetivo y se preparan diagnósticos
independientes (media ocupada de |Fanger PMV| y horas ocupadas con |PMV|>0.5).
En 4.3 se reportan también esos diagnósticos anuales. Fijar PMV o sustituir D en
4.5 sería **otro experimento**. Lambda cooling=0 en 4.3 no equivale a PMV puro
todo el año: heating sigue en −0.293.

**Electricidad:** J / 3.600.000 / **312 m²**. Se audita `mode='air-conditioned'`
y se compara con el denominador del paper (umbral 1%); para publicar se usa
`mode='custom', custom_area=312`. El helper geométrico suma superficies de suelo,
no necesariamente `Zone.Floor_Area` ni multiplicadores. Hay antecedentes de
332.49 m² con `mode='all'`, frente a 312.3717 m² declarados en la zona inspeccionada.
No asumir que son superficies equivalentes: registrar `--area-note`.

La API renombra `Electricity:HVAC` a `Electricity:HVAC_kWh/m2` o cambia `[J]` a
`[kWh/m2]`. Tablas, estadísticas, ahorros y figuras usan la columna resuelta por
nombres/metadatos, con fallo ante ausencia/ambigüedad. Sólo se normaliza la
columna energética: la heurística global también podría tocar parámetros con
“Cooling/Heating”. El confort conserva sus unidades. Los pickles de postproceso
guardan unidad y superficie; si un CSV antiguo ya está normalizado y no declara
área, se exige `--legacy-area` o se recomienda cargar el consolidado **crudo**.
Un cambio conocido de denominador sólo reescala por área antigua/312, no vuelve
a convertir J→kWh. Las funciones de plotting reciben nombres reales y
`normalize_per_m2=False` con el estado normalizado restaurado.

## 5. Figuras y conservación de archivos

Se preparan distribuciones/heatmaps y ahorros frente a controles compatibles
(4.1/4.3), scatters con tendencias, ECDF y violines (4.2), frentes, coordenadas
paralelas y TOPSIS/knee **por clima** (4.4/4.5). En 4.1 el heatmap separa
HVACmode y ComfMod; CS14 sin baseline queda explícitamente sin ahorro calculado.
Se recalcula no-dominancia por EPW antes de elegir compromisos. Knee en esta API
es distancia normalizada a utopía, no una búsqueda geométrica de curvatura.
El Pareto nativo está especializado en Heating/Cooling y algunos plots de
compromiso escalan ambos ejes como energía: se usan aquí figuras explícitas
para no convertir grados-hora/horas a kWh. La resolución flexible de nombres
del plotting no es uniforme ni reemplaza las selecciones pandas.
Para 4.3 se usa `lambda_c [-]` como alias de eje: la heurística de plotting no
debe etiquetar el coeficiente de refrigeración como kWh/m².

`--hourly` lee tres filas del clima elegido (no dominadas en optimización);
`--hourly-indices` selecciona etiquetas `result_row` y `--hourly-all` procesa
todas las filas de ese clima. Usa `read_csv(usecols=...)`, **un archivo por vez**,
comprueba claves/frecuencia/unidades/NaN y guarda columnas y selección exactas.
Las regresiones custom usan **PMOT**, sólo dentro de aplicabilidad 10..aul;
EN usa **RMOT**. Se distinguen consignas `_No Tolerance` de consignas aplicadas.
Las fechas se leen de cada registro: `24:00` pasa al día siguiente; se comprueban
continuidad, 8760/8784 y bisiestos. El año 2001/2000 sólo sirve para representación,
no identifica el año meteorológico; `--calendar-year` debe ser compatible.
No se usa el calendario fijo 2024 ni la expansión horaria que ignora las fechas.

Se conservan todas las carpetas y `.csv/.err/.idf/.rdd/.mdd/.edd/.end` cuando
existan. Las pruebas de discovery no se limpian. Mantener espacio suficiente:
si en otra configuración se elige sólo no dominados, desaparecerán los horarios
de dominados aunque sus escalares estén en la tabla; no será posible reconstruir
los diagnósticos completos ni todos los candidatos históricos.

## 6. Pendiente en el PC de simulaciones

1. `prepare`: comprobar versión IDD, una zona/target, VRF/Fanger sin duplicados,
   schedules, superficie y el plan filtrado. Confirmar especialmente 120 vs 132.
2. `discover --simulate` **por experimento**, aislado en `checks/`: revisar RDD/MDD,
   claves reales `EMS`/People y CSV. La prueba usa el primer EPW y un punto
   representativo: **no valida todos los climas, parámetros ni estaciones**.
   Se rechazan Severe/Fatal, falta de cierre correcto, series ausentes y NaN.
3. Validación EMS numérica en copias de prueba, con outputs por timestep y `.err`/
   `.edd` conservados: To, RMOT, ocupación y Δt alineados al calling point. A
   RMOT=20, límites 21.4/28.4 °C: To=30 y Δt=0.25 h deben dar 0.4 C-hr si ocupado;
   To=20 debe dar 0.35; cómodo/no ocupado, cero. Verificar ambos límites y clamps,
   warmup, suma horaria/anual y que cambiar custom no cambia la referencia fija.
4. aPMV: verificar signo de consignas, temporada, ceros/denominadores próximos
   a cero de `1+lambda*PMV`, horas frente a duración anual y diferencias entre
   contador nativo y diagnósticos ocupados. Revisar posible desfase del contador.
5. En otra carpeta de pruebas, comprobar lectores escalares con uno/dos workers,
   una interrupción paramétrica entre lotes y una entre casos de optimización.
   No usar `resume` del archivo histórico 300/300 para esta prueba.
6. Tras revisar esos resultados, usar `new` con aprobación y notas reales.
   Confirmar recuentos efectivos, no sólo filas retenidas o presupuesto NSGA-II;
   comprobar una suma energética y la conversión a 312 m² por separado.
7. Probar `load` en sesión nueva, sin IDF/EPW: tablas/figuras y una selección
   horaria, después también con rutas trasladadas. Revisar por clima TOPSIS/knee
   y el diagnóstico de acumulación de soluciones cerca de PMV=0.9 en 4.5.

### Evidencia de esta entrega

Se consultaron contexto 6, borradores Methods/Case Study `*_con_doi.md`, los cinco
`*_w-figs.py`, variantes `to_be_hold`, la copia posterior de 4.2, código actual
de accim y tests **como texto**. Se analizaron/compilaron los cinco AST en memoria
(gramática Python 3.9; intérprete aislado), sin imports/ejecución de los scripts.
La integración posterior en accim incluye pruebas herméticas de métricas,
idempotencia, colisiones, API, paths y fechas, **preparadas pero no ejecutadas**
en esta fase. También se verifica por AST que ninguno de los cinco scripts
contiene funciones/clases/lambdas ni depende de otro experimento.
Se contrastaron campos EMS y calling point con el IDD 9.4 como texto. El IDE
advierte incompatibilidad local de `pandas-stubs`; no se alteró el entorno.
Quedan pendientes todas las pruebas numéricas y de EnergyPlus enumeradas arriba.
Los borradores deben actualizar sus recuentos, la referencia móvil de 4.5 y las
afirmaciones sobre horarios/reanudación; no se han modificado aquí.
