import pytest

from ndsi.sensor import Sensor, SensorType


def test_supported_types():
    sensor_types = SensorType.supported_types()
    assert isinstance(sensor_types, set)
    assert len(sensor_types) > 0


def test_sensor_types_factory():
    # valid sensor types
    for sensor_type_expected in SensorType.supported_types():
        sensor_type_actual = SensorType.supported_sensor_type_from_str(
            str(sensor_type_expected)
        )
        assert sensor_type_actual is not None
        assert isinstance(sensor_type_actual, SensorType)
        assert sensor_type_actual is sensor_type_expected
    # invalid sensor types
    sensor_type = SensorType.supported_sensor_type_from_str("foo")
    assert sensor_type is None


def test_sensor_factory():
    for sensor_type in SensorType.supported_types():
        sensor_class = Sensor.class_for_type(sensor_type=sensor_type)
        assert issubclass(sensor_class, Sensor)
