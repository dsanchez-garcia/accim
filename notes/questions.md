---
title: Open questions
type: log
tags: [vault, questions]
created: 2026-09-13
---

# Open questions

Pending questions or blockers that need a human decision. Newest first.
Move a question to [[decisions.md]] once it is resolved (and delete or mark
it here as answered).

## How to use this file

```md
## YYYY-MM-DD — Short question
- Context:
- Why it matters:
- Options considered:
- Owner:
- Status: open | answered (see [[decisions.md]])
```

## Open

## 2026-10-30 — Should `add_accis_to_idf` enable the sizing calculations, as `AddAccis` does?
- Context: `AddAccis` (IDF files) enables the zone, system and plant sizing calculations of `SimulationControl` in every output IDF, because the VRF systems that accim adds are autosized (in 0.8.2, `setSimulationControlSizing`, called only by `addAccis`). `add_accis_to_idf` (IDF objects), which `accim.parametric_and_optimisation` uses, does not, as `accis_single_idf_funcs.addAccis` did not in 0.8.2 (`setSimulationControlSizing` was imported by `accim_Main_single_idf` since commit `ff21dade`, but never called). Branch `v1.0.0` keeps that behaviour. With an input IDF whose zone sizing is off, the VRF models built by `add_accis_to_idf` stop EnergyPlus: "For autosizing of ZoneHVAC:TerminalUnit:VariableRefrigerantFlow ..., a zone sizing run must be done". This is why the scripts of `tests/parametric_and_optimisation_full_workflow` (IDFs `SF_Detached_*`, with zone sizing off) fail, on `master` too.
- Why it matters: the parametric module (predefined and custom models, `vrf_mm` by default) cannot run models whose zone sizing is off, unless the user enables it before.
- Options considered: (a) keep the behaviour of 0.8.2; (b) enable the sizing calculations in `add_accis_to_idf` only for the VRF script types: it cannot break a model that runs now, since such a model stops without zone sizing; (c) enable them for every script type, as `AddAccis`: the same models from both functions, but the models of `ex_ac` and `ex_mm` whose sizing is off would run the sizing calculations, which need sizing periods.
- Owner: author.
- Status: open.
