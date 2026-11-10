"""Tests for the comfort standards defined by their data (proposal B3, :mod:`accim.sim.standards` and
:mod:`accim.sim.ems.standard_lines`).

A comfort standard defined by its data (number 100 or more, decision D1 of the brief of 1.2.0) is registered for the
Python session with ``register_comfort_standard``, or read from a YAML file with ``load_comfort_standards``: accim adds
its branches ``elseif ComfStand == <n>`` to the chains of the built-in comfort standards, whose lines do not change, and
the subprograms of its comfort modes, so AddAccis, modify_accis, compute_setpoints, print_setpoint_ems_code and the
parametric module take it as a built-in one. The registry is global: the fixture of this module leaves it as it was.
The unit tests run the programs with the Erl interpreter of accim (compute_setpoints); the last tests simulate output
IDFs of AddAccis with EnergyPlus 25.1 (verify_accim_simulation, and both backends).
"""
import copy
import dataclasses
import filecmp
import re
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim import standards as st
from accim.sim.ems import program_lines as pl
from accim.sim.ems import standard_lines as sdl
from accim.sim.ems.erl import ErlProgramSet
from accim.sim.ems.setast import MODULAR_COMFORT_MODES
from accim.sim.ems.setpoint_lines import SETPOINT_LINES
from accim.sim.preview import compute_setpoints
from accim.utils import get_setpoint_ems_code, get_setpoint_ems_programs, print_setpoint_ems_code

REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / 'accim' / 'sample_files' / 'comfort_standards'
AQILAH = SAMPLES / 'jpn_aqilah2025_fr.yaml'
QATAR = SAMPLES / 'qat_indraganti2018_hvac.yaml'
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
ZONES = ['Block1_Zone1', 'Block1_Zone2']
STEPS = 6
AQILAH_TITLE = '101 = JPN Aqilah 2025 (dwellings, free-running)'


@pytest.fixture(autouse=True)
def empty_registry():
    """Each test begins without comfort standards in the registry, which is global, and leaves it as it was."""
    state = (dict(st.COMFORT_STANDARDS), copy.deepcopy(pl.REGISTERED_BRANCHES), dict(SETPOINT_LINES),
             copy.deepcopy(MODULAR_COMFORT_MODES))
    assert not st.registered_comfort_standards()
    yield
    for number in list(st.registered_comfort_standards()):
        st.unregister_comfort_standard(number)
    assert (dict(st.COMFORT_STANDARDS), pl.REGISTERED_BRANCHES, dict(SETPOINT_LINES), MODULAR_COMFORT_MODES) == state


def _data(**changes):
    """The data of the YAML file of JPN Aqilah 2025, with some changes (None removes a key)."""
    with open(AQILAH, encoding='utf-8') as stream:
        data = yaml.safe_load(stream)
    for key, value in changes.items():
        if value is None:
            data.pop(key)
        else:
            data[key] = value
    return data


def _categories(*categories):
    """The categories 80 and 90 of the YAML files with the offsets of JPN Aqilah 2025, in the order given."""
    offsets = {80: 2.0, 90: 1.5}
    return {category: {'cooling_offset': offsets[category], 'heating_offset': -offsets[category]}
            for category in categories}


# The definitions and the YAML files ----------------------------------------------------------------------------------

def test_the_yaml_file_of_jpn_aqilah_2025():
    import accim.sim

    # Also in accim.sim
    assert accim.sim.load_comfort_standards is st.load_comfort_standards
    assert accim.sim.register_comfort_standard is st.register_comfort_standard
    assert accim.sim.ComfortStandardDefinition is st.ComfortStandardDefinition
    [definition] = st.load_comfort_standards(AQILAH, register=False)
    # Read only
    assert 101 not in st.COMFORT_STANDARDS and not st.registered_comfort_standards()
    standard = definition.standard
    assert (definition.number, standard.label, standard.title) == (101, 'JPN Aqilah2025 FR', AQILAH_TITLE)
    assert (definition.outdoor_metric, definition.alpha) == ('rmot_alpha', 0.8)
    [regime] = definition.regimes
    assert (regime.slope, regime.intercept, regime.condition) == (0.38, 16.9, 'always')
    assert (regime.cooling_lower_limit, regime.cooling_upper_limit, regime.heating_lower_limit,
            regime.heating_upper_limit) == (5.0, 30.0, 5.0, 30.0)
    assert (regime.cooling_offset, regime.heating_offset) == (0, 0)
    assert definition.category_offsets == {90: (1.5, -1.5), 80: (2.0, -2.0)}
    assert standard.categories == {90: '90 % comfort band', 80: '80 % comfort band'}
    assert list(standard.comfort_modes) == [0, 1, 2, 3]
    assert standard.comfort_modes[1] == ('JPN Aqilah2025 FR Model Adaptive setpoints when applicable, otherwise JPN '
                                         'Aqilah2025 FR Static setpoints')
    # Static setpoints of the author (decision D2): the paper gives none
    assert definition.static_setpoints == (20.0, 28.0)
    assert definition.evidence['N'] == 11566 and definition.evidence['within_band'] == {90: 0.66, 80: 0.79}
    assert 'doi:10.1016/j.enbuild.2025.115469' in definition.citation


def test_the_yaml_file_of_qatar():
    # Indraganti & Boussaa (2018), equation 5 and Table 10 (v03 of the proposals), and the choices of the author of
    # accim where the article gives no values (section 6.3 of v04 of the proposals, finding B3-1 of the review of 1.2.0)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        [definition] = st.load_comfort_standards(QATAR, register=False)
    standard = definition.standard
    assert (definition.number, standard.label) == (102, 'QAT Indraganti2018 HVAC')
    assert (definition.outdoor_metric, definition.alpha) == ('rmot_alpha', 0.8)
    [regime] = definition.regimes
    assert (regime.slope, regime.intercept) == (0.049, 22.5)
    assert (regime.cooling_lower_limit, regime.cooling_upper_limit, regime.heating_lower_limit,
            regime.heating_upper_limit) == (10.0, 40.0, 10.0, 40.0)
    assert definition.category_offsets == {90: (2.5, -2.5), 80: (3.5, -3.5)}
    assert list(standard.comfort_modes) == [0, 1, 2, 3] and definition.static_setpoints == (20.0, 25.5)
    evidence = definition.evidence
    assert {key: evidence[key] for key in ('N', 'R2', 'SE', 'p', 'Tr_mean', 'Tr_sd', 'mode', 'bands')} == {
        'N': 3742, 'R2': 0.015, 'SE': 0.007, 'p': '<0.001', 'Tr_mean': 30.7, 'Tr_sd': 6.4, 'mode': 'HVAC',
        'bands': 'ASHRAE 55, not own'}
    # The folder of the samples loads whole: JPN Aqilah 2025 and Qatar
    assert [d.number for d in st.load_comfort_standards(SAMPLES)] == [101, 102]
    assert sorted(st.registered_comfort_standards()) == [101, 102]
    # Its setpoints, without EnergyPlus: the comfort temperature, almost flat, with the band of 80 %
    result = compute_setpoints(EPW, 102, 80, 3, start_date='01/07')
    inside = (result['Tout_metric'] >= 10) & (result['Tout_metric'] <= 40)
    np.testing.assert_allclose(result.loc[inside, 'ComfTemp'], 0.049 * result.loc[inside, 'Tout_metric'] + 22.5,
                               rtol=0, atol=1e-9)
    np.testing.assert_allclose(result.loc[inside, 'ACSTnoTol'], result.loc[inside, 'ComfTemp'] + 3.5, rtol=0,
                               atol=1e-9)
    # Below 10 °C (in December), comfort mode 3 extends the setpoints of the limit horizontally
    below = result['Tout_metric'] < 10
    assert inside.mean() > 0.8 and below.any() and (inside | below).all()
    np.testing.assert_allclose(result.loc[below, 'ACSTnoTol'], 0.049 * 10 + 22.5 + 3.5, rtol=0, atol=1e-9)


def test_a_warning_for_the_signs_of_the_offsets():
    # Finding B3-3 of the review of 1.2.0: the setpoints are the comfort temperature plus the offsets
    for categories in ({80: {'cooling_offset': -0.5, 'heating_offset': -2.0}},
                       {80: {'cooling_offset': 2.0, 'heating_offset': 0.5}}):
        with pytest.warns(UserWarning, match=r'The offsets \(cooling_offset, heating_offset\) of the categories '
                                             r'\{80: .*\} of the comfort standard 101 have the sign that is not usual'):
            st.definition_from_mapping(_data(categories=categories))
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        st.definition_from_mapping(_data(categories={80: {'cooling_offset': 0, 'heating_offset': 0}}))


def test_the_how_to_notebook_has_the_yaml_files_of_the_samples():
    folder = REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'comfort_standards_registry'
    for path in (AQILAH, QATAR):
        assert (folder / path.name).read_bytes() == path.read_bytes(), path.name


@pytest.mark.parametrize('changes, message', [
    (dict(colour='red'), "unknown keys ['colour']"),
    (dict(evidence=None), "the keys ['evidence'] are missing or empty"),
    (dict(evidence={}), 'The comfort standard 101 must have its evidence: the statistics of the comfort model'),
    (dict(evidence='R2 0.67'), 'evidence must be a mapping with the statistics of the comfort model'),
    (dict(number=23), 'number must be an integer of 100 or more (decision D1), not 23.'),
    (dict(number=True), 'number must be an integer of 100 or more'),
    (dict(number=101.5), 'number must be an integer of 100 or more'),
    (dict(label='JPN [Aqilah]'), 'cannot be empty, nor have the characters'),
    (dict(citation=' '), "citation must be a text, not ' '."),
    (dict(comfort_temperature={'slope': '0.38', 'intercept': 16.9}),
     "comfort_temperature must be a mapping with the numbers ['slope', 'intercept']"),
    (dict(comfort_temperature={'slope': 0.38}), "comfort_temperature must be a mapping with the numbers"),
    (dict(applicability={'metric_min': 30, 'metric_max': 5}),
     'applicability: metric_min (30) must be lower than metric_max (5).'),
    (dict(categories={80: {'cooling_offset': 2}}),
     'the category 80 must have the numbers cooling_offset and heating_offset'),
    (dict(categories={80: {'cooling_offset': 2, 'heating_offset': -2, 'colour': 'red'}}),
     'the category 80 must have the numbers cooling_offset and heating_offset'),
    (dict(categories=[80, 90]), 'categories must be a mapping'),
    (dict(comfort_modes=[4]), 'comfort_modes must be a list of some of [0, 1, 2, 3]'),
    (dict(comfort_modes=[1, 1]), 'comfort_modes must be a list of some of [0, 1, 2, 3]'),
    (dict(static_setpoints=None), 'The comfort modes 0 and 1 of the comfort standard 101 need its static setpoints'),
    (dict(static_setpoints={'heating': 28, 'cooling': 20}), 'with the heating setpoint lower, not (28, 20).'),
    (dict(categories={85: {'cooling_offset': 2, 'heating_offset': -2}}, comfort_modes=[2]),
     'The comfort mode 2 of the comfort standard 101 uses the static setpoints of ISO 7730 that accim has for the '
     'categories [80, 90] only, not for [85].'),
    (dict(outdoor_metric='weekly_mean'), 'The outdoor metric of the comfort standard 101: custom_outdoor_metric must '
                                         'be one of'),
    (dict(alpha=1.5), 'The outdoor metric of the comfort standard 101: custom_alpha must be a number between 0 and 1'),
])
def test_the_data_of_a_comfort_standard_are_checked(changes, message):
    with pytest.raises(ValueError) as error:
        st.definition_from_mapping(_data(**changes), 'aqilah.yaml')
    # The message names the file
    assert str(error.value).startswith('aqilah.yaml: ') and message in str(error.value)


def test_the_definitions_are_checked():
    definition = st.definition_from_mapping(_data())
    with pytest.raises(ValueError, match='a comfort standard must be a mapping with the keys'):
        st.definition_from_mapping([_data()])
    # Several regimes, or a regime with a condition, are not available yet (notes/questions.md)
    regime = definition.regimes[0]
    for regimes in ((regime, regime), (dataclasses.replace(regime, condition='cooling_season'),)):
        with pytest.raises(ValueError, match=r"must have one regime \(a CustomRegime\), with the condition 'always'"):
            dataclasses.replace(definition, regimes=regimes)
    with pytest.raises(ValueError, match=r'must have the offsets of each one of its categories \(\[80, 90\]\), not '
                                         r'those of \[80\]'):
        dataclasses.replace(definition, category_offsets={80: (2.0, -2.0)})
    with pytest.raises(ValueError, match='must have the citation of its source'):
        dataclasses.replace(definition, citation='')
    with pytest.raises(ValueError, match='standard must be a ComfortStandard'):
        dataclasses.replace(definition, standard=101)
    # The asymmetric offsets of the categories, and the alpha and days of the outdoor metric
    other = st.definition_from_mapping(_data(categories={80: {'cooling_offset': 2.5, 'heating_offset': -1.0}},
                                             outdoor_metric='ndrm', days=7))
    assert other.category_offsets == {80: (2.5, -1.0)} and (other.outdoor_metric, other.days) == ('ndrm', 7)


def test_the_yaml_files_are_checked(tmp_path):
    wrong = tmp_path / 'wrong.yaml'
    wrong.write_text('number: [101\n', encoding='utf-8')
    with pytest.raises(ValueError, match='wrong.yaml: it is not a valid YAML file'):
        st.load_comfort_standards(wrong)
    with pytest.raises(ValueError, match='is not a file or a folder'):
        st.load_comfort_standards(tmp_path / 'missing.yaml')
    (tmp_path / 'empty').mkdir()
    with pytest.raises(ValueError, match='has no YAML files'):
        st.load_comfort_standards(tmp_path / 'empty')
    # A file with a list of comfort standards
    both = tmp_path / 'both.yml'
    both.write_text(yaml.safe_dump([_data(), _data(number=102, label='JPN Other', title='102 = Other')]),
                    encoding='utf-8')
    assert [d.number for d in st.load_comfort_standards(both)] == [101, 102]
    assert sorted(st.registered_comfort_standards()) == [101, 102]
    with pytest.raises(ValueError, match='The comfort standard 101 is registered already: give replace=True'):
        st.load_comfort_standards(both)
    assert [d.number for d in st.load_comfort_standards(both, replace=True)] == [101, 102]
    # The same number in two files of a folder
    (tmp_path / 'twice').mkdir()
    for name in ('a', 'b'):
        (tmp_path / 'twice' / f'{name}.yaml').write_text(
            yaml.safe_dump(_data(number=103, label=f'Label {name}', title='103 = Twice')), encoding='utf-8')
    with pytest.raises(ValueError, match=r'The comfort standards \[103\] are defined more than once'):
        st.load_comfort_standards(tmp_path / 'twice')
    assert 103 not in st.COMFORT_STANDARDS


def test_pyyaml_is_a_dependency(monkeypatch):
    import ast
    import builtins

    install_requires = None
    for node in ast.walk(ast.parse((REPO / 'setup.py').read_text(encoding='utf-8'))):
        if isinstance(node, ast.keyword) and node.arg == 'install_requires':
            install_requires = ast.literal_eval(node.value)
    assert 'pyyaml' in install_requires
    # Without it, load_comfort_standards says how to install it
    real_import = builtins.__import__

    def without_yaml(name, *args, **kwargs):
        if name == 'yaml':
            raise ImportError('No module named yaml')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', without_yaml)
    with pytest.raises(ImportError, match='load_comfort_standards needs PyYAML: pip install pyyaml'):
        st.load_comfort_standards(AQILAH)


def test_register_and_unregister_a_comfort_standard():
    definition = st.definition_from_mapping(_data())
    st.register_comfort_standard(definition)
    assert st.COMFORT_STANDARDS[101] is definition.standard and st.get_comfort_standard(101) is definition.standard
    assert list(st.COMFORT_STANDARDS)[-2:] == [99, 101]
    assert st.comfort_standard_definition(101) is definition and st.comfort_standard_definition('101') is definition
    assert st.comfort_standard_definition(1) is None and st.comfort_standard_definition('x') is None
    assert st.registered_comfort_standards() == {101: definition}
    assert set(pl.REGISTERED_BRANCHES[101]) == {'SetComfTemp', 'SetAppLimits', 'ApplyCAT', 'CountHours', 'SetVST'}
    assert MODULAR_COMFORT_MODES[101] == [0, 1, 2, 3]
    assert all(SETPOINT_LINES[(101, mode)] == lines for mode, lines in sdl.setpoint_lines(definition).items())
    with pytest.raises(ValueError, match='The comfort standard 101 is registered already: give replace=True'):
        st.register_comfort_standard(definition)
    # Another definition with the same number replaces it, and its EMS code
    other = st.definition_from_mapping(_data(comfort_modes=[3], static_setpoints=None))
    st.register_comfort_standard(other, replace=True)
    assert st.comfort_standard_definition(101) is other and MODULAR_COMFORT_MODES[101] == [3]
    assert (101, 0) not in SETPOINT_LINES and (101, 3) in SETPOINT_LINES
    # The numbers lower than 100 are those of the built-in comfort standards; the labels name the output IDFs
    built_in = dataclasses.replace(definition, standard=dataclasses.replace(definition.standard, number=23))
    with pytest.raises(ValueError, match='have the numbers 100 or more'):
        st.register_comfort_standard(built_in)
    for label, number in (('jpn aqilah2025 fr', 101), ('JPN Rijal', 3)):
        same = st.definition_from_mapping(_data(number=102, label=label, title='102 = Same'))
        with pytest.raises(ValueError, match=f"The label '{label}' is that of the comfort standard {number}"):
            st.register_comfort_standard(same)
    with pytest.raises(ValueError, match='definition must be a ComfortStandardDefinition'):
        st.register_comfort_standard(definition.standard)
    st.unregister_comfort_standard(101)
    assert 101 not in st.COMFORT_STANDARDS and 101 not in pl.REGISTERED_BRANCHES and 101 not in MODULAR_COMFORT_MODES
    with pytest.raises(ValueError, match=r'101 is not a comfort standard of the registry \(\[\]\)'):
        st.unregister_comfort_standard(101)
    with pytest.raises(ValueError, match='1 is not a comfort standard of the registry'):
        st.unregister_comfort_standard(1)
    with pytest.raises(ValueError, match='101 is not a valid ComfStand'):
        st.get_comfort_standard(101)


# The EMS code ---------------------------------------------------------------------------------------------------------

def test_the_erl_lines_of_a_comfort_standard():
    definition = st.definition_from_mapping(_data())
    branches = sdl.standard_branches(definition)
    assert branches['SetComfTemp'] == ('elseif ComfStand == 101', 'set ComfTemp = Tout_metric*0.38+16.9')
    assert branches['SetAppLimits'] == ('elseif ComfStand == 101', 'set ACSTaul = 30', 'set ACSTall = 5',
                                        'set AHSTaul = 30', 'set AHSTall = 5')
    # In the numeric order of the categories (finding B3-2 of the review of 1.2.0), not that of the YAML file (90, 80)
    assert branches['ApplyCAT'] == ('elseif ComfStand == 101', 'if (CAT == 80)', 'set ACSToffset = 2+CATcoolOffset',
                                    'set AHSToffset = -2+CATheatOffset', 'elseif (CAT == 90)',
                                    'set ACSToffset = 1.5+CATcoolOffset', 'set AHSToffset = -1.5+CATheatOffset',
                                    'endif')
    # As those of JPN Aqilah 2025 built in (23), whose definition has them in that order
    assert branches['ApplyCAT'][1:] == pl.BUILT_IN_BRANCHES[23]['ApplyCAT'][1:]
    assert [line for line in sdl.setpoint_lines(definition)[2] if line.startswith('elseif CAT==')] == [
        'elseif CAT==80', 'elseif CAT==90'] * 2
    # Its outdoor metric is not PMOT, so CountHours and SetVST compare its metric with its limits
    assert branches['CountHours'] == ('elseif ComfStand == 101', *pl._count_hours_body('Tout_metric').split('\n'))
    assert branches['SetVST'] == ('elseif ComfStand == 101', 'if (Tout_metric >= AHSTall) && (Tout_metric <= ACSTaul)',
                                  'set VST = ComfTemp+VSToffset', 'else',
                                  'set VST = (roundedACST+roundedAHST)/2+VSToffset', 'endif')
    lines = sdl.setpoint_lines(definition)
    assert lines[0] == ('set ACST = 28+ACSTtol', 'set AHST = 20+AHSTtol')
    assert lines[1][:6] == ('if (Tout_metric >= ACSTall) && (Tout_metric <= ACSTaul)',
                            'set ACST = Tout_metric*0.38+16.9+ACSToffset+ACSTtol', 'elseif Tout_metric < ACSTall',
                            'set ACST = 28+ACSTtol', 'elseif Tout_metric > ACSTaul', 'set ACST = 28+ACSTtol')
    assert 'set AHST = 20+AHSTtol' in lines[1]
    assert 'set AHST = AHSTaul*0.38+16.9+AHSToffset+AHSTtol' in lines[3]
    # Comfort modes 2 and 3 are those of the built-in comfort standards with the same comfort temperature: ASHRAE 55
    # (with the static setpoints of ISO 7730 of the categories 80 and 90) and JPN Rijal
    ashrae = st.definition_from_mapping(_data(outdoor_metric='pmot', categories=_categories(80, 90),
                                              comfort_temperature={'slope': 0.31, 'intercept': 17.8}))
    assert sdl.setpoint_lines(ashrae)[2] == SETPOINT_LINES[(2, 2)]
    rijal = st.definition_from_mapping(_data(outdoor_metric='pmot', comfort_temperature={'slope': 0.48,
                                                                                         'intercept': 14.4}))
    assert sdl.setpoint_lines(rijal)[3] == SETPOINT_LINES[(3, 3)]
    # PMOT and RMOT are those of EnergyPlus: no CountHours nor SetVST, and no EMS code of the outdoor metric
    negative = st.definition_from_mapping(_data(outdoor_metric='pmot', comfort_temperature={'slope': -0.2,
                                                                                            'intercept': 30}))
    branches = sdl.standard_branches(negative)
    # Erl takes no minus sign after a multiplication sign (EnergyPlus stops), so the intercept goes first
    assert branches['SetComfTemp'][1] == 'set ComfTemp = 30-PMOT*0.2'
    assert 'set ACST = 30-ACSTall*0.2+ACSToffset+ACSTtol' in sdl.setpoint_lines(negative)[3]
    assert 'CountHours' not in branches and 'SetVST' not in branches
    assert not sdl.needs_outdoor_metric_code(negative)
    assert sdl.standard_inputs(negative) == {'CustAST_metric': 0, 'CustAST_alpha': 0.8, 'CustAST_days': 30}
    rmot = st.definition_from_mapping(_data(outdoor_metric='rmot', comfort_temperature={'slope': 0.5,
                                                                                        'intercept': -3.5}))
    assert sdl.standard_branches(rmot)['SetComfTemp'][1] == 'set ComfTemp = RMOT*0.5-3.5'
    # Both negative, in the Erl interpreter of accim
    both = st.definition_from_mapping(_data(outdoor_metric='rmot', comfort_temperature={'slope': -0.2,
                                                                                        'intercept': -3.5}))
    line = sdl.standard_branches(both)['SetComfTemp'][1]
    assert line == 'set ComfTemp = -3.5-RMOT*0.2'
    erl = ErlProgramSet({'P': [line]}, global_variables=['ComfTemp', 'RMOT'])
    erl.set('RMOT', 10)
    erl.run('P')
    assert erl.get('ComfTemp') == pytest.approx(-5.5, abs=1e-12)
    assert sdl.standard_inputs(definition) == {'CustAST_metric': 2, 'CustAST_alpha': 0.8, 'CustAST_days': 30}
    assert [sdl.metric_variable(name) for name in ('pmot', 'rmot', 'ndrm')] == ['PMOT', 'RMOT', 'Tout_metric']


def test_the_chains_of_the_built_in_comfort_standards_do_not_change():
    literal = {'SetComfTemp': pl.SET_COMF_TEMP, 'SetAppLimits': pl.SET_APP_LIMITS, 'ApplyCAT': pl.APPLY_CAT,
               'CountHours': pl.COUNT_HOURS, 'SetVST': pl.SET_VST}
    functions = {'SetComfTemp': pl.set_comf_temp_lines, 'SetAppLimits': pl.set_app_limits_lines,
                 'ApplyCAT': pl.apply_cat_lines, 'CountHours': pl.count_hours_lines, 'SetVST': pl.set_vst_lines}
    # The comfort standards of the literal chains (those of accim 1.1.0), and the branches of JPN Aqilah 2025 (23,
    # built in), at the end of the chains
    others = list(range(23)) + [99]
    aqilah = pl.BUILT_IN_BRANCHES[23]
    assert pl.set_comf_temp_lines() == pl.SET_COMF_TEMP[:-1] + aqilah['SetComfTemp'] + ('endif',)
    assert pl.set_comf_temp_lines(True) == pl.SET_COMF_TEMP_OUTDOOR_METRIC[:-1] + aqilah['SetComfTemp'] + ('endif',)
    for name in ('SetComfTemp', 'SetAppLimits', 'ApplyCAT', 'CountHours'):
        lines = functions[name]()
        assert pl.for_comfort_standards(lines, others) == pl.for_comfort_standards(literal[name], others), name
        assert pl.for_comfort_standards(lines, [23]) == ['if ComfStand == 23', *aqilah[name][1:], 'endif'], name
    assert len(pl.set_vst_lines()) == len(pl.SET_VST) + len(aqilah['SetVST'])
    built_in = [(1, 2, 3), (2, 80, 2), (3, 90, 1), (13, 80, 1.3), (22, 2, 0), (23, 80, 1)]
    codes = [get_setpoint_ems_code(*arguments) for arguments in built_in]
    [definition] = st.load_comfort_standards(AQILAH)
    branches = sdl.standard_branches(definition)
    # The branches of the registry are added at the end of the chains (before their branch else, if they have one),
    # after those of the built-in comfort standards defined by their data
    assert pl.set_comf_temp_lines() == (pl.SET_COMF_TEMP[:-1] + aqilah['SetComfTemp'] + branches['SetComfTemp']
                                        + ('endif',))
    assert pl.apply_cat_lines() == pl.APPLY_CAT[:-1] + aqilah['ApplyCAT'] + branches['ApplyCAT'] + ('endif',)
    for name in ('SetComfTemp', 'SetAppLimits', 'ApplyCAT', 'CountHours'):
        lines = functions[name]()
        assert pl.for_comfort_standards(lines, others) == pl.for_comfort_standards(literal[name], others), name
        assert pl.for_comfort_standards(lines, [23]) == ['if ComfStand == 23', *aqilah[name][1:], 'endif'], name
        assert pl.for_comfort_standards(lines, [101]) == ['if ComfStand == 101', *branches[name][1:], 'endif'], name
    # SetVST: before the branch of the comfort standards that compare PMOT with their limits
    lines = pl.set_vst_lines()
    assert len(lines) == len(pl.SET_VST) + len(aqilah['SetVST']) + len(branches['SetVST'])
    assert pl.set_vst_lines(comfort_standards=[1]) == pl.SET_VST
    assert pl.registered_standards_in(lines) == {23, 101} and pl.registered_standards_in(pl.SET_VST) == set()
    assert [get_setpoint_ems_code(*arguments) for arguments in built_in] == codes


def test_the_ems_code_prints_the_evidence(capsys):
    st.load_comfort_standards(AQILAH)
    code = get_setpoint_ems_code(101, 80, 1)
    for line in (f'! Comfort standard (ComfStand): {AQILAH_TITLE}', '! Category (CAT): 80 = 80 % comfort band',
                 '! Comfort mode (ComfMod): 1 = JPN Aqilah2025 FR Model Adaptive setpoints when applicable, otherwise '
                 'JPN Aqilah2025 FR Static setpoints',
                 '! Comfort standard defined by its data (accim.sim.standards): Aqilah, Rijal, Yoshida & Nicol (2025) '
                 'Energy & Buildings 335, 115469, doi:10.1016/j.enbuild.2025.115469',
                 '! Outdoor metric: rmot_alpha (alpha 0.8), in the EMS Tout_metric',
                 '! Static setpoints: 20.0 for heating and 28.0 for cooling', '! Evidence:', '!     N: 11566',
                 '!     R2: 0.67', '!     p: <0.001', '!     within_band: {90: 0.66, 80: 0.79}',
                 '!     comfort_temperature_range: [14.5, 30.0]'):
        assert line in code.split('\n'), line
    programs = get_setpoint_ems_programs(101, 80, 1)
    assert programs['SetComfTemp'] == ['if ComfStand == 101', 'set ComfTemp = Tout_metric*0.38+16.9', 'endif']
    # The programs of the outdoor metric, which the EMS calculates
    assert {'InitOutdoorMetric', 'SetOutdoorMetric', 'SetOutdoorMetric_<zone>'} <= set(programs)
    print_setpoint_ems_code(101, 80, 1)
    assert capsys.readouterr().out.strip() == code.strip()
    # The built-in comfort standards print no evidence
    assert '! Evidence:' not in get_setpoint_ems_code(3, 80, 1)


# The setpoints (the Erl interpreter of accim) ------------------------------------------------------------------------

def test_compute_setpoints_of_a_comfort_standard():
    st.load_comfort_standards(AQILAH)
    result = compute_setpoints(EPW, 101, 80, 3, frequency='timestep', start_date='01/04')
    metric = result['Tout_metric']
    np.testing.assert_allclose(result['ComfTemp'], 0.38 * metric + 16.9, rtol=0, atol=1e-9)
    np.testing.assert_allclose(result['ACSTnoTol'], result['ComfTemp'] + 2.0, rtol=0, atol=1e-9)
    np.testing.assert_allclose(result['AHSTnoTol'], result['ComfTemp'] - 2.0, rtol=0, atol=1e-9)
    assert (result['applicable'] == 1).all()
    narrow = compute_setpoints(EPW, 101, 90, 3, frequency='timestep', start_date='01/04')
    np.testing.assert_allclose(narrow['ACSTnoTol'], narrow['ComfTemp'] + 1.5, rtol=0, atol=1e-9)


@pytest.mark.parametrize('comfort_mode', [0, 1, 2, 3])
def test_the_comfort_modes_out_of_the_applicability_limits(comfort_mode):
    # The outdoor metric of Seville goes below 15 °C in winter and above 25 °C in summer
    st.register_comfort_standard(st.definition_from_mapping(_data(applicability={'metric_min': 15.0,
                                                                                 'metric_max': 25.0})))
    result = compute_setpoints(EPW, 101, 80, comfort_mode, frequency='timestep')
    metric = result['Tout_metric'].to_numpy()
    below, above = metric < 15, metric > 25
    within = ~below & ~above
    assert below.any() and above.any() and within.any()
    np.testing.assert_array_equal(result['applicable'], within.astype(int))
    adaptive = 0.38 * metric + 16.9
    outside = {0: ((28, 20), (28, 20)), 1: ((28, 20), (28, 20)), 2: ((25, 19), (27, 22)),
               3: ((0.38 * 15 + 18.9, 0.38 * 15 + 14.9), (0.38 * 25 + 18.9, 0.38 * 25 + 14.9))}[comfort_mode]
    for column, index, offset in (('ACSTnoTol', 0, 2.0), ('AHSTnoTol', 1, -2.0)):
        expected = np.select([below, above], [outside[0][index], outside[1][index]], adaptive + offset)
        if comfort_mode == 0:
            expected = np.full(len(metric), outside[0][index], dtype=float)
        np.testing.assert_allclose(result[column], expected, rtol=0, atol=1e-9)


def test_compute_setpoints_with_pmot_and_a_negative_slope():
    st.register_comfort_standard(st.definition_from_mapping(_data(
        outdoor_metric='pmot', comfort_temperature={'slope': -0.2, 'intercept': 30}, comfort_modes=[3],
        static_setpoints=None)))
    result = compute_setpoints(EPW, 101, 80, 3, frequency='timestep', start_date='01/04')
    # The metric of the setpoints is PMOT, that of EnergyPlus
    assert result.attrs['metric'] == 'PMOT' and (result['Tout_metric'] == result['PMOT']).all()
    # The PMOT that the EMS reads: that of the previous day at the first timestep of each day
    pmot = result['PMOT'].to_numpy()
    first = np.arange(len(result)) % (24 * STEPS) == 0
    read = np.where(first, np.r_[0.0, pmot[:-1]], pmot)
    np.testing.assert_allclose(result['ComfTemp'].to_numpy()[1:], -0.2 * read[1:] + 30, rtol=0, atol=1e-9)


# AddAccis, modify_accis and the parametric module --------------------------------------------------------------------

def _add_accis(folder, monkeypatch, **arguments):
    from accim.sim.accis import AddAccis

    folder.mkdir(exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    values = dict(script_type='vrf_mm', supply_air_temp_input_method='temperature difference', output_type='standard',
                  output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                  setpoint_type='temperature', comfort_standard=[1], category=[1], comfort_mode=[1, 3],
                  hvac_mode=[2], ventilation_control=[0], confirm=True, verbose=False)
    values.update(arguments)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(**values)
    return {path.name: path for path in folder.glob('TestModel[[]*.idf')}


def _programs(idf):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
            for p in idf.idfobjects['EnergyManagementSystem:Program']}


@needs_idd
def test_add_accis_with_a_comfort_standard_of_the_registry(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.outdoor_metric import has_outdoor_metric_code

    reference = _add_accis(tmp_path / 'reference', monkeypatch)
    st.load_comfort_standards(AQILAH)
    written = _add_accis(tmp_path / 'registry', monkeypatch, comfort_standard=[1, 101], category=[1, 80],
                         epw=str(EPW))
    # The output IDFs of the built-in comfort standards are those without the registry
    assert len(reference) == 2 and set(reference) < set(written)
    for name, path in reference.items():
        assert filecmp.cmp(path, written[name], shallow=False), name
    names = sorted(name for name in written if name not in reference)
    assert [name.split('[')[1:4] for name in names] == [['CS_JPN Aqilah2025 FR', 'CA_80', 'CM_1'],
                                                        ['CS_JPN Aqilah2025 FR', 'CA_80', 'CM_3']]
    idf = load_idf(written[names[0]])
    programs = _programs(idf)
    assert programs['SetComfTemp'] == ['if ComfStand == 101', 'set ComfTemp = Tout_metric*0.38+16.9', 'endif']
    assert programs['SetAppLimits'][0] == 'if ComfStand == 101'
    assert programs['SetVST'].count('elseif ComfStand == 101') == 1
    assert sorted(name for name in programs if name.startswith('SetAST_CS')) == ['SetAST_CS101_0', 'SetAST_CS101_1']
    for zone in ZONES:
        assert programs[f'CountHours_{zone}'][0] == 'if ComfStand == 101'
        assert 'if (Tout_metric >= AHSTall) && (Tout_metric <= ACSTaul)' in programs[f'CountHours_{zone}']
    for program in input_programs(idf).values():
        inputs = read_inputs(program)
        assert (inputs['ComfStand'], inputs['CAT'], inputs['ComfMod']) == (101, 80, 1)
        assert (inputs['CustAST_metric'], inputs['CustAST_alpha']) == (2, 0.8)
    assert has_outdoor_metric_code(idf)


def _model(tmp_path, script_type='vrf_mm'):
    from accim.sim.accis import add_accis_to_idf, load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    idf = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type=script_type, supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    return idf


@needs_idd
def test_modify_accis_with_a_comfort_standard_of_the_registry(tmp_path):
    from accim.sim.accis import modify_accis
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.outdoor_metric import has_outdoor_metric_code

    # A model with the ACCIS of all the built-in comfort standards
    idf = _model(tmp_path)
    assert not has_outdoor_metric_code(idf)
    st.load_comfort_standards(AQILAH)
    modify_accis(idf, comfort_standard=101, category=90, comfort_mode=2, epw=str(EPW))
    for program in input_programs(idf).values():
        inputs = read_inputs(program)
        assert (inputs['ComfStand'], inputs['CAT'], inputs['ComfMod']) == (101, 90, 2)
        assert (inputs['CustAST_metric'], inputs['CustAST_alpha'], inputs['CustAST_days']) == (2, 0.8, 30)
    assert has_outdoor_metric_code(idf)
    programs = _programs(idf)
    assert 'set ComfTemp = Tout_metric*0.38+16.9' in programs['SetComfTemp']
    assert 'SetAST_CS101_0' in programs and 'SetAST_CS1_0' in programs
    # The zones that keep it keep its outdoor metric
    modify_accis(idf, setpoint_tolerance=0.2)
    assert all(read_inputs(program)['CustAST_metric'] == 2 for program in input_programs(idf).values())
    # A zone can have it while the other has a built-in comfort standard
    modify_accis(idf, zone_arguments={'Block1:Zone2': dict(comfort_standard=3, category=80, comfort_mode=1)})
    standards = {zone: read_inputs(program)['ComfStand'] for zone, program in input_programs(idf).items()}
    assert standards == {'Block1_Zone1': 101, 'Block1_Zone2': 3}


@needs_idd
def test_the_registry_does_not_change_the_models_of_the_built_in_comfort_standards(tmp_path, monkeypatch):
    from accim.sim.accis import modify_accis

    # The output IDFs of modify_accis with a built-in comfort standard are those without the registry
    models = []
    for name in ('without', 'with'):
        (tmp_path / name).mkdir()
        idf = _model(tmp_path / name)
        if name == 'with':
            st.load_comfort_standards(AQILAH)
        modify_accis(idf, comfort_standard=2, category=80, comfort_mode=2)
        idf.save()
        models.append(tmp_path / name / 'model.idf')
    assert filecmp.cmp(*models, shallow=False)


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')


def _output_idf(folder, monkeypatch, begin, end, frequency, script_type='vrf_mm', **arguments):
    """The output IDF of AddAccis of the sample model with JPN Aqilah 2025 (category 80, comfort mode 1, the outdoor
    metric beginning with the weather file), whose input IDF has the run period given."""
    from accim.sim.accis import AddAccis, load_idf

    folder.mkdir(parents=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    model = load_idf(folder / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    model.save()
    monkeypatch.chdir(folder)
    values = dict(script_type=script_type, supply_air_temp_input_method='temperature difference',
                  output_type='standard', output_frequencies=[frequency], keep_existing_outputs=False,
                  energyplus_version='auto', setpoint_type='temperature', comfort_standard=[101], category=[80],
                  comfort_mode=[1], hvac_mode=[2], ventilation_control=[0], epw=str(EPW), confirm=True,
                  verbose=False)
    values.update(arguments)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(**values)
    [path] = folder.glob('TestModel[[]*.idf')
    shutil.copy(path, folder / 'model.idf')
    return folder / 'model.idf'


def _run_energyplus(model, folder):
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    result = subprocess.run([str(energyplus), '-d', str(folder), '-p', 'run', '-s', 'C', '-r', '-x', '-w', str(EPW),
                             str(model)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    return pd.read_csv(folder / 'run.csv')


@needs_energyplus
def test_a_comfort_standard_of_the_registry_in_energyplus(tmp_path, monkeypatch, capsys):
    from accim.utils.verification import verify_accim_simulation

    st.load_comfort_standards(AQILAH)
    model = _output_idf(tmp_path / 'april', monkeypatch, (4, 1), (4, 7), 'timestep')
    results = _run_energyplus(model, tmp_path / 'april' / 'out')
    assert len(results) == 7 * 24 * STEPS
    # The setpoints and the outdoor metric are those of compute_setpoints (check 4)
    mismatches = verify_accim_simulation(str(tmp_path / 'april' / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0 or not mismatches['check'].str.match('Check4').any()
    for zone in ZONES:
        for check in ('Check4_Tout_metric', 'Check4_ACST', 'Check4_AHST', 'Check4_ComfTemp'):
            assert re.search(rf"'{zone}' {check} \(.*\): 0 mismatch\(es\) in 1008 timesteps", output), (zone, check)
    expected = compute_setpoints(EPW, 101, 80, 1, frequency='timestep', start_date='01/04')
    found = results['EMS:Adaptive Cooling Setpoint Temperature_Block1_Zone1 [C](TimeStep)'].to_numpy()
    np.testing.assert_allclose(found, expected['ACST'].to_numpy()[:len(found)], rtol=0, atol=1e-9)


@needs_energyplus
def test_the_ems_and_api_backends_give_the_same_results(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations

    st.load_comfort_standards(AQILAH)
    model = _output_idf(tmp_path / 'model', monkeypatch, (4, 1), (4, 10), 'hourly', category=[90], comfort_mode=[2])
    ems_results = _run_energyplus(model, tmp_path / 'ems')
    results = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    assert len(ems_results) == 10 * 24
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
