'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cimport cturbojpeg as turbojpeg

cdef class Frame:
    cdef turbojpeg.tjhandle tj_context
    cdef unsigned char[:] _bgr_buffer, _gray_buffer,_yuv_buffer #we use numpy for memory management.
    cdef bint _yuv_converted, _bgr_converted
    cdef public double timestamp
    cdef public yuv_subsampling
    cdef bint owns_uvc_frame

    cdef yuv2bgr(self)
    cdef jpeg2yuv(self)
