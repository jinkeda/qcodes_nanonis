import numpy as np

from nanonis.data.models import (
    DatColumn,
    DatData,
    ParserProvenance,
    SxmChannel,
    SxmData,
)
from nanonis.geometry import FrameGeometry
from nanonis.qcodes.data import (
    add_dat_data,
    add_sxm_data,
    register_dat_data,
    register_sxm_data,
)


class Measurement:
    def __init__(self):
        self.parameters = []

    def register_custom_parameter(self, name, **kwargs):
        self.parameters.append((name, kwargs))


class Dataset:
    def __init__(self):
        self.metadata = {}

    def add_metadata(self, key, value):
        self.metadata[key] = value


class Datasaver:
    def __init__(self):
        self.dataset = Dataset()
        self.results = []

    def add_result(self, *pairs):
        self.results.append(pairs)


PARSER = ParserProvenance("test", "1")


def test_sxm_qcodes_adapter_uses_meshgrids_and_orients_file_data():
    raw = np.arange(6).reshape(2, 3)
    data = SxmData(
        (SxmChannel("Z", "m", ("forward",), raw),),
        FrameGeometry(0, 0, 3, 2),
        3,
        2,
        "up",
        {},
        "test.sxm",
        PARSER,
    )
    measurement = Measurement()
    registered = register_sxm_data(measurement, data)
    saver = Datasaver()
    add_sxm_data(saver, registered, data)

    pairs = dict(saver.results[0])
    assert pairs[registered.row].shape == (2, 3)
    np.testing.assert_array_equal(pairs[registered.channels[0][0]], raw[::-1])
    assert "parser" in saver.dataset.metadata
    assert "header_summary" in saver.dataset.metadata
    assert "header" not in saver.dataset.metadata


def test_dat_qcodes_adapter_uses_one_dimensional_sample_setpoint():
    data = DatData(
        (DatColumn("Bias", "V", [-1, 0, 1]), DatColumn("Current", "A", [1, 2, 3])),
        {},
        "test.dat",
        PARSER,
    )
    registered = register_dat_data(Measurement(), data)
    saver = Datasaver()
    add_dat_data(saver, registered, data)

    pairs = dict(saver.results[0])
    np.testing.assert_array_equal(pairs[registered.sample], [0, 1, 2])
    np.testing.assert_array_equal(pairs[registered.columns[1][0]], [1, 2, 3])
