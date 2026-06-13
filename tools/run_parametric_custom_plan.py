"""Robust runner for ACCIM parametric simulations with manual IDF-EPW pairing.

This script is based on the workflow shared by the user and adds:
- explicit validation when the custom plan is empty,
- safer meter selection (case-insensitive + dedup),
- optional accent cleanup without touching original IDFs,
- dry-run and self-test modes.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Sequence, Tuple

if TYPE_CHECKING:
    import pandas as pd

DEFAULT_CITY_TO_ZONE: Dict[str, str] = {
    "leon": "E",
    "seville": "B",
    "madrid": "D",
    "malaga": "A",
    "granada": "C",
}


def collect_input_files(idf_glob: str, epw_glob: str) -> Tuple[List[str], List[str]]:
    """Collect IDF/EPW files from current working directory."""
    all_idfs = sorted(glob.glob(idf_glob))
    all_epws = sorted(glob.glob(epw_glob))
    if not all_idfs:
        raise FileNotFoundError(f"No IDF files found with pattern: {idf_glob}")
    if not all_epws:
        raise FileNotFoundError(f"No EPW files found with pattern: {epw_glob}")
    return all_idfs, all_epws


def build_custom_plan_rows(
    idf_paths: Sequence[str],
    epw_paths: Sequence[str],
    city_to_zone: Dict[str, str] | None = None,
) -> Tuple[List[dict], Dict[str, List[str]]]:
    """Build custom-plan rows from filename rules (no pandas required)."""
    city_to_zone = city_to_zone or DEFAULT_CITY_TO_ZONE

    idf_stems = [Path(idf).stem for idf in idf_paths]
    idfs_by_zone: Dict[str, List[str]] = {}
    for zone in {z.upper() for z in city_to_zone.values()}:
        token = f"_{zone.lower()}_"
        idfs_by_zone[zone] = [stem for stem in idf_stems if token in stem.lower()]

    rows = []
    unmatched_epws = []

    for epw in epw_paths:
        epw_name = Path(epw).name.lower()
        matched_city = None
        matched_zone = None

        for city, zone in city_to_zone.items():
            if city.lower() in epw_name:
                matched_city = city
                matched_zone = zone.upper()
                break

        if matched_zone is None:
            unmatched_epws.append(epw)
            continue

        candidate_idfs = idfs_by_zone.get(matched_zone, [])
        if not candidate_idfs:
            unmatched_epws.append(epw)
            continue

        for idf_stem in candidate_idfs:
            rows.append(
                {
                    "idf": idf_stem,
                    "epw": epw,
                    "city": matched_city,
                    "climate_zone": matched_zone,
                }
            )

    deduped_rows = []
    seen_pairs = set()
    for row in rows:
        pair = (row["idf"], row["epw"])
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        deduped_rows.append(row)
    deduped_rows = sorted(deduped_rows, key=lambda r: (r["idf"], r["epw"]))

    matched_idfs = {row["idf"] for row in deduped_rows}
    unmatched_idfs = sorted([idf for idf in idf_stems if idf not in matched_idfs])

    info = {
        "unmatched_epws": sorted(unmatched_epws),
        "unmatched_idfs": unmatched_idfs,
    }
    return deduped_rows, info


def build_custom_plan(
    idf_paths: Sequence[str],
    epw_paths: Sequence[str],
    city_to_zone: Dict[str, str] | None = None,
) -> Tuple["pd.DataFrame", Dict[str, List[str]]]:
    """Build the custom simulation plan as a pandas DataFrame."""
    import pandas as pd

    rows, info = build_custom_plan_rows(
        idf_paths=idf_paths,
        epw_paths=epw_paths,
        city_to_zone=city_to_zone,
    )
    custom_plan_df = pd.DataFrame(rows)
    return custom_plan_df, info


def get_category_rules() -> Tuple[dict, dict]:
    """Return EPW/IDF category mapping rules for preview and post-processing."""
    epw_mapping_rules = {
        "weather_type": {
            "tmy": "tmy",
            "met": "met",
            "long-term": [str(year) for year in range(2005, 2026)],
        },
        "city": {
            "granada": "granada",
            "seville": "seville",
            "malaga": "malaga",
            "madrid": "madrid",
            "leon": "leon",
        },
    }

    idf_mapping_rules = {
        "climate_zone": {
            "A": "_A_",
            "B": "_B_",
            "C": "_C_",
            "D": "_D_",
            "E": "_E_",
        },
        "performance": {
            "max": "max",
            "min": "min",
        },
        "building_type": {
            "MF": "MF_",
            "SF": "SF_",
        },
    }
    return epw_mapping_rules, idf_mapping_rules


def _idfobjects_case(building, key: str) -> list:
    """Read IDF objects with basic case-insensitive fallbacks."""
    candidates = [key, key.upper(), key.title()]
    for candidate in candidates:
        if candidate in building.idfobjects:
            return list(building.idfobjects[candidate])
    return []


def prepare_buildings_for_outputs(buildings: Sequence[object]) -> None:
    """Normalize output-related objects before creating the simulation class."""
    for building in buildings:
        for obj in _idfobjects_case(building, "Output:Variable"):
            if hasattr(obj, "Reporting_Frequency"):
                obj.Reporting_Frequency = "Hourly"

        output_ctrl = _idfobjects_case(building, "OutputControl:Files")
        if output_ctrl:
            output_ctrl[0].Output_CSV = "Yes"
            output_ctrl[0].Output_MTR = "Yes"
            output_ctrl[0].Output_ESO = "Yes"
        else:
            building.newidfobject(
                key="OUTPUTCONTROL:FILES",
                Output_CSV="Yes",
                Output_MTR="Yes",
                Output_ESO="Yes",
            )


def sanitize_idfs(
    idf_paths: Sequence[str],
    in_place: bool,
) -> Tuple[List[str], str | None]:
    """Remove accents from IDFs in place or on temporary copies."""
    from accim.utils import remove_accents_in_idf

    if in_place:
        for idf in idf_paths:
            remove_accents_in_idf(idf)
        return list(idf_paths), None

    tmp_dir = tempfile.mkdtemp(prefix="idf_ascii_")
    copied_idfs: List[str] = []
    for idf in idf_paths:
        dst = os.path.join(tmp_dir, Path(idf).name)
        shutil.copy2(idf, dst)
        remove_accents_in_idf(dst)
        copied_idfs.append(dst)
    return copied_idfs, tmp_dir


def select_target_meters(df_meters: "pd.DataFrame", target_meters: Sequence[str]) -> "pd.DataFrame":
    """Filter and deduplicate meters for simulation outputs."""
    if df_meters is None or df_meters.empty:
        raise RuntimeError("No Output:Meter rows were returned by get_outputs_df_from_testsim().")
    if "key_name" not in df_meters.columns:
        raise ValueError("Expected column 'key_name' in meters DataFrame.")

    data = df_meters.copy()
    if "frequency" not in data.columns:
        data["frequency"] = "Hourly"

    target = {m.upper() for m in target_meters}
    data = data[data["key_name"].astype(str).str.upper().isin(target)].copy()

    if data.empty:
        raise RuntimeError(
            "None of the requested meters were found in the test simulation outputs. "
            f"Requested: {list(target_meters)}"
        )

    data["frequency"] = data["frequency"].astype(str).replace("", "Hourly")
    data = data[["key_name", "frequency"]].drop_duplicates().reset_index(drop=True)
    return data


def print_plan_diagnostics(custom_plan_df: "pd.DataFrame", diagnostics: Dict[str, List[str]]) -> None:
    """Print key diagnostics before running heavy simulations."""
    print("\nCustom plan diagnostics")
    print("-" * 80)
    print(f"Rows in custom plan: {len(custom_plan_df)}")
    print(f"Unmatched EPWs: {len(diagnostics['unmatched_epws'])}")
    print(f"Unmatched IDFs: {len(diagnostics['unmatched_idfs'])}")

    if diagnostics["unmatched_epws"]:
        print("EPWs without mapping:")
        for epw in diagnostics["unmatched_epws"]:
            print(f"  - {epw}")

    if diagnostics["unmatched_idfs"]:
        print("IDFs without mapping:")
        for idf in diagnostics["unmatched_idfs"]:
            print(f"  - {idf}")

    if not custom_plan_df.empty:
        print("\nCustom plan preview:")
        print(custom_plan_df.head(20).to_string(index=False))


def run_self_test() -> int:
    """Fast logic test that does not launch EnergyPlus simulations."""
    sample_idfs = [
        "MF_Detached_A_max_South.idf",
        "SF_Detached_B_min_North.idf",
        "SF_Detached_C_max_West.idf",
        "MF_Detached_D_min_East.idf",
        "MF_Detached_E_max_North.idf",
    ]
    sample_epws = [
        "Malaga_tmy.epw",
        "Seville_2014.epw",
        "Granada_met.epw",
        "Madrid_long-term_2020.epw",
        "Leon_tmy.epw",
        "UnknownCity_tmy.epw",
    ]

    rows, info = build_custom_plan_rows(sample_idfs, sample_epws)
    pairs = {(row["idf"], row["epw"]) for row in rows}

    expected = {
        ("MF_Detached_A_max_South", "Malaga_tmy.epw"),
        ("SF_Detached_B_min_North", "Seville_2014.epw"),
        ("SF_Detached_C_max_West", "Granada_met.epw"),
        ("MF_Detached_D_min_East", "Madrid_long-term_2020.epw"),
        ("MF_Detached_E_max_North", "Leon_tmy.epw"),
    }

    assert pairs == expected, f"Unexpected mapping pairs. Found={pairs}"
    assert "UnknownCity_tmy.epw" in info["unmatched_epws"], "Expected unmatched EPW not found."

    print("Self-test passed: custom plan mapping logic is consistent.")
    return 0


def run(args: argparse.Namespace) -> int:
    """Execute workflow end to end."""
    all_idfs, all_epws = collect_input_files(args.idf_glob, args.epw_glob)

    # Heavy imports are kept here so --self-test remains lightweight.
    from besos import eppy_funcs as ef
    from accim.parametric_and_optimisation.main import ParametricSimulation

    working_idfs, temp_dir = sanitize_idfs(all_idfs, in_place=args.in_place_accent_clean)

    try:
        buildings = [ef.get_building(idf) for idf in working_idfs]
        prepare_buildings_for_outputs(buildings)

        custom_plan_df, diagnostics = build_custom_plan(working_idfs, all_epws)
        print_plan_diagnostics(custom_plan_df, diagnostics)

        if custom_plan_df.empty:
            raise ValueError(
                "custom_plan is empty. Check EPW/IDF names and mapping rules before running simulations."
            )

        sim = ParametricSimulation(
            buildings=buildings,
            epws=all_epws,
            parameters_type=None,
            bypass_addAccis=True,
        )

        epw_mapping_rules, idf_mapping_rules = get_category_rules()
        sim.set_category_mapping(
            epw_mapping_rules=epw_mapping_rules,
            idf_mapping_rules=idf_mapping_rules,
        )

        if not args.skip_category_preview:
            preview = sim.preview_category_mapping()
            print("\nEPW category preview:")
            print(preview["epw"].head(10).to_string(index=False))
            print("\nIDF category preview:")
            print(preview["idf"].head(10).to_string(index=False))

        target_meters = ["DistrictHeating:Facility", "DistrictCooling:Facility"]
        sim.set_output_meters_to_idf(
            output_meters=target_meters,
            validate=True,
            on_missing="warn",
            auto_filter=True,
        )

        outputs_from_testsim = sim.get_outputs_df_from_testsim(reduce_sim_time=True, idf_scope="all")
        df_meters_ts = outputs_from_testsim["meters"]
        df_output_meter = select_target_meters(df_meters_ts, target_meters)
        sim.set_outputs_for_simulation(df_output_meter=df_output_meter)

        sim.set_parameters()
        sim.set_problem()

        # sampling_custom only needs idf/epw columns.
        sim.sampling_custom(custom_plan_df[["idf", "epw"]])

        if args.dry_run:
            print("\nDry-run enabled. The plan was built and validated; simulation was skipped.")
            return 0

        cpu_count = os.cpu_count() or 1
        processes = max(1, min(args.processes, cpu_count))
        if processes != args.processes:
            print(
                f"Requested processes={args.processes} adjusted to {processes} based on CPU availability ({cpu_count})."
            )

        sim.run_parametric_simulation(
            epws=all_epws,
            out_dir=args.out_dir,
            df=sim.parameters_values_df,
            processes=processes,
            keep_dirs=True,
            keep_input=True,
        )

        print(f"\nDone. Results are in: {args.out_dir}")
        return 0
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run robust ACCIM parametric simulation with custom IDF-EPW mapping."
    )
    parser.add_argument("--idf-glob", default="*.idf", help="Glob pattern for IDF files.")
    parser.add_argument("--epw-glob", default="*.epw", help="Glob pattern for EPW files.")
    parser.add_argument("--out-dir", default="results_parametric", help="Output directory for simulation results.")
    parser.add_argument("--processes", type=int, default=8, help="Parallel worker processes.")
    parser.add_argument(
        "--in-place-accent-clean",
        action="store_true",
        help="If set, remove accents directly in source IDFs. Default uses temporary copies.",
    )
    parser.add_argument(
        "--skip-category-preview",
        action="store_true",
        help="Skip printing category mapping preview tables.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and validate plan without running EnergyPlus simulations.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run internal mapping test and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())


