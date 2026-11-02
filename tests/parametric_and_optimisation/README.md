# Tests for accim Parametric and Optimisation Module

This directory contains comprehensive test suites for the `accim.parametric_and_optimisation` module.

## Test Structure

The files whose names begin with `test_` are unit tests, which pytest collects by default and which run
without EnergyPlus or with short simulations.

The numbered files (`01_test_*.py` to `11_test_*.py`) are integration tests, which run real simulations
with EnergyPlus 9.6. pytest does not collect them by default (their names begin with a number), so they
must be given explicitly (see below):

- `../test_setup.py`: Common setup and utilities for the numbered tests (IDFs, EPWs, `prepare_buildings`,
  `enable_sizing`, `set_meter_readers`, `latest_output`).
- `01_test_simulation_base.py`: Tests for SimulationBase class initialization, outputs, evaluators, and backup functionality.
- `02_test_parametric_sampling.py`: Tests for parametric sampling methods (LHS, Sobol, Morris, Full Set, Full Factorial, Custom).
- `03_test_parametric_run.py`: Tests for parametric simulation runs (Basic, Multi-EPW, Multi-IDF, Output types, APMV, Custom).
- `04_test_optimization.py`: Tests for optimization algorithms (15 algorithms with the settings each one needs, and ParticleSwarm, which cannot run), Multi-EPW, keep_sim_files, estimates.
- `05_test_analysis_mixin.py`: Tests for AnalysisMixin (Floor area, Hourly/Monthly DF, SA Morris, SA Sobol).
- `06_test_data_loading.py`: Tests for data loading (CSV, Pickle, JSON recover).
- `07_test_plotting_mixin.py`: Tests for PlottingMixin (Pareto front, MCDM best solutions).
- `08_test_accim_predef_model.py`: Tests for accim predefined model (Init, Parametric, `comfort_standard` 0 and 22 with the `comfort_mode` of the baseline, the baseline with validated meters and a plan without `comfort_standard`).
- `09_test_integration_complete.py`: Tests for end-to-end workflow integration.
- `10_test_outputs_preflight.py`: Tests for the discovery, selection and preflight of the outputs.
- `11_test_compare_simulation_instances.py`: Tests for the comparison of simulation instances.

## Test Data

The `../test_data/` directory (relative to this folder) contains the necessary files for running the tests:

- `SF_Detached_B_min_North.idf`: Main test IDF file (EnergyPlus 9.6)
- `SF_Detached_D_min_North.idf`: Secondary IDF for multi-IDF tests
- `ALJARAFE CENTER_onlyGeometry.idf`: Additional IDF (not used by the numbered tests)
- `seville_2024.epw`: Primary weather file
- `seville_2025.epw`: Secondary weather file for multi-EPW tests
- `madrid_2024.epw`, `madrid_2025.epw`: Additional weather files for comprehensive tests

The IDFs have no sizing periods and zone sizing off. accim enables the sizing calculations of the VRF
systems it adds (they are autosized), but EnergyPlus also needs sizing periods, so `prepare_buildings`
adds a few days of the EPW as sizing periods, which are not simulated (`enable_sizing`, which also enables
the sizing calculations). It also reduces the run period to two weeks between June and July (hourly
results of two months) with 2 timesteps per hour.

## Running Tests

The unit tests (from the root of the repository):

```bash
python -m pytest tests/parametric_and_optimisation -p no:cacheprovider
```

The numbered tests, from a scratch folder (they write `./test_*` folders in the working folder), giving
the files explicitly (PowerShell):

```powershell
New-Item -ItemType Directory -Force $env:TEMP\accim_numbered_tests | Set-Location
$files = Get-ChildItem D:\Python\accim\tests\parametric_and_optimisation -File |
    Where-Object { $_.Name -match '^\d\d_test_.*\.py$' } | ForEach-Object FullName
python -m pytest @files -p no:cacheprovider -q
```

They take about 15 to 35 minutes (EnergyPlus 9.6 must be installed). To run a specific file or test,
give it the same way (for instance, `...\03_test_parametric_run.py::test_parametric_basic`).

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
- `04_test_optimization.py::test_optimization_all_algorithms` runs each algorithm with the settings it needs
  (`epsilons`, `divisions_outer`, a population of 3 for SPEA2, numeric ranges for OMOPSO, SMPSO and CMAES, and
  for IBEA, which stops when all the solutions of a generation have the same objectives) and enough evaluations
  to iterate, and `test_optimization_particle_swarm` checks that ParticleSwarm stops with a clear error.
