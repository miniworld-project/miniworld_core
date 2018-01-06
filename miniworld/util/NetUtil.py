import errno
import socket

from miniworld.errors import Base

__author__ = 'Nils Schmidt'


class Timeout(Base):
    pass


def get_mac(postfix_as_int, prefix="aa:aa:aa:aa"):
    """ Generate a mac address with suffix `prefix` and postfix `postfix_as_int`
    Supports 2^16 unique mac addresses
    """

    postfix = "%04x" % postfix_as_int
    postfix = '%s:%s' % (postfix[0:2], postfix[2:4])
    return '%s:%s' % (prefix, postfix)


###########################################################
# Network Configuration
###########################################################


def get_ip_addr_change_cmd(dev, ip, netmask, up=True):
    return 'ifconfig {dev} {ip} netmask {netmask} {state}'.format(dev=dev, ip=ip, netmask=netmask,
                                                                  state='up' if up else '')


def get_slash_x(subnets, prefixlen):
    """

    Parameters
    ----------
    subnets
    prefixlen

    Examples
    --------
    >>> get_slash_x(ipaddress.ip_network(u"10.0.0.0/8").subnets(), 30)
    10.0.0.0/30
    10.0.0.4/30
    10.0.0.8/30
    10.0.0.12/30

    Returns
    -------
    generator<IPv4Network>
    """
    for subnet in subnets:
        if subnet.prefixlen == prefixlen:
            yield subnet
        else:
            # simulate 'yield from'
            for subnet in get_slash_x(list(subnet.subnets()), prefixlen):
                yield subnet


###########################################################
# UNIX Domain Socket stuff
###########################################################

def uds_reachable(uds_path, return_sock=False):
    """ Check if the unix domain socket at path `uds_path` is reachable.

    Parameters
    ----------
    uds_path : str
    return_sock: bool, optional (default is False)
        Return the socket.

    Returns
    -------
    bool, socket
        If the socket is reachable, the socket if `return_sock` else None
        Remember to close the socket!
    """
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(uds_path)
    except (ConnectionRefusedError, FileNotFoundError):
        return False, None
    finally:
        if not return_sock:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()

    return True, sock if return_sock else None


def wait_until_uds_reachable(uds_path, return_sock=False):
    """ Wait until the unix domain socket at `uds_path` is reachable.

    Returns
    -------
    socket.socket
    """

    from miniworld.util import ConcurrencyUtil
    sock = ConcurrencyUtil.wait_until_fun_returns_true(lambda x: x[0] is True, uds_reachable, uds_path,
                                                       return_sock=return_sock)[1]
    return sock


def read_remaining_data(sock, buf_size=4096):
    """
    Get the remaining (unread) data from the socket.

    Parameters
    ----------
    sock : socket._socketobject
    buf_size : int

    Returns
    -------
    str
        The data.
    """
    data = ""
    try:
        old_timeout = sock.gettimeout()
        sock.setblocking(0)
        while True:
            data += sock.recv(buf_size)
    except socket.error as e:
        # error: [Errno 11] Resource temporarily unavailable
        if not e[0] == errno.EDEADLK:
            raise e
    finally:
        # reset old timeout and (non)blocking mode
        sock.settimeout(old_timeout)
        return data
