crossmap documentation
======================

`Crossmap <https://github.com/tkonopka/crossmap>`_  is proof-of-concept
software for the exploration of text-based datasets.

The software manages a database and indexes of nearest neighbors, and
provides protocols for querying data using unstructured queries. It can be
used with any text-based data, but its feature set is influenced by the needs
in terms of data exploration in the biological sciences.


Features
~~~~~~~~

- **Querying heterogeneous data**. crossmap can manage multiple datasets at
  once. Queries can be performed against each dataset individually. Protocols
  includes classical search and data decomposition.

- **Data diffusion**. Data diffusion uses information in one dataset to
  adjust queries against another dataset.

- **User-driven learning**. crossmap can record data items from users (in batch
  and using an interactive interface) and use these data to fine-tune search
  results. This allows users to train the search mechanism in real-time.

- **Interactive user interface**. The software provides a graphical user
  interface for interactive data exploration. The interface is based on chat
  and is accessible via a web browser.

- **Programmatic interface**. crossmap can also be used through a command-line
  interface suitable for batch processing.




.. toctree::
   :maxdepth: 2
   :caption: User's guide:

   overview
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
