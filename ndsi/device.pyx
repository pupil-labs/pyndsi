'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''
from .const.event import *

cdef class Device(object):
    ''' Device representation
    '''

    def __cinit__(self, *args, **kwargs):
        pass

    def __init__(self, network, uuid, name, headers=(), callbacks=(), *args, **kwargs):
        self.network = network
        self.uuid = uuid
        self.name = name
        self.headers = headers
        self.sensors = {}
        self.callbacks = [self.on_event]+list(callbacks)

    def __str__(self):
        return '<%s %s [%s]>'%(__name__, self.name, self.uuid.hex)

    def on_event(self, caller, name, event):
        if name == EVENT_SENSOR_ADDED:
            self.sensors.update(event)
        elif name == EVENT_SENSOR_REMOVED:
            try:
                del self.sensors[event]
            except KeyError:
                pass