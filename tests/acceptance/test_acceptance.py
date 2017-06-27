from subprocess import CalledProcessError

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
        r.run_mwcli_command(['stop'])
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


@pytest.fixture(scope='session')
def invalid_image(tmpdir_factory):
    image_path = str(tmpdir_factory.getbasetemp().join('1_byte_image.qcow2'))
    with open(image_path, 'w') as f:
        f.write('\\x0\\x1')

    return image_path


@pytest.mark.skip(reason='Requires server reload config to use the smallest possible timeout')
def test_invalid_image_boot_mode_shell_prompt_timeout_works(runner, invalid_image):
    scenario = {
        "scenario": "acceptance_boot",
        "cnt_nodes": 1,
        "provisioning": {
            "image": invalid_image,
            "regex_shell_prompt": "root@OpenWrt:/#",
        },
        "shell": {
            "pre_network_start": {
                "shell_cmds": [
                    "ifconfig"
                ]
            }
        }
    }
    # TODO: check also that a timeout exception is thrown, but how
    with pytest.raises(CalledProcessError):
        with runner() as r:
            r.start_scenario(scenario)


@pytest.mark.skip(reason='Requires server reload config to use the smallest possible timeout')
def test_invalid_image_boot_mode_boot_prompt_timeout_works(runner, invalid_image):
    scenario = {
        "scenario": "acceptance_boot",
        "cnt_nodes": 1,
        "provisioning": {
            "image": invalid_image,
            "regex_shell_prompt": "root@OpenWrt:/#",
            "regex_boot_completed": "procd: - init complete -.*",
        },
        "shell": {
            "pre_network_start": {
                "shell_cmds": [
                    "ifconfig"
                ]
            }
        }
    }
    # TODO: check also that a timeout exception is thrown, but how
    with pytest.raises(CalledProcessError):
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

@pytest.mark.skip(reason='how to test? we want a scenario where nodes are connected')
@pytest.mark.parametrize('walk_model', ('RandomWalk', 'MoveOnBigStreets'))
def test_random_walk(runner, image_path, walk_model):
    scenario = {
        "scenario": "acceptance_boot",
        "walk_model": {
            "name": walk_model,
        },
        # TODO:
        "cnt_nodes": 2,
        "provisioning": {
            "image": image_path,
            "regex_shell_prompt": "root@OpenWrt:/#"
        },
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
    }

    with runner() as r:
        r.start_scenario(scenario)

        for i in range(10):
            r.step()
            # get positions
            print(r.get_connections())
            print(r.get_distances())
