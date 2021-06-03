"""
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
"""
import glob
import io
import os
import platform
import re

import numpy
from Cython.Build import cythonize
from setuptools import Extension, setup


requirements = [
    "numpy",
    "pyzmq",
    "zeromq-pyre @ https://github.com/zeromq/pyre/archive/master.zip",
]


def examples_requirements() -> list:
    if platform.system() == "Windows":
        pyuvc = "uvc @ https://github.com/pupil-labs/pyuvc/releases/download/v0.13/uvc-0.13-cp36-cp36m-win_amd64.whl"
    else:
        pyuvc = "uvc @ git+https://github.com/pupil-labs/pyuvc@master"
    return [pyuvc]


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8"),
    ) as fp:
        return fp.read()


# pip's single-source version method as described here:
# https://python-packaging-user-guide.readthedocs.io/single_source_version/
def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


libs = []
library_dirs = []
include_dirs = []
extra_link_args = []
extra_objects = []
include_dirs = [numpy.get_include()]
if os.environ.get("CIBUILDWHEEL"):
    if platform.system() == "Windows":
        ffmpeg_base = "C:\\cibw\\vendor\\"
        libjpeg_turbo_base = "C:\\cibw\\libjpeg-turbo-build\\"
        include_dirs += [
            f"{libjpeg_turbo_base}include",
            f"{ffmpeg_base}include",
            "ndsi\\h264\\windows",
        ]
        extra_objects += [f"{libjpeg_turbo_base}lib\\turbojpeg-static.lib"]
        libs = ["winmm"] + [
            f"{ffmpeg_base}lib\\{L}"
            for L in ("avutil", "avformat", "avcodec", "swscale")
        ]
    else:
        include_dirs += ["/tmp/libjpeg-turbo-build/include/", "/tmp/vendor/include/"]
        library_dirs += ["/tmp/libjpeg-turbo-build/lib/", "/tmp/vendor/lib/"]
        for folder in include_dirs + library_dirs:
            assert os.path.exists(folder), f"{folder} not found!"
        libs += ["turbojpeg", "avutil", "avformat", "avcodec", "swscale"]
elif platform.system() == "Darwin":
    include_dirs += ["/usr/local/opt/jpeg-turbo/include/"]
    libs += ["turbojpeg"]
    library_dirs += ["/usr/local/opt/jpeg-turbo/lib/"]
    libs += ["avutil", "avformat", "avcodec", "swscale"]
elif platform.system() == "Linux":
    libs = ["rt", "turbojpeg"]
    libs += ["avutil", "avformat", "avcodec", "swscale"]
elif platform.system() == "Windows":
    libs = ["winmm"]
    tj_dir = "C:\\work\\libjpeg-turbo-VC64"
    tj_lib = tj_dir + "\\lib\\turbojpeg.lib"
    include_dirs += [tj_dir + "\\include"]
    extra_objects += [tj_lib]
    include_dirs += ["ndsi\\h264\\windows"]
    ffmpeg_libs = "C:\\work\\ffmpeg-4.0-win64-dev\\lib"
    include_dirs += ["C:\\work\\ffmpeg-4.0-win64-dev\\include"]
    libs += [
        ffmpeg_libs + "\\avutil",
        ffmpeg_libs + "\\avformat",
        ffmpeg_libs + "\\avcodec",
        ffmpeg_libs + "\\swscale",
    ]

h264_sources = glob.glob("ndsi/h264/*.cpp")
if platform.system() == "Windows":
    h264_sources += glob.glob("ndsi/h264/windows/*.cpp")

extensions = [
    Extension(
        name="ndsi.frame",
        sources=h264_sources + ["ndsi/frame.pyx"],
        include_dirs=[numpy.get_include()] + include_dirs,
        library_dirs=library_dirs,
        libraries=libs,
        extra_link_args=extra_link_args + ["-std=c++11"],
        extra_compile_args=["-std=c++11"],
        extra_objects=extra_objects,
        language="c++",
    ),
    Extension(
        name="ndsi.writer",
        sources=h264_sources + ["ndsi/writer.pyx"],
        include_dirs=[numpy.get_include()] + include_dirs,
        library_dirs=library_dirs,
        libraries=libs,
        extra_link_args=extra_link_args + ["-std=c++11"],
        extra_compile_args=["-std=c++11"],
        extra_objects=extra_objects,
        language="c++",
    ),
]

setup(
    name="ndsi",
    version="1.4.1",
    install_requires=requirements,
    extras_require={
        "examples": examples_requirements(),
        "dev": ["pytest", "bump2version", "black"],
    },
    description="Remote Device Sensor Interface",
    packages=["ndsi"],
    ext_modules=cythonize(extensions),
    url="https://github.com/pupil-labs/pyndsi",
    author="Pupil Labs",
    author_email="info@pupil-labs.com",
    license="LGPL-3.0",
    classifiers={
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: System :: Networking",
    },
    project_urls={"Changelog": "https://github.com/pupil-labs/pyndsi#Changelog"},
)
