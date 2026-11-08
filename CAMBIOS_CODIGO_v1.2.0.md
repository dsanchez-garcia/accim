# Cómo ha cambiado el código de accim en la versión 1.2.0

Guía de los cambios del código de la rama `v1.2.0` respecto a accim 1.1.0, para quien mantiene accim; no es
documentación de uso. Recoge las propuestas del bloque A de `notes/PROPUESTAS_MEJORAS_post_1.1.0_v01.md` (índices de
confort derivados del PMV) que el autor pidió para esta versión: las P1, A2, A1 y A5, en este orden.

Lo que ya está en otros documentos no se repite aquí:

- `CHANGELOG.md` (sección Unreleased): los cambios que ve el usuario.
- `docs/source/4_detailed use.md`, sección 4.8: el uso.
- `DEVLOG.md`: el registro del trabajo, con cómo se comprobó.
- `notes/decisions.md`: las decisiones y sus motivos.

## 1. En resumen

- **A2.** Las consignas basadas en el PMV comparten un motor, `accim.sim.pmv_index`: `apply_apmv_setpoints` llama a
  `apply_pmv_index_setpoints(index='apmv')`, y la nueva `apply_pmv_setpoints`, a `apply_pmv_index_setpoints(index='pmv')`.
  Los IDF del aPMV no cambian (sección 2).

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
  la rama); con los modelos de `AddAccis`, los CSV son idénticos. No se ha buscado la causa dentro de EnergyPlus. La
  sección 4.9 lo dice.

## 3. Pruebas

- `tests/core/test_pmv_index.py` (nuevo): el registro y los parámetros de los índices; `apply_apmv_setpoints` escribe
  el mismo modelo que el motor; los objetos EMS de las consignas PMV; las consignas PMV son las del aPMV con
  coeficientes 0 (los programas ejecutados con el intérprete Erl de accim, en las dos estaciones, con y sin ocupantes);
  dos índices en un modelo; los modificadores del paramétrico; y tres días de julio con los dos backends de
  EnergyPlus 25.1.
- El golden master (`s07` y `s08`) comprueba que los IDF del aPMV no cambian.
