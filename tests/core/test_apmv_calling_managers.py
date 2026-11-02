"""Tests for the EMS program calling managers that accim.sim.apmv.apply_apmv_setpoints adds.

Found by the review of 2026-10-24: apply_apmv_setpoints added a calling manager to every EMS program of the model
without one of the same name, also to the programs of the user, so a program run by another one (with ``run``), or
by a calling manager of another name, was also run at the beginning of each timestep. Now only the programs of the
aPMV setpoints get one.
"""
import shutil
from pathlib import Path

import pytest

from accim.sim.apmv import apply_apmv_setpoints

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
IDD_25_2 = Path('C:/EnergyPlusV25-2-0/Energy+.idd')

pytestmark = pytest.mark.skipif(not (IDD_25_2.exists() and SAMPLE_IDF.exists()),
                                reason='needs EnergyPlus 25.2 and the sample IDF of the repository')


def test_only_the_programs_of_the_apmv_setpoints_get_calling_managers(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))
    # Programs of the user: one run by a calling manager of another name, and one run by that program
    building.newidfobject('EnergyManagementSystem:Program', Name='user_subroutine', Program_Line_1='set x = 1')
    building.newidfobject('EnergyManagementSystem:Program', Name='user_program', Program_Line_1='run user_subroutine')
    building.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name='User manager',
                          EnergyPlus_Model_Calling_Point='BeginNewEnvironment', Program_Name_1='user_program')

    apply_apmv_setpoints(building=building, verbose=False)

    managers = {m.Name: m.Program_Name_1 for m in building.idfobjects['EnergyManagementSystem:ProgramCallingManager']}
    programs = [p.Name for p in building.idfobjects['EnergyManagementSystem:Program']]
    apmv_programs = [name for name in programs if name not in ('user_subroutine', 'user_program')]
    assert managers.pop('User manager') == 'user_program'
    # One calling manager for each program of the aPMV setpoints, in the order of the programs
    assert list(managers) == list(managers.values()) == apmv_programs
    assert 'set_cooling_season' in apmv_programs and any(name.startswith('apply_aPMV_') for name in apmv_programs)
