import os

import pytest


@pytest.mark.parametrize('include_interfaces', (True, False))
def test_parse_core_config_file(core_topologies_dir, include_interfaces):
    from miniworld.util.CoreConfigFileParser import CoreConfigFileParser
    res = CoreConfigFileParser().parse_core_config_file(os.path.join(core_topologies_dir, 'chain5.xml'),
                                                        include_interfaces=include_interfaces)
    if include_interfaces:
        assert res == {
            (0, 0): (1, 0),
            (1, 1): (2, 0),
            (2, 1): (3, 0),
            (3, 1): (4, 0),
        }
    else:
        assert res == {0: set([1]), 1: set([2]), 2: set([3]), 3: set([4])}
