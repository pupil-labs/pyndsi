import abc
import collections
import enum
import functools
import struct
import typing

import numpy as np

from ndsi import StreamError
from ndsi.frame import (
    VIDEO_FRAME_FORMAT_H264,
    VIDEO_FRAME_FORMAT_MJPEG,
    FrameFactory,
    H264Frame,
    JPEGFrame,
)

__all__ = [
    "DataFormat",
    "DataFormatter",
    "DataMessage",
    "VideoDataFormatter",
    "VideoValue",
    "GazeDataFormatter",
    "GazeValue",
    "AnnotateDataFormatter",
    "AnnotateValue",
    "IMUDataFormatter",
    "IMUValue",
]


NANO = 1e-9


"""
To add a new data format version, in `formatter.py`:
1. Add a new case to the `DataFormat` enum.
2. For each concrete sublcass of `DataFormatter` (except `UnsupportedFormatter`), extend the implementation of `get_formatter` to correctly handle the new format version.
3. Run the test suit to make sure that all the tests pass again.
4. Write additional tests to cover the custom behaviour of the new data format.
"""


@enum.unique
class DataFormat(enum.Enum):
    """
    `DataFormat` enum represents the format for serializing and deserializing data between NDSI hosts and clients.
    """

    V3 = "v3"
    V4 = "v4"

    @staticmethod
    def latest() -> "DataFormat":
        return max(DataFormat.supported_formats(), key=lambda f: f.version_major)

    @staticmethod
    def supported_formats() -> typing.Set["DataFormat"]:
        return set(DataFormat)

    @property
    def version_major(self) -> int:
        return int(self.value[1:])

    def __str__(self) -> str:
        return self.value


class DataMessage(typing.NamedTuple):
    sensor_id: str
    header: bytes
    body: bytes


DataValue = typing.TypeVar("DataValue")


class DataFormatter(typing.Generic[DataValue], abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def get_formatter(format: DataFormat) -> "DataFormatter":
        pass

    @abc.abstractmethod
    def encode_msg(self, value: DataValue) -> DataMessage:
        pass

    @abc.abstractmethod
    def decode_msg(self, data_msg: DataMessage) -> typing.Iterator[DataValue]:
        pass


##########


class UnsupportedFormatter(DataFormatter[typing.Any]):
    """
    Represents a formatter that is not supported for a specific data format and sensor type combination.
    """

    @staticmethod
    def get_formatter(format: DataFormat) -> "UnsupportedFormatter":
        return UnsupportedFormatter()

    def encode_msg(self, value: DataValue) -> DataMessage:
        raise ValueError("Unsupported data format.")

    def decode_msg(self, value: DataMessage) -> typing.Iterator[DataValue]:
        raise ValueError("Unsupported data format.")


##########


VideoValue = typing.Union[JPEGFrame, H264Frame]


class VideoDataFormatter(DataFormatter[VideoValue]):
    def __init__(self):
        super().__init__()
        self._frame_factory = FrameFactory()
        self._newest_h264_frame = None

    def reset(self):
        self._newest_h264_frame = None

    @staticmethod
    @functools.lru_cache(maxsize=1, typed=True)
    def get_formatter(
        format: DataFormat,
    ) -> typing.Union["VideoDataFormatter", UnsupportedFormatter]:
        if format == DataFormat.V3:
            return _VideoDataFormatter_V3()
        if format == DataFormat.V4:
            return _VideoDataFormatter_V4()
        raise ValueError(format)

    def encode_msg(self, value: VideoValue) -> DataMessage:
        raise NotImplementedError()


class _VideoDataFormatter_V3(VideoDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> VideoValue:
        meta_data = struct.unpack("<LLLLdLL", data_msg.header)
        meta_data_mutable = list(meta_data)
        meta_data_mutable[4] *= 1e6  #  Convert timestamp s -> us
        meta_data = tuple(meta_data_mutable)
        if meta_data[0] == VIDEO_FRAME_FORMAT_MJPEG:
            yield self._frame_factory.create_jpeg_frame(data_msg.body, meta_data)
        elif meta_data[0] == VIDEO_FRAME_FORMAT_H264:
            frame = self._frame_factory.create_h264_frame(data_msg.body, meta_data)
            self._newest_h264_frame = frame or self._newest_h264_frame
            yield self._newest_h264_frame
        else:
            raise StreamError("Frame was not of format MJPEG or H264")


class _VideoDataFormatter_V4(VideoDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> VideoValue:
        meta_data = struct.unpack("<LLLLQLL", data_msg.header)
        meta_data_mutable = list(meta_data)
        meta_data_mutable[4] /= 1e3  #  Convert timestamp ns -> us
        meta_data = tuple(meta_data_mutable)
        if meta_data[0] == VIDEO_FRAME_FORMAT_MJPEG:
            yield self._frame_factory.create_jpeg_frame(data_msg.body, meta_data)
        elif meta_data[0] == VIDEO_FRAME_FORMAT_H264:
            frame = self._frame_factory.create_h264_frame(data_msg.body, meta_data)
            self._newest_h264_frame = frame or self._newest_h264_frame
            yield self._newest_h264_frame
        else:
            raise StreamError("Frame was not of format MJPEG or H264")


##########


# TODO: Where is the format for annotation data defined?
class AnnotateValue(typing.NamedTuple):
    key: int
    timestamp: float


class AnnotateDataFormatter(DataFormatter[AnnotateValue]):
    @staticmethod
    @functools.lru_cache(maxsize=1, typed=True)
    def get_formatter(
        format: DataFormat,
    ) -> typing.Union["AnnotateDataFormatter", UnsupportedFormatter]:
        if format == DataFormat.V3:
            return _AnnotateDataFormatter_V3()
        if format == DataFormat.V4:
            return _AnnotateDataFormatter_V4()
        raise ValueError(format)

    def encode_msg(self, value: AnnotateValue) -> DataMessage:
        raise NotImplementedError()


class _AnnotateDataFormatter_V3(AnnotateDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> typing.Iterator[AnnotateValue]:
        # NOTE: Annotation sensor is currently not NDSI-conformant.
        key, ts = struct.unpack("<Bd", data_msg[0])
        yield AnnotateValue(key=key, timestamp=ts)


class _AnnotateDataFormatter_V4(AnnotateDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> typing.Iterator[AnnotateValue]:
        # NOTE: Annotation sensor is currently not NDSI-conformant.
        key, ts = struct.unpack("<BQ", data_msg[0])
        ts *= NANO
        yield AnnotateValue(key=key, timestamp=ts)


##########


class GazeValue(typing.NamedTuple):
    x: int
    y: int
    timestamp: float


class GazeDataFormatter(DataFormatter[GazeValue]):
    @staticmethod
    @functools.lru_cache(maxsize=1, typed=True)
    def get_formatter(
        format: DataFormat,
    ) -> typing.Union["GazeDataFormatter", UnsupportedFormatter]:
        if format == DataFormat.V3:
            return UnsupportedFormatter()
        if format == DataFormat.V4:
            return _GazeDataFormatter_V4()
        raise ValueError(format)

    def encode_msg(self, value: GazeValue) -> DataMessage:
        raise NotImplementedError()


class _GazeDataFormatter_V4(GazeDataFormatter):
    def decode_msg(self, data_msg: DataMessage) -> typing.Iterator[GazeValue]:
        (ts,) = struct.unpack("<Q", data_msg.header)
        ts *= NANO
        x, y = struct.unpack("<ff", data_msg.body)
        yield GazeValue(x=x, y=y, timestamp=ts)


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
    def get_formatter(
        format: DataFormat,
    ) -> typing.Union["IMUDataFormatter", UnsupportedFormatter]:
        if format == DataFormat.V3:
            return _IMUDataFormatter_V3()
        if format == DataFormat.V4:
            return _IMUDataFormatter_V4()
        raise ValueError(format)

    def encode_msg(self, value: IMUValue) -> DataMessage:
        raise NotImplementedError()


class _IMUDataFormatter_V3(IMUDataFormatter):
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

    def decode_msg(self, data_msg: DataMessage) -> typing.Iterator[IMUValue]:
        content = np.frombuffer(data_msg.body, dtype=self.CONTENT_DTYPE).view(
            np.recarray
        )
        for imu_frame in content:
            yield IMUValue(*imu_frame)


class _IMUDataFormatter_V4(IMUDataFormatter):
    CONTENT_DTYPE = np.dtype(
        [
            ("time_ns", "<u8"),
            ("accel_x", "<f4"),
            ("accel_y", "<f4"),
            ("accel_z", "<f4"),
            ("gyro_x", "<f4"),
            ("gyro_y", "<f4"),
            ("gyro_z", "<f4"),
        ]
    )

    def decode_msg(self, data_msg: DataMessage) -> typing.Iterator[IMUValue]:
        content = np.frombuffer(data_msg.body, dtype=self.CONTENT_DTYPE).view(
            np.recarray
        )
        for imu_frame in content:
            ts, *data = imu_frame
            ts *= NANO
            yield IMUValue(ts, *data)


##########


class EventValue(typing.NamedTuple):
    timestamp: float
    label: str


class EventDataFormatter(DataFormatter[EventValue]):
    @staticmethod
    @functools.lru_cache(maxsize=1, typed=True)
    def get_formatter(
        format: DataFormat,
    ) -> typing.Union["EventDataFormatter", UnsupportedFormatter]:
        if format == DataFormat.V3:
            return UnsupportedFormatter()
        if format == DataFormat.V4:
            return _EventDataFormatter_V4()
        raise ValueError(format)

    def encode_msg(self, value: EventValue) -> DataMessage:
        raise NotImplementedError()


class _EventDataFormatter_V4(EventDataFormatter):

    _encoding_lookup = {0: "utf-8"}

    def decode_msg(self, data_msg: DataMessage) -> typing.Iterator[EventValue]:
        """
        1. sensor UUID
        2. header:
            - int_64 timestamp_le
            - uint32 body_length_le
            - uint32 encoding_le
                = 0 -> "utf-8"
        3. body:
            - `encoding_le` encoded string of length `body_length_le`
        """
        ts, len_, enc_code = struct.unpack("<qii", data_msg.header)
        ts *= NANO
        enc = self._encoding_lookup[enc_code]
        body = data_msg.body.bytes[:len_]
        label = body.decode(enc)
        yield EventValue(label=label, timestamp=ts)
