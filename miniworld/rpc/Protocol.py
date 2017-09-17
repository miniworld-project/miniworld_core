

# TODO: ABC class
from miniworld.Config import config

REGISTER_MSG_KEY_TUNNEL_ADDR = "tunnel_addr"

# PORT_SYNC_SERVICE = 5561
# PORT_REG_SERVICE  = 5562
# PORT_TUNNEL_SERVICE  = 5563

PORT_DEFAULT_SERVICE = 5561

# Publish-Subscribe only
PORT_PUB_RESET_SERVICE = 5562
PORT_PUB_SERVICE = 5563


class Protocol:
    """
    Abstract protocol which defines how data is represented on the wire.
    """

    def serialize(self, obj):
        """

        Parameters
        ----------
        obj

        Returns
        -------
        obj
        """
        raise NotImplementedError

    def deserialize(self, obj):
        """

        Parameters
        ----------
        obj

        Returns
        -------
        obj
        """
        raise NotImplementedError

    ############################################
    # Messages - For each message a protocol
    ############################################

    def create_register_msg(self, tunnel_addr):
        return {REGISTER_MSG_KEY_TUNNEL_ADDR: tunnel_addr}

    @staticmethod
    def get_register_msg_tunnel_addr(register_msg):
        return register_msg[REGISTER_MSG_KEY_TUNNEL_ADDR]


import json

# TODO: move (en/de)coders here ...


class JSONProtocol(Protocol):

    def serialize(self, obj):
        return json.dumps(obj).encode()

    def deserialize(self, obj):
        return json.loads(obj.decode())


import msgpack


class MsgPackProtocol(Protocol):

    def serialize(self, obj):
        return msgpack.packb(obj)

    def deserialize(self, obj):
        return msgpack.unpackb(obj)


def factory():
    if config.is_protocol_msgpack():
        return MsgPackProtocol
    elif config.is_protocol_json():
        return JSONProtocol
    else:
        raise ValueError("Invalid protocol!")
