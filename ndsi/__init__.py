'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

NDS_PROTOCOL_VERSION = '0.2.16'

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

from . import frame
