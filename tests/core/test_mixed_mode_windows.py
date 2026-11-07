"""Tests for the windows and doors that accim opens and closes in mixed mode ('vrf_mm' and 'ex_mm',
:mod:`accim.sim.windows`).

Until 2026-11-07, accim found the windows of an AirflowNetwork only by the names of DesignBuilder ('..._Win' and
'..._Door', with the zone before the first '_'), so it found none in the example files of EnergyPlus (and their names,
with '-' or spaces, gave invalid EMS variables when it did); it read the zone of the ZoneVentilation objects from a
field that the IDDs of EnergyPlus 25.1 and 26.2 do not have for ZoneVentilation:DesignFlowRate (BadEPFieldError); it
ignored the ZoneVentilation objects of ZoneLists and SpaceLists; it took the fans (Exhaust, Intake, Balanced) as
windows; and it kept the limits of the ZoneVentilation objects, which kept closed the windows that the EMS opened (the
first window of the OSM residential model of the golden master never ventilated: its maximum indoor temperature is 1 C).
The occupant ventilation controls and the hybrid ventilation managers of the models also overrode the EMS.
"""
import lzma
import subprocess
import warnings
from pathlib import Path

import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim import windows

REPO = Path(__file__).resolve().parents[2]
INPUTS = REPO / 'tests' / 'core' / 'golden_master' / 'inputs'
EXAMPLES = default_energyplus_folder('25.1') / 'ExampleFiles'
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
ARGUMENTS = dict(output_type='standard', output_frequencies=['timestep'], keep_existing_outputs=False,
                 setpoint_type='temperature', verbose=False)

pytestmark = pytest.mark.skipif(not (EXAMPLES.exists() and INPUTS.exists()),
                                reason='needs the example files of EnergyPlus 25.1 and the input models of the golden '
                                       'master')


def _example(tmp_path, name):
    from besos.eppy_funcs import get_building

    path = tmp_path / name
    path.write_bytes((EXAMPLES / name).read_bytes())
    return get_building(str(path))


def _input_model(tmp_path, name):
    from besos.eppy_funcs import get_building

    path = tmp_path / f'{name}.idf'
    path.write_bytes(lzma.decompress((INPUTS / f'{name}.idf.xz').read_bytes()))
    return get_building(str(path))


def _add(idf, script_type='ex_mm'):
    """add_accis_to_idf; return the model and the messages of its UserWarnings."""
    from accim.sim.accis import add_accis_to_idf

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model = add_accis_to_idf(idf, script_type=script_type, **ARGUMENTS)
    return model, [str(w.message) for w in caught if w.category is UserWarning]


def _by_name(idf, object_type, name):
    return next(o for o in idf.idfobjects[object_type] if o.obj[1].upper() == name.upper())


def test_the_windows_of_an_airflow_network_are_found_by_their_surfaces(tmp_path):
    """The exterior windows with AirflowNetwork openings, whatever their names, and not the doors between zones."""
    idf = _example(tmp_path, 'AirflowNetwork3zVent.idf')

    model, messages = _add(idf)

    assert model.natural_ventilation_type == 'AFN'
    assert list(zip(model.windows_orig, model.window_zones)) == [
        ('Window11', 'WEST_ZONE'), ('Window12', 'WEST_ZONE'), ('Window2', 'NORTH_ZONE')]
    actuators = {a.Name: a for a in idf.idfobjects['EnergyManagementSystem:Actuator']}
    assert actuators['Window11_VentOpenFact'].Actuated_Component_Unique_Name == 'Window11'
    assert actuators['Window11_VentOpenFact'].Actuated_Component_Type == 'AirFlow Network Window/Door Opening'
    assert any("['EAST_ZONE']" in m and 'accim cannot open their windows' in m for m in messages)


def test_the_ems_names_of_the_windows_are_valid_and_unique():
    from types import SimpleNamespace

    from accim.sim.model import AccimModel

    model = SimpleNamespace(windows_orig=[], windows=[], window_zones=[])
    for window in ('SPACE1-1_Win', 'Zone 1:Wall 1 Win', 'SPACE1_1_Win'):
        AccimModel._add_window(model, window, 'zone')
    assert model.windows == ['SPACE1_1_Win', 'Zone_1_Wall_1_Win', 'SPACE1_1_Win_2']


def test_an_airflow_network_without_multizone_airflows_opens_the_zone_ventilation_objects(tmp_path):
    """With MultizoneWithDistributionOnlyDuringFanOperation, EnergyPlus simulates the ZoneVentilation objects (while
    the fans are off), not the windows of the AirflowNetwork."""
    idf = _example(tmp_path, 'AirflowNetwork_Simple_House.idf')

    model, messages = _add(idf)

    assert model.natural_ventilation_type == 'Scheduled'
    assert model.windows_orig == ['LIVING ZONE_Win']
    assert _by_name(idf, 'ZoneVentilation:DesignFlowRate', 'LIVING ZONE Ventl 1').Schedule_Name == \
        'Vent_Sch_LIVING ZONE'
    assert any('do not ventilate while the fans run' in m for m in messages)


def test_only_the_natural_ventilation_objects_are_windows_and_their_limits_are_removed(tmp_path):
    idf = _example(tmp_path, 'VentilationSimpleTest.idf')
    intake = _by_name(idf, 'ZoneVentilation:DesignFlowRate', 'ZONE 2 Ventl 1').obj[:]
    exhaust = _by_name(idf, 'ZoneVentilation:DesignFlowRate', 'ZONE 3 Ventl 1').obj[:]
    natural = _by_name(idf, 'ZoneVentilation:DesignFlowRate', 'ZONE 1 Ventl 1')
    natural.Minimum_Indoor_Temperature = 18
    natural.Maximum_Outdoor_Temperature_Schedule_Name = 'Constant'

    model, messages = _add(idf)

    assert sorted(model.windows_orig) == ['ZONE 1_Win', 'ZONE 3_Win']
    assert natural.Schedule_Name == 'Vent_Sch_ZONE 1'
    stack = _by_name(idf, 'ZoneVentilation:WindandStackOpenArea', 'ZONE 3 Ventl 2')
    assert stack.Opening_Area_Fraction_Schedule_Name == 'Vent_Sch_ZONE 3'
    for vent in (natural, stack):
        for field, value in windows.VENTILATION_LIMITS.items():
            assert float(getattr(vent, field)) == value
            if f'{field}_Schedule_Name' in vent.fieldnames:
                assert getattr(vent, f'{field}_Schedule_Name') == ''
    # The fans (Intake, Exhaust) are not windows
    assert _by_name(idf, 'ZoneVentilation:DesignFlowRate', 'ZONE 2 Ventl 1').obj == intake
    assert _by_name(idf, 'ZoneVentilation:DesignFlowRate', 'ZONE 3 Ventl 1').obj == exhaust
    assert any("['ZONE 2']" in m and 'accim cannot open their windows' in m for m in messages)


def test_the_zone_ventilation_objects_of_a_zone_list_are_split_for_each_zone(tmp_path):
    idf = _example(tmp_path, 'VentilationSimpleTest.idf')
    idf.newidfobject('ZoneList', Name='Zones 1 and 2', Zone_1_Name='ZONE 1', Zone_2_Name='ZONE 2')
    vent = _by_name(idf, 'ZoneVentilation:DesignFlowRate', 'ZONE 1 Ventl 1')
    setattr(vent, vent.fieldnames[2], 'Zones 1 and 2')

    model, _ = _add(idf)

    assert sorted(model.windows_orig) == ['ZONE 1_Win', 'ZONE 2_Win', 'ZONE 3_Win']
    for zone in ('ZONE 1', 'ZONE 2'):
        copy = _by_name(idf, 'ZoneVentilation:DesignFlowRate', f'{zone} ZONE 1 Ventl 1')
        assert getattr(copy, copy.fieldnames[2]) == zone
        assert copy.Schedule_Name == f'Vent_Sch_{zone}'
    assert not [v for v in idf.idfobjects['ZoneVentilation:DesignFlowRate'] if v.Name == 'ZONE 1 Ventl 1']


def test_the_hybrid_ventilation_managers_are_removed_in_mixed_mode(tmp_path):
    """The hybrid ventilation managers open and close the ZoneVentilation objects of the zones of their air loops (not
    only the one they name, here an intake fan), so they are removed when accim opens and closes windows; without
    windows, they stay."""
    idf = _example(tmp_path, 'HybridVentilationControlGlobalSimple.idf')
    _by_name(idf, 'ZoneVentilation:DesignFlowRate', 'NORTH ZONE Ventl').Ventilation_Type = 'Natural'

    model, messages = _add(idf)

    assert 'NORTH ZONE_Win' in model.windows_orig
    assert not idf.idfobjects['AvailabilityManager:HybridVentilation']
    assert any("AvailabilityManager:HybridVentilation objects ['Hybrid ventilation controller 1'] have been removed"
               in m for m in messages)
    # Without windows (the model only has intake fans), or with full air-conditioning, they stay
    for script_type in ('ex_mm', 'ex_ac'):
        idf = _example(tmp_path, 'HybridVentilationControlGlobalSimple.idf')
        _add(idf, script_type=script_type)
        assert idf.idfobjects['AvailabilityManager:HybridVentilation']


def test_the_hybrid_ventilation_managers_stay_with_an_air_distribution_system(tmp_path):
    """With MultizoneWithDistribution, they switch the air loops off while the windows are open: without them,
    EnergyPlus stopped ('A diagonal entity is zero in AirflowNetwork matrix')."""
    idf = _example(tmp_path, 'AirflowNetwork_MultiZone_SmallOffice_VAV.idf')

    _, messages = _add(idf)

    assert idf.idfobjects['AvailabilityManager:HybridVentilation']
    assert any('MultizoneWithDistribution' in m and 'stay' in m for m in messages)


def test_the_ems_actuators_of_the_model_on_the_windows_get_a_warning(tmp_path):
    """The example file EMSAirflowNetworkOpeningControlByHumidity opens a window with an EMS program of its own."""
    idf = _example(tmp_path, 'EMSAirflowNetworkOpeningControlByHumidity.idf')

    model, messages = _add(idf)

    assert 'Zn001:Wall001:Win001' in model.windows_orig
    assert any("EMS actuators ['MyOpenFactor']" in m for m in messages)


def test_the_windows_are_freed_from_the_occupant_ventilation_controls(tmp_path):
    """EnergyPlus gives the occupant ventilation control of the zone of Window1 (AirflowNetwork:MultiZone:Zone) to all
    its windows and doors without one of their own: the zone loses it, and the door between zones keeps it."""
    idf = _example(tmp_path, 'AirflowNetworkOccupantVentilationControl.idf')

    model, messages = _add(idf)

    surfaces = {s.Surface_Name: s for s in idf.idfobjects['AirflowNetwork:MultiZone:Surface']}
    zones = {z.Zone_Name: z for z in idf.idfobjects['AirflowNetwork:MultiZone:Zone']}
    assert 'Window1' in model.windows_orig
    assert surfaces['Window1'].Occupant_Ventilation_Control_Name == ''
    assert zones['WEST_ZONE'].Occupant_Ventilation_Control_Name == ''
    assert surfaces['DoorInSurface_3'].Occupant_Ventilation_Control_Name == 'OccupantVentilatioControl'
    assert any("occupant ventilation controls of the AirflowNetwork surfaces ['Window1']" in m for m in messages)


def _energyplus_25_1():
    folder = find_energyplus('25.1', required=False)
    return None if folder is None or not (folder / 'energyplus.exe').exists() else folder / 'energyplus.exe'


@pytest.mark.skipif(_energyplus_25_1() is None or not SAMPLE_EPW.exists(),
                    reason='needs EnergyPlus 25.1 and the sample EPW of the repository')
@pytest.mark.parametrize('name, month, day', [('exptac', 6, 5), ('osmresschvent', 4, 20)])
def test_energyplus_opens_and_closes_the_windows_when_the_ems_does(tmp_path, name, month, day):
    """'ex_mm', three days of spring or early summer in Seville: EnergyPlus opens the windows that the EMS opens (the
    ventilation hours of their zones), and only those. The opening factors of the AirflowNetwork windows of the sample
    model with PTACs are those of the EMS; the ZoneVentilation:WindandStackOpenArea objects of the OSM residential model
    ventilate when the EMS opens them, except when the wind blows from behind them (EnergyPlus gives them no flow then:
    their height difference is 0). Before 2026-11-07, the first one never ventilated, whatever the EMS did (its maximum
    indoor temperature was 1 C)."""
    idf = _input_model(tmp_path, name)
    model, _ = _add(idf)
    for run_period in idf.idfobjects['RunPeriod'][1:]:
        idf.removeidfobject(run_period)
    run_period = idf.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month, run_period.End_Month, run_period.End_Day_of_Month = (
        month, day, month, day + 2)
    folder = tmp_path / 'run'
    folder.mkdir()
    idf.saveas(str(folder / 'model.idf'))
    result = subprocess.run([str(_energyplus_25_1()), '-d', str(folder), '-p', 'run', '-s', 'C', '-r',
                             '-w', str(SAMPLE_EPW), str(folder / 'model.idf')], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    results = pd.read_csv(folder / 'run.csv')
    columns = {c.split(' [')[0].upper(): c for c in results.columns}

    ventilated = []
    for zone, ems_name in zip(model.ems_zones, model.ems_names):
        decided = results[columns[f'EMS:VENTILATION HOURS_{ems_name}'.upper()]] > 0
        if model.natural_ventilation_type == 'AFN':
            factors = [results[columns[f'{w}:AFN Surface Venting Window or Door Opening Factor'.upper()]]
                       for w, z in zip(model.windows_orig, model.window_zones) if z.upper() == zone.upper()]
            opened = pd.concat(factors, axis=1).max(axis=1) > 0
            assert (opened == decided).all(), zone
        else:
            opened = results[columns[f'{zone}:Zone Ventilation Standard Density Air Change Rate'.upper()]] > 1e-6
            assert not (opened & ~decided).any(), zone
            assert (opened & decided).sum() > 0.5 * decided.sum(), zone
        ventilated.append(decided.any())
    if model.natural_ventilation_type == 'AFN':
        assert any(ventilated)
    else:
        assert all(ventilated)
