"""Tests for accim.data.preprocessing.rename_epw_files with EPW files that name no scenario or year.

Before, the checks compared the scenario and year cells with the string 'nan', but they are real
NaN (or the column does not exist when no EPW names a scenario or year), so 'Present' was never
assigned and rename_epw_files failed with TypeError or KeyError. The test uses the EPW files of the
sample notebook of rename_epw_files; the dictionaries give the city and country of each EPW,
so nothing is geolocated (no geopy or internet connection needed).
"""
import builtins
import shutil
from pathlib import Path

import pytest

import accim.data.preprocessing as preprocessing

EPW_DIR = Path(__file__).resolve().parents[2] / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'rename_epw_files'
RENAME_CITY_DICT = {'aberdeen': 'Aberdeen', 'london': 'London', 'ponta_grossa': 'Ponta Grossa'}
COUNTRY_TO_CITY_DICT = {'United Kingdom': ['London', 'Aberdeen'], 'Brazil': ['Ponta Grossa']}

pytestmark = pytest.mark.skipif(not EPW_DIR.is_dir(), reason='needs the sample files of the repository')


@pytest.fixture
def epw_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Answer the prompts with Enter (no EPW is excluded from renaming).
    monkeypatch.setattr(builtins, 'input', lambda prompt='': '')
    monkeypatch.setattr(preprocessing, 'import_geopy', lambda: pytest.fail('nothing should be geolocated'))
    return tmp_path


def _rename(folder, epw_names):
    for name in epw_names:
        shutil.copy(EPW_DIR / name, folder)
    preprocessing.rename_epw_files(
        rename_city_dict=RENAME_CITY_DICT,
        country_to_city_dict=COUNTRY_TO_CITY_DICT,
        confirm_renaming=True,
        confirm_deletion=False,
    )


def test_epws_without_scenario_are_present(epw_folder):
    _rename(epw_folder, [
        'GBR_Aberdeen.Dyce.030910_IWEC.epw',
        'GBR_London.Gatwick.037760_IWEC.epw',
        'RCP26_2100_GC03_Ponta_Grossa.epw',
    ])

    assert (epw_folder / 'United-Kingdom_Aberdeen_Present.epw').exists()
    assert (epw_folder / 'United-Kingdom_London_Present.epw').exists()
    assert (epw_folder / 'Brazil_Ponta-Grossa_RCP26-2100.epw').exists()


def test_no_epw_names_a_scenario_or_year(epw_folder):
    _rename(epw_folder, ['GBR_London.Gatwick.037760_IWEC.epw'])

    assert (epw_folder / 'United-Kingdom_London_Present.epw').exists()
