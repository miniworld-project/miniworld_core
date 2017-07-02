Use a custom VM
===============


.. contents:: Table of Contents
   :local:

In general MiniWorld can run any OS/software that runs under KVM.
For automation purposes however, MiniWorld requires access to the `serial console of a VM. This enables MiniWorld to provision the VM without network/SSH access.
The downside of this approach is that a shell has to be spawned on the serial console. Moreover, root has to be logged in automatically.
Note that `OpenWrt <https://downloads.openwrt.org>`_ is usable out of the box with MiniWorld.

The required modifications depend on the **init system**.

Debian 8 (Systemd)
------------------

The following illustrates how VM images can be created and deployed. Moreover, it points out the required modifications of a VM such that it works with MiniWorld.
New images can be created with the commands shown in the following.



.. code-block:: bash
   :linenos:

   wget http://saimei.acc.umu.se/debian-cd/8.6.0/amd64/iso-cd/ debian-8.6.0-amd64-netinst.iso
   qemu-img create -f qcow2 debian_8.qcow2 5G
   kvm -boot once=dc -vga qxl -spice port=5900,addr=127.0.0.1,disable-ticketing -redir :<host_port>::22 -cdrom debian-8.6.0-amd64-netinst.iso debian_8.qcow2


First, an image has to be downloaded. Debian 8 (Jessie) is used in the example (line 1).
Then a QCOW2 image is created which serves as the hard disk for the VM. The VM is booted from the live image (line 2). The user can then install the OS to the harddisk of the VM. Note that starting KVM without the -vga switch does not work for images which have a graphical installer. The UI can be accessed with spice compatible programs.
After installing the VM, it can be started without the live image by leaving out the –boot and the -cdrom command line switches. The -redir CLI switch redirects the port 22 to localhost. This enables accessing the VM via ssh if the network is configured by means of Dynamic Host Configuration Protocol (DHCP) in the VM. Moreover, the VM can access the internet for further deployment. Note that ICMP does not work with the user network backend (SLIRP) of Qemu.
The modifications of the VM required by MiniWorld depend on the boot loader and the init system. For systems with grub, the serial console can be enabled by modifying the /etc/default/grub config file.

.. note::

   Installation hints for the application **remote-viewer**:

   Linux: `apt-get install libvirt-bin`

   Mac: `brew cask install remoteviewer`

Run the following command to connect via spice to the VM:

.. code-block:: bash

   remote-viewer spice://0.0.0.0:5900

The following listing enables the serial console and disables the new NIC naming scheme for Ubuntu 16.04 systems.
The command `update-grub` has to be run after the file is modified.

.. code-block:: bash

   GRUB_CMDLINE_LINUX="console=tty1 console=ttyS0 net.ifnames=0 biosdevname=0"
   GRUB_TIMEOUT=0
   GRUB_TERMINAL=console

This allows the NetworkConfigurator to configure based on the `ethX` naming scheme. The timeout is not required, but improves VM boot times.
The modification of grub redirects the kernel boot log to the `serial console so that MiniWorld can detect when the boot process is over.
There is no autologin mechanism implemented. Therefore, the root user is expected to be logged in on the serial console’s shell. The modification depends on the init system. Ubuntu 16.04 uses Systemd while older versions used the Upstart init system.

The modifications for both systems are depicted in the following listings respectively.

Systemd
^^^^^^^

.. code-block:: bash

   mkdir /etc/systemd/system/serial-getty@.service.d
   cat << EOF >
   /etc/systemd/system/serial-getty@.service.d/override.conf
   [Service]
   ExecStart=
   ExecStart=-/sbin/agetty --keep-baud 115200,38400,9600 -a root %I $TERM
   EOF

Upstart
^^^^^^^

.. code-block:: bash

   T0:23:respawn:/sbin/getty -L ttyS0 --autologin root 38400 vt100

Another reduction of VM boot times can be achieved by disabling any DHCP configuration.