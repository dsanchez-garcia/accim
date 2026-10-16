# 3. Quick tutorial

## 3.1 Implementing adaptive setpoint temperatures

This is a very brief explanation of the main function of accim, `addAccis()`. If you don't get the results you expected or get some error, please read {doc}`4_detailed use`, which explains every argument.

By default, accim takes as input the IDF files located in the working folder (the folder where you run Python), except those whose names contain `[` or `_pymod`, which are the files that accim generates. The argument `idfs` takes a list of IDF files instead. accim saves the output IDF files in the working folder; the input IDF files are not modified.

### 3.1.1 Short version

```python
from accim.sim import accis
accis.addAccis()
```

Once you run this code, you will be asked to enter some information at the terminal or python console to generate the output IDF files.

### 3.1.2 Longer version

You can also enter the information as arguments, so that accim does not ask for it. Use keyword arguments, as below: the first positional argument of `addAccis()` is `idfs`. For instance, to generate the IDFs of EN 16798-1 (categories I, II and III) and ASHRAE 55 (80 % and 90 % acceptability), with static and adaptive setpoint temperatures, and with a VRF system in mixed-mode operation:

```python
from accim.sim import accis
accis.addAccis(
    ScriptType='vrf_mm',                                  # VRF system with mixed-mode operation
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,                           # remove the outputs of the input IDF
    Output_type='standard',
    Output_freqs=['hourly', 'runperiod'],
    EnergyPlus_version='auto',                            # the EnergyPlus version of each IDF
    TempCtrl='temperature',                               # setpoints on the operative temperature
    ComfStand=[1, 2],                                     # EN 16798-1 and ASHRAE 55
    CAT=[1, 2, 3, 80, 90],                                # categories I-III, 80 % and 90 % acceptability
    ComfMod=[0, 3],                                       # static, and adaptive setpoints
    HVACmode=[2],                                         # mixed mode
    VentCtrl=[0],                                         # ventilate above the neutral temperature
    confirmGen=True,                                      # generate the IDFs without asking for confirmation
)
```

Each valid combination of values gives an output IDF: categories I, II and III only apply to EN 16798-1, and 80 % and 90 % acceptability to ASHRAE 55, so this call generates 10 IDFs (6 for EN 16798-1 and 4 for ASHRAE 55). Their names give the values used, for instance:

    TestModel[CS_INT EN16798[CA_1[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf

The arguments that are not given take their default values. Section {ref}`setting-up-the-target-idfs` lists all the arguments, with their values and defaults, and explains the names of the output IDFs.

## 3.2 Other uses

Although the main use of accim is the implementation of adaptive setpoint temperatures, there are some functions, classes and methods that allow to roughly automate the whole process consisting of preparation of the epw and idf files, the simulation runs and the data analysis:

- setpoints based on the adaptive predicted mean vote (`accim.sim.apmv_setpoints`): {doc}`jupyter_notebooks/example_apmv_setpoints_paper/using_apmv_setpoints`;
- renaming EPW files for the data analysis (`accim.data.preprocessing.rename_epw_files`): {doc}`jupyter_notebooks/rename_epw_files/using_rename_epw_files`;
- running the simulations (`accim.run.run.runEp`): {doc}`jupyter_notebooks/runEp/using_runEp`;
- tables and figures of the results (`accim.data.postprocessing.main.Table`): {doc}`jupyter_notebooks/Table/using_Table`;
- parametric simulation and optimisation (`accim.parametric_and_optimisation`): {doc}`parametric_and_optimisation`.

The How-to Guides section of this documentation shows them in Jupyter notebooks, which are part of the sample files (`pip install "accim[samples]"`, see {ref}`running-example-notebooks`).
