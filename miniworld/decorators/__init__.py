__author__ = 'Nils Schmidt'

def memoize_pos_args(fun):
    ''' Memoize the functions positional arguments and return the same result for it '''
    # arguments, result
    memo = {}

    def wrapper(*args, **kwargs):
        if args in memo:
            return memo[args]
        else:
            memoize = True
            if kwargs.get("no_memoize"):
                del kwargs["no_memoize"]
                memoize = False

            res = fun(*args, **kwargs)
            if memoize:
                memo[args] = res
            return res

    return wrapper