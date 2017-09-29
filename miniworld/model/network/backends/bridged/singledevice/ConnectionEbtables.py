from collections import defaultdict

from miniworld import log
from miniworld.Scenario import scenario_config
from miniworld.model.singletons.Singletons import singletons
from miniworld.model.network.backends.bridged.Connection import ConnectionDummy
from miniworld.util import PathUtil


def ConnectionEbtables():
    class ConnectionEbtables(ConnectionDummy()):
        """
        Ebtables setup example
        ----------------------
        # flush rules
        ebtables -F
        # set default policy
        ebtables -P FORWARD DROP

        # add new chain
        ebtables -N miniworld_tap -P ACCEPT
        # redirect to bridge chain
        ebtables -A FORWARD --logical-in miniworld_tap  -j br1
        # allow traffic between the two peers/interfaces
        ebtables (-t filter) -I FORWARD -i tap_00001_2 -o tap_00002_2 -j ACCEPT
        ebtables -I FORWARD -i tap_00002_2 -o tap_00001_2 -j ACCEPT

        Atomic version
        --------------
        ebtables --atomic-file ebtables_commit --atomic-save
        export EBTABLES_ATOMIC_FILE=ebtables_commit
        ebtables -I FORWARD -i tap_00003_2 -o tap_00002_2 -j ACCEPT
        ebtables -I FORWARD -i tap_00002_2 -o tap_00003_2 -j ACCEPT
        ebtables --atomic-commit
        unset EBTABLES_ATOMIC_FILE

        Delete Entries
        --------------
        ebtables -D FORWARD -i tap_00002_2 -o tap_00003_2 -j ACCEPT

        """

        policy_accept = "ACCEPT"
        policy_drop = "DROP"
        ebtables_cmd = "ebtables --concurrent"

        atomic_file = PathUtil.get_temp_file_path("ebtables_atommic")
        atomic_file_str = "--atomic-file %s" % atomic_file

        ebtable_cmd_atomic_init = "{ebtables} {atomic_file} --atomic-init".format(ebtables=ebtables_cmd,
                                                                                  atomic_file=atomic_file_str)

        ebtable_cmd_atomic_save = "{ebtables} {atomic_file} --atomic-save".format(ebtables=ebtables_cmd,
                                                                                  atomic_file=atomic_file_str)

        ebtable_cmd_atomic_commit = "{ebtables} {atomic_file} --atomic-commit".format(ebtables=ebtables_cmd,
                                                                                      atomic_file=atomic_file_str)

        path_connection_log = PathUtil.get_log_file_path("ebtable_connections.txt")

        # TODO: DOC
        _cnt_connections = 1

        @staticmethod
        def inc_counter():
            ConnectionEbtables._cnt_connections += 1
            return ConnectionEbtables._cnt_connections - 1

        @staticmethod
        def get_connection_id(tap_x, tap_y):
            key = tuple(sorted([tap_x, tap_y]))
            return ConnectionEbtables.connections[key]

        # TODO: we should use hosts rather than interfaces here!
        # dict<(str, str>, int>
        # for each connection a connection identifier
        connections = defaultdict(lambda: ConnectionEbtables.inc_counter())

        #########################################
        # Overwrite connection handling methods
        #########################################

        # TODO: #84:
        def tap_link_up(self, tap_x, tap_y, up=True):
            chain = singletons.network_backend.get_br_name(self.interface_x.nr_host_interface)
            change_cmd = self._get_ebtables_cmd(chain, tap_x, tap_y, up)

            network_backend = singletons.network_backend
            # add to command queue
            network_backend.add_shell_ebtables_command(network_backend.EVENT_EBTABLES_COMMANDS, change_cmd)

        def tap_link_up_central(self, tap_x, tap_y, up=True):
            log.info("accept all packets in FORWARD chain ...")
            self.run_shell("{ebtables} -P FORWARD ACCEPT".format(ebtables=ConnectionEbtables.ebtables_cmd))

        def tap_link_up_remote(self, tap_x, tap_y, up=True):
            self.tap_link_up(tap_x, tap_y, up=up)

        #########################################
        ###
        #########################################

        # TODO: clear command list for every step!
        @staticmethod
        def reset_ebtable_commands():
            ConnectionEbtables.ebtable_commands = []

        @staticmethod
        def run_shell(cmd):
            return singletons.shell_helper.run_shell(ConnectionEbtables.__class__.__name__, cmd, prefixes=["ebtables"])

        @staticmethod
        def set_ebtables_forward_policy_accept():
            ConnectionEbtables.set_ebtables_forward_policy(ConnectionEbtables.policy_accept)

        @staticmethod
        def set_ebtables_forward_policy_drop():
            ConnectionEbtables.set_ebtables_forward_policy(ConnectionEbtables.policy_drop)

        @staticmethod
        def set_ebtables_forward_policy(policy):
            log.info("{policy} all packets in FORWARD chain ...".format(policy=policy))
            ConnectionEbtables.run_shell("{ebtables} -P FORWARD {policy}".format(
                ebtables=ConnectionEbtables.ebtables_cmd,
                policy=policy
            ))

        def _get_ebtables_cmd(self, chain, tap_x, tap_y, up):
            # insert or delete?
            up_str = "-I" if up else "-D"
            # use ebtables atomic mode only in batch mode

            # TODO: DOC

            connection_id = ConnectionEbtables.get_connection_id(tap_x, tap_y)
            mark_str = "mark --set-mark {id} --mark-target {policy}".format(id=connection_id, policy=self.policy_accept)

            with open(self.path_connection_log, "a") as f:
                f.write("%s,%s: %d\n" % (tap_x, tap_y, connection_id))

            return "{ebtables} {atomic_prefix} {up_str} {chain} -i {tap_x} -o {tap_y} -j {policy}".format(
                ebtables=self.ebtables_cmd,
                atomic_prefix=self.get_ebtables_atomix_prefix(),
                up_str=up_str,
                chain=chain,
                tap_x=tap_x,
                tap_y=tap_y,
                policy=mark_str
            )

        @staticmethod
        def get_ebtables_atomix_prefix():
            return "--atomic-file %s" % ConnectionEbtables.atomic_file if scenario_config.is_network_backend_bridged_execution_mode_batch() else ""

        @staticmethod
        def get_ebtables_chain_cmd(name, policy):
            return "{ebtables} {atomix_prefix} -N {chain} -P {policy}".format(ebtables=ConnectionEbtables.ebtables_cmd,
                                                                              atomix_prefix=ConnectionEbtables.get_ebtables_atomix_prefix(),
                                                                              chain=name,
                                                                              policy=policy)

        @staticmethod
        def get_ebtables_redirect_cmd(br_name):
            return "{ebtables} {atomic_prefix} -A FORWARD --logical-in {br_name} -j {br_name}".format(
                ebtables=ConnectionEbtables.ebtables_cmd,
                atomic_prefix=ConnectionEbtables.get_ebtables_atomix_prefix(),
                br_name=br_name)

        @staticmethod
        def get_ebtables_clear_cmd():
            return "{ebtables} -F".format(ebtables=ConnectionEbtables.ebtables_cmd)

        @staticmethod
        def get_ebtables_delete_chain_cmd(chain):
            return "{ebtables} -X {chain}".format(ebtables=ConnectionEbtables.ebtables_cmd, chain=chain)

        def _add_filter_cmd(self, dev_name, connection_id):
            # TODO: DOC
            filter_cmd = "tc filter replace dev {tap_dev_name} parent 1:0 protocol all handle {id} fw flowid 1:{id}".format(
                tap_dev_name=dev_name, id=connection_id)

            self.add_shell_command(self.EVENT_LINK_SHAPE_ADD_FILTER, filter_cmd)

        def _get_default_class(self):
            # use filter instead
            return ""

    return ConnectionEbtables
