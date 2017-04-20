VM Shell Access
===============

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
