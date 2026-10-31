"""Shared options and fixtures of tests/core."""
import os

import pytest


def pytest_addoption(parser):
    parser.addoption('--update-golden', action='store_true', default=False,
                     help='Write the golden files of tests/core again instead of comparing with them.')


@pytest.fixture(scope='session')
def update_golden(request):
    """Whether the tests write their golden files again (``--update-golden`` or ``ACCIM_UPDATE_GOLDEN=1``)."""
    from_env = os.environ.get('ACCIM_UPDATE_GOLDEN', '').strip().lower() not in ('', '0', 'false', 'no')
    return bool(request.config.getoption('--update-golden', default=False)) or from_env
