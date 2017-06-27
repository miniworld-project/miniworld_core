'''
Utility functions and class to use json as config file format.
'''
import json
import re
from collections import UserDict
from functools import wraps

from miniworld.errors import ConfigError, ConfigNotSet, ConfigMalformed, ConfigOptionNotSupported
from miniworld.util.Nothing import nothing

CONFIG_COMMENT = "//"

CONFIG_KEY_NODE_DETAILS = "node_details"

###############################################
### Decorators
###############################################

def arg2float(fun):
    def inner(*args, **kwargs):
        res = fun(*args, **kwargs)
        return float(res)
    return inner

def customizable_attrs(*keys, **kwargs):
    '''
    Decorator to read the value for the given keys.
    Prefers the node customized value.

    Parameters
    ----------
    keys: iterable<str>
        The keys in the scenario json mapping

    kwargs['not_null'] : bool, optional (default is False)
        Raises ConfigMalformed if value is null
    kwargs['customizable_key'] : bool, optional (default is False)

    kwargs['default'] : object, optional (default is `nothing`)
        The default value to choose if nothing is supplied.
    kwargs['expected'] : list<object>, optional (default is `[]`)
        Expect the value to be in the given list. Also allow None. You can disable this with 'not_null'.

    Returns
    -------
    object
        The value for the nested keys.

    Raises
    ------
    ConfigMalformed
        If the config is syntactically incorrect.
    ConfigOptionNotSupported
        If the option is not in the expected list.
    '''
    not_null = kwargs.get('not_null', False)

    default = kwargs.get("default", nothing)
    expected = kwargs.get("expected", [])

    customizable_key = kwargs.get("customizable_key", CONFIG_KEY_NODE_DETAILS)

    def wrap(fun):
        def wrap2(self, *fun_args, **fun_kwargs):
            res = nothing
            if customizable_key:
                # prefer node customized value
                node_id = str(fun_kwargs.get("node_id"))
                node_value = None
                if node_id is not None:
                    nested_keys = (("%s" % customizable_key), node_id) + keys
                    node_value = get_dict_nested_value(self.data, nested_keys)

                res = node_value

            if res in (None, nothing):
                 res = get_dict_nested_value(self.data, keys)

            #log.debug("%s : %s", _pretty_format(keys), res)

            # not null check
            if res in (None, nothing):
                if not_null:
                    raise ConfigMalformed("A value for '%s' is required! Customizable: '%s'" % (_pretty_format(keys), customizable_key))
                if default is not nothing:
                    res = default

            # do not return nothing, instead None
            if res is nothing:
                res = None

            # check the value for the expected ones
            if expected:
                # allow None
                expected.append(None)
                if res not in expected:
                    raise ConfigOptionNotSupported("The value for key '%s' is not supported! Is: '%s'. Supported values are: '%s'" % (_pretty_format(keys), res, ', '.join(map(str, expected))))
            return res

        return wrap2
    return wrap


def json2dict(func):
    '''
    Converts json to dict. E.g {"1" : 2} => {1 : 2}.
    The function does not handle this recursive!

    Parameters
    ----------
    func

    Returns
    -------
    dict
        If value was not None
    None
        Else
    '''
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if res is None:
            return res
        return {int(x) : y for x, y in res.items()}
    return func_wrapper

def _pretty_format(keys):
    return '->'.join(keys)

###############################################
### Subclassable Config object
###############################################

class JSONConfig(UserDict):
    '''
    `JSONConfig` leverages JSON to form a config system.
    Access to the values in the config are provided by decorating functions.
    The decorators map the key(s) and therefore the structure of the config layout to the functions.
    The names of the functions are considered to be stable. Therefore allowing abstracted access to the config.
    Changing the config layout requires only to change the mapping (given by the decorators) to the config layout.

    Examples
    --------
    >>> c = JSONConfig()
    >>> c.data = {'foo': {'bar': '5'}, 'node_details': {'1': {'foo': {'bar': '2'}}}}
    >>> print c.get_bar()
    5
    >>> print c.get_bar(node_id = 1)
    2
    >>> print c.get_default()
    1
    >>> print c.get_non_default()
    None
    '''
    def __init__(self):
        self.data = {}

    # ONLY FOR DEMO
    @customizable_attrs("foo", "bar")
    def get_bar(self):
        pass

    # ONLY FOR DEMO
    @customizable_attrs("default", default = 1)
    def get_default(self):
        pass

    # ONLY FOR DEMO
    @customizable_attrs("non_default")
    def get_non_default(self):
        pass
###############################################
### Helper methods
###############################################

def read_json_config(config = None, raw = False):
    '''
    Read a json config file.
    Strips all lines beginning with `CONFIG_COMMENT`.

    Parameters
    ----------
    config : str (optional, default is None)
        The path to the config file or the config itself (as JSON).
    raw : boolean (optional, default is False)
        If True, `config` contains already the config as str.
        Otherwise its the path to the scenario config file.

    Returns
    -------
    dict
        The config as JSON.

    Raises
    ------
    ConfigError
    '''

    try:
        if not raw:
            with open(config, "r") as f:
                config = f.read()

        # remove all comments
        data = re.sub("%s.*?(\n|\r\n)" % CONFIG_COMMENT, "", config)
        return json.loads(data, object_pairs_hook=collections.OrderedDict)
    except (ValueError, IOError):
        raise ConfigError("Config file '%s' could not be opened!" % config)

def get_dict_nested_value(d, keys):
    '''
    Get the nested dictionary value if present.

    Parameters
    ----------
    d : dict
    keys: iterable<str>

    Returns
    -------
    object
        The value if found
    Nothing

    '''
    cur_dict = d

    def dict_check(d):
        if not d is None:
            if not isinstance(d, dict):
                raise ConfigMalformed("The value for '%s' should be a dictionary! Not a value!" % _pretty_format(keys))

    if cur_dict is None:
        raise ConfigNotSet("Cannot read values from the config. It has not been set!")

    # travel in the dict
    for k in keys:
        # check all but the last value
        dict_check(cur_dict)
        cur_dict = cur_dict.get(k)
        if cur_dict is None:
            return nothing

    return cur_dict

# TODO: #40: DOC
def keys_to_int(d):
    if not isinstance(d, dict):
        return d
    return dict(zip(map(int, d.keys()), keys_to_int(d.values())))

if __name__ == '__main__':
    c = JSONConfig()
    c.config = {'foo': {'bar': '5'}, 'node_details': {'1': {'foo': {'bar': '2'}}}}
    # print c.get_bar()
    # print c.get_bar(node_id = 1)
    print(c.get_default())
    print(c.get_non_default())