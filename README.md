[![ci](https://github.com/us-irs/com-interface/actions/workflows/ci.yml/badge.svg)](https://github.com/us-irs/com-interface/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/com-interface/badge/?version=latest)](https://com-interface.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/com-interface.svg)](https://badge.fury.io/py/com-interface)

`com-interface` - Generic communication abstraction to send arbitrary byte packets
======

This library contains a generic communication abstraction specifically targeted
towards the exchange of binary data like CCSDS packets.

The [documentation](https://com-interface.readthedocs.io/en/latest/?badge=latest) contains more
information.

# Install

You can install this package from PyPI

Linux:

```sh
python3 -m pip install com-interface
```

Windows:

```sh
py -m pip install com-interface
```

# Examples

You can find all examples [inside the documentation](https://spacepackets.readthedocs.io/en/latest/examples.html).


# Tests

If you want to run the tests, it is recommended to install `pytest` and `coverage` (optional)
first:

```sh
pip install coverage pytest
```

Running tests regularly:

```sh
pytest .
```

Running tests with coverage:

```sh
coverage run -m pytest
```

# Documentation

The documentation is built with Sphinx and new documentation should be written using the
[NumPy format](https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html#example-numpy).

Install the required dependencies first:

```sh
pip install -r docs/requirements.txt
```

Then the documentation can be built with

```sh
cd docs
make html
```

You can run the doctests with

```sh
make doctest
```

# Formatting and Linting

Linting:

```sh
ruff check .
```

Formatting:

```sh
ruff format .
```
