"""
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
"""

from ndsi.errors import CaptureError, StreamError
from ndsi.formatter import DataFormat

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version("ndsi")
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"

__protocol_version__ = str(DataFormat.latest().version_major)


from ndsi import frame
from ndsi.network import Network
from ndsi.sensor import Sensor
from ndsi.writer import H264Writer

__all__ = [
    "__version__",
    "CaptureError",
    "frame",
    "H264Writer",
    "Network",
    "Sensor",
    "StreamError",
]
