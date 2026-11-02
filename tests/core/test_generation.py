"""Tests for accim.sim.generation: the combinations of arguments of AddAccis and its output IDFs.

AddAccis writes one output IDF for each combination of comfort standard, category, comfort mode, HVAC mode,
ventilation control... Only the programs SetInputData_<zone> change between them, so IdfWriter renders the other
objects once and writes the files that eppy would save, byte for byte.
"""
import os
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

from accim.sim.generation import Combination, GenerationArguments, IdfWriter, OutputIdfs, combinations, output_name

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
IDD_25_1 = Path('C:/EnergyPlusV25-1-0/Energy+.idd')


def _air_conditioned(**kwargs):
    return GenerationArguments.air_conditioned(**kwargs)


def _key(c):
    return c.comfort_standard, c.category, c.comfort_mode, c.hvac_mode, c.ventilation_control


def test_only_the_categories_of_each_comfort_standard_give_output_idfs():
    args = _air_conditioned(comfort_standard=[1, 2], category=[1, 80], comfort_mode=[3])

    assert [_key(c) for c in combinations(args)] == [(1, 1, 3, 0, None), (2, 80, 3, 0, None)]


def test_comfort_standard_0_has_no_category_or_comfort_mode():
    args = _air_conditioned(comfort_standard=[0], category=[1, 2], comfort_mode=[0, 3])

    combos = list(combinations(args))

    assert [_key(c) for c in combos] == [(0, None, None, 0, None)]
    assert output_name('model', combos[0]) == 'model[CS_ESP CTE[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'


def test_combinations_without_setpoints_are_skipped_with_a_warning():
    # CHN GBT50785 Cold (4) only has setpoints for the comfort mode 3
    args = _air_conditioned(comfort_standard=[4], category=[1], comfort_mode=[0, 3])

    with pytest.warns(UserWarning, match=r'\(4, 0\)'):
        combos = list(combinations(args))

    assert [_key(c) for c in combos] == [(4, 1, 3, 0, None)]


def test_natural_ventilation_has_only_the_ventilation_controls_0_and_1():
    args = GenerationArguments(comfort_standard=[1], category=[3], comfort_mode=[3], hvac_mode=[0, 1, 2], ventilation_control=[0, 2])

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        keys = [_key(c) for c in combinations(args)]

    assert keys == [(1, 3, 3, 0, None), (1, 3, 3, 1, 0), (1, 3, 3, 2, 0), (1, 3, 3, 2, 2)]


def test_tolerances_and_ventilation_lists_multiply_the_output_idfs():
    args = GenerationArguments(comfort_standard=[1], category=[3], comfort_mode=[3], hvac_mode=[2], ventilation_control=[0],
                               ventilation_setpoint_offset=[0, 1], setpoint_tolerance_start=0.1, setpoint_tolerance_end=0.3, setpoint_tolerance_step=0.1)

    names = [output_name('m', c) for c in combinations(args)]

    assert names == [
        'm[CS_INT EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf',
        'm[CS_INT EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.2[NS_X.idf',
        'm[CS_INT EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.3[NS_X.idf',
        'm[CS_INT EN16798[CA_3[CM_3[HM_2[VC_0[VO_1.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf',
        'm[CS_INT EN16798[CA_3[CM_3[HM_2[VC_0[VO_1.0[MT_50.0[MW_50.0[AT_0.2[NS_X.idf',
        'm[CS_INT EN16798[CA_3[CM_3[HM_2[VC_0[VO_1.0[MT_50.0[MW_50.0[AT_0.3[NS_X.idf',
    ]


@pytest.mark.parametrize('start, end, step, expected', [
    (0.1, 0.1, 0.1, [0.1]),
    (0, 1, 0.25, [0, 0.25, 0.5, 0.75, 1]),
    # numpy.arange(0.1, 0.3 + 0.1, 0.1) gives 0.4 too, as accim 0.x did
    (0.1, 0.3, 0.1, [0.1, 0.2, 0.3]),
    (0.05, 0.05, 0.15, [0.05]),
])
def test_tolerances_include_the_last_one_and_no_more(start, end, step, expected):
    args = GenerationArguments(comfort_standard=[1], category=[3], comfort_mode=[3], setpoint_tolerance_start=start, setpoint_tolerance_end=end,
                               setpoint_tolerance_step=step)

    assert args.tolerances() == pytest.approx(expected)


def test_tolerance_steps_must_be_positive():
    args = GenerationArguments(comfort_standard=[1], category=[3], comfort_mode=[3], setpoint_tolerance_step=0)

    with pytest.raises(ValueError, match='setpoint_tolerance_step must be greater than 0'):
        args.tolerances()


def test_pmv_control_has_one_output_idf_and_the_name_suffix():
    args = _air_conditioned(comfort_standard=[1, 2], category=[3], comfort_mode=[3], name_suffix='office')

    combos = list(combinations(args, setpoint_type='pmv'))

    assert len(combos) == 1 and combos[0].is_pmv
    assert output_name('m', combos[0], args.name_suffix) == 'm[CS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_office.idf'


def test_generation_arguments_are_normalised():
    args = GenerationArguments(comfort_standard=1, category=3, comfort_mode=3, ventilation_setpoint_offset=1, cooling_season_start='01/05',
                               cooling_season_end=274, name_suffix=None)

    assert (args.comfort_standard, args.category, args.comfort_mode, args.ventilation_setpoint_offset) == ([1], [3], [3], [1.0])
    assert (args.cooling_season_start, args.cooling_season_end, args.name_suffix) == (121, 274, '')
    with pytest.raises(ValueError, match='cooling_season_end'):
        GenerationArguments(comfort_standard=[1], category=[3], comfort_mode=[3], cooling_season_end='31/02')


class _CountingIDF:
    """An IDF class that counts the files it reads."""
    read = []

    def __init__(self, path):
        _CountingIDF.read.append(path)
        self.path = path


def test_output_idfs_are_read_when_they_are_used(monkeypatch):
    monkeypatch.setattr(_CountingIDF, 'read', [])
    idfs = OutputIdfs({'a.idf': '/x/a.idf', 'b.idf': '/x/b.idf'}, _CountingIDF)

    assert (len(idfs), list(idfs), idfs.paths['b.idf']) == (2, ['a.idf', 'b.idf'], '/x/b.idf')
    assert _CountingIDF.read == []
    assert idfs['a.idf'].path == '/x/a.idf'
    assert idfs['a.idf'] is idfs['a.idf']
    assert _CountingIDF.read == ['/x/a.idf']


@pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                    reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
def test_idf_writer_writes_the_files_of_eppy(tmp_path):
    from accim.sim.accis import add_accis_to_idf, load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    idf = load_idf(tmp_path / 'model.idf', 'auto')
    add_accis_to_idf(idf, script_type='vrf_mm', supply_air_temp_input_method='temperature difference',
                     output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                     setpoint_type='temperature', verbose=False)
    args = GenerationArguments(comfort_standard=[1, 99], category=[3], comfort_mode=[3], hvac_mode=[0, 2], ventilation_control=[0],
                               custom_slope=0.31, custom_intercept=17.8)
    writer = IdfWriter(idf, args)
    combos = list(combinations(args))
    assert len(combos) == 4

    for n, combination in enumerate(combos):
        writer.write(tmp_path / f'writer_{n}.idf', combination)
        # The programs of the combination are those of the model, so eppy saves the same file
        idf.saveas(str(tmp_path / f'eppy_{n}.idf'))
        assert (tmp_path / f'writer_{n}.idf').read_bytes() == (tmp_path / f'eppy_{n}.idf').read_bytes()

    programs = {p.Name: p for p in idf.idfobjects['EnergyManagementSystem:Program']}
    for zone in ['Block1_Zone1', 'Block1_Zone2']:
        lines = list(programs[f'SetInputData_{zone}'].obj[2:])
        assert lines[0] == 'set ComfStand = 99'
        assert {'set m = 0.31', 'set CATcoolOffset = 0', 'set MultiplierVOF = 0.25'} <= set(lines)
    assert list(programs['SetAST'].obj[2:]) == ['run SetAST_Master']


@pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                    reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
def test_the_model_does_not_depend_on_the_hash_seed(tmp_path):
    # accim 0.x took the zones from a set, so their order, and that of the objects of each zone, changed from one
    # Python process to another (the hashes of strings)
    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    script = (
        'import sys\n'
        'from accim.sim.accis import add_accis_to_idf, load_idf\n'
        'idf = load_idf(sys.argv[1], "auto")\n'
        'add_accis_to_idf(idf, script_type="vrf_mm", supply_air_temp_input_method="temperature difference",\n'
        '                 output_type="standard", output_frequencies=["hourly"], keep_existing_outputs=False,\n'
        '                 setpoint_type="temperature", verbose=False)\n'
        'idf.saveas(sys.argv[2])\n'
    )
    for seed in ('1', '2'):
        subprocess.run([sys.executable, '-c', script, str(tmp_path / 'model.idf'), str(tmp_path / f'seed_{seed}.idf')],
                       check=True, cwd=REPO, env=dict(os.environ, PYTHONHASHSEED=seed), timeout=600)

    assert (tmp_path / 'seed_1.idf').read_bytes() == (tmp_path / 'seed_2.idf').read_bytes()


def test_combination_is_hashable_and_comparable():
    a = Combination(1, 3, 3, 0, None, None, None, None, 0.1)

    assert a == Combination(1, 3, 3, 0, None, None, None, None, 0.1)
    assert len({a, Combination(1, 3, 3, 0, None, None, None, None, 0.1)}) == 1
    assert not a.is_pmv
