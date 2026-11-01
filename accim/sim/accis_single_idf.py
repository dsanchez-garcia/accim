# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Deprecated module of accim 0.x: use :func:`accim.sim.accis.add_accis_to_idf` and
:func:`accim.sim.accis.modify_accis`, whose arguments follow PEP 8."""

from typing import Dict, Optional

import pandas as pd

from accim._deprecation import warn_deprecated
from accim.sim import accis as _accis
from accim.sim.arguments import LEGACY_ARGUMENT_NAMES
from accim.sim.ems.inputs import input_programs
from accim.sim.outputs import output_variables_dataframe

__all__ = ['addAccis']


class addAccis:  # noqa: N801 (the name of accim 0.x)
    """Deprecated: adds the ACCIS to an IDF object, as :func:`accim.sim.accis.add_accis_to_idf`, and keeps it to
    change its arguments with :meth:`modifyAccis`. Its arguments are those of accim 0.x, in the same order.

    :ivar arguments: The arguments, with the names of accim 0.x.
    :ivar arguments_accis: The arguments of the last call to :meth:`modifyAccis`, with the names of accim 0.x.
    :ivar occupied_zones: The occupied zones, as in the EMS objects.
    :ivar occupied_zones_original_name: The occupied zones.
    :ivar windows_and_doors: The windows and doors that open, as in the EMS objects (mixed mode).
    :ivar windows_and_doors_original_name: The windows and doors that open (mixed mode).
    :ivar df_outputs: The DataFrame of Output:Variable objects (argument ``Output_gen_dataframe``).
    :ivar SetAST: The EMS program SetAST (and likewise ``ApplyCAT``, ``SetComfTemp`` and ``SetAppLimits``; None if
        the model does not have it). ``SetInputData`` and ``SetVOFinputData`` are None: since accim 1.0.0, the
        arguments of each zone are in its program SetInputData_<zone>.
    :ivar zone_input_programs: The programs SetInputData_<zone>, by the name of their zone in the EMS objects.
    """

    _PROGRAMS = ('SetInputData', 'SetVOFinputData', 'SetAST', 'ApplyCAT', 'SetComfTemp', 'SetAppLimits')

    def __init__(
        self,
        idf=None,
        ScriptType: Optional[str] = None,  # noqa: N803 (the arguments of accim 0.x)
        SupplyAirTempInputMethod: Optional[str] = None,  # noqa: N803
        Output_type: Optional[str] = None,  # noqa: N803
        Output_freqs=None,  # noqa: N803
        Output_keep_existing: Optional[bool] = None,  # noqa: N803
        Output_gen_dataframe: Optional[bool] = None,  # noqa: N803
        Output_take_dataframe: Optional[pd.DataFrame] = None,  # noqa: N803
        EnergyPlus_version: Optional[str] = None,  # noqa: N803
        TempCtrl: Optional[str] = None,  # noqa: N803
        VRFschedule: str = 'On 24/7',  # noqa: N803
        verboseMode: bool = True,  # noqa: N803
        eer: float = 2,
        cop: float = 2.1,
        make_averages: bool = False,
        debugging: bool = False,
        hvac_zone_map: Optional[Dict[str, str]] = None,
    ):
        warn_deprecated('accim.sim.accis_single_idf.addAccis', 'accim.sim.accis.add_accis_to_idf')
        self.idf = idf
        self.arguments = {
            'ScriptType': ScriptType,
            'SupplyAirTempInputMethod': SupplyAirTempInputMethod,
            'Output_type': Output_type,
            'Output_freqs': Output_freqs,
            'Output_keep_existing': Output_keep_existing,
            'Output_gen_dataframe': Output_gen_dataframe,
            'Output_take_dataframe': Output_take_dataframe,
            'EnergyPlus_version': EnergyPlus_version,
            'TempCtrl': TempCtrl,
            'verboseMode': verboseMode,
        }
        model = _accis.add_accis_to_idf(
            idf,
            script_type=ScriptType,
            supply_air_temp_input_method=SupplyAirTempInputMethod,
            output_type=Output_type,
            output_freqs=Output_freqs,
            output_keep_existing=Output_keep_existing,
            output_take_dataframe=Output_take_dataframe,
            energyplus_version=EnergyPlus_version,
            temp_ctrl=TempCtrl,
            vrf_schedule=VRFschedule,
            verbose_mode=verboseMode,
            eer=eer,
            cop=cop,
            make_averages=make_averages,
            debugging=debugging,
            hvac_zone_map=hvac_zone_map,
        )
        self.occupied_zones = model.occupied_zones
        self.occupied_zones_original_name = model.occupied_zones_orig
        if model.is_mixed_mode:
            self.windows_and_doors = model.windows
            self.windows_and_doors_original_name = model.windows_orig
        if Output_gen_dataframe and str(Output_type).lower() != 'custom':
            name = str(getattr(idf, 'idfname', '')).split('.idf')[0]
            self.df_outputs = output_variables_dataframe(idf, file=name)
        self._find_programs()

    def _find_programs(self) -> None:
        programs = {p.Name: p for p in self.idf.idfobjects['EnergyManagementSystem:Program']}
        for name in self._PROGRAMS:
            setattr(self, name, programs.get(name))
        self.zone_input_programs = input_programs(self.idf)

    def modifyAccis(  # noqa: N802 (the name of accim 0.x)
        self,
        ComfStand: Optional[int] = None,  # noqa: N803 (the arguments of accim 0.x)
        CAT: Optional[float] = None,  # noqa: N803
        CATcoolOffset: float = 0,  # noqa: N803
        CATheatOffset: float = 0,  # noqa: N803
        ComfMod: Optional[float] = None,  # noqa: N803
        SetpointAcc: float = 10000,  # noqa: N803
        CustAST_ACSTaul: float = 0,  # noqa: N803
        CustAST_ACSTall: float = 0,  # noqa: N803
        CustAST_AHSTaul: float = 0,  # noqa: N803
        CustAST_AHSTall: float = 0,  # noqa: N803
        CustAST_m: float = 0,  # noqa: N803
        CustAST_n: float = 0,  # noqa: N803
        CustAST_ACSToffset: float = 0,  # noqa: N803
        CustAST_AHSToffset: float = 0,  # noqa: N803
        CoolSeasonStart=121,  # noqa: N803
        CoolSeasonEnd=274,  # noqa: N803
        HVACmode: Optional[int] = None,  # noqa: N803
        VentCtrl: Optional[int] = None,  # noqa: N803
        MaxTempDiffVOF: float = 6,  # noqa: N803
        MinTempDiffVOF: float = 1,  # noqa: N803
        MultiplierVOF: float = 0.25,  # noqa: N803
        VSToffset: float = 0,  # noqa: N803
        MinOToffset: float = 50,  # noqa: N803
        MaxWindSpeed: float = 50,  # noqa: N803
        ASTtol: float = 0.1,  # noqa: N803
    ):
        """Set the arguments of the ACCIS in all the zones, as :func:`accim.sim.accis.modify_accis`.

        In accim 0.x, SetAST also got the lines of the comfort standard and comfort mode given; since accim 1.0.0,
        each zone runs SetAST with its own arguments, so SetAST only runs SetAST_Master, which has the lines of all
        of them.
        """
        arguments = dict(locals())
        del arguments['self']
        self.arguments_accis = arguments
        _accis.modify_accis(self.idf, **{LEGACY_ARGUMENT_NAMES[name]: value for name, value in arguments.items()})
        self._find_programs()
