# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestConnection.test_connection_get 1'] = {
    'data': {
        'node': {
            'connected': True,
            'distance': 10.0,
            'emulationNodeX': {
                'iid': 0,
                'kind': 'user'
            },
            'emulationNodeY': {
                'iid': 1,
                'kind': 'user'
            },
            'id': 'Q29ubmVjdGlvbjow',
            'iid': 0,
            'impairment': {
                'loss': 100
            },
            'interfaceX': {
                'iid': 0
            },
            'interfaceY': {
                'iid': 1
            },
            'kind': 'user'
        }
    }
}

snapshots['TestConnection.test_connection_get_nonexisting 1'] = {
    'data': {
        'node': None
    }
}

snapshots['TestConnection.test_links 1'] = {
    'data': {
        'connections': [
            {
                'connected': True,
                'distance': 10.0,
                'emulationNodeX': {
                    'iid': 0,
                    'kind': 'user'
                },
                'emulationNodeY': {
                    'iid': 1,
                    'kind': 'user'
                },
                'id': 'Q29ubmVjdGlvbjow',
                'iid': 0,
                'impairment': {
                    'loss': 100
                },
                'interfaceX': {
                    'iid': 0
                },
                'interfaceY': {
                    'iid': 1
                },
                'kind': 'user'
            },
            {
                'connected': True,
                'distance': 5.0,
                'emulationNodeX': {
                    'iid': 1,
                    'kind': 'user'
                },
                'emulationNodeY': {
                    'iid': 2,
                    'kind': 'user'
                },
                'id': 'Q29ubmVjdGlvbjox',
                'iid': 1,
                'impairment': {
                    'loss': 50
                },
                'interfaceX': {
                    'iid': 1
                },
                'interfaceY': {
                    'iid': 2
                },
                'kind': 'user'
            }
        ]
    }
}
