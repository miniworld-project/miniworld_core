from copy import deepcopy

from miniworld.util import JSONConfig
from miniworld.util.JSONConfig import customizable_attrs, arg2float

__author__ = 'Nils Schmidt'

'''
Contains the global config and config functions.
'''


class GlobalConfig(JSONConfig.JSONConfig):
    '''
    Attributes
    ----------
    is_mode_distributed : bool
    '''

    def __init__(self):
        super(GlobalConfig, self).__init__()

    @customizable_attrs("server", "address", default="localhost")
    def get_server_addr(self):
        pass

    @customizable_attrs("distributed", "use")
    def is_mode_distributed(self):
        pass

    @customizable_attrs("distributed", "cnt_servers")
    def get_mode_distributed_get_cnt_servers(self):
        pass

    # TODO: generic repl timeout?
    @customizable_attrs("provisioning", "boot_wait_timeout", default=300)
    def get_repl_timeout(self):
        pass

    @customizable_attrs("management", "device", default="mgmt")
    def get_bridge_tap_name(self):
        pass

    @customizable_attrs("ramdisk", default=False)
    def is_ramdisk_enabled(self):
        pass

    @customizable_attrs("qemu", "snapshot_boot", default=True)
    def is_qemu_snapshot_boot(self):
        pass

    @customizable_attrs("management", "use", default=False)
    def is_management_switch_enabled(self):
        pass

    @customizable_attrs("logging", "debug", default=False)
    def is_debug(self):
        pass

    @customizable_attrs("logging", "log_provisioning", default=False)
    def is_log_provisioning(self):
        pass

    @customizable_attrs("logging", "log_cleanup", default=False)
    def is_log_cleanup(self):
        pass

    @customizable_attrs("logging", "level", default="INFO")
    def get_log_level(self):
        pass

    @customizable_attrs("network_switching_threads", default=100)
    def get_network_switching_threads(self):
        pass

    ##############################################
    def set_is_coordinator(self, bool):
        self['coordinator'] = bool

    def is_coordinator(self):
        return self.data.get('coordinator', False)

    ###############################################
    ### Protocol
    ###############################################

    PROTOCOL_MSG_PACK = "msgpack"
    PROTOCOL_JSON = "json"

    PROTOCOL_ZMQ_MODE_P2P = "p2p"
    PROTOCOL_ZMQ_MODE_MCAST = "multicast"

    @customizable_attrs("network", "protocol", "name",
                        expected=[PROTOCOL_JSON, PROTOCOL_MSG_PACK],
                        default=PROTOCOL_MSG_PACK)
    def get_protocol(self):
        pass

    def is_protocol_json(self):
        return self.get_protocol() == self.PROTOCOL_JSON

    def is_protocol_msgpack(self):
        return self.get_protocol() == self.PROTOCOL_MSG_PACK

    @customizable_attrs("network", "protocol", "zeromq", "mode", default=PROTOCOL_ZMQ_MODE_MCAST)
    def get_protocol_zeromq_mode(self):
        pass

    def is_protocol_zeromq_mode_p2p(self):
        return self.get_protocol_zeromq_mode() == self.PROTOCOL_ZMQ_MODE_P2P

    def is_protocol_zeromq_mode_mcast(self):
        return self.get_protocol_zeromq_mode() == self.PROTOCOL_ZMQ_MODE_MCAST

    @arg2float
    @customizable_attrs("simulation", "time_step", default=1.0)
    def get_time_step(self):
        pass

    # @customizable_attrs("network", "protocol", "zeromq", "precalculate_distance_matrix", default=False)
    # def is_precalculate_distance_matrix(self):
    #     pass

    @customizable_attrs("network", "protocol", "zeromq", "publish_only_new_distance_matrices", default=True)
    def is_publish_only_new_distance_matrices(self):
        pass

    @customizable_attrs("network", "protocol", "zeromq", "publish_individual_distance_matrices", default=False)
    def is_publish_individual_distance_matrices(self):
        pass

    DISTRIBUTD_SCHEDULER_EQUAL = "equal"
    DISTRIBUTD_SCHEDULER_SCORE = "score"

    @customizable_attrs("distributed", "scheduler",
                        expected=[DISTRIBUTD_SCHEDULER_EQUAL, DISTRIBUTD_SCHEDULER_SCORE],
                        default=DISTRIBUTD_SCHEDULER_SCORE)
    def get_distributed_scheduler(self):
        pass

    def is_distributed_scheduler_score(self):
        return self.get_distributed_scheduler() == self.DISTRIBUTD_SCHEDULER_SCORE

    def is_distributed_scheduler_equal(self):
        return self.get_distributed_scheduler() == self.DISTRIBUTD_SCHEDULER_EQUAL


###############################################
###
###############################################


config = GlobalConfig()
PATH_GLOBAL_CONFIG = "config.json"


###############################################
### Helper
###############################################

def set_global_config(*args, **kwargs):
    ''' Set the global config.

    Returns
    -------
    dict
        The config as JSON.
    '''

    _config = JSONConfig.read_json_config(*args, **kwargs)
    from miniworld.log import log
    log.info("setting global config file '%s'", *args, **kwargs)
    config.data = deepcopy(_config)
    return _config
