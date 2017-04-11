import subprocess

import pytest


def test_boot(image_path, runner):
    scenario = {
        "scenario": "acceptance_boot",
        "cnt_nodes": 1,
        "provisioning": {
            "image": image_path,
            "regex_shell_prompt": "root@OpenWrt:/#"
        }
    }

    with runner() as r:
        r.start_scenario(scenario)


def test_snapshot_boot(image_path, runner):
    scenario = {
        "scenario": "acceptance_boot",
        "cnt_nodes": 1,
        "provisioning": {
            "image": image_path,
            "regex_shell_prompt": "root@OpenWrt:/#"
        }
    }
    with runner() as r:
        r.start_scenario(scenario)
        r.check_for_errors()
        subprocess.check_call(['./mw.py', 'stop'])
        r.start_scenario(scenario)


def test_shell_provisioning(image_path, runner):
    scenario = {
        "scenario": "acceptance_boot",
        "cnt_nodes": 1,
        "provisioning": {
            "image": image_path,
            "regex_shell_prompt": "root@OpenWrt:/#"
        },
        "shell": {
            "pre_network_start": {
                "shell_cmds": [
                    "ifconfig"
                ]
            }
        }
    }
    with runner() as r:
        r.start_scenario(scenario)


# def test_address_configurator(runner):
#     pass
#
#
# def test_network_checking(runner):
#     pass
#
#
# def test_wifi_network_backend(runner):
#     pass
#
#
# def test_link_quality_models(runner):
#     pass

# TODO:
# @pytest.mark.parametrize('walk_model', ('RandomWalk', 'MoveOnBigStreets'))
# def test_random_walk(runner, image_path, walk_model):
#     scenario = {
#         "scenario": "acceptance_boot",
#         "walk_model": {
#             "name": walk_model,
#         },
#         "cnt_nodes": 5,
#         "provisioning": {
#             "image": image_path,
#             "regex_shell_prompt": "root@OpenWrt:/#"
#         },
#         "shell": {
#             "pre_network_start": {
#                 "shell_cmds": [
#                     # we need to wait for the NICs to be up
#                     "until ifconfig eth0; do echo -n . && sleep 1; done",
#                     "until ifconfig br-lan ; do echo -n . && sleep 1; done",
#                     "ifconfig eth0 down",
#                     "ifconfig br-lan down",
#                     "brctl delbr br-lan",
#                     "ifconfig eth0 up",
#                     "ifconfig -a",
#                     "brctl show"
#                 ]
#             }
#         }
#     }
#
#     with runner() as r:
#         r.start_scenario(scenario)
#
#         for i in range(10):
#             r.step()
#             # get positions
