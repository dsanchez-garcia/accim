# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Class for accim."""
from accim.utils import get_idd_path_from_ep_version
from accim.sim.hvac.resolver import resolve_hvac_zone_map


class AccimJob():
    """Class to start the process to add the class ``accim.sim.accis.addAccis``.

    :param filename_temp: the filename of the idf
    :param ScriptType: Inherited from class ``accim.sim.accis.addAccis``
    :param EnergyPlus_version: Inherited from class ``accim.sim.accis.addAccis``
    :param TempCtrl: Inherited from class ``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from class ``accim.sim.accis.addAccis``
    :param accimNotWorking: True if problems detected in class ``accim.sim.accis.addAccis``
    """
    from os import listdir
    import numpy

    from accim.sim.idf_generation import \
        generate_idfs
    from accim.sim.prompts import \
        collect_comfort_inputs
    from accim.sim.hvac.base import \
        set_comfort_fields_people, \
        save, \
        set_pmv_setpoint, \
        add_control_files_objects, \
        add_output_variable_dictionary, \
        add_output_ems, \
        set_simulation_control_sizing
    from accim.sim.ems.programs import \
        add_ems_actuators, \
        add_ems_output_variables, \
        add_ems_pcm, \
        add_ems_programs, \
        add_ems_sensors, \
        add_global_variables, \
        add_internal_variables, \
        add_output_variables_standard, \
        add_output_variables_simplified, \
        add_output_variables_detailed, \
        remove_existing_output_variables, \
        remove_duplicated_output_variables, \
        apply_specified_outputs, \
        gen_output_dataframe, \
        take_output_dataframe, \
        make_averages

    from accim.sim.hvac.existing import \
        add_forscript_schedule_existing_hvac
    from accim.sim.hvac.existing_ems import \
        add_ems_sensors_existing_hvac, \
        add_ems_init_existing_hvac
    from accim.sim.hvac.resolver import \
        resolve_hvac_zone_map
    from accim.sim.hvac.vrf import \
        add_base_schedules, \
        add_curve_objects, \
        add_detailed_hvac_objects, \
        add_forscript_schedule_vrf, \
        add_operative_temp_thermostat, \
        add_vrf_system_schedule, \
        check_ventilation_is_on, \
        set_availability_schedule_on
    from accim.sim.hvac.vrf_ems import \
        add_ems_sensors_vrf

    from accim.utils import amend_idf_version_from_dsb, get_idd_path_from_ep_version
    from accim.sim.utils import scan_zones


    def __init__(self,
                 filename_temp,
                 script_type: str = None,
                 energyplus_version: str = 'auto',
                 temp_control: str = None,
                 verbose: bool = True,
                 accimNotWorking: bool = False,
                 hvac_zone_map: dict = None):
        """
        Constructor method.

        :param hvac_zone_map: Optional manual mapping of existing HVAC object names
            to zone names, used when ScriptType is 'ex_mm' or 'ex_ac' and the
            automatic resolver cannot determine the correct zone (e.g. shared/central
            equipment).  Format: ``{'HVAC Object Name': 'Zone Name'}``.
        :type hvac_zone_map: dict or None
        """
        import eppy
        from eppy.modeleditor import IDF
        self.accimNotWorking = accimNotWorking
        from accim.utils import amend_idf_version_from_dsb
        from besos.eppy_funcs import get_building

        fname1 = filename_temp + '.idf'

        # Checking if idf version is suitable: when exported from Designbuilder 7.X, the version is 9.4.0.002
        amend_idf_version_from_dsb(fname1)

        idf_created = False

        if energyplus_version.lower() != 'auto':
            iddfile = get_idd_path_from_ep_version(energyplus_version=energyplus_version)
            if iddfile == 'not-supported':
                raise ValueError("""EnergyPlus version not supported.\n
                                         Only works for versions between EnergyPlus 9.1 (enter 9.1) and EnergyPlus 25.1 (enter 25.1)""")
            if verbose:
                print('IDD location is: '+iddfile)
            IDF.setiddname(iddfile)
            self.idf0 = IDF(fname1)
            idf_from_eppy = True

        else:
            self.idf0 = get_building(fname1)
            energyplus_version = '.'.join([str(i) for i in self.idf0.idd_version[:2]])
            if verbose:
                print('IDD location is: '+self.idf0.iddname)
            idf_from_eppy = False



        self.idf0.savecopy(filename_temp+'_pymod.idf')

        self.filename = filename_temp+'_pymod'
        fname1 = self.filename+'.idf'

        if idf_from_eppy:
            self.idf1 = IDF(fname1)
        else:
            self.idf1 = get_building(fname1)

        self.filename = filename_temp+'_pymod'

        self.output_idf_dict = {}

        self._scan_and_setup_zones(
            script_type=script_type,
            verbose=verbose,
            hvac_zone_map=hvac_zone_map,
            model_label=filename_temp,
        )

    def _scan_and_setup_zones(self, script_type, verbose=True, hvac_zone_map=None, model_label=''):
        """Common, I/O-free scanning and zone/HVAC setup shared by the batch and
        single (in-memory) entry points.

        Operates on ``self.idf1`` (already loaded in memory) and populates the
        occupied-zone / window / HVAC attributes consumed by the injection methods.
        This is the single source of truth for both paths; the batch path reaches it
        after its disk I/O, the single path right after assigning ``self.idf1``.
        """
        # Scanning occupied zones using function
        self.scan_zones()

        if verbose:
            print(f'The occupied zones in the model {model_label} are:')
            print(*self.occupiedZones_orig, sep="\n")

        self.ismixedmode = False

        if (script_type.lower() == 'vrfsystem_mm' or
            script_type.lower() == 'vrf_mm' or
            script_type.lower() == 'existinghvac_mm' or
            script_type.lower() == 'ex_mm'
        ):
            self.ismixedmode = True
            self.windownamelist_orig = []
            self.windownamelist = []
            self.windownamelist_orig_split = []

            # Check if there is already a ScheduleTypeLimits for Fractional
            if len([stl for stl in self.idf1.idfobjects['ScheduleTypeLimits'] if stl.Name.lower() == 'fractional']) == 0:
                self.idf1.newidfobject(
                    'ScheduleTypeLimits',
                    Name='Fractional',
                    Lower_Limit_Value=0,
                    Upper_Limit_Value=1,
                    Numeric_Type='Continuous',
                    Unit_Type='dimensionless'
                )

            if len(self.idf1.idfobjects['AirflowNetwork:SimulationControl']) > 0:
                self.natural_ventilation_type = 'AFN'
                for i in [window.Name for window in
                          self.idf1.idfobjects
                          ['AirflowNetwork:MultiZone:Component:DetailedOpening']
                          if window.Name.endswith('_Win')
                          or window.Name.endswith('_Door')
                          ]:
                    for k in self.occupiedZones_orig:
                        if i.split('_')[0].lower() == k.lower():
                            self.windownamelist_orig.append(i)

                self.windownamelist = [i.replace(':', '_') for i in self.windownamelist_orig]
                self.windownamelist_orig_split = ([i.split('_') for i in self.windownamelist_orig])
            else:
                self.natural_ventilation_type = 'Scheduled'
                self.scheduled_ventilation_dict = {}

                # Look for ZoneVentilation:WindandStackOpenArea
                for zv in self.idf1.idfobjects['ZoneVentilation:WindandStackOpenArea']:
                    for k in self.occupiedZones_orig:
                        if zv.Zone_or_Space_Name.lower() == k.lower():
                            sch_name = f'Vent_Sch_{k}'
                            if len([sch for sch in self.idf1.idfobjects['Schedule:Constant'] if sch.Name == sch_name]) == 0:
                                self.idf1.newidfobject(
                                    'Schedule:Constant',
                                    Name=sch_name,
                                    Schedule_Type_Limits_Name='Fractional',
                                    Hourly_Value=0
                                )
                            zv.Opening_Area_Fraction_Schedule_Name = sch_name
                            
                            virtual_window_name = f"{k}_Win"
                            self.windownamelist_orig.append(virtual_window_name)
                            self.windownamelist.append(virtual_window_name.replace(':', '_'))
                            self.windownamelist_orig_split.append([k, 'Win'])
                            self.scheduled_ventilation_dict[virtual_window_name] = sch_name

                # Look for ZoneVentilation:DesignFlowRate
                for zv in self.idf1.idfobjects['ZoneVentilation:DesignFlowRate']:
                    for k in self.occupiedZones_orig:
                        if zv.Zone_or_Space_Name.lower() == k.lower():
                            if 'infiltration' in zv.Name.lower():
                                continue
                            sch_name = f'Vent_Sch_{k}'
                            if len([sch for sch in self.idf1.idfobjects['Schedule:Constant'] if sch.Name == sch_name]) == 0:
                                self.idf1.newidfobject(
                                    'Schedule:Constant',
                                    Name=sch_name,
                                    Schedule_Type_Limits_Name='Fractional',
                                    Hourly_Value=0
                                )
                            zv.Schedule_Name = sch_name
                            
                            virtual_window_name = f"{k}_Win"
                            if virtual_window_name not in self.windownamelist_orig:
                                self.windownamelist_orig.append(virtual_window_name)
                                self.windownamelist.append(virtual_window_name.replace(':', '_'))
                                self.windownamelist_orig_split.append([k, 'Win'])
                                self.scheduled_ventilation_dict[virtual_window_name] = sch_name

            if verbose:
                print(f'The windows and doors in the model {model_label} are:')
                print(*self.windownamelist, sep="\n")

        if 'vrf' in script_type.lower():
            self.zonenames = self.occupiedZones
            self.zonenames_orig = self.occupiedZones_orig
            if verbose:
                print(f'The zones in the model {model_label} are:')
                print(*self.zonenames, sep="\n")

        elif 'ex' in script_type.lower():
            TSPtypes = [
                'ThermostatSetpoint:SingleHeating',
                'ThermostatSetpoint:SingleCooling',
                # ThermostatSetpoint:SingleHeatingOrCooling objects are not supported
                # 'ThermostatSetpoint:SingleHeatingOrCooling',
                'ThermostatSetpoint:DualSetpoint'
            ]
            self.ZCTlist = [i for i in self.idf1.idfobjects['ZONECONTROL:THERMOSTAT']]

            self.HVACzonelist = []

            for i in range(len(TSPtypes)):
                temp1 = []
                temp2 = []
                temp3 = []
                if len(self.idf1.idfobjects[TSPtypes[i]]) > 0:
                    for j in range(len(self.ZCTlist)):
                        if self.ZCTlist[j].Control_1_Object_Type in TSPtypes[i]:
                            temp1.append(self.ZCTlist[j].Zone_or_ZoneList_Name.upper())
                            zone_name_upper = self.ZCTlist[j].Zone_or_ZoneList_Name.upper()
                            ems_name = None
                            if hasattr(self, 'ems_zonenames') and hasattr(self, 'ems_objs_name'):
                                for z_name, e_name in zip(self.ems_zonenames, self.ems_objs_name):
                                    if z_name.upper() == zone_name_upper:
                                        ems_name = e_name  # Keep exact matching case
                                        break
                            if ems_name is None:
                                if ':' in self.ZCTlist[j].Zone_or_ZoneList_Name:
                                    ems_name = self.ZCTlist[j].Zone_or_ZoneList_Name.upper().replace(":", "_")
                                else:
                                    sc_names = [s.Name.upper() for s in self.idf1.idfobjects['SPACE'] if s.Zone_Name.upper() == zone_name_upper]
                                    ems_name = sc_names[0] if sc_names else zone_name_upper.replace(":", "_").replace(" ", "_")
                                    
                            temp2.append(ems_name)
                            temp3.append(self.ZCTlist[j].Control_1_Name)
                self.HVACzonelist.append([TSPtypes[i], temp1, temp2, temp3])
            del temp1, temp2, temp3

            if verbose:
                for i in range(len(self.HVACzonelist)):
                    if len(self.HVACzonelist[i][3]) == 0:
                        print(f'There are no {self.HVACzonelist[i][0]} objects in the model')
                    else:
                        print(f'Regarding {self.HVACzonelist[i][0]} objects:')
                        print(f'The zones with {self.HVACzonelist[i][0]} are:')
                        print(*self.HVACzonelist[i][1], sep="\n")
                        print(f'And the existing ThermostatSetpoint objects related to {self.HVACzonelist[i][0]} are:')
                        print(*self.HVACzonelist[i][3], sep="\n")

            self.zonenames_orig = []
            # todo currently all zones regardless the single or dual thermostat object are merged in zonenames_orig;
            #  this would be desirable to be amended

            for i in range(len(self.HVACzonelist)):
                for k in range(len(self.HVACzonelist[i][1])):
                    if self.HVACzonelist[i][1][k] in self.zonenames_orig:
                        continue
                    else:
                        self.zonenames_orig.append(self.HVACzonelist[i][1][k])
            if self.origin_dsb:
                self.zonenames = [i.replace(':', '_') for i in self.zonenames_orig]
            else:
                self.zonenames = [i.replace(' ', '_') for i in self.zonenames_orig]

            if script_type.lower() == 'existinghvac_mm' or script_type.lower() == 'ex_mm':

                self.HVACdict = {
                    # todo if there is a Coil:Heating:Whatever and another Coil:Heating:DifferentWhatever
                    #  coils and windows sensors will be duplicated and simulation will crash; it needs to be solved.

                    # Group Heating and Cooling Coils
                    'Coil:Cooling:Water': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:Water:DetailedGeometry': 'Cooling Coil Total Cooling Rate',
                    # not supported
                    # 'CoilSystem:Cooling:Water:HeatExchangerAssisted':'',
                    'CoilSystem:Cooling:Water': 'Coil System Water Total Cooling Rate',
                    'Coil:Heating:Water': 'Heating Coil Heating Energy',
                    'Coil:Heating:Steam': 'Heating Coil Heating Energy',
                    'Coil:Heating:Electric': 'Heating Coil Heating Energy',
                    'Coil:Heating:Electric:MultiStage': 'Heating Coil Heating Energy',
                    'Coil:Heating:Desuperheater': 'Heating Coil Heating Energy',
                    'Coil:Cooling:DX:VariableRefrigerantFlow': 'Cooling Coil Total Cooling Rate',
                    'Coil:Heating:DX:VariableRefrigerantFlow': 'Heating Coil Heating Energy',
                    'Coil:Cooling:DX:VariableRefrigerantFlow:FluidTemperatureControl': 'Cooling Coil Total Cooling Rate',
                    'Coil:Heating:DX:VariableRefrigerantFlow:FluidTemperatureControl': 'Heating Coil Heating Energy',
                    'Coil:Heating:Fuel': 'Heating Coil Heating Energy',
                    'Coil:Heating:Gas:MultiStage': 'Heating Coil Heating Energy',
                    'Coil:Cooling:DX:SingleSpeed': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:TwoSpeed': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:TwoStageWithHumidityControlMode': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:MultiSpeed': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:VariableSpeed': 'Cooling Coil Total Cooling Rate',
                    # not supported
                    # 'CoilPerformance:DX:Cooling': '',
                    'Coil:Heating:DX:SingleSpeed': 'Heating Coil Heating Energy',
                    'Coil:Heating:DX:MultiSpeed': 'Heating Coil Heating Energy',
                    'Coil:Heating:DX:VariableSpeed': 'Heating Coil Heating Energy',
                    'Coil:WaterHeating:Desuperheater': 'Water Heater Heating Energy',
                    # not supported
                    # 'CoilSystem:Cooling:DX': '',
                    # 'CoilSystem:Heating:DX': '',
                    # 'CoilSystem:Cooling:DX:HeatExchangerAssisted': '',
                    # 'CoilSystem:IntegratedHeatPump:AirSource': '',
                    # 'Coil:WaterHeating:AirToWaterHeatPump:Pumped': 'Heating Coil Heating Energy',
                    # 'Coil:WaterHeating:AirToWaterHeatPump:Wrapped': 'Heating Coil Heating Energy',
                    # 'Coil:WaterHeating:AirToWaterHeatPump:VariableSpeed': 'Cooling Coil Electricity Energy',
                    'Coil:Cooling:WaterToAirHeatPump:ParameterEstimation': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:WaterToAirHeatPump:EquationFit': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:WaterToAirHeatPump:VariableSpeedEquationFit': 'Cooling Coil Total Cooling Rate',
                    'Coil:Heating:WaterToAirHeatPump:ParameterEstimation': 'Heating Coil Heating Energy',
                    'Coil:Heating:WaterToAirHeatPump:EquationFit': 'Heating Coil Heating Energy',
                    'Coil:Heating:WaterToAirHeatPump:VariableSpeedEquationFit': 'Heating Coil Heating Energy',
                    'Coil:Cooling:DX:SingleSpeed:ThermalStorage': 'Cooling Coil Total Cooling Rate',
                    # not supported
                    # 'Secondary Coils of DX System and Heat Pump':'',
                    'Coil:Cooling:DX': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:CurveFit:Performance': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:CurveFit:OperatingMode': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:CurveFit:Speed': 'Cooling Coil Total Cooling Rate',

                    # Group – Radiative / Convective Units
                    # todo many objects have heating or cooling outputs for the same field
                    'ZoneHVAC:Baseboard:RadiantConvective:Water': 'Baseboard Total Heating Rate',
                    'ZoneHVAC:Baseboard:RadiantConvective:Steam': 'Baseboard Total Heating Rate',
                    'ZoneHVAC:Baseboard:RadiantConvective:Electric': 'Baseboard Total Heating Rate',
                    'ZoneHVAC:CoolingPanel:RadiantConvective:Water': 'Cooling Panel Total Cooling Rate',
                    'ZoneHVAC:Baseboard:Convective:Water': 'Baseboard Total Heating Rate',
                    'ZoneHVAC:Baseboard:Convective:Electric': 'Baseboard Total Heating Rate',
                    # not supported
                    # ZoneHVAC:LowTemperatureRadiant:VariableFlow can be a chilled ceiling: Zone Radiant HVAC Cooling Rate
                    # also it can be a heated floor: Zone Radiant HVAC Heating Rate
                    # 'ZoneHVAC:LowTemperatureRadiant:VariableFlow': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:LowTemperatureRadiant:ConstantFlow': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:LowTemperatureRadiant:Electric': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:LowTemperatureRadiant:SurfaceGroup': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:HighTemperatureRadiant': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:VentilatedSlab': '',
                    # 'ZoneHVAC:VentilatedSlab:SlabGroup': '',

                    # Group – Zone HVAC Air Loop Terminal Units
                    # 'AirTerminal:SingleDuct:ConstantVolume:Reheat': '',
                    # 'AirTerminal:SingleDuct:ConstantVolume:NoReheat': '',
                    # 'AirTerminal:SingleDuct:VAV:Reheat': '',
                    # 'AirTerminal:SingleDuct:VAV:Reheat:VariableSpeedFan': '',
                    # 'AirTerminal:SingleDuct:VAV:HeatAndCool:Reheat': '',
                    # 'AirTerminal:SingleDuct:VAV:NoReheat': '',
                    # 'AirTerminal:SingleDuct:VAV:HeatAndCool:NoReheat': '',
                    # 'AirTerminal:SingleDuct:SeriesPIU:Reheat': '',
                    # 'AirTerminal:SingleDuct:ParallelPIU:Reheat': '',
                    # 'AirTerminal:SingleDuct:ConstantVolume:FourPipeInduction': '',
                    # 'AirTerminal:SingleDuct:ConstantVolume:FourPipeBeam': '',
                    'AirTerminal:SingleDuct:ConstantVolume:CooledBeam': 'Zone Air Terminal Beam Chilled Water Energy',
                    # 'AirTerminal:SingleDuct:Mixer': '',
                    # 'AirTerminal:DualDuct:ConstantVolume': '',
                    # 'AirTerminal:DualDuct:VAV': '',
                    # 'AirTerminal:DualDuct:VAV:OutdoorAir': ''
                }

                HVACkeylist = list(self.HVACdict.keys())

                self.ExisHVAC = []

                for hvac_type in HVACkeylist:
                    try:
                        hvac_objs = self.idf1.idfobjects[hvac_type]
                    except KeyError:
                        if verbose:
                            print(f'{hvac_type} HVAC SYSTEM IS NOT SUPPORTED')
                        continue

                    obj_names = [o.Name for o in hvac_objs]
                    if not obj_names:
                        continue

                    # Use the multi-strategy resolver to map each HVAC object
                    # to one or more zone names.
                    zone_map = resolve_hvac_zone_map(
                        idf=self.idf1,
                        hvac_type=hvac_type,
                        hvac_obj_names=obj_names,
                        user_map=hvac_zone_map,
                        verbose=verbose,
                    )

                    # Build flat parallel lists, expanding coils that serve
                    # multiple zones (C2 AirLoop case) into one entry per zone.
                    temp = []          # HVAC object names (may repeat for C2)
                    temp_zone_orig = [] # zone names in original form
                    temp_zone = []      # zone names with ':' replaced by '_'

                    for obj_name, zones in zone_map.items():
                        for zone in zones:
                            temp.append(obj_name)
                            temp_zone_orig.append(zone.upper())
                            if ':' in zone:
                                temp_zone.append(zone.upper().replace(':', '_'))
                            else:
                                temp_zone.append(zone.upper().replace(' ', '_'))

                    # Build matching window list for each (object, zone) entry
                    temp_win = []
                    for tz in temp_zone:
                        for wname in self.windownamelist:
                            if tz.lower() in wname.lower():
                                temp_win.append(wname)

                    self.ExisHVAC.append(
                        [hvac_type, temp, temp_zone_orig, temp_zone, temp_win]
                    )

                for i in range(len(self.ExisHVAC)):
                    for j in range(len(self.ExisHVAC[i][2])):
                        if self.ExisHVAC[i][2][j] not in self.zonenames_orig:
                            if verbose:
                                print(
                                    f'"{self.ExisHVAC[i][2][j]}" is not a valid zone. \n'
                                    f'The HVAC object "{self.ExisHVAC[i][1][j]}" ({self.ExisHVAC[i][0]}) '
                                    f'could not be mapped to any occupied zone. \n'
                                    f'If automatic detection failed, supply the correct mapping via '
                                    f'hvac_zone_map={{"\'{self.ExisHVAC[i][1][j]}\'": "correct_zone_name"}}.'
                                )
                            self.accimNotWorking = True

                if verbose:
                    for i in range(len(self.ExisHVAC)):
                        print(f'The names of the existing {self.ExisHVAC[i][0]} objects are:')
                        print(*self.ExisHVAC[i][1], sep="\n")
                        print(f'The zones related to these {self.ExisHVAC[i][0]} objects are')
                        print(*self.ExisHVAC[i][2], sep='\n')
                        print(f'And the windows related to these {self.ExisHVAC[i][0]} objects are:')
                        print(*self.ExisHVAC[i][4], sep='\n')

    def apply_accis(
        self,
        script_type,
        supply_air_temp_method=None,
        temp_control=None,
        output_type=None,
        output_freqs=None,
        output_keep_existing=None,
        output_take_dataframe=None,
        output_gen_dataframe=False,
        make_averages=False,
        debug=False,
        eer=2,
        cop=2.1,
        vrf_schedule='On 24/7',
        energyplus_version=None,
        verbose=True,
        take_dataframe_filename=None,
        single_idf=False,
    ):
        """Run the full ordered ACCIS injection sequence on ``self.idf1``.

        Single source of truth for the injection sequence, shared by the batch
        (disk) and single (in-memory) entry points. Returns the possibly-updated
        ``output_gen_dataframe`` flag (output type 'custom' disables it). Disk-only
        steps (set_simulation_control_sizing, save, gen_output_dataframe) are
        handled by the batch caller, not here.
        """
        self.set_comfort_fields_people(
            energyplus_version=energyplus_version, temp_control=temp_control, verbose=verbose)

        if 'vrf' in script_type.lower():
            if temp_control.lower() == 'temperature' or temp_control.lower() == 'temp':
                self.add_operative_temp_thermostat(verbose=verbose)
            elif temp_control.lower() == 'pmv':
                self.set_pmv_setpoint(verbose=verbose)
            self.add_base_schedules(verbose=verbose)
            self.set_availability_schedule_on(verbose=verbose)
            self.add_vrf_system_schedule(verbose=verbose)
            self.add_curve_objects(verbose=verbose)
            self.add_detailed_hvac_objects(
                energyplus_version=energyplus_version,
                verbose=verbose,
                supply_air_temp_method=supply_air_temp_method,
                eer=eer,
                cop=cop,
                vrf_schedule=vrf_schedule,
            )
            if script_type.lower() == 'vrf_mm':
                self.check_ventilation_is_on(verbose=verbose)
            self.add_forscript_schedule_vrf(verbose=verbose)
        elif 'ex' in script_type.lower():
            # todo check if PMV can work with ex_ac
            self.add_forscript_schedule_existing_hvac(verbose=verbose)

        self.add_ems_programs(script_type=script_type, verbose=verbose)
        self.add_ems_output_variables(script_type=script_type, verbose=verbose)
        self.add_global_variables(script_type=script_type, verbose=verbose)
        self.add_internal_variables(verbose=verbose)
        self.add_ems_sensors(script_type=script_type, verbose=verbose)
        self.add_ems_actuators(script_type=script_type, verbose=verbose)

        if 'vrf' in script_type.lower():
            self.add_ems_sensors_vrf(script_type=script_type, verbose=verbose)
        elif script_type.lower() == 'ex_mm':
            self.add_ems_sensors_existing_hvac(verbose=verbose)
            self.add_ems_init_existing_hvac(verbose=verbose)

        self.add_ems_pcm(verbose=verbose)

        if make_averages:
            self.make_averages(verbose=verbose)

        if output_keep_existing == 'true':
            output_keep_existing = True
        elif output_keep_existing == 'false':
            output_keep_existing = False
        if output_keep_existing is True:
            pass
        else:
            self.remove_existing_output_variables()

        if output_type.lower() == 'simplified':
            self.add_output_variables_simplified(
                output_freqs=output_freqs, temp_control=temp_control, verbose=verbose)
        elif output_type.lower() == 'standard':
            self.add_output_variables_standard(
                output_freqs=output_freqs, script_type=script_type,
                temp_control=temp_control, verbose=verbose)
        elif output_type.lower() == 'detailed' or output_type.lower() == 'custom':
            self.add_output_variables_standard(
                output_freqs=output_freqs, script_type=script_type,
                temp_control=temp_control, verbose=verbose)
            self.add_output_variables_detailed(output_freqs=output_freqs, verbose=verbose)
            if output_type.lower() == 'custom':
                output_gen_dataframe = False
                self.apply_specified_outputs()

        if output_take_dataframe is not None:
            if single_idf:
                self.take_output_dataframe(
                    idf_filename=take_dataframe_filename,
                    df_outputs_in=output_take_dataframe, verbose=verbose, singleidf=True)
            else:
                self.take_output_dataframe(
                    idf_filename=take_dataframe_filename,
                    df_outputs_in=output_take_dataframe, verbose=verbose)

        self.remove_duplicated_output_variables()

        self.add_control_files_objects(verbose=verbose)
        self.add_output_variable_dictionary(verbose=verbose)

        if debug:
            self.add_output_ems(verbose=verbose)

        return output_gen_dataframe


class AccimJobInMemory(AccimJob):
    """In-memory variant of the ACCIS engine.

    Takes an already-loaded eppy/besos IDF object instead of a filename and runs
    the same scanning/zone-setup as the batch (disk) path, without touching disk.
    Used by the single-IDF entry point (``accim.sim.single``) and by the aPMV
    path. All injection methods are inherited from :class:`AccimJob`.
    """

    def __init__(self,
                 idf_class_instance,
                 script_type: str = None,
                 energyplus_version: str = None,
                 temp_control: str = None,
                 verbose: bool = True,
                 hvac_zone_map: dict = None):
        self.accimNotWorking = False
        self.idf1 = idf_class_instance
        self.output_idf_dict = {}
        self._scan_and_setup_zones(
            script_type=script_type,
            verbose=verbose,
            hvac_zone_map=hvac_zone_map,
            model_label=getattr(idf_class_instance, 'idfname', '') or 'in-memory IDF',
        )
