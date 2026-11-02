"""Tests for accim.data.preprocessing.rename_epw_files with EPW files that name no scenario or year.

Before, the checks compared the scenario and year cells with the string 'nan', but they are real
NaN (or the column does not exist when no EPW names a scenario or year), so 'Present' was never
assigned and rename_epw_files failed with TypeError or KeyError. The test uses the EPW files of the
sample notebook of rename_epw_files; the dictionaries give the city and country of each EPW,
so nothing is geolocated (no geopy or internet connection needed), except in the tests of the geolocation,
which replace Nominatim.

Found on 2026-11-02 (review of 2026-10-24): the original EPWs excluded from the renaming, or not copied, were deleted
too; and the geolocation stopped when Nominatim gave no address or took too long.
"""
import builtins
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

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


NAMES = ['GBR_Aberdeen.Dyce.030910_IWEC.epw', 'GBR_London.Gatwick.037760_IWEC.epw']


def _rename_and_delete(folder, monkeypatch, exclude='', confirm_renaming=True):
    for name in NAMES:
        shutil.copy(EPW_DIR / name, folder)
    monkeypatch.setattr(builtins, 'input', lambda prompt='': exclude if 'exclude some EPWs' in prompt else '')
    preprocessing.rename_epw_files(filelist=NAMES, rename_city_dict=RENAME_CITY_DICT,
                                   country_to_city_dict=COUNTRY_TO_CITY_DICT, confirm_renaming=confirm_renaming,
                                   confirm_deletion=True)
    return sorted(p.name for p in folder.glob('*.epw'))


def test_the_originals_of_the_renamed_epws_are_deleted(epw_folder, monkeypatch):
    assert _rename_and_delete(epw_folder, monkeypatch) == ['United-Kingdom_Aberdeen_Present.epw',
                                                           'United-Kingdom_London_Present.epw']


def test_the_epws_excluded_from_the_renaming_are_kept(epw_folder, monkeypatch):
    # Before, confirm_deletion deleted the originals of all the EPWs, also those excluded from the renaming, which
    # were not copied: they were lost
    assert _rename_and_delete(epw_folder, monkeypatch, exclude='1') == ['GBR_London.Gatwick.037760_IWEC.epw',
                                                                        'United-Kingdom_Aberdeen_Present.epw']


def test_the_originals_are_kept_if_they_are_not_copied(epw_folder, monkeypatch):
    assert _rename_and_delete(epw_folder, monkeypatch, confirm_renaming=False) == NAMES


class _Location:
    def __init__(self, raw):
        self.raw = raw


def _geolocate(folder, monkeypatch, reverse, answers=None):
    """Rename the London EPW without the dictionaries, so it is geolocated with a fake Nominatim of geopy, whose
    reverse() is the function given; the answers to the prompts are those given (by the beginning of the question),
    or Enter."""
    import geopy

    made = {}

    class FakeNominatim:
        def __init__(self, **kwargs):
            made.update(kwargs)

        def reverse(self, query):
            return reverse(query)

    shutil.copy(EPW_DIR / NAMES[1], folder)
    monkeypatch.setattr(preprocessing, 'import_geopy', lambda: (geopy, FakeNominatim))
    answers = answers or {}
    monkeypatch.setattr(builtins, 'input', lambda prompt='': next(
        (answer for question, answer in answers.items() if prompt.startswith(question)), ''))
    preprocessing.rename_epw_files(filelist=[NAMES[1]], confirm_renaming=True, confirm_deletion=False)
    return made, sorted(p.name for p in folder.glob('*.epw') if p.name != NAMES[1])


def test_geolocated_epw(epw_folder, monkeypatch):
    made, renamed = _geolocate(epw_folder, monkeypatch, lambda query: _Location(
        {'address': {'city': 'Crawley', 'country_code': 'gb'}, 'display_name': 'Gatwick, Crawley, United Kingdom'}))

    # The usage policy of Nominatim asks for a User-Agent that identifies the application (before, 'abcd')
    assert made['user_agent'].startswith('accim/') and made['timeout'] == 10
    assert renamed == ['United-Kingdom_Gatwick_Present.epw']


def test_coordinates_without_an_address_are_asked_for(epw_folder, monkeypatch):
    # Nominatim gives no address for some coordinates; before, rename_epw_files stopped with AttributeError
    made, renamed = _geolocate(epw_folder, monkeypatch, lambda query: None, answers={
        'Please enter the city or subcountry': 'London', 'Please enter the country': 'United Kingdom'})

    assert renamed == ['United-Kingdom_London_Present.epw']


def test_without_geopy_service_the_address_is_asked_to_nominatim_directly(epw_folder, monkeypatch):
    # Before, only an unavailable service fell back to give_address: a timeout stopped rename_epw_files
    import geopy.exc

    def timed_out(query):
        raise geopy.exc.GeocoderTimedOut('timed out')

    sent = []

    def fake_get(url, **kwargs):
        sent.append(kwargs)
        return SimpleNamespace(json=lambda: {'address': {'city': 'London', 'country_code': 'gb',
                                                         'country': 'United Kingdom'}})

    monkeypatch.setattr(requests, 'get', fake_get)
    made, renamed = _geolocate(epw_folder, monkeypatch, timed_out)

    assert renamed == ['United-Kingdom_London_Present.epw']
    assert sent[0]['headers']['User-Agent'].startswith('accim/')
