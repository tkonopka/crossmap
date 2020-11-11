## This dockerfile creates a rather large image (1.09GB)
## Suggestions for improvements are welcome.
## Must-have requirements:
## - python 3.7 or higher
## - nmslib must compile with pip install
## - must includes both python executables and npm

FROM ubuntu:18.04

# update the operating stystem, python, npm
RUN apt-get update \
    && apt-get -y install build-essential gfortran libopenblas-dev liblapack-dev \
    && apt-get -y install curl gnupg libyaml-dev \
    && apt-get -y --no-install-recommends install python3-pip python3.7 python3.7-dev
RUN python3.7 -m pip install -U pip setuptools wheel \
    && python3.7 -m pip install --no-cache-dir --compile \
                 numpy pyyaml scipy requests numba pymongo django \
    && python3.7 -m pip install --no-binary :all: nmslib
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash - \
    && apt-get -y --no-install-recommends install nodejs \
    && npm install -g serve \
    && mkdir /crossmap

# set up directories for this project
WORKDIR /crossmap
COPY . /crossmap
RUN python3.7 -m pip install -r requirements.txt \
    && npm --prefix ./crosschat/ install ./crosschat/ \
    && REACT_APP_API_URL=127.0.0.1:8098 npm run build --prefix ./crosschat/ \
    && rm -fr /crossmap/crosschat/node_modules/
