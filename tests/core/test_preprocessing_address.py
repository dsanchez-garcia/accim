"""Tests for the functions of accim.data.preprocessing that rename_epw_files uses to name the EPW files:
capitalize_words, and give_address and give_address_ssl, which find the address of the coordinates of an EPW
file in OpenStreetMap (Nominatim).

Ported from the tests of the branch refactor/sim-v1 (tests/data/test_preprocessing.py). requests.get is
replaced, so nothing is sent to OpenStreetMap. give_address_openssl is not tested: it opens a connection to
OpenStreetMap to read its certificates.
"""
import certifi
import pytest
import requests

from accim.data import preprocessing
from accim.data.preprocessing import capitalize_words

NOMINATIM = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2'
ADDRESS = {'city': 'Seville', 'county': '', 'state': 'Andalusia', 'country': 'Spain', 'country_code': 'es'}


class _Response:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


@pytest.fixture
def requests_sent(monkeypatch):
    """The URL and the keyword arguments of each request; Nominatim answers with ADDRESS."""
    sent = []

    def fake_get(url, **kwargs):
        sent.append((url, kwargs))
        return _Response({'place_id': 1, 'address': dict(ADDRESS)})

    monkeypatch.setattr(requests, 'get', fake_get)
    return sent


@pytest.mark.parametrize('text, expected', [
    ('madrid', 'Madrid'),
    ('new york city', 'New-York-City'),
    ('SAN sebastian', 'San-Sebastian'),
    ('  ponta   grossa ', 'Ponta-Grossa'),
])
def test_capitalize_words(text, expected):
    assert capitalize_words(text) == expected


def test_give_address(requests_sent):
    # rename_epw_files gives the coordinates as they are written in the EPW file
    address = preprocessing.give_address('37.42', '-5.9')

    [(url, kwargs)] = requests_sent
    assert url == f'{NOMINATIM}&lat=37.42&lon=-5.9'
    # The usage policy of Nominatim asks for a User-Agent that identifies the application; before, there was none
    assert kwargs['headers']['User-Agent'].startswith('accim/') and kwargs['timeout'] == 10
    assert address.address == ADDRESS
    # The values that are not empty, without the country code
    assert address.full_address == 'Seville, Andalusia, Spain'


@pytest.mark.parametrize('function', [preprocessing.give_address, preprocessing.give_address_ssl])
def test_coordinates_without_an_address(monkeypatch, capsys, function):
    # Nominatim answers so for the coordinates without an address, such as those in the sea; before, KeyError
    monkeypatch.setattr(requests, 'get', lambda url, **kwargs: _Response({'error': 'Unable to geocode'}))

    address = function(40.0, -30.0)

    assert address.address == {} and address.full_address == ''
    assert 'OpenStreetMap gives no address for the coordinates 40.0, -30.0: Unable to geocode' in capsys.readouterr().out


def test_give_address_ssl_verifies_the_certificates_with_those_of_certifi(requests_sent):
    address = preprocessing.give_address_ssl(57.2, -2.2)

    [(url, kwargs)] = requests_sent
    assert url == f'{NOMINATIM}&lat=57.2&lon=-2.2'
    assert kwargs['verify'] == certifi.where()
    assert kwargs['timeout'] == 10
    assert kwargs['headers']['User-Agent'].startswith('accim/')
    assert address.address == ADDRESS
    assert address.full_address == 'Seville, Andalusia, Spain'
