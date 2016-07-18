'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

EVENT_DEVICE_ADDED              = "device.added"
EVENT_DEVICE_REMOVED            = "device.removed"
EVENT_SENSOR_ADDED              = "sensor.added"
EVENT_SENSOR_REMOVED            = "sensor.removed"
EVENT_PROPERTIES_ADDED          = "properties.added"
EVENT_PROPERTY_CHANGED          = "property.changed"

__all__ = []
for name in dir():
    if name.startswith('EVENT_'):
        __all__.append(name)