Install
=======

.. contents:: Table of Contents
   :local:

Docker-compose
--------------

For ease of use we decided to use docker-compose instead of "pure" Docker since the Docker commands can get very long.
If you decide to use MiniWorld with docker-compose which is highly recommended, just follow the steps at https://docs.docker.com/compose/install/ and step over to the :doc:`introduction` or :doc:`examples` page.

Without Docker
--------------

.. code-block:: bash

   git clone https://github.com/miniworld-project/miniworld_core.git
   git checkout <master|nightly>

Install system dependencies

.. code-block:: bash

   # Mostly copied from the `MiniWorld Dockerfile <https://github.com/miniworld-project/miniworld_core>`_:
   sudo apt-get update
   sudo apt-get install ebtables iproute2 qemu-kvm bridge-utils bison flex libdb-dev psmisc curl wget kmod libdb5.3-dev

Install python dependencies:

Use a virtualenv for MiniWorld or set python3 as system default.
You should install the python packages as root since advanced privileges are required.

.. code-block:: bash

   cd miniworld_core
   pip install --upgrade .\[server,develop\]


