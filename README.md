
![ACCIM Logo with header](https://github.com/dsanchez-garcia/accim/blob/master/docs/images/accim_logo_white_w-header_640x320.png?raw=true) ![CIBSE_BSAwards](https://github.com/dsanchez-garcia/accim/blob/master/docs/images/CIBSE%20BSG%20WINNER%202022%20(610x150px).png?raw=true)

![PyPI](https://img.shields.io/pypi/v/accim)	![PyPI - Python Version](https://img.shields.io/pypi/pyversions/accim)	![GitHub](https://img.shields.io/github/license/dsanchez-garcia/accim)	![Read the Docs](https://img.shields.io/readthedocs/accim?color=cyan)



ACCIM stands for Adaptive Comfort Control Implemented Model.

In research terms, this is a proposal for a paradigm shift, from using fixed PMV-based to adaptive setpoint temperatures, based on adaptive thermal comfort algorithms and it has been widely studied and published on scientific research journals (for more information, refer to https://orcid.org/0000-0002-3080-0821).

In terms of code, this is a python package that transforms fixed setpoint temperature building energy models into adaptive setpoint temperature energy models by adding the Adaptive Comfort Control Implementation Script (ACCIS). This package has been developed to be used in EnergyPlus building energy performance simulations.

The figure below clearly explains the aim of adaptive setpoint temperatures: introducing hourly temperature values into the adaptive comfort zone. On the left column, you can see the simulation results of a naturally ventilated building, while on the right column, the same building in mixed-mode operation with adaptive setpoint temperatures.

![Use of adaptive setpoint](https://raw.githubusercontent.com/dsanchez-garcia/accim/master/docs/images/NV_vs_MM.png)

# 1. Citation

If you use this package, please cite us:

<div class="csl-entry">Sánchez-García, D., Bienvenido-Huertas, D., &#38; Rubio-Bellido, C. (2021). Computational approach to extend the air-conditioning usage to adaptive comfort: Adaptive-Comfort-Control-Implementation Script. <i>Automation in Construction</i>, <i>131</i>, 103900. https://doi.org/10.1016/j.autcon.2021.103900</div>

# 2. How to use

## 2.0 Requirements
To use accim, the following must be installed:
- Python 3.9
- EnergyPlus (any version between 9.1 and 22.2 those included)

## 2.1 Installation
First of all, you need to install the package:

    pip install accim

## 2.2 Usage

### 2.2.1 Full example: from preparation of the input IDFs and EPWs, to simulation and data analysis and visualization

You can see a Jupyter Notebook in the link below:  
https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/full_example/full_example.ipynb

You can also execute it at your computer, at the accim package folder within your site_packages path, in accim/sample_files/jupyter_notebooks/full_example/full_example.ipynb  
The path should be something like this, with your username instead of YOUR_USERNAME:  
C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python39\Lib\site-packages\accim\sample_files\jupyter_notebooks\full_example\full_example.ipynb

### 2.2.2 Transforming PMV-based into adaptive setpoint temperatures

This is a very brief explanation of the usage. Therefore, if you don't get the results you expected or get some error, I would recommend reading the 'how to use' section at the documentation in the link below.

accim will take as input IDF files those located at the same path as the script. You only need to run the following code:


#### 2.2.2.1 Short version

    from accim.sim import accis
    accis.addAccis()

Once you run this code, you will be asked to enter some information at the terminal or python console to generate the output IDF files.

#### 2.2.2.2 Longer version

    from accim.sim import accis
    accis.addAccis(
        ScriptType=str, # ScriptType: 'vrf_mm', 'vrf_ac', 'ex_mm', 'ex_ac'. For instance: ScriptType='vrf_ac',
        SupplyAirTempInputMethod=str, # SupplyAirTempInputMethod: 'supply air temperature', 'temperature difference'. For instance: SupplyAirTempInputMethod='supply air temperature',
        Output_keep_existing=bool, # Output_keep_existing: True or False. For instance: Output_keep_existing=False,
        Output_type=str, # Output_type: 'simplified' or 'standard'. For instance: Output_type='standard',
        Output_freqs=list, # Output_freqs: ['timestep', 'hourly', 'daily', 'monthly', 'runperiod']. For instance: Output_freqs=['hourly', 'runperiod'],
        EnergyPlus_version=str, # EnergyPlus_version: '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1', or '22.2'. For instance: EnergyPlus_version='22.2',
        TempCtrl=str, # TempCtrl: 'temperature' or 'temp', or 'pmv'. For instance: TempCtrl='temp',
        ComfStand=list, # it is the Comfort Standard. Can be any integer from 0 to 21. For instance: ComfStand=[0, 1, 2, 3],
        CAT=list, # it is the Category. Can be 1, 2, 3, 80, 85 or 90. For instance: CAT=[3, 80],
        ComfMod=list, # it is Comfort Mode. Can be 0, 1, 2 or 3. For instance: ComfMod=[0, 3],
        HVACmode=list, # it is the HVAC mode. 0 for Full AC, 1 for NV and 2 for MM. For instance: HVACmode=[0, 2],
        VentCtrl=list, # it is the Ventilation Control. Can be 0 or 1. For instance: VentCtrl=[0, 1],
        MaxTempDiffVOF=float, # When the difference of operative and outdoor temperature exceeds MaxTempDiffVOF, windows will be opened the fraction of MultiplierVOF. For instance: MaxTempDiffVOF=20,
        MinTempDiffVOF=float, # When the difference of operative and outdoor temperature is smaller than MinTempDiffVOF, windows will be fully opened. Between min and max, windows will be linearly opened. For instance: MinTempDiffVOF=1,
        MultiplierVOF=float, # Fraction of window to be opened when temperature difference exceeds MaxTempDiffVOF. For instance: Multiplier=0.2,
        VSToffset=list, # it is the offset for the ventilation setpoint. Can be any number, float or int. For instance: VSToffset=[-1.5, -1, 0, 1, 1.5],
        MinOToffset=list, # it is the offset for the minimum outdoor temperature to ventilate. Can be any positive number, float or int. For instance: MinOToffset=[0.5, 1, 2],
        MaxWindSpeed=list, # it is the maximum wind speed allowed for ventilation. Can be any positive number, float or int. For instance: MinOToffset=[2.5, 5, 10],
        ASTtol_start=float, # it is the start of the tolerance sequence. For instance: ASTtol_start=0,
        ASTtol_end_input=float, # it is the end of the tolerance sequence. For instance: ASTtol_start=2,
        ASTtol_steps=float, # these are the steps of the tolerance sequence. For instance: ASTtol_steps=0.25,
        NameSuffix=str # NameSuffix: some text you might want to add at the end of the output IDF file name. For instance: NameSuffix='whatever',
        verboseMode=bool # verboseMode: True to print all process in screen, False to not to print it. Default is True. For instance: verboseMode=True,
        confirmGen=bool # True to confirm automatically the generation of IDFs; if False, you'll be asked to confirm in command prompt. Default is False. For instance: confirmGen=False,
    )

You can see a Jupyter Notebook in the link below:  
https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/addAccis/using_addAccis.ipynb  

You can also execute it at your computer, at the accim package folder within your site_packages path, in accim/sample_files/jupyter_notebooks/addAccis/using_addAccis.ipynb  
The path should be something like this, with your username instead of YOUR_USERNAME:  
C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python39\Lib\site-packages\accim\sample_files\jupyter_notebooks\addAccis\using_addAccis.ipynb

### 2.2.3 Renaming epw files for later data analysis

You can see a Jupyter Notebook in the link below:  
https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/rename_epw_files/using_rename_epw_files.ipynb

You can also execute it at your computer, at the accim package folder within your site_packages path, in accim/sample_files/jupyter_notebooks/rename_epw_files/using_rename_epw_files.ipynb  
The path should be something like this, with your username instead of YOUR_USERNAME:  
C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python39\Lib\site-packages\accim\sample_files\jupyter_notebooks\rename_epw_files\using_rename_epw_files.ipynb

### 2.2.4 Running simulations

You can see a Jupyter Notebook in the link below:  
https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/runEp/using_runEp.ipynb

You can also execute it at your computer, at the accim package folder within your site_packages path, in accim/sample_files/jupyter_notebooks/runEp/using_runEp.ipynb  
The path should be something like this, with your username instead of YOUR_USERNAME:  
C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python39\Lib\site-packages\accim\sample_files\jupyter_notebooks\runEp\using_runEp.ipynb

### 2.2.5 Functions and methods for data analysis; making figures and tables

You can see a Jupyter Notebook in the link below:  
https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/Table/using_Table.ipynb

You can also execute it at your computer, at the accim package folder within your site_packages path, in accim/sample_files/jupyter_notebooks/Table/using_Table.ipynb  
The path should be something like this, with your username instead of YOUR_USERNAME:  
C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python39\Lib\site-packages\accim\sample_files\jupyter_notebooks\Table\using_Table.ipynb

# 3. Documentation

Detailed documentation, including the explanation of the different arguments, is at: https://accim.readthedocs.io/en/master/

# 4. Credits

It wouldn't have been possible to develop this python package without eppy, so thank you for such an awesome work.
