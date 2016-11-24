'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cimport cturbojpeg as turbojpeg

cdef class JEPGFrame(object):
    cdef turbojpeg.tjhandle tj_context
    #we use numpy for memory management.
    cdef object _raw_data
    cdef unsigned char[:] _jpeg_buffer, _bgr_buffer, _gray_buffer,_yuv_buffer
    cdef long _width, _height, _index, _buffer_len
    cdef bint _yuv_converted, _bgr_converted
    cdef public double timestamp
    cdef public yuv_subsampling
    cdef public bint valid_hash

    cdef yuv2bgr(self)
    cdef jpeg2yuv(self)

    cdef attach_tj_context(self, turbojpeg.tjhandle ctx)
