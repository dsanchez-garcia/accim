"""Tests for the ideal loads systems of the input model when accim adds its VRF systems.

The VRF systems replace the zone equipment lists and connections of the model, so the
ZoneHVAC:IdealLoadsAirSystem objects of the model were left unconnected (until accim 1.0.0), and EnergyPlus
reported one severe error for each of them ("Orphaned ZoneHVAC object found"). The existing HVAC systems
(ScriptType 'ex_ac' and 'ex_mm') are the user's, so their ideal loads systems are kept.
"""
import shutil
from pathlib import Path

import pytest

from accim.sim import accis, apmv

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
IDD_25_1 = Path('C:/EnergyPlusV25-1-0/Energy+.idd')
IDEAL_LOADS = 'ZoneHVAC:IdealLoadsAirSystem'
ADD_ACCIS_ARGS = dict(supply_air_temp_input_method='temperature difference', output_type='simplified',
                      output_freqs=['hourly'], temp_ctrl='temperature', verbose_mode=False)

pytestmark = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                                reason='needs EnergyPlus 25.1 and the sample IDF of the repository')


@pytest.fixture
def building(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))
    # The sample model has one ideal loads system in each of its two zones
    assert len(building.idfobjects[IDEAL_LOADS]) == 2
    return building


def _equipment(building):
    """The (object type, name) pairs of all the zone equipment lists of the model."""
    pairs = []
    for equipment_list in building.idfobjects['ZoneHVAC:EquipmentList']:
        n = 1
        while f'Zone_Equipment_{n}_Object_Type' in equipment_list.fieldnames:
            object_type = equipment_list[f'Zone_Equipment_{n}_Object_Type']
            if object_type:
                pairs.append((object_type.upper(), equipment_list[f'Zone_Equipment_{n}_Name']))
            n += 1
    return pairs


@pytest.mark.parametrize('script_type', ['vrf_ac', 'vrf_mm'])
def test_add_accis_to_idf_removes_the_ideal_loads_systems_that_the_vrf_systems_replace(building, script_type):
    accis.add_accis_to_idf(building, script_type=script_type, **ADD_ACCIS_ARGS)

    assert len(building.idfobjects[IDEAL_LOADS]) == 0
    equipment = _equipment(building)
    assert len(equipment) == 2
    assert {object_type for object_type, _ in equipment} == {'ZONEHVAC:TERMINALUNIT:VARIABLEREFRIGERANTFLOW'}


def test_add_vrf_system_of_the_apmv_setpoints_removes_the_ideal_loads_systems(building):
    apmv.add_vrf_system(building, verbose_mode=False)

    assert len(building.idfobjects[IDEAL_LOADS]) == 0
    assert {object_type for object_type, _ in _equipment(building)} == {
        'ZONEHVAC:TERMINALUNIT:VARIABLEREFRIGERANTFLOW'}


def test_the_existing_hvac_systems_keep_their_ideal_loads_systems(building):
    before = _equipment(building)

    accis.add_accis_to_idf(building, script_type='ex_ac', **ADD_ACCIS_ARGS)

    assert [system.Name for system in building.idfobjects[IDEAL_LOADS]] == [
        'Block1:Zone2 Ideal Loads Air', 'Block1:Zone1 Ideal Loads Air']
    assert _equipment(building) == before
    assert {object_type for object_type, _ in before} == {IDEAL_LOADS.upper()}
