Deploying instances
===================

The graphical-user interface application requires interaction between a
database, an API service, and a front-end app. These components can be
launched and stopped together with a ``docker-compose`` configuration.
 
In GUI configuration, containers are used to manage three independent
components, all linked to a ``crossmap`` instance.
 
A GUI configuration is suitable when a ``crossmap`` instance has already been
built, and the purpose is to manage the web interface.
 
A GUI configuration requires running a one-time preparation step.

- In the root repository, build a docker image of the crossmap software.
  
  .. code:: bash

      docker build --tag crossmap .

  This step can take a few minutes to complete. It is important that the
  image tag is 'crossmap' as this name is required in subsequent steps.

After the image is build, the next steps involve preparing a configuration
for a particular crossmap instance.

- Determine a location on the host file system to store database files.
 
- Copy file `crossmap-instance.yaml`, which is a docker-compose
  configuration file, to the desired directory.
  
- Rename the docker-compose configuration file to reflect the crossmap
  instance, e.g. `crossmap-my-instance.yaml`.
   
- Edit the custom configuration file so that it can interact with the
  crossmap instance. To do this, find the following line
   
  .. code:: yaml

      command: python3.7 crossmap.py server --config data/config.yaml

  Replace the `--config` argument with a path to the crossmap instance, e.g.
    
  .. code:: yaml

      command: python3.7 crossmap.py server --config my-data/my-config.yaml

- Launch the application using docker-compose, e.g.
        
  .. code:: bash

      docker-compose -f crossmap-my-instance.yaml up -d

    
- When it is no-longer needed, stop the application containers, e.g.
    
  .. code:: bash

      docker-compose -f crossmap-my-instance.yaml down

*Note:* the startup procedure for the GUI in the docker container includes a
complication step. This is not instantaneous, so it may take 30s or more for
the web application to become accessible in a web browser.

