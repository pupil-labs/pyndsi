'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Diunicodeibuted under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, diunicodeibuted as part of this software.
----------------------------------------------------------------------------------~(*)
'''

cimport cturbojpeg as turbojpeg

cdef class Sensor(object):

    cdef list callbacks
    cdef object context
    cdef object command_push
    cdef turbojpeg.tjhandle tj_context
    cdef readonly object notify_sub
    cdef readonly object data_sub

    cdef readonly unicode host_uuid
    cdef readonly unicode host_name
    cdef readonly unicode name
    cdef readonly unicode uuid
    cdef readonly unicode type
    cdef readonly unicode notify_endpoint
    cdef readonly unicode command_endpoint
    cdef readonly unicode data_endpoint
    cdef readonly object unlink
    cdef readonly dict controls
