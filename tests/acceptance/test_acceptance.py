import subprocess


def test_boot(image_path, runner):
    scenario = {
        "scenario": "acceptance_boot",
        "walk_model": {
            "name": "core"
        },
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
        "walk_model": {
            "name": "core"
        },
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
        "walk_model": {
            "name": "core"
        },
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
