# Traspaso de la sesión de Claude Science del 11/11/2026 — revisión de la 2.ª sesión de Copilot (accim v1.2.0)

- Para: la próxima sesión de Claude Science (otro PC). Autor del repositorio: Daniel Sánchez-García.
- Estado del repositorio al escribir esto: rama `v1.2.0`, local = `origin/v1.2.0` en `47d0b486` más el commit de este archivo.
- Objetivo pendiente: (1) terminar la revisión de los 17 commits de la 2.ª sesión autónoma de Copilot; (2) escribir `notes/PROPUESTAS_MEJORAS_post_1.1.0_v05.md`; (3) dar al autor el prompt único de la siguiente sesión de Copilot.
- Regla: no modificar código del repositorio; sólo documentos en `notes/` (commit y push de los documentos).
- Etiquetas: **[verificado]** comprobado en fuente o código en esta sesión; **[del informe]** tomado del informe de Copilot sin volver a comprobar; **[preliminar]** veredicto pendiente de la revisión.

---

## 1. Qué hizo Copilot en la 2.ª sesión (10–11/11/2026)

Tareas de la v04 §7, un commit y push cada una **[verificado: `git log`]**:

| Tarea | Commit | Tarea | Commit |
|---|---|---|---|
| Step 0 (36 veredictos a `decisions.md`, TODO desbloqueado, decisión `tr_mode`) | `8c637029` | E-F1 (SET Pierce de EnergyPlus vs `set_tmp`) | `9a496aec` |
| G1 (ganchos → contadores y salidas del ACCIS) | `72ed578f` | F1 (ComfStand 24 INT Sun2026 SET) | `e376a1ae` |
| G2 (rama de enero del PMOT de EnergyPlus) | `33a5a581` | F2 (limitador de deriva) | `43de97a4` |
| G3 (SET por bisección en los *callbacks*, salidas, postura) | `e51e6421` | F3 (indicadores de adaptación interior) | `590461bb` |
| G4 (Aqilah 2025 con el EPW; estáticas como argumentos) | `6109cc16` | H2 (`T0` de `te_ref_nl` diario desde el EPW) | `60d37a50` |
| G5 (saneamiento: besos, `processes=0`, A3, B5, B1, Qatar, E4, docs) | `40eb001e` | H3 (`long_term_range`, método C, `Table` por paso) | `2b3c50ff` |
| H1 (`heating_setpoint_minimum`/`cooling_setpoint_maximum`) | `4e48ca4b` | H4 (saturación ATHB, frecuencias, rangos, test acotado) | `6f61692f` |
| H5 (métrica por régimen; regímenes en YAML) | `90fdddc6` | H6 (`clothing_insulation=callable`) | `7ddd4469` |
| Informe | `47d0b486` | | |

Resumen del propio Copilot **[del informe]**: `tests/core` 1520 pasados y 2 saltados (EnergyPlus 26.1 y jar del FWG); paramétrico 518 pasados; *golden master* idéntico salvo G4, que reescribió a propósito 7 archivos *golden* (los modelos de `add_accis_to_idf` ganan las estáticas del 23); documentación con los mismos 35 avisos; el mensaje del commit de G5 empieza con un BOM. Informe completo: `notes/INFORME_SESION_v1.2.0_2026-11-10_2.md`. Pendiente del autor: **23 decisiones provisionales** en `notes/questions.md`; bloqueados: CIBSE TM52/TM59, cuaderno/test del FWG (falta el jar), estudio de validación de F3; arrastrado: ComfStand 9 y 10.

## 2. Comprobaciones hechas en esta sesión **[verificado]**

### 2.1 ComfStand 9 y 10 (IND IMAC R 7DRM / 30DRM)
- Fuente: Rawal et al. (2022), *Building and Environment* 219, 109187 (PDF en la biblioteca, `Rawal et al._2022_Adaptive thermal comfort model based on field studie…`), Fig. 15, p. 14: modelo A `Tneut = 0.39·Tout-7DRM + 18.42` (R² 0.51, p < 0.001); modelo B `Tneut = 0.42·Tout-30DRM + 17.60` (R² 0.54); bandas 90 % ±2.15 °C y 80 % ±3.60 °C (ΔTSV 0.5 y 0.85); aplicables a `Tout-7DRM` y `Tout-30DRM` entre 5.5 y 33 °C (§4.4), viviendas NV o MM. La nomenclatura distingue `Tout-7DRM` ("7-day running mean Tout") de `Tout-7DRM-W` ("Weighted Tout-7DRM"): la del modelo A es la **media simple** de 7 días.
- accim: pendientes e intercepts (0.39/18.42, 0.42/17.6), offsets de `ApplyCAT` (±2.15/±3.6) y `SetAppLimits` (5.5–33) **correctos** (la v03 redondeaba 18.42 a 18.4 al citar Aqilah 2025 Tabla 1; el código tiene razón).
- **Error: las métricas están intercambiadas.** El 9 usa `PMOT` (media simple de 30 días de EnergyPlus, Eng. Ref. 19.70) y el 10 usa `RMOT` (exponencial α 0.8 de 7 días, Eng. Ref. 19.82–19.84). Recomendación: 10 → `PMOT` (coincide exactamente con el 30DRM); 9 → media aritmética de 7 días con la maquinaria de B1 (`'ndrm'`, 7 días, inicializada desde el EPW; sin EPW, el arranque de B1). `SetComfTemp`, las consignas y `CountHours` coherentes; *golden* actualizado; CHANGELOG *Fixed*; nota de migración (los resultados publicados con accim ≤ 1.1.0 se reproducen con esas versiones). **Decisión del autor** (cambia resultados de 9 y 10).
- **Error de signo en ComfStand 9, *comfort mode* 1**, fuera de aplicabilidad: `AHST = PMOT*0.078+23.25+2.72+AHSTtol` (80) y `+1.5` (90), iguales a las de refrigeración; el *comfort mode* 0 del 9 y el 1 del 10 usan `−`. Corregir a `−`.
- La ecuación estática `0.078·T + 23.25` con ±1.5/±2.11/±2.72 (90/85/80) **no se ha podido verificar**: no está en Manu et al. (2016), doi:10.1016/j.buildenv.2015.12.019 (texto legible; buscados 0.078, 23.25 y 2.72, sin resultados). Probablemente procede del National Building Code of India 2016 (edificios con AC), que no está en la biblioteca. Con las métricas corregidas, comprobar en esa fuente con qué media exterior se define (en el 10 la línea estática usa hoy `RMOT`).

### 2.2 Dos errores de la v04 que Copilot aplicó literalmente
- **Veredicto #13** ("aviso si el suelo supera `ACSTaul` o el techo baja de `AHSTall`"): `ACSTaul`/`AHSTall` son límites de aplicabilidad de la **métrica exterior**, no consignas; comparar con ellos un suelo de consigna interior no tiene sentido. Corrección: quitar ese aviso y sustituirlo por la opción (ii) de `questions.md` (consignas extremas del modelo sobre el rango de la métrica con `compute_setpoints` cuando `AddAccis` recibe EPW) o la (iii) (`@WarnEP` en tiempo de ejecución si `AHST > ACST`; cambia IDF).
- **Estáticas de Qatar** (v04 §6.3: 20/25.5 °C "EN 16798-1 Tabla B.2 oficinas cat. II"): la Tabla B.2 da para oficinas cat. II 20.0/26.0 °C; 25.5 es la cat. I. Corregir a 20/26 °C.

### 2.3 SET de Sun, Brager & Schiavon (2026)
*Energy and Buildings* 370, 118097 (PDF en *Mendeley pendiente 2*, `S0378778826011576-…pdf`): el texto **no dice qué implementación del SET usaron** (buscados "pythermalcomfort", "Gagge", "two-node", "calculated/computed"; sin resultados). Es una **pregunta para Ruiji Sun**. Hasta tener respuesta, F3 puede mantener el SET Pierce de EnergyPlus, pero debería informar también el de pythermalcomfort recalculado (`set_of_results`), porque E-F1 midió diferencias de −0.045 K de media y 0.18–0.20 K como máximo de pie, y −0.12 K y 0.32–0.34 K sentado **[del informe]**, del orden de lo que mueve las horas cerca de los bordes de la banda 19–28 °C.

## 3. Veredictos preliminares sobre las 23 decisiones provisionales de `notes/questions.md` **[preliminar]**

| # | Decisión (título de `questions.md`) | Veredicto preliminar | Motivo / instrucción |
|---|---|---|---|
| 1 | H6: temperatura exterior de las funciones de vestimenta y sus CSV | Aceptar | Añadir a la documentación un ejemplo con la columna `'Tout'` para modelos en función de la temperatura de las 6:00 (Schiavon & Lee 2013, ec. 4; ASHRAE 55-2020 Fig. 5-1). |
| 2 | H5: esquema de `regimes` en los YAML | Aceptar | Un estándar de confort no debe depender del tipo de script (HVAC). |
| 3 | H5: código EMS de un estándar con regímenes | Aceptar | — |
| 4 | H5: métrica de un régimen en las salidas y programas conservados | Aceptar | — |
| 5 | H3: tipo de edificio de `long_term_range` en categorías III y IV | Aceptar | No elige límites por el usuario. |
| 6 | H3: rango del método C en la escala del PMV y su salida | Aceptar | Coherente con cómo reciben los termostatos sus consignas PMV. |
| 7 | H2: carpeta del CSV de `T0` | Aceptar con nota | Documentar que la ruta absoluta se rompe si el IDF se simula en otra máquina; modo relativo opcional en el futuro. |
| 8 | H2: qué modelos llevan el `Schedule:File` | Aceptar | — |
| 9 | F3: SET de los indicadores de la banda causal | **Pendiente (pregunta a Sun, §2.3)** | Mantener Pierce e informar además el SET de pythermalcomfort. |
| 10 | F3: definición del sobreenfriamiento | Aceptar | — |
| 11 | F3: `T_rm_in` y banda de `Tn_exp` (2.5 K) | Aceptar | Mantener la marca de "inferido". |
| 12 | F3: referencia estática del caso (i) | **Decisión del autor con Sun** | Recomendación: (a) `apply_pmv_setpoints` cat. II (±0.5) como referencia de "PMV fijo" (pregunta 1 de `01_informe/propuesta_paper_RuijiSun_v02.md` de la carpeta *Indoor adaptive setpoints*); (b) además, estáticas fijas de EN 16798-1 Tabla B.2 cat. II (oficinas 20/26 °C). |
| 13 | F2: consigna "aplicada el día anterior" del modo `rate` | **Cambiar** | Usar la media de las consignas aplicadas en los pasos ocupados del día anterior: idéntica para consignas constantes en el día (ACCIS), más representativa para las de los ganchos, que varían dentro del día. |
| 14 | F2: días sin horas ocupadas en `T_rm_in` | Aceptar | Sin exposición, sin cambio. |
| 15 | F2: `drift_mode` 0/1/2 en el paramétrico | Aceptar | — |
| 16 | F1: números de los *comfort modes* del 24 | Aceptar | Comprobar que los modos 0 y 3 del 24 dan un error claro. |
| 17 | F1: límites "CustAST" del prompt | Aceptar | El modelo de Sun no tiene límites de aplicabilidad exteriores. |
| 18 | F1: vestimenta del modelo dinámico en el gancho | Aceptar | — |
| 19 | G5: aviso del veredicto #13 con `ACSTaul`/`AHSTall` | **Cambiar** | Error de la v04 (§2.2). |
| 20 | G5: estáticas del YAML de Qatar (20/25.5) | **Cambiar a 20/26** | Error de la v04 (§2.2). |
| 21 | G5: mínimo exacto tras el redondeo | Aceptar | Simetría con el máximo. |
| 22 | G4: criterio del test 23 vs 101 | Aceptar | Documentar el retraso de un día del RMOT nativo en el primer paso de cada día (afecta también al ComfStand 1). |
| 23 | G1: tolerancia con las consignas de los ganchos | Aceptar | Mismo significado que las consignas adaptativas (`noTol` = límite de la banda). |

## 4. Recomendaciones para lo bloqueado y lo arrastrado
- **CIBSE TM52/TM59**: sacarlos del alcance de la 1.2.0 (a `ROADMAP.md`); el CEN/TR 16798-2 Anexo D ya cubre los indicadores de largo plazo.
- **Jar del Future Weather Generator**: acción del autor (descargar el jar global, fijar `ACCIM_FWG_JAR` y la versión de Java que pida); desbloquea el cuaderno y el test de E4 y los escenarios 2050/2080 de F3.
- **Estudio de validación de F3** (decisiones del autor, con Sun): climas (proponer al menos un mediterráneo de verano cálido —Sevilla, la oficina calibrada del artículo de calor, *Energy* 325, 136029— y uno húmedo; el autor los nombra); caso (i), véase §3 #12; caso (iii), vestimenta por estación 1.0/0.5 clo (supuestos de EN 16798-1 Tabla B.2) con estación de refrigeración 121–274 y `DynamicClothingModelASHRAE55` como sensibilidad; caso (iv), velocidades de EN 16798-1 Tabla B.4 (0.6/0.9/1.2 m/s, con control personal y Θo > 25 °C) en las horas ocupadas de la estación de refrigeración, en lugar de 0.6/1.0 m/s, salvo que Sun prefiera otras.
- **ComfStand 9/10**: §2.1 (recomendado corregir en la 1.2.0).

## 5. Estado de la revisión de los 17 commits
- Tres revisores (sub-agentes de esta sesión) se lanzaron el 11/11/2026: **Hooks-SET** (G1, G3, E-F1, F1), **Drift-Indicators** (F2, F3, H3, H4) y **Preview-Custom** (G2, G4, G5, H1, H2, H5, H6). Los reinicios de la sesión los interrumpieron y al escribir esto **no habían entregado**.
- Si existe `notes/attachments/revision2_v1.2.0_hallazgos.json`, contiene sus resultados (se añade en un commit posterior si terminan antes de cerrar este PC). Si no existe, **hay que repetir la revisión** con el Apéndice A.

## 6. Pasos de la próxima sesión
1. `git pull` de `origin/v1.2.0` (comprobar antes `git status`; no perder cambios locales).
2. Leer este archivo, `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (estructura y criterios de la revisión anterior), `notes/INFORME_SESION_v1.2.0_2026-11-10_2.md`, `notes/questions.md` (las 23), `notes/decisions.md` (entradas del 10–11/11) y el bloque F (`notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md`, `notes/PROMPTS_COPILOT_bloque_F_v02.md`).
3. Completar la revisión (§5): usar el JSON si existe; si no, lanzar los tres revisores del Apéndice A (sólo lectura; ejecutar los tests de sus tareas).
4. Escribir `notes/PROPUESTAS_MEJORAS_post_1.1.0_v05.md` con la estructura de la v04: resumen; método; veredicto por tarea; hallazgos; veredictos de las 23 decisiones (partir del §3 y corregir con la revisión); §2 de este archivo (ComfStand 9/10, errores de la v04, pregunta a Sun); bloqueados (§4); tareas para la siguiente sesión de Copilot con un prompt único (mismas reglas que la v04 §7.1: un commit y push por tarea, nada inventado, decisiones nuevas a `questions.md`, informe final).
5. Commit y push de la v05 (y del JSON de la revisión); dar al autor el prompt de Copilot.

## Apéndice A. Encargo de los tres revisores (para repetirlo si hace falta)

**Común.** Revisión de sólo lectura de `0f8bb628..47d0b486` en la rama `v1.2.0`. Leer primero: v04 (§3 hallazgos, §4 plan SET/F, §5–§6 decisiones, §7 definición de las tareas), el informe 2 (§2 desviaciones, §4 decisiones provisionales, §6 bloqueados), `questions.md`, `decisions.md`, v03 §11–§12 (patrón de fórmulas y nombres de EnergyPlus), bloque F (§3, §4, §6, §7) y sus prompts, DEVLOG del 10–11/11, CAMBIOS_CODIGO §23–§37, CHANGELOG [Unreleased]. Comprobar en cada tarea: (1) corrección científica frente a v03 §11/§12 y bloque F §7 (`TSV = 0.11·SET − 2.6`; banda 19.1/28.2 °C con `tsv_limit` 0.5; neutro 23.6 °C; deriva: `rate` 0.5 K/día, `window` α 0.8 y δ 1.0 K); (2) Erl/EMS (calling points, orden de programas, inicialización, *warm-up*, primer paso, redondeo, nunca `TrendVariable`, igualdad de backends donde se afirma); (3) API y compatibilidad (IDF de la 1.1.0 sin cambios salvo lo declarado; deprecaciones); (4) tests (que prueben la afirmación; ejecutarlos); (5) documentación frente a código; (6) las decisiones provisionales de la tarea; (7) si cada hallazgo de la v04 asignado queda cerrado. Informe estructurado: veredicto por tarea, hallazgos (tarea, severidad bug/científico/diseño/test/doc/menor, ubicación, problema, evidencia, corrección), verificado correcto, revisión de decisiones, tests ejecutados, no evaluado. Nada inventado.

**Hooks-SET (G1, G3, E-F1, F1).** G1: orden en el calling point (SetAST → gancho → `ApplyHookSetpoints_<zone>` → límites B5 → contadores); que ComfHours, C2, `HoursBelow` y las salidas "Adaptive … Setpoint" sigan las consignas de los ganchos; modelos sin gancho idénticos; decisión de la tolerancia. G3: qué se calienta y antes de qué import (`prepare_hooks` antes de `load_energyplus_api`); bisección con el reparto `ta`/`tr` de la zona o `tdb = tr`; definición de `SET_<zone>`; documentación reescrita; postura por defecto. E-F1: entradas idénticas a las de EnergyPlus (clo, met con 1.8 m² y 58.2 W/m², velocidad, HR, MRT, postura); comparación justa (Pierce: `hc = 8.6·v^0.53` con v ≥ 0.137 y `5.66·(met − 0.85)^0.39`; código ASHRAE 55: `max(v, 0.1)`); si 0.2–0.34 K es aceptable para F1 y cómo documentarlo. F1: 19.1/28.2/23.6 desde `tsv_limit` (`SET = (±tsv + 2.6)/0.11`), aviso de extrapolación con 0.7/1.0, CAT 80/90 → 0.5, *offset* del modo 2 en K de SET, conversión a Top con la `tr` del paso anterior, mínimo B5 y aviso de 18 °C, fuente de la vestimenta (Clothing Value = 0 con `ClothingInsulationSchedule` en EnergyPlus 25.1), velocidad del `People`, contador de horas en banda, sin ocupación, error claro sin backend API. Tests: `test_comfort_hooks.py`, `test_sun2026_set.py` y el de E-F1.

**Drift-Indicators (F2, F3, H3, H4).** F2: `T_rm_in(d) = (1 − α)·T_occ_mean(d − 1) + α·T_rm_in(d − 1)` sólo con horas ocupadas; regla `rate`; qué consigna es el estado; primer día ocupado sin límite; días sin ocupación; orden con B5 y ganchos; `drift_mode=None` idéntico; backends idénticos. F3: definiciones frente al bloque F (sobreenfriamiento 22 °C, banda de `T_rm_in` 2.5 K inferida, SET Pierce); nombres y unidades en `Table`; medias horarias (documentar). H3: constantes de EN 16798-1 Tabla B.2 (viviendas I 21.0/25.5, II 20.0/26.0, III 18.0/27.0, IV 16.0/28.0; oficinas I 21.0/25.5, II 20.0/26.0, III 19.0/27.0, IV 18.0/28.0); método C `wf = PPD(PMV)/PPD(PMV_limit)`, `PPD = 100 − 95·exp(−0.03353·PMV⁴ − 0.2179·PMV²)`, conversión de las consignas del índice a la escala PMV, PMV del paso anterior, 0 sin ocupación. H4: semántica de la saturación, frecuencias por defecto, umbrales de los avisos (0.8–4 met, 1 m/s), sentido del test acotado. Tests: los de F2, F3, H3 (`test_long_term_discomfort*.py`) y H4; `test_drift_parameters.py` sólo lectura sin besos.

**Preview-Custom (G2, G4, G5, H1, H2, H5, H6).** G2: reproduce la rama de `ThermalComfort.cc` (arranque el día D, 2 ≤ D ≤ 30 de enero: la media diaria del día D−1 de la ventana PMOT se sustituye por la del 31 de diciembre; RMOT no afectado); existe y pasa el test del 8 de enero; se mantiene el arranque del RMOT. G4: inicialización de `rmot_alpha` y *fallback*; criterio del test 23 vs 101 (por qué falla el 1 de enero y en el primer paso de cada día); argumentos de las estáticas en `SetAST_CS23_0/1`, `modify_accis`, `zone_arguments`, GUI y paramétrico; cambios del *golden* sólo adiciones. G5: cada punto hecho; semántica de `adaptive_coefficients`; el YAML de Qatar carga y sus números son los de la v04 §6.3 (corregir 25.5 → 26, §2.2); `fwg_add_uhi`. H1: alias con `DeprecationWarning`; claves EMS renombradas. H2: el `Schedule:File` = (máx+mín)/2 de cada día del EPW; ruta absoluta; horario de verano; sensor sólo en zonas `te_ref_nl`. H5: semántica de la métrica por régimen frente a la v04 §6.1; nombres; esquema YAML. H6: contrato del *callable*, nombres de los CSV, lectura Latin-1 y la documentación de Clothing Value = 0. Tests: `test_preview.py` (G2), `test_jpn_aqilah2025.py`, `test_setpoint_limits.py`, `test_apmv_coefficients.py`, `test_comfort_standard_registry.py`, `test_morphing.py`, `test_outdoor_metric.py`, `test_standard_regimes.py`, `test_custom_regimes.py` y el de H6.

## Apéndice B. Notas de entorno
- En el PC de esta sesión: intérprete de tests `C:\Users\sanga\.claude-science\conda\envs\pecs-eplus\python.exe` (Python 3.12, eppy, pandas, pytest, pythermalcomfort 4.8.1; sin besos) con `PYTHONPATH` = raíz del repositorio y EnergyPlus 25.1; el *sandbox* deniega las tuberías de `multiprocessing` (usar `run_ep(processes=0)`, que existe desde G5, o `run_simulation` en proceso) y `ReadVarsESO.exe` de 25.1 (WinError 623).
- En el PC de Copilot (`D:\DSG\accim`): Python 3.14 (`py`) con besos, numba 0.68.1 y pythermalcomfort 4.8.1; EnergyPlus 9.4, 9.6, 25.1, 25.2 y 26.2; biblioteca en `D:\DSG\Mendeley library`, normas en `D:\DSG\Normativas`, artículos en `D:\DSG\Otros articulos pendientes` **[del DEVLOG]**.

## Apéndice C. Localizar y leer los artículos en el otro PC

- El autor tiene en el otro PC la *Mendeley library* completa, en otra ruta. Pasará: (1) `inventario_para_api.json` (de `local-reference-manager\data\exportacion_mendeley_20261101\`, 1.1 MB; clave `items`: `local_id`, `title`, `doi`, `pdfs[]` con `preferred_path`, `all_paths`, `size`, `sha256`), que en el otro PC está en **`D:\DSG\accim\inventario_para_api.json`** (raíz del repositorio; dicho por el autor el 11/11/2026). **No debe entrar nunca en un commit** (el repositorio es público y el archivo contiene rutas de los equipos del autor): no usar `git add .` ni `git add -A`; conviene añadirlo a `.git/info/exclude` (local, no se sube); (2) opcionalmente `vigilancia_20261105\after.json` (4.3 MB; `documents` con título, autores, año e identificadores de 1776 documentos, también sin PDF; `files` con el nombre de archivo de Mendeley, que no coincide con el del disco); (3) la ruta de la *Mendeley library* en ese PC, que es **`D:\DSG\Mendeley library`** (dicho por el autor el 11/11/2026). Excluir siempre de cualquier búsqueda los manuscritos confidenciales en revisión que hay en esa carpeta (nombres como `BAE-D-26-06614_reviewer.pdf`, `ENB-D-24-05154_reviewer.pdf`, `UCLIM-D-25-00777.pdf`).
- Procedimiento: pedir acceso de lectura a la carpeta de la biblioteca; buscar por **DOI** en el inventario (nunca por parecido de títulos: da falsos positivos); tomar el nombre del archivo de `preferred_path` (las rutas son de este PC: `D:\OneDrive - Universidad de Cádiz (uca.es)\Investigacion\Mendeley library\…`), y buscarlo bajo la nueva raíz; si no aparece, buscar por `size` + `sha256` recorriendo la carpeta. Si el `local-reference-manager` del autor puede regenerar el inventario en ese PC, usar el regenerado.
- PDF que no están en el inventario (añadidos después del 1/11 o fuera de la biblioteca): Schiavon & Lee 2013, Aqilah et al. 2025 y Schweiker 2022 (*Mendeley pendiente 3*; en el otro PC, `D:\DSG\Otros articulos pendientes` según el DEVLOG); Sun, Brager & Schiavon 2026 (*Mendeley pendiente 2*, `S0378778826011576-…pdf`); EN 16798-1:2019, CEN/TR 16798-2:2019 e ISO 7730:2025 (*Normativas*; `D:\DSG\Normativas`); lo añadido a la *Mendeley library* después del 1/11 se encuentra buscando por nombre de archivo.
- Algunos PDF tienen el texto con la fuente codificada (p. ej. Fanger & Toftum 2002): leerlos como imagen de página.
- Copia de `referencias.xlsx` en la carpeta *Proximos papers* de OneDrive (el original de `local-reference-manager\data` no se puede abrir desde el *sandbox*).

## Apéndice D. Prompt para retomar en la nueva sesión de Claude Science

```
Continúa el trabajo de la sesión de Claude Science del 11/11/2026 (hecha en otro PC) sobre accim, rama v1.2.0.
1. Pide acceso de lectura y escritura a D:\DSG\accim, y de lectura a D:\DSG\Mendeley library, D:\DSG\Normativas, D:\DSG\Otros articulos pendientes y a las carpetas de EnergyPlus 25.1 y 25.2.
2. En D:\DSG\accim: comprueba git status (no pierdas cambios locales y no añadas nunca inventario_para_api.json a un commit), haz git pull de origin/v1.2.0 y lee entero notes/TRASPASO_ClaudeScience_2026-11-11_v01.md: es el estado, lo ya comprobado y el plan.
3. Para localizar artículos, busca por DOI en D:\DSG\accim\inventario_para_api.json y localiza el archivo por su nombre bajo D:\DSG\Mendeley library (Apéndice C del traspaso); excluye siempre los manuscritos confidenciales en revisión.
4. Termina la revisión de los 17 commits de la segunda sesión de Copilot (0f8bb628..47d0b486): si existe notes/attachments/revision2_v1.2.0_hallazgos.json, úsalo; si no, lanza los tres revisores del Apéndice A (sólo lectura, ejecutando los tests de sus tareas).
5. Escribe notes/PROPUESTAS_MEJORAS_post_1.1.0_v05.md como indica el §6 del traspaso (estructura de la v04; veredictos de las 23 decisiones partiendo del §3; ComfStand 9/10, los dos errores de la v04 y la pregunta para Ruiji Sun del §2; bloqueados del §4). Haz commit y push sólo de documentos de notes/ y dame el prompt único para la siguiente sesión de GitHub Copilot. No modifiques el código del repositorio.
```