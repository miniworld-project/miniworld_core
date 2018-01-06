# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestInterface.test_interface_get 1'] = {
    'data': {
        'node': {
            'id': 'SW50ZXJmYWNlOjA=',
            'iid': 0,
            'ipv4': '172.16.0.1',
            'mac': '00:00:00:00:00:01',
            'name': 'mesh',
            'nrHostInterface': 0
        }
    }
}

snapshots['TestInterface.test_interface_get_non_existing 1'] = {
    'data': {
        'node': None
    }
}
