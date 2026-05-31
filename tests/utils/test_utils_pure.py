"""Tests for the dependency-free helpers in accim.utils."""

import pytest

from accim.utils import (
    get_idd_path_from_ep_version,
    transform_ddmm_to_int,
    remove_accents,
    amend_idf_version_from_dsb,
    remove_accents_in_idf,
)


@pytest.mark.parametrize("version,expected", [
    ("9.4", "C:/EnergyPlusV9-4-0/Energy+.idd"),
    ("9.6", "C:/EnergyPlusV9-6-0/Energy+.idd"),
    ("23.2", "C:/EnergyPlusV23-2-0/Energy+.idd"),
    ("25.1", "C:/EnergyPlusV25-1-0/Energy+.idd"),
    ("9.9", "not-supported"),
    ("nonsense", "not-supported"),
])
def test_get_idd_path_from_ep_version(version, expected):
    assert get_idd_path_from_ep_version(version) == expected


@pytest.mark.parametrize("ddmm,expected", [
    ("01/01", 1),
    ("15/02", 46),     # 31 (Jan) + 15
    ("31/12", 365),
])
def test_transform_ddmm_to_int(ddmm, expected):
    assert transform_ddmm_to_int(ddmm) == expected


@pytest.mark.parametrize("text,expected", [
    ("Málaga", "Malaga"),
    ("Sevilla", "Sevilla"),
    ("Aragón", "Aragon"),
    ("Crème brûlée", "Creme brulee"),
])
def test_remove_accents(text, expected):
    assert remove_accents(text) == expected


def test_amend_idf_version_from_dsb(tmp_path):
    # DesignBuilder 7.x exports 'Version, 9.4.0.002' which eppy/EnergyPlus reject.
    p = tmp_path / "model.idf"
    p.write_text("Version, 9.4.0.002;\nBuilding, X;\n", encoding="utf-8")
    amend_idf_version_from_dsb(str(p))
    content = p.read_text(encoding="utf-8")
    assert "Version, 9.4;" in content
    assert "9.4.0.002" not in content


def test_remove_accents_in_idf(tmp_path):
    p = tmp_path / "model.idf"
    p.write_text("Zone, Salón;\nZone, Almacén;\n", encoding="utf-8")
    remove_accents_in_idf(str(p))
    content = p.read_text(encoding="utf-8")
    assert "Salon" in content and "Almacen" in content
    assert "ó" not in content and "é" not in content
