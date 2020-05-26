Graphical user interface
========================

The graphical user interface (GUI) consists of two separate servers working
together. In order to launch these servers, monitor their state, and be able
to shut them down, it is recommended to use two separate consoles.

In a first console, launch the back-end server,

.. code:: bash

    python crossmap.py server --config path-to-config.yaml


The command requires access to a configuration file in order to identify what
databases and indexes should be made available for querying. The command
should output messages about its status.

In a second console, launch the front-end server,

.. code:: bash

    python crossmap.py gui --config path-to-config.yaml


This command should also provide output on status. 

If both components launch correctly, a new tab should open in your default
web browser. The content of that tab will be a chat-like interface, with the
first message displaying the datasets available to query.

