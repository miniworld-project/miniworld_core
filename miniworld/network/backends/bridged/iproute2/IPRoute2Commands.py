from miniworld.service.shell.shell import run_shell


def find_empty_group(start=1, end=10000):
    """
    Returns the next free iproute2 group.

    Parameters
    ----------
    start : int
    end : int

    Returns
    -------
    int
    """
    for idx in range(start, end + 1):
        # no links for this group
        if not run_shell("ip link list group {}".format(idx)):
            return idx


# #GROUP_TUNNELS = find_empty_group()
# # we cannot simply call find_empty_group with the same parameters because the method works only if a new group has been created!
# # therefore the pass the start parameter!
# GROUP_BRIDGES = find_empty_group(start=GROUP_TUNNELS + 1)
# GROUP_TAP_DEVS = find_empty_group(start=GROUP_BRIDGES + 1)
#
# GROUPS = {"tunnels": GROUP_TUNNELS,
#           "bridges": GROUP_BRIDGES,
#           "tap_devices": GROUP_TAP_DEVS
#           }
#
# GROUPS_LOG_FILE = PathUtil.get_temp_file_path("iproute2_groups")
#
# # log iproute2 groups
# with open(GROUPS_LOG_FILE, "w") as f:
#     log.info("writing the iproute2 groups to '%s'", GROUPS_LOG_FILE)
#     f.write('\n'.join(["%s:%s" % (key, val) for key, val in GROUPS.items()]))
#
# for iproute2_group, val in GROUPS.items():
#     log.info("%s group is: %d" % (iproute2_group, val))


def get_bridge_add_cmd(bridge_dev_name):
    return "ip link add name {} type bridge".format(bridge_dev_name)


def get_bridge_set_hub_mode_cmd(bridge_dev_name):
    return "ip link set dev {} type bridge ageing_time 0".format(bridge_dev_name)


def get_bridge_add_if_cmd(_if_name, bridge_dev_name):
    return "ip link set dev {_if} master {bridge}".format(_if=_if_name, bridge=bridge_dev_name)


def get_interface_up_cmd(_if_name, state_down=False):
    return "ip link set dev {} {state}".format(_if_name, state='up' if not state_down else 'down')


def get_gretap_tunnel_cmd(tunnel_dev_name, remote_ip, key):
    tunnel_cmd = "ip link add {tunnel_name} type gretap remote {remote_ip} key {key} nopmtudisc".format(
        tunnel_name=tunnel_dev_name,
        remote_ip=remote_ip,
        key=key
    )
    return tunnel_cmd


def get_add_interface_to_group_cmd(if_name, group):
    return 'ip link set dev {interface_name} group {group}'.format(interface_name=if_name, group=group)


def get_link_del_cmd(dev_name):
    return "ip link del {}".format(dev_name)
