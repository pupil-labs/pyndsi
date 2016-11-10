'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

from libc.string cimport memset
cimport cturbojpeg as turbojpeg
cimport numpy as np
import numpy as np

import struct

IF UNAME_SYSNAME == "Windows":
    include "windows_time.pxi"
ELIF UNAME_SYSNAME == "Darwin":
    include "darwin_time.pxi"
ELIF UNAME_SYSNAME == "Linux":
    include "linux_time.pxi"

uvc_error_codes = {  0:"Success (no error)",
                    -1:"Input/output error.",
                    -2:"Invalid parameter.",
                    -3:"Access denied.",
                    -4:"No such device.",
                    -5:"Entity not found.",
                    -6:"Resource busy.",
                    -7:"Operation timed out.",
                    -8:"Overflow.",
                    -9:"Pipe error.",
                    -10:"System call interrupted.",
                    -11:"Insufficient memory.     ",
                    -12:"Operation not supported.",
                    -50:"Device is not UVC-compliant.",
                    -51:"Mode not supported.",
                    -52:"Resource has a callback (can't use polling and async)",
                    -99:"Undefined error."}

VIDEO_FRAME_HEADER_FMT = "<LLLLQL"
AUDIO_FRAME_HEADER_FMT = "<LLLQL"

VIDEO_FRAME_FORMAT_UNKNOWN     = 0x00
VIDEO_FRAME_FORMAT_YUYV        = 0x01
VIDEO_FRAME_FORMAT_MJPEG       = 0x10
VIDEO_FRAME_FORMAT_H264        = 0x12
VIDEO_FRAME_FORMAT_VP8         = 0x13

class CaptureError(Exception):
    def __init__(self, message):
        super(CaptureError, self).__init__()
        self.message = message

class StreamError(CaptureError):
    def __init__(self, message):
        super(StreamError, self).__init__(message)
        self.message = message

class InitError(CaptureError):
    def __init__(self, message):
        super(InitError, self).__init__(message)
        self.message = message

#logging
import logging
logger = logging.getLogger(__name__)

__version__ = '0.0.1' #make sure this is the same in setup.py

@staticmethod
def unpack_metadata(packed_metadata):
    return struct.unpack("<LLLLQL", packed_metadata)

cdef class JEPGFrame(object):
    '''
    The Frame Object holds image data and image metadata.

    The Frame object is returned from Capture.get_frame()

    It will hold the data in the transport format the Capture is configured to grab.
    Usually this is mjpeg or yuyv

    Other formats can be requested and will be converted/decoded on the fly.
    Frame will use caching to avoid redunant work.
    Usually RGB8,YUYV or GRAY are requested formats.

    WARNING:
    When capture.get_frame() is called again previos instances of Frame will point to invalid memory.
    Specifically all image data in the capture transport format.
    Previously converted formats are still valid.
    '''

    def __cinit__(self,*args,**kwargs):
        self._yuv_converted = False
        self._bgr_converted = False
        self.tj_context = NULL

    def __init__(self, data_format, width, height, index, timestamp, data_len, object zmq_frame):
        #if data_format != VIDEO_FRAME_FORMAT_MJPEG:
        #    raise ValueError('%s does not support format %s'%(self.__class__.__name__, hex(data_format)))
        self._width      = width
        self._height     = height
        self._index      = index
        self._buffer_len = np.min([len(zmq_frame.buffer),data_len])
        self._raw_data   = zmq_frame
        self.timestamp   = (<double>timestamp)/1000000
        self._jpeg_buffer = zmq_frame.buffer
        self.owns_ndsi_frame = False

    def __dealloc__(self):
        pass

    property width:
        def __get__(self):
            return self._width

    property height:
        def __get__(self):
            return self._height

    property index:
        def __get__(self):
            return self._index

    property jpeg_buffer:
        def __get__(self):
            return self._jpeg_buffer

    property yuv_buffer:
        def __get__(self):
            if self._yuv_converted is False:
                self.jpeg2yuv()
            cdef np.uint8_t[::1] view = <np.uint8_t[:self._yuv_buffer.shape[0]]>&self._yuv_buffer[0]
            return view

    property yuv420:
        def __get__(self):
            '''
            planar YUV420 returned in 3 numpy arrays:
            420 subsampling:
                Y(height,width) U(height/2,width/2), V(height/2,width/2)
            '''
            if self._yuv_converted is False:
                self.jpeg2yuv()

            cdef np.ndarray[np.uint8_t, ndim=2] Y,U,V
            y_plane_len = self.width*self.height
            Y = np.asarray(self._yuv_buffer[:y_plane_len]).reshape(self.height,self.width)

            if self.yuv_subsampling == turbojpeg.TJSAMP_422:
                uv_plane_len = y_plane_len/2
                offset = y_plane_len
                U = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height,self.width/2)
                offset += uv_plane_len
                V = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height,self.width/2)
                #hack solution to go from YUV422 to YUV420
                U = U[::2,:]
                V = V[::2,:]
            elif self.yuv_subsampling == turbojpeg.TJSAMP_420:
                uv_plane_len = y_plane_len/4
                offset = y_plane_len
                U = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height/2,self.width/2)
                offset += uv_plane_len
                V = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height/2,self.width/2)
            elif self.yuv_subsampling == turbojpeg.TJSAMP_444:
                uv_plane_len = y_plane_len
                offset = y_plane_len
                U = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height,self.width)
                offset += uv_plane_len
                V = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height,self.width)
                #hack solution to go from YUV444 to YUV420
                U = U[::2,::2]
                V = V[::2,::2]
            return Y,U,V

    property yuv422:
        def __get__(self):
            '''
            planar YUV420 returned in 3 numpy arrays:
            422 subsampling:
                Y(height,width) U(height,width/2), V(height,width/2)
            '''
            if self._yuv_converted is False:
                self.jpeg2yuv()

            cdef np.ndarray[np.uint8_t, ndim=2] Y,U,V
            y_plane_len = self.width*self.height
            Y = np.asarray(self._yuv_buffer[:y_plane_len]).reshape(self.height,self.width)

            if self.yuv_subsampling == turbojpeg.TJSAMP_422:
                uv_plane_len = y_plane_len/2
                offset = y_plane_len
                U = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height,self.width/2)
                offset += uv_plane_len
                V = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height,self.width/2)
            elif self.yuv_subsampling == turbojpeg.TJSAMP_420:
                raise Exception("can not convert from YUV420 to YUV422")
            elif self.yuv_subsampling == turbojpeg.TJSAMP_444:
                uv_plane_len = y_plane_len
                offset = y_plane_len
                U = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height,self.width)
                offset += uv_plane_len
                V = np.asarray(self._yuv_buffer[offset:offset+uv_plane_len]).reshape(self.height,self.width)
                #hack solution to go from YUV444 to YUV420
                U = U[:,::2]
                V = V[:,::2]
            return Y,U,V


    property gray:
        def __get__(self):
            # return gray aka luminace plane of YUV image.
            if self._yuv_converted is False:
                self.jpeg2yuv()
            cdef np.ndarray[np.uint8_t, ndim=2] Y
            Y = np.asarray(self._yuv_buffer[:self.width*self.height]).reshape(self.height,self.width)
            return Y


    property bgr:
        def __get__(self):
            if self._bgr_converted is False:
                if self._yuv_converted is False:
                    self.jpeg2yuv()
                self.yuv2bgr()

            cdef np.ndarray[np.uint8_t, ndim=3] BGR
            BGR = np.asarray(self._bgr_buffer).reshape(self.height,self.width,3)
            return BGR


    #for legacy reasons.
    property img:
        def __get__(self):
            return self.bgr

    cdef yuv2bgr(self):
        #2.75 ms at 1080p
        cdef int channels = 3
        cdef int result
        self._bgr_buffer = np.empty(self.width*self.height*channels, dtype=np.uint8)
        result = turbojpeg.tjDecodeYUV(
            self.tj_context, &self._yuv_buffer[0], 4, self.yuv_subsampling,
            &self._bgr_buffer[0], self.width, 0,
            self.height, turbojpeg.TJPF_BGR, 0)
        if result == -1:
            logger.error('Turbojpeg yuv2bgr: %s'%turbojpeg.tjGetErrorStr() )
        self._bgr_converted = True


    cdef jpeg2yuv(self):
        # 7.55 ms on 1080p
        cdef int channels = 1
        cdef int jpegSubsamp, j_width,j_height
        cdef int result
        cdef long unsigned int buf_size
        result = turbojpeg.tjDecompressHeader2(
            self.tj_context, &self._jpeg_buffer[0], self._buffer_len,
            &j_width, &j_height, &jpegSubsamp)

        if result == -1:
            logger.error('Turbojpeg could not read jpeg header: %s'%turbojpeg.tjGetErrorStr() )
            # hacky creation of dummy data, this will break if capture does work with different subsampling:
            j_width, j_height, jpegSubsamp = self.width, self.height, turbojpeg.TJSAMP_422

        buf_size = turbojpeg.tjBufSizeYUV(j_height, j_width, jpegSubsamp)
        self._yuv_buffer = np.empty(buf_size, dtype=np.uint8)
        if result != -1:
            result = turbojpeg.tjDecompressToYUV(
                self.tj_context, &self._jpeg_buffer[0], self._buffer_len,
                &self._yuv_buffer[0], 0)
        if result == -1:
            logger.warning('Turbojpeg jpeg2yuv: %s'%turbojpeg.tjGetErrorStr() )
        self.yuv_subsampling = jpegSubsamp
        self._yuv_converted = True


    def clear_caches(self):
        self._bgr_converted = False
        self._yuv_converted = False


cdef inline int interval_to_fps(int interval):
    return int(10000000./interval)

cdef inline str uint_array_to_GuidCode(np.uint8_t * u):
    cdef str s = ''
    cdef int x
    for x in range(16):
        s += "{0:0{1}x}".format(u[x],2) # map int to rwo digit hex without "0x" prefix.
    return '%s%s%s%s%s%s%s%s-%s%s%s%s-%s%s%s%s-%s%s%s%s-%s%s%s%s%s%s%s%s%s%s%s%s'%tuple(s)

def get_time_monotonic():
    return get_sys_time_monotonic()