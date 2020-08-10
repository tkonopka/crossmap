Configurations
==============

Each crossmap instance is configured via a ``yaml`` file. The settings determine
how data are stored internally. Many of the settings affect the build stage
and it is important that they remain unchanged at all subsequent stages.


Concise configuration
~~~~~~~~~~~~~~~~~~~~~
 
A concise configuration might be as follows:

.. code:: yaml

    name: instance-name
    comment: short comment
    data:
      primary: path-to-primary.yaml.gz
      secondary: path-to-secondary.yaml.gz
    tokens:
      k: 6
    features:
      max_number: 20000
      weighting: [0, 1]

For a line-by-line description of these settings, refer to the complete
settings guide below. Despite some caveats involved with some the settings,
the configuration specifies a ``name`` for the instance, two ``data`` sources,
that data should be parsed into 6-mers, and there will be maximum of 20,000 unique
k-mers used in the data representations.

Of the settings shown in the concise representation, only ``name`` and
``data`` are strictly required. ``crossmap`` can fill in default values
for all the others. Nonetheless, including some of the settings can make
explicit how data will be represented in the back-end.


Complete configuration
~~~~~~~~~~~~~~~~~~~~~~

Configuration files can control many more settings than those in
the concise example. A small group of settings are defined at the root level
of the configuration file, and the remainder are grouped into headings.

The sections below describe each group and each setting individually. Each
section starts with a complete list of settings and representative values.
The setting are then described individually.


Core settings
^^^^^^^^^^^^^

Core settings appear at the top of a configuration file, without a category.

Example:

.. code:: yaml

    name: instance-name
    comment: brief description of the instance


Description:

- ``name`` [string] - an identifier that distinguishes one crossmap instance
  from another. This name is used as a database name as well as in the directory
  name where instance files are stored. It cannot include spaces or special
  characters.

- ``comment`` [string] - a brief description of the crossmap
  instance. This string is only for human readability; it is not used in any
  computations.


data
^^^^
 
The ``data`` subgroup specifies the locations of data files to be included in
the crossmap database.

Example:

.. code:: yaml

    data:
      primary: path-to-primary.yaml.gz
      secondary: path-to-secondary.yaml.gz

Description:

- Each line under ``data`` consists of a label and value pair. In the example,
  the labels are `primary` and `secondary`. However, the labels can be
  arbitrary. Each label is used to identify a dataset. The ``data`` group must
  specify at least one dataset label; there is no upper limit.
 
 
 
tokens
^^^^^^
 
Settings in the 'tokens' group determine how raw data are partitioned into smaller
components, called tokens or k-mers.

Example:

.. code:: yaml

    tokens:
      k: 6
      alphabet: ABCDEFGHIJKLMNOPQRSTUVWXYZ

Descriptions:

- ``k`` [integer] - length of kmers.
- ``alphabet`` [string] - the character set that are allowed to exist in
  tokens. Other characters are removed. The default alphanet consists of
  alphanumeric characters, plus some punctuation like hyphens.


features
^^^^^^^^

Settings in the `features` subgroup control how tokens parsed out of the raw
data are used to build a numerical representation of the data.

Example:

.. code:: yaml

    features:
      data:
        documents: path-to-documents.yaml.gz
      map: path-to-features.tsv.gz
      max_number: 20000
      min_count: 2
      weighting: [0, 1]

Description:

- ``data`` [dictionary with key:file path pairs] - dictionary with file paths
  to auxiliary yaml files with documents. These documents are scanned and
  parsed just like the documents in the `data` group, but are not entered
  into the database.
- ``map`` [file path] - path to a file with a tab-separated table of
  features and weights. When specified, the features listed in the file are
  used as-is. This settings overrides de-novo feature discovery and overrides
  other settings in this group. Defaults to None/null, which indicates that
  features should be extracted and weighted using the datasets in the `data`
  group and in the `data` dictionary under `features`.
- ``max_number`` [integer] - total number of features is estimated from the
  contents of the data files. The number of features, however, is capped at
  this threshold. Defaults to 0, interpreted as an unlimited number of features.
- ``min_count`` [integer] - used to discard some features observed in very few
  data items. Defaults to 0.
- ``weighting`` [array of two numbers] - Used to determine the weight
  of each feature with a linear formula, `weight = a + b * IC`, where `IC` is
  the information content of the feature (logarithm of inverse frequency in the
  datasets). The weighting array defaults to [0, 1].


indexing
^^^^^^^^

``indexing`` settings determine the quality of the nearest-neighbor
index.

Example:

.. code:: yaml

    indexing:
      trim_search: 1
      build_quality: 500
      search_quality: 200

Description:

- ``trim_search`` [integer] - relevant values are 0/1, used to toggle trimming
  of search results to items with distances < 1-(1e-6). Default setting is 1,
  which means search results avoid items that have distance near one.
- Both ``build_quality`` and ``search_quality`` are integers passed to the
  ``nmslib`` library. Higher values indicate a more precise calculation of
  nearest neighbors, but at the cost of a slower running time. Lower values
  can increase speed, but lead to more searches returning imperfect outcomes.


diffusion
^^^^^^^^^

``diffusion`` settings help to optimize the diffusion process.

Example:

.. code:: yaml

    diffusion:
      threshold: 0.0
      num_passes: 2

Description:

- ``threshold`` [floating point number] - determines whether thresholding
  can be applied to limit the number of imputed features.
- ``num_passes`` [integer] - number of diffusion rounds applied on
  each vector. Multiple passes allow coupling diffusion processes driven
  by several data collections.



cache
^^^^^

The ``cache`` settings are not used during the build stage, but rather affect
runtime during subsequent stages (prediction, decomposition, server mode).
The settings specify how many objects from the disk database can be
cached in memory, and thus provide a means to speed up execution at the
cost of increasing memory use.

Example:

.. code:: yaml

    cache:
      counts: 20000
      ids: 10000
      titles: 50000
      data: 20000

Description:

- ``counts`` [integer] - number of database rows pertaining to diffusion
- ``ids`` [integer] - number of mappings between internal identifiers and
  user-specified object ids
- ``titles`` [integer] - number of object titles
- ``data`` [integer] - number of data items


logging
^^^^^^^

``logging`` settings control the amount of information that is output to
the log / console at runtime.

Example:

.. code:: yaml

    logging:
      level: INFO
      progress: 50000

Description:

- ``level`` [string] -  one of 'INFO', 'WARNING', 'ERROR'; determines
  logging level; can be over-ridden by a command line argument
- ``progress`` [integer] - interval at which progress messages are
  displayed during tbe build stage
 

server
^^^^^^

When crossmap is run in server mode, there are additional parameters that
determine who the program communicates with the network.

Example:

.. code:: yaml

    server:
      db_host: 127.0.0.1
      db_port: 8097
      api_port: 8098
      ui_port: 8099

Description:

- ``db_host`` [character] - url to a mongodb database server. **Note:** A value for ``db_host`` can also be provided via an environment variable ``MONGODB_HOST``.
- ``db_port`` [integer] - the network port for the mongodb database. **Note:** A value for ``db_port`` can also be provided via an environment variable ``MONGODB_PORT``.
- ``api_port`` [integer] - the network port on localhost that accepts requests
- ``ui_port`` [integer] - the network port on localhost that displays the
  graphical user interface

