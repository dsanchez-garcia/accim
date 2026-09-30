# Modulo `accim.parametric_and_optimisation`: descripcion tecnica detallada

> Actualizado el 2026-09-30 frente a la rama `feat/comfort-metrics-experiment-api`.
> Las APIs nuevas son incorporaciones de fuente, todavia no publicadas como release.
> Esta descripcion no implica validacion numerica ni ejecucion de EnergyPlus.

## Que es exactamente el modulo

El subpaquete `accim.parametric_and_optimisation` implementa una capa de experimentacion computacional sobre modelos `IDF` de EnergyPlus, integrando tres niveles:

1. Mutacion parametrica del modelo (parametros ACCIM/APMV que alteran programas EMS y consignas).
2. Evaluacion masiva u optimizacion (BESOS + Platypus + ejecucion EnergyPlus).
3. Postproceso reproducible (agregaciones temporales, normalizacion fisica, sensibilidad, clustering, robustez y figuras).

No es solo un runner de simulaciones: es un framework de diseno de experimentos para edificios, donde la unidad logica es una instancia de simulacion que conserva configuracion, muestras, resultados crudos, resultados agregados y metadatos de trazabilidad.

---

## API publica y contrato de uso

En `accim/parametric_and_optimisation/__init__.py` se exponen las clases operativas principales importadas desde `accim/parametric_and_optimisation/main.py`:

- `ParametricSimulation`
- `OptimisationSimulation`

La clase base de orquestacion es `SimulationBase` (tambien importada ahi), sobre la que se montan especializaciones para experimentacion parametrica y optimizacion.

Conceptualmente:

- `SimulationBase` = estado + utilidades + lifecycle comun.
- `ParametricSimulation` = generacion/evaluacion de diseno muestral.
- `OptimisationSimulation` = busqueda multiobjetivo por algoritmos evolutivos.
- Mixins en `analysis.py` y `plotting.py` = analisis y visualizacion desacoplados del core de ejecucion.

La capa de reporting independiente es optativa: `SimulationBase.add_comfort_metrics`
la incorpora a las dos clases sin cambiar consignas ni sustituir objetivos.
El constructor de bajo nivel tambien se publica como `accim.sim.add_comfort_metrics`.
`objectives.checked_sum_results` ofrece una suma estricta importable por workers.

Separadamente, `run_paper_experiment(spec, settings, argv=None)` es una API de
conveniencia para los cinco flujos del paper, no un reemplazo de las clases
generales. Los scripts de entrega son configuracion y llamadas al paquete; su
zona unica, superficie de 312 m2, presupuestos y requisitos de aprobacion son
decisiones del caso de estudio, no defaults globales del modulo. Contratos y
ejemplos: [guia publica de metricas y flujos](source/comfort_metrics.rst).

---

## Arquitectura interna por archivo (vision funcional)

- `accim/parametric_and_optimisation/main.py`: nucleo de ciclo de vida (setup, outputs, parametros, problema BESOS, sampling, ejecucion, checkpoint, agregacion).
- `accim/parametric_and_optimisation/parameters.py`: factoria de parametros (`accis_parameter`) + wrappers OO para parametros frecuentes.
- `accim/parametric_and_optimisation/params_dicts.py`: diccionarios de mapeo nombre de parametro -> funcion modificadora.
- `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py`: mutadores de EMS ACCIM y filtros de combinaciones no validas.
- `accim/parametric_and_optimisation/funcs_for_besos/param_apmv.py`: mutadores EMS APMV por zona.
- `accim/parametric_and_optimisation/objectives.py`: reductores de salida (`mean`, `sum`, serie temporal y `checked_sum_results` estricto).
- `accim/sim/comfort_metrics.py`: EMS de evaluacion independiente, sin actuadores ni cambios de control.
- `accim/parametric_and_optimisation/paper_experiments.py`: preparacion/campana/reanudacion/carga y postproceso de los cinco flujos del paper.
- `accim/parametric_and_optimisation/patches.py`: parcheo de evaluacion para robustez en optimizacion, logging y limpieza de artefactos.
- `accim/parametric_and_optimisation/file_cleanup.py`: politica `'keep'/'delete'` por extensiones.
- `accim/parametric_and_optimisation/analysis.py`: normalizacion por m2, sensibilidad SALib, clustering, robustez.
- `accim/parametric_and_optimisation/plotting.py`: origen de datos, filtros consistentes y graficas parametricas/Pareto/horarias.
- `accim/parametric_and_optimisation/utils.py`: validadores, filtros declarativos (`apply_data_filter`) y ordenacion de subplots.

---

## Como se representa un parametro (semantica alta -> mutacion baja)

El mecanismo central esta en `accim/parametric_and_optimisation/parameters.py`:

- `accis_parameter(parameter_name, values)` valida que el nombre exista en `all_params`.
- Segun `values`, construye descriptor:
  - continuo/rango (`RangeParameter`)
  - categorico/discreto (`CategoryParameter`)
- enlaza descriptor con una funcion mutadora real del IDF.

La tabla de despacho esta en `accim/parametric_and_optimisation/params_dicts.py`:

- `accim_predef_model_params`
- `accim_custom_model_params`
- `apmv_setpoints_params`
- agregado en `all_params`

Es decir, un parametro abstracto como `CustAST_ASToffset` termina en una operacion concreta sobre lineas EMS (por ejemplo, `Program_Line_4`, `Program_Line_5`) en `param_accis.py`. Esta separacion desacopla diseno experimental de implementacion en EnergyPlus.

---

## Inicializacion del experimento y preparacion del IDF

Durante `SimulationBase.__init__` (en `main.py`) se realiza el setup estructural:

- se registran IDFs, climas EPW, frecuencias y opciones de salida;
- se inyecta la logica ACCIM/APMV segun `parameters_type` (via funciones del ecosistema ACCIM);
- se dejan preparados los contenedores de resultados y metadatos.

En la practica, esta fase transforma modelos genericos en modelos experimentables, habilitando que luego cada evaluacion cambie solo el vector parametrico, no la infraestructura completa.

Los IDFs suministrados se mutan: trabajar sobre copias. En el flujo aPMV,
preparar antes el VRF y los campos Fanger necesarios; la inyeccion de aPMV por
el constructor no equivale a incorporar ese sistema HVAC. Las metricas de
reporting se anaden **despues** de la transformacion y la configuracion de
parametros: una nueva transformacion ACCIS/aPMV podria eliminar sus globals o
anadir calling managers incompatibles.

---

## Gestion de salidas: descubrimiento, seleccion y aplicacion

El modulo contiene una tuberia explicita de outputs:

1. `discover_available_outputs` (inventario de variables/meters disponibles),
2. `select_outputs` (filtro de que se quiere medir),
3. `clear_outputs` (evitar residuos o duplicados),
4. `apply_outputs_preflight` (aplicar configuracion final al IDF).

Ademas existen helpers para inyectar `Output:Variable` y `Output:Meter` directamente (`set_output_variables_to_idf`, `set_output_meters_to_idf`).

La inyeccion de requests y el registro de readers son operaciones distintas:
`set_output_readers` reemplaza la lista de lectores BESOS sin modificar el IDF.
`mode='append'` preserva los requests existentes, incluidos los de aPMV;
`mode='replace'` los elimina para el tipo/scope seleccionado. Elegirlo de forma
explicita, no limpiar a ciegas antes de una figura o de un objetivo.

**Discovery puede simular**, incluso con `prefer='rdd_mdd'` si debe regenerar
diccionarios. Los setters usan `validate=True` por defecto y pueden solicitarlo.
`add_comfort_metrics` anade requests con `validate=False`, invalida la cache y
obliga a ignorar diccionarios antiguos en el siguiente discovery explicito;
anadir metricas no ejecuta discovery por si mismo.

Esto es clave para trazabilidad experimental: las variables objetivo y de diagnostico quedan versionadas en la propia configuracion del experimento.

### Referencias de confort independientes del control

`fixed_en` integra grados-hora durante ocupacion frente a EN Cat II: neutral
`0.33*clamp(RMOT,10,30)+18.8`, limite superior +3 K e inferior -4 K. La extension
horizontal fuera de aplicabilidad es una politica explicita. No usa los
coeficientes custom que optimiza el controlador. `fixed_pmv` proporciona integral
ocupada de `abs(Fanger PMV)` y horas ocupadas con `abs(PMV)>0.5`; ambas familias
reportan tambien duracion ocupada. Ocupado significa `People Occupant Count>0`,
no un horario de oficina supuesto ni una ponderacion por personas.

Se reinicia el incremento cada timestep y se reporta `Summed/ZoneTimestep` en
`EndOfZoneTimestepBeforeZoneReporting`. La suma de reportes horarios ya conserva
la integracion temporal; no se multiplica por duracion otra vez. Claves, unidades,
roles devueltos e idempotencia se detallan en la [guia](source/comfort_metrics.rst).
Los outputs son por target; una suma multizona no se interpreta automaticamente
como horas del edificio. En 4.5 se conserva el contador aPMV nativo de referencia
movil y sin filtro de ocupacion; el PMV fijo es diagnostico, no un nuevo objetivo.

---

## Definicion del problema BESOS (inputs, outputs, objetivos)

Una vez definidos parametros y outputs:

- `set_parameters` fija el espacio de decision;
- `set_output_readers` selecciona lecturas y reductores; primero meters y despues variables;
- `set_problem` construye `EPProblem` con readers y objetivos;
- los objetivos se reducen con funciones de `objectives.py` (media, suma o serie completa).

`checked_sum_results` se elige expresamente en `func`, por callable o ruta de
modulo. Exige una serie `Value` no vacia, unidimensional y finita y devuelve un
`float`; no transforma unidades. Evita que una suma permisiva oculte NaN como
si fueran ceros, sin cambiar el comportamiento historico de `sum_results`.
Los metadatos `aggregation='sum'` de una metrica no seleccionan automaticamente
este reductor ni convierten un diagnostico en objetivo.

En terminos formales, se define una funcion vectorial:

```math
\mathbf{f}(\mathbf{x}) = \left(f_1(\mathbf{x}), \dots, f_m(\mathbf{x})\right)
```

donde `x` es el vector de parametros (ACCIM/APMV) y cada `f_i` se obtiene al simular EnergyPlus y reducir sus series de salida.

---

## Flujo parametrico completo

En `run_parametric_simulation` (de `main.py`) el pipeline sigue una logica robusta para campanas largas:

- normaliza politica de limpieza con `normalize_sim_file_cleanup_options` (`file_cleanup.py`);
- crea backup del IDF pre-ejecucion;
- consume el diseno muestral generado previamente (full set/factorial/LHS/Sobol/Morris/custom);
- expande por combinaciones `IDF x EPW` cuando aplica;
- ejecuta en paralelo con `ProcessPoolExecutor`;
- guarda por lotes (`batch`) y permite `checkpoint`;
- soporta `resume_from_checkpoint` para reutilizar tareas con firmas coincidentes;
- fusiona parciales (`_merge_parametric_batch_pickles`) y persiste resultados (`.pkl`/`.csv`/`.json`/`.xlsx`).

Resultado tipico: `outputs_param_simulation` como tabla maestra parametrica.

Este diseno minimiza riesgo de perdida de campana por fallo puntual y facilita reproducibilidad computacional.

El checkpoint y resume son optativos (`checkpoint_every_batch=False` y
`resume_from_checkpoint=False` por defecto). La firma nativa incluye identidad
IDF, EPW y valores de entrada; **no** certifica identidad del contenido del IDF,
objetivos o fuente del paquete. El checkpoint actual conserva `input_plan` y
`resume_plan_source='auto'` puede recuperar el plan original: un LHS nuevo no
debe confundirse con el ejecutado. Conservar todos los lotes referenciados.
El wrapper del paper comprueba ademas manifiesto, plan exacto, cobertura de
firmas y existencia de archivos; esas garantias adicionales no son defaults
del runner general.

---

## Flujo de optimizacion multiobjetivo

En `run_optimisation` (tambien en `main.py`) se activa una fase adicional:

- se parchea `AbstractEvaluator.to_platypus` hacia `_patched_to_platypus` (`patches.py`);
- se selecciona algoritmo (por defecto `NSGAII`, ademas de otros wrappers BESOS/Platypus);
- cada individuo se evalua con funcion parcheada que controla I/O, logging y limpieza;
- al final se anota no-dominancia (estado Pareto) de manera robusta y se persisten tablas de resultados.

Formalmente, se resuelve un problema tipo:

```math
\min_{\mathbf{x} \in \Omega} \; \mathbf{f}(\mathbf{x})
```

con frente de Pareto aproximado por poblacion evolutiva.

La decision de parchear el evaluador permite endurecer comportamiento operativo (copias de `in.idf`, registro JSONL, control de archivos temporales) sin modificar upstream BESOS.

`checkpoint_every_case=False` y `resume_from_checkpoint=False` son los defaults
nativos. La reanudacion reutiliza casos **IDF x EPW terminados**, no restaura una
poblacion, generacion ni estado RNG interrumpidos. Un caso incompleto se vuelve
a optimizar. La firma nativa comprueba algoritmo/presupuesto/opciones/agrupacion
Pareto/retencion de tabla, no todos los inputs o las definiciones de objetivos.
El wrapper del paper activa checkpoints y anade un manifiesto de contenido;
cambiar configuracion requiere otra campana compatible con esa nueva definicion.

---

## Que aporta `patches.py` en terminos de ingenieria experimental

`accim/parametric_and_optimisation/patches.py` anade robustez operativa en escenarios reales de computo:

- eval function parcheada para integrar gestion de carpeta por simulacion;
- serializacion y trazado de evaluaciones (util para auditoria posterior);
- control de limpieza por politica de archivos;
- soporte de eliminacion selectiva (por ejemplo, no dominados vs dominados segun configuracion).

Este bloque convierte una optimizacion teorica en una optimizacion operable a escala, donde disco, concurrencia y trazabilidad importan tanto como el algoritmo.

---

## Limpieza y gobernanza de artefactos

En campanas grandes, EnergyPlus genera gran volumen de archivos (`.err`, `.eso`, `.csv`, etc.).
`accim/parametric_and_optimisation/file_cleanup.py` normaliza extension/politica y aplica acciones `keep` o `delete` tras cada ejecucion.

Desde perspectiva metodologica, esto permite balancear:

- retencion maxima para auditoria profunda,
- retencion minima para viabilidad en disco y rendimiento I/O.

---

## Postproceso temporal y enriquecimiento de resultados

El modulo no se limita a un escalar final por corrida; tambien maneja resolucion temporal y agregaciones:

- expansion horaria desde resultados de simulacion;
- agregados diarios, mensuales y de periodo de simulacion;
- persistencia en atributos diferenciados (`outputs_*_hourly`, `*_daily`, `*_monthly`, `*_runperiod` cuando aplica).

Esto habilita analisis multiescala: desde KPI globales hasta dinamicas intradiarias.

Para postprocesar una campana terminada se cargan consolidados mediante
`load_outputs_parametric` o `load_outputs_optimisation`; no es necesario invocar
run/resume. En el wrapper, `load --result ...` selecciona un consolidado concreto
y rechaza checkpoints. Los historicos se conservan; no se simula para suplir
series ausentes. El wrapper lee CSVs horarios por columnas, conserva las fechas
reales de fin de intervalo (incluido 24:00) y no impone 2024 a cualquier serie.

---

## Analisis cuantitativo avanzado

En `accim/parametric_and_optimisation/analysis.py` destacan:

- `set_building_floor_area` y `normalize_outputs` para intensidades energeticas (kWh/m2):

```math
y_{norm} = \frac{y_{J}}{3.6\times10^{6}\,A}\quad[\mathrm{kWh/m^2}]
```

- sensibilidad global (SALib; por ejemplo Sobol/Morris segun configuracion),
- clustering para identificar regimenes operativos,
- evaluacion de robustez climatica entre escenarios EPW.

Esto aporta una capa analitica cientifica: no solo mejor valor, sino explicacion de estructura de respuesta del sistema.

La normalizacion energetica renombra columnas y no convierte el confort en
kWh/m2. En la entrega del paper se resuelven nombres/metadatos despues de
normalizar y se evita normalizar dos veces. Su denominador publicado de 312 m2
se compara con `mode='air-conditioned'`, sin asumir que `mode='all'` es equivalente.
Las regresiones custom usan PMOT; la referencia EN fija usa RMOT.

---

## Visualizacion reproducible y filtrado consistente

En `accim/parametric_and_optimisation/plotting.py`:

- `_get_plot_source_df` unifica origen (`parametric`, `optimisation`, etc.);
- el filtrado usa utilidades comunes (`apply_data_filter` en `utils.py`) con control estricto de vacios y validacion;
- se soportan visualizaciones para relaciones parametro-respuesta, distribuciones, Pareto y perfiles temporales;
- orden de categorias/subplots controlado por helpers de `utils.py`.

Resultado: figuras comparables entre campanas, con menor riesgo de sesgo por filtrados ad hoc.

---

## Comparacion entre campanas y trazabilidad entre instancias

El ecosistema incluye mecanismos para comparar instancias de simulacion (`compare_simulation_instances` y `SimulationComparisonSession` en `main.py`), con estrategias de correspondencia como `strict`, `auto`, `nearest`, `row_order`.

Esto es util para:

- comparar versiones del modelo,
- contrastar climas o hipotesis de control,
- construir analisis de regresion metodologica entre campanas.

---

## Fortalezas cientificas del diseno

- separacion limpia entre parametrizacion conceptual y mutacion concreta del IDF;
- pipeline completo DoE + optimizacion + analisis + visualizacion en un solo marco;
- soporte explicito de reproducibilidad (checkpoints, persistencia tabular, politicas de cleanup);
- extensibilidad (nuevo parametro = nueva funcion mutadora + registro en diccionario);
- robustez operacional para campanas largas y paralelas.

---

## Limitaciones tecnicas (para discusion del paper)

- dependencia fuerte de nombres/lineas EMS en mutadores (`Program_Line_n`), sensible a cambios en plantillas IDF;
- parcheo dinamico de evaluador (monkey patch) exige cuidado si conviven varias versiones/librerias en el mismo proceso;
- coste I/O elevado en campanas grandes si la politica de archivos no se ajusta;
- calidad de objetivos depende de seleccion y frecuencia de outputs (diseno experimental mal especificado puede sesgar conclusiones).

---

## Recomendacion de narrativa para el articulo

Estructura sugerida para la seccion metodologica:

1. Marco computacional: EnergyPlus + BESOS + ACCIM/APMV, y papel de `parametric_and_optimisation`.
2. Definicion del espacio de diseno: parametros, dominios, restricciones y tipos de muestreo.
3. Funcion objetivo y metricas: como se reducen series de salida y por que.
4. Protocolo de ejecucion: paralelismo, checkpoint/reanudacion, limpieza y persistencia.
5. Postproceso y analisis: normalizacion por area, sensibilidad, clustering, robustez climatica.
6. Validez y reproducibilidad: control de artefactos, comparacion entre campanas y limitaciones.


