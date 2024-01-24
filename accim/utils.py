from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen, remove, rename

def amend_idf_version_from_dsb(file_path, version=9.4):

    if version == 9.4:
        pattern = 'Version, 9.4.0.002'
        subst = 'Version, 9.4'

    #Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    #Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)