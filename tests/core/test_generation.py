"""Tests for accim.sim.generation: the combinations of arguments of AddAccis and its output IDFs.

AddAccis writes one output IDF for each combination of comfort standard, category, comfort mode, HVAC mode,
ventilation control... Only a few EMS programs change between them, so IdfWriter renders the other objects
once and writes the files that eppy would save, byte for byte.
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
    return c.comf_stand, c.cat, c.comf_mod, c.hvac_mode, c.vent_ctrl


def test_only_the_categories_of_each_comfort_standard_give_output_idfs():
    args = _air_conditioned(comf_stand=[1, 2], cat=[1, 80], comf_mod=[3])

    assert [_key(c) for c in combinations(args)] == [(1, 1, 3, 0, None), (2, 80, 3, 0, None)]


def test_comfort_standard_0_has_no_category_or_comfort_mode():
    args = _air_conditioned(comf_stand=[0], cat=[1, 2], comf_mod=[0, 3])

    combos = list(combinations(args))

    assert [_key(c) for c in combos] == [(0, None, None, 0, None)]
    assert output_name('model', combos[0]) == 'model[CS_ESP CTE[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'


def test_combinations_without_setpoints_are_skipped_with_a_warning():
    # CHN GBT50785 Cold (4) only has setpoints for the comfort mode 3
    args = _air_conditioned(comf_stand=[4], cat=[1], comf_mod=[0, 3])

    with pytest.warns(UserWarning, match=r'\(4, 0\)'):
        combos = list(combinations(args))

    assert [_key(c) for c in combos] == [(4, 1, 3, 0, None)]


def test_natural_ventilation_has_only_the_ventilation_controls_0_and_1():
    args = GenerationArguments(comf_stand=[1], cat=[3], comf_mod=[3], hvac_mode=[0, 1, 2], vent_ctrl=[0, 2])

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        keys = [_key(c) for c in combinations(args)]

    assert keys == [(1, 3, 3, 0, None), (1, 3, 3, 1, 0), (1, 3, 3, 2, 0), (1, 3, 3, 2, 2)]


def test_tolerances_and_ventilation_lists_multiply_the_output_idfs():
    args = GenerationArguments(comf_stand=[1], cat=[3], comf_mod=[3], hvac_mode=[2], vent_ctrl=[0],
                               vst_offset=[0, 1], ast_tol_start=0.1, ast_tol_end_input=0.3, ast_tol_steps=0.1)

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
    args = GenerationArguments(comf_stand=[1], cat=[3], comf_mod=[3], ast_tol_start=start, ast_tol_end_input=end,
                               ast_tol_steps=step)

    assert args.tolerances() == pytest.approx(expected)


def test_tolerance_steps_must_be_positive():
    args = GenerationArguments(comf_stand=[1], cat=[3], comf_mod=[3], ast_tol_steps=0)

    with pytest.raises(ValueError, match='ast_tol_steps must be greater than 0'):
        args.tolerances()


def test_pmv_control_has_one_output_idf_and_the_name_suffix():
    args = _air_conditioned(comf_stand=[1, 2], cat=[3], comf_mod=[3], name_suffix='office')

    combos = list(combinations(args, temp_ctrl='pmv'))

    assert len(combos) == 1 and combos[0].is_pmv
    assert output_name('m', combos[0], args.name_suffix) == 'm[CS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_office.idf'


def test_generation_arguments_are_normalised():
    args = GenerationArguments(comf_stand=1, cat=3, comf_mod=3, vst_offset=1, cool_season_start='01/05',
                               cool_season_end=274, name_suffix=None)

    assert (args.comf_stand, args.cat, args.comf_mod, args.vst_offset) == ([1], [3], [3], [1.0])
    assert (args.cool_season_start, args.cool_season_end, args.name_suffix) == (121, 274, '')
    with pytest.raises(ValueError, match='cool_season_end'):
        GenerationArguments(comf_stand=[1], cat=[3], comf_mod=[3], cool_season_end='31/02')


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
                     output_type='standard', output_freqs=['hourly'], output_keep_existing=False,
                     temp_ctrl='temperature', verbose_mode=False)
    args = GenerationArguments(comf_stand=[1, 99], cat=[3], comf_mod=[3], hvac_mode=[0, 2], vent_ctrl=[0],
                               cust_ast_m=0.31, cust_ast_n=17.8)
    writer = IdfWriter(idf, args)
    combos = list(combinations(args))
    assert len(combos) == 4

    for n, combination in enumerate(combos):
        writer.write(tmp_path / f'writer_{n}.idf', combination)
        # The programs of the combination are those of the model, so eppy saves the same file
        idf.saveas(str(tmp_path / f'eppy_{n}.idf'))
        assert (tmp_path / f'writer_{n}.idf').read_bytes() == (tmp_path / f'eppy_{n}.idf').read_bytes()

    programs = {p.Name: p for p in idf.idfobjects['EnergyManagementSystem:Program']}
    assert programs['SetInputData'].Program_Line_1 == 'set ComfStand = 99'
    assert programs['SetAST'].Program_Line_2 == 'set m = 0.31'
    assert programs['ApplyCAT'].Program_Line_1 == 'set CATcoolOffset = 0'


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
        '                 output_type="standard", output_freqs=["hourly"], output_keep_existing=False,\n'
        '                 temp_ctrl="temperature", verbose_mode=False)\n'
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
