# Network Device Sensor Interface

`ndsi-commspec.md` defines the *Network Device Sensor protocol*.

`examples/ndsi-test-host.py` features a (not so pretty) host test implementation.

`examples/ndsi-client-example.py` shows a simple client application.

## Requirements

NDSI requires ffmpeg 3.2 or higher to decode h.264 frames.

## Installation

```sh
git clone git@github.com:pupil-labs/pyndsi.git
# Clone via HTTPS if you did not configure SSH correctly
# git clone https://github.com/pupil-labs/pyndsi.git

cd pyndsi

# Use the Python 3 installation of your choice
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### Windows Developer Installation

Please change the `tj_dir` and `ffmpeg_libs` variables in `setup.py` as well as [`setup.py:L63`](https://github.com/pupil-labs/pyndsi/blob/master/setup.py#L63) to the location of the turbo-jpeg and ffmpeg installations on your machine.
