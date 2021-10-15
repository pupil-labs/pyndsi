# Source installation

## Dependencies

NDSI requires ffmpeg 3.2 or higher to decode h.264 frames, and turbo-jpeg.

### Ubuntu 18.04 LTS (recommended Linux distribution)

#### FFMPEG
```sh
# ffmpeg >= 3.2
sudo apt install -y libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev ffmpeg x264 x265 libportaudio2 portaudio19-dev
```

#### TurboJPEG
```sh
wget -O libjpeg-turbo.tar.gz https://sourceforge.net/projects/libjpeg-turbo/files/1.5.1/libjpeg-turbo-1.5.1.tar.gz/download
tar xvzf libjpeg-turbo.tar.gz
cd libjpeg-turbo-1.5.1
./configure --enable-static=no --prefix=/usr/local
sudo make install
sudo ldconfig
```

### Ubuntu 17.10 or lower

#### FFMPEG
```sh
# Install ffmpeg3 from jonathonf's ppa
sudo add-apt-repository ppa:jonathonf/ffmpeg-4
sudo apt-get update
sudo apt install -y libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev ffmpeg libav-tools x264 x265 libportaudio2 portaudio19-dev
```

#### TurboJPEG
```sh
wget -O libjpeg-turbo.tar.gz https://sourceforge.net/projects/libjpeg-turbo/files/1.5.1/libjpeg-turbo-1.5.1.tar.gz/download
tar xvzf libjpeg-turbo.tar.gz
cd libjpeg-turbo-1.5.1
./configure --enable-static=no --prefix=/usr/local
sudo make install
sudo ldconfig
```

### macOS

#### FFMPEG
```sh
# opencv will install ffmpeg, numpy, and opencv-contributions automatically
# tbb is included by default with https://github.com/Homebrew/homebrew-core/pull/20101
brew install opencv
```

#### TurboJPEG
```sh
brew install libjpeg-turbo
```

### Windows 10

Please change the `tj_dir` and `ffmpeg_libs` variables in `setup.py` as well as [`setup.py:L63`](https://github.com/pupil-labs/pyndsi/blob/master/setup.py#L63) to the location of the [turbo-jpeg](https://sourceforge.net/projects/libjpeg-turbo/files/latest/download) and [ffmpeg](https://ffmpeg.zeranoe.com/builds/) installations on your machine.

## Installation

```sh
git clone git@github.com:pupil-labs/pyndsi.git
# Clone via HTTPS if you did not configure SSH correctly
# git clone https://github.com/pupil-labs/pyndsi.git

cd pyndsi

# Use the Python 3 installation of your choice
python -m pip install -U pip
python -m pip install -e .
```

## Examples

To run the examples, `ndsi` should be installed with additional requirements:

```sh
git clone git@github.com:pupil-labs/pyndsi.git
# Clone via HTTPS if you did not configure SSH correctly
# git clone https://github.com/pupil-labs/pyndsi.git

cd pyndsi

# Use the Python 3 installation of your choice
python -m pip install -U pip
python -m pip install -e ".[examples]"
```
