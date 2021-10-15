# cython: language_level=3
'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Diunicodeibuted under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, diunicodeibuted as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cimport numpy as np
from libcpp.string cimport string


cdef extern from "<libavcodec/avcodec.h>":
    struct AVCodec:
        pass

    struct AVCodecContext:
        pass

cdef extern from "<libavformat/avformat.h>":
    struct AVFormatContext:
        pass


cdef extern from "h264/h264_decoder.h" namespace "serenegiant::media":
    cdef enum color_format_t:
        COLOR_FORMAT_YUV420 = 0
        COLOR_FORMAT_YUV422
        COLOR_FORMAT_RGB565LE
        COLOR_FORMAT_BGR32

    cdef cppclass H264Decoder:
        H264Decoder(const color_format_t &color_format)
        H264Decoder()

        AVCodecContext *get_context()
        const bint is_initialized()
        const bint is_frame_ready()
        const int width()
        const int height()
        const int get_output_bytes()

        int set_input_buffer(np.uint8_t *nal_units,
                             const size_t &bytes,
                             const np.int64_t &presentation_time_us)

        int get_output_buffer(np.uint8_t *buf,
                              const size_t &capacity,
                              np.int64_t &result_pts)


cdef extern from "h264/h264_utils.h" namespace "serenegiant::media":
    int get_vop_type_annexb(const np.uint8_t *data, const size_t &size)


cdef extern from "h264/media_stream.h" namespace "serenegiant::media":
    cdef cppclass MediaStream:
        MediaStream()
        void release()

        const np.uint32_t num_frames_written()
        int set_input_buffer(AVFormatContext *output_context,
                             const np.uint8_t *nal_units,
                             const size_t &bytes,
                             const np.int64_t &presentation_time_us)

cdef extern from "h264/video_stream.h" namespace "serenegiant::media":
    cdef cppclass VideoStream(MediaStream):

        VideoStream(const np.uint32_t &width,
                    const np.uint32_t &height,
                    const int &fps)


cdef extern from "h264/mp4_writer.h" namespace "serenegiant::media":
    cdef cppclass Mp4Writer:
        Mp4Writer(const string &file_name)
        void release()

        int add(MediaStream *stream)
        int start()
        int stop()
        const bint isRunning()
        int set_input_buffer(const int &stream_index,
                             const np.uint8_t *nal_units,
                             const size_t &bytes_,
                             const np.int64_t &presentation_time_us);
