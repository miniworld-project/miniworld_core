
from miniworld import log
from miniworld.Scenario import scenario_config
from miniworld.model.singletons.Singletons import singletons
from miniworld.model.emulation import Qemu
from miniworld.model.network.interface import Interface

# TODO: generic wrapper around network stuff!
# TODO: nic model for -device?


def get_cmd_template_qemu_nic():
    """

    Returns
    -------

    See Also
    --------
    http://www.linux-kvm.org/page/10G_NIC_performance:_VFIO_vs_virtio
    """
    # # TODO: #54,#55: check what vlan means for qemu
    CMD_TEMPLATE_QEMU_NIC = """
    -device {nic_model},netdev=net{vlan},mac={mac_addr}
    -netdev tap,id=net{vlan},ifname={ifname},script=no,downscript=no
    """
    return CMD_TEMPLATE_QEMU_NIC


class QemuTap(Qemu.Qemu):

    # TODO: #54,#55: DOC
    def _build_qemu_nic_command(self):

        # TODO: ABSTRACT COMMAND GENERATION!
        cmd_setup_nics = []

        def add_if(_if, _if_name, vlan):
            cmd_setup_nics.append(self._build_qemu_nic_command_internal(_if, _if_name, vlan))

        cnt_normal_iface = 0
        log.debug("using ifaces: '%s'", self.emulation_node.network_mixin.interfaces)

        # NOTE: sort the interfaces so that the Management interface is the last one
        for vlan, _if in enumerate(self.emulation_node.network_mixin.interfaces):

            _if_name = None
            if type(_if) in (Interface.HubWiFi, Interface.Management):
                _if_name = singletons.network_backend.get_tap_name(self.id, _if)
            else:
                # create for each connection a tap device
                # NOTE: for each new tap device we need to adjust the `nr_host_interface`
                # NOTE: otherwise we have duplicate interface names!
                # iterate over interfaces and connections

                _if_name = singletons.network_backend.get_tap_name(self.id, _if)
                cnt_normal_iface += 1

            log.debug('add_if(%s,%s,%s)', repr(_if), _if_name, vlan)
            add_if(_if, _if_name, vlan)

        return '\n'.join(cmd_setup_nics)

    def _build_qemu_nic_command_internal(self, _if, _if_name, vlan):
        return get_cmd_template_qemu_nic().format(
            ifname=_if_name,
            # node classes have a common mac address prefix
            mac_addr=_if.get_mac(self.emulation_node.id),
            vlan=vlan,
            nic_model=scenario_config.get_qemu_nic()
        )

    # TODO: REMOVE ?
    def after_start(self):
        pass

    def reset(self):
        super(QemuTap, self).reset()
