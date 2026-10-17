"""Tests for the import of geopy in accim.data.preprocessing.

Before, the module imported geopy when it was loaded, but geopy was not a dependency of accim, so
`from accim.data.preprocessing import rename_epw_files` failed on a clean install. Now geopy is in
install_requires, and rename_epw_files imports it only when it geolocates an EPW file.
"""
import ast
import importlib
import sys
from pathlib import Path

import pytest

SETUP_PY = Path(__file__).resolve().parents[2] / 'setup.py'


@pytest.fixture
def without_geopy(monkeypatch):
    """Make `import geopy` fail, as on a computer where geopy is not installed."""
    for name in [m for m in sys.modules if m == 'geopy' or m.startswith('geopy.')]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, 'geopy', None)
    monkeypatch.delitem(sys.modules, 'accim.data.preprocessing', raising=False)


def test_preprocessing_imports_without_geopy(without_geopy):
    module = importlib.import_module('accim.data.preprocessing')

    assert hasattr(module, 'rename_epw_files')


def test_import_geopy_explains_how_to_install_it(without_geopy):
    module = importlib.import_module('accim.data.preprocessing')

    with pytest.raises(ImportError, match='pip install geopy'):
        module.import_geopy()


def test_geopy_is_a_dependency():
    install_requires = None
    for node in ast.walk(ast.parse(SETUP_PY.read_text(encoding='utf-8'))):
        if isinstance(node, ast.keyword) and node.arg == 'install_requires':
            install_requires = ast.literal_eval(node.value)

    assert install_requires is not None
    assert 'geopy' in install_requires
