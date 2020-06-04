Deploying instances
===================

Running the graphical-user interface requires interaction between a
database, an API service, and a front-end app. These components can be
launched and stopped together with a ``docker-compose`` configuration.

Deploying a dockerized GUI application requires preparing a docker image
for the ``crossmap`` software. This is a one-time procedure and does
not have to be repeated every time an application is launched and stopped.
In the root repository, build a docker image using the following command.

  .. code:: bash

      docker build --tag crossmap .

This step can take a few minutes to complete. It is important that the
image tag is 'crossmap' as this name is required in subsequent steps.

After the image is build, the next steps involve preparing a configuration
for a particular crossmap instance. First, determine a location on the
host file system to store database files. Then, copy file
`crossmap-instance.yaml`, which is a docker-compose configuration file,
to that desired directory.
  
Rename the docker-compose configuration file to reflect the crossmap
instance, e.g. `crossmap-my-instance.yaml`. (If you want to deploy
applications based on different ``crossmap`` instances, you will need more
than one docker-compose configuration files.)
   
Within custom configuration file, find the following line:
   
  .. code:: yaml

      command: python3.7 crossmap.py server --config data/config.yaml

Replace the `--config` argument with a path to your crossmap instance, e.g.
    
  .. code:: yaml

      command: python3.7 crossmap.py server --config my-data/my-config.yaml

With these change in place, you can launch the application using docker-compose.
        
  .. code:: bash

      docker-compose -f crossmap-my-instance.yaml up -d

Note that startup of the GUI component includes a production-level
compilation step, which is not instantaneous, so it may take 30
seconds or longer for the web application to become accessible.

When the application is no-longer needed, stop it.
    
  .. code:: bash

      docker-compose -f crossmap-my-instance.yaml down

