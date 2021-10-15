[![CI Build](https://github.com/pupil-labs/pyndsi/actions/workflows/build.yml/badge.svg)](https://github.com/pupil-labs/pyndsi/actions/workflows/build.yml)
[![PyPI version](https://badge.fury.io/py/ndsi.svg)](https://badge.fury.io/py/ndsi)

# Network Device Sensor Interface

`ndsi-commspec.md` defines the *Network Device Sensor protocol*.

`examples/ndsi-test-host.py` features a (not so pretty) host test implementation.

`examples/ndsi-client-example.py` shows a simple client application.

## Installation
We provide pre-compiled wheels for macOS, Windows, and Linux 64-bit architectures and
Python versions 3.6+. You can install them via

```
python -m pip
python -m pip install ndsi
```

For any other architecture or Python version, you will have to run the source installation described in [`SOURCE-INSTALL.md`](SOURCE-INSTALL.md).

## Maintainer documentation

See [`MAINTENANCE.md`](MAINTENANCE.md) for maintainer documentation.

# Changelog

## Version 1.4.1

- Updated TurboJPEG requirement instructions for Ubuntu [#65](https://github.com/pupil-labs/pyndsi/pull/64)
- Automated wheel builds and deployment via PyPI [#65](https://github.com/pupil-labs/pyndsi/pull/65)

## Version 1.4.0 and prior

Previous changelogs can be found at https://github.com/pupil-labs/pyndsi/releases
