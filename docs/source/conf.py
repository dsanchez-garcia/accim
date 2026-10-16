# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# --- CORRECCIÓN IMPORTANTE ---
# Sube dos niveles (desde docs/source/) para llegar a la raíz del proyecto.
# Esto permite a Sphinx encontrar e importar el paquete 'accim'.
sys.path.insert(0, os.path.abspath('../..'))

import accim

# todo re-run all notebooks

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'accim'
copyright = '2021, Daniel Sánchez-García'
author = 'Daniel Sánchez-García'
version = accim.__version__
# release = accim.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'nbsphinx',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'accim/sample_files', '**/.ipynb_checkpoints']

# The notebooks are shown with the outputs stored in them: they need EnergyPlus, so they are run
# beforehand (see docs/prepare_parametric_notebooks.py), never while building the documentation.
nbsphinx_execute = 'never'



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = [
    '_static',
    'previous_versions_pdfs',
]