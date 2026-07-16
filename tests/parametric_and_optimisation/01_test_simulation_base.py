# 01_test_simulation_base.py
"""
Test de la clase base SimulationBase.
Cubre inicialización, métodos de outputs, parámetros y evaluadores.
"""

import os
import pandas as pd
from .. import test_setup as ts

def test_simulationbase_init_accim_predefined():
    """Test: Inicialización con modelo predefinido ACCIM."""
    ts.print_section("TEST: SimulationBase Init - ACCIM Predefined Model")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model',
        output_type='standard',
        output_freqs=['hourly', 'monthly']
    )

    ts.log_test("Init Predefined", "PASS" if sim.building else "FAIL",
             f"Buildings: {len(sim.buildings)}, EPWs: {len(sim.epws)}")
    assert sim.is_accim_predef_model == True
    assert len(sim.buildings) > 0

def test_simulationbase_init_accim_custom():
    """Test: Inicialización con modelo custom ACCIM."""
    ts.print_section("TEST: SimulationBase Init - ACCIM Custom Model")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim custom model',
        output_type='detailed'
    )

    ts.log_test("Init Custom", "PASS" if sim.is_accim_custom_model else "FAIL")
    assert sim.is_accim_custom_model == True

def test_simulationbase_init_apmv():
    """Test: Inicialización con setpoints APMV."""
    ts.print_section("TEST: SimulationBase Init - APMV Setpoints")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='apmv setpoints'
    )

    ts.log_test("Init APMV", "PASS" if sim.is_apmv_setpoints else "FAIL")
    assert sim.is_apmv_setpoints == True

def test_get_output_var_df():
    """Test: Obtener DataFrame de Output:Variable."""
    ts.print_section("TEST: Get Output Variable DataFrame")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    df = sim.get_output_variables_df_from_idf()
    ts.log_test("Get Output Var DF", "PASS" if len(df) > 0 else "FAIL",
             f"Variables: {len(df)}")
    assert len(df) > 0

def test_get_output_meter_df():
    """Test: Obtener DataFrame de Output:Meter."""
    ts.print_section("TEST: Get Output Meter DataFrame")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    df = sim.get_output_meters_df_from_idf()
    ts.log_test("Get Output Meter DF", "PASS" if isinstance(df, pd.DataFrame) else "FAIL",
             f"Meters: {len(df)}")

def test_set_evaluator():
    """Test: Crear evaluador de EnergyPlus."""
    ts.print_section("TEST: Set Evaluator")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    # Configurar parámetros, outputs y problema antes de crear evaluador
    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
    df_var = sim.get_output_variables_df_from_idf()
    df_meter = sim.get_output_meters_df_from_idf()
    # Renombrar columnas para que coincidan con lo esperado por set_output_readers
    if not df_var.empty:
        df_var = df_var.rename(columns={'reporting_frequency': 'frequency'})
    if not df_meter.empty:
        df_meter = df_meter.rename(columns={'reporting_frequency': 'frequency'})
    sim.set_output_readers(df_output_meter=df_meter, df_output_variable=df_var)
    sim.set_problem()

    out_dir = './test_evaluator'
    evaluator = sim.set_evaluator(epw=ts.EPW_PATHS[0], out_dir=out_dir)

    ts.log_test("Set Evaluator", "PASS" if evaluator else "FAIL",
             f"Evaluator: {type(evaluator).__name__}")
    assert evaluator is not None

def test_idf_backup():
    """Test: Backup de IDF."""
    ts.print_section("TEST: IDF Backup")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    backup_path = sim._save_idf_backup(label='test_backup')
    ts.log_test("IDF Backup", "PASS" if os.path.exists(backup_path) else "FAIL",
             f"Backup: {backup_path}")
    assert os.path.exists(backup_path)

if __name__ == '__main__':
    test_simulationbase_init_accim_predef
