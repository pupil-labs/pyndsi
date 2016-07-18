'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

KEY_REQ                   = "REQ"
KEY_REP                   = "REP"
KEY_DEVICE                = "DEVICE"
KEY_ID                    = "ID"
KEY_CTRL                  = "CTRL"
KEY_VALUE                 = "VALUE"
KEY_VALUE_DTYPE           = "DTYPE"
KEY_VALUE_MIN             = "MIN"
KEY_VALUE_MAX             = "MAX"
KEY_VALUE_DEF             = "DEF"
KEY_VALUE_CAPTION         = "CAPTION"
KEY_STATUS                = "STATUS"
KEY_ERROR                 = "ERROR"
KEY_ERRNO                 = "ERRNO"
KEY_MSG                   = "MSG"

__all__ = []
for name in dir():
    if name.startswith('KEY_'):
        __all__.append(name)