'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

import time
import sys
import json as serial
import traceback  as tb

import zmq
from pyre import Pyre, PyreEvent, zhelper

from . import NDS_PROTOCOL_VERSION
from .sensor cimport Sensor

import logging
logger = logging.getLogger(__name__)


cdef class Network(object):
    ''' Communication node

    Creates Pyre node and handles all communication.
    '''
    def __cinit__(self, *args, **kwargs):
        pass

    def __init__(self, context=None, name=None, headers=(), callbacks=()):
        self.name = name
        self.headers = [('nds-protocol-version', NDS_PROTOCOL_VERSION)]+list(headers)
        self.pyre_node = None
        self.context = context or zmq.Context()
        self.sensors = {}
        self.callbacks = [self.on_event]+list(callbacks)

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
            sensor = Sensor(context=self.context, callbacks=callbacks, **self.sensors[sensor_uuid])
            return sensor
        except KeyError:
            raise ValueError('"{}" is not an available sensor id.'.format(sensor_uuid))

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

    property group:
        def __get__(self):
            return 'pupil-mobile'
