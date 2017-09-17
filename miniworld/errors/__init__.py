from miniworld.errors import WrapperException

__author__ = 'Nils Schmidt'


''' Base Exception '''


class Base(WrapperException.WrapperException):
    pass


class AlreadyRunning(Base):
    pass


###############################################
# Qemu
###############################################

class QemuBootWaitTimeout(Base):
    pass


class QemuNoShell(Base):
    pass


###############################################
# Config System
###############################################

class ConfigError(Base):
    pass


class ConfigNotSet(ConfigError):
    pass


class ConfigOptionNoLongerSupported(ConfigError):
    pass


class ConfigOptionNotSupported(ConfigError):
    pass


class ConfigMalformed(ConfigError):
    pass

###############################################
# RPC
###############################################


class RPCError(Base):
    pass

###############################################
# Simulation
###############################################


class SimulationStateError(Base):
    pass


class SimulationStateStartFailed(SimulationStateError):
    pass


class SimulationStateAlreadyStarted(SimulationStateError):
    pass


###############################################
# Interface
###############################################

class InterfaceError(Base):
    pass


class InterfaceUnknown(InterfaceError):
    pass

###############################################
###
###############################################


class Unsupported(Base):
    pass


###############################################
# Network Backend
###############################################


class NetworkSetupError(Base):
    pass


class NetworkBridgeNotExisting(NetworkSetupError):
    pass


class NetworkBackendError(Base):
    pass


class NetworkBackendStartError(NetworkBackendError):
    pass


class NetworkBackendConnectionError(NetworkBackendError):
    pass


class NetworkBackendSwitchError(NetworkBackendError):
    pass


class NetworkBackendErrorReset(NetworkBackendError):
    pass

# Bridged Network Backend specific


class NetworkBackendBridgedError(NetworkBackendError):
    pass


class NetworkBackendBridgedBridgeError(NetworkBackendBridgedError):
    pass


class NetworkBackendUnknown(NotImplementedError):
    pass
