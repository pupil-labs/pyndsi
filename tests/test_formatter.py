import collections
import pytest
from ndsi.formatter import DataFormat, DataMessage
from ndsi.formatter import GazeDataFormatter, GazeValue
from ndsi.formatter import AnnotateDataFormatter
from ndsi.formatter import IMUDataFormatter
from ndsi.formatter import VideoDataFormatter


DataFixture = collections.namedtuple('DataFixture', ['value', 'data_msg'])


@pytest.fixture
def gaze_v4_fixture() -> DataFixture:
    value = GazeValue(
        x=564.1744384765625,
        y=542.271240234375,
        timestamp=1564499230.2196853,
    )
    data_msg = DataMessage(
        sensor_id='6678360f-9850-468e-8b44-47b7c43712dc',
        header=b'\x08\xcd\x9d\xc4\xc27\xb6\x15',
        body=b'*\x0b\rD\\\x91\x07D',
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
        assert isinstance(gaze_formatter, GazeDataFormatter)


def test_gaze_formatter_v4(gaze_v4_fixture: DataFixture):
    formatter_v4 = GazeDataFormatter.get_formatter(format=DataFormat.V4)
    decoded_value = formatter_v4.decode_msg(data_msg=gaze_v4_fixture.data_msg)
    assert decoded_value == gaze_v4_fixture.value


def test_annotate_formatter():
    for format in DataFormat.supported_formats():
        annotate_formatter = AnnotateDataFormatter.get_formatter(format=format)
        assert isinstance(annotate_formatter, AnnotateDataFormatter)


def test_imu_formatter():
    for format in DataFormat.supported_formats():
        imu_formatter = IMUDataFormatter.get_formatter(format=format)
        assert isinstance(imu_formatter, IMUDataFormatter)


def test_video_formatter():
    for format in DataFormat.supported_formats():
        imu_formatter = VideoDataFormatter.get_formatter(format=format)
        assert isinstance(imu_formatter, VideoDataFormatter)
