from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(r"D:\Python\accim\jupyter notebooks\parametric_and_optimisation_series")

# English file names and minimal scaffold content.
NOTEBOOK_SPECS = [
    (
        "00_quickstart_environment_and_first_run",
        "00 - Quickstart: environment and first run",
        "Goal: execute a minimal parametric simulation with `ParametricSimulation`.",
        [
            "Load IDF and EPW",
            "Define outputs",
            "Define parameters",
            "Sample and run",
        ],
        "from accim.parametric_and_optimisation.main import ParametricSimulation",
    ),
    (
        "01_parametric_accim_custom_model",
        "01 - Parametric ACCIM custom model",
        "Goal: walk through a full workflow for `parameters_type='accim custom model'`.",
        [
            "Define custom comfort parameters",
            "Sample parameter values",
            "Run simulation",
            "Review results",
        ],
        "from accim.parametric_and_optimisation.main import ParametricSimulation",
    ),
    (
        "02_parametric_accim_predefined_model",
        "02 - Parametric ACCIM predefined model",
        "Goal: use `AccimPredefModelsParamSim` with option-based parameter combinations.",
        [
            "Initialize predefined model simulation",
            "Select allowed parameters",
            "Build combinations",
            "Run and inspect outputs",
        ],
        "from accim.parametric_and_optimisation.main import AccimPredefModelsParamSim",
    ),
    (
        "03_parametric_apmv_setpoints",
        "03 - Parametric APMV setpoints",
        "Goal: run a parametric workflow with `parameters_type='apmv setpoints'`.",
        [
            "Configure APMV parameters",
            "Define outputs",
            "Sample and run",
            "Compare against a baseline",
        ],
        "from accim.parametric_and_optimisation.main import ParametricSimulation",
    ),
    (
        "04_outputs_preflight_and_output_control",
        "04 - Outputs preflight and output control",
        "Goal: discover, select, clean, and apply outputs in a robust workflow.",
        [
            "Discover available outputs",
            "Build a validated output selection",
            "Apply preflight cleanup",
            "Verify final IDF output objects",
        ],
        "from accim.parametric_and_optimisation.main import ParametricSimulation",
    ),
    (
        "05_sampling_strategies_and_sensitivity_analysis",
        "05 - Sampling strategies and sensitivity analysis",
        "Goal: connect sampling choices (`Sobol`, `Morris`) with sensitivity analysis outputs.",
        [
            "Define a range-based parameter problem",
            "Run Sobol sampling and analysis",
            "Run Morris sampling and analysis",
            "Compare interpretation across EPWs",
        ],
        "from accim.parametric_and_optimisation.main import ParametricSimulation",
    ),
    (
        "06_multi_idf_multi_epw_and_custom_plan",
        "06 - Multi-IDF, multi-EPW, and custom plans",
        "Goal: run custom campaign plans with explicit `idf`/`epw` combinations.",
        [
            "Load multiple IDFs and EPWs",
            "Build a custom plan DataFrame",
            "Run the cross-scenario simulation",
            "Validate coverage and categories",
        ],
        "from accim.parametric_and_optimisation.main import ParametricSimulation",
    ),
    (
        "07_basic_multiobjective_optimization",
        "07 - Basic multi-objective optimization",
        "Goal: run a minimal optimization and inspect the resulting Pareto front.",
        [
            "Define optimization parameters and outputs",
            "Estimate simulation cost",
            "Run `NSGAII`",
            "Inspect `pareto-optimal` rows",
        ],
        "from accim.parametric_and_optimisation.main import OptimisationSimulation",
    ),
    (
        "08_advanced_optimization_algorithms_and_constraints",
        "08 - Advanced optimization: algorithms and constraints",
        "Goal: compare algorithms and include constraints in optimization runs.",
        [
            "Define constraints and bounds",
            "Run alternative algorithms",
            "Tune algorithm options",
            "Compare resulting fronts",
        ],
        "from accim.parametric_and_optimisation.main import OptimisationSimulation",
    ),
    (
        "09_hourly_monthly_postprocessing_normalization_and_plots",
        "09 - Hourly/monthly post-processing, normalization, and plots",
        "Goal: transform outputs and generate analysis plots for interpretation.",
        [
            "Expand to hourly results",
            "Aggregate to monthly results",
            "Normalize per floor area if needed",
            "Generate key plots",
        ],
        "from accim.parametric_and_optimisation.main import ParametricSimulation, OptimisationSimulation",
    ),
    (
        "10_decision_support_robustness_and_session_merge",
        "10 - Decision support, robustness, and session merge",
        "Goal: select compromise solutions, test robustness, and merge sessions.",
        [
            "Compute best compromise solutions",
            "Evaluate weather robustness",
            "Cluster solution families",
            "Merge outputs from multiple sessions",
        ],
        "from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation",
    ),
]


def render_py(name: str, title: str, goal: str, checklist: list[str], import_line: str) -> str:
    markdown_lines = [f"# {title}", "", goal, "", "## Checklist"] + [f"- {item}" for item in checklist]
    py_lines = ["# %% [markdown]"]
    py_lines.extend([f"# {line}" if line else "#" for line in markdown_lines])
    py_lines.append("")
    py_lines.append("# %%")
    py_lines.append("# TODO: complete in the next iteration")
    py_lines.append(import_line)
    py_lines.append("")
    return "\n".join(py_lines)


def py_to_notebook(py_path: Path, ipynb_path: Path) -> None:
    lines = py_path.read_text(encoding="utf-8").splitlines()
    cells = []
    current = []
    current_type = None

    def flush_cell() -> None:
        nonlocal current, current_type
        if current_type is None:
            return
        source = "\n".join(current).rstrip("\n")
        cells.append(
            {
                "cell_type": current_type,
                "metadata": {},
                "source": source,
                "execution_count": None if current_type == "code" else None,
                "outputs": [] if current_type == "code" else None,
            }
        )
        current = []
        current_type = None

    for line in lines:
        if line.startswith("# %%"):
            flush_cell()
            current_type = "markdown" if "[markdown]" in line else "code"
            continue

        if current_type is None:
            continue

        if current_type == "markdown":
            if line.startswith("# "):
                current.append(line[2:])
            elif line == "#":
                current.append("")
            else:
                current.append(line)
        else:
            current.append(line)

    flush_cell()

    normalized_cells = []
    for cell in cells:
        if cell["cell_type"] == "markdown":
            normalized_cells.append(
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": cell["source"],
                }
            )
        else:
            normalized_cells.append(
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": cell["source"],
                }
            )

    nb = {
        "cells": normalized_cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    ipynb_path.write_text(json.dumps(nb, ensure_ascii=True, indent=1) + "\n", encoding="utf-8")


def write_readme() -> None:
    lines = [
        "# Notebook Series: `parametric_and_optimisation`",
        "",
        "This folder is generated from Python notebook sources (`.py` with `# %%` cells).",
        "Workflow: edit `.py` first, then regenerate `.ipynb`.",
        "",
        "## Notebook files",
        "",
    ]
    for idx, spec in enumerate(NOTEBOOK_SPECS, start=1):
        lines.append(f"{idx}. `{spec[0]}.py` -> `{spec[0]}.ipynb`")

    lines.extend(
        [
            "",
            "## Regeneration command",
            "",
            "```powershell",
            "python -u tools/build_parametric_optimisation_notebooks.py",
            "```",
            "",
            "## Notes",
            "",
            "- All notebook text is in English.",
            "- The `.ipynb` files are generated artifacts.",
        ]
    )
    (BASE_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cleanup_legacy_files() -> None:
    legacy = [
        "00_quickstart_entorno_y_primer_run.ipynb",
        "01_parametrico_accim_custom_model.ipynb",
        "02_parametrico_accim_predefined_model.ipynb",
        "03_parametrico_apmv_setpoints.ipynb",
        "04_outputs_preflight_y_control_de_salidas.ipynb",
        "05_estrategias_de_muestreo_y_sensibilidad.ipynb",
        "06_flujos_multi_idf_multi_epw_y_custom_plan.ipynb",
        "07_optimizacion_multiobjetivo_basica.ipynb",
        "08_optimizacion_avanzada_algoritmos_y_restricciones.ipynb",
        "09_postproceso_horario_mensual_normalizacion_plots.ipynb",
        "10_decision_robustez_y_merge_de_sesiones.ipynb",
    ]
    for name in legacy:
        path = BASE_DIR / name
        if path.exists():
            path.unlink()


def main() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_legacy_files()

    for name, title, goal, checklist, import_line in NOTEBOOK_SPECS:
        py_path = BASE_DIR / f"{name}.py"
        ipynb_path = BASE_DIR / f"{name}.ipynb"
        # Keep edited .py notebook sources; create only missing templates.
        if not py_path.exists():
            py_path.write_text(render_py(name, title, goal, checklist, import_line), encoding="utf-8")
        py_to_notebook(py_path, ipynb_path)

    write_readme()
    print(f"Generated {len(NOTEBOOK_SPECS)} .py files and {len(NOTEBOOK_SPECS)} .ipynb files in: {BASE_DIR}")


if __name__ == "__main__":
    main()

