'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

__version__ = '0.3.2'
__protocol_version__ = '3'


class CaptureError(Exception):
    def __init__(self, message):
        super(CaptureError, self).__init__()
        self.message = message


class StreamError(CaptureError):
    def __init__(self, message):
        super(StreamError, self).__init__(message)
        self.message = message

from .network import Network
from .sensor import Sensor
from .writer import H264Writer

from . import frame
