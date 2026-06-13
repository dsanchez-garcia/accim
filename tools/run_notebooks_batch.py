import json
import traceback
from datetime import datetime
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:\Python\accim")
REPORT_PATH = ROOT / "tools" / "notebook_execution_report.json"
LOG_PATH = ROOT / "tools" / "notebook_execution_progress.log"

# Execute optimisation before analysis so dependent artefacts (e.g., optimisation pickle) exist.
TARGET_NOTEBOOKS = [
    ROOT / "tutorial_optimisation_accim_custom_model.ipynb",
    ROOT / "tutorial_analysis_accim_custom_model.ipynb",
    ROOT / "jupyter notebooks" / "tutorial_optimisation_accim_custom_model.ipynb",
    ROOT / "jupyter notebooks" / "tutorial_analysis_accim_custom_model.ipynb",
]
TARGET_NOTEBOOKS.extend(sorted((ROOT / "jupyter notebooks" / "parametric_and_optimisation_series").glob("*.ipynb")))


def write_progress(line: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {line}\n")


def write_report(results):
    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "error": sum(1 for r in results if r["status"] == "error"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")


results = []
LOG_PATH.write_text("", encoding="utf-8")
write_progress("Starting batch notebook execution")

for nb_path in TARGET_NOTEBOOKS:
    item = {
        "notebook": str(nb_path),
        "exists": nb_path.exists(),
        "status": "skipped",
        "error": None,
    }

    if not nb_path.exists():
        write_progress(f"SKIP missing notebook: {nb_path}")
        results.append(item)
        write_report(results)
        continue

    write_progress(f"Inspecting: {nb_path}")

    try:
        with nb_path.open("r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        code_cells = [c for c in nb.cells if c.get("cell_type") == "code"]
        unexecuted_before = sum(1 for c in code_cells if c.get("execution_count") is None)

        item["code_cells"] = len(code_cells)
        item["unexecuted_before"] = unexecuted_before

        if len(code_cells) == 0 or unexecuted_before == 0:
            item["status"] = "skipped"
            item["unexecuted_after"] = 0
            write_progress(f"SKIP already executed: {nb_path}")
            results.append(item)
            write_report(results)
            continue

        write_progress(
            f"EXEC start: {nb_path} | code_cells={len(code_cells)} | unexecuted_before={unexecuted_before}"
        )

        bootstrap_cell = nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "import os\n"
            "import sys\n"
            f"__file__ = r'''{str(nb_path)}'''\n"
            f"REPO_ROOT = Path(r'''{str(ROOT)}''')\n"
            "if str(REPO_ROOT) not in sys.path:\n"
            "    sys.path.insert(0, str(REPO_ROOT))\n"
            "os.chdir(str(REPO_ROOT))\n"
        )
        nb.cells.insert(0, bootstrap_cell)

        client = NotebookClient(
            nb,
            timeout=7200,
            kernel_name="python3",
            # Run from repo root to resolve shared sample files and relative imports.
            resources={"metadata": {"path": str(ROOT)}},
            allow_errors=False,
        )
        client.execute()

        # Remove bootstrap cell before persisting notebook changes.
        nb.cells.pop(0)

        with nb_path.open("w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        code_cells_after = [c for c in nb.cells if c.get("cell_type") == "code"]
        unexecuted_after = sum(1 for c in code_cells_after if c.get("execution_count") is None)

        item["status"] = "ok"
        item["unexecuted_after"] = unexecuted_after
        write_progress(f"EXEC ok: {nb_path} | unexecuted_after={unexecuted_after}")
    except Exception:
        item["status"] = "error"
        item["error"] = traceback.format_exc(limit=12)
        write_progress(f"EXEC error: {nb_path}")

    results.append(item)
    write_report(results)

write_progress("Batch execution complete")
write_report(results)
print(str(REPORT_PATH))
