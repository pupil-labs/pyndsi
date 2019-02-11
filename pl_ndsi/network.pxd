# cython: language_level=3
'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cdef class Network:

    cdef object context
    cdef unicode name
    cdef object headers
    cdef bint _warned_once_older_version, _warned_once_newer_version
    cdef readonly list callbacks
    cdef readonly dict sensors
    cdef readonly object pyre_node
