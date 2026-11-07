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

## 2026-11-07 — Should `vrf_mm` also air-condition the zones on the design days?
- Context: with `ex_mm`, the HVAC systems were off on the design days without occupants, and EnergyPlus sized them for
  no load; since 2026-11-07, `ex_mm` air-conditions the zones on the design days with the windows closed (see the
  decision of 2026-11-07 in [[decisions.md]]). `vrf_mm` has the same rule (HVAC off without occupants) and autosized
  VRF systems, but it was not changed: the request was about `ex_ac` and `ex_mm`, and the sample models of
  DesignBuilder simulate.
- Why it matters: a model whose design days have no occupants would get VRF systems sized for no load with `vrf_mm`.
- Options considered: (a) the same rule for `vrf_mm` (its output IDFs change: the sensor `DesignDay` and the lines of
  the design days); (b) leave `vrf_mm` as it is.
- Owner: the author.
- Status: open

## 2026-11-06 — Keep only the EMS code of the comfort standards of each output IDF of `AddAccis`?
- Context: the author asked what I thought of adding only the EMS code of the comfort standards chosen; he was not
  available to choose, so option 1 was implemented in the branch `v1.1.0` (see the decision of 2026-11-06 in
  [[decisions.md]], and section 7 of [[../CAMBIOS_CODIGO_v1.1.0.md]]).
- Why it matters: the output IDFs are about half as large and easier to read, but their comfort standard can no
  longer be changed by hand in `SetInputData_<zone>` (only with `modify_accis`), which the documentation of 1.0.0
  allowed.
- Options considered: (1) the code of the comfort standards of the zones in all the programs that depend on the
  comfort standard (implemented); (2) only in the subprograms `SetAST_CS<n>_<chunk>` and `SetAST_Master`; (3) the
  code of all the comfort standards, as before (only the indentation).
- Owner: the author.
- Status: open

The questions on the scope and the technology of the GUI and on the names of the arguments of accim 1.0.0 were answered: see [[decisions.md]].
