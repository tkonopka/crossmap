# Docker

This section describes how to run `crossmap` instances using the 
[docker](www.docker.com) container framework.


## Docker setup

The first step toward running `crossmap` in docker containers is to ensure
 that docker itself is installed, configured, and running on the host machine. 

 - Install [docker](https://docs.docker.com/get-docker/) and [docker
 -compose](https://docs.docker.com/compose/install/) following the official
  documentation. 

 - Configure a docker user group. It is important that a docker group exists
  and that a username is assigned to the group.

    ```
    sudo groupadd docker
    usermod -a -G docker [USERNAME]
    ```

   *Note* - it may be necessary to log out and back in for the changes to
    take effect.

 - Ensure that the docker service is running. 

    ```
    sudo service docker start
    ```


## Database-only

All operations on a crossmap instance require a connection to a database. It
 is possible to set one up using a docker container. 
 
In a docker database-only configuration, a container is used to manage the
 required database service. Interactions with `crossmap` instances are
  performed outside of the container framework, i.e. on the host machine.
  
A database-only configuration is suited when working with multiple `crossmap
` instances. 
    
  - Determine a location on the host file system to store the
   database files.
  
  - Copy file `crossmap-db.yaml`, which is a docker-compose configuration, into
   the desired destination.
      
  - Launch the database container using docker-compose.
    
    ```
    docker-compose -f crossmap-db.yaml up -d
    ```

  - When the database is no-longer needed, stop the database container.

    ```
    docker-compose -f crossmap-db.yaml down
    ```
    

## Single-instance GUI application

The graphical-user interface application requires interaction between a
 database, an API service, and a front-end app. These components can be
  launched and stopped together with a docker-compose configuration. 
 
In GUI configuration, containers are used to manage three independent
 components, all linked to a `crossmap` instance. 
 
A GUI configuration is suitable when a `crossmap` instance has already been
 built, and the purpose is to manage the web interface.   
 
A GUI configuration requires running a one-time preparation step.

  - In the root repository, build a docker image of the crossmap software.
  
    ```
    docker build --tag crossmap .
    ``` 
 
    This step can take a few minutes to complete. It is important that the
     image tag is 'crossmap' as this is name is required in subsequent steps.

After the image is build, the next steps involve preparing a configuration
 for a particular crossmap instance.
 
  - Determine a location on the host file system to store database files.
 
  - Copy file `crossmap-instance.yaml`, which is a docker-compose
  configuration file, to the desired directory.
  
  - Rename the docker-compose configuration file to reflect the crossmap
   instance, e.g. `crossmap-my-instance.yaml`.
   
  - Edit the custom configuration file so that it can interact with the
   crossmap instance. To do this, find the following line
   
    ```
    command: python3.7 crossmap.py server --config data/config.yaml
    ``` 

    Replace the `--config` argument with a path to the crossmap instance, e.g.
    
    ```
    command: python3.7 crossmap.py server --config my-data/my-config.yaml
    ``` 
    
  - Launch the application using docker-compose, e.g.
        
    ```
    docker-compose -f crossmap-my-instance.yaml up -d
    ```
    
  - When it is no-longer needed, stop the application containers, e.g.
    
    ```
    docker-compose -f crossmap-my-instance.yaml down
    ```

*Note:* the startup procedure for the GUI in the docker container includes a
 complication step. This is not instantaneous, so it may take 30s or more for
  the web application to become accessible in a web browser.
