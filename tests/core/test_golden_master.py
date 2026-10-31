"""Golden master of the output IDFs of accim: 29 configurations of AddAccis, add_accis_to_idf, modify_accis,
gen_outputs_df and the aPMV setpoints, compared object by object (in their order) with the outputs of accim 1.0.0.

Each configuration runs in its own Python process (``golden_master/runner.py write``), because eppy reads all the
models of a process with the IDD of the first one, and the configurations use EnergyPlus 25.1 and 26.2. The
configurations, and how to compare with another version of accim (0.8.2, for instance), are in
golden_master/README.md. After an intended change of the output IDFs, write the golden files again with
``python -m pytest tests/core/test_golden_master.py -q -p no:cacheprovider --update-golden`` and check the change.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from accim.energyplus import find_energyplus

from ._golden import check_golden
from .golden_master import configs, runner

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GOLDEN = HERE / 'golden_master' / 'golden'
TEST_NAME = 'test_the_outputs_are_those_of_the_golden_master'


def _missing_versions(name):
    return [v for v in configs.energyplus_versions(name) if find_energyplus(v, required=False) is None]


@pytest.fixture(scope='session')
def golden_master_outputs(request, tmp_path_factory):
    """Run the selected configurations (each in its own process, several at a time); return the folder and log."""
    selected = [item.callspec.params['name'] for item in request.session.items
                if getattr(item, 'originalname', None) == TEST_NAME and hasattr(item, 'callspec')]
    names = [name for name in selected if not _missing_versions(name)]
    out = tmp_path_factory.mktemp('golden_master')
    if not names:
        return out, ''
    # The accim of this working tree, whatever is installed
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, [str(REPO), os.environ.get('PYTHONPATH')])))
    jobs = str(min(4, os.cpu_count() or 1))
    result = subprocess.run([sys.executable, str(HERE / 'golden_master' / 'runner.py'), 'write', str(out),
                             '--jobs', jobs, '--only', *names], env=env, capture_output=True, text=True)
    return out, result.stdout + result.stderr


@pytest.mark.parametrize('name', configs.NAMES)
def test_the_outputs_are_those_of_the_golden_master(name, golden_master_outputs, update_golden):
    missing = _missing_versions(name)
    if missing:
        pytest.skip(f'needs EnergyPlus {", ".join(missing)}')
    out, log = golden_master_outputs
    actual = out / f'{name}.txt'
    if not actual.exists():
        pytest.fail(f'The configuration {name} failed:\n{log}', pytrace=False)

    check_golden(GOLDEN / f'{name}.txt.xz', actual.read_bytes(), update_golden,
                 what=f'The output of the configuration {name}', dump=actual)


def test_every_configuration_has_a_golden_file_and_every_golden_file_a_configuration():
    assert sorted(p.name[:-len('.txt.xz')] for p in GOLDEN.glob('*.txt.xz')) == sorted(configs.NAMES)


def test_the_canonical_text_keeps_the_objects_and_their_order_but_not_the_comments_or_the_spaces():
    text = ('Version,25.1;  ! a comment\r\n'
            'Schedule:Compact,\n    On,   !- Name\n    Any Number,\n    Through: 12/31,\n'
            '    For: AllDays,\n    Until: 24:00,1;\n\nOutput:VariableDictionary,IDF;\n')

    assert runner.canonical_idf(text) == ('Version,\n    25.1;\n\n'
                                          'Schedule:Compact,\n    On,\n    Any Number,\n    Through: 12/31,\n'
                                          '    For: AllDays,\n    Until: 24:00,\n    1;\n\n'
                                          'Output:VariableDictionary,\n    IDF;\n')
    swapped = runner.canonical_idf('Output:VariableDictionary,IDF;\nVersion,25.1;')
    in_order = runner.canonical_idf('Version,25.1;\nOutput:VariableDictionary,IDF;')
    assert swapped != in_order
    assert runner.compare_file(swapped, in_order, ignore_order=False) is not None
    assert runner.compare_file(swapped, in_order, ignore_order=True) is None


def test_the_outputs_of_a_configuration_can_be_split_by_file():
    text = runner.canonical_outputs({'b.idf': b'Version,25.1;', 'df_outputs.csv': b'a,b\r\n1,2\r\n'}).decode()

    assert runner.split_outputs(text) == {'b.idf': 'Version,\n    25.1;', 'df_outputs.csv': 'a,b\n1,2'}
    assert runner.split_outputs(runner.canonical_outputs({}).decode()) == {'(no output files)': ''}
