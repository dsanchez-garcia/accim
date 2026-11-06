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

**Lo que no cambia.** El uso, los argumentos, los programas EMS y los objetos y valores de los IDF de salida.

**Lo que cambia.**

- Lectura: `load_idf` lee todos los modelos con eppy, también con `energyplus_version='auto'` (antes, con besos).
- Escritura: eppy guarda cada IDF de salida entero (`IDF.savecopy`). Es más lento que el `IdfWriter` de 1.0.0, que
  escribía una sola vez el texto de los objetos que no cambian: AddAccis con los 140 IDF de salida del modelo de
  ejemplo tarda unos 17 s en vez de unos 6 s.
- Edición: `getobject`, `removeallidfobjects`, `fieldvalues`... en vez de listas de nombres y de `.obj`.
- Algunos números del modelo de entrada se escriben como los escribe eppy (`2.0` como `2`), con los mismos valores:
  eppy lee los campos numéricos como números y besos los dejaba como texto.
- El backend de la API de Python lee y cambia el modelo con eppy, en vez de con un analizador de texto propio.

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
3. `_write_output_idfs`: eppy lee ese texto (`IDF(StringIO(texto))`) y, para cada combinación,
   `generation.set_combination` escribe los argumentos de cada zona en su programa `SetInputData_<zona>` (los de la
   combinación, o los de `zone_arguments`) y `idf.savecopy(ruta)` guarda el IDF de salida.
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

## 7. Pruebas

- Golden master: 19 configuraciones de `AddAccis`, que leían los modelos con besos, cambian solo en la forma de
  escribir los números (2926 campos: `2.0` → `2`, `0.00000001` → `1e-08`, `-0` → `0`...); EnergyPlus da resultados
  idénticos con los IDF de salida de antes y de ahora (`b02`, `b11` y `b17`). Los archivos se escribieron de nuevo.
- Nuevas: `test_chile_funcs.py`, `test_load_idf_versions.py::test_load_idf_reads_the_models_with_eppy` y
  `test_existing_hvac.py::test_a_limit_of_0_is_not_the_default_of_the_idd`.
- Las pruebas del backend de la API leen sus modelos con eppy (necesitan EnergyPlus 25.1, su IDD), y las de `Table`
  sustituyen `load_idf` en lugar de `get_building` de besos.
