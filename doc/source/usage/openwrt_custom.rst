OpenWRT Custom Software
=======================

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
