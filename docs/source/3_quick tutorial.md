# 3. Quick tutorial

## 3.1 Implementing adaptive setpoint temperatures

This is a very brief explanation of the usage. Therefore, if you don’t get the results you expected or get some error, I would recommend reading the ‘Detailed use’ section at the documentation in the link below.

accim will take as input IDF files those located at the same path as the script. You only need to run the following code:

### 3.1.1 Short version

```python
from accim.sim import AddAccis
AddAccis()
```

Once you run this code, you will be asked to enter some information at the terminal or python console to generate the output IDF files.

### 3.1.2 Long version

```python
from accim.sim import AddAccis
AddAccis(
     script_type=str, # script_type: 'vrf_mm', 'vrf_ac', 'ex_mm', 'ex_ac'. For instance: script_type='vrf_ac',
     supply_air_temp_method=str, # supply_air_temp_method: 'supply air temperature', 'temperature difference'. For instance: supply_air_temp_method='supply air temperature',
     output_keep_existing=bool, # output_keep_existing: True or False. For instance: output_keep_existing=False,
     output_type=str, # output_type: 'simplified', 'standard', 'detailed' or 'custom'. For instance: output_type='standard',
     output_freqs=list, # output_freqs: ['timestep', 'hourly', 'daily', 'monthly', 'runperiod']. For instance: output_freqs=['hourly', 'runperiod'],
     output_gen_dataframe=bool, # output_gen_dataframe: True or False. For instance: output_gen_dataframe=False,
     output_take_dataframe=..., # a pandas DataFrame
     energyplus_version=str, # energyplus_version: '9.1' to '25.1', or 'auto'. For instance: energyplus_version='23.1',
     temp_control=str, # temp_control: 'temperature' or 'temp', or 'pmv'. For instance: temp_control='temp',
     comfort_standard=list, # it is the Comfort Standard. Can be any integer from 0 to 22, or 99. For instance: comfort_standard=[0, 1, 2, 3],
     custom_ast_acst_aul=float, # it is the value for the Adaptive Cooling Setpoint Temperature applicability upper limit, only used for comfort_standard=[99]
     custom_ast_acst_all=float, # it is the value for the Adaptive Cooling Setpoint Temperature applicability lower limit, only used for comfort_standard=[99]
     custom_ast_ahst_aul=float, # it is the value for the Adaptive Heating Setpoint Temperature applicability upper limit, only used for comfort_standard=[99]
     custom_ast_ahst_all=float, # it is the value for the Adaptive Heating Setpoint Temperature applicability lower limit, only used for comfort_standard=[99]
     custom_ast_m=float, # it is the value for the slope or gradient of the custom adaptive model, only used for comfort_standard=[99]
     custom_ast_n=float, # it is the value for the y-intercept of the custom adaptive model, only used for comfort_standard=[99]
     custom_ast_acst_offset=float, # it is the value for the upper limit offset from neutral, only used for comfort_standard=[99]
     custom_ast_ahst_offset=float, # it is the value for the lower limit offset from neutral, only used for comfort_standard=[99]
     category=list, # it is the Category. Can be 1, 2, 3, 80, 85 or 90. For instance: category=[3, 80],
     category_cool_offset=float, # it is an offset override for the category argument; the float is summed to the cooling offset,
     category_heat_offset=float, # it is an offset override for the category argument; the float is summed to the heating offset,
     comfort_mode=list, # it is Comfort Mode. Can be 0, 1, 2 or 3. For instance: comfort_mode=[0, 3],
     setpoint_accuracy=float, # it is the accuracy of the setpoint temperatures
     cooling_season_start=..., # dd/mm date in string format or integer to represent the day of the year; it is the start date for the cooling season
     cooling_season_end=..., # dd/mm date in string format or integer to represent the day of the year; it is the end date for the cooling season
     hvac_mode=list, # it is the HVAC mode. 0 for Full AC, 1 for NV and 2 for MM. For instance: hvac_mode=[0, 2],
     vent_control=list, # it is the Ventilation Control. Can be 0 or 1. For instance: vent_control=[0, 1],
     vof_max_temp_diff=float, # When the difference of operative and outdoor temperature exceeds vof_max_temp_diff, windows will be opened the fraction of vof_multiplier. For instance: vof_max_temp_diff=20,
     vof_min_temp_diff=float, # When the difference of operative and outdoor temperature is smaller than vof_min_temp_diff, windows will be fully opened. Between min and max, windows will be linearly opened. For instance: vof_min_temp_diff=1,
     vof_multiplier=float, # Fraction of window to be opened when temperature difference exceeds vof_max_temp_diff. For instance: vof_multiplier=0.2,
     vent_setpoint_offset=list, # it is the offset for the ventilation setpoint. Can be any number, float or int. For instance: vent_setpoint_offset=[-1.5, -1, 0, 1, 1.5],
     min_outdoor_temp_offset=list, # it is the offset for the minimum outdoor temperature to ventilate. Can be any positive number, float or int. For instance: min_outdoor_temp_offset=[0.5, 1, 2],
     max_wind_speed=list, # it is the maximum wind speed allowed for ventilation. Can be any positive number, float or int. For instance: max_wind_speed=[2.5, 5, 10],
     ast_tol_start=float, # it is the start of the tolerance sequence. For instance: ast_tol_start=0,
     ast_tol_end=float, # it is the end of the tolerance sequence. For instance: ast_tol_end=2,
     ast_tol_steps=float, # these are the steps of the tolerance sequence. For instance: ast_tol_steps=0.25,
     name_suffix=str, # name_suffix: some text you might want to add at the end of the output IDF file name. For instance: name_suffix='whatever',
     verbose=bool, # verbose: True to print all process in screen, False to not to print it. Default is True. For instance: verbose=True,
     confirm_generation=bool, # True to confirm automatically the generation of IDFs; if False, you'll be asked to confirm in command prompt. Default is False. For instance: confirm_generation=False,
)
```

## 3.2 Other uses

Although the main use of accim is the implementation of adaptive setpoint temperatures, there are some functions, classes and methods that allow to roughly automate the whole process consisting of preparation of the epw and idf files, the simulation runs and the data analysis. For further information, please refer to the How-to Guides section in this documentation, which contains some Jupyter Notebooks that can also be found in accim's installation folder.