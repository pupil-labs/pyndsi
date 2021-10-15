"""
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
"""
import glob
import os
import pathlib
import platform

import numpy
from Cython.Build import cythonize
from setuptools import Extension, setup

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
            "src\\ndsi\\h264\\windows",
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
    import subprocess

    prefixes = (
        subprocess.check_output(
            ["brew", "--prefix", "--installed", "jpeg-turbo", "ffmpeg"]
        )
        .decode("utf-8")
        .strip()
        .splitlines()
    )

    include_dirs += [os.path.join(pre, "include") for pre in prefixes]
    libs += ["turbojpeg", "avutil", "avformat", "avcodec", "swscale"]
    library_dirs += [os.path.join(pre, "lib") for pre in prefixes]
elif platform.system() == "Linux":
    libs = ["rt", "turbojpeg"]
    libs += ["avutil", "avformat", "avcodec", "swscale"]
elif platform.system() == "Windows":
    libs = ["winmm"]
    tj_dir = "C:\\work\\libjpeg-turbo-VC64"
    tj_lib = tj_dir + "\\lib\\turbojpeg.lib"
    include_dirs += [tj_dir + "\\include"]
    extra_objects += [tj_lib]
    include_dirs += ["src\\ndsi\\h264\\windows"]
    ffmpeg_libs = "C:\\work\\ffmpeg-4.0-win64-dev\\lib"
    include_dirs += ["C:\\work\\ffmpeg-4.0-win64-dev\\include"]
    libs += [
        ffmpeg_libs + "\\avutil",
        ffmpeg_libs + "\\avformat",
        ffmpeg_libs + "\\avcodec",
        ffmpeg_libs + "\\swscale",
    ]

h264_sources = glob.glob("src/ndsi/h264/*.cpp")
if platform.system() == "Windows":
    h264_sources += glob.glob("src/ndsi/h264/windows/*.cpp")

extensions = [
    Extension(
        name="ndsi.frame",
        sources=h264_sources + ["src/ndsi/frame.pyx"],
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
        sources=h264_sources + ["src/ndsi/writer.pyx"],
        include_dirs=[numpy.get_include()] + include_dirs,
        library_dirs=library_dirs,
        libraries=libs,
        extra_link_args=extra_link_args + ["-std=c++11"],
        extra_compile_args=["-std=c++11"],
        extra_objects=extra_objects,
        language="c++",
    ),
]

setup(ext_modules=cythonize(extensions))
