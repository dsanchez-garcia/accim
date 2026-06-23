# Checklist de smoke + resume

Usa esta guia para validar rapidamente el flujo nuevo de `ParametricSimulation` (batch persistido + resume + `accim_results_root`).

## 1) Validacion ligera (sin simulacion)

- [ ] Ejecutar self-test del script.
- [ ] Ejecutar dry-run para revisar plan y rutas.

```powershell
Set-Location "D:\Python\accim"
python -u tools\smoke_resume_runner.py --self-test
python -u tools\smoke_resume_runner.py --dry-run --accim-results-root "D:\accim_results"
```

## 2) Simular interrupcion (stage-1)

- [ ] Ejecutar solo la primera fase para generar checkpoint parcial.
- [ ] Confirmar creacion de checkpoint y lotes.

```powershell
Set-Location "D:\Python\accim"
python -u tools\smoke_resume_runner.py --mode stage1-only --accim-results-root "D:\accim_results" --out-dir "results_parametric_smoke_resume"
```

Comprobar artefactos esperados (ruta final fuera del workspace):

- `D:\accim_results\results_parametric_smoke_resume\outputs_param_simulation_checkpoint_latest.pkl`
- `D:\accim_results\results_parametric_smoke_resume\outputs_param_simulation_checkpoint_latest.pkl.meta.json`
- `D:\accim_results\results_parametric_smoke_resume\outputs_param_simulation_batches\*.pkl`

## 3) Reanudar (stage-2)

- [ ] Reanudar usando el mismo `out_dir`.
- [ ] Revisar en consola que detecta tareas ya completadas.

```powershell
Set-Location "D:\Python\accim"
python -u tools\smoke_resume_runner.py --mode stage2-only --accim-results-root "D:\accim_results" --out-dir "results_parametric_smoke_resume"
```

## 4) Comprobacion rapida de metadata

- [ ] Verificar que `completed_tasks == total_tasks` en el meta del checkpoint.

```powershell
python -c "import json, pathlib; p=pathlib.Path(r'D:\accim_results\results_parametric_smoke_resume\outputs_param_simulation_checkpoint_latest.pkl.meta.json'); d=json.loads(p.read_text(encoding='utf-8')); print(d)"
```

## 5) Ejecucion en un solo paso (opcional)

- [ ] Ejecutar validacion de resume automatica stage1+stage2 en una sola llamada.

```powershell
Set-Location "D:\Python\accim"
python -u tools\smoke_resume_runner.py --mode two-step --accim-results-root "D:\accim_results" --out-dir "results_parametric_smoke_resume"
```

## 6) Lanzamiento de produccion (sugerencia)

- [ ] Mantener `checkpoint_every_batch=True` y `resume_from_checkpoint=True`.
- [ ] Empezar con `processes=2-4` y `batch_size=60-100`.
- [ ] Ejecutar fuera del IDE y guardar log.

```powershell
Set-Location "D:\Python\accim"
$env:PYTHONUNBUFFERED = "1"
python -u .\main_v02_error.py *>&1 | Tee-Object -FilePath ".\run_parametric_prod.log"
```

