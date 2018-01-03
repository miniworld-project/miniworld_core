# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestNode.test_node_get 1'] = {
    'data': {
        'node': {
            'id': 'RW11bGF0aW9uTm9kZTow',
            'iid': 0,
            'virtualization': 'QemuTap'
        }
    }
}

snapshots['TestNode.test_node_get_nonexisting 1'] = {
    'data': {
        'node': None
    }
}

snapshots['TestNode.test_nodes 1'] = {
    'data': {
        'emulationNodes': [
            {
                'id': 'RW11bGF0aW9uTm9kZTow',
                'iid': 0,
                'kind': 'user',
                'virtualization': 'QemuTap'
            },
            {
                'id': 'RW11bGF0aW9uTm9kZTox',
                'iid': 1,
                'kind': 'user',
                'virtualization': 'QemuTap'
            },
            {
                'id': 'RW11bGF0aW9uTm9kZToy',
                'iid': 2,
                'kind': 'user',
                'virtualization': 'QemuTap'
            }
        ]
    }
}

snapshots['TestNode.test_interfaces 1'] = {
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
                                'ipv4': '172.16.0.1',
                                'mac': '00:00:00:00:00:01',
                                'name': 'mesh',
                                'nrHostInterface': 0
                            }
                        }
                    ]
                },
                'kind': 'user',
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
                                'ipv4': '172.16.0.2',
                                'mac': '00:00:00:00:00:02',
                                'name': 'mesh',
                                'nrHostInterface': 0
                            }
                        }
                    ]
                },
                'kind': 'user',
                'virtualization': 'QemuTap'
            },
            {
                'id': 'RW11bGF0aW9uTm9kZToy',
                'iid': 2,
                'interfaces': {
                    'edges': [
                        {
                            'node': {
                                'id': 'SW50ZXJmYWNlOjI=',
                                'iid': 2,
                                'ipv4': '172.16.0.3',
                                'mac': '00:00:00:00:00:03',
                                'name': 'mesh',
                                'nrHostInterface': 0
                            }
                        }
                    ]
                },
                'kind': 'user',
                'virtualization': 'QemuTap'
            }
        ]
    }
}
