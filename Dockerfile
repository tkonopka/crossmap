FROM ubuntu:18.04

# update the operating stystem, python, npm
RUN apt-get update
RUN apt-get -y install curl gnupg libyaml-dev python3-pip python3.7 python3.7-dev
RUN python3.7 -m pip install pip numpy pyyaml scipy numba requests
RUN python3.7 -m pip install --no-binary :all: nmslib
RUN python3.7 -m pip install pymongo django
RUN curl -sL https://deb.nodesource.com/setup_13.x  | bash -
RUN apt-get -y install nodejs
RUN npm install -g serve

# set up directories for this project
RUN mkdir /crossmap
RUN mkdir /crossmap/data
WORKDIR /crossmap
COPY . /crossmap/

# install project-specific packages
RUN python3.7 -m pip install -r requirements.txt
RUN npm --prefix ./crosschat/ install ./crosschat/
RUN npm run build --prefix crosschat/
