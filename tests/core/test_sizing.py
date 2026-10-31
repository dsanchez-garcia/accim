"""Tests for the sizing calculations of the models with the VRF systems of accim, which are autosized.

EnergyPlus cannot run an autosized VRF system without sizing it: with the zone sizing calculation off, it stops
("For autosizing of ZoneHVAC:TerminalUnit:VariableRefrigerantFlow ..., a zone sizing run must be done"). AddAccis
enabled the sizing calculations, but in accim 0.x add_accis_to_idf (which accim.parametric_and_optimisation uses)
and add_vrf_system did not. EnergyPlus also needs sizing periods, so accim warns when a model has none.
"""
import shutil
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

from accim.sim import accis, apmv

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
IDD_25_2 = Path('C:/EnergyPlusV25-2-0/Energy+.idd')
SIZING_FLAGS = ('Do_Zone_Sizing_Calculation', 'Do_System_Sizing_Calculation', 'Do_Plant_Sizing_Calculation')
ADD_ACCIS_ARGS = dict(supply_air_temp_input_method='temperature difference', output_type='simplified',
                      output_freqs=['hourly'], temp_ctrl='temperature', verbose_mode=False)

needs_sample = pytest.mark.skipif(not (IDD_25_2.exists() and SAMPLE_IDF.exists()),
                                  reason='needs EnergyPlus 25.2 and the sample IDF of the repository')


@pytest.fixture
def building(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))
    control = building.idfobjects['SimulationControl'][0]
    for flag in SIZING_FLAGS:
        setattr(control, flag, 'No')
    return building


def _flags(building):
    control = building.idfobjects['SimulationControl'][0]
    return [getattr(control, flag) for flag in SIZING_FLAGS]


def _sizing_period_warnings(record):
    return [w for w in record if 'has no sizing periods' in str(w.message)]


@needs_sample
@pytest.mark.parametrize('script_type', ['vrf_ac', 'vrf_mm'])
def test_add_accis_to_idf_enables_the_sizing_of_the_vrf_systems(building, script_type):
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter('always')
        accis.add_accis_to_idf(building, script_type=script_type, **ADD_ACCIS_ARGS)

    assert _flags(building) == ['Yes', 'Yes', 'Yes']
    # The model has design days, so there is no warning
    assert building.idfobjects['SizingPeriod:DesignDay']
    assert not _sizing_period_warnings(record)


@needs_sample
def test_models_without_sizing_periods_get_a_warning(building):
    for design_day in list(building.idfobjects['SizingPeriod:DesignDay']):
        building.removeidfobject(design_day)

    # The warning names the IDF file (model.idf)
    with pytest.warns(UserWarning, match='The model model has no sizing periods'):
        accis.add_accis_to_idf(building, script_type='vrf_mm', **ADD_ACCIS_ARGS)


@needs_sample
def test_add_vrf_system_enables_the_sizing_calculations(building):
    apmv.add_vrf_system(building, verbose_mode=False)

    assert _flags(building) == ['Yes', 'Yes', 'Yes']


@pytest.mark.parametrize('script_type, enabled', [('vrf_ac', True), ('vrf_mm', True), ('ex_ac', False),
                                                  ('ex_mm', False)])
def test_add_accis_to_idf_only_changes_the_sizing_of_the_vrf_systems(monkeypatch, script_type, enabled):
    # The existing HVAC systems are the user's, so their sizing calculations do not change, as in accim 0.x
    calls = []
    monkeypatch.setattr(accis, 'AccimModel', lambda *args, **kwargs: SimpleNamespace())
    monkeypatch.setattr(accis, 'add_accis_objects', lambda *args, **kwargs: None)
    monkeypatch.setattr(accis, 'add_outputs', lambda *args, **kwargs: None)
    monkeypatch.setattr(accis, 'enable_sizing_calculations', calls.append)

    accis.add_accis_to_idf(SimpleNamespace(idd_version=(25, 1, 0)), script_type=script_type,
                           supply_air_temp_input_method='temperature difference', output_type='standard',
                           output_freqs=['hourly'], temp_ctrl='temp', verbose_mode=False)

    assert bool(calls) == enabled
