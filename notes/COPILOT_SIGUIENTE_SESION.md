# accim v1.2.0 — instructions for the next GitHub Copilot session (session 3)

> **Para el autor.** En PyCharm, en el chat de GitHub Copilot (modo agente), basta con escribir:
>
> `Haz git pull --ff-only de origin v1.2.0, lee entero notes/COPILOT_SIGUIENTE_SESION.md y síguelo de forma autónoma.`
>
> Preparado por Claude Science el 11/11/2026 a partir de `notes/TRASPASO_ClaudeScience_2026-11-11_v01.md`. Incluye la decisión del autor del 11/11/2026: los ComfStand 9 y 10 no se tocan en esta sesión. Copilot no debe preguntar nada hasta el informe final.

You are working autonomously on accim, branch `v1.2.0`, in the repository root of this computer (`D:\DSG\accim` on the computer of the previous Copilot sessions), after `git pull --ff-only` (HEAD = the commit that added this file, or later). Do not ask the author anything until the final report.

## 0. What this session does

The previous session (session 2, commits `0f8bb628..47d0b486`, report `notes/INFORME_SESION_v1.2.0_2026-11-10_2.md`) implemented Step 0, G1–G5, H1–H6, E-F1 and F1–F3. Claude Science checked part of that work and left its verdicts in `notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` (the handoff); its independent reviewers did not finish. This session:

1. Step 0: applies the verdicts of the handoff §3 to the 23 provisional decisions and records the pending items (§4 below).
2. Audits session 2 itself with the checklist of the handoff, Appendix A (§5).
3. Implements the tasks S1–S5 (§6).
4. Fixes what the audit finds, where the fix is unambiguous (§7).
5. Runs the final checks, writes the report and stops (§8).

It does not write `PROPUESTAS_MEJORAS_post_1.1.0_v05.md` and does not edit the documents of Claude Science (`PROPUESTAS_MEJORAS_post_1.1.0_v01`–`v04`, the handoff, this file): the next Claude Science review covers sessions 2 and 3 and writes the v05.

## 1. Read first (whole files)

1. The handoff: §2 (checks verified by Claude Science), §3 (verdicts on the 23 decisions, binding for this session), §4 (blocked items), Appendix A (audit checklist), Appendices B and C (environment; where the papers and standards are).
2. `notes/INFORME_SESION_v1.2.0_2026-11-10_2.md`, `notes/questions.md`, `notes/decisions.md` (entries of 10 and 11 November), `TODO.md`, `ROADMAP.md`, `CHANGELOG.md` [Unreleased], the `DEVLOG.md` entries of 10 and 11 November and `CAMBIOS_CODIGO_v1.2.0.md` §23–§37.
3. `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §3 and §5–§7 (the task definitions of session 2; the rules of its §7.1 still apply) and `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` §11–§12 (formulas and EnergyPlus names).
4. Block F: `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` and `notes/PROMPTS_COPILOT_bloque_F_v02.md`.

## 2. Rules

1. The definition of done of v04 §7.1, unchanged: PEP 8; English reST docstrings with citations; eppy, never besos in the core; Erl through `accim.sim.ems`, never `TrendVariable`; pytest green for the affected test files (skip, never fail, when besos or an EnergyPlus version is missing); golden master byte-identical unless the task changes outputs on purpose (say so in the commit and the DEVLOG); when EMS code or a hook changes, a sample IDF simulated with both backends (identical setpoints and EMS variables); `CHANGELOG.md` [Unreleased], `DEVLOG.md` (Context / Changes / Files / Verification), `TODO.md`, `CAMBIOS_CODIGO_v1.2.0.md`, docs and GUI when arguments or outputs change. The rule of v04 §7.1 on `set_tmp` crashes inside EnergyPlus callbacks also applies.
2. Never invent a formula, coefficient, EnergyPlus name, Erl function or API method that is not in v03 §11–§12, the code, `Energy+.idd`, the EnergyPlus documentation or the cited paper or standard.
3. A decision that the handoff §3, v04 §5–§6, the brief D1–D12 or block F §6 do not cover goes to `notes/questions.md` (same format as the existing entries: Context, Why it matters, Options considered, Owner, Status), with the most conservative, backward-compatible option chosen provisionally; then continue.
4. Three failures of a step: a `TODO.md` entry with the error, and move on. Never loosen a test.
5. One commit and one push to `origin v1.2.0` per task; never force-push; partial work as `wip(...)` with a `TODO.md` entry. Message style as before (`fix(sim): ... (S1)`, `docs(notes): ...`), written as UTF-8 without BOM (the message of `40eb001e` starts with a BOM).
6. Stage files by explicit path; never `git add -A` or `git add .`. Never commit `inventario_para_api.json` (repository root; it holds paths of the author's computers: add it to `.git/info/exclude` if it is not there), PDFs, figures or text copied from papers or standards, or anything from the library folders.
7. Binding decisions of the author: comfort standards 9 and 10 are not changed in this session, neither their running means nor the sign of comfort mode 1 (only recorded, Step 0); the validation study of F3 stays blocked (decisions of the author with Ruiji Sun); CIBSE TM52/TM59 and the jar of the Future Weather Generator stay blocked.

## 3. Papers and standards

- Find a paper by DOI in `inventario_para_api.json` (key `items`; take the file name of `pdfs[].preferred_path`, whose folders are those of another computer) and look for that file name under `D:\DSG\Mendeley library`. The standards (EN 16798-1:2019, CEN/TR 16798-2:2019, ISO 7730:2025) are in `D:\DSG\Normativas`; Schiavon & Lee 2013, Aqilah et al. 2025 and Schweiker 2022 in `D:\DSG\Otros articulos pendientes`; for anything else, search the file name under `D:\DSG`.
- Match by DOI, never by title similarity. Never open or search manuscripts under review (file names such as `BAE-D-26-06614_reviewer.pdf`, `ENB-D-24-05154_reviewer.pdf`, `UCLIM-D-25-00777.pdf`): they are confidential.
- If a PDF cannot be read (some have their fonts encoded), record the check as not assessed.

## 4. Step 0 — decisions and pending items (documents only; one commit)

1. Move the 23 entries of the section Open of `notes/questions.md` to `notes/decisions.md` with the verdicts of the handoff §3, matched by title: "Aceptar" → accepted as implemented; "Aceptar" or "Aceptar con nota" with an instruction (#1, #7, #16, #22) → accepted, the instruction done in S5; "Cambiar" (#13, #19, #20) → changed as stated, done in S3, S1 and S2. Keep #9 (the SET of the F3 indicators) and #12 (the static reference of case (i)) in `notes/questions.md`, pending the author with Ruiji Sun, with the instruction of the handoff added (#9 is done provisionally in S4).
2. Comfort standards 9 and 10: add an entry to `notes/questions.md` (owner: the author) and complete the `TODO.md` entry "Comfort standards 9 and 10 (IND IMAC R 7DRM and 30DRM)" with the verified analysis of the handoff §2.1 (the source and its two metrics, the swap, the recommended correction, the sign of the heating setpoint of 9 in comfort mode 1, the static equation that could not be verified) and the status "the author decided on 2026-11-11 not to change them in session 3".
3. `TODO.md`, the validation study of F3: add the recommendations of the handoff §4 as a proposal for the author (with Ruiji Sun), still blocked. Leave CIBSE TM52/TM59 and the jar of the Future Weather Generator as they are.
4. Commit `docs(notes): verdicts on the 23 provisional decisions and the pending items (Step 0)` and push.

## 5. Audit of session 2 (documents only; one commit)

- Scope: the 15 code tasks of `0f8bb628..47d0b486` (G1–G5, H1–H6, E-F1, F1–F3).
- For every task, the common checks (1)–(7) of the handoff, Appendix A, and the specific checks of its group: Hooks-SET (G1, G3, E-F1, F1), Drift-Indicators (F2, F3, H3, H4), Preview-Custom (G2, G4, G5, H1, H2, H5, H6). Run the test files listed there.
- Act as an independent reviewer: derive each check from the sources and the code (`git show <commit>`, the current files), not from your report or the DEVLOG, and assume that the previous session can be wrong.
- Output: `notes/attachments/autoauditoria_sesion2_v1.2.0.json`, a list with one object per group and the keys of `notes/attachments/revision_v1.2.0_hallazgos.json`: `reviewer` (the group), `frame_id` (null), `deviations`, `proposals_reviewed`, `verdicts` (`proposal`, `verdict`, `summary`), `findings` (`id` A1, A2, …, `proposal`, `severity` = bug, scientific, design, test, doc or minor, `location`, `problem`, `evidence`, `fix`), `verified_correct`, `provisional_decisions_review` (`decision`, `sound`, `recommendation`), `tests_run` (`file`, `result`), `not_assessed`.
- Do not fix anything in this step. Commit `docs(notes): self-audit of session 2 (0f8bb628..47d0b486)` and push.

## 6. Tasks (one commit and push each, in this order)

**S1 — decision #19: the warning of verdict 13.** Remove the literal comparison of `heating_setpoint_minimum` / `cooling_setpoint_maximum` with `AHSTall` / `ACSTaul` (option (i) of the `questions.md` entry: `accim.sim.ems.setpoint_limits.warn_crossed_setpoint_limits`, called by `AddAccis` and `modify_accis`; unreleased, so no deprecation). Implement option (ii): when at least one of the two limits is given and `AddAccis` or `modify_accis` receives the weather file, compute the setpoints of the comfort model of each zone with `accim.sim.preview.compute_setpoints` and log one warning per zone if the minimum is at or above the lowest cooling setpoint, or the maximum is at or below the highest heating setpoint, with the value, the first date and the number of days affected (skip, with a debug message, the models that `compute_setpoints` does not cover). Without a weather file, no warning (documented). Keep the `ValueError` when the minimum is not lower than the maximum. Tests with a case that crosses and one that does not; IDFs unchanged.

**S2 — decision #20: Qatar.** The static setpoints of the YAML file of Qatar become 20.0 / 26.0 °C (EN 16798-1:2019 Table B.2, offices, category II; 25.5 °C is category I), with the tests and docs that cite 25.5.

**S3 — decision #13: the reference of F2 `rate`.** The reference of the daily limit becomes the mean of the setpoints applied in the occupied timesteps of the previous day, for each limited setpoint as now; days without occupied timesteps keep the reference of the last occupied day (decision #14). Results identical for setpoints constant within the day (ACCIS without hooks): check it; a test with a hook whose setpoints vary within the day; both backends.

**S4 — decision #9, provisional: the SET of the F3 indicators.** Keep the Pierce SET of EnergyPlus as the default SET of the F3 indicators and add, behind an optional argument that is off by default (its name following the F3 API), the same indicators computed with the SET of pythermalcomfort (`set_tmp`, through the `set_of_results` helper of G3 and the inputs that E-F1 compared), as extra outputs or columns with a clear suffix. Defaults and existing outputs unchanged. Document the E-F1 differences (handoff §2.3) and that the choice waits for the answer of Ruiji Sun; record the design choices in `notes/questions.md`.

**S5 — the notes of the accepted decisions #1, #7, #16 and #22.** #1: a documentation example of a clothing function that uses the column `'Tout'` for models of the outdoor temperature at 6 a.m. (Schiavon & Lee 2013, eq. 4; ASHRAE 55-2020 Fig. 5-1; formulas from v03 §11). #7: document that the absolute path of the CSV file of `T0` (H2) breaks when the IDF is simulated on another computer, and add a relative mode as a P2 entry of `TODO.md`. #16: a test that comfort modes 0 and 3 of comfort standard 24 raise a clear error (make them do so if they do not). #22: document the one-day delay of the native RMOT in the first timestep of each day (it also affects comfort standard 1) where the test of 23 against 101 and comfort standards 1 and 23 are documented.

## 7. Fixes from the audit

- Each finding of severity bug or scientific with an unambiguous fix that needs no decision of the author: one commit and push (`fix(sim): ... (A3)`, with the id of the finding), with a test that fails before the fix and passes after it.
- Findings of severity design, test, doc or minor: fix them when the fix is small and unambiguous (one commit per group of related fixes); otherwise a `notes/questions.md` or `TODO.md` entry.
- Nothing about comfort standards 9 and 10 or the blocked items.

## 8. Final checks, report and stop

1. Whole suites: `py -m pytest tests/core -q -p no:cacheprovider` and `py -m pytest tests/parametric_and_optimisation -q -p no:cacheprovider`; the golden master; the documentation build `py -m sphinx -E -b html docs/source docs/_build/html -w docs/_build/sphinx_warnings.txt` (baseline: 35 unique warning lines); the changed modules compile with Python 3.9.
2. `notes/INFORME_SESION_v1.2.0_<date>_3.md` with the sections of the previous report (tasks and commits, deviations, TODO entries, provisional decisions, tests and backend comparisons, blocked items with the exact missing information, environment) and one more: the audit (findings by severity and group, the ones fixed with their commits, the ones left open and where).
3. Commit and push the report as the last commit, and stop. In the chat, at most five lines: commits, tests, open questions, blocked items.
