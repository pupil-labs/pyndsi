import abc
import collections
import enum
import functools
import typing
import struct
import numpy as np

from ndsi import StreamError
from ndsi.frame import JPEGFrame, H264Frame, FrameFactory
from ndsi.frame import VIDEO_FRAME_FORMAT_H264, VIDEO_FRAME_FORMAT_MJPEG


__all__ = [
    'DataFormat', 'DataFormatter', 'DataMessage',
    'VideoDataFormatter', 'VideoValue',
    'GazeDataFormatter', 'GazeValue',
    'AnnotateDataFormatter', 'AnnotateValue',
    'IMUDataFormatter', 'IMUValue',
]


NANO = 1e-9


@enum.unique
class DataFormat(enum.Enum):
    V3 = 'v3'
    V4 = 'v4'

    @staticmethod
    def supported_formats() -> typing.Set['DataFormat']:
        return set(DataFormat)


class DataMessage(typing.NamedTuple):
    sensor_id: str
    header: bytes
    body: bytes


DT = typing.TypeVar('DataValue')


class DataFormatter(typing.Generic[DT], abc.ABC):

    @abc.abstractstaticmethod
    def get_formatter(format: DataFormat) -> 'DataFormatter':
        pass

    @abc.abstractmethod
    def encode_msg(self, value: DT) -> DataMessage:
        pass

    @abc.abstractmethod
    def decode_msg(self, data_msg: DataMessage) -> DT:
        pass


##########


VideoValue = typing.Union[JPEGFrame, H264Frame]


class VideoDataFormatter(DataFormatter[VideoValue]):
    def reset(self):
        pass

    @staticmethod
    @functools.lru_cache(maxsize=1, typed=True)
    def get_formatter(format: DataFormat) -> 'VideoDataFormatter':
        if format == DataFormat.V3:
            return _VideoDataFormatter_V3()
        if format == DataFormat.V4:
            return _VideoDataFormatter_V4()
        raise ValueError(format)

    def encode_msg(self, value: VideoValue) -> DataMessage:
        raise NotImplementedError()


class _VideoDataFormatter_V3(VideoDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> VideoValue:
        raise NotImplementedError()  # FIXME


class _VideoDataFormatter_V4(VideoDataFormatter):
    def __init__(self):
        super().__init__()
        self._frame_factory = FrameFactory()
        self._newest_h264_frame = None

    def reset(self):
        super().reset()
        self._newest_h264_frame = None

    def decode_msg(self, data_msg: DataMessage) -> VideoValue:
        meta_data = struct.unpack("<LLLLQLL", data_msg.header)
        if meta_data[0] == VIDEO_FRAME_FORMAT_MJPEG:
            return self._frame_factory.create_jpeg_frame(data_msg.body, meta_data)
        elif meta_data[0] == VIDEO_FRAME_FORMAT_H264:
            frame = self._frame_factory.create_h264_frame(data_msg.body, meta_data)
            self._newest_h264_frame = frame or self._newest_h264_frame
            return self._newest_h264_frame
        else:
            raise StreamError('Frame was not of format MJPEG or H264')


##########


# TODO: Where is the format for annotation data defined?
class AnnotateValue(typing.NamedTuple):
    key: int
    timestamp: float


class AnnotateDataFormatter(DataFormatter[AnnotateValue]):
    @staticmethod
    @functools.lru_cache(maxsize=1, typed=True)
    def get_formatter(format: DataFormat) -> 'AnnotateDataFormatter':
        if format == DataFormat.V3:
            return _AnnotateDataFormatter_V3()
        if format == DataFormat.V4:
            return _AnnotateDataFormatter_V4()
        raise ValueError(format)

    def encode_msg(self, value: AnnotateValue) -> DataMessage:
        raise NotImplementedError()


class _AnnotateDataFormatter_V3(AnnotateDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> AnnotateValue:
        raise NotImplementedError()  # FIXME


class _AnnotateDataFormatter_V4(AnnotateDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> AnnotateValue:
        # data_msg[0]: sensor uuid
        # data_msg[1]: metadata, None for now
        # data_msg[2]: <uint8 - button state> <uint64_t - timestamp>
        key, ts = struct.unpack("<BQ", data_msg[0]) # FIXME: Why do we pass item at index 0 here?
        ts *= NANO
        return AnnotateValue(key=key, timestamp=ts)


##########


class GazeValue(typing.NamedTuple):
    x: int
    y: int
    timestamp: float


class GazeDataFormatter(DataFormatter[GazeValue]):
    @staticmethod
    @functools.lru_cache(maxsize=1, typed=True)
    def get_formatter(format: DataFormat) -> 'GazeDataFormat':
        if format == DataFormat.V3:
            return _GazeDataFormatter_V3()
        if format == DataFormat.V4:
            return _GazeDataFormatter_V4()
        raise ValueError(format)

    def encode_msg(self, value: GazeValue) -> DataMessage:
        raise NotImplementedError()


class _GazeDataFormatter_V3(GazeDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> GazeValue:
        raise NotImplementedError()  # FIXME


class _GazeDataFormatter_V4(GazeDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> GazeValue:
        ts, = struct.unpack("<Q", data_msg.header)
        ts *= NANO
        x, y = struct.unpack("<ff", data_msg.body)
        return GazeValue(x=x, y=y, timestamp=ts)


##########


class IMUValue(typing.NamedTuple):
    timestamp: float
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float


class IMUDataFormatter(DataFormatter[IMUValue]):
    @staticmethod
    @functools.lru_cache(maxsize=1, typed=True)
    def get_formatter(format: DataFormat) -> 'IMUDataFormatter':
        if format == DataFormat.V3:
            return _IMUDataFormatter_V3()
        if format == DataFormat.V4:
            return _IMUDataFormatter_V4()
        raise ValueError(format)

    def encode_msg(self, value: IMUValue) -> DataMessage:
        raise NotImplementedError()


class _IMUDataFormatter_V3(IMUDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> IMUValue:
        raise NotImplementedError()  # FIXME


class _IMUDataFormatter_V4(IMUDataFormatter):
    CONTENT_DTYPE = np.dtype(
        [
            ("time_s", "<f8"),
            ("accel_x", "<f4"),
            ("accel_y", "<f4"),
            ("accel_z", "<f4"),
            ("gyro_x", "<f4"),
            ("gyro_y", "<f4"),
            ("gyro_z", "<f4"),
        ]
    )

    def decode_msg(self, data_msg: DataMessage) -> IMUValue:
        content = np.frombuffer(data_msg.body, dtype=self.CONTENT_DTYPE).view(np.recarray)
        return IMUValue(*content)
