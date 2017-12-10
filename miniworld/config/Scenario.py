import logging
import os
from copy import deepcopy

from miniworld.errors import ConfigMalformed
from miniworld.impairment import LinkQualityConstants
from miniworld.model.domain.interface import Interface
from miniworld.singletons import singletons
from miniworld.util import JSONConfig, ConcurrencyUtil
from miniworld.util.JSONConfig import customizable_attrs, json2dict

"""
Provides access to the current scenario.

Examples
--------
>>> import miniworld.Scenario
>>> miniworld.Scenario.scenario_config.get_network_links_nic_prefix()
eth

This prevents cyclic imports, because the module must not be compiled in order to perform the import.

All functions decorated with @attrs can prefer the node customized value by suppylying the keyword "node_id".

>>> {'foo': {'bar': '0'}, 'node_details': {'1': {'foo': {'bar': '2'}}}}
>>> get_bar(node_id = "1")
2
"""


# keeps the scenario config as dict
# scenario_config = {}


def not_null(fun):
    def wrap(*args, **kwargs):
        res = fun(*args, **kwargs)
        if res is None:
            raise Exception("%s(%s, %s) is None!" % (fun, args, kwargs))
        return res

    return wrap


# execution modes
EXECUTE_MODE_BRCTL = "brctl"
EXECUTE_MODE_IPROUTE2 = "iproute2"
EXECUTE_MODE_PYROUTE2 = "pyroute2"

# TODO: use for scenario config expect parameter!
CONNECTION_MODE_SINGLE = "single"


# TODO: is marshmallow sufficient for schema checking?


class ScenarioConfig(JSONConfig.JSONConfig):
    @customizable_attrs("foo", "bar")
    def get_foo(self):
        pass

    # TODO: #40: ADD CAST FUNCTIONS
    @customizable_attrs("cnt_nodes", default=1)
    def get_number_of_nodes(self):
        pass

    def get_local_node_ids(self):

        res = self.get_distributed_server_node_mapping()
        if res:
            return res[self.get_distributed_server_id()]

        else:
            return range(0, self.get_number_of_nodes())

    def get_all_emulation_node_ids(self):
        """
        Returns
        -------
        list<int>
        """
        return range(1, self.get_number_of_nodes() + 1)

    @customizable_attrs("qemu", "qemu_user_addition")
    def get_qemu_user_addition(self):
        pass

    @customizable_attrs("scenario")
    def get_scenario_name(self):
        pass

    #################################################
    # Provisioning
    #################################################

    @customizable_attrs("provisioning", "parallel", default=True)
    def is_parallel_node_starting(self):
        pass

    @customizable_attrs("provisioning", "overlay_images", default=[])
    def get_overlay_images(self):
        pass

    PROVISIONING_BOOT_MODE_SELECTORS = "selectors"
    PROVISIONING_BOOT_MODE_PEXPECT = "pexpect"

    @customizable_attrs("provisioning", "boot_mode", default=PROVISIONING_BOOT_MODE_SELECTORS)
    def get_provisioning_boot_mode(self):
        pass

    def is_provisioning_boot_mode_selectors(self):
        return self.get_provisioning_boot_mode() == self.PROVISIONING_BOOT_MODE_SELECTORS

    def is_provisioning_boot_mode_pexpect(self):
        return self.get_provisioning_boot_mode() == self.PROVISIONING_BOOT_MODE_PEXPECT

    @customizable_attrs("provisioning", "regex_shell_prompt")
    def get_shell_prompt(self, not_null=True):
        pass

    @customizable_attrs("provisioning", "regex_boot_completed")
    def get_signal_boot_completed(self):
        pass

    @customizable_attrs("provisioning", "image", not_null=True)
    def get_path_image(self):
        pass

    # TODO: default val
    @customizable_attrs("network", "links", "model",
                        default="miniworld.impairment.bridged.Range.Range")
    def get_link_quality_model(self):
        pass

    @customizable_attrs("network", "links", "bandwidth",
                        default=LinkQualityConstants.LINK_QUALITY_VAL_BANDWIDTH_UNLIMITED)
    def get_link_bandwidth(self):
        """ default is unlimited bandwidth """
        pass

    #################################################
    # Walk Model
    #################################################

    WALK_MODEL_NAME_ARMA = 'arma'
    WALK_MODEL_NAME_CORE = 'core'
    WALK_MODEL_NAME_RANDOM_WALK = 'RandomWalk'
    WALK_MODEL_NAME_MOVE_ON_BIG_STREETS = 'MoveOnBigStreets'
    WALK_MODEL_NAMES = [WALK_MODEL_NAME_ARMA, WALK_MODEL_NAME_CORE, WALK_MODEL_NAME_RANDOM_WALK,
                        WALK_MODEL_NAME_MOVE_ON_BIG_STREETS]

    # TODO: add ignore case arguemt
    @customizable_attrs("walk_model", "name", expected=WALK_MODEL_NAMES)
    def get_walk_model_name(self):
        pass

    def get_walk_model_arma_filepath(self):
        return os.path.abspath(self._get_walk_model_arma_filepath())

    @customizable_attrs("walk_model", "filepath")
    def _get_walk_model_arma_filepath(self):
        pass

    #################################################
    # Qemu
    #################################################

    @customizable_attrs("qemu", "ram", default="32M")
    def get_qemu_memory(self):
        pass

    def get_qemu_memory_mb(self):
        return int(self.get_qemu_memory().split("M")[0])

    @customizable_attrs("qemu", "nic", "model", default="virtio-net-pci",
                        # TODO:
                        # expected=miniworld.ScenarioConstants.get_nic_models()
                        )
    def get_qemu_nic(self):
        pass

    #################################################
    # Network Link Configuration Connectivity Check
    #################################################

    @customizable_attrs("network", "links", "configuration", "connectivity_check", "enabled", default=True)
    def is_connectivity_check_enabled(self):
        pass

    @customizable_attrs("network", "links", "configuration", "connectivity_check", "timeout", default=60)
    def get_connectivity_check_timeout(self):
        pass

    @customizable_attrs("network", "links", "configuration", "connectivity_check", "cmd",
                        default='ping -n -c 1 -w {timeout} {ip}')
    def get_connectivity_check_cmd(self):
        pass

    #################################################
    # Network Link Configuration
    #################################################

    @customizable_attrs("network", "links", "configuration", "ip_provisioner", "name", expected=["same_subnet"],
                        default=None)
    def get_network_provisioner_name(self):
        pass

    @customizable_attrs("network", "links", "configuration", "auto_ipv4", default=True)
    def is_network_links_auto_ipv4(self):
        pass

    @customizable_attrs("network", "links", "configuration", "ip_provisioner", "base_network_cidr",
                        default=u"10.0.0.0/8")
    def get_network_configuration_ip_provisioner_base_network_cidr(self):
        pass

    @customizable_attrs("network", "links", "configuration", "ip_provisioner", "prefixlen", default=16)
    def get_network_configuration_ip_provisioner_prefixlen(self):
        pass

    @customizable_attrs("network", "links", "configuration", "nic_prefix", default="eth")
    def get_network_links_nic_prefix(self):
        pass

    #################################################
    # Network Backend
    #################################################

    NETWORK_BACKEND_BRIDGED = "bridged"

    # TODO: check for backend names!

    @customizable_attrs("network", "backend", "name",
                        expected=[NETWORK_BACKEND_BRIDGED],
                        default=NETWORK_BACKEND_BRIDGED)
    def get_network_backend(self):
        pass

    @customizable_attrs("network", "backend", "execution_mode", "parallel", default=True)
    def is_network_backend_parallel(self):
        pass

    def get_network_backend_cnt_minions(self):
        if singletons.scenario_config.is_network_backend_parallel():
            return ConcurrencyUtil.cpu_count()
        else:
            return 1

    @customizable_attrs("network", "backend", "event_hook_script", default=None)
    def get_network_backend_event_hook_script(self):
        pass

    #################################################
    # Network Backend Bridged Specific
    #################################################

    @customizable_attrs("network", "backend", "connection_mode", default="single",
                        expected=["single"])
    def get_network_backend_bridged_connection_mode(self):
        pass

    # other execution modes may get dropped in the future
    EXECUTION_MODES = ["iproute2"]  # , "pyroute2", "brctl"]

    @customizable_attrs("network", "backend", "execution_mode", "name", default="iproute2", expected=EXECUTION_MODES)
    def get_network_backend_bridged_execution_mode(self):
        pass

    @customizable_attrs("network", "backend", "execution_mode", "batch", default=True)
    def is_network_backend_bridged_execution_mode_batch(self):
        pass

    def is_network_backend_bridged_execution_mode_brctl(self):
        return singletons.scenario_config.get_network_backend_bridged_execution_mode() == EXECUTE_MODE_BRCTL

    def is_network_backend_bridged_execution_mode_iproute2(self):
        return self.get_network_backend_bridged_execution_mode() == EXECUTE_MODE_IPROUTE2

    def is_network_backend_bridged_execution_mode_pyroute2(self):
        return self.get_network_backend_bridged_execution_mode() == EXECUTE_MODE_PYROUTE2

    def is_network_backend_bridged_connection_mode_single(self):
        return self.get_network_backend_bridged_connection_mode() == CONNECTION_MODE_SINGLE

    def is_network_backend_bridged_connection_mode_set(self):
        return self.get_network_backend_bridged_connection_mode() is not None

    @customizable_attrs("network", "backend", "execution_mode", "one_shell_call", default=True)
    def is_network_backend_bridged_execution_mode_one_shell_call(self):
        pass

    # TODO: MOVE TO GENERIC SECTION!
    @json2dict
    @customizable_attrs("network", "backend", "tunnel_endpoints")
    def get_network_backend_bridged_tunnel_endpoints(self):
        pass

    def set_network_backend_bridged_tunnel_endpoints(self, tunnel_endpoints):
        """

        Returns
        -------
        tunnel_endpoints : dict<int, str>
            For each server the tunnel ip address.
        """

        # TODO: this is a quickfixi
        self.init_keys(["network", "backend", "tunnel_endpoints"])
        self.data["network"]["backend"]["tunnel_endpoints"] = tunnel_endpoints

    def init_keys(self, keys):
        d = self.data
        for key in keys:
            if d.get(key) is None:
                d[key] = {}
            d = d[key]

    KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_VLAN = "vlan"
    KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_GRETAP = "gretap"
    KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_VXLAN = "vxlan"

    """ distributed mode """

    @customizable_attrs("network", "backend", "distributed_mode",
                        expected=[KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_VLAN,
                                  KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_GRETAP,
                                  KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_VXLAN],
                        default=KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_GRETAP)
    def get_network_backend_bridged_distributed_mode(self):
        pass

    def is_network_backend_bridged_distributed_mode_vlan(self):
        return self.get_network_backend_bridged_distributed_mode() == self.KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_VLAN

    def is_network_backend_bridged_distributed_mode_gretap(self):
        return self.get_network_backend_bridged_distributed_mode() == self.KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_GRETAP

    def is_network_backend_bridged_distributed_mode_vxlan(self):
        return self.get_network_backend_bridged_distributed_mode() == self.KEY_NETWORK_BACKEND_BRIDGED_DISTRIBUTED_MODE_VXLAN

    #################################################
    # Network
    #################################################

    @customizable_attrs("network", "links", "interfaces", default=[Interface.InterfaceType.mesh.value])
    def get_interfaces(self):
        pass

    def any_hub_interface(self) -> bool:
        return Interface.InterfaceType.hub.value in self.get_interfaces()

    @customizable_attrs("network", "core", "topologies")
    def get_core_scenarios(self):
        pass

    CORE_MODE_LAN = "lan"
    CORE_MODE_WIFI = "wifi"

    @customizable_attrs("network", "core", "mode", default=CORE_MODE_WIFI)
    def get_core_mode(self):
        pass

    def is_core_mode_lan(self):
        return self.get_core_mode() == self.CORE_MODE_LAN

    def is_core_mode_wifi(self):
        return self.get_core_mode() == self.CORE_MODE_WIFI

    @customizable_attrs("network", "core", "loop", default=False)
    def is_core_loop(self):
        pass

    #################################################
    # Shell
    #################################################

    def get_all_shell_commands_pre_network_start(self, node_id=None):
        """
        See :py:meth:`._get_all_shell_commands`
        """
        return self._get_all_shell_commands(self._get_shell_commands_path_pre_network_start(node_id=node_id),
                                            self._get_shell_commands_pre_network_start(node_id=node_id))

    def get_all_shell_commands_post_network_start(self, node_id=None):
        """
        See :py:meth:`._get_all_shell_commands`
        """
        return self._get_all_shell_commands(self._get_shell_commands_path_post_network_start(node_id=node_id),
                                            self._get_shell_commands_post_network_start(node_id=node_id))

    # def get_all_shell_commands_before_snapshot(self, node_id = None):
    #     """
    #     See :py:meth:`._get_all_shell_commands`
    #     """
    #     return self._get_all_shell_commands(self._get_shell_commands_path_before_snapshot(node_id = node_id),
    #                                         self._get_shell_commands_before_snapshot(node_id = node_id))

    def _get_all_shell_commands(self, shell_commands_path, shell_commands_list):
        """
        Get the shell commands.
        Concatenates the commands from the shell script to the direct commands.
        (shell_cmds_path + shell_cmds)

        Parameters
        ----------
        shell_commands_path : str
        shell_commands_list : list<str>

        Raises
        ------
        ConfigMalformed

        Returns
        -------
        str
            The commands as string
        """

        shell_commands_from_path = ""
        shell_commands_from_config = ''

        # convert list of strings to string
        if shell_commands_list:
            shell_commands_from_config = '\n'.join(shell_commands_list)

        if shell_commands_path:
            try:
                with open(shell_commands_path, "r") as f:
                    shell_commands_from_path = f.read()
            except IOError as e:
                raise ConfigMalformed("The path ('%s') to the shell script does not exist!" % shell_commands_path)
        return ('%s\n\n%s' % (shell_commands_from_path, shell_commands_from_config)).strip()

    @customizable_attrs("provisioning", "shell", "pre_network_start", "shell_cmds")
    def _get_shell_commands_pre_network_start(self):
        pass

    @customizable_attrs("provisioning", "shell", "pre_network_start", "shell_cmd_file_path")
    def _get_shell_commands_path_pre_network_start(self):
        pass

    @customizable_attrs("provisioning", "shell", "post_network_start", "shell_cmds")
    def _get_shell_commands_post_network_start(self):
        pass

    @customizable_attrs("provisioning", "shell", "post_network_start", "shell_cmd_file_path")
    def _get_shell_commands_path_post_network_start(self):
        pass

        # @customizable_attrs("provisioning", "shell", "before_snapshot", "shell_cmds")
        # def _get_shell_commands_before_snapshot(self):
        #     pass
        #
        #
        # @customizable_attrs("provisioning", "shell", "before_snapshot", "shell_cmd_file_path")
        # def _get_shell_commands_path_before_snapshot(self):
        #     pass
        #

    #################################################
    # Distributed Settings
    #################################################

    def create_distributed_section(self):
        if "distributed" not in self.data:
            self.data["distributed"] = {}

    @json2dict
    @customizable_attrs("distributed", "server_node_mapping", default=None)
    def get_distributed_server_node_mapping(self):
        pass

    def get_distributed_server_ids(self):
        return list(self.get_distributed_server_node_mapping().keys())

    def set_distributed_server_node_mapping(self, server_node_mapping):
        """
        Parameters
        ----------
        server_node_mapping : dict

        """
        self.create_distributed_section()

        self.data["distributed"]["server_node_mapping"] = server_node_mapping

    @customizable_attrs("distributed", "server_id")
    def get_distributed_server_id(self):
        pass

    def set_distributed_server_id(self, server_id):
        self.create_distributed_section()
        self.data["distributed"]["server_id"] = server_id


#################################################
###
#################################################

scenario_config = ScenarioConfig()


###############################################
# Scenario config file setter
###############################################


def set_scenario_config(*args, **kwargs):
    """ Set the scenario singletons.config.

    Returns
    -------
    dict
        The config as JSON.
    """

    _config = JSONConfig.read_json_config(*args, **kwargs)
    logging.getLogger().info("settting scenario config file '%s'", *args)
    singletons.scenario_config = ScenarioConfig()
    singletons.scenario_config.data = deepcopy(_config)
    return _config


###############################################
# Scenario access API
###############################################


if __name__ == '__main__':
    # sc = ScenarioConfig()
    # sc.config = {'foo': {'bar': '0'}, 'node_details': {'1': {'foo': {'bar': '2'}}}}
    # print sc.get_foo(node_id = 1)
    # print sc.get_qemu_user_addition()

    sc = ScenarioConfig()
    sc.config = {
        "network": {
            "core_scenarios": {
                "10": "MiniWorld_Images/serval_paper/chain3.xml",
                "15": "MiniWorld_Images/serval_paper/chain3.xml",
                "20": "MiniWorld_Images/serval_paper/chain3.xml"
            }
        }
    }
    print(sc.get_core_scenarios())
