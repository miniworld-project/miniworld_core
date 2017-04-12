from functools import partial

import os
import pytest

from miniworld import Scenario


# TODO: theoretically we need to manually check network connectivity since network checking code may not run at all :/
def _create_scenarios():
    for connection_mode in [Scenario.CONNECTION_MODE_SINGLE, Scenario.CONNECTION_MODE_MULTI]:
        for execution_mode in Scenario.ScenarioConfig.EXECUTION_MODES:
            def fun(connection_mode, execution_mode, image_path, request, core_topologies_dir):
                return {
                    "scenario": "acceptance_network_switching",
                    "walk_model": {
                        "name": "core"
                    },
                    "cnt_nodes": 5,
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
                                    "brctl delbr br-lan",
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
                            "connection_mode": connection_mode,
                            "execution_mode": {
                                "name": execution_mode,
                            }
                        },
                        "links": {
                            "model": "miniworld.model.network.linkqualitymodels.LinkQualityModelRange.LinkQualityModelRange"
                        },
                        "core": {
                            "topologies": [
                                [0, os.path.join(core_topologies_dir, "chain5.xml")],
                                [0, os.path.join(core_topologies_dir, "clique5.xml")],
                                [0, os.path.join(core_topologies_dir, "cycle5.xml")],
                                [0, os.path.join(core_topologies_dir, "star5.xml")],
                                [0, os.path.join(core_topologies_dir, "wheel5.xml")],
                            ],
                            "mode": "lan"
                        }
                    }
                }

            # we need to inject the environment into the function
            yield partial(fun, connection_mode, execution_mode), '{}_{}'.format(connection_mode, execution_mode)


@pytest.mark.parametrize('scenario_fun', **dict(zip(['argvalues', 'ids'], zip(*_create_scenarios()))))
def test_network_switching(scenario_fun, runner, image_path, request, core_topologies_dir):
    scenario = scenario_fun(image_path, request, core_topologies_dir)

    with runner() as r:
        r.start_scenario(scenario)

        for i in range(len(scenario['network']['core']['topologies'])):
            r.step()
