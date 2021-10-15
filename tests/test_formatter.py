import collections
from datetime import datetime

import numpy as np
import pytest

from ndsi.formatter import (
    AnnotateDataFormatter,
    DataFormat,
    DataMessage,
    GazeDataFormatter,
    GazeValue,
    IMUDataFormatter,
    UnsupportedFormatter,
    VideoDataFormatter,
)

DataFixture = collections.namedtuple("DataFixture", ["value", "data_msg"])


@pytest.fixture
def gaze_v4_fixture() -> DataFixture:
    value = GazeValue(
        x=564.1744384765625, y=542.271240234375, timestamp=1564499230.2196853
    )
    data_msg = DataMessage(
        sensor_id="6678360f-9850-468e-8b44-47b7c43712dc",
        header=b"\x08\xcd\x9d\xc4\xc27\xb6\x15",
        body=b"*\x0b\rD\\\x91\x07D",
    )
    return DataFixture(value=value, data_msg=data_msg)


def test_supported_formats():
    formats = DataFormat.supported_formats()
    assert isinstance(formats, set)
    assert len(formats) > 0
    assert DataFormat.latest() in formats


def test_format_version():
    for format in DataFormat.supported_formats():
        major = format.version_major
        assert isinstance(major, int)
        assert major > 0


def test_gaze_formatter():
    for format in DataFormat.supported_formats():
        gaze_formatter = GazeDataFormatter.get_formatter(format=format)
        assert isinstance(gaze_formatter, (GazeDataFormatter, UnsupportedFormatter))


def test_gaze_formatter_v4(gaze_v4_fixture: DataFixture):
    formatter_v4 = GazeDataFormatter.get_formatter(format=DataFormat.V4)
    decoded_value = formatter_v4.decode_msg(data_msg=gaze_v4_fixture.data_msg)
    assert next(decoded_value) == gaze_v4_fixture.value


def test_annotate_formatter():
    for format in DataFormat.supported_formats():
        annotate_formatter = AnnotateDataFormatter.get_formatter(format=format)
        assert isinstance(
            annotate_formatter, (AnnotateDataFormatter, UnsupportedFormatter)
        )


def test_imu_formatter():
    for format in DataFormat.supported_formats():
        imu_formatter = IMUDataFormatter.get_formatter(format=format)
        assert isinstance(imu_formatter, (IMUDataFormatter, UnsupportedFormatter))


def test_imu_formatter_v4_decoding():
    imu_v4_fmt = IMUDataFormatter.get_formatter(format=DataFormat.V4)

    data_msg = DataMessage(
        sensor_id=b"fa25fb2f-ab58-4058-990c-bcd49a67c3ce",
        header=b"\x00\x00\x00\x00\x07\x00\x00\x00\x12\x00\x00\x00@\x02\x00\x00\x00\x00\x00\x00",
        body=b"\x81\x01\x9d}\xcaS\x86\x16\x00PB>\x00\xcc{?\x00\xa0\xec=\x90\xc1y=\x90\xc1y>\xfa\x18\x1c\xbfab\xe8}\xcaS\x86\x16\x00\xc0@>\x00\x18|?\x00\xa0\xe8=\x90\xc1y=,Q;>\xe1|\x0c\xbfA\xc33~\xcaS\x86\x16\x00 @>\x00<{?\x00@\xe0=\x00\x00\x00\x80,Q;>\xe1|\x0c\xbf!$\x7f~\xcaS\x86\x16\x00\xf0@>\x00\xc4{?\x00\x80\xeb=\x00\x00\x00\x80\x90\xc1y>\xe1|\x0c\xbf\x01\x85\xca~\xcaS\x86\x16\x00pA>\x00\xcc{?\x00\x00\xec=\x90\xc1\xf9\xbd\x90\xc1\xf9=\x90\xc1\xf9\xbe\xe1\xe5\x15\x7f\xcaS\x86\x16\x00PA>\x00L{?\x00\x00\xea=\x90\xc1y\xbd\x90\xc1\xf9=^\x89\xda\xbe\xc1Fa\x7f\xcaS\x86\x16\x00\xa0?>\x00\xf4z?\x00 \xe6=\x00\x00\x00\x80\x90\xc1\xf9=\xe1|\x0c\xbf\xa1\xa7\xac\x7f\xcaS\x86\x16\x00\xa0C>\x00|{?\x00\x80\xe1=\x90\xc1y=\x90\xc1y>\x13\xb5+\xbf\x81\x08\xf8\x7f\xcaS\x86\x16\x00@@>\x00${?\x00@\xe6=\x90\xc1\xf9=,Q;>\xe1|\x0c\xbfaiC\x80\xcaS\x86\x16\x00p?>\x00\xcc{?\x00\x00\xe4=\x90\xc1\xf9=\x90\xc1y=\x13\xb5+\xbfA\xca\x8e\x80\xcaS\x86\x16\x00\xf0B>\x00\x80{?\x00 \xee=\x90\xc1y=\x90\xc1\xf9=,Q;\xbf!+\xda\x80\xcaS\x86\x16\x00@C>\x00\xdcz?\x00\xc0\xe8=\x90\xc1\xf9=,Q;>\x13\xb5+\xbf\x01\x8c%\x81\xcaS\x86\x16\x00\xe0C>\x00\xa4{?\x00@\xe6=,Q;>\x90\xc1\xf9=\x13\xb5+\xbf\xe1\xecp\x81\xcaS\x86\x16\x00\xd0@>\x00\xcc{?\x00\x80\xea=\x90\xc1y=,Q;>\x13\xb5+\xbf\xc1M\xbc\x81\xcaS\x86\x16\x00\x80D>\x00\xc8{?\x00 \xe7=\x90\xc1y\xbd\xfa\x18\x9c>\xe1|\x0c\xbf\xa1\xae\x07\x82\xcaS\x86\x16\x00pA>\x00\xac{?\x00\xc0\xe5=\x90\xc1y=\x90\xc1\xf9=\xe1|\x0c\xbf\x81\x0fS\x82\xcaS\x86\x16\x00\xb0?>\x00\xb0{?\x00\xa0\xe5=\x00\x00\x00\x80\x90\xc1y>\x13\xb5+\xbfap\x9e\x82\xcaS\x86\x16\x00\xf0A>\x00\x88{?\x00@\xe7=\x00\x00\x00\x80\x90\xc1\xf9=\xfa\x18\x1c\xbf",
    )

    imu_vals = list(imu_v4_fmt.decode_msg(data_msg=data_msg))
    assert len(imu_vals) == 18

    for imu_val in imu_vals:
        assert isinstance(imu_val.timestamp, float)
        dt = datetime.utcfromtimestamp(imu_val.timestamp)
        assert (dt.day, dt.month, dt.year) == (7, 6, 2021)
        assert (dt.hour, dt.minute, dt.second) == (14, 40, 44)

        assert isinstance(imu_val.accel_x, np.float32), type(imu_val.accel_x)
        assert -1 <= imu_val.accel_x <= 1

        assert isinstance(imu_val.accel_y, np.float32)
        assert -1 <= imu_val.accel_y <= 1

        assert isinstance(imu_val.accel_z, np.float32)
        assert -1 <= imu_val.accel_z <= 1

        assert isinstance(imu_val.gyro_x, np.float32)
        assert -1 <= imu_val.gyro_x <= 1

        assert isinstance(imu_val.gyro_y, np.float32)
        assert -1 <= imu_val.gyro_y <= 1

        assert isinstance(imu_val.gyro_z, np.float32)
        assert -1 <= imu_val.gyro_z <= 1


def test_video_formatter():
    for format in DataFormat.supported_formats():
        imu_formatter = VideoDataFormatter.get_formatter(format=format)
        assert isinstance(imu_formatter, (VideoDataFormatter, UnsupportedFormatter))
