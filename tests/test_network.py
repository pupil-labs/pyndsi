import pytest

from ndsi.formatter import DataFormat
from ndsi.network import group_name_from_format


def test_group_name():
    group_names = set()
    data_formats = DataFormat.supported_formats()

    for format in data_formats:
        group_name = group_name_from_format(format=format)
        assert isinstance(group_name, str), "Group names must be instances of str"
        assert len(group_name) > 0, "Group names must be non-empty"
        group_names.add(group_name)

    assert len(group_names) == len(data_formats), "Group names must be unique"

    # Public spec
    assert group_name_from_format(DataFormat.V3) == "pupil-mobile-v3"
    assert group_name_from_format(DataFormat.V4) == "pupil-mobile-v4"
