# crossmap

crossmap


Intro - to do

[Documentation](docs/README.md)



docker

# Setting up docker

After install docker and docker-compose.

```
# create a group docker (it may already exist)
sudo groupadd docker
# add a username to the group
usermod -a -G docker [USERNAME]
# log out and log in to allow the group membership changes to take effect
```

After logging in

```
sudo service docker start
```

To start the mongodb instance

```
docker-compose up -d
```

To cleanup

```
docker-compose down
```





