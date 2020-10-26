Graphical user interface
========================

*This page describes how to launch the graphical user interface (GUI).
For documentation on how to use the GUI, see pages on*
`interactive use <chat.html>`_.

The graphical user interface (GUI) consists of two separate servers working
together. It is recommended to use two separate consoles in order to launch these servers. This will allow you to monitor their state and to shut them down at the end.

Starting up
~~~~~~~~~~~

In a first console, launch the back-end server.

.. code:: bash

    python crossmap.py server --config path-to-config.yaml


The command requires access to a configuration file in order to identify what
databases and indexes should be made available for querying. The command
should output messages about its status.

In a second console, launch the front-end server.

.. code:: bash

    python crossmap.py gui --config path-to-config.yaml


This command should also provide output on status. 

Upon launching the front-end server, a new tab should open in your default
web browser. The content of that tab will be a chat-like interface, with the
first message displaying the datasets available to query. More information
about using this interface is available `here <chat.html>`_.


Shutting down
~~~~~~~~~~~~~

To shut down the services, press ``Ctrl+C`` in each of the two consoles.

