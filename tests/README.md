# Tests Directory

This directory contains test suites for the accim library.

## Structure

- `core/`: Tests for the modules outside `parametric_and_optimisation` (`accim.sim`, `accim.run`, `accim.data`, `accim.utils`). The few that read an IDD of EnergyPlus 25.1, 25.2 or 26.2 are skipped when that version is not installed. Those of 26.2 update a sample IDF with its transition programs and run accim in a separate Python process, which imports accim from the repository; four of them simulate 1 day with EnergyPlus 26.2 (the custom model; the sample model with `People` objects against the same model with `People:Definition` and `People:Instance` objects, with `addAccis` and with aPMV setpoints; and the sample model with `Space` objects, with the occupants in a space, in zones of one and two spaces and in a space list). `test_energyplus_api.py` simulates 3 days of an output IDF of `AddAccis` with EnergyPlus 25.1, with the EMS of EnergyPlus and through its Python API, and checks that the results are identical; the others do not run simulations
  - `core/golden_master/` and `test_golden_master.py`: the golden master of the output IDFs (29 configurations of `AddAccis`, the in-memory functions and the aPMV setpoints, each in its own Python process, about a minute and a half; see `core/golden_master/README.md`)
  - Golden files: the tests that compare an output with a stored copy (`core/_golden.py`) fail when the copy is missing or different. After an intended change, write them again with `--update-golden` (or `ACCIM_UPDATE_GOLDEN=1`) and review the change before committing them
- `parametric_and_optimisation/`: Test suite for the parametric and optimisation module
- `test_data/`: Shared test data files (IDF models and EPW weather files)
- `../tools/`: development scripts that are not tests (`compare_backends.py`: the EMS and API backends on one model)

## Running Tests

### From the project root (D:\Python\accim):

```bash
pytest tests/core/ tests/parametric_and_optimisation/
```

To write the golden files of `tests/core` again after an intended change:

```bash
pytest tests/core/ --update-golden
```

### From this tests directory:

```bash
pytest parametric_and_optimisation/
```

Or:

```bash
cd parametric_and_optimisation
pytest
```
