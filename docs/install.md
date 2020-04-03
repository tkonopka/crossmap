# Installation

## Primary software

The primary `crossmap` software is written in `python`. Development is
 carried out using `python` 3.7 and it is best to use this version (or later
 ). You can check your version using

```
python --version
``` 

If your version is lower than 3.7, it is recommended to install the latest
 python interpreter before proceeding. (It is possible to have multiple
  python versions installed on a single computer, so upgrading python for
   `crossmap` should not conflict with existing workflows.)

Beyond the python interpreter, the software requires a number of packages
. These can be installed using the package manager `pip`.

```
pip install sqlite3 numpy scipy numba nmslib pymongo yaml
```

Some of these, in particular nmslib, have bindings to libraries for high
-performance numerical computations. They can exploit hardware-specific
 features such as CPU instruction sets to maximize running speed. As a result
 , the default installations via `pip` may output messages or warnings that
  the default installation may be sub-optimal and provide hints on how to
   compile the packages from sources. It is recommended to follow those hints
    and re-install the packages if needed. 

After installing `python` and the required packages, the `crossmap` utility
 should be ready to run. As a diagnostic, the utility should be able to display
  a summary of the available arguments. 

```
python crossmap.py --help
``` 

This should display several lines with short descriptions of the arguments
. Practical use-cases are covered in the documentation of the [command-line interface](cli.md).



## User interface

A graphical user interface is available to facilitate querying `crossmap
` instances. Executing the GUI requires some additional `python` packages and
 a `javascript` development environment.

The back-end functionality is implemented using [Django](https://www
.djangoproject.com/). This can be installed via `pip`. 

```python
pip install django
```

The front-end is implemented as a [React](https://reactjs.org/) application
. To use this, you will first need to have the node package manager, `npm
`. You can check your version using

```
npm --version
```

Development is carried out using version 6.9 and it is best to use this
 version (or later). If you don't have `npm`, installation is described on
  the [node home page](https://nodejs.org/). 

The front-end uses certain node packages and these must be installed using
 `npm` from the `crosschat` directory.

```
cd crosschat
npm install
cd ..
```

The `npm` command downloads several components relevant for this application
. Its output should summarize the steps and success status. 

