
![ACCIM Logo with header](docs/images/accim_logo_nohatch_w-header.svg)

![PyPI](https://img.shields.io/pypi/v/accim)	![PyPI - Python Version](https://img.shields.io/pypi/pyversions/accim)	![GitHub](https://img.shields.io/github/license/dsanchez-garcia/accim)	![Read the Docs](https://img.shields.io/readthedocs/accim?color=cyan)



ACCIM stands for Adaptive Comfort Control Implemented Model.

In research terms, this is a proposal for a paradigm shift, from using fixed PMV-based to adaptive setpoint temperatures, based on adaptive thermal comfort algorithms and it has been widely studied and published on scientific research journals (for more information, refer to https://orcid.org/0000-0002-3080-0821).

In terms of code, this is a python package that transforms fixed setpoint temperature building energy models into adaptive setpoint temperature energy models by adding the Adaptive Comfort Control Implementation Script (ACCIS). This package has been developed to be used in EnergyPlus building energy performance simulations.

### Citation

If you use this package, please cite us:

<div class="csl-entry">Sánchez-García, D., Bienvenido-Huertas, D., &#38; Rubio-Bellido, C. (2021). Computational approach to extend the air-conditioning usage to adaptive comfort: Adaptive-Comfort-Control-Implementation Script. <i>Automation in Construction</i>, <i>131</i>, 103900. https://doi.org/10.1016/j.autcon.2021.103900</div>

### How to use
#### Installation
First of all, you need to install the package:

    pip install accim

#### Usage

This is a very brief explanation of the usage. Therefore, if you don't get the results you expected or get some error, I would recommend reading the 'how to use' section at the documentation in the link below.

accim will take as input IDF files those located at the same path as the script. You only need to run the following code:


##### Quick version

    from accim.sim import accis
    accis.addAccis()

Once you run this code, you will be asked to enter some information at the terminal or python console to generate the output IDF files.

##### Longer version

    from accim.sim import accis
    accis.addAccis(
        ScriptType=str, # ScriptType: 'vrf', 'ex_mm', 'ex_ac'. For instance: ScriptType='vrf',
        Outputs=str, # Outputs: 'simplified', 'standard' or 'timestep'. For instance: Outputs='standard',
        EnergyPlus_version=str, # EnergyPlus_version: 'ep91', 'ep92', 'ep93', 'ep94', 'ep95' or 'ep96'. For instance: EnergyPlus_version='ep96',
        TempCtrl=str, # TempCtrl: 'temperature' or 'temp', or 'pmv'. For instance: TempCtrl='temp',
        ComfStand=list, # it is the Comfort Standard. Can be any integer from 0 to 16. For instance: ComfStand=[0, 1, 2, 3],
        CAT=list, # it is the Category. Can be 1, 2, 3, 80, 85 or 90. For instance: CAT=[3, 80],
        ComfMod=list, # it is Comfort Mode. Can be 0, 1, 2 or 3. For instance: ComfMod=[0, 3],
        HVACmode=list, # it is the HVAC mode. 0 for Full AC, 1 for NV and 2 for MM. For instance: HVACmode=[0, 2],
        VentCtrl=list, # it is the Ventilation Control. Can be 0 or 1. For instance: VentCtrl=[0, 1],
        VSToffset=list, # it is the offset for the ventilation setpoint. Can be any number, float or int. For instance: VSToffset=[-1.5, -1, 0, 1, 1.5],
        MinOToffset=list, # it is the offset for the minimum outdoor temperature to ventilate. Can be any positive number, float or int. For instance: MinOToffset=[0.5, 1, 2],
        MaxWindSpeed=list, # it is the maximum wind speed allowed for ventilation. Can be any positive number, float or int. For instance: MinOToffset=[2.5, 5, 10],
        ASTtol_start=float, # it is the start of the tolerance sequence. For instance: ASTtol_start=0,
        ASTtol_end_input=float, # it is the end of the tolerance sequence. For instance: ASTtol_start=2,
        ASTtol_steps=float, # these are the steps of the tolerance sequence. For instance: ASTtol_steps=0.25,
        NameSuffix=str # NameSuffix: some text you might want to add at the end of the output IDF file name
        verboseMode=bool # verboseMode: True to print all process in screen, False to not to print it. Default is True.
        bool # confirmGen: True to confirm automatically the generation of IDFs; if False, you'll be asked to confirm in command prompt. Default is False. 
    )

### Documentation

The documentation is at: https://accim.readthedocs.io/en/master/

### Credits

It wouldn't have been possible to develop this python package without eppy, so thank you for such an awesome work.
