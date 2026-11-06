"""Tests for accim.utils.get_idf_hierarchy and get_spaces_from_spacelist: the zones of a model, their spaces and
the zone and space lists.

Ported from the tests of accim.utils of the branch refactor/sim-v1 (tests/utils/test_utils_idf.py). The
hierarchies with the occupants (get_people_hierarchy and get_idf_hierarchy_with_people) are tested in
test_people_instance.py and test_space_instance_names.py.

The IDDs before EnergyPlus 9.6 have no Space or SpaceList objects, and get_idf_hierarchy and
get_spaces_from_spacelist stopped with a KeyError ('SPACE', 'SPACELIST') for their models, whose zones have no
spaces. Now they read the classes that the IDD has, as the other hierarchy functions do.
"""
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from accim.energyplus import default_energyplus_folder
from accim.utils import get_idf_hierarchy, get_spaces_from_spacelist

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'


class _ObjectClasses(dict):
    """The idfobjects of eppy: the classes of the IDD, whatever the case of their names (KeyError for others)."""

    def __getitem__(self, key):
        return super().__getitem__(key.upper())


@pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                    reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
def test_get_idf_hierarchy_links_the_spaces_and_lists_of_a_model(tmp_path, capsys):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))
    # EnergyPlus does not distinguish the case of the names
    building.newidfobject('Space', Name='Office', Zone_Name='BLOCK1:ZONE1')
    building.newidfobject('Space', Name='Corridor', Zone_Name='Block1:Zone1')
    building.newidfobject('Space', Name='Orphan', Zone_Name='Block9:Zone9')
    building.newidfobject('ZoneList', Name='All Zones', Zone_1_Name='Block1:Zone1', Zone_2_Name='Block1:Zone2')
    building.newidfobject('SpaceList', Name='Offices', Space_1_Name='Office', Space_2_Name='Corridor')

    hierarchy = get_idf_hierarchy(building)

    assert hierarchy == {
        'zones': {
            'Block1:Zone1': {'object_type': 'Zone', 'spaces': ['Office', 'Corridor']},
            'Block1:Zone2': {'object_type': 'Zone', 'spaces': []},
        },
        'groups': {
            'zone_lists': {'All Zones': ['Block1:Zone1', 'Block1:Zone2']},
            'space_lists': {'Offices': ['Office', 'Corridor']},
        },
    }
    assert "WARNING: Space 'Orphan' references an unknown Zone: 'Block9:Zone9'" in capsys.readouterr().out


def test_get_idf_hierarchy_of_a_model_of_an_idd_without_spaces():
    # The classes of the IDD of EnergyPlus 9.4 that get_idf_hierarchy reads
    zone_list = SimpleNamespace(Name='All Zones', fieldvalues=['ZoneList', 'All Zones', 'Block1:Zone1', 'Block1:Zone2'])
    idf = SimpleNamespace(idfobjects=_ObjectClasses(
        ZONE=[SimpleNamespace(Name='Block1:Zone1'), SimpleNamespace(Name='Block1:Zone2')],
        ZONELIST=[zone_list],
    ))

    assert get_idf_hierarchy(idf) == {
        'zones': {
            'Block1:Zone1': {'object_type': 'Zone', 'spaces': []},
            'Block1:Zone2': {'object_type': 'Zone', 'spaces': []},
        },
        'groups': {'zone_lists': {'All Zones': ['Block1:Zone1', 'Block1:Zone2']}, 'space_lists': {}},
    }


def test_get_spaces_from_spacelist_of_a_model_of_an_idd_without_space_lists():
    # As its docstring says, a space list that is not found gives []; before, KeyError: 'SPACELIST'
    idf = SimpleNamespace(idfobjects=_ObjectClasses(ZONE=[SimpleNamespace(Name='Block1:Zone1')]))

    assert get_spaces_from_spacelist(idf, 'Offices') == []
