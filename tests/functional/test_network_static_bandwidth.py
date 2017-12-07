import os

import pytest

from tests.acceptance.conftest import *


@pytest.fixture(scope='module')
def runner(tmpdir_factory, image_path, request, config_path, core_topologies_dir):
    runner = create_runner(tmpdir_factory, request, config_path)

    scenario = {
        "scenario": "",
        "walk_model": {
            "name": "core"
        },
        "cnt_nodes": 3,
        "provisioning": {
            "image": image_path,
            "regex_shell_prompt": "root@OpenWrt:/#",
            "shell": {
                "pre_network_start": {
                    "shell_cmds": [
                        # we need to wait for the NICs to be up
                        "until ifconfig eth0; do echo -n . && sleep 1; done",
                        "until ifconfig br-lan ; do echo -n . && sleep 1; done",
                        "ifconfig eth0 down",
                        "ifconfig br-lan down",
                        "brctl delif br-lan eth0",
                        "ifconfig eth0 up",
                        "ifconfig -a",
                        "brctl show"
                    ]
                }
            }
        },
        "network": {
            "backend": {
                "name": "bridged",
                "connection_mode": "single",
                "execution_mode": {
                    "name": "iproute2",
                    "parallel": False,
                    "batch": False,
                    "one_shell_call": False
                }
            },
            "links": {
                "bandwidth": 55296000
            },
            "core": {
                "topologies": [
                    [0, os.path.join(core_topologies_dir, "chain5.xml")]
                ],
                "mode": "lan"
            }
        }
    }

    with runner() as r:
        yield r, scenario


@pytest.fixture
def snapshot_runner(runner):
    runner, scenario = runner
    runner.start_scenario(scenario, force_snapshot_boot=True)
    yield runner
    runner.stop(hard=False)


class TestAPI:
    def test_node_get(self, snapshot_runner, client, snapshot):
        res = client.execute('''
        {
          node(id: "RW11bGF0aW9uTm9kZTow") {
            id
            ... on EmulationNode {
              id
              iid
              virtualization
            }
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_node_get_nonexisting(self, snapshot_runner, client, snapshot):
        res = client.execute('''
        {
          node(id: "RW11bGF0aW9uTm9kZToxMDAwMAo=") {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_connection_get(self, snapshot_runner, client, snapshot):
        for _ in range(2):
            res = client.execute('''
            {
              node(id: "Q29ubmVjdGlvbjowCg==") {
                ... on Connection {
                    id
                    iid
                    kind
                    impairment
                    connected
                    distance
                    emulationNodeX { iid kind }
                    emulationNodeY { iid kind }
                    interfaceX { iid }
                    interfaceY { iid }
                }
              }
            }
            ''')
            snapshot.assert_match(res)
            snapshot_runner.step()

    def test_connection_get_nonexisting(self, snapshot_runner, client, snapshot):
        res = client.execute('''
        {
          node(id: "Q29ubmVjdGlvbjoxMDAwMAo=") {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_interface_get(self, snapshot_runner, client, snapshot):
        res = client.execute('''
        {
          node(id: "SW50ZXJmYWNlOjAK") {
            id
            ... on Interface {
              iid
              id
              name
              mac
              ipv4
              nrHostInterface
            }
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_interface_get_non_existing(self, snapshot_runner, client, snapshot):
        res = client.execute('''
        {
          node(id: "SW50ZXJmYWNlOjEwMDAwCg==") {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_nodes(self, snapshot_runner, client, snapshot):
        res = client.execute('''
        {
          emulationNodes {
            id
            iid
            kind
            virtualization
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_interfaces(self, snapshot_runner, client, snapshot):
        res = client.execute('''
    {
      emulationNodes {
        id
        iid
        kind
        virtualization
        interfaces {
          edges {
            node {
              iid
              id
              name
              mac
              ipv4
              nrHostInterface
            }
          }
        }
      }
    }
    ''')
        snapshot.assert_match(res)

    # TODO: test for all steps()
    def test_links(self, snapshot_runner, client, snapshot):
        for _ in range(2):
            res = client.execute('''
            {
              emulationNodes {
                id
                iid
                kind
                virtualization
                links {
                  edges {
                    node {
                    id
                    iid
                    kind
                    impairment
                    connected
                    distance
                    emulationNodeX { iid kind }
                    emulationNodeY { iid kind }
                    interfaceX { iid }
                    interfaceY { iid }
                    }
                  }
                }
              }
            }
            ''')
            snapshot.assert_match(res)
            snapshot_runner.step()

# def test_info_links(snapshot_runner):
#     links_mgmt = {
#         # no link impairment for management network
#         u"('1', 'mgmt')": None,
#         u"('2', 'mgmt')": None,
#         u"('3', 'mgmt')": None,
#     }
#     links_full = deepcopy(links_mgmt)
#     # static link impairment here
#     links_full.update({
#         u"('1', '2')": {u'loss': u'0', u'bandwidth': u'55296000'},
#         u"('2', '3')": {u'loss': u'0', u'bandwidth': u'55296000'},
#     })
#
#     res = snapshot_runner.get_links()
#     assert res == links_mgmt
#
#     snapshot_runner.step()
#     res = snapshot_runner.get_links()
#     assert res == links_full
#
#
# def test_info_distances(snapshot_runner, client, snapshot):
#     res = client.execute('''
# {
#   emulationNodes {
#     iid
#     distances {
#       edges {
#         node {
#           distance
#           emulationNode {
#             id
#             iid
#           }
#         }
#       }
#     }
#   }
# }
# ''')
#     snapshot.assert_match(res)
#     assert False
#     return
#     distances = {
#         "('1', '2')": "1",
#         "('1', '3')": "-1",
#         "('2', '3')": "1",
#     }
#
#     res = snapshot_runner.get_distances()
#     assert res == {}
#
#     snapshot_runner.step()
#     res = snapshot_runner.get_distances()
#     assert res == distances
#
#
# def test_info_addr(snapshot_runner):
#     snapshot_runner.step()
#     print(snapshot_runner.get_addr())
