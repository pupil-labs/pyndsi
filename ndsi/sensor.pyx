'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

import zmq, traceback as tb, json as serial, logging
logger = logging.getLogger(__name__)

class NotDataSubSupportedError(Exception):
    def __init__(self, value=None):
        self.value = value or 'This sensor does not support data subscription.'
    def __str__(self):
        return repr(self.value)

cdef class Sensor(object):

    def __cinit__(self, *args, **kwargs):
        pass

    def __init__(self,
            host_uuid,
            host_name,
            sensor_uuid,
            sensor_name,
            sensor_type,
            notify_endpoint,
            command_endpoint,
            data_endpoint=None,
            context=None,
            callbacks=()):
        self.callbacks = [self.on_notification]+list(callbacks)
        self.context = context or zmq.Context()
        self.host_uuid = host_uuid
        self.host_name = host_name
        self.name = sensor_name
        self.type = sensor_type
        self.uuid = sensor_uuid
        self.notify_endpoint = notify_endpoint
        self.command_endpoint = command_endpoint
        self.data_endpoint = data_endpoint
        self.controls = {}

        self.notify_sub = context.socket(zmq.SUB)
        self.notify_sub.connect(self.notify_endpoint)
        self.notify_sub.setsockopt(zmq.SUBSCRIBE, str(self.uuid))

        self.command_push = context.socket(zmq.PUSH)
        self.command_push.connect(self.command_endpoint)

        if self.data_endpoint:
            self.data_sub = context.socket(zmq.SUB)
            self.data_sub.connect(self.data_endpoint)
            self.data_sub.setsockopt(zmq.SUBSCRIBE, str(self.uuid))
        else:
            self.data_sub = None

        self.refresh_controls()

    def unlink(self):
        self.notify_sub.close()
        self.command_push.close()
        if self.supports_data_subscription:
            self.data_sub.close()

    def __del__(self):
        logger.debug('Sensor deleted: %s',self)
        self.unlink()

    property supports_data_subscription:
        def __get__(self):
            return bool(self.data_sub)

    property has_notifications:
        def __get__(self):
            has_n = self.notify_sub.get(zmq.EVENTS) & zmq.POLLIN
            return has_n

    property has_data:
        def __get__(self):
            try:
                return self.data_sub.get(zmq.EVENTS) & zmq.POLLIN
            except AttributeError:
                raise NotDataSubSupportedError()

    def __str__(self):
        return '<%s %s@%s [%s]>'%(__name__, self.name, self.host_name, self.type)

    def handle_notification(self):
        msg = self.notify_sub.recv_multipart()
        try:
            if msg[0] != self.uuid:
                raise ValueError('Message was destined for %s but was recieved by %s'%(msg[0],self.uuid))
            notification = serial.loads(msg[1])
            notification['subject']
        except Exception:
            tb.print_exc()
        else:
            self.execute_callbacks(notification)

    def execute_callbacks(self, event):
        for callback in self.callbacks:
            callback(self, event)

    def on_notification(self, caller, notification):
        if   notification['subject'] == 'update':
            class UnsettableDict(dict):
                def __setitem__(self, key, value):
                    raise ValueError('Dictionary is read-only. Use Sensor.set_control_value instead.')

            self.controls.update({
                notification['control_id']: UnsettableDict(notification['changes'])
            })
        elif notification['subject'] == 'remove':
            try:
                del self.controls[notification['control_id']]
            except KeyError:
                pass

    def get_data(self):
        try:
            return self.data_sub.recv()
        except AttributeError:
            raise NotDataSubSupportedError()

    def refresh_controls(self):
        cmd = serial.dumps({'action': 'refresh_controls'})
        self.command_push.send_multipart([str(self.uuid), cmd])

    def reset_all_control_values(self):
        for control_id in self.controls:
            self.reset_control_value(control_id)

    def reset_control_value(self, control_id):
        value = self.controls[control_id]['def']
        self.set_control_value(control_id, value)

    def set_control_value(self, control_id, value):
        cmd = serial.dumps({
            'action'    : 'set_control_value',
            "control_id": control_id,
            "value"     : value
        })
        self.command_push.send_multipart([str(self.uuid), cmd])

    def stream_on(self):
        cmd = serial.dumps({'action': 'stream_on'})
        self.command_push.send_multipart([str(self.uuid), cmd])

    def stream_off(self):
        cmd = serial.dumps({'action': 'stream_off'})
        self.command_push.send_multipart([str(self.uuid), cmd])

    def record_on(self):
        cmd = serial.dumps({'action': 'record_on'})
        self.command_push.send_multipart([str(self.uuid), cmd])

    def record_off(self):
        cmd = serial.dumps({'action': 'record_off'})
        self.command_push.send_multipart([str(self.uuid), cmd])