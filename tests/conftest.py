# Shared pytest configuration for accim's characterization (golden-file) tests.
#
# Both tests/sim and tests/data use golden snapshots that freeze the exact output
# of the code under test, so any accidental behavioural change is detected.
#
# Regenerate the goldens (deliberately, e.g. when first creating them):
#
#     pytest tests/sim --update-golden
#     pytest tests/data --update-golden
#
# or with the environment variable ACCIM_UPDATE_GOLDEN=1.

import os
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Regenerate (overwrite) the golden files instead of comparing against them.",
    )


@pytest.fixture(scope="session")
def update_golden(request):
    return bool(request.config.getoption("--update-golden")) or \
        os.environ.get("ACCIM_UPDATE_GOLDEN", "") not in ("", "0", "false", "False")
