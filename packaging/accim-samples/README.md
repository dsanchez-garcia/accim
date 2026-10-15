# accim-samples

Sample files for [accim](https://pypi.org/project/accim/): Jupyter notebooks,
IDF and EPW files, CSV outputs, figures, tables and usage scripts.

These files used to be installed together with accim. They are now published
as this separate package so that the main `accim` package stays lightweight.

## Installation

Install accim together with the sample files of the same version:

    pip install "accim[samples]"

If you only need the library, install it without the sample files:

    pip install accim

You can add the sample files later with `pip install "accim[samples]"` and
remove them with `pip uninstall accim-samples`; accim itself is not affected.

## Where are the files?

The files are installed into the `accim/sample_files` folder within your
`site-packages` path. To print the exact path, run:

    python -c "import accim.sample_files, os; print(os.path.dirname(accim.sample_files.__file__))"

Copy the folder you need (for example, `jupyter_notebooks/addAccis`) to a
different path before running the notebooks, so that the installed files are
not modified.

The same files can be browsed online in the
[accim GitHub repository](https://github.com/dsanchez-garcia/accim/tree/master/accim/sample_files).

## Versioning

Each version of `accim-samples` matches the version of `accim` with the same
number, and requires it.
