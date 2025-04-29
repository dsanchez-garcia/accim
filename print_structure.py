import os

def print_project_structure(startpath='.'):
    """
    Prints the directory tree structure starting from the given path.

    :param startpath: The starting path for printing the structure (default is the current directory).
    """
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f'{subindent}{f}')

if __name__ == '__main__':
    print("Project Structure:")
    print_project_structure()