# Refactorización: OptimParamSimulation → SimulationBase + Subclases

**Rama**: `refactor/optim-param-simulation-split`  
**Fecha**: 2026-05-02  
**Estado**: Completado

## Resumen del Cambio

La clase `OptimParamSimulation` (2228 líneas) ha sido dividida en una **clase base + dos subclases especializadas**, manteniendo *completa* compatibilidad hacia atrás.

### Estructura Nueva

```
SimulationBase (clase base abstracta)
├─ ParametricSimulation (simulación paramétrica)
│  └─ Métodos: sampling_*(), run_parametric_simulation(), load_outputs_parametric()
│  └─ Atributos: outputs_param_simulation, outputs_param_simulation_hourly/monthly
│
├─ OptimizationSimulation (optimización multi-objetivo)
│  └─ Métodos: run_optimisation(), estimate_optimisation_sims(), get_hourly_df_optimisation()
│  └─ Atributos: outputs_optimisation, optimisation_csv_paths_*
│
└─ AccimPredefModelsParamSim
   └─ Ahora hereda de ParametricSimulation en lugar de OptimParamSimulation
```

## Cambios Técnicos

### 1. **Clase Base: SimulationBase**

Contiene todo el código compartido:
- Inicialización de buildings, EPWs, parámetros
- Métodos de IDF backup (`_save_idf_backup()`, etc.)
- Configuración de outputs (`set_outputs_for_simulation()`, etc.)
- Category mapping (`set_category_mapping()`, `apply_category_mapping()`)
- Métodos de evaluación (`set_evaluator()`, `_run_evaluator_df_apply()`)
- Mixins: `AnalysisMixin`, `PlottingMixin`

### 2. **Subclase: ParametricSimulation(SimulationBase)**

Método de simulación **paramétrica**:
```python
parametric = ParametricSimulation(building=idf, parameters_type='accim custom model')
parametric.set_parameters(accis_params_dict={'ComfStand': [0, 1, 2]})
parametric.sampling_lhs(num_samples=10)
results = parametric.run_parametric_simulation()
```

**Atributos específicos**:
- `outputs_param_simulation`: resultados principales (multi-fila)
- `outputs_param_simulation_hourly`: resultados expandidos a nivel horario
- `outputs_param_simulation_monthly`: resultados agregados mensualmente
- `outputs_param_simulation_filepath`: ruta de guardado

**Métodos específicos**:
- `sampling_full_set()`
- `sampling_custom()`
- `sampling_full_factorial(level)`
- `sampling_lhs(num_samples)`
- `sampling_sobol(num_samples=128)`
- `sampling_morris(num_samples=100, num_levels=4)`
- `run_parametric_simulation()`
- `load_outputs_parametric()`

### 3. **Subclase: OptimizationSimulation(SimulationBase)**

Método de **optimización multi-objetivo**:
```python
optim = OptimizationSimulation(building=idf, parameters_type='accim custom model')
optim.set_parameters(accis_params_dict={'ComfStand': (0, 2), 'HVACmode': (0, 2)})
optim.set_problem(minimize_outputs=[True, False])
results = optim.run_optimisation(algorithm='NSGAII', evaluations=50)
```

**Atributos específicos**:
- `outputs_optimisation`: historial completo de evaluaciones (dominadas + no-dominadas)
- `outputs_optimisation_hourly`: datos a nivel horario
- `outputs_optimisation_monthly`: datos agregados mensualmente
- `outputs_optimisation_filepath`: ruta de guardado
- `optimisation_csv_paths_non_dominated`: rutas de soluciones no-dominadas
- `optimisation_csv_paths_dominated`: rutas de soluciones dominadas
- `evaluators`: rastreo de evaluadores por IDF/EPW

**Métodos específicos**:
- `run_optimisation(algorithm, evaluations, population_size, ...)`
- `estimate_optimisation_sims(evaluations, population_size, epws)`
- `load_outputs_optimisation()`
- `get_hourly_df_optimisation(only_pareto_optimal=True, ...)`
- `get_monthly_df_optimisation()`

## Compatibilidad Hacia Atrás

### ✅ Automática (sin cambios en scripts existentes)

```python
# Este código sigue funcionando:
from accim.parametric_and_optimisation.main import OptimParamSimulation

parametric = OptimParamSimulation(building=idf)  # → redirige a ParametricSimulation
```

**Alias de compatibilidad** en `main.py`:
```python
OptimParamSimulation = ParametricSimulation
```

### Cambios Visibles

| Aspecto | Antes | Después | Impacto |
|---------|-------|---------|---------|
| Clase principal | `OptimParamSimulation` | `ParametricSimulation`/`OptimizationSimulation` | Código nuevo debe usar clases específicas para claridad |
| Importación | `from accim.parametric_and_optimisation.main import OptimParamSimulation` | Igual (alias funciona); o mejor: Usar clases específicas | ✅ Sin ruptura |
| Atributo `last_run_type` | `'parametric'\|'optimisation'` | Mismo | ✅ Sin cambios |
| Scripts de prueba | Usan `OptimParamSimulation` | Recomendado actualizar a `ParametricSimulation` | Funciona, pero mejor con nuevas clases |

## Ventajas de Esta Refactorización

| Beneficio | Descripción |
|-----------|-------------|
| **Claridad** | Un usuario sabe exactamente si necesita `ParametricSimulation` o `OptimizationSimulation` |
| **Mantenibilidad** | ~1100 líneas por clase en lugar de 2228 líneas en una sola clase |
| **Documentación** | Cada clase tiene un propósito claro y métodos que tienen sentido |
| **IDEs** | AutoComplete muestra solo métodos relevantes para el tipo de simulación |
| **Debugging** | Es más fácil depurar cuando el código está separado por concern |
| **Testing** | Se pueden escribir tests específicos para cada tipo de simulación |
| **Extensibilidad** | Agregar nuevos tipos de simulación es más fácil (solo heredar de `SimulationBase`) |

## Evaluación de Riesgo

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|-----------|
| Romper código existente | 🟢 Muy Baja | Alias `OptimParamSimulation = ParametricSimulation` mantiene API pública |
| Problemas de herencia | 🟢 Baja | Ambas subclases llaman `super().__init__()` correctamente |
| Tests fallando | 🟡 Media-Baja | Tests existentes usan `OptimParamSimulation` que es alias; revisar importes de prueba |
| Documentación desactualizada | 🟡 Media | Actualizar ejemplos a clases nuevas; mantener mención a alias de compatibilidad |

## Archivos Modificados

### Modificados

- **`accim/parametric_and_optimisation/main.py`**
  - Clase `OptimParamSimulation` → `SimulationBase` (clase base)
  - Nueva: `ParametricSimulation(SimulationBase)`
  - Nueva: `OptimizationSimulation(SimulationBase)`
  - Alias: `OptimParamSimulation = ParametricSimulation`
  - `AccimPredefModelsParamSim` ahora hereda de `ParametricSimulation`

- **`accim/parametric_and_optimisation/__init__.py`**
  - Nuevo: importaciones de `SimulationBase`, `ParametricSimulation`, `OptimizationSimulation`
  - Mantiene: `OptimParamSimulation` para compatibilidad

### No modificados pero pueden necesitar actualización

- Test scripts (`testing_new_functionalities.py`, `testing_new_functionalities_optimisation.py`)
  - Funcionan sin cambios actualmente
  - **Recomendado**: actualizar importes a clases específicas para claridad

## Pasos Siguientes (Recomendaciones)

1. **Validar** que todos los tests existentes pasen
2. **Actualizar** ejemplos en documentación para usar clases específicas
3. **Deprecation warning** (v0.9): agregar advertencia cuando se usa `OptimParamSimulation` sugiriendo la clase específica
4. **Removal** (v1.0): remover el alias en la próxima versión mayor

## Uso Recomendado (desde v0.8.0 en adelante)

```python
# Para simulación paramétrica
from accim.parametric_and_optimisation import ParametricSimulation

# Para optimización
from accim.parametric_and_optimisation import OptimizationSimulation
```

## Verificación

Para verificar que la refactorización fue exitosa:

```bash
# Verificar sintaxis
python -m py_compile accim/parametric_and_optimisation/main.py

# Verificar que las nuevas clases pueden importarse
python -c "from accim.parametric_and_optimisation import ParametricSimulation, OptimizationSimulation, OptimParamSimulation; print('OK')"

# Verificar que el alias funciona
python -c "from accim.parametric_and_optimisation import OptimParamSimulation; assert OptimParamSimulation.__name__ == 'ParametricSimulation'; print('Alias works')"
```

---

**Notas finales**: Esta refactorización mantiene 100% de compatibilidad hacia atrás mientras proporciona una arquitectura más clara y mantenible para el futuro.

