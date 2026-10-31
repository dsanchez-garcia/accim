# Development tools

Scripts for the developers of accim; they are not part of the package.

| Script | What it does |
| --- | --- |
| `compare_backends.py` | Simulates a model with the EMS of EnergyPlus and with the Python API backend of accim (`accim.sim.energyplus_api`), and compares their hourly CSV files column by column (exit code 0 when they are the same, or within `--tolerance`). Needs EnergyPlus 24.2 or later. |

```bash
PYTHONPATH=. python tools/compare_backends.py "MODEL[CS_INT EN16798[...].idf" WEATHER.epw OUT_DIR --days 6 --start 7/1
```

To check the backends on many models, run it on the output IDFs of the golden master
(`python tests/core/golden_master/runner.py write OUT_DIR` writes their canonical text; the IDFs themselves come
from `AddAccis` or `add_accis_to_idf` on the models of `tests/core/golden_master/inputs`). For accim 1.0.0, the
CSV files of both backends were identical for the 10 model types of accim (EnergyPlus 25.1, 25.2 and 26.2) and for
9 of the 11 EMS examples of EnergyPlus (`DEVLOG.md`, 2026-10-30).

The golden master of the output IDFs, with its own command-line tool to compare two versions of accim, is in
`tests/core/golden_master` (see its `README.md`).
