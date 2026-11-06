"""Tests for accim.sim.chile_funcs.apply_heating_activation_time_sch, which adds the heating activation time of Chile
to a model, read and saved with eppy."""
import shutil
from pathlib import Path

import pytest

from accim.energyplus import find_energyplus
from accim.sim.accis import load_idf
from accim.sim.chile_funcs import HEATING_ACTIVATION_SCHEDULE, apply_heating_activation_time_sch

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')

pytestmark = pytest.mark.skipif(not (find_energyplus('25.1', required=False) and SAMPLE_IDF.exists()),
                                reason='needs EnergyPlus 25.1 and the sample IDF of the repository')


@pytest.mark.parametrize('apply_to_occupancy', [True, False])
def test_the_schedule_is_added_and_applied_to_the_occupancy(tmp_path, apply_to_occupancy):
    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')

    apply_heating_activation_time_sch(str(tmp_path / 'model.idf'), apply_to_occupancy=apply_to_occupancy)

    model = load_idf(tmp_path / 'model_heat_act_time_added.idf')
    schedule = model.getobject('Schedule:Compact', HEATING_ACTIVATION_SCHEDULE)
    fields = schedule.fieldvalues[3:]
    # January: off until 6:00, on until 9:00, off until 17:00, on until 23:00
    assert fields[:12] == ['Through: 1/31', 'For: AllDays', 'Until: 6:00', '0', 'Until: 9:00', '1', 'Until: 17:00',
                           '0', 'Until: 23:00', '1', 'Until: 24:00', '0']
    # December: on from 17:00
    assert len(fields) == 130 and fields[-10:] == ['Through: 12/31', 'For: AllDays', 'Until: 6:00', '0', 'Until: 9:00',
                                                   '1', 'Until: 17:00', '0', 'Until: 24:00', '1']
    schedules = {p.Number_of_People_Schedule_Name for p in model.idfobjects['People']}
    assert (schedules == {HEATING_ACTIVATION_SCHEDULE}) is apply_to_occupancy


def test_a_model_with_the_schedule_does_not_change(tmp_path, capsys):
    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    apply_heating_activation_time_sch(str(tmp_path / 'model.idf'))

    apply_heating_activation_time_sch(str(tmp_path / 'model_heat_act_time_added.idf'))

    assert 'Heating_activation_time_chile already was in the model.' in capsys.readouterr().out
    assert not (tmp_path / 'model_heat_act_time_added_heat_act_time_added.idf').exists()
