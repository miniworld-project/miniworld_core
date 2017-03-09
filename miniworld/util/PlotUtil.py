import json
from collections import defaultdict
from itertools import combinations, combinations_with_replacement, ifilter

__author__ = 'Nils Schmidt'

# TODO: #42

def combinations_with_replacement_no_identical(iterable, r):
    return ifilter(lambda v : v[0] != v[1], list(combinations_with_replacement(iterable, r)))

def fill_quadratic_matrix(matrix, size, fill_in):
    fill = dict(zip(list(combinations_with_replacement_no_identical(range(1, size + 1), 2)) + [(x,x) for x in range(1, size + 1)], [fill_in for _ in range(size ** 2 )]))
    fill.update(matrix)
    return fill

def merge_matrices(stats_lines):
    '''
    Merges the lines of several matrices.

    Parameters
    ----------
    stats_lines : iterable< list<list<object>>> >
        Each element contains the lines of a matrix.

    Returns
    -------
    list<list<object>>
    '''

    cnt_lists = len(stats_lines)
    res = defaultdict(list)
    for line_nr in range(len(stats_lines[0])):
        for item_nr in range(len((stats_lines[0][line_nr]))):
            stats_items = [stats_lines[list_idx][line_nr][item_nr] for list_idx in range(cnt_lists)]
            stats_item_strs = [str(x) for x in stats_items]
            if len(filter(lambda x: len(x) > 0, stats_item_strs)) > 0:
                res[line_nr].append ( ' / '.join(stats_item_strs))
            else:
                res[line_nr].append( "" )

    return res.values()

def format_matrix(values_as_lines, ids):
    '''
    Pretty-format the matrix.

    Parameters
    ----------
    values_as_lines : list<list<str>>
        Contains the lines of the matrix.

    ids : list<str>
        Label the rows and columns.

    Returns
    -------
    str
    '''
    import pandas
    return str(pandas.DataFrame(values_as_lines,
                                index = ids,
                                columns = ids))