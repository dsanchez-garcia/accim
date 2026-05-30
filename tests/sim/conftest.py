# conftest.py — tests/sim
#
# Red de seguridad (golden-file / characterization) para el refactor del nucleo
# accim/sim. Estos tests capturan la salida EXACTA (IDF generado) del codigo
# actual y la comparan tras cada cambio, de modo que cualquier alteracion
# accidental del IDF producido por addAccis se detecta de inmediato.
#
# Regenerar los goldens (solo de forma deliberada, p.ej. al crearlos por
# primera vez):
#
#     pytest tests/sim --update-golden
#
# o bien con la variable de entorno ACCIM_UPDATE_GOLDEN=1.

import os
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Regenera (sobrescribe) los ficheros golden de tests/sim en vez de comparar.",
    )


@pytest.fixture(scope="session")
def update_golden(request):
    return bool(request.config.getoption("--update-golden")) or \
        os.environ.get("ACCIM_UPDATE_GOLDEN", "") not in ("", "0", "false", "False")
