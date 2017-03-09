from miniworld.model.StartableObject import StartableSimulationStateObject
from miniworld.model.events.EventSystem import EventSystem

class MyEventSystem(EventSystem, StartableSimulationStateObject):
    '''
    Concrete implementation of the MiniWorld Event-System.
    Contains all events used in the project.
    '''

    EVENT_VM_BOOT = "vm_boot"
    EVENT_VM_SHELL_READY = "vm_shell_ready"
    EVENT_VM_SHELL_PRE_NETWORK_COMMANDS = "vm_shell_pre_network_commands"
    EVENT_VM_SHELL_POST_NETWORK_COMMANDS = "vm_shell_post_network_commands"

    EVENT_NETWORK_BACKEND_SETUP = "network_backend_setup"

    EVENT_NETWORK_SETUP = "network_setup"
    EVENT_NETWORK_CHECK = "network_check"

    STATIC_EVENTS = [EVENT_VM_BOOT, EVENT_VM_SHELL_READY, EVENT_VM_SHELL_PRE_NETWORK_COMMANDS]
    # dynamic: EVENT_VM_SHELL_POST_NETWORK_COMMANDS, EVENT_NETWORK_BACKEND_SETUP, EVENT_NETWORK_SETUP, EVENT_NETWORK_CHECK

    def __init__(self, *args, **kwargs):
        super(MyEventSystem, self).__init__(self.STATIC_EVENTS, *args, **kwargs)

    def reset(self):
        super(MyEventSystem, self).reset()
        self.events.extend(self.STATIC_EVENTS)