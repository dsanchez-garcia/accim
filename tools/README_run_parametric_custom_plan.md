# run_parametric_custom_plan.py

Script for robust parametric simulation runs with explicit IDF-EPW pairing.

## What it improves

- Fails fast if the custom plan ends up empty.
- Uses `set_output_meters_to_idf` (non-deprecated API).
- Filters `DistrictHeating:Facility` and `DistrictCooling:Facility` in a case-insensitive way.
- Removes duplicate meter rows before `set_outputs_for_simulation`.
- By default, cleans accents on temporary IDF copies (does not overwrite source IDFs).

## Quick checks

Run the internal logic test (no simulation):

```powershell
python -u tools\run_parametric_custom_plan.py --self-test
```

Run a dry-run against local `*.idf` and `*.epw` (build plan + validation, no EnergyPlus run):

```powershell
python -u tools\run_parametric_custom_plan.py --dry-run
```

## Full run

```powershell
python -u tools\run_parametric_custom_plan.py --out-dir results_parametric --processes 8
```

## Notes

- Default matching is city-to-zone:
  - `leon -> E`, `seville -> B`, `madrid -> D`, `malaga -> A`, `granada -> C`
- Keep filenames aligned with those tokens so the custom plan is not empty.
- If needed, you can edit `DEFAULT_CITY_TO_ZONE` inside `tools\run_parametric_custom_plan.py`.

