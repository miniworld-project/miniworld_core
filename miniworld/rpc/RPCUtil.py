from miniworld.Config import config

LOCAL_IP_V4 = "127.0.0.1"

PORT_CLIENT = 5000
PORT_COORDINATOR = 5001

def get_rpc_port():
    if config.is_mode_distributed():
        if not config.is_coordinator():
            return PORT_CLIENT

    return PORT_COORDINATOR


def addr_from_ip(ip,port=get_rpc_port()):
    return 'http://{ip}:{port}/RPC2'.format(ip=ip,port=port)


def local_addr():
    return addr_from_ip(LOCAL_IP_V4)