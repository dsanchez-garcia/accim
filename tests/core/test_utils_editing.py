"""Tests for accim.utils.editing: dates, accents, the version of the IDF files of DesignBuilder, the fields of
the objects and the settings that reduce the runtime.

Ported from the tests of accim.utils of the branch refactor/sim-v1 (tests/utils/test_utils_pure.py and
test_utils_idf.py). The messages of reduce_runtime and modify_timesteps are tested in
tests/parametric_and_optimisation/test_reduce_runtime_messages.py.

- amend_idf_version_from_dsb read and wrote the file as text in the encoding of the locale, so a file in UTF-8
  with some accented capitals (such as 'Á', whose second byte is not a character of Windows-1252) stopped it on
  Windows, a file in Windows-1252 with accents would stop it where the locale encoding is UTF-8 (the default
  from Python 3.15), and it wrote the line endings of the operating system. Now it only replaces the bytes of
  the version, as AddAccis does with the IDF files of DesignBuilder.
- get_available_fields(source='idf') raised a KeyError for an object type that the IDD does not have, instead
  of warning and returning an empty list, as with source='idd' and as its docstring says.
"""
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from accim.energyplus import default_energyplus_folder
from accim.utils import (amend_idf_version_from_dsb, get_available_fields, modify_timesteps, reduce_runtime,
                         remove_accents, remove_accents_in_idf, transform_ddmm_to_int)

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'

needs_energyplus_25_1 = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                                           reason='needs EnergyPlus 25.1 and the sample IDF of the repository')


@pytest.fixture
def building(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    return get_building(str(tmp_path / 'model.idf'))


@pytest.mark.parametrize('ddmm, day', [('01/01', 1), ('15/02', 46), ('1/3', 60), ('31/12', 365)])
def test_transform_ddmm_to_int(ddmm, day):
    assert transform_ddmm_to_int(ddmm) == day


@pytest.mark.parametrize('text, expected', [
    ('Málaga', 'Malaga'),
    ('Sevilla', 'Sevilla'),
    ('Aragón', 'Aragon'),
    ('Crème brûlée', 'Creme brulee'),
    ('Ñandú', 'Nandu'),
])
def test_remove_accents(text, expected):
    assert remove_accents(text) == expected


def test_amend_idf_version_from_dsb(tmp_path):
    # The IDF files of DesignBuilder 7 have the version '9.4.0.002'
    path = tmp_path / 'model.idf'
    path.write_text('Version, 9.4.0.002;\nBuilding, X;\n', encoding='utf-8')

    amend_idf_version_from_dsb(str(path))

    content = path.read_text(encoding='utf-8')
    assert 'Version, 9.4;' in content
    assert '9.4.0.002' not in content


@pytest.mark.parametrize('encoding', ['utf-8', 'cp1252'])
def test_amend_idf_version_from_dsb_only_changes_the_version(tmp_path, encoding):
    text = '! \u00c1lava: sal\u00f3n, almac\u00e9n y ba\u00f1o\nVersion, 9.4.0.002;\nZone, Sal\u00f3n;\n'
    path = tmp_path / 'model.idf'
    path.write_bytes(text.encode(encoding))

    amend_idf_version_from_dsb(str(path))

    assert path.read_bytes() == text.replace('9.4.0.002', '9.4').encode(encoding)


def test_remove_accents_in_idf(tmp_path):
    path = tmp_path / 'model.idf'
    path.write_text('Zone, Sal\u00f3n;\nZone, Almac\u00e9n;\n', encoding='utf-8')

    remove_accents_in_idf(str(path))

    assert path.read_text(encoding='utf-8') == 'Zone, Salon;\nZone, Almacen;\n'


@needs_energyplus_25_1
def test_get_available_fields_of_the_idd_and_of_the_objects_of_the_model(building):
    from_idd = get_available_fields(building, 'Zone', source='idd')
    from_idf = get_available_fields(building, 'zone', source='idf')

    assert from_idd[:3] == ['Name', 'Direction_of_Relative_North', 'X_Origin']
    assert set(from_idd) <= set(from_idf)
    assert get_available_fields(building, 'Output:Variable', separator=' ') == [
        'Key Value', 'Variable Name', 'Reporting Frequency', 'Schedule Name']
    # The colons are removed, as in the names of the fields in eppy
    assert 'Sunday_ScheduleDay_Name' in get_available_fields(building, 'Schedule:Week:Daily')


@needs_energyplus_25_1
@pytest.mark.parametrize('source', ['idd', 'idf'])
def test_get_available_fields_of_an_unknown_object_type(building, source):
    with pytest.warns(UserWarning, match="Object type 'Not:An:Object' not found in the loaded IDD"):
        assert get_available_fields(building, 'Not:An:Object', source=source) == []


@needs_energyplus_25_1
def test_get_available_fields_of_an_object_type_without_objects_in_the_model(building):
    # The IDD of EnergyPlus 25.1 has Space objects, but the sample model has none
    with pytest.warns(UserWarning, match="No instances of 'Space' found"):
        assert get_available_fields(building, 'Space', source='idf') == []
    assert get_available_fields(building, 'Space', source='idd')[:2] == ['Name', 'Zone_Name']


@needs_energyplus_25_1
def test_get_available_fields_rejects_an_invalid_source(building):
    with pytest.raises(ValueError, match="'source' must be either 'idd' or 'idf'"):
        get_available_fields(building, 'Zone', source='epjson')


@needs_energyplus_25_1
def test_reduce_runtime_simplifies_the_model(building):
    reduce_runtime(building, minimal_shadowing=True, shading_calculation_update_frequency=30,
                   maximum_figures_in_shadow_overlap_calculations=500, timesteps=4,
                   runperiod_begin_month=6, runperiod_begin_day_of_month=1,
                   runperiod_end_month=7, runperiod_end_day_of_month=31)

    assert building.idfobjects['Building'][0].Solar_Distribution == 'MinimalShadowing'
    run_period = building.idfobjects['RunPeriod'][0]
    assert [run_period.Begin_Month, run_period.Begin_Day_of_Month, run_period.End_Month,
            run_period.End_Day_of_Month] == [6, 1, 7, 31]
    shadow_calculation = building.idfobjects['ShadowCalculation'][0]
    assert shadow_calculation.Shading_Calculation_Update_Frequency == 30
    assert shadow_calculation.Maximum_Figures_in_Shadow_Overlap_Calculations == 500
    assert building.idfobjects['Timestep'][0].Number_of_Timesteps_per_Hour == 4


@pytest.mark.parametrize('arguments', [
    dict(timesteps=1),
    dict(timesteps=61),
    dict(shading_calculation_update_frequency=0),
    dict(shading_calculation_update_frequency=366),
])
def test_reduce_runtime_rejects_values_out_of_range(arguments):
    # The values are checked before the model is changed
    with pytest.raises(ValueError, match='cannot be smaller than'):
        reduce_runtime(SimpleNamespace(), **arguments)


@pytest.mark.parametrize('timesteps', [0, 7, 61])
def test_modify_timesteps_rejects_the_values_that_energyplus_does_not_allow(timesteps):
    with pytest.raises(ValueError, match='not in allowable values'):
        modify_timesteps(SimpleNamespace(), timesteps)
