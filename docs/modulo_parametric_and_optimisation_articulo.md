# Modulo `accim.parametric_and_optimisation`: descripcion tecnica detallada

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

---

## Arquitectura interna por archivo (vision funcional)

- `accim/parametric_and_optimisation/main.py`: nucleo de ciclo de vida (setup, outputs, parametros, problema BESOS, sampling, ejecucion, checkpoint, agregacion).
- `accim/parametric_and_optimisation/parameters.py`: factoria de parametros (`accis_parameter`) + wrappers OO para parametros frecuentes.
- `accim/parametric_and_optimisation/params_dicts.py`: diccionarios de mapeo nombre de parametro -> funcion modificadora.
- `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py`: mutadores de EMS ACCIM y filtros de combinaciones no validas.
- `accim/parametric_and_optimisation/funcs_for_besos/param_apmv.py`: mutadores EMS APMV por zona.
- `accim/parametric_and_optimisation/objectives.py`: reductores de salida (`mean`, `sum`, serie temporal).
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

---

## Gestion de salidas: descubrimiento, seleccion y aplicacion

El modulo contiene una tuberia explicita de outputs:

1. `discover_available_outputs` (inventario de variables/meters disponibles),
2. `select_outputs` (filtro de que se quiere medir),
3. `clear_outputs` (evitar residuos o duplicados),
4. `apply_outputs_preflight` (aplicar configuracion final al IDF).

Ademas existen helpers para inyectar `Output:Variable` y `Output:Meter` directamente (`set_output_variables_to_idf`, `set_output_meters_to_idf`).

Esto es clave para trazabilidad experimental: las variables objetivo y de diagnostico quedan versionadas en la propia configuracion del experimento.

---

## Definicion del problema BESOS (inputs, outputs, objetivos)

Una vez definidos parametros y outputs:

- `set_parameters` fija el espacio de decision;
- `set_problem` construye `EPProblem` con readers y objetivos;
- los objetivos se reducen con funciones de `objectives.py` (media, suma o serie completa).

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
- genera/consume el diseno muestral (full set/factorial/LHS/Sobol/Morris);
- expande por combinaciones `IDF x EPW` cuando aplica;
- ejecuta en paralelo con `ProcessPoolExecutor`;
- guarda por lotes (`batch`) y permite `checkpoint`;
- soporta `resume_from_checkpoint` usando firmas para validar compatibilidad de reanudacion;
- fusiona parciales (`_merge_parametric_batch_pickles`) y persiste resultados (`.pkl`/`.csv`).

Resultado tipico: `outputs_param_simulation` como tabla maestra parametrica.

Este diseno minimiza riesgo de perdida de campana por fallo puntual y facilita reproducibilidad computacional.

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

---

## Analisis cuantitativo avanzado

En `accim/parametric_and_optimisation/analysis.py` destacan:

- `set_building_floor_area` y `normalize_outputs` para intensidades energeticas (kWh/m2):

```math
y_{norm} = \frac{y}{A}
```

- sensibilidad global (SALib; por ejemplo Sobol/Morris segun configuracion),
- clustering para identificar regimenes operativos,
- evaluacion de robustez climatica entre escenarios EPW.

Esto aporta una capa analitica cientifica: no solo mejor valor, sino explicacion de estructura de respuesta del sistema.

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


