"""Typed scan configuration, settings, and wire-value conversions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from typing import Any, Literal, Mapping, TypeAlias

from ...geometry import FrameGeometry
from ..errors import ScanResponseError
from ..models import TipRestorePolicy
from ..protocols import CommandClient

ScanDirection: TypeAlias = Literal["up", "down"]
DataDirection: TypeAlias = Literal["forward", "backward"]
SaveMode: TypeAlias = Literal["all", "next", "off"]
KeepConstant: TypeAlias = Literal["linear_speed", "time_per_line"]


def decode_on_off_get(value: int) -> bool:
    if int(value) not in (0, 1):
        raise ScanResponseError(f"invalid Scan.PropsGet on/off value {value!r}")
    return bool(value)


def encode_on_off_set(value: bool | None) -> int:
    return 0 if value is None else (1 if value else 2)


def decode_save_mode_get(value: int) -> SaveMode:
    try:
        return {0: "all", 1: "next", 2: "off"}[int(value)]  # type: ignore[return-value]
    except (KeyError, TypeError, ValueError) as exc:
        raise ScanResponseError(f"invalid scan save-mode value {value!r}") from exc


def encode_save_mode_set(value: SaveMode | None) -> int:
    if value is None:
        return 0
    try:
        return {"all": 1, "next": 2, "off": 3}[value]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"invalid scan save mode {value!r}") from exc


def decode_keep_constant_get(value: int) -> KeepConstant:
    try:
        return {0: "linear_speed", 1: "time_per_line"}[int(value)]  # type: ignore[return-value]
    except (KeyError, TypeError, ValueError) as exc:
        raise ScanResponseError(f"invalid Scan.SpeedGet selector {value!r}") from exc


def encode_keep_constant_set(value: KeepConstant | None) -> int:
    if value is None:
        return 0
    try:
        return {"linear_speed": 1, "time_per_line": 2}[value]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"invalid scan speed selector {value!r}") from exc


# Explicit aliases make each asymmetric protocol field discoverable.
decode_autosave_get = decode_save_mode_get
encode_autosave_set = encode_save_mode_set
decode_autopaste_get = decode_save_mode_get
encode_autopaste_set = encode_save_mode_set
decode_speed_keep_get = decode_keep_constant_get
encode_speed_keep_set = encode_keep_constant_set


@dataclass(frozen=True)
class ScanConfig:
    channel_indexes: tuple[int, ...]
    direction: ScanDirection = "up"
    pixels: int | None = None
    lines: int | None = None
    forward_line_time: float | None = None
    backward_line_time: float | None = None
    speed_ratio: float | None = None
    autosave: SaveMode | None = None
    series_name: str | None = None
    comment: str | None = None
    data_directions: tuple[DataDirection, ...] = ("forward",)
    grab_data: bool = True
    acquisition_timeout: float | None = None
    recovery_timeout: float = 15.0
    status_poll_interval: float = 0.1
    restore_state: bool = True
    restore_tip_state: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "channel_indexes", tuple(self.channel_indexes))
        object.__setattr__(self, "data_directions", tuple(self.data_directions))
        if not self.channel_indexes:
            raise ValueError("need >= 1 scan channel")
        if len(set(self.channel_indexes)) != len(self.channel_indexes):
            raise ValueError("duplicate channel indexes")
        if any(not isinstance(index, int) or isinstance(index, bool) or index < 0
               for index in self.channel_indexes):
            raise ValueError("channel indexes must be non-negative integers")
        if self.direction not in ("up", "down"):
            raise ValueError("direction must be 'up' or 'down'")
        if len(set(self.data_directions)) != len(self.data_directions):
            raise ValueError("duplicate data directions")
        if any(value not in ("forward", "backward") for value in self.data_directions):
            raise ValueError("invalid data direction")
        if self.grab_data and not self.data_directions:
            raise ValueError("grab_data requires at least one data direction")
        for dimension_name, dimension_value in (
            ("pixels", self.pixels),
            ("lines", self.lines),
        ):
            if dimension_value is not None and (
                not isinstance(dimension_value, int)
                or isinstance(dimension_value, bool)
                or dimension_value < 2
            ):
                raise ValueError(f"{dimension_name} must be an integer >= 2")
        for timing_name, timing_value in (
            ("forward_line_time", self.forward_line_time),
            ("backward_line_time", self.backward_line_time),
            ("speed_ratio", self.speed_ratio),
        ):
            if timing_value is not None and (
                not isfinite(timing_value) or timing_value <= 0
            ):
                raise ValueError(f"{timing_name} must be finite and > 0")
        if self.autosave is not None and self.autosave not in ("all", "next", "off"):
            raise ValueError("autosave must be 'all', 'next', 'off', or None")
        for text_name, text_value in (
            ("series_name", self.series_name),
            ("comment", self.comment),
        ):
            if text_value is not None and not isinstance(text_value, str):
                raise TypeError(f"{text_name} must be a string or None")
        if self.acquisition_timeout is not None and (
            not isfinite(self.acquisition_timeout) or self.acquisition_timeout <= 0
        ):
            raise ValueError("acquisition_timeout must be finite and > 0")
        if not isfinite(self.recovery_timeout) or self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be finite and > 0")
        if not isfinite(self.status_poll_interval) or self.status_poll_interval <= 0:
            raise ValueError("status_poll_interval must be finite and > 0")
        if self.status_poll_interval > self.recovery_timeout:
            raise ValueError("status_poll_interval cannot exceed recovery_timeout")


@dataclass(frozen=True)
class ScanSafetyPolicy:
    max_pixels: int
    max_lines: int
    piezo_safety_margin: float
    min_line_time: float
    max_line_time: float
    min_linear_speed: float
    max_linear_speed: float
    tip: TipRestorePolicy | None = None

    def __post_init__(self) -> None:
        if self.max_pixels < 2 or self.max_lines < 2:
            raise ValueError("scan dimension limits must be >= 2")
        if not isfinite(self.piezo_safety_margin) or self.piezo_safety_margin < 0:
            raise ValueError("piezo_safety_margin must be finite and >= 0")
        for low, high, label in (
            (self.min_line_time, self.max_line_time, "line time"),
            (self.min_linear_speed, self.max_linear_speed, "linear speed"),
        ):
            if not isfinite(low) or low <= 0 or not isfinite(high) or high < low:
                raise ValueError(f"invalid {label} safety bounds")


@dataclass(frozen=True, init=False)
class ScanRegion:
    """The scan frame: where/what to measure (center, size, rotation).

    A first-class, round-trippable value object: read the controller's current
    frame with :meth:`snapshot`, produce a modified copy with :meth:`patch`, and
    write it back with :meth:`apply`. Passed to ``ScanWorkflow.run`` as the
    per-shot target, separate from the stable ``ScanConfig`` recipe. All fields
    are SI (metres, degrees); ``angle`` defaults to 0.
    """

    geometry: FrameGeometry

    def __init__(
        self,
        center_x: float | FrameGeometry | None = None,
        center_y: float | None = None,
        width: float | None = None,
        height: float | None = None,
        angle: float = 0.0,
        *,
        geometry: FrameGeometry | None = None,
    ) -> None:
        if geometry is not None:
            if center_x is not None or any(
                value is not None for value in (center_y, width, height)
            ):
                raise TypeError("geometry cannot be combined with scalar frame fields")
            center_x = geometry
        if isinstance(center_x, FrameGeometry):
            if any(value is not None for value in (center_y, width, height)):
                raise TypeError("geometry cannot be combined with scalar frame fields")
            geometry = center_x
        else:
            if center_y is None or width is None or height is None:
                raise TypeError("center_y, width, and height are required")
            geometry = FrameGeometry(center_x, center_y, width, height, angle)
        object.__setattr__(self, "geometry", geometry)

    @property
    def center_x(self) -> float:
        return self.geometry.center_x

    @property
    def center_y(self) -> float:
        return self.geometry.center_y

    @property
    def width(self) -> float:
        return self.geometry.width

    @property
    def height(self) -> float:
        return self.geometry.height

    @property
    def angle(self) -> float:
        return self.geometry.angle

    @classmethod
    def snapshot(cls, client: CommandClient) -> "ScanRegion":
        """Read the controller's current frame via ``Scan.FrameGet``."""
        frame = _mapping(client.send("Scan.FrameGet"), "FrameGet")
        return cls(
            float(frame["center_x_m"]),
            float(frame["center_y_m"]),
            float(frame["width_m"]),
            float(frame["height_m"]),
            float(frame["angle_deg"]),
        )

    def apply(self, client: CommandClient) -> None:
        """Write this frame via ``Scan.FrameSet`` (five float32, no wait flag)."""
        client.send(
            "Scan.FrameSet",
            self.center_x,
            self.center_y,
            self.width,
            self.height,
            self.angle,
        )

    def patch(
        self,
        *,
        center_x: float | None = None,
        center_y: float | None = None,
        width: float | None = None,
        height: float | None = None,
        angle: float | None = None,
    ) -> "ScanRegion":
        """Return a copy with the given fields overridden; ``None`` keeps mine."""
        return type(self)(
            self.center_x if center_x is None else center_x,
            self.center_y if center_y is None else center_y,
            self.width if width is None else width,
            self.height if height is None else height,
            self.angle if angle is None else angle,
        )

    def corners(self) -> tuple[tuple[float, float], ...]:
        """Return rotated frame corners in controller coordinates."""
        return self.geometry.corners()


@dataclass(frozen=True)
class ScanSpeed:
    forward_linear_speed: float
    backward_linear_speed: float
    forward_time_per_line: float
    backward_time_per_line: float
    keep_parameter_constant: KeepConstant
    speed_ratio: float

    @classmethod
    def from_response(cls, response: Mapping[str, Any]) -> "ScanSpeed":
        return cls(
            float(response["forward_linear_speed_m_s"]),
            float(response["backward_linear_speed_m_s"]),
            float(response["forward_time_per_line_s"]),
            float(response["backward_time_per_line_s"]),
            decode_keep_constant_get(int(response["keep_parameter_constant"])),
            float(response["speed_ratio"]),
        )

    def setter_args(self) -> tuple[float, float, float, float, int, float]:
        return (
            self.forward_linear_speed,
            self.backward_linear_speed,
            self.forward_time_per_line,
            self.backward_time_per_line,
            encode_keep_constant_set(self.keep_parameter_constant),
            self.speed_ratio,
        )


@dataclass(frozen=True)
class ScanProps:
    continuous: bool
    bouncy: bool
    autosave: SaveMode
    series_name: str
    comment: str
    modules_names: tuple[str, ...]
    num_parameters_per_module: tuple[int, ...]
    parameters: tuple[tuple[str, ...], ...]
    autopaste: SaveMode

    @classmethod
    def from_response(cls, response: Mapping[str, Any]) -> "ScanProps":
        return cls(
            continuous=decode_on_off_get(int(response["continuous_scan"])),
            bouncy=decode_on_off_get(int(response["bouncy_scan"])),
            autosave=decode_autosave_get(int(response["autosave"])),
            series_name=str(response["series_name"]),
            comment=str(response["comment"]),
            modules_names=tuple(str(value) for value in response.get("modules_names", ())),
            num_parameters_per_module=tuple(
                int(value)
                for value in response.get("num_parameters_per_module_array", ())
            ),
            parameters=tuple(
                tuple(str(value) for value in row)
                for row in response.get("parameters", ())
            ),
            autopaste=decode_autopaste_get(int(response["autopaste"])),
        )

    def setter_args(self) -> tuple[Any, ...]:
        names = self.modules_names
        return (
            encode_on_off_set(self.continuous),
            encode_on_off_set(self.bouncy),
            encode_autosave_set(self.autosave),
            self.series_name,
            self.comment,
            sum(4 + len(name.encode("utf-8")) for name in names),
            len(names),
            names,
            encode_autopaste_set(self.autopaste),
        )


@dataclass(frozen=True)
class ScanSettings:
    frame: ScanRegion
    channels: tuple[int, ...]
    pixels: int
    lines: int
    props: ScanProps
    speed: ScanSpeed

    @classmethod
    def snapshot(cls, client: CommandClient) -> "ScanSettings":
        buffer = _mapping(client.send("Scan.BufferGet"), "BufferGet")
        props = _mapping(client.send("Scan.PropsGet"), "PropsGet")
        speed = _mapping(client.send("Scan.SpeedGet"), "SpeedGet")
        channels = tuple(int(value) for value in buffer["channel_indexes"])
        declared = int(buffer.get("num_channels", len(channels)))
        if declared != len(channels):
            raise ScanResponseError("Scan.BufferGet channel count does not match indexes")
        return cls(
            frame=ScanRegion.snapshot(client),
            channels=channels,
            pixels=int(buffer["pixels"]),
            lines=int(buffer["lines"]),
            props=ScanProps.from_response(props),
            speed=ScanSpeed.from_response(speed),
        )

    def patch(
        self, config: ScanConfig, region: "ScanRegion | None" = None
    ) -> "ScanSettings":
        frame = self.frame if region is None else region
        line_time_changed = (
            config.forward_line_time is not None
            or config.backward_line_time is not None
        )
        speed = replace(
            self.speed,
            forward_time_per_line=(
                self.speed.forward_time_per_line
                if config.forward_line_time is None
                else config.forward_line_time
            ),
            backward_time_per_line=(
                self.speed.backward_time_per_line
                if config.backward_line_time is None
                else config.backward_line_time
            ),
            speed_ratio=(
                self.speed.speed_ratio if config.speed_ratio is None else config.speed_ratio
            ),
            keep_parameter_constant=(
                "time_per_line" if line_time_changed else self.speed.keep_parameter_constant
            ),
        )
        props = replace(
            self.props,
            continuous=False,
            autosave=self.props.autosave if config.autosave is None else config.autosave,
            series_name=(
                self.props.series_name if config.series_name is None else config.series_name
            ),
            comment=self.props.comment if config.comment is None else config.comment,
        )
        return replace(
            self,
            frame=frame,
            channels=config.channel_indexes,
            pixels=self.pixels if config.pixels is None else config.pixels,
            lines=self.lines if config.lines is None else config.lines,
            props=props,
            speed=speed,
        )

    def apply(self, client: CommandClient) -> dict[str, BaseException]:
        """Write complete settings in lab-defined order, best effort."""
        operations = (
            (
                "frame",
                "Scan.FrameSet",
                (
                    self.frame.center_x,
                    self.frame.center_y,
                    self.frame.width,
                    self.frame.height,
                    self.frame.angle,
                ),
            ),
            (
                "buffer",
                "Scan.BufferSet",
                (len(self.channels), self.channels, self.pixels, self.lines),
            ),
            ("speed", "Scan.SpeedSet", self.speed.setter_args()),
            ("properties", "Scan.PropsSet", self.props.setter_args()),
        )
        failures: dict[str, BaseException] = {}
        for field, command, args in operations:
            try:
                client.send(command, *args)
            except BaseException as exc:
                failures[field] = exc
        return failures

    def restore(self, client: CommandClient) -> dict[str, BaseException]:
        return self.apply(client)


def _mapping(value: Any, command: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ScanResponseError(f"Scan.{command} must return a mapping")
    return value
