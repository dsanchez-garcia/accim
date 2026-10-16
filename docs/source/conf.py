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
release = accim.__version__

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

# The Markdown pages write the version as {{ version }} (|version| only works in reST pages).
myst_enable_extensions = ['substitution']
myst_substitutions = {'version': version}

# accim.data.preprocessing imports geopy, which is not a dependency of accim: mock it so that the
# API reference of the module can be generated.
autodoc_mock_imports = ['geopy']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['custom.css']

# -- Options for LaTeX output ------------------------------------------------

# The PDF of Read the Docs is built with pdflatex, which stops at each Unicode character it has no
# definition for (the notebooks use λ, ≤, −, ⌈, ⌉ and a few emoji) and leaves it out of the PDF.
latex_elements = {
    'preamble': r'''
\DeclareUnicodeCharacter{03BB}{\ensuremath{\lambda}}
\DeclareUnicodeCharacter{2264}{\ensuremath{\leq}}
\DeclareUnicodeCharacter{2212}{\ensuremath{-}}
\DeclareUnicodeCharacter{2308}{\ensuremath{\lceil}}
\DeclareUnicodeCharacter{2309}{\ensuremath{\rceil}}
\DeclareUnicodeCharacter{2705}{[OK]}
\DeclareUnicodeCharacter{274C}{[X]}
\DeclareUnicodeCharacter{26A0}{[!]}
\DeclareUnicodeCharacter{FE0F}{}
''',
}