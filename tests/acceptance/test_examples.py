from typing import Dict

from miniworld.util import JSONConfig


# TODO: examples/batman_adv.json, problem is configurator
def test_snapshot_boot_single_scenario(image_path, runner):
    with runner() as r:
        for _ in range(5):
            scenario = JSONConfig.read_json_config('examples/nb_bridged_lan.json')  # type: Dict
            r.start_scenario(scenario)
            r.step()
            r.step()
            r.stop(hard=False)

# TODO: test stop/step
def test_snapshot_boot_multiple_scenarios(image_path, runner):
    with runner() as r:
        scenario = JSONConfig.read_json_config('examples/batman_adv.json')  # type: Dict
        r.start_scenario(scenario)
        for _ in range(5):
            r.step()
        r.stop(hard=False)

        scenario = JSONConfig.read_json_config('examples/nb_bridged_lan.json')  # type: Dict
        r.start_scenario(scenario)
        for _ in range(5):
            r.step()
        r.stop(hard=False)

        scenario = JSONConfig.read_json_config('examples/nb_bridged_wifi.json')  # type: Dict
        r.start_scenario(scenario)
        for _ in range(5):
            r.step()
        r.stop(hard=False)
