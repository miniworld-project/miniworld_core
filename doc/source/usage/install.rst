Install
=======

.. contents:: Table of Contents
   :local:

.. note::

   MiniWorld is tested on Ubuntu 16.04.2 LTS and Ubuntu 14.04.5 LTS (Travis CI).
   Probably the latest HWE stack is required.

Docker-compose
--------------

For ease of use we decided to use docker-compose instead of "pure" Docker since the Docker commands can get very long.
If you decide to use MiniWorld with docker-compose which is highly recommended, just follow the steps at https://docs.docker.com/compose/install/ to install docker-compose.

Then follow the instructions at the `MiniWorld Playground repository <https://github.com/miniworld-project/miniworld_playground/>`_ on how to use docker-compose.
Afterwards you should visit the :doc:`introduction page <introduction>`.

Without Docker
--------------

.. code-block:: bash

   git clone https://github.com/miniworld-project/miniworld_core.git
   git checkout <master|nightly>

Install system dependencies

.. code-block:: bash

   # Mostly copied from the `MiniWorld Dockerfile <https://github.com/miniworld-project/miniworld_core>`_:
   sudo apt-get update
   sudo apt-get install ebtables iproute2 qemu-kvm bridge-utils bison flex libdb-dev psmisc curl wget kmod libdb5.3-dev libxtables11 iptables-dev pkg-config socat

You should install the python packages as ``root`` since advanced privileges are required for kvm, network switching etc.

.. code-block:: bash

   sudo su

Use a virtualenv for MiniWorld or set python3 as system default.

.. code-block:: bash

   pip install virtualenv
   virtualenv -p python3 mw
   source mw/bin/activate

Install python dependencies:

.. code-block:: bash

   cd miniworld_core
   pip install --upgrade .\[server,develop\]

Install iproute2:

.. code-block:: bash

   ./scripts/install_iproute2.sh

