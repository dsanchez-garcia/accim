# 4. Detailed use and explanation of arguments

## 4.1 First steps

Four main branches of functions have been developed, which are:

-   VRF system with full air-conditioning mode (script_type='vrf_ac'): This mode has been developed mainly to support models originated with OpenStudio, which up to date does not support Airflow Network objects and subsequently Calculated Natural Ventilation. It adds standard VRF systems for each occupied zone and applies the adaptive or PMV-based setpoint temperatures, but only works with full air-conditioning mode. It does not change the natural ventilation of the model: `ZoneVentilation` objects and AirflowNetwork openings keep the control of the input model, so the windows that are open in it stay open. To simulate such a model fully air-conditioned with its windows closed, use `vrf_mm` with `hvac_mode=[0]`, or close them in the model.
-   VRF system with mixed mode (script_type='vrf_mm'): It adds standard VRF systems for each occupied zone and applies the adaptive or PMV-based setpoint temperatures. Works with Calculated Natural Ventilation (AirflowNetwork), although full air-conditioning mode can also be used. In models without AirflowNetwork, it controls the natural ventilation of the `ZoneVentilation:WindandStackOpenArea` and `ZoneVentilation:DesignFlowRate` objects of the occupied zones (except those whose names contain "infiltration"): each zone gets a schedule `Vent_Sch_<zone>`, which accim opens and closes as the windows of the AirflowNetwork, so models made with OpenStudio can also use mixed mode. On the design days (the days of the types `SummerDesignDay` and `WinterDesignDay`), the zones are air-conditioned with the windows closed, whether they are occupied or not, so that EnergyPlus sizes the VRF systems for the setpoints: before accim 1.1.0, the VRF systems were off on the design days without occupants (often the winter design day) and while the windows were open, so EnergyPlus sized them without those timesteps (the heating design loads of the zones of the sample model were 0). Section 4.1.2 explains which windows accim opens and closes in mixed mode.
-   Existing HVAC system only with full air-conditioning mode (script_type='ex_ac'): Keeps the existing HVAC systems and modify the existing setpoint temperatures to adaptive or PMV-based setpoint temperatures. However, mixed-mode and naturally ventilated modes are not available in this mode. As with `vrf_ac`, the natural ventilation of the model keeps the control of the input model. By default, the thermostats of the occupied zones control the operative temperature, as those of the VRF systems; other arguments make the existing HVAC systems always available, widen their outdoor temperature limits or add backup ideal loads air systems (see section 4.1.1).
-   Existing HVAC system with mixed mode (script_type='ex_mm'): Keeps the existing HVAC systems and modify the existing setpoint temperatures to adaptive or PMV-based setpoint temperatures, considering mixed-mode. As with `vrf_mm`, it opens the windows (or the `ZoneVentilation` objects, in models without AirflowNetwork) of each zone only when its HVAC system is off: with the existing HVAC systems, accim reads it from the thermostat of the zone, whatever its equipment (zone equipment, air loops, baseboards, radiant systems, beams...): the HVAC system is off when the thermostat asks it for no load, that is, when the temperature of the zone is between its heating and cooling setpoints (the EnergyPlus output `Zone Predicted Sensible Load to Setpoint Heat Transfer Rate` of the previous timestep is 0). So each occupied zone needs a thermostat (`ZoneControl:Thermostat`), as with `ex_ac`. Before accim 1.0.0, `ex_mm` read the coils of one heating and one cooling object of each zone, so it rejected the models with several kinds of coils and stopped EnergyPlus with zones without cooling (or heating) equipment; the argument `hvac_zone_map`, which gave the zones of these objects, is no longer needed. In a zone whose thermostat has a cooling setpoint but no equipment that cools (radiators only, for instance), the windows stay closed while the thermostat asks for cooling, as with a system that cools; HVAC mode 2 only opens them below the cooling setpoint anyway. On the design days (the days of the types `SummerDesignDay` and `WinterDesignDay`), the zones are air-conditioned with the windows closed, whether they are occupied or not, so that EnergyPlus sizes the HVAC systems for the setpoints: before accim 1.1.0, the HVAC systems were off on the design days without occupants (often the winter design day), and EnergyPlus sized them for no load and stopped, or they could not heat. The arguments of section 4.1.1 also apply to `ex_mm`, and section 4.1.2 explains which windows accim opens and closes.

Therefore, if you are going to use the VRF system script, you’re supposed to have one or multiple IDFs with fixed setpoint temperature, or even without any HVAC objects at all (it doesn’t matter, since the module is going to add a standard VRF system for each zone, and the simulation is going to be calculated with these VRF systems), and with natural ventilation (Calculated Natural Ventilation, or `ZoneVentilation` objects) if you’re going to use the Mixed Mode. The VRF systems replace the zone equipment of the model, so accim removes its `ZoneHVAC:IdealLoadsAirSystem` objects, which no zone would use (before accim 1.0.0 they were kept, and EnergyPlus reported a severe error for each of them). The VRF systems are autosized, so accim enables the sizing calculations of the model, which needs sizing periods (design days, or `SizingPeriod:WeatherFileDays` objects): if it has none, accim warns, since EnergyPlus would stop. On the other hand, if you are going to use any ExistingHVAC script, again you’re supposed to have one or multiple IDFs, however in this case there must be a fully functional HVAC system. Therefore, you must be able to successfully run a simulation with fixed setpoint temperatures in order for the accim package to work. The HVAC system can be any: accim 1.1.0 was tested with 618 example files of EnergyPlus 25.1 (VAV, PTAC, fan coils, furnaces, heat pumps, VRF, radiant systems, chilled beams, dual ducts...), with and without the arguments of section 4.1.1. If the model has `HVACTemplate` objects, `AddAccis` expands them first (`accim.energyplus.expand_objects()`, which runs the program ExpandObjects of EnergyPlus), since their thermostats and HVAC objects only exist once expanded; `add_accis_to_idf` stops with a `ValueError` for them (expand the file first). The main difference between ExistingHVAC only with full air-conditioning and with mixed mode is that in the latter, accim reads whether the existing HVAC system of each zone is on (from the load that its thermostat asks for), and windows need to be actuated in case conditions for natural ventilation are favourable. In both cases, when you export the IDF, please do not request ASHRAE 55 or CEN 15251 results. accim will do so by adding the relevant fields to the People objects (or to the `People:Definition` objects of the `People:Instance` objects, in EnergyPlus 26.2).

By using any ExistingHVAC script you might not get the results that you expect, even if there are no errors in the accim and simulation processes: the operative temperature may be out of the setpoints in some hours. The reason lies on the HVAC system itself, and that is why the VRFsystem script was developed, which keeps the operative temperature between the setpoints. Section 4.1.1 explains the reasons and the arguments that make the existing HVAC systems keep it between them too.

No matter what type or functions are you going to use, the language of the software used to create the input IDF should be English (for example, if you use Designbuilder in Spanish, accim won’t work properly), and it’s not recommended to use any non-standard characters in the input IDF, just like written accents or “ñ”.

Said that, by default accim will transform all the IDF files located in the working folder (the folder where Python is run), except those whose names contain `[` or `_pymod`, which are the files generated by accim; the argument `idfs` takes a list of IDF files instead. Therefore, the quickest way to run the script is opening a prompt command dialog in the folder where the IDF files are located (you can do this by holding Shift and right-click inside the folder, and click on ‘Open PowerShell window here’, or ‘Open in Terminal’ in Windows 11). Then run Python by typing ‘python’ in the command prompt.

First you need to import the module ‘accis’ (stands for Adaptive-Comfort-Control-Implementation Script):

```python
>>> from accim.sim import accis
```

And then, you just need to call the class `AddAccis`:

```python
>>> accis.AddAccis()
```

```{note}
In accim 1.0.0, `addAccis` became `AddAccis`, and its arguments follow the naming conventions of Python
(PEP 8): `script_type` instead of `ScriptType`, `comfort_standard` instead of `ComfStand`, and so on. The old
names still work, with a `DeprecationWarning` that gives the new name, so the scripts written for previous
versions run without changes. The prompts still show the old names. See {doc}`9_migration_guide`.
```

Then you’ll be asked in the prompt to enter some information so that python knows how do you want to set up the output IDFs (the values after the colons are the answers of this example):

```
--------------------------------------------------------
Adaptive-Comfort-Control-Implemented Model (ACCIM) v1.1.0
--------------------------------------------------------

This tool allows to apply adaptive setpoint temperatures. 
For further information, please read the documentation: 
https://accim.readthedocs.io/en/master/
For a visual understanding of the tool, please visit the following jupyter notebooks:
-    Using AddAccis() to apply adaptive setpoint temperatures
https://accim.readthedocs.io/en/master/jupyter_notebooks/addAccis/using_addAccis.html
-    Using rename_epw_files() to rename the EPWs for proper data analysis after simulation
https://accim.readthedocs.io/en/master/jupyter_notebooks/rename_epw_files/using_rename_epw_files.html
-    Using run_ep() to directly run simulations with EnergyPlus
https://accim.readthedocs.io/en/master/jupyter_notebooks/runEp/using_runEp.html
-    Using the class Table() for data analysis
https://accim.readthedocs.io/en/master/jupyter_notebooks/Table/using_Table.html
-    Full example
https://accim.readthedocs.io/en/master/jupyter_notebooks/full_example_IBPSA/full_example_IBPSA.html

Starting with the process.

Now, you are going to be asked to enter some information for different arguments to generate the output IDFs with adaptive setpoint temperatures. 
If you are not sure about how to use these parameters, please take a look at the documentation in the following link: 
https://accim.readthedocs.io/en/master/4_detailed%20use.html

Please, enter the following information:

Enter the ScriptType (
for VRFsystem with full air-conditioning mode: vrf_ac;
for VRFsystem with mixed-mode: vrf_mm;
for ExistingHVAC with mixed mode: ex_mm;
for ExistingHVAC with full air-conditioning mode: ex_ac
): vrf_mm

Enter the SupplyAirTempInputMethod (
for Supply Air Temperature: supply air temperature;
for Temperature Difference: temperature difference;
): temperature difference

Do you want to keep the existing outputs (true or false)?: false

Enter the Output type (standard, simplified, detailed or custom): standard

Enter the Output frequencies separated by space (timestep, hourly, daily, monthly, runperiod): hourly runperiod

Do you want to generate a dataframe to see all outputs? (true or false): false

Enter the EnergyPlus version (9.1 to 26.2, or auto): auto

Enter the Temperature Control method (temperature or pmv): temperature
```

where:

*   script_type (ScriptType in the prompts) can be ‘vrf_mm’, ‘vrf_ac’, ‘ex_mm’ or ‘ex_ac’, and it refers to the type of functions as explained above
*   supply_air_temp_input_method (SupplyAirTempInputMethod) can be ‘supply air temperature’ or ‘temperature difference’, and it is the supply air temperature input method for the VRF systems.
*   keep_existing_outputs (Do you want to keep the existing outputs): existing outputs in the IDF can be kept if entered ‘true’. Otherwise, if entered ‘false’, they will be removed for clarity purposes at results stage.
*   output_type (Output type) can be ‘standard’, ‘detailed’, ‘simplified’ or ‘custom’ and it refers to the simulation results: ‘standard’ means that results will contain the full selection relevant to accim;‘detailed’ is mainly used for testing the software tool; ‘simplified’ means that results are just going to be the hourly operative temperature and VRF consumption of each zone, mainly used when you need the results not to be heavy files, because you are going to run a lot of simulations and capacity is limited; and finally, ‘custom’ allows the user to specify the outputs to be kept or removed by entering them in the python console.
*   output_frequencies (Output frequencies) can be timestep, hourly, daily, monthly and/or runperiod, and these must be entered separated by space. It will add the specified output type (standard or simplified) in all entered frequencies. The outputs decide the size of the results of the simulations: before writing the output IDFs, accim prints its estimate for each simulation and for all the output IDFs (section 4.4), so that you can choose other outputs; `accim.run.estimate_results_size()` estimates or measures it for the IDFs and EPWs of a folder (section 4.6).
*   make_outputs_dataframe (Do you want to generate a dataframe): a pandas DataFrame instance can be created containing all Output:Variable objects. This allows the user to filter the DataFrame as needed, so that it only contains the needed Output:Variable objects, and then it can be entered in the argument `outputs_dataframe`
*   energyplus_version (EnergyPlus version) can be ‘auto’ or a version from ‘9.1’ to ‘26.2’. With ‘auto’ (the default when the arguments are given in the function call), accim reads the version of each IDF and uses the IDD file of that version of EnergyPlus, which must be installed in its default path (for instance, “C:\EnergyPlusV26-2-0” for an IDF of EnergyPlus 26.2). If you enter a version, for instance ‘9.1’, accim will look for the E+9.1.0 IDD file in path “C:\EnergyPlusV9-1-0”, or in the folder given by the environment variable `ACCIM_ENERGYPLUS_DIR` if it has that version.
*   setpoint_type (Temperature Control method) can be ‘temperature’ or ‘temp’, or ‘pmv’. If ‘temp’ is used, the setpoint will be the operative temperature, otherwise if ‘pmv’ is used, the setpoint will be the PMV index.

accis will show on the prompt command dialog all the objects it adds, and those that doesn’t need to be added because were already in the IDF, and finally ask you to enter some values to set up the IDFs as you desire. Please refer to the section titled ‘Setting up the target IDFs’.

Once you run the simulations, check the EnergyPlus warnings and errors in the `.err` file of each simulation.

### 4.1.1 Keeping the operative temperature between the setpoints with the existing HVAC systems

The adaptive setpoints are setpoints of the operative temperature, but the thermostats of EnergyPlus (`ZoneControl:Thermostat`) control the air temperature, unless a `ZoneControl:Thermostat:OperativeTemperature` object makes them control the operative temperature: the VRF systems of accim have one, and so do the models made with DesignBuilder, but few others (3 of the 619 example files of EnergyPlus 25.1). Besides, the existing HVAC systems may not be available while the zones are occupied (a schedule of HVAC operation, night cycle managers, systems that switch off with the outdoor temperature...), may not work with some outdoor temperatures (the VRF systems of EnergyPlus do not cool above 43 °C or heat above 16 °C by default, the heat pumps do not heat below a minimum outdoor temperature, the supplemental heaters do not heat above a maximum one...), or may lack capacity or equipment that heats or cools, or have controls that do not reach the setpoints (the supply air temperature of an air loop, the minimum air flow of the VAV terminals...). The VRF systems of accim avoid all of this: they control the operative temperature, are always available (`'On 24/7'`), work between -20 and 80 °C, and are autosized.

With `ex_ac` and `ex_mm`, five arguments adapt the existing HVAC systems. Only the first two change the model by default; with all of them `False` (or `None`), the existing HVAC systems are simulated as in the input model, with only their setpoints changed:

-   `existing_hvac_operative_temperature_control` (`True` by default, with `setpoint_type='temperature'`): the thermostat of each occupied zone controls the operative temperature of the zone between its setpoints at all times, as those of the VRF systems. It gets a `ThermostatSetpoint:DualSetpoint` object of its own with the setpoint schedules of the zone (`AHST_Sch_<zone>` and `ACST_Sch_<zone>`, which the EMS actuates), the control type schedule `Control type schedule: Always 4` (always dual setpoint), and a `ZoneControl:Thermostat:OperativeTemperature` object if it has none, with the radiative fraction of `TypOperativeTempControlSch` (0.5, as in the output `Zone Operative Temperature`, and 0 on the design days, so that the sizing of the HVAC systems does not change), as with the VRF systems. If it has one, its radiative fraction does not change, but an adaptive comfort model of EnergyPlus in it is removed (it would replace the cooling setpoint of accim). The thermostats of the zones without occupants do not change, and so do the models whose thermostats already work so (those of DesignBuilder). `False` keeps the thermostats of the model, which control the air temperature, and gives the setpoints only to the setpoint object of the first control of each thermostat, as accim 0.x did: with the thermostats of the example files of EnergyPlus (a single cooling, a single heating and a dual setpoint object, shared by all the zones), the zones then keep the setpoints of the model in most of the year, and EnergyPlus may stop. accim needs a thermostat for each occupied zone: the thermostats of ZoneLists are replaced with one thermostat per zone of the list (`<zone> <thermostat>`, as EnergyPlus names them, with copies of the objects that name the thermostat), and a warning lists the occupied zones without a thermostat (except those whose radiant systems follow the setpoints, see the next argument). The thermal comfort thermostats (`ZoneControl:Thermostat:ThermalComfort`, with setpoints of the PMV of Fanger) of the occupied zones, which EnergyPlus uses instead of the temperature thermostats while their control type schedules are not 0, are removed with a warning; the staged thermostats (`ZoneControl:Thermostat:StagedDualSetpoint`), with which the multispeed and unitary systems with staged control heat and cool, get the setpoint schedules of their zones (those of ZoneLists are split as the other thermostats). With `False`, accim only warns about them.
-   `existing_hvac_radiant_setpoints` (`True` by default, with `setpoint_type='temperature'`): the radiant systems (`ZoneHVAC:LowTemperatureRadiant:*`, `ZoneHVAC:HighTemperatureRadiant`), the ventilated slabs (`ZoneHVAC:VentilatedSlab`) and the cooling panels (`ZoneHVAC:CoolingPanel:RadiantConvective:Water`) do not follow the thermostats of the zones, but setpoint schedules of their own, so they would keep the setpoints of the model. Those of the occupied zones get the setpoint schedules of their zones, `AHST_Sch_<zone>` (heating) and `ACST_Sch_<zone>` (cooling), which the EMS of accim actuates, in the setpoint fields that they have in the model (so they heat, cool or both, as in the model), and the operative temperature as their control temperature: the variable flow systems, in their heating and cooling control temperatures (in their `:Design` object since EnergyPlus 9.6, which is copied for each zone if the systems of several zones share it), with their throttling ranges; the constant flow systems and the ventilated slabs, in both the high and the low control temperatures of each mode, so they work at their highest (heating) or lowest (cooling) water or air temperature beyond the setpoint and stop between the setpoints; the electric and high temperature radiant systems, in their heating setpoint. The cooling panels of a zone with a thermostat get instead the control type `ZoneTotalLoad`, so they follow the thermostat (with the operative temperature as their control temperature, EnergyPlus reported plant flow errors), and those of a zone without one, the cooling setpoint schedule; the panels whose control type is `ZoneTotalLoad` or `ZoneConvectiveLoad` already follow the thermostat, and do not change. The objects of the zones without occupants do not change. `False` keeps them as in the model, and warns about them.
-   `existing_hvac_availability_schedule` (`None` by default): the name of a schedule of the model, or `'On 24/7'` (added if the model does not have it), which becomes the availability schedule of the HVAC objects that heat or cool the zones (zone equipment, air terminals, unitary systems, fans, coils, coil systems, VRF systems and evaporative coolers; not the exhaust fans, the units that supply outdoor air and the dehumidifiers), of their air and plant loops, whose availability managers are replaced with an `AvailabilityManager:Scheduled` object with that schedule, and of the plant and condenser operation schemes objects with one scheme (those with several schemes, for different times, do not change). `None` keeps their availability, and warns if a schedule (0 at some time of the run period) or an availability manager can switch them off. In full air-conditioning mode (`ex_ac`), the setpoints apply also when the zones are not occupied, so with `'On 24/7'` the HVAC systems keep the zones between them all day (as `vrf_ac`); in mixed mode (`ex_mm`), they switch off when the zones are not occupied. With `ex_ac`, the outdoor air systems then also work while the zones are empty: with those of the sample OSM office, EnergyPlus warns in each of these timesteps that the minimum outdoor air fraction is greater than the one that the mechanical ventilation asks for (it supplies the minimum; the warnings do not stop the simulation).
-   `existing_hvac_widen_outdoor_temperature_limits` (`False` by default): `True` widens the outdoor temperature limits of the HVAC objects (the fields `Minimum/Maximum Outdoor ... Temperature ...` and `Minimum/Maximum Condenser Inlet Node Temperature in ... Mode`, except those of the defrost, the crankcase heaters and the heat recovery mode) to those of the VRF systems of accim, -20 and 80 °C, or to the bounds of the IDD, if they are narrower (the supplemental heaters of some packaged heat pumps cannot work above 21 °C). Only the narrower limits change. `False` keeps them, and warns about those that are narrower.
-   `existing_hvac_ideal_loads_backup` (`False` by default): `True` adds to each occupied zone with zone HVAC equipment a backup ideal loads air system (`<zone> ACCIS Backup Ideal Loads`), the last equipment of the zone in its cooling and heating sequences (with the load distribution scheme `SequentialLoad`), so the existing equipment supplies the load to the setpoints that it can, and the backup supplies the rest, whatever the HVAC system and the reason (capacity, controls, operating limits, availability, no equipment that cools or heats...). The backup has no limits of capacity and no outdoor air, only meets the sensible load, and has inlet and exhaust nodes of its own (in NodeLists of accim, `<zone> ACCIS Inlet Nodes` and `<zone> ACCIS Exhaust Nodes`, with the nodes of the zone: the NodeLists of the model do not change, since other objects can use them as single nodes). No backup is added to the models whose AirflowNetwork simulates the air distribution system (EnergyPlus needs all the air nodes of their zones in the AirflowNetwork), nor to the zones of the RoomAir model AirflowNetwork (whose `RoomAir:Node:AirflowNetwork:HVACEquipment` objects must have all the equipment of the zone), with a warning. EnergyPlus reports its energy as district heating and cooling, apart from that of the existing HVAC system, and accim adds the outputs `Zone Ideal Loads Zone Sensible Heating Rate` and `Zone Ideal Loads Zone Sensible Cooling Rate` of the backups to the output types `'simplified'` and `'standard'`: they are the loads that the existing HVAC system does not meet, a measure of how far it is from keeping the operative temperature between the setpoints.

The radiant systems (`ZoneHVAC:LowTemperatureRadiant:*`, `ZoneHVAC:HighTemperatureRadiant`), the ventilated slabs and the cooling panels follow the setpoints of accim only with `existing_hvac_radiant_setpoints` (above); other HVAC objects with setpoints of their own (the setpoint managers of the supply air temperature of the air loops, for instance) keep them, and can limit how close the zones get to the setpoints: `existing_hvac_ideal_loads_backup` measures it.

In a year in Seville, the sample OSM office (packaged heat pumps whose thermostats control the air temperature, and an HVAC operation schedule from 6 to 19 h while the zones are occupied until 23 h) had 53 to 77 % of its occupied hours within the setpoints with `ex_ac`; with the operative temperature control, 86 to 93 %; and also always available, or with the backup, 100 %. The sample models of DesignBuilder (PTACs, cooled beams), whose thermostats already controlled the operative temperature, had 99.9 to 100 % (31 to 79 % without the operative temperature control); the one with electric radiators, which cannot cool, 27 to 32 %, and 99.9 to 100 % with the backup; and the example file `5ZoneAirCooled` of EnergyPlus (VAV with reheat), which accim could not simulate before (EnergyPlus stopped), 93 to 100 %, and 100 % with the backup. With the radiant setpoints, the example file `RadLoHydrHeatCoolAuto` of EnergyPlus (variable flow radiant systems that heat and cool) had 99.5 to 100 % of its occupied hours within the setpoints, and 65 to 82 % without them; in the example files whose radiant systems or ventilated slabs heat (`RadLoTempCFloHeatCool`, `RadLoTempElecTermReheat`, `RadHiTempElecTermReheat` and `VentilatedSlab`), the degree-hours below the heating setpoint fell from 49 to 479 K·h in the year in each zone to 0 to 64 K·h, and the hours above the cooling setpoint that remain come from the models (radiant systems that only heat, with air loops that do not reach the setpoints; constant flow systems and a ventilated slab without enough cooling, or that react slowly); and a zone of `5ZoneCoolingPanelBaseboard` (cooling panels) went from 98.9 to 99.9 %. In mixed mode, the operative temperature can still be out of the setpoints in a few hours, while the windows are open or right after them (the windows open for a whole timestep, and the outdoor air can cool the zone below the heating setpoint before they close: `ventilation_control` 2 or 3 and `min_outdoor_temp_offset` limit this), and when the zones become occupied, since the HVAC systems are off while they are not.

### 4.1.2 The windows that accim opens and closes in mixed mode

In mixed mode (`vrf_mm` and `ex_mm`), accim opens the windows of each occupied zone with the EMS when natural ventilation can keep the zone comfortable and its HVAC system is off, and closes them otherwise (section 4.2 describes the conditions, with `hvac_mode` and `ventilation_control`). Which windows these are depends on how the model simulates its natural ventilation (`accim.sim.windows`):

-   With an AirflowNetwork that simulates the multizone airflows (the field `AirflowNetwork Control` of `AirflowNetwork:SimulationControl` is `MultizoneWithoutDistribution` or `MultizoneWithDistribution`): the windows, doors and glass doors of the exterior surfaces of the occupied zones whose `AirflowNetwork:MultiZone:Surface` objects have an opening (`AirflowNetwork:MultiZone:Component:DetailedOpening`, `SimpleOpening` or `HorizontalOpening`), whatever their names. The EMS actuates their venting opening factor, which replaces their own venting control (ventilation control mode, venting availability schedule...). The openings of the interior surfaces (the doors between zones) keep the control of the model. Before accim 1.1.0, accim only found the windows named as in DesignBuilder (`..._Win` and `..._Door`).
-   Otherwise (no AirflowNetwork, or one with `NoMultizoneOrDistribution` or `MultizoneWithDistributionOnlyDuringFanOperation`, with which EnergyPlus simulates the `ZoneVentilation` objects instead): the `ZoneVentilation:WindandStackOpenArea` objects and the `ZoneVentilation:DesignFlowRate` objects of the type `Natural` of the occupied zones, except those whose names contain "infiltration". The other types of `ZoneVentilation:DesignFlowRate` (`Exhaust`, `Intake` and `Balanced`) are fans, not windows, and keep the control of the model. Each occupied zone gets a schedule `Vent_Sch_<zone>`, which the EMS actuates (a virtual window `<zone>_Win`). The objects of spaces count for their zones, and those of ZoneLists and SpaceLists with occupied zones are replaced with one object per zone or space of the list (`<zone or space> <name>`). Their own limits (minimum and maximum indoor and outdoor temperatures, delta temperature and maximum wind speed, and their schedules) are removed, since the EMS decides when they ventilate (with `min_outdoor_temp_offset` and `max_wind_speed`, among others): otherwise they would keep the windows closed when the EMS opens them. Before accim 1.1.0 they were kept: the first window of the sample OSM residential model never ventilated, since its maximum indoor temperature was a schedule of 1 °C.

Other objects of EnergyPlus also open and close the windows, and would override the EMS, so accim removes them, with a warning: the occupant ventilation controls (`AirflowNetwork:OccupantVentilationControl`) of the AirflowNetwork windows (EnergyPlus gives that of a zone, in its `AirflowNetwork:MultiZone:Zone` object, to all the windows and doors of the zone without one of their own: accim removes it from the zone and gives it to the windows and doors that it does not control, such as the doors between zones), and the hybrid ventilation managers (`AvailabilityManager:HybridVentilation`), if accim controls some windows (they act on the AirflowNetwork windows, or on all the `ZoneVentilation` objects of the zones of their air loops, not only on the one they name). The hybrid ventilation managers stay when the AirflowNetwork simulates the air distribution system together with the windows (`MultizoneWithDistribution`): EnergyPlus may fail to solve the airflows of open windows while the fans of the air loops run (it stopped with the example file `AirflowNetwork_MultiZone_SmallOffice_VAV`), and these managers switch the air loops off when they let the windows open; the windows then open only when both the EMS and the managers let them. With `MultizoneWithDistributionOnlyDuringFanOperation`, EnergyPlus simulates the `ZoneVentilation` objects only while the fans of the distribution system are off, so the windows do not ventilate while the fans run (a warning says so). The EMS actuators of the model on the opening factors of the windows that accim controls get a warning: in each timestep, the opening is that of the last EMS program that sets it. A warning lists the occupied zones without windows, which are only air-conditioned.

The windows are those of the model, with their geometry and their physics: for instance, EnergyPlus gives no wind-driven airflow to a `ZoneVentilation:WindandStackOpenArea` object when the wind blows from behind its opening (at more than 90° from its effective angle), and no stack airflow if its height difference is 0, so such a window does not ventilate then, although the EMS opens it. In the tests with the example files of EnergyPlus (`DEVLOG.md`), the windows ventilated when the EMS opened them, and only then, except in the cases above (the hybrid ventilation managers that stay, the fans of the distribution systems that run), and the airflows of the fans (`ZoneVentilation:DesignFlowRate` objects of the types `Exhaust`, `Intake` and `Balanced`), which keep the control of the model.

(setting-up-the-target-idfs)=
## 4.2 Setting up the target IDFs

If you have run `accis.AddAccis()`, you will be asked in the prompt to enter a few more values separated by space to set up the desired IDFs. However, you can also skip the command prompt process by running accis directly including the arguments in the function. Give them as keyword arguments (`script_type='vrf_mm'`, and so on): the order of the arguments is not the one of the prompts, and the first one is `idfs`. The table below lists all the arguments, and their names in accim 0.x, which still work; "asked" means that, if the argument is not given, accim asks for it in the prompt.

| Argument | Name in accim 0.x | Values | Default |
| :--- | :--- | :--- | :--- |
| `idfs` | `idfs` | list of IDF files | all the IDFs of the working folder |
| `script_type` | `ScriptType` | `'vrf_ac'`, `'vrf_mm'`, `'ex_ac'` or `'ex_mm'` | asked |
| `supply_air_temp_input_method` | `SupplyAirTempInputMethod` | `'supply air temperature'` or `'temperature difference'` (only used by the VRF systems) | asked with `vrf_ac` and `vrf_mm` |
| `keep_existing_outputs` | `Output_keep_existing` | `True` or `False` | asked |
| `output_type` | `Output_type` | `'standard'`, `'simplified'`, `'detailed'` or `'custom'` | asked |
| `output_frequencies` | `Output_freqs` | list of `'timestep'`, `'hourly'`, `'daily'`, `'monthly'` and `'runperiod'` | asked |
| `make_outputs_dataframe` | `Output_gen_dataframe` | `True` or `False` | asked with the prompts; otherwise, no DataFrame |
| `outputs_dataframe` | `Output_take_dataframe` | pandas DataFrame | `None` |
| `energyplus_version` | `EnergyPlus_version` | `'auto'`, or from `'9.1'` to `'26.2'` | `'auto'` |
| `setpoint_type` | `TempCtrl` | `'temperature'` (or `'temp'`) or `'pmv'` | asked |
| `comfort_standard` | `ComfStand` | list of numbers from 0 to 22, or 99 (custom model) | asked |
| `custom_slope`, `custom_intercept`, `custom_cooling_offset`, `custom_heating_offset`, `custom_cooling_upper_limit`, `custom_cooling_lower_limit`, `custom_heating_upper_limit`, `custom_heating_lower_limit` | `CustAST_m`, `CustAST_n`, `CustAST_ACSToffset`, `CustAST_AHSToffset`, `CustAST_ACSTaul`, `CustAST_ACSTall`, `CustAST_AHSTaul`, `CustAST_AHSTall` | numbers (only used with `comfort_standard=[99]`) | 0 |
| `category` | `CAT` | list of 1, 2, 3, 80, 85 and 90 | asked |
| `category_cooling_offset`, `category_heating_offset` | `CATcoolOffset`, `CATheatOffset` | numbers (K) | 0 |
| `comfort_mode` | `ComfMod` | list of 0, 0.X, 1, 1.X, 2 and 3 | asked |
| `setpoint_accuracy` | `SetpointAcc` | number greater than 0 | 10000 |
| `cooling_season_start`, `cooling_season_end` | `CoolSeasonStart`, `CoolSeasonEnd` | date `'dd/mm'` or day of the year | 121 (1 May), 274 (1 October) |
| `hvac_mode` | `HVACmode` | list of 0, 1 and 2 | asked with `vrf_mm` and `ex_mm` |
| `ventilation_control` | `VentCtrl` | list of 0, 1, 2 and 3 | asked with `vrf_mm` and `ex_mm` |
| `opening_factor_max_temp_diff`, `opening_factor_min_temp_diff`, `min_opening_factor` | `MaxTempDiffVOF`, `MinTempDiffVOF`, `MultiplierVOF` | numbers | 6, 1, 0.25 |
| `ventilation_setpoint_offset` | `VSToffset` | list of numbers | `[0]` |
| `min_outdoor_temp_offset` | `MinOToffset` | list of positive numbers | `[50]` |
| `max_wind_speed` | `MaxWindSpeed` | list of positive numbers | `[50]` |
| `setpoint_tolerance_start`, `setpoint_tolerance_end`, `setpoint_tolerance_step` | `ASTtol_start`, `ASTtol_end_input`, `ASTtol_steps` | numbers (`setpoint_tolerance_step` greater than 0) | 0.1, 0.1, 0.1 |
| `name_suffix` | `NameSuffix` | text | `''` |
| `vrf_availability_schedule` | `VRFschedule` | name of the availability schedule of the VRF systems | `'On 24/7'` |
| `vrf_eer`, `vrf_cop` | `eer`, `cop` | energy efficiency ratio and coefficient of performance of the VRF systems | 2, 2.1 |
| `existing_hvac_operative_temperature_control` | (new in 1.0.0) | `True` to make the thermostat of each occupied zone control its operative temperature between the setpoints at all times (`ex_ac` and `ex_mm`, see section 4.1.1) | `True` |
| `existing_hvac_radiant_setpoints` | (new in 1.0.0) | `True` to make the radiant systems, ventilated slabs and cooling panels of the occupied zones follow the setpoints, with the operative temperature (`ex_ac` and `ex_mm`, see section 4.1.1) | `True` |
| `existing_hvac_availability_schedule` | (new in 1.0.0) | name of a schedule (or `'On 24/7'`) that makes the existing HVAC systems available, or `None` to keep their availability | `None` |
| `existing_hvac_widen_outdoor_temperature_limits` | (new in 1.0.0) | `True` to widen the outdoor temperature limits of the existing HVAC systems to those of the VRF systems (-20 and 80 °C) | `False` |
| `existing_hvac_ideal_loads_backup` | (new in 1.0.0) | `True` to add a backup ideal loads air system to each occupied zone, which supplies the load that the existing HVAC system does not meet | `False` |
| `hvac_zone_map` | `hvac_zone_map` | deprecated since 1.0.0, without effect (`ex_mm` no longer needs the zone of each HVAC object) | `None` |
| `zone_arguments` | (new in 1.0.0) | dictionary `{zone: {argument: value}}` with the arguments of some zones (see section 4.2.1) | `None` |
| `add_building_averages` | `make_averages` | `True` to add the building averages of the hour-counting variables and some outputs | `False` |
| `debug_ems` | `debugging` | `True` to generate the EDD file of the Energy Management System | `False` |
| `verbose` | `verboseMode` | `True` or `False` | `True` |
| `confirm` | `confirmGen` | `True` to generate the IDFs without asking for confirmation | asked |

The prompts work in two stages. If any of `script_type`, `keep_existing_outputs`, `output_type`, `output_frequencies` or `setpoint_type` (and, with `vrf_ac` and `vrf_mm`, `supply_air_temp_input_method`) is missing, accim asks for all the values of the first stage (those of section 4.1), and these values are used instead of those specified in the function call. Likewise, if any of `comfort_standard`, `category` or `comfort_mode` (and, with `vrf_mm` and `ex_mm`, `hvac_mode` or `ventilation_control`) is missing, accim asks for all the values of the second stage, from `comfort_standard` to `setpoint_tolerance_step` (see section 4.4); `name_suffix`, `verbose` and `confirm` keep the values of the call.

Some example of the usage could be:

```python
from accim.sim import accis
job = accis.AddAccis(
    script_type='vrf_mm',                     # 'vrf_mm', 'vrf_ac', 'ex_mm' or 'ex_ac'
    supply_air_temp_input_method='supply air temperature',
    keep_existing_outputs=False,
    output_type='standard',                   # 'standard', 'simplified', 'detailed' or 'custom'
    output_frequencies=['hourly', 'runperiod'],
    make_outputs_dataframe=False,
    # we just omit outputs_dataframe
    energyplus_version='auto',                # the EnergyPlus version of each IDF
    setpoint_type='temperature',              # 'temperature' (or 'temp') or 'pmv'
    comfort_standard=[0, 1, 2, 3],            # Comfort Standards
    category=[1, 2, 3, 80, 90],               # Categories
    comfort_mode=[0, 1, 2, 3],                # Comfort Modes
    setpoint_accuracy=10,                     # setpoints will be rounded to the first decimal
    # we just omit cooling_season_start, since the default date is May 1st
    # we just omit cooling_season_end, since the default date is October 1st
    hvac_mode=[0, 1, 2],                      # HVAC modes
    ventilation_control=[0, 1],               # Ventilation Controls
    opening_factor_max_temp_diff=20,          # above a difference of 20°C between operative and outdoor temperature,
                                              # windows open the fraction min_opening_factor
    opening_factor_min_temp_diff=1,           # below a difference of 1°C, windows open fully; in between, linearly
    min_opening_factor=0.2,                   # fraction of window opened above opening_factor_max_temp_diff
    ventilation_setpoint_offset=[0, 1, 2],    # Ventilation Setpoint Temperature offsets
    min_outdoor_temp_offset=[0, 1, 2],        # Minimum Outdoor Temperature offsets
    max_wind_speed=[10, 20, 30],              # Maximum Wind Speeds
    setpoint_tolerance_start=0,               # start of the tolerance sequence
    setpoint_tolerance_end=2,                 # end of the tolerance sequence
    setpoint_tolerance_step=0.25,             # steps of the tolerance sequence
    name_suffix='standard',                   # for example, just in case you want to clarify the outputs
    confirm=True,                             # generate the IDFs without asking
)
job.output_idfs.paths                                 # {'output IDF name': path of the file}
```

The returned object keeps the arguments (`job.arguments`), the occupied zones and the windows of each input IDF (`job.occupied_zones`, `job.windows_and_doors`), and the output IDFs (`job.output_idfs`, a dictionary whose IDF objects are read when they are used). The order of the output IDFs and of the objects of each file does not change from one run to another, and the combinations of comfort standard and comfort mode without setpoints (for instance, the static comfort modes of the Chinese models) are skipped with a warning, instead of generating IDFs that EnergyPlus cannot run.

accim reads, changes and writes the models with [eppy](https://eppy.readthedocs.io/) (the input IDFs, `job.input_idfs`, and the output IDFs are IDF objects of eppy). eppy reads each IDF with the IDD of its EnergyPlus version (with `energyplus_version='auto'`, that of its `Version` object), and it reads all the models of a Python session with the same IDD: to work with the models of another EnergyPlus version, use a new Python session (or restart the kernel of the notebook). `accim.sim.accis.load_idf()` reads an IDF file in the same way.

Each argument is explained below:

-   comfort_standard (ComfStand): refers to the thermal comfort standard or model to be applied. Enter any number from 0 to 22 or 99 to select the comfort standard or model to be used; you can see which model is each number in the table below. For example, if you enter ‘0 1 2 3’, you’ll get IDFs for CTE, EN16798-1, ASHRAE 55 and the local model developed by Rijal et al for Japanese dwellings. If you enter 99, that means you want to use some custom adaptive model. Therefore, you'll be asked to enter the slope, y-intercept among other parameters; in the function call, these are the arguments `custom_slope` (slope of the neutral temperature against the running mean outdoor temperature), `custom_intercept` (y-intercept), `custom_cooling_offset` and `custom_heating_offset` (offsets of the cooling and heating setpoints from the neutral temperature, positive and negative respectively), and `custom_cooling_upper_limit`, `custom_cooling_lower_limit`, `custom_heating_upper_limit` and `custom_heating_lower_limit` (upper and lower limits of the running mean outdoor temperature in which the adaptive cooling and heating setpoints are applicable). If you don’t enter any number, it’ll ask you to enter the numbers again.

| comfort_standard | Name | Area | Reference |
| :--- | :--- | :--- | :--- |
| 0 | ESP CTE | Spain | The Government of Spain. Royal Decree 314/2006. Approving the Spanish Technical Building Code CTE-DB-HE-1 2013:1–43. https://www.boe.es/eli/es/rd/2006/03/17/314 (accessed August 6, 2021). |
| 1 | INT EN16798 | Europe | European committee for standardization. EN 16798-1:2019 Energy performance of buildings. Ventilation for buildings. Indoor environmental input parameters for design and assessment of energy performance of buildings addressing indoor air quality, thermal environment, lighting and acoustics. 2019. https://en.tienda.aenor.com/norma-bsi-bs-en-16798-1-2019-000000000030297474 (accessed August 6, 2021). |
| 2 | INT ASHRAE55 | Worldwide | ASHRAE Standard 55-2020 Thermal Environmental Conditions for Human Occupancy, ASHRAE Standard (2020). |
| 3 | JPN Rijal | Japan | Rijal, H. B., Humphreys, M. A., & Nicol, J. F. (2019). Adaptive model and the adaptive mechanisms for thermal comfort in Japanese dwellings. Energy and Buildings, 202, 109371. https://doi.org/10.1016/j.enbuild.2019.109371 |
| 4 | CHN GBT50785 Cold | China | MOHURD, Evaluation Standard for Indoor Thermal Environment in Civil Buildings (GB/T 50785-2012), Ministry of Housing and Urban-Rural Development (MOHURD), Beijing, China, 2012. |
| 5 | CHN GBT50785 HotMild | China | MOHURD, Evaluation Standard for Indoor Thermal Environment in Civil Buildings (GB/T 50785-2012), Ministry of Housing and Urban-Rural Development (MOHURD), Beijing, China, 2012. |
| 6 | CHN Yang | China | Yang, L., Fu, R., He, W., He, Q., & Liu, Y. (2020). Adaptive thermal comfort and climate responsive building design strategies in dry–hot and dry–cold areas: Case study in Turpan, China. Energy and Buildings, 209, 109678. https://doi.org/10.1016/j.enbuild.2019.109678 |
| 7 | IND IMAC C NV | India | Manu, S., Shukla, Y., Rawal, R., Thomas, L. E., & de Dear, R. (2016). Field studies of thermal comfort across multiple climate zones for the subcontinent: India Model for Adaptive Comfort (IMAC). Building and Environment, 98, 55–70. https://doi.org/10.1016/j.buildenv.2015.12.019 |
| 8 | IND IMAC C MM | India | Manu, S., Shukla, Y., Rawal, R., Thomas, L. E., & de Dear, R. (2016). Field studies of thermal comfort across multiple climate zones for the subcontinent: India Model for Adaptive Comfort (IMAC). Building and Environment, 98, 55–70. https://doi.org/10.1016/j.buildenv.2015.12.019 |
| 9 | IND IMAC R 7DRM | India | Rawal, R., Shukla, Y., Vardhan, V., Asrani, S., Schweiker, M., de Dear, R., Garg, V., Mathur, J., Prakash, S., Diddi, S., Ranjan, S. V., Siddiqui, A. N., & Somani, G. (2022). Adaptive thermal comfort model based on field studies in five climate zones across India. Building and Environment, 219, 109187. https://doi.org/10.1016/J.BUILDENV.2022.109187 |
| 10 | IND IMAC R 30DRM | India | Rawal, R., Shukla, Y., Vardhan, V., Asrani, S., Schweiker, M., de Dear, R., Garg, V., Mathur, J., Prakash, S., Diddi, S., Ranjan, S. V., Siddiqui, A. N., & Somani, G. (2022). Adaptive thermal comfort model based on field studies in five climate zones across India. Building and Environment, 219, 109187. https://doi.org/10.1016/J.BUILDENV.2022.109187 |
| 11 | IND Dhaka | India | Dhaka, S., Mathur, J., Brager, G., & Honnekeri, A. (2015). Assessment of thermal environmental conditions and quantification of thermal adaptation in naturally ventilated buildings in composite climate of India. Building and Environment, 86, 17–28. https://doi.org/10.1016/J.BUILDENV.2014.11.024 |
| 12 | ROM Udrea | Romania | Udrea, I., Croitoru, C., Nastase, I., Crutescu, R., & Badescu, V. (2018). First adaptive thermal comfort equation for naturally ventilated buildings in Bucharest, Romania. International Journal of Ventilation, 17(3), 149–165. https://doi.org/10.1080/14733315.2017.1356057 |
| 13 | AUS Williamson | Australia | Williamson, T., & Daniel, L. (2020). A new adaptive thermal comfort model for homes in temperate climates of Australia. Energy and Buildings, 210, 109728. https://doi.org/10.1016/j.enbuild.2019.109728 |
| 14 | AUS DeDear | Australia | de Dear, R., Kim, J., & Parkinson, T. (2018). Residential adaptive comfort in a humid subtropical climate—Sydney Australia. Energy and Buildings, 158, 1296–1305. https://doi.org/10.1016/j.enbuild.2017.11.028 |
| 15 | BRA Rupp NV | Brazil | Rupp, R. F., de Dear, R., & Ghisi, E. (2018). Field study of mixed-mode office buildings in Southern Brazil using an adaptive thermal comfort framework. Energy and Buildings, 158, 1475–1486. https://doi.org/10.1016/J.ENBUILD.2017.11.047 |
| 16 | BRA Rupp AC | Brazil | Rupp, R. F., de Dear, R., & Ghisi, E. (2018). Field study of mixed-mode office buildings in Southern Brazil using an adaptive thermal comfort framework. Energy and Buildings, 158, 1475–1486. https://doi.org/10.1016/J.ENBUILD.2017.11.047 |
| 17 | MEX Oropeza Arid | Mexico | I. Oropeza-Perez, A.H. Petzold-Rodriguez, C. Bonilla-Lopez, Adaptive thermal comfort in the main Mexican climate conditions with and without passive cooling, Energy and Buildings. 145 (2017) 251–258. https://doi.org/10.1016/j.enbuild.2017.04.031. |
| 18 | MEX Oropeza DryTropic | Mexico | I. Oropeza-Perez, A.H. Petzold-Rodriguez, C. Bonilla-Lopez, Adaptive thermal comfort in the main Mexican climate conditions with and without passive cooling, Energy and Buildings. 145 (2017) 251–258. https://doi.org/10.1016/j.enbuild.2017.04.031. |
| 19 | MEX Oropeza Temperate | Mexico | I. Oropeza-Perez, A.H. Petzold-Rodriguez, C. Bonilla-Lopez, Adaptive thermal comfort in the main Mexican climate conditions with and without passive cooling, Energy and Buildings. 145 (2017) 251–258. https://doi.org/10.1016/j.enbuild.2017.04.031. |
| 20 | MEX Oropeza HumTropic | Mexico | I. Oropeza-Perez, A.H. Petzold-Rodriguez, C. Bonilla-Lopez, Adaptive thermal comfort in the main Mexican climate conditions with and without passive cooling, Energy and Buildings. 145 (2017) 251–258. https://doi.org/10.1016/j.enbuild.2017.04.031. |
| 21 | CHL Perez-Fargallo | Chile | A. Pérez-Fargallo, J.A. Pulido-Arcas, C. Rubio-Bellido, M. Trebilcock, B. Piderit, S. Attia, Development of a new adaptive comfort model for low income housing in the central-south of chile, Energy Build. 178 (2018) 94–106. https://doi.org/10.1016/j.enbuild.2018.08.030. |
| 22 | INT ISO7730 | Worldwide | ISO, 2005. ISO 7730: Ergonomics of the thermal environment Analytical determination and interpretation of thermal comfort using calculation of the PMV and PPD indices and local thermal comfort criteria. Management 3, 605–615. https://doi.org/10.1016/j.soildyn.2004.11.005 |
| 99 | CUSTOM | - | Custom adaptive model, defined by the arguments `custom_*` (`custom_slope`, `custom_intercept`...) |

-   category (CAT): refers to the category of the thermal comfort model applied. Most of the Comfort Standards work with 80 and 90% acceptability levels, except the European EN 16798-1 (works with Categories 1, 2 and 3), the Chinese GB/T 50785 (works with categories 1 and 2), and the India Model for Adaptive Comfort - Commercial (which works with 80, 85 and 90% acceptability levels). So, for example, if you are going to use the EN16798-1 (comfort_standard = 1), you can enter ‘1 2 3’ to generate setpoint temperatures for Categories 1, 2 and 3. Or, if you are going to use the IMAC Commercial in naturally ventilated mode (comfort_standard = 7), you can enter ‘80 85 90’ to generate setpoint temperatures for these acceptability levels. All categories are referenced in the [full list of setpoint temperatures](https://htmlpreview.github.io/?https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html) at the end of this section. Please note that the Category values must be consistent with the Comfort Standard values previously entered. If, for instance, you enter ‘1’ in the Comfort Standard value (means you’re asking for EN16798 model), but then enter ‘80’ or ‘90’ in the Category value (which are categories used in ASHRAE55), you won’t get the results you want.
-   category_cooling_offset (CATcoolOffset): it is an offset in celsius degrees summed to the upper comfort limit. For instance, ASHRAE 55 80% acceptability is +-3.5K; if 1 was entered in category_cooling_offset, then the upper comfort limit would be raised to 4.5K
-   category_heating_offset (CATheatOffset): it is an offset in celsius degrees summed to the lower comfort limit. For instance, ASHRAE 55 80% acceptability is +-3.5K; if -1 was entered in category_heating_offset, then the lower comfort limit would be lowered to 4.5K
-   comfort_mode (ComfMod): is the Comfort Mode, and refers to the setpoint behaviour. It controls if the setpoints are static (when comfort_mode = 0 or 0.X) or adaptive (when comfort_mode = 1 or 1.X, 2 or 3). When they are adaptive, it also controls the comfort model applied when the adaptive model is not applicable (that is, when the running mean outdoor temperature limits are exceeded), in which case a PMV-based model is applied. Each comfort mode for each comfort standard and category is referenced at the [full list of setpoint temperatures](https://htmlpreview.github.io/?https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html). Please refer to the research article https://www.mdpi.com/1996-1073/12/8/1498 for more information. Figure below shows the variation of setpoint temperatures when comfort_mode is 0 (upper left), 1 (upper right), 2 (lower left) and 3 (lower right), when comfort_standard is 1 (EN 16798-1, although figure shows the superseded standard, but the setpoint behaviour is similar)

![ComfMod](https://www.mdpi.com/energies/energies-12-01498/article_deploy/html/images/energies-12-01498-g002.png)

-   setpoint_accuracy (SetpointAcc): refers to the accuracy of the setpoint temperatures. Any number, integer or float, can be entered in this argument. For instance, if 1 was entered, the cooling setpoint would be rounded to the nearest integer below adaptive upper comfort limit minus tolerance (setpoint_tolerance), and the heating setpoint would be rounded to the nearest integer above adaptive lower comfort limit plus tolerance. If 27.46 and 20.46 were the upper and lower comfort limits and its tolerances were respectively -0.1 and +0.1, then the nearest integers to 27.36 and 20.56 would be 27 and 21, and therefore, these would be the cooling and heating setpoint temperatures. If 2 was used instead, then the rounding would be done to the nearest half. If 10 were used, the rounding would be done to the first decimal. If 0.5 or 0.1 were used, the rounding would be done respectively every 2 or 10 celsius degrees.
-   cooling_season_start (CoolSeasonStart): it is the start of the cooling season, only used when EN16798-1, ASHRAE 55 or ISO7730 are entered in comfort_standard (respectively, comfort_standard = 1, 2 and 22) and setpoint behaviour is set to static (i.e. comfort_mode = 0). This argument can take the number of the day in the year (i.e. an integer) or a string containing a date in format dd/mm (for instance, “01/05”). Values of cooling_season_start greater than cooling_season_end can be used, therefore denoting the location of the EPW file should be in the south hemisphere. The default value is 121 (May 1st).
-   cooling_season_end (CoolSeasonEnd): Similar to cooling_season_start, but it is the end of the cooling season. Again, only used when EN16798-1, ASHRAE 55 or ISO7730 are entered in comfort_standard (respectively, comfort_standard = 1, 2 and 22) and setpoint behaviour is set to static (i.e. comfort_mode = 0). Again, this argument can take the number of the day in the year (i.e. an integer) or a string containing a date in format dd/mm (for instance, “01/05”). Values of cooling_season_end smaller than cooling_season_start can be used, therefore denoting the location of the EPW file should be in the south hemisphere. The default value is 274 (October 1st).
-   hvac_mode (HVACmode): refers to the HVAC mode applied. Enter 0 for Fully Air-conditioned (AC), 1 for Naturally ventilated (NV) and/or 2 for Mixed Mode (MM). Please note that Calculated natural ventilation must be enabled so that Mixed Mode works. So, for example, if you enter ‘0 1 2’ you’ll be getting all HVAC modes, or if you just enter ‘0 1’ you’ll be getting just Fully Air-conditioned and Naturally ventilated.
-   ventilation_control (VentCtrl): refers to the ventilation control, only used in for NV and MM. When using NV, If you enter ‘0’, ventilation will be allowed if operative temperature exceeds neutral temperature (also known as comfort temperature); if you enter ‘1’, ventilation will be allowed if operative temperature exceeds the upper comfort limit. In other words, sets the value of the neutral temperature or the upper comfort limit to the Ventilation Setpoint Temperature (VST). When using MM, 0 = Ventilates above neutral temperature and fully opens doors and windows; 1 = Ventilates above lower comfort limit and fully opens doors and windows; 2 = Ventilates above neutral temperature and opens doors and windows based on the customised venting opening factor; and 3 = Ventilates above lower comfort limit and opens doors and windows based on the customised venting opening factor. Either way, if you enter ‘0 1’ you’ll be getting both ventilation control modes.
-   opening_factor_max_temp_diff (MaxTempDiffVOF): Maximum Temperature Difference for Venting Opening Factor. Maximum temperature difference between indoor operative and outdoor temperatures, which when exceeded, windows and doors are opened only the fraction specified in the min_opening_factor argument. If temperature difference oscillates between maximum and minimum, the windows and doors are opened based on the linear equation. Follows the same operation as explained in [Designbuilder help website](https://designbuilder.co.uk/helpv7.0/Content/CalculatedNatVent.htm). The default value is 6.
-   opening_factor_min_temp_diff (MinTempDiffVOF): Minimum Temperature Difference for Venting Opening Factor. Minimum temperature difference between indoor operative and outdoor temperatures, which when smaller, windows and doors are fully opened. If temperature difference oscillates between maximum and minimum, the windows and doors are opened based on the linear equation. Follows the same operation as explained in [Designbuilder help website](https://designbuilder.co.uk/helpv7.0/Content/CalculatedNatVent.htm). The default value is 1.
-   min_opening_factor (MultiplierVOF): the minimum Venting Opening Factor, that is, the fraction of the windows that will be opened when temperature difference exceeds opening_factor_max_temp_diff, between 0 and 1 (between the minimum and the maximum temperature differences, the fraction goes linearly from 1 to this value). Follows the same operation as explained in [Designbuilder help website](https://designbuilder.co.uk/helpv7.0/Content/CalculatedNatVent.htm). The default value is 0.25. ![Venting Opening Factor](images/VentingOpeningFactor.png)
-   ventilation_setpoint_offset (VSToffset): stands for Ventilation Setpoint Temperature (VST) offset, again only used in Mixed Mode (HVAC Mode ‘2’). Applies the entered values as an offset to the VST, in Celsius degrees. Values entered can be positive or negative float or integers, and must be space-separated. For example, if you enter ‘-2 -1 0 1 2’ you’ll be getting offsets of -2°C, -1°C, 0°C, 1°C and 2°C to the VST. If you don’t enter any number, it’ll be used ‘0’ as the default value.
-   min_outdoor_temp_offset (MinOToffset): stands for Minimum Outdoor Temperature offset, again only used in Mixed Mode (HVAC Mode ‘2’). Sets the minimum outdoor temperature an offset to the heating setpoint temperature. For example, if you enter ‘1’ (please, note that the numbers must be positive), ventilation won’t be allowed if outdoor temperature falls below 1°C below the heating setpoint, in order to prevent from entering excessive cold. Therefore, below said limit, windows are closed and, if needed, air conditioning starts to work. Entered values can be float or integers, but always positive numbers, and must be space-separated. For example, if you enter ‘0 1 2’ you’ll be getting offsets of 0°C, 1°C and 2°C to the heating setpoint temperature. If you don’t enter any number, it’ll be used ‘50’ as the default value (that is 50°C below heating setpoint temperature, and therefore no limit is applied).
-   max_wind_speed (MaxWindSpeed): stands for maximum wind speed, again only used in Mixed Mode (HVAC Mode ‘2’). Sets the maximum wind speed in which ventilation is allowed, in m/s. Therefore, if you enter ‘20’, ventilation won’t be allowed if wind speed is greater than 20 m/s. Entered values can be float or integers, but always positive numbers, and must be space-separated. For example, if you enter ‘5 10 15 20’ you’ll be getting different IDFs with maximum wind speeds of 5 m/s, 10 m/s, 15 m/s and 20 m/s. If you don’t enter any number, it’ll be used ‘50’ as the default value (that is 50 m/s, and therefore no limit is applied).
-   setpoint_tolerance_start, setpoint_tolerance_end and setpoint_tolerance_step (ASTtol): stand for Adaptive Setpoint Temperature tolerance. It applies the number that you enter as a tolerance for the adaptive heating and cooling setpoint temperatures. The original problem was that, if we assigned the adaptive setpoint straight to the comfort limit (i.e. you enter ‘0’ for the tolerance), there were a few hours that fell outside the comfort zone because of the error in some decimals in the simulation of the operative temperature. Therefore, the original purpose of this feature is to control that all hours are comfortable hours (i.e. operative temperature falls within the comfort zone), and we can make that sure by considering a little tolerance of 0.10 °C. For example, say that adaptive cooling and heating setpoints are originally 29.5 and 21.5°C at some day; if you enter ‘1’ for the tolerance, then the setpoints would be modified to 28.5 and 22.5°C (1°C below original cooling setpoint, and 1°C above original heating setpoint). The function will create a sequence of numbers based on the entered values. So, numbers must be entered in 3 stages: first, the start of the sequence; second, the end of the sequence, and third, the steps. So for example, if you enter ‘0’ for the start, ‘1’ for the end, and ‘0.25’ for the steps, you would be getting tolerances of 0°C, 0.25°C, 0.5°C, 0.75°C and 1°C. If you don’t enter any number, it’ll be used ‘0.1’ as the default value (as previously said, to make sure all hours are comfortable hours), and you would be getting only one variation of 0.1°C.
-   name_suffix (NameSuffix): the text you would like to add at the end of the file name.
-   verbose (verboseMode): True to print all process in screen, False to not to print it. Default is True.
-   confirm (confirmGen): if omitted, accim lists the output IDFs and asks you to confirm in command prompt before generating them. True to confirm automatically the generation of IDFs, and False to stop before generating them (for instance, to get only the DataFrame of `make_outputs_dataframe`). So, if you are going to set it True, be sure about the number of IDFs you are going to generate, because these might be thousands.
-   idfs: a list of the IDF files to use as input, instead of all the IDF files of the working folder.
-   make_outputs_dataframe and outputs_dataframe (Output_gen_dataframe and Output_take_dataframe): with `make_outputs_dataframe=True`, accim stores a pandas DataFrame with all the Output:Variable objects in the attribute `df_outputs` of the returned object; you can filter it and enter it in `outputs_dataframe` to keep only those outputs (see {doc}`jupyter_notebooks/addAccis/using_addAccis`).
-   vrf_availability_schedule (VRFschedule), vrf_eer and vrf_cop: the availability schedule (‘On 24/7’ by default), the energy efficiency ratio (2) and the coefficient of performance (2.1) of the VRF systems added by the scripts ‘vrf_ac’ and ‘vrf_mm’.
-   existing_hvac_operative_temperature_control, existing_hvac_radiant_setpoints, existing_hvac_availability_schedule, existing_hvac_widen_outdoor_temperature_limits and existing_hvac_ideal_loads_backup: how accim adapts the existing HVAC systems of the scripts ‘ex_ac’ and ‘ex_mm’ so that they keep the operative temperature between the setpoints (see section 4.1.1). Only the first two change the model by default; with all of them `False` (or `None`), the HVAC systems are simulated as in the input model, with only their setpoints changed.
-   hvac_zone_map: deprecated since accim 1.0.0, without effect (with a `DeprecationWarning`): it gave the zone served by the HVAC objects that `ex_mm` could not assign to a zone, and `ex_mm` now reads the loads of the thermostats instead (see section 4.1).
-   zone_arguments: the arguments of some occupied zones, which are the same in all the output IDFs; the other zones have those of each output IDF (see section 4.2.1).
-   add_building_averages: True to make averages of the hour-counting variables. Default is False.
-   debug_ems: True to add an Output:EnergyManagementSystem object, so that EnergyPlus writes the EDD file with the details of the Energy Management System programs. Default is False.

So, below you can see a sample name of an IDF created by using accim’s VRFsystem functions. The package takes the original IDF file as a reference, saves a copy, run all the functions so that setpoint temperatures are transformed from static to adaptive, an changes its name based on the values previously entered:

**TestModel_onlyGeometryForVRFsystem[CS_INT EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_standard**

where:

-   ‘TestModel_onlyGeometryForVRFsystem’ is the name of the original IDF.
-   CS refers to the Comfort Standard, and it’s followed by the thermal comfort standard applied (could be ‘ESP CTE’, ‘INT EN16798’, ‘INT ASHRAE55’, ‘JPN Rijal’, etc).
-   CA refers to the Category, which could be 1, 2 or 3 if CS is EN16798, 80 or 90 if CS is ASHRAE55 or other models, or 80, 85 or 90 in case of the IMAC C.
-   CM refers to the Comfort Mode, which could be 0 (Static), 1, 2, or 3 (Adaptive modes).
-   HM refers to the HVAC Mode, which could be 0 (Full air conditioning), 1 (Naturally ventilated), or 2 (Mixed Mode).
-   VC refers to the Ventilation Control, which could be 0, 1, 2 or 3.
-   VO refers to the Ventilation setpoint temperature offset, which could be any number, float or integer, positive or negative.
-   MT refers to the Minimum Outdoor Temperature offset, which could be any number, float or integer, but always positive number.
-   MW refers to the Maximum Wind Speed, which could be any number, float or integer, but always positive number.
-   AT refers to the Adaptive Setpoint Temperature tolerance (setpoint_tolerance), which could be any number, float or integer, but always positive number. Please remember this number comes from a 3-stage process (refer to the explanation above).
-   NS refers to the Name Suffix, here ‘standard’, which can be whatever you want; it is ‘X’ if no suffix is given. For example, this allows you to make a for loop with ‘standard’, ‘simplified’ and ‘timestep’ and run the simulations with all type of outputs.

The numbers of the name keep the format in which they were entered: when they are entered in the prompt, they are read as decimal numbers, so the name contains, for instance, ‘CM_3.0’; with `comfort_mode=[3]` in the function call, it contains ‘CM_3’.

If some inputs are not used or don’t make sense, you’ll be able to se an ‘X’ in the output IDF file. For example, if you use CTE as Comfort Standard, then the inputs for Category and Comfort Mode (which are only for EN16798-1 and ASHRAE 55) are not used in the process, and the output IDF would contain in its name ‘CS_ESP CTE[CA_X[CM_X’. Another similar case occurs if you use Full air-conditioning HVAC Mode (i.e. enter ‘0’ for HVAC Mode), or if you use the ‘ex_ac’ script type, where the output IDF would contain in its name ‘[HM_0[VC_X[VO_X[MT_X[MW_X’.

(zone-arguments)=
### 4.2.1 Different arguments for each zone

By default, all the occupied zones of a model have the same arguments. Since accim 1.0.0, each zone can have its own: for instance, the offices with the adaptive model of EN 16798-1 and air conditioning, and the meeting rooms with that of ASHRAE 55 and natural ventilation. The argument `zone_arguments` of `AddAccis` and of `modify_accis` gives the arguments of some zones, as a dictionary `{zone: {argument: value}}`:

```python
from accim.sim import accis

accis.AddAccis(
    script_type='vrf_mm',
    supply_air_temp_input_method='temperature difference',
    output_type='standard',
    output_frequencies=['hourly'],
    keep_existing_outputs=False,
    setpoint_type='temperature',
    comfort_standard=[1, 2],      # The other zones: EN 16798-1 and ASHRAE 55, in two output IDFs
    category=[3, 80],
    comfort_mode=[3],
    hvac_mode=[2],
    ventilation_control=[0],
    zone_arguments={
        'Block1:Zone2': {'comfort_standard': 99, 'category': 80, 'comfort_mode': 3, 'hvac_mode': 0,
                         'custom_slope': 0.3, 'custom_intercept': 18, 'custom_cooling_offset': 3,
                         'custom_heating_offset': -3, 'custom_cooling_upper_limit': 30,
                         'custom_cooling_lower_limit': 10, 'custom_heating_upper_limit': 30,
                         'custom_heating_lower_limit': 10},
    },
    confirm=True,
)
```

-   The zones are the occupied zones of the models, given by their names (in upper or lower case), or by the keys of the dictionaries of the aPMV setpoints (‘<space> <people>’, see section 4.8, and `accim.sim.apmv.get_available_target_names()`). With several input IDFs, each zone is applied to the models that have it, and accim stops if a zone is in none of them.
-   The arguments are those of `modify_accis`, with one value each: `comfort_standard`, `category`, `comfort_mode`, `category_cooling_offset`, `category_heating_offset`, `setpoint_accuracy`, the arguments of the custom model (`custom_slope`, `custom_intercept`...), `cooling_season_start`, `cooling_season_end`, `hvac_mode`, `ventilation_control`, `ventilation_setpoint_offset`, `min_outdoor_temp_offset`, `max_wind_speed`, `opening_factor_max_temp_diff`, `opening_factor_min_temp_diff`, `min_opening_factor` and `setpoint_tolerance` (the tolerance of the setpoints). The arguments that a zone does not give are those of each output IDF; when the output IDF has no natural ventilation (HVAC mode 0) and the zone has it, its ventilation arguments are the first values of `ventilation_control`, `ventilation_setpoint_offset`, `min_outdoor_temp_offset` and `max_wind_speed`.
-   With `AddAccis`, the zones of `zone_arguments` have the same arguments in all the output IDFs, whose names give the arguments of the other zones (use `name_suffix` to tell them apart). Each of these zones needs a comfort standard with setpoints for its category and comfort mode, and HVAC modes 1 and 2 only with ‘vrf_mm’ and ‘ex_mm’: accim checks it before writing any output IDF. `zone_arguments` needs `setpoint_type='temperature'`. The attribute `zone_arguments` of the returned object gives the zones found in each input IDF.

With an IDF object, `add_accis_to_idf` adds the ACCIS with the same arguments in all the zones, and `modify_accis` sets them for all the zones or, with `zone_arguments`, for some of them:

```python
accis.add_accis_to_idf(idf, script_type='vrf_mm', supply_air_temp_input_method='temperature difference',
                       output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                       setpoint_type='temperature')
accis.modify_accis(idf, comfort_standard=1, category=3, comfort_mode=3, hvac_mode=2, ventilation_control=0,
                   zone_arguments={'Block1:Zone2': {'comfort_standard': 2, 'category': 80, 'hvac_mode': 0}})
```

The arguments of `modify_accis` that are `None` (`comfort_standard`, `category`, `comfort_mode`, `hvac_mode` and `ventilation_control`, by default) keep the values of each zone. The models of earlier versions of accim, whose zones share the program `SetInputData`, can only have the same arguments in all the zones.

In the output IDFs, each zone has all its arguments in the Energy Management System program `SetInputData_<zone>`, and its program `RunACCIS_<zone>` runs it, and then the programs that calculate and apply the setpoints of the zone (`SetAppLimits`, `ApplyCAT`, `SetComfTemp`, `SetAST`...). You can edit the arguments of a zone in its program `SetInputData_<zone>`, except the comfort standard: each output IDF of `AddAccis` only has the EMS code of the comfort standards of its zones (in `SetComfTemp`, `SetAppLimits`, `ApplyCAT`, `CountHours_<zone>`, `SetAST_Master` and the subprograms `SetAST_CS<n>_<chunk>`), so EnergyPlus stops with a comfort standard without its code. Change it with `modify_accis`, which adds the code of the comfort standards that it sets; the models of `add_accis_to_idf` have the code of all of them. The lines of the EMS programs are indented inside the blocks `IF` and `WHILE`, which EnergyPlus ignores. Besides the outputs of the whole model (`Comfort Temperature`, `Adaptive Cooling Setpoint Temperature`...), which have the values of the last zone (those of every zone if all the zones have the same arguments), the setpoints of each zone are reported as `Comfort Temperature_<zone>`, `Adaptive Cooling Setpoint Temperature_<zone>`, `Adaptive Heating Setpoint Temperature_<zone>`, their values without tolerance and, in mixed mode, `Ventilation Setpoint Temperature_<zone>` and `Minimum Outdoor Temperature for ventilation_<zone>`.

(setpoint-ems-code)=
## 4.3 Full list of setpoint temperatures

Depending on the arguments comfort_standard, category and comfort_mode, cooling and heating setpoint temperatures will be the following:

(If it is too small, you can look at it also at the [Github repository](https://htmlpreview.github.io/?https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html))

![full_table.png](images/full_table.png)

To see how the ACCIS calculates the setpoints of a comfort standard, category and comfort mode before adding it to a model (which setpoints apply, and what they are out of the applicability limits), print their EMS code with `print_setpoint_ems_code` (`get_setpoint_ems_code` gives it as text). They take the arguments of `modify_accis`, with one value each:

```python
>>> from accim.utils import print_setpoint_ems_code
>>> print_setpoint_ems_code(comfort_standard=1, category=2, comfort_mode=3)
```

The code is that of the output IDFs, indented, in the order in which the program `RunACCIS_<zone>` of each zone runs it in each timestep: the inputs of the zone (`SetInputData_<zone>`), the applicability limits (`SetAppLimits`), the offsets of the category (`ApplyCAT`), the comfort temperature (`SetComfTemp`), the cooling season (`SetAST_Master`), the setpoints of the comfort mode with their rounding (its lines in the subprogram `SetAST_CS<n>_<chunk>`) and the setpoints without tolerance (`SetASTnoTol`), with comments that explain the variables. For INT EN16798, category II and comfort mode 3, the setpoints are these: out of the applicability limits (a running mean outdoor temperature of 10 to 30 °C), they keep the value that they have at the limit.

```text
! --- SetAST_CS1_1, its lines for ComfMod == 3: the setpoints, and their rounding ---
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
    set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol
elseif RMOT < ACSTall
    set ACST = ACSTall*0.33+18.8+ACSToffset+ACSTtol
elseif RMOT > ACSTaul
    set ACST = ACSTaul*0.33+18.8+ACSToffset+ACSTtol
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
    set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol
elseif RMOT < AHSTall
    set AHST = AHSTall*0.33+18.8+AHSToffset+AHSTtol
elseif RMOT > AHSTaul
    set AHST = AHSTaul*0.33+18.8+AHSToffset+AHSTtol
endif
```

Without `category` or `comfort_mode`, the code covers all of them (the offsets of every category, and the subprograms of the comfort standard, whole). The combinations that give no setpoints raise a `ValueError`, as in `AddAccis`.

## 4.4 Putting it into practice: Adaptive setpoint temperatures step by step

You can see a Jupyter Notebook in the How-to Guides section of this documentation: {doc}`jupyter_notebooks/addAccis/using_addAccis`. To run it on your computer, copy the folder `jupyter_notebooks/addAccis` of the sample files to a working folder (see {ref}`running-example-notebooks`).

You can also see an example below. The input file is included in the folder `sample IDFs/input_IDFs` of the sample files, and it was originally named `TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf` (a model of EnergyPlus 25.1), but for clarity purposes in this case has been renamed to “TestModel.idf”.

So, say you have an IDF in some folder, called ‘TestModel.idf’. So, you can either open an IDE or simply a CMD dialog pointing at that path and execute python. Let’s run the functions to get the energy models with adaptive setpoint temperatures.

```python
>>> from accim.sim import accis
>>> accis.AddAccis()
```

When we hit enter, we’ll be asked to enter some information regarding the script type, the outputs and the EnergyPlus version (the values after the colons are the answers of this example):

```

--------------------------------------------------------
Adaptive-Comfort-Control-Implemented Model (ACCIM) v1.1.0
--------------------------------------------------------

This tool allows to apply adaptive setpoint temperatures.
For further information, please read the documentation:
https://accim.readthedocs.io/en/master/
For a visual understanding of the tool, please visit the following jupyter notebooks:
-    Using AddAccis() to apply adaptive setpoint temperatures
https://accim.readthedocs.io/en/master/jupyter_notebooks/addAccis/using_addAccis.html
-    Using rename_epw_files() to rename the EPWs for proper data analysis after simulation
https://accim.readthedocs.io/en/master/jupyter_notebooks/rename_epw_files/using_rename_epw_files.html
-    Using run_ep() to directly run simulations with EnergyPlus
https://accim.readthedocs.io/en/master/jupyter_notebooks/runEp/using_runEp.html
-    Using the class Table() for data analysis
https://accim.readthedocs.io/en/master/jupyter_notebooks/Table/using_Table.html
-    Full example
https://accim.readthedocs.io/en/master/jupyter_notebooks/full_example_IBPSA/full_example_IBPSA.html

Starting with the process.

Now, you are going to be asked to enter some information for different arguments to generate the output IDFs with adaptive setpoint temperatures.
If you are not sure about how to use these parameters, please take a look at the documentation in the following link:
https://accim.readthedocs.io/en/master/4_detailed%20use.html

Please, enter the following information:

Enter the ScriptType (
for VRFsystem with full air-conditioning mode: vrf_ac;
for VRFsystem with mixed-mode: vrf_mm;
for ExistingHVAC with mixed mode: ex_mm;
for ExistingHVAC with full air-conditioning mode: ex_ac
): vrf_mm

Enter the SupplyAirTempInputMethod (
for Supply Air Temperature: supply air temperature;
for Temperature Difference: temperature difference;
): temperature difference

Do you want to keep the existing outputs (true or false)?: false

Enter the Output type (standard, simplified, detailed or custom): standard

Enter the Output frequencies separated by space (timestep, hourly, daily, monthly, runperiod): hourly runperiod

Do you want to generate a dataframe to see all outputs? (true or false): false

Enter the EnergyPlus version (9.1 to 26.2, or auto): auto

Enter the Temperature Control method (temperature or pmv): temperature
```

When we hit enter, it’s going to add all the EnergyPlus objects needed:

```
Basic input data:
Script type is: vrf_mm
Supply Air Temperature Input Method is: temperature difference
Output type is: standard
Output frequencies are:
['hourly', 'runperiod']
Temperature Control method is: temperature

=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================

Starting with file:
TestModel
IDD location is: C:\EnergyPlusV25-1-0\Energy+.idd
The occupied zones in the model TestModel are:
Block1:Zone2
Block1:Zone1
The windows and doors in the model TestModel are:
Block1_Zone2_Wall_3_0_0_0_0_0_Win
.
.
.
Added Output:Meter for Cooling:EnergyTransfer (runperiod)
Added Output:Meter for Heating:Electricity (runperiod)
Added Output:Meter for Cooling:Electricity (runperiod)
Modified - SimulationControl object: enabled Zone, System, and Plant Sizing Calculations
Ending with file:
TestModel

=======================END OF GENERIC IDF FILE GENERATION PROCESS=======================

The following IDFs will not work, so no output IDFs will be generated from them:
None

```

And then ask us to enter the required information to generate the output IDF files (you can omit some by hitting enter without entering any value):

```
=======================START OF OUTPUT IDF FILES GENERATION PROCESS=======================

The information you will be required to enter below will be used to generate the customised output IDFs:
Enter the Comfort Standard numbers separated by space (
0 = ESP CTE;
1 = INT EN16798-1;
2 = INT ASHRAE55;
3 = JPN Rijal;
4 = CHN GBT50785 Cold;
5 = CHN GBT50785 HotMild;
6 = CHN Yang;
7 = IND IMAC C NV;
8 = IND IMAC C MM;
9 = IND IMAC R 7DRM;
10 = IND IMAC R 30DRM;
11 = IND Dhaka;
12 = ROM Udrea;
13 = AUS Williamson;
14 = AUS DeDear;
15 = BRA Rupp NV;
16 = BRA Rupp AC;
17 = MEX Oropeza Arid;
18 = MEX Oropeza DryTropic;
19 = MEX Oropeza Temperate;
20 = MEX Oropeza HumTropic;
21 = CHL Perez-Fargallo;
22 = INT ISO7730;
99 = CUSTOM;
Please refer to the full list of setpoint temperatures at https://htmlpreview.github.io/?https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html
): 1 2 7
          Are you sure the numbers are correct? [y or [] / n]:


For the comfort standard 1 = INT EN16798, the available categories you can choose are:
1 = EN16798 Category I
2 = EN16798 Category II
3 = EN16798 Category III
For the comfort standard 2 = INT ASHRAE55, the available categories you can choose are:
80 = ASHRAE 55 80% acceptability
90 = ASHRAE 55 90% acceptability
For the comfort standard 7 = IND IMAC C NV, the available categories you can choose are:
80 = 80% acceptability
85 = 85% acceptability
90 = 90% acceptability
Enter the Category numbers separated by space (
1 = CAT I / CAT A;
2 = CAT II / CAT B;
3 = CAT III / CAT C;
80 = 80% ACCEPT;
85 = 85% ACCEPT;
90 = 90% ACCEPT;
Please refer to the full list of setpoint temperatures at https://htmlpreview.github.io/?https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html
):2 3 85 90
          Are you sure the numbers are correct? [y or [] / n]:


For the comfort standard 1 = INT EN16798, the available ComfMods you can choose are:
0 = EN16798 Static setpoints
1 = EN16798 Adaptive setpoints when applicable, otherwise CTE
2 = EN16798 Adaptive setpoints when applicable, otherwise EN16798 Static setpoints
3 = EN16798 Adaptive setpoints when applicable, otherwise EN16798 Adaptive setpoints horizontally extended
For the comfort standard 2 = INT ASHRAE55, the available ComfMods you can choose are:
0 = ISO 7730 Static setpoints
1 = ASHRAE 55 Adaptive setpoints when applicable, otherwise CTE
2 = ASHRAE 55 Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints
3 = ASHRAE 55 Adaptive setpoints when applicable, otherwise ASHRAE 55 Adaptive setpoints horizontally extended
For the comfort standard 7 = IND IMAC C NV, the available ComfMods you can choose are:
0 = Indian Building Code Static setpoints
1 = IMAC C NV Model Adaptive setpoints when applicable, otherwise Indian Building Code Static setpoints
2 = IMAC C NV Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints
3 = IMAC C NV Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended
Enter the Comfort Mode numbers separated by space (
0 or 0.X = Static;
1, 1.X, 2, 3 = Adaptive;
Please refer to the full list of setpoint temperatures at https://htmlpreview.github.io/?https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html
): 0 3
          Are you sure the numbers are correct? [y or [] / n]:

Enter the setpoint accuracy number (any number greater than 0, if omitted will be 10000): 100
          Are you sure the number is correct? [y or [] / n]:

Enter the number for the CAT cooling offset modifier (value will be summed to the ACST, if omitted will be 0):
          Are you sure the number is correct? [y or [] / n]:

Enter the number for the CAT heating offset modifier (value will be summed to the AHST, if omitted will be 0):
          Are you sure the number is correct? [y or [] / n]:

Enter the start of the cooling season in numeric date format dd/mm or the day of the year: 01/05
          Are you sure the number is correct? [y or [] / n]:

Enter the end of the cooling season in numeric date format dd/mm or the day of the year: 01/10
          Are you sure the number is correct? [y or [] / n]:

Enter the HVAC Mode numbers separated by space (
0 = Fully Air-conditioned;
1 = Naturally ventilated;
2 = Mixed Mode;
): 2
          Are you sure the numbers are correct? [y or [] / n]:

Enter the Ventilation Control numbers separated by space (
If HVACmode = 1:
   0 = Ventilates above neutral temperature;
   1 = Ventilates above upper comfort limit;
If HVACmode = 2:
   0 = Ventilates above neutral temperature and fully opens doors and windows;
   1 = Ventilates above lower comfort limit and fully opens doors and windows;
   2 = Ventilates above neutral temperature and opens doors and windows based on the customised venting opening factor;
   3 = Ventilates above lower comfort limit and opens doors and windows based on the customised venting opening factor;
): 2 3
          Are you sure the numbers are correct? [y or [] / n]:
Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): 15
          Are you sure the number is correct? [y or [] / n]:
Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): 1
          Are you sure the number is correct? [y or [] / n]:
Enter the multiplier number for Ventilation Opening Factor (any number between 0 and 1): 0.2
          Are you sure the number is correct? [y or [] / n]:

Enter the VSToffset numbers separated by space (if omitted, will be 0):
          Are you sure the numbers are correct? [y or [] / n]:

Enter the MinOToffset numbers separated by space (if omitted, will be 50):
          Are you sure the numbers are correct? [y or [] / n]:

Enter the MaxWindSpeed numbers separated by space (if omitted, will be 50):
          Are you sure the numbers are correct? [y or [] / n]:

Enter the ASTtol value from (if omitted, will be 0.1):
          Are you sure the numbers are correct? [y or [] / n]:
Enter the ASTtol value to (if omitted, will be 0.1):
          Are you sure the numbers are correct? [y or [] / n]:
Enter the ASTtol value steps (if omitted, will be 0.1):
          Are you sure the number is correct? [y or [] / n]:
```

Afterwards, ACCIS will let us know which the output IDFs are going to be, the total number of them, and the estimated size of the results of their simulations, and will ask for our confirmation to proceed:

```
The list of output IDFs is going to be:
TestModel[CS_INT EN16798[CA_2[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_2[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_2[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_2[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_3[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_3[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_3[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_3[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT ASHRAE55[CA_90[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT ASHRAE55[CA_90[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT ASHRAE55[CA_90[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT ASHRAE55[CA_90[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_85[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_85[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_85[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_85[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_90[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_90[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_90[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_90[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
And the total number of output IDFs is going to be 20
The estimated size of the results of each simulation of the output IDFs, from their outputs (without simulating them):
    TestModel (20 output IDFs): 31.2 MB (ESO 16.4 MB, CSV 12.2 MB, MTR and Meter.csv 2.0 MB, other files 630.0 kB); 110 values every hour, 110 every run period
With each EPW, the 20 output IDFs: 625.0 MB (571.7 MB after accim.run.remove_files(), which keeps the ESO and CSV files).
The outputs decide it (output_type, output_frequencies, outputs_dataframe); accim.run.estimate_results_size(simulate=True) measures it in a simulation of an output IDF.
Do you still want to run ACCIS? [y/n]: y
```

If we entered `n`, the whole process would shut down. Otherwise, if we entered ‘y’, the generation of output IDF files would start, and ACCIS would print on screen each output IDF name as it generates it. The estimated size helps to choose the outputs before generating the output IDFs: with 6 EPWs, these 20 output IDFs would write about 3.7 GB, and with `output_type='simplified'` (the operative temperature and the coil rates of each zone, 6 values every hour) 2.7 MB per simulation, about 320 MB; it is also in the attribute `results_size` of `AddAccis` (a row for each input IDF, in MB). It is estimated from the outputs of each model, without simulating it (within about 10 % for results of more than 5 MB in the simulations of its calibration), and section 4.6 explains how to measure it with a simulation. As you can see, we are going to use the EN16798-1, ASHRAE 55 and IMAC Commercial for naturally ventilated buildings, categories 2 and 3 for EN16798, 90% acceptability levels for ASHRAE 55, 85 and 90% acceptability levels for IMAC C NV, all with comfort_mode 0 (with static setpoint temperatures) and 3 (with adaptive setpoint temperatures when the model is applicable, otherwise horizontally extending the adaptive setpoint temperatures), Mixed Mode, and we just went ahead with the remaining default values.

```
Generating the following output IDF files:
TestModel[CS_INT EN16798[CA_2[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_2[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_2[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_2[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_3[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_3[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_3[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT EN16798[CA_3[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT ASHRAE55[CA_90[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT ASHRAE55[CA_90[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT ASHRAE55[CA_90[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_INT ASHRAE55[CA_90[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_85[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_85[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_85[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_85[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_90[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_90[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_90[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel[CS_IND IMAC C NV[CA_90[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf

=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================
```

Afterwards, you just need to run the simulation. Once you have run the simulations you need, you’ll get the files you usually get when you run any simulation, including the hourly results on a CSV file.

## 4.5 Renaming epw files for later data analysis

You can see a Jupyter Notebook in the How-to Guides section of this documentation: {doc}`jupyter_notebooks/rename_epw_files/using_rename_epw_files`.

To run it on your computer, copy the folder `jupyter_notebooks/rename_epw_files` of the sample files to a working folder (see {ref}`running-example-notebooks`).

`rename_epw_files` takes the country and city from the coordinates of each EPW file, which needs an internet connection (it uses the package `geopy`, installed with accim), unless `rename_city_dict` and `country_to_city_dict` give them.

(running-simulations)=
## 4.6 Running simulations

You can see a Jupyter Notebook in the How-to Guides section of this documentation: {doc}`jupyter_notebooks/runEp/using_runEp`.

To run it on your computer, copy the folder `jupyter_notebooks/runEp` of the sample files to a working folder (see {ref}`running-example-notebooks`).

This script has been created by eppy’s development team (https://eppy.readthedocs.io/en/latest/runningeplus.html, specifically from section ‘Running in parallel processes using Generators’), however I did some changes. Anyway, you probably should check out eppy package, since it’s absolutely awesome.

By using this script, the EnergyPlus version used to simulate the IDFs will be the IDF’s version. Therefore, if your IDF is in version 25.1, but you don’t have EnergyPlus 25.1 installed, you’ll get an error.

The main difference is that this one allows to run simulations with several EPW files. It takes all EPW files and IDF files located in the working folder, and runs them. So for example, say you have 2 no. IDFs (1.idf and 2.idf) and 2 no. EPW files (a.epw and b.epw). Then, this script will run the following simulations: 1[a; 1[b; 2[a; 2[b, and the output files will be named after them (for instance, `1[a.csv` for the hourly results). The character ‘[’ has been used as separator in order to not to be in conflict with other programs, and the class `Table` (section 4.7) uses it to read the results.

So, how to use it? Say you have already run `AddAccis()`, and therefore you have a folder with the output IDFs and the EPW files. Then you can run the simulations with `run_ep()` (`runEp()` in accim 0.x, whose name and arguments still work):

```python
from accim.run import run
run.run_ep(
    only_accim_idfs=True,       # True to run only the IDFs generated by accim (with '[' in the name), False to run all
    confirm=True,               # True to run without asking for confirmation
    processes=2,                # number of simulations run at the same time
    energyplus_version='auto',  # EnergyPlus version of the IDFs, or 'auto' to read it from them
    backend='ems',              # 'ems' (the EMS of EnergyPlus) or 'api' (the Python API of EnergyPlus, section 4.9)
)
```

If you omit `only_accim_idfs`, `confirm` or `energyplus_version`, `run_ep()` asks for them in the prompt. Before running, it lists the IDFs, the EPWs and the simulations, and their number, and asks for your confirmation (unless `confirm=True`), because you might start thousands of simulations by mistake. `energyplus_version` is the version of the IDFs, from ‘9.1’ to ‘26.2’, or ‘auto’ to read it from the IDFs, which must then be of the same version; `processes` is 2 by default.

Thousands of simulations can also fill the disk. Before running them, `estimate_results_size()` gives the size of their results, for the IDFs and EPWs of the working folder (or those of its arguments `idfs` and `epws`):

```python
from accim.run import estimate_results_size
sizes = estimate_results_size(
    simulate=False,        # False to estimate it from the outputs of the IDFs; True to measure it in a simulation
    only_accim_idfs=True,  # as in run_ep(): True for the IDFs generated by accim, False for all
)
```

```
The size of the results of run_ep, estimated from the outputs of the IDFs, without simulating them (simulate=True measures them in a simulation):
    TestModel[CS_IND IMAC C NV[CA_85[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf and 19 other IDFs with the same outputs: 31.2 MB (ESO 16.4 MB, CSV 12.2 MB, MTR and Meter.csv 2.0 MB, other files 630.0 kB) each simulation; 110 values every hour, 110 every run period
20 IDFs and 6 EPWs: 120 simulations, 3.7 GB (3.4 GB after accim.run.remove_files(), which keeps the ESO and CSV files); 1.9 GB of memory to read the values of their CSV files (8 bytes each).
```

Without simulation (the default, in a few seconds), the size of the files of each simulation is estimated from the outputs of its IDF: the values that its `Output:Variable` and `Output:Meter` objects report (each key of each variable, counted from the objects of the model when the key is `*`, at each frequency), the times they are reported in its run periods (and sizing periods, if it simulates them), and the bytes of each value in each file, measured with EnergyPlus 25.1. In 16 simulations of output IDFs of accim and of example files of EnergyPlus, it was within 10 % of the files for results of more than 5 MB (within 45 % for smaller ones, where the other files, estimated more roughly, are a larger part); it notes what it cannot count, such as the keys of variables it does not know (counted as one) or the EDD file of `debug_ems=True`. With `simulate=True`, it runs a simulation of the IDF with the first EPW, as `run_ep()` runs it, in a temporary folder, and measures its files: it takes as long as that simulation, but gives the size of the results of that IDF and EPW (other EPWs give about the same). In both cases, the IDFs whose output objects are the same (all the output IDFs of a model of `AddAccis`, which differ in the arguments of the ACCIS) are taken as a group, and only one of them is read or simulated. `estimate_results_size()` returns a table with a row for each IDF: the number of its simulations, how the size was found (`'estimate'` or `'simulation'`), the size in MB of each file of each simulation (`eso_mb`, `csv_mb`, `mtr_mb`, `meter_csv_mb`, `sql_mb`, `other_mb`) and of the whole simulation (`simulation_mb`), that of the files that `remove_files()` keeps (`kept_mb`), the memory to read the values of its CSV file (`csv_memory_mb`, 8 bytes each, as the estimate of the hourly tables of the parametric module) and the size of all its simulations (`total_mb`, `total_kept_mb`). `AddAccis` prints the same estimate before writing the output IDFs (section 4.4), so that you can choose other outputs.

Afterwards, you’ll see the calculations progress, and you’ll get the usual simulation files of each simulation: `.audit`, `.eio`, `.err`, `.eso`, `.csv`, `Table.csv`, `Table.htm` and so on, all of them named `IDF name[EPW name`. You might need to keep these in order to debug some error, or any other reason, but if you only need the CSV files with the hourly results, you can run the `remove_files()` function (`removefiles()` in accim 0.x):

```python
run.remove_files()
```

`remove_files()` deletes the simulation files of the working folder, that is, the files with ‘[’ in the name, except the `.py`, `.idf`, `.epw`, `.csv` and `.eso` files, and it also deletes the `Table.csv`, `Meter.csv` and `Zsz.csv` files of the simulations. It does not delete subfolders or files without ‘[’ in the name, such as a Jupyter notebook; files of other programs whose names contain ‘[’ would be deleted.

## 4.7 Functions and methods for data analysis; making figures and tables

You can see a Jupyter Notebook in the How-to Guides section of this documentation: {doc}`jupyter_notebooks/Table/using_Table`.

To run it on your computer, copy the folder `jupyter_notebooks/Table` of the sample files to a working folder (see {ref}`running-example-notebooks`).

(hours-within-setpoints)=
### 4.7.1 Hours within the setpoints

The ACCIS reports EMS outputs that count hours in each occupied zone: in each timestep, their value is the length of the timestep (in hours) or 0, so their sums are hours. With `add_building_averages=True`, the outputs `<output>_Building_Average` are their averages over the zones.

| Output | Counts the timesteps... |
| --- | --- |
| `Comfortable Hours_No Applicability_<zone>` | with the operative temperature within the setpoints without tolerance (the comfort limits of the comfort model) |
| `Occupied Comfortable Hours_No Applicability_<zone>` | the same, while the zone is occupied |
| `Occupied Discomfortable Hours_No Applicability_<zone>` | out of the setpoints without tolerance, while the zone is occupied |
| `Occupied Hours_<zone>` | while the zone is occupied |
| `Comfortable Hours_Applicability_<zone>` | within the setpoints without tolerance, with the running mean outdoor temperature within the applicability limits of the comfort model |
| `Discomfortable Applicable Hot Hours_<zone>`, `Discomfortable Applicable Cold Hours_<zone>` | above the cooling setpoint or below the heating setpoint without tolerance, within the applicability limits |
| `Discomfortable Non Applicable Hot Hours_<zone>`, `Discomfortable Non Applicable Cold Hours_<zone>` | with the running mean outdoor temperature above or below the applicability limits |
| `Ventilation Hours_<zone>` (mixed mode) | in which accim ventilates the zone while it is occupied |

In each timestep, one of the five counters with applicability is the length of the timestep, and the occupied comfortable and discomfortable hours add up to the occupied hours (since accim 1.0.0, which corrected these counters; see section 9.3).

The percentage of the occupied hours within the setpoints shows whether the HVAC system or the natural ventilation keeps the setpoints, so that the simulations in which it does not (an undersized system, natural ventilation alone in a hot week...) can be left out of the analysis. The module `accim.data.postprocessing.setpoint_hours` computes it for each zone (the ratio of the sums of `Occupied Comfortable Hours_No Applicability_<zone>` and `Occupied Hours_<zone>`) and for the building (the ratio of their sums over all the zones), and filters the simulations by it:

```python
from accim.data.postprocessing.setpoint_hours import filter_by_hours_within_setpoints, hours_within_setpoints

# The CSV files of the simulations of run_ep in the working folder (or a CSV file, or a list of them)
summary = hours_within_setpoints('.')
print(summary[['Source', 'Occupied Hours Within Setpoints_Building [%]']])

# The simulations with at least 90 % of the occupied hours of the building within the setpoints
kept = filter_by_hours_within_setpoints(summary, min_percentage=90)
# ... of each zone: zones='all'; or of some zones: zones=['Block1_Zone1']

# Table with these simulations only (see the notebook of Table for its arguments)
from accim.data.postprocessing.main import Table
table = Table(datasets=list(kept['Source']), source_frequency='hourly', frequency='runperiod',
              frequency_agg_func='sum', standard_outputs=True, level=['building'], level_agg_func=['sum'],
              level_excluded_zones=[], idf_path='TestModel.idf')
```

- `hours_within_setpoints` returns one row for each CSV file: `Source` (the file), the sums of the two outputs of each zone, and the percentages, in the columns `Occupied Hours Within Setpoints_<zone> [%]` and `Occupied Hours Within Setpoints_Building [%]`. A zone without occupied hours has no percentage.
- The CSV files need these outputs (`output_type` 'standard', 'detailed' or 'custom' of `AddAccis`), at any frequency: their sums are the same. If the model simulates its sizing periods, their hours count too.
- It also takes a table with one row for each simulation and the sums of these outputs, such as the results of the parametric module (see {doc}`parametric_and_optimisation`, step 3), or the table of `Table` (`Table.df`, whose percentages are those of each row: a month, a day...), and returns it with the percentages.
- `filter_by_hours_within_setpoints` takes the same results, or the table of `hours_within_setpoints`, and keeps the rows that reach `min_percentage` in the building (`zones='building'`, the default), in every occupied zone (`zones='all'`) or in the zones of a list.

(saving-sessions)=
### 4.7.2 Saving the tables to resume the session

The CSV files of the simulations stay in the working folder, but the tables of `Table` are lost when the script ends or the kernel of the notebook restarts, and making them again reads all the CSV files, which takes a while with many hourly files. Since accim 1.0.0, they can be saved in files, to resume the session later without making them again:

```python
from accim.data.postprocessing.main import Table
from accim.utils import load_session, save_session

# One table: case_study_runperiod.pkl, which Table.load reads, and case_study_runperiod.json, to read it
dataset_runperiod.save('case_study_runperiod')
dataset_runperiod = Table.load('case_study_runperiod.pkl')

# Several objects at once (tables, lists of files, arguments...): case_study.pkl and case_study.json
save_session('case_study', dataset_runperiod=dataset_runperiod, dataset_hourly=dataset_hourly, csvs=csvs)
session = load_session('case_study.pkl')  # a dictionary: {'dataset_runperiod': <Table>, ..., 'csvs': [...]}
dataset_hourly = session['dataset_hourly']
# globals().update(session) gives them all back as variables
```

- The pickle file (`.pkl`) has the objects as they were: the methods of a table (`format_table`, `wrangled_table`, the figures...) work after loading it as before saving it. Open only the pickle files that you or someone you trust saved, since pickle files can run code when they are read; they also need a version of pandas that can read the objects of the version that saved them. The pickle files of hourly tables of many simulations are large, as their CSV files.
- The JSON file (`.json`), with the same name, is a copy to read with any text editor or with other programs; accim does not read it back. It has the version of accim, the date and the working folder, and, for each table, its arguments (`arguments`), its frequency, occupied zones and blocks, the variables whose values differ between the simulations and their values (`suggested_vars_dict`), the columns given by `format_table` (`type_of_table`, `custom_cols`, `indexcols`, `val_cols`), its rows (`df`, as it is after `format_table`) and the tables of `wrangled_table` (the names of their columns of several levels joined with `[`). Each of these tables, and each DataFrame of a session, shows its number of rows and the values of its first 1000 rows, as `{"number_of_rows": ..., "rows_shown": ..., "data": {column: [values]}}`: hourly tables of many simulations have hundreds of thousands of rows, which would make the JSON file large and slow to write. The argument `json_max_rows` of `save` and `save_session` changes this number (`None` shows all the rows); the pickle file always has all of them. The other objects of a session are written with their type: the lists, dictionaries, texts and numbers as they are (NaN as `null`, and infinity as `"Infinity"`), and other objects as their representation in Python.
- The parametric module saves its results in the same way: each run writes them in CSV, Excel, pickle and JSON files, which `load_outputs_parametric` and `load_outputs_optimisation` read ({doc}`parametric_and_optimisation`).
- The graphical user interface also saves its sessions and its tables in these files ({ref}`graphical-user-interface`).

The notebook of the research paper case study (How-to Guides) saves and resumes its tables in this way.

## 4.8 Setpoints based on the predicted mean vote (PMV) and the adaptive PMV (aPMV)

Besides adaptive setpoint temperatures, accim can apply setpoints based on the predicted mean vote (PMV) of Fanger and on indices derived from it. The adaptive predicted mean vote (aPMV) corrects the PMV for the adaptation of the occupants: aPMV = PMV / (1 + λ·PMV), where λ is the adaptive coefficient, with one value for the cooling season and another for the heating season. The thermostats keep the aPMV of each zone between the heating and cooling setpoints, instead of keeping the operative temperature between two temperatures.

The function `apply_apmv_setpoints()` of the module `accim.sim.apmv` (`accim.sim.apmv_setpoints` in accim 0.x, whose argument names, such as `adap_coeff_cooling` or `pmv_cooling_sp`, still work; see {doc}`9_migration_guide`) adds this control, with Energy Management System programs, to an eppy or besos IDF object. Each zone needs an HVAC system; `apply_apmv_setpoints()` adds the thermal comfort thermostats that control it, and `add_vrf_system()` adds a VRF system to the zones if the model has none:

```python
from accim.sim.accis import load_idf
from accim.sim.apmv import add_vrf_system, apply_apmv_setpoints, set_pmv_input_parameters

building = load_idf('TestModel.idf')    # an IDF object of eppy
add_vrf_system(building)
apply_apmv_setpoints(
    building,
    output_frequencies=['hourly'],
    adaptive_coefficient_cooling=0.293,     # λ of the cooling season
    adaptive_coefficient_heating=-0.293,    # λ of the heating season
    pmv_cooling_setpoint=0.5,               # aPMV setpoint for cooling
    pmv_heating_setpoint=-0.5,              # aPMV setpoint for heating
    cooling_season_start='01/05',           # dd/mm, or the day of the year
    cooling_season_end='01/10',
)
set_pmv_input_parameters(building, air_velocity=0.1, work_efficiency=0.0)
building.saveas('TestModel_aPMV.idf')
```

- By default, the setpoints are 0.5 for cooling and −0.5 for heating, λ is 0.293 in the cooling season and −0.293 in the heating season, and the cooling season goes from day 121 (1 May) to day 274 (1 October), which is not included, as in `AddAccis()`. Give them explicitly, as above, so that the results do not depend on the defaults: up to accim 0.7.7, the default setpoints were inverted and the cooling season ended on 29 July.
- The coefficients, setpoints and tolerances take one value for the whole model, or a dictionary with a value for each occupied zone: `get_available_target_names(building)` lists the valid names, and `get_input_template_dictionary(building)` returns a template of the dictionary. The name of a zone is the zone name if its People object is assigned to a zone without Space objects, and `<Space Name> <People Name>` otherwise (the space of a zone without Space objects has the name of the zone), except in the zones described below.
- A zone whose occupants EnergyPlus splits among several spaces (People assigned to a zone of several spaces, or to a list that covers several spaces of the zone) or that has several People objects is controlled as a whole: its name is the zone name, it is occupied while any of its occupants is, and its PMV is the average PMV of its occupants, weighted by their number. If some surfaces of a zone with Space objects have no Space Name, EnergyPlus creates a space named `<Zone Name>-Remainder` for them, which takes part of the occupants assigned to the zone; accim warns about it.
- The tolerances widen or narrow the setpoints: by default, the heating setpoint is raised by 0.1 and the cooling setpoint is lowered by 0.1, in both seasons.
- The PMV depends on the inputs of the People objects (activity level, clothing insulation, air velocity and work efficiency), which do not affect temperature setpoints but do affect aPMV setpoints. `set_pmv_input_parameters()` sets them for all the People objects, or for each zone with dictionaries. In models of EnergyPlus 26.2 with `People:Instance` objects, these inputs are in the `People:Instance` objects, and the Fanger model in their `People:Definition` objects.
- The cooling season is given by dates: for a location in the southern hemisphere, swap them.
- The aPMV of each zone (the output `aPMV_<zone>`) and the hours within the setpoints are calculated at the beginning of each timestep, from the last PMV that EnergyPlus has calculated, that of the previous timestep.

Since accim 1.2.0, `apply_pmv_setpoints()` applies setpoints based on the PMV itself, such as those of the categories of ISO 7730 and EN 16798-1 (−0.2 and 0.2, −0.5 and 0.5, −0.7 and 0.7). It takes the arguments of `apply_apmv_setpoints()` except the adaptive coefficients, and its setpoints are those of `apply_apmv_setpoints()` with adaptive coefficients of 0, with EMS objects named after the PMV: the programs `apply_PMV_<zone>` and `count_PMV_comfort_hours_<zone>`, and the outputs `PMV_<zone>` (the PMV of the zone), `PMV Heating Setpoint_<zone>`, `PMV Cooling Setpoint_<zone>`... and the hours within the setpoints.

```python
from accim.sim.apmv import apply_pmv_setpoints

apply_pmv_setpoints(building, pmv_cooling_setpoint=0.5, pmv_heating_setpoint=-0.5)   # category II
```

Both functions call `apply_pmv_index_setpoints()` of the module `accim.sim.pmv_index`, with the index `'apmv'` or `'pmv'` and the parameters of the index in `index_parameters` (for instance, `{'adaptive_coefficient_cooling': 0.293}`). The indices share the thermostats and the EMS programs; only the lines that convert the setpoints of the index into the PMV setpoints of the thermostats (the inverse of the index) and those that calculate the index of each zone depend on the index (`PMV_INDICES`). A model has the setpoints of one index only: the functions stop with a `ValueError` if it has those of another one.

You can see a Jupyter Notebook in the How-to Guides section of this documentation: {doc}`jupyter_notebooks/example_apmv_setpoints_paper/using_apmv_setpoints`. Parametric studies and optimisations of these setpoints are explained in {doc}`parametric_and_optimisation`.

(python-api-backend)=
## 4.9 Running the simulations with the Python API of EnergyPlus

The output IDFs of accim control the setpoints with Energy Management System (EMS) programs, which EnergyPlus runs with its EMS. Since accim 1.0.0, they can also run in Python, through the Python API of EnergyPlus (the package `pyenergyplus` of each installation, EnergyPlus 24.2 or later): EnergyPlus runs the model without the EMS programs and actuators, and accim runs the programs in the callbacks of the API with the rules of the EMS (the order of the operators, the values Null and uninitialised, the errors, the variables reset at each new environment...). The results are the same as with the EMS: the tests of accim run the same model with both backends and compare their CSV files, which are identical. With the thermal comfort thermostats of the setpoints based on the PMV (section 4.8), the setpoints and the variables of the programs are identical, but the results of EnergyPlus differ by rounding errors (less than 1e-9 °C in the zone temperatures of the tests), as they did with accim 1.1.0.

To run the simulations of a folder with the API, use the argument `backend` of `run_ep()`:

```python
from accim.run import run
results = run.run_ep(only_accim_idfs=True, confirm=True, processes=4, backend='api')
[r.success for r in results]
```

Each simulation runs in its own process (a Python process can only load the API of one EnergyPlus version), and the output files have the same names as with the EMS. `run_simulation()` runs a single model, which it reads with eppy (so, in a Python session, it runs the models of one EnergyPlus version), and its hooks can read and change the variables of the programs during the simulation, for instance to test other controls with Python code:

```python
from accim.sim.energyplus_api import run_simulation

def raise_cooling_setpoint(controller, calling_point):
    # Called at each calling point, after the EMS programs and before the actuators are set
    if calling_point == 'BEGINTIMESTEPBEFOREPREDICTOR':
        controller.set('ACST', controller.get('ACST') + 0.5)

result = run_simulation('TestModel[CS_INT EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf',
                        'Seville.epw', after_programs=[raise_cooling_setpoint])
```

The variables are those of the EMS programs (`controller.get(name, program)` reads the local variables of a program). The actuators are set as the EMS sets them: the integer ones (for instance, the status of a window shading control) to the number rounded down, and the logical ones to true only for 1, while the Python API itself would round the integers and take as true the numbers within 1e-5 of 1. The messages of `@WarnEP`, `@SevereWarnEP` and `@FatalHaltEP` go to the error file of EnergyPlus, and `@FatalHaltEP` stops the simulation. The API backend supports the EMS objects that accim writes, and most of those of other models; it does not support `EnergyManagementSystem:TrendVariable`, `EnergyManagementSystem:CurveOrTableIndexVariable`, `EnergyManagementSystem:ConstructionIndexVariable`, the external interface, Python plugins, the calling point `UserDefinedComponentModel` and the psychrometric and curve functions of the EMS, and it raises an error for them: run those models with the EMS backend.



(graphical-user-interface)=
## 4.10 Graphical user interface

Since accim 1.0.0, a graphical user interface (GUI), in English, does the main steps without writing Python: add the ACCIS or the aPMV setpoints to the IDF files of a folder, rename the EPW files, run the simulations, measure the occupied hours within the setpoints, make tables and figures of the results, and run a basic parametric study; and it saves the session, to resume it later. Open it with the command `accim-gui`, which is installed with accim, or with:

```
python -m accim.gui
```

It uses tkinter, which comes with Python on Windows and macOS (on Linux, it may need a package of the distribution, such as `python3-tk`). The seven tabs share a working folder:

1. **Add the ACCIS**: the input IDFs of the folder (all, or those selected), and the arguments of `AddAccis()` (sections 4.2 and 4.4): the script type (with the availability schedule, EER and COP of the VRF systems), the setpoint type, the outputs (and `debug_ems`), the comfort standards (with the categories and comfort modes of each one, the offsets of the category and the accuracy of the setpoints), the arguments of mixed mode, those of the custom model (comfort standard 99), the options of the existing HVAC systems (`existing_hvac_*`, section 4.1.1, with `ex_ac` and `ex_mm`; the availability schedule can be empty, `On 24/7` or the name of a schedule of the model), the tolerances, and the arguments of each zone (`zone_arguments`, {ref}`zone-arguments`), right below the comfort models (the button *Other values for some zones...* scrolls to them): *Find the occupied zones* lists the zones of the first selected IDF, and each zone of the table gets its comfort standard, category, comfort mode and, in mixed mode, HVAC mode and ventilation control, chosen in lists (those of the categories and comfort modes are those of the comfort standard of the zone), and other arguments as pairs `name=value`, such as `setpoint_tolerance=0.25`; the empty fields, and the other zones, take the arguments of each output IDF. The fields that do not apply to the script type, the setpoint type or the comfort standards are disabled. The buttons stay at the bottom of the tab: *Preview* shows the number of output IDFs and the arguments of `AddAccis()` in the log, and checks that each zone of the table has setpoints in all the output IDFs; *EMS code of the setpoints...* shows in a window the EMS code with which the ACCIS calculates the setpoints of the comfort standards, categories and comfort modes of the form and of the zones (`get_setpoint_ems_code()`, section 4.3), which can be saved in a text file; *Add the ACCIS* prepares the models, shows the number of output IDFs and the estimated size of the results of their simulations (section 4.4), and asks whether to write them in the folder.
2. **aPMV setpoints**: `apply_apmv_setpoints()` (section 4.8) on an input IDF of the folder, with the setpoints of the form in all the zones except those of the table of the zones, whose setpoints (the adaptive coefficients and the aPMV setpoints in fields, and the tolerances as pairs `name=value`) replace them, optionally with a VRF system in each zone, the occupants always present and other inputs of the PMV of the occupants; the new IDF is saved in the folder as `<input>_aPMV.idf`, or with another name.
3. **Rename the EPWs**: `rename_epw_files()` (section 4.5) on the selected EPWs of the folder; the cities and countries that OpenStreetMap does not give can be entered in the form.
4. **Run the simulations**: `run_ep()` (section 4.6) with the IDFs and EPWs of the folder, with the EMS or the Python API backend (section 4.9), `remove_files()`, and `estimate_results_size()` (section 4.6), which estimates the size of the results from the outputs of the IDFs in a few seconds, or measures it in a simulation.
5. **Hours within the setpoints**: the percentage of the occupied hours within the setpoints of each simulation, in each zone and in the building, from the CSV files of the folder ({ref}`hours-within-setpoints`), the simulations that reach a minimum percentage (in the building, in every zone, or in some zones), and a CSV file with the table.
6. **Table and figures**: `Table` (section 4.7) of the CSV files of the simulations of the folder, with its frequency, the totals of the blocks and of the building and the columns of the table, which can be exported to a CSV file; and its scatter plots and time plots, whose subplots group the simulations by the variables whose values differ between them (the comfort standard, the category, the EPW...), saved as PNG files in the folder. *Save the table...* saves the table in a pickle file and a JSON file with the same name ({ref}`saving-sessions`), and *Open a table...* opens it again without the CSV files, as well as the tables saved in Python with `Table.save`, to make their figures.
7. **Parametric study**: a basic `ParametricSimulation` ({doc}`parametric_and_optimisation`) of the predefined or the custom model of accim, on an input IDF of the folder and the selected EPWs (with the existing HVAC systems, `ex_ac`, and their options): the full set of the options of the parameters, or a Latin hypercube sample of their ranges (custom model); the results are the sums of some meters over the run period of each simulation.

Each task runs in the background, one at a time, and what accim prints appears in the log at the bottom of the window (EnergyPlus writes its own messages in the console). The GUI does not ask anything in the prompt, so it gives all the arguments, and it checks them before running (for instance, that the lists of numbers are numbers); it only answers the questions of `rename_epw_files()` about amending or excluding EPWs (none), and those of the figures about renaming the rows and columns of the subplots (no), and it asks in a dialog the confirmation of `AddAccis()` before writing the output IDFs. It does not cover the `custom` output type, `modify_accis()`, the other figures of `Table` and the reshaping of its tables, nor the aPMV setpoints, outputs, objectives, optimisations and plots of the parametric module: use Python for them.

The menu **Session** saves the session (*Save the session...*): the working folder, the values of the forms of all the tabs, and the results of the tabs 5, 6 and 7 (the hours within the setpoints, the table and the results of the parametric study), in a pickle file and a JSON file with the same name, which shows these values and results ({ref}`saving-sessions`). *Open a session...* restores them, and lists in the log the files of the forms that are no longer in the working folder. accim reads the IDFs with eppy, which keeps the IDD of the first EnergyPlus version that it reads while the GUI is open: to work with IDFs of another version, save the session, close the GUI, open it again and open the session.
