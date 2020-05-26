Installation
############

To install ``crossmap``, first clone the
`source-code repository <https://github.com/tkonopka/crossmap>`_.

.. code:: bash

    git clone https://github.com/tkonopka/crossmap.git

To execute the program, navigate to its directory and use the python
interpreted. For example, to see a list of all possible arguments:

.. code:: bash

    cd crossmap
    python crossmap.py --help

In practice, however, a first attempt to execute the above command may
generate errors signaling missing dependencies. Furthermore, practical
calculations require set up of a database and the graphical interface
requires further libraries.


Primary software
~~~~~~~~~~~~~~~~

The primary ``crossmap`` software is written in python and development is
carried out using python version 3.7. You can check your version using

.. code:: bash

    python --version

If your version is lower than 3.7, it is recommended to install the latest
python interpreter before proceeding. (It is possible to have multiple
python versions installed on a single computer, so upgrading python for
`crossmap` should not conflict with existing workflows.)

Beyond the python interpreter, the software requires a number of packages.
These can be installed using the package manager ``pip``.

.. code:: bash

    pip install numpy scipy numba nmslib pymongo requests yaml

Note that the ``nmslib`` is a libraries for high-performance numerical
computations. It can exploit hardware-specific
features such as CPU instruction sets to maximize running speed. As a result,
the default installations via ``pip`` may output messages or warnings that
the default installation may be sub-optimal. If this is the case, the
warnings will provide hints on how to compile the package from sources.
It is recommended to follow those hints and re-install the package if
needed.

After installing the required packages, the ``crossmap`` utility
should be ready to run. As a diagnostic, the utility should be able to display
a summary of the available arguments.

.. code:: bash

    python crossmap.py --help

This should display several lines with short descriptions of the arguments. 
Practical use-cases are covered in the documentation of the 
`command-line interface`.


User interface
~~~~~~~~~~~~~~

A graphical user interface is available to facilitate querying ``crossmap``
instances. This is implemented using a server-client design and requires
additional python packages and a javascript development environment.

The back-end functionality is implemented using
[Django](https://www.djangoproject.com/). This can be installed via `pip`.

.. code:: bash

    pip install django

The front-end is implemented as a [React](https://reactjs.org/) application.
To use this, you will first need to have the node package manager, ``npm``.
You can check your version using

.. code:: bash

    npm --version

If you do not yet have ``npm``, or if your version is below 6.13, install it
by following the instructions on the `node home page <https://nodejs.org/>`_.

The front-end uses certain javascript packages. To install all the requirement,
navigate into the ``crosschat`` directory and install the application.

.. code:: bash

    cd crosschat
    npm install
    cd ..

The ``npm install`` command downloads several components.
Its output should summarize the steps and success status. 



Database
~~~~~~~~



Docker setup
^^^^^^^^^^^^

The first step toward running ``crossmap`` in docker containers is to ensure
 that docker itself is installed, configured, and running on the host machine.

- Install `docker <https://docs.docker.com/get-docker/>`_ and
  `docker-compose <https://docs.docker.com/compose/install/>`_ following the official
  documentation.

- Configure a docker user group. It is important that a docker group exists
  and that a username is assigned to the group.

  .. code:: bash

      sudo groupadd docker
      usermod -a -G docker [USERNAME]

  *Note* - it may be necessary to log out and back in for the changes to
  take effect.

- Ensure that the docker service is running.

  .. code:: bash

    sudo service docker start
    # or
    sudo dockerd &
    ```


Database container
^^^^^^^^^^^^^^^^^^

All operations on a crossmap instance require a connection to a database. It
is possible to set one up using a docker container.

In a docker database-only configuration, a container is used to manage the
required database service. Interactions with `crossmap` instances are
performed outside of the container framework, i.e. on the host machine.

A database-only configuration is suited when working with multiple ``crossmap``
instances.

- Determine a location on the host file system to store the
  database files.

- Copy file `crossmap-db.yaml`, which is a docker-compose configuration, into
  the desired destination.

- Launch the database container using docker-compose.

  .. code:: bash

      docker-compose -f crossmap-db.yaml up -d


- When the database is no-longer needed, stop the database container.

  .. code:: bash

      docker-compose -f crossmap-db.yaml down



