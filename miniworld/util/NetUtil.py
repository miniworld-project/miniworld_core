import errno
import time
import socket
import selectors
from miniworld.errors import Base
from miniworld.log import get_logger

__author__ = 'Nils Schmidt'

def get_mac(postfix_as_int, prefix = "aa:aa:aa:aa"):
    ''' Generate a mac address with suffix `prefix` and postfix `postfix_as_int`
    Supports 2^16 unique mac addresses
    '''

    postfix = "%04x" % postfix_as_int
    postfix = '%s:%s' % (postfix[0:2], postfix[2:4])
    return'%s:%s' % (prefix, postfix)

###########################################################
### Network Configuration
###########################################################

def get_ip_addr_change_cmd(dev, ip, netmask, up=True):
    return 'ifconfig {dev} {ip} netmask {netmask} {state}'.format(dev=dev, ip=ip, netmask=netmask,
                                                                  state='up' if up else '')

def get_slash_x(subnets, prefixlen):
    '''

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
    '''
    for subnet in subnets:
        if subnet.prefixlen == prefixlen:
            yield subnet
        else:
            # simulate 'yield from'
            for subnet in get_slash_x(list(subnet.subnets()), prefixlen):
                yield subnet


###########################################################
### UNIX Domain Socket stuff
###########################################################

def uds_reachable(uds_path, return_sock=False):
    ''' Check if the unix domain socket at path `uds_path` is reachable.

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
    '''
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
    ''' Wait until the unix domain socket at `uds_path` is reachable.

    Returns
    -------
    socket.socket
    '''

    from miniworld.util import ConcurrencyUtil
    sock = ConcurrencyUtil.wait_until_fun_returns_true(lambda x : x[0] is True, uds_reachable, uds_path, return_sock=return_sock)[1]
    return sock

class Timeout(Base):
    pass

# # TODO: DOC
# TODO: use for multiple sockets in parallel!
class SocketExpect(object):

    # TODO: REMOVE expected_length
    # TODO: support timeout!
    def __init__(self, sock, check_fun, read_buf_size = 1, timeout = None, send_data = None):
        '''
        Read from the socket `sock` until the function
        `check_fun` return True.

        Parameters
        ----------
        sock: socket
        check_fun : str -> str -> bool
            Currently received data, whole data, expected result?
        read_buf_size : int, optional (default is 1)
            Reads bytewise from the socket.
        send_data: bytes
        '''

        if timeout is not None and timeout < 0:
            raise ValueError("timeout must be > 0!")
        self.sock = sock
        self.check_fun = check_fun
        self.read_buf_size = read_buf_size

        self.output = ""

        # get the best selector for the system
        self.selector = selectors.DefaultSelector()

        self.timeout = timeout

        self.send_data = send_data
        self.logger = get_logger(self.__class__.__name__)

    # TODO: DOC
    def read(self):
        '''

        Returns
        -------
        str
            The read stream content.


        Raises
        ------
        Timeout
            If `timeout` is not None.
        '''
        try:
            self.selector.register(self.sock, selectors.EVENT_READ)
            t_start = time.time()
            last_check = None

            while 1:
                if last_check is None:
                    last_check = time.time()

                # data available or timeout occurred ?
                events = self.selector.select(0.5)
                if time.time() - t_start > self.timeout:
                    raise Timeout("Timeout (%s) occurred!" % self.timeout)

                if self.send_data is not None and time.time() - last_check > 1:
                    last_check = time.time()
                    self.sock.send(self.send_data)
                    self.logger.debug('sending {}'.format(self.send_data))
                for key, mask in events:
                    if mask == selectors.EVENT_READ:
                        res = self.process_socket()
                        if res:
                            return self.output

        finally:
            self.selector.unregister(self.sock)

    def process_socket(self):

        try:
            data = self.sock.recv(self.read_buf_size)
            self.output += data.decode('utf-8')
            res = self.check_fun(data, self.output)
            if res:
                return res
        except socket.error as e:
            # # error: [Errno 104] Connection reset by peer
            # if e.errno == 104:
            #     log.critical("Socket '%s' caused troubles! %s, %s.Read yet:%s", self.sock, self.sock.getpeername(), self.sock.getsockname(), self.output)
            raise

def wait_for_socket_result(*args, **kwargs):
    buffered_socket_reader = SocketExpect(*args, **kwargs)
    return buffered_socket_reader.read()


def wait_for_boot(*args, **kwargs):
    '''
    Raises
    ------
    Timeout
    '''
    # enter shell after each select timeout
    kwargs['send_data'] = b'\n'
    buffered_socket_reader = SocketExpect(*args, **kwargs)
    return buffered_socket_reader.read()

if __name__ == '__main__':
    import selectors
    import socket

    def foo():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 2000))
        sock.send("GET /")

        sel = selectors.DefaultSelector()
        sel.register(sock, selectors.EVENT_READ)

        while 1:
            events = sel.select(None)
            for key, mask in events:
                #print key, mask
                if mask == selectors.EVENT_READ:
                    sock = key.fileobj
                    data = sock.recv(1)
                    print(data)
                else:
                    print(mask)


        sel.unregister(sock)

    foo()

def read_remaining_data(sock, buf_size = 4096):
    '''
    Get the remaining (unread) data from the socket.

    Parameters
    ----------
    sock : socket._socketobject
    buf_size : int

    Returns
    -------
    str
        The data.
    '''
    data = ""
    try:
        old_timeout = sock.gettimeout()
        sock.setblocking(0)
        while 1:
            data += sock.recv(buf_size)
    except socket.error as e:
        # error: [Errno 11] Resource temporarily unavailable
        if not e[0] == errno.EDEADLK:
            raise e
    finally:
        # reset old timeout and (non)blocking mode
        sock.settimeout(old_timeout)
        return data