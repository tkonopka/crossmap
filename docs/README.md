# Documentation

The documentation is prepared using sphinx and hosted on 
[readthedocs](https://diffusion-map.readthedocs.io/en/latest/).

To generate a local version of the documentation, first install `sphinx`.

```
pip install sphinx
pip install sphinx_rtd_theme
```

To compile the source files into html documents, run the following command.

```
make html      # quick build
make -E html   # more thorough build
```
