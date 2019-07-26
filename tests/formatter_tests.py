import pytest
from ndsi.formatter import DataFormat
from ndsi.formatter import GazeDataFormatter
from ndsi.formatter import AnnotateDataFormatter
from ndsi.formatter import IMUDataFormatter
from ndsi.formatter import VideoDataFormatter


def test_supported_formats():
    formats = DataFormat.supported_formats()
    assert isinstance(formats, set)
    assert len(formats) > 0


def test_gaze_formatter():
    for format in DataFormat.supported_formats():
        gaze_formatter = GazeDataFormatter.get_formatter(format=format)
        assert isinstance(gaze_formatter, GazeDataFormatter)


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


if __name__ == "__main__":
    test_supported_formats()
    test_gaze_formatter()
    test_annotate_formatter()
    test_imu_formatter()
    test_video_formatter()
