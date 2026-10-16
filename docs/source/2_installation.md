# 2. Installation

First of all, you need to install the package. There are two options.

**Library only** (lightweight). Use this option if you don't need the sample
files:

    pip install accim

**Library + sample files** (Jupyter notebooks, IDFs, EPWs, CSVs, figures and
scripts):

    pip install "accim[samples]"

The sample files are published as the separate package `accim-samples`, with
the same version as accim, and are installed into the `accim/sample_files`
folder within your site-packages path. You can add them later with
`pip install "accim[samples]"` and remove them with
`pip uninstall accim-samples`; accim itself is not affected. To print the path
of the installed sample files, run:

    python -c "import accim.sample_files, os; print(os.path.dirname(accim.sample_files.__file__))"

In earlier versions, the sample files were always installed together with the
library.

To install some specific version, execute the same code followed by
"==version number". For instance, to install version 0.6.11:

    pip install accim==0.6.11

To install a specific version together with its sample files, add the extra
before the version number (only for versions that provide the `samples`
extra):

    pip install "accim[samples]==<version number>"

(running-example-notebooks)=
## Running the example notebooks

The example notebooks of this documentation are part of the sample files, in
the folder `jupyter_notebooks`. Each example has its own folder, with the
notebook and the input files it uses (IDFs, EPWs...):

| Folder | Content | Page |
| --- | --- | --- |
| `addAccis` | Adaptive setpoint temperatures with `addAccis()` | {doc}`jupyter_notebooks/addAccis/using_addAccis` |
| `rename_epw_files` | Renaming EPW files | {doc}`jupyter_notebooks/rename_epw_files/using_rename_epw_files` |
| `runEp` | Running simulations | {doc}`jupyter_notebooks/runEp/using_runEp` |
| `Table` | Data analysis, figures and tables | {doc}`jupyter_notebooks/Table/using_Table` |
| `full_example_IBPSA` | Full example, from the input files to the figures | {doc}`jupyter_notebooks/full_example_IBPSA/full_example_IBPSA` |
| `example_apmv_setpoints_paper` | aPMV setpoints | {doc}`jupyter_notebooks/example_apmv_setpoints_paper/using_apmv_setpoints` |
| `research_paper_case_study_v0-7-3` | Case study of a research paper | {doc}`jupyter_notebooks/research_paper_case_study/research_paper_case_study` |
| `parametric_and_optimisation_examples` | Parametric simulation and optimisation: tutorials `00`-`10` and complete workflows `wf1`-`wf5` | {doc}`jupyter_notebooks/parametric_and_optimisation_examples/index` |

To run them on your computer:

1. Install accim with the sample files, and Jupyter if you do not have it:

       pip install "accim[samples]" notebook

   If accim is already installed, this adds the sample files of the same
   version. When you upgrade accim, upgrade the sample files with it:
   `pip install --upgrade "accim[samples]"`.

2. Find the folder of the sample files with the command above:

       python -c "import accim.sample_files, os; print(os.path.dirname(accim.sample_files.__file__))"

3. Copy the folder of the example (for instance, `jupyter_notebooks/addAccis`)
   to a working folder, such as your Desktop. Run the notebooks there rather
   than in site-packages: they write their results next to them, and the
   installed sample files should not be modified.

4. Open a terminal (e.g. cmd) in the copied folder and run `jupyter notebook`.
   An internet browser will pop up, where you can open the .ipynb file.

The notebooks that run simulations need EnergyPlus. The sample models of
`parametric_and_optimisation_examples` are in the format of EnergyPlus 25.2;
the page {doc}`jupyter_notebooks/parametric_and_optimisation_examples/index`
explains how to run these notebooks and in which order.

The pages in the table show each notebook with its outputs. The same files can
be browsed on
[GitHub](https://github.com/dsanchez-garcia/accim/tree/master/accim/sample_files/jupyter_notebooks),
which shows the development version: it may be ahead of the version you
installed, while the installed sample files always match your version of accim.
