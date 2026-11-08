# Cómo ha cambiado el código de accim en la versión 1.1.0

Guía de la reestructuración de `accim.sim` con eppy (rama `v1.1.0`) respecto a accim 1.0.0, para quien mantiene
accim; no es documentación de uso. La estructura de módulos de 1.0.0 se mantiene (`CAMBIOS_CODIGO_v1.0.0.md`); lo que
cambia es cómo se leen, cambian y escriben los modelos.

Lo que ya está en otros documentos no se repite aquí:

- `CHANGELOG.md` (sección Unreleased): los cambios que ve el usuario.
- `docs/source/9_migration_guide.md`, sección 9.4: lo que puede notar el usuario.
- `DEVLOG.md`: el registro del trabajo, con cómo se comprobó.
- `notes/decisions.md`: la decisión y sus motivos.

## 1. En resumen

**La idea.** accim lee, cambia y escribe los modelos con los métodos de eppy, en lugar de con utilidades propias, para
que quien conozca eppy pueda leer `accim.sim` sin aprender nada más. Cuando eppy es más lento que el código anterior, se
prefiere eppy (decisión del autor: "prefiero que sea más entendible aunque sea un poco más lento"); y se usa eppy en vez
de besos siempre que se puede.

**Lo que no cambia.** El uso, los argumentos y los resultados de las simulaciones. Los IDF de salida tienen los mismos
objetos y valores, salvo en los programas EMS (sección 7) y en lo que corrigieron las pruebas de los sistemas HVAC
existentes con los archivos de ejemplo de EnergyPlus (sección 8).

**Lo que cambia.**

- Lectura: `load_idf` lee todos los modelos con eppy, también con `energyplus_version='auto'` (antes, con besos).
- Escritura: eppy guarda cada IDF de salida entero (`IDF.savecopy`). Es más lento que el `IdfWriter` de 1.0.0, que
  escribía una sola vez el texto de los objetos que no cambian: AddAccis con los 140 IDF de salida del modelo de
  ejemplo tarda unos 16 s en vez de unos 5 s.
- Edición: `getobject`, `removeallidfobjects`, `fieldvalues`... en vez de listas de nombres y de `.obj`.
- Algunos números del modelo de entrada se escriben como los escribe eppy (`2.0` como `2`), con los mismos valores:
  eppy lee los campos numéricos como números y besos los dejaba como texto.
- El backend de la API de Python lee y cambia el modelo con eppy, en vez de con un analizador de texto propio.
- Los programas EMS de los IDF de salida solo tienen el código de los estándares de confort de sus zonas, y las líneas
  de todos los programas EMS van sangradas dentro de los bloques `IF` y `WHILE` (sección 7).
- `ex_ac` y `ex_mm` funcionan con cualquier sistema HVAC de los archivos de ejemplo de EnergyPlus cuyo modelo original
  funcione, y en modo mixto las ventanas se abren y se cierran cuando lo decide el EMS, con AirflowNetwork o con
  ventilación por horario (sección 8).

## 2. De las utilidades de accim a los métodos de eppy

| accim 1.0.0 | accim 1.1.0 |
| --- | --- |
| `idf_tools.try_objects(idf, tipo)` | `idf.idfobjects[tipo]`, para los tipos que tienen todos los IDD (9.1 a 26.2); `idf.idfobjects.get('SPACE', [])` para los que no: `Space` y `SpaceList` (desde 9.6), `People:Instance` y `People:Definition` (desde 26.2) y los `...:Design` de los sistemas radiantes (desde 9.6) |
| `idf_tools.remove_objects(idf, tipo)` | `idf.removeallidfobjects(tipo)` |
| `idf_tools.idf_text(idf)` | `idf.idfstr()` |
| `idf_tools.copy_idf(idf)` | Leer el archivo otra vez con `load_idf` (`AddAccis` lo lee dos veces: `input_idfs` y el modelo al que añade el ACCIS) |
| `if nombre in [o.Name for o in idf.idfobjects[tipo]]` | `idf.getobject(tipo, nombre) is not None` |
| `next((o for o in ... if o.Name.upper() == nombre.upper()), None)` | `idf.getobject(tipo, nombre)` |
| `obj.obj[2:]`, `obj.obj[0]` | `obj.fieldvalues[2:]`, `obj.key` |
| `idf_tools.add_program`, `set_program_lines`, `replace_program_lines` | `ems.programs.add_program(idf, nombre, líneas)` y `ems.programs.set_program_lines(programa, líneas)` |
| `generation.IdfWriter` | `generation.set_combination(idf, argumentos, combinación)` y `idf.savecopy(ruta)` |
| `energyplus_api.parse_idf`, `read_idf`, `render_idf`, `objects_for_api`, `IdfObject` | `load_idf`, `energyplus_api.read_ems(idf)`, `energyplus_api.prepare_for_api(idf)` e `idf.saveas(ruta)` |
| `besos.eppy_funcs.get_building(ruta)` (en `load_idf`, `Table`, `chile_funcs` y `accim.utils`) | `accim.sim.accis.load_idf(ruta)` |
| `_add_sensor` (`hvac/vrf.py`), `_new_sensor` (`ems/objects.py`), los sensores de `hvac/existing.py` | `ems.objects.add_sensor(modelo, nombre, clave, variable)` |
| `existing._add_schedule` | `hvac.schedules.add_compact_schedule` |

besos se sigue usando donde hace falta lo que solo tiene besos: el módulo paramétrico (problemas, evaluadores,
optimización) y `accim.utils.outputs` (ejecuta EnergyPlus y lee los resultados del ESO). `accim.utils.get_building`
sigue siendo el de besos.

## 3. Lo que hay que saber de eppy

- **Un IDD por sesión de Python.** El IDD es un atributo de la clase `IDF` de eppy: el primer modelo que se lee lo
  fija. `load_idf` da un `ValueError` claro con un modelo de otra versión ("eppy is already using the IDD..."). besos
  tiene su propia clase `IDF` (una subclase), con su propio IDD, así que los modelos de besos del módulo paramétrico no
  chocan con los de eppy.
- **`idf.idfobjects` no distingue mayúsculas**: en eppy, ni con `[]` ni con `in` ni con `.get`; en besos, solo con
  `[]`. Por eso, con `.get` las claves van en mayúsculas (`idf.idfobjects.get('SPACE', [])`): las funciones que reciben
  un objeto IDF (`add_accis_to_idf`, `apply_apmv_setpoints`...) también reciben los de besos.
- **`idf.getobject(tipo, nombre)`** compara el primer campo de cada objeto (`Name`, `Heat_Pump_Name`,
  `Thermostat_Name`, `Zone_Name`...) sin distinguir mayúsculas, como EnergyPlus; da `None` si no está. Recorre los
  objetos del tipo cada vez, así que en bucles grandes es algo más lento que un conjunto de nombres.
- **Los números son números.** eppy lee los campos numéricos del IDD como números (besos los dejaba como texto), y
  los vacíos como `''`. Cuidado con `str(valor or '')`: convierte el `0` en `''` (era el fallo de los límites de
  temperatura exterior de 0 °C); hay que comprobar `str(valor).strip() == ''`.
- **Las líneas de los programas EMS** son los valores de los campos después del nombre: `programa.fieldvalues[2:]`.
  Para cambiarlas, `set_program_lines` borra las que hay (`del programa.fieldvalues[2:]`) y asigna cada una por su
  nombre (`programa['Program_Line_3'] = ...`): así eppy amplía los nombres de los campos del IDD cuando hacen falta.
  Asignar la lista directamente en `fieldvalues` no los amplía, y eppy no escribe los valores sin nombre de campo.
  `IDF.removeextensibles` de eppy hace lo mismo que el `del`, pero necesita el tipo en mayúsculas y busca el programa
  por su nombre.
- **`EpBunch.__repr__` es lento**: da el texto de un objeto con los comentarios de todos los campos del IDD de su tipo;
  `idfstr`, `save`, `saveas` y `savecopy` lo llaman para cada objeto. Es lo que hace más lenta la generación de los IDF
  de salida.
- **`IDF.copyidf()` de eppy no copia el objeto `Version`**, y crea un `IDF` de eppy aunque el modelo sea de besos: no
  sirve para copiar modelos.
- **Un modelo de eppy ocupa mucha memoria** (unos 20 MB el modelo de ejemplo de 140 kB, unas 140 veces su texto). Por
  eso `AddAccis` guarda el texto de cada modelo con el ACCIS (`idf.idfstr()`) mientras pregunta los argumentos de los
  IDF de salida, y eppy lo lee otra vez para escribirlos.

## 4. `AddAccis`

Los pasos de `CAMBIOS_CODIGO_v1.0.0.md` (sección 4) siguen, con estos cambios:

1. Para cada IDF de entrada, `load_idf` lo lee dos veces con eppy: `input_idfs[nombre]`, que no cambia, y el modelo al
   que se añade el ACCIS (antes, una copia hecha a partir del texto).
2. Se guarda el texto del modelo con el ACCIS: `idf.idfstr()`.
3. `_write_output_idfs`: eppy lee ese texto (`IDF(StringIO(texto))`), `indent_programs` vuelve a sangrar los
   programas (eppy quita los espacios al leer) y, para cada combinación, `generation.set_combination` escribe los
   argumentos de cada zona en su programa `SetInputData_<zona>` (los de la combinación, o los de `zone_arguments`),
   `set_comfort_standard_code` deja en los programas solo el código de los estándares de confort de las zonas y
   `idf.savecopy(ruta)` guarda el IDF de salida.
4. `output_idfs` lee cada IDF de salida con eppy cuando se pide.

## 5. El backend de la API de Python

`run_simulation(ruta, ...)`: lee la versión del archivo (`read_idf_version`), carga la API de esa versión, lee el
modelo con `load_idf`, `prepare_for_api(idf)` lee sus objetos EMS (`read_ems`, con los nombres de los campos de eppy:
`sensor.OutputVariable_or_OutputMeter_Index_Key_Name`...) y quita los programas, gestores de llamada y actuadores, y
`idf.saveas` escribe el modelo que ejecuta EnergyPlus. Como lee el modelo con eppy, en una sesión de Python solo
ejecuta los modelos de una versión de EnergyPlus; `run_simulations` y `run_ep(backend='api')` ejecutan cada
simulación en su propio proceso. El controlador (`controller.py`) y el intérprete de Erl (`ems/erl.py`) no cambian.

## 6. Otros cambios del código

- `chile_funcs.py`: lee el modelo con `load_idf` (antes importaba besos al importar el módulo), y los 130 campos del
  horario salen de una tabla de los meses (`_MONTHS`) en vez de escribirse uno a uno.
- `apmv.py`: los programas EMS son listas de líneas (`add_program`), y los cuatro bloques de `set_pmv_input_parameters`,
  un bucle. Las líneas de la temporada de refrigeración, que eran las mismas que las de `SetAST_Master`, están en
  `ems/setast.COOLING_SEASON_LINES`.
- `hvac/vrf.py`: el objeto de prueba que da los nombres de los límites de temperatura del IDD se crea una vez, no una
  vez por zona.

## 7. El código EMS de los estándares de confort y la sangría

**Por qué.** El autor preguntó si el código EMS de los IDF generados podía tener sangría, para ver dónde empiezan y
terminan los bloques `if`-`elseif`-`else`-`endif`, y qué tal sería añadir solo el código de los estándares de confort
elegidos. Un IDF de salida del modelo de ejemplo con dos zonas en modo mixto tenía 78 programas con 6851 líneas
(645 kB), 5166 de ellas en los subprogramas de los 24 estándares; ahora tiene 34 programas con 1393 líneas (357 kB).

**Sangría.** `ems.programs.indent_lines(líneas)` pone 4 espacios (`INDENTATION`) por cada bloque `IF` o `WHILE` que
contiene la línea; la palabra clave es lo que va antes del primer espacio, como en EnergyPlus. Quita antes los
espacios que tuviera la línea, así que se puede aplicar varias veces. `add_program` y `set_program_lines` sangran lo
que escriben. eppy quita los espacios del principio de los campos al leer un IDF, así que `indent_programs(idf)`
vuelve a sangrar todos los programas y subrutinas de un modelo: lo llaman `AddAccis`, después de leer otra vez el
texto del modelo, y `modify_accis`, porque sus modelos suelen venir de un archivo. EnergyPlus quita los espacios de
cada línea (los mismos resultados con 9.4, 9.6, 25.1 y 26.2), y el intérprete de Erl de accim (`ems/erl.py`) también.

**El código de los estándares de confort.** Dependen del estándar de confort SetComfTemp, SetAppLimits, ApplyCAT y
CountHours_<zona> (cada uno es una cadena `if ComfStand == ... elseif ... else ... endif`), SetAST_Master (un
`if (ComfStand == n)` por estándar, que ejecuta sus subprogramas) y los subprogramas `SetAST_CS<n>_<trozo>`.

- `program_lines.for_comfort_standards(líneas, estándares)` deja las ramas de esos estándares de una cadena: cada
  condición nombra solo los estándares pedidos, y la rama `else` pasa a ser un `elseif` con los estándares pedidos que
  no nombra ninguna condición. Si ninguno tiene rama, no quedan líneas. Da un `ValueError` si las líneas no son una
  cadena sobre `ComfStand`, para que una cadena con otra forma no se recorte mal sin avisar.
- `setast.master_program_lines(estándares)` y `setast.subprograms(estándares)` (antes `comf_stands`) dan
  SetAST_Master y los subprogramas de esos estándares; `setast.subprogram_comfort_standards(idf)`, los estándares
  cuyos subprogramas tiene un modelo.
- `programs.set_comfort_standard_code(idf, estándares)` escribe en un modelo el código de esos estándares (el de todos
  con `None`). Escribe las líneas de SetComfTemp, SetAppLimits, ApplyCAT, CountHours_<zona> y SetAST_Master a partir
  de las de `program_lines` y `setast`, no de las del modelo, para poder volver a añadir estándares; quita todos los
  subprogramas y añade los de esos estándares, al final de los programas. Un programa que no tiene nada que hacer con
  esos estándares (SetComfTemp y ApplyCAT con ESP CTE e INT ISO7730, que no usan ni la temperatura de confort ni los
  desfases de las categorías) queda con una sola línea `return`: EnergyPlus no admite un programa sin líneas
  (`\min-fields 2`), y quitarlo obligaría a quitar también su `run` de RunACCIS_<zona>.
- `AddAccis` llama a `set_comfort_standard_code(idf, zone_comfort_standards(idf))` antes de guardar cada IDF de salida
  (`inputs.zone_comfort_standards` lee `ComfStand` de los programas `SetInputData_<zona>`). Como el mismo modelo sirve
  para todas las combinaciones, la función tiene que poder volver a añadir lo que quitó para la combinación anterior.
- `add_accis_to_idf` no cambia: sus modelos tienen el código de todos los estándares, porque el módulo paramétrico
  cambia `ComfStand` en cada muestra (`param_accis.modify_ComfStand`, en `SetInputData_<zona>`).
- `modify_accis` añade el código de los estándares de las zonas que el modelo no tiene, y no quita nada: un modelo con
  el código de todos los estándares lo sigue teniendo. `param_accis.modify_ComfStand`, que el módulo paramétrico usa en
  cada muestra, hace lo mismo con el estándar que pone (por ejemplo, con un IDF de salida y `bypass_add_accis=True`).
  Las dos usan `programs.add_comfort_standard_code(idf, estándares)`.

**Lo que se pierde.** En un IDF de salida, el estándar de confort ya no se puede cambiar a mano en
`SetInputData_<zona>`: EnergyPlus se para ("used in expression has not been initialized"), porque nada fija las
temperaturas de consigna de un estándar sin su código. Con `modify_accis` sí se puede. La categoría, el modo de
confort y los demás argumentos se pueden seguir cambiando a mano.

**Ver el código antes de añadir el ACCIS** (2026-11-07, a petición del autor: conocer la lógica de las consignas y qué
pasa fuera de los límites de aplicabilidad antes de usar accim). `utils/ems_code.py` (nuevo):
`get_setpoint_ems_code(comfort_standard, category, comfort_mode, ...)` da el código de las consignas como texto, y
`print_setpoint_ems_code(...)` lo imprime; las dos se importan de `accim.utils` y tienen los argumentos de
`modify_accis`, con un valor cada uno. Arma el código con las mismas funciones que escriben los IDF de salida y en el
orden en que lo ejecuta RunACCIS_<zona>: las entradas de las consignas (`input_values`, solo esas, y las del modelo
personalizado con `ComfStand` 99), SetAppLimits, ApplyCAT y SetComfTemp (`for_comfort_standards`, o `return`),
SetAST, SetAST_Master (`master_program_lines`), las consignas del modo de confort con su redondeo
(`get_setpoint_lines`; `setast.subprogram_name`, nuevo, da el subprograma que las tiene) o, sin modo de confort, los
subprogramas enteros, y SetASTnoTol; todo sangrado con `indent_lines`, y con comentarios (`!`) que dicen el estándar,
la categoría, el modo y qué es cada variable. Rechaza con `ValueError` lo que `AddAccis` no genera: un estándar que no
existe, una categoría que no es del estándar y un modo sin consignas.

## 8. Los sistemas HVAC existentes con los archivos de ejemplo de EnergyPlus

**Por qué.** El autor pidió probar `ex_mm` y `ex_ac` con muchos IDF, existentes o modificados, con distintos sistemas
HVAC, para comprobar que funcionan con cualquiera siempre que el modelo original funcione, teniendo en cuenta que en
`ex_mm` la ventilación puede ser por horario o con AirflowNetwork, y que las ventanas deben abrirse y cerrarse cuando
haga falta para trabajar en modo mixto.

**Cómo.** Un script (fuera del repositorio, en la carpeta de la sesión) preparó cada archivo de ejemplo de EnergyPlus
25.1 con personas (631; los 13 más grandes se dejaron fuera): sus archivos externos, tres periodos de simulación en
Sevilla y unas salidas; lo simuló, y si funcionaba, generó con `AddAccis` las variantes `ex_ac`, `ex_mm` (con
ventilación natural añadida a las zonas que no tenían) y las dos con todos los argumentos `existing_hvac_*`, las
simuló y midió los errores, si los termostatos siguen las consignas de accim, el tiempo ocupado dentro de las
consignas y, en modo mixto, si EnergyPlus abre las ventanas que abre el EMS y solo esas. La primera vez (588 modelos
que funcionaban, 10 días por periodo) se probó el código de antes; la segunda, 170 modelos elegidos (los que
fallaron, como mucho dos por tipo de fallo, los de ventilación natural y los que cubren cada tipo de objeto HVAC), con
5 días por periodo, para que tardara menos.

**Las ventanas del modo mixto** (`accim/sim/windows.py`, nuevo; `AccimModel._scan_windows` y `_add_window` en
`model.py`):

- `uses_airflow_network(idf)`: las ventanas son las del AirflowNetwork solo si simula los flujos multizona
  (`MultizoneWithoutDistribution` o `MultizoneWithDistribution`); con `NoMultizoneOrDistribution` (antes se tomaba
  como AirflowNetwork) y `MultizoneWithDistributionOnlyDuringFanOperation`, EnergyPlus simula los objetos
  `ZoneVentilation`.
- `afn_openings(idf, zonas)`: las ventanas, puertas y puertas de vidrio de superficies exteriores
  (`exterior_subsurface_zones`) de las zonas ocupadas cuyo `AirflowNetwork:MultiZone:Surface` tiene una apertura
  (`OPENING_COMPONENTS`), sea cual sea su nombre. Antes solo las de DesignBuilder (`..._Win`, `..._Door`, con la zona
  antes del primer `_`), y las puertas interiores de DesignBuilder se abrían como ventanas.
- `control_ventilation_objects(idf, zonas, horario, log, taken)`: los `ZoneVentilation:WindandStackOpenArea` y los
  `ZoneVentilation:DesignFlowRate` de tipo `Natural` (`is_natural_ventilation`; los ventiladores `Exhaust`, `Intake` y
  `Balanced` no son ventanas) de las zonas ocupadas, también de espacios, ZoneLists y SpaceLists (estos se sustituyen
  por un objeto por zona o espacio); la zona se lee del tercer campo, porque su nombre cambia con la versión (antes,
  `Zone_or_Space_Name`, que no tienen los `DesignFlowRate` ni los IDD antiguos: `BadEPFieldError`). `_take_control`
  les pone el horario de la zona y quita sus límites (`VENTILATION_LIMITS`): el EMS decide cuándo ventilan, y los
  límites dejaban cerradas las ventanas que el EMS abría.
- `release_occupant_ventilation_controls(idf, superficies)` quita los controles de ventilación por ocupantes de las
  ventanas, que anulan el EMS: el campo de la superficie, y el de su zona (`AirflowNetwork:MultiZone:Zone`), que
  EnergyPlus da a todas las ventanas y puertas de la zona sin uno propio, sea cual sea su modo de control (comprobado en
  `AirflowNetwork/src/Solver.cpp` de 25.1): se quita de la zona y se pone en las demás ventanas y puertas de la zona
  (`subsurface_zones`), como las puertas interiores. `remove_hybrid_ventilation_managers(idf)` quita los
  `AvailabilityManager:HybridVentilation` si accim controla ventanas (actúan sobre las ventanas del AirflowNetwork o
  sobre todos los `ZoneVentilation` de las zonas de su bucle de aire, no solo el que nombran), salvo si el
  AirflowNetwork simula la distribución de aire con las ventanas (`simulates_air_distribution_with_windows`): sin ellos
  EnergyPlus se paraba al abrir ventanas con los ventiladores en marcha. `_scan_windows` avisa también de los
  actuadores EMS del modelo sobre las ventanas que controla accim y de `MultizoneWithDistributionOnlyDuringFanOperation`
  (EnergyPlus solo simula los `ZoneVentilation` con los ventiladores parados).
- `_scan_windows` avisa de lo que quita y de las zonas ocupadas sin ventanas; `_add_window` da a cada ventana un nombre
  EMS válido y único (`sanitize_ems_name`; antes `SPACE1-1_Win_OpT` era un nombre EMS inválido y EnergyPlus se paraba).

**El modo mixto en los días de diseño** (`program_lines._DESIGN_DAY_ZONE` y `_DESIGN_DAY_WINDOW`, al final de las
variantes de modo mixto de `ApplyAST_<zona>` y `SetWindowOperation_<ventana>`; `ems.objects.add_design_day_sensor` y
`schedules.add_design_day_schedule`): con el sensor `DesignDay` del horario `ACCIS Design Days` (1 en los días de tipo
`SummerDesignDay` y `WinterDesignDay`), las zonas se climatizan con las ventanas cerradas, haya ocupantes o no. Las
líneas van al final de los programas y no envuelven el cuerpo en otro `IF`, porque EnergyPlus no admite más de 5
niveles de `IF` anidados y el de las ventanas ya tiene 5. Sin esto, con `ex_mm` los sistemas se dimensionaban sin
carga en los días de diseño sin ocupantes (casi siempre el de invierno), y EnergyPlus se paraba. Primero fue solo para
`ex_mm`; después el autor eligió (2026-11-07) la misma regla para `vrf_mm`, así que la función del sensor pasó de
`hvac/existing.py` a `ems/objects.py`, y `build.py` la llama en modo mixto. Con el modelo de ejemplo `TestModel` (sin
ocupantes el día de diseño de invierno) y `vrf_mm`, la carga de calefacción de diseño de sus dos zonas pasa de 0
(EnergyPlus avisaba de ello) a 1,9 y 2,2 kW, y la de refrigeración baja en torno a un 6 % (antes las zonas flotaban
sin ocupantes, y el pico incluía la recuperación al llegar estos), así que sus VRF salen en torno a un 6 % más
pequeños.

**Termostatos** (`model.py`, `hvac/existing.py`):

- `AccimModel._split_zone_list_thermostats` sustituye los termostatos (y los escalonados) de ZoneLists con zonas
  ocupadas por uno por zona (`<zona> <termostato>`), con copias de los objetos que los nombran (`_THERMOSTAT_REFERENCES`)
  y los `DemandManager:Thermostats` actualizados (`_replace_thermostat`). Antes, `ValueError`.
- `AccimModel._check_hvac_templates` para con un `ValueError` si el modelo tiene objetos `HVACTemplate`;
  `AddAccis` los expande antes con `accim.energyplus.expand_objects` (ExpandObjects, con el IDD en su carpeta de
  trabajo, en una carpeta temporal), y `hvac_template_types` los encuentra.
- Con `existing_hvac_operative_temperature_control=True`, `remove_thermal_comfort_thermostats` quita los termostatos
  de confort (PMV de Fanger) de las zonas ocupadas y `set_staged_thermostat_setpoints` da a los escalonados los
  horarios de consigna de su zona; con `False`, `own_thermal_comfort_warning` avisa (en `build.py`).

**Otras correcciones.**

- `ems/objects.py`: `add_global_variables` y `add_internal_variables` añaden las de ACCIS que faltan y dejan las del
  modelo (antes las sustituían, y el EMS del modelo dejaba de funcionar).
- `existing._add_node`: la zona recibe una NodeList de accim (`<zona> ACCIS Inlet Nodes`) con sus nodos y el del
  respaldo, y la NodeList del modelo no cambia (la usaban como nodo los `SetpointManager:SingleZone:*`).
  `add_ideal_loads_backups` no añade respaldos con distribución de aire del AirflowNetwork
  (`_airflow_network_distribution`) ni en las zonas del modelo RoomAir AirflowNetwork.
- `existing.make_available` escribe en el registro `_object_name(obj)` en vez de `obj.Name`, que no tienen los
  `AirConditioner:VariableRefrigerantFlow` (`Heat_Pump_Name`).
- `existing.add_setpoint_schedules` (con `existing_hvac_operative_temperature_control=False`) añade los horarios de
  consigna de todas las zonas ocupadas, como el camino de `True`: el EMS los actúa, y EnergyPlus se paraba con las zonas
  sin termostato o con una sola consigna (`HeatPumpVSAS`).

**Lo que queda del modelo o de EnergyPlus.** EnergyPlus 25.1 y 25.2 se cierran (violación de acceso) con los
archivos de ejemplo `ZoneCoupledKivaConvection*` (Kiva y algoritmo de convección adaptativo, `CalcClearRoof` en un suelo
de Kiva) con el control de la temperatura operativa; con `existing_hvac_operative_temperature_control=False` simulan.
EnergyPlus 25.1 se cierra a veces (3 de cada 5 ejecuciones del mismo archivo) con `HeatPumpVSAS` cuando la fracción
radiante del termostato de temperatura operativa viene de un horario (`Scheduled`, aunque sea siempre 0,5); con
`Constant`, o con EnergyPlus 25.2 (convertido con su programa de transición), nunca: es un error de 25.1, y accim
mantiene su horario `TypOperativeTempControlSch`. Con muchas simulaciones en paralelo, EnergyPlus también se cerró a
veces con archivos que simulan bien solos (memoria). Las zonas sin termostato (los sistemas
unitarios controlados desde otra zona) no siguen las consignas, con un aviso; algunos errores graves que no paran la
simulación aparecen con las consignas de accim (convergencia del precalentamiento, controladores de baterías de agua).
Un `ZoneVentilation:WindandStackOpenArea` no ventila si el viento le llega por detrás y su diferencia de alturas es 0
(EnergyPlus 25.1 le da efectividad 0), aunque el EMS lo abra.

## 9. Pruebas

- Golden master (eppy): 19 configuraciones de `AddAccis`, que leían los modelos con besos, cambiaron solo en la forma
  de escribir los números (2926 campos: `2.0` → `2`, `0.00000001` → `1e-08`, `-0` → `0`...); EnergyPlus da resultados
  idénticos con los IDF de salida de antes y de ahora (`b02`, `b11` y `b17`).
- Golden master (código de los estándares): cambian las 22 configuraciones de `AddAccis`. En sus 424 IDF de salida, un
  script comprobó que los demás objetos son idénticos, que solo se quitan subprogramas de estándares que no usan las
  zonas (18434) y que SetComfTemp, SetAppLimits, ApplyCAT, CountHours_<zona> y SetAST_Master son los de antes
  recortados con `for_comfort_standards`. Las 9 configuraciones de las funciones sobre objetos IDF no cambian (la
  comparación no tiene en cuenta los espacios). EnergyPlus da los mismos resultados (CSV idénticos) con 19 IDF de
    salida de antes y de ahora: 13 del golden master (ESP CTE, CHN, AUS, MEX, INT ISO7730, modo mixto, PMV, sistemas
    existentes, oficina y vivienda de OpenStudio, y tres de 26.2, dos con `People:Instance`), uno de INT EN16798 en
    modo mixto, los dos de una prueba con `zone_arguments` (estándares 0 y 13, 1 y 13), el modelo personalizado con
    coeficientes válidos y los modelos de 9.4 y 9.6. Con los coeficientes por defecto, el modelo personalizado se para
    en el dimensionado, antes y ahora.
- Nuevas: `test_chile_funcs.py`, `test_load_idf_versions.py::test_load_idf_reads_the_models_with_eppy`,
  `test_existing_hvac.py::test_a_limit_of_0_is_not_the_default_of_the_idd` y `test_comfort_standard_code.py`: la
  sangría, las cadenas, y los programas con el código de un estándar, ejecutados con el intérprete de Erl, que dan lo
  mismo que con el de todos para cada estándar, categoría y modo de confort, en 36 pasos de tiempo con RMOT y PMOT
  distintos (la prueba falla si se olvida la rama `else` o si un estándar de PMOT usa la rama de RMOT: comprobado);
  un estándar sin su código para EnergyPlus; dos zonas con estándares distintos; `modify_accis` y `modify_ComfStand`.
- Las pruebas del backend de la API leen sus modelos con eppy (necesitan EnergyPlus 25.1, su IDD), y las de `Table`
  sustituyen `load_idf` en lugar de `get_building` de besos. Las que comparan líneas de programas con bloques las
  comparan sangradas (`indent_lines`).

- Pruebas de los sistemas HVAC existentes y de las ventanas: `test_mixed_mode_windows.py` (nuevo: las ventanas del
  AirflowNetwork por sus superficies, los nombres EMS, `MultizoneWithDistributionOnlyDuringFanOperation`, solo la
  ventilación natural y sin límites, las ZoneLists, los gestores de ventilación híbrida, los controles por ocupantes, y
  dos simulaciones en las que EnergyPlus abre las ventanas que abre el EMS y solo esas: las del AirflowNetwork del modelo
  de ejemplo con PTAC, paso a paso, y las de la vivienda de OpenStudio, cuya primera ventana no ventilaba nunca);
  `test_existing_hvac.py` (los termostatos de ZoneLists, el EMS del modelo, las NodeLists y los casos sin respaldo,
  los VRF con disponibilidad, las plantillas HVAC, los termostatos de confort y escalonados, y una simulación de
  `ex_mm` que dimensiona los generadores de aire caliente (furnaces) de `House-2FurnaceAC-SequentialLoad`); `test_existing_hvac_mixed_mode.py` (los días
  de diseño con el intérprete de Erl). Golden master: cambian las configuraciones de `ex_mm` (los días de diseño), `b13`
  y `b15` (sin los horarios de 1 °C de los límites de la ventilación de la vivienda de OpenStudio) y `b22` (las
  NodeLists del respaldo); nada más, comprobado línea a línea.
- `vrf_mm` en los días de diseño: la prueba de Erl de los días de diseño y una nueva, que comprueba el sensor
  `DesignDay`, su horario y las líneas de los programas, se hacen con `ex_mm` y con `vrf_mm`; las dos fallan con
  `vrf_mm` si se quitan las líneas o el sensor (comprobado). `test_hour_counters.py` da valor al sensor `DesignDay`
  (0), como a los demás sensores. Golden master: cambian las 12 configuraciones de `vrf_mm`, solo con líneas añadidas
  (el sensor, el horario y las líneas de los días de diseño de cada zona y ventana), comprobado línea a línea.
- `test_ems_code.py` (nuevo): el código de las consignas de un estándar, categoría y modo de confort; cada sección es
  la que escriben las funciones de los IDF de salida, y las líneas de cada modo de confort de cada estándar son las de
  su rama en su subprograma; sin categoría ni modo, todos; los estándares estáticos (`return`); las entradas del modelo
  personalizado; los argumentos que no dan consignas.
