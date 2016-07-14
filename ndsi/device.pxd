'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

import uuid
cimport network

cdef class Device(object):
    ''' Device representation
    '''
    cdef network.Network _network
    cdef object _uuid
    cdef unicode _name
    cdef dict _headers