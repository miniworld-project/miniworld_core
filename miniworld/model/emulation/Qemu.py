import hashlib
import socket
import time
from StringIO import StringIO

import re
from UserDict import UserDict

import miniworld.model.network.interface.Interface
from miniworld.Config import config
from miniworld.Scenario import scenario_config
from miniworld.management.ShellHelper import run_shell
from miniworld.model.emulation.QemuMonitorRepl import QemuMonitorRepl, QemuMonitorSnapshotLoadError
from miniworld.model.emulation.VirtualizationLayer import VirtualizationLayer
from miniworld.util.NetUtil import Timeout

__author__ = 'Nils Schmidt'

from os.path import basename, abspath
from os.path import splitext
import pexpect
from miniworld.errors import QemuBootWaitTimeout
from miniworld.util import PathUtil, NetUtil
from miniworld.model.singletons.Singletons import singletons

from miniworld.script.TemplateEngine import *
from miniworld.repl.REPLable import REPLable
from miniworld.model.ShellCmdWrapper import ShellCmdWrapper

###############################################
### Command templates
###############################################

CMD_TEMPLATE_QEMU_CREATE_OVERLAY_IMAGE = """
qemu-img create
    -b "{base_image_path}"
    -f qcow2
    "{overlay_image_path}"
"""

# TODO: check for kvm!
# Ticket: #8
def is_kvm_usable():
    '''
    Check if the system has kvm support and the module is not used.
    '''
    # TODO: REMOVEs
    try:
        # Ticket: #8: CHECK IF MODULE REALLY USABLE! E.G. NOT USABLE TOGETHER WITH VIRTUALBOX
        with open("/dev/kvm", "r"):
            pass
    except IOError as e:
        return False
    return True

def log_kvm_usable():
    kvm_usable = is_kvm_usable()
    if kvm_usable:
        log.info("Using kvm for virtualization ...")
    else:
        log.info("Kvm already in use or not supported! Falling back to emulation ...")

# TODO: CHANGE RAM
# Ticket: #10
def get_qemu_cmd_template():
    '''
    Delay the command creation until some variables are accessable.
    '''
    CMD_TEMPLATE_QEMU = """
    qemu-system-x86_64
        {kvm_support}
        -m {memory}
        -serial unix:{path_serial_uds_socket},server
        -monitor unix:{path_qmp_uds_socket},server
        -nographic
        {network_interfaces}
        -watchdog-action poweroff
        -hda "{path_overlay_image}"
        {overlay_images}
        {user_addition}
    """
    return CMD_TEMPLATE_QEMU

CMD_TEMPLATE_QEMU_KVM = """
    -enable-kvm
    -cpu host
"""

CMD_TEMPLATE_QEMU_MOUNT_DISK = """
-drive file={image_path},index={index},media=disk
"""

READ_BUF_SIZE = 8192 * 5

def get_nic_models():
    output = run_shell("kvm -device ?")
    output = output.split("Network devices:")[1:]
    return re.findall('name\s+"([^"]+)', output, re.MULTILINE)

###############################################
### Other constants
###############################################

class QemuProcessSingletons(UserDict):
    pass


class Qemu(VirtualizationLayer, ShellCmdWrapper, REPLable):
    '''
    Handles the starting of a Qemu instance.

    Attributes
    ----------
    log_path_qemu_boot : str
        The log for the qemu boot process.
    monitor_repl : QemuMonitorRepl
    '''

    exit_code_identifier = "exit code:"
    exit_code_shell_cmd_checker = " ; echo -n %s$?" % exit_code_identifier
    re_zero_ret_code_text = '%s0' % exit_code_identifier
    re_zero_ret_code = re.compile(re_zero_ret_code_text, flags=re.DOTALL)

    def __init__(self, id, emulation_node):
        VirtualizationLayer.__init__(self, id, emulation_node)

        self.emulation_node = emulation_node

        # log file for qemu boot
        self.log_path_qemu_boot = PathUtil.get_log_file_path("qemu_boot_%s.txt" % self.id)

        self.monitor_repl = QemuMonitorRepl(self)

        self.booted_from_snapshot = False

        ################################
        # REPLable
        ################################

        REPLable.__init__(self)

        # unix domain socket paths
        self.path_uds_socket = self.get_qemu_sock_path(self.id)
        self.uds_socket = None

    def reset(self):
        try:
            self.uds_socket.shutdown(socket.SHUT_RDWR)
        except socket.error as e:
            self.nlog.exception(e)

        try:
            self.uds_socket.close()
        except socket.error as e:
            self.nlog.exception(e)
            
        super(Qemu, self).reset()

    # TODO: #54,#55: DOC
    def after_start(self):
        pass

    def _build_qemu_overlay_images_command(self):
        '''
        Create an overlay image for each user supplied image.

        Returns
        -------
        str

        '''
        # start by 1 (0 is reserved for -hda of base image!)
        index = 1
        overlay_image_cmd = ""

        for image_path in scenario_config.get_overlay_images():
            overlay_image_path = self.create_qemu_overlay_image(abspath(image_path))
            overlay_image_cmd += "%s %s" % (overlay_image_cmd, CMD_TEMPLATE_QEMU_MOUNT_DISK.format(image_path=overlay_image_path, index = index))
            index += 1

        return overlay_image_cmd

    def _build_qemu_nic_command(self):
        raise NotImplementedError

    def _build_qemu_command(self, path_qemu_base_image, qemu_user_addition = None):
        '''
        Build the qemu cli command.

        Parameters
        ----------
        path_qemu_base_image : str
            Path to the base image used as read layer.
        qemu_user_addition : str, optional (default is the value from the scenario config file)
            Additional parameters for QEMU.
        '''

        if qemu_user_addition is None:
            qemu_user_addition = scenario_config.get_qemu_user_addition(node_id = self.id) or ""

        log_kvm_usable()

        return get_qemu_cmd_template().format(
            kvm_support = CMD_TEMPLATE_QEMU_KVM if is_kvm_usable() else "",
            path_serial_uds_socket = self.path_uds_socket,
            path_qmp_uds_socket = self.monitor_repl.path_uds_socket,
            path_overlay_image = self.create_qemu_overlay_image(abspath(path_qemu_base_image)),
            network_interfaces = self._build_qemu_nic_command(),
            overlay_images = self._build_qemu_overlay_images_command(),
            user_addition = qemu_user_addition,
            memory = scenario_config.get_qemu_memory()
            )


    @staticmethod
    def sha1(file_path):
        BLOCKSIZE = 65536
        hasher = hashlib.sha1()
        with open(file_path, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        return hasher.hexdigest()

    @staticmethod
    def get_snapshot_id():
        #return '%s_%s' % (scenario_config.get_scenario_name(), Qemu.sha1(scenario_config.get_path_image()))
        return scenario_config.get_scenario_name()

    def _start(self, path_qemu_base_image):
        '''
        Start the QEMU instance:

        1. Set qemu process ownership
        2. Try to load a snapshot, kill the old process and snapshot if it fails
        3. Build the command line for Qemu
            3.1 Check if KVM is available
            3.2 Build NIC command
            3.3 Create disk overlay
            3.4 Include user command line additions
        4. Start the Qemu process, take process ownership for snapshot mode
            (to keep the snapshots alive in the process)
        5. Enter the Qemu Monitor first, then the serial console
        6. Boot VM
        7. Set event progress
        8. Create snapshot
        9. Store Qemu process in singleton map
        10. Call after_start

        Parameters
        ----------
        path_qemu_base_image : str
            Path to the base image used as read layer.

        Raises
        ------
        QemuBootWaitTimeout
            Timeout while booting the vm.
        REPLTimeout
            Timeout while doing stuff on the shell.
        '''

        es = singletons.event_system
        self.process = None
        snapshot_load_failed = False

        if config.is_qemu_snapshot_boot():
            self.process = singletons.qemu_process_singletons.get(self.id)
            take_process_ownership = False
        else:
            take_process_ownership = True

        # check if a snapshot exists
        if self.process is not None:
            id_snapshot = self.get_snapshot_id()
            self.nlog.info("loading vm snapshot %s", id_snapshot)
            t_start = time.time()
            try:
                self.monitor_repl.loadvm(id_snapshot)
                t_end = time.time()
                log.debug("loaded snapshot in %0.2f seconds", t_end - t_start)
                self.booted_from_snapshot = True

            except QemuMonitorSnapshotLoadError:
                # kill old qemu process and snapshot
                snapshot_load_failed = True
                # terminate old qemu process
                self.process.kill()
                self.process.wait()

        if self.process is None or snapshot_load_failed:
            self.monitor_repl = QemuMonitorRepl(self)

            # build qemu shell command from template
            qemu_cmd = self._build_qemu_command(path_qemu_base_image)
            # run the qemu command
            self.process = singletons.shell_helper.run_shell_async(self.id, qemu_cmd, prefixes = [self.shell_prefix],
                                                                   # we are responsible ourselves for killing the process
                                                                   take_process_ownership=take_process_ownership)

            # we need to connect to both sockets once, first to the qemu monitor socket (this creates the serial shell socket)
            self.monitor_repl.run_commands_eager(StringIO("\n"))
            #NetUtil.wait_until_uds_reachable(self.path_uds_socket)

            booted_signal = scenario_config.get_signal_boot_completed(node_id = self.id)
            shell_prompt = scenario_config.get_shell_prompt(node_id=self.id)

            # boot signal and shell prompt supplied
            # use boot signal for boot and shell prompt for entering the shell
            if booted_signal is not None and shell_prompt is not None:
                func = NetUtil.wait_for_socket_result
                booted_signal = scenario_config.get_signal_boot_completed(node_id = self.id)
            else:
                booted_signal = scenario_config.get_shell_prompt(node_id=self.id)
                func = NetUtil.wait_for_boot

            if scenario_config.is_provisioning_boot_mode_selectors():
                # connected via unix domain socket
                self.wait_until_qemu_booted(func, self.log_path_qemu_boot,
                                            booted_signal=booted_signal,
                                            # TODO:
                                            timeout = config.get_repl_timeout()
                                            )

            else:
                raise ValueError("Unknown boot mode!")

        # notify EventSystem that the VM booted successfully
        with es.event_no_init_finish(es.EVENT_VM_BOOT) as ev:
            ev.update([self.id], 1.0)

        if not self.booted_from_snapshot:
            # connect to the serial shell
            self.run_commands_eager(StringIO("\n"))

        # notify EventSystem that the VMs shell is ready
        with es.event_no_init_finish(es.EVENT_VM_SHELL_READY) as ev:
            ev.update([self.id], 1.0)

        self.nlog.info("qemu instance running ...")

        if config.is_qemu_snapshot_boot():
            # store process singleton
            singletons.qemu_process_singletons[self.id] = self.process

        self.after_start()

    @staticmethod
    def get_qemu_sock_path(node_id):
        return PathUtil.get_temp_file_path("qemu_%s.sock" % node_id)

    def create_qemu_overlay_image(self, base_image_path):
        '''
        Create an overlay image used for write operations (based on the image `base_image_path`)

        Returns the path of the created overlay image.
        None if an error occurred.

        Parameters
        ----------
        base_image_path: str
            Absolute path to image!

        Returns
        -------
        str
        '''

        base_image_file_name = basename(base_image_path)

        # image name without file suffix
        overlay_image_name = splitext(base_image_file_name)[0]
        overlay_image_name = '%s_overlay_%s.img' % (overlay_image_name, self.id)
        # get the temp file for the final overlay image
        overlay_image_path = PathUtil.get_temp_file_path(overlay_image_name)
        # create it
        cmd_qemu_create_overlay_image = CMD_TEMPLATE_QEMU_CREATE_OVERLAY_IMAGE.format(base_image_path = base_image_path, overlay_image_path = overlay_image_path)

        # TODO: #2 : error handling
        singletons.shell_helper.run_shell(self.id, cmd_qemu_create_overlay_image, [self.shell_prefix, "create_overlay", basename(base_image_path)])

        return overlay_image_path

    ##########################################################
    ### Wait operations
    ##########################################################

    def wait_until_qemu_booted(self, func, path_log_file, booted_signal = None, timeout = None):
        '''
        Wait until the qemu instance has been booted.

        Parameters
        ---------
        path_unix_sock : str
        path_log_file : str
        booted_signal : str
            Regexp to detect that the VM has booted.
        timeout : int (optional, default is the value from the global config file)
            After which time to give up and raise QemuBootWaitTimeout.

        Raises
        ------
        QemuBootWaitTimeout
            Timeout while booting the vm.
        '''

        sock = self.wait_until_uds_reachable(return_sock=True)
        assert sock is not None

        compiled_regex = re.compile(booted_signal, flags=re.MULTILINE | re.DOTALL)
        with open(path_log_file, "w") as f:
            # TODO: REMOVE SELF REF
            # TODO: USE PARTIAL BUFFER ONLY!
            def check_fun(buf, whole_data):
                f.write(buf)
                # TODO: #35: more efficient!!!
                if compiled_regex.search(whole_data) is not None:
                    return True

            self.nlog.info("waiting for '%s'", booted_signal)

            try:
                func(sock, check_fun, read_buf_size=READ_BUF_SIZE, timeout=timeout)
            except Timeout as e:
                raise QemuBootWaitTimeout("Timeout occurred while waiting for boot completed signal ('%s') of QEMU instance: %s" % (booted_signal, self), caused_by=e)

            self.nlog.info("qemu boot completed ...")

        # TODO:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

    def make_snapshot(self, name=None):
        if not self.booted_from_snapshot:
            self.monitor_repl.make_snapshot(name=None)

    ###############################################
    ### REPLable
    ###############################################

    def run_commands_eager_check_ret_val(self, flo, *args, **kwargs):
        '''
        Overwrite this method to provide a way of checking the return values of commands executed in the REPL.
        NOTE: We expect that every line is a command and therefore checked for return value,
        '''


        commands = []
        for cmd in flo.buf.split("\n"):
            # append return value checker
            commands.append( "%s%s" % (cmd, self.exit_code_shell_cmd_checker) )

        def _return_value_checker(cmd, res):
            if not self.re_zero_ret_code.search(res):
                raise ValueError("Expected return code `0`. Command: '%s', result:\n%s" % (cmd, res))

        return self.run_commands_eager(StringIO('\n'.join(commands)),
                                       *args,
                                       return_value_checker=_return_value_checker,
                                       **kwargs
                                       )

    def run_commands(self, *args, **kwargs):

        kwargs.update({
            'brief_logger': self.nlog,
            'verbose_logger': self.nlog if config.is_log_provisioning() else None,
            'shell_prompt' : scenario_config.get_shell_prompt(node_id = self.id)
        })
        return REPLable.run_commands(self, *args, **kwargs)

    def render_script_from_flo(self, flo, **kwargs):
        '''
        Render the script from the file-like-object and inject some variables like ip addr and node id
        (from the `Interface` class)

        Returns
        -------
        str
        '''

        kwargs.update(self.get_repl_variables(kwargs))
        return render_script_from_flo(flo, **kwargs)

    # TODO: ABSTRACT AND MOVE TO REPL?
    @staticmethod
    def get_repl_variables_static(id, vars=None):
        if vars is None:
            vars = {}

        # set node id
        vars[KEYWORD_NODE_ID] = id
        # get key/value pairs from each node class
        for node_class_type in miniworld.model.network.interface.Interface.INTERFACE_ALL_CLASSES_TYPES:
            vars.update(node_class_type().get_template_dict(id))

        return vars

    def get_repl_variables(self, vars = None):
        return self.get_repl_variables_static(self.id)

    ###############################################
    ###
    ###############################################

    def set_link_mtu(self, iface, mtu):
        cmd = StringIO("ifconfig {iface} mtu {mtu}".format(iface=iface, mtu=mtu))
        self.run_commands_eager_check_ret_val(
            cmd)

    def get_ifaces(self):
        '''
        Returns
        -------
        list<str>
        '''
        return ['%s%s' % (scenario_config.get_network_links_nic_prefix(), iface_idx) for iface_idx in
                range(len(self.emulation_node.network_mixin.interfaces.filter_normal_interfaces()))]
        # res = self.run_commands_eager_check_ret_val(
        #     StringIO("ls /sys/class/net/|grep {iface_prefix}".format(iface_prefix=scenario_config.get_network_links_nic_prefix())))
        # return res.split("\n")[2:][0].split(" ")

    def set_link_mtus(self, mtu):
        for iface in self.get_ifaces():
            self.set_link_mtu(iface, mtu)