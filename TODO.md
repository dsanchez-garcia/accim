# TODO

Active short-term tasks.

## Conventions

- Use priorities:
  - `P0` (critical): it stops users or a release now (a crash or wrong results in a published version, lost data, a security problem); it goes before anything else.
  - `P1` (high): needed for the next release, or wrong behaviour that has a workaround, failing tests, or documentation that misleads.
  - `P2` (normal): improvements, refactors, reviews and tasks without a date.
  - When in doubt, the lower priority; raise it when a user is affected.
- Use status tags: `todo`, `in progress`, `blocked`.
- Reference issues and pull requests when available: `#123` for those of this repository and `owner/repo#123` for those of other repositories (for instance, `NatLabRockies/EnergyPlus#11409`, the repository of EnergyPlus, formerly `NREL/EnergyPlus`), which GitHub links in both cases (as plain text: not inside code spans); full URLs only for other sites.
- When a task is completed, move the outcome to `DEVLOG.md`.

## Task template

```md
- [ ] [P1][todo] Short title
  - Context:
  - Definition of done:
  - References:
```

## Backlog

- [ ] [P2][todo] The tests of `tests/core` that need besos without skipping
  - Context: task G5 (2026-11-10) gave `pytest.importorskip('besos')` to the four tests of the finding of v04 §3.4; other tests of `tests/core` also need besos, and fail without it instead of being skipped: `test_modifyaccis_setast.py` imports `param_accis` at module level (an error of collection), and `test_apmv_calling_managers.py`, `test_apmv_defaults.py`, `test_energyplus_versions.py`, `test_existing_hvac.py`, `test_existing_hvac_mixed_mode.py`, `test_mixed_mode_windows.py`, `test_sizing.py`, `test_utils_accim_args.py`, `test_utils_editing.py`, `test_utils_idf_hierarchy.py`, `test_vrf_ideal_loads.py`, `test_zone_arguments.py` and `golden_master/runner.py` read models with `besos.eppy_funcs.get_building`, and `test_comfort_standard_code.py`, `test_epmv.py`, `test_pmv_index.py` and `test_gui.py` import the parametric module in some tests.
  - Definition of done: the tests that only read models use `accim.sim.accis.load_idf` (eppy), and those of the parametric module call `pytest.importorskip('besos')` first; `py -m pytest tests/core` without besos (a plugin that sets `sys.modules['besos'] = None`) skips them and fails none.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§3.4), `tests/core/test_setpoint_limits.py` and `tests/core/test_jpn_aqilah2025.py` (the four tests).

- [ ] [P1][todo] Block F: F1 and F2 (the causal SET of Sun et al. 2026 as comfort standard 24, and the limiter of the setpoint drift)
  - Context: `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` (§3, §4, §6) and its prompts (`notes/PROMPTS_COPILOT_bloque_F_v02.md`), for the paper with Ruiji Sun; the order of the author for this session: F1 on `SetSetpointHook(method='bisection')` of G3 with the names of H1 and the `tr_mode` decision of 2026-11-10, then F2. E-F1 is done (2026-11-10, `notes/decisions.md`: the SET of pythermalcomfort is 0.045 K below that of EnergyPlus on average, at most 0.20 K, standing; 0.116 K, at most 0.34 K, sitting).
  - Definition of done: as the prompts of v02 say, one commit each.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§4, §7), `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md`, `notes/PROMPTS_COPILOT_bloque_F_v02.md`.

- [ ] [P2][todo] Block F: F3, the indicators of the indoor adaptation and the design of the validation study
  - Context: `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §4 (F3): the columns of `Table` for the SET, the causal TSV, the hours within the causal band and `T_rm_in`, and an indicator of overcooling; the diagnostic `Tn_exp` of Parkinson et al. (2020, Fig. 6); the parametric study of the paper.
  - Definition of done: the indicators in `Table` (D1/D2), with tests; the study is a design for the paper.
  - References: `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` (§4 F3, §7).

- [ ] [P2][todo] B1: T0 of `te_ref_nl`, the mean of the maximum and the minimum of the whole day (task H2 of v04 §7)
  - Context: finding B1-1 and verdict #8 (`notes/decisions.md`, 2026-11-10): T0 is the running (max+min)/2 of the hours of the day that have ended, so Te,ref drifts within the day, while van der Linden et al. (2006) define Ti with the maximum and minimum of the whole day.
  - Definition of done: with the weather file, the daily (Tmax+Tmin)/2 of the current day as a `Schedule:File` read by a sensor `Schedule Value`; without it, the value of the previous day, with a warning; both backends identical, `compute_setpoints` and the docs.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§3.3 B1-1, §7 H2), `accim/sim/ems/outdoor_metric.py`.

- [ ] [P2][todo] A4: the saturation of the ATHB setpoints, the frequencies of their outputs, the ranges of met and air speed, and a bounded scientific test (task H4 of v04 §7)
  - Context: findings A4-1 to A4-3 and the test finding of §3.4 (v04): the setpoints saturate silently at the limits of `temperature_range`; `output_frequencies=('hourly',)` ignores those of the model; `met = 0` is accepted; the relation between W/person and met, and the relative air speed, are undocumented; the EnergyPlus test only checks −3 ≤ ATHB_PMV ≤ 3.
  - Definition of done: a saturation counter and a warning; `output_frequencies=None` (those of the ACCIS outputs of the model); warnings for met outside 0.8–4 met and an air speed above 1 m/s; the documentation; a bounded test of the ATHB_PMV within the setpoints (or an IdealLoads variant of the sample model).
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§3.3 A4-1 to A4-3, §3.4, §7 H4), `accim/sim/comfort_hooks.py`.

- [ ] [P2][todo] A4: the setpoints of the ATHB in mixed mode
  - Context: verdict #34 (`notes/decisions.md`, 2026-11-10): the ATHB setpoints are for full air-conditioning only (a `ValueError` in mixed mode, whose windows follow the setpoints of the ACCIS); mixed mode stays a P2 task.
  - Definition of done: a design for the windows and the HVAC system with the ATHB setpoints (a question for the author first), with tests.
  - References: `accim/sim/comfort_hooks.py` (`apply_athb_setpoints`).

- [ ] [P1][todo] `Table` with `source_frequency='timestep'` and `standard_outputs=True` drops all the outputs (found with D1; part of task H3 of v04 §7, finding D1-1)
  - Context: the filter of the standard outputs keeps the columns that contain `SFdict[source_frequency]`, which is `'Timestep'` for timestep frequency, but EnergyPlus names these columns `[C](TimeStep)` (capital S), so no output is kept: with the CSV of a simulation of an output IDF of `AddAccis` at timestep frequency (2026-11-09), `Table(source_frequency='timestep', frequency='hourly', standard_outputs=True, ...)` found no occupied zones and asked for `level_excluded_zones` in the prompt; with `standard_outputs=False`, it reads them. The aggregation of the timestep rows into hours also reported "rows not correctly aggregated" (the first row, 00:10, counted alone). Not changed, since it is not part of D1 (the code has "todo timestep frequency to be tested").
  - Definition of done: the filters compare the frequency without case (also `output_cols_to_keep`), with a test with the columns that EnergyPlus writes at timestep frequency, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/data/postprocessing/main.py` (the filter of `standard_outputs`, `SFdict`).

- [ ] [P2][todo] B2: an outdoor metric for each regime of the custom model (task H5 of v04 §7)
  - Context: B2 is done (2026-11-09, `DEVLOG.md`), but for the field `outdoor_metric` of `CustomRegime` ("overrides custom_outdoor_metric for this regime (B1)" in the design of v03): `CustomRegime(outdoor_metric=...)` raises a `ValueError` unless it is None. Unblocked by the author on 2026-11-10 (`notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §6.1, `notes/decisions.md`): the conditions of all the regimes are evaluated with the metric of the zone (`CustAST_metric`), and the selected regime can set its own metric (`outdoor_metric`, `alpha`, `days`; those of the zone when None) to calculate `ComfTemp`; `SetOutdoorMetric` calculates every distinct metric of the regimes of the zone (a variable `Tout_metric_<k>` for each one), and `SelectCustomRegime_<zone>` copies that of the selected regime into `Tout_metric`. H5 also documents the possible alternation of the regimes with `'hvac_on'`/`'hvac_off'` (finding B2-1) and that the hourly `CustomRegime_<zone>` is a mean (B2-2).
  - Definition of done: the program of the regimes sets the metric of the regime (with the EMS code of B1 for the metrics of the regimes), `compute_setpoints` and `verify_accim_simulation` follow it, with tests against EnergyPlus and both backends identical.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§3.3 B2-1, B2-2; §6.1; §7 H5), `accim/sim/arguments.py` (`CustomRegime`), `accim/sim/ems/custom_regimes.py`, `accim/sim/ems/outdoor_metric.py`.

- [ ] [P2][todo] B2: check 4 of `verify_accim_simulation` with the conditions `'hvac_off'` and `'hvac_on'`
  - Context: `compute_setpoints` cannot evaluate these conditions (they depend on the HVAC system of the simulation in the previous timestep), so check 4 does not check the zones whose regimes have them ("not checked" in the summary). The output `CustomRegime_<zone>` gives the regime of each timestep, and `compute_setpoints` the setpoints of each regime, so the setpoints could be checked given the reported regime (as `tests/core/test_custom_regimes.py::test_the_condition_hvac_off_in_energyplus` does), and the regime against the outputs of the coils or of the load of the previous timestep, if the model reports them at timestep frequency.
  - Definition of done: check 4 checks these zones with the reported regime (and the condition, when the outputs of the HVAC system are there), with a test with EnergyPlus.
  - References: `accim/utils/verification.py` (`_setpoint_mismatches`), `accim/sim/preview.py`.

- [ ] [P2][todo] The full table of the setpoints lacks JPN Aqilah 2025 (23)
  - Context: `docs/source/html_files/full_setpoint_table.html` and `docs/source/images/full_table.png` (section 4.3 of the detailed use, and the prompts of `AddAccis`) are exports of a spreadsheet of the author, without comfort standard 23 (B4, 2026-11-09) and the comfort standards defined by their data; section 4.3 says so and points to `print_setpoint_ems_code`.
  - Definition of done: the spreadsheet has the rows of comfort standard 23 (categories 80 and 90, comfort modes 0 to 3: the static setpoints `static_cooling_setpoint`/`static_heating_setpoint`, 28/20 °C by default (G4), ISO 7730 25/27 and 19/22 °C (80), 24/26 and 20/23 °C (90), 0.38·RMOT + 16.9 ± 2.0 or 1.5, limits 5 and 30 °C), exported again to the HTML file and the image; the note of section 4.3 changes.
  - References: `docs/source/html_files/full_setpoint_table.html`, `docs/source/images/full_table.png`, `accim/sim/ems/setpoint_lines.py`.

- [ ] [P2][todo] B3: several regimes of a comfort standard defined by its data (task H5 of v04 §7; after the metric of each regime of B2)
  - Context: a `ComfortStandardDefinition` takes one `CustomRegime` with the condition `'always'` (a `ValueError` otherwise). Decided by the author (v04 §6.4, `notes/decisions.md`): a key `regimes:` (a list) with the schema of `CustomRegime` of B2 (`slope`, `intercept`, offsets, limits, `condition`, optional `outdoor_metric`); a scalar `comfort_temperature` is one regime `'always'`.
  - Definition of done: `accim.sim.ems.standard_lines` writes the regimes (with the conditions of B2), and the loader, `compute_setpoints` and `verify_accim_simulation` follow them, with tests against EnergyPlus.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§6.4), `accim/sim/standards.py` (`ComfortStandardDefinition`), `accim/sim/ems/standard_lines.py`.

- [ ] [P2][todo] C2: Method C (the PPD-weighted hours) as an objective, for the setpoints based on the PMV (task H3 of v04 §7)
  - Context: C2 is done (2026-11-10, `DEVLOG.md`) for Methods A and B of CEN/TR 16798-2:2019, Annex D. Decided by the author (v04 §6.5, `notes/decisions.md`): Method C only for the models with setpoints based on the PMV (`pmv_index`), with the limits `pmv_heating_setpoint`/`pmv_cooling_setpoint` without the tolerance and the PMV of the zone that the EMS already measures; wf = PPD(PMV)/PPD(PMV_limit) with formula (5) of ISO 7730:2025 in Erl (`@Exp`); counter `PpdWeightedHours_<zone>`; a documented `ValueError` for the temperature models of the ACCIS (no PMV). Verdict #20: the range of wf = 0 follows the literal text, PMVlimit,lower ≤ PMV < PMVlimit,upper (`ppd_weighted_hours` of D1 too). H3 also adds `long_term_range=('en16798', category)` with constant limits (finding C2-1) and documents the difference between the hourly indicators of `Table` and the EMS counters by timestep (D1-1).
  - Definition of done: the EMS counts the PPD-weighted hours of each zone (and the building), a reducer `ppd_weighted_hours` reads them, `verify_accim_simulation` checks them, with tests against `accim.data.postprocessing.long_term_discomfort.ppd_weighted_hours` and EnergyPlus, both backends identical.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§3.3 C2-1, D1-1; §6.5; §7 H3), `accim/sim/ems/long_term_discomfort.py`, `accim/sim/pmv_index.py`, `accim/parametric_and_optimisation/objectives.py`.

- [ ] [P2][todo] C2: the weekly and monthly deviations of Table E.1 as constraints of the optimisation
  - Context: v03 (C2) makes the acceptable deviations of CEN/TR 16798-2:2019, Annex E, Table E.1 (3 % or 6 % of the occupied hours of a year, 12 % or 25 % of a month, 20 % or 50 % of a week) constraints of the optimisation. `deviation_constraint_bound` gives the bound of the hours outside the range in the simulated period (the yearly criterion, with a run period of a year); the weekly and monthly criteria compare the hours outside of each week or month with the occupied hours of that week or month, two outputs that a reducer of besos does not get together, so they are checked after the simulations (`deviation_check`, `Table(long_term_indicators=True)`), as the docs say (2026-11-10).
  - Definition of done: the constraint of the worst week or month (for instance, an EMS counter of the hours outside minus the deviation of the occupied hours of each period, or a reducer with the occupied hours of each period as data), with tests against `deviation_check`.
  - References: `accim/parametric_and_optimisation/objectives.py` (`deviation_constraint_bound`), `accim/data/postprocessing/long_term_discomfort.py` (`deviation_limit`, `deviation_check`), `docs/source/parametric_and_optimisation.rst`.

- [ ] [P2][blocked] C2 and D1: the overheating criteria of CIBSE TM52 and TM59 (documents not available)
  - Context: v03 (C2 and D1) leaves out the thresholds of CIBSE TM52 (2013) and TM59 (2017) until their texts are available, and decision D12 of the brief makes anything about them out of scope (TODO entries only, no code). Neither text is in the sources of this session.
  - Definition of done: with the texts, the criteria (TM52: the hours of exceedance, the weighted exceedance of a day and the upper limit; TM59: those of dwellings) as functions of `accim.data.postprocessing.long_term_discomfort` and, if the author wants, objectives of the optimisation, with tests from the examples of the texts.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` (C2, D1, §9), `notes/COPILOT_BRIEF_v1.2.0_v01.md` (D12).

- [ ] [P2][blocked] E4: the How-to notebook of the future weather files, and the test with the tool (pending the jar of the Future Weather Generator)
  - Context: E4 is done (2026-11-10, `DEVLOG.md`) but for the notebook that v03 asks for (a present EPW → its future EPWs → `run_ep` → `Table` with the indicators of D1): the jar file of the global Future Weather Generator is not on this machine (searched in `D:\`, the user folder and the program folders on 2026-11-10), so neither `morph_epws` nor pyfwg could morph an EPW; Java 1.8.0_481 is installed, and the version of Java that each version of the tool needs is not in the sources of the session. The behaviour of `engine='pyfwg'` is tested with pyfwg mocked, and its arguments against the signature of `pyfwg.morph_epw_global` of pyfwg 0.4.0; `tests/core/test_morphing.py::test_morph_epws_with_pyfwg_and_the_tool` runs the tool when the environment variable `ACCIM_FWG_JAR` is the path of its jar (skipped otherwise).
  - Definition of done: with the jar (and the Java it needs), the test passes; the notebook (`accim/sample_files/jupyter_notebooks/<folder>`, with `docs/prepare_howto_notebooks.py`) morphs `Seville_Present.epw`, simulates the sample model with the present and future EPWs (`run_ep`) and compares their long-term discomfort (`Table(long_term_indicators=True)`), run with EnergyPlus 25.1 and exported to the How-to Guides; section 4.5.1 links it.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` (E4), `accim/data/morphing.py`, `tests/core/test_morphing.py`, `docs/README.md` (the How-to notebooks).

- [ ] [P2][todo] E4: the command line of `morph_epws(engine='java')` may not be that of the current versions of the Future Weather Generator (to check with the jar)
  - Context: `engine='java'` gives the tool 8 positional arguments (the EPW, the climate models, the ensemble, the hours of the transition between months, the output folder, the threads, the interpolation and the limits of the variables), as before accim 1.2.0. pyfwg 0.4.0 builds 12 for the version 3 of the global tool (`_build_command_v3` of `pyfwg/workflow.py`: also the SD shift, after the ensemble, and the solar hour adjustment, the diffuse irradiation model and the UHI) and arguments of key and value for the versions 4 and 5. Found while writing E4 (2026-11-10); not changed, since the jar was not available to check which versions the command of accim supports.
  - Definition of done: with the jars of the versions of the tool, check which ones `engine='java'` runs correctly; document them (section 4.5.1 and the docstring), and update the command or make `'pyfwg'` the recommended engine, with `CHANGELOG.md`. Decided by the author (v04 §6.7, `notes/decisions.md`, 2026-11-10): the command line of pyfwg (12 arguments for version 3) is the reference; still pending the jar.
  - References: `accim/data/morphing.py` (`morph_epws`), `pyfwg/workflow.py` (`_build_command_v3`, `_build_command_new_cli`).

- [ ] [P2][todo] A4 and A6: the setpoints of the ATHB and of the SET in the model, for `verify_accim_simulation`, the GUI and to make the hooks again
  - Context: A4 and A6 are done (2026-11-10, `DEVLOG.md`). The arguments of the setpoints of the ATHB (the setpoints of the ATHB_PMV, the metabolic rate, the air speed, the clothing, the range and the tolerance) are only in the hook that `apply_athb_setpoints` returns, not in the model, so `verify_accim_simulation` cannot check its setpoints (the tests check them against the bisection with the outputs of the zones), and the model cannot be simulated again without the Python object; the same holds for those of the SET (`apply_set_setpoints`, `SetSetpointHook`). For the same reason the GUI applies and runs neither hook (its tab of the simulations has the backend, but `run_ep(hooks=...)` needs the hook made from the model), and the hooks of a folder are those of one model (`run_ep` gives the same hooks to all its simulations).
  - Definition of done: the model keeps the arguments (for instance, as the lines of an EMS program that no calling manager runs; a design for the author, `notes/questions.md`), `AthbSetpointHook.from_model` and `SetSetpointHook.from_model` make the hooks from them, `verify_accim_simulation` checks the setpoints of the schedules and the adapted clothing and metabolic rate (with pythermalcomfort, when installed), and the GUI can apply them and run each model with its hook, with tests.
  - References: `accim/sim/comfort_hooks.py`, `accim/run/run.py` (`run_ep`), `accim/utils/verification.py`, `accim/gui/app.py`, `tests/core/test_comfort_hooks.py`.

- [ ] [P2][todo] A6: the cooling effect of the elevated air speed, as an indicator (F3)
  - Context: v03 (A6) names the setpoints "by cooling effect" (the outputs *ASHRAE 55 Elevated Air Speed Cooling Effect* and *... Adjusted PMV/PPD* of the model `CoolingEffectASH55` of the People objects) without a design. Decided by the author (v04 §6.8, `notes/decisions.md`, 2026-11-10): the proportional control in Erl of the SET setpoint (way (a) of v03) is discarded, since the author chose the API backend in block F; the cooling effect is postponed to F3, as an indicator, not a setpoint; the convergence plan A6 → F1 of v04 §4.6 replaces the rest of the old task (G3, E-F1, F1–F3).
  - Definition of done: with F3, the cooling effect as an output or indicator of `Table`, if the design of F3 includes it, with tests.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§4.6, §6.8), `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` (F3), `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` (A6, §12.2).

- [ ] [P2][todo] A5: the clothing insulation as a function of the outdoor temperature (task H6 of v04 §7)
  - Context: A5 is done (2026-11-09, `DEVLOG.md`). The design of the proposal also has the clothing insulation as a function of the outdoor temperature (`callable(rmot) -> clo`). Decided by the author (v04 §6, `notes/decisions.md`, 2026-11-10): `clothing_insulation=callable`, written as a `Schedule:File` generated from the weather file with `accim.sim.preview.outdoor_metrics`; no Erl version by sections.
  - Definition of done: `set_pmv_input_parameters(clothing_insulation=callable, ...)` (with the weather file) writes the `Schedule:File`, with tests, documentation and `CHANGELOG.md`.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v02.md` (A5 and E1), `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§6, §7 H6), `CAMBIOS_CODIGO_v1.2.0.md` §4 and §8.

- [ ] [P1][todo] Comfort standards 9 and 10 (IND IMAC R 7DRM and 30DRM): their running means look swapped (pending the author)
  - Context: found while checking `accim.sim.preview.compute_setpoints` (E1) against EnergyPlus. Comfort standard 9 is IMAC-R with the 7-day running mean (`9 = IND IMAC R 7DRM`) and 10 with the 30-day one, and v03 lists IMAC-R as `Tc = 0.39·T7DRM + 18.4` and `Tc = 0.42·T30DRM + 17.6` (Aqilah 2025, Table 1, citing Rawal et al.). But the setpoints of comfort standard 9 (`0.39·x + 18.42`) use `PMOT`, the 30-day mean of ASHRAE 55 in EnergyPlus, and those of 10 (`0.42·x + 17.6`) use `RMOT`, the running mean of CEN 15251 (α = 0.8, 7 days at the start); `SetComfTemp` uses `PMOT` for both, and `CountHours_<zone>` `PMOT` for 9 and `RMOT` for 10. The output IDFs were not changed (the session must not change them without the proposal or the author). The intercept is 18.42 in the code and 18.4 in v03.
  - Definition of done: the author confirms which running mean each one must use (EnergyPlus has no 7-day arithmetic mean: `RMOT` is exponential; B1, done on 2026-11-09, gives it to the custom model only, `custom_outdoor_metric='ndrm'` with `custom_days=7`); if they change, the setpoint lines, `SetComfTemp` and `CountHours` agree, the golden master is updated with `--update-golden`, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/sim/standards.py:114`, `accim/sim/ems/setpoint_lines.py:703` (9) and `:787` (10), `accim/sim/ems/program_lines.py` (`SET_COMF_TEMP`, `COUNT_HOURS`), `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md:350` and `:734`.

- [ ] [P1][todo] Comfort standard 9, comfort mode 1: the heating setpoint out of the applicability limits is that of cooling (pending the author)
  - Context: found with E1. Out of the applicability limits, comfort mode 1 of comfort standard 9 sets `AHST = PMOT*0.078+23.25+2.72+AHSTtol` (category 80) and `+1.5` (category 90), the values of the cooling setpoint, while comfort standards 0 and 10 and comfort mode 0 of 9 use `-2.72` and `-1.5` for the heating setpoint; so the heating and cooling setpoints are equal (but the tolerances) out of the limits. The output IDFs were not changed.
  - Definition of done: the author confirms the sign; if it is a bug, the lines are fixed, the golden master is updated with `--update-golden`, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/sim/ems/setpoint_lines.py:703` (comfort mode 1 of 9), `:687` (comfort mode 0 of 9), `:787` (comfort mode 1 of 10).

- [ ] [P2][todo] E1: the running mean of ASHRAE 55 with a .stat file, and leap years
  - Context: `accim.sim.preview` reproduces the running means of EnergyPlus from the EPW (Engineering Reference 25.2, 19.1). With a .stat file next to the EPW, EnergyPlus takes the running mean of ASHRAE 55 from the monthly means of the .stat file, which `compute_setpoints` does not reproduce (documented); and the running means of EnergyPlus need an EPW of 365 days (a ValueError otherwise; `outdoor_metrics` takes any number of whole days).
  - Definition of done: `energyplus_running_means` reads the .stat file as `ThermalComfort.cc` of EnergyPlus does, and handles EPWs of 366 days, with tests against EnergyPlus.
  - References: `accim/sim/preview.py` (`_energyplus_daily`), `docs/source/4_detailed use.md` §4.3.1.

- [ ] [P1][todo] `verify_accim_simulation`, check 1: the zones whose names have ':' are not checked (found with E2)
  - Context: `verify_accim_simulation` joins the key and the variable of each output as `<key>:<variable>`, and `find_col` splits them at the first ':', so the key of a zone such as `Block1:Zone1` (the sample model) is `BLOCK1`: its operative temperature is not found, and check 1 skips the zone with the warning "No 'Operative Temperature' column found" (seen in the tests of E2, 2026-11-09). `AccimSimulationVerifier._evaluate` splits the names of the columns of the CSV file in the same way. The checks of E2 look the outputs up by key and variable and are not affected. Not changed, since check 1 would then report the mismatches of models where it did nothing.
  - Definition of done: checks 1 and 2 find the outputs of the keys with ':' (from the key and the variable that `read_eso_using_readvarseso` gives), with a test with the sample model, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/utils/verification.py:191` (`find_col`) and `:198`, `tests/core/test_verification.py`.

- [ ] [P2][todo] `AccimSimulationVerifier` has checks 1 and 2 only
  - Context: the object-oriented verifier of `accim.utils.verification` evaluates checks 1 and 2 of `verify_accim_simulation`; checks 3 (the indices derived from the PMV, E2), 4 (the setpoints against `compute_setpoints`, E2 and B1), 5 (the minimum and maximum of the setpoints, B5) and 6 (the long-term discomfort, C2) are only in `verify_accim_simulation` (noted with E2, B5 and C2, 2026-11-09 and 2026-11-10).
  - Definition of done: the class runs the same checks as the function (or calls it), with tests, or its docstring points to the function for checks 3 to 6.
  - References: `accim/utils/verification.py` (`AccimSimulationVerifier`, `verify_accim_simulation`).

- [ ] [P2][todo] `read_eso_using_readvarseso` keeps only the last 8760 rows of long outputs at timestep frequency (found with B1)
  - Context: with `only_run_period=True` (the default, which `verify_accim_simulation` uses), if the CSV file of ReadVarsESO has no rows of design days (no jump back of the date) and more than 8800 rows, it keeps the last 8760 (`df_all.tail(8760)`), as for an hourly year: the outputs at timestep frequency of a run period of more than about 61 days lose their first days, and check 4 says "Not checked: the last environment of the outputs begins on 14/01, not on the first day of the RunPeriod (01/01)" (74 days, 10656 rows, 2026-11-09). ReadVarsESO itself writes all the rows (10656, with and without the argument `unlimited`). Not changed, since it is not part of B1.
  - Definition of done: the run period is taken without cutting the rows (for instance, from the environments of the ESO file), with a test, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/utils/outputs.py:194` (`read_eso_using_readvarseso`, `only_run_period`), `accim/utils/verification.py` (`_setpoint_mismatches`).
