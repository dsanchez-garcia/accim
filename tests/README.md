# Tests Directory

This directory contains test suites for the accim library.

## Structure

- `core/`: Tests for the modules outside `parametric_and_optimisation` (`accim.sim`, `accim.run`, `accim.data`, `accim.utils`). They do not run EnergyPlus; the few that read an IDD of EnergyPlus 25.1 or 25.2 are skipped when it is not installed
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
