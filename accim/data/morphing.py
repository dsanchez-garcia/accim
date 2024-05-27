def morph_epws(
        fwg_path: str,
        epw_filepaths: any = 'all',
        delete_morphing_files: bool = True,
        verbose: bool = False,
        fwg_options_gcms: str = None,
        fwg_options_ensemble: int = 1,
        fwg_options_month_transition_hours: int = 72,
        fwg_options_do_multithread_computation: bool = True,
        fwg_options_interpolation_method_id: int = 0,
        fwg_options_do_limit_variables: bool = True,
):
    """
    This function is a wrapper for the use of the FutureWeatherGenerator tool (https://future-weather-generator.adai.pt/),
    developed by Eugènio Rodrigues et al., in command line.
    It will move the epws in the working directory to a folder with the same name,
    will morph them within their respective directories,
    then will rename them using the original epw filename with the suffix depending on the scenario
    (e.j. the future scenarios for Granada.epw will be Granada_ssp126_2050.epw, Granada_ssp126_2080.epw, etc.)
    and move them back to the parent directory.
    If requested, the files generated from the moprhing process will be deleted.

    :param fwg_path: The path to the FutureWeatherGenerator tool.
    :param epw_filepaths: A list of epw filenames to be morphed.
    :param delete_morphing_files: True to delete all files resulting from the morphing process
        except .epw files.
    :param verbose: True to print on screen the performed actions.
    :param fwg_options_gcms: The GCMs separated by a comma (without white space).
    :param fwg_options_ensemble: Option to create an ensemble from the selected models: 0 is no, 1 is yes.
    :param fwg_options_month_transition_hours: the number of hours to smooth the transition between months: 0 to 336 hours.
    :param fwg_options_do_multithread_computation: True to do the computations in multithread.
    :param fwg_options_interpolation_method_id: Selects the grid method: 0 – bilinear interpolation, 1 – an average of the four nearest points; 2 – nearest point.
    :param fwg_options_do_limit_variables: True to bound each generated variable to its physical limits
    """
    import os
    import shutil
    import subprocess

    # Get the absolute path of the current working directory
    cwd = os.getcwd()

    # Get a list of all .epw files in the current working directory
    if epw_filepaths == 'all':
        epw_files = [file for file in os.listdir() if file.endswith(".epw")]
    else:
        epw_files = epw_filepaths

    if fwg_options_gcms is None:
        fwg_options_gcms = 'BCC_CSM2_MR,CanESM5,CanESM5_1,CanESM5_CanOE,CAS_ESM2_0,CMCC_ESM2,CNRM_CM6_1_HR,CNRM_ESM2_1,EC_Earth3,EC_Earth3_Veg,FGOALS_g3,GISS_E2_1_G,GISS_E2_1_H,GISS_E2_2_G,IPSL_CM6A_LR,MIROC_ES2H,MIROC_ES2L,MIROC6,MRI_ESM2_0,UKESM1_0_LL'

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
        if verbose:
            print(f"Moved {epw_file} to folder {folder_name}")

    for folder_name, epw_name, folder_path, epw_path in [i for i in directory_file_paths]:
        # directory = os.path.dirname(epw)
        # directory = r'D:\OneDrive - ZER0CEM\Python\testing_morphing_python'
        subprocess.run(f'java -cp '
                       f'"{fwg_path}" '
                       f'futureweathergenerator.Morph "{epw_path}" '
                       f'{fwg_options_gcms} '
                       f'{fwg_options_ensemble} '
                       f'{fwg_options_month_transition_hours} '
                       f'"{folder_path}/" '
                       f'{fwg_options_do_multithread_computation} '
                       f'{fwg_options_interpolation_method_id} '
                       f'{fwg_options_do_limit_variables}')


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
                    if verbose:
                        print(f"Renamed {file_name} to {new_file_name}")

                    # Move the renamed file to the parent folder
                    parent_folder_path = os.path.dirname(folder_path)
                    moved_file_path = os.path.join(parent_folder_path, new_file_name)
                    shutil.move(new_file_path, moved_file_path)
                    if verbose:
                        print(f"Moved {new_file_name} to {parent_folder_path}")

        # Move the original EPW file to the parent folder
        original_file_path = os.path.join(folder_path, folder_name + ".epw")
        shutil.move(original_file_path, parent_folder_path)
        if verbose:
            print(f"Moved {folder_name}.epw to {parent_folder_path}")

    if delete_morphing_files:
        # Delete the folders created during the process
        for folder_name, epw_name, folder_path, epw_path in [i for i in directory_file_paths]:
            shutil.rmtree(folder_path)
            if verbose:
                print(f"Deleted folder: {folder_path}")

