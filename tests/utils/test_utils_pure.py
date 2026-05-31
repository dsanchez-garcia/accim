"""Tests for the dependency-free helpers in accim.utils."""

import pytest

from accim.utils import (
    get_idd_path_from_ep_version,
    transform_ddmm_to_int,
    remove_accents,
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
