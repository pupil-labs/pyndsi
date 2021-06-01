# Maintainer documentation

## CI

This repo uses [Github Actions](.github/workflows/build.yml) for automated wheel building, testing, and deployment.
The Github Action is inspired by this [pyav Github action](https://github.com/PyAV-Org/PyAV/blob/9ac05d9ac902d71ecb2fe80f04dcae454008378c/.github/workflows/tests.yml).
To build the wheels, we use the [pre-built ffmpeg binaries](https://github.com/PyAV-Org/pyav-ffmpeg/releases) released by the PyAV organtisation.

The built wheels and source distribution are deployed to PyPI if a tag is being pushed.

## Code format

This repo uses [black](https://github.com/psf/black) for automated code formatting. You
can install it via the `dev` ndsi extra requirements or directly via
`pip install black`.

Note: The CI requires the `black check` to pass in order to start building wheels.

## Version bump

This repo has a [bump2version](https://github.com/c4urself/bump2version) config to
automate version changes. You can install it via the `dev` ndsi extra requirements or
directly via `pip install bump2version`.
