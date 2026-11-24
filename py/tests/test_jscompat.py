import math

import pytest

from nodegoat.jscompat import parse_int, strict_equals, truthy


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("42", 42),
        ("  42", 42),
        ("\t\n12", 12),
        ("12 ", 12),
        ("42abc", 42),
        ("-7", -7),
        ("+7", 7),
        ("0x1f", 31),
        ("0X1F", 31),
        ("-0x10", -16),
        ("1e3", 1),
        ("3.9", 3),
        ("1_000", 1),
        (42, 42),
        (3.9, 3),
        (-3.9, -3),
        (0.5, 0),
        (5e-7, 5),
        (1e21, 1),
        ("9007199254740993", 9007199254740992.0),
    ],
)
def test_parse_int(value, expected):
    result = parse_int(value)
    assert result == expected
    if value == "9007199254740993":
        assert isinstance(result, float)


@pytest.mark.parametrize(
    "value",
    ["", "abc", "-", "0x", "0xg", "Infinity", "٣", None, True, {}, [5], float("nan"), float("inf")],
)
def test_parse_int_nan(value):
    assert math.isnan(parse_int(value))


def test_parse_int_huge_string():
    assert math.isinf(parse_int("9" * 5000))


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("a", "a", True),
        ("a", "b", False),
        ("1", 1, False),
        (1, 1.0, True),
        (True, 1, False),
        (True, True, True),
        (None, None, True),
        (None, "", False),
        ({}, {}, False),
        ([], [], False),
        (float("nan"), float("nan"), False),
    ],
)
def test_strict_equals(a, b, expected):
    assert strict_equals(a, b) is expected


@pytest.mark.parametrize("value", ["", 0, 0.0, None, False, float("nan")])
def test_truthy_false(value):
    assert truthy(value) is False


@pytest.mark.parametrize("value", ["0", " ", "false", [], {}, 1])
def test_truthy_true(value):
    assert truthy(value) is True
