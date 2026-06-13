import json
import re
import traceback
from datetime import datetime
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:\Python\accim")
PREV_REPORT = ROOT / "tools" / "notebook_execution_report.json"
RERUN_REPORT = ROOT / "tools" / "notebook_rerun_report.json"
RERUN_LOG = ROOT / "tools" / "notebook_rerun_progress.log"


def log(line: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with RERUN_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")


def write_report(results):
    data = {
        "total": len(results),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "error": sum(1 for r in results if r["status"] == "error"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "results": results,
    }
    RERUN_REPORT.write_text(json.dumps(data, indent=2), encoding="utf-8")


def force_single_process_cell_source(source: str) -> str:
    # Force notebooks that define PROCESSES to run sequentially and avoid BrokenProcessPool on Windows.
    source = re.sub(r"(?m)^(\s*PROCESSES\s*=\s*).*$", r"\g<1>1", source)
    source = re.sub(r"processes\s*=\s*PROCESSES", "processes=1", source)
    source = re.sub(r"processes\s*=\s*\d+", "processes=1", source)
    return source


if not PREV_REPORT.exists():
    raise FileNotFoundError(f"Previous report not found: {PREV_REPORT}")

prev = json.loads(PREV_REPORT.read_text(encoding="utf-8"))
failed_paths = [Path(r["notebook"]) for r in prev.get("results", []) if r.get("status") == "error"]

results = []
RERUN_LOG.write_text("", encoding="utf-8")
log(f"Starting rerun of failed notebooks: {len(failed_paths)} targets")

for nb_path in failed_paths:
    item = {
        "notebook": str(nb_path),
        "exists": nb_path.exists(),
        "status": "skipped",
        "error": None,
    }

    if not nb_path.exists():
        log(f"SKIP missing notebook: {nb_path}")
        results.append(item)
        write_report(results)
        continue

    log(f"Inspecting: {nb_path}")

    bootstrap_inserted = False
    try:
        with nb_path.open("r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        code_cells = [c for c in nb.cells if c.get("cell_type") == "code"]
        item["code_cells"] = len(code_cells)

        original_sources = {}
        for idx, cell in enumerate(nb.cells):
            if cell.get("cell_type") != "code":
                continue
            original_sources[idx] = cell.get("source", "")
            cell["source"] = force_single_process_cell_source(cell.get("source", ""))

        bootstrap = nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "import os\n"
            "import sys\n"
            f"__file__ = r'''{str(nb_path)}'''\n"
            f"REPO_ROOT = Path(r'''{str(ROOT)}''')\n"
            "if str(REPO_ROOT) not in sys.path:\n"
            "    sys.path.insert(0, str(REPO_ROOT))\n"
            "os.chdir(str(REPO_ROOT))\n"
        )
        nb.cells.insert(0, bootstrap)
        bootstrap_inserted = True

        log(f"EXEC start: {nb_path}")
        client = NotebookClient(
            nb,
            timeout=7200,
            kernel_name="python3",
            resources={"metadata": {"path": str(ROOT)}},
            allow_errors=False,
        )
        client.execute()

        if bootstrap_inserted:
            nb.cells.pop(0)
            bootstrap_inserted = False

        # Restore original code sources so only outputs/execution_count are updated.
        for idx, src in original_sources.items():
            if idx < len(nb.cells) and nb.cells[idx].get("cell_type") == "code":
                nb.cells[idx]["source"] = src

        with nb_path.open("w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        item["status"] = "ok"
        log(f"EXEC ok: {nb_path}")

    except Exception:
        if bootstrap_inserted and nb.cells and nb.cells[0].get("cell_type") == "code":
            nb.cells.pop(0)
        item["status"] = "error"
        item["error"] = traceback.format_exc(limit=12)
        log(f"EXEC error: {nb_path}")

    results.append(item)
    write_report(results)

log("Rerun complete")
write_report(results)
print(str(RERUN_REPORT))

