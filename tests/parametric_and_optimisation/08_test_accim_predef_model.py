# 08_test_accim_predef_model.py
"""
Test de AccimPredefModelsParamSim wrapper.
"""

from .. import test_setup as ts

def test_accim_predef_models_init():
    """Test: Inicializar AccimPredefModelsParamSim."""
    ts.print_section("TEST: AccimPredefModelsParamSim Init")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])

    sim = ts.AccimPredefModelsParamSim(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        output_type='standard',
        script_type='vrf_mm'
    )

    ts.log_test("Init AccimPredefModelsParamSim", "PASS" if sim.building else "FAIL",
             f"Script Type: {sim.script_type}")
    assert sim.script_type == 'vrf_mm'

def test_accim_predef_models_parametric():
    """Test: Parametric con AccimPredefModelsParamSim."""
    ts.print_section("TEST: AccimPredefModelsParamSim Parametric")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])

    sim = ts.AccimPredefModelsParamSim(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1]
    )

    sim.set_parameters(accis_params_dict={'comfort_standard': [1], 'category': [1, 2], 'comfort_mode': [3]})
    ts.set_meter_readers(sim)
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_predef_param',
        processes=1
    )

    ts.log_test("AccimPredefModelsParamSim Parametric", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows")
    assert len(results) == 2
    assert results[ts.METERS].notna().all().all()

def test_accim_predef_models_static_comfort_standards():
    """Test: comfort_standard 0 (ESP CTE) y 22 (INT ISO7730) con el comfort_mode del modelo base (3).

    Sus setpoints no dependen de comfort_mode; en accim 0.x solo se fijaban con comfort_mode 0, y EnergyPlus se detenía.
    """
    ts.print_section("TEST: AccimPredefModelsParamSim comfort_standard 0 y 22")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])

    sim = ts.AccimPredefModelsParamSim(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1]
    )

    sim.set_parameters(accis_params_dict={'comfort_standard': [0, 22], 'category': [1, 2]})
    ts.set_meter_readers(sim)
    sim.set_problem()
    # sampling_full_set daría comfort_standard 0 solo con la primera categoría (no depende de ella); el plan custom
    # simula cada norma con una categoría distinta
    sim.sampling_custom(ts.pd.DataFrame({'comfort_standard': [0, 22], 'category': [1, 2]}))

    results = sim.run_parametric_simulation(
        out_dir='./test_predef_static',
        processes=1
    )

    ts.log_test("AccimPredefModelsParamSim comfort_standard 0 y 22", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows")
    assert len(results) == 2
    assert results[ts.METERS].notna().all().all()

def test_accim_predef_models_baseline():
    """Test: el modelo base del wrapper (modelo custom con los coeficientes por defecto) simula.

    En accim 0.x no tenía coeficientes: la consigna de calefacción quedaba por encima de la de refrigeración, y
    EnergyPlus se detenía en la simulación de prueba de los outputs y en los planes sin comfort_standard.
    """
    ts.print_section("TEST: AccimPredefModelsParamSim modelo base")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])

    sim = ts.AccimPredefModelsParamSim(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1]
    )

    # La simulación de prueba del modelo base valida los meters
    sim.set_output_meters_to_idf(output_meters=ts.METERS, validate=True, on_missing='raise')
    sim.set_output_readers(
        df_output_meter=ts.pd.DataFrame({'key_name': ts.METERS, 'frequency': ['Hourly'] * len(ts.METERS)})
    )
    sim.set_parameters(accis_params_dict={'hvac_mode': [0, 2]})
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_predef_baseline',
        processes=1
    )

    ts.log_test("AccimPredefModelsParamSim modelo base", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows")
    assert len(results) == 2
    assert results[ts.METERS].notna().all().all()

if __name__ == '__main__':
    test_accim_predef_models_init()
    test_accim_predef_models_parametric()
    test_accim_predef_models_static_comfort_standards()
    test_accim_predef_models_baseline()
