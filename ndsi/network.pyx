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

cdef class Network(object):
    ''' Communication node

    Creates Pyre node and handles all communication.
    '''
    def __cinit__(self, *args, **kwargs):
        pass

    def __init__(self, context=None, name=None, headers=(),):
        self._context = context or zmq.Context()
        self._name = name
        self._uuid = None
        self._headers = headers
        self._thread_pipe = None
        self._devices = {}

    def start(self):
        if self._thread_pipe:
            logger.warning('Network has already started.')
        else:
            logger.debug('Starting network...')
            self._thread_pipe = zhelper.zthread_fork(self.context, self._thread_loop)

    def stop(self):
        if not self._thread_pipe:
            logger.warning('Network has already stopped.')
        else:
            logger.debug('Stopping network...')
            self._thread_pipe.send('$TERM')
            while self._thread_pipe:
                time.sleep(.1)

    def list_devices(self):
        return tuple(self._devices)

    def __str__(self):
        return '<%s %s [%s]>'%(__name__, self.name, self.uuid.hex)

    property running:
        def __get__(self):
            return self._thread_pipe is not None

    property name:
        def __get__(self):
            return self._name

    property uuid:
        def __get__(self):
            return self._uuid

    property headers:
        def __get__(self):
            return self._headers

    property context:
        def __get__(self):
            return self._context

    property group:
        def __get__(self):
            return 'pupil-mobile'

##############################################################################
##                              Background                                  ##
##############################################################################

    def _thread_loop(self,context,pipe):

        # Setup node
        node = Pyre(self.name)
        self._name = node.name()
        self._uuid = node.uuid()
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
                    self._add_device(node,event)
                elif (event.type == 'LEAVE' and \
                      event.group == self.group) or \
                      event.type == 'EXIT':
                    self._remove_device(event)
                    pass

            # Local input
            if pipe in readable:
                command = pipe.recv().decode('UTF-8')
                if command == '$TERM':
                    break
                else:
                    logger.warning('Unknown local command: %s'%command)

        # Shutdown node
        node.leave(self.group)
        node.stop()
        self._thread_pipe = None

    def _add_device(self, node, event):
        uuid = event.peer_uuid
        headers = node.peer_headers(uuid)
        dev = Device(self, uuid, event.peer_name, headers)
        self._devices.update({uuid:dev})
        logger.debug('%s found new %s'%(self,dev))
        # TODO: callback

    def _remove_device(self, event):
        try:
            uuid = event.peer_uuid
            logger.debug('%s lost %s'%(self,self._devices[uuid]))
            del self._devices[uuid]
            # TODO: callback
        except KeyError:
            pass