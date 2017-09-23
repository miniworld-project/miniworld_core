from miniworld.Scenario import scenario_config
from miniworld.model.emulation import Qemu
from miniworld.model.network.backends.vde.VDESwitch import VDESwitch
from miniworld.model.network.backends.vde.VDEConstants import PORT_QEMU


# TODO: #54, #55: adopt to no vlan or remove!
def get_cmd_template_qemu_nic_vde():
    CMD_TEMPLATE_QEMU_NIC = """
        -device {nic_model},netdev=net{vlan},mac={mac_addr}
        -netdev vde,id=net{vlan},port={port},sock={path_vde_uds_socket}
    """
    return CMD_TEMPLATE_QEMU_NIC

# old qemu network config
# def get_cmd_template_qemu_nic_vde(vlan_enabled):
#     CMD_TEMPLATE_QEMU_NIC = """
#         -net nic,model={nic_model},vlan={vlan},macaddr={mac_addr}
#         -net vde,vlan={vlan},port={port},sock={path_vde_uds_socket}
#     """ if vlan_enabled else \
#     """
#         -net nic,model={nic_model},macaddr={mac_addr}
#         -net vde,port={port},sock={path_vde_uds_socket}
#     """
#
# # TODO: #54,#55: DOC
#     return CMD_TEMPLATE_QEMU_NIC


class QemuVDE(Qemu.Qemu):

    def _build_qemu_nic_command(self):
        cmd_setup_nics = ""
        # construct cli commands for networking
        for idx, _if in enumerate(self.emulation_node.network_mixin.interfaces):
            cmd_setup_nics += "\n" + get_cmd_template_qemu_nic_vde().format(
                port=PORT_QEMU,
                # node classes have a common mac address prefix
                mac_addr=_if.get_mac(self.emulation_node.id),
                path_vde_uds_socket=VDESwitch.get_vde_switch_sock_path(VDESwitch.get_interface_class_dependent_id(self.id, _if.node_class, _if.nr_host_interface)),
                nic_model=scenario_config.get_qemu_nic(),
                # separate interface class through VLANs
                vlan=idx
            )

        return cmd_setup_nics

    def reset(self):
        super(QemuVDE, self).reset()
