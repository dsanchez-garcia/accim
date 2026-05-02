# AGENTS.md - AI Coding Agent Guidelines for accim

## Project Overview
accim is a Python library (v0.7.8) that transforms EnergyPlus building energy models from fixed PMV-based setpoints to adaptive thermal comfort setpoints. It implements the Adaptive Comfort Control Implementation Script (ACCIS) using EnergyPlus EMS (Energy Management System) to dynamically adjust HVAC setpoints based on outdoor conditions and comfort standards.

## Architecture
- **Core Module**: `accim/sim/` - Contains IDF modification logic, EMS script generation, and comfort model implementations
- **Optimization**: `accim/parametric_and_optimisation/` - Uses besos/platypus for parametric studies and optimization
- **Simulation Runner**: `accim/run/` - **OUTDATED**: Interfaces with EnergyPlus for running simulations (likely to cause errors; use EnergyPlus directly)
- **Data Analysis**: `accim/data/` and analysis functions - **OUTDATED**: Processes simulation outputs using pandas/matplotlib/seaborn (likely to cause errors; use custom pandas/matplotlib scripts)
- **Utilities**: `accim/utils.py` - Helper functions for file operations and data manipulation

## Key Workflows

### 1. IDF Modification
```python
from accim.sim import accis
accis.addAccis(
    ScriptType='vrf_mm',  # 'vrf_ac', 'vrf_mm', 'ex_ac', 'ex_mm'
    ComfStand=[0, 1, 2],  # Comfort standards (0=ESP CTE, 1=EN16798, etc.)
    HVACmode=[0, 2],      # 0=AC, 1=NV, 2=MM
    Output_type='standard',
    Output_freqs=['hourly', 'runperiod']
)
```
- Processes all .idf files in current directory
- Adds EMS programs for adaptive setpoints
- Generates multiple output IDFs based on parameter combinations

### 2. Running Simulations
**Note**: `accim/run/` is outdated and may cause errors. Use EnergyPlus directly:
```bash
energyplus -w weather.epw -p output_prefix -d output_dir modified.idf
```
- Runs EnergyPlus on modified IDFs
- Handles weather files (.epw) and output processing

### 3. Data Analysis
**Note**: `accim/data/` is outdated and may cause errors. Use custom pandas/matplotlib scripts:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load ESO or CSV outputs
df = pd.read_csv('eplusout.csv')
# Custom analysis code here
```
- Aggregates EnergyPlus .eso outputs
- Generates plots and summary tables

### 4. Parametric Optimization
```python
from accim.parametric_and_optimisation.main import OptimParamSimulation

parametric = OptimParamSimulation(
    buildings=building,  # besos.IDF_class instance
    epws=['weather.epw'],
    parameters_type='accim predefined model'
)
parametric.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
parametric.run_parametric_simulation()
```
- Uses besos for multi-objective optimization

## Project-Specific Conventions

### Comfort Standards
- **0**: ESP CTE (Spain)
- **1**: INT EN16798
- **2**: INT ASHRAE55
- **3**: JPN Rijal
- **13**: AUS Williamson
- **14**: AUS DeDear
- **15**: BRA Rupp NV
- **16**: BRA Rupp AC
- Full list in `accim/lists.py`

### Script Types
- `vrf_ac`: VRF system, full AC mode
- `vrf_mm`: VRF system, mixed-mode
- `ex_ac`: Existing HVAC, full AC
- `ex_mm`: Existing HVAC, mixed-mode

### Output Types
- `simplified`: Basic comfort outputs
- `standard`: Standard set (default)
- `detailed`: All possible outputs
- `custom`: User-defined via dataframe

### File Naming
- Modified IDFs: `{original}_ComfStand_{X}_CAT_{Y}_ComfMod_{Z}_HVACmode_{W}_VentCtrl_{V}_VSToffset_{U}_MinOToffset_{T}_MaxWindSpeed_{S}_ASTtol_{R}_{suffix}.idf`
- Outputs follow EnergyPlus conventions with prefixes

## Dependencies & Integration

### Required Libraries
- `eppy`: IDF file manipulation
- `besos`: Building optimization framework
- `pandas`, `numpy`, `matplotlib`, `seaborn`: Data analysis
- `SALib`: Sensitivity analysis
- `scikit-learn`: Machine learning utilities

### External Tools
- **EnergyPlus** (9.1-25.1): Core simulation engine
- **Weather Files** (.epw): Required for simulations
- **IDD Modification**: Library modifies EnergyPlus IDD file for extended EMS capabilities (handled automatically)

### Data Flow
1. Input IDF + EPW → `addAccis()` → Modified IDF with EMS
2. Modified IDF + EPW → EnergyPlus → .eso/.csv outputs
3. Outputs → `Table()` → Processed DataFrames → Plots/Tables

## Development Workflow

### Building & Testing
- `python setup.py develop` for development install
- Test scripts in root: `test_*.py`
- Sample notebooks in `accim/sample_files/jupyter_notebooks/`

### Documentation
- Sphinx-based docs in `docs/`
- Build with `docs/make.bat html` (Windows)
- Source in `docs/source/`

### Key Files for Reference
- `accim/sim/accis.py`: Main `addAccis` class
- `accim/sim/accim_Main.py`: Core modification logic
- `accim/lists.py`: Comfort standard definitions
- `accim/sample_files/`: Example IDFs and notebooks
- `verification-hourly.py`: Output verification script

## Common Patterns

### EMS Implementation
- Uses EnergyPlus EMS for runtime setpoint adjustment
- Programs named `ACCIS_Comfort_Temperature_*`
- Sensors for outdoor temperature, occupancy
- Actuators for thermostat setpoints

### Parameter Combinations
- Generates combinatorial outputs (e.g., 3 ComfStand × 2 HVACmode = 6 IDFs)
- Use `confirmGen=False` for automated processing

### Error Handling
- Validates EnergyPlus version compatibility
- Checks for required IDF objects (Thermostats, Schedules)
- Provides verbose mode for debugging

### Performance Considerations
- EMS scripts add computational overhead
- Large parametric runs may require HPC
- Output frequency affects file sizes significantly
