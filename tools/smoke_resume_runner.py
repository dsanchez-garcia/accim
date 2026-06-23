"""Smoke runner for ParametricSimulation resume and output-root checks.

This utility validates two things with a small plan:
- relative out_dir resolution via accim_results_root,
- checkpoint-based resume behavior across interrupted runs.

It is designed for Windows/PowerShell usage and keeps API usage aligned with
ParametricSimulation.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Sequence, Tuple

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

PREFERRED_METERS = [
    "DistrictHeating:Facility",
    "DistrictCooling:Facility",
]


def collect_input_files(idf_glob: str, epw_glob: str) -> Tuple[List[str], List[str]]:
    """Collect IDF/EPW files from the current working directory."""
    all_idfs = sorted(glob.glob(idf_glob))
    all_epws = sorted(glob.glob(epw_glob))
    if not all_idfs:
        raise FileNotFoundError(f"No IDF files found with pattern: {idf_glob}")
    if not all_epws:
        raise FileNotFoundError(f"No EPW files found with pattern: {epw_glob}")
    return all_idfs, all_epws


def normalize_idf_name(idf_name: str) -> str:
    """Return IDF stem for names with or without .idf extension."""
    return idf_name[:-4] if idf_name.lower().endswith(".idf") else idf_name


def require_pandas():
    """Import pandas lazily and raise a clear message if unavailable."""
    try:
        import pandas as pd  # type: ignore
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pandas is required for this command. Install dependencies from requirements-dev.txt."
        ) from exc
    return pd


def build_cross_plan_rows(idf_paths: Sequence[str], epw_paths: Sequence[str], max_cases: int) -> List[dict]:
    """Build deterministic IDF-EPW pairs as plain rows (pandas-free)."""
    rows = []
    seen_pairs = set()
    for idf in idf_paths:
        idf_stem = normalize_idf_name(Path(idf).name)
        for epw in epw_paths:
            row = {"idf": idf_stem, "epw": Path(epw).name}
            pair = (row["idf"], row["epw"])
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            rows.append(row)
            if max_cases > 0 and len(rows) >= max_cases:
                return rows
    return rows


def build_cross_plan(idf_paths: Sequence[str], epw_paths: Sequence[str], max_cases: int):
    """Build a deterministic IDF-EPW cross plan with optional cap."""
    pd = require_pandas()
    rows = build_cross_plan_rows(idf_paths=idf_paths, epw_paths=epw_paths, max_cases=max_cases)
    plan_df = pd.DataFrame(rows).reset_index(drop=True)
    return plan_df


def prepare_buildings_for_outputs(buildings: Sequence[object]) -> None:
    """Ensure simulation files include CSV/MTR/ESO exports with hourly variables."""
    for building in buildings:
        for obj in building.idfobjects["output:variable"]:
            obj.Reporting_Frequency = "Hourly"

        output_control_files = building.idfobjects["outputcontrol:files"]
        if output_control_files:
            output_control_files[0].Output_CSV = "Yes"
            output_control_files[0].Output_MTR = "Yes"
            output_control_files[0].Output_ESO = "Yes"
        else:
            building.newidfobject(
                key="OUTPUTCONTROL:FILES",
                Output_CSV="Yes",
                Output_MTR="Yes",
                Output_ESO="Yes",
            )


def sanitize_idfs(idf_paths: Sequence[str], in_place: bool) -> Tuple[List[str], str | None]:
    """Remove accents from IDFs in place or in temporary copies."""
    from accim.utils import remove_accents_in_idf

    if in_place:
        for idf in idf_paths:
            remove_accents_in_idf(idf)
        return list(idf_paths), None

    temp_dir = tempfile.mkdtemp(prefix="accim_smoke_idf_")
    copied_idfs: List[str] = []
    for idf in idf_paths:
        dst = os.path.join(temp_dir, Path(idf).name)
        shutil.copy2(idf, dst)
        remove_accents_in_idf(dst)
        copied_idfs.append(dst)
    return copied_idfs, temp_dir


def select_output_meters(sim, max_meters: int):
    """Select output meters using preferred names, with fallback to discovered meters."""
    pd = require_pandas()
    available_outputs = sim.discover_available_outputs(
        idf_scope="first",
        reduce_sim_time=True,
        refresh=True,
    )
    meters_df = available_outputs.get("meters", pd.DataFrame())
    if meters_df.empty or "key_name" not in meters_df.columns:
        raise RuntimeError("No available meters detected in discover_available_outputs().")

    meters_df = meters_df.copy()
    if "frequency" not in meters_df.columns:
        meters_df["frequency"] = "Hourly"

    preferred_set = {name.upper() for name in PREFERRED_METERS}
    preferred_df = meters_df[meters_df["key_name"].astype(str).str.upper().isin(preferred_set)].copy()

    if preferred_df.empty:
        selected_df = (
            meters_df[["key_name", "frequency"]]
            .drop_duplicates(subset=["key_name", "frequency"])
            .head(max_meters)
            .reset_index(drop=True)
        )
    else:
        selected_df = (
            preferred_df[["key_name", "frequency"]]
            .drop_duplicates(subset=["key_name", "frequency"])
            .head(max_meters)
            .reset_index(drop=True)
        )

    if selected_df.empty:
        raise RuntimeError("No output meters could be selected for smoke run.")

    selected_df["frequency"] = selected_df["frequency"].astype(str).replace("", "Hourly")
    selected_meters = selected_df["key_name"].astype(str).drop_duplicates().tolist()
    return selected_meters, selected_df


def create_configured_simulation(idf_paths: Sequence[str], epw_paths: Sequence[str], args: argparse.Namespace):
    """Instantiate ParametricSimulation with conservative defaults for smoke checks."""
    from besos import eppy_funcs as ef
    from accim.parametric_and_optimisation.main import ParametricSimulation

    working_idfs, temp_dir = sanitize_idfs(idf_paths=idf_paths, in_place=args.in_place_accent_clean)
    try:
        buildings = [ef.get_building(idf) for idf in working_idfs]
        prepare_buildings_for_outputs(buildings)

        sim = ParametricSimulation(
            buildings=buildings,
            epws=[Path(epw).name for epw in epw_paths],
            parameters_type=None,
            bypass_addAccis=True,
            accim_results_root=args.accim_results_root,
        )

        selected_meters, selected_meter_df = select_output_meters(sim=sim, max_meters=args.max_meters)
        sim.set_output_meters_to_idf(
            output_meters=selected_meters,
            idf_scope="all",
            validation_idf_scope="first",
        )
        sim.set_outputs_for_simulation(df_output_meter=selected_meter_df)
        sim.set_parameters()
        sim.set_problem()
        return sim, temp_dir
    except Exception:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def run_stage(
    stage_name: str,
    idf_paths: Sequence[str],
    epw_paths: Sequence[str],
    plan_df,
    resume_from_checkpoint: bool,
    args: argparse.Namespace,
):
    """Run one simulation stage and always release temporary IDF copies."""
    sim = None
    temp_dir = None
    try:
        sim, temp_dir = create_configured_simulation(idf_paths=idf_paths, epw_paths=epw_paths, args=args)
        sim.sampling_custom(plan_df[["idf", "epw"]])

        print(
            f"[{stage_name}] cases={len(plan_df)}, resume_from_checkpoint={resume_from_checkpoint}, "
            f"out_dir={args.out_dir}, root={args.accim_results_root or '<none>'}"
        )

        outputs_df = sim.run_parametric_simulation(
            epws=[Path(epw).name for epw in epw_paths],
            out_dir=args.out_dir,
            df=sim.parameters_values_df,
            processes=args.processes,
            keep_dirs=True,
            keep_input=True,
            batch_size=args.batch_size,
            checkpoint_every_batch=True,
            resume_from_checkpoint=resume_from_checkpoint,
        )

        print(f"[{stage_name}] done: output rows={len(outputs_df)}")
        return outputs_df
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


def split_stage_plan(full_plan_df, stage1_cases: int):
    """Return stage-1 subset used to seed checkpoint for resume validation."""
    if full_plan_df.empty:
        raise ValueError("The full simulation plan is empty.")
    if len(full_plan_df) == 1:
        return full_plan_df.copy()

    capped = max(1, min(int(stage1_cases), len(full_plan_df) - 1))
    return full_plan_df.head(capped).reset_index(drop=True)


def split_stage_rows(full_rows: List[dict], stage1_cases: int) -> List[dict]:
    """Pure-python equivalent of split_stage_plan used by self-test."""
    if len(full_rows) == 0:
        raise ValueError("The full simulation plan is empty.")
    if len(full_rows) == 1:
        return list(full_rows)
    capped = max(1, min(int(stage1_cases), len(full_rows) - 1))
    return list(full_rows[:capped])


def print_plan_summary(full_plan_df, stage1_plan_df, args: argparse.Namespace) -> None:
    """Print a concise plan summary before running heavy tasks."""
    print("\nSmoke plan summary")
    print("-" * 80)
    print(f"Mode                 : {args.mode}")
    print(f"IDFs x EPWs (rows)   : {len(full_plan_df)}")
    print(f"Stage-1 rows         : {len(stage1_plan_df)}")
    print(f"Output dir           : {args.out_dir}")
    print(f"accim_results_root   : {args.accim_results_root or '<none>'}")
    print(f"Processes / batch    : {args.processes} / {args.batch_size}")
    print("\nPlan preview:")
    print(full_plan_df.head(20).to_string(index=False))


def run_self_test() -> int:
    """Validate pure-python logic with no BESOS/EnergyPlus calls."""
    sample_idfs = ["A.idf", "B.idf", "C.idf"]
    sample_epws = ["x.epw", "y.epw"]
    rows = build_cross_plan_rows(sample_idfs, sample_epws, max_cases=100)
    assert len(rows) == 6, f"Unexpected cross-plan size: {len(rows)}"

    stage1_rows = split_stage_rows(rows, stage1_cases=2)
    assert len(stage1_rows) == 2, f"Unexpected stage1 size: {len(stage1_rows)}"

    one_case_rows = build_cross_plan_rows(["A.idf"], ["x.epw"], max_cases=10)
    one_case_stage = split_stage_rows(one_case_rows, stage1_cases=2)
    assert len(one_case_stage) == 1, "Single-case stage split should preserve the only case."

    print("Self-test passed: smoke-runner planning logic is consistent.")
    return 0


def run(args: argparse.Namespace) -> int:
    """Execute requested smoke workflow."""
    all_idfs, all_epws = collect_input_files(idf_glob=args.idf_glob, epw_glob=args.epw_glob)

    selected_idfs = all_idfs[: args.max_idfs] if args.max_idfs > 0 else all_idfs
    selected_epws = all_epws[: args.max_epws] if args.max_epws > 0 else all_epws

    full_plan_df = build_cross_plan(
        idf_paths=selected_idfs,
        epw_paths=selected_epws,
        max_cases=args.max_cases,
    )
    if full_plan_df.empty:
        raise ValueError("The generated smoke plan is empty. Check IDF/EPW filters.")

    stage1_plan_df = split_stage_plan(full_plan_df=full_plan_df, stage1_cases=args.stage1_cases)
    print_plan_summary(full_plan_df=full_plan_df, stage1_plan_df=stage1_plan_df, args=args)

    if args.dry_run:
        print("\nDry-run enabled. No simulation was launched.")
        return 0

    if args.mode in ("stage1-only", "two-step"):
        run_stage(
            stage_name="stage1",
            idf_paths=selected_idfs,
            epw_paths=selected_epws,
            plan_df=stage1_plan_df,
            resume_from_checkpoint=False,
            args=args,
        )

    if args.mode == "stage1-only":
        print("\nStage-1 completed. Re-run with --mode stage2-only to validate resume.")
        return 0

    if args.mode in ("stage2-only", "two-step", "full"):
        target_plan_df = full_plan_df if args.mode != "full" else full_plan_df
        outputs_df = run_stage(
            stage_name="stage2" if args.mode != "full" else "full",
            idf_paths=selected_idfs,
            epw_paths=selected_epws,
            plan_df=target_plan_df,
            resume_from_checkpoint=(args.mode != "full"),
            args=args,
        )

        expected_rows = len(full_plan_df)
        if len(outputs_df) < expected_rows:
            raise RuntimeError(
                f"Resume check failed: output rows={len(outputs_df)} < expected plan rows={expected_rows}."
            )

    print("\nSmoke workflow completed successfully.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke runner to validate ParametricSimulation resume and accim_results_root behavior."
    )
    parser.add_argument("--idf-glob", default="*.idf", help="Glob pattern for IDF files.")
    parser.add_argument("--epw-glob", default="*.epw", help="Glob pattern for EPW files.")
    parser.add_argument("--out-dir", default="results_parametric_smoke_resume", help="Output folder name/path.")
    parser.add_argument(
        "--accim-results-root",
        default=None,
        help="Optional root used to resolve relative out_dir without relying on environment variables.",
    )
    parser.add_argument(
        "--mode",
        choices=["two-step", "stage1-only", "stage2-only", "full"],
        default="two-step",
        help="two-step validates resume in one call; stage1/stage2 split it in two calls.",
    )
    parser.add_argument("--processes", type=int, default=2, help="Worker processes for simulation runs.")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for checkpointed runs.")
    parser.add_argument("--stage1-cases", type=int, default=8, help="Rows to execute in stage-1 before resume.")
    parser.add_argument("--max-idfs", type=int, default=3, help="Max IDFs to include in smoke plan (0=all).")
    parser.add_argument("--max-epws", type=int, default=2, help="Max EPWs to include in smoke plan (0=all).")
    parser.add_argument("--max-cases", type=int, default=24, help="Max plan rows after cross join (0=all).")
    parser.add_argument("--max-meters", type=int, default=2, help="Max meter outputs to keep in smoke run.")
    parser.add_argument(
        "--in-place-accent-clean",
        action="store_true",
        help="If set, remove accents directly in source IDFs. Default uses temporary copies.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build plan and print checks without launching simulations.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run internal lightweight tests and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())



