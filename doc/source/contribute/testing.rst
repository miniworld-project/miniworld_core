Testing
=======

.. contents:: Table of Contents
   :local:

Run tests
---------

Docker-compose
^^^^^^^^^^^^^^

.. code-block:: bash

   ./scripts/start.sh
   ./scripts/test.sh

Locally
^^^^^^^

.. code-block:: bash

   mwserver
   pytest -x -vvvvv -m "not examples" tests/

Further Tips
------------

To drop to pdb and do not terminate QEMU processes add the `--pdb` flag to pytest or run `./scripts/test.sh --pdb`


