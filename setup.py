'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''
import platform
import numpy
import glob
import os
import io
import re

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


# pip's single-source version method as described here:
# https://python-packaging-user-guide.readthedocs.io/single_source_version/
def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


libs = []
library_dirs = []
include_dirs = []
extra_link_args = []
extra_objects = []
include_dirs = [numpy.get_include()]
if platform.system() == 'Darwin':
    include_dirs += ['/usr/local/opt/jpeg-turbo/include/']
    libs += ['turbojpeg']
    library_dirs += ['/usr/local/opt/jpeg-turbo/lib/']
    libs += ['avutil', 'avformat', 'avcodec', 'swscale']
elif platform.system() == 'Linux':
    libs = ['rt', 'turbojpeg']
    libs += ['avutil', 'avformat', 'avcodec', 'swscale']
elif platform.system() == 'Windows':
    libs = ['winmm']
    tj_dir = 'C:\\work\\libjpeg-turbo-VC64'
    tj_lib = tj_dir + '\\lib\\turbojpeg.lib'
    include_dirs += [tj_dir + '\\include']
    extra_objects += [tj_lib]
    include_dirs += ['ndsi\\h264\\windows']
    ffmpeg_libs = 'C:\\work\\ffmpeg-3.2-win64-dev\\lib'
    include_dirs += ['C:\\work\\ffmpeg-3.2-win64-dev\\include']
    libs += [ffmpeg_libs+'\\avutil',ffmpeg_libs+'\\avformat',ffmpeg_libs+'\\avcodec',ffmpeg_libs+'\\swscale']

h264_sources = glob.glob('ndsi/h264/*.cpp')
if platform.system() == 'Windows':
    h264_sources += glob.glob('ndsi/h264/windows/*.cpp')

extensions = [
    Extension(name="ndsi.frame",
              sources=h264_sources+['ndsi/frame.pyx'],
              include_dirs=[numpy.get_include()]+include_dirs,
              library_dirs=library_dirs,
              libraries=libs,
              extra_link_args=extra_link_args+["-std=c++11"],
              extra_compile_args=["-std=c++11"],
              extra_objects=extra_objects,
              language='c++'),
    Extension(name="ndsi.writer",
              sources=h264_sources+['ndsi/writer.pyx'],
              include_dirs=[numpy.get_include()]+include_dirs,
              library_dirs=library_dirs,
              libraries=libs,
              extra_link_args=extra_link_args+["-std=c++11"],
              extra_compile_args=["-std=c++11"],
              extra_objects=extra_objects,
              language='c++'),
    Extension(name="ndsi.sensor",
              sources=h264_sources+['ndsi/sensor.pyx'],
              include_dirs=[numpy.get_include()]+include_dirs,
              library_dirs=library_dirs,
              libraries=libs,
              extra_link_args=extra_link_args+["-std=c++11"],
              extra_compile_args=["-std=c++11"],
              extra_objects=extra_objects,
              language='c++'),
    Extension(name="ndsi.network",
              sources=h264_sources+['ndsi/network.pyx'],
              include_dirs=[numpy.get_include()]+include_dirs,
              library_dirs=library_dirs,
              libraries=libs,
              extra_link_args=extra_link_args+["-std=c++11"],
              extra_compile_args=["-std=c++11"],
              extra_objects=extra_objects,
              language='c++')]

setup(name="ndsi",
      version=find_version('ndsi', '__init__.py'),
      description="Remote Device Sensor Interface",
      packages=['ndsi'],
      ext_modules=cythonize(extensions))
