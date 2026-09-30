"""Package-owned, opt-in workflows for the five single-zone paper experiments.

The public entry point is :func:`run_paper_experiment`. The scripts supply only
configuration; model preparation, metrics, checkpoints and postprocessing live
in accim. Importing this module never prepares models or launches simulations.
The ``load`` and ``prepare`` actions never invoke EnergyPlus; execution and
discovery require explicit ``--simulate``. Numerical/EMS validation remains a
separate obligation on the simulation PC.
"""

from __future__ import annotations

import argparse
import calendar
import csv
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
from importlib import metadata
import inspect
import json
import os
from pathlib import Path, PureWindowsPath
import pickle
import re
import shutil
import warnings

import numpy as np
import pandas as pd

__all__ = ["run_paper_experiment"]

PAPER_AREA_M2 = 312.0
AREA_RELATIVE_TOLERANCE = 0.01
EER, COP = 4.42, 4.95
POPULATION, EVALUATIONS = 20, 200
SEED = 20260930
SCHEMA = "paper-prepared-v2"
KEEP_EXTENSIONS = [".csv", ".err", ".idf", ".rdd", ".mdd", ".edd", ".end"]
REDUCER = "accim.parametric_and_optimisation.objectives:checked_sum_results"
ENERGY = "Electricity:HVAC [J]"
EN_DH = "EN16798 CatII occupied discomfort [C-hr]"
APMV_HOURS = "aPMV native discomfort [h]"
OCC_HOURS = "Occupied reporting time [h]"
PMV_INTEGRAL = "Occupied absolute Fanger PMV integral [h]"
FIXED_PMV_HOURS = "Occupied Fanger abs(PMV)>0.5 [h]"
PMOT = "Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature"
RMOT = "Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature"
EN_OUTPUT = "Paper EN16798 CatII Occupied Degree Hours"
PATH_COLUMNS = ("output_dir", "simulation_directory", "simulation_output_csv_path")


# %% Internal workflow support; reducers and EMS construction have their own APIs.
def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def portable_name(value):
    return PureWindowsPath(str(value).replace("/", "\\")).name


def climate_name(value):
    """Exact canonical climate matching; no fragile case/hyphen substring rules."""
    token = portable_name(value).casefold().removesuffix(".epw")
    token = re.sub(r"[^a-z0-9]", "", token)
    known = {
        "sevillepresent": "Present", "present": "Present",
        "sevillessp2452050": "SSP245_2050", "ssp2452050": "SSP245_2050",
        "sevillessp5852080": "SSP585_2080", "ssp5852080": "SSP585_2080",
    }
    if token not in known:
        raise ValueError(f"Unrecognised EPW/scenario {value!r}; no silent fallback category.")
    return known[token]


def canonical_column(name):
    name = re.sub(r"\[[^]]*]|\([^)]*\)", "", str(name).casefold())
    name = re.sub(r"_?kwh\s*/\s*m[²2]|_?kwh|_?c-hr", "", name)
    return re.sub(r"[^a-z0-9]", "", name)


def resolve_column(df, aliases, *, required=True):
    """Resolve once from real columns AND saved aliases; never choose match [0]."""
    wanted = {canonical_column(a) for a in aliases}
    matches = [c for c in df.columns if canonical_column(c) in wanted]
    if len(matches) == 1:
        return matches[0]
    if not matches and not required:
        return None
    raise ValueError(f"Missing/ambiguous column for {aliases}: {matches}; available={list(df.columns)}")


def finite_columns(df, columns):
    if df.empty or not df.columns.is_unique:
        raise ValueError("Empty results or duplicate column names.")
    for column in columns:
        if column not in df:
            raise KeyError(f"Required column {column!r} is absent.")
        try:
            values = pd.to_numeric(df[column], errors="raise")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Column {column!r} must contain scalar numeric results, not arrays or strings.") from exc
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"NaN/Inf in {column!r}; failed simulations must not become zero.")
        df[column] = values


@contextmanager
def working_directory(path):
    """BESOS needs basename EPWs; a controlled cwd also isolates discovery cache."""
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def simulation_class(spec):
    from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation
    return OptimisationSimulation if spec["kind"] == "optimisation" else ParametricSimulation


def require_api(spec):
    cls = simulation_class(spec)
    required: dict[str, tuple[str, ...]] = {
        "__init__": ("bypass_addAccis", "eer", "cop"),
        "set_output_readers": ("df_output_variable", "df_output_meter"),
        "discover_available_outputs": ("prefer", "refresh", "keep_available_outputs"),
        "set_output_variables_to_idf": ("mode", "validate", "on_missing"),
        "set_output_meters_to_idf": ("mode", "validate", "on_missing"),
        "add_comfort_metrics": ("metrics", "name_prefix", "idf_scope"),
        "set_building_floor_area": ("mode", "custom_area"),
        "normalize_outputs": ("df_types",),
    }
    if spec["kind"] == "parametric":
        required["run_parametric_simulation"] = ("df", "resume_plan_source", "checkpoint_every_batch")
        required["load_outputs_parametric"] = ("pickle_path", "outputs_names")
    else:
        required["run_optimisation"] = ("evaluations", "population_size", "checkpoint_every_case", "keep_df")
        required["load_outputs_optimisation"] = ("pickle_path", "minimize_outputs")
    for method, arguments in required.items():
        function = getattr(cls, method, None)
        if not callable(function) or not set(arguments).issubset(inspect.signature(function).parameters):
            raise RuntimeError(f"Installed accim lacks {method}{arguments}; install the reviewed source revision.")


def implementation_record():
    """Version strings alone do not identify the recent fixes used by the paper."""
    import accim
    module_file = accim.__file__
    if module_file is None:
        raise RuntimeError("Installed accim has no source file to fingerprint.")
    root = Path(module_file).resolve().parent
    versions = {}
    for package in ("accim", "besos", "eppy", "platypus-opt", "numpy", "pandas", "scipy"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not recorded"
    return {
        "versions": versions,
        "accim_python_sources": {
            p.relative_to(root).as_posix(): sha256_file(p) for p in sorted(root.rglob("*.py"))
        },
        "workflow_source_sha256": sha256_file(Path(__file__)),
    }


def objects(building, key):
    try:
        return list(building.idfobjects[key.upper()])
    except KeyError:
        return []


def single_target(building):
    """The paper is explicitly single-zone AND single resolved People target."""
    from accim.sim.apmv_setpoints import _resolve_targets
    zones, people = objects(building, "ZONE"), objects(building, "PEOPLE")
    targets = _resolve_targets(building)
    if len(zones) != 1 or len(people) != 1 or len(targets) != 1:
        raise ValueError("Expected one zone, one People object and one resolved control target; no multi-zone [0] selection.")
    target = targets[0]
    if target["zone_name"].casefold() != zones[0].Name.casefold():
        raise ValueError("People/Space resolution does not match the only zone.")
    equipment_zones = {str(o.Zone_Name).casefold() for o in objects(building, "ZoneHVAC:EquipmentConnections")}
    if equipment_zones and equipment_zones != {zones[0].Name.casefold()}:
        raise ValueError("Conditioned and occupied zone references differ.")
    return target


def metric_aliases(spec):
    if spec["comfort"] == "fixed_en":
        return [EN_DH, "EN16798 CatII discomfort (Ch)", EN_OUTPUT]
    return [APMV_HOURS, "Discomfort hours (h)"]


def build_session(spec, args, work):
    """Preparation only: copy inputs, mutate the copy in memory; no discovery."""
    from besos import eppy_funcs
    from accim.sim import apmv_setpoints
    from accim.parametric_and_optimisation.params_dicts import all_params
    from accim.utils import remove_accents_in_idf

    require_api(spec)
    input_files = [args.idf] + [args.epw_dir / name for name in spec["epws"]]
    missing = [str(p) for p in input_files if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing input files: {missing}")
    work.mkdir(parents=True, exist_ok=False)
    input_hashes = {p.name: sha256_file(p) for p in input_files}
    for path in input_files:
        shutil.copy2(path, work / path.name)
    copied_idf = work / args.idf.name
    remove_accents_in_idf(str(copied_idf))
    with working_directory(work):
        building = eppy_funcs.get_building(str(copied_idf))
        target = single_target(building)
        if objects(building, "EnergyManagementSystem:Program") or objects(building, "AirConditioner:VariableRefrigerantFlow"):
            raise ValueError("Use the pristine onlyGeometry IDF, not an already transformed ACCIS/aPMV model.")
        periods = objects(building, "RunPeriod")
        if len(periods) != 1:
            raise ValueError("The paper requires exactly one annual weather RunPeriod.")
        period = periods[0]
        if [int(period.Begin_Month), int(period.Begin_Day_of_Month), int(period.End_Month), int(period.End_Day_of_Month)] != [1, 1, 12, 31]:
            raise ValueError("RunPeriod is not Jan 1 through Dec 31; review the working model explicitly.")
        for control in objects(building, "SimulationControl"):
            control.Run_Simulation_for_Sizing_Periods = "No"
            control.Run_Simulation_for_Weather_File_Run_Periods = "Yes"
        kwargs = dict(buildings=[building], epws=list(spec["epws"]),
                      parameters_type=spec["parameters_type"], output_freqs=["hourly"], verbosemode=False)
        if spec["comfort"] == "apmv":
            apmv_setpoints.add_vrf_system(building, eer=EER, cop=COP, verbose_mode=False)
            # Explicit signs repair the reversed PMV defaults in the reviewed API.
            # The heating coefficient is the observed default, not a sampled global lambda.
            apmv_setpoints.apply_apmv_setpoints(
                building, outputs_freq=["hourly"], adap_coeff_heating=-0.293,
                pmv_cooling_sp=0.5, pmv_heating_sp=-0.5, verbose_mode=False,
            )
            session = simulation_class(spec)(**kwargs, bypass_addAccis=True)
        else:
            session = simulation_class(spec)(
                **kwargs, ScriptType=spec["ScriptType"], output_type="simplified",
                EnergyPlus_version=None, eer=EER, cop=COP,
            )
        target = single_target(building)
        if len(objects(building, "AirConditioner:VariableRefrigerantFlow")) != 1:
            raise ValueError("Expected exactly one VRF outdoor system after preparation.")
        if spec["comfort"] == "apmv":
            person = objects(building, "PEOPLE")[0]
            models = [str(getattr(person, f, "")).casefold() for f in person.fieldnames if "Thermal_Comfort_Model" in f]
            if "fanger" not in models:
                raise ValueError("VRF preparation did not enable Fanger on People.")
            for field in ("Activity_Level_Schedule_Name", "Work_Efficiency_Schedule_Name", "Clothing_Insulation_Schedule_Name", "Air_Velocity_Schedule_Name"):
                if not getattr(person, field, ""):
                    raise ValueError(f"Missing Fanger input {field}; do not invent metabolic/clothing schedules.")
        session.set_parameters(accis_params_dict=deepcopy(spec["parameters"]))
        # Valid representative values before future discovery (never n/a).
        representative = {k: (v[0] if isinstance(v, list) else sum(v) / 2) for k, v in spec["parameters"].items()}
        for key, value in representative.items():
            all_params[key](building, value)
        metric_report = session.add_comfort_metrics(
            metrics=("fixed_en",) if spec["comfort"] == "fixed_en" else ("fixed_pmv",),
            name_prefix="ACCIM_Paper", output_freqs=["hourly"],
        )
        requests, reader_variables = output_specifications(spec, building, target, metric_report)
        meters = pd.DataFrame([{"key_name": "Electricity:HVAC", "frequency": "Hourly", "name": ENERGY, "func": REDUCER}])
        reader_df = pd.DataFrame(reader_variables)
        apply_requests(session, requests, validate=False)
        session.set_output_readers(df_output_meter=meters, df_output_variable=reader_df)
        session.set_problem(minimize_outputs=[True, True] if spec["kind"] == "optimisation" else None)
        audit = geometry_and_schedule_audit(session, building)
        building.savecopy(str(work / "prepared_model.idf"))
    identity = {
        "schema": SCHEMA, "experiment": spec, "inputs": input_hashes,
        "implementation": implementation_record(), "area_m2": PAPER_AREA_M2,
        "eer": EER, "cop": COP, "seed": SEED, "population": POPULATION,
        "evaluations": EVALUATIONS, "keep_sim_files": "all", "requests": requests,
        "parameter_names": list(session.problem.names("inputs")),
        "objective_names": list(session.problem.names("outputs")),
        "comfort_policy": "fixed occupied EN +3/-4 with clamped RMOT" if spec["comfort"] == "fixed_en" else "native all-time moving-reference aPMV hours; fixed Fanger diagnostics only",
        "annual_weather_only": True,
    }
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
    manifest = {"identity": identity, "fingerprint": fingerprint, "audit": audit,
                "target": target, "requests": requests, "status": "prepared-not-simulated",
                "created": datetime.now().isoformat()}
    write_json(work.parent / "preparation.json", manifest)
    return session, manifest


def output_specifications(spec, building, target, metric_report):
    def request(role, variable, key="EMS", units="", kind="variable"):
        return {"role": role, "variable": variable, "key": key, "units": units, "kind": kind}
    metric_outputs = metric_report["outputs"]
    if metric_outputs.empty or metric_outputs["metric"].duplicated().any():
        raise ValueError("Paper workflow requires one output per metric (one target/frequency).")
    metric_names = metric_outputs.set_index("metric")["variable_name"].to_dict()
    requests = [request("energy", "Electricity:HVAC", units="J", kind="meter"),
                request("operative", "Zone Operative Temperature", target["zone_name"], "C"),
                request("people", "People Occupant Count", target["sensor_key"], ""),
                request("occupied", metric_names["occupied"], units="hr")]
    if spec["comfort"] == "fixed_en":
        requests += [request("comfort", metric_names["fixed_en"], units="C-hr"),
                     request("pmot", PMOT, target["sensor_key"], "C"),
                     request("rmot", RMOT, target["sensor_key"], "C")]
        for role, name in (("cooling_no_tolerance", "Adaptive Cooling Setpoint Temperature_No Tolerance"),
                           ("heating_no_tolerance", "Adaptive Heating Setpoint Temperature_No Tolerance"),
                           ("cooling_applied", "Adaptive Cooling Setpoint Temperature"),
                           ("heating_applied", "Adaptive Heating Setpoint Temperature")):
            requests.append(request(role, name, units="C"))
        readers = [(metric_names["fixed_en"], EN_DH)]
    else:
        counters = [o for o in objects(building, "EnergyManagementSystem:OutputVariable")
                    if o.Name.casefold().startswith("discomfortable total hours_")]
        if len(counters) != 1:
            raise ValueError(f"Expected ONE aPMV discomfort counter, found {[o.Name for o in counters]}.")
        counter = counters[0]
        if str(counter.Type_of_Data_in_Variable).casefold() != "summed" or str(counter.Update_Frequency).casefold() != "zonetimestep" or str(counter.Units).casefold() not in {"h", "hr"}:
            raise ValueError("aPMV counter semantics changed; review its aggregation before using it.")
        suffix = target["ems_suffix"]
        requests += [request("comfort", counter.Name, units="h"),
                     request("pmv", "Zone Thermal Comfort Fanger Model PMV", target["sensor_key"], ""),
                     request("pmv_integral", metric_names["pmv_integral"], units="hr"),
                     request("fixed_pmv_hours", metric_names["fixed_pmv_hours"], units="hr")]
        for role, name in (("apmv", "aPMV"), ("coefficient", "Adaptive Coefficient"),
                           ("cooling_no_tolerance", "aPMV Cooling Setpoint No Tolerance"),
                           ("heating_no_tolerance", "aPMV Heating Setpoint No Tolerance"),
                           ("cooling_applied", "aPMV Cooling Setpoint"),
                           ("heating_applied", "aPMV Heating Setpoint")):
            requests.append(request(role, f"{name}_{suffix}"))
        readers = [(counter.Name, APMV_HOURS)]
        if spec["kind"] == "parametric":
            readers += [(metric_names["pmv_integral"], PMV_INTEGRAL), (metric_names["occupied"], OCC_HOURS), (metric_names["fixed_pmv_hours"], FIXED_PMV_HOURS)]
    return requests, [{"key_value": "EMS", "variable_name": variable, "frequency": "Hourly", "name": alias, "func": REDUCER} for variable, alias in readers]


def apply_requests(session, requests, *, validate):
    # Wildcard requests preserve native requests without creating key-specific duplicates.
    variables = pd.DataFrame([{"key_value": "*", "variable_name": r["variable"], "frequency": "Hourly"}
                              for r in requests if r["kind"] == "variable"])
    meters = pd.DataFrame([{"key_name": r["variable"], "frequency": "Hourly"}
                          for r in requests if r["kind"] == "meter"])
    reports = [session.set_output_variables_to_idf(df_output_variable=variables, mode="append", validate=validate, on_missing="raise", auto_filter=False),
               session.set_output_meters_to_idf(df_output_meter=meters, mode="append", validate=validate, on_missing="raise", auto_filter=False)]
    if validate and any(not r.get("validated") or r.get("missing") for r in reports):
        raise RuntimeError(f"Output requests were NOT fully validated: {reports}")
    return reports


def geometry_and_schedule_audit(session, building):
    session.set_building_floor_area(mode="air-conditioned")
    value = session.building_floor_area
    if isinstance(value, dict):
        if len(value) != 1:
            raise ValueError("Expected one conditioned-area value.")
        value = next(iter(value.values()))
    measured = float(value)
    if not np.isfinite(measured) or measured <= 0:
        raise ValueError("Conditioned geometry area is not positive/finite.")
    zone = objects(building, "ZONE")[0]
    people = objects(building, "PEOPLE")[0]
    audit = {
        "conditioned_floor_surfaces_m2": measured, "paper_denominator_m2": PAPER_AREA_M2,
        "relative_difference": (measured - PAPER_AREA_M2) / PAPER_AREA_M2,
        "outside_one_percent": abs(measured - PAPER_AREA_M2) / PAPER_AREA_M2 > AREA_RELATIVE_TOLERANCE,
        "zone_declared_floor_area": str(getattr(zone, "Floor_Area", "")),
        "zone_multiplier": str(getattr(zone, "Multiplier", "")),
        "people_schedule": str(people.Number_of_People_Schedule_Name),
        "hvac_availability": "On 24/7 (ACCIM default; verify against intended office operation)",
        "warning": "Geometry helper uses floor surfaces, not Zone.Floor_Area/multipliers. Occupancy gate follows People schedule, not manuscript clock.",
    }
    session.set_building_floor_area(mode="custom", custom_area=PAPER_AREA_M2)
    print(json.dumps(audit, indent=2))
    return audit


# %% Future discovery is isolated and MUST be explicitly authorised on the other PC
def run_discovery(session, manifest, folder):
    with working_directory(folder / "work"):
        inventory = session.discover_available_outputs(
            prefer="rdd_mdd", refresh=True, reduce_sim_time=True,
            idf_scope="all", keep_available_outputs=True,
        )
        for kind in ("variables", "meters"):
            if inventory[kind].empty:
                raise RuntimeError(f"Discovery returned no {kind}.")
            inventory[kind].to_csv(folder / f"discovery_{kind}.csv", index=False)
        reports = apply_requests(session, manifest["requests"], validate=True)
    err = folder / "work" / "available_outputs" / "eplusout.err"
    if not err.is_file():
        raise FileNotFoundError("Discovery produced no .err; do not approve the campaign.")
    text = err.read_text(encoding="utf-8", errors="replace")
    if re.search(r"\*\*\s*(Severe|Fatal)\s*\*\*", text, re.I):
        raise RuntimeError(f"EnergyPlus severe/fatal errors in {err}.")
    if "energyplus completed successfully" not in text.casefold():
        raise RuntimeError(f"Discovery did not report successful completion in {err}.")
    csv_path = err.with_name("eplusout.csv")
    frame, mapping = read_hourly(csv_path, manifest["requests"], annual=False)
    frame.describe().to_csv(folder / "discovery_series_summary.csv")
    write_json(folder / "discovery_columns.json", mapping)
    # Names from RDD alone are insufficient: actual CSV keys, units and finite series checked above.
    approval = {"fingerprint": manifest["fingerprint"], "created": datetime.now().isoformat(),
                "reports": reports, "status": "output-contract-checked; numerical-EMS-review-still-required"}
    write_json(folder / "discovery_approval.json", approval)
    print(f"Review {err} and numerical EMS behaviour before campaign use: {folder / 'discovery_approval.json'}")


def make_plan(session, spec):
    if spec["sampling"] == "lhs":
        # BESOS has no seed argument; persist the actual expanded plan, not just the seed.
        import random
        random.seed(SEED)
        np.random.seed(SEED)
        session.sampling_lhs(num_samples=100)
    else:
        session.sampling_full_set()
    plan = session.parameters_values_df.copy()
    validate_plan(plan, spec)
    return plan


def validate_plan(plan, spec):
    finite_columns(plan, list(spec["parameters"]))
    if "epw" not in plan or set(plan["epw"]) != set(spec["epws"]):
        raise ValueError("Plan weather strings must exactly match the staged EPW basenames.")
    if len(plan) != spec["expected_runs"]:
        message = f"Plan has {len(plan)} tasks, not the manuscript forecast {spec['expected_runs']}."
        if spec["number"] != "4.1":
            raise ValueError(message + " Review the input plan before proceeding.")
        warnings.warn(message + " Current CS14 excludes ComfMod=0 (40 combinations / 120 tasks). Do not add invalid combinations; campaign requires --count-note.")
    subset = list(spec["parameters"]) + ["epw"]
    if plan.duplicated(subset).any():
        raise ValueError("Duplicate parameter/weather rows in the saved plan.")
    if spec["sampling"] == "lhs" and len(plan[list(spec["parameters"])].drop_duplicates()) != 100:
        raise ValueError("LHS plan does not contain exactly 100 original parameter vectors.")
    for name, domain in spec["parameters"].items():
        valid = plan[name].isin(domain) if isinstance(domain, list) else plan[name].between(*domain)
        if not valid.all():
            raise ValueError(f"Saved plan is outside domain {name}: {domain}.")


def rebase_path(value, *, old_root, new_root, base=None, require_exists=True):
    if value is None or (isinstance(value, float) and np.isnan(value)) or str(value) == "":
        raise ValueError("Missing saved simulation path.")
    text = str(value).replace("\\", "/")
    absolute = PureWindowsPath(text).is_absolute() or Path(text).is_absolute()
    if not absolute:
        text = str(base or new_root).replace("\\", "/").rstrip("/") + "/" + text
    if old_root:
        old = str(old_root).replace("\\", "/").rstrip("/")
        new = str(new_root).replace("\\", "/").rstrip("/")
        if text.casefold() == old.casefold() or text.casefold().startswith(old.casefold() + "/"):
            path = Path(new_root) / text[len(old):].lstrip("/")
        elif text.casefold() == new.casefold() or text.casefold().startswith(new.casefold() + "/"):
            path = Path(text)
        else:
            raise ValueError(f"Saved path is outside explicit old/new roots: {text}")
    else:
        path = Path(text)
        if not path.is_absolute():
            if PureWindowsPath(text).is_absolute():
                raise ValueError("A foreign Windows path needs --old-root and --new-root.")
            path = Path(base or new_root) / path
    path = path.resolve()
    if require_exists and not path.exists():
        raise FileNotFoundError(f"Saved artifact is unavailable: {path}. Supply an explicit path mapping; no basename search fallback.")
    return path


def native_optimisation_signature():
    payload = dict(algorithm="NSGAII", evaluations=EVALUATIONS, population_size=POPULATION,
                   algorithm_options={}, pareto_separate_by_epw=True, pareto_separate_by_idf=False, keep_df="all")
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def recover_checkpoint(folder, old_manifest, spec):
    """Only our manifested campaigns. Copy checkpoint first; never overwrite archive.

    Basename IDF/EPW identities stay unchanged across PCs. Legacy campaigns without
    this content manifest are load-only, rather than risking incompatible reuse.
    """
    filename = f"outputs_{spec['kind'] if spec['kind'] == 'optimisation' else 'param_simulation'}_checkpoint_latest.pkl"
    if spec["kind"] == "optimisation":
        filename = "outputs_optimisation_checkpoint_latest.pkl"
    pointer = folder / "active_checkpoint.txt"
    checkpoint = folder / pointer.read_text(encoding="utf-8").strip() if pointer.exists() else folder / "accim" / filename
    try:
        checkpoint.resolve().relative_to(folder.resolve())
    except ValueError as exc:
        raise ValueError("Active checkpoint must stay inside its campaign directory.") from exc
    if not checkpoint.is_file():
        raise FileNotFoundError(f"Resume requires an existing checkpoint: {checkpoint}")
    with checkpoint.open("rb") as stream:
        state = pickle.load(stream)   # Trusted local campaign only; never unpickle untrusted downloads.
    if not isinstance(state, dict):
        raise ValueError("Unexpected checkpoint format; use consolidated results for load.")
    old_root = old_manifest["campaign_root"]

    def relocate_frame(frame):
        if not isinstance(frame, pd.DataFrame):
            raise ValueError("Checkpoint result chunk is not a DataFrame.")
        frame = frame.copy(deep=True)
        for col in PATH_COLUMNS:
            if col in frame:
                frame[col] = frame[col].map(lambda p: str(rebase_path(p, old_root=old_root, new_root=folder)))
        return frame

    recovery = folder / "recovery" / stamp()
    recovery.mkdir(parents=True, exist_ok=False)
    if spec["kind"] == "parametric":
        plan_path = folder / "plan.pkl"
        if not plan_path.is_file():
            raise FileNotFoundError("Original explicit LHS/full-set plan is missing; resampling is forbidden on resume.")
        plan = pd.read_pickle(plan_path)
        saved_plan = state.get("input_plan")
        if isinstance(saved_plan, pd.DataFrame):
            compare = list(spec["parameters"]) + ["epw"]
            pd.testing.assert_frame_equal(plan[compare].reset_index(drop=True), saved_plan[compare].reset_index(drop=True), check_exact=True)
        validate_plan(plan, spec)
        completed = set(state.get("completed_signatures", []))
        if len(completed) != int(state.get("completed_tasks", -1)) or int(state.get("total_tasks", -1)) != len(plan):
            raise ValueError("Inconsistent checkpoint task counts.")
        cls = simulation_class(spec)
        names = old_manifest["identity"].get("parameter_names", list(spec["parameters"]))
        planned_signatures = {
            cls._build_parametric_task_signature(old_manifest["idf_stem"], row["epw"], names, row.to_dict())
            for _, row in plan.iterrows()
        }
        if len(planned_signatures) != len(plan) or not completed.issubset(planned_signatures):
            raise ValueError("Checkpoint signatures do not belong to the exact saved plan; no silent rerun is allowed.")
        if len(completed) == len(plan):
            raise ValueError("Checkpoint is complete: use load with an explicit consolidated file, not resume.")
        chunks, found = [], set()
        for i, path in enumerate(state.get("batch_pickles", [])):
            local = rebase_path(path, old_root=old_root, new_root=folder)
            chunk = relocate_frame(pd.read_pickle(local))
            finite_columns(chunk, old_manifest["identity"]["objective_names"])
            if "_accim_task_signature" not in chunk:
                raise ValueError("Cannot verify completed-task coverage in checkpoint batches.")
            found.update(chunk["_accim_task_signature"].astype(str))
            destination = recovery / f"batch_{i:05d}.pkl"
            chunk.to_pickle(destination)
            chunks.append(str(destination))
        if found != completed:
            raise ValueError("Completed signatures and preserved result chunks differ; refusing silent task loss.")
        state["batch_pickles"], state["input_plan"] = chunks, plan.copy()
    else:
        plan = None
        if state.get("resume_signature") != native_optimisation_signature():
            raise ValueError("Native optimisation signature mismatch; no implicit fresh optimisation on resume.")
        cases = state.get("cases")
        if not isinstance(cases, dict) or len(cases) != int(state.get("completed_cases", -1)):
            raise ValueError("Invalid optimisation case checkpoint.")
        if int(state.get("case_count", -1)) != len(cases) or int(state.get("total_cases", -1)) != len(spec["epws"]):
            raise ValueError("Inconsistent optimisation case counts.")
        if len(cases) == len(spec["epws"]):
            raise ValueError("All weather cases are complete; use load, not resume.")
        expected = {f"{old_manifest['idf_stem']}::{Path(epw).stem}" for epw in spec["epws"]}
        if not set(cases).issubset(expected):
            raise ValueError("Checkpoint IDF/EPW case identities differ; automatic identity rewriting is forbidden.")
        for case_id, case in cases.items():
            idf_label, epw_label = case_id.split("::", 1)
            if case.get("idf") != idf_label or case.get("epw") != epw_label or case.get("key") != epw_label:
                raise ValueError("Checkpoint case metadata disagree with its IDF/EPW key.")
            for key in ("outputs_non_dominated", "outputs_full"):
                case[key] = relocate_frame(case[key])
                finite_columns(case[key], old_manifest["identity"]["objective_names"])
                for column, label in (("idf", idf_label), ("epw", epw_label)):
                    if column in case[key] and set(case[key][column]) != {label}:
                        raise ValueError(f"Checkpoint {key} mixes {column} identities.")
    destination = recovery / filename
    state["checkpoint_path"] = str(destination)
    with destination.open("wb") as stream:
        pickle.dump(state, stream, protocol=pickle.HIGHEST_PROTOCOL)
    sidecar_keys = ("saved_at", "checkpoint_path", "completed_tasks", "total_tasks", "completed_cases", "total_cases", "case_count", "resume_signature")
    write_json(Path(str(destination) + ".meta.json"), {key: state[key] for key in sidecar_keys if key in state})
    pointer.write_text(destination.relative_to(folder).as_posix(), encoding="utf-8")
    return destination, plan


def execute_campaign(session, manifest, spec, args, folder, *, resume):
    if not all(note.strip() for note in (args.area_note, args.schedule_note, args.ems_note)):
        raise ValueError("Campaign needs --area-note, --schedule-note and --ems-note after reviewing the isolated checks.")
    if args.approval is None or not args.approval.is_file():
        raise ValueError("Supply --approval from isolated discovery, after numerical/EMS review on the simulation PC.")
    approval = json.loads(args.approval.read_text(encoding="utf-8"))
    if approval.get("fingerprint") != manifest["fingerprint"]:
        raise ValueError("Discovery belongs to a different model/API/configuration.")
    old = None
    checkpoint, plan = False, None
    if resume:
        old = json.loads((folder / "campaign.json").read_text(encoding="utf-8"))
        if old.get("fingerprint") != manifest["fingerprint"]:
            raise ValueError("Campaign content differs (IDF, EPW, source, parameters or objectives). Use a NEW campaign name.")
        checkpoint, plan = recover_checkpoint(folder, old, spec)
    elif spec["kind"] == "parametric":
        plan = make_plan(session, spec)
        plan.to_pickle(folder / "plan.pkl")
        plan.to_csv(folder / "plan.csv", index=False)
    planned_count = len(plan) if isinstance(plan, pd.DataFrame) else None
    if planned_count is not None and planned_count != spec["expected_runs"] and not args.count_note.strip():
        raise ValueError("Review preview_plan.csv and supply --count-note acknowledging the actual compatibility-filtered count; the forecast is not a target to force.")
    manifest.update(campaign_root=str(folder), idf_stem=args.idf.stem, status="running",
                    area_review=args.area_note, schedule_review=args.schedule_note,
                    numerical_ems_review=args.ems_note, count_review=args.count_note,
                    actual_planned_tasks=planned_count)
    if old:
        write_json(folder / f"campaign_before_resume_{stamp()}.json", old)
    write_json(folder / "campaign.json", manifest)
    with working_directory(Path(manifest["work_directory"])):
        if spec["kind"] == "parametric":
            session.sampling_custom(plan)
            results = session.run_parametric_simulation(
                epws=list(spec["epws"]), out_dir=str(folder / "accim"), df=plan,
                processes=args.workers, batch_size=args.batch_size, keep_input=True, keep_dirs=True,
                checkpoint_every_batch=True, resume_from_checkpoint=str(checkpoint) if checkpoint else False,
                resume_plan_source="auto", sim_files_extensions=KEEP_EXTENSIONS, sim_files_policy="keep",
            )
        else:
            import random
            random.seed(SEED)
            np.random.seed(SEED)
            # Resume only reuses FINISHED IDF x EPW cases; interrupted populations restart.
            results = session.run_optimisation(
                epws=list(spec["epws"]), out_dir=str(folder / "accim"), algorithm="NSGAII",
                population_size=POPULATION, evaluations=EVALUATIONS, processes=args.workers,
                keep_sim_files="all", keep_df="all", sim_files_extensions=KEEP_EXTENSIONS,
                sim_files_policy="keep", pareto_separate_by_epw=True, pareto_separate_by_idf=False,
                checkpoint_every_case=True, resume_from_checkpoint=str(checkpoint) if checkpoint else False,
            )
    if not isinstance(results, pd.DataFrame):
        attr = "outputs_param_simulation" if spec["kind"] == "parametric" else "outputs_optimisation"
        results = getattr(session, attr)
    finite_columns(results, manifest["identity"]["objective_names"])
    actual = len(results)
    print(f"Forecast {spec['expected_runs']} campaign evaluations; retained result rows {actual}. Reconcile engine logs, retries and cache separately.")
    raw = results.copy(deep=True)
    for col in PATH_COLUMNS:
        if col in raw:
            def relative_saved_path(value):
                path = rebase_path(value, old_root=None, new_root=folder)
                try:
                    return path.relative_to(folder).as_posix()
                except ValueError as exc:
                    raise ValueError(f"Simulation files escaped campaign root: {path}") from exc
            raw[col] = raw[col].map(relative_saved_path)
    manifest.update(status="completed", actual_result_rows=actual)
    raw.attrs["paper"] = {"schema": SCHEMA, "manifest": manifest, "area_m2": None,
                          "energy_unit": "J", "energy_column": ENERGY, "path_base": "."}
    destination = folder / f"results_raw_{stamp()}.pkl"
    raw.to_pickle(destination)
    write_json(folder / "campaign.json", manifest)
    print(f"Raw consolidated results preserved: {destination}\nUse load --result with this exact file; campaign execution does not invoke postprocessing.")


# %% Load-only postprocessing: no IDF loading, model construction or simulation calls
def load_results(spec, args):
    if args.result is None or not args.result.is_file():
        raise FileNotFoundError("load requires --result pointing to one explicitly chosen consolidated .pkl/.json/.csv.")
    if "checkpoint" in args.result.name.casefold():
        raise ValueError("A checkpoint is not a consolidated DataFrame. Select outputs_*_<timestamp>.pkl or results_raw_*.pkl.")
    require_api(spec)
    cls = simulation_class(spec)
    post = cls(buildings=None, parameters_type=None, bypass_addAccis=True)
    suffix = args.result.suffix.casefold()
    keyword = {".pkl": "pickle_path", ".pickle": "pickle_path", ".json": "json_path", ".csv": "csv_path"}.get(suffix)
    if keyword is None:
        raise ValueError("Unsupported consolidated format.")
    method = post.load_outputs_parametric if spec["kind"] == "parametric" else post.load_outputs_optimisation
    # A fresh object has no output filepath to rewrite; never run against an archive.
    frame = method(**{keyword: str(args.result)})
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("Selected artifact is not a consolidated results DataFrame.")
    frame = frame.copy(deep=True).reset_index(drop=True)
    frame["result_row"] = frame.index
    finite_columns(frame, list(spec["parameters"]))
    if "epw" not in frame:
        raise ValueError("Results have no EPW identity.")
    frame["scenario"] = frame["epw"].map(climate_name)
    expected_climates = {climate_name(p) for p in spec["epws"]}
    if set(frame["scenario"]) != expected_climates:
        raise ValueError(f"Loaded climates {set(frame['scenario'])} differ from {expected_climates}.")
    if "idf" in frame and frame["idf"].nunique(dropna=False) != 1:
        raise ValueError("This delivery expects a single building in each results file.")
    paper = frame.attrs.get("paper", {})
    manifest = paper.get("manifest", {})
    if manifest and manifest["identity"]["experiment"]["number"] != spec["number"]:
        raise ValueError("Results belong to another experiment.")
    if spec["kind"] == "optimisation" and not manifest and not args.legacy_metric_note.strip():
        raise ValueError("Legacy optimisation metrics have different definitions. Supply --legacy-metric-note after checking their provenance; they are not validated by this delivery.")
    aliases = [ENERGY, "Electricity:HVAC", "HVAC electricity (J)"]
    if paper.get("energy_column"):
        aliases.append(paper["energy_column"])
    saved_objectives = manifest.get("identity", {}).get("objective_names", [])
    if saved_objectives:
        aliases.append(saved_objectives[0])  # This delivery records meter first, then comfort.
    energy = resolve_column(frame, aliases)
    finite_columns(frame, [energy])
    comfort_aliases = metric_aliases(spec) + (saved_objectives[1:2] if saved_objectives else [])
    comfort = resolve_column(frame, comfort_aliases, required=spec["kind"] == "optimisation")
    if comfort:
        finite_columns(frame, [comfort])
    else:
        warnings.warn("Legacy parametric results contain energy only. Exact timestep comfort cannot be reconstructed from hourly mean temperatures.")
    output_attr = "outputs_param_simulation" if spec["kind"] == "parametric" else "outputs_optimisation"
    # Normalize ONLY the energy field, not e.g. 'Adaptive cooling coefficient'.
    # The installed API uses a broad name heuristic which is not a unit registry.
    unit = paper.get("energy_unit")
    if unit is None:
        label = energy.casefold().replace("²", "2")
        unit = "kWh/m2" if "kwh/m2" in label else ("kWh" if "kwh" in label else "J")
    energy_frame = frame[[energy]].copy()
    if unit == "kWh/m2":
        old_area = paper.get("area_m2") or args.legacy_area
        if old_area is None:
            raise ValueError("Normalized legacy data lack their denominator. Prefer the raw consolidated file or specify --legacy-area.")
        if not np.isfinite(float(old_area)) or float(old_area) <= 0:
            raise ValueError("Legacy area must be finite and positive.")
        frame[energy] *= float(old_area) / PAPER_AREA_M2
    else:
        if unit not in {"J", "kWh"}:
            raise ValueError(f"Unsupported energy unit {unit!r}.")
        if unit == "kWh":
            energy_frame[energy] *= 3600000.0
        energy_frame.rename(columns={energy: ENERGY}, inplace=True)
        setattr(post, output_attr, energy_frame)
        post.set_building_floor_area(mode="custom", custom_area=PAPER_AREA_M2)
        post.normalize_outputs(df_types=[spec["kind"]])
        normalized = getattr(post, output_attr)
        normalized_column = resolve_column(normalized, [ENERGY])
        frame.drop(columns=[energy], inplace=True)
        frame[normalized_column] = normalized[normalized_column].to_numpy()
        energy = normalized_column
    finite_columns(frame, [energy])
    setattr(post, output_attr, frame)
    post.set_building_floor_area(mode="custom", custom_area=PAPER_AREA_M2)
    post._normalized_output_df_types = {spec["kind"]}
    post._refresh_outputs_normalized_flag()
    post.last_run_type = spec["kind"]
    post.problem = ResultProblem(list(spec["parameters"]), [energy] + ([comfort] if comfort else []))
    post.epws = list(frame["epw"].unique())
    saved_base = args.legacy_path_base or paper.get("path_base", ".")
    path_base = (args.result.parent / saved_base).resolve() if not (Path(saved_base).is_absolute() or PureWindowsPath(str(saved_base)).is_absolute()) else saved_base
    frame.attrs["paper"] = {**paper, "schema": SCHEMA, "energy_unit": "kWh/m2",
                             "energy_column": energy, "area_m2": PAPER_AREA_M2,
                             "path_base": str(path_base), "manifest": manifest,
                             "legacy_metric_review": args.legacy_metric_note}
    integral = resolve_column(frame, [PMV_INTEGRAL], required=False)
    occupied = resolve_column(frame, [OCC_HOURS], required=False)
    if spec["number"] == "4.3" and integral and occupied:
        finite_columns(frame, [integral, occupied])
        if (frame[occupied] <= 0).any():
            raise ValueError("Mean occupied |PMV| is undefined with no occupied hours.")
        frame["Occupied mean absolute Fanger PMV [-]"] = frame[integral] / frame[occupied]
    return post, frame, energy, comfort


class ResultProblem:
    """Postprocessing names/directions only; cannot be used to start a simulation."""
    def __init__(self, inputs, outputs):
        self._inputs, self._outputs = list(inputs), list(outputs)
        self.minimize_outputs = [True] * len(outputs)
        self.add_outputs = []

    def names(self, kind):
        return {"inputs": self._inputs, "outputs": self._outputs, "constraints": []}[kind]


def nondominated(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("Pareto objectives must be a finite 2D matrix.")
    return np.array([not np.any(np.all(values <= row, axis=1) & np.any(values < row, axis=1)) for row in values])


def annual_figures(post, frame, energy, comfort, spec, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frame.to_csv(destination / "table_runs.csv", index=False)
    frame.to_pickle(destination / "table_runs.pkl")
    metrics = [energy] + ([comfort] if comfort else [])
    for alias in ("Occupied mean absolute Fanger PMV [-]", FIXED_PMV_HOURS):
        column = resolve_column(frame, [alias], required=False)
        if column:
            metrics.append(column)
    frame.groupby("scenario", observed=True)[metrics].describe().to_csv(destination / "table_by_climate.csv")
    units = {energy: "kWh/m2", **({comfort: "C-hr" if spec["comfort"] == "fixed_en" else "h"} if comfort else {})}
    for alias, unit in (("Occupied mean absolute Fanger PMV [-]", "dimensionless"), (FIXED_PMV_HOURS, "h"), (OCC_HOURS, "h"), (PMV_INTEGRAL, "h * dimensionless PMV")):
        column = resolve_column(frame, [alias], required=False)
        if column:
            units[column] = unit
    write_json(destination / "units.json", units)
    if spec["kind"] == "optimisation":
        frame["pareto-optimal"] = False
        selected = []
        for climate, group in frame.groupby("scenario", sort=False, observed=True):
            idx = group.index
            flags = nondominated(group[[energy, comfort]].to_numpy())
            frame.loc[idx, "pareto-optimal"] = flags
            group = frame.loc[idx].copy()
            post.outputs_optimisation = group
            for method in ("topsis", "knee_point"):
                best = post.get_best_compromise_solution(method=method, weights=[0.5, 0.5] if method == "topsis" else None)
                if len(best) != 1 or best["scenario"].iloc[0] != climate:
                    raise ValueError("Compromise selection escaped its climate subset.")
                best["selection_method"] = method
                selected.append(best)
            fig, ax = plt.subplots(figsize=(7, 5))
            colour = "PMV setpoint" if spec["comfort"] == "apmv" else "CustAST_ASToffset"
            points = ax.scatter(group[energy], group[comfort], c=group[colour], cmap="viridis", alpha=0.65)
            front = group[group["pareto-optimal"]].sort_values(energy)
            ax.plot(front[energy], front[comfort], color="black", linewidth=0.8, label="Non-dominated within climate")
            for best in selected[-2:]:
                ax.scatter(best[energy], best[comfort], marker="X", s=100, label=best["selection_method"].iloc[0])
            ax.set(xlabel=energy, ylabel=comfort, title=climate)
            ax.legend(fontsize="small")
            fig.colorbar(points, ax=ax, label=colour)
            fig.tight_layout()
            fig.savefig(destination / f"pareto_compromise_{climate}.png", dpi=200)
            plt.close(fig)
            front.to_csv(destination / f"front_{climate}.csv", index=False)
            columns = list(spec["parameters"]) + [energy, comfort]
            scaled = (front[columns] - group[columns].min()) / (group[columns].max() - group[columns].min()).replace(0, 1)
            fig, ax = plt.subplots(figsize=(11, 5))
            ax.plot(range(len(columns)), scaled.to_numpy().T, alpha=0.4)
            ax.set_xticks(range(len(columns)))
            ax.set_xticklabels(columns, rotation=25, ha="right")
            ax.set(ylabel="Within-climate min-max scale [-]", title=f"Non-dominated solutions: {climate}")
            fig.tight_layout()
            fig.savefig(destination / f"parallel_coordinates_{climate}.png", dpi=200)
            plt.close(fig)
            if spec["comfort"] == "apmv":
                group.assign(at_widest_pmv=group["PMV setpoint"] >= 0.89).groupby("pareto-optimal").agg(
                    count=(energy, "size"), widest_fraction=("at_widest_pmv", "mean"),
                    pmv_min=("PMV setpoint", "min"), pmv_max=("PMV setpoint", "max"),
                ).to_csv(destination / f"moving_reference_diagnostic_{climate}.csv")
        post.outputs_optimisation = frame
        pd.concat(selected, ignore_index=True).to_csv(destination / "best_compromise_by_climate.csv", index=False)
        frame.to_csv(destination / "table_evaluations_with_local_fronts.csv", index=False)
    elif spec["number"] == "4.1":
        frame["operation"] = "HVAC=" + frame["HVACmode"].astype(str) + "; ComfMod=" + frame["ComfMod"].astype(str)
        post.plot_parametric_distributions(x="ComfStand", y_vars=[energy], kind="box", hue="HVACmode", col="scenario", row="ComfMod", show_points=True, normalize_per_m2=False, out_dir=str(destination))
        post.plot_parametric_heatmap(x="ComfStand", y="CAT", z=energy, col="scenario", row="operation", annot=True, fmt=".1f", normalize_per_m2=False, out_dir=str(destination))
        keys = ["epw", "ComfStand", "CAT", "HVACmode"]
        baseline = frame[frame["ComfMod"] == 0][keys + [energy]].rename(columns={energy: "static_energy_kWh_m2"})
        if baseline.duplicated(keys).any():
            raise ValueError("Ambiguous static baselines.")
        adaptive = frame[frame["ComfMod"] == 3].merge(baseline, on=keys, how="left", validate="one_to_one")
        # CS14 has no ComfMod=0 in the current compatibility catalogue: leave it explicitly unmatched.
        adaptive["baseline_available"] = adaptive["static_energy_kWh_m2"].notna()
        available = adaptive["baseline_available"]
        if (adaptive.loc[available, "static_energy_kWh_m2"] <= 0).any():
            raise ValueError("Nonpositive static energy cannot define percentage savings.")
        adaptive.loc[available, "saving_percent"] = 100 * (1 - adaptive.loc[available, energy] / adaptive.loc[available, "static_energy_kWh_m2"])
        adaptive.to_csv(destination / "savings_vs_matched_static.csv", index=False)
    elif spec["number"] == "4.2":
        for parameter in ("CustAST_ASToffset", "CustAST_m", "CustAST_n", "CustAST_ASTaul"):
            post.plot_parametric_scatter(x=parameter, y=energy, hue="scenario", add_trend="linear", normalize_per_m2=False, out_dir=str(destination))
        post.plot_parametric_ecdf(x=energy, hue="scenario", normalize_per_m2=False, out_dir=str(destination))
        post.plot_parametric_distributions(x="scenario", y_vars=[energy], kind="violin", show_points=True, normalize_per_m2=False, out_dir=str(destination))
    else:
        # The installed plotting heuristic treats 'cooling' as an energy name.
        # A dimensionless alias avoids falsely labelling lambda in kWh/m2.
        frame["lambda_c [-]"] = frame["Adaptive cooling coefficient"]
        post.plot_parametric_lines(x="lambda_c [-]", y_vars=[energy], hue="PMV setpoint", col="scenario", normalize_per_m2=False, out_dir=str(destination))
        post.plot_parametric_heatmap(x="lambda_c [-]", y="PMV setpoint", z=energy, col="scenario", annot=True, fmt=".1f", normalize_per_m2=False, out_dir=str(destination))
        reference = frame[frame["Adaptive cooling coefficient"] == 0][["epw", "PMV setpoint", energy]].rename(columns={energy: "lambda_c_zero_energy"})
        savings = frame.merge(reference, on=["epw", "PMV setpoint"], how="left", validate="many_to_one")
        if savings["lambda_c_zero_energy"].isna().any():
            raise ValueError("Missing lambda_c=0 reference for a climate/PMV group; savings must not silently drop rows.")
        if (savings["lambda_c_zero_energy"] <= 0).any():
            raise ValueError("Nonpositive cooling-lambda reference energy.")
        savings["saving_percent"] = 100 * (1 - savings[energy] / savings["lambda_c_zero_energy"])
        savings.to_csv(destination / "savings_vs_lambda_c_zero_heating_unchanged.csv", index=False)
    if spec["kind"] == "parametric" and comfort:
        fig, ax = plt.subplots(figsize=(7, 5))
        for climate, group in frame.groupby("scenario", observed=True):
            ax.scatter(group[energy], group[comfort], s=15, label=climate)
        ax.set(xlabel=energy, ylabel=comfort, title="Reported energy and comfort (not optimisation)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(destination / "energy_comfort_by_climate.png", dpi=200)
        plt.close(fig)
    plt.close("all")


# %% Exact, bounded-I/O CSV reading and actual EnergyPlus end-of-interval dates
def hourly_column(headers, request):
    matches = []
    for header in headers:
        match = re.fullmatch(r"\s*(.*?)\s*\[([^]]*)]\s*\(([^()]*)\)\s*", header)
        if not match or match.group(3).casefold() != "hourly":
            continue
        base, unit = match.group(1).strip(), match.group(2).strip()
        name = request["variable"]
        if request["kind"] == "meter":
            valid = base.casefold() == name.casefold()
        elif request.get("key"):
            valid = base.casefold() == f"{request['key']}:{name}".casefold()
        else:
            valid = base.casefold().endswith(":" + name.casefold())
        if valid:
            expected = request.get("units", "").casefold()
            accepted = {expected}
            if expected in {"h", "hr"}:
                accepted = {"h", "hr"}
            if expected and unit.casefold() not in accepted:
                raise ValueError(f"Unexpected units in {header!r}; expected {accepted}.")
            matches.append(header)
    if len(matches) != 1:
        raise ValueError(f"Expected one Hourly CSV column for {request}, found {matches}. Missing data are not fabricated.")
    return matches[0]


def energyplus_dates(values, *, annual, year=None):
    parts = []
    for value in values:
        match = re.fullmatch(r"\s*(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*", str(value))
        if not match:
            raise ValueError(f"Unrecognised EnergyPlus Date/Time {value!r}; review environment/calendar.")
        month, day, hour, minute, second = [int(v or 0) for v in match.groups()]
        if hour > 24 or minute > 59 or second > 59 or (hour == 24 and (minute or second)):
            raise ValueError(f"Invalid interval end {value!r}.")
        parts.append((month, day, hour, minute, second))
    leap = any(m == 2 and d == 29 for m, d, *_ in parts)
    # Display calendar only, not the meteorological source year of a TMY EPW.
    chosen_year = year if year is not None else (2000 if leap else 2001)
    if leap != calendar.isleap(chosen_year):
        raise ValueError("Display year leap status disagrees with the actual CSV dates; do not force 2024 onto 8760 records.")
    dates = pd.DatetimeIndex([datetime(chosen_year, m, d) + timedelta(hours=h, minutes=mi, seconds=s) for m, d, h, mi, s in parts])
    if dates.has_duplicates or not dates.is_monotonic_increasing or (len(dates) > 1 and not ((dates[1:] - dates[:-1]) == pd.Timedelta(hours=1)).all()):
        raise ValueError("Hourly timestamps are duplicated, discontinuous or mixed across simulation environments.")
    if annual:
        expected = 8784 if leap else 8760
        if len(dates) != expected or dates[0] != pd.Timestamp(chosen_year, 1, 1, 1) or dates[-1] != pd.Timestamp(chosen_year + 1, 1, 1):
            raise ValueError(f"Expected one complete annual hourly series ({expected} records), received {len(dates)}.")
    return dates


def read_hourly(path, requests, *, annual=True, year=None):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    # pandas mangles duplicated headers; inspect the untouched header first.
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        headers = next(csv.reader(stream), [])
    if not headers or len(headers) != len(set(headers)):
        raise ValueError("Empty/duplicate CSV headers; output-key ambiguity must be resolved explicitly.")
    date_columns = [c for c in headers if c.strip().casefold() == "date/time"]
    if len(date_columns) != 1:
        raise ValueError("CSV must have exactly one Date/Time column.")
    mapping = {r["role"]: hourly_column(headers, r) for r in requests}
    raw = pd.read_csv(path, usecols=[date_columns[0]] + list(dict.fromkeys(mapping.values())))
    finite_columns(raw, list(mapping.values()))
    index = energyplus_dates(raw[date_columns[0]], annual=annual, year=year)
    frame = pd.DataFrame({role: raw[column].to_numpy() for role, column in mapping.items()}, index=index)
    frame.index.name = "interval_end_display_calendar"
    return frame, mapping


def legacy_hourly_requests(spec):
    # Exact semantic names; lack of no-tolerance output is NOT equivalent to an applied setpoint.
    if spec["comfort"] == "apmv":
        raise ValueError("Legacy aPMV hourly loading needs saved target/output metadata; use new manifest-backed results.")
    names = [("operative", "Zone Operative Temperature"), ("pmot", PMOT), ("rmot", RMOT),
             ("cooling_no_tolerance", "Adaptive Cooling Setpoint Temperature_No Tolerance"),
             ("heating_no_tolerance", "Adaptive Heating Setpoint Temperature_No Tolerance")]
    if spec["number"] == "4.2":
        names = [(role, name) for role, name in names if role != "rmot"]
    return [{"role": role, "variable": name, "key": None, "units": "C", "kind": "variable"} for role, name in names]


def hourly_postprocess(frame, spec, args, destination):
    import matplotlib.pyplot as plt
    climate = climate_name(args.climate)
    selected = frame[frame["scenario"] == climate]
    if args.hourly_indices:
        indices = [int(i) for i in args.hourly_indices.split(",")]
        if not set(indices).issubset(selected.index):
            raise ValueError("Requested row labels are missing or belong to another climate.")
        selected = selected.loc[indices]
    elif spec["kind"] == "optimisation" and not args.hourly_all:
        selected = selected[selected["pareto-optimal"]].head(3)
    elif not args.hourly_all:
        selected = selected.head(3)
    if selected.empty:
        raise ValueError("Hourly filter is empty.")
    selected.to_csv(destination / "hourly_selection.csv", index=False)
    paper = frame.attrs.get("paper", {})
    requests = paper.get("manifest", {}).get("requests") or legacy_hourly_requests(spec)
    base = Path(paper.get("path_base", args.result.parent))
    if not base.is_absolute():
        base = args.result.parent / base
    diagnostics, regressions = [], []
    for row_id, row in selected.iterrows():
        if "simulation_output_csv_path" in row and pd.notna(row["simulation_output_csv_path"]):
            saved = row["simulation_output_csv_path"]
            csv_path = rebase_path(saved, old_root=args.old_root, new_root=args.new_root or base, base=base)
        else:
            col = "output_dir" if "output_dir" in row else "simulation_directory"
            directory = rebase_path(row[col], old_root=args.old_root, new_root=args.new_root or base, base=base)
            csv_path = directory / "eplusout.csv"
        hourly, mapping = read_hourly(csv_path, requests, year=args.calendar_year)
        hourly.to_csv(destination / f"hourly_selected_{row_id}.csv")
        write_json(destination / f"hourly_columns_{row_id}.json", mapping)
        if spec["comfort"] == "fixed_en":
            role = "rmot" if spec["number"] == "4.1" and int(row["ComfStand"]) == 1 else "pmot"
            fig, ax = plt.subplots(figsize=(7, 5))
            for variable in ("operative", "cooling_no_tolerance", "heating_no_tolerance"):
                ax.scatter(hourly[role], hourly[variable], s=2, alpha=0.2, label=variable)
            ax.set(xlabel=f"{role.upper()} [C]", ylabel="Temperature [C]", title=f"{climate}, result row {row_id}")
            ax.legend(markerscale=4)
            if "CustAST_m" in row:
                inside = hourly["pmot"].between(10, row["CustAST_ASTaul"])
                for variable in ("cooling_no_tolerance", "heating_no_tolerance"):
                    x, y = hourly.loc[inside, "pmot"], hourly.loc[inside, variable]
                    if len(x) >= 3 and x.nunique() >= 2:
                        slope, intercept = np.polyfit(x, y, 1)
                        expected_intercept = row["CustAST_n"] + (row["CustAST_ASToffset"] if variable.startswith("cooling") else -row["CustAST_ASToffset"])
                        regressions.append({"row": row_id, "scenario": climate, "output": variable,
                                            "slope": slope, "intercept": intercept, "points_within_applicability": len(x),
                                            "configured_m": row["CustAST_m"], "configured_n": row["CustAST_n"],
                                            "expected_intercept_n_plus_minus_offset": expected_intercept,
                                            "slope_difference": slope - row["CustAST_m"],
                                            "intercept_difference": intercept - expected_intercept})
                    else:
                        warnings.warn(f"Row {row_id}: insufficient distinct unclamped PMOT values for {variable} regression.")
            if "comfort" in hourly:
                diagnostics.append({"row": row_id, "scenario": climate,
                                    "EN_occupied_degree_hours": float(hourly["comfort"].sum()),
                                    "occupied_hours": float(hourly["occupied"].sum())})
        else:
            fig, ax = plt.subplots(figsize=(11, 4))
            window = hourly.iloc[:24 * 14]
            for variable in ("apmv", "cooling_no_tolerance", "heating_no_tolerance"):
                ax.plot(window.index, window[variable], label=variable)
            ax.set(ylabel="aPMV [-]", title=f"{climate}, row {row_id}; first 14 days, interval ends")
            ax.legend()
            occupied = float(hourly["occupied"].sum())
            if occupied <= 0:
                raise ValueError("No occupied hours for independent PMV diagnostic.")
            diagnostics.append({"row": row_id, "scenario": climate,
                                "PMV setpoint": row["PMV setpoint"],
                                "native_all_time_discomfort_hours": float(hourly["comfort"].sum()),
                                "fixed_occupied_PMV_hours": float(hourly["fixed_pmv_hours"].sum()),
                                "occupied_mean_abs_Fanger_PMV": float(hourly["pmv_integral"].sum()) / occupied,
                                "occupied_hours": occupied})
        fig.tight_layout()
        fig.savefig(destination / f"hourly_{climate}_{row_id}.png", dpi=200)
        plt.close(fig)
    if diagnostics:
        pd.DataFrame(diagnostics).to_csv(destination / "hourly_comfort_diagnostics.csv", index=False)
    if regressions:
        pd.DataFrame(regressions).to_csv(destination / "custom_regressions_unclamped_PMOT.csv", index=False)


# %% Explicit operations; no implicit resume, discovery, preflight or postprocess rerun
def run_paper_experiment(spec, settings, argv=None):
    """Run an explicitly selected paper workflow using accim's public APIs.

    ``spec`` contains number, kind, parameters_type, ScriptType, parameter
    domains (lists for options, tuples for ranges), EPW basenames, expected_runs,
    sampling and comfort. The supported workflows are 4.1--4.5, for one zone and
    one resolved People target. This is a paper-specific convenience API, not a
    replacement for ParametricSimulation/OptimisationSimulation.

    ``settings`` must include an ABSOLUTE ``script_directory`` and ``idf``,
    ``epw_dir``, ``results_root``; optional campaign/result/area_note/schedule_note
    set defaults. All relative paths, including CLI overrides, resolve from the
    entry script's directory, never the installed package or launch cwd.

    Pass an explicit ``argv`` list in Spyder/Jupyter, e.g. ``['load', '--result',
    'results.pkl']``. ``None`` reads CLI arguments; no arguments prints help.
    Parallel campaigns should run from a saved main-guarded script. No local
    objective callables or sibling-experiment imports are required.

    Actions: ``prepare`` (no simulation), ``load`` (no IDF loading/simulation),
    ``discover``, ``new``, ``resume`` (the latter three require ``--simulate``).
    New/resume require explicit output-contract approval and geometry/schedule/
    EMS review notes. Resume preserves the sampled plan and only reuses completed
    optimisation cases, not populations. Returns the session (or None for help).
    """
    spec, settings = deepcopy(spec), dict(settings)
    base = Path(settings["script_directory"])
    if not base.is_absolute():
        raise ValueError("settings['script_directory'] must be an absolute path.")
    base = base.resolve()
    if spec.get("number") not in {"4.1", "4.2", "4.3", "4.4", "4.5"}:
        raise ValueError("This convenience API implements only paper experiments 4.1--4.5.")
    parser = argparse.ArgumentParser(description=f"Experiment {spec['number']}; default is help, not execution.")
    parser.add_argument("action", nargs="?", default="help", choices=("help", "prepare", "discover", "new", "resume", "load"))
    parser.add_argument("--simulate", action="store_true", help="Explicitly authorise EnergyPlus ON THE SIMULATION PC ONLY")
    parser.add_argument("--idf", type=Path, default=settings["idf"])
    parser.add_argument("--epw-dir", type=Path, default=settings["epw_dir"])
    parser.add_argument("--results-root", type=Path, default=settings["results_root"])
    parser.add_argument("--campaign", default=settings.get("campaign", "paper-v1"))
    parser.add_argument("--result", type=Path, default=settings.get("result"))
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--area-note", default=settings.get("area_note", ""))
    parser.add_argument("--schedule-note", default=settings.get("schedule_note", ""))
    parser.add_argument("--ems-note", default="", help="Record completed numerical/EMS checks on the simulation PC")
    parser.add_argument("--count-note", default="", help="Acknowledge a compatibility-filtered plan differing from the manuscript forecast")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--legacy-area", type=float)
    parser.add_argument("--legacy-path-base", type=Path, help="Original working directory for legacy relative output paths (before old/new-root mapping)")
    parser.add_argument("--legacy-metric-note", default="", help="Explicit provenance/definition review for legacy optimisation results")
    parser.add_argument("--hourly", action="store_true", help="Load a small explicit selection of retained hourly CSVs")
    parser.add_argument("--hourly-all", action="store_true", help="Process all rows in the selected climate, one CSV at a time")
    parser.add_argument("--hourly-indices", help="Comma-separated result row labels; must belong to --climate")
    parser.add_argument("--climate", default="Present")
    parser.add_argument("--calendar-year", type=int, help="Display year, whose leap status must match actual dates")
    parser.add_argument("--old-root", help="Exact historical path prefix in transferred artifacts")
    parser.add_argument("--new-root", type=Path, help="Existing replacement prefix; no heuristic file search")
    args = parser.parse_args(argv)
    if args.action == "help":
        parser.print_help()
        return None
    for name in ("idf", "epw_dir", "results_root", "result", "approval", "new_root", "legacy_path_base"):
        value = getattr(args, name)
        if value is not None:
            value = Path(value)
            setattr(args, name, (base / value).resolve() if not value.is_absolute() else value.resolve())
    if bool(args.old_root) != bool(args.new_root):
        parser.error("--old-root and --new-root must be supplied together.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.campaign):
        parser.error("Campaign must be a simple name, not a path.")
    if args.workers < 1 or args.batch_size < 1:
        parser.error("Workers and batch size must be positive.")
    root = args.results_root / ("exp_" + spec["number"].replace(".", "_"))
    if args.action == "load":
        if args.simulate:
            parser.error("load never accepts --simulate.")
        post, frame, energy, comfort = load_results(spec, args)
        destination = root / "postprocess" / stamp()
        destination.mkdir(parents=True, exist_ok=False)
        annual_figures(post, frame, energy, comfort, spec, destination)
        if args.hourly or args.hourly_all or args.hourly_indices:
            hourly_postprocess(frame, spec, args, destination)
        write_json(destination / "provenance.json", {"source": str(args.result), "source_sha256": sha256_file(args.result),
                                                     "validation": "postprocessing only; no EnergyPlus execution",
                                                     "forecast_campaign_runs": spec["expected_runs"], "loaded_rows": len(frame)})
        print(f"Postprocessing written separately: {destination}")
        return post
    if args.action in {"discover", "new", "resume"} and not args.simulate:
        parser.error("This action can simulate. Supply --simulate only on the simulation PC; load/prepare cannot launch EnergyPlus.")
    if args.action in {"new", "resume"} and (args.approval is None or not all(note.strip() for note in (args.area_note, args.schedule_note, args.ems_note))):
        parser.error("Before campaign creation, provide --approval, --area-note, --schedule-note and --ems-note from the reviewed isolated checks.")
    if args.action in {"prepare", "discover"}:
        folder = root / "checks" / stamp()
    else:
        folder = root / "campaigns" / args.campaign
        if args.action == "new" and folder.exists():
            raise FileExistsError("New campaigns require a NEW directory; never overwrite archived results.")
        if args.action == "resume" and not (folder / "campaign.json").is_file():
            raise FileNotFoundError("Resume requires this delivery's campaign manifest. Archived legacy campaigns are load-only.")
    folder.mkdir(parents=True, exist_ok=args.action == "resume")
    preparation = folder / ("resume_preparation_" + stamp()) if args.action == "resume" else folder
    preparation.mkdir(parents=True, exist_ok=True)
    work = preparation / "work"
    session, manifest = build_session(spec, args, work)
    manifest["work_directory"] = str(work)
    if args.action == "prepare":
        if spec["kind"] == "parametric":
            plan = make_plan(session, spec)
            plan.to_pickle(folder / "preview_plan.pkl")
            plan.to_csv(folder / "preview_plan.csv", index=False)
        print(f"Prepared ONLY, no simulations: {folder}. Forecast {spec['expected_runs']} campaign evaluations remains to be checked.")
    elif args.action == "discover":
        run_discovery(session, manifest, folder)
    else:
        execute_campaign(session, manifest, spec, args, folder, resume=args.action == "resume")
    return session

