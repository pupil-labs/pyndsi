'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

from network cimport Network

cdef class Device(object):
    ''' Device representation
    '''
    cdef readonly Network network
    cdef readonly object uuid
    cdef readonly unicode name
    cdef readonly dict headers

    cdef readonly list callbacks
    cdef readonly dict sensors