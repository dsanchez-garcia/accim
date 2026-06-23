# smoke_resume_runner.py

Runner corto para validar:

- `accim_results_root` (sin usar `setx`),
- checkpoint por lotes,
- reanudacion (`resume_from_checkpoint`) en `ParametricSimulation`.

## Uso rapido

Self-test (sin BESOS/EnergyPlus):

```powershell
Set-Location "D:\Python\accim"
python -u tools\smoke_resume_runner.py --self-test
```

Dry-run (solo plan + rutas):

```powershell
Set-Location "D:\Python\accim"
python -u tools\smoke_resume_runner.py --dry-run --accim-results-root "D:\accim_results"
```

Validacion completa stage1+stage2 en una llamada:

```powershell
Set-Location "D:\Python\accim"
python -u tools\smoke_resume_runner.py --mode two-step --accim-results-root "D:\accim_results" --out-dir "results_parametric_smoke_resume"
```

Validacion partida (simular interrupcion manual):

```powershell
Set-Location "D:\Python\accim"
python -u tools\smoke_resume_runner.py --mode stage1-only --accim-results-root "D:\accim_results" --out-dir "results_parametric_smoke_resume"
python -u tools\smoke_resume_runner.py --mode stage2-only --accim-results-root "D:\accim_results" --out-dir "results_parametric_smoke_resume"
```

## Checklist

Consulta `tools/CHECKLIST_smoke_resume.md`.

