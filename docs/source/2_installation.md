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
