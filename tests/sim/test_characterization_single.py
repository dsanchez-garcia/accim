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
VRF2510 = SAMPLE_IDF_DIR / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf"

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
    # NOTA: el camino UNICO con ex_* sobre un IDF sin objetos SPACE casados 1:1 con
    # las zonas del termostato falla (IndexError en accim_Main_single_idf.py:247).
    # El mismo IDF si funciona en el camino LOTE (que usa el resolver de HVAC).
    # Documentado en test_known_bugs.py.
]


def _require_energyplus(version):
    idd = accim.utils.get_idd_path_from_ep_version(version)
    if idd == "not-supported" or not os.path.exists(idd):
        pytest.skip(f"EnergyPlus {version} no instalado (IDD ausente: {idd})")


def _run_single(workdir, source_idf, kwargs):
    """Carga el IDF, aplica el ACCIS generico in-memory y devuelve el idfstr."""
    from besos import eppy_funcs as ef
    import accim.sim.accis_single_idf_funcs as accis

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
