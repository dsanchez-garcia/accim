# Tests for accim Parametric and Optimisation Module

This directory contains comprehensive test suites for the `accim.parametric_and_optimisation` module.

## Test Structure

- `00_test_setup.py`: Common setup and utilities for all tests
- `01_test_simulation_base.py`: Tests for SimulationBase class initialization, outputs, evaluators, and backup functionality.
- `02_test_parametric_sampling.py`: Tests for parametric sampling methods (LHS, Sobol, Morris, Full Set, Full Factorial, Custom).
- `03_test_parametric_run.py`: Tests for parametric simulation runs (Basic, Multi-EPW, Multi-IDF, Output types, APMV, Custom).
- `04_test_optimization.py`: Tests for optimization algorithms (16 algorithms), Multi-EPW, keep_sim_files, estimates.
- `05_test_analysis_mixin.py`: Tests for AnalysisMixin (Floor area, Hourly/Monthly DF, SA Morris, SA Sobol).
- `06_test_data_loading.py`: Tests for data loading (CSV, Pickle, JSON recover).
- `07_test_plotting_mixin.py`: Tests for PlottingMixin (Pareto front, MCDM best solutions).
- `08_test_accim_predef_model.py`: Tests for accim predefined model (Init, Parametric).
- `09_test_integration_complete.py`: Tests for end-to-end workflow integration.

## Test Data

The `../test_data/` directory (relative to this folder) contains the necessary files for running the tests:

- `ALJARAFE CENTER_onlyGeometry.idf`: Main test IDF file
- `SF_Detached_B_min_North.idf`: Secondary IDF for multi-IDF tests
- `SF_Detached_D_min_North.idf`: Tertiary IDF for comprehensive tests
- `madrid_2024.epw`: Primary weather file
- `madrid_2025.epw`: Secondary weather file for multi-EPW tests
- `seville_2024.epw`: Additional weather file
- `seville_2025.epw`: Additional weather file for comprehensive tests

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest 01_test_simulation_base.py
```

To run with verbose output:

```bash
pytest -v
```

## Dependencies

Tests require:
- pytest
- accim (with parametric_and_optimisation module)
- SALib (for sensitivity analysis tests, optional)
- matplotlib/seaborn (for plotting tests, optional)

## Notes

- Some tests may be skipped if required dependencies (e.g., SALib) are not installed.
- Tests use small simulation sizes to keep execution time reasonable.
- Test files are designed to be independent and can be run in any order.
