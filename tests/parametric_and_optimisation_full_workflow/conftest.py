# conftest.py — parametric_and_optimisation_full_workflow
#
# Cambia el directorio de trabajo a esta subcarpeta antes de ejecutar
# cualquier test, de forma que los paths relativos a IDF y EPW sean correctos
# independientemente de desde dónde se invoque pytest.

import os
import pytest

# Directorio de esta subcarpeta (donde están los IDFs, EPWs y scripts)
TEST_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(autouse=True)
def change_to_test_dir(monkeypatch):
    """Cambia el cwd a la carpeta del test antes de cada test."""
    monkeypatch.chdir(TEST_DIR)
