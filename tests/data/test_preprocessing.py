"""Tests for accim.data.preprocessing.

Network access (reverse geocoding via OpenStreetMap) is mocked, so the
address-parsing logic of the give_address* classes is exercised without hitting
the network. capitalize_words is a pure function.
"""

import pytest

from accim.data import preprocessing
from accim.data.preprocessing import capitalize_words


class _FakeResp:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


@pytest.mark.parametrize("text,expected", [
    ("madrid", "Madrid"),
    ("new york city", "New-York-City"),
    ("SAN sebastian", "San-Sebastian"),
    ("a b c", "A-B-C"),
])
def test_capitalize_words(text, expected):
    assert capitalize_words(text) == expected


def test_give_address_parses_address_and_full_address(monkeypatch):
    import requests
    fake = {"address": {"city": "Madrid", "country": "Spain",
                        "country_code": "es", "state": ""}}
    monkeypatch.setattr(requests, "get", lambda url, *a, **k: _FakeResp(fake))

    addr = preprocessing.give_address(40.4, -3.7)
    assert addr.address == fake["address"]
    # full_address joins non-empty values, excluding 'country_code'
    assert addr.full_address == "Madrid, Spain"


def test_give_address_ssl_same_parsing(monkeypatch):
    # give_address_ssl uses certifi/ssl locally and then requests.get; mocking
    # requests.get is enough (no real network).
    import requests
    fake = {"address": {"town": "Aberdeen", "country": "United Kingdom",
                        "country_code": "gb"}}
    monkeypatch.setattr(requests, "get", lambda url, *a, **k: _FakeResp(fake))

    addr = preprocessing.give_address_ssl(57.1, -2.1)
    assert addr.address == fake["address"]
    assert addr.full_address == "Aberdeen, United Kingdom"
