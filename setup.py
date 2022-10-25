import setuptools
from os import path
from setuptools.command.install import install



class PostInstallCommand(install):
    """Post-installation for installation mode."""
    messages = []

    def run(self):
        install.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        import os
        import shutil

        # Creating a dictionary with IDD paths, IDD backups paths and the first line to modify
        dict_lines = {
            'EnergyPlus 22.2.0': [r"C:\EnergyPlusV22-2-0\Energy+.idd", r"C:\EnergyPlusV22-2-0\Energy+_backup.idd", 82643],
            'EnergyPlus 22.1.0': [r"C:\EnergyPlusV22-1-0\Energy+.idd", r"C:\EnergyPlusV22-1-0\Energy+_backup.idd", 81925],
            'EnergyPlus 9.6.0': [r"C:\EnergyPlusV9-6-0\Energy+.idd", r"C:\EnergyPlusV9-6-0\Energy+_backup.idd", 81798],
            'EnergyPlus 9.5.0': [r"C:\EnergyPlusV9-5-0\Energy+.idd", r"C:\EnergyPlusV9-5-0\Energy+_backup.idd", 80493],
            'EnergyPlus 9.4.0': [r"C:\EnergyPlusV9-4-0\Energy+.idd", r"C:\EnergyPlusV9-4-0\Energy+_backup.idd", 80526],
            'EnergyPlus 9.3.0': [r"C:\EnergyPlusV9-3-0\Energy+.idd", r"C:\EnergyPlusV9-3-0\Energy+_backup.idd", 80397],
            'EnergyPlus 9.2.0': [r"C:\EnergyPlusV9-2-0\Energy+.idd", r"C:\EnergyPlusV9-2-0\Energy+_backup.idd", 79641],
            'EnergyPlus 9.1.0': [r"C:\EnergyPlusV9-1-0\Energy+.idd", r"C:\EnergyPlusV9-1-0\Energy+_backup.idd", 79116],
            'EnergyPlus 9.0.0': [r"C:\EnergyPlusV9-0-0\Energy+.idd", r"C:\EnergyPlusV9-0-0\Energy+_backup.idd", 78635],
        }

        new_lines_no = 7500

        # global messages
        # messages = []

        # Iterating through EnergyPlus versions
        for i in dict_lines:
            # Renaming the original IDD file to keep it as a backup
            try:
                os.rename(dict_lines[i][0], dict_lines[i][1])
            except FileExistsError:
                message = f'The file Energy+_backup.idd already exists, therefore this script has already been run for {i}.'
                print(message)
                PostInstallCommand.messages.append(message)
                os.remove(dict_lines[i][0])
                # os.rename(dict_lines[i][1], dict_lines[i][0])
                shutil.copy(dict_lines[i][1], dict_lines[i][0])
                # continue
            except FileNotFoundError:
                message = f'The file Energy+.idd has not been found, therefore {i} is not installed at default path.'
                print(message)
                PostInstallCommand.messages.append(message)
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
                message = f"{i}'s IDD has been correctly modified. {new_lines_no} lines have been added to the object EnergyManagementSystem:Program."
            print(message)
            PostInstallCommand.messages.append(message)



this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='accim',
    version='0.3.1',
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
           '*.xls',
           '*.ipynb'
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

# print('IDD modifications:')
# print(PostInstallCommand.messages, sep='\n')