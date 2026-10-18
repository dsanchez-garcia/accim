# Tests Directory

This directory contains test suites for the accim library.

## Structure

- `core/`: Tests for the modules outside `parametric_and_optimisation` (`accim.sim`, `accim.run`, `accim.data`, `accim.utils`). The few that read an IDD of EnergyPlus 25.1, 25.2 or 26.2 are skipped when that version is not installed. Those of 26.2 update a sample IDF with its transition programs and run accim in a separate Python process, which imports accim from the repository; three of them simulate 1 day with EnergyPlus 26.2 (the custom model, and the sample model with `People` objects against the same model with `People:Definition` and `People:Instance` objects, with `addAccis` and with aPMV setpoints); the others do not run simulations
- `parametric_and_optimisation/`: Test suite for the parametric and optimisation module
- `test_data/`: Shared test data files (IDF models and EPW weather files)

## Running Tests

### From the project root (D:\Python\accim):

```bash
pytest tests/core/ tests/parametric_and_optimisation/
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
