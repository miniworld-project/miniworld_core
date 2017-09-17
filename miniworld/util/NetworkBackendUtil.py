
def szudzik_pairing_function(a, b):
    '''
    a, b >= 0


    See Also
    --------
    http://stackoverflow.com/questions/919612/mapping-two-integers-to-one-in-a-unique-and-deterministic-way
    Parameters
    ----------
    a
    b

    Returns
    -------

    '''
    if a >= b:
        return a * a + a + b
    return a + b * b
