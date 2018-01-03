# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestNodes.test_node_get 1'] = {
    'data': {
        'node': {
            'id': 'RW11bGF0aW9uTm9kZTow',
            'iid': 0
        }
    }
}

snapshots['TestNodes.test_node_get_nonexisting 1'] = {
    'data': {
        'node': None
    }
}

snapshots['TestNodes.test_node_interfaces 1'] = {
    'data': {
        'emulationNodes': [
            {
                'id': 'RW11bGF0aW9uTm9kZTow',
                'iid': 0,
                'interfaces': {
                    'edges': [
                        {
                            'node': {
                                'id': 'SW50ZXJmYWNlOjA=',
                                'iid': 0,
                                'ipv4': '10.0.0.1',
                                'kind': None,
                                'mac': '00:00:00:00:00:00',
                                'name': 'mesh'
                            }
                        }
                    ]
                },
                'virtualization': 'QemuTap'
            },
            {
                'id': 'RW11bGF0aW9uTm9kZTox',
                'iid': 1,
                'interfaces': {
                    'edges': [
                        {
                            'node': {
                                'id': 'SW50ZXJmYWNlOjE=',
                                'iid': 1,
                                'ipv4': '10.0.0.2',
                                'kind': None,
                                'mac': '00:00:00:00:00:01',
                                'name': 'mesh'
                            }
                        }
                    ]
                },
                'virtualization': 'QemuTap'
            }
        ]
    }
}

snapshots['TestNodes.test_node_distances[3] 1'] = {
    'data': {
        'emulationNodes': [
            {
                'distances': {
                    'edges': [
                        {
                            'node': {
                                'distance': 1.0,
                                'emulationNode': {
                                    'id': 'RW11bGF0aW9uTm9kZTox',
                                    'iid': 1
                                }
                            }
                        }
                    ]
                },
                'iid': 0
            },
            {
                'distances': {
                    'edges': [
                        {
                            'node': {
                                'distance': 1.0,
                                'emulationNode': {
                                    'id': 'RW11bGF0aW9uTm9kZToy',
                                    'iid': 2
                                }
                            }
                        }
                    ]
                },
                'iid': 1
            },
            {
                'distances': {
                    'edges': [
                    ]
                },
                'iid': 2
            }
        ]
    }
}
