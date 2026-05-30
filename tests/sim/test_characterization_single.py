"""Tests de caracterizacion (golden-file) del camino UNICO / in-memory.

`accim.sim.accis_single_idf_funcs.addAccis(idf=...)` inyecta el ACCIS generico
(programas/sensores/actuadores EMS, schedules, HVAC, outputs) sobre un objeto IDF
en memoria y lo devuelve, SIN escribir a disco ni ejecutar EnergyPlus. Es el motor
compartido que el subpaquete parametric_and_optimisation reutiliza; por eso se
caracteriza aqui de forma rapida (forma canonica de idf.idfstr()).

Bootstrap inicial de los goldens:
    pytest tests/sim/test_characterization_single.py --update-golden
"""

import os
from pathlib import Path

import pytest

import accim.utils

from ._golden import canonicalize_idf_text, assert_or_write_golden

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_IDF_DIR = REPO_ROOT / "accim" / "sample_files" / "sample IDFs" / "input_IDFs"
TEST_DATA_DIR = REPO_ROOT / "tests" / "test_data"
GOLDEN_DIR = Path(__file__).parent / "golden" / "single"

VRF960 = SAMPLE_IDF_DIR / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V960.idf"
VRF940 = SAMPLE_IDF_DIR / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf"
VRF2510 = SAMPLE_IDF_DIR / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf"
SF = TEST_DATA_DIR / "SF_Detached_B_min_North.idf"

COMMON = dict(
    SupplyAirTempInputMethod="supply air temperature",
    Output_keep_existing=False,
    verboseMode=False,
)


def _cfg(id, source, version, **kwargs):
    merged = dict(COMMON)
    merged.update(kwargs)
    # El camino unico no admite 'auto': hay que pasar la version explicita.
    merged["EnergyPlus_version"] = version
    return {"id": id, "source": source, "version": version, "kwargs": merged}


CONFIGS = [
    _cfg("single_vrf_mm_temp_v960", VRF960, "9.6", ScriptType="vrf_mm",
         TempCtrl="temperature", Output_type="standard", Output_freqs=["hourly"]),
    _cfg("single_vrf_ac_temp_v960", VRF960, "9.6", ScriptType="vrf_ac",
         TempCtrl="temperature", Output_type="standard", Output_freqs=["hourly"]),
    _cfg("single_vrf_mm_temp_v2510", VRF2510, "25.1", ScriptType="vrf_mm",
         TempCtrl="temperature", Output_type="detailed", Output_freqs=["hourly"]),
    # ex_* en el camino unico ya funciona tras converger al motor del lote
    # (Fase 1): hereda el resolver de HVAC y el guard del fallback SPACE.
    _cfg("single_ex_mm_temp_v960", SF, "9.6", ScriptType="ex_mm",
         TempCtrl="temperature", Output_type="standard", Output_freqs=["hourly"]),
]


def _require_energyplus(version):
    idd = accim.utils.get_idd_path_from_ep_version(version)
    if idd == "not-supported" or not os.path.exists(idd):
        pytest.skip(f"EnergyPlus {version} no instalado (IDD ausente: {idd})")


def _run_single(workdir, source_idf, kwargs):
    """Carga el IDF, aplica el ACCIS generico in-memory y devuelve el idfstr."""
    from besos import eppy_funcs as ef
    import accim.sim.single as accis

    prev = os.getcwd()
    os.chdir(str(workdir))  # por si el codigo escribiese algun fichero auxiliar
    try:
        building = ef.get_building(str(source_idf))
        result = accis.addAccis(idf=building, **kwargs)
    finally:
        os.chdir(prev)
    idf_out = result if result is not None else building
    return idf_out.idfstr()


@pytest.mark.parametrize("cfg", CONFIGS, ids=[c["id"] for c in CONFIGS])
def test_single_characterization(cfg, tmp_path, update_golden):
    if not Path(cfg["source"]).exists():
        pytest.skip(f"IDF de muestra ausente: {cfg['source']}")
    _require_energyplus(cfg["version"])

    text = _run_single(tmp_path, cfg["source"], cfg["kwargs"])
    actual = canonicalize_idf_text(text)
    assert actual.strip(), "idfstr() vacio tras aplicar el ACCIS"

    golden_file = GOLDEN_DIR / (cfg["id"] + ".idf.gz")
    err = assert_or_write_golden(golden_file, actual, update_golden, dump_suffix=".actual.idf")
    if err:
        pytest.fail(f"idf.idfstr() cambio para '{cfg['id']}'.\n{err}")


# --------------------------------------------------------------------------- #
# Flujo real del subpaquete parametric_and_optimisation: addAccis + modifyAccis
# (modifyAccis fija una variante concreta reescribiendo lineas de los programas
# EMS SetInputData/ApplyCAT/SetAST, incl. get_SetAST_lines). Es el objetivo del
# refactor de Fase 4, por lo que conviene caracterizarlo aqui.
# --------------------------------------------------------------------------- #
def _base_addaccis(version):
    return dict(
        ScriptType="vrf_mm",
        SupplyAirTempInputMethod="supply air temperature",
        TempCtrl="temperature",
        Output_type="standard",
        Output_freqs=["hourly"],
        Output_keep_existing=False,
        EnergyPlus_version=version,
        verboseMode=False,
    )


MODIFY_CONFIGS = [
    # id, source, version, modify_kwargs
    ("single_modify_cs2_v960", VRF960, "9.6",
     dict(ComfStand=2, CAT=80, ComfMod=3, HVACmode=2, VentCtrl=0)),
    # ComfStand=99 (modelo custom) es exactamente lo que aplica el wrapper
    # AccimPredefModelsParamSim (main.py:4603).
    ("single_modify_cs99_v960", VRF960, "9.6",
     dict(ComfStand=99, CAT=80, ComfMod=3, HVACmode=2, VentCtrl=0)),
    ("single_modify_cs1_v940", VRF940, "9.4",
     dict(ComfStand=1, CAT=3, ComfMod=1, HVACmode=2, VentCtrl=1)),
]


def _run_single_modify(workdir, source_idf, version, modify_kwargs):
    from besos import eppy_funcs as ef
    import accim.sim.single as accis

    prev = os.getcwd()
    os.chdir(str(workdir))
    try:
        building = ef.get_building(str(source_idf))
        accis.addAccis(idf=building, **_base_addaccis(version))
        accis.modifyAccis(idf=building, **modify_kwargs)
    finally:
        os.chdir(prev)
    return building.idfstr()


@pytest.mark.parametrize("cid,source,version,modify_kwargs", MODIFY_CONFIGS,
                         ids=[c[0] for c in MODIFY_CONFIGS])
def test_single_modify_characterization(cid, source, version, modify_kwargs, tmp_path, update_golden):
    if not Path(source).exists():
        pytest.skip(f"IDF de muestra ausente: {source}")
    _require_energyplus(version)

    text = _run_single_modify(tmp_path, source, version, modify_kwargs)
    actual = canonicalize_idf_text(text)
    assert actual.strip(), "idfstr() vacio tras addAccis+modifyAccis"

    golden_file = GOLDEN_DIR / (cid + ".idf.gz")
    err = assert_or_write_golden(golden_file, actual, update_golden, dump_suffix=".actual.idf")
    if err:
        pytest.fail(f"addAccis+modifyAccis cambio para '{cid}'.\n{err}")


# --------------------------------------------------------------------------- #
# Via aPMV: apply_apmv_setpoints (la usa parametric con parameters_type='apmv
# setpoints'). Convierte termostatos DualSetpoint a confort Fanger e inyecta EMS.
# --------------------------------------------------------------------------- #
def _run_apmv(workdir, source_idf):
    from besos import eppy_funcs as ef
    from accim.sim import apmv as apmv_setpoints

    prev = os.getcwd()
    os.chdir(str(workdir))
    try:
        building = ef.get_building(str(source_idf))
        apmv_setpoints.apply_apmv_setpoints(
            building=building, outputs_freq=["hourly"], verbose_mode=False
        )
    finally:
        os.chdir(prev)
    return building.idfstr()


@pytest.mark.parametrize("cid,source,version", [
    ("single_apmv_sf_v960", SF, "9.6"),
], ids=["single_apmv_sf_v960"])
def test_single_apmv_characterization(cid, source, version, tmp_path, update_golden):
    if not Path(source).exists():
        pytest.skip(f"IDF de muestra ausente: {source}")
    _require_energyplus(version)

    text = _run_apmv(tmp_path, source)
    actual = canonicalize_idf_text(text)
    assert actual.strip(), "idfstr() vacio tras apply_apmv_setpoints"

    golden_file = GOLDEN_DIR / (cid + ".idf.gz")
    err = assert_or_write_golden(golden_file, actual, update_golden, dump_suffix=".actual.idf")
    if err:
        pytest.fail(f"apply_apmv_setpoints cambio para '{cid}'.\n{err}")
