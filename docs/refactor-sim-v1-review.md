# Revisión de `refactor/sim-v1` y de la API Python de EnergyPlus

Fecha: **2026-10-24**. Informe interno; no forma parte del sitio Sphinx.

**Seguimiento de implementación (2026-10-24):** después de esta auditoría se
implementó el bloque de checkpoints verificables, limpieza de archivos propios
(incluido batch) y Pareto con restricciones. Véanse [la guía](source/checkpoint_integrity.rst)
y [DEVLOG](../DEVLOG.md). Las referencias, hallazgos y resultados de la auditoría
que siguen se conservan como instantánea de las versiones indicadas; la sección 9
no incluye ese bloque posterior. La selección de salidas multi-IDF y las
correcciones científicas siguen pendientes.

## 1. Dictamen

**Aprovechar la arquitectura, no fusionar ni adoptar la rama completa.** La
convergencia de los caminos batch/single y la separación de responsabilidades
son buenas ideas. Sin embargo, el código histórico no está listo para sustituir
al actual, ni basta con dar por válidos sus tests golden y aplicar mecánicamente
el plan de julio. Hay fallos funcionales, riesgos de borrado, comportamientos
numéricos sin un oráculo independiente y correcciones recientes que se perderían.

**`parametric_and_optimisation` sí está en la rama.** El informe de julio lo
excluyó de su revisión por considerarlo obsoleto; no dijo que no existiera.
Contiene incluso el arreglo de `set_problem()` que faltaba en `master`. No
obstante, su ejecución, persistencia, salidas y API pública están atrasadas
respecto a la versión actual.

**Base recomendada: el `master` actual, con extracciones incrementales detrás de
las interfaces existentes.** El trabajo de esta revisión está en
`review/refactor-sim-v1-20261024`, creada desde `master`. No se han fusionado,
rebasado, borrado ni publicado las ramas originales; tampoco se han hecho commits.

**La API Python merece un backend opcional y experimental, no una sustitución
inmediata.** Puede evitar parte del coste de lanzar el ejecutable y habilitar
controles externos. No sustituye el editor IDF, las reglas de confort, BESOS ni
el postprocesado. Sus ventajas de rendimiento deben medirse por carga de trabajo.

## 2. Alcance y trazabilidad

| Referencia | Estado revisado |
|---|---|
| Ancestro común | `c03250f` |
| Rama histórica, abreviada **H** | `refactor/sim-v1`, `ef1ec593` |
| Base mantenida, abreviada **M** | `master`, `1a2f5947`, accim 0.8.2 |
| Divergencia | 117 commits exclusivos de M; 36 exclusivos de H |
| Cambios de H desde el ancestro | 118 archivos; 8.419 inserciones y 5.960 eliminaciones, según Git |
| Entorno de pruebas | Windows, CPython 3.14.0, pytest 9.0.3, BESOS 2.2.3, eppy 0.5.69, NumPy 2.5.1, pandas 3.0.5, Matplotlib 3.10.8, PuLP 3.3.0 |

Se contrastaron el motor sim, sus entradas y plantillas EMS/HVAC, los límites con
parametric/BESOS, ejecución, utilidades, postprocesado, tests, dependencias y
contratos públicos. Se consultaron el informe y el plan históricos del
2026-07-19, pero sus conclusiones se contrastaron con el código. Las versiones
instaladas de EnergyPlus incluyen 9.4, 9.6, 25.1, 25.2 y 26.2; **no 26.1**.

No es una revisión línea a línea de todos los notebooks ni una validación
científica de todas las combinaciones de confort. Tampoco se han medido campañas
completas de optimización, consumo de memoria o concurrencia API. El conjunto
paramétrico histórico completo no se ejecutó: se ejecutó su regresión específica
de `set_problem`, además de las suites históricas de sim/data/run/utils.

Las referencias `H ruta:línea` y `M ruta:línea` corresponden a esas instantáneas,
antes de los pequeños cambios de esta rama. Se pueden consultar con
`git show refactor/sim-v1:ruta` y `git show master:ruta`. En M, los cuatro renglones
añadidos a `parametric_and_optimisation/main.py` desplazan referencias posteriores.

**Evidencia:** **R** = reproducción ejecutada; **S** = comprobación estática;
**V** = validación física/integral pendiente. «Nuevo» significa no identificado
en las revisiones consultadas, no necesariamente introducido recientemente.

## 3. Qué mejora realmente la refactorización

### Recuperable

- **Un único motor de preparación e inyección.** H comparte
  `_scan_and_setup_zones` y `apply_accis` entre disco y memoria
  (`sim/engine.py:152-167,503-646`, `batch.py:426-475`, `single.py:277-309`).
  M conserva dos constructores y tres secuencias de inyección. Esa duplicación
  ya produce diferencias reales, especialmente con HVAC existente y ventilación
  programada. La extracción debe partir del código **actual** de batch.
- **Organización por responsabilidades:** engine, batch, single, ems, hvac y
  prompts. Es más comprensible que una sucesión de archivos `accim_*`, pero
  mover funciones no elimina sus acoplamientos ni su estado implícito.
- **Aislamiento de la interacción:** es una dirección adecuada. Aún falta una
  capa de configuración y validación no interactiva; `prompts.py` no convierte
  automáticamente toda la biblioteca en una API headless.
- **Más pruebas de caracterización**, especialmente para utilidades y `Table`.
  Son un complemento útil de pruebas numéricas e integración, no su sustituto.
- **Pequeños arreglos independientes** recuperables sin cambiar nombres públicos:
  los tres portados en esta rama se detallan en la sección 9.

### Lo que no debe retroceder

- Inicialización EMS para EnergyPlus 26.1+, `People:Definition/Instance`,
  resolución de ocupantes en Space/SpaceList y consolidación por zona.
- Correcciones actuales de SetAST, PMV por lotes, `ComfStand=0`, signos/defaults
  de aPMV y ejecución con versión automática.
- Atribución y normalización de energía por zona en `Table`; compatibilidad
  de gráficos con pandas 3 y Matplotlib actuales.
- Planes multi-IDF/EPW, orden y duplicados de resultados, parámetros BESOS
  adicionales en los workers, checkpoints, metadatos, outputs adicionales,
  almacenamiento y aislamiento de directorios de la versión actual.
- Separación de `accim-samples`, restricciones de dependencias y ejemplos
  mantenidos. No restaurar ejemplos eliminados ni bytecode versionado.

### El módulo paramétrico no es una copia intercambiable

H tiene las clases `SimulationBase`, `ParametricSimulation`,
`OptimisationSimulation` y el wrapper de modelos predefinidos, multiprocessing,
preflight, backups y registro de evaluaciones. De los 16 archivos Python actuales,
12 tienen contraparte histórica; faltan `file_cleanup.py`,
`optimisation_progress.py`, `mn_filter.py` y `hourly_plotting.py`.

`main.py` pasó de 4.616 a 13.675 líneas físicas; este dato incluye docstrings y
**no es una medida de complejidad**. Los dos runners continúan en la clase base:
separar las clases públicas no ha separado todavía planificación, ejecución,
persistencia y postprocesado.

Además de nuevos métodos, han cambiado contratos: tuple frente a dict en
selección/discovery de outputs, argumentos posicionales de setters, alias
exportados y constructor. H importa los módulos renombrados de sim; M importa
los nombres actuales. Superponer el módulo de M sobre sim de H rompe imports y
keywords. En H, el despacho de optimización queda fuera del bucle interior de
EPWs (`main.py:3336-3394`): solo se optimiza el último clima de cada IDF. M ya
corrige este problema.

## 4. Hallazgos que impiden una adopción directa

### 4.1. Defectos históricos y propuestas que no se deben portar literalmente

| Prioridad | Evidencia | Hallazgo y referencia |
|---|---|---|
| P1 | R/S | H `sim/engine.py:119` usa `energyplus_version=` frente al parámetro real `EnergyPlus_version`. Se reprodujo el `TypeError` tanto con versión explícita 9.6 y un IDF como con `auto` y dos copias del mismo IDF 9.6. M no tiene el fallo del keyword, pero conserva la fuga de versión entre modelos. |
| P1 | R/S | H mantiene el generador PMV con variables de otro bucle: su propia prueba lo declara `xfail`. También conserva problemas de `ComfStand=0` y reemplazo/truncado de SetAST. M tiene regresiones específicas y arreglos posteriores; no recuperar estos archivos completos. |
| P1 | S | La supuesta corrección de `Table` sustituye `list.remove()` como argumento del pivot, pero deja `col_to_pivot` en `self.indexcols` y cambia la forma de las columnas sin adaptar las comparaciones. H `data/postprocessing/main.py:1687-1702,1782-1801,1834-1856,1904-1917`; el error original sigue en M `:2023-2029`. Hace falta una reparación coherente con índices locales y comparaciones por variable/categoría. |
| P1 | S | `removefiles()` histórico borra archivos ajenos y sus tests congelan ese comportamiento. H `run/run.py:145-157`, `tests/run/test_run.py:46-55`. Mantener el filtro y la exclusión de directorios actuales; aun así, un marcador en el nombre no demuestra propiedad. |
| P2 | R | `Table.time_plot` histórico falla con pandas 3 al usar `[0]` sobre un índice de texto. H `data/postprocessing/main.py:3773`; M usa acceso posicional y frecuencias compatibles. |
| P2 | S | El clean break no es únicamente un renombrado: el wrapper single histórico pierde miembros y métodos de la clase anterior, y exporta `modify_param` aunque no modifica parámetros. H `single.py:315-361,712-742`, `sim/__init__.py:6-17`. |
| P2 | S | La propuesta histórica T27 sobre ApplyCAT no demuestra el defecto que afirma: las líneas modificadas están dentro de `ComfStand == 99`. No aplicarla como corrección de estándares no custom. H `PLAN_IMPLEMENTACION_2026-07-19.md:890-901`, `ems/programs.py:349-365`. |

El soporte moderno de ocupantes/26.x y varias correcciones de M no son simples
listas de versiones: reemplazar esos módulos por H introduce regresiones de
semántica y de objetos. El plan antiguo de recortar SetAST a 18 campos tampoco
es compatible con la base actual de cuatro líneas.

### 4.2. Problemas compartidos o todavía presentes en M

| Prioridad | Evidencia | Hallazgo, impacto y siguiente prueba |
|---|---|---|
| P1 | S | **Propiedad de archivos.** Borrado por subcadena de `_pymod.idf`, barrido final de todos los temporales, incluso al cancelar, y reescritura del IDF original antes de la validación. M `sim/accis.py:651-660`, `accim_IDFgeneration.py:1685-1691`, `utils.py:325-339`. Probar sentinelas `a`/`ab`, cancelación y excepción; registrar archivos de esta invocación, no inferir propiedad por nombre. |
| P1 | S | **Objetos de salida compartidos.** `output_idfs` almacena repetidamente el mismo IDF mutable: los archivos pueden ser distintos pero las entradas apuntan al último estado. M `accim_IDFgeneration.py:1391-1440`. Probar dos variantes y correspondencia objeto/archivo. Cambiar los valores a `None` o rutas rompería el contrato: ofrecer snapshots o una nueva interfaz explícita. |
| P1 | S | **Preview y generación divergentes.** Las combinaciones HVACmode/VentCtrl filtradas en preview no se filtran igual al generar; el nombre PMV también difiere. M `accim_IDFgeneration.py:1266-1309,1601-1608,1659-1683`. Una sola secuencia inmutable debe producir nombres y modificaciones. |
| P1 | S | **HVAC existente.** Falta el bucle SingleCooling; hay incompatibilidad entre schedules únicos y ambos actuadores, selección del primer coil en lugar de agregación, y asociaciones de ventanas por subcadena. M `accim_ExistingHVAC.py:64-111`, `accim_ExistingHVAC_EMS.py:28-107`, `accim_Main.py:548-565`. Probar SingleHeating/SingleCooling, dos coils y `ZONE1`/`ZONE10`; no considerar suficiente arreglar solo el bucle. |
| P1 | S | **EMS ajeno.** ACCIS elimina todos los global/internal variables y construye gestores para programas que no necesariamente le pertenecen. aPMV puede gestionar de nuevo programas de ACCIS, incluyendo fragmentos de SetAST. M `accim_Base_EMS.py:1071-1126,1270-1371`, `apmv_setpoints.py:845-862`. Conservar variables y calling managers de usuario y restringir los cambios a objetos propios. |
| P1 | S/V | **Horas de confort.** El bloque frío de `CountHours_*` es inalcanzable con una banda ordenada; `OccComfHoursNoApp_*` no se reinicia en todos los caminos. M `accim_Base_EMS.py:117-139,649-677`. En M, el orden explícito también sitúa CountHours antes de actualizar umbrales. Validar transiciones frío/confort/calor y que las categorías particionen las horas, con un oráculo independiente. |
| P1 | S | **Lectura ejecutable de datos IDF.** `get_accim_args` mantiene `eval` sobre el RHS de programas: M `utils.py:484-503`, señalado ya en julio. No usar con entradas no confiables. Un `literal_eval` sin más convertiría a texto offsets legítimos como `3.5 + 1`, que hoy devuelve como `4.5`; estos se generan en `accis_single_idf_funcs.py:737-744` y `accim_IDFgeneration.py:1569-1579`. Sustituir por evaluación AST limitada a números y operadores aritméticos necesarios; nunca llamadas, nombres resolubles, atributos ni acceso a objetos. |
| P2 | S | **Validación e interacción.** Frecuencias inválidas producen `TypeError`, precisión cero llega a una división, pasos cero llegan a `arange`, fechas y reintentos no son coherentes, y parámetros explícitos pueden acabar en prompts. M `accis.py:461-465,754-770`, `accis_single_idf_funcs.py:640-678`, `accim_IDFgeneration.py:602-640,1052-1054`. Validar toda la configuración antes de mutar. |
| P2 | S | **Outputs.** La deduplicación compara cadenas contra objetos y eliminaría objetos equivocados; el filtrado de dataframes usa subcadenas/regex de nombres de archivo. M `accim_Base_EMS.py:1418-1434,1571-1591`. Dedupe por identidad completa (key, variable, frecuencia, schedule) y comparación exacta del identificador. |
| P2 | S | **Otros pendientes.** `pd.concat([])` con todos los modelos descartados, `make_averages` de VentHours sin variables en AC, SetpointAcc no aplicado igual en AC/MM y `outputsSpecified` no interactivo con variable sin inicializar. Pruebas pequeñas antes de extraer código. |

En utilidades meteorológicas también siguen pendientes el control del retorno de
Java, rutas EPW con directorios y limpieza de directorios preexistentes; restaurar
el original cuando no hay escenarios **no resuelve** esos otros problemas. En
postprocesado de ESO, truncar a 8.760 **filas** no representa un año subhorario,
y dividir nombres por el primer `:` pierde claves de zona: M
`utils.py:1501-1521,2183-2197,3026-3032`.

### 4.3. Hallazgos actuales fuera de la revisión histórica de sim

1. **P1 — Checkpoint incompleto que omite resultados [R].** Se ejecutaron cuatro
   evaluaciones sintéticas, en dos batches; se eliminó únicamente un pickle
   creado por la prueba y se reanudó. Resultado: **2 filas, ninguna evaluación
   repetida**, aunque el plan sigue teniendo cuatro. Se emite un warning, pero
   se conservan las firmas de tareas cuyo resultado desapareció.
   M `parametric_and_optimisation/main.py:9474-9485,9608-9621,9812-9835`.
   Reconciliar firmas con chunks legibles o rechazar el checkpoint de forma
   explícita; nunca devolver resultados parciales como una reanudación completa.
2. **P1 — Identidad incompleta de checkpoints [S].** El identificador paramétrico
   usa etiqueta IDF, EPW y parámetros; el de optimización tampoco captura el
   problema completo. Cambiar el modelo, lectores/reductores, restricciones o
   versión de motor bajo los mismos nombres puede reutilizar datos obsoletos.
   M `:8185-8195,10211-10224,10346-10367`. Necesita un fingerprint versionado de
   la evaluación y política de compatibilidad/migración.
3. **P1 — Pareto sin factibilidad [R/S].** Con objetivo a minimizar `[1,2]` y
   restricción `g <= 0`, valores `[1,0]`, `_annotate_pareto_status` marca
   `[True,False]`: el punto inviable domina al viable. La prueba es sintética,
   no una optimización EnergyPlus. La poda de workers tampoco integra
   restricciones; puede eliminar el artefacto de una solución viable.
   M `main.py:10617-10629,10722-10765`, `patches.py:304-340`.
4. **P1 — Selección de outputs multi-IDF que pierde su alcance [R/S].** Dos
   filas idénticas salvo `idf=A/B` se reducen a una fila con A. Se reprodujo la
   selección; el setter de variables filtra luego por IDF, mientras que el
   setter de meters aplica una lista global. M
   `main.py:4396-4417,4833-4958,5698-5700,5778-5780`.
5. **P1 — Limpieza paramétrica no limitada a la ejecución [S].** La optimización
   con `keep_sim_files='none'` borra todos los directorios `BESOS_Output*` y logs
   del directorio de salida; discovery utiliza `available_outputs` compartido.
   M `main.py:5479-5484,10504-10521`, `utils.py:373-405`.
6. **P1 — Single no equivale a batch [R/S].** El motor single puede indexar una
   lista vacía al resolver una zona sin `:`; importa el resolver en el cuerpo de
   la clase, pero lo llama como nombre global; no prepara la ventilación
   Scheduled como batch. M `accim_Main_single_idf.py:61-67,188-211,236-249,384-396`.
   Además, ambos `modifyAccis` buscan siempre `SetVOFinputData`, inexistente en
   AC-only; la clase lo busca durante su construcción. M
   `accis_single_idf_funcs.py:598-605`, `accis_single_idf.py:398-403`.
   Se reprodujo el `IndexError` de la función después de inyectar `vrf_ac` en
   una copia del modelo de muestra 25.2; los demás extremos son estáticos.
7. **P1 — Matriz y fórmulas SetAST [R/S/V].** M anuncia CS6/CM0 y CM1 pero ambos
   generadores devuelven cero asignaciones de ACST/AHST (reproducido). La tabla
   histórica solo anunciaba CM2/CM3. Además, CS6/CM2/CAT80 usa el mismo centro
   `PMOT*0.30+25.9` para calefacción y refrigeración: con PMOT=20 y tolerancias
   -0.1/+0.1 resulta ACST=31.8 y AHST=32.0. La inversión algebraica es verificable;
   la fórmula científica correcta debe contrastarse con su fuente antes de
   cambiarla. M `setAST_models.py:411-482,2113-2157`.
8. **P2 — Parámetros BESOS genéricos sin parámetros ACCIS [R].**
   `set_parameters(additional_params=[RangeParameter envuelto en Parameter])`
   da `TypeError`: los flags dependen de un diccionario ACCIS no vacío.
   M `main.py:6226-6262`. Es distinto del arreglo ya incorporado al worker.
9. **P2 — Cobertura que no se recoge [S].** De los 36 archivos originales del
   directorio paramétrico, 11 numerados no coinciden con `test_*.py`. El
   `pytest.ini` anidado usa `[tool:pytest]`, no `[pytest]`. Algunos tests además
   están desactualizados o atrapan toda excepción sin fallar. No basta con
   cambiar el patrón de colección: hay que reparar sus contratos.

Otros pendientes del informe paramétrico de julio que continúan: backup por
subcadena, `Parameter.modify()` que ejecuta todos los modificadores al construir
el diccionario, filtrado de combinaciones que omite comprobaciones al faltar
CAT, exportación XLSX incondicional y estimador que no multiplica por número de
IDFs. No se presentan como descubrimientos nuevos.

## 5. Qué prueban y qué no prueban los goldens

- H `tests/sim/_golden.py:25-45` ordena todos los objetos, incluidos los
  ProgramCallingManager. Así puede ocultar un cambio en el orden de ejecución
  que M considera significativo.
- H `tests/sim/_golden.py:57-67` y
  `tests/data/test_table_characterization.py:79-94` crean un golden ausente y
  aceptan el test sin exigir `--update-golden`. Falta el oráculo precisamente
  cuando más se necesita.
- Las configuraciones batch históricas usan un IDF, `auto` y una combinación;
  no simulan. No detectan el segundo IDF, objetos alias, inicialización Erl,
  factibilidad ni convergencia térmica.
- Los tests actuales de reemplazo SetAST comparan con el propio generador:
  protegen la mecánica de sustitución, no la validez científica de la fórmula.
- Mantener goldens revisados, fallo por ausencia, fixtures pequeñas y pruebas
  explícitas de orden/propiedad; añadir invariantes numéricas y simulaciones
  aisladas por versión. No regenerar snapshots para ocultar una diferencia.

## 6. Disposición de los 36 commits históricos

**Port** = recuperar el cambio independiente; **adapt** = conservar la intención
sobre M con nuevas pruebas; **drop** = no trasladar el diff porque está superado,
es incompatible o solo documenta el clean break abandonado. No son órdenes de
cherry-pick: un mismo commit mezcla producción, tests y documentación.

| Commit | Disposición | Motivo |
|---|---|---|
| `35a272e2` | adapt | Caracterización sim; endurecer goldens y añadir casos no cubiertos. |
| `8c3b52d1` | adapt | Cobertura single/modify/aPMV con API y semántica actuales. |
| `6c1cb805` | port al adaptar goldens | Gzip determinista, sin aceptar automáticamente referencias ausentes. |
| `ff94c014` | adapt | Unificación single/batch desde el motor actual. |
| `4b7b6fd1` | adapt | Organización por responsabilidades; no transportar bytecode ni implementación obsoleta. |
| `ab1faff4` | adapt | Nombres internos PEP8 después de estabilizar contratos. |
| `539d7ae8` | drop como cambio público | Mantener keywords actuales; aliases/deprecación si se decide otra API. |
| `9acc2589` | adapt | Una fachada single sin perder atributos/métodos ni wrappers actuales. |
| `6dea3cc4` | adapt | Exportar solo interfaces completas y compatibles; excluir `modify_param` incompleto. |
| `07da26c8` | adapt | Compartir preparación en memoria conservando People/Space/26.x. |
| `50db30f3` | adapt | Limpiar código muerto/defaults mutables selectivamente. |
| `b172cdce` | drop | No publicar ni reinstaurar la versión 1.0 histórica ni su migración literal. |
| `76b62e77` | adapt | Secuencia única de inyección; conservar inicialización y orden actuales. |
| `e53d246e` | drop literal | Los ejemplos deben seguir la API vigente y las fuentes actuales. |
| `5a84769b` | adapt | Prompts sobre configuración validada, no dentro del motor. |
| `d9144407` | drop literal | Notebooks/documentación ya mantenidos; no copiar salidas antiguas. |
| `b43b2fa3` | drop literal | Igual para samples; no restaurar ejemplos eliminados. |
| `83652a5a` | adapt | Caracterización Table con resultados de zonas/unidades corregidos. |
| `2ff043c2` | adapt | Guard de IDF útil; pivot necesita reparación completa, no el diff de H. |
| `2e628af2` | adapt parcialmente | Helpers/tests útiles; preservar auto, nombre público y limpieza actual. |
| `4a1d3a32` | port parcial aplicado | Inicialización por EPW; limpieza de código muerto separable. |
| `3213b98a` | adapt | Tests de datos/runner, sin expectativas de borrado inseguras. |
| `e0c034a1` | adapt | Cobertura Table/utils con fixtures mínimas. |
| `24def6c7` | drop producción / adapt tests | Arreglos Matplotlib superados en M. |
| `4d46f1f4` | adapt tests | Prueba útil, pero necesita la corrección actual de pandas. |
| `5b0029a9` | adapt tests | Comparaciones/gráficos y oráculos más fuertes que existencia de PNG. |
| `c43d1294` | adapt | Probar consultas/orden sin reemplazar ejemplos mantenidos. |
| `11b7b29c` | port parcial aplicado | Sentinel de cleaner; reforzada la seguridad de las pruebas. |
| `b7c8a260` | adapt tests | Retener utilidades no cubiertas; evitar duplicar tests de versiones. |
| `c0c20acf` | adapt tests | Round-trip con API actual y lectura segura de expresiones. |
| `0848b189` | drop | Notas de una release 1.0 que no se va a adoptar. |
| `50366d53` | port aplicado | `sim_outputs=None`; regresión sin IDF ni EnergyPlus. |
| `efc91e23` | drop literal / adapt ideas | Documentar la API actual, no los nombres históricos. |
| `c68eb1c9` | drop | No reintroducir el changelog histórico. |
| `48f7e9e3` | adapt | Fixtures y configuración con goldens obligatorios. |
| `ef1ec593` | conservar como antecedente | Informe/plan de julio, revisados críticamente; no aplicar como parches. |

## 7. EnergyPlus Python API: utilidad y límites

### Alternativas

| Alternativa | Utilidad | Coste/riesgo | Recomendación |
|---|---|---|---|
| Mantener CLI, EMS e IDF | Portabilidad de los IDF y aislamiento del motor; lectores actuales. | Coste de proceso y de archivos. | Default mantenido. |
| API Runtime solo para ejecutar | DLL residente por worker, progreso/cancelación/callbacks opcionales. | Gestión de estado, instalación/DLL, errores y preservación de artefactos. | Primer experimento razonable; no está integrado en ACCIM. |
| Control adaptativo Python por callbacks | Fórmulas testeables sin construir tanto Erl; controles interactivos. | Reescribir orden, warmup, historia, sensores, actuadores y reporting; perder el IDF autocontenido. | Investigación separada, no migración automática. |
| `PythonPlugin` dentro del IDF | Control Python desplegado con el modelo. | Scripts y Python embebido adicionales; diferencias de soporte por versión. | No confundir con Runtime externo ni asumir su compatibilidad en toda la matriz. |
| Sustituir lectores por DataExchange | Evitar algunos archivos si solo se precisan ciertos agregados. | Los meters son instantáneos; se deben reproducir unidades, integración, frecuencias y metadatos. | Solo tras medir y probar equivalencia de resultados. |

### Hechos verificados en el SDK instalado

- Runtime acepta opciones equivalentes a CLI; sin callbacks ejecuta el mismo
  motor. No es un motor numérico alternativo.
- DataExchange ofrece variables, actuadores, variables internas y nombres de
  objetos; **no es un editor general de objetos IDF**. Eppy/BESOS sigue siendo
  necesario, o debe reemplazarse por otra capa de modelado independiente.
- Pedir variables antes de ejecutar, esperar `api_data_fully_ready(state)`,
  comprobar handles `-1`/flags de error y distinguir readiness de fin de warmup.
  Reset exige registrar de nuevo callbacks, peticiones y handles.
- `new_state`/`delete_state` deben estar en un ciclo protegido por `finally`.
  Estado ctypes y handles no se serializan entre workers.
- Los wrappers 9.4 y 26.2 normalizan de forma distinta el booleano nativo de
  readiness; la versión de protocolo `0.2` no identifica la release de EnergyPlus.
  Cargar siempre wrapper y DLL de la **misma instalación**.
- El README documenta thread safety del motor desde 9.5, no 9.4. Eso no hace
  thread-safe al conjunto ACCIM/eppy: hay IDD global y patches/globales Python;
  el wrapper conserva callbacks globales y `clear_callbacks()` no es por estado.
  Mantener procesos como frontera de aislamiento es una decisión del cliente,
  no afirmar que las versiones modernas del motor prohíben threads.
- ExpandObjects, ReadVarsESO y Transition no desaparecen al usar la API.
  En 26.2 Runtime configura la raíz para localizar herramientas auxiliares;
  ese comportamiento no debe suponerse para 9.4.

Fuentes consultadas, locales y ligadas a versiones reales:
`C:/EnergyPlusV26-2-0/pyenergyplus/{api,runtime,state,datatransfer,plugin}.py`,
`include/EnergyPlus/api/runtime.h:104-132`, `readme.html:207-215` y sus
contrapartes en `C:/EnergyPlusV9-4-0/pyenergyplus/`.
En DataExchange 26.2: peticiones/handles `:454-506`, meters `:593-628`,
actuadores `:630-687`, globals/trends de plugins `:839-938`, warmup `:1267-1307`.
Referencias oficiales: [API](https://energyplus.readthedocs.io/en/latest/),
[documentación general](https://energyplus.net/documentation) y
[EMS](https://energyplus.readthedocs.io/en/stable/ems-application-guide/ems-application-guide.html).
No se presenta como verificada la compatibilidad plugin/API conjunta de todas
las releases ni el comportamiento de su GIL.

### Dónde conectar un futuro backend

Bajo la evaluación/modelado BESOS, antes de lanzar EnergyPlus: entrada IDF ya
preparada, EPW, instalación/opciones y directorio propio; salida con estado,
diagnósticos, rutas y procedencia del `in.idf` ejecutado. Compartir ese contrato
entre serial, multiprocessing, optimización y discovery. `set_evaluator()` por
sí solo no basta: los workers paramétricos construyen `EvaluatorEP` directamente
y discovery llama también a `run_building`. `runEp()` es otro camino eppy, no
el backend único de parametric.

Conservar outputs CSV/ESO/MTR/RDD/MDD, preprocessing, keep-files, logs,
checkpoints y errores. Un exit code de API no equivale a una evaluación BESOS.
Extraer estos contratos del módulo actual antes de mover monkey-patches o hacer
BESOS opcional: también lo importan sim, utils y Table.

## 8. Medición reproducible CLI frente a API

El script [benchmarks/energyplus_api.py](../benchmarks/energyplus_api.py) es un
experimento independiente, **no un backend de producción**. No modifica el IDF,
requiere directorio nuevo, alterna el orden de pares CLI/API, separa warmups e
importación/DLL de API, crea/libera estado por simulación y verifica todas las
filas y valores de los CSV de variables y meters emitidos (tolerancias
`rtol=1e-10`, `atol=1e-9`). Una ejecución fallida o datos distintos abortan la
medición; no se declara éxito por tener solo exit code cero.

El tiempo CLI incluye crear/esperar el proceso; API representa un worker Python
**residente**, no arrancar un intérprete por evaluación. La carga inicial de DLL
se informa aparte. Se mantienen los mismos inputs, outputs y opciones `-r`.
No se incluyen generación de modelos, BESOS, preflight, extracción de objetivos,
optimización ni transferencia IPC. No hay callbacks Python de control.

EnergyPlus **26.2.0**, cinco pares medidos por caso, más un par previo descartado:

| Caso | Mediana CLI | Mediana API | API/CLI | Paridad comprobada |
|---|---:|---:|---:|---|
| `1ZoneUncontrolled`, anual, Golden-NREL, `-r -a` | 19,452 s | 19,898 s | 1,023 | 8.760 filas de variables y meters; 1.209.646 celdas numéricas |
| ACCIM TestModel, 2 zonas, `vrf_ac`, CS99, Sevilla, 1 día, `-r` | 3,094 s | 2,828 s | 0,914 | 24 filas y 144 celdas numéricas de variables |

Carga inicial de API: 0,072 s y 0,067 s respectivamente, fuera de esas medianas.
Rangos observados: anual CLI 18,951–19,740 s / API 18,890–20,723 s;
ACCIM CLI 2,988–3,576 s / API 2,776–2,987 s. Los tiempos y su alcance están en el
[resumen JSON versionado](../benchmarks/results/energyplus-api-2026-10-24.json).
Los JSON originales, hashes de inputs, warmups y todos los artefactos se conservan
en `D:/Python/accim-api-audit-20261024/`.

**Interpretación:** ahorro de unos 0,266 s (8,6 %) en el caso ACCIM corto; ningún
ahorro observado en el anual, cuya mediana API es 2,3 % mayor. Cinco pares y dos
modelos en un equipo no permiten afirmar una aceleración general ni significación
estadística. El caso anual incluye unos 16–18 s en ReadVarsESO para las variables:
reducir salidas y evitar conversiones redundantes merece medirse antes de cambiar
el backend. Esto complementa, no sustituye, la estrategia de salidas mínimas ya
acordada para los notebooks paramétricos.

En el modelo ACCIM no se emite CSV de meters por ninguna vía; ReadVarsESO avisa
del MTR ausente. El modelo mantiene los dos diagnósticos conocidos de IdealLoads
huérfanos y termina correctamente. También solicita CSV nativo, que `-r`
sobrescribe. No se han ocultado esos avisos ni interpretado la paridad como
validación física del modelo. ExpandObjects, plugins, callbacks de control y
otras versiones **no** se han ensayado en este benchmark.

Para reproducir el caso oficial desde PowerShell, usando un directorio nuevo:

```powershell
python 'D:\Python\accim\benchmarks\energyplus_api.py' --energyplus-home 'C:\EnergyPlusV26-2-0' --idf 'C:\EnergyPlusV26-2-0\ExampleFiles\1ZoneUncontrolled.idf' --epw 'C:\EnergyPlusV26-2-0\WeatherData\USA_CO_Golden-NREL.724666_TMY3.epw' --output-dir 'D:\runs\api-audit-one-zone' --annual --repeats 5 --warmups 1
```

El input ACCIM se preparó ejecutando exclusivamente
`tests/core/test_energyplus_versions.py::test_custom_model_simulates_with_26_2`,
con `--basetemp=D:/Python/accim-api-audit-20261024/prepared` (directorio nuevo:
pytest puede eliminar el contenido de un `--basetemp` existente). Su
`custom_model_1_day.idf` y `Seville.epw` se pasaron al mismo script, sin `--annual`.
El script requiere el SDK de la instalación indicada, no instalar `pyenergyplus`
desde PyPI.

## 9. Cambios aplicados y validación

Solo tres arreglos de producción, sin cambiar versión, dependencias, fórmulas,
API pública ni backend:

1. `WorkspaceArtifactCleaner`: diferenciar snapshot vacío de snapshot no capturado.
2. `morph_epws`: calcular el directorio padre por EPW aunque no haya escenarios.
3. `SimulationBase`: inicializar `sim_outputs=None` y documentar el contrato.

Pruebas nuevas: 13 casos de regresión para esos arreglos y 9 casos del benchmark
(diferencias/ausencia/no-finitos en CSV, liberación de estado, restauración de CWD
y no reutilizar/borrar directorios existentes). Las de morphing simulan Java:
**no se ha validado FutureWeatherGenerator real**.

| Ejecución | Resultado |
|---|---|
| M antes de editar producción: core + parametric estándar | **339 passed**, 1.906 warnings, 433,56 s |
| Casos nuevos antes de los arreglos | **7 failed, 15 passed** |
| Mismos casos después | **22 passed**, 1 warning |
| Primera colección histórica con Python del usuario | Bloqueada por `geopy` ausente; no confundir con fallo del código probado |
| Histórica con geopy 2.5.0/geographiclib 2.1 en venv aislado que comparte el resto de dependencias | **81 passed, 1 failed, 1 xfailed**, 10 warnings, 147,08 s; fallo pandas en `time_plot`, xfail PMV |
| Casos sintéticos adicionales | Checkpoint: 4 → 2 filas; Pareto inviable; scope multi-IDF perdido; parámetros genéricos rechazados; CS6/CM0-1 sin asignaciones |
| Generación/modificación con IDF copiados | H: fallo del keyword en versión explícita y segundo IDF auto; M: modificación AC-only con `IndexError` |
| Integración y benchmark adicionales | Preparación ACCIM 26.2: 1 passed; 24 ejecuciones CLI/API (incluidos warmups), todas con paridad de los CSV emitidos |
| Suite mantenida completa tras cambios | **361 passed**, 1.906 warnings, 324,68 s; exit code 0 |
| Comprobaciones adicionales | `git diff --check`, enlaces locales/wiki, renderizado de las tablas y correspondencia del resumen JSON con los datos crudos; sintaxis de los cinco archivos Python nuevos compatible con la gramática 3.9 |

Los warnings del IDE incluyen anotaciones preexistentes de morphing y escapes
regex en utils, además de incompatibilidad de pandas-stubs. No se ha afirmado
que todo el repositorio esté libre de warnings. Los resultados baseline no
incluyen los 11 archivos paramétricos numerados que no recoge pytest por defecto.

Registros de esta sesión: `C:/Users/sanga/AppData/Local/Temp/accim-sim-audit-36c00023/`
(XML JUnit y logs de ambas bases, regresiones antes/después,
`confirmed-probes.json`, `historical-probes.json` y `current-single-probe.json`). La copia histórica aislada es
`D:/Python/accim-sim-v1-audit`, usada en detached HEAD y **retirada al terminar**.
Las primeras importaciones regeneraron bytecode histórico versionado; se
comprobó que eran los únicos cambios, se restauró/eliminó exclusivamente ese
bytecode y se retiró el worktree limpio, sin forzar. No cambió su código fuente,
documentación ni goldens. `master` sigue en `1a2f5947` y `refactor/sim-v1` en
`ef1ec593`; el otro worktree preexistente no se tocó.

## 10. Secuencia de trabajo recomendada

1. **Integridad antes que reorganización:** corregir ownership de temporales,
   limpieza, checkpoints perdidos y su fingerprint; sustituir `eval` sin cambiar
   la interpretación de los offsets válidos. Tests con sentinelas y fallos
   inducidos, no solo caminos exitosos.
2. **Contratos y corrección:** scope multi-IDF, factibilidad/Pareto, AC-only,
   HVAC existente, ventilación programada e invariantes de confort. Resolver
   científicamente CS6 antes de elegir una nueva fórmula.
3. **Extracción de sim actual:** preparación común de zonas/ocupantes y
   `apply_accis`, separando la política de sizing de la inyección; fachada
   compatible para las entradas existentes. No mezclar aquí cambios numéricos.
4. **Unificar combinaciones/configuración:** un iterador para preview/generación,
   validación previa y prompts como adaptador opcional. Respetar el contrato de
   `output_idfs` o introducir otro explícito, no mutarlo silenciosamente.
5. **Descomponer parametric:** plan, ejecución, outputs, persistencia y reporting
   detrás de `SimulationBase`; preservar los tests y contratos actuales. Arreglar
   colección de tests y excluir `tests` del paquete distribuido.
6. **Piloto API opt-in:** validar serial/2 workers, varias versiones y modelos,
   outputs/add_outputs, error/cancelación, preprocessing, storage y resume;
   medir throughput y memoria de campañas reales. Mantener fallback CLI.

Cada etapa debe ser un cambio revisable con pruebas. No hay razón técnica para
supeditar los arreglos de integridad ni la extracción de funciones a adoptar
la API de EnergyPlus. Tampoco se justifica todavía sustituir Erl por Python.
La revisión está completada cuando quedan discriminados qué reutilizar y qué
no; **la refactorización integral y los defectos pendientes no se dan por resueltos**.




