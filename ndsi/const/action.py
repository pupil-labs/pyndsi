'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

ACTION_COMSPEC_VERSION    = "COMSPEC_VERSION"
ACTION_APP_VERSION        = "APP_VERSION"
ACTION_DEVICES            = "DEVICES"
ACTION_STREAM_ON          = "STREAM_ON"
ACTION_STREAM_OFF         = "STREAM_OFF"
ACTIION_STREAM_TERMINATE  = "STREAM_TERMINATE"
ACTION_STORE_ON           = "STORE_ON"
ACTION_STORE_OFF          = "STORE_OFF"
ACTION_CONTROLS           = "CONTROLS"
ACTION_GET                = "GET"
ACTION_SET                = "SET"
ACTION_INFO               = "INFO"

__all__ = []
for name in dir():
    if name.startswith('ACTION_'):
        __all__.append(name)