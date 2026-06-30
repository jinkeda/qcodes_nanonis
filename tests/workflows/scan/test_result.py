from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from nanonis.workflows import NaNPolicy, NonFiniteScanDataError
from nanonis.workflows.scan import (
    ScanChannelImage,
    ScanConfig,
    normalize_scan,
    normalize_scan_images,
)

from .test_models import snapshot


def test_image_owns_and_freezes_two_dimensional_data():
    source = np.arange(6.0).reshape(2, 3)
    image = ScanChannelImage("I", 0, "forward", source, "up")
    source[:] = -1

    assert not np.any(image.data == -1)
    assert not image.data.flags.writeable
    with pytest.raises(ValueError):
        image.data[0, 0] = 1


def test_grab_normalization_keeps_data_and_scan_directions_explicit():
    data = np.arange(6).reshape(2, 3)
    images = normalize_scan_images([
        (0, "forward", {"channel_name": "I", "scan_data_rows": 2,
                         "scan_data_columns": 3, "scan_data": data,
                         "scan_direction": 1}),
        (0, "backward", {"channel_name": "I", "scan_data_rows": 2,
                          "scan_data_columns": 3, "scan_data": data,
                          "scan_direction": 0}),
    ])
    assert [(image.direction, image.scan_direction) for image in images] == [
        ("forward", "up"), ("backward", "down")
    ]


def test_nan_raise_carries_normalized_scan_result():
    settings, _ = snapshot()
    now = datetime.now(timezone.utc)
    image = ScanChannelImage("I", 0, "forward", [[1, np.nan]])
    with pytest.raises(NonFiniteScanDataError) as caught:
        normalize_scan(
            (image,), saved_path="scan.sxm", config=ScanConfig((0,)),
            effective=settings, acquisition_started_at=now,
            acquisition_finished_at=now + timedelta(seconds=1),
            acquisition_duration=1, estimated_acquisition_duration=2,
            acquisition_timeout_used=8, nan_policy=NaNPolicy.RAISE,
        )
    assert caught.value.result.saved_path == "scan.sxm"
    assert caught.value.diagnostics.nan_count == 1
