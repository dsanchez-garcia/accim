import os
import shutil
import subprocess

fwg = "D:\OneDrive - ZER0CEM\SIMULATION\Tools\FutureWeatherGenerator_v1.2.3.jar"

# Get the absolute path of the current working directory
cwd = os.getcwd()

# Get a list of all .epw files in the current working directory
epw_files = [file for file in os.listdir() if file.endswith(".epw")]

# List to store tuples of directories, EPW file names, absolute paths of folders, and absolute paths of EPW files
directory_file_paths = []

# Iterate through each .epw file
for epw_file in epw_files:
    # Create a folder with the same name as the .epw file (without extension)
    folder_name = os.path.splitext(epw_file)[0]
    folder_path = os.path.join(cwd, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # Move the .epw file into the created folder
    epw_file_path = os.path.join(folder_path, epw_file)
    shutil.move(epw_file, epw_file_path)

    # Save the directory name, EPW file name, folder absolute path, and EPW file absolute path in the list
    directory_file_paths.append((folder_name, epw_file, folder_path, epw_file_path))

    print(f"Moved {epw_file} to folder {folder_name}")

# Print the list of tuples containing directory name, EPW file name, folder absolute path, and EPW file absolute path
print(directory_file_paths)


for folder_name, epw_name, folder_path, epw_path in [i for i in directory_file_paths]:
    # directory = os.path.dirname(epw)
    # directory = r'D:\OneDrive - ZER0CEM\Python\testing_morphing_python'
    subprocess.run(f'java -cp '
                   f'"{fwg}" '
                   f'futureweathergenerator.Morph "{epw_path}" '
                   f'BCC_CSM2_MR,CanESM5,CanESM5_1,CanESM5_CanOE,CAS_ESM2_0,CMCC_ESM2,CNRM_CM6_1_HR,CNRM_ESM2_1,EC_Earth3,EC_Earth3_Veg,FGOALS_g3,GISS_E2_1_G,GISS_E2_1_H,GISS_E2_2_G,IPSL_CM6A_LR,MIROC_ES2H,MIROC_ES2L,MIROC6,MRI_ESM2_0,UKESM1_0_LL 1 72 '
                   f'"{folder_path}/" '
                   f'true '
                   f'0 '
                   f'true')


##

# Search for new EPW files in the folder paths and rename them according to the pattern
scenario_strings = ['ssp126_2050', 'ssp126_2080', 'ssp245_2050', 'ssp245_2080', 'ssp370_2050', 'ssp370_2080',
                    'ssp585_2050', 'ssp585_2080']

for folder_name, epw_name, folder_path, epw_path in [i for i in directory_file_paths]:
    # List files in the folder path
    files_in_folder = [ i for i in os.listdir(folder_path) if i.endswith('.epw')]

    for file_name in files_in_folder:
        # Check if the file name contains any of the scenario strings
        for scenario in scenario_strings:
            if scenario in file_name:
                # Rename the file following the specified pattern
                new_file_name = f"{folder_name}_{scenario}.epw"
                old_file_path = os.path.join(folder_path, file_name)
                new_file_path = os.path.join(folder_path, new_file_name)
                os.rename(old_file_path, new_file_path)
                print(f"Renamed {file_name} to {new_file_name}")

                # Move the renamed file to the parent folder
                parent_folder_path = os.path.dirname(folder_path)
                moved_file_path = os.path.join(parent_folder_path, new_file_name)
                shutil.move(new_file_path, moved_file_path)
                print(f"Moved {new_file_name} to {parent_folder_path}")

delete_files = False
if delete_files:
    # Delete the folders created during the process
    for folder_name, epw_name, folder_path, epw_path in [i for i in directory_file_paths]:
        shutil.rmtree(folder_path)
        print(f"Deleted folder: {folder_path}")

# Print the list of tuples containing directory name, EPW file name, folder absolute path, and EPW file absolute path
print(directory_file_paths)