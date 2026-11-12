# Development tools

Scripts for the developers of accim; they are not part of the package.

| Script | What it does |
| --- | --- |
| `compare_backends.py` | Simulates a model with the EMS of EnergyPlus and with the Python API backend of accim (`accim.sim.energyplus_api`), and compares their hourly CSV files column by column (exit code 0 when they are the same, or within `--tolerance`). Needs EnergyPlus 24.2 or later. |
| `indoor_adaptation_study.py` | Makes and simulates the cases of the validation study of block F (task F3 of accim 1.2.0, `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §4, with the choices of `notes/decisions.md` of 2026-11-12) from a model with the ACCIS: fixed setpoints of 20 and 26 °C, the adaptive setpoints of EN 16798-1 and ASHRAE 55, the causal SET model (comfort standard 24) with the clothing insulation by season or the dynamic clothing model and elevated air speeds, and the limiter of the drift of the setpoints at three rates (`--list` lists them). It writes `indicators.csv`: the energy, the long-term discomfort with the seasonal range of EN 16798-1, and the hours within the causal band with the reference SET and with the Pierce SET. Needs EnergyPlus 24.2 or later and pythermalcomfort; a year of a case of the causal SET model takes hours, so try a week first. |

```bash
PYTHONPATH=. python tools/compare_backends.py "MODEL[CS_INT EN16798[...].idf" WEATHER.epw OUT_DIR --days 6 --start 7/1
PYTHONPATH=. python tools/indoor_adaptation_study.py OUT_DIR --epw Seville_Present.epw --begin 7/15 --end 7/21
```

To check the backends on many models, run it on the output IDFs of the golden master
(`python tests/core/golden_master/runner.py write OUT_DIR` writes their canonical text; the IDFs themselves come
from `AddAccis` or `add_accis_to_idf` on the models of `tests/core/golden_master/inputs`). For accim 1.0.0, the
CSV files of both backends were identical for the 10 model types of accim (EnergyPlus 25.1, 25.2 and 26.2) and for
9 of the 11 EMS examples of EnergyPlus (`DEVLOG.md`, 2026-10-30).

The golden master of the output IDFs, with its own command-line tool to compare two versions of accim, is in
`tests/core/golden_master` (see its `README.md`).
