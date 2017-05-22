'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Diunicodeibuted under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, diunicodeibuted as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cimport numpy as np
from .h264 cimport VideoStream, Mp4Writer

cdef class H264Writer(object):

    cdef readonly np.uint32_t width, height, fps
    cdef readonly bint waiting_for_iframe
    cdef VideoStream *video_stream
    cdef Mp4Writer *proxy
    cdef object timestamps
    cdef int frame_count

    cdef readonly unicode video_loc
