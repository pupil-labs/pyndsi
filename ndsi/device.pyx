'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cdef class Device(object):
    ''' Device representation
    '''

    def __cinit__(self, *args, **kwargs):
        pass

    def __init__(self, network, uuid, name, headers):
        self._network = network
        self._uuid = uuid
        self._name = name
        self._headers = headers

    def __str__(self):
        return '<%s %s [%s]>'%(__name__, self.name, self.uuid.hex)

    property name:
        def __get__(self):
            return self._name
    property uuid:
        def __get__(self):
            return self._uuid
    property headers:
        def __get__(self):
            return self._headers