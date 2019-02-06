# cython: language_level=3
'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Diunicodeibuted under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, diunicodeibuted as part of this software.
----------------------------------------------------------------------------------~(*)
'''

import logging
from os import path, remove

import numpy as np

from ndsi.frame cimport H264Frame

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

cdef class H264Writer:

    def __cinit__(self, video_loc,int width,int height,int fps, *args, **kwargs):
        self.video_loc = video_loc
        # Mp4Writer takes a std:string
        # http://cython.readthedocs.io/en/latest/src/tutorial/strings.html#c-strings
        assert fps
        self.fps = fps
        self.width = width
        self.height = height
        self.timestamps = []
        self.waiting_for_iframe = True
        self.frame_count = 0
        self.video_stream = new VideoStream(width, height, fps)
        self.proxy = new Mp4Writer(self.video_loc.encode('utf-8'))
        self.proxy.add(self.video_stream)
        self.proxy.start()
        logger.debug("Opened '{}' for writing.".format(self.video_loc))

    def __init__(self, *args, **kwargs):
        pass

    def write_video_frame(self, input_frame):
        if not self.proxy.isRunning():
            logger.error('Mp4Writer not running')
            return
        if not isinstance(input_frame, H264Frame):
            logger.error('Expected H264Frame but got {}'.format(type(input_frame)))
            return
        if not self.width == input_frame.width:
            logger.error('Expected width {} but got {}'.format(self.width, input_frame.width))
        if not self.height == input_frame.height:
            logger.error('Expected height {} but got {}'.format(self.height, input_frame.height))

        if self.waiting_for_iframe:
            if input_frame.is_iframe:
                self.waiting_for_iframe = False
            else:
                logger.debug('No I-frame found yet -- dropping frame.')
                return

        cdef unsigned char[:] buffer_ = input_frame.h264_buffer
        #we are using indexing pts instead of real pts
        # cdef long long pts = <long long>(input_frame.timestamp * 1e6)
        cdef long long pts = <long long>int((self.frame_count*1e6/self.fps))
        self.proxy.set_input_buffer(0, &buffer_[0], len(buffer_), pts)
        self.timestamps.append(input_frame.timestamp)
        self.frame_count +=1

    def close(self):
        # Access number of written frames first
        # since proxy.release() releases the stream
        if self.video_stream != NULL:
            num_frames_written = self.video_stream.num_frames_written()
        else:
            num_frames_written = 0

        if self.proxy != NULL:
            self.proxy.release()
            self.proxy = NULL

        if num_frames_written:
            self.write_timestamps()
        else:
            try:
                # no frames have been written. Do not write timestamps
                # and delete empty video container
                remove(self.video_loc)
            except OSError:
                logger.debug('Video file has not been created')
            raise RuntimeError('Empty world video recording')

    def release(self):
        self.close()

    def write_timestamps(self):
        directory, video_file = path.split(self.video_loc)
        name, ext = path.splitext(video_file)
        ts_file = '{}_timestamps.npy'.format(name)
        ts_loc = path.join(directory, ts_file)
        ts = np.array(self.timestamps)
        np.save(ts_loc, ts)
