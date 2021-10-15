# cython: language_level=3
'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cimport ndsi.cturbojpeg as turbojpeg
from ndsi.h264 cimport COLOR_FORMAT_YUV422, H264Decoder


cdef class FrameFactory:
    cdef H264Decoder *decoder
    cdef turbojpeg.tjhandle tj_context

cdef class JPEGFrame:
    cdef turbojpeg.tjhandle tj_context
    #we use numpy for memory management.
    cdef object _raw_data
    cdef unsigned char[:] _bgr_buffer, _gray_buffer,_yuv_buffer
    cdef long _width, _height, _index, _buffer_len
    cdef bint _yuv_converted, _bgr_converted
    cdef public double timestamp
    cdef public yuv_subsampling

    cdef yuv2bgr(self)
    cdef jpeg2yuv(self)

    cdef attach_tj_context(self, turbojpeg.tjhandle ctx)

cdef class H264Frame:
    cdef turbojpeg.tjhandle tj_context
    cdef unsigned char[:] _yuv_buffer, _bgr_buffer, _gray_buffer, _h264_buffer
    cdef long _width, _height, _index, _buffer_len
    cdef bint _bgr_converted
    cdef public double timestamp

    cdef attach_tj_context(self, turbojpeg.tjhandle ctx)
    cdef yuv2bgr(self)
