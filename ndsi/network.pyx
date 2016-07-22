'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

import zmq, time, logging, sys, traceback as tb, json as serial
from pyre import Pyre, PyreEvent, zhelper
logger = logging.getLogger(__name__)

from . import NDS_PROTOCOL_VERSION
from sensor cimport Sensor

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
                msg = serial.loads(event.msg.pop(0))
                msg['subject']
                key = '%s@%s'%(msg['sensor_name'], event.peer_uuid.hex)
                msg['sensor_id'] = key
                msg['host_uuid'] = unicode(event.peer_uuid.hex)
                msg['host_name'] = event.peer_name
            except (ValueError, KeyError):
                logger.warning('Malformatted message: %s'%msg)
            except Exception:
                tb.print_exc()
            else:
                self.execute_callbacks(msg)
        elif event.type == 'EXIT':
            gone_peer = event.peer_uuid.hex
            for sensor_id in self.sensors.keys():
                host = sensor_id.split('@')[-1]
                if host == gone_peer:
                    self.execute_callbacks({
                        'subject'    : 'detach',
                        'sensor_id'  : sensor_id,
                        'sensor_name': self.sensors[sensor_id]['sensor_name'],
                        'host_uuid'  : self.sensors[sensor_id]['host_uuid'],
                        'host_name'  : self.sensors[sensor_id]['host_name']
                    })
        else:
            logger.debug('Dropping %s'%event)

    def execute_callbacks(self, event):
        for callback in self.callbacks:
            callback(self, event)

    def sensor(self, sensor_id, callbacks=()):
        try:
            sensor = Sensor(context=self.context, callbacks=callbacks, **self.sensors[sensor_id])
            return sensor
        except KeyError:
            raise ValueError('"%s" is not a available sensor id.'%sensor_id)

    def on_event(self, caller, event):
        if   event['subject'] == 'attach':
            subject_less = event.copy()
            del subject_less['subject']
            self.sensors.update({ event['sensor_id']: subject_less })
        elif event['subject'] == 'detach':
            try:
                del self.sensors[event['sensor_id']]
            except KeyError:
                pass

    def __str__(self):
        return '<%s %s [%s]>'%(__name__, self.name, self.pyre_node.uuid().hex)

    property has_events:
        def __get__(self):
            return self.running and self.pyre_node.socket().get(zmq.EVENTS) & zmq.POLLIN

    property running:
        def __get__(self):
            return bool(self.pyre_node)

    property group:
        def __get__(self):
            return 'pupil-mobile'
