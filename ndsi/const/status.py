'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

STATUS_OFFLINE            = "offline"
STATUS_IDLE               = "idle"
STATUS_STREAMING          = "streaming"
STATUS_CAPTURE            = "capturing"
STATUS_PREVIEW            = "previewing"

__all__ = []
for name in dir():
    if name.startswith('STATUS_'):
        __all__.append(name)