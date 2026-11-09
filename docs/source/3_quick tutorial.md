# 3. Quick tutorial

## 3.1 Implementing adaptive setpoint temperatures

This is a very brief explanation of the main class of accim, `AddAccis()` (`addAccis()` before accim 1.0.0, whose name and arguments still work; see {doc}`9_migration_guide`). If you don't get the results you expected or get some error, please read {doc}`4_detailed use`, which explains every argument.

By default, accim takes as input the IDF files located in the working folder (the folder where you run Python), except those whose names contain `[` or `_pymod`, which are the files that accim generates. The argument `idfs` takes a list of IDF files instead. accim saves the output IDF files in the working folder; the input IDF files are not modified.

### 3.1.1 Short version

```python
from accim.sim import accis
accis.AddAccis()
```

Once you run this code, you will be asked to enter some information at the terminal or python console to generate the output IDF files.

### 3.1.2 Longer version

You can also enter the information as arguments, so that accim does not ask for it. Use keyword arguments, as below: the first positional argument of `AddAccis()` is `idfs`. For instance, to generate the IDFs of EN 16798-1 (categories I, II and III) and ASHRAE 55 (80 % and 90 % acceptability), with static and adaptive setpoint temperatures, and with a VRF system in mixed-mode operation:

```python
from accim.sim import accis
accis.AddAccis(
    script_type='vrf_mm',                           # VRF system with mixed-mode operation
    supply_air_temp_input_method='temperature difference',
    keep_existing_outputs=False,                    # remove the outputs of the input IDF
    output_type='standard',
    output_frequencies=['hourly', 'runperiod'],
    energyplus_version='auto',                      # the EnergyPlus version of each IDF
    setpoint_type='temperature',                    # setpoints on the operative temperature
    comfort_standard=[1, 2],                        # EN 16798-1 and ASHRAE 55
    category=[1, 2, 3, 80, 90],                     # categories I-III, 80 % and 90 % acceptability
    comfort_mode=[0, 3],                            # static, and adaptive setpoints
    hvac_mode=[2],                                  # mixed mode
    ventilation_control=[0],                        # ventilate above the neutral temperature
    confirm=True,                                   # generate the IDFs without asking for confirmation
)
```

Each valid combination of values gives an output IDF: categories I, II and III only apply to EN 16798-1, and 80 % and 90 % acceptability to ASHRAE 55, so this call generates 10 IDFs (6 for EN 16798-1 and 4 for ASHRAE 55). Their names give the values used, for instance:

    TestModel[CS_INT EN16798[CA_1[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf

The arguments that are not given take their default values. Section {ref}`setting-up-the-target-idfs` lists all the arguments, with their values and defaults, and explains the names of the output IDFs.

### 3.1.3 Before generating the IDFs: the setpoints and the size of the results

Before generating many output IDFs, it is worth knowing how the ACCIS calculates the setpoints of the comfort models you choose, and how much disk space the results of their simulations will take.

`print_setpoint_ems_code()` prints the EMS code with which the ACCIS calculates the setpoints of a comfort standard, category and comfort mode: which setpoints apply, and what they are out of the applicability limits of the comfort model. It is the code of the output IDFs, with comments that explain the variables. For instance, for EN 16798-1, category II and adaptive setpoints horizontally extended out of the applicability limits:

```python
from accim.utils import print_setpoint_ems_code
print_setpoint_ems_code(comfort_standard=1, category=2, comfort_mode=3)
```

The outputs of the output IDFs decide the size of the results of their simulations. Before writing the output IDFs, `AddAccis()` prints the estimated size of the results of each simulation and of all the output IDFs with each EPW (in the example of section 3.1.2, about 31 MB for each simulation, that is, about 310 MB for the 10 output IDFs with each EPW), so that you can choose other outputs, and keeps it in its attribute `results_size`. Before running the simulations, `estimate_results_size()` estimates it for the IDFs and EPWs of the working folder, or measures it in a simulation (`simulate=True`):

```python
from accim.run import estimate_results_size
estimate_results_size(only_accim_idfs=True)
```

The How-to Guides {doc}`jupyter_notebooks/addAccis/using_addAccis` and {doc}`jupyter_notebooks/runEp/using_runEp` show both, and sections {ref}`setpoint-ems-code` and {ref}`running-simulations` explain them.

## 3.2 Other uses

Although the main use of accim is the implementation of adaptive setpoint temperatures, there are some functions, classes and methods that allow to roughly automate the whole process consisting of preparation of the epw and idf files, the simulation runs and the data analysis:

- setpoints based on the adaptive predicted mean vote (`accim.sim.apmv`): {doc}`jupyter_notebooks/example_apmv_setpoints_paper/using_apmv_setpoints`;
- setpoints based on the PMV with the expectancy factor (ePMV) of Fanger and Toftum (`accim.sim.apmv.apply_epmv_setpoints`): {doc}`jupyter_notebooks/example_epmv_setpoints/using_epmv_setpoints`;
- renaming EPW files for the data analysis (`accim.data.preprocessing.rename_epw_files`): {doc}`jupyter_notebooks/rename_epw_files/using_rename_epw_files`;
- changing the arguments of the ACCIS of an output IDF, also its comfort standard (`accim.sim.accis.modify_accis`): {doc}`jupyter_notebooks/addAccis/using_addAccis`;
- running the simulations (`accim.run.run_ep`), with the Energy Management System of EnergyPlus or through its Python API, and estimating the size of their results before running them (`accim.run.estimate_results_size`): {doc}`jupyter_notebooks/runEp/using_runEp` and {ref}`python-api-backend`;
- tables and figures of the results (`accim.data.postprocessing.main.Table`): {doc}`jupyter_notebooks/Table/using_Table`;
- parametric simulation and optimisation (`accim.parametric_and_optimisation`): {doc}`parametric_and_optimisation`.

The How-to Guides section of this documentation shows them in Jupyter notebooks, which are part of the sample files (`pip install "accim[samples]"`, see {ref}`running-example-notebooks`).
