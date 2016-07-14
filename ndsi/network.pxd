'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cdef class Network(object):

    cdef object _context
    cdef unicode _name
    cdef object _uuid
    cdef object _headers
    cdef object _thread_pipe
    cdef dict _devices