"""Bugs pre-existentes detectados al construir la red de seguridad del refactor.

Se registran como tests `xfail` para que: (1) queden documentados y no se olviden,
y (2) si una fase posterior los corrige, el test pase a XPASS y avise de que ya se
puede promover a golden / cerrar la incidencia.

No se corrigen aqui: la Fase 0 solo construye la red de seguridad.
"""

import os
import shutil
from pathlib import Path

import pytest

import accim.utils

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_IDF_DIR = REPO_ROOT / "accim" / "sample_files" / "sample IDFs" / "input_IDFs"
VRF960 = SAMPLE_IDF_DIR / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V960.idf"


@pytest.mark.xfail(
    reason="Camino LOTE con TempCtrl='pmv' roto: UnboundLocalError 'ComfStand_value' "
           "en accim_IDFgeneration.genIDF (la rama PMV del bucle de generacion usa la "
           "variable de bucle de la rama 'temp').",
    strict=True,
    raises=UnboundLocalError,
)
def test_batch_pmv_currently_broken(tmp_path):
    idd = accim.utils.get_idd_path_from_ep_version("9.6")
    if idd == "not-supported" or not os.path.exists(idd):
        pytest.skip("EnergyPlus 9.6 no instalado")
    if not VRF960.exists():
        pytest.skip(f"IDF de muestra ausente: {VRF960}")

    shutil.copy(str(VRF960), str(tmp_path))
    prev = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        from accim.sim import accis
        accis.addAccis(
            ScriptType="vrf_mm",
            SupplyAirTempInputMethod="supply air temperature",
            TempCtrl="pmv",
            Output_keep_existing=False,
            Output_gen_dataframe=False,
            Output_type="standard",
            Output_freqs=["hourly"],
            EnergyPlus_version="auto",
            ComfStand=[2], CAT=[80], ComfMod=[3], HVACmode=[2], VentCtrl=[0],
            confirmGen=True,
            verboseMode=False,
        )
    finally:
        os.chdir(prev)


# NOTA: el bug del camino UNICO con ex_* (IndexError en accim_Main_single_idf.py:247)
# quedo CORREGIDO en la Fase 1 al converger el camino unico al motor del lote. Su
# caracterizacion vive ahora como golden real en test_characterization_single.py
# (config 'single_ex_mm_temp_v960').
