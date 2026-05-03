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
        ScriptType='vrf_mm'
    )

    ts.log_test("Init AccimPredefModelsParamSim", "PASS" if sim.building else "FAIL",
             f"Script Type: {sim.ScriptType}")
    assert sim.ScriptType == 'vrf_mm'

def test_accim_predef_models_parametric():
    """Test: Parametric con AccimPredefModelsParamSim."""
    ts.print_section("TEST: AccimPredefModelsParamSim Parametric")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])

    sim = ts.AccimPredefModelsParamSim(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1]
    )

    sim.set_parameters()
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_predef_param',
        processes=1
    )

    ts.log_test("AccimPredefModelsParamSim Parametric", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows")

if __name__ == '__main__':
    test_accim_predef_models_init()
    test_accim_predef_models_parametric()
