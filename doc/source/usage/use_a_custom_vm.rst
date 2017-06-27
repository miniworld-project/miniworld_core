Use a custom VM
===============


.. contents:: Table of Contents
   :local:

In general MiniWorld can run any OS/software that runs under KVM.
For automation purposes however, MiniWorld requires access to the **serial console** of a VM. This enables MiniWorld to provision the VM without network/SSH access.
The downside of this approach is that a shell has to be spawned on the serial console. Moreover, root has to be logged in automatically.
Note that **OpenWrt** TODO: link is usable out of the box with MiniWorld.

The required modifications depend on the **init system**.

Systemd
-------

Upstart
-------

SysVinit
--------
