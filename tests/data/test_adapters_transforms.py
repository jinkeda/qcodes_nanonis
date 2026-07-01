import numpy as np
import pytest

from nanonis.data.adapters.xarray import (
    grid_3ds_to_xarray,
    orient_sxm_array,
    sxm_raw_orders,
    sxm_to_xarray,
)
from nanonis.data.models import (
    Grid3DChannel,
    Grid3DData,
    ParserProvenance,
    SxmChannel,
    SxmData,
    SweepAxis,
)
from nanonis.data.transforms import (
    subtract_average,
    subtract_line,
    subtract_plane,
    subtract_vaverage,
    subtract_vline,
)
from nanonis.geometry import FrameGeometry
from nanonis.types import NaNPolicy


def test_sxm_orientation_convention_is_applied_only_by_adapter():
    raw = np.arange(6).reshape(2, 3)
    expected = np.flip(np.flip(raw, axis=0), axis=1)
    np.testing.assert_array_equal(
        orient_sxm_array(raw, scan_direction="up", data_direction="backward"),
        expected,
    )
    assert sxm_raw_orders("up", "backward") == (
        "bottom_to_top",
        "right_to_left",
    )


def test_sxm_xarray_has_oriented_values_and_physical_grids():
    raw = np.arange(6).reshape(2, 3)
    data = SxmData(
        (SxmChannel("Z", "m", ("forward",), raw),),
        FrameGeometry(0, 0, 3, 2),
        3,
        2,
        "up",
        {},
        "test.sxm",
        ParserProvenance("test", "1"),
    )
    dataset = sxm_to_xarray(data)
    np.testing.assert_array_equal(dataset["z_forward"], np.flip(raw, axis=0))
    assert dataset.x_m.shape == (2, 3)
    assert dataset.y_m[0, 0] > dataset.y_m[-1, 0]


def test_3ds_xarray_requires_explicit_unverified_row_order(caplog):
    data = Grid3DData(
        SweepAxis("Bias", "V", [-1, 1]),
        (Grid3DChannel("Current", "A", np.zeros((2, 2, 2))),),
        {"Z": np.zeros((2, 2))},
        FrameGeometry(0, 0, 2, 2),
        2,
        2,
        {},
        "test.3ds",
        ParserProvenance("test", "1"),
    )
    with pytest.raises(TypeError, match="row_order"):
        grid_3ds_to_xarray(data)  # type: ignore[call-arg]
    dataset = grid_3ds_to_xarray(data, row_order="bottom_to_top")
    assert dataset.attrs["orientation_ground_truth_validated"] is False
    assert "not ground-truth validated" in caplog.text


def test_finite_transforms_match_expected_detrending():
    yy, xx = np.indices((4, 5))
    plane = 2 * xx + 3 * yy + 7
    np.testing.assert_allclose(subtract_plane(plane), 0, atol=1e-12)
    np.testing.assert_allclose(subtract_line(plane), 0, atol=1e-12)
    np.testing.assert_allclose(subtract_vline(plane), 0, atol=1e-12)
    np.testing.assert_allclose(subtract_average(plane).mean(axis=1), 0)
    np.testing.assert_allclose(subtract_vaverage(plane).mean(axis=0), 0)


def test_transforms_fit_finite_values_and_preserve_nan():
    values = np.array([[1.0, 2.0, np.nan], [3.0, 4.0, 5.0]])
    output = subtract_line(values, nan_policy=NaNPolicy.ALLOW)
    assert np.isnan(output[0, 2])
    np.testing.assert_allclose(output[0, :2], 0, atol=1e-12)
    with pytest.raises(ValueError, match="non-finite"):
        subtract_line(values, nan_policy=NaNPolicy.RAISE)
