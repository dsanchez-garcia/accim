# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Add the Adaptive-Comfort-Control Implementation Script (ACCIS) to EnergyPlus models.

The ACCIS is an EnergyManagementSystem script that applies adaptive setpoint temperatures.

- :class:`AddAccis` adds it to the IDF files of the working folder (or those given) and writes an output
  IDF for each combination of the arguments (comfort standard, category, comfort mode, HVAC mode...).
- :func:`add_accis_to_idf` adds it to an IDF object of eppy or besos, and :func:`modify_accis` sets the
  arguments of that model.
"""

import os
import warnings
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd

from accim import __version__
from accim._deprecation import rename_legacy_kwargs, warn_deprecated
from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS
from accim.energyplus import idd_path, unsupported_version_message
from accim.sim import prompts
from accim.sim.arguments import (
    LEGACY_ARGUMENT_NAMES,
    OUTPUT_FREQUENCIES,
    OUTPUT_TYPES,
    SCRIPT_TYPES,
    SUPPLY_AIR_TEMP_INPUT_METHODS,
    as_list,
    check_choice,
    is_mixed_mode,
    normalise_energyplus_version,
    normalise_temp_ctrl,
    to_bool,
    to_day_of_year,
)
from accim.sim.build import add_accis_objects, add_outputs
from accim.sim.ems.inputs import (
    check_zone_arguments,
    input_programs,
    input_values,
    resolve_zone_arguments,
    set_inputs,
    zone_names,
)
from accim.sim.ems.setast import MODULAR_COMFORT_MODES, depends_on_comfort_mode, master_program_lines, subprograms
from accim.sim.generation import (
    GenerationArguments,
    IdfWriter,
    OutputIdfs,
    combinations,
    output_name,
    zone_arguments_errors,
    zone_input_arguments,
)
from accim.sim.idf_tools import add_program, copy_idf, idf_text, replace_program_lines, set_program_lines
from accim.sim.model import AccimModel
from accim.sim.outputs import OUTPUT_DATAFRAME_COLUMNS, enable_sizing_calculations, output_variables_dataframe
from accim.sim.targets import resolve_targets

__all__ = ['AddAccis', 'add_accis_to_idf', 'addAccis', 'gen_outputs_df', 'load_idf', 'modify_accis']

Number = Union[int, float]

BANNER = (
    '\n--------------------------------------------------------'
    f'\nAdaptive-Comfort-Control-Implemented Model (ACCIM) v{__version__}'
    '\n--------------------------------------------------------'
    '\n\nThis tool allows to apply adaptive setpoint temperatures. '
    '\nFor further information, please read the documentation: '
    '\nhttps://accim.readthedocs.io/en/master/'
    '\nFor a visual understanding of the tool, please visit the following jupyter notebooks:'
    '\n-    Using AddAccis() to apply adaptive setpoint temperatures'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/addAccis/using_addAccis.html'
    '\n-    Using rename_epw_files() to rename the EPWs for proper data analysis after simulation'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/rename_epw_files/using_rename_epw_files.html'
    '\n-    Using run_ep() to directly run simulations with EnergyPlus'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/runEp/using_runEp.html'
    '\n-    Using the class Table() for data analysis'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/Table/using_Table.html'
    '\n-    Full example'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/full_example_IBPSA/full_example_IBPSA.html'
    '\n'
    '\nStarting with the process.'
)
_START_MODEL = '\n=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================\n'
_END_MODEL = '\n=======================END OF GENERIC IDF FILE GENERATION PROCESS=======================\n'
_START_OUTPUTS = '\n=======================START OF OUTPUT IDF FILES GENERATION PROCESS=======================\n'
_END_OUTPUTS = '\n=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================\n'


class _Arguments(dict):
    """The arguments of an ACCIS run. The names of accim 0.x also work, with a DeprecationWarning."""

    def _new_name(self, key) -> Optional[str]:
        new = LEGACY_ARGUMENT_NAMES.get(key)
        return new if new is not None and dict.__contains__(self, new) else None

    def __missing__(self, key):
        new = self._new_name(key)
        if new is None:
            raise KeyError(key)
        warn_deprecated(f'arguments[{key!r}]', f'arguments[{new!r}]')
        return dict.__getitem__(self, new)

    def __contains__(self, key) -> bool:
        return dict.__contains__(self, key) or self._new_name(key) is not None

    def get(self, key, default=None):
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        new = self._new_name(key)
        if new is None:
            return default
        warn_deprecated(f'arguments[{key!r}]', f'arguments[{new!r}]')
        return dict.__getitem__(self, new)


# ----------------------------------------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------------------------------------

def _amend_designbuilder_version(path: Union[str, os.PathLike]) -> None:
    """Replace the version of the IDF files of DesignBuilder 7 ('9.4.0.002') with '9.4'."""
    with open(path, 'rb') as file:
        data = file.read()
    if b'Version, 9.4.0.002' in data:
        with open(path, 'wb') as file:
            file.write(data.replace(b'Version, 9.4.0.002', b'Version, 9.4'))


def _set_idd(idf_class, path: str) -> None:
    """Set the IDD of eppy, which can only read the models of one EnergyPlus version in a Python session."""
    current = idf_class.iddname
    if current is None:
        idf_class.setiddname(path)
    elif Path(current).resolve() != Path(path).resolve():
        raise ValueError(
            f'eppy is already using the IDD {current} in this Python session, and it cannot read the models of '
            f'other EnergyPlus versions (whose IDD is {path}). Use a new Python session for them.'
        )


def load_idf(path: Union[str, os.PathLike], energyplus_version: str = 'auto'):
    """Read an IDF file: with besos (which finds the IDD of its version) if ``energyplus_version`` is 'auto',
    or with eppy and the IDD of ``energyplus_version`` otherwise.

    :param path: The path of the IDF file.
    :param energyplus_version: 'auto' or an EnergyPlus version, such as '25.1'.
    """
    _amend_designbuilder_version(path)
    if normalise_energyplus_version(energyplus_version) == 'auto':
        from besos.eppy_funcs import get_building
        return get_building(str(path))
    from eppy.modeleditor import IDF
    _set_idd(IDF, idd_path(energyplus_version))
    return IDF(str(path))


def _idf_version(idf) -> str:
    return '.'.join(str(i) for i in idf.idd_version[:2])


def _input_files(idfs: Optional[Iterable[Union[str, os.PathLike]]]) -> List[str]:
    """The input IDF files: those given, or those in the working folder, without the output IDFs."""
    if idfs is None:
        candidates = sorted(os.listdir())
    else:
        candidates = [os.fspath(f) for f in ([idfs] if isinstance(idfs, (str, os.PathLike)) else idfs)]
    files = [f for f in candidates
             if f.endswith('.idf') and '[' not in os.path.basename(f) and '_pymod' not in os.path.basename(f)]
    if not files:
        raise FileNotFoundError('No idf files were found. There must be at least 1 idf file located at the path '
                                'where this script is being run.')
    return files


# ----------------------------------------------------------------------------------------------------------
# Arguments
# ----------------------------------------------------------------------------------------------------------

def _check_model_arguments(script_type, supply_air_temp_input_method, output_type, output_freqs, temp_ctrl) -> Tuple:
    """Check the arguments of the models; return output_type, output_freqs and temp_ctrl normalised."""
    check_choice('script_type', script_type, SCRIPT_TYPES)
    if script_type.startswith('vrf'):
        check_choice('supply_air_temp_input_method', supply_air_temp_input_method, SUPPLY_AIR_TEMP_INPUT_METHODS)
    check_choice('output_type', output_type.lower() if isinstance(output_type, str) else output_type, OUTPUT_TYPES)
    if output_freqs is None:
        raise ValueError(f'output_freqs is required: a list such as {list(OUTPUT_FREQUENCIES[:2])}.')
    output_freqs = as_list(output_freqs)
    invalid = [f for f in output_freqs if not isinstance(f, str) or f.lower() not in OUTPUT_FREQUENCIES]
    if invalid:
        raise ValueError(f'{invalid} are not valid output_freqs. Valid values: {list(OUTPUT_FREQUENCIES)}.')
    return output_type.lower(), output_freqs, normalise_temp_ctrl(temp_ctrl)


def _print_model_arguments(script_type, supply_air_temp_input_method, output_type, output_freqs,
                           energyplus_version, temp_ctrl) -> None:
    print('Basic input data:')
    print(f'Script type is: {script_type}')
    if script_type.startswith('vrf'):
        print(f'Supply Air Temperature Input Method is: {supply_air_temp_input_method}')
    print(f'Output type is: {output_type}')
    print('Output frequencies are: ')
    print(output_freqs)
    if energyplus_version != 'auto':
        print(f'EnergyPlus version is: {energyplus_version}')
    print(f'Temperature Control method is: {temp_ctrl}')


def _check_version(version: str) -> None:
    if version not in SUPPORTED_ENERGYPLUS_VERSIONS:
        raise ValueError(unsupported_version_message(version))


def _to_confirmation(value: Any) -> bool:
    if value is None:
        return input('Do you still want to run ACCIS? [y/n]: ') == 'y'
    if isinstance(value, str):
        return value.lower() in ('y', 'yes', 'true')
    return bool(value)


def _warn_hvac_zone_map(hvac_zone_map: Optional[Dict[str, str]]) -> None:
    """hvac_zone_map is no longer used: 'ex_mm' does not look for the HVAC equipment of each zone."""
    if hvac_zone_map is not None:
        warnings.warn(
            "hvac_zone_map is deprecated since accim 1.0.0 and has no effect: in mixed mode with the existing HVAC "
            "systems (script type 'ex_mm'), accim reads whether the HVAC system of each zone is on from the load "
            'that its thermostat asks for, whatever its equipment, so it no longer needs the zone of each HVAC '
            'object.',
            DeprecationWarning,
            stacklevel=3,
        )


# ----------------------------------------------------------------------------------------------------------
# AddAccis: files
# ----------------------------------------------------------------------------------------------------------

class AddAccis:
    """Add the ACCIS to IDF files and write an output IDF for each combination of the arguments.

    The input IDFs are those given in ``idfs`` or, by default, all the IDF files in the working folder
    (except the output IDFs, whose names contain '['). The output IDFs are written next to them, with
    names that give their arguments, such as ``Model[CS_INT EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf``.

    The missing arguments are asked: those of the models if ``script_type``, ``output_type``,
    ``output_freqs``, ``output_keep_existing``, ``temp_ctrl`` or (with VRF systems)
    ``supply_air_temp_input_method`` is None, and those of the output IDFs if ``comf_stand``, ``cat``,
    ``comf_mod`` or (in mixed mode) ``hvac_mode`` or ``vent_ctrl`` is None.

    :param idfs: The IDF files. By default, those in the working folder.
    :param script_type: 'vrf_ac' (a new VRF system in each occupied zone, full air-conditioning), 'vrf_mm' (VRF
        system, mixed mode), 'ex_ac' (the existing HVAC systems, full air-conditioning) or 'ex_mm' (existing HVAC
        systems, mixed mode).
    :param supply_air_temp_input_method: 'supply air temperature' or 'temperature difference' (VRF systems only).
    :param output_type: 'standard', 'simplified', 'detailed' or 'custom' (which asks which outputs to keep).
    :param output_freqs: The reporting frequencies of the outputs: a list of 'timestep', 'hourly', 'daily',
        'monthly' and 'runperiod'.
    :param output_keep_existing: True to keep the Output:Variable objects of the models.
    :param output_gen_dataframe: True to keep a DataFrame with the Output:Variable objects in ``df_outputs``.
    :param output_take_dataframe: A DataFrame like ``df_outputs``, filtered to keep the outputs wanted, which
        replace those of the models.
    :param energyplus_version: '9.1' to '26.2', or 'auto' to read it from the models.
    :param temp_ctrl: 'temperature' (or 'temp') for adaptive setpoint temperatures, or 'pmv' for setpoints based
        on the PMV of Fanger.
    :param vrf_schedule: The availability schedule of the VRF systems.
    :param comf_stand: The comfort standards (a list): 0 = ESP CTE; 1 = INT EN16798-1; 2 = INT ASHRAE55;
        3 = JPN Rijal; 4 = CHN GBT50785 Cold; 5 = CHN GBT50785 HotMild; 6 = CHN Yang; 7 = IND IMAC C NV;
        8 = IND IMAC C MM; 9 = IND IMAC R 7DRM; 10 = IND IMAC R 30DRM; 11 = IND Dhaka; 12 = ROM Udrea;
        13 = AUS Williamson; 14 = AUS DeDear; 15 = BRA Rupp NV; 16 = BRA Rupp AC; 17 = MEX Oropeza Arid;
        18 = MEX Oropeza DryTropic; 19 = MEX Oropeza Temperate; 20 = MEX Oropeza HumTropic;
        21 = CHL Perez-Fargallo; 22 = INT ISO7730; 99 = CUSTOM.
    :param cat: The categories (a list): 1, 2 or 3 (CAT I, II, III), or 80, 85 or 90 (% of acceptability).
    :param cat_cool_offset: An offset summed to the cooling setpoint offset of the category.
    :param cat_heat_offset: An offset summed to the heating setpoint offset of the category.
    :param comf_mod: The comfort modes (a list): 0 or 0.X = static; 1 or 1.X = adaptive when applicable,
        otherwise the local static model; 2 = adaptive when applicable, otherwise the international static
        model; 3 = adaptive when applicable, otherwise the adaptive setpoints extended horizontally.
    :param setpoint_acc: The accuracy of the setpoints: 2 rounds them to every half degree, 10 to the first
        decimal...
    :param cust_ast_acst_aul: Custom model (comf_stand 99): upper applicability limit of the cooling setpoint.
    :param cust_ast_acst_all: Custom model: lower applicability limit of the cooling setpoint.
    :param cust_ast_ahst_aul: Custom model: upper applicability limit of the heating setpoint.
    :param cust_ast_ahst_all: Custom model: lower applicability limit of the heating setpoint.
    :param cust_ast_m: Custom model: slope m of the comfort temperature (m * running mean outdoor temperature + n).
    :param cust_ast_n: Custom model: intercept n of the comfort temperature.
    :param cust_ast_acst_offset: Custom model: offset of the cooling setpoint from the comfort temperature (positive).
    :param cust_ast_ahst_offset: Custom model: offset of the heating setpoint from the comfort temperature (negative).
    :param cool_season_start: The start of the cooling season (a date 'dd/mm' or a day of the year), used by
        some static models.
    :param cool_season_end: The end of the cooling season.
    :param hvac_mode: The HVAC modes (a list): 0 = fully air-conditioned; 1 = naturally ventilated; 2 = mixed mode.
    :param vent_ctrl: The ventilation controls (a list). With HVAC mode 1: 0 = ventilates above the comfort
        temperature; 1 = above the upper comfort limit. With HVAC mode 2: 0 = above the comfort temperature,
        opening the windows fully; 1 = above the lower comfort limit, opening them fully; 2 and 3 = like 0 and 1,
        with the customised venting opening factor.
    :param max_temp_diff_vof: The maximum temperature difference of the venting opening factor (greater than 0).
    :param min_temp_diff_vof: The minimum temperature difference of the venting opening factor.
    :param multiplier_vof: The multiplier of the venting opening factor (between 0 and 1).
    :param vst_offset: The offsets of the ventilation setpoint temperature (a list).
    :param min_ot_offset: The offsets of the minimum outdoor temperature for ventilation (a list).
    :param max_wind_speed: The maximum wind speeds for ventilation (a list).
    :param ast_tol_start: The first tolerance of the setpoints.
    :param ast_tol_end_input: The last tolerance of the setpoints.
    :param ast_tol_steps: The step between tolerances.
    :param name_suffix: A suffix for the names of the output IDFs.
    :param verbose_mode: True to print the process.
    :param confirm_gen: True to write the output IDFs without asking; None to ask.
    :param eer: The energy efficiency ratio of the VRF systems.
    :param cop: The coefficient of performance of the VRF systems.
    :param make_averages: True to add the building averages of the hours of each zone and of some outputs.
    :param debugging: True to make EnergyPlus write the EDD file of the EMS.
    :param hvac_zone_map: Deprecated since accim 1.0.0, without effect: 'ex_mm' reads whether the HVAC system of
        each zone is on from the load that its thermostat asks for, so it no longer needs the zone of each existing
        HVAC object.
    :param zone_arguments: The arguments of some zones, which are the same in all the output IDFs:
        ``{zone: {argument: value}}``, for instance ``{'Block1:Zone1': {'comf_stand': 2, 'cat': 80,
        'comf_mod': 3}}``. The zones are the occupied zones, given by their names (or '<space> <people>', as in
        the dictionaries of :func:`accim.sim.apmv.apply_apmv_setpoints`); the arguments are those of
        :func:`modify_accis`, with one value each (the tolerance of the setpoints is ``ast_tol``). The other
        arguments of these zones, and the arguments of the other zones, are those of each output IDF, whose name
        does not change. Each zone needs a valid combination of comfort standard, category and comfort mode, and
        the HVAC mode and ventilation control of mixed mode only with 'vrf_mm' and 'ex_mm'. Only with temperature
        control (``temp_ctrl`` 'temperature').
    :ivar arguments: The arguments, after asking the missing ones.
    :ivar input_idfs: The input IDFs, {'input IDF name': IDF object}.
    :ivar occupied_zones: The occupied zones of each input IDF, as in the EMS objects.
    :ivar occupied_zones_original_name: The occupied zones of each input IDF.
    :ivar windows_and_doors: The windows and doors that open in each input IDF, as in the EMS objects (mixed mode).
    :ivar windows_and_doors_original_name: The windows and doors that open in each input IDF (mixed mode).
    :ivar zone_arguments: The arguments of the zones of ``zone_arguments`` in each input IDF, by the names of the
        zones in the EMS objects: ``{input IDF name: {zone: {argument: value}}}``.
    :ivar output_idfs: The output IDFs, {'output IDF file name': IDF object} (each one is read when it is used;
        ``output_idfs.paths`` has their paths).
    :ivar df_outputs: The DataFrame of Output:Variable objects (argument ``output_gen_dataframe``).
    """

    def __init__(
        self,
        idfs: Optional[Sequence[Union[str, os.PathLike]]] = None,
        script_type: Optional[str] = None,
        supply_air_temp_input_method: Optional[str] = None,
        output_type: Optional[str] = None,
        output_freqs: Optional[Sequence[str]] = None,
        output_keep_existing: Optional[bool] = None,
        output_gen_dataframe: Optional[bool] = None,
        output_take_dataframe: Optional[pd.DataFrame] = None,
        energyplus_version: str = 'auto',
        temp_ctrl: Optional[str] = None,
        vrf_schedule: str = 'On 24/7',
        comf_stand: Optional[Sequence[int]] = None,
        cat: Optional[Sequence[Number]] = None,
        cat_cool_offset: Number = 0,
        cat_heat_offset: Number = 0,
        comf_mod: Optional[Sequence[Number]] = None,
        setpoint_acc: Number = 10000,
        cust_ast_acst_aul: Number = 0,
        cust_ast_acst_all: Number = 0,
        cust_ast_ahst_aul: Number = 0,
        cust_ast_ahst_all: Number = 0,
        cust_ast_m: Number = 0,
        cust_ast_n: Number = 0,
        cust_ast_acst_offset: Number = 0,
        cust_ast_ahst_offset: Number = 0,
        cool_season_start: Union[int, str] = 121,
        cool_season_end: Union[int, str] = 274,
        hvac_mode: Optional[Sequence[int]] = None,
        vent_ctrl: Optional[Sequence[int]] = None,
        max_temp_diff_vof: Number = 6,
        min_temp_diff_vof: Number = 1,
        multiplier_vof: Number = 0.25,
        vst_offset: Sequence[Number] = (0,),
        min_ot_offset: Sequence[Number] = (50,),
        max_wind_speed: Sequence[Number] = (50,),
        ast_tol_start: Number = 0.1,
        ast_tol_end_input: Number = 0.1,
        ast_tol_steps: Number = 0.1,
        name_suffix: str = '',
        verbose_mode: bool = True,
        confirm_gen: Optional[bool] = None,
        eer: Number = 2,
        cop: Number = 2.1,
        make_averages: bool = False,
        debugging: bool = False,
        hvac_zone_map: Optional[Dict[str, str]] = None,
        zone_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        files = _input_files(idfs)
        print(BANNER)
        _warn_hvac_zone_map(hvac_zone_map)
        self.verbose_mode = verbose_mode
        checked_zone_arguments = check_zone_arguments(zone_arguments)

        if (script_type is None or output_type is None or output_freqs is None or output_keep_existing is None
                or temp_ctrl is None
                or (supply_air_temp_input_method is None and script_type not in ('ex_mm', 'ex_ac'))):
            asked = prompts.ask_model_arguments()
            script_type = asked['script_type']
            supply_air_temp_input_method = asked['supply_air_temp_input_method']
            output_keep_existing = asked['output_keep_existing']
            output_type = asked['output_type']
            output_freqs = asked['output_freqs']
            output_gen_dataframe = asked['output_gen_dataframe']
            energyplus_version = asked['energyplus_version']
            temp_ctrl = asked['temp_ctrl']
        energyplus_version = normalise_energyplus_version(energyplus_version)
        output_type, output_freqs, temp_ctrl = _check_model_arguments(
            script_type, supply_air_temp_input_method, output_type, output_freqs, temp_ctrl)
        if checked_zone_arguments and temp_ctrl == 'pmv':
            raise ValueError("zone_arguments needs temp_ctrl 'temperature': with 'pmv', the Fanger thermostats "
                             "control the zones and the arguments of the ACCIS are not used.")
        if verbose_mode:
            _print_model_arguments(script_type, supply_air_temp_input_method, output_type, output_freqs,
                                   energyplus_version, temp_ctrl)
        output_keep_existing = to_bool(output_keep_existing, 'output_keep_existing')
        # The outputs chosen with 'custom' are not known before
        output_gen_dataframe = False if output_type == 'custom' else bool(output_gen_dataframe)

        self.arguments = _Arguments(
            script_type=script_type,
            supply_air_temp_input_method=supply_air_temp_input_method,
            output_type=output_type,
            output_freqs=output_freqs,
            output_keep_existing=output_keep_existing,
            output_gen_dataframe=output_gen_dataframe,
            output_take_dataframe=output_take_dataframe,
            energyplus_version=energyplus_version,
            temp_ctrl=temp_ctrl,
        )
        self.input_idfs: Dict[str, Any] = {}
        self.occupied_zones: Dict[str, List[str]] = {}
        self.occupied_zones_original_name: Dict[str, List[str]] = {}
        self.windows_and_doors: Dict[str, List[str]] = {}
        self.windows_and_doors_original_name: Dict[str, List[str]] = {}
        self.zone_arguments: Dict[str, Dict[str, Dict[str, Any]]] = {}

        models = []
        not_working = []
        dataframes = []
        idf_class = None
        found_zones = set()
        for file in files:
            stem = file[:-len('.idf')]
            self._log(_START_MODEL, 'Starting with file:', stem)
            idf0 = load_idf(file, energyplus_version)
            idf_class = type(idf0)
            self._log(f'IDD location is: {idf0.iddname}')
            version = _idf_version(idf0)
            _check_version(version)
            if self.arguments['energyplus_version'] == 'auto':
                self.arguments['energyplus_version'] = version
            idf = copy_idf(idf0)
            model = AccimModel(idf, script_type, temp_ctrl, verbose_mode=verbose_mode,
                               hvac_zone_map=hvac_zone_map, name=stem)
            self.input_idfs[stem] = idf0
            self.occupied_zones[stem] = model.occupied_zones
            self.occupied_zones_original_name[stem] = model.occupied_zones_orig
            if model.is_mixed_mode:
                self.windows_and_doors[stem] = model.windows
                self.windows_and_doors_original_name[stem] = model.windows_orig
            names = zone_names(model.targets)
            aliases = {str(alias).upper() for zone_aliases in names.values() for alias in zone_aliases}
            found_zones.update(key for key in checked_zone_arguments if str(key).upper() in aliases)
            self.zone_arguments[stem] = resolve_zone_arguments(checked_zone_arguments, names, strict=False)
            if self.zone_arguments[stem]:
                self._log('The zones with their own arguments are:',
                          *(f'{zone}: {arguments}' for zone, arguments in self.zone_arguments[stem].items()))
            if model.not_working:
                not_working.append(stem)
                continue
            add_accis_objects(model, supply_air_temp_input_method, vrf_schedule=vrf_schedule, eer=eer, cop=cop,
                              make_averages=make_averages, debugging=debugging)
            add_outputs(model, output_type, output_freqs, output_keep_existing, output_take_dataframe, file=stem)
            if output_gen_dataframe:
                dataframes.append(output_variables_dataframe(idf, file=stem))
            enable_sizing_calculations(model)
            # The text of the model is kept instead of the model, which needs much more memory
            models.append((stem, idf_text(idf)))
            self._log('Ending with file:', stem, _END_MODEL)

        missing_zones = [key for key in checked_zone_arguments if key not in found_zones]
        if missing_zones:
            raise ValueError(f'The zones {missing_zones} of zone_arguments are not occupied zones of the input IDFs. '
                             f'Their occupied zones are {self.occupied_zones_original_name}.')
        if output_gen_dataframe:
            self.df_outputs = (pd.concat(dataframes) if dataframes
                               else pd.DataFrame(columns=['file'] + OUTPUT_DATAFRAME_COLUMNS))
        self._log('The following IDFs will not work, so no output IDFs will be generated from them:',
                  *(not_working or ['None']))
        self._log(_START_OUTPUTS)

        generation = self._generation_arguments(
            script_type, comf_stand=comf_stand, cat=cat, cat_cool_offset=cat_cool_offset,
            cat_heat_offset=cat_heat_offset, comf_mod=comf_mod, setpoint_acc=setpoint_acc,
            cust_ast_acst_aul=cust_ast_acst_aul, cust_ast_acst_all=cust_ast_acst_all,
            cust_ast_ahst_aul=cust_ast_ahst_aul, cust_ast_ahst_all=cust_ast_ahst_all, cust_ast_m=cust_ast_m,
            cust_ast_n=cust_ast_n, cust_ast_acst_offset=cust_ast_acst_offset,
            cust_ast_ahst_offset=cust_ast_ahst_offset, cool_season_start=cool_season_start,
            cool_season_end=cool_season_end, hvac_mode=hvac_mode, vent_ctrl=vent_ctrl,
            max_temp_diff_vof=max_temp_diff_vof, min_temp_diff_vof=min_temp_diff_vof, multiplier_vof=multiplier_vof,
            vst_offset=vst_offset, min_ot_offset=min_ot_offset, max_wind_speed=max_wind_speed,
            ast_tol_start=ast_tol_start, ast_tol_end_input=ast_tol_end_input, ast_tol_steps=ast_tol_steps,
            name_suffix=name_suffix)
        self.arguments.update({k: v for k, v in vars(generation).items()})
        self.arguments.update(verbose_mode=verbose_mode, confirm_gen=confirm_gen, zone_arguments=zone_arguments)

        paths = self._write_output_idfs(models, generation, temp_ctrl, confirm_gen, idf_class,
                                        is_mixed_mode(script_type))
        self.output_idfs = OutputIdfs(paths, idf_class)
        self._log(_END_OUTPUTS)

    def _log(self, *lines) -> None:
        if self.verbose_mode:
            print(*lines, sep='\n')

    @staticmethod
    def _generation_arguments(script_type: str, **kwargs) -> GenerationArguments:
        """The arguments of the output IDFs, asking them if some are missing."""
        name_suffix = kwargs.pop('name_suffix')
        needed = ['comf_stand', 'cat', 'comf_mod'] + (['hvac_mode', 'vent_ctrl'] if is_mixed_mode(script_type) else [])
        if any(kwargs[name] is None for name in needed):
            kwargs = prompts.ask_generation_arguments(script_type)
        if not is_mixed_mode(script_type):
            return GenerationArguments.air_conditioned(**kwargs, name_suffix=name_suffix)
        return GenerationArguments(**kwargs, name_suffix=name_suffix)

    def _check_zone_arguments(self, models, generation: GenerationArguments, combos, mixed_mode: bool) -> None:
        """Check that the zones of zone_arguments have setpoints in all the output IDFs."""
        errors = []
        for stem, _ in models:
            for zone, arguments in self.zone_arguments.get(stem, {}).items():
                for combination in combos:
                    reasons = zone_arguments_errors(zone_input_arguments(generation, combination, arguments),
                                                    mixed_mode)
                    if reasons:
                        errors.append(f'zone {zone} of {stem}, in {output_name(stem, combination)}: '
                                      f'{"; ".join(reasons)}')
        if errors:
            raise ValueError('The arguments of some zones of zone_arguments are not valid (give the comfort '
                             'standard, category and comfort mode of each of these zones):\n' + '\n'.join(errors))

    def _write_output_idfs(self, models, generation: GenerationArguments, temp_ctrl: str, confirm_gen,
                           idf_class, mixed_mode: bool) -> Dict[str, str]:
        combos = list(combinations(generation, temp_ctrl))
        self._check_zone_arguments(models, generation, combos, mixed_mode)
        names = [output_name(stem, c, generation.name_suffix) for stem, _ in models for c in combos]
        self._log('The list of output IDFs is going to be:', *names,
                  f'And the total number of output IDFs is going to be {len(names)}')
        paths: Dict[str, str] = {}
        if not _to_confirmation(confirm_gen):
            self._log('IDF generation has been shut down')
            return paths
        self._log('Generating the following output IDF files:')
        for stem, text in models:
            writer = IdfWriter(idf_class(StringIO(text)), generation, temp_ctrl, self.zone_arguments.get(stem))
            for combination in combos:
                path = output_name(stem, combination, generation.name_suffix)
                self._log(path)
                writer.write(path, combination)
                paths[os.path.basename(path)] = os.path.abspath(path)
        return paths


class addAccis(AddAccis):  # noqa: N801 (the name of accim 0.x)
    """Deprecated alias of :class:`AddAccis`, which also accepts the argument names of accim 0.x
    (``ScriptType``, ``Output_type``, ``ComfStand``...)."""

    def __init__(self, *args, **kwargs):
        warn_deprecated('accim.sim.accis.addAccis', 'accim.sim.accis.AddAccis')
        super().__init__(*args, **rename_legacy_kwargs(kwargs, LEGACY_ARGUMENT_NAMES, 'addAccis'))


# ----------------------------------------------------------------------------------------------------------
# IDF objects
# ----------------------------------------------------------------------------------------------------------

def add_accis_to_idf(
    idf,
    script_type: Optional[str] = None,
    supply_air_temp_input_method: Optional[str] = None,
    output_type: Optional[str] = None,
    output_freqs: Optional[Sequence[str]] = None,
    output_keep_existing: Optional[bool] = None,
    output_take_dataframe: Optional[pd.DataFrame] = None,
    energyplus_version: Optional[str] = None,
    temp_ctrl: Optional[str] = None,
    vrf_schedule: str = 'On 24/7',
    verbose_mode: bool = True,
    eer: Number = 2,
    cop: Number = 2.1,
    make_averages: bool = False,
    debugging: bool = False,
    hvac_zone_map: Optional[Dict[str, str]] = None,
) -> AccimModel:
    """Add the ACCIS to an IDF object of eppy or besos (in place).

    The arguments of the ACCIS (comfort standard, category, HVAC mode...) are those of :func:`modify_accis`
    (by default, ComfStand 1, CAT 1, ComfMod 2, HVACmode 2 and VentCtrl 0, in all the zones), which can change
    them later, also for each zone. The arguments are those of :class:`AddAccis`. With the VRF systems
    (``script_type`` 'vrf_ac' and 'vrf_mm'), which are autosized, the zone, system and plant sizing calculations of
    the model are enabled, as :class:`AddAccis` does; with the existing HVAC systems, the sizing calculations do not
    change.

    :param idf: The IDF object.
    :param energyplus_version: The EnergyPlus version of the model; None or 'auto' to take that of its IDD.
    :return: The model, whose attributes give its occupied zones and windows.
    :raises ValueError: If an argument is missing or not valid.
    """
    if verbose_mode:
        print(BANNER)
    _warn_hvac_zone_map(hvac_zone_map)
    if energyplus_version is None or str(energyplus_version).lower() == 'auto':
        energyplus_version = _idf_version(idf)
    output_type, output_freqs, temp_ctrl = _check_model_arguments(
        script_type, supply_air_temp_input_method, output_type, output_freqs, temp_ctrl)
    if verbose_mode:
        _print_model_arguments(script_type, supply_air_temp_input_method, output_type, output_freqs,
                               energyplus_version, temp_ctrl)
    check_choice('energyplus_version', energyplus_version, SUPPORTED_ENERGYPLUS_VERSIONS)
    output_keep_existing = bool(output_keep_existing) if not isinstance(output_keep_existing, str) \
        else to_bool(output_keep_existing, 'output_keep_existing')
    if verbose_mode:
        print(_START_MODEL)
    model = AccimModel(idf, script_type, temp_ctrl, verbose_mode=verbose_mode, hvac_zone_map=hvac_zone_map)
    add_accis_objects(model, supply_air_temp_input_method, vrf_schedule=vrf_schedule, eer=eer, cop=cop,
                      make_averages=make_averages, debugging=debugging)
    add_outputs(model, output_type, output_freqs, output_keep_existing, output_take_dataframe)
    if script_type.startswith('vrf'):
        # EnergyPlus cannot run the VRF systems without sizing them (they are autosized). The existing HVAC systems
        # are the user's, so their sizing does not change (in accim 0.x, this function did not change it either)
        enable_sizing_calculations(model)
    if verbose_mode:
        print(_END_MODEL)
    return model


def gen_outputs_df(
    idf,
    script_type: Optional[str] = None,
    output_type: Optional[str] = None,
    output_freqs: Optional[Sequence[str]] = None,
    output_keep_existing: Optional[bool] = None,
    temp_ctrl: Optional[str] = None,
    make_averages: bool = False,
    verbose_mode: bool = False,
) -> pd.DataFrame:
    """Add the ACCIS to an IDF object (in place, see :func:`add_accis_to_idf`) and return a DataFrame with its
    Output:Variable objects, which can be filtered and given as ``output_take_dataframe``."""
    add_accis_to_idf(idf, script_type=script_type, output_type=output_type, output_freqs=output_freqs,
                     output_keep_existing=output_keep_existing, temp_ctrl=temp_ctrl, make_averages=make_averages,
                     supply_air_temp_input_method='temperature difference', verbose_mode=verbose_mode)
    return output_variables_dataframe(idf)


def _programs(idf) -> Dict[str, Any]:
    return {p.Name: p for p in idf.idfobjects['EnergyManagementSystem:Program']}


def modify_accis(
    idf,
    comf_stand: Optional[int] = None,
    cat: Optional[Number] = None,
    cat_cool_offset: Number = 0,
    cat_heat_offset: Number = 0,
    comf_mod: Optional[Number] = None,
    setpoint_acc: Number = 10000,
    cust_ast_acst_aul: Number = 0,
    cust_ast_acst_all: Number = 0,
    cust_ast_ahst_aul: Number = 0,
    cust_ast_ahst_all: Number = 0,
    cust_ast_m: Number = 0,
    cust_ast_n: Number = 0,
    cust_ast_acst_offset: Number = 0,
    cust_ast_ahst_offset: Number = 0,
    cool_season_start: Union[int, str] = 121,
    cool_season_end: Union[int, str] = 274,
    hvac_mode: Optional[int] = None,
    vent_ctrl: Optional[int] = None,
    max_temp_diff_vof: Number = 6,
    min_temp_diff_vof: Number = 1,
    multiplier_vof: Number = 0.25,
    vst_offset: Number = 0,
    min_ot_offset: Number = 50,
    max_wind_speed: Number = 50,
    ast_tol: Number = 0.1,
    zone_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    """Set the arguments of the ACCIS of an IDF object (one value of each argument of :class:`AddAccis`), in all
    its occupied zones or, with ``zone_arguments``, in some of them.

    Each zone has its arguments in the EMS program SetInputData_<zone>. The comfort standard, category, comfort
    mode, HVAC mode and ventilation control that are None keep their values. The setpoints are set in each timestep
    by the subprograms of the comfort standard (SetAST_Master), so these arguments can also be changed later in
    the programs SetInputData_<zone>.

    The models of earlier versions of accim, which have one program SetInputData for all the zones, can only have
    the same arguments in all the zones, and they get the subprograms of this version where they behave
    differently (those of ESP CTE and INT ISO7730 set the setpoints whatever the comfort mode is).

    :param ast_tol: The tolerance of the setpoints.
    :param zone_arguments: The arguments of some zones, which replace those of the call in these zones:
        ``{zone: {argument: value}}``, for instance ``{'Block1:Zone1': {'comf_stand': 2, 'cat': 80, 'comf_mod': 3}}``
        (see :class:`AddAccis`). An argument that is None in the call and is not given for a zone keeps its value
        in the zone.
    :raises ValueError: If the model has no ACCIS, setpoint_acc is negative, or zone_arguments is not valid (or is
        given for a model of an earlier version of accim).
    """
    arguments = dict(
        comf_stand=comf_stand, cat=cat, cat_cool_offset=cat_cool_offset, cat_heat_offset=cat_heat_offset,
        comf_mod=comf_mod, setpoint_acc=setpoint_acc, cust_ast_acst_aul=cust_ast_acst_aul,
        cust_ast_acst_all=cust_ast_acst_all, cust_ast_ahst_aul=cust_ast_ahst_aul, cust_ast_ahst_all=cust_ast_ahst_all,
        cust_ast_m=cust_ast_m, cust_ast_n=cust_ast_n, cust_ast_acst_offset=cust_ast_acst_offset,
        cust_ast_ahst_offset=cust_ast_ahst_offset, cool_season_start=cool_season_start,
        cool_season_end=cool_season_end, hvac_mode=hvac_mode, vent_ctrl=vent_ctrl,
        max_temp_diff_vof=max_temp_diff_vof, min_temp_diff_vof=min_temp_diff_vof, multiplier_vof=multiplier_vof,
        vst_offset=vst_offset, min_ot_offset=min_ot_offset, max_wind_speed=max_wind_speed, ast_tol=ast_tol,
    )
    programs = _programs(idf)
    zone_programs = input_programs(idf)
    if not zone_programs:
        if zone_arguments and 'SetInputData' in programs:
            raise ValueError('The model has the ACCIS of an earlier version of accim, whose arguments are the same in '
                             'all the zones (program SetInputData). To give the arguments of each zone, add the ACCIS '
                             'with this version of accim to the model without it.')
        _modify_accis_of_earlier_versions(idf, programs, **arguments)
        return
    missing = [n for n in ('SetAST', 'ApplyCAT', 'SetComfTemp', 'SetAppLimits') if n not in programs]
    if missing:
        raise ValueError(f'The model has no EMS programs {missing}. Add the ACCIS first with add_accis_to_idf().')
    if setpoint_acc < 0:
        raise ValueError('The value for setpoint_acc cannot be less than 0.')
    zones = check_zone_arguments(zone_arguments)
    resolved: Dict[str, Dict[str, Any]] = {}
    if zones:
        resolved = resolve_zone_arguments(zones, zone_names(resolve_targets(idf), list(zone_programs)))
    for zone, program in zone_programs.items():
        set_inputs(program, input_values(dict(arguments, **resolved.get(zone, {}))))


def _modify_accis_of_earlier_versions(
    idf, programs: Dict[str, Any], comf_stand, cat, cat_cool_offset, cat_heat_offset, comf_mod, setpoint_acc,
    cust_ast_acst_aul, cust_ast_acst_all, cust_ast_ahst_aul, cust_ast_ahst_all, cust_ast_m, cust_ast_n,
    cust_ast_acst_offset, cust_ast_ahst_offset, cool_season_start, cool_season_end, hvac_mode, vent_ctrl,
    max_temp_diff_vof, min_temp_diff_vof, multiplier_vof, vst_offset, min_ot_offset, max_wind_speed, ast_tol,
) -> None:
    """:func:`modify_accis` for the models of earlier versions of accim, which have one program SetInputData for all
    the zones, and the other arguments in SetAST, ApplyCAT, SetAppLimits and SetVOFinputData."""
    missing = [n for n in ('SetInputData', 'SetAST', 'ApplyCAT', 'SetComfTemp', 'SetAppLimits') if n not in programs]
    if missing:
        raise ValueError(f'The model has no EMS programs {missing}. Add the ACCIS first with add_accis_to_idf().')
    if setpoint_acc < 0:
        raise ValueError('The value for setpoint_acc cannot be less than 0.')
    start = to_day_of_year(cool_season_start, 'cool_season_start')
    end = to_day_of_year(cool_season_end, 'cool_season_end')

    input_data = [('ComfStand', comf_stand), ('CAT', cat), ('ComfMod', comf_mod), ('HVACmode', hvac_mode),
                  ('VentCtrl', vent_ctrl), ('VSToffset', vst_offset), ('MinOToffset', min_ot_offset),
                  ('MaxWindSpeed', max_wind_speed), ('ACSTtol', -ast_tol), ('AHSTtol', ast_tol),
                  ('CoolSeasonStart', start), ('CoolSeasonEnd', end)]
    for number, (name, value) in enumerate(input_data, start=1):
        if value is not None:
            setattr(programs['SetInputData'], f'Program_Line_{number}', f'set {name} = {value}')

    programs['SetComfTemp'].Program_Line_2 = f'set ComfTemp = PMOT*{cust_ast_m}+{cust_ast_n}'
    set_program_lines(programs['SetAppLimits'], [
        f'set ACSTaul = {cust_ast_acst_aul}', f'set ACSTall = {cust_ast_acst_all}',
        f'set AHSTaul = {cust_ast_ahst_aul}', f'set AHSTall = {cust_ast_ahst_all}'], first=2)
    replace_program_lines(programs['SetAST'], [f'set SetpointAcc = {setpoint_acc}', f'set m = {cust_ast_m}',
                                               f'set n = {cust_ast_n}', 'run SetAST_Master'])
    # The models of accim before 0.8 have no SetAST_Master
    if 'SetAST_Master' not in programs:
        add_program(idf, 'SetAST_Master', master_program_lines())
        for name, lines in subprograms().items():
            if name not in programs:
                add_program(idf, name, lines)
    else:
        # The models of accim before 1.0 only set the setpoints of ESP CTE and INT ISO7730 if ComfMod is 0
        static = [cs for cs in MODULAR_COMFORT_MODES if not depends_on_comfort_mode(cs)]
        for name, lines in subprograms(static).items():
            if name in programs:
                replace_program_lines(programs[name], lines)
    if 'SetVOFinputData' in programs:
        set_program_lines(programs['SetVOFinputData'], [
            f'set MaxTempDiffVOF = {max_temp_diff_vof}', f'set MinTempDiffVOF = {min_temp_diff_vof}',
            f'set MultiplierVOF = {multiplier_vof}'])
    set_program_lines(programs['ApplyCAT'], [f'set CATcoolOffset = {cat_cool_offset}',
                                             f'set CATheatOffset = {cat_heat_offset}'])
    set_program_lines(programs['ApplyCAT'], [f'set ACSToffset = {cust_ast_acst_offset} + {cat_cool_offset}',
                                             f'set AHSToffset = {cust_ast_ahst_offset} + {cat_heat_offset}'], first=4)
