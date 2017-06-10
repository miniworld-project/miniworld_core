import argparse
import json
import time
import xmlrpc
from collections import OrderedDict
from threading import Thread

from miniworld import Scenario, Config
from miniworld import log
from miniworld.errors import ConfigMalformed
from miniworld.util import JSONConfig, DictUtil

__author__ = "Nils Schmidt"


'''
This is a base `ArgumentParser` which reads and expects a scenario config file.
'''
# TODO: REMOVE
scenario_config_parser = argparse.ArgumentParser(add_help=False)
scenario_config_parser.add_argument('scenario_config', help='The scenario description (Path to *.json)')
scenario_config_parser.add_argument('--customize-scenario', "-cs", default='{}', help='Customize the scenario by supplying a json string which gets updates the scenario file (in memory)')

# TODO: use
rpc_parser = argparse.ArgumentParser(add_help=False)
def get_default_rpc_addr():
    try:
        Config.set_global_config(Config.PATH_GLOBAL_CONFIG)
        return Config.config.get_server_addr()
    except Exception:
        return "127.0.0.1"
rpc_parser.add_argument("--addr", default=get_default_rpc_addr(), help="The address of the rpc server, default is: '%(default)s'")

def parse_scenario_config(scenario_config = None, customize_scenario = None):
    '''

    Parameters
    ----------
    scenario_config : optional (default value is taken from the `scenario_config_parser`)
    customize_scenario : optional (default value is taken from the `scenario_config_parser`)

    Returns
    -------
    str, str, str
    '''
    def parse_args():
        return scenario_config_parser.parse_known_args()[0]

    if customize_scenario is None:
        customize_scenario = parse_args().customize_scenario
    if scenario_config is None:
        scenario_config = parse_args().scenario_config

    # set scenario config
    if scenario_config:
        scenario_config = JSONConfig.read_json_config(scenario_config)

    if customize_scenario:
        try:
            custom_scenario = JSONConfig.read_json_config(customize_scenario, raw = True)
            # TODO: #61
            DictUtil.merge_recursive_in_place(scenario_config, custom_scenario)
        except ValueError as e:
            log.exception(e)
            raise ConfigMalformed("The supplied custom json scenario is invalid!")

    scenario_config_json = json.dumps(scenario_config)
    Scenario.set_scenario_config(scenario_config_json, raw = True)
    return scenario_config, custom_scenario, scenario_config_json

CLI_REFRESH_RATE = 0.25
def start_scenario(scenario_config, autostepping=None, blocking=True, connection=None):
    '''

    Parameters
    ----------
    scenario_config
    blocking

    Returns
    -------
    '''

    from miniworld.management.events.CLIEventDisplay import CLIEventDisplay

    if connection is None:
        con_progress = xmlrpc.ServerProxy('http://localhost:5001/RPC2')
        con = xmlrpc.ServerProxy('http://localhost:5001/RPC2')
    else:
        con_progress = con = connection

    cli_display = CLIEventDisplay()

    def show_progress():
        while 1:
            progress_dict = OrderedDict(con_progress.get_progress(False))
            if progress_dict is not None:

                cli_display.print_progress(progress_dict)
                if cli_display.is_finished(progress_dict):

                    t2 = time.time()
                    log.info("took '%s'", t2 - t1)
                    log.info("simulation started ...")
                    return

            time.sleep(CLI_REFRESH_RATE)
    t = None
    # async
    if not blocking:
        t = Thread(target=show_progress)
        t.daemon = True
        t1 = time.time()

    con.simulation_start(scenario_config, autostepping, blocking)
    if not blocking:
        t.start()

    if not blocking:
        while 1:
            t.join(0.5)
            if not t.isAlive():
                return

    return con