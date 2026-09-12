# 00_test_setup.py - Configuración común para todos los tests
"""
Setup común y utilidades para testing del módulo parametric_and_optimisation.
Define IDFs, EPWs, funciones auxiliares y configuraciones base.
"""

import os
import sys
from pathlib import Path
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

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

def prepare_buildings(idf_list, reduce_runtime=True):
    """
    Carga IDFs usando besos y aplica reduce_runtime para acelerar simulaciones.
    """
    buildings = []
    for idf_path in idf_list:
        building = ef.get_building(idf_path)
        if reduce_runtime:
            accim.utils.reduce_runtime(
                idf_object=building,
                runperiod_begin_month=6,
                runperiod_begin_day_of_month=1,
                runperiod_end_month=7,
                runperiod_end_day_of_month=31
            )
        buildings.append(building)
    return buildings

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