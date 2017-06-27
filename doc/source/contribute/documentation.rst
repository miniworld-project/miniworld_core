Documentation
=============

.. contents:: Table of Contents
   :local:

Documentation should be edited and tested locally.
If you push to a remote branch for which there are hooks on `readthedocs.org <http://readthedocs.org/projects/miniworld-core>`_ (currently master and nightly), the documentation will be build and updated accordingly.

The documentation is build with `sphinx <http://www.sphinx-doc.org/en/stable>`_.
We use `reStructuredText <http://docutils.sourceforge.net/rst.html>`_ sine it offers more possibilities compared to markdown.
Either learn reStructuredText from the website's `quick reference <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_ or simply have a look at the source of existing documentation (click on `Show Source` on the side bar).

If you have not installed sphinx, install it with pip (works for us on python2.7):

.. code-block:: bash

   pip install sphinx

Afterwards go to the doc directory and create the documentation:

.. code-block:: bash

   cd doc
   make clean
   make html

Open the html file:

.. code-block:: bash

   open build/html/index.html

.. note::

   If you encounter problems, try it within a virtualenv:

   .. code-block:: bash

      pip install virtualenvwrapper
      source virtualenvwrapper_lazy.sh
      mkvirtualenv -p python3 <envname>
      workon <envname>
      # try again ...
