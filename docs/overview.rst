Overview
========

From a user's perspective, a project using crossmap consists of distinct
stages.

- **Installation**. The software and dependencies are installed.
  This may require installation of python, javascript, and docker.

- **Data preparation**. Raw data are prepared into a format that can be
  processed by the crossmap software. This data format is not
  highly structured, so it can accommodate many types of text-based data.

- **Instance configuration**. A configuration file is prepared to instruct
  the software what data to load, and how the data should be indexed.
  Configuration files offer many settings, but a minimal/typical
  file consists of just a few lines.

- **Instance build**. Prepared data are copied into an 'instance'.
  During this stage, the software transfer data into a database,
  encodes data items into numeric representations, and constructs indexes
  for efficient querying. After this stage, the instance is ready for use.

- **Querying**. A crossmap instance is queried using a command-line or
  graphical user interface. Queries can consist of simple searches, searches
  enhanced by diffusion processes, and decomposition queries.

- **Training**. Optionally, an existing instance can be trained with
  additional data. New data can be added in batch using the
  command-line interface, or one item at a time using the graphical
  interface. The new data can then be used to modify and fine-tune search
  results.

