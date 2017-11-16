import selectors
import time

from miniworld.util.NetUtil import Timeout

from miniworld.singletons import singletons


class SocketExpect(object):
    def __init__(self, sock, check_fun, read_buf_size=1, timeout=None, send_data=None):
        """
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
        """

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
        self.logger = singletons.logger_factory.get_logger(self)

    # TODO: DOC
    def read(self):
        """

        Returns
        -------
        str
            The read stream content.


        Raises
        ------
        Timeout
            If `timeout` is not None.
        """
        try:
            self.selector.register(self.sock, selectors.EVENT_READ)
            t_start = time.time()
            last_check = None

            while True:
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
        data = self.sock.recv(self.read_buf_size)
        self.output += data.decode('utf-8')
        res = self.check_fun(data, self.output)
        if res:
            return res
