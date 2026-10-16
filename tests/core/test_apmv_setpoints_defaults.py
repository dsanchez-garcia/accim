"""Tests for the default values of accim.sim.apmv_setpoints.apply_apmv_setpoints.

Before, the defaults were pmv_cooling_sp=-0.5 and pmv_heating_sp=0.5, the opposite of the
docstring and of the defaults for missing dictionary keys (dflt_for_pmv_cooling_sp=0.5 and
dflt_for_pmv_heating_sp=-0.5). Since the EMS takes them as aPMV setpoints, both PMV setpoints of
the thermostat ended up at 0. The cooling season went from day 120 to day 210 (30 April to
29 July); now it goes from 1 May to 1 October, as CoolSeasonStart and CoolSeasonEnd in addAccis.
"""
import inspect
import shutil
from pathlib import Path

import pytest

from accim.sim.apmv_setpoints import apply_apmv_setpoints

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
IDD_25_2 = Path('C:/EnergyPlusV25-2-0/Energy+.idd')


def test_default_setpoints_and_cooling_season():
    params = inspect.signature(apply_apmv_setpoints).parameters

    assert params['pmv_cooling_sp'].default == 0.5
    assert params['pmv_heating_sp'].default == -0.5
    assert params['cooling_season_start'].default == 121
    assert params['cooling_season_end'].default == 274
    # The defaults for the keys missing in dictionaries agree with the defaults for single values.
    assert params['dflt_for_pmv_cooling_sp'].default == params['pmv_cooling_sp'].default
    assert params['dflt_for_pmv_heating_sp'].default == params['pmv_heating_sp'].default


@pytest.mark.skipif(not (IDD_25_2.exists() and SAMPLE_IDF.exists()),
                    reason='needs EnergyPlus 25.2 and the sample IDF of the repository')
def test_default_values_reach_the_ems_programs(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))

    apply_apmv_setpoints(building=building, verbose_mode=False)

    programs = {p.Name: p for p in building.idfobjects['EnergyManagementSystem:Program']}
    season = programs['set_cooling_season_input_data']
    assert season.Program_Line_1 == 'set CoolSeasonStart = 121'
    assert season.Program_Line_2 == 'set CoolSeasonEnd = 274'

    zone_inputs = [p for name, p in programs.items() if name.startswith('set_zone_input_data_')]
    assert len(zone_inputs) > 0
    for program in zone_inputs:
        suffix = program.Name[len('set_zone_input_data_'):]
        assert program.Program_Line_3 == f'set pmv_cooling_sp_{suffix} = 0.5'
        assert program.Program_Line_4 == f'set pmv_heating_sp_{suffix} = -0.5'
