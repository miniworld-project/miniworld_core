import hashlib
import logging
import os
import re
import socket
import time
from collections import UserDict
from io import StringIO
from os.path import basename, abspath
from os.path import splitext

from miniworld.errors import QemuBootWaitTimeout
from miniworld.model.ShellProcess import ShellProcess
from miniworld.model.domain.interface import Interface
from miniworld.model.domain.node import Node
from miniworld.nodes.REPLable import REPLable
from miniworld.nodes.VirtualizationLayer import VirtualizationLayer
from miniworld.nodes.qemu.QemuMonitorRepl import QemuMonitorRepl
from miniworld.service.emulation.interface import InterfaceService
from miniworld.service.persistence.interfaces import InterfacePersistenceService
from miniworld.service.provisioning import TemplateEngine
from miniworld.service.provisioning.SocketExpect import SocketExpect
from miniworld.service.shell.shell import run_shell
from miniworld.singletons import singletons
from miniworld.util import PathUtil
from miniworld.util.NetUtil import Timeout

__author__ = 'Nils Schmidt'

###############################################
# Command templates
###############################################

CMD_TEMPLATE_QEMU_CREATE_OVERLAY_IMAGE = """
qemu-img create
    -b "{base_image_path}"
    -f qcow2
    "{overlay_image_path}"
"""


def get_cmd_template_qemu_nic():
    """

    Returns
    -------

    See Also
    --------
    http://www.linux-kvm.org/page/10G_NIC_performance:_VFIO_vs_virtio
    """
    # # TODO: #54,#55: check what vlan means for qemu
    CMD_TEMPLATE_QEMU_NIC = """
    -device {nic_model},netdev=net{vlan},mac={mac_addr}
    -netdev tap,id=net{vlan},ifname={ifname},script=no,downscript=no
    """
    return CMD_TEMPLATE_QEMU_NIC


# TODO: check for kvm!
# Ticket: #8


def is_kvm_usable():
    """
    Check if the system has kvm support and the module is not used.
    """
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
        logging.getLogger().info("Using kvm for virtualization ...")
    else:
        logging.getLogger().info("Kvm already in use or not supported! Falling back to emulation ...")


# TODO: CHANGE RAM
# Ticket: #10


def get_qemu_cmd_template():
    """
    Delay the command creation until some variables are accessable.
    """
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
# Other constants
###############################################


class QemuProcessSingletons(UserDict):
    pass


class Qemu(VirtualizationLayer, ShellProcess, REPLable):
    """
    Handles the starting of a Qemu instance.

    Attributes
    ----------
    log_path_qemu_boot : str
        The log for the qemu boot process.
    monitor_repl : QemuMonitorRepl
    """

    exit_code_identifier = "exit code:"
    exit_code_shell_cmd_checker = " ; echo -n %s$?" % exit_code_identifier
    re_zero_ret_code_text = '%s0' % exit_code_identifier
    re_zero_ret_code = re.compile(re_zero_ret_code_text, flags=re.DOTALL)

    def __init__(self, node: Node):
        VirtualizationLayer.__init__(self, node=node)

        self._interface_service = InterfaceService()
        self._interface_persistence_service = InterfacePersistenceService()

        # log file for qemu boot
        self.log_path_qemu_boot = PathUtil.get_log_file_path("qemu_boot_%s.txt" % self.node._id)

        self.monitor_repl = QemuMonitorRepl(self)

        self.booted_from_snapshot = False

        ################################
        # REPLable
        ################################

        REPLable.__init__(self)

        # unix domain socket paths
        self.path_uds_socket = self.get_qemu_sock_path(self.node._id)
        # self.uds_socket = None

    def reset(self):
        # try:
        #     self.uds_socket.shutdown(socket.SHUT_RDWR)
        # except socket.error as e:
        #     self.nlog.exception(e)
        #
        # try:
        #     self.uds_socket.close()
        # except socket.error as e:
        #     self.nlog.exception(e)

        super(Qemu, self).reset()

    # TODO: #54,#55: DOC
    def after_start(self):
        pass

    def _build_qemu_overlay_images_command(self):
        """
        Create an overlay image for each user supplied image.

        Returns
        -------
        str

        """
        # start by 1 (0 is reserved for -hda of base image!)
        index = 1
        overlay_image_cmd = ""

        for image_path in singletons.scenario_config.get_overlay_images():
            overlay_image_path = self.create_qemu_overlay_image(abspath(image_path))
            overlay_image_cmd += "%s %s" % (
                overlay_image_cmd, CMD_TEMPLATE_QEMU_MOUNT_DISK.format(image_path=overlay_image_path, index=index))
            index += 1

        return overlay_image_cmd

    # TODO: #54,#55: DOC
    def _build_qemu_nic_command(self):

        # TODO: ABSTRACT COMMAND GENERATION!
        cmd_setup_nics = []

        def add_if(_if, _if_name, vlan):
            cmd_setup_nics.append(self._build_qemu_nic_command_internal(_if, _if_name, vlan))

        cnt_normal_iface = 0
        self._logger.debug("using ifaces: '%s'", self.node.interfaces)

        # NOTE: sort the interfaces so that the Management interface is the last one
        for vlan, _if in enumerate(self.node.interfaces):

            _if_name = None
            if not Interface.InterfaceType(_if.name) in Interface.INTERFACE_TYPE_NORMAL:
                _if_name = singletons.network_backend.get_tap_name(self.node._id, _if)
            else:
                # create for each connection a tap device
                # NOTE: for each new tap device we need to adjust the `nr_host_interface`
                # NOTE: otherwise we have duplicate interface names!
                # iterate over interfaces and connections

                _if_name = singletons.network_backend.get_tap_name(self.node._id, _if)
                cnt_normal_iface += 1

            self._logger.debug('add_if(%s,%s,%s)', repr(_if), _if_name, vlan)
            add_if(_if, _if_name, vlan)

        return '\n'.join(cmd_setup_nics)

    def _build_qemu_nic_command_internal(self, _if, _if_name, vlan):
        # node classes have a common mac address prefix
        mac = InterfaceService.get_mac(node_id=self.node._id, interface=_if)
        # self._interface_persistence_service.update_mac(interface=_if, mac=mac)
        _if.mac = mac
        return get_cmd_template_qemu_nic().format(
            ifname=_if_name,
            mac_addr=mac,
            vlan=vlan,
            nic_model=singletons.scenario_config.get_qemu_nic()
        )

    def _build_qemu_command(self, path_qemu_base_image, qemu_user_addition=None):
        """
        Build the qemu cli command.

        Parameters
        ----------
        path_qemu_base_image : str
            Path to the base image used as read layer.
        qemu_user_addition : str, optional (default is the value from the scenario config file)
            Additional parameters for QEMU.
        """

        if qemu_user_addition is None:
            qemu_user_addition = singletons.scenario_config.get_qemu_user_addition(node_id=self.node._id) or ""

        log_kvm_usable()

        return get_qemu_cmd_template().format(
            kvm_support=CMD_TEMPLATE_QEMU_KVM if is_kvm_usable() else "",
            path_serial_uds_socket=self.path_uds_socket,
            path_qmp_uds_socket=self.monitor_repl.path_uds_socket,
            path_overlay_image=self.create_qemu_overlay_image(os.path.realpath(abspath(path_qemu_base_image))),
            network_interfaces=self._build_qemu_nic_command(),
            overlay_images=self._build_qemu_overlay_images_command(),
            user_addition=qemu_user_addition,
            memory=singletons.scenario_config.get_qemu_memory()
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
        # return '%s_%s' % (singletons.scenario_config.get_scenario_name(), Qemu.sha1(singletons.scenario_config.get_path_image()))
        return singletons.scenario_config.get_scenario_name()

    def _start(self, path_qemu_base_image: str, node: Node):
        """
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
        InvalidImage
        """

        if os.path.getsize(path_qemu_base_image) == 0:
            raise self.InvalidImage()

        es = singletons.event_system
        self.process = None
        snapshot_load_failed = False

        if singletons.config.is_qemu_snapshot_boot():
            self.process = singletons.qemu_process_singletons.get(self.node._id)
            take_process_ownership = False
        else:
            take_process_ownership = True

        def kill_qemu_snapshot_process():

            # kill old qemu process and snapshot
            # terminate old qemu process
            self.process.kill()
            self.process.wait()
            self.process = None

        # check if a snapshot exists
        if self.process is not None:

            # only snapshot boot if scenario did not change
            # TODO: unit test
            if singletons.simulation_manager.scenario_changed:
                snapshot_load_failed = True
                self._logger.info('scenario config changed -> no snapshot boot possible')
            else:
                id_snapshot = self.get_snapshot_id()
                self.nlog.info("loading vm snapshot %s", id_snapshot)
                t_start = time.time()
                try:
                    self.monitor_repl.loadvm(id_snapshot)
                    t_end = time.time()
                    self._logger.debug("loaded snapshot in %0.2f seconds", t_end - t_start)
                    self.booted_from_snapshot = True

                except QemuMonitorRepl.QemuMonitorSnapshotLoadError:
                    snapshot_load_failed = True

        if snapshot_load_failed:
            kill_qemu_snapshot_process()

        if self.process is None or snapshot_load_failed:
            self.monitor_repl = QemuMonitorRepl(self)

            # build qemu shell command from template
            qemu_cmd = self._build_qemu_command(path_qemu_base_image)
            # run the qemu command
            self.process = singletons.shell_helper.run_shell_async(self.node._id, qemu_cmd, prefixes=[self.shell_prefix],
                                                                   # we are responsible ourselves for killing the process
                                                                   take_process_ownership=take_process_ownership)

            # we need to connect to both sockets once, first to the qemu monitor socket (this creates the serial shell socket)
            self.monitor_repl.run_commands_eager(StringIO("\n"))
            # NetUtil.wait_until_uds_reachable(self.path_uds_socket)

            booted_signal = singletons.scenario_config.get_signal_boot_completed(node_id=self.node._id)
            shell_prompt = singletons.scenario_config.get_shell_prompt(node_id=self.node._id)

            # boot signal and shell prompt supplied
            # use boot signal for boot and shell prompt for entering the shell
            if booted_signal is not None and shell_prompt is not None:
                func = Qemu.wait_for_socket_result
                booted_signal = singletons.scenario_config.get_signal_boot_completed(node_id=self.node._id)
            else:
                booted_signal = singletons.scenario_config.get_shell_prompt(node_id=self.node._id)
                func = Qemu.wait_for_boot

            if singletons.scenario_config.is_provisioning_boot_mode_selectors():
                # connected via unix domain socket
                self.wait_until_qemu_booted(func, self.log_path_qemu_boot,
                                            booted_signal=booted_signal,
                                            # TODO:
                                            timeout=singletons.config.get_repl_timeout()
                                            )

            else:
                raise ValueError("Unknown boot mode!")

        # notify EventSystem that the VM booted successfully
        with es.event_no_init_finish(es.EVENT_VM_BOOT) as ev:
            ev.update([self.node._id], 1.0)

        if not self.booted_from_snapshot:
            # connect to the serial shell
            self.run_commands_eager(StringIO("\n"))

        # notify EventSystem that the VMs shell is ready
        with es.event_no_init_finish(es.EVENT_VM_SHELL_READY) as ev:
            ev.update([self.node._id], 1.0)

        self.nlog.info("qemu instance running ...")

        if singletons.config.is_qemu_snapshot_boot():
            # store process singleton
            singletons.qemu_process_singletons[self.node._id] = self.process

        self.after_start()

    @staticmethod
    def get_qemu_sock_path(node_id):
        return PathUtil.get_temp_file_path("qemu_%s.sock" % node_id)

    def create_qemu_overlay_image(self, base_image_path):
        """
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
        """

        base_image_file_name = basename(base_image_path)

        # image name without file suffix
        overlay_image_name = splitext(base_image_file_name)[0]
        overlay_image_name = '%s_overlay_%s.img' % (overlay_image_name, self.node._id)
        # get the temp file for the final overlay image
        overlay_image_path = PathUtil.get_temp_file_path(overlay_image_name)
        # create it
        cmd_qemu_create_overlay_image = CMD_TEMPLATE_QEMU_CREATE_OVERLAY_IMAGE.format(base_image_path=base_image_path,
                                                                                      overlay_image_path=overlay_image_path)

        # TODO: #2 : error handling
        singletons.shell_helper.run_shell(self.node._id, cmd_qemu_create_overlay_image,
                                          [self.shell_prefix, "create_overlay", basename(base_image_path)])

        return overlay_image_path

    ##########################################################
    # Wait operations
    ##########################################################

    @staticmethod
    def wait_for_socket_result(*args, **kwargs):
        buffered_socket_reader = SocketExpect(*args, **kwargs)
        return buffered_socket_reader.read()

    @staticmethod
    def wait_for_boot(*args, **kwargs):
        """
        Expect data from the socket and send a newline approx. each second.

        Raises
        ------
        Timeout
        """
        # enter shell after each select timeout
        kwargs['send_data'] = b'\n'
        buffered_socket_reader = SocketExpect(*args, **kwargs)
        return buffered_socket_reader.read()

    def wait_until_qemu_booted(self, func, path_log_file, booted_signal=None, timeout=None):
        """
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
        """

        sock = self.wait_until_uds_reachable(return_sock=True)
        assert sock is not None

        compiled_regex = re.compile(booted_signal, flags=re.MULTILINE | re.DOTALL)
        with open(path_log_file, "w") as f:
            # TODO: REMOVE SELF REF
            # TODO: USE PARTIAL BUFFER ONLY!
            def check_fun(buf, whole_data):
                f.write(buf.decode())
                # TODO: #35: more efficient!!!
                if compiled_regex.search(whole_data) is not None:
                    return True

            self.nlog.info("waiting for '%s'", booted_signal)

            try:
                func(sock, check_fun, read_buf_size=READ_BUF_SIZE, timeout=timeout)
            except Timeout as e:
                raise QemuBootWaitTimeout(
                    "Timeout occurred while waiting for boot completed signal ('%s') of QEMU instance: %s" % (
                        booted_signal, self)) from e

            self.nlog.info("qemu boot completed ...")

        # TODO:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

    def make_snapshot(self, name=None):
        if not self.booted_from_snapshot:
            self.monitor_repl.make_snapshot(name=None)

    ###############################################
    # REPLable
    ###############################################

    def run_commands_eager_check_ret_val(self, flo, *args, **kwargs):
        """
        Overwrite this method to provide a way of checking the return values of commands executed in the REPL.
        NOTE: We expect that every line is a command and therefore checked for return value,
        """

        commands = []
        flo.seek(0)
        for cmd in flo.read().split("\n"):
            # append return value checker
            commands.append("%s%s" % (cmd, self.exit_code_shell_cmd_checker))

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
            'verbose_logger': self.nlog if singletons.config.is_log_provisioning() else None,
            'shell_prompt': singletons.scenario_config.get_shell_prompt(node_id=self.node._id)
        })
        return REPLable.run_commands(self, *args, **kwargs)

    def render_script_from_flo(self, flo, **kwargs):
        """
        Render the script from the file-like-object and inject some variables like ip addr and node id
        (from the `Interface` class)

        Returns
        -------
        str
        """

        kwargs.update(self.get_repl_variables(kwargs))
        return TemplateEngine.render_script_from_flo(flo, **kwargs)

    # TODO: ABSTRACT AND MOVE TO REPL?
    @staticmethod
    def get_repl_variables_static(id, vars=None):
        if vars is None:
            vars = {}

        # set node id
        vars[TemplateEngine.KEYWORD_NODE_ID] = id
        # get key/value pairs from each node class
        # TODO: adjust to new InterfaceService

        return vars

    def get_repl_variables(self, vars=None):
        return self.get_repl_variables_static(self.node._id)

    ###############################################
    ###
    ###############################################

    def set_link_mtu(self, iface, mtu):
        cmd = StringIO("ifconfig {iface} mtu {mtu}".format(iface=iface, mtu=mtu))
        self.run_commands_eager_check_ret_val(
            cmd)

    def get_ifaces(self):
        """
        Returns
        -------
        list<str>
        """
        interface_service = InterfaceService()
        return ['%s%s' % (singletons.scenario_config.get_network_links_nic_prefix(), iface_idx) for iface_idx in
                range(len(interface_service.filter_normal_interfaces(self.node.interfaces)))]
        # res = self.run_commands_eager_check_ret_val(
        #     StringIO("ls /sys/class/net/|grep {iface_prefix}".format(iface_prefix=singletons.scenario_config.get_network_links_nic_prefix())))
        # return res.split("\n")[2:][0].split(" ")

    def set_link_mtus(self, mtu):
        for iface in self.get_ifaces():
            self.set_link_mtu(iface, mtu)
