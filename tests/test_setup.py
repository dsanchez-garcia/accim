# 00_test_setup.py - Configuración común para todos los tests
"""
Setup común y utilidades para testing del módulo parametric_and_optimisation.
Define IDFs, EPWs, funciones auxiliares y configuraciones base.
"""

import os
import sys
from pathlib import Path
import pandas as pd
from besos import eppy_funcs as ef
import accim
import accim.utils
from accim.parametric_and_optimisation.main import (
    ParametricSimulation,
    OptimisationSimulation,
    AccimPredefModelsParamSim
)

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS Y CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# Directorio base de datos de test
TEST_DATA_DIR = Path(__file__).parent / 'test_data'

IDF_PATHS = [
    str(TEST_DATA_DIR / 'SF_Detached_B_min_North.idf'),
    str(TEST_DATA_DIR / 'SF_Detached_D_min_North.idf')
]

EPW_PATHS = [
    str(TEST_DATA_DIR / 'seville_2024.epw'),
    str(TEST_DATA_DIR / 'seville_2025.epw'),
    str(TEST_DATA_DIR / 'madrid_2024.epw'),
    str(TEST_DATA_DIR / 'madrid_2025.epw')
]

# CATEGORÍAS PARA TESTS
TEST_CATEGORIES = {
    'fast': {'epws': EPW_PATHS[:1], 'idfs': IDF_PATHS[:1]},  # Un IDF, un EPW
    'medium': {'epws': EPW_PATHS[:2], 'idfs': IDF_PATHS},     # Ambos IDFs, 2 EPWs
    'comprehensive': {'epws': EPW_PATHS, 'idfs': IDF_PATHS}   # Todos
}

# Periodo de simulación: dos semanas a caballo entre junio y julio, para que haya resultados horarios y de dos
# meses (mes inicial, día, mes final, día), con 2 timesteps por hora, como los notebooks paramétricos
RUN_PERIOD = (6, 24, 7, 7)
TIMESTEPS = 2

# Días del EPW con los que EnergyPlus dimensiona los sistemas VRF (no se simulan)
SIZING_PERIODS = (
    ('Winter sizing days', 1, 15, 1, 17),
    ('Summer sizing days', 7, 15, 7, 17),
)

# Meters de los outputs de los tests (consumo de los sistemas VRF que añade accim)
METERS = ['Heating:Electricity', 'Cooling:Electricity']

# Rangos (tuplas) del modelo custom ('accim custom model'): los muestreos de rangos (LHS, Sobol, Morris, factorial)
# solo admiten rangos, que el modelo predefinido no admite (solo listas de opciones). Los demás coeficientes toman
# los valores por defecto del modelo custom, con los que las temperaturas de consigna son válidas.
CUSTOM_RANGES = {'custom_slope': (0.2, 0.4), 'custom_intercept': (15.0, 20.0)}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

def prepare_buildings(idf_list, reduce_runtime=True, sizing=True):
    """
    Carga IDFs usando besos y aplica reduce_runtime para acelerar simulaciones.
    Con sizing=True activa el dimensionado, que necesitan los sistemas VRF de accim (ver enable_sizing).
    """
    buildings = []
    for idf_path in idf_list:
        building = ef.get_building(idf_path)
        if reduce_runtime:
            begin_month, begin_day, end_month, end_day = RUN_PERIOD
            accim.utils.reduce_runtime(
                idf_object=building,
                timesteps=TIMESTEPS,
                runperiod_begin_month=begin_month,
                runperiod_begin_day_of_month=begin_day,
                runperiod_end_month=end_month,
                runperiod_end_day_of_month=end_day
            )
        if sizing:
            enable_sizing(building)
        buildings.append(building)
    return buildings

def enable_sizing(building):
    """
    Activa los cálculos de dimensionado y, si el modelo no tiene periodos de dimensionado, añade dos periodos de
    días del EPW.

    Los IDF de test no tienen periodos de dimensionado y tienen desactivado el dimensionado de zonas. accim activa
    los cálculos de dimensionado de los sistemas VRF (autosize) que añade, pero no añade periodos de dimensionado,
    sin los que EnergyPlus se detiene ("Sizing for Zones has been requested but there are no design environments
    specified"). Los periodos de dimensionado no se simulan, para que los resultados sean solo los del periodo de
    simulación.
    """
    control = building.idfobjects['SimulationControl'][0]
    control.Do_Zone_Sizing_Calculation = 'Yes'
    control.Do_System_Sizing_Calculation = 'Yes'
    control.Do_Plant_Sizing_Calculation = 'Yes'
    control.Run_Simulation_for_Sizing_Periods = 'No'
    control.Run_Simulation_for_Weather_File_Run_Periods = 'Yes'
    sizing_periods = [obj for kind in ('SizingPeriod:DesignDay', 'SizingPeriod:WeatherFileDays',
                                       'SizingPeriod:WeatherFileConditionType')
                      for obj in building.idfobjects[kind]]
    if not sizing_periods:
        for name, begin_month, begin_day, end_month, end_day in SIZING_PERIODS:
            building.newidfobject(
                'SizingPeriod:WeatherFileDays',
                Name=name,
                Begin_Month=begin_month,
                Begin_Day_of_Month=begin_day,
                End_Month=end_month,
                End_Day_of_Month=end_day,
            )
    return building

def set_meter_readers(sim, meters=None):
    """
    Añade los meters al IDF y registra sus lectores (MeterReader de besos), que son los outputs del problema:
    set_problem() los necesita (sin ellos, el objeto no tiene 'sim_outputs').
    """
    meters = list(meters or METERS)
    sim.set_output_meters_to_idf(output_meters=meters, validate=False)
    sim.set_output_readers(
        df_output_meter=pd.DataFrame({'key_name': meters, 'frequency': ['Hourly'] * len(meters)})
    )
    return meters

def latest_output(out_dir, prefix, extension):
    """Ruta del último archivo de resultados <prefix>_<fecha y hora>.<extension> de out_dir."""
    files = sorted(Path(out_dir).glob(f'{prefix}_*.{extension}'))
    assert files, f'No {prefix}_*.{extension} files in {out_dir}'
    return str(files[-1])

def log_test(test_name, status, details=""):
    """Registra resultados de tests con formato claro."""
    symbol = "✓" if status == "PASS" else "✗"
    print(f"\n{symbol} [{test_name}] {status}")
    if details:
        print(f"   {details}")

def print_section(title):
    """Imprime un separador de sección."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")