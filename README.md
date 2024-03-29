# crossmap

`crossmap` is an application for general-purpose data exploration that can 
adapt to user preferences. It implements algorithms based on nearest-neighbor
search, data decomposition, and diffusion to provide advanced data querying
capabilities.

The documentation pages ([sources](docs/), 
[readthedocs](https://diffusion-map.readthedocs.io/en/latest/)) provide 
information on setup, data-preparation, querying, and the graphical-user 
interface.


## Installation and development

`crossmap` is written in python (3.7) and javascript. It relies on a
 connection to a mongodb instance. 
 
A minimal installation procedure is as follows. 
 
```
# clone the repository source
git clone https://github.com/tkonopka/crossmap.git
cd crossmap
# install required python packages
pip install -r requirements.txt
# install required javascript packages
npm --prefix ./crosschat/ install ./crosschat/
```

If the installation was successful, all tests in the test suite should
 execute cleanly.
 
```
# launch a database
docker-compose -f crossmap-tests-db.yaml up -d
# execute the unit tests
python -m unittest
# stop the database
docker-compose -f crossmap-tests-db.yaml down
```


## Contributing

Comments and contributions are welcome. Please raise an issue on the github
 repository or send email.

