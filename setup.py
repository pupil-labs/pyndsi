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

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import glob

libs = []
library_dirs = []
extra_link_args = []
extra_objects = []
if platform.system() == 'Darwin':
    try:
        tj_lib = glob.glob('/usr/local/opt/jpeg-turbo/lib/libturbojpeg.dylib')[0]
    except IndexError:
        raise Exception("Please install libturbojpeg")
    include_dirs = ['/usr/local/opt/jpeg-turbo/include/']
    libs += ['turbojpeg']
    library_dirs += ['/usr/local/opt/jpeg-turbo/lib/']
elif platform.system() == 'Linux':
    try:
        # check for tubo jpeg offical lib and select appropriate lib32/lib64 path.
        tj_lib = glob.glob('/opt/libjpeg-turbo/lib*')[0]+'/libturbojpeg.a'
    except IndexError:
        raise Exception("Please install libturbojpeg")
    libs = ['rt']
    extra_link_args = []  # ['-Wl,-R/usr/local/lib/']
    include_dirs = ['/opt/libjpeg-turbo/include']
    extra_objects += [tj_lib]
elif platform.system() == 'Windows':
    # raise NotImplementedError("please fix me.")
    libs = ['winmm']
    tj_dir = 'C:\\work\\libjpeg-turbo-VC64'
    tj_lib = tj_dir + '\\lib\\turbojpeg.lib'
    include_dirs = [tj_dir + '\\include']
    extra_objects += [tj_lib]

libs += ['avformat', 'avcodec', 'swscale']

extensions = [
    Extension(name="ndsi.frame",
              sources=['ndsi/frame.pyx'],
              include_dirs=[numpy.get_include()]+include_dirs,
              library_dirs=library_dirs,
              libraries=libs,
              extra_link_args=extra_link_args,
              extra_objects=extra_objects,
              language='c++'),
    Extension(name="ndsi.sensor",
              sources=glob.glob('ndsi/h264/*.cpp')+['ndsi/sensor.pyx'],
              include_dirs=[numpy.get_include()]+include_dirs,
              library_dirs=library_dirs,
              libraries=libs,
              extra_link_args=extra_link_args+["-std=c++11"],
              extra_compile_args=["-std=c++11"],
              extra_objects=extra_objects,
              language='c++'),
    Extension(name="ndsi.network",
              sources=['ndsi/network.pyx'],
              include_dirs=[numpy.get_include()]+include_dirs,
              library_dirs=library_dirs,
              libraries=libs,
              extra_link_args=extra_link_args,
              extra_objects=extra_objects,
              language='c++')]

setup(name="ndsi",
      version="0.2.16",  # make sure this is the same as in ndsi/__init__.py
      description="Remote Device Sensor Interface",
      packages=['ndsi'],
      ext_modules=cythonize(extensions))
