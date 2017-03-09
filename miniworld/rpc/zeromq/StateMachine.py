from pprint import pformat

from miniworld import log

'''
The classes in this module helps to implement a state machine used for
group communication based on ZeroMQ.

Clients and the server are always expected to be in the same state.
Clients which have a wrong state, are simply ignored (but logged).

The communication between the server and the clients is asynchronous on the server, but synchronous on the client.

The class :py:class:`.Expecter` handles the asynchronous message receiving,
 whereas the :py:class:`Responder` handles the asynchronous responding.
Both use a :py:class:`.Protocol` to handle serialiation/deserialization transparently.

There are different responders for different responder patterns:
- :py:class:`ResponderArgument` responds each client with the same argument.
- :py:class:`ResponderServerID` responds each client with its allocated ID
- :py:class:`ResponderPerServerID` responds each client with a different argument.
    The arguments are passed as dictionary where each entry contains the server id.
'''

class Expecter(object):

    '''
    Expects a multi part messages from each client with a specific number of message parts.

    Protocol for multipart messages:
    address | space | state | arg_1 | ... | arg_n

    The class enables us to abstract the underlying protocol of the message passing system.
    Each expect call is responsible to handle one client. The received arguments are stored in expect_storage.
    But first, it is checked that the client is in the correct state.

    The :py:func:`expect_for_all` expects from each client to send a message in the current state.
    For each response, the :py:func:`after_response_fun` is called.

    See Also
    --------
    http://rfc.zeromq.org/spec:28/REQREP/

    Attributes
    ----------
    socket : zmq.sugar.socket.Socket
        Router socket.
    cnt_peers : int
    state : str
    protocol : Protocol
        The protocol for serialization/deserialization
    after_response_fun : Expecter -> int -> int -> void
        Called after a client has been handled.
        First arg is cnt of already handles peers, the second the total peer count.
    expect_storage : list<obj>
        address, message part 1, ..., message part n
    cnt_message_parts : int
        How much parts the messages is expected to have
    '''
    def __init__(self, socket, cnt_peers, protocol, state,
                 cnt_message_parts = 1,
                 after_response_fun=None
                 ):
        '''
        Parameters
        ----------
        cnt_message_parts : int, optional (default is 1)
            Expect at least one argument.
        '''
        self.socket = socket
        self.cnt_peers = cnt_peers
        self.state = state
        self.protocol = protocol
        self.after_response_fun = after_response_fun

        # address, item_1, ..., item_n
        self.expect_storage = []

        self.cnt_message_parts = cnt_message_parts
        # address, space, state
        self.cnt_minimal_args_per_message = 3

    def expect_for_all(self):
        '''
        Call :py:func:`expect` for each client and before the first client.
        Therefore, the method first returns, if each client responded in the current state
        with the correct number of parts in the message.

        Returns
        -------
        expect_storage : list<obj>
            address, message part 1, ..., message part n
        '''

        if self.after_response_fun:
            self.after_response_fun(self, 0, self.cnt_peers)

        for idx in range(1, self.cnt_peers + 1):

            # wait until we have a valid expect call
            while 1:
                if self.expect():
                    break

            if self.after_response_fun:
                self.after_response_fun(self, idx, self.cnt_peers)

    def expect(self):
        '''
        Receives a multipart message and checks if the multi part message contains the correct number of parts.
        Moreover, deserialize all message parts.

        Returns
        -------
        list<obj>
            The received objects if no error occurred!
        '''
        msgs = self.socket.recv_multipart()
        expected_msg_parts = self.cnt_minimal_args_per_message + self.cnt_message_parts
        if len(msgs) == expected_msg_parts:
            # address, empty, state
            msgs[2:] = map(self.protocol.deserialize, msgs[2:])
            state = msgs[2]

            if state == self.state:
                self.expect_storage.append([msgs[0]] + msgs[3:])
                return msgs
            else:
                log.critical("client requested state '%s', but current state is '%s'", state, self.state)
        else:
            log.critical("Received invalid message: %s, expected %d parts in the message, has: %d", msgs, expected_msg_parts, len(msgs))


    ############################################################
    ### Access the message parts
    ############################################################

    def get_message_parts_no_id(self):
        return self.get_message_parts(_from=1)

    def get_message_parts(self, _from=2):
        '''
        Get all message parts by cutting off the addr and node_id from the stored arguments.
        '''
        return [arg_list[_from:] for arg_list in self.expect_storage]

    def get_message_parts_per_node_id(self):
        '''
        cut off addr and node_id from stored arguments

        Returns
        -------
        dict<int, list<obj>>
        '''
        return {arg_list[1]: arg_list[2:] for arg_list in self.expect_storage}

    def get_message_part_per_node_id(self, arg_nr=1):
        '''
        Assume there is only one part in the message.
        Return them per node id.

        Parameters
        ----------
        arg_nr : int, optional (default is 1)

        Returns
        -------
        dict<int, obj>
        '''
        return {arg_list[1]: arg_list[2 + arg_nr - 1] for arg_list in self.expect_storage}

    def get_server_ids(self):
        '''
        Get the server ids as list.

        Returns
        -------
        list<str>
        '''
        return [arg_list[1] for arg_list in self.expect_storage]

    def get_addresses(self):
        '''
        Get the addresses from each client.

        Returns
        -------
        list<obj>
        '''
        return [item[0] for item in self.expect_storage]

    def get_server_id_addr_mapping(self):
        '''
        Get for each server the address.

        Returns
        -------
        dict<str, obj>
        '''
        return {item[1]: item[0] for item in self.expect_storage}


class Responder(object):
    '''
    This is the base class used to implement different responder patterns.
    It has access to the :py:class:`.Expecter` because we need the addresses of the clients.
    Each responder implements its own :py:func:`.respond` method to provide different responder patterns.
    For this it used different arguments from the expecter class.

    Attributes
    ----------
    socket : zmq.sugar.socket.Socket
        Router socket.
    protocol : Protocol
        The protocol for serialization/deserialization
    expecter : Expecter
    '''

    def __init__(self, socket, protocol, expecter):
        self.socket = socket
        self.protocol = protocol
        self.expecter = expecter

    def __call__(self, *args, **kwargs):
        '''
        Use this method if data received with the expecter can be simply passed to the responder.
        '''
        self.expecter.expect_for_all()
        self.respond()

    def respond(self):
        raise NotImplementedError

class ResponderArgument(Responder):
    '''
    Send each client the same response/argument.

    Attributes
    ----------
    response : obj
    '''

    def __init__(self, socket, protocol, expecter, response):
        super(ResponderArgument, self).__init__(socket, protocol, expecter)
        self.response = response

    def respond(self):
        '''
        Run over addresses and send the response.
        '''
        for addr in self.expecter.get_addresses():
            self.socket.send_multipart([
                addr,
                b'',
                self.protocol.serialize(self.response),
            ])


class ResponderServerID(Responder):
    '''
    Send each client it's id.
    This is allocated in a first-come-first-served manner.
    Therefore the order in which the clients registered (hold by the expecter class).
    '''

    def __init__(self, socket, protocol, expecter):
        super(ResponderServerID, self).__init__(socket, protocol, expecter)

    def respond(self):
        '''

        Returns
        -------
        dict<int, obj>
        '''

        server_id_addr_mapping = {}

        for idx, addr in enumerate(self.expecter.get_addresses(), 1):
            self.socket.send_multipart([
                addr,
                b'',
                # send node its id
                self.protocol.serialize(idx)
            ])
            server_id_addr_mapping[idx] = addr

        return server_id_addr_mapping


class ResponderPerServerID(Responder):
    '''
    Respond individually for each server.

    Attributes
    ----------
    responses : dict<int, obj>
        For each server the object to send.
    '''
    def __init__(self, socket, protocol, expecter, responses):
        super(ResponderPerServerID, self).__init__(socket, protocol, expecter)
        self.responses = responses

    def respond(self):
        '''

        Parameters
        ----------

        Returns
        -------

        '''
        for server_id, addr in self.expecter.get_server_id_addr_mapping().items():
            self.socket.send_multipart([
                addr,
                b'',
                self.protocol.serialize(self.responses[server_id]),
            ])