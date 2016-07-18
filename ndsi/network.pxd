'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cdef class Network(object):

    cdef object context
    cdef object thread_pipe
    cdef readonly unicode name
    cdef readonly object uuid
    cdef readonly object headers
    cdef readonly list callbacks
    cdef readonly dict devices