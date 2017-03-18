import os

import subprocess


def test_boot(server, runner):
    scenario = {
        "scenario": "acceptance_boot",
        "cnt_nodes": 1,
        "provisioning": {
            "image": os.path.abspath("tests/acceptance/openwrt-15.05.1-x86-kvm_guest-combined-ext4.img"),
            "regex_shell_prompt": "root@OpenWrt:/#"
        }
    }
    runner.start_scenario(scenario)


def test_snapshot_boot(server, runner):
    scenario = {
        "scenario": "acceptance_boot",
        "cnt_nodes": 1,
        "provisioning": {
            "image": os.path.abspath("tests/acceptance/openwrt-15.05.1-x86-kvm_guest-combined-ext4.img"),
            "regex_shell_prompt": "root@OpenWrt:/#"
        }
    }
    runner.start_scenario(scenario)
    runner.check_for_errors()
    subprocess.check_call(['./mw.py', 'stop'])
    runner.start_scenario(scenario)


def test_shell_provisioning(server, runner):
    scenario = {
        "scenario": "acceptance_boot",
        "cnt_nodes": 1,
        "provisioning": {
            "image": os.path.abspath("tests/acceptance/openwrt-15.05.1-x86-kvm_guest-combined-ext4.img"),
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
    runner.start_scenario(scenario)


# def test_network_switching(server):
#     pass
#
#
# def test_address_configurator(server):
#     pass
#
#
# def test_network_checking(server):
#     pass
#
#
# def test_wifi_network_backend(server):
#     pass
#
#
# def test_link_quality_models(server):
#     pass
