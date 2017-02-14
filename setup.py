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

libs = []
library_dirs = []
extra_link_args = []
extra_objects = []
if platform.system() == 'Darwin':
    include_dirs = ['/usr/local/opt/jpeg-turbo/include/']
    libs += ['turbojpeg']
    library_dirs += ['/usr/local/opt/jpeg-turbo/lib/']
elif platform.system() == 'Linux':
    libs = ['rt','turbojpeg']
    include_dirs = ['/opt/libjpeg-turbo/include']
elif platform.system() == 'Windows':
    # raise NotImplementedError("please fix me.")
    libs = ['winmm']
    tj_dir = 'C:\\work\\libjpeg-turbo-VC64'
    tj_lib = tj_dir + '\\lib\\turbojpeg.lib'
    include_dirs = [tj_dir + '\\include']
    extra_objects += [tj_lib]

extensions = [
    Extension(name="*",
              sources=['ndsi/*.pyx'],
              include_dirs=[numpy.get_include()]+include_dirs,
              library_dirs=library_dirs,
              libraries=libs,
              extra_link_args=extra_link_args,
              extra_objects=extra_objects)]

setup(name="ndsi",
      version="0.2.14",  # make sure this is the same as in ndsi/__init__.py
      description="Remote Device Sensor Interface",
      packages=['ndsi'],
      ext_modules=cythonize(extensions))
