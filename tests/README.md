# Tests Directory

This directory contains test suites for the accim library.

## Structure

- `parametric_and_optimisation/`: Test suite for the parametric and optimisation module
- `test_data/`: Shared test data files (IDF models and EPW weather files)

## Running Tests

### From the project root (D:\Python\accim):

```bash
pytest tests/parametric_and_optimisation/
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
