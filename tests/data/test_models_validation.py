import numpy as np
import pytest

from nanonis.data.models import (
    DatColumn,
    DatData,
    ParserProvenance,
    SxmChannel,
    SxmData,
    SweepAxis,
)
from nanonis.data.validation import NonFiniteFileDataError, apply_nan_policy
from nanonis.geometry import FrameGeometry
from nanonis.types import NaNPolicy

PARSER = ParserProvenance("test", "1")


def test_sxm_model_checks_shapes_and_direction_availability():
    channel = SxmChannel("Z", "m", ("forward",), np.zeros((2, 3)))
    with pytest.raises(ValueError, match="shape"):
        SxmData(
            (channel,),
            FrameGeometry(0, 0, 1, 1),
            2,
            2,
            "down",
            {},
            "test.sxm",
            PARSER,
        )
    with pytest.raises(ValueError, match="availability"):
        SxmChannel("Z", "m", ("forward",), None)


def test_dat_model_checks_unique_columns():
    column = DatColumn("Current", "A", [1, 2])
    with pytest.raises(ValueError, match="unique"):
        DatData((column, column), {}, "test.dat", PARSER)


def test_shared_nan_policy_raises_with_diagnostics():
    data = DatData(
        (DatColumn("Current", "A", [1, np.nan, np.inf]),),
        {},
        "test.dat",
        PARSER,
    )
    with pytest.raises(NonFiniteFileDataError) as error:
        apply_nan_policy(data, NaNPolicy.RAISE)
    assert error.value.diagnostics.nan_count == 1
    assert error.value.diagnostics.inf_count == 1


def test_sweep_monotonicity_uses_finite_subsequence_for_nan_policy():
    axis = SweepAxis("Bias", "V", [0.0, np.nan, 1.0])
    assert axis.direction == "increasing"
    with pytest.raises(ValueError, match="monotonic"):
        SweepAxis("Bias", "V", [0.0, np.nan, 2.0, 1.0])
