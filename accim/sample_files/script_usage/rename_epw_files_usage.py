from accim.data.preprocessing import rename_epw_files
z = rename_epw_files(
    rename_dict={
        'Brasov': 'Brasov',
        'Bucarest': 'Bucharest',
        'Cluj': 'Cluj',
        'Constanza': 'Constanza',
        'Miercurea': 'Harguita'
    }
)