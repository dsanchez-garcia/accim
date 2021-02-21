import setuptools
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
      name='accim',
      version='0.0.14',
      description="Transforms PMV-based into adaptive setpoint temperature EnergyPlus building energy models",
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/dsanchez-garcia/accim',
      author='Daniel Sánchez-García',
      author_email='dsanchez7@us.es',
      license="MIT License",
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Topic :: Scientific/Engineering"
          ],
      packages=setuptools.find_packages(),
      package_data={
           "": ["*.csv", "*.idf"]
           },
      install_requires=[
           "eppy"
           ],
      scripts=['bin/accis.py'],
      keywords=[
          'adaptive thermal comfort',
          'building energy model',
          'building performance simulation',
          'energy efficiency'
          ]
      )
