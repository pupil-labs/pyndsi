# Network Device Sensor Interface

`CommSpecs-2.md` defines the *Network Device Sensor protocol*.

`examples/ndsi-test-host.py` features a (not so pretty) host test implementation.

`examples/ndsi-client-example.py` shows a simple client application.

## Requirements

NDSI requires ffmpeg 3.2 to decode h.264 frames.

## Windows Developer Installation

Please change the `tj_dir` and `ffmpeg_libs` variables in `setup.py` as well as [`setup.py:L40`](https://github.com/pupil-labs/pyndsi/blob/302387085a3fca57cb5a9af65bf60129954a7f89/setup.py#L40) to the location of the turbo-jpeg and ffmpeg installations on your machine.
