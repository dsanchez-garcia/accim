import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
      name='accim',
      version='0.0.11',
      description="Transforms PMV-based into adaptive setpoint temperature EnergyPlus building energy models",
      long_description_content_type="text/markdown",
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
      scripts=['bin/accis.py']
      )
