import numpy as np
import pytest

from nanonis.data._utils import convert_to_si, split_label_unit


@pytest.mark.parametrize(
    ("unit", "expected_unit", "factor"),
    [
        ("pA", "A", 1e-12),
        ("nA", "A", 1e-9),
        ("uA", "A", 1e-6),
        ("µA", "A", 1e-6),
        ("mA", "A", 1e-3),
        ("uV", "V", 1e-6),
        ("µV", "V", 1e-6),
        ("mV", "V", 1e-3),
        ("nm", "m", 1e-9),
        ("um", "m", 1e-6),
        ("µm", "m", 1e-6),
        ("mm", "m", 1e-3),
        ("us", "s", 1e-6),
        ("µs", "s", 1e-6),
        ("ms", "s", 1e-3),
        ("kHz", "Hz", 1e3),
        ("mT", "T", 1e-3),
    ],
)
def test_convert_to_si_prefix_table(unit, expected_unit, factor):
    values, normalized = convert_to_si([1.0], unit)
    np.testing.assert_allclose(values, [factor], rtol=0, atol=abs(factor) * 1e-15)
    assert normalized == expected_unit


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Current (A)", ("Current", "A")),
        ("Z [nm]", ("Z", "nm")),
        ("Current (A) [filt]", ("Current [filt]", "A")),
        ("Sample index", ("Sample index", "")),
    ],
)
def test_split_label_unit(label, expected):
    assert split_label_unit(label) == expected


def test_unknown_unit_is_preserved_without_scaling():
    values, unit = convert_to_si([2.0], "arb")
    np.testing.assert_array_equal(values, [2.0])
    assert unit == "arb"
