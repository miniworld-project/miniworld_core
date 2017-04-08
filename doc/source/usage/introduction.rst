Introduction
============

MiniWorld is an acronym for `Mobile Infrastructure'n'Network Integrated World`.
Its purpose is to help evaluating/developing any kind of software that relies on network.
MiniWorld requires you to deploy the software-under-test in a VM.
A custom network topology can then be used to interconnect the VMs, additionally simulating link impairment such as delay, loss etc.

MiniWorld supports both wired and wireless emulation.
In the following, you will learn how to create a B.A.T.M.A.N. advanced topology with 3 nodes based on OpenWRT:

#. In the following you will learn how to deploy software in an OpenWRT image. We will use B.A.T.M.A.N advanced for the routing on layer 2.
#. Afterwards you will see the basic unit MiniWorld uses, a **scenario config**.
#. Finally, you will start 3 VMs interconnected in a chain where node 1 routes to node 3 with the help of B.A.T.M.A.N.


.. contents:: Table of Contents
   :local:

Deploy OpenWRT Image
--------------------

First, get OpenWRT:

.. code-block:: bash

   wget https://downloads.openwrt.org/chaos_calmer/15.05/x86/kvm_guest/openwrt-15.05-x86-kvm_guest-combined-ext4.img.gz
   gunzip openwrt-15.05-x86-kvm_guest-combined-ext4.img.gz

The image does not have batman installed yet, hence we need to boot the VM with KVM.
We leverage the qemu user network backend to get internet access. Note that **ICMP** is not working in the user network backend.

.. code-block:: bash

   kvm -nographic -netdev user,id=net0 -device virtio-net-pci,netdev=net0 openwrt-15.05-x86-kvm_guest-combined-ext4.img

You need to press enter until you see the following login banner:

.. code-block:: bash

   _______                     ________        __
   |       |.-----.-----.-----.|  |  |  |.----.|  |_
   |   -   ||  _  |  -__|     ||  |  |  ||   _||   _|
   |_______||   __|_____|__|__||________||__|  |____|
         |__| W I R E L E S S   F R E E D O M
   -----------------------------------------------------
   CHAOS CALMER (15.05.1, r48532)
   -----------------------------------------------------
   * 1 1/2 oz Gin            Shake with a glassful
   * 1/4 oz Triple Sec       of broken ice and pour
   * 3/4 oz Lime Juice       unstrained into a goblet.
   * 1 1/2 oz Orange Juice
   * 1 tsp. Grenadine Syrup
   -----------------------------------------------------
   root@OpenWrt:/#

Next, we need to get an IP on the **eth0** network interface via DHCP.

Edit `/etc/config/network` such that the config block for interface **lan** looks like the following:

.. code-block:: bash

   config interface 'lan'
           option ifname 'eth0'
           option proto 'dhcp'


Afterwards, apply the new network settings:

.. code-block:: bash

   /etc/init.d/network restart

Now, verify eth0 has an ip address

.. code-block:: bash

   root@OpenWrt:/# ifconfig eth0
   eth0      Link encap:Ethernet  HWaddr 52:54:00:12:34:56
             inet addr:10.0.2.15  Bcast:10.0.2.255  Mask:255.255.255.0
             inet6 addr: fe80::5054:ff:fe12:3456/64 Scope:Link
             UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
             RX packets:44 errors:0 dropped:0 overruns:0 frame:0
             TX packets:66 errors:0 dropped:0 overruns:0 carrier:0
             collisions:0 txqueuelen:1000
             RX bytes:7028 (6.8 KiB)  TX bytes:7416 (7.2 KiB)

We can proceed with our actual intention, to prepare batman advanced on the OpenWrt image:

.. code-block:: bash

   opkg update
   opkg install kmod-batman-adv
   opkg install batctl

Now that batman is installed, power off the VM. We are going to use this image as a read-layer later.

.. code-block:: bash

   poweroff


Prepare Scenario Config
-----------------------

For simplicity, we will work from the miniworld repo directory.

This is the scenario config we are going to use. Save in in the directory where you cloned MiniWorld as **batman_adv.json**.
Moreover, make sure that the openwrt image on line 8 is named correctly.

.. literalinclude:: examples/batman-adv/scenario.json
   :language: json
   :emphasize-lines: 8,36
   :linenos:

Run Scenario
------------

Now we have everything ready. We will use 2 shells. In the first, we are going to start MiniWorld's RPC server.
In the second we are using a command-line tool to start the scenario.

In **shell 1** start the RPC Server:

.. code-block:: bash

   ./start_server.sh

.. code-block:: bash

   (mw) root@miniworld-fusion:~/repos/miniworld-project/miniworld_core# ./start_server.sh &
   ...
   INFO __main__ <module>: rpc server running

.. note::

   If for any reasons, MiniWorld won't stop correctly, you can force the RPC server to exit and perform the necessary cleanup with **./cleanup.sh**

In **shell 2**, start the scenario and wait until the command returns:

.. code-block:: bash

   ./mw.py start batman_adv.json



In **shell 1** you should see the 3 OpenWRT VMs booting. There is not yet any network set up:

.. code-block:: bash

   INFO MiniWorld 2017-04-06 21:19:52,598 RPCServer: starting in local mode ...
   INFO MiniWorld 2017-04-06 21:19:52,599 Scenario: setting scenario config file '{"provisioning": {"image": "openwrt-15.05-x86-kvm_guest-combined-ext4.img", "regex_shell_prompt": "r
   oot@OpenWrt:/#", "shell": {"pre_network_start": {"shell_cmds": ["until ifconfig eth0; do echo -n . && sleep 1; done", "ifconfig eth0 0.0.0.0", "modprobe batman-adv", "batctl if ad
   d eth0", "iperf -s &"]}}}, "cnt_nodes": 3, "network": {"core": {"mode": "lan", "topologies": [[0, "tests/core_topologies/chain5.xml"]]}, "links": {"configuration": {"nic_prefix":
   "bat"}, "model": "miniworld.model.network.linkqualitymodels.LinkQualityModelRange.LinkQualityModelWiFiExponential"}}, "scenario": "batman-adv", "walk_model": {"name": "core"}, "qe
   mu": {"nic": {"model": "virtio-net-pci"}}}'
   INFO SimulationManager start: responsible for nodes: 1,2,3
   INFO SimulationManager start: using interface link quality: {'bandwidth': None, 'loss': 0}
   miniworld.model.network.linkqualitymodels.LinkQualityModelRange LinkQualityModelWiFiExponential
   INFO MiniWorld 2017-04-06 21:19:52,611 LinkQualityModelRange: max_bandwidth: 54000
   ...
   1>>>  qemu boot completed ...
   1>>>  qemu instance running ...
   1>>>  node running ...
   1>>>  until ifconfig eth0; do echo -n . && sleep 1; done
   1>>>  ifconfig eth0 0.0.0.0
   1>>>  modprobe batman-adv
   1>>>  batctl if add eth0
   1>>>  iperf -s &
   1>>>  pre_network_shell_commands done
   1>>>  # name management interface
   1>>>  last_eth=$(ls -1 /sys/class/net/|grep bat|tail -n 1)
   1>>>  ip link set name mgmt $last_eth
   ...
   1>>>  savevm batman-adv
   ...


VM Access
---------

You can enter the shell of each VM with the following command, exit with **CTRL-D**.

.. code-block:: bash

   socat `tty`,raw,echo=0,escape=0x4 UNIX-Connect:/tmp/MiniWorld/qemu_1.sock


It is preferable to include the following in your ~/.{bash,zsh}rc

.. code-block:: bash

   function mw_qemu {
       path=/tmp/MiniWorld/qemu_$1.sock
       echo "connecting to $path"
       socat `tty`,raw,echo=0,escape=0x4 UNIX-Connect:$path
   }


Then you can use

.. code-block:: bash

   mw_qemu <node_id (1+)>

