import setuptools
from os import path
from setuptools import setup
from setuptools.command.install import install


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        import os

        # Creating a dictionary with IDD paths, IDD backups paths and the first line to modify
        dict_lines = {
            'EnergyPlus 9.6.0': [r"C:\EnergyPlusV9-6-0\Energy+.idd", r"C:\EnergyPlusV9-6-0\Energy+_backup.idd", 81798],
            'EnergyPlus 9.5.0': [r"C:\EnergyPlusV9-5-0\Energy+.idd", r"C:\EnergyPlusV9-5-0\Energy+_backup.idd", 80493],
            'EnergyPlus 9.4.0': [r"C:\EnergyPlusV9-4-0\Energy+.idd", r"C:\EnergyPlusV9-4-0\Energy+_backup.idd", 80526],
            'EnergyPlus 9.3.0': [r"C:\EnergyPlusV9-3-0\Energy+.idd", r"C:\EnergyPlusV9-3-0\Energy+_backup.idd", 80397],
            'EnergyPlus 9.2.0': [r"C:\EnergyPlusV9-2-0\Energy+.idd", r"C:\EnergyPlusV9-2-0\Energy+_backup.idd", 79641],
            'EnergyPlus 9.1.0': [r"C:\EnergyPlusV9-1-0\Energy+.idd", r"C:\EnergyPlusV9-1-0\Energy+_backup.idd", 79116],
            'EnergyPlus 9.0.0': [r"C:\EnergyPlusV9-0-0\Energy+.idd", r"C:\EnergyPlusV9-0-0\Energy+_backup.idd", 78635],
        }

        new_lines_no = 1500

        # Iterating through EnergyPlus versions
        for i in dict_lines:
            # Renaming the original IDD file to keep it as a backup
            try:
                os.rename(dict_lines[i][0], dict_lines[i][1])
            except FileExistsError:
                print(
                    f'The file Energy+_backup.idd already exists, therefore this script has already been run for {i}.')
                continue
            except FileNotFoundError:
                print(f'The file Energy+.idd has not been found, therefore {i} is not installed at defalut path.')
                continue
            # Reading the content of the IDD
            with open(dict_lines[i][1], 'r') as file:
                data = file.readlines()
            # Making amendments in variable data
            data[dict_lines[i][2]] = data[dict_lines[i][2]].replace(';', ',')
            for j in range(503, new_lines_no + 1):
                if j == 503:
                    line = dict_lines[i][2] + 1
                if j == new_lines_no:
                    data.insert(line, f'A{j};\n')
                else:
                    data.insert(line, f'A{j},\n')
                line = line + 1

            # Overwriting the IDD with the amendments in variable data
            with open(dict_lines[i][0], 'w') as file:
                file.writelines(data)
            print(
                f"{i}'s IDD has been correctly modified. {new_lines_no} lines have been added to the object EnergyManagementSystem:Program.")


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='accim',
    version='0.2.4',
    description='Transforms PMV-based into adaptive setpoint temperature EnergyPlus building energy models',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dsanchez-garcia/accim',
    author='Daniel Sánchez-García',
    author_email='dsanchez7@us.es',
    license='MIT License',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering'
        ],
    packages=setuptools.find_packages(),
    package_data={
       '': [
           '*.csv',
           '*.idf',
           '*.epw',
           '*.eso',
           '*.jpg',
           '*.png',
           '*.xlsx',
           '*.xls'
            ]
       },
    python_requires='<3.10',
    install_requires=[
        'eppy',
        'pycountry',
        'geopy',
        'matplotlib',
        'pandas',
        'datapackage',
        # 'shutil',
        # 'glob'
        ],
    scripts=['bin/addAccis.py'],
    keywords=[
        'adaptive thermal comfort',
        'building energy model',
        'building performance simulation',
        'energy efficiency'
        ],
    cmdclass={
        'install': PostInstallCommand
    }
    )
