"""Tests de caracterizacion (golden-file) del camino LOTE de addAccis.

Estos tests congelan la salida EXACTA del codigo actual antes del refactor del
nucleo accim/sim. addAccis() solo manipula texto IDF via eppy/besos (no ejecuta
EnergyPlus), por lo que la captura es offline; solo requiere que la instalacion
de EnergyPlus correspondiente a la version del IDF este presente para leer el IDD.

Cada configuracion:
  1. copia un IDF de muestra a un directorio temporal,
  2. ejecuta addAccis() de forma headless (todos los argumentos provistos),
  3. recoge el/los IDF de salida generados (nombre con '['),
  4. compara nombre + contenido CANONICO (insensible al orden) contra el golden.

Bootstrap inicial de los goldens:
    pytest tests/sim/test_characterization_batch.py --update-golden
"""

import os
import shutil
from pathlib import Path

import pytest

import accim.utils

from ._golden import canonicalize_idf_text, assert_or_write_golden, FS

# --------------------------------------------------------------------------- #
# Rutas
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_IDF_DIR = REPO_ROOT / "accim" / "sample_files" / "sample IDFs" / "input_IDFs"
TEST_DATA_DIR = REPO_ROOT / "tests" / "test_data"
GOLDEN_DIR = Path(__file__).parent / "golden" / "batch"

VRF940 = SAMPLE_IDF_DIR / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf"
VRF960 = SAMPLE_IDF_DIR / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V960.idf"
VRF2510 = SAMPLE_IDF_DIR / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf"
SF = TEST_DATA_DIR / "SF_Detached_B_min_North.idf"

# Argumentos comunes a todas las configuraciones.
COMMON = dict(
    supply_air_temp_method="supply air temperature",  # ignorado por ex_*
    output_keep_existing=False,
    output_gen_dataframe=False,
    energyplus_version="auto",
    confirm_generation=True,
    verbose=False,
)


def _cfg(id, source, version, **kwargs):
    merged = dict(COMMON)
    merged.update(kwargs)
    return {"id": id, "source": source, "version": version, "kwargs": merged}


# Matriz representativa: 4 ScriptTypes, standard/detailed/simplified, 3 versiones de
# EnergyPlus, varios ComfStand/CAT/ComfMod, VentCtrl 0/1/2.
CONFIGS = [
    _cfg("vrf_mm_temp_v960", VRF960, "9.6", script_type="vrf_mm", temp_control="temperature",
         output_type="standard", output_freqs=["hourly"],
         comfort_standard=[2], category=[80], comfort_mode=[3], hvac_mode=[2], vent_control=[0]),
    _cfg("vrf_ac_temp_v960", VRF960, "9.6", script_type="vrf_ac", temp_control="temperature",
         output_type="standard", output_freqs=["hourly"],
         comfort_standard=[2], category=[80], comfort_mode=[3]),
    # NOTA: el camino LOTE con TempCtrl='pmv' esta ROTO en el codigo actual
    # (UnboundLocalError 'ComfStand_value' en accim_IDFgeneration.generate_idfs:1686, la
    # rama PMV reutiliza la variable de bucle de la rama 'temp'). Documentado en
    # test_known_bugs.py; se anadira aqui como golden cuando se corrija.
    _cfg("vrf_mm_temp_v940", VRF940, "9.4", script_type="vrf_mm", temp_control="temperature",
         output_type="standard", output_freqs=["hourly"],
         comfort_standard=[1], category=[3], comfort_mode=[1], hvac_mode=[2], vent_control=[1]),
    _cfg("vrf_mm_temp_v2510", VRF2510, "25.1", script_type="vrf_mm", temp_control="temperature",
         output_type="detailed", output_freqs=["hourly"],
         comfort_standard=[3], category=[80], comfort_mode=[3], hvac_mode=[2], vent_control=[2]),
    _cfg("ex_mm_temp_v960", SF, "9.6", script_type="ex_mm", temp_control="temperature",
         output_type="standard", output_freqs=["hourly"],
         comfort_standard=[2], category=[80], comfort_mode=[3], hvac_mode=[2], vent_control=[0]),
    _cfg("ex_ac_temp_v960", SF, "9.6", script_type="ex_ac", temp_control="temperature",
         output_type="simplified", output_freqs=["hourly"],
         comfort_standard=[2], category=[80], comfort_mode=[3]),
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _require_energyplus(version):
    idd = accim.utils.get_idd_path_from_ep_version(version)
    if idd == "not-supported" or not os.path.exists(idd):
        pytest.skip(f"EnergyPlus {version} no instalado (IDD ausente: {idd})")


def _run_batch(workdir, source_idf, kwargs):
    """Ejecuta addAccis headless en workdir y devuelve {filename: texto_idf}."""
    shutil.copy(str(source_idf), str(workdir))
    prev = os.getcwd()
    os.chdir(str(workdir))
    try:
        from accim.sim import batch
        batch.AddAccis(**kwargs)
    finally:
        os.chdir(prev)
    outputs = {}
    for name in sorted(os.listdir(str(workdir))):
        if name.endswith(".idf") and "[" in name:
            outputs[name] = (Path(workdir) / name).read_bytes().decode("utf-8", "surrogateescape")
    return outputs


def _canonical(outputs):
    """Forma canonica: por cada IDF generado, su nombre + su contenido canonicalizado."""
    chunks = []
    for name in sorted(outputs):
        chunks.append(("FILENAME" + FS + name).encode("utf-8", "surrogateescape"))
        chunks.append(canonicalize_idf_text(outputs[name]))
    return b"\n".join(chunks)


# --------------------------------------------------------------------------- #
# Test
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("cfg", CONFIGS, ids=[c["id"] for c in CONFIGS])
def test_batch_characterization(cfg, tmp_path, update_golden):
    if not Path(cfg["source"]).exists():
        pytest.skip(f"IDF de muestra ausente: {cfg['source']}")
    _require_energyplus(cfg["version"])

    outputs = _run_batch(tmp_path, cfg["source"], cfg["kwargs"])
    assert outputs, "addAccis no genero ningun IDF de salida"
    actual = _canonical(outputs)

    golden_file = GOLDEN_DIR / (cfg["id"] + ".txt.gz")
    err = assert_or_write_golden(golden_file, actual, update_golden)
    if err:
        pytest.fail(f"La salida de addAccis cambio para '{cfg['id']}'.\n{err}")
