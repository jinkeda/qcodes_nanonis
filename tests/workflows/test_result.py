from dataclasses import replace
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from nanonis.workflows import (
    BiasSpectroscopyAdvanced,
    BiasSpectroscopyConfig,
    BiasSpectroscopySettings,
    BiasSpectroscopyTiming,
    NaNPolicy,
    NonFiniteSpectroscopyDataError,
    SpectroscopyParameter,
    SpectroscopyResponseError,
    normalize_bias_spectroscopy_response,
)
from nanonis.workflows.spectroscopy.result import BiasSpectroscopyResult


def config(**changes):
    value = BiasSpectroscopyConfig(-1, 1, 3, (0, 1))
    return replace(value, **changes)


def settings(**changes):
    value = BiasSpectroscopySettings(
        channels=(0, 1),
        save_all=False,
        sweeps=1,
        include_backward=False,
        points=3,
        autosave=False,
        show_save_dialog=False,
        timing=BiasSpectroscopyTiming(0.1, 0.0, 0.1, 1.0, 0.01, 0.02, 0.1, 0.1),
        advanced=BiasSpectroscopyAdvanced(False, True, False, False),
        limits=(-1, 1),
        parameter_names=("Start",),
        fixed_parameter_names=("Z",),
    )
    return replace(value, **changes)


def normalized(data=None, names=("Current (A)", "Current (A)"), nan_policy=NaNPolicy.WARN):
    matrix = np.arange(6).reshape(2, 3) if data is None else data
    now = datetime.now(timezone.utc)
    return normalize_bias_spectroscopy_response(
        {
            "channels_names": names,
            "num_channels": len(names),
            "data_rows": len(names),
            "data_columns": 3,
            "data": matrix,
            "num_parameters": 2,
            "parameters": [1.0, 2.0],
        },
        config=config(),
        effective=settings(),
        acquisition_started_at=now,
        acquisition_finished_at=now + timedelta(seconds=1),
        acquisition_duration=1.0,
        estimated_acquisition_duration=2.0,
        acquisition_timeout_used=8.0,
        nan_policy=nan_policy,
    )


def test_channel_major_duplicate_names_and_parameter_order_are_preserved():
    result = normalized()

    assert result.data.shape == (2, 3)
    assert result.points_match_request
    assert [trace.unique_name for trace in result.traces()] == [
        "Current (A)",
        "Current (A)#2",
    ]
    assert [parameter.name for parameter in result.parameters] == ["Z", "Start"]


def test_result_owns_and_freezes_matrix_while_traces_are_views():
    source = np.arange(6.0).reshape(2, 3)
    result = normalized(source)
    source[:] = -1

    assert not np.any(result.data == -1)
    assert not result.data.flags.writeable
    trace = result.traces()[0].values
    assert np.shares_memory(trace, result.data)
    with pytest.raises(ValueError):
        trace[0] = 4


def test_normalizer_rejects_shape_orientation_and_metadata_mismatch():
    now = datetime.now(timezone.utc)
    common = dict(
        config=config(),
        effective=settings(),
        acquisition_started_at=now,
        acquisition_finished_at=now,
        acquisition_duration=0,
        estimated_acquisition_duration=1,
        acquisition_timeout_used=6,
    )
    with pytest.raises(SpectroscopyResponseError, match="shape"):
        normalize_bias_spectroscopy_response(
            {
                "channels_names": ["one"],
                "num_channels": 1,
                "data_rows": 1,
                "data_columns": 3,
                "data": np.zeros((2, 3)),
                "num_parameters": 0,
                "parameters": [],
            },
            **common,
        )


def test_nan_raise_carries_fully_normalized_result():
    data = np.array([[1, np.nan, 3], [np.inf, 2, 3]])
    with pytest.raises(NonFiniteSpectroscopyDataError) as caught:
        normalized(data, nan_policy=NaNPolicy.RAISE)

    assert caught.value.result.data.shape == (2, 3)
    assert caught.value.diagnostics.nan_count == 1
    assert caught.value.diagnostics.inf_count == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"acquisition_started_at": datetime.now()},
        {"acquisition_duration": -1},
        {
            "acquisition_started_at": datetime.now(timezone.utc),
            "acquisition_finished_at": datetime.now(timezone.utc) - timedelta(days=1),
        },
    ],
)
def test_result_timestamps_and_duration_are_validated(changes):
    now = datetime.now(timezone.utc)
    kwargs = dict(
        channel_names=("one",),
        data=np.zeros((1, 2)),
        data_rows=1,
        data_columns=2,
        parameters=(SpectroscopyParameter(None, 1),),
        requested_config=config(points=2, channel_indexes=(0,)),
        effective_settings=settings(channels=(0,), points=2),
        acquisition_started_at=now,
        acquisition_finished_at=now,
        acquisition_duration=0,
        estimated_acquisition_duration=1,
        acquisition_timeout_used=2,
    )
    kwargs.update(changes)
    with pytest.raises(ValueError):
        BiasSpectroscopyResult(**kwargs)


def test_backward_and_forward_axes_are_explicit_reconstructions():
    result = normalized()
    assert result.forward_axis().values.tolist() == [-1, 0, 1]
    assert result.backward_axis().values.tolist() == [1, 0, -1]
    assert result.forward_axis().source == "configured sweep limits"

