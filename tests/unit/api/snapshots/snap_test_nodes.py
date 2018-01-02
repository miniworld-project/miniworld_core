# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestNodes.test_node_links[3] 1'] = {
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
                    'bandwidth': 500,
                    'loss': 0.5
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
                'distance': 10.0,
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
                    'bandwidth': 500,
                    'loss': 0.5
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
