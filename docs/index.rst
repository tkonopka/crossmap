crossmap
========

`crossmap <https://github.com/tkonopka/crossmap>`_  is proof-of-concept
software for the exploration of text-based datasets.

The software manages a database and indexes of nearest neighbors, and
provides protocols for querying data using unstructured queries. It can be
used with any text-based data, but its feature set is influenced by the needs
in terms of data exploration in the biological sciences.

As an example, a crossmap instance can be loaded with text documents
containing gene pathways, diseases phenotypes, and disease descriptions. Its
protocols can then be used to search this knowledge-base using gene sets,
phenotypes, keywords, or any combination at once.


Features
~~~~~~~~

- **Querying heterogeneous data**. crossmap can manage multiple datasets at
  once. Queries can be performed against each dataset individually. Protocols
  includes classical search and data decomposition.

- **Data diffusion**. Data diffusion is an approach for data imputation.
  It uses information in one dataset to adjust augment user queries before
  carrying out classical search or data decomposition.

- **User-driven learning**. crossmap can record data items from users (in batch
  and using an interactive interface) and use these data to fine-tune search
  results. This allows users to train the search mechanism in real-time.

- **Interactive user interface**. The software provides a graphical user
  interface for interactive data exploration. The interface is based on chat
  and is accessible via a web browser.

- **Programmatic interface**. All software features are accesible through a
  command-line interface that is suitable for batch processing.


Getting started
~~~~~~~~~~~~~~~

There are a few steps to start using crossmap in a practical project. The
brief bullets summarize these stages, and other documentation pages provide
in-depth information on each topic.

- **Installation**. The software and dependencies are installed.
  This may require installation of python, javascript, and docker.
  `[more] <install.html>`_

- **Instance configuration**. A configuration file is prepared to instruct
  the software what data to load, and how the data should be indexed.
  Configuration files offer many settings, but a minimal/typical
  file consists of just a few lines. `[more] <configurations.html>`_

- **Instance build**. Prepared data are copied into an 'instance'.
  During this stage, the software transfer data into a database,
  encodes data items into numeric representations, and constructs indexes
  for efficient querying. After this stage, the instance is ready for use.
  `[more] <cli.html>`_

- **Querying**. A crossmap instance is queried using a command-line or
  graphical user interface. Queries can consist of simple searches, searches
  enhanced by diffusion processes, and decomposition queries.

- **Training**. Optionally, an existing instance can be trained with
  additional data. New data can be added in batch using the
  command-line interface, or one item at a time using the graphical
  interface. The new data can then be used to modify and fine-tune search
  results.

crossmap processes text-based data in yaml format. Data must be prepared in
this format during an initial project setup and throughout querying.

- **Data preparation**. Raw data are prepared into a format that can be
  processed by the crossmap software. This data format is not
  highly structured, so it can accommodate many types of text-based data.
  `[more] <data_format.html>`_

Many features are available through a graphical user interface.

- **Chat-based interface**. Optionally, instances can be explored via a
  graphical user interface that runs within a web browser. The interface
  supports data querying and training. `[more] <chat.html>`_


.. toctree::
   :maxdepth: 2
   :caption: Documentation:

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
