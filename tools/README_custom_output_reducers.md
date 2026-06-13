# Custom Output Reducers (`processes > 1`)

Use top-level importable functions for output reducers when running multiprocessing on Windows.

## Files

- `tools/custom_output_funcs.py`: sample reducer functions.
- `tools/optimisation_callable_processes_example.py`: notebook-style optimisation example.

## Supported `func` formats in `set_outputs_for_simulation(...)`

1. Callable object:

```python
from tools.custom_output_funcs import return_time_series
df_output_variable["func"] = return_time_series
```

2. Import path string:

```python
df_output_variable["func"] = "tools.custom_output_funcs:return_time_series"
```

## Quick smoke run

```powershell
py -3.9 -u "D:\Python\accim\tools\optimisation_callable_processes_example.py"
```

By default the example runs in dry mode (`RUN_FULL=False`). Set `RUN_FULL=True` in the script to execute EnergyPlus optimisation.

