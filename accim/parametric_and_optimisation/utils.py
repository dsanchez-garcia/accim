def descriptor_has_options(values):
    #Checking value entered is a list containing floats or a tuple containing the minimum and maximum values
    descriptor_has_options = False
    if type(values) == tuple and len(values) == 2 and all([type(i) == float or type(i) == int for i in values]):
        pass
    elif type(values) == list and all(type(j) == float or type(j) == int for j in values):
        descriptor_has_options = True
    else:
        raise ValueError('values argument must be, FOR ALL CASES, '
                         'a list containing int or float, '
                         'or a tuple which contains the minimum and maximum values for the range')
    return descriptor_has_options
