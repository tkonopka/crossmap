crossmap documentation
======================

``crossmap`` is proof-of-concept software for the exploration of heterogeneous
datasets. The software manages a database and indexes of nearest neighbors to enable
searching data via unstructured queries and to enable tuning through
user-driven learning.


Paradigm
~~~~~~~~




Features
~~~~~~~~

The software is designed to facilitate exploration of any text-based data.
Its feature set, however, is strongly motivated by data challenges in the life
sciences.

 - **Querying heterogeneous data**. ``crossmap`` can manage multiple datasets at once. It can query each dataset individually, or use a diffusion process to utilize informationin one dataset to adjust queries against another.

 - **User-driven learning**. ``crossmap`` can manage small, user-maintained, data repositories and use these data to fine-tune search results. This allows users to train the search mechanism in real-time.

 - **Interactive user interface**. The software provides a graphical user interface for interactive data exploration. The interface is based on chat and is accessible via a web browser.





.. toctree::
   :maxdepth: 2
   :caption: User's guide:

   install
   configurations
   cli
   gui
   deployment

.. toctree::
   :maxdepth: 2
   :caption: Preparing datasets:

   data_format
   crossprep

.. toctree::
   :maxdepth: 2
   :caption: Interactive use:

   chat
   controller



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
