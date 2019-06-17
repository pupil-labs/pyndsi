# cython: language_level=3
'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

import json as serial
import logging
import sys
import time
import traceback  as tb

import zmq
from pyre import Pyre, PyreEvent, zhelper

from ndsi import __protocol_version__
from ndsi.sensor import Sensor, VideoSensor, AnnotateSensor, GazeSensor

logger = logging.getLogger(__name__)

SENSOR_TYPE_CLASS_MAP = {
    "hardware": Sensor,
    "video": VideoSensor,
    "annotate": AnnotateSensor,
    "gaze": GazeSensor,
    "imu": IMUSensor,
}

cdef class Network:
    ''' Communication node

    Creates Pyre node and handles all communication.
    '''

    group = 'pupil-mobile-v{}'.format(__protocol_version__)

    def __cinit__(self, *args, **kwargs):
        pass

    def __init__(self, context=None, name=None, headers=(), callbacks=()):
        self.name = name
        self.headers = headers
        self.pyre_node = None
        self.context = context or zmq.Context()
        self.sensors = {}
        self.callbacks = [self.on_event]+list(callbacks)
        self._warned_once_older_version = False
        self._warned_once_newer_version = False

    def start(self):
        # Setup node
        logger.debug('Starting network...')
        self.pyre_node = Pyre(self.name)
        self.name = self.pyre_node.name()
        for header in self.headers:
            self.pyre_node.set_header(*header)
        self.pyre_node.join(self.group)
        self.pyre_node.start()

    def rejoin(self):
        for sensor_uuid, sensor in list(self.sensors.items()):
            self.execute_callbacks({
                'subject': 'detach',
                'sensor_uuid': sensor_uuid,
                'sensor_name': sensor['sensor_name'],
                'host_uuid': sensor['host_uuid'],
                'host_name': sensor['host_name']})
        self.pyre_node.leave(self.group)
        self.pyre_node.join(self.group)

    def stop(self):
        logger.debug('Stopping network...')
        self.pyre_node.leave(self.group)
        self.pyre_node.stop()
        self.pyre_node = None

    def handle_event(self):
        event = PyreEvent(self.pyre_node)
        uuid = event.peer_uuid
        if event.type == 'SHOUT' or event.type == 'WHISPER':
            try:
                payload = event.msg.pop(0).decode()
                msg = serial.loads(payload)
                msg['subject']
                msg['sensor_uuid']
                msg['host_uuid'] = event.peer_uuid.hex
                msg['host_name'] = event.peer_name
            except serial.decoder.JSONDecodeError:
                logger.warning('Malformatted message: "{}"'.format(payload))
            except (ValueError, KeyError):
                logger.warning('Malformatted message: {}'.format(msg))
            except Exception:
                logger.debug(tb.format_exc())
            else:
                if msg['subject'] == 'attach':
                    if self.sensors.get(msg['sensor_uuid']):
                        # Sensor already attached. Drop event
                        return
                elif msg['subject'] == 'detach':
                    sensor_entry = self.sensors.get(msg['sensor_uuid'])
                    # Check if sensor has been detached already
                    if not sensor_entry: return
                    msg.update(sensor_entry)
                else:
                    logger.debug('Unknown host message: {}'.format(msg))
                    return
                self.execute_callbacks(msg)
        elif event.type == 'JOIN':
            # possible values for `group_version`
            # - [<unrelated group>]
            # - [<unrelated group>, <unrelated version>]
            # - ['pupil-mobile']
            # - ['pupil-mobile', <version>]
            group_version = event.group.split('-v')
            group = group_version[0]
            version = group_version[1] if len(group_version) > 1 else '0'
            if group == 'pupil-mobile':
                if not self._warned_once_older_version and version < __protocol_version__:
                    logger.warning('Devices with outdated NDSI version found. Please update these devices.')
                    self._warned_once_older_version = True
                elif not self._warned_once_newer_version and version > __protocol_version__:
                    logger.warning('Devices with newer NDSI version found. You should update.')
                    self._warned_once_newer_version = True

        elif event.type == 'EXIT':
            gone_peer = event.peer_uuid.hex
            for sensor_uuid in list(self.sensors.keys()):
                host = self.sensors[sensor_uuid]['host_uuid']
                if host == gone_peer:
                    self.execute_callbacks({
                        'subject': 'detach',
                        'sensor_uuid': sensor_uuid,
                        'sensor_name': self.sensors[sensor_uuid]['sensor_name'],
                        'host_uuid': host,
                        'host_name': self.sensors[sensor_uuid]['host_name']})
        else:
            logger.debug('Dropping {}'.format(event))

    def execute_callbacks(self, event):
        for callback in self.callbacks:
            callback(self, event)

    def sensor(self, sensor_uuid, callbacks=()):
        try:
            sensor_settings = self.sensors[sensor_uuid]
        except KeyError:
            raise ValueError('"{}" is not an available sensor id.'.format(sensor_uuid))

        try:
            sensor_type = sensor_settings.get("sensor_type", "unknown")
            sensor_cls = SENSOR_TYPE_CLASS_MAP[sensor_type]
        except KeyError:
            raise ValueError('Sensor of type "{}" is not supported.'.format(sensor_type))

        sensor = sensor_cls(
            context=self.context,
            callbacks=callbacks,
            **sensor_settings
        )
        return sensor

    def on_event(self, caller, event):
        if event['subject'] == 'attach':
            subject_less = event.copy()
            del subject_less['subject']
            self.sensors.update({event['sensor_uuid']: subject_less})
        elif event['subject'] == 'detach':
            try:
                del self.sensors[event['sensor_uuid']]
            except KeyError:
                pass

    def __str__(self):
        return '<{} {} [{}]>'.format(__name__, self.name, self.pyre_node.uuid().hex)

    property has_events:
        def __get__(self):
            return self.running and self.pyre_node.socket().get(zmq.EVENTS) & zmq.POLLIN

    property running:
        def __get__(self):
            return bool(self.pyre_node)
