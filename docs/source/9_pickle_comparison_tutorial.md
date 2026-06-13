# Tutorial narrativo: comparacion de resultados en pickles

Este tutorial esta pensado para cuando ya tienes resultados de simulacion guardados en `.pkl` y quieres responder preguntas reales de trabajo:

- "Estos dos lotes son el mismo experimento?"
- "Si la bateria no es identica, aun asi puedo compararlos con una referencia razonable?"
- "Como comparo muchos pickles contra uno de referencia sin volverme loco?"
- "Como comparo automaticamente carpetas completas o una lista mixta de rutas, carpetas y patrones glob?"

La idea central de las utilidades nuevas es separar dos niveles de verificacion:

1. **Comparacion estricta**: exige misma bateria de entradas (mismos inputs).
2. **Comparacion flexible (relaxed)**: si la bateria cambia, intenta construir una referencia y comparar resultados por emparejamiento.

---

## 1) Mapa mental rapido

La funcion base es:

```python
from accim.parametric_and_optimisation import compare_simulation_instances
```

Y las funciones de orquestacion son:

```python
from accim.parametric_and_optimisation import (
    compare_latest_pickles_in_folders,
    compare_multiple_pickles_with_reference,
)
```

Si prefieres trabajar con estado y atributos inspeccionables (inputs, outputs,
reference, attrs), usa la clase:

```python
from accim.parametric_and_optimisation import SimulationComparisonSession

session = SimulationComparisonSession(
    inputs_mismatch_strategy="auto",
    equal_mode="relaxed",
    compare_attrs=False,
)
```

Ademas, cualquier instancia de simulacion expone:

```python
report = sim_a.compare_with(sim_b)
```

Con `SimulationComparisonSession`, despues de comparar puedes inspeccionar:

```python
session.last_inputs
session.last_outputs
session.last_reference
session.last_attrs
session.history
```

---

## 2) Primer caso: dos resultados, comparacion directa

Supongamos que tienes dos resultados guardados:

```python
from accim.parametric_and_optimisation import compare_simulation_instances

report = compare_simulation_instances(
    left=r"D:\\Python\\accim\\results_a\\outputs_param_simulation_20260611_110242.pkl",
    right=r"D:\\Python\\accim\\results_b\\outputs_param_simulation_20260611_111030.pkl",
)

print("equal:", report["equal"])
print("equal_strict:", report["equal_strict"])
print("equal_relaxed:", report["equal_relaxed"])
```

### Que hace internamente

- Carga ambos datos (desde instancia, DataFrame o archivo).
- Intenta inferir columnas de entrada (`parameters_names` + `epw`/`idf`) y de salida (`outputs_names`).
- Compara outputs alineando por inputs.
- Si la bateria no coincide, puede activar una comparacion de referencia (`report["reference"]`).

---

## 3) Entender `equal`, `equal_strict` y `equal_relaxed`

La funcion devuelve tres banderas importantes:

- `equal_strict`: mismo set de inputs + outputs equivalentes.
- `equal_relaxed`: permite bateria distinta **si** el emparejamiento de referencia demuestra equivalencia.
- `equal`: depende de `equal_mode`.

Por defecto:

```python
equal_mode="strict"
```

Si quieres una lectura flexible:

```python
report = compare_simulation_instances(
    left="a.pkl",
    right="b.pkl",
    equal_mode="relaxed",
)
print(report["equal"])
```

---

## 4) Argumentos clave de `compare_simulation_instances`

## Fuentes de datos

`left` y `right` aceptan:

- instancia `ParametricSimulation` o `OptimisationSimulation`
- `pandas.DataFrame`
- ruta a `.pkl`, `.pickle`, `.csv` o `.json`

## Control de columnas

- `input_columns`: columnas usadas como llave de comparacion.
- `output_columns`: columnas que se evaluan como resultados.
- `ignore_columns`: columnas que se ignoran (por defecto ya ignora rutas de salida de simulacion).

Ejemplo explicitando columnas:

```python
report = compare_simulation_instances(
    left="a.pkl",
    right="b.pkl",
    input_columns=["ComfStand", "VentCtrl", "epw", "idf"],
    output_columns=["HVAC energy", "Discomfort hours"],
)
```

## Metadatos (`attrs`)

- `compare_attrs=True` compara `DataFrame.attrs`.
- `ignore_attr_keys` permite excluir claves de metadatos.

```python
report = compare_simulation_instances(
    left="a.pkl",
    right="b.pkl",
    compare_attrs=True,
    ignore_attr_keys=["idf_backup_path", "timestamp"],
)
```

## Tolerancias numericas

- `numeric_atol` (absoluta)
- `numeric_rtol` (relativa)

```python
report = compare_simulation_instances(
    left="a.pkl",
    right="b.pkl",
    numeric_atol=1e-4,
    numeric_rtol=1e-3,
)
```

## Flexibilidad cuando cambia la bateria

- `inputs_mismatch_strategy`: `"strict" | "auto" | "nearest" | "row_order"`
- `reference_columns`: columnas para emparejamiento por referencia
- `reference_max_distance`: umbral maximo de distancia normalizada (solo `nearest`)
- `equal_mode`: `"strict" | "relaxed"`

---

## 5) Estrategias de mismatch: cuando no hay misma bateria

Este es el punto mas importante.

### `inputs_mismatch_strategy="strict"`

No intenta emparejar filas no comunes.

```python
report = compare_simulation_instances(
    left="a.pkl",
    right="b.pkl",
    inputs_mismatch_strategy="strict",
    equal_mode="strict",
)
```

### `inputs_mismatch_strategy="auto"` (recomendado)

- Si hay columnas de referencia utiles, usa `nearest`.
- Si no, cae a `row_order`.

```python
report = compare_simulation_instances(
    left="a.pkl",
    right="b.pkl",
    inputs_mismatch_strategy="auto",
    equal_mode="relaxed",
)
```

### `inputs_mismatch_strategy="nearest"`

Empareja filas no comunes por distancia en `reference_columns`.

```python
report = compare_simulation_instances(
    left="a.pkl",
    right="b.pkl",
    inputs_mismatch_strategy="nearest",
    reference_columns=["ComfStand", "CAT", "VentCtrl"],
    reference_max_distance=0.35,
    equal_mode="relaxed",
)
```

### `inputs_mismatch_strategy="row_order"`

Empareja por orden determinista. Util para comparaciones de lotes secuenciales.

```python
report = compare_simulation_instances(
    left="a.pkl",
    right="b.pkl",
    inputs_mismatch_strategy="row_order",
    equal_mode="relaxed",
)
```

---

## 6) Leer el bloque `report["reference"]`

Cuando las baterias no son identicas, aqui esta la evidencia del emparejamiento flexible.

Campos utiles:

- `enabled`
- `strategy_used`
- `reference_columns_used`
- `left_unmatched_rows`, `right_unmatched_rows`
- `pairs_compared`
- `unpaired_left_count`, `unpaired_right_count`
- `column_mismatch_counts`
- `mismatched_pairs_count`
- `mismatched_pairs_examples`
- `all_pairs_equal`
- `notes`

Ejemplo de inspeccion:

```python
ref = report["reference"]
print("strategy:", ref["strategy_used"])
print("pairs:", ref["pairs_compared"])
print("all_pairs_equal:", ref["all_pairs_equal"])
print("notes:", ref["notes"])
```

---

## 7) Comparar el ultimo pickle de dos carpetas

Ideal para pipelines donde cada corrida guarda un archivo timestamped.

```python
from accim.parametric_and_optimisation import compare_latest_pickles_in_folders

report = compare_latest_pickles_in_folders(
    left_dir=r"D:\\Python\\accim\\param_results_A",
    right_dir=r"D:\\Python\\accim\\param_results_B",
    glob_pattern="*.pkl",
    recursive=False,
    inputs_mismatch_strategy="auto",
    equal_mode="relaxed",
)

print(report["left_latest_pickle"])
print(report["right_latest_pickle"])
print(report["comparison"]["equal"])
```

---

## 8) Comparar multiples pickles contra referencia

Esta funcion soporta varias formas de seleccionar archivos.

```python
from accim.parametric_and_optimisation import compare_multiple_pickles_with_reference
```

### Caso A: lista explicita

```python
report = compare_multiple_pickles_with_reference(
    pickle_paths=[
        r"D:\\Python\\accim\\r1.pkl",
        r"D:\\Python\\accim\\r2.pkl",
        r"D:\\Python\\accim\\r3.pkl",
    ],
    reference=r"D:\\Python\\accim\\r1.pkl",
)
```

### Caso B: alias `pickle_list`

```python
report = compare_multiple_pickles_with_reference(
    pickle_list=["r1.pkl", "r2.pkl", "r3.pkl"],
    reference="r1.pkl",
)
```

### Caso C: escaneo de carpeta

```python
report = compare_multiple_pickles_with_reference(
    directory=r"D:\\Python\\accim\\batch_results",
    glob_pattern="*.pkl",
    recursive=True,
    reference=0,          # indice en la lista ordenada
    order_by="mtime",    # o "name"
    descending=True,
)
```

### Caso D: lista mixta (archivos + carpetas + glob)

```python
report = compare_multiple_pickles_with_reference(
    pickle_sources=[
        r"D:\\Python\\accim\\single\\reference.pkl",  # archivo
        r"D:\\Python\\accim\\batch_A",                  # carpeta
        r"D:\\Python\\accim\\batch_B\\*.pkl",         # patron glob
    ],
    reference="reference.pkl",  # tambien vale ruta completa o indice
    inputs_mismatch_strategy="auto",
    reference_columns=["ComfStand", "CAT", "epw"],
    equal_mode="relaxed",
)
```

### Resultado agregado

```python
print("total:", report["total_pickles"])
print("comparados:", report["compared_pickles_count"])
print("iguales:", report["equal_count"])
print("diferentes:", report["different_count"])
print("equal_all:", report["equal_all"])
```

Cada entrada en `report["comparisons"]` trae el `comparison` completo de bajo nivel.

---

## 9) Uso desde instancias (`compare_with`)

Si ya tienes objetos en memoria:

```python
report = sim_a.compare_with(
    sim_b,
    inputs_mismatch_strategy="auto",
    reference_columns=["ComfStand", "epw"],
    equal_mode="relaxed",
)

print(report["equal"], report["equal_strict"], report["equal_relaxed"])
```

Tambien puedes comparar instancia contra archivo:

```python
report = sim_a.compare_with(
    r"D:\\Python\\accim\\old_results\\outputs_param_simulation_20260601_100000.pkl",
    equal_mode="strict",
)
```

---

## 10) Patron recomendado de trabajo en proyectos reales

En practico, este flujo suele ser el mas robusto:

1. Primero ejecuta comparacion **estricta**.
2. Si falla por bateria distinta, activa comparacion **relaxed** con referencia.
3. Revisa `report["reference"]["notes"]` y `mismatched_pairs_examples`.
4. Solo marca equivalencia final si el criterio tecnico de tu estudio lo permite.

Ejemplo completo:

```python
strict_report = compare_simulation_instances(
    left="run_old.pkl",
    right="run_new.pkl",
    equal_mode="strict",
)

if strict_report["equal"]:
    print("Comparacion estricta OK")
else:
    relaxed_report = compare_simulation_instances(
        left="run_old.pkl",
        right="run_new.pkl",
        inputs_mismatch_strategy="auto",
        reference_columns=["ComfStand", "CAT", "VentCtrl"],
        equal_mode="relaxed",
    )
    print("strict:", relaxed_report["equal_strict"])
    print("relaxed:", relaxed_report["equal_relaxed"])
    print("notes:", relaxed_report["reference"]["notes"])
```

---

## 11) Checklist de diagnostico rapido

Si algo no cuadra, revisa en este orden:

1. `schema.columns_only_left` / `schema.columns_only_right`
2. `inputs.same_input_set`
3. `outputs.mismatched_rows_count`
4. `reference.strategy_used` y `reference.mismatched_pairs_count`
5. `attrs.equal`
6. `settings` (tolerancias, modo de igualdad, estrategia)

---

## 12) Cierre

Con este conjunto de funciones puedes cubrir desde comparaciones simples 1-a-1 hasta validacion de lotes grandes con bateria no identica.

- Usa **strict** cuando necesites reproducibilidad exacta.
- Usa **relaxed** cuando necesites equivalencia funcional con referencia.
- Usa `pickle_sources` para construir inventarios flexibles sin preparar listas manuales.

Si quieres, el siguiente paso natural es definir un criterio de aprobacion de negocio (por ejemplo, tolerancias por KPI) y automatizar un informe final tipo "PASS/FAIL" por lote.

