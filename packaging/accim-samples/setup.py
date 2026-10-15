"""setup.py of the 'accim-samples' distribution.

Do not build this folder directly. ``packaging/build_samples_dist.py`` copies
this file, together with ``MANIFEST.in``, ``README.md``, the repository
``LICENSE``, a ``VERSION`` file and a copy of ``accim/sample_files``, into a
staging folder and builds the distribution there.

The resulting wheel only contains ``accim/sample_files/**``. It never contains
``accim/__init__.py`` or any other module of the core ``accim`` distribution,
so both distributions can be installed (and uninstalled) independently into
the same ``site-packages/accim`` folder.
"""
import os

import setuptools

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, 'VERSION'), encoding='utf-8') as f:
    VERSION = f.read().strip()

with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

# Only accim/sample_files and its subfolders are packaged ('accim' itself is
# not included). Subfolders whose names are not valid Python identifiers
# (e.g. 'sample IDFs' or 'research_paper_case_study_v0-7-3') are not
# packages: their files are shipped as data files of the closest parent
# package through include_package_data and MANIFEST.in.
PACKAGES = [
    package
    for package in setuptools.find_namespace_packages(
        include=['accim.sample_files', 'accim.sample_files.*']
    )
    if all(part.isidentifier() for part in package.split('.'))
]

setuptools.setup(
    name='accim-samples',
    version=VERSION,
    description=(
        'Sample files for accim: Jupyter notebooks, IDFs, EPWs, CSVs, '
        'figures and scripts'
    ),
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://github.com/dsanchez-garcia/accim',
    author='Daniel Sánchez-García',
    author_email='daniel.sanchezgarcia@uca.es',
    license='GPL-3.0-or-later',
    license_files=('LICENSE',),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Intended Audience :: Science/Research',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Scientific/Engineering',
    ],
    packages=PACKAGES,
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.9',
    # The sample files are written for this exact version of accim.
    install_requires=[f'accim=={VERSION}'],
    keywords=[
        'adaptive thermal comfort',
        'building energy model',
        'building performance simulation',
        'energy efficiency',
        'examples',
    ],
)
