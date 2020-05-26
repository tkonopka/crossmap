Command-line interface
======================

The ``crossmap`` software is a single command-line interface that can be
used for several distinct tasks, including building new instances and
for performing queries.

The interface is invoked with the following pattern:

.. code:: bash

    python crossmap.py ACTION --config config.yaml \
                       --PARAM_1 VAL_1 --PARAM_2 VAL_2 ... \
                       --FLAG_1 ...

 
The first argument is always an action code, and the latter settings are
provided in parameter/value pairs or as flags.
 
One of the parameters is usually ``--config`` and its value is a path to a
configuration file (above, the file is assumed to be ``config.yaml``).
The remaining arguments change depending on the desired action.


Building instances
~~~~~~~~~~~~~~~~~~

Building a new instance requires a configuration file in a yaml format.
Assuming this file is called ``config.yaml``, the build command is

.. code:: bash

    python crossmap.py build --config config.yaml

This provides a moderate level of logging that help track progress. It is
possible to adjust the level of logging via the ``--logging`` argument.


Search & decomposition
~~~~~~~~~~~~~~~~~~~~~~

Once an instance is created, all its files are stored in a directory adjacent
to its configuration file. Search and decomposition read an external data
file and compare objects therein to the contents of the instance.
  
Data file must be prepared in a yaml format, for example using one of the
data preparation/conversion utilities. Assuming the data file is called
``data.yaml``, search and decomposition are performed as follows
  
.. code:: bash

    python crossmapy.py search --config config.yaml \
                        --data data.yaml
    python crossmapy.py decompose --config config.yaml \
                        --data data.yaml

The outputs are json-formatted arrays with results for all the documents in
the data file.
  
Because the above commands are minimalistic, the search and decomposition
analyses are performed using a number of assumptions. In practice, several
additional arguments help to adjust the analysis.
  
- ``--dataset`` [path to file] - specifies the data collection to search
  against. The provided value must match a collection name from the
  configuration file. The default behavior is to use the first data collection
  in the configuration file.
- ``--n`` [integer] - specifies the number of hits to report for each object in
  the data file. The default is 1.
- ``--pretty`` [flag, no value necessary] - formats the output using
  human-readable spacing.
- ``--tsv`` [flag, no value necessary] - format the output into a
  tab-separated table instead of json.
- ``--diffusion`` [character string] - specifies the type of diffusion process
  to apply onto to the query before search/decomposition. The string must be
  provided as a json-formatted dictionary, without any spaces, mapping data
  collections to numbers. The default is ``"{}"``, which disables diffusion.
     
Using all these arguments, and assuming the instance has a data collection
named ``collection``, a complete search query might be as follows

.. code:: bash

    python crossmap.py search --config config.yaml \
                       --data data.yaml \
                       --pretty --n 5 \
                       --dataset collection \
                       --diffusion "{\"collection\":0.5}"

Unfortunately, specifying the diffusion setting on the command line is
tedious. However, the formatting is convenient when the search is performed
programmatically.


Distances and matrix-breakdowns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While search and decomposition compare external data to entire collections in
the crossmap instance, it is also possible to query how external data
related to specific objects. Two relevant actions are ``distances`` and
``matrix``.
   
Here, let's assume the instance has a data collection called ``collection``,
which contains objects ``obj:1`` and ``obj:2``. The distance utility is
executed as follows

.. code:: bash

    python crossmap.py distances --config config.yaml \
                       --data data.yaml \
                       --ids obj:1,obj:2 \
                       --pretty --diffusion "{\"collection\":1}"


The first two lines of this command provide the essential components; the
third line tunes the calculation and output (see above).
 
The output is a json-formatted object with distance values.
 
The ``matrix`` utility has a similar syntax, but provides a detailed
breakdown of the the features that participate in the calculation of
distances.
   
**Note** the `distance` and `matrix` utilities only process the first object
defined in the external data file.


Diffusion
~~~~~~~~~

Diffusion is a major component of the crossmap algorithms. The `diffuse`
action provides a means to extract before-diffusion and after-diffusion data
representations.

Inputs can be specified as plain text or in data files. 
 
- ``--data`` [path to file] specifies a path to a data file
- ``--text`` [character string] comma-separated list of inputs, but limited
   to strings without spaces and special characters.
   
Example queries are as follows
 
.. code:: bash

    python crossmap.py diffuse --config config.yaml --text abcd \
                           --pretty --diffusion "{}"
    python crossmap.py diffuse --config config.yaml --text abcd \
                           --pretty --diffusion "{\"collection\":0.5}" 


The outputs are json-formatted tables that describe how each text input is
broken into features, and how those features are weighted.

