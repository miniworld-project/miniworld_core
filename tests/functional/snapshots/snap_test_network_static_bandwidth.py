# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestAPI.test_node_get 1'] = {
    'data': {
        'node': {
            'id': 'RW11bGF0aW9uTm9kZTow',
            'iid': 0,
            'virtualization': 'QemuTap'
        }
    }
}

snapshots['TestAPI.test_node_get_nonexisting 1'] = {
    'data': {
        'node': None
    }
}

snapshots['TestAPI.test_connection_get 1'] = {
    'data': {
        'node': None
    }
}

snapshots['TestAPI.test_connection_get 2'] = {
    'data': {
        'node': {
            'connected': True,
            'distance': 1.0,
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
                'bandwidth': 55296000,
                'loss': 0
            },
            'interfaceX': {
                'iid': 0
            },
            'interfaceY': {
                'iid': 2
            },
            'kind': 'user'
        }
    }
}

snapshots['TestAPI.test_connection_get_nonexisting 1'] = {
    'data': {
        'node': None
    }
}

snapshots['TestAPI.test_interface_get 1'] = {
    'data': {
        'node': {
            'id': 'SW50ZXJmYWNlOjA=',
            'iid': 0,
            'ipv4': '10.0.0.1',
            'mac': None,
            'name': 'mesh',
            'nrHostInterface': 0
        }
    }
}

snapshots['TestAPI.test_interface_get_non_existing 1'] = {
    'data': {
        'node': None
    }
}

snapshots['TestAPI.test_nodes 1'] = {
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
            },
            {
                'id': 'RW11bGF0aW9uTm9kZToz',
                'iid': 3,
                'kind': 'mgmt',
                'virtualization': 'QemuTap'
            }
        ]
    }
}

snapshots['TestAPI.test_interfaces 1'] = {
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
                                'mac': None,
                                'name': 'mesh',
                                'nrHostInterface': 0
                            }
                        },
                        {
                            'node': {
                                'id': 'SW50ZXJmYWNlOjE=',
                                'iid': 1,
                                'ipv4': None,
                                'mac': None,
                                'name': 'management',
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
                                'id': 'SW50ZXJmYWNlOjI=',
                                'iid': 2,
                                'ipv4': '10.0.0.2',
                                'mac': None,
                                'name': 'mesh',
                                'nrHostInterface': 0
                            }
                        },
                        {
                            'node': {
                                'id': 'SW50ZXJmYWNlOjM=',
                                'iid': 3,
                                'ipv4': None,
                                'mac': None,
                                'name': 'management',
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
                                'id': 'SW50ZXJmYWNlOjQ=',
                                'iid': 4,
                                'ipv4': '10.0.0.3',
                                'mac': None,
                                'name': 'mesh',
                                'nrHostInterface': 0
                            }
                        },
                        {
                            'node': {
                                'id': 'SW50ZXJmYWNlOjU=',
                                'iid': 5,
                                'ipv4': None,
                                'mac': None,
                                'name': 'management',
                                'nrHostInterface': 0
                            }
                        }
                    ]
                },
                'kind': 'user',
                'virtualization': 'QemuTap'
            },
            {
                'id': 'RW11bGF0aW9uTm9kZToz',
                'iid': 3,
                'interfaces': {
                    'edges': [
                        {
                            'node': {
                                'id': 'SW50ZXJmYWNlOjY=',
                                'iid': 6,
                                'ipv4': None,
                                'mac': None,
                                'name': 'management',
                                'nrHostInterface': 0
                            }
                        }
                    ]
                },
                'kind': 'mgmt',
                'virtualization': 'QemuTap'
            }
        ]
    }
}

snapshots['TestAPI.test_links 1'] = {
    'data': {
        'connections': [
        ]
    }
}

snapshots['TestAPI.test_links 2'] = {
    'data': {
        'connections': [
            {
                'connected': True,
                'distance': 1.0,
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
                    'bandwidth': 55296000,
                    'loss': 0
                },
                'interfaceX': {
                    'iid': 0
                },
                'interfaceY': {
                    'iid': 2
                },
                'kind': 'user'
            },
            {
                'connected': True,
                'distance': 1.0,
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
                    'bandwidth': 55296000,
                    'loss': 0
                },
                'interfaceX': {
                    'iid': 2
                },
                'interfaceY': {
                    'iid': 4
                },
                'kind': 'user'
            }
        ]
    }
}
