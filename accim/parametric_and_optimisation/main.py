import os
import re
import json
import glob as pyglob
from typing import Literal, List, Union, Optional, Any
import warnings
import functools
import accim
import numpy as np
import pandas as pd
import besos
from besos import sampling
from besos.evaluator import EvaluatorEP
import besos.optimizer as optimizer
from besos.parameters import RangeParameter, CategoryParameter
from besos.problem import EPProblem
from besos.objectives import VariableReader, MeterReader
from besos import IDF_class
from accim.utils import print_available_outputs_mod, modify_timesteps, set_occupancy_to_always, remove_accents_in_idf, reduce_runtime, read_eso_using_readvarseso
from accim.parametric_and_optimisation.utils import expand_to_hourly_dataframe, identify_hourly_columns
import accim.sim.accis_single_idf_funcs as accis
import accim.sim.apmv_setpoints as apmv
import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf_accim
import accim.parametric_and_optimisation.funcs_for_besos.param_apmv as bf_apmv
import accim.parametric_and_optimisation.parameters as params
from accim.parametric_and_optimisation.analysis import AnalysisMixin
from accim.parametric_and_optimisation.plotting import PlottingMixin
from accim.parametric_and_optimisation.patches import GlobalAllCapsDict, _patched_eval_func, _patched_to_platypus, _ensure_run_energyplus_copies_in_idf
import accim.parametric_and_optimisation.params_dicts as params_dicts
allowed_output_freqs = Literal['timestep', 'hourly', 'daily', 'monthly', 'runperiod']

def get_rdd_file_as_df():
    """
    Returns the .rdd file from the test simulation as a pandas DataFrame

    :return: a pandas DataFrame containing the .rdd file from the test simulation
    """
    rdd_df = pd.read_csv(filepath_or_buffer='available_outputs/eplusout.rdd', sep=',|;', skiprows=2, names=['object', 'key_value', 'variable_name', 'frequency', 'units'], engine='python')
    return rdd_df

def parse_mtd_file() -> list[Union[dict[str, Union[str, None, list[str]]], dict[str, Union[str, None, list[str]]]]]:
    """
    Returns a list of the objects in the .mtd file from the test simulation.

    :return: a list of the objects in the .mtd file from the test simulation
    """
    meter_list = []
    with open('available_outputs/eplusout.mtd', 'r') as file:
        lines = file.readlines()
    (meter_id, description) = (None, None)
    on_meters = []
    for line in lines:
        line = line.strip()
        if line.startswith('Meters for'):
            if meter_id is not None:
                meter_list.append({'meter_id': meter_id, 'description': description, 'on_meters': on_meters})
            match = re.match('Meters for (\\d+),(.+)', line)
            if match:
                meter_id = match.group(1)
                description = match.group(2)
                on_meters = []
        elif line.startswith('OnMeter'):
            on_meters.append(line.split('=')[1].strip())
    if meter_id is not None:
        meter_list.append({'meter_id': meter_id, 'description': description, 'on_meters': on_meters})
    return meter_list

def get_mdd_file_as_df():
    """
    Returns the .mdd file from the test simulation as a pandas DataFrame

    :return: a pandas DataFrame containing the .mdd file from the test simulation
    """
    mdd_df = pd.read_csv(filepath_or_buffer='available_outputs/eplusout.mdd', sep=',|;', skiprows=2, names=['object', 'meter_name', 'frequency', 'units'], engine='python')
    return mdd_df

def _run_single_evaluation_worker(
    idf_path: str,
    epw: str,
    epwname: str,
    idf_basename: str,
    out_dir: str,
    problem_names_inputs: list,
    problem_names_outputs: list,
    row_dict: dict,
    keep_dirs: bool,
    keep_input: bool
) -> dict:
    import warnings
    warnings.filterwarnings('ignore')
    from besos.evaluator import EvaluatorEP
    from besos.problem import EPProblem
    from besos.parameters import Parameter

    _ensure_run_energyplus_copies_in_idf()

    print(f"[WORKER] Loading IDF: {idf_path}")
    from accim.utils import get_building
    try:
        b = get_building(idf_path)
    except Exception as e:
        print(f"[WORKER] Crash while loading {idf_path}: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Ensure each sampled value is really written into the IDF/EMS before the run.
    # In multiprocessing mode we reconstruct a lightweight EPProblem in the worker;
    # applying setters here guarantees custom ACCIS parameters are not lost.
    available_setters = {k.lower(): v for (k, v) in params_dicts.all_params.items()}
    for (param_name, param_value) in row_dict.items():
        setter = available_setters.get(str(param_name).lower())
        if setter is not None:
            setter(b, param_value)
        
    dummy_inputs = [Parameter(name=n) for n in problem_names_inputs]
    prob = EPProblem(inputs=dummy_inputs, outputs=problem_names_outputs)
    
    evaluator = EvaluatorEP(problem=prob, building=b, epw=epw, out_dir=out_dir)
    row_values = [row_dict[n] for n in problem_names_inputs]
    
    result = evaluator(row_values, keep_dirs=keep_dirs)
    if not isinstance(result, (list, tuple)):
        result = (result,)
        
    result_dict = {
        problem_names_outputs[idx]: result[idx]
        for idx in range(len(problem_names_outputs))
    }
    
    if keep_dirs and len(result) > len(problem_names_outputs):
        result_dict['output_dir'] = result[-1]
        
    if keep_input:
        result_dict.update(row_dict)
        
    result_dict['epw'] = epwname
    result_dict['idf'] = idf_basename
    
    return result_dict

class SimulationBase(AnalysisMixin, PlottingMixin):
    """
    Base class for parametric simulations and multi-objective optimization.

    Contains shared functionality for managing buildings, EPWs, parameters, outputs,
    and IDF backup operations. Subclasses should override simulation-specific methods.

    .. versionadded:: 0.8.0
        Split from OptimParamSimulation for better code organization and reduced cognitive load.
    """

    def __init__(self, buildings: Union[Any, List]=None, epws: list=None, parameters_type: Literal['accim custom model', 'accim predefined model', 'apmv setpoints', None]=None, output_type: Literal['standard', 'custom', 'detailed', 'simplified']='standard', output_keep_existing: bool=False, output_freqs: List[allowed_output_freqs]=['hourly'], ScriptType: Literal['vrf_mm', 'vrf_ac', 'ex_ac']='vrf_mm', SupplyAirTempInputMethod: Literal['temperature difference', 'supply air temperature']='temperature difference', make_averages: bool=False, debugging: bool=False, verbosemode: bool=True, bypass_addAccis: bool=False, **kwargs):
        """
        Initialize the simulation base instance.

        :param buildings: the besos.IDF_class returned from method get_building(idfpath)
        :param epws: a list of .epw filenames
        :param parameters_type: to specify the type of parameters that should be used
        :param output_type: to specify the outputs that are going to be requested
        :param output_keep_existing: to keep or remove existing outputs
        :param output_freqs: output frequency specification
        :param ScriptType: 'vrf_mm', 'vrf_ac', or 'ex_ac'
        :param SupplyAirTempInputMethod: supply air temperature input method
        :param make_averages: to make average outputs
        :param debugging: True to generate the .EDD file
        :param bypass_addAccis: True to skip the internal addAccis execution
        """
        if buildings is None and 'building' in kwargs:
            buildings = kwargs['building']
            
        is_accim_predef_model = False
        is_accim_custom_model = False
        is_apmv_setpoints = False
        if parameters_type == 'accim custom model':
            temp_ctrl = 'temperature'
            is_accim_custom_model = True
        elif parameters_type == 'accim predefined model':
            temp_ctrl = 'temperature'
            is_accim_predef_model = True
        elif parameters_type == 'apmv setpoints':
            temp_ctrl = 'PMV'
            is_apmv_setpoints = True
        elif parameters_type is None:
            temp_ctrl = None
        else:
            raise KeyError(f'String {parameters_type} entered in argument parametric_simulation_type is not supported. Valid strings are: "accim custom model", "accim predefined model" or "apmv setpoints".')
        allowed_ScriptType = ['vrf_mm', 'vrf_ac', 'ex_ac']
        if ScriptType not in allowed_ScriptType:
            raise ValueError(f'Invalid ScriptType: {ScriptType}. Allowed values are: {allowed_ScriptType}')
        allowed_SupplyAirTempInputMethod = ['temperature difference', 'supply air temperature']
        if SupplyAirTempInputMethod not in allowed_SupplyAirTempInputMethod:
            raise ValueError(f'Invalid ScriptType: {SupplyAirTempInputMethod}. Allowed values are: {allowed_SupplyAirTempInputMethod}')
        allowed_output_type = ['standard', 'custom', 'detailed', 'simplified']
        if output_type not in allowed_output_type:
            raise ValueError(f'Invalid output_type: {output_type}. Allowed values are: {allowed_output_type}')
        if is_accim_custom_model or is_accim_predef_model:
            self.ScriptType = ScriptType
            self.temp_ctrl = temp_ctrl
            self.SupplyAirTempInputMethod = SupplyAirTempInputMethod
            self.output_keep_existing = output_keep_existing
            self.output_type = output_type
            self.make_averages = make_averages
            if not bypass_addAccis:
                if isinstance(buildings, list):
                    for b in buildings:
                        accis.addAccis(idf=b, ScriptType=ScriptType, SupplyAirTempInputMethod=SupplyAirTempInputMethod, Output_keep_existing=output_keep_existing, Output_type=output_type, Output_freqs=output_freqs, TempCtrl=temp_ctrl, make_averages=make_averages, debugging=debugging, verboseMode=verbosemode)
                else:
                    accis.addAccis(idf=buildings, ScriptType=ScriptType, SupplyAirTempInputMethod=SupplyAirTempInputMethod, Output_keep_existing=output_keep_existing, Output_type=output_type, Output_freqs=output_freqs, TempCtrl=temp_ctrl, make_averages=make_averages, debugging=debugging, verboseMode=verbosemode)
        elif is_apmv_setpoints:
            if not bypass_addAccis:
                if isinstance(buildings, list):
                    for b in buildings:
                        apmv.apply_apmv_setpoints(building=b, outputs_freq=output_freqs)
                else:
                    apmv.apply_apmv_setpoints(building=buildings, outputs_freq=output_freqs)
            print('Arguments output_type, output_keep_existing, ScriptType, and SupplyAirTempInputMethod are only used in accim predefined and custom models, therefore these will not have any effect in this case.')
        elif parameters_type is None:
            self.ScriptType = None
            self.temp_ctrl = None
            self.SupplyAirTempInputMethod = None
            self.output_keep_existing = None
            self.output_type = None
            self.make_averages = None
        self.building = buildings[0] if isinstance(buildings, list) and len(buildings) > 0 else buildings
        self.buildings = buildings if isinstance(buildings, list) else ([buildings] if buildings is not None else [])
        self.epws = epws if isinstance(epws, list) else ([epws] if epws is not None else [])
        self.output_freqs = output_freqs
        self.parameters_type = parameters_type
        self.is_accim_custom_model = is_accim_custom_model
        self.is_accim_predef_model = is_accim_predef_model
        self.is_apmv_setpoints = is_apmv_setpoints
        self.bypass_addAccis = bypass_addAccis
        self.last_run_type = None
        # Save an initial IDF backup right after addAccis/apply_apmv_setpoints so the
        # modified IDF (with EMS scripts and outputs already injected) is always
        # recoverable, even if run_parametric_simulation / run_optimisation are not called yet.
        self.idf_backup_path: str = None
        # NOTE: IDF backup is deferred until run_parametric_simulation /
        # run_optimisation are called, so the backup is always written to the
        # results folder (out_dir) rather than creating a separate
        # 'accim_idf_backups' directory in the working directory.

    # ------------------------------------------------------------------
    # IDF backup helpers
    # ------------------------------------------------------------------

    def _save_idf_backup(self, label: str = '', out_dir: str = None) -> str:
        """
        Saves a copy of ``self.buildings`` to disk as an IDF file and stores
        the path in ``self.idf_backup_path``.

        :param label: optional suffix to embed in the filename.
        :param out_dir: directory where the backup should be saved.  Must be
            provided; backups are always written inside the simulation results
            folder so that no extra ``accim_idf_backups`` directory is created
            in the working directory.
        :return: absolute path to the saved IDF.
        """
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if out_dir is None:
            raise ValueError(
                "'out_dir' must be specified when saving an IDF backup. "
                "Pass the simulation results directory (e.g. 'param_results' "
                "or 'optim_results') so the backup lands there instead of "
                "creating a separate 'accim_idf_backups' folder."
            )
        backup_dir = out_dir
        os.makedirs(backup_dir, exist_ok=True)
        suffix = f'_{label}' if label else ''
        self.idf_backup_path = []
        for i, b in enumerate(self.buildings):
            idf_basename = os.path.basename(b.idfname).replace('.idf', '') if hasattr(b, 'idfname') and b.idfname else f'unknown_idf_{i}'
            filename = f'accim_idf_backup_{idf_basename}{suffix}_{timestamp}.idf'
            backup_path = os.path.join(backup_dir, filename)
            b.savecopy(backup_path)
            self.idf_backup_path.append(os.path.abspath(backup_path))
        if len(self.idf_backup_path) == 1:
            self.idf_backup_path = self.idf_backup_path[0]
        return self.idf_backup_path

    def get_output_var_df_from_idf(self) -> pd.DataFrame:
        """
        Gets a pandas DataFrame which contains the Output:Variable objects from the idf.
        Therefore, it may contain wildcards such as '*', which means the variable is requested
        for all zones.

        :return: a pandas DataFrame which contains the Output:Variable objects from the idf
        """
        if self.is_accim_custom_model or self.is_accim_predef_model:
            output_variable_df = accis.gen_outputs_df(idf=self.building, ScriptType=self.ScriptType, Output_keep_existing=self.output_keep_existing, Output_type=self.output_type, Output_freqs=self.output_freqs, TempCtrl=self.temp_ctrl, verboseMode=False)
        else:
            output_var_dict = {'key_value': [i.Key_Value for i in self.building.idfobjects['Output:Variable']], 'variable_name': [i.Variable_Name for i in self.building.idfobjects['Output:Variable']], 'frequency': [i.Reporting_Frequency for i in self.building.idfobjects['Output:Variable']], 'schedule_name': [i.Schedule_Name for i in self.building.idfobjects['Output:Variable']]}
            output_variable_df = pd.DataFrame.from_dict(output_var_dict)
        return output_variable_df

    def _get_idf_identifier(self, building: Any, index: int = None) -> str:
        if hasattr(building, 'idfname') and building.idfname:
            return os.path.basename(building.idfname).replace('.idf', '')
        if index is not None:
            return f'unknown_idf_{index}'
        return 'unknown_idf'

    def _get_buildings_by_idf(self) -> dict:
        buildings_by_idf = {}
        for (idx, building) in enumerate(self.buildings):
            idf_name = self._get_idf_identifier(building=building, index=idx)
            if idf_name in buildings_by_idf:
                raise ValueError(
                    f'Duplicate IDF identifier detected: {idf_name}. '
                    f'Please provide buildings with unique file names.'
                )
            buildings_by_idf[idf_name] = building
        return buildings_by_idf

    def _get_problem_input_names(self) -> list:
        if hasattr(self, 'problem') and hasattr(self.problem, 'names'):
            return list(self.problem.names('inputs'))
        if hasattr(self, 'parameters_list'):
            return [parameter.name for parameter in self.parameters_list]
        return []

    def _get_external_input_names(self) -> list:
        return ['idf'] if len(self.buildings) > 1 else []

    def _get_all_input_names(self) -> list:
        return self._get_problem_input_names() + self._get_external_input_names()

    def _prepare_dataframe_for_buildings(self, df: pd.DataFrame, epws: list = None) -> dict:
        if df is None:
            raise ValueError('Argument df must be a pandas DataFrame.')
        if not isinstance(df, pd.DataFrame):
            raise TypeError('Argument df must be a pandas DataFrame.')

        prepared_df = df.copy()
        buildings_by_idf = self._get_buildings_by_idf()
        input_names = self._get_problem_input_names()
        allowed_external_columns = self._get_external_input_names()
        if epws is not None:
            allowed_external_columns = allowed_external_columns + ['epw']

        if len(self.buildings) > 1:
            if 'idf' in prepared_df.columns:
                unknown_idfs = sorted(set(prepared_df['idf'].dropna().astype(str)) - set(buildings_by_idf.keys()))
                if unknown_idfs:
                    raise ValueError(
                        f'The following IDFs in df are not part of this OptimParamSimulation instance: {unknown_idfs}'
                    )
                prepared_df['idf'] = prepared_df['idf'].astype(str)
            else:
                if len(prepared_df) == 0:
                    prepared_df = pd.DataFrame({'idf': list(buildings_by_idf.keys())})
                else:
                    prepared_df = pd.concat(
                        [prepared_df.assign(idf=idf_name) for idf_name in buildings_by_idf.keys()],
                        ignore_index=True,
                    )
        elif 'idf' in prepared_df.columns:
            prepared_df = prepared_df.drop(columns=['idf'])

        if 'epw' in prepared_df.columns:
            allowed_epws = {str(epw) for epw in epws or []}
            unknown_epws = sorted(set(prepared_df['epw'].dropna().astype(str)) - allowed_epws)
            if unknown_epws:
                raise ValueError(
                    f'The following EPWs in df are not part of the epws argument: {unknown_epws}'
                )
            prepared_df['epw'] = prepared_df['epw'].astype(str)

        missing_columns = [column for column in input_names if column not in prepared_df.columns]
        if missing_columns:
            raise ValueError(f'The following input columns are missing in df: {missing_columns}')

        extra_columns = [column for column in prepared_df.columns if column not in input_names + allowed_external_columns]
        if extra_columns:
            warnings.warn(
                f'The following columns in df are not used by the evaluator and will be ignored: {extra_columns}',
                UserWarning,
            )

        grouped = {}
        if len(self.buildings) > 1:
            for idf_name, subset in prepared_df.groupby('idf', sort=False):
                grouped[idf_name] = subset.reset_index(drop=True)
        else:
            grouped[self._get_idf_identifier(self.building, 0)] = prepared_df.reset_index(drop=True)

        return grouped

    def get_output_meter_df_from_idf(self) -> pd.DataFrame:
        """
        Gets a pandas DataFrame which contains the Output:Meter objects from the idf.

        :return: a pandas DataFrame which contains the Output:Meter objects from the idf
        """
        output_meter_dict = {'key_name': [i.Key_Name for i in self.building.idfobjects['Output:Meter']], 'frequency': [i.Reporting_Frequency for i in self.building.idfobjects['Output:Meter']]}
        output_meter_df = pd.DataFrame.from_dict(output_meter_dict)
        return output_meter_df

    def set_output_var_df_to_idf(self, outputs_df: pd.DataFrame=None):
        """
        Keeps the Output:Variable objects contained in the input pandas DataFrame and removes
        all others. This is important to save space if thousands of simulations with heavy outputs
        are run.

        :type outputs_df: pd.DataFrame
        :param outputs_df: the DataFrame containing Output:Variable objects to be kept
        :return:
        """
        if self.is_accim_custom_model or self.is_accim_predef_model:
            for b in self.buildings:
                accis.addAccis(idf=b, ScriptType=self.ScriptType, SupplyAirTempInputMethod=self.SupplyAirTempInputMethod, Output_keep_existing=self.output_keep_existing, Output_type=self.output_type, Output_take_dataframe=outputs_df, Output_freqs=self.output_freqs, TempCtrl=self.temp_ctrl, make_averages=self.make_averages, verboseMode=False)
        else:
            for b in self.buildings:
                alloutputs = [output for output in b.idfobjects['Output:Variable']]
                for i in alloutputs:
                    b.removeidfobject(i)
                for i in outputs_df.index:
                    b.newidfobject('Output:Variable', Key_Value=outputs_df.loc[i, 'key_value'], Variable_Name=outputs_df.loc[i, 'variable_name'], Reporting_Frequency=outputs_df.loc[i, 'frequency'].capitalize(), Schedule_Name=outputs_df.loc[i, 'schedule_name'])

    def set_output_met_objects_to_idf(self, output_meters: list):
        """
        Adds the Output:Meter objects from the output_meters argument.

        :type output_meters: list
        :param output_meters: a list containing Output:Meter objects to be added
        :return:
        """
        for b in self.buildings:
            for meter in output_meters:
                for freq in self.output_freqs:
                    b.newidfobject(key='OUTPUT:METER', Key_Name=meter, Reporting_Frequency=freq)

    def get_outputs_df_from_testsim(self, reduce_sim_time: bool=True) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Gets two pandas DataFrames which contain the Output:Variable and Output:Meter objects from a test simulation.
        Therefore, it won't contain wildcards such as '*'.

        :param reduce_sim_time: True to reduce the simulation runtime

        :return: a tuple containing the DataFrames containing Output:Variable and Output:Meter
        """
        building_for_testsim = self.building
        if reduce_sim_time:
            from besos.eppy_funcs import get_building
            self.building.savecopy('temp_reduced_runtime.idf')
            building_for_testsim = get_building('temp_reduced_runtime.idf')
            reduce_runtime(idf_object=building_for_testsim, maximum_figures_in_shadow_overlap_calculations=200, timesteps=2)
            # Agregar período de sizing si no existe (requerido para autosizing de equipos como VRF)
            sizing_periods = building_for_testsim.idfobjects.get('SIZINGPERIOD:WEATHERFILEDAYS', [])
            if len(sizing_periods) == 0:
                # Crear un período de sizing que coincida con el runperiod
                runperiod = building_for_testsim.idfobjects['Runperiod'][0]
                building_for_testsim.newidfobject(
                    'SIZINGPERIOD:WEATHERFILEDAYS',
                    Name='SizingPeriod',
                    Begin_Month=int(runperiod.Begin_Month),
                    Begin_Day_of_Month=int(runperiod.Begin_Day_of_Month),
                    End_Month=int(runperiod.End_Month),
                    End_Day_of_Month=int(runperiod.End_Day_of_Month),
                    Day_of_Week_for_Start_Day='Sunday',
                    Use_Weather_File_Daylight_Saving_Period='Yes',
                    Use_Weather_File_Rain_and_Snow_Indicators='Yes'
                )
        available_outputs = print_available_outputs_mod(building_for_testsim)
        if reduce_sim_time:
            from os import remove
            remove('temp_reduced_runtime.idf')
        df_outputmeters = pd.DataFrame(available_outputs.meterreaderlist, columns=['key_name', 'frequency'])
        df_outputvariables = pd.DataFrame(available_outputs.variablereaderlist, columns=['key_value', 'variable_name', 'frequency'])
        return (df_outputmeters, df_outputvariables)

    def set_outputs_for_simulation(self, df_output_variable: pd.DataFrame=None, df_output_meter: pd.DataFrame=None):
        """
        Sets the outputs for the parametric analysis or optimisation based on the input pandas DataFrames
        for Output:Variable and/or Output:Meter objects. These DataFrames can include columns for the output name
        and the aggregation function (see the 'func' argument of MeterReader and VariableReader classes in besos),
        respectively named 'name' and 'func'. If no 'name' and/or 'func' columns are provided,
        the names will be the variable and meter names, and the hourly values will be summed.

        :param df_output_variable: a pandas DataFrame containing the Output:Variable objects, similar to that one
            returned from method get_outputs_df_from_testsim()
        :param df_output_meter: a pandas DataFrame containing the Output:Meter objects, similar to that one
            returned from method get_outputs_df_from_testsim()
        """
        if df_output_variable is not None:
            df_output_variable['output_name'] = 'temp'
            if 'name' in df_output_variable.columns:
                df_output_variable['output_name'] = df_output_variable['name']
            else:
                df_output_variable['output_name'] = df_output_variable['variable_name']
        if df_output_meter is not None:
            df_output_meter['output_name'] = 'temp'
            if 'name' in df_output_meter.columns:
                df_output_meter['output_name'] = df_output_meter['name']
            else:
                df_output_meter['output_name'] = df_output_meter['key_name']
        objs_meters = []
        if df_output_meter is not None:
            for i in df_output_meter.index:
                if 'func' in [c for c in df_output_meter.columns]:
                    objs_meters.append(MeterReader(key_name=df_output_meter.loc[i, 'key_name'], frequency=df_output_meter.loc[i, 'frequency'], name=df_output_meter.loc[i, 'output_name'], func=df_output_meter.loc[i, 'func']))
                else:
                    objs_meters.append(MeterReader(key_name=df_output_meter.loc[i, 'key_name'], frequency=df_output_meter.loc[i, 'frequency'], name=df_output_meter.loc[i, 'output_name']))
        objs_variables = []
        if df_output_variable is not None:
            for i in df_output_variable.index:
                if 'func' in [c for c in df_output_variable.columns]:
                    objs_variables.append(VariableReader(key_value=df_output_variable.loc[i, 'key_value'], variable_name=df_output_variable.loc[i, 'variable_name'], frequency=df_output_variable.loc[i, 'frequency'], name=df_output_variable.loc[i, 'output_name'], func=df_output_variable.loc[i, 'func']))
                else:
                    objs_variables.append(VariableReader(key_value=df_output_variable.loc[i, 'key_value'], variable_name=df_output_variable.loc[i, 'variable_name'], frequency=df_output_variable.loc[i, 'frequency'], name=df_output_variable.loc[i, 'output_name']))
        self.sim_outputs = objs_meters + objs_variables

    def get_available_parameters(self) -> list:
        """
        Returns a list containing the available parameters depending on the parameters_type argument previously input.

        :return: a list containing the available parameters depending on the parameters_type argument previously input
        """
        if self.is_accim_predef_model:
            available_params = [i for i in params_dicts.accim_predef_model_params.keys()]
        elif self.is_accim_custom_model:
            available_params = [i for i in params_dicts.accim_custom_model_params.keys()]
        elif self.is_apmv_setpoints:
            available_params = [i for i in params_dicts.apmv_setpoints_params.keys()]
        else:
            available_params = []
        return available_params

    def set_parameters(self, accis_params_dict: dict = None, additional_params: list=None, use_dflt_values: bool=True):
        """
        Sets the parameters for the parametric analysis or optimisation.

        :param accis_params_dict: a dictionary containing the parameters names in the keys,
            and in the values, the options or range of values using respectively
            a list or tuple with min and max values.
        :param additional_params: any other additional parameter, as it would be added in besos
        :param HVACmode: only used in accim predefined and custom models; sets the HVACmode argument;
            for more information, refer to addAccis
        :param VentCtrl: only used in accim predefined and custom models; sets the VentCtrl argument;
            for more information, refer to addAccis
        """
        if accis_params_dict is None:
            accis_params_dict = {}
        accis_descriptors_has_options = False
        add_descriptors_has_options = False
        descriptors_has_options = False
        if len(accis_params_dict) > 0 and all([type(v) == list for v in accis_params_dict.values()]):
            accis_descriptors_has_options = True
        if additional_params is not None:
            if all([type(additional_params[i].value_descriptor) == CategoryParameter for i in range(len(additional_params))]):
                add_descriptors_has_options = True
        if accis_descriptors_has_options:
            if additional_params is not None:
                if add_descriptors_has_options:
                    descriptors_has_options = True
            else:
                descriptors_has_options = True
        if descriptors_has_options is True:
            for (k, v) in accis_params_dict.items():
                accis_params_dict[k] = [round(float(i), 2) for i in v]
        accis_descriptors_has_range = False
        add_descriptors_has_range = False
        descriptors_has_range = False
        if len(accis_params_dict) > 0 and all([type(v) == tuple for v in accis_params_dict.values()]):
            accis_descriptors_has_range = True
        if additional_params is not None:
            if all([type(additional_params[i].value_descriptor) == RangeParameter for i in range(len(additional_params))]):
                add_descriptors_has_range = True
        if accis_descriptors_has_range:
            if additional_params is not None:
                if add_descriptors_has_range:
                    descriptors_has_range = True
            else:
                descriptors_has_range = True
        if descriptors_has_options is False and descriptors_has_range is False and additional_params is None and len(accis_params_dict) == 0:
            parameters_list = []
        elif descriptors_has_options is False and descriptors_has_range is False:
            raise TypeError('All Descriptors are not CategoryParameters or RangeParameters.')
        parameters = [k for k in accis_params_dict.keys()]
        available_parameters = self.get_available_parameters()
        not_allowed_parameters = []
        for p in parameters:
            if p not in available_parameters:
                not_allowed_parameters.append(p)
        if len(not_allowed_parameters) > 0 and self.parameters_type is not None:
            raise ValueError(f'The following parameters are not allowed in parameters_type {self.parameters_type}: {not_allowed_parameters}')
        if self.is_accim_custom_model and len(accis_params_dict) > 0:
            bf_accim.modify_ComfStand(self.building, 99)
            bf_accim.modify_ComfMod(self.building, 3)
            bf_accim.modify_CAT(self.building, 80)
            bf_accim.modify_CustAST_m(self.building, 0)
            bf_accim.modify_CustAST_n(self.building, 0)
            bf_accim.modify_CustAST_ASToffset(self.building, 0)
            bf_accim.modify_CustAST_ASTaul(self.building, 0)
            bf_accim.modify_CustAST_ASTall(self.building, 0)
            args = accim.utils.get_accim_args(self.building)
            parameters_to_check = [k for (k, v) in args['CustAST'].items() if 'CustAST_' + k not in parameters and v == 0]
            if 'CustAST_ASToffset' in parameters:
                try:
                    parameters_to_check.remove('AHSToffset')
                    parameters_to_check.remove('ACSToffset')
                except ValueError:
                    pass
            if 'CustAST_ASTall' in parameters:
                try:
                    parameters_to_check.remove('AHSTall')
                    parameters_to_check.remove('ACSTall')
                except ValueError:
                    pass
            if 'CustAST_ASTaul' in parameters:
                try:
                    parameters_to_check.remove('AHSTaul')
                    parameters_to_check.remove('ACSTaul')
                except ValueError:
                    pass
            parameters_to_be_defined = []
            for p in parameters_to_check:
                if args['CustAST'][p] == 0:
                    parameters_to_be_defined.append(p)
            if len(parameters_to_be_defined) > 0:
                print(f'The following parameters are not included in the parameters to be set, and have not been defined yet (i.e. the value is 0): {parameters_to_be_defined}')
                dflt_values = {'m': 0.31, 'n': 17.8, 'ACSToffset': 3.5, 'AHSToffset': -3.5, 'ACSTaul': 33.5, 'ACSTall': 10, 'AHSTaul': 33.5, 'AHSTall': 10}
                if use_dflt_values:
                    print('Default values will be set for these parameters. The default values are:')
                    for p in parameters_to_be_defined:
                        print(f'{p}: {dflt_values[p]}')
                    if 'm' in parameters_to_be_defined:
                        bf_accim.modify_CustAST_m(self.building, dflt_values['m'])
                    if 'n' in parameters_to_be_defined:
                        bf_accim.modify_CustAST_n(self.building, dflt_values['n'])
                    if 'ACSToffset' in parameters_to_be_defined:
                        bf_accim.modify_CustAST_ACSToffset(self.building, dflt_values['ACSToffset'])
                    if 'AHSToffset' in parameters_to_be_defined:
                        bf_accim.modify_CustAST_AHSToffset(self.building, dflt_values['AHSToffset'])
                    if 'ACSTaul' in parameters_to_be_defined:
                        bf_accim.modify_CustAST_ACSTaul(self.building, dflt_values['ACSTaul'])
                    if 'ACSTall' in parameters_to_be_defined:
                        bf_accim.modify_CustAST_ACSTall(self.building, dflt_values['ACSTall'])
                    if 'AHSTaul' in parameters_to_be_defined:
                        bf_accim.modify_CustAST_AHSTaul(self.building, dflt_values['AHSTaul'])
                    if 'AHSTall' in parameters_to_be_defined:
                        bf_accim.modify_CustAST_AHSTall(self.building, dflt_values['AHSTall'])
                else:
                    print('If you want, default values can be set for these parameters. The default values are:')
                    for p in parameters_to_be_defined:
                        print(f'{p}: {dflt_values[p]}')
                    user_decision = input('Do you want to continue with default values? [y/n]: ')
                    if user_decision.lower() == 'y' or user_decision == '':
                        if 'm' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_m(self.building, dflt_values['m'])
                        if 'n' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_n(self.building, dflt_values['n'])
                        if 'ACSToffset' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSToffset(self.building, dflt_values['ACSToffset'])
                        if 'AHSToffset' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSToffset(self.building, dflt_values['AHSToffset'])
                        if 'ACSTaul' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSTaul(self.building, dflt_values['ACSTaul'])
                        if 'ACSTall' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSTall(self.building, dflt_values['ACSTall'])
                        if 'AHSTaul' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSTaul(self.building, dflt_values['AHSTaul'])
                        if 'AHSTall' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSTall(self.building, dflt_values['AHSTall'])
                    else:
                        user_values = {}
                        for p in parameters_to_be_defined:
                            value = float(input(f'Enter the value for argument {p}: '))
                            user_values.update({p: value})
                        if 'm' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_m(self.building, user_values['m'])
                        if 'n' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_n(self.building, user_values['n'])
                        if 'ACSToffset' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSToffset(self.building, user_values['ACSToffset'])
                        if 'AHSToffset' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSToffset(self.building, user_values['AHSToffset'])
                        if 'ACSTaul' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSTaul(self.building, user_values['ACSTaul'])
                        if 'ACSTall' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_ACSTall(self.building, user_values['ACSTall'])
                        if 'AHSTaul' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSTaul(self.building, user_values['AHSTaul'])
                        if 'AHSTall' in parameters_to_be_defined:
                            bf_accim.modify_CustAST_AHSTall(self.building, user_values['AHSTall'])
        elif self.is_accim_predef_model and len(accis_params_dict) > 0:
            if descriptors_has_range:
                raise KeyError('Accim predefined models approach is only valid with options descriptors.')
        if not (descriptors_has_options or descriptors_has_range):
            parameters_list = []
        else:
            parameters_list = [params.accis_parameter(k, v) for (k, v) in accis_params_dict.items()]
        if additional_params is not None:
            parameters_list.extend(additional_params)
        self.parameters_list = parameters_list
        self.descriptors_has_options = descriptors_has_options
        self.descriptors_has_range = descriptors_has_range

    def set_problem(self, minimize_outputs: list=None, constraints: list=None, constraint_bounds: list=None, **kwargs):
        """
        Sets the besos EPProblem class instance, using for inputs the parameters previously set in the set_parameters
        method, and for outputs, those set using the set_outputs_for_simulation method.

        :param minimize_outputs: only used in optimisation; a list containing booleans to specify if the outputs must
            be minimized (True), maximized (False), or just show the output (None).
        :param constraints: only used in optimisation;
            a list containing the Output:Meter key names to be considered as constraints
        :param constraint_bounds: only used in optimisation;
            a list containing the logical expressions for the constraints
        """
        problem = EPProblem(inputs=self.parameters_list, outputs=self.sim_outputs, minimize_outputs=minimize_outputs, constraints=constraints, constraint_bounds=constraint_bounds, **kwargs)
        self.problem = problem

    def sampling_full_set(self):
        """
        Combines all values from all parameters and saves it into a pandas DataFrame, stored in an internal variable
        named parameters_values_df.
        """
        from accim.parametric_and_optimisation.utils import make_all_combinations
        
        has_params = hasattr(self, 'parameters_list') and len(self.parameters_list) > 0
        if has_params and not getattr(self, 'descriptors_has_options', False):
            raise KeyError('sampling_full_set method can only be used with option (i.e. category) descriptors.')
            
        parameters_values = {}
        if has_params:
            for p in self.parameters_list:
                parameters_values.update({p.value_descriptors[0].name: p.value_descriptors[0].options})
                
        if hasattr(self, 'buildings') and len(self.buildings) > 0:
            idf_names = [self._get_idf_identifier(b, i) for i, b in enumerate(self.buildings)]
            parameters_values['idf'] = idf_names
            
        if hasattr(self, 'epws') and len(self.epws) > 0:
            parameters_values['epw'] = self.epws
            
        if not parameters_values:
            parameters_values_df = pd.DataFrame()
        else:
            parameters_values_df = make_all_combinations(parameters_values)
            if self.is_accim_predef_model:
                parameters_values_df = bf_accim.drop_invalid_param_combinations(parameters_values_df)
        self.parameters_values_df = parameters_values_df

    def sampling_custom(self, custom_plan: Union[List[dict], dict, pd.DataFrame]):
        """
        Sets a custom simulation plan.
        :param custom_plan: A pandas DataFrame, a list of dictionaries, or a dictionary mapping IDFs to EPWs.
            Example list: [{'idf': 'Building_A', 'epw': 'seville.epw'}, {'idf': 'Building_B', 'epw': 'madrid.epw'}]
            Example dict: {'Building_A': 'seville.epw', 'Building_B': ['madrid_2024.epw', 'madrid_2025.epw']}
        """
        import pandas as pd
        if isinstance(custom_plan, pd.DataFrame):
            self.parameters_values_df = custom_plan.copy()
        elif isinstance(custom_plan, list):
            self.parameters_values_df = pd.DataFrame(custom_plan)
        elif isinstance(custom_plan, dict):
            rows = []
            for idf, epws in custom_plan.items():
                if isinstance(epws, str):
                    epws = [epws]
                for epw in epws:
                    rows.append({'idf': idf, 'epw': epw})
            self.parameters_values_df = pd.DataFrame(rows)
        else:
            raise TypeError('custom_plan must be a pandas DataFrame, a list of dicts, or a dict.')

    def _expand_samples_with_buildings_and_epws(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Expands a parameter samples DataFrame with cartesian products for IDFs and EPWs.
        """
        if df is None or df.empty:
            return df
            
        dfs_to_concat = []
        idf_names = [self._get_idf_identifier(b, i) for i, b in enumerate(self.buildings)] if hasattr(self, 'buildings') and self.buildings else [None]
        epw_names = self.epws if hasattr(self, 'epws') and self.epws else [None]
        
        for idf_name in idf_names:
            for epw_name in epw_names:
                temp_df = df.copy()
                if idf_name is not None and len(self.buildings) > 1:
                    temp_df['idf'] = idf_name
                if epw_name is not None and len(self.epws) > 0:
                    temp_df['epw'] = epw_name
                dfs_to_concat.append(temp_df)
                
        if dfs_to_concat:
            return pd.concat(dfs_to_concat, ignore_index=True)
        return df

    def sampling_full_factorial(self, level: int):
        """
        Split the range of every parameter in the number of parts specified in argument level,
        and saves it into a pandas DataFrame, stored in an internal variable named parameters_values_df.
        For more information, see besos.sampling.dist_sampler and besos.sampling.full_factorial

        :param level: an integer; represents the number of parts to split each parameter's range
        """
        if self.descriptors_has_range:
            parameters_values_df = sampling.dist_sampler(sampling.full_factorial, self.problem, num_samples=2, level=level)
        else:
            raise KeyError('sampling_full_factorial method can only be used with range descriptors.')
        self.parameters_values_df = self._expand_samples_with_buildings_and_epws(parameters_values_df)

    def sampling_lhs(self, num_samples: int):
        """
        Uses Latin Hypercube Sampling to make samples, where the total number is specified in the num_samples argument,
        and saves it into a pandas DataFrame, stored in an internal variable named parameters_values_df.
        For more information, see besos.sampling.dist_sampler and besos.sampling.lhs

        :param num_samples: an integer; represents the total number of samples
        """
        if self.descriptors_has_range:
            parameters_values_df = sampling.dist_sampler(sampling.lhs, self.problem, num_samples=num_samples)
        else:
            raise KeyError('sampling_lhs method can only be used with range descriptors.')
        self.parameters_values_df = self._expand_samples_with_buildings_and_epws(parameters_values_df)

    def _get_salib_problem(self) -> dict:
        """
        Internal method to build the SALib problem dictionary based on besos parameters.
        """
        names = self.problem.names('inputs')
        bounds = []
        from besos.parameters import RangeParameter
        for inp in self.problem.inputs:
            desc = inp.value_descriptors[0]
            if not isinstance(desc, RangeParameter):
                raise ValueError(f'Parameter {inp.name} must be a RangeParameter for Sensitivity Analysis.')
            bounds.append([desc.min, desc.max])
        problem = {'num_vars': len(names), 'names': names, 'bounds': bounds}
        return problem

    def sampling_sobol(self, num_samples: int=128):
        """
        Uses Saltelli's extension of the Sobol sequence to generate samples for Sensitivity Analysis.
        The samples are saved into a pandas DataFrame, stored in an internal variable named parameters_values_df.
        Requires SALib to be installed.

        :param num_samples: an integer; represents the number of samples to generate.
            The total number of samples generated will be num_samples * (2 * num_vars + 2).
            For Sobol, num_samples should preferably be a power of 2 (e.g. 64, 128, 256, 512, 1024).
        """
        if not self.descriptors_has_range:
            raise KeyError('sampling_sobol method can only be used with range descriptors.')
        try:
            from SALib.sample import saltelli
        except ImportError:
            raise ImportError('SALib is required for Sensitivity Analysis. Install it with: pip install SALib')
        problem = self._get_salib_problem()
        samples = saltelli.sample(problem, num_samples)
        parameters_values_df = pd.DataFrame(samples, columns=problem['names'])
        self.parameters_values_df = self._expand_samples_with_buildings_and_epws(parameters_values_df)

    def sampling_morris(self, num_samples: int=100, num_levels: int=4):
        """
        Uses Morris' method to generate samples for Sensitivity Analysis.
        The samples are saved into a pandas DataFrame, stored in an internal variable named parameters_values_df.
        Requires SALib to be installed.

        :param num_samples: an integer; represents the number of trajectories (N).
            The total number of samples generated will be num_samples * (num_vars + 1).
        :param num_levels: number of grid levels.
        """
        if not self.descriptors_has_range:
            raise KeyError('sampling_morris method can only be used with range descriptors.')
        try:
            from SALib.sample import morris as morris_sampler
        except ImportError:
            raise ImportError('SALib is required for Sensitivity Analysis. Install it with: pip install SALib')
        problem = self._get_salib_problem()
        samples = morris_sampler.sample(problem, N=num_samples, num_levels=num_levels)
        parameters_values_df = pd.DataFrame(samples, columns=problem['names'])
        self.parameters_values_df = self._expand_samples_with_buildings_and_epws(parameters_values_df)

    # ------------------------------------------------------------------
    # Category mapping helpers
    # ------------------------------------------------------------------

    def set_category_mapping(self, epw_mapping_rules: dict = None, idf_mapping_rules: dict = None) -> None:
        """
        Defines keyword-based mapping rules to automatically assign category labels to EPW
        and/or IDF files in the simulation results. Once set, categories are applied
        automatically at the end of ``run_parametric_simulation`` and ``run_optimisation``,
        and can be re-applied manually at any time with :meth:`apply_category_mapping`.

        The format follows the pyfwg convention:

        .. code-block:: python

            epw_mapping_rules = {
                'city': {
                    'seville': ['sevilla', 'SVQ'],
                    'london': ['london', 'gatwick'],
                },
                'scenario': {
                    'historical': 'hist',
                    'future': ['rcp45', 'rcp85'],
                },
            }

            idf_mapping_rules = {
                'typology': {
                    'residential': ['res', 'house'],
                    'office': ['office', 'ofic'],
                },
            }

        Matching is **case-insensitive substring search** on the file basename (without path
        or extension). The first matching keyword wins. If no keyword matches, the category
        value for that row will be ``None``.

        :param epw_mapping_rules: dict of ``{category_name: {category_value: keyword_or_list}}``.
            Applied to the ``epw`` column of result DataFrames.
        :param idf_mapping_rules: dict of ``{category_name: {category_value: keyword_or_list}}``.
            Applied to the ``idf`` column of result DataFrames.
        """
        def _validate_rules(rules: dict, name: str):
            if rules is None:
                return
            if not isinstance(rules, dict):
                raise TypeError(f'{name} must be a dict, got {type(rules).__name__}.')
            for category, mapping in rules.items():
                if not isinstance(mapping, dict):
                    raise TypeError(
                        f'{name}[{category!r}] must be a dict mapping category values to keywords, '
                        f'got {type(mapping).__name__}.'
                    )
                for value, keywords in mapping.items():
                    if not isinstance(keywords, (str, list)):
                        raise TypeError(
                            f'{name}[{category!r}][{value!r}] must be a str or list of str, '
                            f'got {type(keywords).__name__}.'
                        )

        _validate_rules(epw_mapping_rules, 'epw_mapping_rules')
        _validate_rules(idf_mapping_rules, 'idf_mapping_rules')
        self.epw_mapping_rules = epw_mapping_rules or {}
        self.idf_mapping_rules = idf_mapping_rules or {}
        print(f'  [info] Category mapping set: '
              f'{len(self.epw_mapping_rules)} EPW categor{"y" if len(self.epw_mapping_rules)==1 else "ies"}, '
              f'{len(self.idf_mapping_rules)} IDF categor{"y" if len(self.idf_mapping_rules)==1 else "ies"}.')

    @staticmethod
    def _resolve_category_for_value(filename: str, category_rules: dict):
        """
        Returns the category value for *filename* based on *category_rules*, or ``None``
        if no keyword matches.

        :param filename: the EPW or IDF basename (without path or extension).
        :param category_rules: a ``{category_value: keyword_or_list}`` dict for one category.
        :return: matched category value string, or ``None``.
        """
        name_lower = os.path.basename(filename).lower()
        # Strip common extensions so matching works on the stem
        for ext in ('.epw', '.idf'):
            if name_lower.endswith(ext):
                name_lower = name_lower[:-len(ext)]
                break
        for cat_value, keywords in category_rules.items():
            if isinstance(keywords, str):
                keywords = [keywords]
            for kw in keywords:
                if kw.lower() in name_lower:
                    return cat_value
        return None

    def apply_category_mapping(self, df_types: list = None) -> None:
        """
        Applies the category mapping rules (previously set via :meth:`set_category_mapping`)
        to the specified result DataFrames, adding one new column per category.

        Columns are inserted immediately after the ``epw`` or ``idf`` column they derive from.
        If a category column already exists it is overwritten with a warning.

        :param df_types: list of strings specifying which DataFrames to process.
            Valid values: ``'parametric'``, ``'parametric_hourly'``, ``'parametric_monthly'``,
            ``'optimisation'``, ``'optimisation_hourly'``, ``'optimisation_monthly'``.
            If ``None``, all available DataFrames are processed.
        """
        epw_rules = getattr(self, 'epw_mapping_rules', {})
        idf_rules = getattr(self, 'idf_mapping_rules', {})
        if not epw_rules and not idf_rules:
            return  # Nothing to do — preserve existing behaviour

        if df_types is None:
            df_types = [
                'parametric', 'parametric_hourly', 'parametric_monthly',
                'optimisation', 'optimisation_hourly', 'optimisation_monthly',
            ]

        df_attr_map = {
            'parametric':            'outputs_param_simulation',
            'parametric_hourly':     'outputs_param_simulation_hourly',
            'parametric_monthly':    'outputs_param_simulation_monthly',
            'optimisation':          'outputs_optimisation',
            'optimisation_hourly':   'outputs_optimisation_hourly',
            'optimisation_monthly':  'outputs_optimisation_monthly',
        }

        for df_key in df_types:
            attr = df_attr_map.get(df_key)
            if not attr:
                continue
            df = getattr(self, attr, None)
            if df is None or df.empty:
                continue

            # ---- EPW categories ----
            if epw_rules and 'epw' in df.columns:
                epw_insert_pos = df.columns.get_loc('epw') + 1
                for category, rules in epw_rules.items():
                    col_values = df['epw'].apply(
                        lambda v: self._resolve_category_for_value(str(v), rules)
                    )
                    if category in df.columns:
                        warnings.warn(
                            f"Column '{category}' already exists in {attr} and will be overwritten.",
                            UserWarning,
                        )
                        df[category] = col_values
                    else:
                        df.insert(epw_insert_pos, category, col_values)
                        epw_insert_pos += 1  # keep inserting after previous new column

            # ---- IDF categories ----
            if idf_rules and 'idf' in df.columns:
                idf_insert_pos = df.columns.get_loc('idf') + 1
                for category, rules in idf_rules.items():
                    col_values = df['idf'].apply(
                        lambda v: self._resolve_category_for_value(str(v), rules)
                    )
                    if category in df.columns:
                        warnings.warn(
                            f"Column '{category}' already exists in {attr} and will be overwritten.",
                            UserWarning,
                        )
                        df[category] = col_values
                    else:
                        df.insert(idf_insert_pos, category, col_values)
                        idf_insert_pos += 1

            setattr(self, attr, df)
            n_new = len(epw_rules) + len(idf_rules)
            print(f'  [info] apply_category_mapping: added/updated {n_new} category column(s) in {attr}.')

            # --- Persist mapping rules in DataFrame.attrs so they survive pickle/load ---
            df.attrs['epw_mapping_rules'] = epw_rules
            df.attrs['idf_mapping_rules'] = idf_rules

            # Overwrite the last saved .pkl on disk with the updated data
            for pkl_attr in ('outputs_param_simulation_filepath', 'outputs_optimisation_filepath'):
                last_path = getattr(self, pkl_attr, None)
                if last_path and last_path.endswith('.csv'):
                    pkl_path = last_path.replace('.csv', '.pkl')
                    if os.path.isfile(pkl_path):
                        try:
                            getattr(self, attr).to_pickle(pkl_path)
                            print(f'  [info] Mapping rules persisted to {pkl_path}')
                        except Exception as _e:
                            print(f'  [!] Could not update {pkl_path}: {_e}')

    def preview_category_mapping(self) -> dict:
        """
        Returns a dictionary containing DataFrames showing the category labels that would be assigned to each
        EPW and IDF currently registered in this instance, based on the rules defined
        via :meth:`set_category_mapping`. The DataFrames are also saved in the attribute
        `category_mapping_preview_dfs`.

        Use this **before running any simulation** to verify that the mapping rules
        produce the expected results.

        :return: a dictionary with keys ``'epw'`` and ``'idf'``, where each value is a pandas DataFrame.
            Returns empty DataFrames if no mapping rules have been set.

        Example::

            preview = parametric.preview_category_mapping()
            print(preview['epw'].to_string(index=False))
            # file                       city      scenario
            # seville_2024.epw           seville   historical
            # london_gatwick_rcp85.epw   london    future
            print(preview['idf'].to_string(index=False))
            # file                       typology
            # office_building_A.idf      None
        """
        epw_rules = getattr(self, 'epw_mapping_rules', {})
        idf_rules = getattr(self, 'idf_mapping_rules', {})
        
        epw_rows = []
        idf_rows = []

        # EPW rows
        if epw_rules:
            epws = getattr(self, 'epws', [])
            for epw in epws:
                row = {'file': os.path.basename(epw)}
                for category, rules in epw_rules.items():
                    row[category] = self._resolve_category_for_value(str(epw), rules)
                epw_rows.append(row)

        # IDF rows
        if idf_rules:
            buildings = getattr(self, 'buildings', [])
            for idx, b in enumerate(buildings):
                idf_name = self._get_idf_identifier(b, idx)
                row = {'file': idf_name}
                for category, rules in idf_rules.items():
                    row[category] = self._resolve_category_for_value(idf_name, rules)
                idf_rows.append(row)

        epw_df = pd.DataFrame(epw_rows)
        idf_df = pd.DataFrame(idf_rows)

        if not epw_rules and not idf_rules:
            print('  [info] No category mapping rules are defined. Call set_category_mapping() first.')

        # Warn about any files that didn't match any category
        unmatched = []
        if epw_rules and not epw_df.empty:
            category_cols = list(epw_rules.keys())
            for _, r in epw_df.iterrows():
                unmatched_cats = [c for c in category_cols if c in r and r[c] is None]
                if unmatched_cats:
                    unmatched.append(f"  EPW '{r['file']}' -> no match for: {unmatched_cats}")

        if idf_rules and not idf_df.empty:
            category_cols = list(idf_rules.keys())
            for _, r in idf_df.iterrows():
                unmatched_cats = [c for c in category_cols if c in r and r[c] is None]
                if unmatched_cats:
                    unmatched.append(f"  IDF '{r['file']}' -> no match for: {unmatched_cats}")

        if unmatched:
            print('[!] Warning: the following files did not match any keyword for some categories:')
            for msg in unmatched:
                print(msg)

        self.category_mapping_preview_dfs = {'epw': epw_df, 'idf': idf_df}
        return self.category_mapping_preview_dfs

    def set_evaluator(self, epw: str, out_dir: str, building: Any = None) -> besos.evaluator.EvaluatorEP:
        """
        Used internally for setting the evaluator in run_parametric_simulation and run_optimisation methods.

        :param epw: The epw file name
        :param out_dir: The name of the output directory to save the results.
        :param building: Optional building to evaluate (if multiple are simulated)
        :return: the besos.evaluator.EvaluatorEP class instance
        """
        b = building if building is not None else self.building
        evaluator = EvaluatorEP(problem=self.problem, building=b, epw=epw, out_dir=out_dir)
        return evaluator

    def _run_evaluator_df_apply(
        self,
        evaluator: EvaluatorEP,
        df: pd.DataFrame,
        keep_input: bool,
        keep_dirs: bool,
        processes: int,
    ) -> pd.DataFrame:
        if len(self._get_problem_input_names()) > 0:
            return evaluator.df_apply(
                df=df,
                keep_input=keep_input,
                keep_dirs=keep_dirs,
                processes=processes,
            )

        rows = []
        output_names = evaluator.problem.names('outputs')
        for (_, row) in df.iterrows():
            result = evaluator(row, keep_dirs=keep_dirs)
            if not isinstance(result, (list, tuple)):
                result = (result,)
            result_dict = {
                output_names[idx]: result[idx]
                for idx in range(len(output_names))
            }
            if keep_dirs and len(result) > len(output_names):
                result_dict['output_dir'] = result[-1]
            if keep_input:
                result_dict.update(row.to_dict())
            rows.append(result_dict)
        return pd.DataFrame(rows)

    def run_parametric_simulation(self, epws: list = None, out_dir: str = 'param_results', df: pd.DataFrame = None, processes: int=2, keep_input: bool=True, keep_dirs: bool=True) -> pd.DataFrame:
        """
        Runs the parametric simulation.

        :param epws: a list of .epw filenames
        :param out_dir: the name of the directory to store the outputs
        :param df: a pandas DataFrame which contains the values of the parameters to simulate
        :param processes: the number of CPUs to be used in simulation
        :param keep_input: True to keep the input DataFrame in the results
        :param keep_dirs: True to keep the simulation results
        :return: a pandas DataFrame
        """
        if epws is None:
            epws = getattr(self, 'epws', [])
        if not epws:
            raise ValueError("No EPWs provided and no default EPWs found in class instance.")
        if df is None:
            df = getattr(self, 'parameters_values_df', None)
            if df is None:
                raise ValueError("Argument 'df' cannot be None if self.parameters_values_df is not populated. Run a sampling method first or provide 'df'.")

        os.makedirs(out_dir, exist_ok=True)
        # Update the IDF backup with the exact building state used for this run
        self._save_idf_backup(label='pre_parametric', out_dir=out_dir)

        grouped_dfs = self._prepare_dataframe_for_buildings(df=df, epws=epws)
        
        problem_names_inputs = self._get_problem_input_names()
        problem_names_outputs = self.problem.names('outputs') if hasattr(self, 'problem') and hasattr(self.problem, 'names') else getattr(self, 'outputs_names', [])
        
        tasks = []
        # Ensure idf_backup_path is iterable even if it's a single string
        _backup_paths = []
        if hasattr(self, 'idf_backup_path') and self.idf_backup_path:
            _backup_paths = self.idf_backup_path if isinstance(self.idf_backup_path, list) else [self.idf_backup_path]

        for (idf_basename, df_for_idf) in grouped_dfs.items():
            # Find the actual path to the saved backup for this IDF
            idf_backup_file = None
            for p in _backup_paths:
                # The backup filename format is accim_idf_backup_{idf_basename}{suffix}_{timestamp}.idf
                # We can check if the idf_basename is in the path
                if f"_{idf_basename}_" in os.path.basename(p) or f"_{idf_basename}." in os.path.basename(p):
                    idf_backup_file = p
                    break
            
            if not idf_backup_file:
                # Fallback: assume the file is in the current directory with .idf appended if missing
                idf_backup_file = idf_basename if idf_basename.lower().endswith('.idf') else f"{idf_basename}.idf"
                
            epws_for_idf = df_for_idf['epw'].drop_duplicates().tolist() if 'epw' in df_for_idf.columns else epws
            for epw in epws_for_idf:
                epwname = epw.split('.epw')[0]
                if 'epw' in df_for_idf.columns:
                    evaluator_input_df = df_for_idf.loc[df_for_idf['epw'] == epw, problem_names_inputs]
                else:
                    evaluator_input_df = df_for_idf[problem_names_inputs]
                    
                evaluator_df = evaluator_input_df.reset_index(drop=True).copy()
                
                for _, row in evaluator_df.iterrows():
                    tasks.append((
                        idf_backup_file,
                        epw,
                        epwname,
                        idf_basename,
                        out_dir,
                        problem_names_inputs,
                        problem_names_outputs,
                        row.to_dict(),
                        keep_dirs,
                        keep_input
                    ))

        all_results = []
        if processes > 1 and len(tasks) > 1:
            import concurrent.futures
            from tqdm import tqdm
            with concurrent.futures.ProcessPoolExecutor(max_workers=processes) as executor:
                futures = [executor.submit(_run_single_evaluation_worker, *t) for t in tasks]
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(tasks), desc="Executing parametric simulations", unit="row"):
                    all_results.append(future.result())
        else:
            from tqdm import tqdm
            for t in tqdm(tasks, desc="Executing parametric simulations", unit="row"):
                all_results.append(_run_single_evaluation_worker(*t))
                
        import pandas as pd
        outputs_param_simulation = pd.DataFrame(all_results)
        
        if len(epws) > 1 or len(self.buildings) > 1:
            outputs_param_simulation = outputs_param_simulation.reset_index(drop=True)
            
        outputs_param_simulation.attrs = getattr(outputs_param_simulation, 'attrs', {})
        if hasattr(self, 'problem') and hasattr(self.problem, 'names'):
            outputs_param_simulation.attrs['parameters_names'] = self._get_all_input_names()
            outputs_param_simulation.attrs['outputs_names'] = self.problem.names('outputs')
        elif hasattr(self, 'parameters_names') and hasattr(self, 'outputs_names'):
            outputs_param_simulation.attrs['parameters_names'] = self.parameters_names + self._get_external_input_names()
            outputs_param_simulation.attrs['outputs_names'] = self.outputs_names
            
        self.outputs_param_simulation = outputs_param_simulation
        self.evaluators = {} 
        
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.outputs_param_simulation.attrs['idf_backup_path'] = getattr(self, 'idf_backup_path', [])
        self.outputs_param_simulation.attrs['epws'] = epws
        
        _base = os.path.join(out_dir, f'outputs_param_simulation_{timestamp}')
        self.outputs_param_simulation.to_csv(f'{_base}.csv', index=False)
        self.outputs_param_simulation.to_pickle(f'{_base}.pkl')
        
        import json as _json
        _json_payload = {
            'attrs': self.outputs_param_simulation.attrs,
            'data': self.outputs_param_simulation.to_dict(orient='list'),
            'idf_backup_path': getattr(self, 'idf_backup_path', []),
        }
        with open(f'{_base}.json', 'w', encoding='utf-8') as _f:
            _json.dump(_json_payload, _f, indent=2, default=str)
            
        self.outputs_param_simulation_filepath = f'{_base}.csv'
        self.epws = self.outputs_param_simulation.attrs.get('epws', [])
        self.last_run_type = 'parametric'
        
        if getattr(self, 'epw_mapping_rules', {}) or getattr(self, 'idf_mapping_rules', {}):
            self.apply_category_mapping(df_types=['parametric'])
        
        return self.outputs_param_simulation

    def load_outputs_parametric(self, csv_path: str=None, pickle_path: str=None, json_path: str=None, hourly_csv_path: str=None, hourly_pickle_path: str=None, parameters_names: list=None, outputs_names: list=None) -> pd.DataFrame:
        """
        Loads outputs of a previous parametric simulation from a CSV, Pickle, or JSON file.
        This allows you to resume a parametric session without rerunning the simulations.
        
        :param csv_path: path to the CSV file containing parametric simulation results.
        :param pickle_path: path to the Pickle file containing parametric simulation results (recommended).
        :param json_path: path to the JSON file containing parametric simulation results (human-readable).
        :param hourly_csv_path: path to the CSV file containing hourly parametric simulation results.
        :param hourly_pickle_path: path to the Pickle file containing hourly parametric simulation results.
        :param parameters_names: optional list of parameter names to reconstruct the internal problem object.
        :param outputs_names: optional list of output names to reconstruct the internal problem object.
        :return: pandas DataFrame containing the loaded parametric simulation outputs.
        """
        import pandas as pd
        if not csv_path and (not pickle_path) and (not json_path):
            raise ValueError('A valid csv_path, pickle_path, or json_path must be provided.')
        if pickle_path:
            self.outputs_param_simulation = pd.read_pickle(pickle_path)
            # Restore idf_backup_path from attrs if it was embedded at save time
            _ibp = self.outputs_param_simulation.attrs.get('idf_backup_path')
            if _ibp:
                self.idf_backup_path = _ibp
                print(f'  [info] idf_backup_path restored: {self.idf_backup_path}')
        elif json_path:
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            self.outputs_param_simulation = pd.DataFrame(payload['data'])
            for (k, v) in payload.get('attrs', {}).items():
                self.outputs_param_simulation.attrs[k] = v
            # Restore the IDF backup path stored at save time
            if payload.get('idf_backup_path'):
                self.idf_backup_path = payload['idf_backup_path']
                print(f'  [info] idf_backup_path restored: {self.idf_backup_path}')
        else:
            self.outputs_param_simulation = pd.read_csv(csv_path)
        if hourly_pickle_path:
            self.outputs_param_simulation_hourly = pd.read_pickle(hourly_pickle_path)
        elif hourly_csv_path:
            self.outputs_param_simulation_hourly = pd.read_csv(hourly_csv_path)
        parameters_names = parameters_names or self.outputs_param_simulation.attrs.get('parameters_names')
        outputs_names = outputs_names or self.outputs_param_simulation.attrs.get('outputs_names')
        if parameters_names and outputs_names and not (hasattr(self, 'problem') and type(self.problem).__name__ != 'MockProblem'):

            class MockProblem:

                def __init__(self, inputs, outputs):
                    self._inputs = inputs
                    self._outputs = outputs

                def names(self, typ):
                    if typ == 'inputs':
                        return self._inputs
                    elif typ == 'outputs':
                        return self._outputs
            self.problem = MockProblem(parameters_names, outputs_names)
            self.parameters_names = parameters_names
            self.outputs_names = outputs_names
        self.epws = self.outputs_param_simulation.attrs.get('epws', [])
        self.last_run_type = 'parametric'
        # Restore category mapping rules saved in .attrs at apply_category_mapping time
        _epw_rules = self.outputs_param_simulation.attrs.get('epw_mapping_rules')
        _idf_rules = self.outputs_param_simulation.attrs.get('idf_mapping_rules')
        if _epw_rules or _idf_rules:
            self.epw_mapping_rules = _epw_rules or {}
            self.idf_mapping_rules = _idf_rules or {}
            print(f'  [info] Category mapping rules restored from pickle.')
        # Re-apply category mapping if rules are already set on this instance
        if getattr(self, 'epw_mapping_rules', {}) or getattr(self, 'idf_mapping_rules', {}):
            self.apply_category_mapping(df_types=['parametric'])
        return self.outputs_param_simulation

    def estimate_optimisation_sims(self, evaluations: int, population_size: int, epws: list) -> int:
        """
        Estimates the maximum number of EnergyPlus simulations that will be run by
        :meth:`run_optimisation` **before** launching it.

        NSGA-II (and most platypus algorithms) work in discrete generations, each of which
        evaluates exactly ``population_size`` individuals.  The stopping criterion
        ``evaluations`` is checked **between** generations, so the algorithm always
        completes the current generation before stopping.  Therefore:

        .. code-block:: text

            sims_per_epw = population_size × ⌈evaluations / population_size⌉
            total_sims   = sims_per_epw × len(epws)

        Special case: if ``evaluations < population_size`` the initial generation
        already exceeds the budget, but it is always completed in full, so
        ``sims_per_epw`` equals ``population_size``.

        :param evaluations: same value you will pass to :meth:`run_optimisation`
        :param population_size: same value you will pass to :meth:`run_optimisation`
        :param epws: same list you will pass to :meth:`run_optimisation`
        :return: estimated total number of EnergyPlus simulations
        """
        import math
        sims_per_epw = population_size * math.ceil(evaluations / population_size)
        total = sims_per_epw * len(epws)
        print(f"Estimated simulations\n  evaluations    : {evaluations}\n  population_size: {population_size}\n  EPWs           : {len(epws)} ({', '.join(epws)})\n  sims per EPW   : {sims_per_epw}  ({math.ceil(evaluations / population_size)} generation(s) × {population_size})\n  TOTAL          : {total}")
        self.epws = self.outputs_param_simulation.attrs.get('epws', [])
        self.last_run_type = 'parametric'
        return total

    def run_optimisation(self, epws: list = None, out_dir: str = 'optim_results', evaluations: int = 2, population_size: int = 2, algorithm: str='NSGAII', processes: int=1, keep_sim_files: Literal['all', 'non-dominated', 'none']='all', keep_sim_files_batch_size: int=50, keep_df: Literal['all', 'non-dominated']='all', **kwargs) -> pd.DataFrame:
        """
        Runs the optimisation.

        :param epws: a list of .epw filenames
        :param out_dir: the directory name to save the outputs
        :param evaluations: the algorithm will be stopped once it uses more than this many
            evaluations (i.e. EnergyPlus simulations).  Because the algorithm always completes
            the current generation before stopping, the actual number of simulations per EPW
            is ``population_size × ⌈evaluations / population_size⌉``.
            Use :meth:`estimate_optimisation_sims` to preview the count before running.
        :param population_size: number of individuals in each generation; each individual
            corresponds to one EnergyPlus simulation
        :param algorithm: the optimisation algorithm to use; default is 'NSGAII'
        :param processes: number of CPU cores to use for parallel evaluation of individuals
            within each generation.  Uses ``platypus.ProcessPoolEvaluator`` internally.
            Default is 1 (sequential).  Values > 1 are useful when ``population_size`` is
            large and each simulation is independent.
        :param keep_sim_files: specifies which simulation results directories to keep:
            'all' (keeps everything), 'non-dominated' (deletes directories of dominated solutions to save space),
            or 'none' (keeps no simulation files).
        :param keep_sim_files_batch_size: number of evaluations per worker to wait before running the local pareto batch cleanup.
        :param keep_df: specifies which evaluations to keep in the outputs_optimisation DataFrame:
            'all' (keeps dominated and non-dominated) or 'non-dominated'.
        :return: a pandas DataFrame
        """
        if epws is None:
            epws = getattr(self, 'epws', [])
        if not epws:
            raise ValueError("No EPWs provided and no default EPWs found in class instance.")
        self.epws = epws
        available_algorithms = ['GeneticAlgorithm', 'EvolutionaryStrategy', 'NSGAII', 'EpsMOEA', 'GDE3', 'SPEA2', 'MOEAD', 'NSGAIII', 'ParticleSwarm', 'OMOPSO', 'SMPSO', 'CMAES', 'IBEA', 'PAES', 'PESA2', 'EpsNSGAII']
        outputs_dict = {}
        full_outputs_dict = {}
        evaluators = {}
        os.makedirs(out_dir, exist_ok=True)
        # Save an IDF backup into the results folder before starting
        self._save_idf_backup(label='pre_optimisation', out_dir=out_dir)
        from besos.evaluator import AbstractEvaluator
        if not hasattr(AbstractEvaluator, '_original_to_platypus'):
            AbstractEvaluator._original_to_platypus = AbstractEvaluator.to_platypus
        AbstractEvaluator.to_platypus = _patched_to_platypus
        if processes > 1:
            import platypus
            from platypus.config import PlatypusConfig
            original_evaluator = PlatypusConfig.default_evaluator
            platypus_evaluator = platypus.ProcessPoolEvaluator(processes)
            PlatypusConfig.default_evaluator = platypus_evaluator
        try:
            buildings_by_idf = self._get_buildings_by_idf()
            for (idf_basename, b) in buildings_by_idf.items():
                for epw in epws:
                    evaluator = self.set_evaluator(epw=epw, out_dir=out_dir, building=b)
                    evaluator._keep_sim_files = keep_sim_files
                    evaluator._keep_sim_files_batch_size = keep_sim_files_batch_size
                    evaluator._keep_dirs = False if keep_sim_files == 'none' else True
                    evaluator._optimisation_eval_records = []
                    epwname = epw.split('.epw')[0]
                    evaluator._optimisation_log_base = os.path.join(out_dir, f'optim_eval_log_{idf_basename}_{epwname}_{os.getpid()}')
                    for log_file in pyglob.glob(f'{evaluator._optimisation_log_base}_*.jsonl'):
                        try:
                            os.remove(log_file)
                        except OSError:
                            pass
                if processes > 1 and hasattr(evaluator, '_building') and hasattr(evaluator._building, 'idfobjects'):
                    evaluator._building.idfobjects = GlobalAllCapsDict(evaluator._building.idfobjects)
                if algorithm == 'GeneticAlgorithm':
                    outputs_optimisation = optimizer.GeneticAlgorithm(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'EvolutionaryStrategy':
                    outputs_optimisation = optimizer.EvolutionaryStrategy(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'NSGAII':
                    outputs_optimisation = optimizer.NSGAII(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'EpsMOEA':
                    outputs_optimisation = optimizer.EpsMOEA(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'GDE3':
                    outputs_optimisation = optimizer.GDE3(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'SPEA2':
                    outputs_optimisation = optimizer.SPEA2(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'MOEAD':
                    outputs_optimisation = optimizer.MOEAD(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'NSGAIII':
                    outputs_optimisation = optimizer.NSGAIII(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'ParticleSwarm':
                    outputs_optimisation = optimizer.ParticleSwarm(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'OMOPSO':
                    outputs_optimisation = optimizer.OMOPSO(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'SMPSO':
                    outputs_optimisation = optimizer.SMPSO(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'CMAES':
                    outputs_optimisation = optimizer.CMAES(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'IBEA':
                    outputs_optimisation = optimizer.IBEA(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'PAES':
                    outputs_optimisation = optimizer.PAES(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'PESA2':
                    outputs_optimisation = optimizer.PESA2(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                elif algorithm == 'EpsNSGAII':
                    outputs_optimisation = optimizer.EpsNSGAII(evaluator, evaluations=evaluations, population_size=population_size, **kwargs)
                else:
                    raise KeyError(f'Input algorithm {algorithm} not found. Available algorithms are: {available_algorithms}')
                outputs_optimisation['epw'] = epwname
                outputs_optimisation['idf'] = idf_basename
                key = f"{idf_basename}_{epwname}" if len(self.buildings) > 1 else epwname
                outputs_dict.update({key: outputs_optimisation})
                full_outputs_optimisation = self._build_full_optimisation_outputs_df(evaluator=evaluator, epwname=epwname)
                full_outputs_optimisation['idf'] = idf_basename
                full_outputs_dict.update({key: full_outputs_optimisation})
                evaluators.update({key: evaluator})
        finally:
            if processes > 1:
                platypus_evaluator.close()
                PlatypusConfig.default_evaluator = original_evaluator
                if hasattr(AbstractEvaluator, '_original_to_platypus'):
                    AbstractEvaluator.to_platypus = AbstractEvaluator._original_to_platypus
        outputs_optimisation_non_dominated = pd.concat([df for df in outputs_dict.values()])
        if len(epws) > 1 or len(self.buildings) > 1:
            outputs_optimisation_non_dominated = outputs_optimisation_non_dominated.reset_index(drop=True)
        outputs_optimisation = pd.concat([df for df in full_outputs_dict.values()])
        if len(epws) > 1 or len(self.buildings) > 1:
            outputs_optimisation = outputs_optimisation.reset_index(drop=True)
        outputs_optimisation = self._annotate_pareto_status(outputs_optimisation_full=outputs_optimisation, outputs_optimisation=outputs_optimisation_non_dominated)
        if keep_sim_files == 'non-dominated':
            import shutil
            for (idx, row) in outputs_optimisation[~outputs_optimisation['pareto-optimal']].iterrows():
                sim_dir = row.get('simulation_directory')
                if pd.notna(sim_dir) and isinstance(sim_dir, str) and os.path.exists(sim_dir):
                    try:
                        shutil.rmtree(sim_dir)
                    except Exception:
                        pass
                outputs_optimisation.at[idx, 'simulation_directory'] = pd.NA
                outputs_optimisation.at[idx, 'simulation_output_csv_path'] = pd.NA
        elif keep_sim_files == 'none':
            import shutil
            import glob
            worker_dirs = glob.glob(os.path.join(out_dir, 'BESOS_Output*'))
            for w_dir in worker_dirs:
                if os.path.isdir(w_dir):
                    try:
                        shutil.rmtree(w_dir)
                    except Exception:
                        pass
            log_files = glob.glob(os.path.join(out_dir, 'optim_eval_log_*.jsonl'))
            for log_file in log_files:
                try:
                    os.remove(log_file)
                except OSError:
                    pass
            outputs_optimisation['simulation_directory'] = pd.NA
            outputs_optimisation['simulation_output_csv_path'] = pd.NA
        if keep_df == 'non-dominated':
            outputs_optimisation = outputs_optimisation[outputs_optimisation['pareto-optimal']].copy()
            if len(epws) > 1:
                outputs_optimisation = outputs_optimisation.reset_index(drop=True)
        self._set_optimisation_outputs(outputs_optimisation_full=outputs_optimisation, outputs_optimisation_non_dominated=outputs_optimisation_non_dominated)
        self._save_outputs_optimisation_full(out_dir=out_dir)
        self.epws = self.outputs_optimisation.attrs.get('epws', [])
        self.last_run_type = 'optimisation'
        self.evaluators = evaluators
        # Auto-apply category mapping if rules were previously set
        if getattr(self, 'epw_mapping_rules', {}) or getattr(self, 'idf_mapping_rules', {}):
            self.apply_category_mapping(df_types=['optimisation'])

    def _build_full_optimisation_outputs_df(self, evaluator: EvaluatorEP, epwname: str) -> pd.DataFrame:
        records = getattr(evaluator, '_optimisation_eval_records', [])
        if len(records) == 0:
            log_base = getattr(evaluator, '_optimisation_log_base', None)
            if log_base is not None:
                log_files = pyglob.glob(f'{log_base}_*.jsonl')
                for log_file in log_files:
                    with open(log_file, 'r', encoding='utf-8') as logfile:
                        for line in logfile:
                            payload = json.loads(line)
                            records.append({'inputs': tuple(payload['inputs']), 'results': tuple(payload['results']), 'sim_dir': payload['sim_dir']})
        input_names = evaluator.problem.names('inputs')
        output_names = evaluator.problem.names('outputs')
        constraint_names = evaluator.problem.names('constraints')
        rows = []
        for record in records:
            row = {}
            for (idx, input_name) in enumerate(input_names):
                row[input_name] = record['inputs'][idx]
            for (idx, output_name) in enumerate(output_names):
                row[output_name] = record['results'][idx]
            for (idx, constraint_name) in enumerate(constraint_names):
                row[constraint_name] = record['results'][len(output_names) + idx]
            if record['sim_dir'] is not None:
                row['simulation_directory'] = record['sim_dir']
                row['simulation_output_csv_path'] = os.path.join(record['sim_dir'], 'eplusout.csv')
            else:
                row['simulation_directory'] = None
                row['simulation_output_csv_path'] = None
            row['epw'] = epwname
            rows.append(row)
        full_df = pd.DataFrame(rows)
        required_columns = ['simulation_directory', 'simulation_output_csv_path', 'epw']
        for col in required_columns:
            if col not in full_df.columns:
                full_df[col] = pd.Series(dtype=object)
        return full_df

    @staticmethod
    def _make_match_key(df: pd.DataFrame, match_columns: list) -> pd.Series:
        key_df = df[match_columns].copy()
        for column in match_columns:
            if pd.api.types.is_numeric_dtype(key_df[column]):
                key_df[column] = key_df[column].astype(float).round(12)
            key_df[column] = key_df[column].astype(str)
        return key_df.apply(lambda row: '|'.join(row.values.tolist()), axis=1)

    def _annotate_pareto_status(self, outputs_optimisation_full: pd.DataFrame, outputs_optimisation: pd.DataFrame) -> pd.DataFrame:
        """
        Recomputes the Pareto front from scratch using the objective values
        directly on the full evaluation history, grouped per EPW.

        This approach is more reliable than matching against the final NSGA-II
        population (which only contains the last generation), avoiding both
        false negatives caused by points evaluated in earlier generations that
        are genuinely non-dominated, and floating-point matching issues.
        """
        if outputs_optimisation_full.empty:
            outputs_optimisation_full['pareto-optimal'] = pd.Series(dtype=bool)
            return outputs_optimisation_full
        output_names = self.problem.names('outputs')
        minimize_outputs = getattr(self.problem, 'minimize_outputs', None)
        if minimize_outputs is None:
            minimize_flags = [True] * len(output_names)
        else:
            minimize_flags = [m if m is not None else True for m in minimize_outputs]

        def _is_pareto_optimal(costs: np.ndarray) -> np.ndarray:
            """
            Return a boolean mask of length n where True means the row is
            Pareto-non-dominated (all objectives already in minimisation space).

            Solution i is dominated iff there exists j such that:
              j <= i on ALL objectives  AND  j < i on AT LEAST ONE objective.
            """
            n = costs.shape[0]
            is_pareto = np.ones(n, dtype=bool)
            for i in range(n):
                if not is_pareto[i]:
                    continue
                others_mask = np.arange(n) != i
                dominated_i = np.all(costs[others_mask] <= costs[i], axis=1) & np.any(costs[others_mask] < costs[i], axis=1)
                if np.any(dominated_i):
                    is_pareto[i] = False
            return is_pareto

        def _pareto_mask_for_group(group: pd.DataFrame) -> pd.Series:
            """Compute Pareto mask for a single EPW group."""
            objective_data = group[output_names].values.astype(float)
            for (j, minimise) in enumerate(minimize_flags):
                if not minimise:
                    objective_data[:, j] = -objective_data[:, j]
            mask = _is_pareto_optimal(objective_data)
            return pd.Series(mask, index=group.index)
        pareto_mask = pd.Series(False, index=outputs_optimisation_full.index)
        if 'epw' in outputs_optimisation_full.columns and outputs_optimisation_full['epw'].notna().any():
            for (epw, group) in outputs_optimisation_full.groupby('epw'):
                pareto_mask.loc[group.index] = _pareto_mask_for_group(group)
        else:
            pareto_mask = _pareto_mask_for_group(outputs_optimisation_full)
        outputs_optimisation_full['pareto-optimal'] = pareto_mask
        return outputs_optimisation_full

    def _set_optimisation_outputs(self, outputs_optimisation_full: pd.DataFrame, outputs_optimisation_non_dominated: pd.DataFrame=None):
        if 'pareto-optimal' not in outputs_optimisation_full.columns:
            raise KeyError("Column 'pareto-optimal' is required in outputs_optimisation_full.")
        if 'simulation_output_csv_path' not in outputs_optimisation_full.columns:
            outputs_optimisation_full['simulation_output_csv_path'] = pd.NA
        if 'epw' not in outputs_optimisation_full.columns:
            outputs_optimisation_full['epw'] = pd.NA
        if outputs_optimisation_non_dominated is not None and 'epw' in outputs_optimisation_non_dominated.columns and outputs_optimisation_full['epw'].isna().all() and (len(outputs_optimisation_non_dominated['epw'].dropna().unique()) == 1):
            outputs_optimisation_full['epw'] = outputs_optimisation_non_dominated['epw'].dropna().iloc[0]
        if outputs_optimisation_full.empty and outputs_optimisation_non_dominated is not None:
            fallback_full = outputs_optimisation_non_dominated.copy()
            if 'pareto-optimal' not in fallback_full.columns:
                fallback_full['pareto-optimal'] = True
            if 'simulation_output_csv_path' not in fallback_full.columns:
                fallback_full['simulation_output_csv_path'] = pd.NA
            if 'simulation_directory' not in fallback_full.columns:
                fallback_full['simulation_directory'] = pd.NA
            outputs_optimisation_full = fallback_full
        if hasattr(self, 'problem') and hasattr(self.problem, 'names'):
            outputs_optimisation_full.attrs['parameters_names'] = self._get_all_input_names()
            outputs_optimisation_full.attrs['outputs_names'] = self.problem.names('outputs')
            outputs_optimisation_full.attrs['minimize_outputs'] = getattr(self.problem, 'minimize_outputs', [])
        elif hasattr(self, 'parameters_names') and hasattr(self, 'outputs_names'):
            outputs_optimisation_full.attrs['parameters_names'] = self.parameters_names + self._get_external_input_names()
            outputs_optimisation_full.attrs['outputs_names'] = self.outputs_names
            outputs_optimisation_full.attrs['minimize_outputs'] = getattr(self.problem, 'minimize_outputs', []) if hasattr(self, 'problem') else []
        self.outputs_optimisation = outputs_optimisation_full
        if 'epw' not in self.outputs_optimisation.columns:
            self.outputs_optimisation['epw'] = pd.NA
        self.optimisation_csv_paths_non_dominated = self.outputs_optimisation[self.outputs_optimisation['pareto-optimal']]['simulation_output_csv_path'].dropna().drop_duplicates().tolist()
        self.optimisation_csv_paths_non_dominated_by_epw = {}
        self.optimisation_csv_paths_dominated_by_epw = {}
        if 'epw' in outputs_optimisation_full.columns:
            non_dominated_df = outputs_optimisation_full[outputs_optimisation_full['pareto-optimal']].copy()
            dominated_df = outputs_optimisation_full[~outputs_optimisation_full['pareto-optimal']].copy()
            epws = sorted({str(epw) for epw in outputs_optimisation_full['epw'].dropna().unique().tolist()})
            for epw in epws:
                self.optimisation_csv_paths_non_dominated_by_epw[epw] = non_dominated_df.loc[non_dominated_df['epw'].astype(str) == epw, 'simulation_output_csv_path'].dropna().drop_duplicates().tolist()
                self.optimisation_csv_paths_dominated_by_epw[epw] = dominated_df.loc[dominated_df['epw'].astype(str) == epw, 'simulation_output_csv_path'].dropna().drop_duplicates().tolist()
        self.optimisation_csv_paths_dominated = outputs_optimisation_full[~outputs_optimisation_full['pareto-optimal']]['simulation_output_csv_path'].dropna().drop_duplicates().tolist()

    def _save_outputs_optimisation_full(self, out_dir: str):
        import json
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs(out_dir, exist_ok=True)
        # Update the IDF backup with the exact building state used for this optimisation run
        self._save_idf_backup(label='pre_optimisation', out_dir=out_dir)
        # Embed the backup path and epws in attrs so they survive pickle serialisation
        self.outputs_optimisation.attrs['idf_backup_path'] = self.idf_backup_path
        self.outputs_optimisation.attrs['epws'] = getattr(self, 'epws', [])
        full_results_filename = f'outputs_optimisation_{timestamp}'
        full_results_path = os.path.join(out_dir, f'{full_results_filename}.csv')
        self.outputs_optimisation.to_csv(full_results_path, index=False)
        self.outputs_optimisation.to_pickle(os.path.join(out_dir, f'{full_results_filename}.pkl'))
        json_payload = {
            'attrs': self.outputs_optimisation.attrs,
            'data': self.outputs_optimisation.to_dict(orient='list'),
            'idf_backup_path': self.idf_backup_path,
        }
        with open(os.path.join(out_dir, f'{full_results_filename}.json'), 'w', encoding='utf-8') as f:
            json.dump(json_payload, f, indent=2, default=str)
        self.outputs_optimisation_filepath = full_results_path

    def load_outputs_optimisation(self, csv_path: str=None, pickle_path: str=None, json_path: str=None, hourly_csv_path: str=None, hourly_pickle_path: str=None, parameters_names: list=None, outputs_names: list=None, minimize_outputs: list=None) -> pd.DataFrame:
        """
        Loads full optimisation outputs (dominated + non-dominated) from a CSV, Pickle, or JSON file
        previously generated by :meth:`run_optimisation`, and rebuilds the related
        internal attributes without rerunning simulations.

        :param csv_path: path to a CSV file with full optimisation outputs.
        :param pickle_path: path to a Pickle file with full optimisation outputs (recommended).
        :param json_path: path to a JSON file with full optimisation outputs (human-readable).
        :param hourly_csv_path: path to a CSV file with hourly optimisation outputs.
        :param hourly_pickle_path: path to a Pickle file with hourly optimisation outputs.
        :param parameters_names: optional list of parameter names to reconstruct the internal problem object.
        :param outputs_names: optional list of output names to reconstruct the internal problem object.
        :param minimize_outputs: optional list of booleans indicating if outputs should be minimized.
        :return: pandas DataFrame containing full optimisation outputs (dominated + non-dominated)
        """
        target_path = pickle_path or json_path or csv_path or self.outputs_optimisation_filepath
        if target_path is None:
            raise ValueError('No path was provided and no previous outputs_optimisation file is available. Run run_optimisation first or provide a valid csv_path/pickle_path/json_path.')
        if pickle_path or str(target_path).endswith('.pkl') or str(target_path).endswith('.pickle'):
            outputs_optimisation = pd.read_pickle(target_path)
            # Restore idf_backup_path from attrs if it was embedded at save time
            _ibp = outputs_optimisation.attrs.get('idf_backup_path')
            if _ibp:
                self.idf_backup_path = _ibp
                print(f'  [info] idf_backup_path restored: {self.idf_backup_path}')
        elif json_path or str(target_path).endswith('.json'):
            import json
            with open(target_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            outputs_optimisation = pd.DataFrame(payload['data'])
            for (k, v) in payload.get('attrs', {}).items():
                outputs_optimisation.attrs[k] = v
            # Restore the IDF backup path stored at save time
            if payload.get('idf_backup_path'):
                self.idf_backup_path = payload['idf_backup_path']
                print(f'  [info] idf_backup_path restored: {self.idf_backup_path}')
        else:
            outputs_optimisation = pd.read_csv(target_path)
        if 'pareto-optimal' not in outputs_optimisation.columns:
            raise KeyError("Column 'pareto-optimal' not found in the provided file. Please load a file generated from outputs_optimisation.")
        self.outputs_optimisation_filepath = target_path
        self._set_optimisation_outputs(outputs_optimisation_full=outputs_optimisation)
        if hourly_pickle_path:
            self.outputs_optimisation_hourly = pd.read_pickle(hourly_pickle_path)
        elif hourly_csv_path:
            self.outputs_optimisation_hourly = pd.read_csv(hourly_csv_path)
        parameters_names = parameters_names or outputs_optimisation.attrs.get('parameters_names')
        outputs_names = outputs_names or outputs_optimisation.attrs.get('outputs_names')
        minimize_outputs = minimize_outputs or outputs_optimisation.attrs.get('minimize_outputs')
        if parameters_names and outputs_names and not (hasattr(self, 'problem') and type(self.problem).__name__ != 'MockProblem'):

            class MockProblem:

                def __init__(self, inputs, outputs, minimize_flags):
                    self._inputs = inputs
                    self._outputs = outputs
                    self.minimize_outputs = minimize_flags

                def names(self, typ):
                    if typ == 'inputs':
                        return self._inputs
                    elif typ == 'outputs':
                        return self._outputs
            self.problem = MockProblem(parameters_names, outputs_names, minimize_outputs)
            self.parameters_names = parameters_names
            self.outputs_names = outputs_names
        self.epws = self.outputs_optimisation.attrs.get('epws', [])
        self.last_run_type = 'optimisation'
        # Re-apply category mapping if rules are already set on this instance
        if getattr(self, 'epw_mapping_rules', {}) or getattr(self, 'idf_mapping_rules', {}):
            self.apply_category_mapping(df_types=['optimisation'])
        return self.outputs_optimisation

    def get_hourly_df(self, start_date: str='2024-01-01 01', normalize_per_m2: bool = False):
        """
        Transforms the hourly values of outputs_param_simulation to a new pandas DataFrame, saved in the
         internal variable named outputs_param_simulation_hourly.

        :param start_date: the start date for the simulation results, in format 'YYY-MM-DD HH'
        :param normalize_per_m2: if True, divides energy columns by the building floor area.
        """
        if getattr(self, 'outputs_param_simulation', None) is None or self.outputs_param_simulation.empty:
            raise ValueError('No parametric simulation data available to expand hourly.')

        if hasattr(self, 'parameters_list'):
            parameter_columns = [i.name for i in self.parameters_list]
        elif hasattr(self, 'problem') and hasattr(self.problem, 'names'):
            parameter_columns = self.problem.names('inputs')
        elif hasattr(self, 'outputs_param_simulation') and self.outputs_param_simulation.attrs.get('parameters_names'):
            parameter_columns = list(self.outputs_param_simulation.attrs['parameters_names'])
        else:
            parameter_columns = []
        if 'epw' not in parameter_columns:
            parameter_columns.append('epw')
        if 'idf' not in parameter_columns and 'idf' in self.outputs_param_simulation.columns:
            parameter_columns.append('idf')
            
        for extra_col in ['pareto-optimal']:
            if extra_col in self.outputs_param_simulation.columns and extra_col not in parameter_columns:
                parameter_columns.append(extra_col)

        parameter_columns = [c for c in parameter_columns if c in self.outputs_param_simulation.columns]
        
        from accim.parametric_and_optimisation.utils import identify_hourly_columns
        hourly_cols = identify_hourly_columns(self.outputs_param_simulation)
        
        # If no list columns are detected, attempt to read them from the CSV files natively
        if len(hourly_cols) == 0:
            print("[get_hourly_df] No hourly lists found in outputs_param_simulation. Attempting to extract from output CSV files...")
            try:
                source_df = self._attach_hourly_outputs_from_simulation_files(df=self.outputs_param_simulation, file_source='csv', file_output_columns=None)
            except Exception as e:
                raise ValueError(f"Failed to extract hourly columns from simulation files: {e}")
        else:
            source_df = self.outputs_param_simulation
            
        self.outputs_param_simulation_hourly = expand_to_hourly_dataframe(df=source_df, parameter_columns=parameter_columns, start_date=start_date)
        
        if normalize_per_m2:
            if getattr(self, 'outputs_normalized', False):
                print('[!] Warning: outputs_normalized is already True. The argument normalize_per_m2=True will have no effect to prevent double normalization.')
            else:
                self.normalize_outputs(df_types=['parametric_hourly'])
                self.outputs_normalized = False # Revert to False because we only normalized the hourly df

    def get_monthly_df(self, agg_funcs: dict = None, start_date: str='2024-01-01 01', normalize_per_m2: bool = False):
        """
        Transforms the hourly values of outputs_param_simulation to a new pandas DataFrame with monthly aggregated values,
        saved in the internal variable named outputs_param_simulation_monthly.

        :param agg_funcs: a dictionary mapping column names to aggregation functions 
            (e.g. {'DistrictHeating:Facility': 'sum', 'Zone Mean Air Temperature': 'mean'}).
            Defaults to 'mean' for temperature, PMV, PPD, rate, and coefficient, and 'sum' for everything else.
        :param start_date: the start date for the simulation results, in format 'YYY-MM-DD HH'
        :param normalize_per_m2: if True, divides energy columns by the building floor area.
        """
        if getattr(self, 'outputs_param_simulation_hourly', None) is None:
            self.get_hourly_df(start_date=start_date)

        df_hourly = self.outputs_param_simulation_hourly.copy()
        
        if hasattr(self, 'parameters_list'):
            parameter_columns = [i.name for i in self.parameters_list]
        elif hasattr(self, 'problem') and hasattr(self.problem, 'names'):
            parameter_columns = self.problem.names('inputs')
        elif hasattr(self, 'outputs_param_simulation') and self.outputs_param_simulation.attrs.get('parameters_names'):
            parameter_columns = list(self.outputs_param_simulation.attrs['parameters_names'])
        else:
            parameter_columns = []
            
        if 'epw' not in parameter_columns:
            parameter_columns.append('epw')
        if 'idf' not in parameter_columns and 'idf' in df_hourly.columns:
            parameter_columns.append('idf')
            
        parameter_columns = [c for c in parameter_columns if c in df_hourly.columns]
        
        # Identify data columns (excluding parameters, datetime, hour, etc)
        exclude_cols = set(parameter_columns + ['datetime', 'hour'])
        data_columns = [c for c in df_hourly.columns if c not in exclude_cols]
        
        # Determine default aggregations
        default_agg = {}
        for col in data_columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['temperature', 'pmv', 'ppd', 'rate', 'coefficient']):
                default_agg[col] = 'mean'
            else:
                default_agg[col] = 'sum'
                
        if agg_funcs:
            default_agg.update(agg_funcs)
            
        # Extract month from datetime for grouping
        df_hourly['month'] = df_hourly['datetime'].dt.to_period('M')
        groupby_cols = parameter_columns + ['month']
        
        monthly_df = df_hourly.groupby(groupby_cols).agg(default_agg).reset_index()
        self.outputs_param_simulation_monthly = monthly_df
        
        if normalize_per_m2:
            if getattr(self, 'outputs_normalized', False):
                print('[!] Warning: outputs_normalized is already True. The argument normalize_per_m2=True will have no effect to prevent double normalization.')
            else:
                self.normalize_outputs(df_types=['parametric_monthly'])
                self.outputs_normalized = False # Revert because we only normalized the monthly df

    @staticmethod
    def _resolve_simulation_file_path(row: pd.Series, file_source: Literal['csv', 'eso']) -> str:
        error_msg = f"{file_source.upper()} path cannot be resolved for this simulation. If you used keep_sim_files='non-dominated' and this is a dominated simulation, the files were deleted to save space. To analyze this simulation, re-run keeping its files."
        if file_source == 'csv':
            if pd.notna(row.get('simulation_output_csv_path', pd.NA)):
                return str(row['simulation_output_csv_path'])
            if pd.notna(row.get('simulation_directory', pd.NA)):
                return os.path.join(str(row['simulation_directory']), 'eplusout.csv')
            # Parametric runs store the BESOS output dir in 'output_dir'
            if pd.notna(row.get('output_dir', pd.NA)):
                return os.path.join(str(row['output_dir']), 'eplusout.csv')
            raise ValueError(error_msg)
        if file_source == 'eso':
            if pd.notna(row.get('simulation_directory', pd.NA)):
                return os.path.join(str(row['simulation_directory']), 'eplusout.eso')
            if pd.notna(row.get('simulation_output_csv_path', pd.NA)):
                csv_path = str(row['simulation_output_csv_path'])
                return os.path.join(os.path.dirname(csv_path), 'eplusout.eso')
            # Parametric runs store the BESOS output dir in 'output_dir'
            if pd.notna(row.get('output_dir', pd.NA)):
                return os.path.join(str(row['output_dir']), 'eplusout.eso')
            raise ValueError(error_msg)
        raise ValueError(f"Unsupported file_source '{file_source}'. Use 'csv' or 'eso'.")

    @staticmethod
    def _flatten_eso_column_name(col: tuple) -> str:
        (area, variable, units) = col
        return f'{variable} [{units}] | {area}'

    def _extract_hourly_outputs_from_file(self, row: pd.Series, file_source: Literal['csv', 'eso'], file_output_columns: Optional[List[str]]=None, eplus_install_dir: Optional[str]=None, only_run_period: bool=True) -> dict:
        path = self._resolve_simulation_file_path(row=row, file_source=file_source)
        if not os.path.exists(path):
            raise FileNotFoundError(f'Simulation output file not found: {path}')
        if file_source == 'csv':
            df_file = pd.read_csv(path)
            excluded_columns = {'Date/Time', 'date/time'}
            numeric_cols = [c for c in df_file.columns if c not in excluded_columns and pd.api.types.is_numeric_dtype(df_file[c])]
            if file_output_columns is None:
                selected_cols = numeric_cols
            else:
                selected_cols = []
                missing = []
                lower_exact_map = {c.lower(): c for c in df_file.columns}
                for requested in file_output_columns:
                    if requested in df_file.columns:
                        selected_cols.append(requested)
                        continue
                    requested_lower = requested.lower()
                    if requested_lower in lower_exact_map:
                        selected_cols.append(lower_exact_map[requested_lower])
                        continue
                    contains_matches = [c for c in df_file.columns if requested_lower in c.lower()]
                    if len(contains_matches) == 1:
                        selected_cols.append(contains_matches[0])
                    else:
                        missing.append(requested)
                if missing:
                    sample_cols = [c for c in df_file.columns if ':Zone Operative Temperature' in c or 'VRF Heat Pump Cooling Electricity Energy' in c]
                    raise KeyError(f"Requested CSV columns not found in '{path}': {missing}. Example available columns: {sample_cols[:8]}")
            return {c: df_file[c].tolist() for c in selected_cols}
        eso_results = read_eso_using_readvarseso(eso_file_path=path, eplus_install_dir=eplus_install_dir, only_run_period=only_run_period, cleanup=True)
        data_by_freq = eso_results.get('data', {})
        hourly_df = data_by_freq.get('Hourly')
        if hourly_df is None or hourly_df.empty:
            non_empty = [df for df in data_by_freq.values() if isinstance(df, pd.DataFrame) and (not df.empty)]
            if len(non_empty) == 0:
                raise ValueError(f'No readable data found in ESO file: {path}')
            hourly_df = non_empty[0]
        flattened_map = {}
        for col in hourly_df.columns:
            flattened_name = self._flatten_eso_column_name(col)
            flattened_map[flattened_name] = hourly_df[col].tolist()
        if file_output_columns is None:
            return flattened_map
        missing = [c for c in file_output_columns if c not in flattened_map]
        if missing:
            raise KeyError(f"Requested ESO columns not found in '{path}': {missing}")
        return {c: flattened_map[c] for c in file_output_columns}

    def _attach_hourly_outputs_from_simulation_files(self, df: pd.DataFrame, file_source: Literal['csv', 'eso'], file_output_columns: Optional[List[str]]=None, eplus_install_dir: Optional[str]=None, only_run_period: bool=True) -> pd.DataFrame:
        df_augmented = df.copy()
        per_row_outputs = []
        all_output_cols = set()
        for (_, row) in df_augmented.iterrows():
            try:
                row_outputs = self._extract_hourly_outputs_from_file(row=row, file_source=file_source, file_output_columns=file_output_columns, eplus_install_dir=eplus_install_dir, only_run_period=only_run_period)
            except (ValueError, FileNotFoundError) as e:
                row_outputs = {}
            per_row_outputs.append(row_outputs)
            all_output_cols.update(row_outputs.keys())
        for col in all_output_cols:
            target_col = col
            if target_col in df_augmented.columns:
                target_col = f'{target_col}__from_{file_source}'
            df_augmented[target_col] = [row_outputs[col] if col in row_outputs else [] for row_outputs in per_row_outputs]
        return df_augmented

    def get_hourly_df_optimisation(self, only_pareto_optimal: bool=True, epw_filter: Union[str, List[str]]=None, simulation_indices: Optional[List[int]]=None, output_columns: Optional[List[str]]=None, include_summary_columns: bool=True, file_source: Literal['csv', 'eso']='csv', eplus_install_dir: Optional[str]=None, only_run_period: bool=True, start_date: Optional[str]=None, skip_confirmation: bool=False, normalize_per_m2: bool = False):
        """
        Expands optimisation results to hourly frequency and saves the result
        in ``outputs_optimisation_hourly``.

        The method reads hourly values directly from the simulation output files
        (CSV or ESO), giving you full control over which simulations and which
        outputs are expanded to avoid memory saturation with large batches.

        When ``epw_filter`` and ``output_columns`` are both left as None (defaults),
        an automatic size estimate is printed and you will be asked to confirm before
        the expansion proceeds. Use ``skip_confirmation=True`` to bypass this prompt.

        :param only_pareto_optimal: if True (default), only Pareto-optimal (non-dominated)
            solutions are expanded. Set to False to include dominated solutions too.
        :param epw_filter: EPW name or list of EPW names to limit the expansion to
            specific climates. Partial strings are accepted (substring match).
            If None (default), all available EPWs are included.
            Example: ``'Seville'`` or ``['Seville', 'Sydney']``.
        :param simulation_indices: optional list of integer row indices (0-based, from
            ``outputs_optimisation``) to select exactly which simulations to expand.
            This is the most direct way to expand specific runs.
            Overrides ``only_pareto_optimal`` and ``epw_filter`` when provided.

            Example – expand only the 3rd and 7th rows::

                parametric.get_hourly_df_optimisation(simulation_indices=[2, 6])

            Example – expand only the Pareto-optimal rows with index < 10::

                pareto_idx = parametric.outputs_optimisation[
                    parametric.outputs_optimisation['pareto-optimal']
                ].index[:10].tolist()
                parametric.get_hourly_df_optimisation(simulation_indices=pareto_idx)

        :param output_columns: list of column names (or partial names) to extract from
            the simulation output file. If None (default), all numeric hourly columns
            are used. Use ``get_hourly_df_columns()`` first to discover available names.
            Example: ``['Zone Operative Temperature', 'VRF Heat Pump Cooling']``.
        :param include_summary_columns: if True (default), the parameter columns
            (e.g. ``CustAST_m``, ``CustAST_n`` …), ``epw`` and ``pareto-optimal`` are
            preserved as identifier columns in the expanded DataFrame.
        :param file_source: source file to read hourly values from: ``'csv'`` (default)
            or ``'eso'``.
        :param eplus_install_dir: EnergyPlus installation directory, only required
            when ``file_source='eso'``.
        :param only_run_period: when ``file_source='eso'``, keep only the run-period
            data (True by default).
        :param start_date: start date and time for the hourly index in
            ``'YYYY-MM-DD HH'`` format. When None (default), the date is inferred
            automatically from the first simulation CSV file.
        :param skip_confirmation: if True, skips the interactive size-confirmation
            prompt that is shown when ``epw_filter`` and ``output_columns`` are both
            left at their defaults. Useful for running in non-interactive environments
            (scripts, notebooks, CI pipelines).
        """
        if getattr(self, 'last_run_type', None) != 'optimisation':
            raise ValueError('This method requires optimisation outputs. Please run run_optimisation() or load_outputs_optimisation() first.')
        if getattr(self, 'outputs_optimisation', None) is None or self.outputs_optimisation.empty:
            raise ValueError('No optimisation data available to expand hourly.')
        _using_defaults = epw_filter is None and output_columns is None and (simulation_indices is None)
        source_df = self.outputs_optimisation.copy()
        if simulation_indices is not None:
            source_df = source_df.loc[simulation_indices]
        else:
            if only_pareto_optimal and 'pareto-optimal' in source_df.columns:
                source_df = source_df[source_df['pareto-optimal']]
            if epw_filter is not None:
                if isinstance(epw_filter, str):
                    epw_filter = [epw_filter]
                epw_mask = source_df['epw'].astype(str).apply(lambda x: any((f.lower() in x.lower() for f in epw_filter)))
                source_df = source_df[epw_mask]
        if source_df.empty:
            raise ValueError('The applied filters resulted in an empty selection. Relax only_pareto_optimal, epw_filter, or simulation_indices.')
        source_df = self._attach_hourly_outputs_from_simulation_files(df=source_df, file_source=file_source, file_output_columns=output_columns, eplus_install_dir=eplus_install_dir, only_run_period=only_run_period)
        if start_date is None:
            try:
                first_row = self.outputs_optimisation.iloc[0]
                csv_path = self._resolve_simulation_file_path(row=first_row, file_source='csv')
                if os.path.exists(csv_path):
                    _dt_raw = pd.read_csv(csv_path, usecols=['Date/Time'], nrows=1)['Date/Time'].iloc[0]
                    if isinstance(_dt_raw, str):
                        _dt_clean = _dt_raw.strip()
                        (_month_day, _time) = _dt_clean.split()
                        (_month, _day) = _month_day.split('/')
                        _hour = int(_time.split(':')[0])
                        start_date = f'2024-{int(_month):02d}-{int(_day):02d} {_hour:02d}'
            except Exception:
                pass
            if start_date is None:
                start_date = '2024-01-01 01'
        if include_summary_columns:
            if hasattr(self, 'parameters_list'):
                param_cols = [i.name for i in self.parameters_list if i.name in source_df.columns]
            elif hasattr(self, 'problem') and hasattr(self.problem, 'names'):
                param_cols = [c for c in self.problem.names('inputs') if c in source_df.columns]
            elif self.outputs_optimisation.attrs.get('parameters_names'):
                param_cols = [c for c in self.outputs_optimisation.attrs['parameters_names'] if c in source_df.columns]
            else:
                _known_non_param = {'epw', 'pareto-optimal', 'simulation_output_csv_path', 'simulation_directory'}
                if hasattr(self, 'problem') and hasattr(self.problem, 'names'):
                    _known_non_param.update(self.problem.names('outputs') or [])
                param_cols = [c for c in source_df.columns if c not in _known_non_param and (not source_df[c].apply(lambda x: isinstance(x, (list, tuple))).any())]
            for extra_col in ['epw', 'pareto-optimal']:
                if extra_col in source_df.columns and extra_col not in param_cols:
                    param_cols.append(extra_col)
        else:
            param_cols = []
        from accim.parametric_and_optimisation.utils import identify_hourly_columns
        hourly_cols = identify_hourly_columns(source_df)
        n_rows = len(source_df)
        n_hourly = len(hourly_cols)
        if n_hourly > 0:
            sample = source_df[hourly_cols[0]].iloc[0]
            n_steps = len(sample) if isinstance(sample, (list, tuple)) else 8760
        else:
            n_steps = 8760
        total_rows = n_rows * n_steps
        total_cols = len(param_cols) + n_hourly + 2
        approx_mb = total_rows * total_cols * 8 / 1000000.0
        size_msg = f"\n  Simulations selected : {n_rows}\n  Hourly steps per sim : {n_steps}\n  Hourly output columns: {n_hourly}  → {hourly_cols[:5]}{('...' if n_hourly > 5 else '')}\n  Expanded shape       : ~{total_rows:,} rows × {total_cols} cols\n  Approx. memory       : ~{approx_mb:.1f} MB"
        if _using_defaults and (not skip_confirmation):
            print(f'[get_hourly_df_optimisation] Estimated output size:{size_msg}')
            answer = input('\nProceed with expansion? [y/N]: ').strip().lower()
            if answer != 'y':
                print('Expansion cancelled. Use epw_filter, output_columns or simulation_indices to reduce the size.')
                return None
        else:
            print(f'[get_hourly_df_optimisation] Expanding…{size_msg}')
        self.outputs_optimisation_hourly = expand_to_hourly_dataframe(df=source_df, parameter_columns=param_cols, start_date=start_date)
        if normalize_per_m2:
            if getattr(self, 'outputs_normalized', False):
                print('[!] Warning: outputs_normalized is already True. The argument normalize_per_m2=True will have no effect to prevent double normalization.')
            else:
                self.normalize_outputs(df_types=['optimisation_hourly'])
                self.outputs_normalized = False # Revert to False because we only normalized the hourly df

    def get_monthly_df_optimisation(self, agg_funcs: dict = None, **kwargs):
        """
        Transforms the hourly values of outputs_optimisation to a new pandas DataFrame with monthly aggregated values,
        saved in the internal variable named outputs_optimisation_monthly.
        
        :param agg_funcs: a dictionary mapping column names to aggregation functions 
            (e.g. {'DistrictHeating:Facility': 'sum', 'Zone Mean Air Temperature': 'mean'}).
            Defaults to 'mean' for temperature, PMV, PPD, rate, and coefficient, and 'sum' for everything else.
        :param kwargs: arguments passed to get_hourly_df_optimisation if the hourly df needs to be generated.
        """
        if getattr(self, 'outputs_optimisation_hourly', None) is None:
            self.get_hourly_df_optimisation(**kwargs)
            
        if getattr(self, 'outputs_optimisation_hourly', None) is None:
            raise ValueError('Failed to generate hourly dataframe for optimisation.')

        df_hourly = self.outputs_optimisation_hourly.copy()
        
        param_cols = []
        if hasattr(self, 'parameters_list'):
            param_cols = [i.name for i in self.parameters_list]
        elif hasattr(self, 'problem') and hasattr(self.problem, 'names'):
            param_cols = self.problem.names('inputs')
        elif getattr(self, 'outputs_optimisation', None) is not None and self.outputs_optimisation.attrs.get('parameters_names'):
            param_cols = list(self.outputs_optimisation.attrs['parameters_names'])
            
        for extra_col in ['epw', 'idf', 'pareto-optimal']:
            if extra_col not in param_cols and extra_col in df_hourly.columns:
                param_cols.append(extra_col)
                
        param_cols = [c for c in param_cols if c in df_hourly.columns]
        
        # Identify data columns (excluding parameters, datetime, hour, etc)
        exclude_cols = set(param_cols + ['datetime', 'hour'])
        data_columns = [c for c in df_hourly.columns if c not in exclude_cols]
        
        # Determine default aggregations
        default_agg = {}
        for col in data_columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['temperature', 'pmv', 'ppd', 'rate', 'coefficient']):
                default_agg[col] = 'mean'
            else:
                default_agg[col] = 'sum'
                
        if agg_funcs:
            default_agg.update(agg_funcs)
            
        # Extract month from datetime for grouping
        df_hourly['month'] = df_hourly['datetime'].dt.to_period('M')
        groupby_cols = param_cols + ['month']
        
        monthly_df = df_hourly.groupby(groupby_cols).agg(default_agg).reset_index()
        self.outputs_optimisation_monthly = monthly_df
        
        normalize_per_m2 = kwargs.get('normalize_per_m2', False)
        if normalize_per_m2:
            if getattr(self, 'outputs_normalized', False):
                print('[!] Warning: outputs_normalized is already True. The argument normalize_per_m2=True will have no effect to prevent double normalization.')
            else:
                self.normalize_outputs(df_types=['optimisation_monthly'])
                self.outputs_normalized = False # Revert because we only normalized the monthly df

    def get_hourly_df_columns(self):
        """
        Identifies the columns which contain hourly values, and save the names in a list, saved in the
        internal variable named outputs_hourly_columns. Supports both parametric and optimisation runs.
        """
        import os
        import pandas as pd
        if getattr(self, 'last_run_type', None) == 'optimisation':
            if getattr(self, 'outputs_optimisation', None) is None or self.outputs_optimisation.empty:
                raise ValueError('Optimisation outputs not found. Run or load optimisation first.')
            for (_, row) in self.outputs_optimisation.iterrows():
                try:
                    path = self._resolve_simulation_file_path(row=row, file_source='csv')
                    if os.path.exists(path):
                        df_file = pd.read_csv(path, nrows=5)
                        excluded_columns = {'Date/Time', 'date/time'}
                        numeric_cols = [c for c in df_file.columns if c not in excluded_columns and pd.api.types.is_numeric_dtype(df_file[c])]
                        self.outputs_hourly_columns = numeric_cols
                        return self.outputs_hourly_columns
                except Exception:
                    continue
            raise FileNotFoundError('Could not find any valid simulation output CSV files to infer hourly columns.')
        elif getattr(self, 'last_run_type', None) == 'parametric':
            if getattr(self, 'outputs_param_simulation', None) is None or self.outputs_param_simulation.empty:
                raise ValueError('Parametric outputs not found. Run or load parametric simulation first.')
            self.outputs_hourly_columns = identify_hourly_columns(self.outputs_param_simulation)
            return self.outputs_hourly_columns
        else:
            raise ValueError('No previous simulation run type detected. Please run parametric or optimisation first.')


class ParametricSimulation(SimulationBase):
    """
    Specialization of SimulationBase for parametric simulations.

    This class handles parameter sampling, running multiple simulations with different
    parameter values, and collecting/analyzing parametric simulation results.

    Parameters specific to parametric simulations:
    - outputs_param_simulation: main results DataFrame
    - outputs_param_simulation_hourly: hourly-level expanded results
    - outputs_param_simulation_monthly: monthly-level aggregated results
    - outputs_param_simulation_filepath: path to saved results

    Methods specific to parametric simulations:
    - sampling_*(): parameter sampling strategies
    - run_parametric_simulation(): execute parametric simulation
    - load_outputs_parametric(): restore previous parametric results

    .. versionadded:: 0.8.0
        Extracted from OptimParamSimulation for better separation of concerns.
    """

    def __init__(self, *args, **kwargs):
        """Initialize ParametricSimulation instance."""
        super().__init__(*args, **kwargs)
        # Parametric-specific attributes
        self.outputs_param_simulation = None
        self.outputs_param_simulation_hourly = None
        self.outputs_param_simulation_monthly = None
        self.outputs_param_simulation_filepath = None


class OptimisationSimulation(SimulationBase):
    """
    Specialization of SimulationBase for multi-objective optimization.

    This class handles multi-objective optimization using various genetic/evolutionary
    algorithms (NSGA-II, EpsNSGAII, etc.), Pareto analysis, and optimization-specific
    output management.

    Parameters specific to optimization:
    - outputs_optimisation: complete evaluation history (dominated + non-dominated)
    - outputs_optimisation_filepath: path to saved results
    - optimisation_csv_paths_non_dominated: paths to non-dominated simulation outputs
    - optimisation_csv_paths_dominated: paths to dominated simulation outputs
    - optimisation_csv_paths_non_dominated_by_epw: non-dominated paths grouped by EPW
    - optimisation_csv_paths_dominated_by_epw: dominated paths grouped by EPW
    - evaluators: tracking of besos evaluators per IDF/EPW combination

    Methods specific to optimization:
    - run_optimisation(): execute multi-objective optimization
    - estimate_optimisation_sims(): preview expected run count
    - load_outputs_optimisation(): restore previous optimization results
    - get_hourly_df_optimisation(): retrieve hourly data from optimization
    - get_monthly_df_optimisation(): retrieve monthly data from optimization

    .. versionadded:: 0.8.0
        Extracted from OptimParamSimulation for better separation of concerns.
    """

    def __init__(self, *args, **kwargs):
        """Initialize OptimisationSimulation instance."""
        super().__init__(*args, **kwargs)
        # Optimization-specific attributes
        self.outputs_optimisation = None
        self.outputs_optimisation_filepath = None
        self.outputs_optimisation_hourly = None
        self.outputs_optimisation_monthly = None
        self.optimisation_csv_paths_non_dominated = []
        self.optimisation_csv_paths_dominated = []
        self.optimisation_csv_paths_non_dominated_by_epw = {}
        self.optimisation_csv_paths_dominated_by_epw = {}
        self.evaluators = {}


# Backward compatibility alias
# Using factory function allows auto-selection based on usage patterns in future versions
OptimParamSimulation = ParametricSimulation


class AccimPredefModelsParamSim(ParametricSimulation):

    def __init__(self, buildings: Union[Any, List]=None, epws: list=None, output_type: str='standard', output_keep_existing: bool=False, output_freqs: list=['hourly'], ScriptType: str='vrf_mm', SupplyAirTempInputMethod: str='temperature difference', debugging: bool=False, **kwargs):
        if buildings is None and 'building' in kwargs:
            buildings = kwargs['building']
        super().__init__(buildings=buildings, epws=epws, parameters_type='accim predefined model', output_type=output_type, output_keep_existing=output_keep_existing, output_freqs=output_freqs, ScriptType=ScriptType, SupplyAirTempInputMethod=SupplyAirTempInputMethod, debugging=debugging)
        for b in self.buildings:
            accis.modifyAccis(idf=b, ComfStand=99, ComfMod=3, CAT=80, HVACmode=2, VentCtrl=0)

