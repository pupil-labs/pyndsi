'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

import zmq, time, logging
from pyre import Pyre, PyreEvent, zhelper
logger = logging.getLogger(__name__)

from device cimport Device
from .const.event import *

cdef class Network(object):
    ''' Communication node

    Creates Pyre node and handles all communication.
    '''
    def __cinit__(self, *args, **kwargs):
        pass

    def __init__(self, context=None, name=None, headers=(), callbacks=()):
        self.name = name
        self.uuid = None
        self.headers = headers
        self.thread_pipe = None
        self.context = context or zmq.Context()
        self.devices = {}
        self.callbacks = [self.on_event]+list(callbacks)

    def start(self):
        if self.thread_pipe:
            logger.warning('Network has already started.')
        else:
            logger.debug('Starting network...')
            self.thread_pipe = zhelper.zthread_fork(self.context, self._thread_loop)

    def stop(self):
        if not self.thread_pipe:
            logger.warning('Network has already stopped.')
        else:
            logger.debug('Stopping network...')
            self.thread_pipe.send('$TERM')
            while self.thread_pipe:
                time.sleep(.1)

    def execute_callbacks(self, event):
        for callback in self.callbacks:
            callback(self, event)

    def device(self, callbacks=()):
        return Device(self, *args, **kwargs)

    def __str__(self):
        return '<%s %s [%s]>'%(__name__, self.name, self.uuid.hex)

    def on_event(self, caller, event):
        if event['type'] == EVENT_DEVICE_ADDED:
            self.devices.update(event['device'])
        elif event['type'] == EVENT_DEVICE_REMOVED:
            try:
                del self.devices[event['device_uuid']]
            except KeyError:
                pass

    property running:
        def __get__(self):
            return self.thread_pipe is not None

    property group:
        def __get__(self):
            return 'pupil-mobile'

##############################################################################
##                              Background                                  ##
##############################################################################

    def _thread_loop(self,context,pipe):
        try:
            # Setup node
            node = Pyre(self.name)
            self.name = node.name() 
            self.uuid = node.uuid()
            for header in self.headers:
                node.set_header(*header)
            node.join(self.group)
            node.start()

            # Configure poller
            poller = zmq.Poller()
            poller.register(pipe, zmq.POLLIN)
            poller.register(node.socket(), zmq.POLLIN)

            # Event loop
            while True:
                # Check for readable sockets
                readable = dict(poller.poll())

                # Network input
                if node.socket() in readable:
                    event = PyreEvent(node)
                    if event.type == 'JOIN' and event.group == self.group:
                        self.execute_callbacks({
                            'type': EVENT_DEVICE_ADDED,
                            'device': description
                        })
                    elif (event.type == 'LEAVE' and \
                          event.group == self.group) or \
                          event.type == 'EXIT':
                        self.execute_callbacks({
                            'type': EVENT_DEVICE_REMOVED,
                            'device_uuid': event.peer_uuid
                        })

                # Local input
                if pipe in readable:
                    frame = pipe.recv_multipart()
                    command = frame.pop(0).decode('UTF-8')
                    if command == '$TERM':
                        break
                    else:
                        logger.warning('Unknown local command: %s'%command)
        except Exception as e:
            raise e
        finally:
            # Shutdown node
            node.leave(self.group)
            node.stop()
            self.thread_pipe = None
