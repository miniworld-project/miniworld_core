from collections import defaultdict

# TODO: RENAME


def to_fully_staffed_matrix_3(d):
    '''

    Parameters
    ----------
    d : dict<object, object>

    Returns
    -------
    dict<object, object>
    '''
    for key, val in d.items():
        d[val] = key

    return d


def to_fully_staffed_matrix(d):
    '''

    Parameters
    ----------
    d : dict<object, set<object>>

    Returns
    -------
    dict<object, set<object>>
    '''
    fully_staffed = defaultdict(set)

    # copy entries
    for k, vals in d.items():
        fully_staffed[k] = set(vals)

    # make it fully staffed
    for k, vals in d.items():
        for val in vals:
            fully_staffed[val].add(k)

    return fully_staffed

# TODO: RENAME, MOVE TO NETWORKMANAGER!


def to_fully_staffed_matrix_2(d):
    '''
    Note: The key object must support the creation of the same object via its constructor.

    Parameters
    ----------
    d : dict<(object, object>, list<object>>

    Returns
    -------
    d : dict<reversed<object, object>>, list<reversed<object>>>
    '''
    fully_staffed = {}

    for k, vals in d.items():
        # copy entry
        fully_staffed[k] = vals
        # make it fully staffed, reverse keys and values
        k2 = type(k)(reversed(k))
        fully_staffed[k2] = list(map(lambda x: type(x)(reversed(x)), vals))

    return fully_staffed


# TODO: DOC
def list_merge_values(d, d2, in_place=True):
    '''

    Parameters
    ----------
    d
    d2
    in_place : bool, optional (default is True)
        Do the update in-place.

    Examples
    --------
    >>> list_merge_values({1:[2]}, {1:[3]})
    {1: [2, 3]}

    Returns
    -------

    '''
    d3 = d.copy() if not in_place else d
    for key, val in d2.items():
        if key not in d3:
            d3[key] = val
        else:
            d3[key].extend(val)
    return d3


def merge_recursive_in_place(d, d2):
    '''

    Parameters
    ----------
    d
    d2

    Returns
    -------
    '''

    if d2 is None:
        return d

    if isinstance(d, dict) and isinstance(d2, dict):

        for k in set(d2.keys()) & set(d.keys()):
            d[k] = merge_recursive_in_place(d.get(k, None), d2.get(k, None))
        return d
    else:
        # prefer keys from d2
        return d2


if __name__ == '__main__':
    d = {'foo': {'bar': 1, 'rest': 'foO'}}
    d2 = {'foo': {'bar': 2}}

    print(merge_recursive_in_place(d, d2))
    print(merge_recursive_in_place({}, d2))
    print(merge_recursive_in_place(d, {}))
