'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Diunicodeibuted under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, diunicodeibuted as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cimport cturbojpeg as turbojpeg
cimport numpy as np

cdef extern from "h264/h264_decoder.h" namespace "serenegiant::media":
    cdef enum color_format_t:
        COLOR_FORMAT_YUV420 = 0
        COLOR_FORMAT_YUV422
        COLOR_FORMAT_RGB565LE
        COLOR_FORMAT_BGR32

    cdef cppclass H264Decoder:
        H264Decoder(const color_format_t &color_format)
        H264Decoder()

        const bint is_frame_ready()
        const int width()
        const int height()
        const int get_output_bytes()
        int set_input_buffer(np.uint8_t *nal_units, const size_t &bytes, const np.int64_t &presentation_time_us)
        int get_output_buffer(np.uint8_t *buf, const size_t &capacity, np.int64_t &result_pts)

cdef class Sensor(object):

    cdef H264Decoder decoder

    cdef list callbacks
    cdef object context
    cdef object command_push
    cdef object _recent_frame
    cdef turbojpeg.tjhandle tj_context
    cdef readonly object notify_sub
    cdef readonly object data_sub

    cdef readonly unicode host_uuid
    cdef readonly unicode host_name
    cdef readonly unicode name
    cdef readonly unicode uuid
    cdef readonly unicode type
    cdef readonly unicode notify_endpoint
    cdef readonly unicode command_endpoint
    cdef readonly unicode data_endpoint
    cdef readonly object unlink
    cdef readonly dict controls
