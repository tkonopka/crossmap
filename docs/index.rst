crossmap documentation
======================

``crossmap`` is proof-of-concept software for the exploration of heterogeneous
datasets that are composed of text.


Features
~~~~~~~~

The software is designed for use with any text-based data.
It manages a database and indexes of nearest neighbors to enable
searching via unstructured queries and to enable tuning through
user-driven learning.

 - **Querying heterogeneous data**. ``crossmap`` can manage multiple datasets at once. It can query each dataset individually, or use a diffusion process to utilize information in one dataset to adjust queries against another.

 - **User-driven learning**. ``crossmap`` can manage and update user-maintained repositories and use these data to fine-tune search results. This allows users to train the search mechanism in real-time.

 - **Interactive user interface**. The software provides a graphical user interface for interactive data exploration. The interface is based on chat and is accessible via a web browser.

 - **Programmatic interface**. ``crossmap`` can also be used through a command-line interface suitable for batch processing.





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
   training


..
  Indices and tables
  ==================

  * :ref:`genindex`
  * :ref:`modindex`
  * :ref:`search`
