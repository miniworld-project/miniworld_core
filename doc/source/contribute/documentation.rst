Documentation
=============

Documenation should be edited locally.

For that purpose sphinx has to be installed.

::

    pip install sphinx

Afterwards go to the doc directory and create the documentation.

.. code-block:: bash

   cd doc
   make clean
   make html

   # open build/html/index.html
